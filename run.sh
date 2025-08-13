#!/bin/bash

echo "🎙️ Starting Whisper Transcription Service..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run ./setup.sh first to set up the environment."
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Verify activation
if [ "$VIRTUAL_ENV" != "" ]; then
    echo "✅ Virtual environment activated: $VIRTUAL_ENV"
else
    echo "⚠️  Warning: Virtual environment may not be properly activated"
    echo "   Continuing anyway..."
fi

echo ""
echo "🌐 Server: http://localhost:8000"
echo "📊 Processing speed ≈ audio duration (1 hour audio ≈ 1 hour processing)"
echo "⌨️  Press Ctrl+C to stop"
echo ""

# Run the FastAPI server using the venv Python
python app.py