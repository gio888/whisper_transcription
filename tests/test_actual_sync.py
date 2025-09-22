#!/usr/bin/env python3
"""
Test the actual sync_analysis_to_notion method
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables BEFORE importing config
load_dotenv()

from meeting_analyzer import MeetingAnalyzer
from notion_sync import get_notion_sync

async def test_actual_sync():
    """Test the actual sync method that's failing"""
    
    print("=== ACTUAL NOTION SYNC TEST ===")
    
    # Load the analysis data
    analyzer = MeetingAnalyzer()
    analysis_id = "analysis_test_fallback_001_20250910_163407"
    analysis_data = await analyzer.get_analysis(analysis_id)
    
    if not analysis_data:
        print("❌ ERROR: Could not load analysis data")
        return
    
    print(f"✅ Analysis data loaded: {analysis_id}")
    print(f"Fields: {list(analysis_data.keys())}")
    
    # Test the actual sync
    print(f"\n=== RUNNING ACTUAL SYNC ===")
    
    try:
        notion = get_notion_sync()
        sync_result = await notion.sync_analysis_to_notion(analysis_data)
        
        print(f"Sync Success: {sync_result.success}")
        print(f"Meeting ID: {sync_result.meeting_id}")
        print(f"Meeting URL: {sync_result.meeting_url}")
        print(f"Tasks Created: {len(sync_result.tasks_created)}")
        print(f"Tasks Failed: {len(sync_result.tasks_failed)}")
        print(f"Errors: {sync_result.errors}")
        
        if sync_result.meeting_id:
            print(f"\n=== VERIFYING CREATED PAGE ===")
            
            # Use the notion client to check what was actually created
            from notion_client import AsyncClient
            client = AsyncClient(auth=os.getenv("NOTION_API_KEY"))
            
            try:
                # Get the page
                page = await client.pages.retrieve(page_id=sync_result.meeting_id)
                print(f"✅ Page exists: {page['id']}")
                
                # Get the page content
                children = await client.blocks.children.list(block_id=sync_result.meeting_id)
                actual_blocks = children['results']
                
                print(f"📄 Page has {len(actual_blocks)} blocks:")
                
                for i, block in enumerate(actual_blocks):
                    block_type = block.get('type', 'unknown')
                    print(f"  Block {i+1}: {block_type}")
                    
                    # Show content for text blocks
                    if block_type in ['heading_1', 'heading_2', 'paragraph']:
                        rich_text = block.get(block_type, {}).get('rich_text', [])
                        if rich_text:
                            text_content = rich_text[0].get('text', {}).get('content', 'NO CONTENT')
                            print(f"    Content: {text_content[:50]}{'...' if len(text_content) > 50 else ''}")
                    
                    elif block_type == 'bulleted_list_item':
                        rich_text = block.get('bulleted_list_item', {}).get('rich_text', [])
                        if rich_text:
                            text_content = rich_text[0].get('text', {}).get('content', 'NO CONTENT')
                            print(f"    Content: {text_content[:50]}{'...' if len(text_content) > 50 else ''}")
                    
                    elif block_type == 'toggle':
                        rich_text = block.get('toggle', {}).get('rich_text', [])
                        if rich_text:
                            text_content = rich_text[0].get('text', {}).get('content', 'NO CONTENT')
                            print(f"    Title: {text_content}")
                        
                        # Check if toggle has children
                        if block.get('has_children', False):
                            toggle_children = await client.blocks.children.list(block_id=block['id'])
                            print(f"    Children: {len(toggle_children['results'])} blocks")
                            
                            for child in toggle_children['results']:
                                child_type = child.get('type', 'unknown')
                                if child_type == 'paragraph':
                                    child_rich_text = child.get('paragraph', {}).get('rich_text', [])
                                    if child_rich_text:
                                        child_content = child_rich_text[0].get('text', {}).get('content', 'NO CONTENT')
                                        print(f"      Child content: {child_content[:100]}{'...' if len(child_content) > 100 else ''}")
                        else:
                            print(f"    Children: 0 (no has_children flag)")
                
                if len(actual_blocks) == 0:
                    print("❌ CONFIRMED: Page was created but has NO CONTENT!")
                else:
                    print(f"✅ Page has content: {len(actual_blocks)} blocks")
                    
            except Exception as e:
                print(f"❌ Error checking page: {e}")
        
        # Also check tasks
        if sync_result.tasks_created:
            print(f"\n=== TASK CREATION RESULTS ===")
            for task in sync_result.tasks_created:
                print(f"✅ Task: {task.get('task', 'NO TASK NAME')}")
                if task.get('task_id'):
                    print(f"  ID: {task['task_id']}")
        
        if sync_result.tasks_failed:
            print(f"\n=== FAILED TASKS ===")
            for task in sync_result.tasks_failed:
                print(f"❌ Task: {task.get('task', 'NO TASK NAME')}")
                print(f"  Error: {task.get('error', 'NO ERROR INFO')}")
    
    except Exception as e:
        print(f"❌ Sync failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_actual_sync())