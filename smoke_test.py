#!/usr/bin/env python3
"""
Smoke Test Script - Run this before overnight batch processing!

This script performs quick validation tests to catch common errors:
- JSON serialization issues (like the PosixPath bug)
- Import errors
- Configuration issues
- Basic API functionality

Usage:
    python smoke_test.py
    
Returns:
    0 if all tests pass
    1 if any test fails
"""

import sys
import json
import asyncio
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import traceback

# Add colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_test(name: str, passed: bool, error: str = None):
    """Print test result with color."""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"  {status} {name}")
    if error and not passed:
        print(f"      {Colors.YELLOW}→ {error}{Colors.RESET}")


def test_imports() -> bool:
    """Test that all required modules can be imported."""
    print(f"\n{Colors.BOLD}Testing imports...{Colors.RESET}")
    
    required_imports = [
        "app",
        "config", 
        "transcriber",
        "fastapi",
        "websockets",
        "aiofiles"
    ]
    
    all_passed = True
    for module_name in required_imports:
        try:
            __import__(module_name)
            print_test(f"Import {module_name}", True)
        except ImportError as e:
            print_test(f"Import {module_name}", False, str(e))
            all_passed = False
    
    return all_passed


def test_json_serialization() -> bool:
    """Test that all data models can be JSON serialized."""
    print(f"\n{Colors.BOLD}Testing JSON serialization (PosixPath bug check)...{Colors.RESET}")
    
    try:
        from app import BatchFile, FileStatus, BatchJob
        
        # Test 1: BatchFile with Path object
        batch_file = BatchFile(
            id="test-123",
            original_name="test.mp3",
            original_path="/original/test.mp3",
            file_path=Path("/uploads/test.mp3"),  # This is a Path object!
            size=1024,
            status=FileStatus.QUEUED
        )
        
        # Try to serialize using to_dict
        file_dict = batch_file.to_dict()
        json_str = json.dumps(file_dict)
        print_test("BatchFile.to_dict() serialization", True)
        
        # Test 2: Multiple files in list
        files = [batch_file.to_dict() for _ in range(3)]
        json.dumps(files)
        print_test("Multiple BatchFiles serialization", True)
        
        # Test 3: Complex nested structure (like WebSocket messages)
        message = {
            "type": "batch_status",
            "batch_id": "test-batch",
            "files": files,
            "metadata": {
                "timestamp": "2024-01-01T00:00:00",
                "path": str(Path("/some/path"))  # Ensure Path is converted
            }
        }
        json.dumps(message)
        print_test("Complex WebSocket message serialization", True)
        
        return True
        
    except Exception as e:
        print_test("JSON serialization", False, str(e))
        traceback.print_exc()
        return False


def test_configuration() -> bool:
    """Test that configuration is valid."""
    print(f"\n{Colors.BOLD}Testing configuration...{Colors.RESET}")
    
    try:
        from config import UPLOAD_DIR, STATIC_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
        
        # Check directories exist
        if not UPLOAD_DIR.exists():
            print_test("Upload directory exists", False, f"{UPLOAD_DIR} not found")
            return False
        print_test("Upload directory exists", True)
        
        if not STATIC_DIR.exists():
            print_test("Static directory exists", False, f"{STATIC_DIR} not found")
            return False
        print_test("Static directory exists", True)
        
        # Check file size limit is reasonable
        if MAX_FILE_SIZE <= 0 or MAX_FILE_SIZE > 1024 * 1024 * 1024:  # 1GB max
            print_test("MAX_FILE_SIZE configuration", False, f"Invalid size: {MAX_FILE_SIZE}")
            return False
        print_test("MAX_FILE_SIZE configuration", True)
        
        # Check allowed extensions
        if not ALLOWED_EXTENSIONS or not all(ext.startswith('.') for ext in ALLOWED_EXTENSIONS):
            print_test("ALLOWED_EXTENSIONS configuration", False, "Invalid extensions")
            return False
        print_test("ALLOWED_EXTENSIONS configuration", True)
        
        return True
        
    except Exception as e:
        print_test("Configuration", False, str(e))
        return False


async def test_api_endpoints() -> bool:
    """Test basic API functionality."""
    print(f"\n{Colors.BOLD}Testing API endpoints...{Colors.RESET}")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        
        # Test 1: Root endpoint
        response = client.get("/")
        if response.status_code != 200:
            print_test("GET / endpoint", False, f"Status code: {response.status_code}")
            return False
        print_test("GET / endpoint", True)
        
        # Test 2: Batch upload with invalid data (should handle gracefully)
        response = client.post("/batch-upload", files=[])
        if response.status_code not in [400, 422]:  # Should reject empty upload
            print_test("POST /batch-upload validation", False, "Accepted empty upload")
            return False
        print_test("POST /batch-upload validation", True)
        
        # Test 3: Create a simple test file and upload
        with tempfile.NamedTemporaryFile(suffix='.mp3') as f:
            f.write(b"test audio content")
            f.seek(0)
            
            files = {'file': ('test.mp3', f.read(), 'audio/mpeg')}
            response = client.post("/upload", files=files)
            
            if response.status_code != 200:
                print_test("POST /upload endpoint", False, f"Status code: {response.status_code}")
                return False
            print_test("POST /upload endpoint", True)
        
        return True
        
    except Exception as e:
        print_test("API endpoints", False, str(e))
        traceback.print_exc()
        return False


async def test_websocket_messages() -> bool:
    """Test WebSocket message serialization."""
    print(f"\n{Colors.BOLD}Testing WebSocket messages...{Colors.RESET}")
    
    try:
        from app import BatchFile, BatchJob, FileStatus
        from pathlib import Path
        import json
        
        # Simulate WebSocket messages that would be sent
        batch_file = BatchFile(
            id="ws-test",
            original_name="audio.mp3",
            original_path=None,
            file_path=Path("/test/audio.mp3"),
            size=2048,
            status=FileStatus.PROCESSING,
            progress=50
        )
        
        # Test various message types
        messages = [
            {
                "type": "batch_status",
                "files": [batch_file.to_dict()],
                "total_files": 1
            },
            {
                "type": "file_progress",
                "file_id": batch_file.id,
                "progress": 75,
                "status": "processing"
            },
            {
                "type": "file_complete",
                "file_id": batch_file.id,
                "status": "completed",
                "transcript_path": str(Path("/transcripts/output.txt"))
            }
        ]
        
        for i, msg in enumerate(messages):
            try:
                json.dumps(msg)
                print_test(f"WebSocket message type: {msg['type']}", True)
            except Exception as e:
                print_test(f"WebSocket message type: {msg['type']}", False, str(e))
                return False
        
        return True
        
    except Exception as e:
        print_test("WebSocket messages", False, str(e))
        return False


def main():
    """Run all smoke tests."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}🔥 Running Smoke Tests...{Colors.RESET}")
    print("=" * 50)
    
    all_passed = True
    
    # Run synchronous tests
    all_passed &= test_imports()
    all_passed &= test_json_serialization()
    all_passed &= test_configuration()
    
    # Run async tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        all_passed &= loop.run_until_complete(test_api_endpoints())
        all_passed &= loop.run_until_complete(test_websocket_messages())
    finally:
        loop.close()
    
    # Print summary
    print("\n" + "=" * 50)
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All smoke tests passed!{Colors.RESET}")
        print(f"{Colors.GREEN}Safe to proceed with batch processing.{Colors.RESET}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Some tests failed!{Colors.RESET}")
        print(f"{Colors.YELLOW}Fix the issues before running overnight batch processing.{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()