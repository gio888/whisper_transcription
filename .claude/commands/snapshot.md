---
description: End session - Create snapshot, update logs, commit and push to GitHub
---

# End Session Workflow

This command does EVERYTHING to properly end a session following the "one problem, one session, one update" discipline.

## Steps:

1. **Review session and capture decisions**:
   - Review this entire session from end to end
   - Identify any significant architectural decisions made
   - Note any decisions that should become ADRs (if project uses ADRs)
   - Draft any changelog entries for stakeholder communication

1b. **Handle incomplete problems (CRITICAL)**:
   - If problem NOT solved this session:
     - Write plan INLINE in CURRENT_STATE.md under "Active Session Plans" section
     - Include: Status, Plan steps, Blockers, Decisions needed
     - **NEVER reference `~/.claude/plans/`** (ephemeral, not committed to git)
   - If problem WAS solved:
     - Remove from "Active Session Plans" (if it was there)
     - Add to "Recent Accomplishments"
   - **WHY:** Plan files in ~/.claude/plans/ are NOT in git. Referencing them breaks session handoff.

2. **Create local snapshot** (for recovery):
   - Generate 2-4 word description using kebab-case (lowercase, hyphens)
   - Get current timestamp using: `date +%Y-%m-%d-%H%M%S`
   - Create `.claude/snapshots/YYYY-MM-DD-HHMMSS_description.md`
   - **EXACT FORMAT:** `2025-12-05-180530_ripestat-collection-complete.md`
   - **NOT:** `2025-12-05-180000_description.md` (don't round times)
   - **NOT:** `2025-12-05_description.md` (don't omit timestamp)
   - Create file with:
     - Problem solved
     - Decisions made (link to ADRs if created)
     - Metrics/validation
     - Modified files
     - Next steps

3. **Update TODO.md** (for LLM next action):
   - Review session and identify which TODOs were completed
   - Review session and identify new TODOs that emerged during work
   - Update TODO.md:
     - Mark completed items as done
     - Add new items to appropriate priority section
     - Update "Last updated" date

4. **Update CHANGELOG.md** (for stakeholders):
   - Review session for user-visible changes (features, fixes, breaking changes)
   - Draft CHANGELOG entries in appropriate categories:
     - Added / Changed / Deprecated / Removed / Fixed / Security
   - Add entries to "Unreleased" section
   - Use format: "Brief description (Session YYYY-MM-DD, ADR-NNNN if applicable)"

5. **MANDATORY: Verify all claims before writing** (CRITICAL - prevents false claims):

   Before writing ANYTHING to CURRENT_STATE.md, verify EVERY claim:

   **A. Number/Percentage Claims → Run Query or Command**
   ```
   CLAIM: "<some metric is X%>"
   VERIFY: Run the appropriate query/command to get actual value
   RESULT: <actual result>
   ```
   - If not verified → DO NOT WRITE THE CLAIM

   **B. File/Artifact Claims → Verify Exists**
   ```
   CLAIM: "Output ready at <path>"
   VERIFY: ls -la <path>
   RESULT: File exists, X rows/size
   ```
   - If file doesn't exist → DO NOT CLAIM "READY"

   **C. "Complete" Claims → Checklist Evidence**
   ```
   CLAIM: "<Task> complete"
   EVIDENCE:
   [x] Command/script ran successfully
   [x] Output verified (file exists, tests pass, etc.)
   [x] No errors in output
   ```
   - If any checkbox missing → DO NOT CLAIM "COMPLETE"

   **D. "Ready for X" Claims → Artifact Must Exist**
   - "Ready for review" → Review file must exist at known path
   - "Ready for production" → Tests must pass, shown in session
   - No artifact → say "needs X before ready" not "ready"

   **E. Counts/Metrics → Verify Immediately Before Writing**
   - Counts change. Don't copy from earlier in session.
   - Run fresh query/command, show result, then write.

   **RULE: If you cannot show evidence for a claim in THIS session, do not write the claim.**

6. **Update CURRENT_STATE.md** (for session resume):
   - Update `.claude/CURRENT_STATE.md` with:
     - Last session date and problem solved
     - Current accomplishments (rolling last 3 sessions)
     - Next 3 priority actions from TODO.md
     - **Active Session Plans** (if problem incomplete - see step 1b)
     - Current blockers (if any)
     - Open decisions (if any)
   - This file is what `/session-start` reads for context
   - **IMPORTANT:** All plans must be INLINE, never external file references
   - **IMPORTANT:** Every claim must have been verified in step 5

7. **Optional: Update SESSIONS.md** (weekly, not per-session):
   - Skip for individual sessions (reduces overhead)
   - Update weekly or after major milestones
   - Format when updating (add at TOP):

     ```markdown
     ## Week of YYYY-MM-DD: <Weekly Summary>
     **Sessions**: <count> sessions this week
     **Accomplishments**: <bullet list of key outcomes>
     **Decisions**: <links to ADRs created>
     **Next Week**: <planned focus>
     ```

8. **Execute git commit and push**:
   - Show summary of changes (`git diff --stat`)
   - Stage all changes: `git add .`
   - Generate commit message with format:

     ```text
     feat/fix/docs: <title>

     <description>


     ```

   - Commit the changes
   - Push to all configured remotes:
     - Get list of remotes: `git remote`
     - Get current branch: `git branch --show-current`
     - Push to each remote: `git push <remote> <branch>` for all remotes
   - If push fails:
     - Load SSH keys: `ssh-add --apple-load-keychain`
     - Retry the failed push
     - If still fails, show error and ask user

9. **Remind**:
   - "✅ Session complete and pushed! Type `/clear` for fresh context"
   - "Next session: Start with `/session-start` to resume from where you left off"
   - If ADRs created: "📝 New ADR(s) added"
   - If CHANGELOG updated: "📋 CHANGELOG.md updated for stakeholder communication"

---

**Keep snapshots ≤300 tokens. Focus on scannability.**
