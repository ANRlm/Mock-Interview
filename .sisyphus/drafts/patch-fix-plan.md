# Patch 应用修复计划

## 概述

执行 `git apply --reject` 后，有 2 个文件存在未应用的 rejected hunks：
- `backend/app/ws/interview_ws.py` - 4 个 hunks 被拒
- `frontend/package-lock.json` - 3 个 hunks 被拒

## interview_ws.py 修复清单

### 1. msg_payload 变量重命名 (Lines 297-332)
**问题**: 第 290 行已正确使用 `msg_payload = json.loads(raw)`，但后续处理仍使用 `payload`

**需要修改**:
- Line 297-300: `payload.get("turn_id")` → `msg_payload.get("turn_id")`
- Line 300: `payload.get("reason")` → `msg_payload.get("reason")`
- Line 303-305: `payload.get("text")` → `msg_payload.get("text")` 等
- Line 310-312: `payload.get("data")` → `msg_payload.get("data")` 等
- Line 331-332: `payload` → `msg_payload`

### 2. WebSocketDisconnect 清理 (Lines 339-343)
**问题**: 需要在 disconnect 时清理 `_behavior_warning_last_sent` 字典

**需要修改**:
```python
except WebSocketDisconnect:
    runtime.closed = True
    if runtime._stt_worker_task:
        runtime._stt_worker_task.cancel()
    _behavior_warning_last_sent.pop(str(session_id), None)  # 添加此行
    return
```

### 3. _handle_behavior_frame 中的 key 类型 (Lines 762-764)
**问题**: 代码已使用 `str(session_id)`，无需修改（已正确）

**确认**: 当前实现已使用 `str(session_id)` 作为 key

## package-lock.json 修复清单

### 需要添加的依赖 (Playwright)

**1. devDependencies 中添加 (Line 24 区域)**:
```json
"@playwright/test": "^1.40.0",
```

**2. node_modules 中添加 @playwright/test (Line 653 区域)**:
```json
"node_modules/@playwright/test": {
  "version": "1.59.1",
  "resolved": "https://registry.npmjs.org/@playwright/test/-/test-1.59.1.tgz",
  "integrity": "sha512-PG6q63nQg5c9rIi4/Z5lR5IVF7yU5MqmKaPOe0HSc0O2cX1fPi96sUQu5j7eo4gKCkB2AnNGoWt7y4/Xx3Kcqg==",
  "dev": true,
  "license": "Apache-2.0",
  "dependencies": {
    "playwright": "1.59.1"
  },
  "bin": {
    "playwright": "cli.js"
  },
  "engines": {
    "node": ">=18"
  }
},
```

**3. node_modules 中添加 playwright 和 playwright-core (Line 4273 区域)**:
```json
"node_modules/playwright": {
  "version": "1.59.1",
  ...
},
"node_modules/playwright-core": {
  "version": "1.59.1",
  ...
},
"node_modules/playwright/node_modules/fsevents": {
  ...
}
```

## 执行步骤

1. **修复 interview_ws.py**:
   - 将 `payload` 改为 `msg_payload` (除了已经是 `msg_payload` 的地方)
   - 在 WebSocketDisconnect 处理中添加 cleanup

2. **修复 package-lock.json**:
   - 在适当位置插入 Playwright 相关依赖

3. **清理 .rej 文件**:
   - 删除 `backend/app/ws/interview_ws.py.rej`
   - 删除 `frontend/package-lock.json.rej`

4. **验证应用**:
   - 运行 `git apply --check` 确认无剩余冲突

## 提交信息

```
fix: apply patch mock-interview-fixes.patch with manual fixes for rejected hunks

- interview_ws.py: rename payload to msg_payload, add WebSocketDisconnect cleanup
- package-lock.json: add @playwright/test and playwright dependencies
- Remove .rej files after successful application
```