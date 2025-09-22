#!/usr/bin/env python3
"""
Test script for Filipino/Taglish support and analysis quality improvements
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

async def test_filipino_analysis():
    """Test analysis with Filipino/Taglish content similar to user's example"""
    logger.info("Testing Filipino/Taglish meeting analysis...")
    
    # Sample transcript with mixed content like the user's example
    filipino_transcript = """
    Speaker A: I just have 130 hard stock because I have to meet with EPI.
    Speaker B: Bakit? Where is the meeting?
    Speaker A: Because I'm going to EPI, okay? Nasa Makati kasi.
    Speaker B: Ah sige, no problem.
    Speaker A: No, it's on Makati, so I have to go back. But that's okay.
    I've explained to you guys what our plans are.
    Speaker B: Yes, nakuha namin.
    Speaker A: So yung discussion natin about the wholesale business...
    No, because after our meeting, I told you, we need to focus on partnerships.
    Speaker B: Tama, partnerships talaga ang kelangan natin.
    Speaker A: The whole sale, the situation is this.
    Would we actually talk to the cable companies and ISPs?
    Speaker B: Yes, and usually mga maliliit na ISP sa probinsya.
    Speaker A: Okay, so we're really just a challenger there.
    We need to build relationships with small cable companies.
    Speaker B: The transit is not that important to us right now.
    But yung infrastructure sharing, that's the key.
    Speaker A: I agree. Let's schedule another meeting next week to discuss the partnership strategy.
    Speaker B: Sige, I'll prepare the presentation about ISP partnerships.
    """
    
    try:
        from meeting_analyzer import get_analyzer
        
        analyzer = get_analyzer()
        logger.info("Meeting analyzer initialized")
        
        # Run analysis
        logger.info("Starting Filipino/Taglish transcript analysis...")
        analysis_complete = False
        
        async for update in analyzer.analyze_transcript(
            transcript=filipino_transcript,
            session_id="test_filipino_001"
        ):
            status = update.get("status")
            progress = update.get("progress", 0)
            message = update.get("message", "")
            
            logger.info(f"Status: {status} - Progress: {progress}% - {message}")
            
            if status == "completed":
                analysis_complete = True
                result = update.get("result", {})
                
                logger.info("\n" + "="*60)
                logger.info("ANALYSIS RESULTS")
                logger.info("="*60)
                logger.info(f"Summary: {result.get('summary', 'N/A')}")
                logger.info(f"\nKey Decisions ({len(result.get('key_decisions', []))}):")
                for i, decision in enumerate(result.get('key_decisions', []), 1):
                    logger.info(f"  {i}. {decision}")
                    
                logger.info(f"\nAction Items ({len(result.get('action_items', []))}):")
                for i, item in enumerate(result.get('action_items', []), 1):
                    logger.info(f"  {i}. {item.get('task')} | {item.get('owner')} | {item.get('deadline', 'No deadline')}")
                
                # Quality assessment
                if (result.get('summary') and 
                    len(result.get('key_decisions', [])) > 0 and 
                    len(result.get('action_items', [])) > 0):
                    logger.info("\n✅ Analysis quality: GOOD - Contains meaningful content")
                else:
                    logger.warning("\n⚠️ Analysis quality: POOR - Missing key elements")
                
            elif status == "error":
                logger.error(f"❌ Analysis failed: {update.get('error')}")
                
        return analysis_complete
        
    except Exception as e:
        logger.error(f"❌ Error in Filipino analysis test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_fallback_behavior():
    """Test fallback behavior with poor quality transcript"""
    logger.info("\nTesting fallback behavior with challenging content...")
    
    # Transcript with lots of [FOREIGN] markers like the user's example
    challenging_transcript = """
    Speaker A: [BLANK_AUDIO]
    Speaker B: [FOREIGN]
    Speaker A: Because I'm going to EPI, okay?
    Speaker B: [FOREIGN]
    Speaker A: No, it's on Makati, so I have to go back.
    But that's okay.
    Speaker B: [FOREIGN]
    Speaker A: [FOREIGN]
    Speaker B: [FOREIGN]
    Speaker A: How is that? How is our business?
    Speaker B: [FOREIGN]
    Speaker A: This year.
    Speaker B: [FOREIGN]
    Speaker A: The whole sale, the situation is this.
    Would we actually talk to the cable companies and ISPs?
    Speaker B: [FOREIGN]
    """
    
    try:
        from meeting_analyzer import get_analyzer
        
        analyzer = get_analyzer()
        
        fallback_triggered = False
        analysis_complete = False
        
        async for update in analyzer.analyze_transcript(
            transcript=challenging_transcript,
            session_id="test_fallback_001"
        ):
            status = update.get("status")
            progress = update.get("progress", 0)
            message = update.get("message", "")
            
            logger.info(f"Status: {status} - Progress: {progress}% - {message}")
            
            # Check if fallback was triggered
            if "fallback" in message.lower() or "retrying" in message.lower():
                fallback_triggered = True
                logger.info("🔄 Fallback mechanism activated!")
            
            if status == "completed":
                analysis_complete = True
                result = update.get("result", {})
                
                logger.info(f"\nFallback triggered: {'✅ YES' if fallback_triggered else '❌ NO'}")
                logger.info(f"Summary length: {len(result.get('summary', ''))}")
                logger.info(f"Decisions found: {len(result.get('key_decisions', []))}")
                logger.info(f"Action items: {len(result.get('action_items', []))}")
                
        return analysis_complete and fallback_triggered
        
    except Exception as e:
        logger.error(f"❌ Error in fallback test: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("Starting Filipino/Taglish Integration Tests")
    logger.info("=" * 60)
    
    # Test 1: Filipino/Taglish analysis
    filipino_ok = await test_filipino_analysis()
    
    # Test 2: Fallback behavior
    fallback_ok = await test_fallback_behavior()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)
    logger.info(f"Filipino/Taglish Analysis: {'✅ PASSED' if filipino_ok else '❌ FAILED'}")
    logger.info(f"Fallback Mechanism: {'✅ PASSED' if fallback_ok else '❌ FAILED'}")
    
    if filipino_ok and fallback_ok:
        logger.info("\n🎉 All improvements working! System should now handle:")
        logger.info("   • Filipino/Taglish mixed content")
        logger.info("   • Automatic quality detection")
        logger.info("   • Fallback to cloud models when needed")
    else:
        logger.info("\n⚠️ Some issues detected. Check logs for details.")
    
    logger.info("\n💡 Next steps:")
    logger.info("   1. Update whisper config to use 'auto' language detection")
    logger.info("   2. Test with actual audio files containing Filipino")
    logger.info("   3. Verify fallback works with real poor-quality transcripts")

if __name__ == "__main__":
    asyncio.run(main())