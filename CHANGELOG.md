# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0] - 2025-01-16

### Added
- **🎯 Output Folder Selection**: Choose where to save transcripts using File System Access API
- **📁 Direct Folder Writing**: Transcripts save directly to chosen folder (Chrome/Edge)
- **📥 Download Fallback**: Automatic individual downloads for unsupported browsers
- **🚀 Manual Processing Start**: User controls when batch processing begins after folder selection

### Fixed
- **CRITICAL: WebSocket Hang**: Fixed batch processing hanging indefinitely waiting for file paths
- **Batch Flow**: Restored proper batch processing workflow with user-controlled start

### Technical
- **File System Access API**: Modern browser folder selection and writing capabilities
- **Enhanced WebSocket Protocol**: Includes transcript content in completion messages
- **Graceful Fallbacks**: Works across all browsers with appropriate feature detection

## [2.2.1] - 2025-01-16

### Fixed
- **Transcript Save Location**: Fixed transcripts saving to wrong location (uploads/ with UUID names instead of next to original files)
- **Corrupted File Detection**: Added file size validation and ffprobe checks to detect corrupted files early
- **Error Handling**: Improved batch processing error handling to skip corrupted files and continue processing
- **Original Path Integration**: Enhanced WebSocket protocol to receive and use original file paths properly

### Added
- **File Validation**: New `validate_audio_file()` method that checks file size and audio stream validity
- **Early Error Detection**: Corrupted files (like 13KB "moov atom not found" files) are now caught before processing
- **Path Communication**: WebSocket now receives original file paths from client for proper transcript placement

## [2.2.0] - 2025-01-16

### Fixed
- **CRITICAL: Batch Processing Hang**: Fixed async generator consumption bug that caused batch processing to hang indefinitely
- **Whisper Command**: Updated from deprecated `whisper-cpp` to `whisper-cli` 
- **Conversion Progress**: Fixed audio conversion progress not properly yielding, causing UI to show 100% while stuck
- **Timeout Protection**: Added proper timeout handling to prevent infinite waits during transcription
- **Debug Logging**: Enhanced logging to track actual progress and identify bottlenecks

### Added
- **Real Test Suite**: Created tests with ACTUAL audio files that catch real bugs (not theatrical mocks)
- **Reproducer Tests**: Added tests that specifically catch the hanging bug that wasted 12 hours
- **Test Data**: Added real .m4a audio files for testing (tests/test_data/)
- **Working Batch Test**: Comprehensive end-to-end batch processing test with real files

### Technical
- **Async Generator Fix**: Properly yield conversion status updates in transcribe_with_progress()
- **Process Timeout**: Added 5-second readline timeout and 1-hour total process timeout
- **Error Recovery**: Better error handling for conversion and transcription failures
- **Test Verification**: Tests now use real audio files and verify actual functionality

### Removed
- **Fake Tests**: Previous "comprehensive" tests that used mocked transcriber and fake data proved inadequate

## [2.1.0] - 2025-01-15

### Added
- **Comprehensive Test Suite**: Full testing infrastructure with pytest, preventing runtime errors
- **Smoke Test Script**: Quick 5-second validation before overnight batch processing
- **Unit Tests**: Data model serialization tests that catch JSON encoding issues
- **Integration Tests**: API endpoint validation for upload and batch processing
- **WebSocket Tests**: Real-time message serialization validation
- **Mock Transcriber**: Fast testing without actual Whisper processing
- **GitHub Actions CI**: Automated testing on every commit and pull request
- **Test Coverage Reporting**: HTML coverage reports with pytest-cov
- **Testing Documentation**: Complete testing guide with pre-deployment checklist

### Fixed
- **Critical Bug Fix**: PosixPath JSON serialization error in batch processing WebSocket messages
- **BatchFile Serialization**: Added proper `to_dict()` method to handle Path objects correctly
- **WebSocket Messages**: Fixed transcript_path serialization in file completion messages

### Technical
- **Test Dependencies**: Added pytest, pytest-asyncio, pytest-cov, httpx, pytest-mock, faker
- **Test Configuration**: pytest.ini with asyncio auto mode and coverage settings
- **CI/CD Pipeline**: Multi-version Python testing (3.10, 3.11, 3.12) with caching

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