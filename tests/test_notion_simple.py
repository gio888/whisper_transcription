#!/usr/bin/env python3
"""
Simple Notion API test to identify the actual problem
"""
import asyncio
import os
from dotenv import load_dotenv
from notion_client import AsyncClient
from notion_config import NotionConfig

# Load environment variables
load_dotenv()

async def test_notion_simple():
    """Test basic Notion API operations"""
    
    print("=== SIMPLE NOTION API TEST ===")
    
    # Check environment
    api_key = os.getenv("NOTION_API_KEY")
    if not api_key:
        print("❌ ERROR: NOTION_API_KEY not found in environment")
        print("Add NOTION_API_KEY=your_key to your .env file")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        # Initialize client
        client = AsyncClient(auth=api_key)
        
        # Test 1: Check database access
        print(f"\n1. Testing database access...")
        db_id = NotionConfig.INTERACTIONS_REGISTRY_DB_ID
        print(f"Database ID: {db_id}")
        
        try:
            db_response = await client.databases.retrieve(database_id=db_id)
            print(f"✅ Database accessible: {db_response['title'][0]['plain_text']}")
            
            # Show properties
            properties = db_response.get('properties', {})
            print(f"Database properties: {list(properties.keys())}")
            
            # Check for title property
            title_prop = None
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'title':
                    title_prop = prop_name
                    break
            
            if title_prop:
                print(f"✅ Title property: '{title_prop}'")
                if title_prop != "Name":
                    print(f"⚠️  WARNING: Title property is '{title_prop}', not 'Name'")
            else:
                print(f"❌ ERROR: No title property found!")
            
        except Exception as e:
            print(f"❌ Database access failed: {e}")
            return
        
        # Test 2: Create a minimal page
        print(f"\n2. Testing page creation...")
        
        minimal_page = {
            "parent": {"database_id": db_id},
            "properties": {
                title_prop: {
                    "title": [
                        {
                            "text": {
                                "content": "TEST - Debug Page"
                            }
                        }
                    ]
                }
            }
        }
        
        try:
            page_response = await client.pages.create(**minimal_page)
            page_id = page_response['id']
            print(f"✅ Minimal page created: {page_id}")
            
            # Test 3: Add content to the page
            print(f"\n3. Testing content addition...")
            
            content_blocks = [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"text": {"content": "Test Heading"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": "This is a test paragraph to verify content can be added."}}]
                    }
                }
            ]
            
            try:
                append_response = await client.blocks.children.append(
                    block_id=page_id,
                    children=content_blocks
                )
                print(f"✅ Content added successfully: {len(append_response['results'])} blocks")
                
            except Exception as e:
                print(f"❌ Content addition failed: {e}")
                print("This is likely the source of your empty pages!")
                
                # Try to add content one block at a time
                print(f"\n4. Testing individual block addition...")
                for i, block in enumerate(content_blocks):
                    try:
                        single_response = await client.blocks.children.append(
                            block_id=page_id,
                            children=[block]
                        )
                        print(f"✅ Block {i+1} added successfully")
                    except Exception as block_error:
                        print(f"❌ Block {i+1} failed: {block_error}")
            
            # Test 4: Try creating page with children in one call (like the original code)
            print(f"\n5. Testing page creation with children...")
            
            page_with_content = {
                "parent": {"database_id": db_id},
                "properties": {
                    title_prop: {
                        "title": [
                            {
                                "text": {
                                    "content": "TEST - Page with Content"
                                }
                            }
                        ]
                    }
                },
                "children": content_blocks
            }
            
            try:
                full_response = await client.pages.create(**page_with_content)
                full_page_id = full_response['id']
                print(f"✅ Page with content created: {full_page_id}")
                
                # Verify content was actually added
                children_response = await client.blocks.children.list(block_id=full_page_id)
                actual_blocks = len(children_response['results'])
                print(f"✅ Verified: Page has {actual_blocks} content blocks")
                
                if actual_blocks == 0:
                    print("❌ PROBLEM FOUND: Page created but content blocks ignored!")
                elif actual_blocks < len(content_blocks):
                    print(f"⚠️  PARTIAL PROBLEM: Expected {len(content_blocks)}, got {actual_blocks}")
                
            except Exception as e:
                print(f"❌ Page creation with children failed: {e}")
                print("This confirms the issue is with the 'children' parameter")
        
        except Exception as e:
            print(f"❌ Page creation failed: {e}")
            
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_notion_simple())