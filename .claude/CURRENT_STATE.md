# Current State
- Last session: 2026-01-12 — Fixed server startup error (`ModuleNotFoundError: No module named 'httpx'`) by moving test-only WebSocketTestSession import and patching code from app.py to tests/conftest.py.
- Recent accomplishments: Server starts successfully; separated test utilities from production code; snapshot captured at `.claude/snapshots/2026-01-12-084700_fix-httpx-import-error.md`.
- Next priorities (top 3 from TODO.md): add env flag to opt out of automatic pytest mock mode in `transcriber.py`; document new allowed extensions and updated upload error semantics; decide whether `whisper.db` should remain untracked or be added to .gitignore.
- Additional follow-up: Install httpx/requests for smoke_test.py API tests; upstream meeting/notion tests need deps installed or marked skipped.
- Blockers: none.
- Open decisions: whether to keep automatic mock mode under pytest or gate with env var; tracking strategy for `whisper.db`; approach for meeting/notion test dependencies.
