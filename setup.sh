#!/bin/bash

echo "🚀 Setting up Whisper Transcription Service..."

# Check if whisper-cli is installed (from whisper-cpp package)
if ! command -v whisper-cli &> /dev/null; then
    echo "❌ whisper-cli not found. Please install whisper-cpp first:"
    echo "   brew install whisper-cpp"
    echo "   Note: The command is now 'whisper-cli', not 'whisper-cpp'"
    exit 1
fi

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg not found. Please install it first:"
    echo "   brew install ffmpeg"
    exit 1
fi

# Create necessary directories
mkdir -p models uploads static

# Create Python virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment. Make sure python3-venv is installed:"
        echo "   On macOS: This should work by default"
        echo "   On Ubuntu/Debian: sudo apt install python3-venv"
        exit 1
    fi
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip in virtual environment
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Download the small model (better for multilingual)
if [ ! -f "models/small.bin" ]; then
    echo "📥 Downloading Whisper small model (461MB)..."
    echo "   This provides better accuracy for English/Filipino mixed audio"
    curl -L -o models/small.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin
    
    if [ $? -eq 0 ]; then
        echo "✅ Model downloaded successfully"
    else
        echo "❌ Failed to download model. Trying alternative source..."
        curl -L -o models/small.bin https://ggml.ggerganov.com/ggml-model-whisper-small.bin
    fi
else
    echo "✅ Model already exists"
fi

# Install Python dependencies in virtual environment
echo "📦 Installing Python dependencies in virtual environment..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies."
    echo "   Please check the error messages above."
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Virtual environment created at: ./venv"
echo "Dependencies installed in isolated environment"
echo ""
echo "To start the service, run:"
echo "   ./run.sh"
echo ""
echo "Then open http://localhost:8000 in your browser"