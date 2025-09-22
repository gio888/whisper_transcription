import os
from typing import Dict, List, Optional
from enum import Enum

class NotionConfig:
    """Configuration for Notion integration"""
    
    # API Configuration
    NOTION_API_KEY = os.getenv("NOTION_API_KEY")
    NOTION_VERSION = "2022-06-28"  # Notion API version

    # Database IDs - configured via environment variables
    INTERACTIONS_REGISTRY_DB_ID = os.getenv("NOTION_INTERACTIONS_DB_ID")
    PROJECTS_DB_ID = os.getenv("NOTION_PROJECTS_DB_ID")
    TASKS_DB_ID = os.getenv("NOTION_TASKS_DB_ID")
    CONTACTS_DB_ID = os.getenv("NOTION_CONTACTS_DB_ID")
    
    # Field names for Tasks database
    TASK_FIELDS = {
        "title": "Task name",  # The title property (updated to match actual database)
        "meeting": "Meeting",  # Relation to Interactions Registry
        "project": "Project",  # Relation to Projects database
        "who": "Who",  # Select field (formerly "Delegated To")
        "due": "Due",  # Date field
        "priority": "Priority",  # Select: High/Medium/Low
        "status": "Status",  # Select: Not Started, etc.
    }
    
    # Priority mapping based on urgency keywords
    PRIORITY_KEYWORDS = {
        "High": [
            "urgent", "critical", "immediately", "asap", "today", 
            "crucial", "blocker", "blocking", "emergency"
        ],
        "Medium": [
            "soon", "this week", "next week", "important", 
            "coordinate", "follow up", "check", "review"
        ],
        "Low": [
            "eventually", "nice to have", "consider", "explore", 
            "research", "investigate", "optional"
        ]
    }
    
    # Status options
    DEFAULT_STATUS = "Not Started"
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    # Content formatting
    MEETING_TITLE_MAX_LENGTH = 50  # Characters for meeting title phrase
    
    # Template configuration
    USE_TEMPLATE = os.getenv("USE_NOTION_TEMPLATE", "true").lower() == "true"
    TEMPLATE_ID = os.getenv("NOTION_MEETING_TEMPLATE_ID", None)  # None = use database default template
    
    @classmethod
    def validate_config(cls):
        """Validate that necessary configuration is present"""
        if not cls.NOTION_API_KEY:
            raise ValueError("NOTION_API_KEY environment variable is required")
        return True
    
    @classmethod
    def get_priority_from_text(cls, text: str) -> str:
        """Determine priority based on text content"""
        text_lower = text.lower()
        
        # Check for high priority keywords
        for keyword in cls.PRIORITY_KEYWORDS["High"]:
            if keyword in text_lower:
                return "High"
        
        # Check for medium priority keywords
        for keyword in cls.PRIORITY_KEYWORDS["Medium"]:
            if keyword in text_lower:
                return "Medium"
        
        # Default to low priority
        return "Low"
    
    @classmethod
    def extract_names_from_text(cls, text: str) -> List[str]:
        """Extract potential assignee names from text"""
        names = []
        
        # Common patterns for names/teams
        patterns = [
            "assigned to", "owner:", "responsible:", "delegate to",
            "team:", "person:", "who:"
        ]
        
        # Simple extraction logic - can be enhanced
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            for pattern in patterns:
                if pattern in line_lower:
                    # Extract the part after the pattern
                    parts = line.split(pattern, 1)
                    if len(parts) > 1:
                        name = parts[1].strip().split(',')[0].split('.')[0]
                        if name and len(name) < 50:  # Reasonable name length
                            names.append(name)
        
        # Also look for capitalized words that might be names
        words = text.split()
        for word in words:
            # Simple heuristic: capitalized words that aren't common words
            if (word[0].isupper() and 
                len(word) > 2 and 
                word.lower() not in ['the', 'and', 'for', 'with', 'from', 'will']):
                # Could be a name or team
                if word not in names:
                    names.append(word)
        
        return names[:5]  # Return up to 5 potential names