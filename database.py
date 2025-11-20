import aiosqlite
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from config import BASE_DIR

DB_PATH = BASE_DIR / "whisper.db"
logger = logging.getLogger(__name__)

async def init_db():
    """Initialize the database tables"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS batches (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_files INTEGER,
                completed_files INTEGER DEFAULT 0,
                failed_files INTEGER DEFAULT 0,
                status TEXT DEFAULT 'processing'
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                batch_id TEXT,
                original_name TEXT,
                original_path TEXT,
                file_path TEXT,
                size INTEGER,
                status TEXT,
                error_message TEXT,
                transcript_path TEXT,
                progress INTEGER DEFAULT 0,
                FOREIGN KEY(batch_id) REFERENCES batches(id)
            )
        """)
        await db.commit()

async def create_batch(batch_id: str, total_files: int):
    """Create a new batch record"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO batches (id, total_files) VALUES (?, ?)",
            (batch_id, total_files)
        )
        await db.commit()

async def create_file(batch_id: str, file_data: Dict[str, Any]):
    """Create a new file record"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO files (
                id, batch_id, original_name, original_path, file_path, 
                size, status, progress
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                file_data['id'], batch_id, file_data['original_name'],
                file_data.get('original_path'), str(file_data['file_path']),
                file_data['size'], file_data['status'], file_data.get('progress', 0)
            )
        )
        await db.commit()

async def update_file_status(file_id: str, status: str, error_message: Optional[str] = None, transcript_path: Optional[str] = None, progress: int = 0):
    """Update file status and progress"""
    async with aiosqlite.connect(DB_PATH) as db:
        query = "UPDATE files SET status = ?, progress = ?"
        params = [status, progress]
        
        if error_message:
            query += ", error_message = ?"
            params.append(error_message)
            
        if transcript_path:
            query += ", transcript_path = ?"
            params.append(transcript_path)
            
        query += " WHERE id = ?"
        params.append(file_id)
        
        await db.execute(query, params)
        await db.commit()

async def update_batch_stats(batch_id: str, completed: int, failed: int):
    """Update batch statistics"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE batches SET completed_files = ?, failed_files = ? WHERE id = ?",
            (completed, failed, batch_id)
        )
        await db.commit()

async def get_recent_batches(limit: int = 5) -> List[Dict[str, Any]]:
    """Get recent batches with their files"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Get batches
        async with db.execute(
            "SELECT * FROM batches ORDER BY created_at DESC LIMIT ?", 
            (limit,)
        ) as cursor:
            batches = []
            async for row in cursor:
                batch = dict(row)
                
                # Get files for this batch
                async with db.execute(
                    "SELECT * FROM files WHERE batch_id = ?", 
                    (batch['id'],)
                ) as file_cursor:
                    files = [dict(f) for f in await file_cursor.fetchall()]
                    batch['files'] = files
                
                batches.append(batch)
                
            return batches

async def get_batch(batch_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific batch with its files"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute("SELECT * FROM batches WHERE id = ?", (batch_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            
            batch = dict(row)
            
            async with db.execute("SELECT * FROM files WHERE batch_id = ?", (batch_id,)) as file_cursor:
                files = [dict(f) for f in await file_cursor.fetchall()]
                batch['files'] = files
                
            return batch
