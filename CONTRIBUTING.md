# Contributing Guide

## Commit Message Convention

All major changes must be committed with the following format:

```text
<type>(<scope>): <short summary>

why:
- <reason 1>
- <reason 2>

what:
- <change 1>
- <change 2>

validation:
- <command/result 1>
- <command/result 2>
```

### Allowed `type`

- `feat`: new capability
- `fix`: bug fix
- `perf`: performance optimization
- `refactor`: code structure change without behavior change
- `docs`: documentation-only change
- `chore`: maintenance/config cleanup

### Example

```text
perf(backend): switch interviewer flow to native ollama no-thinking path

why:
- OpenAI-compatible endpoint still produced long reasoning traces
- Interview first-token latency was unstable under mixed workloads

what:
- Route local ollama host to /api/chat native endpoint
- Pass think=false for interviewer/reporter calls
- Keep GPU runtime and service health checks unchanged

validation:
- phase123 smoke x3 passed
- avg first token latency reduced to ~0.2s (measured on RTX 5080)
```
