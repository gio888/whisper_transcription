"""
Configuration Validator for Whisper Transcription Service
Ensures all required environment variables are properly configured
"""

import os
import sys
from typing import Dict, List, Tuple, Optional
from enum import Enum
from pathlib import Path

class ConfigStatus(Enum):
    VALID = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    INFO = "ℹ️"

class ConfigValidator:
    """Validates application configuration at startup"""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def validate_all(self) -> bool:
        """Run all configuration validations"""
        print("\n" + "="*60)
        print("🔍 CONFIGURATION VALIDATION")
        print("="*60)

        # Check core requirements
        self._validate_core()

        # Check LLM configuration
        self._validate_llm_config()

        # Check Notion configuration (if enabled)
        self._validate_notion_config()

        # Check file system
        self._validate_filesystem()

        # Check dependencies
        self._validate_dependencies()

        # Print summary
        return self._print_summary()

    def _validate_core(self):
        """Validate core configuration"""
        print("\n📦 Core Configuration:")

        # Check if .env file exists
        if not Path(".env").exists():
            self.warnings.append("No .env file found. Using defaults from .env.example")
            print(f"  {ConfigStatus.WARNING.value} .env file: Not found (using defaults)")
        else:
            print(f"  {ConfigStatus.VALID.value} .env file: Found")

        # Check Python version
        py_version = sys.version_info
        if py_version.major >= 3 and py_version.minor >= 8:
            print(f"  {ConfigStatus.VALID.value} Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
        else:
            self.errors.append(f"Python 3.8+ required, found {py_version.major}.{py_version.minor}")
            print(f"  {ConfigStatus.ERROR.value} Python version: {py_version.major}.{py_version.minor} (3.8+ required)")

    def _validate_llm_config(self):
        """Validate LLM provider configuration"""
        print("\n🤖 LLM Configuration:")

        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        default_provider = os.getenv("DEFAULT_PROVIDER", "local")
        local_model = os.getenv("LOCAL_MODEL", "qwen2.5:7b")
        local_url = os.getenv("LOCAL_API_URL", "http://localhost:11434")

        # Check default provider
        print(f"  {ConfigStatus.INFO.value} Default provider: {default_provider}")

        # Validate based on provider
        if default_provider.lower() == "openai":
            if openai_key and openai_key != "your_openai_api_key_here":
                print(f"  {ConfigStatus.VALID.value} OpenAI API key: Configured")
            else:
                self.errors.append("DEFAULT_PROVIDER is 'openai' but OPENAI_API_KEY not configured")
                print(f"  {ConfigStatus.ERROR.value} OpenAI API key: Not configured")

        elif default_provider.lower() == "anthropic":
            if anthropic_key and anthropic_key != "your_anthropic_api_key_here":
                print(f"  {ConfigStatus.VALID.value} Anthropic API key: Configured")
            else:
                self.errors.append("DEFAULT_PROVIDER is 'anthropic' but ANTHROPIC_API_KEY not configured")
                print(f"  {ConfigStatus.ERROR.value} Anthropic API key: Not configured")

        elif default_provider.lower() == "local":
            print(f"  {ConfigStatus.INFO.value} Local model: {local_model}")
            print(f"  {ConfigStatus.INFO.value} Local URL: {local_url}")
            self.info.append("Using local Ollama. Ensure 'ollama serve' is running")

        # Check fallback configuration
        if os.getenv("ENABLE_ANALYSIS_FALLBACK", "true").lower() == "true":
            fallback = os.getenv("FALLBACK_PROVIDER", "anthropic")
            print(f"  {ConfigStatus.INFO.value} Fallback enabled: {fallback}")

            if fallback.lower() == "anthropic" and not anthropic_key:
                self.warnings.append("Fallback enabled but Anthropic API key not configured")
            elif fallback.lower() == "openai" and not openai_key:
                self.warnings.append("Fallback enabled but OpenAI API key not configured")

    def _validate_notion_config(self):
        """Validate Notion integration configuration"""
        notion_key = os.getenv("NOTION_API_KEY")

        # Skip if Notion not configured
        if not notion_key or notion_key == "your_notion_api_key_here":
            print("\n📝 Notion Integration: Not configured (optional)")
            return

        print("\n📝 Notion Integration:")
        print(f"  {ConfigStatus.VALID.value} API key: Configured")

        # Check database IDs
        db_configs = [
            ("NOTION_INTERACTIONS_DB_ID", "Interactions Registry"),
            ("NOTION_PROJECTS_DB_ID", "Projects"),
            ("NOTION_TASKS_DB_ID", "Tasks"),
            ("NOTION_CONTACTS_DB_ID", "Contacts"),
        ]

        missing_dbs = []
        for env_var, name in db_configs:
            db_id = os.getenv(env_var)
            if db_id and db_id != f"your_{env_var.lower()}_here":
                print(f"  {ConfigStatus.VALID.value} {name} DB: Configured")
            else:
                missing_dbs.append(name)
                print(f"  {ConfigStatus.WARNING.value} {name} DB: Not configured")

        if missing_dbs:
            self.warnings.append(f"Notion enabled but missing database IDs: {', '.join(missing_dbs)}")

    def _validate_filesystem(self):
        """Validate file system setup"""
        print("\n📁 File System:")

        # Check required directories
        dirs_to_check = [
            ("models", "Whisper models directory"),
            ("uploads", "Upload directory"),
            ("static", "Static files directory"),
        ]

        for dir_path, description in dirs_to_check:
            if Path(dir_path).exists():
                print(f"  {ConfigStatus.VALID.value} {description}: Exists")
            else:
                self.warnings.append(f"{description} not found: {dir_path}")
                print(f"  {ConfigStatus.WARNING.value} {description}: Missing (will be created)")

        # Check Whisper model
        model_path = Path("models/small.bin")
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"  {ConfigStatus.VALID.value} Whisper model: Found ({size_mb:.1f} MB)")
        else:
            self.errors.append("Whisper model not found. Run ./setup.sh to download")
            print(f"  {ConfigStatus.ERROR.value} Whisper model: Not found")

    def _validate_dependencies(self):
        """Check external dependencies"""
        print("\n🔧 Dependencies:")

        # Check for whisper-cli
        if os.system("which whisper-cli > /dev/null 2>&1") == 0:
            print(f"  {ConfigStatus.VALID.value} whisper-cli: Installed")
        else:
            self.errors.append("whisper-cli not found. Install with: brew install whisper-cpp")
            print(f"  {ConfigStatus.ERROR.value} whisper-cli: Not found")

        # Check for ffmpeg
        if os.system("which ffmpeg > /dev/null 2>&1") == 0:
            print(f"  {ConfigStatus.VALID.value} ffmpeg: Installed")
        else:
            self.errors.append("ffmpeg not found. Install with: brew install ffmpeg")
            print(f"  {ConfigStatus.ERROR.value} ffmpeg: Not found")

        # Check if Ollama is running (for local provider)
        if os.getenv("DEFAULT_PROVIDER", "local").lower() == "local":
            import requests
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    print(f"  {ConfigStatus.VALID.value} Ollama: Running")
                else:
                    self.warnings.append("Ollama server not responding. Run: ollama serve")
                    print(f"  {ConfigStatus.WARNING.value} Ollama: Not responding")
            except:
                self.warnings.append("Ollama not running. Run: ollama serve")
                print(f"  {ConfigStatus.WARNING.value} Ollama: Not running")

    def _print_summary(self) -> bool:
        """Print validation summary and return success status"""
        print("\n" + "="*60)
        print("📊 VALIDATION SUMMARY")
        print("="*60)

        # Print errors
        if self.errors:
            print(f"\n{ConfigStatus.ERROR.value} Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")

        # Print warnings
        if self.warnings:
            print(f"\n{ConfigStatus.WARNING.value} Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")

        # Print info
        if self.info:
            print(f"\n{ConfigStatus.INFO.value} Info:")
            for info in self.info:
                print(f"   • {info}")

        # Final status
        if self.errors:
            print(f"\n{ConfigStatus.ERROR.value} Configuration validation FAILED")
            print("Please fix the errors above before starting the service")
            return False
        elif self.warnings:
            print(f"\n{ConfigStatus.WARNING.value} Configuration valid with warnings")
            print("Service can start but some features may not work properly")
            return True
        else:
            print(f"\n{ConfigStatus.VALID.value} Configuration validation PASSED")
            return True

def validate_config(exit_on_error: bool = False) -> bool:
    """
    Validate configuration and optionally exit on error

    Args:
        exit_on_error: If True, exit the program on validation errors

    Returns:
        True if configuration is valid, False otherwise
    """
    validator = ConfigValidator()
    is_valid = validator.validate_all()

    if not is_valid and exit_on_error:
        sys.exit(1)

    return is_valid

if __name__ == "__main__":
    # Run validation when script is executed directly
    validate_config(exit_on_error=True)