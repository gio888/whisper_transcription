---
originating_branch: main
originating_commit: 5819cb4ab738102f312cedb7ee003a0b3260c8d6
created_at: 2026-07-15T00:21:00+08:00
session_topic: project-review-and-backlog
---

## Completed
- Mapped the local transcription, analysis, and Notion flows and reviewed architecture tradeoffs.
- Verified real Whisper transcription and download on Apple M1; focused core suite passed 36 tests.
- Recorded smoke/full-suite failures and created `BACKLOG.md` with 28 prioritized items.
- Corrected ignore rules for dependency manifests, continuity files, and safe generated audio fixtures.

## Decisions
- Keep the existing FastAPI, vanilla JS, SQLite, and local subprocess stack; prefer targeted lifecycle repairs over a rewrite.
- Keep long real-audio fixtures local for privacy; track only short generated fixtures.

## Next
- Resolve WT-001, WT-004, and WT-005 before completing analysis UI work.
- Repair optional dependency declarations and full-suite collection under WT-201 and WT-202.
