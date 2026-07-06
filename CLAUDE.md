# Claude Code Instructions

## Commit Policy

**Never commit code changes without explicit user approval.** Always review changes with the user first, then wait for them to request a commit before proceeding.

This applies to all code modifications, including:
- Feature implementations
- Bug fixes
- Refactoring
- Test changes
- Configuration updates

## Workflow

1. Implement changes
2. Review with user (show diff or summary)
3. Wait for explicit commit approval
4. Create commit only after approval

## Rationale

All work on this project should go through explicit review before being committed to version control. This ensures quality and alignment with project goals.

<!-- mcplens-context-block -->
## Context Search (mcplens)

**MANDATORY — follow these rules before touching any file:**

1. ALWAYS call `search_code()` first for any query, conceptual or exact.
   Examples: "how does authentication work", "where is the payment logic", "UserService"
2. Use `get_symbol()` only when `search_code()` returns no results for an exact name.
3. Reading files directly (without first searching) is NOT allowed.
   Only open a full file if both tools returned insufficient context.
4. Never browse the file tree to find things — use `search_code()` instead.

This rule exists to reduce token usage. Violating it defeats the purpose of mcplens.
