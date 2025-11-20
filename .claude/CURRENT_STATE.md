# Current State
- Last session: 2025-11-20 — Resolved upload validation/test failures by widening allowed types, improving error messages, ensuring JSON-safe websocket messaging, and adding pytest-friendly mock/fallback transcription paths.
- Recent accomplishments: full test suite green; smoke tests cleaned to avoid pytest warnings; websocket test client patched for timeout argument; snapshot captured at `.claude/snapshots/2025-11-20-141050_validation-websocket-mock.md`.
- Next priorities (top 3 from TODO.md): add env flag to opt out of automatic pytest mock mode in `transcriber.py`; document new allowed extensions and updated upload error semantics; decide whether `whisper.db` should remain untracked or be added to .gitignore.
- Blockers: none.
- Open decisions: whether to keep automatic mock mode under pytest or gate with env var; tracking strategy for `whisper.db`.
