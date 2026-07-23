# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-07-22

## User Preferences

- User likes terse caveman-mode communication (prefer fragments over full sentences)
- User requested lazy-load strategy with toggle checkbox + schema selector for table search

## Key Learnings

- **Project:** procedures-visualizer — PySide6 GUI for SQL Server exploration
- **Architecture:** DatabaseExplorer widget manages tree UI, DatabaseAccessor queries backend, lazy-load uses QTimer + LoadingOverlay for async ops
- **Lazy-load pattern:** Schema expand triggers on_item_expanded() → loads procs/funcs into tree via _load_schema_contents()
- **Test setup:** Tests mock DatabaseAccessor; syntax_colors must be dict with keyword/builtin/string/comment/number/function keys or SqlSyntaxHighlighter fails
- **Build issue:** pyproject.toml needs explicit `packages = ["app"]` or setuptools autodiscovers 'packaging/' dir as package
- **Integration tests:** Opt-in SQL Server tests use `PROC_VIZ_INTEGRATION=1`; fixture creates only `DummyDB` or `proc_viz_test*`, applies seed once, and skips clearly when server unavailable
- **Seed batches:** SQL Server routine DDL must execute in separate batches; `init-db.sql` now includes `FunctionSchema` and deterministic employee rows
- **Test runner:** `run_tests.sh` sets offscreen Qt; syntax highlighter must merge partial theme colors with defaults
- **Keyring:** Password cleanup must catch `keyring.errors.KeyringError`; headless systems may have no backend

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
