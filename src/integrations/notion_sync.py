import asyncio
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
import time

from notion_client import AsyncClient
from .notion_config import NotionConfig

logger = logging.getLogger(__name__)

@dataclass
class SyncResult:
    """Result of a Notion sync operation"""
    success: bool
    meeting_id: Optional[str] = None
    meeting_url: Optional[str] = None
    tasks_created: List[Dict] = None
    tasks_failed: List[Dict] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.tasks_created is None:
            self.tasks_created = []
        if self.tasks_failed is None:
            self.tasks_failed = []
        if self.errors is None:
            self.errors = []

class NotionSync:
    """Handles synchronization with Notion databases"""
    
    def __init__(self):
        NotionConfig.validate_config()
        self.client = AsyncClient(auth=NotionConfig.NOTION_API_KEY)
        self.config = NotionConfig()
    
    async def sync_analysis_to_notion(
        self, 
        analysis_result: Dict,
        meeting_date: Optional[date] = None
    ) -> SyncResult:
        """
        Sync meeting analysis to Notion databases
        
        Args:
            analysis_result: The analysis result from meeting_analyzer
            meeting_date: Optional meeting date, defaults to today
        
        Returns:
            SyncResult with details of what was created
        """
        result = SyncResult(success=False)
        
        try:
            # Use today's date if not provided
            if not meeting_date:
                meeting_date = date.today()
            
            # 1. Create meeting in Interactions Registry
            logger.info("Creating meeting in Interactions Registry...")
            meeting_page = await self._create_meeting_page(
                analysis_result, 
                meeting_date
            )
            
            if meeting_page:
                result.meeting_id = meeting_page["id"]
                result.meeting_url = meeting_page.get("url", "")
                logger.info(f"Created meeting page: {result.meeting_id}")
            else:
                result.errors.append("Failed to create meeting page")
                return result
            
            # 2. Extract and create tasks
            logger.info("Extracting action items...")
            action_items = analysis_result.get("action_items", [])
            
            if not action_items:
                logger.warning("No action items found in analysis")
                result.success = True  # Meeting created successfully
                return result
            
            # 3. Create tasks with retry logic
            for item in action_items:
                task_result = await self._create_task_with_retry(
                    item, 
                    result.meeting_id
                )
                
                if task_result["success"]:
                    result.tasks_created.append(task_result)
                else:
                    result.tasks_failed.append(task_result)
            
            # 4. Verify created tasks
            logger.info("Verifying created tasks...")
            verified_count = await self._verify_tasks(result.tasks_created)
            logger.info(f"Verified {verified_count}/{len(result.tasks_created)} tasks")
            
            result.success = True
            
        except Exception as e:
            logger.error(f"Error during Notion sync: {e}")
            result.errors.append(str(e))
        
        return result
    
    async def _create_meeting_page(
        self, 
        analysis_result: Dict, 
        meeting_date: date
    ) -> Optional[Dict]:
        """Create a new page in the Interactions Registry database"""
        try:
            # Generate intelligent meeting title
            title_phrase = self._generate_meeting_title(analysis_result)
            page_title = f"{meeting_date.isoformat()} {title_phrase}"
            
            # Prepare page creation parameters
            create_params = {
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
                }
            }
            
            # Create meeting page with complete template structure
            logger.info("Creating meeting page with complete template structure")
            
            # Step 1: Create the page
            response = await self.client.pages.create(**create_params)
            page_id = response["id"]
            
            # Step 2: Add Meeting Minutes and Transcription sections
            content_blocks = self._format_meeting_content(analysis_result)
            if content_blocks:
                await self.client.blocks.children.append(
                    block_id=page_id,
                    children=content_blocks
                )
                logger.info(f"Added {len(content_blocks)} meeting content blocks")
            
            # Step 3: Add Action Items and Attendees database views
            database_views_success = await self._create_database_views(page_id)
            if database_views_success:
                logger.info("Successfully created complete template structure")
            else:
                logger.warning("Template structure created but database views may have failed")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to create meeting page: {e}")
            
            # Fallback: try creating without template if template creation failed
            if NotionConfig.USE_TEMPLATE:
                logger.warning("Template creation failed, falling back to non-template method")
                try:
                    content_blocks = self._format_meeting_content(analysis_result)
                    fallback_params = {
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
                    response = await self.client.pages.create(**fallback_params)
                    logger.info("Successfully created page using fallback method")
                    return response
                except Exception as fallback_error:
                    logger.error(f"Fallback creation also failed: {fallback_error}")
            
            return None
    
    def _generate_meeting_title(self, analysis_result: Dict) -> str:
        """Generate intelligent meeting title from analysis content"""
        summary = analysis_result.get("summary", "")
        key_decisions = analysis_result.get("key_decisions", [])
        discussion_points = analysis_result.get("discussion_points", [])
        
        # Strategy 1: Look for explicit meeting types or topics in summary
        if summary:
            summary_lower = summary.lower()
            
            # Common meeting patterns
            meeting_patterns = [
                ("partnership", "Partnership Discussion"),
                ("weekly", "Weekly Meeting"),
                ("standup", "Team Standup"),
                ("retrospective", "Retrospective"),
                ("planning", "Planning Session"),
                ("review", "Review Meeting"),
                ("checkpoint", "Checkpoint"),
                ("sync", "Sync Meeting"),
                ("kickoff", "Project Kickoff"),
                ("demo", "Demo Session"),
                ("training", "Training Session"),
                ("interview", "Interview"),
                ("onboarding", "Onboarding Session")
            ]
            
            for pattern, title in meeting_patterns:
                if pattern in summary_lower:
                    return title
        
        # Strategy 2: Extract key topics from key decisions
        if key_decisions:
            first_decision = key_decisions[0]
            # Extract main subject/topic
            if "partnership" in first_decision.lower():
                return "Partnership Discussion"
            elif "project" in first_decision.lower():
                return "Project Discussion"
            elif "budget" in first_decision.lower():
                return "Budget Meeting"
            elif "strategy" in first_decision.lower():
                return "Strategy Session"
        
        # Strategy 3: Extract from discussion points
        if discussion_points:
            first_point = discussion_points[0]
            if len(first_point) > 10:
                # Extract key words and create title
                words = first_point.split()[:4]  # First 4 words
                topic = " ".join(words)
                if len(topic) < 40:
                    return f"{topic} Discussion"
        
        # Strategy 4: Fallback to first meaningful sentence from summary
        if summary:
            sentences = summary.split('.')
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 10 and len(sentence) < 60:
                    # Clean up the sentence
                    if sentence.startswith("The meeting"):
                        sentence = sentence.replace("The meeting", "").strip()
                    if sentence.startswith("focused on"):
                        sentence = sentence.replace("focused on", "").strip()
                    if sentence:
                        return sentence.title()
        
        # Final fallback
        return "Team Meeting"
    
    def _format_meeting_content(self, analysis_result: Dict) -> List[Dict]:
        """Format the meeting content using the 4-section template structure"""
        blocks = []
        
        # Section 1: Meeting Minutes
        blocks.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"text": {"content": "Meeting Minutes"}}]
            }
        })
        
        # Add summary
        summary = analysis_result.get("summary", "")
        if summary:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Summary"}}]
                }
            })
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": summary}}]
                }
            })
        
        # Add key decisions
        key_decisions = analysis_result.get("key_decisions", [])
        if key_decisions:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Key Decisions"}}]
                }
            })
            for decision in key_decisions:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": decision}}]
                    }
                })
        
        # Add discussion points
        discussion_points = analysis_result.get("discussion_points", [])
        if discussion_points:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Discussion Points"}}]
                }
            })
            for point in discussion_points:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": point}}]
                    }
                })
        
        # Section 2: Meeting Transcription Cleaned (Toggle)
        cleaned_transcript = analysis_result.get("cleaned_transcript", "")
        if cleaned_transcript:
            blocks.append({
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"text": {"content": "Meeting Transcription Cleaned"}}],
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{
                                    "text": {
                                        "content": cleaned_transcript[:2000]  # Notion has limits
                                    }
                                }]
                            }
                        }
                    ]
                }
            })
        
        return blocks
    
    async def _create_database_views(self, page_id: str) -> bool:
        """Create the Action Items and Attendees database views"""
        try:
            # Section 3: Action Items heading
            action_items_heading = [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"text": {"content": "Action Items"}}]
                    }
                }
            ]
            
            await self.client.blocks.children.append(
                block_id=page_id,
                children=action_items_heading
            )
            
            # Create linked database view for Action Items (references existing Tasks DB)
            try:
                # Add link to Tasks database with filtering instructions
                tasks_info_block = {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "💡 View action items: Open "
                                }
                            },
                            {
                                "type": "text",
                                "text": {
                                    "content": "Tasks Database",
                                    "link": {
                                        "url": f"https://www.notion.so/{NotionConfig.TASKS_DB_ID.replace('-', '')}"
                                    }
                                },
                                "annotations": {
                                    "bold": True
                                }
                            },
                            {
                                "type": "text",
                                "text": {
                                    "content": " and filter by 'Meeting = This Page'"
                                }
                            }
                        ]
                    }
                }
                
                await self.client.blocks.children.append(
                    block_id=page_id,
                    children=[tasks_info_block]
                )
                logger.info(f"Added Tasks database link with filtering instructions")
            except Exception as e:
                logger.warning(f"Tasks database link creation failed: {e}")
            
            # Section 4: Attendees heading
            attendees_heading = [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"text": {"content": "Attendees"}}]
                    }
                }
            ]
            
            await self.client.blocks.children.append(
                block_id=page_id,
                children=attendees_heading
            )
            
            # Create linked database view for Attendees (references existing Contacts DB)
            try:
                # Add link to Contacts database
                contacts_info_block = {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "👥 Manage attendees: Open "
                                }
                            },
                            {
                                "type": "text",
                                "text": {
                                    "content": "Contacts Database",
                                    "link": {
                                        "url": f"https://www.notion.so/{NotionConfig.CONTACTS_DB_ID.replace('-', '')}"
                                    }
                                },
                                "annotations": {
                                    "bold": True
                                }
                            },
                            {
                                "type": "text",
                                "text": {
                                    "content": " to add or update contact information"
                                }
                            }
                        ]
                    }
                }
                
                await self.client.blocks.children.append(
                    block_id=page_id,
                    children=[contacts_info_block]
                )
                logger.info(f"Added Contacts database link")
            except Exception as e:
                logger.warning(f"Contacts database link creation failed: {e}")
            
            logger.info("Successfully created database links and instructions")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database views: {e}")
            return False
    
    async def _create_task_with_retry(
        self, 
        action_item: Dict,
        meeting_id: str
    ) -> Dict:
        """Create a task with retry logic"""
        task_result = {
            "success": False,
            "task": action_item.get("task", ""),
            "error": None,
            "task_id": None,
            "attempts": 0
        }
        
        for attempt in range(NotionConfig.MAX_RETRIES):
            task_result["attempts"] = attempt + 1
            
            try:
                # Create the task
                task_page = await self._create_task(action_item, meeting_id)
                
                if task_page:
                    task_result["success"] = True
                    task_result["task_id"] = task_page["id"]
                    logger.info(f"Created task: {action_item.get('task', '')}")
                    return task_result
                    
            except Exception as e:
                task_result["error"] = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < NotionConfig.MAX_RETRIES - 1:
                    await asyncio.sleep(NotionConfig.RETRY_DELAY)
        
        return task_result
    
    async def _create_task(
        self, 
        action_item: Dict,
        meeting_id: str
    ) -> Optional[Dict]:
        """Create a single task in the Tasks database"""
        try:
            task_text = action_item.get("task", "")
            owner = action_item.get("owner", "")
            deadline = action_item.get("deadline", "")
            
            # Determine priority
            priority = NotionConfig.get_priority_from_text(task_text)
            
            # Build properties
            properties = {
                NotionConfig.TASK_FIELDS["title"]: {  # Use config for title field name
                    "title": [
                        {
                            "text": {
                                "content": task_text[:100]  # Limit to 100 chars
                            }
                        }
                    ]
                },
                NotionConfig.TASK_FIELDS["meeting"]: {
                    "relation": [
                        {
                            "id": meeting_id
                        }
                    ]
                },
                NotionConfig.TASK_FIELDS["priority"]: {
                    "select": {
                        "name": priority
                    }
                },
                NotionConfig.TASK_FIELDS["status"]: {
                    "status": {  # Changed from select to status (status is a special field type)
                        "name": NotionConfig.DEFAULT_STATUS
                    }
                }
            }
            
            # Add Who field if we have an owner (now multi-select)
            if owner:
                # Handle both single owners and comma-separated multiple owners
                owner_list = [o.strip() for o in owner.split(',') if o.strip()]
                multi_select_options = []
                
                for owner_name in owner_list:
                    multi_select_options.append({
                        "name": owner_name
                    })
                
                properties[NotionConfig.TASK_FIELDS["who"]] = {
                    "multi_select": multi_select_options
                }
            
            # Note: Due date is left empty as per requirements
            # User will manually add dates
            
            # Create the task
            response = await self.client.pages.create(
                parent={"database_id": NotionConfig.TASKS_DB_ID},
                properties=properties
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to create task '{action_item.get('task', '')}': {e}")
            return None
    
    async def _verify_tasks(self, created_tasks: List[Dict]) -> int:
        """Verify that tasks were created with correct fields"""
        verified_count = 0
        
        for task_info in created_tasks:
            if not task_info.get("task_id"):
                continue
            
            try:
                # Fetch the task to verify fields
                page = await self.client.pages.retrieve(
                    page_id=task_info["task_id"]
                )
                
                # Check if Meeting relation is set
                meeting_relation = page["properties"].get("Meeting", {}).get("relation", [])
                if meeting_relation:
                    verified_count += 1
                    logger.info(f"✓ Task verified: {task_info['task']}")
                else:
                    logger.warning(f"✗ Task missing Meeting relation: {task_info['task']}")
                    
            except Exception as e:
                logger.error(f"Failed to verify task {task_info['task_id']}: {e}")
        
        return verified_count
    
    async def check_notion_connection(self) -> bool:
        """Test if Notion API connection is working"""
        try:
            # Try to retrieve the databases to verify access
            await self.client.databases.retrieve(
                database_id=NotionConfig.INTERACTIONS_REGISTRY_DB_ID
            )
            return True
        except Exception as e:
            logger.error(f"Notion connection test failed: {e}")
            return False

# Global sync instance (initialized lazily)
notion_sync = None

def get_notion_sync():
    """Get the global Notion sync instance, creating it if necessary"""
    global notion_sync
    if notion_sync is None:
        notion_sync = NotionSync()
    return notion_sync