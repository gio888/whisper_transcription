"""
Test that reproduces the exact hanging bug that wasted 12 hours.

This test uses REAL audio files and tests the ACTUAL async generator
consumption issue that caused batch processing to hang.
"""
import pytest
import asyncio
import time
from pathlib import Path
from unittest.mock import patch

from transcriber import transcriber


class TestHangingBugReproducer:
    """Tests that would have caught the hanging bug"""
    
    @pytest.fixture
    def real_audio_file(self):
        """Use REAL audio file, not fake data"""
        test_file = Path("tests/test_data/test1.m4a")
        if not test_file.exists():
            pytest.skip(f"Real test file not found: {test_file}")
        return test_file
    
    @pytest.mark.asyncio
    async def test_conversion_progress_yielding(self, real_audio_file):
        """
        Test that conversion actually yields progress updates.
        
        The original bug: conversion was called but never properly yielded,
        causing the UI to show 100% while still stuck in conversion.
        """
        progress_updates = []
        
        async def capture_progress(update):
            progress_updates.append(update)
        
        # This should yield conversion progress for .m4a files
        updates = []
        async for update in transcriber.transcribe_with_progress(
            real_audio_file, 
            progress_callback=capture_progress
        ):
            updates.append(update)
            
            # If we get a conversion update, break early (don't wait for full transcription)
            if update.get("status") == "converting" and update.get("progress") == 100:
                break
        
        # Verify we got conversion progress updates
        conversion_updates = [u for u in updates if u.get("status") == "converting"]
        assert len(conversion_updates) >= 2, f"Expected conversion start and end, got: {updates}"
        
        # Verify progress goes from 0 to 100
        assert any(u.get("progress") == 0 for u in conversion_updates), "No start progress"
        assert any(u.get("progress") == 100 for u in conversion_updates), "No completion progress"
    
    @pytest.mark.asyncio
    async def test_transcription_doesnt_hang_forever(self, real_audio_file):
        """
        Test that transcription doesn't hang indefinitely.
        
        The original bug: async generator wasn't properly consumed,
        causing infinite waiting.
        """
        start_time = time.time()
        timeout_seconds = 60  # Reasonable timeout for conversion + initial transcription
        
        try:
            # Use asyncio.wait_for to enforce timeout
            updates = []
            async def collect_updates():
                async for update in transcriber.transcribe_with_progress(real_audio_file):
                    updates.append(update)
                    # Break after we get transcription started (don't wait for full completion)
                    if update.get("status") == "transcribing" and update.get("progress", 0) > 0:
                        break
                return updates
            
            updates = await asyncio.wait_for(collect_updates(), timeout=timeout_seconds)
            
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            pytest.fail(f"Transcription hung for {elapsed:.1f} seconds - this is the bug!")
        
        elapsed = time.time() - start_time
        assert elapsed < timeout_seconds, f"Took too long: {elapsed:.1f}s"
        
        # Verify we got some progress
        assert len(updates) > 0, "No progress updates received"
        assert any(u.get("status") in ["converting", "transcribing"] for u in updates), \
            f"No valid status updates: {updates}"
    
    @pytest.mark.asyncio 
    async def test_batch_processing_simulation(self, real_audio_file):
        """
        Test the exact pattern that failed in batch processing.
        
        This simulates how app.py consumes the async generator.
        """
        # Create a second test file by copying the first
        test_file_2 = Path("tests/test_data/test_batch.m4a")
        if not test_file_2.exists():
            import shutil
            shutil.copy(real_audio_file, test_file_2)
        
        files_to_process = [real_audio_file, test_file_2]
        all_updates = []
        
        start_time = time.time()
        timeout_per_file = 45  # Reasonable timeout per file
        
        for i, file_path in enumerate(files_to_process):
            file_start_time = time.time()
            file_updates = []
            
            try:
                # This is the exact pattern from app.py that was hanging
                async for update in transcriber.transcribe_with_progress(file_path):
                    file_updates.append(update)
                    all_updates.append({**update, "file_index": i})
                    
                    # Check if file processing is done
                    if update.get("status") == "completed":
                        break
                    elif update.get("status") == "error":
                        break
                    
                    # Timeout protection per file
                    if time.time() - file_start_time > timeout_per_file:
                        pytest.fail(f"File {i} hung for {timeout_per_file}s")
                        
            except Exception as e:
                # Clean up the copied file
                if test_file_2.exists():
                    test_file_2.unlink()
                raise
        
        # Clean up
        if test_file_2.exists():
            test_file_2.unlink()
        
        total_elapsed = time.time() - start_time
        
        # Verify we processed both files
        file_0_updates = [u for u in all_updates if u.get("file_index") == 0]
        file_1_updates = [u for u in all_updates if u.get("file_index") == 1]
        
        assert len(file_0_updates) > 0, "No updates for file 0"
        assert len(file_1_updates) > 0, "No updates for file 1"
        
        # Verify we got conversion progress for both
        file_0_converting = [u for u in file_0_updates if u.get("status") == "converting"]
        file_1_converting = [u for u in file_1_updates if u.get("status") == "converting"]
        
        assert len(file_0_converting) > 0, "No conversion updates for file 0"
        assert len(file_1_converting) > 0, "No conversion updates for file 1"
        
        print(f"✅ Batch processing completed in {total_elapsed:.1f}s")
        print(f"File 0: {len(file_0_updates)} updates")
        print(f"File 1: {len(file_1_updates)} updates")


class TestWithBrokenCode:
    """Tests using the old broken transcriber code to verify they fail"""
    
    @pytest.mark.asyncio
    async def test_broken_code_hangs(self):
        """
        This test should FAIL on the original broken code.
        If this passes, the test isn't detecting the bug.
        """
        # This would hang with the original code
        # TODO: Run this against the original broken transcriber to verify it fails
        pass