#!/usr/bin/env python3
"""
Test meeting analysis with the actual failing transcript
"""
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Save the actual transcript to a file for testing
REAL_TRANSCRIPT = """ Concerned lang because we are thinking of a high risk to a film concert, yun niya na menyo namin before because of the need to have in terms of documentation wise yun sa contract although you discussed with us or any mga nilagay ninyo para dun sa diniscass namin na satchitist pero may provisions, but anyway sir, I just want to be transparent lang.
 Tamaba kasi baka there's just a disconnect. Baka lang, there's just a disconnect. We just have to set the record straight because from our understanding sir is that ang magiging strategy natin for every lit building that we have, we will treat it as LMP.
 What's LMP again sir? Last mile partner. Yung sa inyong ata last tail ba yun? Naka-tail. Last mile sir. So ngayon, okay naman kami dun. It's just that based on our understanding, we cannot tell our client or the lit building na we will, we are in partner and we will be getting it from rice.
 So just to reiterate this because I do understand, I also talked to Mon kasi sabi ko Mon. I really want to understand because maybe ibalay yung process namin, ibayong sa inyo and what are ibadin kasi yung priorities namin, maka iba talaga yun. So we really want to make this like, how is it in your shoes right? So maybe one of the things that we can do is,
 if you can describe to us what is your sales process. So we can also identify at some point, we'll also present what our process is. Bakang maano natin saan yung disconnect or hindi mag-work. So is that okay if we can get your, how does, it doesn't have to be in detail of me NDA but I just want to understand how is it when you guys sell tapos ganyan."""

async def test_meeting_analysis():
    """Test the meeting analyzer with real transcript"""
    print("🧪 TESTING MEETING ANALYSIS WITH REAL TRANSCRIPT")
    print("=" * 60)
    
    from meeting_analyzer import MeetingAnalyzer
    
    analyzer = MeetingAnalyzer()
    
    print(f"📋 Configuration:")
    print(f"  Provider: {analyzer.provider}")
    print(f"  Model: {analyzer.model}")
    print(f"  Fallback: {os.getenv('ENABLE_ANALYSIS_FALLBACK', 'false')}")
    print()
    
    print(f"📝 Transcript length: {len(REAL_TRANSCRIPT)} characters")
    print(f"🔍 First 200 chars: {REAL_TRANSCRIPT[:200]}...")
    print()
    
    # Test the analysis
    print("🚀 Running analysis...")
    print("-" * 40)
    
    try:
        # analyze_transcript is a generator, so we need to iterate through it
        final_result = None
        async for update in analyzer.analyze_transcript(REAL_TRANSCRIPT, "test_session"):
            if "status" in update:
                print(f"  {update['status']}: {update.get('message', '')}")
            if "result" in update:
                final_result = update["result"]
        
        result = final_result
        
        print("✅ Analysis completed!")
        print()
        
        if not result:
            print("❌ No result returned from analysis")
            return None
            
        # Check the results - result is a dict with analysis data
        print("📊 ANALYSIS RESULTS:")
        print("-" * 40)
        
        print(f"Summary: {'✅' if result.get('summary') else '❌'}")
        if result.get('summary'):
            print(f"  Length: {len(result['summary'])} chars")
            print(f"  Preview: {result['summary'][:100]}...")
        
        print(f"\nKey Decisions: {'✅' if result.get('key_decisions') else '❌'}")
        if result.get('key_decisions'):
            print(f"  Count: {len(result['key_decisions'])}")
            for i, decision in enumerate(result['key_decisions'][:3], 1):
                print(f"  {i}. {decision[:60]}...")
        
        print(f"\nDiscussion Points: {'✅' if result.get('discussion_points') else '❌'}")
        if result.get('discussion_points'):
            print(f"  Count: {len(result['discussion_points'])}")
            for i, point in enumerate(result['discussion_points'][:3], 1):
                print(f"  {i}. {point[:60]}...")
        
        print(f"\nAction Items: {'✅' if result.get('action_items') else '❌'}")
        if result.get('action_items'):
            print(f"  Count: {len(result['action_items'])}")
            for i, item in enumerate(result['action_items'][:5], 1):
                if isinstance(item, dict):
                    print(f"  {i}. Task: {item.get('task', 'No task')[:50]}...")
                    print(f"     Owner: {item.get('owner', 'No owner')}")
                    print(f"     Deadline: {item.get('deadline', 'Not specified')}")
                else:
                    print(f"  {i}. Task: {item.task[:50]}...")
                    print(f"     Owner: {item.owner}")
                    print(f"     Deadline: {item.deadline or 'Not specified'}")
        else:
            print("  ⚠️  NO ACTION ITEMS EXTRACTED!")
        
        print(f"\nCleaned Transcript: {'✅' if result.get('cleaned_transcript') else '❌'}")
        if result.get('cleaned_transcript'):
            print(f"  Length: {len(result['cleaned_transcript'])} chars")
            # Check if action items are hiding in cleaned transcript
            if "action" in result['cleaned_transcript'].lower() or "task" in result['cleaned_transcript'].lower():
                print("  🔍 Found 'action' or 'task' keywords in cleaned transcript")
                # Find and show those sections
                lines = result['cleaned_transcript'].split('\n')
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['action', 'task', 'need to', 'will', 'should']):
                        print(f"    → {line[:80]}...")
        
        # Export the raw analysis for inspection
        print("\n📄 RAW ANALYSIS OUTPUT:")
        print("-" * 40)
        
        # Get the raw LLM response (if available)
        if hasattr(result, '_raw_response'):
            print(result._raw_response[:500])
        else:
            # Show key results
            sections = []
            if result.get('summary'):
                sections.append(f"Summary: {result['summary'][:100]}...")
            if result.get('key_decisions'):
                sections.append(f"Key Decisions: {len(result['key_decisions'])} items")
            if result.get('action_items'):
                sections.append(f"Action Items: {len(result['action_items'])} items")
            
            if sections:
                print('\n'.join(sections))
        
        # Final verdict
        print("\n🎯 VERDICT:")
        print("-" * 40)
        
        success_criteria = {
            "Summary exists": bool(result.get('summary')),
            "Key decisions found": bool(result.get('key_decisions')),
            "Discussion points found": bool(result.get('discussion_points')),
            "Action items found": bool(result.get('action_items')),
            "Cleaned transcript exists": bool(result.get('cleaned_transcript'))
        }
        
        for criteria, passed in success_criteria.items():
            print(f"{criteria}: {'✅ PASS' if passed else '❌ FAIL'}")
        
        all_pass = all(success_criteria.values())
        
        if all_pass:
            print("\n✅ ALL TESTS PASSED!")
        else:
            print("\n❌ SOME TESTS FAILED!")
            if not result.get('action_items'):
                print("\n⚠️  CRITICAL: No action items extracted despite clear tasks in transcript")
                print("   The transcript mentions:")
                print("   - Aligning sales processes")
                print("   - Understanding each other's processes")
                print("   - Being transparent with clients")
                print("   But these weren't extracted as action items!")
        
        return result
        
    except Exception as e:
        print(f"❌ Analysis failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_meeting_analysis())
    
    if result:
        print(f"\n📊 Final Summary:")
        print(f"Analysis produced results but action items: {len(result.get('action_items', [])) if result else 0}")
    else:
        print(f"\n❌ Analysis completely failed")