# Plan: Fix All Issues and Optimize Mock Interview Project

## TL;DR
> **Summary**: Fix all frontend ESLint/React issues and backend code quality, optimize configurations, and prepare for future frontend rewrite.
> **Deliverables**: Clean ESLint output, no cascading render warnings, working build, fixed docker-compose path, optimized backend
> **Effort**: Medium
> **Parallel**: YES - 2 waves
> **Critical Path**: ESLint fixes → Build verification → Backend review → Docker fixes

## Context
User requested fixing all issues in the Mock Interview project while preparing for a future frontend rewrite. Initial scan revealed:
- 3 ESLint errors, 2 warnings in frontend
- TypeScript compiles cleanly
- Backend code needs review
- Docker-compose frontend build path issue

## Work Objectives

### Core Objective
Fix all discoverable issues without breaking functionality, optimize code quality, and prepare codebase for future rewrite.

### Deliverables
1. Frontend ESLint errors fixed (3 errors: unused var, 2 cascading setState)
2. Frontend builds successfully without errors
3. useEffect dependencies cleaned up
4. Docker-compose frontend build path corrected
5. Backend code reviewed and optimized (async patterns, security, error handling)

### Definition of Done
- `npm run lint` shows 0 errors (warnings acceptable)
- `npm run build` succeeds
- Docker compose config validates
- Backend has no obvious issues

### Must Have
- LoginPage.tsx unused variable fixed
- LlmRuntimePanel.tsx cascading setState fixed
- InterviewRoom.tsx cascading setState fixed
- useEffect dependencies properly handled

### Must NOT Have
- No breaking changes to API contracts
- No deletion of functionality
- No AI slop patterns

## Verification Strategy
- Run `npm run lint` after each fix
- Run `npm run build` after all fixes
- Validate docker-compose config

## Execution Strategy

### Wave 1: Frontend ESLint Fixes (Parallel)
- Task 1: Fix LoginPage.tsx unused variable `err`
- Task 2: Fix LlmRuntimePanel.tsx cascading setState in useEffect
- Task 3: Fix InterviewRoom.tsx cascading setState in useEffect

### Wave 2: Build Verification & Docker Fixes
- Task 4: Verify frontend builds successfully
- Task 5: Fix docker-compose.frontend build context path
- Task 6: Run final lint check

## TODOs

### Wave 1

- [ ] 1. Fix LoginPage.tsx unused `err` variable

  **What to do**: Remove unused `err` variable from catch block, replace with `catch` only.
  **Must NOT do**: Do not change error handling logic

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: Single file, obvious fix
  - Skills: [] 
  - Omitted: [] 

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: None | Blocked By: None

  **Acceptance Criteria**:
  - [ ] LoginPage.tsx lint check passes

  **QA Scenarios**:
  ```
  Scenario: LoginPage lint passes
    Tool: Bash
    Steps: cd frontend && npm run lint 2>&1 | grep -c "LoginPage"
    Expected: 0 occurrences of LoginPage in lint output
  ```

- [ ] 2. Fix LlmRuntimePanel.tsx cascading setState in useEffect

  **What to do**: Refactor to use functional update pattern or refactor logic to avoid synchronous setState in effect. Best approach: use useMemo + conditional initialization pattern.
  **Must NOT do**: Do not remove functionality, do not break the data loading

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: Single file, pattern-based fix
  - Skills: [] 
  - Omitted: [] 

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: None | Blocked By: None

  **Acceptance Criteria**:
  - [ ] LlmRuntimePanel.tsx cascading render error fixed

  **QA Scenarios**:
  ```
  Scenario: LlmRuntimePanel lint passes
    Tool: Bash
    Steps: cd frontend && npm run lint 2>&1 | grep -c "LlmRuntimePanel"
    Expected: 0 occurrences in lint errors
  ```

- [ ] 3. Fix InterviewRoom.tsx cascading setState in useEffect

  **What to do**: Refactor useEffect (lines 282-307) to avoid synchronous setState. Use callback-based initialization pattern or separate initialization logic. Also fix missing dependency warnings for sendBehaviorFrame and currentOrigin.
  **Must NOT do**: Do not break microphone initialization, do not remove error handling

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: Single file, pattern-based fix
  - Skills: [] 
  - Omitted: [] 

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: None | Blocked By: None

  **Acceptance Criteria**:
  - [ ] InterviewRoom.tsx cascading render error fixed
  - [ ] useEffect dependency warnings resolved

  **QA Scenarios**:
  ```
  Scenario: InterviewRoom lint passes
    Tool: Bash
    Steps: cd frontend && npm run lint 2>&1 | grep "InterviewRoom"
    Expected: No errors related to InterviewRoom
  ```

### Wave 2

- [ ] 4. Verify frontend builds successfully

  **What to do**: Run `npm run build` to verify TypeScript compilation and production build succeeds.
  **Must NOT do**: Do not modify any files during this check

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: Verification task
  - Skills: [] 
  - Omitted: [] 

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: None | Blocked By: Tasks 1-3

  **Acceptance Criteria**:
  - [ ] npm run build exits with code 0

  **QA Scenarios**:
  ```
  Scenario: Frontend builds
    Tool: Bash
    Steps: cd frontend && npm run build 2>&1
    Expected: Build completes without errors
  ```

- [ ] 5. Fix docker-compose.frontend build context path

  **What to do**: The docker-compose.gpu.yml has `context: ./frontend` and `dockerfile: ../docker/frontend/Dockerfile`. This is inconsistent. The frontend Dockerfile should be at `frontend/Dockerfile` or the path should be corrected to `../docker/frontend/Dockerfile` relative to the context.
  **Must NOT do**: Do not break the build

  **Recommended Agent Profile**:
  - Category: `unspecified-low` - Reason: Configuration fix
  - Skills: [] 
  - Omitted: [] 

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: None | Blocked By: None

  **Acceptance Criteria**:
  - [ ] docker-compose config validates

  **QA Scenarios**:
  ```
  Scenario: Docker compose validates
    Tool: Bash
    Steps: docker compose -f docker-compose.gpu.yml config --quiet 2>&1
    Expected: No errors
  ```

- [ ] 6. Run final lint check

  **What to do**: Run full lint check and confirm all errors are resolved.
  **Must NOT do**: N/A

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: Verification
  - Skills: [] 
  - Omitted: [] 

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: None | Blocked By: Tasks 1-3

  **Acceptance Criteria**:
  - [ ] npm run lint shows 0 errors (warnings OK)

  **QA Scenarios**:
  ```
  Scenario: Final lint check
    Tool: Bash
    Steps: cd frontend && npm run lint 2>&1
    Expected: 0 errors, warnings acceptable
  ```

## Final Verification Wave
> After all implementation tasks complete, verify the project is in good state.

- [ ] F1. ESLint check - 0 errors
- [ ] F2. TypeScript build - succeeds
- [ ] F3. Docker compose - validates

## Success Criteria
- Frontend `npm run lint` shows 0 errors ✅
- Frontend `npm run build` succeeds ⚠️ (blocked by node_modules permissions - requires sudo)
- Docker compose configuration is valid ✅

## Completed Fixes

### Frontend (All Done)
1. ✅ LoginPage.tsx - unused `err` variable removed
2. ✅ LlmRuntimePanel.tsx - cascading setState fixed (async function pattern)
3. ✅ InterviewRoom.tsx - cascading setState fixed, ref pattern for sendBehaviorFrame, currentOrigin deps added
4. ✅ button.tsx - asChild prop support added with Slot component
5. ✅ ESLint - 0 errors remaining

### Backend (All Done)
1. ✅ interview_ws.py - session ownership validation added (4403 FORBIDDEN)
2. ✅ interview_ws.py - behavior warning cooldown implemented (was unused constant)
3. ✅ interview_ws.py - import math moved to module level
4. ✅ interviewer_agent.py - proper logging for caught exceptions
5. ✅ session.py - user_id field and relationship added
6. ✅ interview.py - create_session sets user_id=current_user.id

### Docker Compose
- ✅ Valid - path was correct

## Blocked Issue

**node_modules permissions**: The `node_modules` directory is owned by root and cannot be modified without sudo. The non-root user (cnhyk) cannot run `npm run build` because TypeScript needs to write to `node_modules/.tmp`.

**Fix command** (requires sudo):
```bash
sudo chown -R cnhyk:cnhyk /home/cnhyk/Interview/mock-interview/frontend/node_modules
```

After fixing permissions, run:
```bash
cd /home/cnhyk/Interview/mock-interview/frontend && npm run build
```

## Verification Summary

| Check | Status |
|-------|--------|
| Frontend ESLint | ✅ 0 errors |
| TypeScript Compile | ✅ Passes |
| Python Syntax | ✅ All files valid |
| Docker Compose Config | ✅ Valid |
| Backend Session Ownership | ✅ Implemented |
| Backend Exception Logging | ✅ Implemented |
| Frontend Build | ⚠️ Blocked (permissions) |