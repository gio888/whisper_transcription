#!/usr/bin/env python3
"""
Debug script to test Notion content formatting
"""
import json
import sys
from notion_config import NotionConfig

def format_meeting_content(analysis_result):
    """Replicate the _format_meeting_content method from NotionSync"""
    blocks = []
    
    # Add summary section
    blocks.append({
        "object": "block",
        "type": "heading_1",
        "heading_1": {
            "rich_text": [{"text": {"content": "Meeting Summary"}}]
        }
    })
    
    summary = analysis_result.get("summary", "")
    if summary:
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": summary}}]
            }
        })
    
    # Add key decisions
    blocks.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"text": {"content": "Key Decisions"}}]
        }
    })
    
    decisions = analysis_result.get("key_decisions", [])
    for decision in decisions:
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": decision}}]
            }
        })
    
    # Add discussion points
    blocks.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"text": {"content": "Discussion Points"}}]
        }
    })
    
    discussions = analysis_result.get("discussion_points", [])
    for point in discussions:
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": point}}]
            }
        })
    
    # Add action items
    blocks.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"text": {"content": "Action Items"}}]
        }
    })
    
    action_items = analysis_result.get("action_items", [])
    for item in action_items:
        task_text = item.get("task", "")
        owner = item.get("owner", "")
        deadline = item.get("deadline", "")
        
        item_text = f"• {task_text}"
        if owner:
            item_text += f" (Owner: {owner})"
        if deadline:
            item_text += f" [Due: {deadline}]"
        
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": item_text}}]
            }
        })
    
    # Add cleaned transcript in a toggle
    blocks.append({
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": [{"text": {"content": "Full Transcript"}}],
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "text": {
                                "content": analysis_result.get("cleaned_transcript", "")[:2000]  # Notion has limits
                            }
                        }]
                    }
                }
            ]
        }
    })
    
    return blocks

def test_content_formatting():
    """Test the Notion content formatting with actual analysis results"""
    
    # Load the actual analysis results
    with open('analysis_results/analysis_test_fallback_001_20250910_163407.json', 'r') as f:
        analysis_result = json.load(f)
    
    print("=== ANALYSIS RESULTS ===")
    print(f"Summary: {analysis_result.get('summary', 'MISSING')}")
    print(f"Key Decisions: {len(analysis_result.get('key_decisions', []))} items")
    print(f"Discussion Points: {len(analysis_result.get('discussion_points', []))} items") 
    print(f"Action Items: {len(analysis_result.get('action_items', []))} items")
    
    # Check for cleaned_transcript
    cleaned_transcript = analysis_result.get('cleaned_transcript', '')
    print(f"Cleaned Transcript: {'PRESENT' if cleaned_transcript else 'MISSING'}")
    if cleaned_transcript:
        print(f"  Length: {len(cleaned_transcript)} chars")
        print(f"  Preview: {cleaned_transcript[:100]}...")
    else:
        print("  This is likely the cause of empty Notion pages!")
    
    # Check all fields in the analysis result
    print(f"\nAll fields in analysis_result: {list(analysis_result.keys())}")
    print()
    
    # Try to load the cleaned transcript from the separate file
    try:
        with open('analysis_results/analysis_test_fallback_001_20250910_163407_cleaned.txt', 'r') as f:
            cleaned_transcript_from_file = f.read()
        print("=== CLEANED TRANSCRIPT FROM FILE ===")
        print(f"Length: {len(cleaned_transcript_from_file)} chars")
        print(f"Preview: {cleaned_transcript_from_file[:200]}...")
        
        # Update the analysis result with the transcript from file
        analysis_result['cleaned_transcript'] = cleaned_transcript_from_file
        print("Added cleaned_transcript to analysis_result for testing")
        print()
    except FileNotFoundError:
        print("Cleaned transcript file not found")
        print()
    
    # Test the content formatting
    content_blocks = format_meeting_content(analysis_result)
    
    print("=== GENERATED NOTION BLOCKS ===")
    print(f"Total blocks: {len(content_blocks)}")
    
    for i, block in enumerate(content_blocks):
        block_type = block.get('type', 'UNKNOWN')
        print(f"Block {i}: {block_type}")
        
        if block_type == 'heading_1':
            text_content = block.get('heading_1', {}).get('rich_text', [{}])[0].get('text', {}).get('content', 'NO CONTENT')
            print(f"  Content: {text_content}")
            
        elif block_type == 'heading_2':
            text_content = block.get('heading_2', {}).get('rich_text', [{}])[0].get('text', {}).get('content', 'NO CONTENT')
            print(f"  Content: {text_content}")
            
        elif block_type == 'paragraph':
            text_content = block.get('paragraph', {}).get('rich_text', [{}])[0].get('text', {}).get('content', 'NO CONTENT')
            print(f"  Content: {text_content[:100]}{'...' if len(text_content) > 100 else ''}")
            
        elif block_type == 'bulleted_list_item':
            text_content = block.get('bulleted_list_item', {}).get('rich_text', [{}])[0].get('text', {}).get('content', 'NO CONTENT')
            print(f"  Content: {text_content[:100]}{'...' if len(text_content) > 100 else ''}")
            
        elif block_type == 'toggle':
            text_content = block.get('toggle', {}).get('rich_text', [{}])[0].get('text', {}).get('content', 'NO CONTENT')
            children = block.get('toggle', {}).get('children', [])
            print(f"  Content: {text_content}")
            print(f"  Children: {len(children)} blocks")
            
        print()

def test_priority_extraction():
    """Test priority extraction from action items"""
    
    with open('analysis_results/analysis_test_fallback_001_20250910_163407.json', 'r') as f:
        analysis_result = json.load(f)
    
    print("=== PRIORITY TESTING ===")
    action_items = analysis_result.get('action_items', [])
    
    for i, item in enumerate(action_items):
        task_text = item.get('task', '')
        priority = NotionConfig.get_priority_from_text(task_text)
        print(f"Task {i+1}: {task_text}")
        print(f"  Priority: {priority}")
        print(f"  Owner: {item.get('owner', 'NONE')}")
        print(f"  Deadline: {item.get('deadline', 'NONE')}")
        print()

if __name__ == "__main__":
    try:
        print("Testing Notion content formatting...\n")
        test_content_formatting()
        print("\n" + "="*60 + "\n")
        test_priority_extraction()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)