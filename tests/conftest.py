"""Shared test fixtures and configuration."""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def setup_test_directories(tmp_path):
    """Create temporary directories for testing."""
    # Create temp upload and static dirs
    upload_dir = tmp_path / "uploads"
    static_dir = tmp_path / "static"
    upload_dir.mkdir()
    static_dir.mkdir()
    
    # Patch the directories in config
    with pytest.MonkeyPatch.context() as m:
        m.setattr("config.UPLOAD_DIR", upload_dir)
        m.setattr("config.STATIC_DIR", static_dir)
        m.setattr("app.UPLOAD_DIR", upload_dir)
        m.setattr("app.STATIC_DIR", static_dir)
        yield upload_dir, static_dir


@pytest.fixture
def mock_whisper_model():
    """Mock Whisper model to avoid loading during tests."""
    mock_model = MagicMock()
    mock_model.transcribe = MagicMock(return_value={"text": "Test transcription"})
    return mock_model


@pytest.fixture(autouse=True)
def mock_transcriber_init():
    """Mock transcriber initialization to avoid loading Whisper model."""
    with pytest.MonkeyPatch.context() as m:
        # Mock the WhisperTranscriber initialization
        class MockTranscriber:
            def __init__(self):
                self.model = None
                
            async def transcribe_with_progress(self, file_path, original_path=None):
                """Mock transcription with progress."""
                yield {"status": "processing", "progress": 0, "message": "Starting transcription..."}
                yield {"status": "processing", "progress": 50, "message": "Processing audio..."}
                yield {
                    "status": "completed",
                    "progress": 100,
                    "transcript": "This is a test transcription.",
                    "output_file": str(file_path).replace(".mp3", "_transcript.txt")
                }
        
        # Replace the transcriber module
        mock_transcriber = MockTranscriber()
        m.setattr("app.transcriber", mock_transcriber)
        m.setattr("transcriber.transcriber", mock_transcriber)
        yield mock_transcriber


@pytest.fixture
def create_test_audio_file():
    """Factory fixture to create test audio files."""
    created_files = []
    
    def _create_file(filename="test.mp3", size=1024):
        """Create a test audio file with specified name and size."""
        with tempfile.NamedTemporaryFile(suffix=filename, delete=False) as f:
            f.write(b"fake audio data " * (size // 16))
            created_files.append(f.name)
            return f.name
    
    yield _create_file
    
    # Cleanup
    for file in created_files:
        Path(file).unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def clear_active_batches():
    """Clear active batches before each test."""
    from app import active_batches, active_connections
    active_batches.clear()
    active_connections.clear()
    yield
    active_batches.clear()
    active_connections.clear()