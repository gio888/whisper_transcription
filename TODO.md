# TODO
Last updated: 2026-01-12

## In Progress
- **Wire up analysis/meeting minutes feature** - Plan at `plans/2026-01-12-wire-up-analysis-feature.md`
  - Backend exists, UI hidden, need JavaScript integration
  - Per-file analysis for batch mode

## Next actions
- Install httpx/requests for smoke_test.py API endpoint tests (optional test dependency).
- Add env flag to opt out of automatic pytest mock mode in `transcriber.py` when real binaries are available.
- Document new allowed upload extensions and updated error semantics in README/CHANGELOG.
- Decide whether `whisper.db` should remain untracked or be added to .gitignore.
- Address new upstream tests requiring meeting analysis/notion deps (install/mocks/skips for `meeting_analyzer`, `notion_client`, etc.).

## Completed this session
- Explored codebase and confirmed analysis feature exists but is UI-hidden
- Created implementation plan for wiring up analysis feature
- Created `plans/` folder for permanent session memory
