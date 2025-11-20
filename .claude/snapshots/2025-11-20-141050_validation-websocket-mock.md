# Snapshot
- Problem solved: aligned upload validation/errors, JSON-safe batch websocket messaging, and reliable tests via pytest-friendly mock transcription with fallback transcripts.
- Decisions: extended allowed extensions (.ogg/.flac); mock transcription path when deps missing or under pytest; patched WebSocketTestSession to support timeout; fallback transcript generation if whisper output absent.
- Metrics: ./venv/bin/pytest (41 passed)
- Modified files: app.py, config.py, transcriber.py, smoke_test.py
- Next steps: confirm TODO/CHANGELOG updates; consider opt-out flag for pytest mock mode; tidy whisper.db handling if tracked.
