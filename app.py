import asyncio
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles

from config import UPLOAD_DIR, STATIC_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from transcriber import transcriber

logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed output
    format='%(asctime)s - %(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Whisper Transcription Service")
    
    # Clean old files from uploads directory
    for file in UPLOAD_DIR.glob("*"):
        try:
            if file.is_file():
                file.unlink()
        except Exception as e:
            logger.error(f"Failed to delete {file}: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Whisper Transcription Service")

app = FastAPI(title="Whisper Transcription Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# Batch processing data structures
class FileStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    SKIPPED = "skipped"

@dataclass
class BatchFile:
    id: str
    original_name: str
    original_path: Optional[str]
    file_path: Path
    size: int
    status: FileStatus
    error_message: Optional[str] = None
    transcript_path: Optional[str] = None
    progress: int = 0
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "original_name": self.original_name,
            "original_path": self.original_path,
            "file_path": str(self.file_path),
            "size": self.size,
            "status": self.status.value,
            "error_message": self.error_message,
            "transcript_path": self.transcript_path,
            "progress": self.progress
        }

@dataclass
class BatchJob:
    batch_id: str
    files: List[BatchFile]
    current_file_index: int = 0
    total_files: int = 0
    completed_files: int = 0
    failed_files: int = 0
    is_processing: bool = False

# Store active batch jobs
active_batches: Dict[str, BatchJob] = {}
batch_processing_lock = asyncio.Lock()

@app.get("/")
async def read_index():
    """Serve the main HTML page"""
    return FileResponse(STATIC_DIR / "index.html")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle single file upload and start transcription"""
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not supported. Supported types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    
    # Save uploaded file
    file_path = UPLOAD_DIR / f"{session_id}{file_ext}"
    
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
                )
            await f.write(content)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")
    
    return {
        "session_id": session_id,
        "filename": file.filename,
        "size": len(content),
        "message": "File uploaded successfully. Connect to WebSocket for progress updates."
    }

@app.post("/batch-upload")
async def upload_batch_files(files: List[UploadFile] = File(...)):
    """Handle multiple file uploads for batch transcription"""
    
    if len(files) > 50:  # Reasonable limit
        raise HTTPException(
            status_code=400,
            detail="Too many files. Maximum 50 files per batch."
        )
    
    # Generate unique batch ID
    batch_id = str(uuid.uuid4())
    batch_files = []
    
    for file in files:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            continue  # Skip invalid files rather than failing entire batch
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{batch_id}_{file_id}{file_ext}"
        
        try:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                continue  # Skip files that are too large
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Create batch file record
            batch_file = BatchFile(
                id=file_id,
                original_name=file.filename,
                original_path=None,  # Will be set from client
                file_path=file_path,
                size=len(content),
                status=FileStatus.QUEUED
            )
            batch_files.append(batch_file)
            
        except Exception as e:
            logger.error(f"Failed to save file {file.filename}: {e}")
            continue  # Skip failed files
    
    if not batch_files:
        raise HTTPException(
            status_code=400,
            detail="No valid files uploaded. Check file formats and sizes."
        )
    
    # Create batch job
    batch_job = BatchJob(
        batch_id=batch_id,
        files=batch_files,
        total_files=len(batch_files)
    )
    
    active_batches[batch_id] = batch_job
    
    return {
        "batch_id": batch_id,
        "files_count": len(batch_files),
        "files": [{
            "id": bf.id,
            "name": bf.original_name,
            "size": bf.size,
            "status": bf.status.value
        } for bf in batch_files],
        "message": "Files uploaded successfully. Connect to WebSocket for batch progress updates."
    }

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time transcription progress"""
    await websocket.accept()
    active_connections[session_id] = websocket
    
    try:
        # Find the uploaded file
        file_path = None
        for ext in ALLOWED_EXTENSIONS:
            potential_path = UPLOAD_DIR / f"{session_id}{ext}"
            if potential_path.exists():
                file_path = potential_path
                break
        
        if not file_path:
            await websocket.send_json({
                "status": "error",
                "error": "File not found. Please upload again."
            })
            return
        
        # Start transcription with progress updates
        async for update in transcriber.transcribe_with_progress(file_path):
            await websocket.send_json(update)
            
            # If completed, include download link
            if update.get("status") == "completed":
                update["download_url"] = f"/download/{session_id}"
                await websocket.send_json(update)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        await websocket.send_json({
            "status": "error",
            "error": str(e)
        })
    finally:
        if session_id in active_connections:
            del active_connections[session_id]

@app.websocket("/ws/batch/{batch_id}")
async def batch_websocket_endpoint(websocket: WebSocket, batch_id: str):
    """WebSocket endpoint for batch transcription progress"""
    await websocket.accept()
    active_connections[batch_id] = websocket
    
    try:
        # Check if batch exists
        if batch_id not in active_batches:
            await websocket.send_json({
                "status": "error",
                "error": "Batch not found. Please upload files again."
            })
            return
        
        # Start batch processing
        await process_batch(batch_id)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for batch {batch_id}")
    except Exception as e:
        logger.error(f"Error during batch processing: {e}")
        await websocket.send_json({
            "status": "error",
            "error": str(e)
        })
    finally:
        if batch_id in active_connections:
            del active_connections[batch_id]

@app.get("/download/{session_id}")
async def download_transcript(session_id: str):
    """Download the transcription result"""
    
    # Look for transcript file
    transcript_files = list(UPLOAD_DIR.glob(f"{session_id}*_transcript.txt"))
    
    if not transcript_files:
        # Try to find by the base session ID
        for file in UPLOAD_DIR.glob("*_transcript.txt"):
            if session_id in str(file):
                return FileResponse(
                    file,
                    media_type="text/plain",
                    filename=f"transcript_{session_id}.txt"
                )
        
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return FileResponse(
        transcript_files[0],
        media_type="text/plain",
        filename=f"transcript_{session_id}.txt"
    )

# Startup logic moved to lifespan handler above

async def process_batch(batch_id: str):
    """Process all files in a batch sequentially"""
    async with batch_processing_lock:
        batch_job = active_batches.get(batch_id)
        if not batch_job or batch_job.is_processing:
            return
        
        batch_job.is_processing = True
        websocket = active_connections.get(batch_id)
        
        if not websocket:
            batch_job.is_processing = False
            return
        
        # Send initial batch status
        await websocket.send_json({
            "type": "batch_status",
            "batch_id": batch_id,
            "total_files": batch_job.total_files,
            "completed_files": batch_job.completed_files,
            "failed_files": batch_job.failed_files,
            "current_file_index": batch_job.current_file_index,
            "files": [f.to_dict() for f in batch_job.files]
        })
        
        # Process each file sequentially
        for i, batch_file in enumerate(batch_job.files):
            if batch_file.status != FileStatus.QUEUED:
                continue
                
            batch_job.current_file_index = i
            batch_file.status = FileStatus.PROCESSING
            
            # Send file processing start
            await websocket.send_json({
                "type": "file_start",
                "file_id": batch_file.id,
                "file_name": batch_file.original_name,
                "file_index": i
            })
            
            try:
                # Process the file
                async for update in transcriber.transcribe_with_progress(
                    batch_file.file_path, 
                    original_path=batch_file.original_path
                ):
                    # Update file progress
                    if "progress" in update:
                        batch_file.progress = update["progress"]
                    
                    # Send progress update
                    update["type"] = "file_progress"
                    update["file_id"] = batch_file.id
                    update["file_index"] = i
                    await websocket.send_json(update)
                    
                    # Check if completed
                    if update.get("status") == "completed":
                        batch_file.status = FileStatus.COMPLETED
                        batch_file.transcript_path = update.get("output_file")
                        batch_job.completed_files += 1
                        break
                    elif update.get("status") == "error":
                        batch_file.status = FileStatus.ERROR
                        batch_file.error_message = update.get("error")
                        batch_job.failed_files += 1
                        break
                        
            except Exception as e:
                logger.error(f"Error processing file {batch_file.original_name}: {e}")
                batch_file.status = FileStatus.ERROR
                batch_file.error_message = str(e)
                batch_job.failed_files += 1
                
                # Send error update
                await websocket.send_json({
                    "type": "file_progress",
                    "status": "error",
                    "error": str(e),
                    "file_id": batch_file.id,
                    "file_index": i
                })
            
            # Send file completion status
            await websocket.send_json({
                "type": "file_complete",
                "file_id": batch_file.id,
                "status": batch_file.status.value,
                "error_message": batch_file.error_message,
                "transcript_path": str(batch_file.transcript_path) if batch_file.transcript_path else None
            })
        
        # Send batch completion
        batch_job.is_processing = False
        await websocket.send_json({
            "type": "batch_complete",
            "batch_id": batch_id,
            "total_files": batch_job.total_files,
            "completed_files": batch_job.completed_files,
            "failed_files": batch_job.failed_files
        })

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)