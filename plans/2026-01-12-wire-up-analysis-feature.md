# Plan: Wire Up Analysis/Meeting Minutes Feature

**Created:** 2026-01-12
**Status:** Pending implementation

## Summary
The backend analysis feature and HTML UI elements already exist but are disconnected. This plan wires them together so users can analyze transcripts and get meeting summaries, key decisions, and action items.

## Current State
- **Backend**: Fully functional (`/api/analyze-transcript`, `/ws/analyze/{id}`, `/api/sync-to-notion`)
- **HTML**: All UI elements exist but hidden with `display: none;`
- **JavaScript**: No event listeners or handlers for analysis functionality

## Files to Modify

| File | Changes |
|------|---------|
| [static/app.js](../static/app.js) | Add analysis methods, event listeners, WebSocket handling |
| [static/index.html](../static/index.html) | Remove `style="display: none;"` from key elements (conditional via JS) |

## Implementation Steps

### Step 1: Add DOM Element References
In `TranscriptionApp` constructor, add references to analysis elements:
- `analyzeBtn`, `analysisTabBtn`, `cleanedTabBtn`
- `analysisTab`, `cleanedTab`, `analysisContent`
- `analysisSummary`, `analysisDecisions`, `analysisDiscussion`, `analysisActions`
- `cleanedTranscript`, `analysisProgress`, `analysisProgressBar`, `analysisStatus`
- `notionSyncBtn`, `notionSyncModal`, `syncProgress`, `syncResults`, `syncSummary`
- `exportDropdown`

### Step 2: Add Feature Detection on Init
Add method `checkAnalysisFeatures()` that calls:
```javascript
// On app initialization
const [analysisStatus, notionStatus] = await Promise.all([
  fetch('/api/analysis-status').then(r => r.json()),
  fetch('/api/notion-status').then(r => r.json())
]);
this.analysisEnabled = analysisStatus.enabled;
this.notionEnabled = notionStatus.enabled && analysisStatus.enabled;
```

### Step 3: Show Analyze Button After Transcription
In `showResult()` method (~line 695), add:
```javascript
if (this.analysisEnabled) {
  this.analyzeBtn.style.display = 'inline-flex';
}
```

### Step 4: Add Event Listeners
In constructor or `init()`:
- `analyzeBtn.onclick` → `startAnalysis()`
- `analysisTabBtn.onclick` → `switchTab('analysis')`
- `cleanedTabBtn.onclick` → `switchTab('cleaned')`
- `notionSyncBtn.onclick` → `syncToNotion()`
- `closeSyncModal.onclick` → hide modal
- Tab buttons → `switchTab(tabName)`
- Export dropdown items → `exportAnalysis(format)`

### Step 5: Implement `startAnalysis()` Method
```javascript
async startAnalysis() {
  // 1. Get transcript text (from this.lastTranscript or batch file)
  // 2. POST to /api/analyze-transcript with transcript_text
  // 3. Get analysis_id from response
  // 4. Show progress UI
  // 5. Connect WebSocket to /ws/analyze/{analysis_id}
  // 6. Handle progress messages
  // 7. On completion, call displayAnalysisResults(result)
}
```

### Step 6: Implement `connectAnalysisWebSocket(analysisId)` Method
Handle message types:
- `status: "analyzing"` → update progress bar
- `status: "cleaning"` → update progress bar
- `status: "completed"` → call `displayAnalysisResults(message.result)`
- `status: "error"` → show error message

### Step 7: Implement `displayAnalysisResults(result)` Method
```javascript
displayAnalysisResults(result) {
  // 1. Hide progress, show analysis content
  // 2. Populate #analysisSummary with result.summary
  // 3. Populate #analysisDecisions with result.key_decisions (as <li> items)
  // 4. Populate #analysisDiscussion with result.discussion_points (as <li> items)
  // 5. Populate #analysisActions with result.action_items (formatted cards)
  // 6. Populate #cleanedTranscript with result.cleaned_transcript
  // 7. Show analysis tabs (#analysisTabBtn, #cleanedTabBtn)
  // 8. Show Notion sync button if this.notionEnabled
  // 9. Show export dropdown
  // 10. Store result in this.currentAnalysis for export/sync
}
```

### Step 8: Implement `switchTab(tabName)` Method
```javascript
switchTab(tabName) {
  // 1. Remove 'active' class from all tab buttons
  // 2. Add 'active' to clicked tab button
  // 3. Hide all .tab-pane elements
  // 4. Show the matching tab pane (#transcriptTab, #analysisTab, or #cleanedTab)
}
```

### Step 9: Implement `syncToNotion()` Method
```javascript
async syncToNotion() {
  // 1. Show #notionSyncModal with progress state
  // 2. POST to /api/sync-to-notion with analysis_id
  // 3. On success: show results with meeting URL and task count
  // 4. On error: show error message
}
```

### Step 10: Implement `exportAnalysis(format)` Method
```javascript
exportAnalysis(format) {
  // Generate content based on format (markdown, text, json)
  // Trigger download with appropriate filename
}
```

### Step 11: Handle Batch Mode (Per-File Analysis)
In batch mode, add an "Analyze" button to each completed file in the queue:
- Modify `updateFileStatus()` to add analyze button when file status = 'completed'
- Button click → `startAnalysis(fileId)` passing the specific file's transcript
- Analysis results shown in a modal or the main result section
- Each file can be analyzed independently

## State Variables to Add
```javascript
this.analysisEnabled = false;      // Set by /api/analysis-status
this.notionEnabled = false;        // Set by /api/notion-status
this.currentAnalysis = null;       // Stores completed analysis result
this.analysisWebSocket = null;     // WebSocket for analysis progress
this.lastTranscript = null;        // Store transcript for analysis
```

## Verification Steps
1. Run `python smoke_test.py` to verify backend still works
2. Start server with `./run.sh`
3. Test single file transcription → verify "Analyze Meeting" button appears
4. Click analyze → verify progress bar updates via WebSocket
5. Verify analysis results display in tabs (Summary, Decisions, Discussion, Actions)
6. Verify "Cleaned Transcript" tab shows formatted version
7. Test export dropdown (Markdown, Text, JSON formats)
8. If Notion configured: test "Sync to Notion" button
9. Test batch mode → verify analysis option available after completion
10. Hard refresh browser (Cmd+Shift+R) to ensure JS changes load

## Edge Cases to Handle
- Analysis feature disabled (no API keys) → don't show analyze button
- WebSocket disconnection during analysis → show retry option
- Empty analysis results (no decisions/actions) → show "None identified" message
- Long transcripts → backend handles chunking, frontend just shows progress
- Notion sync fails → show error with details, don't crash
