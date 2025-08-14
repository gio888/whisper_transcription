# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-13

### Added
- **Batch Processing**: Multi-file drag & drop support for processing multiple audio files sequentially
- **Original Location Saving**: Transcripts automatically save next to source files as `filename.txt`
- **Queue Management**: Visual file queue with status indicators (queued, processing, completed, error)
- **Real-time Batch Progress**: Overall batch progress plus individual file progress tracking
- **Error Recovery**: Failed files are skipped, batch continues processing remaining files
- **Mobile-Optimized Batch Interface**: Responsive design for monitoring progress on mobile devices
- **Collapsible File Details**: Expandable queue view to save screen space
- **Enhanced Error Messages**: Specific, actionable error messages with recovery suggestions
- **Time Estimation**: Processing time estimates based on file size and duration
- **Accessibility Improvements**: Full WCAG compliance with screen reader support

### Enhanced
- **Multi-file Support**: Interface automatically switches between single-file and batch mode
- **WebSocket Architecture**: Separate WebSocket endpoints for single files vs batch processing
- **Progress Indicators**: Enhanced progress bars with ARIA attributes for accessibility
- **File Validation**: Improved validation with detailed feedback for unsupported files
- **Touch Targets**: Minimum 44px touch targets for mobile accessibility
- **Keyboard Navigation**: Full keyboard support including Space/Enter for file selection

### Technical
- **Sequential Processing**: Files process one at a time to prevent thermal throttling
- **Dynamic Host Detection**: WebSocket URLs adapt to deployment environment
- **Virtual Environment**: Clean Python dependency isolation
- **Production Ready**: Removed development-only features and warnings

## [1.1.0] - 2025-01-13

### Fixed
- **Prompt Issue**: Removed problematic prompt that caused repeated text in transcripts
- **WebSocket Startup**: Fixed server connection issues with proper uvicorn configuration
- **Event Handlers**: Updated to modern FastAPI lifespan handlers

### Enhanced
- **UX Improvements**: Based on comprehensive UX review
- **Error Handling**: More specific error messages with contextual help
- **Time Feedback**: Better processing time communication to users

## [1.0.0] - 2025-01-13

### Added
- **Initial Release**: Web-based audio transcription using whisper.cpp
- **Drag & Drop Interface**: Clean, accessible file upload with visual feedback
- **Local Processing**: Complete offline transcription using Apple Silicon optimization
- **Multi-language Support**: English and Filipino/Tagalog mixed audio support
- **Real-time Progress**: WebSocket-powered progress updates during transcription
- **Format Support**: M4A, MP3, WAV, AAC, MP4 audio file support
- **Accessibility**: Full WCAG 2.1 AA compliance with screen reader support
- **Responsive Design**: Mobile-first design with touch-friendly interface
- **Virtual Environment**: Isolated Python dependencies for clean installation

### Technical Features
- **FastAPI Backend**: Async web server with WebSocket support
- **whisper.cpp Integration**: Local AI transcription with Metal acceleration
- **FFmpeg Audio Processing**: Automatic format conversion for Whisper compatibility
- **Error Recovery**: Graceful error handling with retry capabilities
- **Setup Automation**: One-command setup script for dependencies and models

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.