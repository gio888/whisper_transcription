# Whisper Transcription Web Service

Simple drag-and-drop web interface for transcribing M4A files using whisper.cpp locally on your Mac.

## Features
- 🎯 Drag-and-drop M4A files directly in browser
- 🌐 Supports English and Filipino/Tagalog mixed audio
- 📊 Real-time transcription progress
- 💾 Download transcripts as text files
- 🔒 Fully local - no cloud services required
- ⚡ Optimized for Apple Silicon

## Prerequisites
```bash
# Install whisper.cpp
brew install whisper-cpp

# Install ffmpeg for audio conversion
brew install ffmpeg
```

## Setup
```bash
# 1. Run setup script (downloads model, installs dependencies)
./setup.sh

# 2. Start the service
./run.sh

# 3. Open browser to http://localhost:8000
```

## Usage
1. Open http://localhost:8000 in your browser
2. Drag and drop your M4A file onto the upload zone
3. Watch real-time progress as it transcribes
4. Download the completed transcript

## Supported Formats
- M4A (primary)
- MP3, WAV, AAC, MP4

## Technical Details
- Backend: FastAPI with WebSocket support
- Model: Whisper small.bin (461MB, multilingual)
- Processing: whisper.cpp with Metal acceleration
- Max file size: 500MB

## Troubleshooting

### If transcription shows Spanish instead of Filipino:
The model is correctly configured to expect English with Filipino/Tagalog. This is handled automatically.

### If the service won't start:
```bash
# Check if port 8000 is in use
lsof -i :8000

# Install Python dependencies manually
pip3 install fastapi uvicorn python-multipart websockets aiofiles
```

### For long audio files:
Processing time is approximately 1:1 with audio length on M1/M2 Macs (1 hour audio = ~1 hour processing)