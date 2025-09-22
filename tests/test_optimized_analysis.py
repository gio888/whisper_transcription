#!/usr/bin/env python3
"""
Optimized test for meeting analysis with performance measurements
Tests the complete pipeline with the actual failing transcript
"""
import asyncio
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# The actual transcript that was failing in production
REAL_TRANSCRIPT = """ Concerned lang because we are thinking of a high risk to a film concert, yun niya na menyo namin before because of the need to have in terms of documentation wise yun sa contract although you discussed with us or any mga nilagay ninyo para dun sa diniscass namin na satchitist pero may provisions, but anyway sir, I just want to be transparent lang.
 Tamaba kasi baka there's just a disconnect. Baka lang, there's just a disconnect. We just have to set the record straight because from our understanding sir is that ang magiging strategy natin for every lit building that we have, we will treat it as LMP.
 What's LMP again sir? Last mile partner. Yung sa inyong ata last tail ba yun? Naka-tail. Last mile sir. So ngayon, okay naman kami dun. It's just that based on our understanding, we cannot tell our client or the lit building na we will, we are in partner and we will be getting it from rice.
 So just to reiterate this because I do understand, I also talked to Mon kasi sabi ko Mon. I really want to understand because maybe ibalay yung process namin, ibayong sa inyo and what are ibadin kasi yung priorities namin, maka iba talaga yun. So we really want to make this like, how is it in your shoes right? So maybe one of the things that we can do is,
 if you can describe to us what is your sales process. So we can also identify at some point, we'll also present what our process is. Bakang maano natin saan yung disconnect or hindi mag-work. So is that okay if we can get your, how does, it doesn't have to be in detail of me NDA but I just want to understand how is it when you guys sell tapos ganyan."""

async def test_optimized_analysis():
    """Test the optimized meeting analyzer with performance measurements"""
    print("🚀 TESTING OPTIMIZED MEETING ANALYSIS")
    print("=" * 70)
    
    from meeting_analyzer import MeetingAnalyzer
    
    # Initialize with local provider
    analyzer = MeetingAnalyzer()
    
    print(f"📋 Configuration:")
    print(f"  Provider: {analyzer.provider.value}")
    print(f"  Model: {analyzer.model}")
    print(f"  Ollama URL: {analyzer.config.LOCAL_API_URL}")
    print()
    
    # Test connection first
    print("🔗 Testing Ollama connection...")
    connection_start = time.time()
    
    if hasattr(analyzer, 'client') and hasattr(analyzer.client, 'check_connection'):
        connected = await analyzer.client.check_connection()
    else:
        # Fallback connection test
        try:
            from local_llm_provider import OllamaProvider
            test_client = OllamaProvider()
            connected = await test_client.check_connection()
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            connected = False
    
    connection_time = time.time() - connection_start
    if connected:
        print(f"✅ Connected to Ollama in {connection_time:.2f}s")
    else:
        print(f"❌ Failed to connect to Ollama")
        return None
    
    print()
    print(f"📝 Test Transcript:")
    print(f"  Length: {len(REAL_TRANSCRIPT)} characters")
    print(f"  Preview: {REAL_TRANSCRIPT[:150]}...")
    print()
    
    # Test the complete analysis pipeline
    print("🧠 Running optimized analysis pipeline...")
    print("-" * 50)
    
    total_start = time.time()
    
    try:
        # Track progress and timing
        progress_log = []
        final_result = None
        
        async for update in analyzer.analyze_transcript(REAL_TRANSCRIPT, "optimized_test_session"):
            if "status" in update:
                timestamp = time.time() - total_start
                status_msg = f"[{timestamp:6.1f}s] {update['status']}: {update.get('message', '')}"
                print(f"  {status_msg}")
                progress_log.append({
                    "timestamp": timestamp,
                    "status": update['status'],
                    "message": update.get('message', ''),
                    "progress": update.get('progress', 0)
                })
            
            if "result" in update:
                final_result = update["result"]
        
        total_time = time.time() - total_start
        
        print(f"✅ Analysis completed in {total_time:.1f}s")
        print()
        
        if not final_result:
            print("❌ No result returned from analysis")
            return None
        
        # Analyze the results
        print("📊 PERFORMANCE ANALYSIS:")
        print("-" * 50)
        
        # Timing breakdown
        analysis_phases = {}
        for i, log in enumerate(progress_log):
            phase = log['status']
            if phase not in analysis_phases:
                analysis_phases[phase] = {"start": log['timestamp'], "end": log['timestamp']}
            analysis_phases[phase]['end'] = log['timestamp']
        
        print("⏱️  Phase Timing:")
        for phase, timing in analysis_phases.items():
            duration = timing['end'] - timing['start']
            print(f"  {phase}: {duration:.1f}s")
        
        print(f"\n⏱️  Total Processing Time: {total_time:.1f}s")
        print(f"⚡ Performance vs Previous: ~{max(1, 60/total_time):.1f}x faster" if total_time < 60 else f"⚠️  Still slow: {total_time:.1f}s")
        print()
        
        # Quality Analysis
        print("🎯 RESULTS QUALITY ANALYSIS:")
        print("-" * 50)
        
        quality_metrics = {
            "Summary": final_result.get('summary', ''),
            "Key Decisions": final_result.get('key_decisions', []),
            "Discussion Points": final_result.get('discussion_points', []),
            "Action Items": final_result.get('action_items', []),
            "Cleaned Transcript": final_result.get('cleaned_transcript', '')
        }
        
        for metric, value in quality_metrics.items():
            if isinstance(value, list):
                status = "✅ GOOD" if len(value) > 0 else "❌ MISSING"
                detail = f"Count: {len(value)}"
                if len(value) > 0:
                    # Show first item preview
                    first_item = value[0]
                    if isinstance(first_item, dict):
                        preview = first_item.get('task', str(first_item))[:50]
                    else:
                        preview = str(first_item)[:50]
                    detail += f" | Preview: {preview}..."
            elif isinstance(value, str):
                status = "✅ GOOD" if len(value) > 0 else "❌ MISSING"
                detail = f"Length: {len(value)} chars"
                if len(value) > 0:
                    detail += f" | Preview: {value[:50]}..."
            else:
                status = "❓ UNKNOWN"
                detail = f"Type: {type(value)}"
            
            print(f"  {metric}: {status}")
            print(f"    {detail}")
        
        # Critical Success Metrics
        print("\n🎯 CRITICAL SUCCESS METRICS:")
        print("-" * 50)
        
        success_criteria = {
            "Action Items Extracted": len(final_result.get('action_items', [])) > 0,
            "Response Time < 2min": total_time < 120,
            "Analysis Completed": final_result.get('summary') is not None,
            "No Errors": True  # If we got here, no major errors
        }
        
        all_passed = all(success_criteria.values())
        
        for criterion, passed in success_criteria.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {criterion}: {status}")
        
        # Final verdict
        print(f"\n{'='*70}")
        if all_passed:
            print("🎉 ALL OPTIMIZATIONS SUCCESSFUL!")
            print(f"   ✅ Analysis completed in {total_time:.1f}s")
            print(f"   ✅ {len(final_result.get('action_items', []))} action items extracted")
            print(f"   ✅ Ready for production use")
        else:
            print("⚠️  SOME ISSUES REMAIN:")
            failed_criteria = [k for k, v in success_criteria.items() if not v]
            for criterion in failed_criteria:
                print(f"   ❌ {criterion}")
        
        # Action Items Deep Dive (most critical)
        action_items = final_result.get('action_items', [])
        if action_items:
            print(f"\n🎯 ACTION ITEMS EXTRACTED ({len(action_items)}):")
            print("-" * 50)
            for i, item in enumerate(action_items[:5], 1):  # Show first 5
                if isinstance(item, dict):
                    task = item.get('task', 'No task specified')
                    owner = item.get('owner', 'No owner')
                    deadline = item.get('deadline', 'No deadline')
                    print(f"  {i}. Task: {task}")
                    print(f"     Owner: {owner}")
                    print(f"     Deadline: {deadline}")
                else:
                    print(f"  {i}. {item}")
                print()
        else:
            print("\n❌ CRITICAL ISSUE: NO ACTION ITEMS EXTRACTED!")
            print("   This suggests the optimization didn't solve the core problem.")
        
        return final_result
        
    except Exception as e:
        total_time = time.time() - total_start
        print(f"❌ Analysis failed after {total_time:.1f}s")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_notion_integration(analysis_result):
    """Test the Notion integration with the analysis result"""
    if not analysis_result:
        print("⏭️  Skipping Notion integration test (no analysis result)")
        return False
    
    print("\n📄 TESTING NOTION INTEGRATION:")
    print("-" * 50)
    
    try:
        from notion_sync import NotionSyncManager
        
        notion_manager = NotionSyncManager()
        
        print("🔗 Testing Notion connection...")
        
        # Create a test page
        notion_start = time.time()
        page_url = await notion_manager.sync_analysis(analysis_result, "Optimized Test Meeting")
        notion_time = time.time() - notion_start
        
        if page_url:
            print(f"✅ Notion page created in {notion_time:.1f}s")
            print(f"   📄 Page URL: {page_url}")
            return True
        else:
            print("❌ Notion page creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Notion integration failed: {e}")
        return False

async def main():
    """Run the complete optimized test suite"""
    print(f"🧪 OPTIMIZED MEETING ANALYSIS TEST SUITE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    
    # Test 1: Meeting Analysis
    analysis_result = await test_optimized_analysis()
    
    # Test 2: Notion Integration (if analysis succeeded)
    if analysis_result and os.getenv('NOTION_API_KEY'):
        notion_success = await test_notion_integration(analysis_result)
    else:
        print("⏭️  Skipping Notion integration test (no API key or analysis failed)")
        notion_success = False
    
    # Final Summary
    print(f"\n{'='*70}")
    print("🏁 FINAL TEST RESULTS:")
    print("-" * 30)
    print(f"Meeting Analysis: {'✅ SUCCESS' if analysis_result else '❌ FAILED'}")
    print(f"Notion Integration: {'✅ SUCCESS' if notion_success else '⏭️ SKIPPED/FAILED'}")
    
    if analysis_result:
        action_count = len(analysis_result.get('action_items', []))
        print(f"Action Items Extracted: {action_count}")
        print(f"Status: {'🚀 READY FOR PRODUCTION' if action_count > 0 else '⚠️ NEEDS ATTENTION'}")
    
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())