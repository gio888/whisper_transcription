"""Unit tests for data models and serialization."""
import json
from pathlib import Path
import pytest
from app import BatchFile, BatchJob, FileStatus


class TestBatchFileSerialization:
    """Tests for BatchFile model - this would have caught the PosixPath bug!"""
    
    def test_batch_file_to_dict_with_path_object(self):
        """Test that BatchFile.to_dict() properly serializes Path objects."""
        # Create a BatchFile with a Path object
        batch_file = BatchFile(
            id="test-123",
            original_name="test_audio.mp3",
            original_path="/original/path/test_audio.mp3",
            file_path=Path("/uploads/test_audio.mp3"),  # This is a Path object!
            size=1024,
            status=FileStatus.QUEUED
        )
        
        # Convert to dict
        file_dict = batch_file.to_dict()
        
        # This should NOT raise TypeError about PosixPath not being JSON serializable
        json_str = json.dumps(file_dict)
        
        # Verify the structure
        assert file_dict["id"] == "test-123"
        assert file_dict["original_name"] == "test_audio.mp3"
        assert file_dict["file_path"] == "/uploads/test_audio.mp3"  # Should be string, not Path
        assert file_dict["status"] == "queued"
        assert file_dict["progress"] == 0
        
    def test_batch_file_to_dict_with_transcript_path(self):
        """Test that transcript_path is properly handled."""
        batch_file = BatchFile(
            id="test-456",
            original_name="test_audio.mp3",
            original_path=None,
            file_path=Path("/uploads/test_audio.mp3"),
            size=2048,
            status=FileStatus.COMPLETED,
            transcript_path="/transcripts/test_audio_transcript.txt"
        )
        
        file_dict = batch_file.to_dict()
        json_str = json.dumps(file_dict)  # Should not raise
        
        assert file_dict["transcript_path"] == "/transcripts/test_audio_transcript.txt"
        assert file_dict["status"] == "completed"
        
    def test_batch_file_to_dict_with_error(self):
        """Test serialization with error state."""
        batch_file = BatchFile(
            id="test-789",
            original_name="bad_file.wav",
            original_path=None,
            file_path=Path("/uploads/bad_file.wav"),
            size=512,
            status=FileStatus.ERROR,
            error_message="Failed to process: Invalid format"
        )
        
        file_dict = batch_file.to_dict()
        json_str = json.dumps(file_dict)  # Should not raise
        
        assert file_dict["status"] == "error"
        assert file_dict["error_message"] == "Failed to process: Invalid format"
        
    def test_batch_file_all_statuses(self):
        """Test all FileStatus enum values serialize correctly."""
        for status in FileStatus:
            batch_file = BatchFile(
                id=f"test-{status.value}",
                original_name="test.mp3",
                original_path=None,
                file_path=Path("/uploads/test.mp3"),
                size=1024,
                status=status
            )
            
            file_dict = batch_file.to_dict()
            json_str = json.dumps(file_dict)  # Should not raise
            assert file_dict["status"] == status.value


class TestBatchJob:
    """Tests for BatchJob model."""
    
    def test_batch_job_with_multiple_files(self):
        """Test BatchJob with multiple BatchFile objects."""
        files = [
            BatchFile(
                id=f"file-{i}",
                original_name=f"audio_{i}.mp3",
                original_path=None,
                file_path=Path(f"/uploads/audio_{i}.mp3"),
                size=1024 * (i + 1),
                status=FileStatus.QUEUED
            )
            for i in range(3)
        ]
        
        batch_job = BatchJob(
            batch_id="batch-123",
            files=files,
            total_files=3
        )
        
        # Test that all files can be serialized
        for file in batch_job.files:
            file_dict = file.to_dict()
            json_str = json.dumps(file_dict)  # Should not raise
            
        assert batch_job.total_files == 3
        assert batch_job.completed_files == 0
        assert batch_job.failed_files == 0
        assert batch_job.current_file_index == 0
        assert batch_job.is_processing == False