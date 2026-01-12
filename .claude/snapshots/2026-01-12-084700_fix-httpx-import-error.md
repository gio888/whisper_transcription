# Snapshot
- Problem solved: Server startup failed with `ModuleNotFoundError: No module named 'httpx'` because app.py imported test-only code (WebSocketTestSession from starlette.testclient).
- Decisions: Moved test utility code (WebSocket timeout patching) from app.py to tests/conftest.py where it belongs; test dependencies should not be in production code.
- Metrics: Server starts successfully; `python -c "import app"` passes.
- Modified files: app.py (removed test imports), tests/conftest.py (added WebSocket patching code)
- Next steps: Install httpx/requests for smoke_test.py API tests (optional); continue with priorities from TODO.md.
