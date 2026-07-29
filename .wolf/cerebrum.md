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
- **Execution layer:** Parameterized queries use pymssql %s placeholders for values; identifiers quoted with brackets [schema].[routine]. ExecutionRequest/Result separate driver from UI. ExecutionWorker (QRunnable) + QThreadPool handles async without blocking UI.
- **Procedure execution:** INOUT parameters need initialization but passed as OUTPUT; OUT parameters initialized as NULL OUTPUT. Result sets captured via cursor.fetchall() + cursor.description after EXEC. Output params queried separately via SELECT statement.

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->
- [2026-07-25] Tree filtering with lazy-load: Placeholder items are created before real content loads. Tests must either disable lazy-load or wait for expansion before checking visibility.

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
- **Task 3 debounce strategy:** Use QTimer with 300ms timeout instead of immediate filtering. Prevents excessive tree recalculation on rapid keystrokes; doesn't interfere with Ctrl+K focus behavior (immediate focus, debounced filter).
- **Search scope vs table reference search:** Keep separate. Routine name filter uses local tree filtering (fast, no DB). Table reference search uses server-side query (different UI, different flow). Avoids conflating two independent features.
- **Schema filter application:** Apply to both routine filter AND table search for consistency. User can filter results by schema in either mode.
- **Task 5 execution strategy:** Use parameterized queries with %s placeholders for all parameter values and identifier quoting with brackets. ExecutionRequest/Result models decouple driver from UI. ExecutionWorker + QThreadPool for async execution prevents UI freeze. No logging of parameter values by default for security.
- **Confirmation dialog content:** Show server, database, schema, routine, timeout to make it clear what will execute and on which connection.
