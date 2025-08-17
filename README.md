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
git clone https://github.com/gio888/whisper_transcription.git
cd whisper_transcription

# One-command setup (downloads model + installs dependencies)
./setup.sh
```

### 2. Start the Service
```bash
./run.sh
```

### 3. Open in Browser
Navigate to http://localhost:8000

### 4. Run Tests (Recommended before batch processing)
```bash
# Quick smoke test (5 seconds) - Run this before overnight batches!
python smoke_test.py

# Full test suite
pytest -v
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
├── app.py              # FastAPI server
├── transcriber.py      # Whisper integration
├── config.py          # Configuration
├── static/            # Web interface
│   ├── index.html     # Main UI
│   ├── app.js         # Client logic
│   └── style.css      # Styling
├── setup.sh           # Installation script
├── run.sh            # Start script
└── requirements.txt   # Python dependencies
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