import os
from pathlib import Path
from typing import Optional
from enum import Enum

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"

class AnalyzerConfig:
    
    # API Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Local Model Configuration
    LOCAL_MODEL = os.getenv("LOCAL_MODEL", "qwen2.5:7b")
    LOCAL_API_URL = os.getenv("LOCAL_API_URL", "http://localhost:11434")
    
    # Model Selection
    DEFAULT_PROVIDER = LLMProvider[os.getenv("DEFAULT_PROVIDER", "LOCAL").upper()]
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    
    # Hybrid Mode Settings
    ENABLE_FALLBACK = os.getenv("ENABLE_ANALYSIS_FALLBACK", "true").lower() == "true"
    FALLBACK_PROVIDER = LLMProvider[os.getenv("FALLBACK_PROVIDER", "ANTHROPIC").upper()]
    
    # Processing Settings
    MAX_CONTEXT_LENGTH = 100000  # Characters, not tokens
    CHUNK_OVERLAP = 500  # Characters to overlap between chunks
    TEMPERATURE = 0.3  # Lower for more consistent output
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 60
    
    # Output Settings
    INCLUDE_TIMESTAMPS = False  # We don't have timestamps from whisper
    MAX_SUMMARY_LENGTH = 1000  # Words
    MAX_ACTION_ITEMS = 20
    
    # Company Context - customizable via environment variable
    COMPANY_CONTEXT = os.getenv("COMPANY_CONTEXT", """
    Generic business context.
    Meetings may involve product development, partnerships, operations,
    customer needs, or strategic discussions.

    Note: Configure COMPANY_CONTEXT in your .env file for industry-specific analysis.
    """)
    
    # Prompts
    ANALYSIS_SYSTEM_PROMPT = """You are an expert meeting analyst specializing in technology and telecommunications businesses. 
    You analyze meeting transcripts to extract key insights, decisions, and action items.
    
    Context: {company_context}
    
    Your analysis should be practical, actionable, and focused on business value."""
    
    ANALYSIS_USER_PROMPT = """Analyze this meeting transcript and provide a structured analysis. 

IMPORTANT INSTRUCTIONS:
- Handle Filipino/Taglish content professionally
- Translate Filipino phrases to English when needed
- If transcript contains placeholders like [FOREIGN] or [BLANK_AUDIO], work with available content
- Focus on extracting actionable business insights
- Be concise but thorough

Please provide:

## Summary of the Meeting
Main topics discussed, key insights and conclusions, overall outcome (2-3 sentences)

## Key Decisions  
- Concrete decisions made
- Agreements reached  
- Strategic choices

## Notable Discussion Points
- Important debates or disagreements
- Reasoning behind decisions
- Risks or concerns raised

## Action Items
IMPORTANT: Extract ALL tasks and follow-ups mentioned or implied in the meeting.
For each action item, provide on separate lines:
Task: [Clear, specific description of what needs to be done]
Owner: [Person/team responsible - use "Sales Team", "Operations", "Leadership", etc. if unclear]
Deadline: [Timeline if mentioned like "next week", "by month end", or leave blank if not specified]

Look for action items in:
- "We need to..." → Task: [what needs to be done]
- "Let's discuss..." → Task: Schedule discussion about [topic]
- "We should align on..." → Task: Align on [topic]
- "Follow up on..." → Task: Follow up on [topic]
- "Will check..." → Task: Check [what needs checking]
- Decisions that need implementation
- Any next steps or future actions mentioned

If the meeting discussed partnerships, alignment, or follow-ups, create specific tasks for those.
Example: If they discussed aligning sales processes → Task: Align sales processes between teams

Transcript:
{transcript}

Provide your analysis in the exact format above with clear sections."""

    CLEANING_SYSTEM_PROMPT = """You are an expert editor who transforms raw meeting transcripts into clear, readable dialogues.
    You preserve the original meaning while improving clarity and flow."""
    
    CLEANING_USER_PROMPT = """Transform this raw meeting transcript into a clean, readable dialogue:

Requirements:
- Assign speaker labels (Speaker A, B, C, etc.) based on conversation flow
- Translate Filipino phrases to English (note the translation)
- Remove filler words and false starts
- Fix grammar while preserving meaning
- Group related statements by the same speaker
- Make it professional but preserve the conversational tone

Output format:
Speaker A: [cleaned statement]
Speaker B: [cleaned response]
[etc.]

Note: Add [Translated from Filipino] where translations occur.

Raw transcript:
{transcript}"""
    
    # Filipino Common Terms (for reference)
    FILIPINO_BUSINESS_TERMS = {
        "ano": "what",
        "oo": "yes", 
        "hindi": "no",
        "sige": "okay/sure",
        "teka": "wait",
        "kasi": "because",
        "tapos": "then/finished",
        "ganun": "like that",
        "diba": "right?",
        "nga": "indeed",
        "naman": "though/anyway",
        "talaga": "really",
        "pwede": "can/possible",
        "kelangan": "need",
        "salamat": "thank you",
    }
    
    # File Storage
    ANALYSIS_DIR = Path("analysis_results")
    ANALYSIS_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def get_provider(cls):
        """Determine which LLM provider to use based on available API keys"""
        if cls.DEFAULT_PROVIDER == LLMProvider.LOCAL:
            return LLMProvider.LOCAL
        elif cls.DEFAULT_PROVIDER == LLMProvider.OPENAI and cls.OPENAI_API_KEY:
            return LLMProvider.OPENAI
        elif cls.DEFAULT_PROVIDER == LLMProvider.ANTHROPIC and cls.ANTHROPIC_API_KEY:
            return LLMProvider.ANTHROPIC
        elif cls.OPENAI_API_KEY:
            return LLMProvider.OPENAI
        elif cls.ANTHROPIC_API_KEY:
            return LLMProvider.ANTHROPIC
        else:
            # Fallback to local if no API keys available
            return LLMProvider.LOCAL
    
    @classmethod
    def validate_config(cls):
        """Validate that necessary configuration is present"""
        provider = cls.get_provider()
        if provider == LLMProvider.OPENAI and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        elif provider == LLMProvider.ANTHROPIC and not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        elif provider == LLMProvider.LOCAL:
            # Local provider doesn't need API keys
            return True
        return True