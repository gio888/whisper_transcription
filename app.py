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

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

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

# Import meeting analyzer if API keys are configured
try:
    from src.analyzers.meeting_analyzer import get_analyzer
    from src.analyzers.analyzer_config import AnalyzerConfig
    # Don't create analyzer immediately, just check if we can
    try:
        AnalyzerConfig.validate_config()
        ANALYSIS_ENABLED = True
    except ValueError as e:
        logger.warning(f"Meeting analysis disabled: {e}")
        ANALYSIS_ENABLED = False
except ImportError as e:
    logger.warning(f"Meeting analysis disabled: {e}")
    ANALYSIS_ENABLED = False

# Import Notion sync if API key is configured
try:
    from src.integrations.notion_sync import get_notion_sync
    from src.integrations.notion_config import NotionConfig
    try:
        NotionConfig.validate_config()
        NOTION_ENABLED = True
        logger.info("Notion integration enabled")
    except ValueError as e:
        logger.warning(f"Notion integration disabled: {e}")
        NOTION_ENABLED = False
except ImportError as e:
    logger.warning(f"Notion integration disabled: {e}")
    NOTION_ENABLED = False

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
        
        # Start batch processing immediately
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

@app.websocket("/ws/analysis/{analysis_id}")
async def websocket_analysis_endpoint(websocket: WebSocket, analysis_id: str):
    """WebSocket endpoint for real-time analysis progress"""
    
    if not ANALYSIS_ENABLED:
        await websocket.close(code=1008, reason="Analysis not configured")
        return
    
    await websocket.accept()
    logger.info(f"Analysis WebSocket connected: {analysis_id}")
    
    try:
        # Get transcript from session
        transcript = None
        
        # Check if there's a transcript file
        transcript_files = list(UPLOAD_DIR.glob(f"{analysis_id}*_transcript.txt"))
        if transcript_files:
            with open(transcript_files[0], 'r', encoding='utf-8') as f:
                transcript = f.read()
        
        if not transcript:
            # Wait for transcript to be sent via WebSocket
            data = await websocket.receive_json()
            transcript = data.get('transcript')
            
            if not transcript:
                await websocket.send_json({
                    "status": "error",
                    "message": "No transcript provided"
                })
                return
        
        # Process the transcript and send updates
        analyzer = get_analyzer()
        async for update in analyzer.analyze_transcript(
            transcript=transcript,
            session_id=analysis_id,
            metadata={"source": "websocket"}
        ):
            await websocket.send_json(update)
            
    except WebSocketDisconnect:
        logger.info(f"Analysis WebSocket disconnected: {analysis_id}")
    except Exception as e:
        logger.error(f"Error in analysis WebSocket: {e}")
        await websocket.send_json({
            "status": "error",
            "message": str(e)
        })
    finally:
        try:
            await websocket.close()
        except:
            pass

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

@app.post("/api/analyze-transcript")
async def analyze_transcript_endpoint(
    session_id: str = None,
    transcript_text: str = None,
    file: UploadFile = File(None)
):
    """Analyze a meeting transcript using AI"""
    
    if not ANALYSIS_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Meeting analysis is not configured. Please set up API keys."
        )
    
    # Get transcript text from various sources
    transcript = None
    
    if transcript_text:
        transcript = transcript_text
    elif file:
        content = await file.read()
        transcript = content.decode('utf-8')
    elif session_id:
        # Try to find transcript file by session ID
        transcript_files = list(UPLOAD_DIR.glob(f"{session_id}*_transcript.txt"))
        if transcript_files:
            with open(transcript_files[0], 'r', encoding='utf-8') as f:
                transcript = f.read()
    
    if not transcript:
        raise HTTPException(
            status_code=400,
            detail="No transcript provided. Send transcript_text, file, or session_id."
        )
    
    # Generate analysis ID
    analysis_session_id = session_id or str(uuid.uuid4())
    
    # Return immediately with analysis ID, process in background
    return {
        "analysis_id": analysis_session_id,
        "status": "processing",
        "message": "Analysis started. Use WebSocket for real-time updates."
    }

@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Retrieve a completed analysis"""
    
    if not ANALYSIS_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Meeting analysis is not configured."
        )
    
    analyzer = get_analyzer()
    result = await analyzer.get_analysis(analysis_id)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found or still processing."
        )
    
    return result

@app.get("/api/analysis-status")
async def get_analysis_status():
    """Check if analysis feature is enabled"""
    return {
        "enabled": ANALYSIS_ENABLED,
        "message": "Analysis feature is enabled" if ANALYSIS_ENABLED else "Please configure API keys for analysis"
    }

@app.post("/api/sync-to-notion")
async def sync_to_notion(
    analysis_id: str = None,
    analysis_data: Dict = None
):
    """Sync analysis results to Notion"""
    
    if not NOTION_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Notion integration is not configured. Please set up NOTION_API_KEY."
        )
    
    if not ANALYSIS_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Analysis must be enabled to sync to Notion."
        )
    
    # Get analysis data if not provided
    if not analysis_data and analysis_id:
        analyzer = get_analyzer()
        analysis_data = await analyzer.get_analysis(analysis_id)
        
    if not analysis_data:
        raise HTTPException(
            status_code=400,
            detail="No analysis data provided or found."
        )
    
    # Sync to Notion
    try:
        notion = get_notion_sync()
        sync_result = await notion.sync_analysis_to_notion(analysis_data)
        
        # Log results
        logger.info(f"Notion sync completed: {sync_result.success}")
        if sync_result.meeting_id:
            logger.info(f"Meeting created: {sync_result.meeting_id}")
        logger.info(f"Tasks created: {len(sync_result.tasks_created)}")
        logger.info(f"Tasks failed: {len(sync_result.tasks_failed)}")
        
        # Return detailed response
        return {
            "success": sync_result.success,
            "meeting": {
                "id": sync_result.meeting_id,
                "url": sync_result.meeting_url
            },
            "tasks": {
                "created": len(sync_result.tasks_created),
                "failed": len(sync_result.tasks_failed),
                "details": {
                    "created": sync_result.tasks_created,
                    "failed": sync_result.tasks_failed
                }
            },
            "errors": sync_result.errors
        }
        
    except Exception as e:
        logger.error(f"Notion sync failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync to Notion: {str(e)}"
        )

@app.get("/api/notion-status")
async def get_notion_status():
    """Check if Notion integration is enabled and working"""
    
    if not NOTION_ENABLED:
        return {
            "enabled": False,
            "message": "Notion integration not configured"
        }
    
    # Test connection
    try:
        notion = get_notion_sync()
        connected = await notion.check_notion_connection()
        
        return {
            "enabled": True,
            "connected": connected,
            "message": "Notion integration is ready" if connected else "Cannot connect to Notion API"
        }
    except Exception as e:
        return {
            "enabled": True,
            "connected": False,
            "message": f"Notion integration error: {str(e)}"
        }

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
            completion_data = {
                "type": "file_complete",
                "file_id": batch_file.id,
                "status": batch_file.status.value,
                "error_message": batch_file.error_message,
                "transcript_path": str(batch_file.transcript_path) if batch_file.transcript_path else None
            }
            
            # Include transcript content for client-side saving
            if batch_file.status == FileStatus.COMPLETED and batch_file.transcript_path:
                try:
                    with open(batch_file.transcript_path, 'r', encoding='utf-8') as f:
                        completion_data["transcript"] = f.read()
                except Exception as e:
                    logger.error(f"Failed to read transcript for {batch_file.original_name}: {e}")
            
            await websocket.send_json(completion_data)
        
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