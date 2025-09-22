#!/usr/bin/env python3
"""
Test with real Filipino/Taglish business meeting transcript
"""
import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables BEFORE importing config
load_dotenv()

from meeting_analyzer import MeetingAnalyzer
from notion_sync import get_notion_sync

# This is a truncated version of the actual Filipino/Taglish transcript
FILIPINO_TRANSCRIPT = """
Speaker A: Concerned lang because we are thinking of a high risk. Yun niya na mention namin before because of the need to have in terms of documentation wise yun sa contract. I just want to be transparent lang.

Speaker B: Tama ba kasi baka there's just a disconnect. We just have to set the record straight because from our understanding sir is that ang magiging strategy natin for every lit building that we have, we will treat it as LMP.

Speaker A: What's LMP again sir? Last mile partner. So ngayon, okay naman kami dun. It's just that based on our understanding, we cannot tell our client or the lit building na we are in partner and we will be getting it from Rice.

Speaker B: So just to reiterate this, I really want to understand because maybe iba yung process namin, iba yung sa inyo. So we really want to make this like, how is it in your shoes right? If you can describe to us what is your sales process.

Speaker A: The primary reason is really to understand it from your side kasi baka iba yung mindset namin. Number two is, we had some problems also with you being our tail partner in some areas, which became a really big concern escalated na to the top management.

Speaker B: Siguro one thing that we would want to align is, how do you sell in buildings wherein Philcom is not yet there in the building? From the site acquisition perspective, if the building requires us to have MOC or TOR, we will comply regardless if it is DTC or LMP.

Speaker A: Even if you are not in the building, you will still talk to the building and let them know that we are going to use example lang PLDT to install your client. What is your contract with the building? Do you pay anything?

Speaker B: It depends. Some of the buildings nagpapabayad sila ng access fee, some wala naman. From telcos naman, we know that it's a win-win solution if we don't have presence there, we can get it from other telcos and vice versa.

Speaker A: For example, the affiliates yung mga ibang like China Bank, of course not all is in the on-net buildings namin. So meron talaga na ibibigay nung client dun sa 300 plus nila. We have to be transparent especially kung yun naman ang concern with the government.

Speaker B: Ang nangyari kasi is nagbid kami knowing that the building is nandun na kami sa labas. But the building itself hindi siya on-net ni Philcom. Only to find out the building stops us kasi meron na kami dito na certain telco sir, so hindi ka pwedeng pumasok.

Speaker A: Two things I want to ask. If we're going to do this, especially for selected clients, we'd require a redundant connection. Second thing is we want to align with you guys on the cadence of our builds. We acquire and wire buildings regardless of our sales velocity.

Speaker B: We're acquiring around 10 to 20 buildings a month. We're wiring around 10 buildings a month as well. I want to know what is your build velocity on the OSP. Kasi hindi mag-work kung sa amin lang yung nandun.

Speaker A: So internally, may discuss namin yung worst case scenarios. The possibility is there but let's meet in the middle. We really want this partnership to work.
"""

# Simulated analysis output that would come from the LLM
SIMULATED_ANALYSIS = """
## Summary of the Meeting
The meeting focused on establishing a partnership between Philcom and Rice for telecommunications services, addressing concerns about transparency with building administrators, Last Mile Partner (LMP) vs Direct to Customer (DTC) models, and risk management. Key challenges discussed include building access rights, partner coordination, and the need for redundant connections.

## Key Decisions
• Both companies will align their sales processes for buildings where they don't have presence
• Philcom will be transparent with clients about using Rice as a partner, but careful with building administration communication
• Rice agreed to shoulder penalties for the first 3 months if building admin discovers the partnership arrangement
• Redundant connections will be required for strategic clients to mitigate risks
• Both parties will align their build velocity to ensure coordinated deployment

## Notable Discussion Points
• Transparency concerns with building administration about partner arrangements
• Previous bad experiences with tail partners that escalated to top management
• Different approaches between LMP (Last Mile Partner) and DTC (Direct to Customer) models
• Building access fees vary - some buildings charge, others don't
• Government contracts require full transparency about last mile partners
• Risk of being blocked by buildings that have exclusive telco arrangements
• Need for 10-20 buildings per month acquisition and wiring velocity

## Action Items
Task: Document and align sales processes between Philcom and Rice
Owner: Sales Teams (both companies)
Deadline: Within 2 weeks

Task: Create risk management protocol for building admin discovery scenarios
Owner: Operations Team
Deadline: Next week

Task: Establish redundancy requirements for strategic clients
Owner: Network Engineering Team
Deadline: Within 1 week

Task: Align build velocity plans for OSP and in-building infrastructure
Owner: Infrastructure Planning Team
Deadline: End of month

Task: Develop transparency guidelines for client and building communications
Owner: Legal and Compliance Team
Deadline: Within 2 weeks

Task: Review and address previous tail partner issues
Owner: Operations Management
Deadline: Immediate

Task: Map out buildings with exclusive telco arrangements
Owner: Site Acquisition Team
Deadline: Within 3 weeks

Task: Create pricing model for penalty scenarios
Owner: Finance Team
Deadline: Within 2 weeks
"""

async def test_filipino_meeting():
    """Test the complete pipeline with Filipino/Taglish business meeting"""
    print("🚀 TESTING WITH FILIPINO/TAGLISH BUSINESS MEETING")
    print("=" * 60)
    
    # Test 1: Parse the analysis
    print("\n📋 TEST 1: PARSING ANALYSIS")
    print("-" * 40)
    
    analyzer = MeetingAnalyzer()
    result = analyzer._parse_analysis_response(SIMULATED_ANALYSIS)
    
    print(f"Summary: {'✅' if result.summary else '❌'} ({len(result.summary)} chars)")
    print(f"Key Decisions: {'✅' if result.key_decisions else '❌'} ({len(result.key_decisions)} items)")
    print(f"Discussion Points: {'✅' if result.discussion_points else '❌'} ({len(result.discussion_points)} items)")
    print(f"Action Items: {'✅' if result.action_items else '❌'} ({len(result.action_items)} items)")
    
    if result.action_items:
        print(f"\n🎯 EXTRACTED ACTION ITEMS:")
        for i, item in enumerate(result.action_items, 1):
            print(f"{i}. {item.task[:60]}...")
            print(f"   Owner: {item.owner} | Deadline: {item.deadline or 'Not set'}")
    
    # Test 2: Create Notion meeting
    print(f"\n📄 TEST 2: CREATING NOTION MEETING PAGE")
    print("-" * 40)
    
    # Convert to format expected by Notion sync
    analysis_data = {
        "analysis_id": f"test_filipino_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "summary": result.summary,
        "key_decisions": result.key_decisions,
        "discussion_points": result.discussion_points,
        "action_items": [
            {
                "task": item.task,
                "owner": item.owner,
                "deadline": item.deadline
            } for item in result.action_items
        ],
        "cleaned_transcript": FILIPINO_TRANSCRIPT,
        "metadata": {
            "test": True,
            "language": "Filipino/Taglish",
            "meeting_type": "Partnership Discussion"
        },
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat()
    }
    
    try:
        notion = get_notion_sync()
        sync_result = await notion.sync_analysis_to_notion(analysis_data)
        
        print(f"Meeting Created: {'✅' if sync_result.meeting_id else '❌'}")
        if sync_result.meeting_id:
            print(f"  ID: {sync_result.meeting_id}")
            print(f"  URL: {sync_result.meeting_url}")
        
        print(f"Tasks Created: {len(sync_result.tasks_created)}")
        print(f"Tasks Failed: {len(sync_result.tasks_failed)}")
        
        # Test 3: Verify content
        print(f"\n🔍 TEST 3: VERIFYING CONTENT")
        print("-" * 40)
        
        if sync_result.meeting_id:
            from notion_client import AsyncClient
            client = AsyncClient(auth=os.getenv("NOTION_API_KEY"))
            
            # Check page content
            children = await client.blocks.children.list(block_id=sync_result.meeting_id)
            blocks = children['results']
            
            # Check for key content
            has_filipino_content = any("Philcom" in str(block) or "Rice" in str(block) for block in blocks)
            has_lmp_discussion = any("LMP" in str(block) or "Last Mile" in str(block) for block in blocks)
            has_transparency = any("transparency" in str(block).lower() for block in blocks)
            
            print(f"Filipino/Business Terms: {'✅' if has_filipino_content else '❌'}")
            print(f"LMP/DTC Discussion: {'✅' if has_lmp_discussion else '❌'}")
            print(f"Transparency Topics: {'✅' if has_transparency else '❌'}")
            print(f"Total Content Blocks: {len(blocks)}")
        
        # Test 4: Verify tasks
        print(f"\n✅ TEST 4: TASK VERIFICATION")
        print("-" * 40)
        
        critical_tasks = [
            "sales processes",
            "risk management",
            "redundancy",
            "build velocity",
            "transparency"
        ]
        
        tasks_found = []
        for task_info in sync_result.tasks_created:
            task_name = task_info.get('task', '').lower()
            for critical in critical_tasks:
                if critical in task_name:
                    tasks_found.append(critical)
                    print(f"✅ Found {critical} task: {task_info.get('task', '')[:50]}...")
        
        missing = set(critical_tasks) - set(tasks_found)
        if missing:
            print(f"⚠️  Missing critical tasks: {missing}")
        
        # Final Summary
        print(f"\n🎯 FINAL RESULTS")
        print("=" * 60)
        
        success_criteria = [
            ("Action Items Extracted", len(result.action_items) >= 5),
            ("Meeting Page Created", bool(sync_result.meeting_id)),
            ("Tasks Created", len(sync_result.tasks_created) >= 5),
            ("No Failed Tasks", len(sync_result.tasks_failed) == 0),
            ("Filipino Content Handled", has_filipino_content if sync_result.meeting_id else False),
            ("Critical Topics Covered", len(tasks_found) >= 3)
        ]
        
        for criteria, passed in success_criteria:
            print(f"{criteria}: {'✅ PASS' if passed else '❌ FAIL'}")
        
        all_pass = all(passed for _, passed in success_criteria)
        
        if all_pass:
            print(f"\n🎉 ALL TESTS PASSED!")
            print("The system successfully handled the Filipino/Taglish business meeting!")
            if sync_result.meeting_url:
                print(f"\n📋 View meeting in Notion: {sync_result.meeting_url}")
        else:
            print(f"\n⚠️  SOME TESTS FAILED")
            print("Review the results above to identify issues.")
        
        return all_pass
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_filipino_meeting())
    exit(0 if success else 1)