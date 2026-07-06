# General Rules

## Context Management

- Prefer rg, fd, git grep, and semantic search before opening files.
- Never read entire directories.
- Read the smallest relevant file section possible.
- Inspect git diff before inspecting full files.
- Avoid re-reading files already analyzed in the current task.

## Search Strategy

1. Search for symbols first.
2. Search for references second.
3. Open files only after identifying likely locations.

## Code Changes

- Make minimal changes.
- Preserve existing architecture.
- Avoid broad refactors unless explicitly requested.

## Verification

Before finishing:

- Run only the tests affected by the change.
- Run full test suites only when necessary.

## Communication

- Summarize findings before making changes.
- Explain why a file is being opened.
- Keep responses concise.
