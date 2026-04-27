# patch-application - Apply mock-interview-fixes.patch

## Status

- **Created**: 2026-04-27T12:03:00Z
- **Priority**: high
- **Session**: ses_23138aadeffeYxXhhc6lCeVXM0
- **Tags**: patch, git, fix

## TODOs

- [x] Fix interview_ws.py rejected hunks (4 hunks)
  - [x] Rename `payload` → `msg_payload` in message handling loop
  - [x] Add `_behavior_warning_last_sent.pop()` in WebSocketDisconnect handler
  - [x] Confirm _handle_behavior_frame uses correct key type
- [x] Fix package-lock.json rejected hunks (3 hunks) - Already present, no changes needed
- [ ] Clean up .rej files
- [ ] Verify patch application with git apply --check
- [ ] Create Git commit

## Details

### Problem Statement

The `mock-interview-fixes.patch` was applied using `git apply --reject`, but 2 files had rejected hunks that need manual fixing:

1. **backend/app/ws/interview_ws.py** - 4 hunks rejected
2. **frontend/package-lock.json** - 3 hunks rejected

### Plan

1. **Fix interview_ws.py**:
   - Lines 297-332: Change `payload` references to `msg_payload` (the variable was correctly renamed at line 290)
   - Lines 339-343: Add cleanup call `_behavior_warning_last_sent.pop(str(session_id), None)` in WebSocketDisconnect handler
   - Lines 762-764: Already using `str(session_id)` as key - confirm correct

2. **Fix package-lock.json**:
   - Add @playwright/test dependency in devDependencies
   - Add playwright and playwright-core in node_modules

3. **Cleanup**:
   - Remove *.rej files
   - Verify clean application

4. **Commit**:
   - Create commit with message: "fix: apply patch mock-interview-fixes.patch with manual fixes for rejected hunks"

## Execution Log

| Time | Action | Result |
|------|--------|--------|
| 2026-04-27T12:00 | git apply --reject mock-interview-fixes.patch | 17 files applied, 2 with rejects |
| 2026-04-27T12:03 | Created this plan | Pending |
| 2026-04-27T12:03 | ses_23138aadeffeYxXhhc6lCeVXM0 | Started |
