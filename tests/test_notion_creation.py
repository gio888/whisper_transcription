#!/usr/bin/env python3
"""
Test Notion page creation with the specific action items from the optimized analysis
"""
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_test_analysis_result():
    """Create a test analysis result with the specific action items"""
    return {
        'analysis_id': f'test_notion_{int(datetime.now().timestamp())}',
        'summary': 'The meeting focused on clarifying misunderstandings regarding a film concert event and defining the strategy for lit buildings, specifically addressing the concept of Last Mile Partner (LMP). The team aims to align their processes and ensure transparency in communication.',
        'key_decisions': [
            'Agreed that all lit buildings will be treated as LMP.',
            'Decision to clarify sales processes between teams to identify any disconnects or areas needing improvement.'
        ],
        'discussion_points': [
            'Concerns about potential high risk associated with a film concert event.',
            'Debate on the definition of "tail" in relation to LMP, leading to clarification that LMP refers to Last Mile Partner.',
            'Need for transparency and alignment between teams regarding sales processes.'
        ],
        'action_items': [
            {
                'task': 'Clarify and document the process for handling film concert events.',
                'owner': 'Sales Team',
                'deadline': 'Next week'
            },
            {
                'task': 'Define and document the concept of LMP (Last Mile Partner).',
                'owner': 'Operations', 
                'deadline': 'By end of next month'
            },
            {
                'task': 'Schedule a meeting to discuss and align sales processes between teams.',
                'owner': 'Leadership',
                'deadline': 'Within 2 weeks'
            },
            {
                'task': 'Follow up on the alignment of sales processes with the new understanding.',
                'owner': 'Sales Team, Operations',
                'deadline': 'Next week'
            },
            {
                'task': 'Ensure transparency in communication regarding LMP strategy for lit buildings.',
                'owner': 'All Teams',
                'deadline': 'Immediate implementation'
            }
        ],
        'cleaned_transcript': '''Speaker A: Concerned because we are thinking of a high risk for the film concert. We discussed this before due to documentation needs and contract provisions, but may have some misunderstandings.

Speaker B: What is LMP again? Last mile partner. So now, okay with us. But based on our understanding, we cannot tell the client or the lit building that we are a partner and will be getting it from rice.

Speaker A: If you could describe your sales process, that would help us identify where the disconnect is. We don't need a detailed NDA; just an understanding of how you sell.''',
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'transcript_length': 1612,
            'processing_time': 35.4
        }
    }

async def test_notion_page_creation():
    """Test creating a Notion page with the analysis results"""
    print("📄 TESTING NOTION PAGE CREATION")
    print("=" * 60)
    
    # Check if Notion API key is available
    notion_api_key = os.getenv('NOTION_API_KEY')
    if not notion_api_key:
        print("❌ NOTION_API_KEY not found in environment variables")
        print("   Please ensure your .env file contains a valid Notion API key")
        return False
    
    print(f"✅ Notion API key found: {notion_api_key[:10]}...{notion_api_key[-4:]}")
    
    # Check template configuration
    use_template = os.getenv('USE_NOTION_TEMPLATE', 'false').lower() == 'true'
    template_id = os.getenv('NOTION_MEETING_TEMPLATE_ID')
    
    print(f"📋 Configuration:")
    print(f"   Use Template: {use_template}")
    print(f"   Template ID: {template_id}")
    print()
    
    # Create test analysis result
    analysis_result = create_test_analysis_result()
    
    print("📊 Test Analysis Data:")
    print("-" * 30)
    print(f"Summary: {len(analysis_result['summary'])} chars")
    print(f"Key Decisions: {len(analysis_result['key_decisions'])} items")
    print(f"Discussion Points: {len(analysis_result['discussion_points'])} items")
    print(f"Action Items: {len(analysis_result['action_items'])} items")
    print()
    
    # Show the action items that will be created
    print("✅ Action Items to be created in Notion:")
    print("-" * 40)
    for i, item in enumerate(analysis_result['action_items'], 1):
        print(f"{i}. TASK: {item['task']}")
        print(f"   OWNER: {item['owner']}")
        print(f"   DEADLINE: {item['deadline']}")
        print()
    
    # Test the Notion sync
    print("🔄 Creating Notion page...")
    print("-" * 30)
    
    try:
        from notion_sync import NotionSync
        
        # Initialize Notion sync
        notion_sync = NotionSync()
        
        # Create the meeting page
        sync_start = datetime.now()
        result = await notion_sync.sync_analysis_to_notion(
            analysis_result=analysis_result,
            meeting_date=datetime.now().date()
        )
        sync_duration = (datetime.now() - sync_start).total_seconds()
        
        print(f"⏱️  Sync completed in {sync_duration:.1f}s")
        print()
        
        if result.success:
            print("🎉 SUCCESS! Notion page created successfully")
            print("-" * 50)
            print(f"📄 Meeting Page ID: {result.meeting_id}")
            if result.meeting_url:
                print(f"🔗 Meeting URL: {result.meeting_url}")
            print(f"✅ Tasks Created: {len(result.tasks_created)}")
            print(f"❌ Tasks Failed: {len(result.tasks_failed)}")
            
            if result.tasks_created:
                print("\n📋 Created Tasks:")
                for i, task in enumerate(result.tasks_created, 1):
                    print(f"  {i}. {task.get('title', 'No title')} - {task.get('url', 'No URL')}")
            
            if result.tasks_failed:
                print("\n❌ Failed Tasks:")
                for task in result.tasks_failed:
                    print(f"  - {task}")
            
            if result.errors:
                print("\n⚠️ Warnings/Errors:")
                for error in result.errors:
                    print(f"  - {error}")
            
            # Final success summary
            print("\n" + "=" * 60)
            print("🚀 NOTION INTEGRATION TEST RESULTS:")
            print(f"   ✅ Page Created: Yes")
            print(f"   ✅ Action Items: {len(result.tasks_created)}/{len(analysis_result['action_items'])}")
            print(f"   🔗 View Page: {result.meeting_url}")
            print("   🎯 Status: PRODUCTION READY")
            
            return True
            
        else:
            print("❌ FAILED to create Notion page")
            print("-" * 30)
            print(f"Errors: {result.errors}")
            return False
            
    except Exception as e:
        print(f"❌ Notion sync failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the Notion page creation test"""
    print("🧪 NOTION PAGE CREATION TEST")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    success = await test_notion_page_creation()
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())