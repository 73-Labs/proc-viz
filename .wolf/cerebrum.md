# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-07-17

## User Preferences

- User likes terse caveman-mode communication (prefer fragments over full sentences)
- User requested lazy-load strategy with toggle checkbox + schema selector for table search

## Key Learnings

- **Project:** procedures-visualizer — PySide6 GUI for SQL Server exploration
- **Architecture:** DatabaseExplorer widget manages tree UI, DatabaseAccessor queries backend, lazy-load uses QTimer + LoadingOverlay for async ops
- **Lazy-load pattern:** Schema expand triggers on_item_expanded() → loads procs/funcs into tree via _load_schema_contents()
- **Test setup:** Tests mock DatabaseAccessor; syntax_colors must be dict with keyword/builtin/string/comment/number/function keys or SqlSyntaxHighlighter fails
- **Build issue:** pyproject.toml needs explicit `packages = ["app"]` or setuptools autodiscovers 'packaging/' dir as package

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
