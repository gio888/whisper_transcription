"""Integration tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app import app, active_batches, UPLOAD_DIR
from faker import Faker

fake = Faker()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_transcriber():
    """Mock the transcriber to avoid actual processing during tests."""
    with patch('app.transcriber') as mock:
        # Mock the transcribe_with_progress method
        async def mock_transcribe(*args, **kwargs):
            yield {"status": "processing", "progress": 50, "message": "Processing..."}
            yield {"status": "completed", "progress": 100, "transcript": "Test transcript", "output_file": "/test/output.txt"}
        
        mock.transcribe_with_progress = mock_transcribe
        yield mock


@pytest.fixture
def temp_audio_files():
    """Create temporary audio files for testing."""
    files = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            # Write some dummy content
            f.write(b"fake audio content " * 100)
            files.append(f.name)
    yield files
    # Cleanup
    for file in files:
        Path(file).unlink(missing_ok=True)


class TestBatchUpload:
    """Tests for batch upload endpoint."""
    
    def test_batch_upload_success(self, client, temp_audio_files):
        """Test successful batch file upload."""
        # Prepare files for upload
        files = []
        for file_path in temp_audio_files:
            with open(file_path, 'rb') as f:
                files.append(('files', (Path(file_path).name, f.read(), 'audio/mpeg')))
        
        # Upload files
        response = client.post("/batch-upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "batch_id" in data
        assert data["files_count"] == 3
        assert len(data["files"]) == 3
        
        # Verify files have correct structure
        for file_info in data["files"]:
            assert "id" in file_info
            assert "name" in file_info
            assert "size" in file_info
            assert file_info["status"] == "queued"
        
        # Verify batch is registered
        assert data["batch_id"] in active_batches
        
    def test_batch_upload_invalid_format(self, client):
        """Test batch upload with invalid file format."""
        # Create a text file (invalid format)
        files = [('files', ('test.txt', b'text content', 'text/plain'))]
        
        response = client.post("/batch-upload", files=files)
        
        assert response.status_code == 400
        assert "No valid files uploaded" in response.json()["detail"]
        
    def test_batch_upload_too_many_files(self, client):
        """Test batch upload with too many files."""
        # Create 51 files (over the limit)
        files = []
        for i in range(51):
            files.append(('files', (f'audio_{i}.mp3', b'content', 'audio/mpeg')))
        
        response = client.post("/batch-upload", files=files)
        
        assert response.status_code == 400
        assert "Too many files" in response.json()["detail"]
        
    def test_batch_upload_oversized_file(self, client):
        """Test batch upload with oversized file."""
        # Create a file larger than MAX_FILE_SIZE
        large_content = b'x' * (500 * 1024 * 1024 + 1)  # 500MB + 1 byte
        files = [('files', ('large.mp3', large_content, 'audio/mpeg'))]
        
        response = client.post("/batch-upload", files=files)
        
        # Should skip the oversized file
        assert response.status_code == 400
        assert "No valid files uploaded" in response.json()["detail"]
        
    def test_batch_upload_mixed_valid_invalid(self, client):
        """Test batch upload with mix of valid and invalid files."""
        files = [
            ('files', ('valid.mp3', b'audio content', 'audio/mpeg')),
            ('files', ('invalid.txt', b'text content', 'text/plain')),
            ('files', ('valid2.wav', b'audio content', 'audio/wav')),
        ]
        
        response = client.post("/batch-upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only upload valid files
        assert data["files_count"] == 2
        assert len(data["files"]) == 2
        
    def test_batch_upload_empty(self, client):
        """Test batch upload with no files."""
        response = client.post("/batch-upload", files=[])
        
        assert response.status_code == 422  # Validation error


class TestSingleUpload:
    """Tests for single file upload endpoint."""
    
    def test_single_upload_success(self, client):
        """Test successful single file upload."""
        content = b"fake audio content" * 1000
        files = {'file': ('test.mp3', content, 'audio/mpeg')}
        
        response = client.post("/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert data["filename"] == "test.mp3"
        assert data["size"] == len(content)
        
    def test_single_upload_invalid_format(self, client):
        """Test single upload with invalid format."""
        files = {'file': ('test.pdf', b'pdf content', 'application/pdf')}
        
        response = client.post("/upload", files=files)
        
        assert response.status_code == 400
        assert "Invalid file format" in response.json()["detail"]
        
    def test_single_upload_oversized(self, client):
        """Test single upload with oversized file."""
        large_content = b'x' * (500 * 1024 * 1024 + 1)  # 500MB + 1 byte
        files = {'file': ('large.mp3', large_content, 'audio/mpeg')}
        
        response = client.post("/upload", files=files)
        
        assert response.status_code == 400
        assert "File too large" in response.json()["detail"]


class TestFileValidation:
    """Tests for file validation logic."""
    
    @pytest.mark.parametrize("extension,should_pass", [
        (".mp3", True),
        (".wav", True),
        (".m4a", True),
        (".aac", True),
        (".ogg", True),
        (".flac", True),
        (".mp4", True),
        (".txt", False),
        (".pdf", False),
        (".exe", False),
        ("", False),
    ])
    def test_file_extension_validation(self, client, extension, should_pass):
        """Test validation of various file extensions."""
        filename = f"test{extension}" if extension else "test"
        files = {'file': (filename, b'content', 'application/octet-stream')}
        
        response = client.post("/upload", files=files)
        
        if should_pass:
            assert response.status_code == 200
        else:
            assert response.status_code == 400
            assert "Invalid file format" in response.json()["detail"]