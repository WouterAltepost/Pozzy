# ping

Feature: `smoke`. Model: fast. Used only by `api/scripts/claude_smoke.py` to prove the whole path works (call, JSON parse, schema, ai_calls row).

Schema the model must return:

```json
{"ok": true, "message": "string, one short sentence"}
```

## System
You are a connectivity check for a personal dashboard. Reply with JSON only, no prose, no code fences.

## User
Echo this note back in a short friendly sentence: "{{note}}".
Reply exactly in this shape: {"ok": true, "message": "..."}
