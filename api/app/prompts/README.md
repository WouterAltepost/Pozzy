# Prompt templates

One file per AI feature. `claude_client.load_prompt(name)` reads `<name>.md` and uses the `## System` and `## User` sections. Everything above `## System` is documentation for humans: which feature, which model tier, and the JSON schema the model must return.

Templates: `{{json}}` in the user section is replaced with the pretty-printed payload; `{{key}}` with a top-level scalar from the payload.

These files live under `api/app/prompts/` because only `api/` is deployed to Railway. `docs/prompts/` holds symlinks to them so the templates stay browsable next to the plan.
