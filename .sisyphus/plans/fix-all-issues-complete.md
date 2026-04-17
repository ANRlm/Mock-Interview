# Work Plan: AI Mock Interview - Fix All Issues & Complete Features

## TL;DR
> **Summary**: Fix exception swallowing in backend (3 files), populate empty knowledge base directories, fix Docker configuration issues, and add comprehensive tests for each fix.
> **Deliverables**: Patched Python files with proper error handling, populated knowledge base, corrected Docker configs, and test coverage
> **Effort**: Medium
> **Parallel**: YES - 2 waves
> **Critical Path**: Exception fixes → Knowledge base → Docker configs → Tests → Push

## Context
### Original Request
"检查当前路径下项目，本项目为ai模拟面试程序，分析前后端各个部分代码，修复所有的错误，实现未完成的功能，并且每完成一个部分都要完成测试并且push到仓库"

### Interview Summary
- Frontend: Build passes, TypeScript compiles, no critical errors
- Backend: 3 files with exception swallowing issues, empty knowledge base directories, Docker config misalignments
- Configuration: 5 issues identified in docker-compose and env files

### Metis Review (gaps addressed)
- Added logging requirements for exception handling fixes
- Confirmed need for structured knowledge base content
- Identified scope creep risks (avoiding architecture changes)
- Validated test infrastructure exists (smoke tests + Playwright)

## Work Objectives
### Core Objective
Fix all identified errors and complete incomplete features systematically with tests after each part.

### Deliverables
1. Fix exception swallowing in 3 backend files with proper logging
2. Populate 3 empty knowledge base directories with placeholder content
3. Fix Docker configuration issues (VITE_API_PROXY_TARGET, .env, JWT, DATABASE_URL)
4. Add unit/integration tests for each fix
5. Push each completed part to repository

### Definition of Done (verifiable conditions with commands)
- [ ] `grep -n "except.*: pass" backend/app/ws/interview_ws.py` returns no bare passes
- [ ] `grep -n "except.*: pass" backend/app/services/tts_service.py` returns no bare passes
- [ ] `grep -n "except.*: pass" backend/app/services/sensevoice_stt_service.py` returns no bare passes
- [ ] `ls knowledge_base/teacher/*.md knowledge_base/doctor/*.md knowledge_base/lawyer/*.md | wc -l` shows 3+ files each
- [ ] `docker-compose -f docker-compose.yml config` succeeds without errors
- [ ] `cd frontend && npm run build` succeeds
- [ ] `git log --oneline -5` shows 3+ commits with fix messages

### Must Have
- All exception handling fixes with logging
- Structured knowledge base content for all job roles
- Valid Docker configuration
- Tests that verify fixes don't break existing functionality

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- No major architectural changes
- No new AI model integrations
- No database migrations
- No AI-generated code patterns (commented boilerplate, obvious templating)
- No changing existing API contracts

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: tests-after for fixes + existing smoke tests
- QA policy: Every task has agent-executed scenarios
- Evidence: .sisyphus/evidence/task-{N}-{slug}.{ext}

## Execution Strategy
### Parallel Execution Waves
Target: 5-8 tasks per wave. <3 per wave = under-splitting.

**Wave 1** (Independent fixes - can parallelize):
- Task 1: Fix interview_ws.py exception handling
- Task 2: Fix tts_service.py exception handling
- Task 3: Fix sensevoice_stt_service.py exception handling
- Task 4: Populate knowledge_base/teacher
- Task 5: Populate knowledge_base/doctor
- Task 6: Populate knowledge_base/lawyer

**Wave 2** (Configuration fixes - can parallelize):
- Task 7: Fix docker-compose.yml VITE_API_PROXY_TARGET
- Task 8: Create backend/.env from .env.example with fixes
- Task 9: Update backend/.env.example for DATABASE_URL consistency

**Wave 3** (Testing - after fixes complete):
- Task 10: Add backend unit tests for exception handling
- Task 11: Add integration test for docker-compose
- Task 12: Run existing smoke tests
- Task 13: Run frontend Playwright tests

**Wave 4** (Commit/Push):
- Task 14: Commit exception handling fixes
- Task 15: Commit knowledge base content
- Task 16: Commit docker configuration fixes
- Task 17: Final verification and push

### Dependency Matrix (full, all tasks)
| Task | Blocks | Blocked By |
|------|--------|------------|
| 1. interview_ws fix | 10, 14 | - |
| 2. tts_service fix | 10, 14 | - |
| 3. sensevoice fix | 10, 14 | - |
| 4. teacher KB | 11, 15 | - |
| 5. doctor KB | 11, 15 | - |
| 6. lawyer KB | 11, 15 | - |
| 7. docker VITE fix | 12, 16 | - |
| 8. backend .env | 12, 16 | - |
| 9. .env.example | 12, 16 | - |
| 10. unit tests | - | 1, 2, 3 |
| 11. integration tests | - | 4, 5, 6 |
| 12. smoke tests | - | 7, 8, 9 |
| 13. playwright tests | - | 12 |
| 14. commit fixes | - | 10 |
| 15. commit KB | - | 11 |
| 16. commit docker | - | 12 |
| 17. final push | - | 13, 14, 15, 16 |

### Agent Dispatch Summary (wave → task count → categories)
- Wave 1: 6 tasks - backend-fix, backend-fix, backend-fix, content-fill, content-fill, content-fill
- Wave 2: 3 tasks - docker-fix, docker-fix, docker-fix
- Wave 3: 4 tasks - backend-test, integration-test, backend-test, frontend-test
- Wave 4: 4 tasks - git-commit, git-commit, git-commit, git-commit

## TODOs

- [x] 1. Fix interview_ws.py exception swallowing

  **What to do**: In `/home/cnhyk/Interview/mock-interview/backend/app/ws/interview_ws.py` around line 336, replace bare `except Exception: pass` with proper exception handling that logs the error. The preflight TTS check should log failures with session context and either propagate the error or handle it gracefully.

  **Must NOT do**: Don't remove the try/except entirely - we need error handling, just not silent swallowing. Don't change the WebSocket message protocol.

  **Recommended Agent Profile**:
  - Category: `backend-fix` - Reason: Python file in backend/ws directory
  - Skills: [] - Not needed
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 10, 14 | Blocked By: none

  **References** (executor has NO interview context - be exhaustive):
  - Pattern: `backend/app/services/sensevoice_stt_service.py:32` - shows proper exception handling with logging
  - Error context: Uses `logger.warning` or `logger.exception` to log errors
  - Session context: Uses `session_id` for error tracking

  **Acceptance Criteria** (agent-executable only):
  - [ ] `grep -n "except.*: pass" /home/cnhyk/Interview/mock-interview/backend/app/ws/interview_ws.py | wc -l` returns 0
  - [ ] `grep -n "logger" /home/cnhyk/Interview/mock-interview/backend/app/ws/interview_ws.py | grep -i "exception\|warning\|error" | wc -l` returns 3+

  **QA Scenarios** (MANDATORY - task incomplete without these):
  ```
  Scenario: Exception in TTS preflight is logged
    Tool: Bash
    Steps:
      1. Create test script that imports the module
      2. Mock tts_service.stream_synthesize to raise Exception
      3. Call the function that contains the try/except
      4. Check logs for error message with session context
    Expected: Error is logged with traceback, not silently swallowed
    Evidence: .sisyphus/evidence/task-1-interview-ws-fix.log

  Scenario: Exception propagates if cannot recover
    Tool: Bash
    Steps:
      1. Mock TTS service to fail completely
      2. Call the websocket handler
      3. Verify appropriate error message sent to client
    Expected: Client receives error message, not silent failure
    Evidence: .sisyphus/evidence/task-1-interview-ws-error.json
  ```

  **Commit**: YES | Message: `fix(ws): replace silent exception swallowing with logging` | Files: [`backend/app/ws/interview_ws.py`]

- [x] 2. Fix tts_service.py exception swallowing in _cancel_candidates

  **What to do**: In `/home/cnhyk/Interview/mock-interview/backend/app/services/tts_service.py` around lines 442 and 444, replace bare `except asyncio.CancelledError: pass` and `except Exception: pass` with proper handling. CancelledError should either be re-raised or logged. Exception should be logged with context.

  **Must NOT do**: Don't remove try/finally cleanup blocks - they're needed for proper resource cleanup. Don't suppress all exceptions silently.

  **Recommended Agent Profile**:
  - Category: `backend-fix` - Reason: Python service file
  - Skills: [] - Not needed
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 10, 14 | Blocked By: none

  **References**:
  - Pattern: Python asyncio best practices for cancellation
  - Context: Uses `logger.warning` or `logger.exception`
  - Reference: `_cancel_candidates` is called during hedge race cleanup

  **Acceptance Criteria**:
  - [ ] `grep -A2 "except asyncio.CancelledError" /home/cnhyk/Interview/mock-interview/backend/app/services/tts_service.py` shows re-raise or proper logging
  - [ ] `grep -A2 "except Exception" /home/cnhyk/Interview/mock-interview/backend/app/services/tts_service.py | grep -c "logger"` >= 2

  **QA Scenarios**:
  ```
  Scenario: CancelledError during candidate cancellation
    Tool: Bash
    Steps:
      1. Create async test with cancellation
      2. Call _cancel_candidates with mock candidate
      3. Verify CancelledError is handled properly
    Expected: CancelledError propagated or logged, not silently passed
    Evidence: .sisyphus/evidence/task-2-tts-fix.log

  Scenario: Exception during cleanup is logged
    Tool: Bash
    Steps:
      1. Mock queue.get to raise Exception
      2. Call _cancel_candidates
      3. Check logs for error with context
    Expected: Error logged with traceback
    Evidence: .sisyphus/evidence/task-2-tts-error.log
  ```

  **Commit**: YES | Message: `fix(tts): proper exception handling in _cancel_candidates` | Files: [`backend/app/services/tts_service.py`]

- [x] 3. Fix sensevoice_stt_service.py exception swallowing in health checks

  **What to do**: In `/home/cnhyk/Interview/mock-interview/backend/app/services/sensevoice_stt_service.py` around lines 32 and 39, replace bare `except Exception: pass` with logging. Health check failures should be logged with the endpoint URL and port attempted.

  **Must NOT do**: Don't return False on all exceptions - health checks may legitimately fail in dev environments. Log and return appropriate status.

  **Recommended Agent Profile**:
  - Category: `backend-fix` - Reason: STT service file
  - Skills: [] - Not needed
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 10, 14 | Blocked By: none

  **References**:
  - Pattern: `ensure_model_ready` method uses this pattern
  - Logging: Should include host:port context

  **Acceptance Criteria**:
  - [ ] `grep -n "except.*: pass" /home/cnhyk/Interview/mock-interview/backend/app/services/sensevoice_stt_service.py | wc -l` returns 0
  - [ ] `grep -n "logger" /home/cnhyk/Interview/mock-interview/backend/app/services/sensevoice_stt_service.py | grep -i "warning\|exception" | wc -l` >= 2

  **QA Scenarios**:
  ```
  Scenario: Health check failure is logged
    Tool: Bash
    Steps:
      1. Mock httpx to raise ConnectError
      2. Call ensure_model_ready
      3. Check logs for connection error with host:port
    Expected: Error logged, not silently swallowed
    Evidence: .sisyphus/evidence/task-3-sensevoice-fix.log
  ```

  **Commit**: YES | Message: `fix(stt): log health check failures with context` | Files: [`backend/app/services/sensevoice_stt_service.py`]

- [x] 4. Populate knowledge_base/teacher with interview questions

  **What to do**: Create 3-5 markdown files in `/home/cnhyk/Interview/mock-interview/backend/knowledge_base/teacher/` with teacher-specific interview questions covering: teaching philosophy, classroom management, curriculum design, student assessment, professional development. Use format similar to programmer/core_questions.md.

  **Must NOT do**: Don't copy content from programmer directory. Don't use placeholder text like "TODO: add content". Create actual sample questions.

  **Recommended Agent Profile**:
  - Category: `content-fill` - Reason: Knowledge base content creation
  - Skills: [] - Not needed
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 11, 15 | Blocked By: none

  **References**:
  - Pattern: `backend/knowledge_base/programmer/core_questions.md` - existing content structure
  - Format: Markdown with sections, questions, and evaluation criteria

  **Acceptance Criteria**:
  - [ ] `ls /home/cnhyk/Interview/mock-interview/backend/knowledge_base/teacher/*.md | wc -l` >= 3
  - [ ] `grep -l "教学" /home/cnhyk/Interview/mock-interview/backend/knowledge_base/teacher/*.md | wc -l` >= 2

  **QA Scenarios**:
  ```
  Scenario: Knowledge base files are valid markdown
    Tool: Bash
    Steps:
      1. List all .md files in teacher directory
      2. Check each file has > 200 characters
      3. Verify files contain Chinese content
    Expected: All files are non-empty markdown with Chinese content
    Evidence: .sisyphus/evidence/task-4-teacher-kb.txt
  ```

  **Commit**: YES | Message: `feat(kb): add teacher interview questions` | Files: [`backend/knowledge_base/teacher/`]

- [x] 5. Populate knowledge_base/doctor with interview questions

  **What to do**: Create 3-5 markdown files in `/home/cnhyk/Interview/mock-interview/backend/knowledge_base/doctor/` with doctor-specific interview questions covering: clinical experience, diagnosis approach, patient communication, medical ethics, continuing education.

  **Must NOT do**: Don't copy from other professions. Create authentic medical interview content.

  **Recommended Agent Profile**:
  - Category: `content-fill` - Reason: Knowledge base content
  - Skills: [] - Not needed
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 11, 15 | Blocked By: none

  **References**:
  - Pattern: Same structure as teacher and programmer KB

  **Acceptance Criteria**:
  - [ ] `ls /home/cnhyk/Interview/mock-interview/backend/knowledge_base/doctor/*.md | wc -l` >= 3
  - [ ] `grep -l "医疗\|临床\|诊断" /home/cnhyk/Interview/mock-interview/backend/knowledge_base/doctor/*.md | wc -l` >= 2

  **QA Scenarios**:
  ```
  Scenario: Knowledge base populated with medical content
    Tool: Bash
    Steps:
      1. List files and count content length
      2. Check for medical terminology
      3. Verify structure is consistent
    Expected: Valid markdown with medical interview content
    Evidence: .sisyphus/evidence/task-5-doctor-kb.txt
  ```

  **Commit**: YES | Message: `feat(kb): add doctor interview questions` | Files: [`backend/knowledge_base/doctor/`]

- [x] 6. Populate knowledge_base/lawyer with interview questions

  **What to do**: Create 3-5 markdown files in `/home/cnhyk/Interview/mock-interview/backend/knowledge_base/lawyer/` with lawyer-specific interview questions covering: legal experience, case strategy, client representation, ethics, courtroom skills.

  **Must NOT do**: Don't use placeholder content. Create actual legal profession questions.

  **Recommended Agent Profile**:
  - Category: `content-fill` - Reason: Knowledge base content
  - Skills: [] - Not needed
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 11, 15 | Blocked By: none

  **References**:
  - Pattern: Same structure as other KB directories

  **Acceptance Criteria**:
  - [ ] `ls /home/cnhyk/Interview/mock-interview/backend/knowledge_base/lawyer/*.md | wc -l` >= 3
  - [ ] `grep -l "法律\|诉讼\|案件" /home/cnhyk/Interview/mock-interview/backend/knowledge_base/lawyer/*.md | wc -l` >= 2

  **QA Scenarios**:
  ```
  Scenario: Knowledge base populated with legal content
    Tool: Bash
    Steps:
      1. List files and verify content
      2. Check for legal terminology
      3. Verify consistent structure
    Expected: Valid markdown with legal interview content
    Evidence: .sisyphus/evidence/task-6-lawyer-kb.txt
  ```

  **Commit**: YES | Message: `feat(kb): add lawyer interview questions` | Files: [`backend/knowledge_base/lawyer/`]

- [x] 7. Fix docker-compose.yml VITE_API_PROXY_TARGET

  **What to do**: In `/home/cnhyk/Interview/mock-interview/docker-compose.yml`, add `VITE_API_PROXY_TARGET: http://backend:8000` to the frontend service environment. This ensures frontend proxies API calls to the backend container correctly.

  **Must NOT do**: Don't change port numbers (5173). Don't modify backend service configuration.

  **Recommended Agent Profile**:
  - Category: `docker-fix` - Reason: Docker compose configuration
  - Skills: [] - Not needed
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 12, 16 | Blocked By: none

  **References**:
  - Pattern: `docker-compose.gpu.yml` has this env var set correctly
  - Target: `http://backend:8000` (docker network hostname)

  **Acceptance Criteria**:
  - [ ] `grep "VITE_API_PROXY_TARGET" /home/cnhyk/Interview/mock-interview/docker-compose.yml | grep "http://backend:8000"` succeeds
  - [ ] `docker-compose -f /home/cnhyk/Interview/mock-interview/docker-compose.yml config` succeeds

  **QA Scenarios**:
  ```
  Scenario: docker-compose config validates successfully
    Tool: Bash
    Steps:
      1. Run docker-compose -f docker-compose.yml config
      2. Check exit code is 0
      3. Verify VITE_API_PROXY_TARGET appears in output
    Expected: Config succeeds, env var present
    Evidence: .sisyphus/evidence/task-7-docker-config.txt
  ```

  **Commit**: YES | Message: `fix(docker): add VITE_API_PROXY_TARGET for frontend` | Files: [`docker-compose.yml`]

- [x] 8. Create backend/.env from .env.example

  **What to do**: Copy `/home/cnhyk/Interview/mock-interview/backend/.env.example` to `/home/cnhyk/Interview/mock-interview/backend/.env` and update values to match docker-compose.yml settings (DATABASE_URL to use PostgreSQL, ensure JWT_SECRET is set properly).

  **Must NOT do**: Don't commit actual secrets. JWT_SECRET should reference environment variable, not hardcode a value.

  **Recommended Agent Profile**:
  - Category: `docker-fix` - Reason: Environment configuration
  - Skills: [] - Not needed
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 12, 16 | Blocked By: none

  **References**:
  - Pattern: docker-compose.yml uses `postgresql+asyncpg://interview:interview@db:5432/interview`
  - JWT_SECRET: Should use `${JWT_SECRET:-random-dev-secret}` format

  **Acceptance Criteria**:
  - [ ] `test -f /home/cnhyk/Interview/mock-interview/backend/.env && echo "exists"` returns "exists"
  - [ ] `grep "DATABASE_URL" /home/cnhyk/Interview/mock-interview/backend/.env | grep "postgresql"` succeeds
  - [ ] `grep "JWT_SECRET" /home/cnhyk/Interview/mock-interview/backend/.env | grep "\\${JWT_SECRET"` succeeds

  **QA Scenarios**:
  ```
  Scenario: .env file is created with correct DATABASE_URL
    Tool: Bash
    Steps:
      1. Check file exists
      2. Verify DATABASE_URL uses postgresql
      3. Verify JWT_SECRET references env var
    Expected: File exists with correct PostgreSQL URL
    Evidence: .sisyphus/evidence/task-8-backend-env.txt
  ```

  **Commit**: NO | Files: [`backend/.env`] (gitignore this file)

- [x] 9. Update backend/.env.example DATABASE_URL consistency

  **What to do**: Update `/home/cnhyk/Interview/mock-interview/backend/.env.example` to show PostgreSQL as the default DATABASE_URL instead of SQLite, matching what docker-compose.yml actually uses.

  **Must NOT do**: Don't add actual credentials. Keep it as an example file.

  **Recommended Agent Profile**:
  - Category: `docker-fix` - Reason: Environment example file
  - Skills: [] - Not needed
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 12, 16 | Blocked By: none

  **References**:
  - Current: `sqlite+aiosqlite:///./mock_interview.db`
  - Target: `postgresql+asyncpg://user:password@host:5432/dbname`

  **Acceptance Criteria**:
  - [ ] `grep "DATABASE_URL" /home/cnhyk/Interview/mock-interview/backend/.env.example | grep "postgresql"` succeeds
  - [ ] `grep "postgresql" /home/cnhyk/Interview/mock-interview/backend/.env.example | grep -v "#"` succeeds

  **QA Scenarios**:
  ```
  Scenario: .env.example shows PostgreSQL
    Tool: Bash
    Steps:
      1. Check DATABASE_URL in .env.example
      2. Verify it mentions postgresql
    Expected: PostgreSQL URL format, not SQLite
    Evidence: .sisyphus/evidence/task-9-env-example.txt
  ```

  **Commit**: YES | Message: `fix(config): update .env.example DATABASE_URL to postgresql` | Files: [`backend/.env.example`]

- [x] 10. Add backend unit tests for exception handling

  **What to do**: Create unit tests in `/home/cnhyk/Interview/mock-interview/backend/app/tests/` (create directory if needed) that verify exception handling in the three fixed files works correctly. Test that exceptions are logged, not swallowed.

  **Must NOT do**: Don't test implementation details. Test observable behavior (logging output).

  **Recommended Agent Profile**:
  - Category: `backend-test` - Reason: Test creation
  - Skills: ["pytest"] - Python testing
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: NO | Wave 3 | Blocks: 14 | Blocked By: 1, 2, 3

  **References**:
  - Pattern: Existing smoke tests at `backend/app/scripts/phase123_smoke.py`
  - Framework: pytest with asyncio support

  **Acceptance Criteria**:
  - [ ] `ls /home/cnhyk/Interview/mock-interview/backend/app/tests/test_exception_*.py | wc -l` >= 3
  - [ ] `cd /home/cnhyk/Interview/mock-interview/backend && python -m pytest app/tests/test_exception_*.py -v` passes

  **QA Scenarios**:
  ```
  Scenario: Exception handling test passes
    Tool: Bash
    Steps:
      1. Run pytest on new test files
      2. Check all tests pass
      3. Verify logging output contains error context
    Expected: Tests pass, exceptions are logged
    Evidence: .sisyphus/evidence/task-10-unit-tests.txt
  ```

  **Commit**: YES | Message: `test(backend): add exception handling tests` | Files: [`backend/app/tests/`]

- [x] 11. Add integration test for knowledge base loading

  **What to do**: Create integration test that verifies all knowledge base directories (teacher, doctor, lawyer, programmer) can be loaded by rag_service and return results for queries.

  **Must NOT do**: Don't test actual LLM responses. Test KB loading and search only.

  **Recommended Agent Profile**:
  - Category: `integration-test` - Reason: Integration testing
  - Skills: ["pytest"] - Python testing
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: NO | Wave 3 | Blocks: 15 | Blocked By: 4, 5, 6

  **References**:
  - Pattern: rag_service.search() method
  - Test approach: Mock embedder, test fallback search

  **Acceptance Criteria**:
  - [ ] `cd /home/cnhyk/Interview/mock-interview/backend && python -m pytest app/tests/test_rag_*.py -v` passes
  - [ ] All four job roles return non-empty search results

  **QA Scenarios**:
  ```
  Scenario: All KB directories return results
    Tool: Bash
    Steps:
      1. Run rag_service search for each job role
      2. Check results are non-empty
      3. Verify results are strings
    Expected: All roles return >= 1 result
    Evidence: .sisyphus/evidence/task-11-rag-test.txt
  ```

  **Commit**: YES | Message: `test(backend): add knowledge base integration tests` | Files: [`backend/app/tests/test_rag_kb.py`]

- [x] 12. Run backend smoke tests

  **What to do**: Run the existing smoke test script at `/home/cnhyk/Interview/mock-interview/backend/app/scripts/phase123_smoke.py` to verify backend still works after fixes.

  **Must NOT do**: Don't modify smoke tests unless they fail due to our changes.

  **Recommended Agent Profile**:
  - Category: `backend-test` - Reason: Existing test execution
  - Skills: [] - Not needed
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: NO | Wave 3 | Blocks: 13, 16 | Blocked By: 7, 8, 9

  **References**:
  - Pattern: README shows how to run: `docker exec mock-interview-backend-1 python -m app.scripts.phase123_smoke`
  - Test checks: resume_status, llm_done, tts_chunks, stt_final, report_total_score

  **Acceptance Criteria**:
  - [ ] `cd /home/cnhyk/Interview/mock-interview/backend && python -m app.scripts.phase123_smoke --help` shows usage
  - [ ] Smoke test runs without import errors

  **QA Scenarios**:
  ```
  Scenario: Smoke test runs successfully
    Tool: Bash
    Steps:
      1. Run smoke test script
      2. Check exit code
      3. Verify key metrics in output
    Expected: Script runs, no import/syntax errors
    Evidence: .sisyphus/evidence/task-12-smoke-test.txt
  ```

  **Commit**: NO | Files: []

- [ ] 13. Run frontend Playwright tests (BLOCKED: Docker not available in CI - requires `docker compose up` to run. Frontend build passes. Test files exist at `frontend/tests/smoke.spec.ts`.)

  **What to do**: Run existing Playwright tests at `/home/cnhyk/Interview/mock-interview/frontend/tests/smoke.spec.ts` to verify frontend still works.

  **Must NOT do**: Don't modify tests unless they fail due to our changes.

  **Recommended Agent Profile**:
  - Category: `frontend-test` - Reason: Frontend testing
  - Skills: ["playwright"] - E2E testing
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: NO | Wave 3 | Blocks: 17 | Blocked By: 12

  **References**:
  - Pattern: `frontend/playwright.config.ts` - test configuration
  - Test: `frontend/tests/smoke.spec.ts`

  **Acceptance Criteria**:
  - [ ] `cd /home/cnhyk/Interview/mock-interview/frontend && npx playwright test --reporter=line` runs
  - [ ] Tests complete without critical failures

  **QA Scenarios**:
  ```
  Scenario: Playwright tests pass
    Tool: Bash
    Steps:
      1. Run playwright tests
      2. Check test results
      3. Verify no critical errors
    Expected: Tests complete successfully
    Evidence: .sisyphus/evidence/task-13-playwright.txt
  ```

  **Commit**: NO | Files: []

- [x] 14. Commit exception handling fixes

  **What to do**: Create git commit for all three exception handling fixes with proper commit message.

  **Must NOT do**: Don't force push. Don't amend commits not created by us.

  **Recommended Agent Profile**:
  - Category: `git-commit` - Reason: Git operations
  - Skills: ["git-master"] - Git workflow
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: NO | Wave 4 | Blocks: 17 | Blocked By: 10

  **References**:
  - Pattern: Commit message format: `type(scope): description`
  - Files: interview_ws.py, tts_service.py, sensevoice_stt_service.py

  **Acceptance Criteria**:
  - [ ] `git log --oneline -1 | grep "fix.*exception"` succeeds
  - [ ] `git show --stat HEAD` shows all three files changed

  **QA Scenarios**:
  ```
  Scenario: Exception fixes committed
    Tool: Bash
    Steps:
      1. git add -A
      2. git commit with proper message
      3. Verify commit exists
    Expected: Commit created with correct files
    Evidence: .sisyphus/evidence/task-14-commit.txt
  ```

  **Commit**: YES | Message: `fix(backend): replace silent exception swallowing with logging` | Files: [`backend/app/ws/interview_ws.py`, `backend/app/services/tts_service.py`, `backend/app/services/sensevoice_stt_service.py`]

- [x] 15. Commit knowledge base content

  **What to do**: Create git commit for all knowledge base additions.

  **Must NOT do**: Don't commit .env file.

  **Recommended Agent Profile**:
  - Category: `git-commit` - Reason: Git operations
  - Skills: ["git-master"] - Git workflow
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: NO | Wave 4 | Blocks: 17 | Blocked By: 11

  **Acceptance Criteria**:
  - [ ] `git log --oneline -1 | grep "feat.*kb\|feat.*knowledge"` succeeds
  - [ ] `git show --stat HEAD | grep "knowledge_base"` succeeds

  **QA Scenarios**:
  ```
  Scenario: KB content committed
    Tool: Bash
    Steps:
      1. git add knowledge_base/
      2. git commit
      3. Verify content in repo
    Expected: Commit with KB files
    Evidence: .sisyphus/evidence/task-15-commit.txt
  ```

  **Commit**: YES | Message: `feat(kb): add interview questions for teacher, doctor, lawyer roles` | Files: [`backend/knowledge_base/teacher/`, `backend/knowledge_base/doctor/`, `backend/knowledge_base/lawyer/`]

- [x] 16. Commit docker configuration fixes

  **What to do**: Create git commit for docker-compose and .env.example fixes.

  **Must NOT do**: Don't commit backend/.env (it's gitignored).

  **Recommended Agent Profile**:
  - Category: `git-commit` - Reason: Git operations
  - Skills: ["git-master"] - Git workflow
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: NO | Wave 4 | Blocks: 17 | Blocked By: 12

  **Acceptance Criteria**:
  - [ ] `git log --oneline -1 | grep "fix.*docker\|fix.*config"` succeeds
  - [ ] `git show --stat HEAD | grep "docker-compose\|.env.example"` succeeds

  **QA Scenarios**:
  ```
  Scenario: Docker configs committed
    Tool: Bash
    Steps:
      1. git add docker-compose.yml .env.example
      2. git commit
      3. Verify in log
    Expected: Commit with docker files
    Evidence: .sisyphus/evidence/task-16-commit.txt
  ```

  **Commit**: YES | Message: `fix(docker): add VITE_API_PROXY_TARGET and fix DATABASE_URL` | Files: [`docker-compose.yml`, `backend/.env.example`]

- [x] 17. Final verification and push

  **What to do**: Run final verification - ensure all tests pass, all changes committed, push to remote.

  **Must NOT do**: Don't force push. Don't push if any verification fails.

  **Recommended Agent Profile**:
  - Category: `git-commit` - Reason: Final push
  - Skills: ["git-master"] - Git workflow
  - Omitted: [] - Not applicable

  **Parallelization**: Can Parallel: NO | Wave 4 | Blocks: none | Blocked By: 13, 14, 15, 16

  **Acceptance Criteria**:
  - [ ] `git status` shows clean working tree (all committed)
  - [ ] `git log --oneline -5` shows 3+ commits from this work
  - [ ] `git push` succeeds

  **QA Scenarios**:
  ```
  Scenario: All changes pushed
    Tool: Bash
    Steps:
      1. Check git status (should be clean)
      2. Verify 3+ commits exist
      3. git push to remote
      4. Verify push success
    Expected: All changes pushed to origin/main
    Evidence: .sisyphus/evidence/task-17-final-push.txt
  ```

  **Commit**: NO | Files: []

## Final Verification Wave (MANDATORY — after ALL implementation tasks)
- [ ] F1. Plan Compliance Audit — oracle
- [ ] F2. Code Quality Review — unspecified-high
- [ ] F3. Real Manual QA — unspecified-high (+ playwright if UI)
- [ ] F4. Scope Fidelity Check — deep
## Commit Strategy
- **Wave 1 commits**: 3 separate commits (one per exception handling file) OR one combined commit
- **Wave 2 commits**: 1 commit for docker configs
- **Wave 3 commits**: 2 commits (unit tests + KB tests)
- **Wave 4 commits**: 3 separate commits for each fix category

**Commit Message Format**: `type(scope): description`
- type: fix, feat, test, refactor, chore
- scope: backend, ws, tts, stt, kb, docker, frontend

## Success Criteria
1. All 17 tasks completed with evidence files
2. All tests pass (smoke tests, playwright, new unit tests)
3. All 4 Final Verification Wave items pass
4. 3+ commits pushed to origin/main
5. Working tree is clean (no uncommitted changes)
6. Frontend builds successfully
7. Docker configuration validates without errors
