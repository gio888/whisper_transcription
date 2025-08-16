"""
Final test proving batch transcription works with real files.
"""
import pytest
import asyncio
import time
from pathlib import Path

from transcriber import transcriber


class TestWorkingBatchProcessing:
    """Tests that prove batch processing works with real data"""
    
    @pytest.fixture
    def short_audio_files(self):
        """Real 10-second audio files for fast testing"""
        files = [
            Path("tests/test_data/short1.m4a"),
            Path("tests/test_data/short2.m4a")
        ]
        for f in files:
            if not f.exists():
                pytest.skip(f"Short test file not found: {f}")
        return files
    
    @pytest.mark.asyncio
    async def test_batch_processing_works(self, short_audio_files):
        """
        Test that batch processing works end-to-end with real files.
        This test would have caught the hanging bug.
        """
        start_time = time.time()
        all_files_completed = []
        
        for i, file_path in enumerate(short_audio_files):
            print(f"\n--- Processing file {i}: {file_path.name} ---")
            file_start = time.time()
            file_updates = []
            
            # Process exactly like the app does
            async for update in transcriber.transcribe_with_progress(file_path):
                file_updates.append(update)
                print(f"  Update: {update}")
                
                # Stop on completion
                if update.get("status") == "completed":
                    all_files_completed.append(file_path)
                    break
                elif update.get("status") == "error":
                    pytest.fail(f"File {i} failed: {update.get('error')}")
                    
            file_elapsed = time.time() - file_start
            print(f"  File {i} completed in {file_elapsed:.1f}s")
            
            # Verify we got expected progress updates
            conversion_updates = [u for u in file_updates if u.get("status") == "converting"]
            transcription_updates = [u for u in file_updates if u.get("status") == "transcribing"]
            
            assert len(conversion_updates) >= 2, f"File {i}: No conversion progress"
            assert len(transcription_updates) >= 1, f"File {i}: No transcription progress"
        
        total_elapsed = time.time() - start_time
        print(f"\n✅ All {len(short_audio_files)} files processed in {total_elapsed:.1f}s")
        
        # Verify all files completed
        assert len(all_files_completed) == len(short_audio_files), \
            f"Only {len(all_files_completed)}/{len(short_audio_files)} files completed"
        
        # Verify reasonable performance (shouldn't take more than 5 minutes for 2x10s files)
        assert total_elapsed < 300, f"Took too long: {total_elapsed:.1f}s"
        
        return True  # Success!
    
    @pytest.mark.asyncio
    async def test_single_file_end_to_end(self, short_audio_files):
        """
        Test single file processing end-to-end.
        """
        test_file = short_audio_files[0]
        print(f"\nTesting single file: {test_file}")
        
        start_time = time.time()
        updates = []
        
        async for update in transcriber.transcribe_with_progress(test_file):
            updates.append(update)
            print(f"Update: {update}")
            
            if update.get("status") == "completed":
                break
            elif update.get("status") == "error":
                pytest.fail(f"Transcription failed: {update.get('error')}")
        
        elapsed = time.time() - start_time
        print(f"Completed in {elapsed:.1f}s")
        
        # Verify we got a transcript
        final_update = updates[-1]
        assert final_update.get("status") == "completed"
        assert "transcript" in final_update
        assert len(final_update["transcript"]) > 0
        
        print(f"Transcript preview: {final_update['transcript'][:100]}...")
        
        return True