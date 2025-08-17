# CLAUDE.md - Architecture Guide for Whisper Transcription Service

This file provides high-level architecture guidance for Claude Code instances working in this repository. Focus on system-wide understanding that requires knowledge of multiple files.

## 🛠️ Common Commands

### Setup & Development
```bash
# Initial setup (downloads Whisper model + creates venv)
./setup.sh

# Start development server
./run.sh

# Quick validation before overnight batch processing
python smoke_test.py

# Full test suite with real audio files
pytest -v

# Activate virtual environment manually
source venv/bin/activate
```

### Testing Commands
```bash
# CRITICAL: Always run before batch processing
python smoke_test.py  # 5-second test catches major issues

# Real file testing (not mocks)
pytest tests/test_working_batch.py -v
pytest tests/test_hanging_bug_reproducer.py -v

# Test with actual audio files
pytest tests/test_data/  # Contains real .m4a files
```

### Debugging Commands
```bash
# Monitor WebSocket connections
lsof -i :8000

# Check whisper-cli installation
whisper-cli --help

# Validate audio files
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 audio.m4a

# Check virtual environment
echo $VIRTUAL_ENV
```

## 🏗️ High-Level Architecture

### Multi-Component Real-Time System
This is NOT a simple transcription script. It's a **real-time web application** with:

1. **FastAPI Backend** (`app.py`): Async server with WebSocket support
2. **WebSocket Streaming** (`/ws/` endpoints): Real-time progress updates
3. **File System Access API** (`static/app.js`): Modern browser folder selection
4. **Local AI Processing** (`transcriber.py`): Whisper.cpp integration
5. **Batch Management** (`BatchJob`/`BatchFile` classes): Sequential processing

### Critical WebSocket Architecture

**Two Separate WebSocket Endpoints:**
- `/ws/{session_id}` - Single file transcription
- `/ws/batch/{batch_id}` - Batch processing with progress aggregation

**WebSocket Message Types in Batch Processing:**
```python
# app.py:338-346 - Initial batch status
{"type": "batch_status", "total_files": N, "completed_files": 0...}

# app.py:357-362 - File start notification  
{"type": "file_start", "file_id": "...", "file_name": "..."}

# app.py:375-378 - Real-time progress updates
{"type": "file_progress", "file_id": "...", "progress": 45, "status": "transcribing"}

# app.py:408-424 - File completion with transcript content
{"type": "file_complete", "file_id": "...", "transcript": "..."}
```

### Real-Time File Saving Architecture

**Client-Side Folder Selection** (`static/app.js:782-807`):
- Uses File System Access API (`showDirectoryPicker()`)
- Non-blocking: user can select folder while processing continues
- Individual file saving: `app.js:837-874` saves each transcript immediately
- Fallback: downloads if folder selection unavailable/fails

**Folder Persistence** (`static/app.js:68-261`):
- IndexedDB storage for FileSystemDirectoryHandle objects
- Automatic restoration on page load with permission checking
- One-click re-authorization for expired permissions
- Clear folder option to reset saved selection

**Key UI Elements** (`static/index.html:96-114`):
```html
<div id="processingFolderSection">  <!-- Shows during batch processing -->
  <button id="chooseFolderBtn">📁 Choose Folder</button>
  <div id="selectedFolder">...</div>
</div>
```

## 🔧 Critical Technical Concepts

### Async Generator Pattern (`transcriber.py:112-291`)
The transcription uses Python async generators for streaming progress:
```python
async def transcribe_with_progress(audio_path) -> AsyncGenerator[dict, None]:
    yield {"status": "validating", "progress": 0}
    yield {"status": "converting", "progress": 50}  
    yield {"status": "transcribing", "progress": 80}
    yield {"status": "completed", "transcript": "..."}
```

### Audio File Validation (`transcriber.py:69-111`)
**CRITICAL**: Files are validated before processing to catch corrupted files:
- File size validation (rejects <1KB files)
- FFprobe structural validation
- Audio stream verification
- Prevents "moov atom not found" errors that waste processing time

### Batch Processing State Management (`app.py:58-104`)
```python
@dataclass
class BatchFile:
    id: str                    # UUID for tracking
    original_name: str         # Display name
    original_path: str         # For saving transcript next to source
    status: FileStatus         # QUEUED -> PROCESSING -> COMPLETED/ERROR
    transcript_path: str       # Final output location
```

## ⚠️ Critical Bug History & Lessons

### WebSocket Hanging Bug (Fixed in v2.3.0)
**Problem**: Batch processing hung indefinitely waiting for file paths from client
**Root Cause**: Complex `waiting_for_paths` logic in WebSocket handler
**Solution**: Removed path waiting, start processing immediately (`app.py:281-282`)
**Key Learning**: Simple workflow beats complex coordination

### Browser Caching Issues
**Problem**: Updated JavaScript not loading, causing missing UI elements
**Root Cause**: Browser caching prevents code updates during development
**Solution**: Hard refresh (Cmd+Shift+R) to bypass cache
**Debug Tool**: Added extensive console logging (`static/app.js:46-48`, `258-267`)

### Testing Philosophy: Real vs Theatrical
**Problem**: "Comprehensive" tests with mocks missed critical bugs
**Solution**: Tests now use actual audio files (`tests/test_data/*.m4a`)
**Key Files**: 
- `tests/test_working_batch.py` - End-to-end batch test
- `tests/test_hanging_bug_reproducer.py` - Catches WebSocket hanging
- `smoke_test.py` - 5-second validation before overnight batches

## 📁 Key File Relationships

### Core Processing Flow
1. **Upload**: `app.py:149-221` handles multi-file upload
2. **WebSocket**: `app.py:266-294` accepts connection, starts `process_batch()`
3. **Sequential Processing**: `app.py:323-434` processes files one by one
4. **Real-Time Progress**: `transcriber.py:112-291` yields progress updates
5. **Client Saving**: `static/app.js:668-707` saves completed files

### UI State Management (`static/app.js`)
```javascript
// Key state variables (lines 50-57)
this.outputFolderHandle = null;        // File System Access API handle
this.isBatchMode = false;              // Single vs batch processing
this.batchFiles = [];                  // File tracking array
this.currentBatchId = null;            // WebSocket session ID

// Critical UI sections
this.processingFolderSection           // Folder selection during processing
this.batchSection                      // Batch progress display
this.fileQueue                         // Individual file status list
```

### Configuration & Dependencies
- `config.py`: Whisper model settings, file limits, directories
- `requirements.txt`: Python dependencies for production
- `requirements-test.txt`: Additional test dependencies
- `setup.sh`: Model download + venv creation
- `run.sh`: Server startup with venv activation

## 🔍 Development Workflow

### Before Making Changes
1. **Run smoke test**: `python smoke_test.py` (5 seconds)
2. **Check virtual environment**: `echo $VIRTUAL_ENV`
3. **Review recent changes**: `git log --oneline -10`

### Testing Changes
1. **Real file testing**: Use `tests/test_data/*.m4a` for validation
2. **WebSocket testing**: Test both single and batch endpoints
3. **Browser caching**: Hard refresh to see JavaScript changes
4. **Error handling**: Test with corrupted files

### Common Issues & Solutions

**Missing UI Elements**: Hard refresh browser cache
**WebSocket Hanging**: Check `process_batch()` logic, ensure no blocking waits
**File Saving Fails**: Verify File System Access API support in browser
**Transcription Errors**: Validate audio with `ffprobe` first
**Virtual Environment**: Ensure `source venv/bin/activate` before running

### Important Code Sections
- `app.py:323-434` - Batch processing logic (sequential file handling)
- `static/app.js:164-196` - Batch upload and UI switching
- `static/app.js:350-392` - WebSocket message handling
- `static/app.js:617-707` - Folder selection and file saving
- `transcriber.py:112-291` - Core transcription with progress streaming

## 🎯 Key Success Patterns

1. **Real Testing**: Always test with actual audio files, not mocks
2. **Sequential Processing**: Process files one at a time to prevent system overload
3. **Progressive Saving**: Save files immediately as they complete
4. **Non-Blocking UX**: Let users select output folder while processing continues
5. **Graceful Degradation**: Download files individually if folder selection fails
6. **Comprehensive Validation**: Check file integrity before processing

---

**Architecture Summary**: Multi-component real-time system with WebSocket streaming, client-side file management, and local AI processing. Focus on the interaction between async generators, WebSocket messaging, and browser APIs rather than individual file operations.