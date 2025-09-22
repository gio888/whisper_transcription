# Whisper Transcription Web Service

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![macOS](https://img.shields.io/badge/macOS-Apple%20Silicon-black.svg)](https://www.apple.com/mac/)

A modern web-based interface for transcribing audio files locally using OpenAI's Whisper. Built for privacy-conscious users who want powerful speech-to-text capabilities without sending data to external services.

## ✨ Features

### 🎯 **Batch Processing**
- **Multi-file Upload**: Drag and drop multiple audio files for overnight processing
- **Sequential Processing**: Files process one-by-one to prevent system overload
- **Persistent Folder Selection**: Output folder choice remembered across sessions
- **Auto-save**: Transcripts save automatically to your selected folder as `filename.txt`
- **Smart Error Handling**: Failed files are skipped, batch continues processing

### 🌟 **Core Features**
- **Drag & Drop Interface**: Clean, accessible web interface with real-time progress
- **Multi-language Support**: Optimized for English and Filipino/Tagalog mixed audio
- **Fully Local**: No cloud services, no API keys, complete privacy
- **Apple Silicon Optimized**: Metal acceleration for M1/M2 Macs
- **Mobile Friendly**: Responsive design for monitoring progress on any device

### 🎨 **User Experience**
- **WCAG 2.1 AA Compliant**: Full accessibility with screen reader support
- **Keyboard Navigation**: Complete keyboard accessibility
- **Real-time Progress**: WebSocket-powered progress updates
- **Error Recovery**: Graceful error handling with actionable messages

## 📋 Prerequisites

### Required Software
```bash
# Install whisper.cpp (installs whisper-cli command)
brew install whisper-cpp

# Install ffmpeg for audio conversion
brew install ffmpeg

# Python 3.8+ (usually pre-installed on macOS)
python3 --version
```

### Supported Formats
- **Primary**: M4A (Apple's format from Voice Memos/Notes)
- **Also Supported**: MP3, WAV, AAC, MP4
- **Max File Size**: 500MB per file

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/yourusername/whisper_transcription.git
cd whisper_transcription

# One-command setup (downloads model + installs dependencies)
./setup.sh
```

### 2. Configure Environment (REQUIRED)
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
# At minimum, configure:
# - LLM API keys (or use local Ollama)
# - Notion integration (optional)
# - Company context for better analysis
nano .env  # or use your preferred editor
```

### 3. Start the Service
```bash
./run.sh
```

### 4. Open in Browser
Navigate to http://localhost:8000

### 5. Run Tests (Recommended before batch processing)
```bash
# Quick smoke test (5 seconds) - Run this before overnight batches!
python smoke_test.py

# Full test suite
pytest -v
```

## 🔧 Configuration

### Environment Variables
All user-specific configuration is managed through the `.env` file. Copy `.env.example` to `.env` and customize:

#### LLM Providers (Choose one or more)
```bash
# OpenAI (for meeting analysis)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Anthropic (alternative/fallback)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-haiku-20240307

# Local Ollama (FREE, no API key needed)
DEFAULT_PROVIDER=local
LOCAL_MODEL=qwen2.5:7b
LOCAL_API_URL=http://localhost:11434
```

#### Notion Integration (Optional)
```bash
# Get your API key from https://www.notion.so/my-integrations
NOTION_API_KEY=your_notion_api_key_here

# Database IDs (found in Notion URLs after the workspace name)
NOTION_INTERACTIONS_DB_ID=your_database_id_here
NOTION_PROJECTS_DB_ID=your_database_id_here
NOTION_TASKS_DB_ID=your_database_id_here
NOTION_CONTACTS_DB_ID=your_database_id_here
```

#### Business Context Customization
```bash
# Improve analysis accuracy with your business context
COMPANY_CONTEXT="We are a software consultancy specializing in web applications.
Common meeting topics include:
- Client requirements and project scope
- Technical architecture decisions
- Sprint planning and retrospectives
- Team coordination and resource allocation"
```

### Setting up Notion Integration

1. **Create Notion Integration:**
   - Go to https://www.notion.so/my-integrations
   - Click "New integration"
   - Give it a name (e.g., "Whisper Transcription")
   - Copy the API key to your `.env` file

2. **Share Databases with Integration:**
   - Open each database in Notion
   - Click "..." menu → "Add connections"
   - Select your integration

3. **Get Database IDs:**
   - Open database in Notion
   - Look at the URL: `https://notion.so/workspace/DATABASE_ID_HERE?v=...`
   - Copy the 32-character ID to your `.env` file

### Using Local LLM with Ollama

For completely free, private meeting analysis:

```bash
# Install Ollama
brew install ollama

# Start Ollama service
ollama serve

# Pull a model (one-time download)
ollama pull qwen2.5:7b

# Configure in .env
DEFAULT_PROVIDER=local
LOCAL_MODEL=qwen2.5:7b
```

## 📖 Usage

### Single File Transcription
1. Open http://localhost:8000
2. Drag and drop your audio file onto the upload zone
3. Watch real-time progress as it transcribes
4. Download the completed transcript

### Batch Processing
1. Drag multiple audio files at once onto the upload zone
2. Optionally select output folder (remembered for future sessions)
3. Files are queued and processed sequentially
4. Each transcript automatically saves to your selected folder
5. Monitor overall progress and individual file status
6. Perfect for overnight processing of large batches

### Keyboard Shortcuts
- **Tab**: Navigate through interface
- **Space/Enter**: Open file picker when drop zone is focused
- **Escape**: Cancel current operation

## ⚙️ Technical Details

### Architecture
- **Backend**: FastAPI with async WebSocket support
- **Frontend**: Vanilla JavaScript (no build tools required)
- **AI Model**: Whisper small.bin (461MB, multilingual)
- **Processing**: whisper.cpp with Metal GPU acceleration
- **Dependencies**: Isolated Python virtual environment

### Performance
- **Processing Speed**: ~1x realtime on Apple Silicon (1 hour audio ≈ 1 hour processing)
- **Memory Usage**: ~2GB RAM during processing
- **GPU Acceleration**: Automatic Metal backend on M1/M2 Macs
- **Concurrent Batches**: Sequential processing prevents thermal throttling

### File Structure
```
whisper_transcription/
├── app.py                    # FastAPI server
├── transcriber.py            # Whisper integration
├── config.py                 # Core configuration
├── config_validator.py       # Configuration validation
├── smoke_test.py            # Quick validation tests
├──
├── src/                     # Core application modules
│   ├── analyzers/           # Meeting analysis components
│   │   ├── meeting_analyzer.py
│   │   └── analyzer_config.py
│   ├── providers/           # LLM provider integrations
│   │   └── local_llm_provider.py
│   └── integrations/        # External service integrations
│       ├── notion_sync.py
│       └── notion_config.py
├──
├── tests/                   # All test files
│   ├── test_api.py
│   ├── test_websocket.py
│   └── test_*.py
├──
├── scripts/                 # Utility scripts
│   ├── check_secrets.py
│   └── start_ollama_optimized.sh
├──
├── dev/                     # Development utilities
│   ├── debug_analysis_parsing.py
│   └── inspect_notion_databases.py
├──
├── static/                  # Web interface
│   ├── index.html          # Main UI
│   ├── app.js              # Client logic
│   └── style.css           # Styling
├──
├── setup.sh                # Installation script
├── run.sh                  # Start script
└── requirements.txt        # Python dependencies
```

## 🐛 Troubleshooting

### Common Issues

**Service Won't Start**
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill any existing process
kill -9 $(lsof -ti:8000)
```

**Missing Dependencies**
```bash
# Reinstall dependencies
./setup.sh

# Or manually install
pip3 install -r requirements.txt
```

**Transcription Errors**
```bash
# Verify whisper.cpp installation
whisper-cli --help

# Check model file
ls -la models/small.bin
```

**Performance Issues**
```bash
# Check CPU temperature
sudo powermetrics -n 1 --samplers smc -a

# Monitor memory usage
activity monitor
```

### Testing

See [README_TESTING.md](README_TESTING.md) for comprehensive testing documentation.

**Quick Test Before Batch Processing:**
```bash
python smoke_test.py  # Takes 5 seconds, catches critical errors
```

### Getting Help

1. Check the [CHANGELOG.md](CHANGELOG.md) for recent updates
2. Review [README_TESTING.md](README_TESTING.md) for testing guidance
3. Search existing [GitHub Issues](https://github.com/gio888/whisper_transcription/issues)
4. Create a new issue with:
   - Your macOS version
   - Audio file format and size
   - Complete error messages
   - Steps to reproduce

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Code style guidelines
- Pull request process
- Testing requirements

### Quick Development Setup
```bash
# Clone and setup development environment
git clone https://github.com/gio888/whisper_transcription.git
cd whisper_transcription
./setup.sh

# Install test dependencies
pip install -r requirements-test.txt

# Run tests
pytest -v

# Start development server with auto-reload
python app.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for the incredible speech recognition model
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) for the efficient local implementation
- [FastAPI](https://fastapi.tiangolo.com/) for the modern web framework
- The open source community for continuous inspiration

## 🔗 Related Projects

- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) - C++ implementation of Whisper
- [OpenAI Whisper](https://github.com/openai/whisper) - Original Python implementation
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Alternative efficient implementation

---

**Built with ❤️ for privacy-conscious transcription**

Star ⭐ this repo if you find it useful!