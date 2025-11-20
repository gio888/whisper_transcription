import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
import database

client = TestClient(app)

@pytest.mark.asyncio
async def test_persistence_api():
    # Initialize DB
    await database.init_db()
    
    # Upload batch of 2 files
    files = [
        ('files', ('file1.m4a', b'content', 'audio/mp4')),
        ('files', ('file2.m4a', b'content', 'audio/mp4')),
    ]
    response = client.post("/batch-upload", files=files)
    assert response.status_code == 200
    data = response.json()
    batch_id = data['batch_id']
    
    # Check DB for batch creation
    batch = await database.get_batch(batch_id)
    assert batch is not None
    assert batch['total_files'] == 2
    assert len(batch['files']) == 2
    
    # Check /api/batches
    response = client.get("/api/batches")
    assert response.status_code == 200
    batches = response.json()['batches']
    assert len(batches) > 0
    # The most recent batch should be ours
    assert batches[0]['id'] == batch_id
    
    print("✅ Persistence API verification passed")
