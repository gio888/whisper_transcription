#!/usr/bin/env python3
"""
Test task creation directly
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables BEFORE importing config
load_dotenv()

from notion_client import AsyncClient
from notion_config import NotionConfig

async def test_task_creation():
    """Test creating a task directly"""
    
    print("=== DIRECT TASK CREATION TEST ===\n")
    
    client = AsyncClient(auth=os.getenv("NOTION_API_KEY"))
    
    # Create a test meeting page first
    print("1. Creating test meeting page...")
    meeting_response = await client.pages.create(
        parent={"database_id": NotionConfig.INTERACTIONS_REGISTRY_DB_ID},
        properties={
            "Name": {
                "title": [{"text": {"content": "TEST - Meeting for Task Test"}}]
            }
        }
    )
    meeting_id = meeting_response['id']
    print(f"✅ Meeting created: {meeting_id}\n")
    
    # Now try to create a task
    print("2. Creating task with config field names...")
    
    task_properties = {
        NotionConfig.TASK_FIELDS["title"]: {
            "title": [{"text": {"content": "TEST - Sample Task"}}]
        },
        NotionConfig.TASK_FIELDS["meeting"]: {
            "relation": [{"id": meeting_id}]
        },
        NotionConfig.TASK_FIELDS["priority"]: {
            "select": {"name": "High"}
        },
        NotionConfig.TASK_FIELDS["status"]: {
            "status": {"name": "Not Started"}  # Changed from select to status
        },
        NotionConfig.TASK_FIELDS["who"]: {
            "select": {"name": "Gio"}
        }
    }
    
    print("Task properties:")
    for key, value in task_properties.items():
        print(f"  '{key}': {list(value.keys())[0]} type")
    
    try:
        task_response = await client.pages.create(
            parent={"database_id": NotionConfig.TASKS_DB_ID},
            properties=task_properties
        )
        
        task_id = task_response['id']
        print(f"\n✅ Task created successfully: {task_id}")
        
        # Verify the task
        print("\n3. Verifying task...")
        task_page = await client.pages.retrieve(page_id=task_id)
        
        # Check if meeting relation is set
        meeting_relation = task_page["properties"].get(NotionConfig.TASK_FIELDS["meeting"], {}).get("relation", [])
        if meeting_relation:
            print(f"✅ Meeting relation set: {meeting_relation[0]['id']}")
        else:
            print("❌ Meeting relation NOT set")
        
        # Check status
        status = task_page["properties"].get(NotionConfig.TASK_FIELDS["status"], {})
        if status:
            print(f"✅ Status: {status.get('status', {}).get('name', 'Unknown')}")
        
        # Check priority
        priority = task_page["properties"].get(NotionConfig.TASK_FIELDS["priority"], {})
        if priority:
            print(f"✅ Priority: {priority.get('select', {}).get('name', 'Unknown')}")
        
        # Check who
        who = task_page["properties"].get(NotionConfig.TASK_FIELDS["who"], {})
        if who:
            print(f"✅ Who: {who.get('select', {}).get('name', 'Unknown')}")
        
    except Exception as e:
        print(f"\n❌ Task creation failed: {e}")
        print("\nFull error details:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_task_creation())