# Configuration Guide

This document provides a comprehensive guide to configuring the Whisper Transcription Service.

## Configuration Matrix

| Variable | Required | Feature | Default | Description |
|----------|----------|---------|---------|-------------|
| **Core Configuration** |
| `DEFAULT_PROVIDER` | ✅ | LLM Analysis | `local` | Primary LLM provider (`local`, `openai`, `anthropic`) |
| **OpenAI Configuration** |
| `OPENAI_API_KEY` | ❌* | Meeting Analysis | - | Required if DEFAULT_PROVIDER=openai |
| `OPENAI_MODEL` | ❌ | Meeting Analysis | `gpt-4o-mini` | OpenAI model selection |
| **Anthropic Configuration** |
| `ANTHROPIC_API_KEY` | ❌* | Meeting Analysis | - | Required if DEFAULT_PROVIDER=anthropic |
| `ANTHROPIC_MODEL` | ❌ | Meeting Analysis | `claude-3-haiku-20240307` | Anthropic model selection |
| **Local LLM Configuration** |
| `LOCAL_MODEL` | ❌ | Local Analysis | `qwen2.5:7b` | Ollama model name |
| `LOCAL_API_URL` | ❌ | Local Analysis | `http://localhost:11434` | Ollama server URL |
| **Fallback Configuration** |
| `ENABLE_ANALYSIS_FALLBACK` | ❌ | Quality Control | `true` | Enable fallback on poor analysis |
| `FALLBACK_PROVIDER` | ❌ | Quality Control | `anthropic` | Provider for fallback |
| **Notion Integration** |
| `NOTION_API_KEY` | ❌ | Notion Sync | - | Notion integration API key |
| `NOTION_INTERACTIONS_DB_ID` | ❌* | Notion Sync | - | Required if Notion enabled |
| `NOTION_PROJECTS_DB_ID` | ❌* | Notion Sync | - | Required if Notion enabled |
| `NOTION_TASKS_DB_ID` | ❌* | Notion Sync | - | Required if Notion enabled |
| `NOTION_CONTACTS_DB_ID` | ❌* | Notion Sync | - | Required if Notion enabled |
| `NOTION_MEETING_TEMPLATE_ID` | ❌ | Notion Sync | - | Optional template ID |
| **Business Context** |
| `COMPANY_CONTEXT` | ❌ | Analysis Quality | Generic | Industry-specific context |

*Required only when the associated feature is enabled

## Configuration Profiles

### 🚀 Quick Start (Local Only)
Minimal configuration for basic transcription with local LLM:

```bash
# .env
DEFAULT_PROVIDER=local
LOCAL_MODEL=qwen2.5:7b
```

### 💼 Professional (OpenAI)
For business use with OpenAI integration:

```bash
# .env
DEFAULT_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

COMPANY_CONTEXT="Software development company focusing on web applications"
```

### 🏢 Enterprise (Full Features)
Complete setup with Notion integration and fallback:

```bash
# .env
# Primary LLM
DEFAULT_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Fallback
ENABLE_ANALYSIS_FALLBACK=true
FALLBACK_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Notion Integration
NOTION_API_KEY=secret_...
NOTION_INTERACTIONS_DB_ID=403e42ac80c0457ca6cc0fad107d598e
NOTION_PROJECTS_DB_ID=8b52a89a496e442391676f85bf89cd11
NOTION_TASKS_DB_ID=556f8a1f-b141-4fb5-8a65-81d7eaced707
NOTION_CONTACTS_DB_ID=533ef09266a6484aa343c897ebe1cff8

# Business Context
COMPANY_CONTEXT="Tech consulting firm specializing in cloud infrastructure..."
```

### 🔒 Privacy-First (Local Only)
Complete privacy with no external API calls:

```bash
# .env
DEFAULT_PROVIDER=local
LOCAL_MODEL=llama3.2:8b
LOCAL_API_URL=http://localhost:11434
ENABLE_ANALYSIS_FALLBACK=false
```

## Validation

Run the configuration validator to check your setup:

```bash
# Validate configuration
python config_validator.py

# Or as part of smoke test
python smoke_test.py
```

## Environment-Specific Configuration

### Development
```bash
cp .env.example .env.development
# Edit with test API keys and local settings
```

### Production
```bash
cp .env.example .env.production
# Use production API keys and optimized settings
```

### Testing
```bash
cp .env.example .env.test
# Use test/sandbox API keys
```

## Security Best Practices

### 1. API Key Management
- **Never** commit API keys to version control
- Rotate keys regularly
- Use separate keys for development/production
- Restrict API key permissions when possible

### 2. Secret Storage
```bash
# macOS Keychain (recommended for local development)
security add-generic-password -a "$USER" -s "OPENAI_API_KEY" -w "your-api-key"

# Retrieve in shell
export OPENAI_API_KEY=$(security find-generic-password -a "$USER" -s "OPENAI_API_KEY" -w)
```

### 3. File Permissions
```bash
# Restrict .env file access
chmod 600 .env

# Verify permissions
ls -la .env
# Should show: -rw------- (only owner can read/write)
```

### 4. Git Security
```bash
# Ensure .env is ignored
git check-ignore .env
# Should output: .env

# Check for accidentally committed secrets
git log --all --full-history -- "**/.env*"
```

## Troubleshooting

### Missing Configuration
```
Error: OPENAI_API_KEY environment variable is required
```
**Solution:** Ensure your `.env` file contains the required API key

### Invalid API Key
```
Error: OpenAI API authentication failed
```
**Solution:** Verify your API key is correct and has proper permissions

### Notion Connection Issues
```
Warning: Notion enabled but missing database IDs
```
**Solution:** Add all required database IDs to your `.env` file

### Local LLM Not Running
```
Warning: Ollama not running. Run: ollama serve
```
**Solution:** Start Ollama with `ollama serve` in a separate terminal

## Configuration Debugging

Enable debug mode to see configuration details:

```bash
# Add to .env
DEBUG_CONFIG=true

# Run validator with verbose output
python config_validator.py
```

## Migration Guide

### From Hardcoded Configuration
If upgrading from an older version with hardcoded values:

1. Copy `.env.example` to `.env`
2. Fill in your specific values
3. Remove any local modifications to `notion_config.py` or `analyzer_config.py`
4. Run `python config_validator.py` to verify

### From Different Providers
Switching between LLM providers:

```bash
# From OpenAI to Local
# Before: DEFAULT_PROVIDER=openai
# After:
DEFAULT_PROVIDER=local
LOCAL_MODEL=qwen2.5:7b

# From Local to Anthropic
# Before: DEFAULT_PROVIDER=local
# After:
DEFAULT_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key-here
```

## Support

For configuration issues:
1. Run `python config_validator.py` for diagnostics
2. Check this documentation
3. Review `.env.example` for all options
4. Open an issue on GitHub with validator output