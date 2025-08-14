import asyncio
import subprocess
import tempfile
import os
import re
from pathlib import Path
from typing import Optional, AsyncGenerator
import logging

from config import WHISPER_CONFIG, UPLOAD_DIR

logger = logging.getLogger(__name__)

class WhisperTranscriber:
    def __init__(self):
        self.whisper_executable = "whisper-cpp"
        self.ffmpeg_executable = "ffmpeg"
        
    async def convert_to_wav(self, input_path: Path) -> Path:
        """Convert audio file to WAV format required by whisper.cpp"""
        output_path = UPLOAD_DIR / f"{input_path.stem}_converted.wav"
        
        cmd = [
            self.ffmpeg_executable,
            "-i", str(input_path),
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            "-y",
            str(output_path)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg conversion failed: {stderr.decode()}")
            
        return output_path
    
    async def get_duration(self, file_path: Path) -> float:
        """Get audio duration in seconds"""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        try:
            return float(stdout.decode().strip())
        except:
            return 0.0
    
    async def transcribe_with_progress(
        self, 
        audio_path: Path,
        progress_callback: Optional[callable] = None,
        original_path: Optional[str] = None
    ) -> AsyncGenerator[dict, None]:
        """Transcribe audio file with progress updates
        
        Args:
            audio_path: Path to the uploaded audio file
            progress_callback: Optional callback for progress updates
            original_path: Original file path to save transcript next to source file
        """
        
        # Convert to WAV if needed
        if audio_path.suffix.lower() != ".wav":
            logger.info(f"Converting {audio_path.suffix} to WAV...")
            if progress_callback:
                await progress_callback({"status": "converting", "progress": 0})
            wav_path = await self.convert_to_wav(audio_path)
            if progress_callback:
                await progress_callback({"status": "converting", "progress": 100})
        else:
            wav_path = audio_path
        
        # Get duration for progress calculation
        duration = await self.get_duration(wav_path)
        
        # Determine output file location
        if original_path:
            # Save transcript next to original file
            original_file_path = Path(original_path)
            output_txt = original_file_path.parent / f"{original_file_path.stem}.txt"
            logger.info(f"Saving transcript to original location: {output_txt}")
        else:
            # Default behavior: save in upload directory
            output_txt = UPLOAD_DIR / f"{audio_path.stem}_transcript.txt"
        
        # Build whisper command
        cmd = [
            self.whisper_executable,
            "--model", WHISPER_CONFIG["model"],
            "--file", str(wav_path),
            "--language", WHISPER_CONFIG["language"],
            "--threads", str(WHISPER_CONFIG["threads"]),
            "--processors", str(WHISPER_CONFIG["processors"]),
            "--output-txt",
            "--output-file", str(output_txt.with_suffix("")),
            "--print-progress"
        ]
        
        # Run whisper
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Parse progress from stderr
        last_progress = 0
        while True:
            line = await process.stderr.readline()
            if not line:
                break
                
            line_text = line.decode('utf-8', errors='ignore')
            
            # Parse progress indicators
            if "whisper_full" in line_text or "progress" in line_text:
                # Extract percentage if available
                match = re.search(r'(\d+)%', line_text)
                if match:
                    progress = int(match.group(1))
                    if progress > last_progress:
                        last_progress = progress
                        yield {
                            "status": "transcribing",
                            "progress": progress,
                            "message": f"Transcribing... {progress}%"
                        }
            
            # Check for timing info
            if "[" in line_text and "]" in line_text:
                # Extract timestamp from transcription output
                match = re.search(r'\[(\d{2}:\d{2}:\d{2}\.\d{3})', line_text)
                if match and duration > 0:
                    timestamp = match.group(1)
                    # Convert timestamp to seconds
                    parts = timestamp.split(':')
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                    progress = min(int((seconds / duration) * 100), 99)
                    yield {
                        "status": "transcribing",
                        "progress": progress,
                        "message": f"Processing audio... {progress}%"
                    }
        
        await process.wait()
        
        # Clean up temporary WAV if we converted
        if wav_path != audio_path and wav_path.exists():
            wav_path.unlink()
        
        # Read final transcript
        temp_output = UPLOAD_DIR / f"{audio_path.stem}_transcript.txt"
        
        if temp_output.exists():
            with open(temp_output, 'r', encoding='utf-8') as f:
                transcript = f.read()
            
            # If we need to save to original location, copy the file there
            final_output_path = temp_output
            if original_path and output_txt != temp_output:
                try:
                    # Ensure the original directory exists
                    output_txt.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy transcript to original location
                    with open(output_txt, 'w', encoding='utf-8') as f:
                        f.write(transcript)
                    
                    final_output_path = output_txt
                    logger.info(f"Transcript saved to: {output_txt}")
                    
                except Exception as e:
                    logger.error(f"Failed to save transcript to original location: {e}")
                    # Fall back to temp location if original save fails
                    pass
            
            yield {
                "status": "completed",
                "progress": 100,
                "transcript": transcript,
                "output_file": str(final_output_path)
            }
        else:
            yield {
                "status": "error",
                "progress": 0,
                "error": "Transcription failed - no output file generated"
            }

transcriber = WhisperTranscriber()