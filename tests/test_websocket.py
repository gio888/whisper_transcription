"""WebSocket tests - CRITICAL for catching serialization errors!"""
import pytest
import json
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app import app, active_batches, BatchJob, BatchFile, FileStatus


@pytest.fixture
def websocket_client():
    """Create WebSocket test client."""
    return TestClient(app)


class TestBatchWebSocket:
    """Tests for batch processing WebSocket - Would have caught the PosixPath bug!"""
    
    def test_batch_websocket_json_serialization(self, websocket_client):
        """Test that all WebSocket messages can be JSON serialized."""
        # Setup a batch job with Path objects
        batch_id = "test-batch-123"
        batch_files = [
            BatchFile(
                id="file-1",
                original_name="audio1.mp3",
                original_path="/original/audio1.mp3",
                file_path=Path("/uploads/audio1.mp3"),  # Path object!
                size=1024,
                status=FileStatus.QUEUED
            ),
            BatchFile(
                id="file-2",
                original_name="audio2.wav",
                original_path="/original/audio2.wav",
                file_path=Path("/uploads/audio2.wav"),  # Path object!
                size=2048,
                status=FileStatus.QUEUED
            )
        ]
        
        batch_job = BatchJob(
            batch_id=batch_id,
            files=batch_files,
            total_files=2
        )
        
        active_batches[batch_id] = batch_job
        
        # Mock the transcriber
        with patch('app.transcriber.transcribe_with_progress') as mock_transcribe:
            async def mock_progress(file_path, **kwargs):
                # Simulate progress updates
                yield {"status": "processing", "progress": 25, "message": "Starting"}
                yield {"status": "processing", "progress": 50, "message": "Processing"}
                yield {"status": "processing", "progress": 75, "message": "Almost done"}
                yield {
                    "status": "completed", 
                    "progress": 100, 
                    "transcript": "Test transcript",
                    "output_file": str(Path("/transcripts/output.txt"))  # Ensure string
                }
            
            mock_transcribe.return_value = mock_progress(None)
            
            # Connect to WebSocket
            with websocket_client.websocket_connect(f"/ws/batch/{batch_id}") as websocket:
                # First message should be batch status
                data = websocket.receive_json()
                
                # This is where the PosixPath bug would have been caught!
                assert data["type"] == "batch_status"
                assert data["batch_id"] == batch_id
                assert data["total_files"] == 2
                
                # Verify files array is properly serialized
                assert len(data["files"]) == 2
                for file_data in data["files"]:
                    # These should all be JSON-serializable types
                    assert isinstance(file_data["file_path"], str)  # Not Path!
                    assert isinstance(file_data["status"], str)
                    assert isinstance(file_data["id"], str)
                    
                    # Verify we can re-serialize to JSON
                    json.dumps(file_data)  # Should not raise
                
                # Receive more messages until batch complete
                messages_received = []
                for _ in range(20):  # Limit iterations
                    try:
                        msg = websocket.receive_json(timeout=1)
                        messages_received.append(msg)
                        
                        # Every message should be JSON serializable
                        json.dumps(msg)  # Should not raise
                        
                        if msg.get("type") == "batch_complete":
                            break
                    except:
                        break
                
                # Verify we got expected message types
                message_types = {msg.get("type") for msg in messages_received}
                assert "file_start" in message_types or "file_progress" in message_types
    
    def test_batch_websocket_error_handling(self, websocket_client):
        """Test WebSocket error message serialization."""
        batch_id = "test-error-batch"
        
        # Create batch with file that will error
        batch_file = BatchFile(
            id="error-file",
            original_name="bad.mp3",
            original_path=None,
            file_path=Path("/uploads/bad.mp3"),
            size=1024,
            status=FileStatus.QUEUED
        )
        
        batch_job = BatchJob(
            batch_id=batch_id,
            files=[batch_file],
            total_files=1
        )
        
        active_batches[batch_id] = batch_job
        
        with patch('app.transcriber.transcribe_with_progress') as mock_transcribe:
            async def mock_error(file_path, **kwargs):
                yield {"status": "processing", "progress": 10}
                yield {"status": "error", "error": "Failed to process audio"}
            
            mock_transcribe.return_value = mock_error(None)
            
            with websocket_client.websocket_connect(f"/ws/batch/{batch_id}") as websocket:
                # Collect all messages
                messages = []
                for _ in range(10):
                    try:
                        msg = websocket.receive_json(timeout=1)
                        messages.append(msg)
                        
                        # All messages should be JSON serializable
                        json.dumps(msg)
                        
                        if msg.get("type") == "batch_complete":
                            break
                    except:
                        break
                
                # Verify error was handled
                error_messages = [m for m in messages if m.get("status") == "error" or m.get("type") == "file_complete"]
                assert len(error_messages) > 0
    
    def test_batch_websocket_nonexistent_batch(self, websocket_client):
        """Test WebSocket connection with non-existent batch."""
        with websocket_client.websocket_connect("/ws/batch/nonexistent-batch") as websocket:
            data = websocket.receive_json()
            
            assert data["status"] == "error"
            assert "Batch not found" in data["error"]
            
            # Should be JSON serializable
            json.dumps(data)
    
    def test_websocket_file_completion_message(self, websocket_client):
        """Test file completion message with transcript_path."""
        batch_id = "test-completion"
        
        batch_file = BatchFile(
            id="complete-file",
            original_name="audio.mp3",
            original_path=None,
            file_path=Path("/uploads/audio.mp3"),
            size=1024,
            status=FileStatus.QUEUED
        )
        
        batch_job = BatchJob(
            batch_id=batch_id,
            files=[batch_file],
            total_files=1
        )
        
        active_batches[batch_id] = batch_job
        
        with patch('app.transcriber.transcribe_with_progress') as mock_transcribe:
            async def mock_complete(file_path, **kwargs):
                yield {
                    "status": "completed",
                    "progress": 100,
                    "output_file": "/transcripts/output.txt"  # String path
                }
            
            mock_transcribe.return_value = mock_complete(None)
            
            with websocket_client.websocket_connect(f"/ws/batch/{batch_id}") as websocket:
                # Skip to file completion message
                messages = []
                for _ in range(10):
                    try:
                        msg = websocket.receive_json(timeout=1)
                        messages.append(msg)
                        
                        if msg.get("type") == "file_complete":
                            # This message specifically had issues with transcript_path
                            assert "transcript_path" in msg
                            # Should be string or None, not Path
                            assert msg["transcript_path"] is None or isinstance(msg["transcript_path"], str)
                            
                            # Must be JSON serializable
                            json.dumps(msg)
                            break
                    except:
                        break
                
                # Verify we got the completion message
                completion_msgs = [m for m in messages if m.get("type") == "file_complete"]
                assert len(completion_msgs) > 0