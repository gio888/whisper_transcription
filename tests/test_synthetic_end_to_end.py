#!/usr/bin/env python3
"""
Comprehensive synthetic tests for the entire pipeline
"""
import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables BEFORE importing config
load_dotenv()

from meeting_analyzer import MeetingAnalyzer, MeetingAnalysis, ActionItem
from notion_sync import get_notion_sync

# Synthetic Filipino/Taglish business meeting transcript
SYNTHETIC_TRANSCRIPT = """
Speaker A: Good morning everyone. So today we're here to discuss yung partnership between our company and Philcom. We need to talk about the sales process and how we can align better.

Speaker B: Yes, tama. The main issue is that we don't have visibility sa building administration. Kailangan natin ng transparency.

Speaker A: Exactly. So what we agreed on before is that we will use the direct-to-customer model. But we need to make sure na walang issues with the building admin.

Speaker B: I think we should schedule a meeting with the building management next week. Tapos we also need to review our current contracts.

Speaker A: Good idea. Also, we need to train our sales team on the new process. Siguro we can do that within two weeks?

Speaker B: Oo, that sounds reasonable. But we also need to create documentation para sa new procedures.

Speaker A: Alright, so let me summarize. We will meet with building admin, train the sales team, and create new documentation. Who will handle each task?

Speaker B: I can take care of the building admin meeting. For training, maybe our HR team can coordinate with sales?

Speaker A: Perfect. And I'll handle the documentation. When do we need to complete everything?

Speaker B: I think by end of this month would be good. That gives us enough time to implement before the next quarter.

Speaker A: Agreed. Let's also follow up on the Philcom integration status. We need to know kung ano na yung progress.

Speaker B: Yes, I'll check with their technical team this week. We should also prepare a risk assessment for the partnership.

Speaker A: Excellent. So we have clear action items now. Anything else we need to discuss?

Speaker B: Just one more thing - we need to inform our existing clients about the changes. Communication is key.

Speaker A: Good point. Let's add that to our tasks. I think we're good for today.
"""

async def test_1_action_item_extraction():
    """Test 1: Can we extract action items from synthetic transcript?"""
    print("🧪 TEST 1: ACTION ITEM EXTRACTION")
    print("=" * 50)
    
    try:
        analyzer = MeetingAnalyzer()
        
        # Simulate what the LLM would return
        synthetic_analysis = """
## Summary of the Meeting
Discussion focused on partnership between company and Philcom, addressing sales processes, building administration transparency, and implementation timeline.

## Key Decisions
• Will use direct-to-customer model for partnership
• Agreed to schedule building management meeting next week
• Sales team training to be completed within two weeks
• All tasks to be completed by end of month

## Notable Discussion Points
• Lack of visibility with building administration creates transparency concerns
• Need for proper documentation of new procedures
• Importance of client communication about changes
• Philcom integration status needs follow-up

## Action Items
Task: Schedule meeting with building management
Owner: Speaker B
Deadline: Next week

Task: Train sales team on new process
Owner: HR Team
Deadline: Within two weeks

Task: Create documentation for new procedures
Owner: Speaker A
Deadline: End of month

Task: Follow up on Philcom integration status
Owner: Speaker B
Deadline: This week

Task: Prepare risk assessment for partnership
Owner: Operations Team
Deadline: End of month

Task: Inform existing clients about changes
Owner: Communications Team
Deadline: End of month
"""
        
        # Parse the analysis
        result = analyzer._parse_analysis_response(synthetic_analysis)
        
        print(f"📊 RESULTS:")
        print(f"  Summary: {'✅ Present' if result.summary else '❌ Missing'} ({len(result.summary)} chars)")
        print(f"  Key Decisions: {'✅ Present' if result.key_decisions else '❌ Missing'} ({len(result.key_decisions)} items)")
        print(f"  Discussion Points: {'✅ Present' if result.discussion_points else '❌ Missing'} ({len(result.discussion_points)} items)")
        print(f"  Action Items: {'✅ Present' if result.action_items else '❌ Missing'} ({len(result.action_items)} items)")
        
        if result.action_items:
            print(f"\n📋 EXTRACTED ACTION ITEMS:")
            for i, item in enumerate(result.action_items, 1):
                print(f"  {i}. Task: {item.task}")
                print(f"     Owner: {item.owner}")
                print(f"     Deadline: {item.deadline or 'Not specified'}")
                print()
        
        success = len(result.action_items) >= 3
        print(f"🎯 TEST 1 RESULT: {'✅ PASS' if success else '❌ FAIL'}")
        return success, result
        
    except Exception as e:
        print(f"❌ TEST 1 FAILED WITH ERROR: {e}")
        return False, None

async def test_2_notion_meeting_creation(analysis_result):
    """Test 2: Can we create a meeting page in Notion?"""
    print(f"\n🧪 TEST 2: NOTION MEETING PAGE CREATION")
    print("=" * 50)
    
    try:
        # Convert MeetingAnalysis to the dict format expected by notion_sync
        analysis_data = {
            "analysis_id": f"test_synthetic_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "summary": analysis_result.summary,
            "key_decisions": analysis_result.key_decisions,
            "discussion_points": analysis_result.discussion_points,
            "action_items": [
                {
                    "task": item.task,
                    "owner": item.owner,
                    "deadline": item.deadline
                } for item in analysis_result.action_items
            ],
            "cleaned_transcript": SYNTHETIC_TRANSCRIPT[:2000],  # Limit for Notion
            "metadata": {"test": True},
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat()
        }
        
        print(f"📝 Creating meeting page with:")
        print(f"  - Summary: {len(analysis_data['summary'])} chars")
        print(f"  - Key Decisions: {len(analysis_data['key_decisions'])} items")
        print(f"  - Discussion Points: {len(analysis_data['discussion_points'])} items")
        print(f"  - Action Items: {len(analysis_data['action_items'])} items")
        print(f"  - Transcript: {len(analysis_data['cleaned_transcript'])} chars")
        
        # Test meeting creation
        notion = get_notion_sync()
        sync_result = await notion.sync_analysis_to_notion(analysis_data)
        
        print(f"\n📊 SYNC RESULTS:")
        print(f"  Success: {'✅ Yes' if sync_result.success else '❌ No'}")
        print(f"  Meeting ID: {sync_result.meeting_id or 'None'}")
        print(f"  Meeting URL: {sync_result.meeting_url or 'None'}")
        print(f"  Tasks Created: {len(sync_result.tasks_created)}")
        print(f"  Tasks Failed: {len(sync_result.tasks_failed)}")
        print(f"  Errors: {sync_result.errors}")
        
        # Verify the meeting page content
        if sync_result.meeting_id:
            print(f"\n🔍 VERIFYING MEETING PAGE CONTENT...")
            
            from notion_client import AsyncClient
            client = AsyncClient(auth=os.getenv("NOTION_API_KEY"))
            
            # Get page content
            children = await client.blocks.children.list(block_id=sync_result.meeting_id)
            actual_blocks = children['results']
            
            print(f"  📄 Page has {len(actual_blocks)} content blocks")
            
            # Check for key sections
            has_summary = any("Meeting Summary" in str(block) for block in actual_blocks)
            has_decisions = any("Key Decisions" in str(block) for block in actual_blocks)
            has_discussions = any("Discussion Points" in str(block) for block in actual_blocks)
            has_actions = any("Action Items" in str(block) for block in actual_blocks)
            has_transcript = any("Full Transcript" in str(block) for block in actual_blocks)
            
            print(f"  ✅ Summary section: {'Present' if has_summary else 'Missing'}")
            print(f"  ✅ Key Decisions section: {'Present' if has_decisions else 'Missing'}")
            print(f"  ✅ Discussion Points section: {'Present' if has_discussions else 'Missing'}")
            print(f"  ✅ Action Items section: {'Present' if has_actions else 'Missing'}")
            print(f"  ✅ Transcript toggle: {'Present' if has_transcript else 'Missing'}")
            
            content_complete = all([has_summary, has_decisions, has_discussions, has_actions, has_transcript])
        else:
            content_complete = False
        
        success = sync_result.success and sync_result.meeting_id and content_complete
        print(f"\n🎯 TEST 2 RESULT: {'✅ PASS' if success else '❌ FAIL'}")
        return success, sync_result
        
    except Exception as e:
        print(f"❌ TEST 2 FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False, None

async def test_3_notion_task_creation(sync_result):
    """Test 3: Were tasks properly created in Notion?"""
    print(f"\n🧪 TEST 3: NOTION TASK CREATION")
    print("=" * 50)
    
    try:
        if not sync_result or not sync_result.success:
            print("❌ Cannot test tasks - meeting creation failed")
            return False
        
        print(f"📊 TASK CREATION SUMMARY:")
        print(f"  Tasks Created: {len(sync_result.tasks_created)}")
        print(f"  Tasks Failed: {len(sync_result.tasks_failed)}")
        
        if sync_result.tasks_created:
            print(f"\n✅ SUCCESSFULLY CREATED TASKS:")
            
            from notion_client import AsyncClient
            client = AsyncClient(auth=os.getenv("NOTION_API_KEY"))
            
            for i, task_info in enumerate(sync_result.tasks_created, 1):
                task_id = task_info.get('task_id')
                task_name = task_info.get('task', 'Unknown')
                
                print(f"  {i}. Task: {task_name}")
                print(f"     ID: {task_id}")
                
                if task_id:
                    # Verify task properties
                    try:
                        task_page = await client.pages.retrieve(page_id=task_id)
                        properties = task_page["properties"]
                        
                        # Check meeting relation
                        meeting_relation = properties.get("Meeting", {}).get("relation", [])
                        has_meeting_link = len(meeting_relation) > 0
                        
                        # Check status
                        status = properties.get("Status", {}).get("status", {}).get("name", "Unknown")
                        
                        # Check priority
                        priority = properties.get("Priority", {}).get("select", {}).get("name", "Unknown")
                        
                        # Check owner
                        who = properties.get("Who", {}).get("select", {}).get("name", "Unknown")
                        
                        print(f"     ✅ Meeting Link: {'Yes' if has_meeting_link else 'No'}")
                        print(f"     ✅ Status: {status}")
                        print(f"     ✅ Priority: {priority}")
                        print(f"     ✅ Owner: {who}")
                        
                    except Exception as e:
                        print(f"     ❌ Error verifying task: {e}")
                
                print()
        
        if sync_result.tasks_failed:
            print(f"\n❌ FAILED TASKS:")
            for i, task_info in enumerate(sync_result.tasks_failed, 1):
                task_name = task_info.get('task', 'Unknown')
                error = task_info.get('error', 'No error details')
                print(f"  {i}. Task: {task_name}")
                print(f"     Error: {error}")
        
        success = len(sync_result.tasks_created) >= 3 and len(sync_result.tasks_failed) == 0
        print(f"\n🎯 TEST 3 RESULT: {'✅ PASS' if success else '❌ PARTIAL/FAIL'}")
        print(f"   Expected: At least 3 tasks created, 0 failures")
        print(f"   Actual: {len(sync_result.tasks_created)} created, {len(sync_result.tasks_failed)} failed")
        
        return success
        
    except Exception as e:
        print(f"❌ TEST 3 FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_all_tests():
    """Run all synthetic tests"""
    print("🚀 SYNTHETIC END-TO-END TESTING")
    print("=" * 60)
    print("Testing with synthetic Filipino/Taglish business meeting data")
    print("=" * 60)
    
    # Test 1: Action Item Extraction
    test1_pass, analysis_result = await test_1_action_item_extraction()
    
    if not test1_pass:
        print("\n💥 STOPPING - Test 1 failed. Fix action item extraction first.")
        return
    
    # Test 2: Notion Meeting Creation
    test2_pass, sync_result = await test_2_notion_meeting_creation(analysis_result)
    
    if not test2_pass:
        print("\n💥 STOPPING - Test 2 failed. Fix Notion meeting creation.")
        return
    
    # Test 3: Notion Task Creation
    test3_pass = await test_3_notion_task_creation(sync_result)
    
    # Final Summary
    print(f"\n🎯 FINAL TEST RESULTS")
    print("=" * 60)
    print(f"Test 1 - Action Item Extraction: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"Test 2 - Notion Meeting Creation: {'✅ PASS' if test2_pass else '❌ FAIL'}")
    print(f"Test 3 - Notion Task Creation: {'✅ PASS' if test3_pass else '❌ FAIL'}")
    
    all_pass = test1_pass and test2_pass and test3_pass
    
    if all_pass:
        print(f"\n🎉 ALL TESTS PASSED!")
        print("The system is ready for real speech-to-text analysis.")
        if sync_result and sync_result.meeting_url:
            print(f"\n📋 View test meeting: {sync_result.meeting_url}")
    else:
        print(f"\n⚠️  SOME TESTS FAILED")
        print("Fix the failing components before running real analysis.")
    
    return all_pass

if __name__ == "__main__":
    asyncio.run(run_all_tests())