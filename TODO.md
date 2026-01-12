# TODO
Last updated: 2026-01-12

## Completed this session
- Fixed server startup error (httpx import) by moving test utilities from app.py to tests/conftest.py.

## Next actions
- Install httpx/requests for smoke_test.py API endpoint tests (optional test dependency).
- Add env flag to opt out of automatic pytest mock mode in `transcriber.py` when real binaries are available.
- Document new allowed upload extensions and updated error semantics in README/CHANGELOG.
- Decide whether `whisper.db` should remain untracked or be added to .gitignore.
- Address new upstream tests requiring meeting analysis/notion deps (install/mocks/skips for `meeting_analyzer`, `notion_client`, etc.).
