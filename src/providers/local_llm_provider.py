import asyncio
import aiohttp
import json
import logging
import time
from typing import AsyncGenerator, List, Dict, Optional

logger = logging.getLogger(__name__)

class OllamaProvider:
    """
    Local LLM provider using Ollama API
    Provides OpenAI-compatible interface for local model inference
    """
    
    def __init__(self, api_url: str = "http://localhost:11434", model: str = "qwen2.5:7b"):
        """
        Initialize Ollama provider
        
        Args:
            api_url: Ollama API endpoint URL
            model: Model name to use (e.g., qwen2.5:7b, llama3.2:8b)
        """
        self.api_url = api_url
        self.model = model
        self.timeout = aiohttp.ClientTimeout(total=600)  # 10 minute timeout for model loading + inference
        self._model_warmed = False
        self._session = None
        
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def check_connection(self) -> bool:
        """Check if Ollama server is running and accessible"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.api_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [m['name'] for m in data.get('models', [])]
                    if self.model in models:
                        logger.info(f"Ollama server connected. Model {self.model} available.")
                        # Warm up the model on first connection
                        await self._warmup_model()
                        return True
                    else:
                        logger.warning(f"Model {self.model} not found. Available models: {models}")
                        return False
                return False
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response using Ollama API
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for context
            
        Returns:
            Generated text response
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower for more consistent output
                "top_p": 0.9,
                "num_predict": 4000  # Max tokens to generate
            }
        }
        
        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            data = await self._make_request_with_retry("/api/generate", payload)
            return data.get("response", "")
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    async def generate_stream(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response using Ollama API
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for context
            
        Yields:
            Generated text chunks
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 4000
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.api_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status == 200:
                        async for line in response.content:
                            if line:
                                try:
                                    data = json.loads(line)
                                    if "response" in data:
                                        yield data["response"]
                                    if data.get("done", False):
                                        break
                                except json.JSONDecodeError:
                                    continue
                    else:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error: {response.status} - {error_text}")
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            raise
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4000
    ) -> str:
        """
        Chat completion endpoint compatible with OpenAI format
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        # Convert OpenAI-style messages to Ollama format
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": max_tokens
            }
        }
        
        try:
            data = await self._make_request_with_retry("/api/chat", payload)
            return data.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise
    
    async def list_models(self) -> List[str]:
        """List available models on the Ollama server"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.api_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return [m['name'] for m in data.get('models', [])]
                return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def _warmup_model(self) -> None:
        """Warm up the model to keep it loaded in memory"""
        if self._model_warmed:
            return
            
        logger.info(f"Warming up model {self.model}...")
        try:
            warmup_start = time.time()
            await self._make_request_with_retry(
                endpoint="/api/generate",
                payload={
                    "model": self.model,
                    "prompt": "Hello",
                    "stream": False,
                    "options": {"num_predict": 1}
                }
            )
            warmup_time = time.time() - warmup_start
            logger.info(f"Model warmup completed in {warmup_time:.1f}s")
            self._model_warmed = True
        except Exception as e:
            logger.warning(f"Model warmup failed: {e}")
    
    async def _make_request_with_retry(
        self,
        endpoint: str,
        payload: dict,
        max_retries: int = 3
    ) -> dict:
        """
        Make HTTP request with exponential backoff retry logic
        
        Args:
            endpoint: API endpoint (e.g., "/api/generate")
            payload: Request payload
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response data dictionary
        """
        for attempt in range(max_retries + 1):
            try:
                session = await self._get_session()
                async with session.post(
                    f"{self.api_url}{endpoint}",
                    json=payload
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 500 and attempt < max_retries:
                        # Retry on 500 errors (common with Ollama under load)
                        wait_time = (2 ** attempt) + (attempt * 0.1)  # Exponential backoff
                        logger.warning(f"Request failed with 500, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries + 1})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
            except asyncio.TimeoutError:
                if attempt < max_retries:
                    wait_time = (2 ** attempt) + (attempt * 0.1)
                    logger.warning(f"Request timed out, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception("Request timed out after all retry attempts")
            except Exception as e:
                if attempt < max_retries and "500" in str(e):
                    wait_time = (2 ** attempt) + (attempt * 0.1)
                    logger.warning(f"Request failed: {e}, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise