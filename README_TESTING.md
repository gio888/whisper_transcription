# Testing Guide for Whisper Transcription Service

## Quick Start - Run Before Overnight Processing!

**IMPORTANT**: Always run the smoke test before starting overnight batch processing:

```bash
python smoke_test.py
```

This will catch common issues like:
- JSON serialization errors (like the PosixPath bug we just fixed!)
- Import errors
- Configuration issues
- Basic API functionality

## Full Test Suite

### Installation
```bash
pip install -r requirements-test.txt
```

### Run All Tests
```bash
pytest -v
```

### Run Specific Test Categories

#### Unit Tests (Data Model Serialization)
```bash
pytest tests/test_models.py -v
```
**These tests would have caught the PosixPath bug immediately!**

#### API Integration Tests
```bash
pytest tests/test_api.py -v
```

#### WebSocket Tests
```bash
pytest tests/test_websocket.py -v
```

### Test Coverage
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## Critical Tests That Prevent Overnight Failures

### 1. BatchFile.to_dict() Serialization Test
Located in `tests/test_models.py::TestBatchFileSerialization::test_batch_file_to_dict_with_path_object`

This test specifically checks that Path objects are properly converted to strings for JSON serialization. **This exact test would have caught the bug that caused your overnight batch to fail!**

### 2. WebSocket Message Serialization
Located in `tests/test_websocket.py::TestBatchWebSocket::test_batch_websocket_json_serialization`

Ensures all WebSocket messages sent during batch processing can be serialized to JSON.

### 3. Smoke Test Script
The `smoke_test.py` script runs quick validation checks in under 5 seconds:
- ✅ Import validation
- ✅ JSON serialization checks
- ✅ Configuration validation
- ✅ API endpoint checks
- ✅ WebSocket message validation

## CI/CD Pipeline

GitHub Actions automatically runs tests on:
- Every push to main/develop branches
- All pull requests

See `.github/workflows/test.yml` for configuration.

## Pre-Deployment Checklist

Before running overnight batch processing:

1. **Run smoke test**: `python smoke_test.py`
2. **Check for any recent code changes**: `git status`
3. **Run full test suite if code changed**: `pytest`
4. **Monitor first few files**: Watch the UI for the first 2-3 files to ensure they process correctly

## Common Issues Caught by Tests

| Issue | Test That Catches It | Time Saved |
|-------|---------------------|------------|
| PosixPath JSON serialization | `test_batch_file_to_dict_with_path_object` | 8+ hours |
| Invalid file format handling | `test_batch_upload_invalid_format` | Hours of debugging |
| WebSocket message errors | `test_batch_websocket_json_serialization` | Overnight run failure |
| File size limits | `test_batch_upload_oversized_file` | Processing failures |

## Adding New Tests

When adding new features:
1. Write unit tests for data models
2. Write integration tests for API endpoints
3. Update smoke test if adding critical functionality
4. Run full test suite before committing

## Test Philosophy

> "A 5-second test can save an 8-hour overnight run."

The PosixPath bug is a perfect example - a simple serialization test would have caught it immediately, saving you from discovering it after running overnight.