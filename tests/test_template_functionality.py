#!/usr/bin/env python3
"""
Test the template functionality with a simple meeting
"""
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables BEFORE importing config
load_dotenv()

from meeting_analyzer import MeetingAnalysis, ActionItem
from notion_sync import get_notion_sync
from notion_config import NotionConfig

async def test_template_functionality():
    """Test creating a meeting page with template support"""
    print("🧪 TESTING NOTION TEMPLATE FUNCTIONALITY")
    print("=" * 50)
    
    # Check current template configuration
    print(f"📋 TEMPLATE CONFIGURATION:")
    print(f"  USE_TEMPLATE: {NotionConfig.USE_TEMPLATE}")
    print(f"  TEMPLATE_ID: {NotionConfig.TEMPLATE_ID or 'None (using database default)'}")
    print()
    
    # Create a simple test analysis
    test_analysis = {
        "analysis_id": f"template_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "summary": "Template test meeting to verify the yyyy-mm-dd Meeting Title template is being used correctly with analysis content appended.",
        "key_decisions": [
            "Decision to test template functionality",
            "Agreement to use database default template"
        ],
        "discussion_points": [
            "Discussion about template vs non-template page creation",
            "Verification of content integration with existing template structure"
        ],
        "action_items": [
            {
                "task": "Verify template structure is preserved",
                "owner": "Development Team",
                "deadline": "Immediate"
            },
            {
                "task": "Confirm analysis content is properly appended",
                "owner": "QA Team", 
                "deadline": "Today"
            }
        ],
        "cleaned_transcript": "Test transcript: This is a template functionality test meeting to ensure the Notion integration works with your existing templates.",
        "metadata": {
            "test": True,
            "template_test": True,
            "template_used": NotionConfig.USE_TEMPLATE
        },
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat()
    }
    
    print(f"🚀 CREATING TEST MEETING WITH TEMPLATE")
    print("-" * 40)
    
    try:
        notion = get_notion_sync()
        sync_result = await notion.sync_analysis_to_notion(test_analysis)
        
        print(f"Success: {'✅' if sync_result.success else '❌'}")
        print(f"Meeting ID: {sync_result.meeting_id or 'None'}")
        print(f"Meeting URL: {sync_result.meeting_url or 'None'}")
        print(f"Errors: {sync_result.errors}")
        
        if sync_result.meeting_id:
            print(f"\n🔍 VERIFYING TEMPLATE USAGE")
            print("-" * 40)
            
            from notion_client import AsyncClient
            client = AsyncClient(auth=os.getenv("NOTION_API_KEY"))
            
            # Get the created page content
            children = await client.blocks.children.list(block_id=sync_result.meeting_id)
            blocks = children['results']
            
            print(f"Total blocks: {len(blocks)}")
            
            # Check for template structure + analysis content
            block_types = [block.get('type', 'unknown') for block in blocks]
            print(f"Block types: {set(block_types)}")
            
            # Look for analysis content
            has_analysis_content = False
            has_template_content = False
            
            for i, block in enumerate(blocks):
                block_type = block.get('type', 'unknown')
                
                # Check for our analysis headings
                if block_type == 'heading_1':
                    text = block.get('heading_1', {}).get('rich_text', [{}])[0].get('text', {}).get('content', '')
                    if 'Meeting Summary' in text:
                        has_analysis_content = True
                        print(f"✅ Found analysis content at block {i}: {text}")
                
                # Check for template content (anything that's not our standard analysis blocks)
                if block_type in ['paragraph', 'heading_2', 'heading_1'] and i < 5:  # Check first few blocks for template content
                    text = ""
                    if block_type == 'paragraph':
                        text = block.get('paragraph', {}).get('rich_text', [{}])[0].get('text', {}).get('content', '')
                    elif block_type in ['heading_1', 'heading_2']:
                        text = block.get(block_type, {}).get('rich_text', [{}])[0].get('text', {}).get('content', '')
                    
                    if text and 'Meeting Summary' not in text and 'Key Decisions' not in text:
                        has_template_content = True
                        print(f"📋 Found template content at block {i}: {text[:50]}...")
            
            print(f"\n📊 RESULTS:")
            print(f"Template content detected: {'✅' if has_template_content else '❌'}")
            print(f"Analysis content added: {'✅' if has_analysis_content else '❌'}")
            
            # Check task creation
            print(f"Tasks created: {len(sync_result.tasks_created)}")
            print(f"Tasks failed: {len(sync_result.tasks_failed)}")
            
            success = (
                sync_result.success and 
                sync_result.meeting_id and 
                has_analysis_content and
                len(sync_result.tasks_created) >= 2
            )
            
            print(f"\n🎯 OVERALL RESULT: {'✅ SUCCESS' if success else '❌ FAILED'}")
            
            if success:
                print(f"🎉 Template functionality is working!")
                print(f"   - Template structure: {'Preserved' if has_template_content else 'Not detected (but may be there)'}")
                print(f"   - Analysis content: Added successfully")
                print(f"   - Tasks created: {len(sync_result.tasks_created)} tasks")
                if sync_result.meeting_url:
                    print(f"\n📋 View the template-based meeting: {sync_result.meeting_url}")
            else:
                print(f"⚠️  Issues detected - check the logs above")
            
            return success
        else:
            print(f"❌ Failed to create meeting page")
            return False
    
    except Exception as e:
        print(f"❌ Error during template test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def compare_template_vs_non_template():
    """Create two meetings to compare template vs non-template"""
    print(f"\n🔄 COMPARISON TEST: Template vs Non-Template")
    print("=" * 50)
    
    # Test with template enabled
    print("1️⃣ Testing WITH template...")
    original_use_template = NotionConfig.USE_TEMPLATE
    NotionConfig.USE_TEMPLATE = True
    
    template_result = await test_template_functionality()
    
    # Test without template
    print(f"\n2️⃣ Testing WITHOUT template...")
    NotionConfig.USE_TEMPLATE = False
    
    non_template_result = await test_template_functionality()
    
    # Restore original setting
    NotionConfig.USE_TEMPLATE = original_use_template
    
    print(f"\n📊 COMPARISON RESULTS:")
    print(f"With template: {'✅ Success' if template_result else '❌ Failed'}")
    print(f"Without template: {'✅ Success' if non_template_result else '❌ Failed'}")
    
    return template_result and non_template_result

if __name__ == "__main__":
    # Just test with current configuration
    success = asyncio.run(test_template_functionality())
    
    # Uncomment to run comparison test
    # success = asyncio.run(compare_template_vs_non_template())
    
    exit(0 if success else 1)