import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, AsyncGenerator
from dataclasses import dataclass, asdict
from enum import Enum

from .analyzer_config import AnalyzerConfig, LLMProvider

logger = logging.getLogger(__name__)

class AnalysisStatus(Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    CLEANING = "cleaning"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class ActionItem:
    task: str
    owner: str
    deadline: Optional[str] = None
    
@dataclass
class MeetingAnalysis:
    summary: str
    key_decisions: List[str]
    discussion_points: List[str]
    action_items: List[ActionItem]
    
@dataclass
class AnalysisResult:
    analysis_id: str
    original_transcript: str
    cleaned_transcript: str
    meeting_analysis: MeetingAnalysis
    metadata: Dict
    status: AnalysisStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class MeetingAnalyzer:
    def __init__(self):
        self.config = AnalyzerConfig()
        self.provider = self.config.get_provider()
        self._setup_llm_client()
        
    def _setup_llm_client(self):
        """Initialize the appropriate LLM client based on configuration"""
        if self.provider == LLMProvider.OPENAI:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.config.OPENAI_API_KEY)
                self.model = self.config.OPENAI_MODEL
                logger.info(f"Using OpenAI model: {self.model}")
            except ImportError:
                raise ImportError("Please install openai: pip install openai")
                
        elif self.provider == LLMProvider.ANTHROPIC:
            try:
                from anthropic import AsyncAnthropic
                self.client = AsyncAnthropic(api_key=self.config.ANTHROPIC_API_KEY)
                self.model = self.config.ANTHROPIC_MODEL
                logger.info(f"Using Anthropic model: {self.model}")
            except ImportError:
                raise ImportError("Please install anthropic: pip install anthropic")
                
        elif self.provider == LLMProvider.LOCAL:
            try:
                from ..providers.local_llm_provider import OllamaProvider
                self.client = OllamaProvider(
                    api_url=self.config.LOCAL_API_URL,
                    model=self.config.LOCAL_MODEL
                )
                self.model = self.config.LOCAL_MODEL
                logger.info(f"Using local model via Ollama: {self.model}")
            except ImportError:
                raise ImportError("Local LLM provider module not found")
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def analyze_transcript(
        self, 
        transcript: str, 
        session_id: str,
        metadata: Optional[Dict] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        Analyze a meeting transcript and yield progress updates
        
        Yields progress updates with status and results
        """
        analysis_id = f"analysis_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = AnalysisResult(
            analysis_id=analysis_id,
            original_transcript=transcript,
            cleaned_transcript="",
            meeting_analysis=None,
            metadata=metadata or {},
            status=AnalysisStatus.PENDING,
            created_at=datetime.now()
        )
        
        try:
            # Yield initial status
            yield {
                "status": "analyzing",
                "progress": 10,
                "message": "Starting meeting analysis..."
            }
            
            # Check transcript length and chunk if necessary
            if len(transcript) > self.config.MAX_CONTEXT_LENGTH:
                chunks = self._chunk_transcript(transcript)
                logger.info(f"Transcript split into {len(chunks)} chunks")
            else:
                chunks = [transcript]
            
            # Analyze the transcript
            result.status = AnalysisStatus.ANALYZING
            yield {
                "status": "analyzing",
                "progress": 30,
                "message": "Analyzing meeting content and extracting insights..."
            }
            
            analysis_text = await self._call_llm_for_analysis(chunks)
            result.meeting_analysis = self._parse_analysis_response(analysis_text)
            
            # Evaluate analysis quality - for local provider, be more lenient since user explicitly wants local-only
            quality_check = self._evaluate_analysis_quality(result.meeting_analysis)
            
            if quality_check["should_retry"] and self.provider != LLMProvider.LOCAL:
                # Only use fallback for cloud providers - user explicitly wants local-only
                logger.warning(f"Analysis quality poor (score: {quality_check['score']}). Issues: {quality_check['issues']}")
                logger.info(f"Retrying with fallback provider: {self.config.FALLBACK_PROVIDER.value}")
                
                yield {
                    "status": "analyzing",
                    "progress": 40,
                    "message": f"Retrying analysis with {self.config.FALLBACK_PROVIDER.value} for better quality..."
                }
                
                # Create fallback analyzer
                fallback_analyzer = MeetingAnalyzer()
                fallback_analyzer.provider = self.config.FALLBACK_PROVIDER
                fallback_analyzer._setup_llm_client()
                
                # Retry analysis with fallback
                fallback_analysis_text = await fallback_analyzer._call_llm_for_analysis(chunks)
                fallback_result = self._parse_analysis_response(fallback_analysis_text)
                
                # Use fallback result if it's better
                fallback_quality = self._evaluate_analysis_quality(fallback_result)
                if fallback_quality["score"] > quality_check["score"]:
                    result.meeting_analysis = fallback_result
                    logger.info(f"Used fallback analysis (score improved: {quality_check['score']} → {fallback_quality['score']})")
                else:
                    logger.info(f"Kept original analysis (fallback score: {fallback_quality['score']})")
            elif quality_check["should_retry"] and self.provider == LLMProvider.LOCAL:
                # For local provider, log the quality issues but continue (per user requirement)
                logger.info(f"Local analysis quality score: {quality_check['score']}. Issues: {quality_check['issues']}")
                logger.info("Continuing with local analysis as requested (no fallback to cloud providers)")
            
            yield {
                "status": "analyzing", 
                "progress": 60,
                "message": "Meeting analysis complete. Cleaning transcript..."
            }
            
            # Clean the transcript
            result.status = AnalysisStatus.CLEANING
            yield {
                "status": "cleaning",
                "progress": 70,
                "message": "Formatting transcript for readability..."
            }
            
            cleaned_text = await self._call_llm_for_cleaning(chunks)
            result.cleaned_transcript = cleaned_text
            
            yield {
                "status": "cleaning",
                "progress": 90,
                "message": "Transcript cleaning complete. Finalizing..."
            }
            
            # Save results
            result.status = AnalysisStatus.COMPLETED
            result.completed_at = datetime.now()
            
            await self._save_results(result)
            
            # Yield final result
            yield {
                "status": "completed",
                "progress": 100,
                "message": "Analysis complete!",
                "result": {
                    "analysis_id": result.analysis_id,
                    "summary": result.meeting_analysis.summary,
                    "key_decisions": result.meeting_analysis.key_decisions,
                    "discussion_points": result.meeting_analysis.discussion_points,
                    "action_items": [asdict(item) for item in result.meeting_analysis.action_items],
                    "cleaned_transcript": result.cleaned_transcript,
                    "metadata": result.metadata
                }
            }
            
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            result.status = AnalysisStatus.ERROR
            result.error_message = str(e)
            
            yield {
                "status": "error",
                "progress": 0,
                "message": f"Analysis failed: {str(e)}",
                "error": str(e)
            }
    
    def _chunk_transcript(self, transcript: str) -> List[str]:
        """Split transcript into manageable chunks optimized for local models"""
        # For local provider, use larger chunks to leverage the 16K context window
        if self.provider == LLMProvider.LOCAL:
            chunk_size = min(self.config.MAX_CONTEXT_LENGTH * 2, 40000) - 1000  # Use more context
            overlap = self.config.CHUNK_OVERLAP * 2  # Increase overlap for better continuity
            logger.info(f"Using optimized chunking for local model: {chunk_size} chars with {overlap} overlap")
        else:
            chunk_size = self.config.MAX_CONTEXT_LENGTH - 1000  # Leave room for prompts
            overlap = self.config.CHUNK_OVERLAP
        
        chunks = []
        
        start = 0
        while start < len(transcript):
            end = min(start + chunk_size, len(transcript))
            
            # Try to break at sentence boundary
            if end < len(transcript):
                last_period = transcript.rfind('.', start, end)
                if last_period > start + chunk_size // 2:
                    end = last_period + 1
            
            chunks.append(transcript[start:end])
            start = end - overlap if end < len(transcript) else end
            
        logger.info(f"Transcript split into {len(chunks)} chunks (provider: {self.provider.value})")
        return chunks
    
    async def _call_llm_for_analysis(self, chunks: List[str]) -> str:
        """Call LLM to analyze the transcript chunks"""
        if self.provider == LLMProvider.OPENAI:
            return await self._call_openai_for_analysis(chunks)
        elif self.provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic_for_analysis(chunks)
        elif self.provider == LLMProvider.LOCAL:
            return await self._call_local_for_analysis(chunks)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def _call_openai_for_analysis(self, chunks: List[str]) -> str:
        """Call OpenAI API for analysis"""
        responses = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} for analysis")
            
            messages = [
                {
                    "role": "system",
                    "content": self.config.ANALYSIS_SYSTEM_PROMPT.format(
                        company_context=self.config.COMPANY_CONTEXT
                    )
                },
                {
                    "role": "user",
                    "content": self.config.ANALYSIS_USER_PROMPT.format(
                        transcript=chunk
                    )
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.config.TEMPERATURE,
                max_tokens=4000
            )
            
            responses.append(response.choices[0].message.content)
        
        # If multiple chunks, combine the analyses
        if len(responses) > 1:
            combined_prompt = f"""Combine these partial meeting analyses into one comprehensive analysis:

{chr(10).join(f"Part {i+1}:{chr(10)}{r}" for i, r in enumerate(responses))}

Provide a unified analysis following the original format."""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a meeting analysis expert."},
                    {"role": "user", "content": combined_prompt}
                ],
                temperature=self.config.TEMPERATURE,
                max_tokens=4000
            )
            
            return response.choices[0].message.content
        
        return responses[0]
    
    async def _call_anthropic_for_analysis(self, chunks: List[str]) -> str:
        """Call Anthropic API for analysis"""
        responses = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} for analysis")
            
            system_prompt = self.config.ANALYSIS_SYSTEM_PROMPT.format(
                company_context=self.config.COMPANY_CONTEXT
            )
            
            user_prompt = self.config.ANALYSIS_USER_PROMPT.format(
                transcript=chunk
            )
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=self.config.TEMPERATURE,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            responses.append(response.content[0].text)
        
        # If multiple chunks, combine the analyses
        if len(responses) > 1:
            combined_prompt = f"""Combine these partial meeting analyses into one comprehensive analysis:

{chr(10).join(f"Part {i+1}:{chr(10)}{r}" for i, r in enumerate(responses))}

Provide a unified analysis following the original format."""
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=self.config.TEMPERATURE,
                messages=[
                    {"role": "user", "content": combined_prompt}
                ]
            )
            
            return response.content[0].text
        
        return responses[0]
    
    async def _call_llm_for_cleaning(self, chunks: List[str]) -> str:
        """Call LLM to clean the transcript"""
        if self.provider == LLMProvider.OPENAI:
            return await self._call_openai_for_cleaning(chunks)
        elif self.provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic_for_cleaning(chunks)
        elif self.provider == LLMProvider.LOCAL:
            return await self._call_local_for_cleaning(chunks)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def _call_openai_for_cleaning(self, chunks: List[str]) -> str:
        """Call OpenAI API for transcript cleaning"""
        cleaned_parts = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} for cleaning")
            
            messages = [
                {
                    "role": "system",
                    "content": self.config.CLEANING_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": self.config.CLEANING_USER_PROMPT.format(
                        transcript=chunk
                    )
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.config.TEMPERATURE,
                max_tokens=4000
            )
            
            cleaned_parts.append(response.choices[0].message.content)
        
        return "\n\n---\n\n".join(cleaned_parts)
    
    async def _call_anthropic_for_cleaning(self, chunks: List[str]) -> str:
        """Call Anthropic API for transcript cleaning"""
        cleaned_parts = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} for cleaning")
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=self.config.TEMPERATURE,
                system=self.config.CLEANING_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": self.config.CLEANING_USER_PROMPT.format(
                            transcript=chunk
                        )
                    }
                ]
            )
            
            cleaned_parts.append(response.content[0].text)
        
        return "\n\n---\n\n".join(cleaned_parts)
    
    async def _call_local_for_analysis(self, chunks: List[str]) -> str:
        """Call local LLM (Ollama) for analysis with optimizations"""
        responses = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} for analysis with local model (estimated 30-60 seconds)")
            
            system_prompt = self.config.ANALYSIS_SYSTEM_PROMPT.format(
                company_context=self.config.COMPANY_CONTEXT
            )
            
            user_prompt = self.config.ANALYSIS_USER_PROMPT.format(
                transcript=chunk
            )
            
            # Use chat endpoint with optimized parameters for local model
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Optimized settings for local model performance and quality
            response = await self.client.chat(
                messages=messages,
                temperature=0.2,  # Lower temperature for more consistent output
                max_tokens=6000   # Increased for comprehensive analysis
            )
            
            responses.append(response)
            logger.info(f"Completed chunk {i+1}/{len(chunks)} analysis")
        
        # If multiple chunks, combine the analyses
        if len(responses) > 1:
            logger.info("Combining multiple chunk analyses into unified result")
            combined_prompt = f"""Combine these partial meeting analyses into one comprehensive analysis:

{chr(10).join(f"Part {i+1}:{chr(10)}{r}" for i, r in enumerate(responses))}

Provide a unified analysis following the original format."""
            
            messages = [
                {"role": "system", "content": "You are a meeting analysis expert."},
                {"role": "user", "content": combined_prompt}
            ]
            
            response = await self.client.chat(
                messages=messages,
                temperature=0.2,
                max_tokens=6000
            )
            
            return response
        
        return responses[0]
    
    async def _call_local_for_cleaning(self, chunks: List[str]) -> str:
        """Call local LLM (Ollama) for transcript cleaning with optimizations"""
        cleaned_parts = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} for cleaning with local model (estimated 20-40 seconds)")
            
            messages = [
                {
                    "role": "system",
                    "content": self.config.CLEANING_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": self.config.CLEANING_USER_PROMPT.format(
                        transcript=chunk
                    )
                }
            ]
            
            # Optimized settings for cleaning task
            response = await self.client.chat(
                messages=messages,
                temperature=0.1,  # Very low temperature for consistent cleaning
                max_tokens=5000   # Enough for detailed cleaning
            )
            
            cleaned_parts.append(response)
            logger.info(f"Completed chunk {i+1}/{len(chunks)} cleaning")
        
        return "\n\n---\n\n".join(cleaned_parts)
    
    def _parse_analysis_response(self, response_text: str) -> MeetingAnalysis:
        """Parse the LLM response into structured MeetingAnalysis"""
        lines = response_text.strip().split('\n')
        
        summary = ""
        key_decisions = []
        discussion_points = []
        action_items = []
        
        current_section = None
        current_action = {}
        
        for line in lines:
            line = line.strip()
            
            if not line:
                # Empty line might signal end of an action item
                if current_action and current_section == "actions":
                    if current_action.get("task"):
                        action_items.append(ActionItem(
                            task=current_action["task"],
                            owner=current_action.get("owner", "Team"),
                            deadline=current_action.get("deadline")
                        ))
                        current_action = {}
                continue
                
            # Detect section headers
            if "summary" in line.lower() and ("meeting" in line.lower() or "##" in line):
                current_section = "summary"
                continue
            elif "key decision" in line.lower() or "## key decision" in line.lower():
                current_section = "decisions"
                continue
            elif "discussion point" in line.lower() or "notable" in line.lower():
                current_section = "discussion"
                continue
            elif "action item" in line.lower():
                current_section = "actions"
                continue
            
            # Skip separator lines
            if line.startswith("===") or line.startswith("---") or line == "##":
                continue
            
            # Parse content based on current section
            if current_section == "summary":
                if not line.startswith(('#', '==', '--')):
                    summary += line + " "
            elif current_section == "decisions" and line.startswith(('-', '•', '*')):
                key_decisions.append(line.lstrip('-•* '))
            elif current_section == "discussion" and line.startswith(('-', '•', '*')):
                discussion_points.append(line.lstrip('-•* '))
            elif current_section == "actions":
                # Handle multiple action item formats
                if line.startswith("Task:"):
                    # Save previous action if exists
                    if current_action.get("task"):
                        action_items.append(ActionItem(
                            task=current_action["task"],
                            owner=current_action.get("owner", "Team"),
                            deadline=current_action.get("deadline")
                        ))
                    # Start new action (only if task text is not empty)
                    task_text = line[5:].strip()
                    if task_text:
                        current_action = {"task": task_text}
                    else:
                        current_action = {}
                elif line.startswith("Owner:"):
                    if current_action:
                        owner_text = line[6:].strip()
                        # Only set owner if we have a valid task
                        if current_action.get("task"):
                            current_action["owner"] = owner_text if owner_text and owner_text != "---" else "Team"
                elif line.startswith(("Deadline:", "Due:")):
                    if current_action:
                        deadline_text = line.split(":", 1)[1].strip()
                        current_action["deadline"] = deadline_text if deadline_text and deadline_text != "---" else None
                elif line.startswith(('-', '•', '*')):
                    # Parse action items with pipe delimiter or other formats
                    text = line.lstrip('-•* ')
                    
                    # Try pipe-delimited format first
                    if '|' in text:
                        parts = text.split('|')
                        if len(parts) >= 2:
                            task = parts[0].strip()
                            owner = parts[1].strip() if parts[1].strip() else "Team"
                            deadline = parts[2].strip() if len(parts) > 2 and parts[2].strip() else None
                            
                            if task:
                                action_items.append(ActionItem(
                                    task=task,
                                    owner=owner,
                                    deadline=deadline
                                ))
                    else:
                        # Try to extract from patterns like "Task (Owner) [Deadline]"
                        import re
                        
                        # Extract owner in parentheses
                        owner_match = re.search(r'\(([^)]+)\)', text)
                        owner = owner_match.group(1) if owner_match else "Team"
                        
                        # Extract deadline in brackets
                        deadline_match = re.search(r'\[([^\]]+)\]', text)
                        deadline = deadline_match.group(1) if deadline_match else None
                        
                        # Remove owner and deadline from task text
                        task = text
                        if owner_match:
                            task = task.replace(f"({owner_match.group(1)})", "")
                        if deadline_match:
                            task = task.replace(f"[{deadline_match.group(1)}]", "")
                        task = task.strip()
                        
                        if task:
                            action_items.append(ActionItem(
                                task=task,
                                owner=owner,
                                deadline=deadline
                            ))
        
        # Don't forget the last action item if we were building one
        if current_action and current_action.get("task"):
            action_items.append(ActionItem(
                task=current_action["task"],
                owner=current_action.get("owner", "Team"),
                deadline=current_action.get("deadline")
            ))
        
        # If no action items were found, try to extract from key decisions
        if not action_items and key_decisions:
            logger.info("No action items found, generating from key decisions")
            for decision in key_decisions[:3]:  # Take first 3 decisions
                # Convert decisions to action items
                if "will" in decision.lower() or "agreed to" in decision.lower():
                    # Extract the action part
                    task = decision.replace("will ", "").replace("agreed to ", "")
                    task = f"Implement: {task}" if not task.startswith(("Implement", "Execute")) else task
                    
                    # Try to identify owner from decision text
                    owner = "Team"
                    if "sales" in decision.lower():
                        owner = "Sales Team"
                    elif "operations" in decision.lower() or "ops" in decision.lower():
                        owner = "Operations Team"
                    elif "leadership" in decision.lower() or "management" in decision.lower():
                        owner = "Leadership Team"
                    elif "philcom" in decision.lower():
                        owner = "Philcom Team"
                    elif "rice" in decision.lower():
                        owner = "Rice Team"
                    
                    action_items.append(ActionItem(
                        task=task[:200],  # Limit length
                        owner=owner,
                        deadline="To be determined"
                    ))
        
        # If still no action items but discussion points exist, create follow-up tasks
        if not action_items and discussion_points:
            logger.info("No action items found, generating follow-up tasks from discussion points")
            for point in discussion_points[:2]:  # Take first 2 discussion points
                if any(word in point.lower() for word in ["debate", "concern", "risk", "issue", "discuss"]):
                    task = f"Address and resolve: {point[:150]}"
                    action_items.append(ActionItem(
                        task=task,
                        owner="Team",
                        deadline="Next meeting"
                    ))
        
        return MeetingAnalysis(
            summary=summary.strip(),
            key_decisions=key_decisions,
            discussion_points=discussion_points,
            action_items=action_items
        )
    
    def _evaluate_analysis_quality(self, analysis: MeetingAnalysis) -> dict:
        """Evaluate the quality of analysis results"""
        score = 0
        issues = []
        
        # Check if summary is meaningful (not empty, not too short)
        if not analysis.summary or len(analysis.summary.strip()) < 50:
            issues.append("Summary too short or empty")
        else:
            score += 3
            
        # Check for key decisions
        if not analysis.key_decisions:
            issues.append("No key decisions found")
        else:
            score += 2
            
        # Check for action items
        if not analysis.action_items:
            issues.append("No action items extracted")
        else:
            score += 2
            
        # Check for discussion points
        if analysis.discussion_points:
            score += 1
            
        # Check for generic/irrelevant content
        generic_phrases = ["hair loss", "generic", "unrelated", "example"]
        if any(phrase in analysis.summary.lower() for phrase in generic_phrases):
            issues.append("Analysis contains generic/irrelevant content")
            score -= 2
            
        quality_level = "good" if score >= 6 else "poor" if score < 3 else "fair"
        
        return {
            "score": score,
            "quality": quality_level,
            "issues": issues,
            "should_retry": quality_level == "poor" and self.config.ENABLE_FALLBACK
        }
    
    async def _save_results(self, result: AnalysisResult):
        """Save analysis results to files"""
        # Create analysis directory if it doesn't exist
        self.config.ANALYSIS_DIR.mkdir(exist_ok=True)
        
        # Save analysis JSON
        analysis_file = self.config.ANALYSIS_DIR / f"{result.analysis_id}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump({
                "analysis_id": result.analysis_id,
                "summary": result.meeting_analysis.summary,
                "key_decisions": result.meeting_analysis.key_decisions,
                "discussion_points": result.meeting_analysis.discussion_points,
                "action_items": [asdict(item) for item in result.meeting_analysis.action_items],
                "metadata": result.metadata,
                "created_at": result.created_at.isoformat(),
                "completed_at": result.completed_at.isoformat() if result.completed_at else None
            }, f, indent=2, ensure_ascii=False)
        
        # Save cleaned transcript
        cleaned_file = self.config.ANALYSIS_DIR / f"{result.analysis_id}_cleaned.txt"
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            f.write(result.cleaned_transcript)
        
        logger.info(f"Analysis results saved: {analysis_file} and {cleaned_file}")
    
    async def get_analysis(self, analysis_id: str) -> Optional[Dict]:
        """Retrieve a saved analysis by ID"""
        analysis_file = self.config.ANALYSIS_DIR / f"{analysis_id}.json"
        cleaned_file = self.config.ANALYSIS_DIR / f"{analysis_id}_cleaned.txt"
        
        if not analysis_file.exists():
            return None
        
        with open(analysis_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if cleaned_file.exists():
            with open(cleaned_file, 'r', encoding='utf-8') as f:
                data['cleaned_transcript'] = f.read()
        
        return data

# Global analyzer instance (initialized lazily)
analyzer = None

def get_analyzer():
    """Get the global analyzer instance, creating it if necessary"""
    global analyzer
    if analyzer is None:
        analyzer = MeetingAnalyzer()
    return analyzer