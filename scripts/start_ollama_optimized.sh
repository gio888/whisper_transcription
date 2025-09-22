#!/bin/bash

# Optimized Ollama Configuration for Meeting Analysis
# This script starts Ollama with settings optimized for local LLM performance

echo "🚀 Starting Ollama with optimized configuration for meeting analysis..."

# Ollama Performance Optimizations
export OLLAMA_NUM_PARALLEL=1              # Prevent memory competition between requests
export OLLAMA_CONTEXT_LENGTH=16384        # Increase context window (balanced performance/memory)
export OLLAMA_KEEP_ALIVE=30m              # Keep model loaded for 30 minutes to prevent reloading
export OLLAMA_MAX_LOADED_MODELS=1         # Load only one model at a time for memory efficiency
export OLLAMA_LOAD_TIMEOUT=10m            # Allow more time for model loading
export OLLAMA_DEBUG=INFO                  # Keep info level logging
export OLLAMA_MAX_QUEUE=128               # Reduce queue size to prevent memory issues

# GPU/Memory Optimizations (for Apple Silicon)
export OLLAMA_GPU_OVERHEAD=0              # No additional GPU overhead
export OLLAMA_FLASH_ATTENTION=true        # Enable flash attention for better performance

echo "📊 Ollama Configuration:"
echo "  - Parallel requests: $OLLAMA_NUM_PARALLEL"
echo "  - Context length: $OLLAMA_CONTEXT_LENGTH"
echo "  - Keep alive: $OLLAMA_KEEP_ALIVE"
echo "  - Max loaded models: $OLLAMA_MAX_LOADED_MODELS"
echo "  - Load timeout: $OLLAMA_LOAD_TIMEOUT"
echo "  - Flash attention: $OLLAMA_FLASH_ATTENTION"

# Start Ollama server
echo "🔧 Starting Ollama server with optimizations..."
ollama serve