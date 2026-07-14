# Product Backlog

Last updated: 2026-07-14

## Purpose

This is the single source of truth for planned product, reliability, testing, and documentation work. Items are ordered by priority, then by likely implementation sequence.

## Status and priority

- **Status:** `Ready`, `Needs decision`, `Blocked`, `In progress`, or `Done`
- **P0:** Prevents reliable use or creates an unsafe default
- **P1:** Required to complete the intended end-to-end product flow
- **P2:** Important consistency, maintainability, or user-experience work
- **P3:** Useful improvement that can wait

## Baseline recorded on 2026-07-14

- Manual transcription completed successfully with the real local Whisper model on Apple M1.
- The generated transcript was available through the download endpoint.
- The focused core suite passed: 36 tests covering models, upload APIs, WebSockets, SQLite persistence, hang prevention, and batch processing.
- The smoke test failed because `requests` is imported by configuration validation but is not declared as a dependency.
- The full suite stopped during collection with 14 analysis and Notion errors.
- The pinned Pydantic version does not install on Python 3.13, although the project currently advertises Python 3.8+ without an upper bound.
- Notion is unavailable in the default declared environment because `notion_client` is not declared.

## P0: Reliability and safe defaults

### WT-001: Define and enforce the batch recovery contract

- **Status:** Needs decision
- **Problem:** The UI offers recent-batch restoration, but startup deletes uploaded source files and transcripts. Interrupted batches can remain in SQLite while their required files no longer exist.
- **Desired outcome:** Browser refresh, WebSocket disconnection, and server restart each have explicit, truthful behavior.
- **Acceptance criteria:**
  - Product behavior is documented for all three interruption types.
  - The UI never offers an action that cannot succeed with the retained files.
  - Missing source or output files produce a clear terminal state rather than a misleading resume attempt.
  - Automated tests cover the selected recovery behavior.
- **Dependencies:** Product decision on whether server-restart recovery is required.
- **Source:** Architecture review and manual test.

### WT-002: Replace indiscriminate startup cleanup with a retention policy

- **Status:** Ready
- **Problem:** Application startup deletes every file in `uploads`, including recoverable inputs and completed transcripts.
- **Desired outcome:** Files are removed only when they are expired and no longer needed by an active or recoverable job.
- **Acceptance criteria:**
  - Retention periods exist for source audio, converted WAV files, and transcripts.
  - Cleanup ignores active and recoverable jobs.
  - Cleanup reconciles affected SQLite records.
  - Tests verify that startup cannot silently invalidate a resumable batch.
- **Dependencies:** WT-001.
- **Source:** Architecture review.

### WT-003: Bind to localhost by default

- **Status:** Ready
- **Problem:** The service binds to `0.0.0.0` while providing unauthenticated upload and Notion write endpoints with permissive CORS.
- **Desired outcome:** The default configuration matches the documented local-only security model.
- **Acceptance criteria:**
  - Default host is `127.0.0.1`.
  - LAN exposure requires an explicit configuration setting.
  - CORS is restricted to the configured application origin.
  - Documentation explains the implications of enabling LAN access.
- **Dependencies:** None.
- **Source:** Architecture review.

### WT-004: Restore a reproducible supported development environment

- **Status:** Ready
- **Problem:** The declared dependencies fail on Python 3.13, and the repository has no lockfile or enforced interpreter range.
- **Desired outcome:** Setup and test commands produce the same environment reliably.
- **Acceptance criteria:**
  - The project declares its supported Python range accurately.
  - Dependencies install through `uv` on every supported Python version.
  - A lockfile or equivalent reproducible dependency mechanism is committed.
  - Setup, run, and test documentation use `uv run`.
- **Dependencies:** None.
- **Source:** 2026-07-14 baseline.

### WT-005: Repair the smoke test dependency contract

- **Status:** Ready
- **Problem:** `config_validator.py` imports `requests`, but `requests` is absent from the declared dependencies, causing the smoke test to fail.
- **Desired outcome:** A clean declared environment can run the smoke test successfully.
- **Acceptance criteria:**
  - Every smoke-test runtime import is declared or removed.
  - The smoke test passes in a newly resolved supported environment.
  - CI runs the same smoke-test command documented for users.
- **Dependencies:** WT-004.
- **Source:** 2026-07-14 baseline.

## P1: Complete the meeting workflow

### WT-101: Make analysis creation start a real analysis job

- **Status:** Ready
- **Problem:** `POST /api/analyze-transcript` returns an ID but does not store the input or start analysis. The analysis WebSocket must receive the transcript separately.
- **Desired outcome:** One request creates and starts analysis; subsequent connections only observe or retrieve it.
- **Acceptance criteria:**
  - The create endpoint validates and stores the transcript.
  - Analysis starts exactly once and returns a stable analysis ID.
  - The progress WebSocket never requires the client to resend transcript content.
  - Completed results are retrievable after reconnecting.
  - Duplicate requests and failures have defined behavior.
- **Dependencies:** Decision from WT-001 can inform, but need not block, analysis persistence.
- **Source:** Architecture review.

### WT-102: Connect meeting analysis to the browser

- **Status:** Ready
- **Problem:** Analysis controls and result panels exist in HTML but have no JavaScript behavior.
- **Desired outcome:** A user can analyze a completed transcript and review structured results without calling the API manually.
- **Acceptance criteria:**
  - The UI detects whether analysis is available.
  - The analyze action starts analysis and displays live progress.
  - Summary, decisions, discussion points, action items, and cleaned transcript render correctly.
  - Loading, disabled, failure, retry, and reconnect states are accessible and understandable.
  - Single-file and batch transcript entry points are explicitly supported or excluded.
- **Dependencies:** WT-101 and WT-202.
- **Source:** Product-flow review.

### WT-103: Connect Notion sync to the browser

- **Status:** Ready
- **Problem:** The Notion button and modal exist, but the browser does not check status or call the sync endpoint.
- **Desired outcome:** A user can publish a reviewed analysis to Notion and see exactly what was created.
- **Acceptance criteria:**
  - The UI detects whether Notion is configured and connected.
  - Sync is available only for a completed analysis.
  - The result shows the created meeting link and task success/failure counts.
  - Retrying cannot silently create duplicate meetings or tasks.
  - Partial success and API failures are presented clearly.
- **Dependencies:** WT-102, WT-201, and an idempotency decision.
- **Source:** Product-flow review.

### WT-104: Implement analysis result export controls

- **Status:** Ready
- **Problem:** Export controls exist in HTML but are not implemented in JavaScript.
- **Desired outcome:** Users can save useful analysis artifacts without Notion.
- **Acceptance criteria:**
  - Supported export formats are explicitly chosen and implemented.
  - Export includes a predictable subset of summary, decisions, action items, and cleaned transcript.
  - Filenames derive safely from the source recording.
  - Controls are hidden or disabled until an analysis is complete.
- **Dependencies:** WT-102.
- **Source:** Dormant browser UI.

## P1: Test and integration health

### WT-201: Declare and validate optional analysis and Notion dependencies

- **Status:** Ready
- **Problem:** Analysis and Notion code imports packages that are absent from the declared environment, including `notion_client`.
- **Desired outcome:** Core-only and full-feature installations are both intentional and testable.
- **Acceptance criteria:**
  - Optional dependency groups exist for local analysis, cloud analysis, and Notion as appropriate.
  - Missing optional features disable cleanly without breaking unrelated tests.
  - Full-feature CI installs and exercises the full declared integration set with mocks or safe fixtures.
  - Configuration documentation matches the dependency groups.
- **Dependencies:** WT-004.
- **Source:** Full-suite collection errors and existing TODO.

### WT-202: Repair analysis and Notion test collection

- **Status:** Ready
- **Problem:** Fourteen test modules fail during collection because of stale top-level imports, an obsolete historical path, unsafe dotenv discovery, and missing optional dependencies.
- **Desired outcome:** The entire suite collects from the current repository layout.
- **Acceptance criteria:**
  - Tests import from `src.analyzers` and `src.integrations`, or use a supported package layout.
  - No collected module resolves through `/Users/gio/Code/whisper_transcription` or any machine-specific path.
  - dotenv loading uses an explicit valid path or is isolated from unit tests.
  - Integration tests requiring credentials are marked and skipped safely when unavailable.
  - `pytest --collect-only` completes without errors.
- **Dependencies:** WT-201.
- **Source:** 2026-07-14 full-suite baseline and existing TODO.

### WT-203: Separate unit, integration, external-service, and real-audio tests

- **Status:** Ready
- **Problem:** The default suite mixes fast isolated tests with scripts that appear to require local models, credentials, historical files, or live Notion access.
- **Desired outcome:** Developers know which tests are safe, deterministic, and required at each validation level.
- **Acceptance criteria:**
  - Pytest markers define unit, integration, real-audio, Ollama, and Notion groups.
  - The default test command is deterministic and performs no external writes.
  - Live-service tests require explicit opt-in.
  - README_TESTING documents every supported command and expected prerequisites.
- **Dependencies:** WT-202.
- **Source:** Test-suite review.

### WT-204: Add a documented real-binary transcription test mode

- **Status:** Ready
- **Problem:** Pytest automatically selects mock transcription, with no documented standard path for verifying installed Whisper and FFmpeg binaries during tests.
- **Desired outcome:** Fast tests remain mocked, while an explicit command verifies the real local toolchain.
- **Acceptance criteria:**
  - An environment flag or marked test opts into real binaries.
  - The test uses a short committed or generated audio fixture.
  - The default suite remains fast and deterministic.
  - Documentation distinguishes mocked success from real transcription success.
- **Dependencies:** WT-203.
- **Source:** Existing TODO and baseline review.

## P2: Batch execution and state clarity

### WT-301: Decouple processing lifetime from one WebSocket connection

- **Status:** Needs decision
- **Problem:** Batch processing runs inside the WebSocket handler, making disconnect and reconnect behavior unreliable.
- **Desired outcome:** Processing behavior remains consistent with the recovery contract when a progress connection closes.
- **Acceptance criteria:**
  - A disconnect has an explicit effect: continue, cancel, or pause.
  - Reconnection receives current persisted state without starting duplicate work.
  - Progress delivery failures cannot corrupt job status.
  - Tests cover disconnect and reconnect during active work.
- **Dependencies:** WT-001.
- **Source:** Architecture review.

### WT-302: Replace the whole-batch global lock with explicit worker capacity

- **Status:** Ready
- **Problem:** One global lock is held for an entire batch while a separate semaphore controls per-file concurrency.
- **Desired outcome:** System capacity is expressed in one understandable policy and multiple batches cannot starve one another unexpectedly.
- **Acceptance criteria:**
  - A single configurable capacity limit governs active Whisper processes.
  - Scheduling behavior across batches is documented.
  - CPU, memory, and thermal safeguards remain intact.
  - Concurrency tests cover two simultaneous batches.
- **Dependencies:** WT-301.
- **Source:** Architecture review.

### WT-303: Clarify the authoritative state for jobs and files

- **Status:** Ready
- **Problem:** Job state is duplicated across SQLite, in-memory batch objects, browser state, uploaded files, transcript files, and IndexedDB.
- **Desired outcome:** Each state store has a documented responsibility and reconciliation behavior.
- **Acceptance criteria:**
  - Server job status has one authoritative representation.
  - Memory contains runtime handles rather than competing durable state.
  - Browser state can be rebuilt from server responses after refresh.
  - File absence and database state disagreement are detected and resolved predictably.
- **Dependencies:** WT-001 and WT-301.
- **Source:** Architecture review.

### WT-304: Decide the role and tracking policy for `whisper.db`

- **Status:** Needs decision
- **Problem:** The repository does not state whether the local SQLite database is disposable runtime state, a user artifact, or a tracked fixture.
- **Desired outcome:** Database ownership and version-control behavior are explicit.
- **Acceptance criteria:**
  - The database is either ignored as runtime state or replaced with a deliberate test fixture strategy.
  - No personal batch metadata can be committed accidentally.
  - Schema initialization and migrations work from a missing database.
  - SQLite uses DELETE journal mode and leaves no WAL artifacts.
- **Dependencies:** WT-303.
- **Source:** Existing TODO and repository rules.

## P2: Browser and product consistency

### WT-401: Align supported formats across frontend and backend

- **Status:** Ready
- **Problem:** The backend accepts OGG and FLAC, while browser validation rejects them.
- **Desired outcome:** One supported-format definition drives validation and user messaging.
- **Acceptance criteria:**
  - OGG and FLAC are consistently accepted or consistently removed.
  - File-picker attributes, client validation, server validation, tests, and documentation agree.
  - Rejection messages list the actual supported formats.
- **Dependencies:** None.
- **Source:** Architecture review and existing TODO.

### WT-402: Align concurrency language with actual behavior

- **Status:** Ready
- **Problem:** README and contributor documentation describe sequential processing, while the server runs two files concurrently by default.
- **Desired outcome:** Product copy, configuration, and runtime behavior describe the same processing model.
- **Acceptance criteria:**
  - Documentation states the actual default and why it exists.
  - UI wording does not imply strict sequential processing when concurrency is enabled.
  - The concurrency setting has a validated safe range.
- **Dependencies:** WT-302 may change the final wording.
- **Source:** Architecture review.

### WT-403: Make feature availability truthful in the UI

- **Status:** Ready
- **Problem:** HTML exposes analysis, Notion, and export controls that are hidden or non-functional rather than capability-driven.
- **Desired outcome:** The interface presents only actions that work in the current configuration.
- **Acceptance criteria:**
  - Capability endpoints drive visibility and disabled states.
  - Unconfigured optional features explain how to enable them without presenting dead controls.
  - Keyboard and screen-reader behavior remains correct as controls appear.
- **Dependencies:** WT-102 through WT-104.
- **Source:** Product-flow review.

### WT-404: Define single-file and batch post-transcription journeys

- **Status:** Needs decision
- **Problem:** The single-file flow exposes a preview and download, while batch completion saves files immediately and does not define how users select a transcript for analysis.
- **Desired outcome:** Both entry points have deliberate, understandable next actions.
- **Acceptance criteria:**
  - Product requirements state whether analysis supports single files, individual batch files, combined batches, or a subset.
  - The UI exposes the selected behavior without ambiguity.
  - Transcript ownership and naming remain predictable.
- **Dependencies:** WT-102.
- **Source:** Product-flow review.

### WT-405: Remove excessive debug logging from normal operation

- **Status:** Ready
- **Problem:** The server runs at DEBUG level and emits very verbose multipart, SQLite, and Whisper logs during ordinary use.
- **Desired outcome:** Normal operation is readable while detailed diagnostics remain available on demand.
- **Acceptance criteria:**
  - Default logging is INFO or WARNING.
  - A configuration flag enables detailed diagnostics.
  - Secrets, transcript content, and personal filenames are not logged unnecessarily.
- **Dependencies:** None.
- **Source:** 2026-07-14 manual run.

## P2: Documentation and repository hygiene

### WT-501: Update setup, run, and test documentation for `uv`

- **Status:** Ready
- **Problem:** Documentation and scripts prescribe raw Python, pip, and direct pytest commands, conflicting with repository rules and the working environment.
- **Desired outcome:** A new contributor can reproduce setup, server startup, smoke testing, and full testing with documented commands.
- **Acceptance criteria:**
  - README, README_TESTING, CONFIGURATION, CONTRIBUTING, setup, and run instructions agree.
  - All Python execution uses `uv run`.
  - The documented interpreter range matches WT-004.
  - Optional feature setup is separated from the core transcription setup.
- **Dependencies:** WT-004 and WT-201.
- **Source:** Baseline setup review.

### WT-502: Document current API and error semantics

- **Status:** Ready
- **Problem:** Upload formats and validation behavior changed without complete documentation.
- **Desired outcome:** API consumers and UI behavior share a precise contract.
- **Acceptance criteria:**
  - Supported formats and limits are documented.
  - Missing extension, unsupported extension, oversized file, corrupt audio, and partial batch acceptance semantics are specified.
  - README and changelog match automated tests.
- **Dependencies:** WT-401.
- **Source:** Existing TODO.

### WT-503: Modularize only along active feature boundaries

- **Status:** Ready
- **Problem:** `app.py` and `static/app.js` combine several responsibilities, but broad restructuring would add risk without immediate value.
- **Desired outcome:** New analysis and job-lifecycle work introduces focused modules without an unrelated rewrite.
- **Acceptance criteria:**
  - Analysis UI behavior is isolated from transcription upload behavior.
  - Job execution logic is separated from transport handlers when WT-301 is implemented.
  - Existing public behavior remains covered by tests during extraction.
  - No framework migration or speculative abstraction is introduced.
- **Dependencies:** Implement incrementally with WT-101, WT-102, and WT-301.
- **Source:** Reviewed architecture recommendation.

## P3: Product polish

### WT-601: Add a favicon and complete static asset polish

- **Status:** Ready
- **Problem:** Browsers request `/favicon.ico` and receive 404.
- **Desired outcome:** The local application has complete basic browser identity without noisy 404s.
- **Acceptance criteria:**
  - A favicon is served successfully.
  - The asset follows the project visual style and has appropriate sizes.
- **Dependencies:** None.
- **Source:** 2026-07-14 manual run.

### WT-602: Validate claimed accessibility and responsive behavior

- **Status:** Ready
- **Problem:** Documentation claims WCAG 2.1 AA and mobile friendliness, but the current baseline does not include an auditable UI acceptance suite.
- **Desired outcome:** Accessibility and responsive claims are supported by repeatable checks.
- **Acceptance criteria:**
  - Keyboard-only flows cover upload, progress, results, analysis, and Notion actions.
  - Screen-reader names and live-region announcements are verified.
  - Color contrast and responsive layouts are checked at documented breakpoints.
  - Any remaining limitations are stated accurately.
- **Dependencies:** Complete after WT-102 and WT-103 stabilize the interface.
- **Source:** Documentation review.

## Completed evidence

### WT-D001: Verify the existing local transcription path

- **Status:** Done
- **Outcome:** On 2026-07-14, the application accepted real audio, ran `whisper-cli` with Metal acceleration, reached 100 percent, wrote a transcript, and served it through the download endpoint.
- **Evidence:** Manual server log and successful HTTP download response during the test session.
