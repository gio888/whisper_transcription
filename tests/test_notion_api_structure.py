#!/usr/bin/env python3
"""
Test the Notion API call structure to identify potential issues
"""
import asyncio
import json
from datetime import date
from meeting_analyzer import MeetingAnalyzer
from notion_config import NotionConfig

def generate_meeting_title(summary: str) -> str:
    """Generate a concise meeting title from the summary"""
    # Take first sentence or line
    first_line = summary.split('\n')[0] if summary else "Meeting Notes"
    first_sentence = first_line.split('.')[0]
    
    # Truncate to max length
    if len(first_sentence) > NotionConfig.MEETING_TITLE_MAX_LENGTH:
        first_sentence = first_sentence[:NotionConfig.MEETING_TITLE_MAX_LENGTH-3] + "..."
    
    return first_sentence

def format_meeting_content(analysis_result):
    """Format the analysis result as Notion blocks (exact copy from NotionSync)"""
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

async def test_notion_api_structure():
    """Test the exact structure that would be sent to Notion API"""
    
    analyzer = MeetingAnalyzer()
    analysis_id = "analysis_test_fallback_001_20250910_163407"
    meeting_date = date.today()
    
    print(f"=== NOTION API STRUCTURE TEST ===")
    print(f"Analysis ID: {analysis_id}")
    
    # Load analysis data
    analysis_result = await analyzer.get_analysis(analysis_id)
    
    if not analysis_result:
        print("ERROR: Could not load analysis data")
        return
    
    # Generate meeting title
    summary = analysis_result.get("summary", "")
    title_phrase = generate_meeting_title(summary)
    page_title = f"{meeting_date.isoformat()} {title_phrase}"
    
    print(f"Meeting title: {page_title}")
    print(f"Title length: {len(page_title)} chars")
    
    # Format content for Notion
    content_blocks = format_meeting_content(analysis_result)
    
    print(f"Content blocks: {len(content_blocks)} blocks")
    
    # Create the exact structure that would be sent to Notion API
    notion_api_request = {
        "parent": {"database_id": NotionConfig.INTERACTIONS_REGISTRY_DB_ID},
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": page_title
                        }
                    }
                ]
            }
        },
        "children": content_blocks
    }
    
    print(f"\n=== NOTION API REQUEST STRUCTURE ===")
    print(f"Database ID: {NotionConfig.INTERACTIONS_REGISTRY_DB_ID}")
    print(f"Page Title: {page_title}")
    print(f"Children Blocks: {len(content_blocks)}")
    
    # Validate request structure
    print(f"\n=== VALIDATION ===")
    
    # Check database ID format
    db_id = NotionConfig.INTERACTIONS_REGISTRY_DB_ID
    if len(db_id) == 32:
        print("✅ Database ID format: Valid (32 chars)")
    else:
        print(f"❌ Database ID format: Invalid ({len(db_id)} chars, expected 32)")
    
    # Check title length
    if len(page_title) <= 100:  # Notion title limit
        print(f"✅ Title length: Valid ({len(page_title)} chars)")
    else:
        print(f"❌ Title length: Too long ({len(page_title)} chars, max 100)")
    
    # Check blocks structure
    valid_blocks = 0
    invalid_blocks = 0
    
    for i, block in enumerate(content_blocks):
        try:
            # Check required fields
            if "object" not in block or "type" not in block:
                print(f"❌ Block {i}: Missing required fields")
                invalid_blocks += 1
                continue
            
            block_type = block["type"]
            if block_type not in block:
                print(f"❌ Block {i}: Missing type-specific content")
                invalid_blocks += 1
                continue
            
            # Check specific block types
            if block_type in ["heading_1", "heading_2"]:
                rich_text = block[block_type].get("rich_text", [])
                if not rich_text or not rich_text[0].get("text", {}).get("content"):
                    print(f"❌ Block {i}: Empty heading")
                    invalid_blocks += 1
                    continue
            
            elif block_type == "paragraph":
                rich_text = block[block_type].get("rich_text", [])
                if not rich_text or not rich_text[0].get("text", {}).get("content"):
                    print(f"❌ Block {i}: Empty paragraph")
                    invalid_blocks += 1
                    continue
            
            elif block_type == "bulleted_list_item":
                rich_text = block[block_type].get("rich_text", [])
                if not rich_text or not rich_text[0].get("text", {}).get("content"):
                    print(f"❌ Block {i}: Empty list item")
                    invalid_blocks += 1
                    continue
            
            elif block_type == "toggle":
                rich_text = block[block_type].get("rich_text", [])
                children = block[block_type].get("children", [])
                if not rich_text or not rich_text[0].get("text", {}).get("content"):
                    print(f"❌ Block {i}: Empty toggle title")
                    invalid_blocks += 1
                    continue
                if not children:
                    print(f"❌ Block {i}: Toggle without children")
                    invalid_blocks += 1
                    continue
            
            valid_blocks += 1
            
        except Exception as e:
            print(f"❌ Block {i}: Validation error - {e}")
            invalid_blocks += 1
    
    print(f"\n=== BLOCK VALIDATION RESULTS ===")
    print(f"Valid blocks: {valid_blocks}")
    print(f"Invalid blocks: {invalid_blocks}")
    print(f"Total blocks: {len(content_blocks)}")
    
    if invalid_blocks == 0:
        print("✅ ALL BLOCKS VALID - Structure should work with Notion API")
    else:
        print("❌ SOME BLOCKS INVALID - This could cause content to be rejected")
    
    # Save the API request for inspection
    with open('notion_api_request_debug.json', 'w', encoding='utf-8') as f:
        json.dump(notion_api_request, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Saved API request structure to: notion_api_request_debug.json")
    
    # Check for common Notion API issues
    print(f"\n=== COMMON NOTION ISSUES CHECK ===")
    
    # Check for text length limits
    total_text_length = 0
    long_blocks = []
    
    for i, block in enumerate(content_blocks):
        block_text = ""
        block_type = block.get("type", "")
        
        if block_type in ["heading_1", "heading_2", "paragraph", "bulleted_list_item"]:
            rich_text = block.get(block_type, {}).get("rich_text", [])
            if rich_text:
                block_text = rich_text[0].get("text", {}).get("content", "")
        elif block_type == "toggle":
            rich_text = block.get(block_type, {}).get("rich_text", [])
            if rich_text:
                block_text = rich_text[0].get("text", {}).get("content", "")
            children = block.get(block_type, {}).get("children", [])
            if children:
                child_text = children[0].get("paragraph", {}).get("rich_text", [])
                if child_text:
                    block_text += child_text[0].get("text", {}).get("content", "")
        
        total_text_length += len(block_text)
        
        if len(block_text) > 1000:  # Flag potentially long blocks
            long_blocks.append((i, len(block_text)))
    
    print(f"Total text length: {total_text_length} chars")
    if long_blocks:
        print(f"Long blocks (>1000 chars): {long_blocks}")
    
    if total_text_length > 100000:  # Rough Notion limit
        print("⚠️  WARNING: Total content might exceed Notion limits")
    else:
        print("✅ Content length within reasonable limits")

if __name__ == "__main__":
    asyncio.run(test_notion_api_structure())