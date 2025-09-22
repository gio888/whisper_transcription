#!/usr/bin/env python3
"""
Test script for local LLM integration using Ollama
Tests both the OllamaProvider directly and meeting analysis integration
"""

import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_ollama_connection():
    """Test basic connection to Ollama server"""
    logger.info("Testing Ollama connection...")
    
    try:
        from local_llm_provider import OllamaProvider
        
        provider = OllamaProvider()
        connected = await provider.check_connection()
        
        if connected:
            logger.info("✅ Successfully connected to Ollama server")
            models = await provider.list_models()
            logger.info(f"Available models: {models}")
            return True
        else:
            logger.error("❌ Failed to connect to Ollama server")
            logger.info("Make sure Ollama is running: ollama serve")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing Ollama connection: {e}")
        return False

async def test_simple_generation():
    """Test simple text generation"""
    logger.info("\nTesting simple text generation...")
    
    try:
        from local_llm_provider import OllamaProvider
        
        provider = OllamaProvider()
        
        # Simple prompt test
        prompt = "What are the three main points from this meeting: We discussed the Q4 budget, decided to hire 2 new engineers, and scheduled the product launch for January."
        
        logger.info(f"Prompt: {prompt[:100]}...")
        response = await provider.generate(prompt)
        
        if response:
            logger.info(f"✅ Generated response: {response[:200]}...")
            return True
        else:
            logger.error("❌ No response generated")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error in text generation: {e}")
        return False

async def test_meeting_analysis():
    """Test full meeting analysis with local model"""
    logger.info("\nTesting meeting analysis with local model...")
    
    try:
        # Sample transcript for testing
        sample_transcript = """
        John: Good morning everyone. Let's start with our Q4 planning meeting.
        
        Sarah: Thanks John. First, I'd like to discuss our budget allocation. 
        We have $500K remaining for Q4, and I propose we allocate 60% to product development.
        
        Mike: That sounds reasonable. We also need to hire those two senior engineers we discussed last week.
        
        John: Agreed. Let's post those positions by end of week. 
        Sarah, can you work with HR on the job descriptions?
        
        Sarah: Will do. I'll have drafts ready by Thursday.
        
        Mike: Also, about the new product launch - are we still targeting January 15th?
        
        John: Yes, let's stick with January 15th. Mike, you'll lead the technical preparation.
        Sarah will handle the marketing campaign.
        
        Sarah: I'll need the product specs finalized by December 1st to prepare materials.
        
        Mike: No problem, we'll have everything ready.
        
        John: Great. Let's meet again next Tuesday to review progress. Thanks everyone.
        """
        
        # Test the meeting analyzer with local model
        from meeting_analyzer import get_analyzer
        
        analyzer = get_analyzer()
        logger.info("Meeting analyzer initialized with local model")
        
        # Run analysis
        logger.info("Starting transcript analysis...")
        analysis_complete = False
        
        async for update in analyzer.analyze_transcript(
            transcript=sample_transcript,
            session_id="test_local_001"
        ):
            status = update.get("status")
            progress = update.get("progress", 0)
            message = update.get("message", "")
            
            logger.info(f"Status: {status} - Progress: {progress}% - {message}")
            
            if status == "completed":
                analysis_complete = True
                result = update.get("result", {})
                
                logger.info("\n✅ Analysis completed successfully!")
                logger.info(f"Summary: {result.get('summary', 'N/A')[:200]}...")
                logger.info(f"Key Decisions: {result.get('key_decisions', [])[:2]}")
                logger.info(f"Action Items: {len(result.get('action_items', []))} items found")
                
            elif status == "error":
                logger.error(f"❌ Analysis failed: {update.get('error')}")
                
        return analysis_complete
        
    except Exception as e:
        logger.error(f"❌ Error in meeting analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("Starting Local LLM Integration Tests")
    logger.info("=" * 60)
    
    # Test 1: Connection
    connection_ok = await test_ollama_connection()
    if not connection_ok:
        logger.warning("Skipping remaining tests - Ollama connection failed")
        logger.info("\nTo fix:")
        logger.info("1. Make sure Ollama is installed: brew install ollama")
        logger.info("2. Start Ollama server: ollama serve")
        logger.info("3. Download model: ollama pull qwen2.5:7b")
        return
    
    # Test 2: Simple generation
    generation_ok = await test_simple_generation()
    
    # Test 3: Full meeting analysis
    analysis_ok = await test_meeting_analysis()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)
    logger.info(f"Connection Test: {'✅ PASSED' if connection_ok else '❌ FAILED'}")
    logger.info(f"Generation Test: {'✅ PASSED' if generation_ok else '❌ FAILED'}")
    logger.info(f"Analysis Test: {'✅ PASSED' if analysis_ok else '❌ FAILED'}")
    
    if all([connection_ok, generation_ok, analysis_ok]):
        logger.info("\n🎉 All tests passed! Local LLM integration is working.")
    else:
        logger.info("\n⚠️ Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    asyncio.run(main())