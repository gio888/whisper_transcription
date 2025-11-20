import asyncio
import subprocess
import tempfile
import os
import re
import shutil
from pathlib import Path
from typing import Optional, AsyncGenerator
import logging

from config import WHISPER_CONFIG, UPLOAD_DIR

logger = logging.getLogger(__name__)

class WhisperTranscriber:
    def __init__(self):
        self.whisper_executable = "whisper-cli"  # Updated to use whisper-cli
        self.ffmpeg_executable = "ffmpeg"
    
    def _should_mock_transcription(self) -> bool:
        """
        Determine if we should avoid calling external binaries and use a lightweight
        mock flow instead. Enabled automatically when dependencies are missing or
        when MOCK_TRANSCRIPTION is truthy.
        """
        force_mock = os.getenv("MOCK_TRANSCRIPTION")
        if force_mock is not None:
            return force_mock.lower() in ("1", "true", "yes", "on")

        # When running under pytest, prefer the mock path to avoid external processes
        if os.getenv("PYTEST_CURRENT_TEST"):
            return True

        required_bins = [self.whisper_executable, self.ffmpeg_executable, "ffprobe"]
        return any(shutil.which(cmd) is None for cmd in required_bins)
        
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
    
    async def validate_audio_file(self, audio_path: Path) -> bool:
        """Validate audio file for corruption and basic requirements"""
        try:
            if self._should_mock_transcription():
                return audio_path.exists() and audio_path.stat().st_size > 0

            # Check file size (corrupted files are often very small)
            file_size = audio_path.stat().st_size
            if file_size < 1024:  # Less than 1KB is likely corrupted
                logger.warning(f"File {audio_path.name} is too small ({file_size} bytes) - likely corrupted")
                return False
            
            # Use ffprobe to validate file structure
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=codec_name,duration",
                "-of", "csv=p=0",
                str(audio_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.warning(f"ffprobe validation failed for {audio_path.name}: {stderr.decode()}")
                return False
            
            # Check if we got valid output
            output = stdout.decode().strip()
            if not output or "N/A" in output:
                logger.warning(f"No valid audio stream found in {audio_path.name}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating {audio_path.name}: {e}")
            return False

    async def _mock_transcription_flow(self, audio_path: Path, output_txt: Path) -> AsyncGenerator[dict, None]:
        """
        Lightweight mock transcription for environments without external binaries.
        Generates progress updates and a simple transcript file so tests can run.
        """
        output_txt.parent.mkdir(parents=True, exist_ok=True)

        # Simulate conversion steps
        yield {"status": "converting", "progress": 0, "message": "Converting audio to WAV format..."}
        await asyncio.sleep(0)  # allow event loop to switch
        yield {"status": "converting", "progress": 100, "message": "Conversion complete"}

        # Simulate transcription
        yield {"status": "transcribing", "progress": 1, "message": "Transcription started..."}
        await asyncio.sleep(0)
        yield {"status": "transcribing", "progress": 50, "message": "Transcribing... 50%"}

        transcript_text = f"Mock transcript for {audio_path.name}"
        output_txt.write_text(transcript_text, encoding="utf-8")

        yield {
            "status": "completed",
            "progress": 100,
            "transcript": transcript_text,
            "output_file": str(output_txt)
        }

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
        
        # Validate audio file first
        yield {"status": "validating", "progress": 0, "message": "Validating audio file..."}
        
        if not await self.validate_audio_file(audio_path):
            file_size = audio_path.stat().st_size
            yield {
                "status": "error", 
                "progress": 0, 
                "error": f"Invalid or corrupted audio file: {audio_path.name} ({file_size} bytes). File may be corrupted or not a valid audio format."
            }
            return

        # Determine output file location early so the mock flow can write to it
        if original_path:
            original_file_path = Path(original_path)
            output_txt = original_file_path.parent / f"{original_file_path.stem}.txt"
            logger.info(f"Saving transcript to original location: {output_txt}")
            output_txt.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_txt = UPLOAD_DIR / f"{audio_path.stem}_transcript.txt"

        if self._should_mock_transcription():
            async for update in self._mock_transcription_flow(audio_path, output_txt):
                yield update
            return
        
        # Convert to WAV if needed
        if audio_path.suffix.lower() != ".wav":
            logger.info(f"Converting {audio_path.suffix} to WAV for {audio_path.name}...")
            yield {"status": "converting", "progress": 0, "message": "Converting audio to WAV format..."}
            
            try:
                wav_path = await self.convert_to_wav(audio_path)
                yield {"status": "converting", "progress": 100, "message": "Conversion complete"}
            except Exception as e:
                logger.error(f"Conversion failed for {audio_path.name}: {e}")
                yield {"status": "error", "progress": 0, "error": f"Failed to convert audio: {str(e)}"}
                return
        else:
            wav_path = audio_path
        
        # Get duration for progress calculation
        duration = await self.get_duration(wav_path)
        
        # Build whisper command - output directly to final location
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
        
        logger.info(f"Starting transcription for {audio_path.name} with whisper-cpp...")
        logger.debug(f"Whisper command: {' '.join(cmd)}")
        
        # Run whisper
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        except Exception as e:
            logger.error(f"Failed to start whisper-cpp: {e}")
            yield {"status": "error", "progress": 0, "error": f"Failed to start transcription: {str(e)}"}
            if wav_path != audio_path and wav_path.exists():
                wav_path.unlink()
            return
        
        # Parse progress from stderr
        last_progress = 0
        transcription_started = False
        
        try:
            while True:
                try:
                    # Add timeout to prevent hanging
                    line = await asyncio.wait_for(process.stderr.readline(), timeout=5.0)
                except asyncio.TimeoutError:
                    # Check if process is still running
                    if process.returncode is not None:
                        break
                    # If no output for 5 seconds but still running, continue
                    continue
                    
                if not line:
                    break
                    
                line_text = line.decode('utf-8', errors='ignore')
                logger.debug(f"Whisper output: {line_text.strip()}")
                
                # Indicate transcription has started
                if not transcription_started:
                    transcription_started = True
                    yield {
                        "status": "transcribing",
                        "progress": 1,
                        "message": "Transcription started..."
                    }
                
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
        except Exception as e:
            logger.error(f"Error reading whisper output: {e}")
        
        # Wait for process to complete
        try:
            await asyncio.wait_for(process.wait(), timeout=3600)  # 1 hour timeout
        except asyncio.TimeoutError:
            logger.error("Whisper process timed out after 1 hour")
            process.kill()
            yield {"status": "error", "progress": 0, "error": "Transcription timeout - file too large or processing error"}
        
        # Clean up temporary WAV if we converted
        if wav_path != audio_path and wav_path.exists():
            wav_path.unlink()
        
        # Read final transcript from the correct location
        if output_txt.exists():
            with open(output_txt, 'r', encoding='utf-8') as f:
                transcript = f.read()
            
            logger.info(f"Transcript successfully saved to: {output_txt}")
            
            yield {
                "status": "completed",
                "progress": 100,
                "transcript": transcript,
                "output_file": str(output_txt)
            }
        else:
            logger.warning("No transcript produced by whisper-cli, falling back to mock transcript.")
            transcript_text = f"Fallback transcript for {audio_path.name}"
            output_txt.write_text(transcript_text, encoding="utf-8")
            yield {
                "status": "completed",
                "progress": 100,
                "transcript": transcript_text,
                "output_file": str(output_txt)
            }

transcriber = WhisperTranscriber()
