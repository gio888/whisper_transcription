import asyncio
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles

from config import UPLOAD_DIR, STATIC_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from transcriber import transcriber

logging.basicConfig(level=logging.INFO)
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

@app.get("/")
async def read_index():
    """Serve the main HTML page"""
    return FileResponse(STATIC_DIR / "index.html")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file upload and start transcription"""
    
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

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)