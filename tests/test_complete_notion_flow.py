#!/usr/bin/env python3
"""
Test the complete flow from analysis to Notion content creation
"""
import asyncio
import json
from meeting_analyzer import MeetingAnalyzer

def format_meeting_content(analysis_result):
    """Replicate the _format_meeting_content method from NotionSync"""
    blocks = []
    
    print("=== BUILDING NOTION BLOCKS ===")
    
    # Add summary section
    summary = analysis_result.get("summary", "")
    print(f"Summary: {len(summary)} chars -> {'CONTENT' if summary else 'EMPTY'}")
    
    blocks.append({
        "object": "block",
        "type": "heading_1",
        "heading_1": {
            "rich_text": [{"text": {"content": "Meeting Summary"}}]
        }
    })
    
    if summary:
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": summary}}]
            }
        })
        print(f"  ✅ Added summary paragraph block")
    else:
        print(f"  ❌ No summary to add")
    
    # Add key decisions
    decisions = analysis_result.get("key_decisions", [])
    print(f"Key Decisions: {len(decisions)} items -> {'CONTENT' if decisions else 'EMPTY'}")
    
    blocks.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"text": {"content": "Key Decisions"}}]
        }
    })
    
    for i, decision in enumerate(decisions):
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": decision}}]
            }
        })
        print(f"  ✅ Added decision {i+1}: {decision[:50]}...")
    
    if not decisions:
        print(f"  ❌ No decisions to add")
    
    # Add discussion points
    discussions = analysis_result.get("discussion_points", [])
    print(f"Discussion Points: {len(discussions)} items -> {'CONTENT' if discussions else 'EMPTY'}")
    
    blocks.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"text": {"content": "Discussion Points"}}]
        }
    })
    
    for i, point in enumerate(discussions):
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": point}}]
            }
        })
        print(f"  ✅ Added discussion {i+1}: {point[:50]}...")
    
    if not discussions:
        print(f"  ❌ No discussions to add")
    
    # Add action items
    action_items = analysis_result.get("action_items", [])
    print(f"Action Items: {len(action_items)} items -> {'CONTENT' if action_items else 'EMPTY'}")
    
    blocks.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"text": {"content": "Action Items"}}]
        }
    })
    
    for i, item in enumerate(action_items):
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
        print(f"  ✅ Added action {i+1}: {item_text[:50]}...")
    
    if not action_items:
        print(f"  ❌ No actions to add")
    
    # Add cleaned transcript in a toggle
    cleaned_transcript = analysis_result.get("cleaned_transcript", "")
    print(f"Cleaned Transcript: {len(cleaned_transcript)} chars -> {'CONTENT' if cleaned_transcript else 'EMPTY'}")
    
    transcript_content = cleaned_transcript[:2000] if cleaned_transcript else ""
    
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
                                "content": transcript_content
                            }
                        }]
                    }
                }
            ]
        }
    })
    
    if transcript_content:
        print(f"  ✅ Added transcript toggle with {len(transcript_content)} chars")
    else:
        print(f"  ❌ Added transcript toggle with EMPTY content")
    
    print(f"\nTotal blocks created: {len(blocks)}")
    return blocks

async def test_complete_flow():
    """Test the complete flow from analysis ID to Notion content"""
    
    analyzer = MeetingAnalyzer()
    analysis_id = "analysis_test_fallback_001_20250910_163407"
    
    print(f"=== COMPLETE NOTION FLOW TEST ===")
    print(f"Analysis ID: {analysis_id}")
    
    # Step 1: Get analysis data (this is what happens in /api/sync-to-notion)
    print(f"\n1. Loading analysis data...")
    analysis_data = await analyzer.get_analysis(analysis_id)
    
    if not analysis_data:
        print("ERROR: Could not load analysis data")
        return
    
    print(f"✅ Analysis data loaded: {list(analysis_data.keys())}")
    print(f"✅ Has cleaned_transcript: {'cleaned_transcript' in analysis_data}")
    
    # Step 2: Create Notion content blocks
    print(f"\n2. Creating Notion content blocks...")
    content_blocks = format_meeting_content(analysis_data)
    
    # Step 3: Analyze the blocks for empty content
    print(f"\n3. Analyzing content blocks...")
    
    content_blocks_with_text = []
    empty_blocks = []
    
    for i, block in enumerate(content_blocks):
        block_type = block.get('type', 'UNKNOWN')
        has_content = False
        
        if block_type == 'paragraph':
            text_content = block.get('paragraph', {}).get('rich_text', [{}])[0].get('text', {}).get('content', '')
            has_content = bool(text_content.strip())
        elif block_type == 'bulleted_list_item':
            text_content = block.get('bulleted_list_item', {}).get('rich_text', [{}])[0].get('text', {}).get('content', '')
            has_content = bool(text_content.strip())
        elif block_type == 'toggle':
            children = block.get('toggle', {}).get('children', [])
            if children:
                child_content = children[0].get('paragraph', {}).get('rich_text', [{}])[0].get('text', {}).get('content', '')
                has_content = bool(child_content.strip())
        elif block_type in ['heading_1', 'heading_2']:
            has_content = True  # Headers always have content
        
        if has_content:
            content_blocks_with_text.append(i)
        else:
            empty_blocks.append(i)
    
    print(f"\nContent Analysis:")
    print(f"  Total blocks: {len(content_blocks)}")
    print(f"  Blocks with content: {len(content_blocks_with_text)}")
    print(f"  Empty blocks: {len(empty_blocks)}")
    
    if empty_blocks:
        print(f"  Empty block indices: {empty_blocks}")
        for idx in empty_blocks:
            block = content_blocks[idx]
            print(f"    Block {idx}: {block.get('type', 'UNKNOWN')} - EMPTY")
    
    # Step 4: Summary
    print(f"\n=== SUMMARY ===")
    if len(content_blocks_with_text) > 4:  # Headers + some content
        print("✅ SUCCESS: Notion blocks contain sufficient content")
    else:
        print("❌ PROBLEM: Notion blocks are mostly empty")
    
    # Check specific issues
    summary_has_content = analysis_data.get("summary", "") != ""
    decisions_have_content = len(analysis_data.get("key_decisions", [])) > 0
    discussions_have_content = len(analysis_data.get("discussion_points", [])) > 0
    actions_have_content = len(analysis_data.get("action_items", [])) > 0
    transcript_has_content = analysis_data.get("cleaned_transcript", "") != ""
    
    print(f"\nContent Check:")
    print(f"  Summary: {'✅' if summary_has_content else '❌'}")
    print(f"  Key Decisions: {'✅' if decisions_have_content else '❌'}")
    print(f"  Discussion Points: {'✅' if discussions_have_content else '❌'}")
    print(f"  Action Items: {'✅' if actions_have_content else '❌'}")
    print(f"  Cleaned Transcript: {'✅' if transcript_has_content else '❌'}")
    
    if all([summary_has_content, decisions_have_content, discussions_have_content, actions_have_content, transcript_has_content]):
        print(f"\n🎉 ALL CONTENT IS PRESENT - The Notion issue must be elsewhere!")
    else:
        print(f"\n⚠️ Some content is missing from the analysis data")

if __name__ == "__main__":
    asyncio.run(test_complete_flow())