---
description: Resume from last session - Show context and next actions
---

# Start Session Workflow

Read current project state and help user pick next task.

## Steps:

1. **Load current state** (from .claude/CURRENT_STATE.md):
   - Read the entire CURRENT_STATE.md file
   - This contains:
     - Most recent accomplishment
     - Last 3 sessions summary
     - Next 3 priority actions
     - Current blockers
     - Open decisions
     - Project metrics

2. **Display session context**:
   ```
   📋 Last Session: YYYY-MM-DD
   ✅ Accomplished: <what was done>

   📊 Current State:
   - Progress: <current status/phase>
   - Metrics: <key project metrics from CURRENT_STATE.md>
   - Blockers: <any current blockers or "None">
   ```

3. **Show next priorities**:
   Display the "Next Priority Actions" from CURRENT_STATE.md:
   ```
   🎯 Next Priorities:

   1. [ ] <priority action 1>
   2. [ ] <priority action 2>
   3. [ ] <priority action 3>

   ⚠️ Open Decisions: <count> decisions pending
   ```

4. **Highlight important context**:
   If there are blockers or open decisions, mention them:
   ```
   💡 Context to consider:
   - Blocker: <blocker description>
   - Decision needed: <decision description>
   ```

5. **Prompt for action**:
   ```
   Which task would you like to work on?
   - Enter number (1, 2, 3...)
   - Or describe a different task
   - Or ask me to recommend based on priority and blockers
   ```

6. **Show Mandatory Workflow Reminder**:
   ```
   ⚠️ REMINDER: Before implementing, I MUST follow proper workflow:

   1. Context Loading (Read CLAUDE.md, CURRENT_STATE.md, and any project-specific docs)
   2. Design Review (Draft approach, consider alternatives)
   3. Spec Compliance Check (Follow project architecture and conventions)
   4. User Approval (Present design before major changes)
   5. Implementation (Only after approval)
   6. Validation (Verify changes work as expected)

   I will NOT write code without following these steps.
   ```

7. **Prepare to work**:
   - Once user picks a task, acknowledge and say:
     "Let's work on: <task description>"
     "Before I start, I'll follow the workflow:"
     "1. Load context from project docs"
     "2. Draft design approach"
     "3. Present plan for approval"
     "4. Then implement"

---

**Purpose**: Load current state from CURRENT_STATE.md for efficient session resume.

**CRITICAL**: The workflow reminder ensures I don't jump straight to coding without reading context and getting design approval first.
