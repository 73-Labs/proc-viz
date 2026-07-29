# Proc-Viz Next Features

Implementation roadmap for an AI coding agent. This document describes the next feature set after schema selector and lazy loading.

## Current baseline

Proc-viz is a PySide6 desktop application for exploring SQL Server routines.

Existing capabilities:

- Saved connection profiles with keyring-backed passwords.
- SQL Server connection through `DatabaseDriver` and `SQLServerDriver`.
- Schema, procedure, and function tree.
- Lazy loading of routine children.
- Procedure/function source, parameters, and details tabs.
- Caller/callee dependency trees.
- Table-reference search with schema selection.
- SQL export, themes, zoom, loading overlay, and refresh action.
- Unit tests using mocked `DatabaseDriver` objects.

Primary modules:

- `app/drivers/database_driver.py` — abstract driver and data models.
- `app/drivers/sqlserver_driver.py` — SQL Server queries.
- `app/db_accessor.py` — driver delegation and DTO conversion.
- `app/widgets/database_explorer.py` — tree, search, source, details, dependencies.
- `app/widgets/parameters_widget.py` — parameter metadata, inputs, SQL preview.
- `app/main_window.py` — connection lifecycle, refresh, status bar.
- `tests/` — PySide6 and mocked driver tests.
- `init-db.sql` — deterministic seed database for integration testing.

## Implementation rules

1. Preserve `DatabaseDriver` as the only database abstraction used by widgets.
2. Keep database calls out of Qt event handlers when they can block the UI. Use the existing loading pattern or introduce a reusable worker abstraction.
3. Never execute SQL by string-concatenating untrusted object names or user values. Validate or parameterize values; quote identifiers with a driver-owned helper.
4. Do not silently swallow database errors. Show a useful UI message and retain enough context for retry.
5. Keep lazy loading enabled by default and preserve current schema selector behavior.
6. Add tests for every changed behavior. Mock driver calls in unit tests; use `init-db.sql` for integration tests.
7. Keep changes small enough to review. Complete one roadmap task and its tests before starting the next.
8. Update `FEATURES.md`, `README.md`, and this file when behavior or shortcuts change.

## Recommended order

### Phase 0 — Verification foundation

Implement Tasks 1 and 2 first. They reduce risk in every later feature.

### Phase 1 — Exploration workflow

Implement Tasks 3, 4, and 5. They improve daily browsing and analysis.

### Phase 2 — Productivity

Implement Tasks 6 and 7.

### Phase 3 — Advanced scope

Implement Tasks 8, 9, and 10 only after the previous phases are stable.

---

## Task 1 — End-to-end database test suite ✅

### Objective

Prove application behavior against deterministic SQL Server database defined in `init-db.sql`, while keeping ordinary unit tests fast and offline.

### Scope

- Add documented integration-test mode.
- Start SQL Server with `docker-compose.yml` when available, or accept externally supplied test connection settings.
- Apply `init-db.sql` once per test run.
- Test schemas, routines, parameters, source, table references, and dependencies.
- Add CI integration job when runner supports SQL Server service/container.

### Likely files

- `tests/integration/` — integration tests and fixtures.
- `tests/conftest.py` — opt-in fixtures and skip behavior.
- `docker-compose.yml` — health checks or test credentials only if needed.
- `init-db.sql` — missing deterministic test cases only.
- `README.md` — setup and commands.
- `.github/workflows/` — integration workflow.

### Requirements

- Integration tests skip with clear message when Docker or credentials are unavailable.
- Unit tests remain offline and fast.
- Seed database includes procedure input/output parameters, function, caller/callee chain, and table references.
- Tests never use production credentials or mutate non-test databases.

### Acceptance criteria

- `pytest` passes without Docker.
- Explicit integration command runs against seed database.
- Failures identify feature and database operation.
- CI runs unit tests on every change; integration tests run where SQL Server is available.

### Delivered

- Added opt-in `tests/integration/` fixtures and end-to-end driver coverage.
- Added guarded database creation, one-time seed application, and clear skip behavior.
- Added deterministic `FunctionSchema` and employee seed data.
- Documented `PROC_VIZ_INTEGRATION=1 pytest -m integration` and external connection variables.

---

## Task 2 — Reliable refresh, reconnect, cancellation, and stale-state handling

### Objective

Make refresh and transient connection failures safe. Current refresh calls `load_procedures()` directly and can leave stale selection or a blocked UI during slow queries.

### Scope

- Add a refresh operation that clears or replaces tree state atomically.
- Preserve selected object, active tab, filter text, schema selection, and lazy-load setting when possible.
- Add retry action after schema or child-load failure.
- Add cancellation for long-running loads.
- Ensure old driver/explorer callbacks cannot update a newly connected profile.
- Update status-bar routine count after lazy-loaded schemas expand.

### Likely files

- `app/widgets/database_explorer.py`
- `app/main_window.py`
- `app/widgets/loading_spinner.py`
- New reusable worker module if needed, preferably under `app/widgets/` or `app/services/`.
- `tests/test_database_explorer.py`
- New lifecycle/worker tests.

### Requirements

- UI remains responsive during database work.
- Cancellation stops result application, even if underlying driver cannot cancel immediately.
- Refresh failure must not destroy the last usable tree unless replacement state is ready.
- Reconnect must close the old driver exactly once.
- Errors must include operation and object context, without exposing passwords.

### Acceptance criteria

- Refresh works in both lazy and eager modes.
- Failed refresh offers retry and leaves no mixed old/new tree state.
- Selecting another connection during loading cannot populate the old connection's data.
- Cancelled work produces no late UI mutation.
- Tests cover success, failure, cancellation, reconnect, and stale callback cases.

---

## Task 3 — Unified search and filtering

### Objective

Make routine and table discovery predictable across large databases.

### Scope

- Add search scope: all objects, procedures, functions, tables, or views where supported.
- Support schema filter for routine search, not only table search.
- Add case-insensitive name matching and optional exact-match mode.
- Debounce text filtering without breaking `Ctrl+K`.
- Highlight matches and show visible-result count.
- Add a clear-search action and preserve filters during refresh.
- Keep table-reference search distinct from local name filtering.

### Likely files

- `app/widgets/database_explorer.py`
- `app/drivers/database_driver.py` if a server-side search method is required.
- `app/db_accessor.py`
- `app/drivers/sqlserver_driver.py`
- `tests/test_database_explorer.py`
- `FEATURES.md` and `README.md`

### Requirements

- Local filtering must not trigger database queries on every keystroke.
- Server-side search must use parameters for user values.
- Search results must retain object metadata needed for navigation.
- Empty search restores normal tree state.

### Acceptance criteria

- User can find a routine by name, schema, or object type.
- Search works with lazy-loaded schemas and clearly indicates unloaded content when relevant.
- Table search can be cleared without requiring reconnection.
- Result count and match highlighting remain correct after expand, collapse, refresh, and schema changes.

---

## Task 4 — Dependency graph view

### Objective

Turn caller/callee tree data into a visual dependency analysis feature, the main differentiator implied by proc-viz's name.

### Scope

- Add a Graph tab or separate graph dialog for selected routine.
- Display selected node, callers, callees, and optionally recursive levels.
- Add depth selector and direction selector.
- Prevent infinite traversal with visited-node tracking.
- Detect and visually mark cycles.
- Allow node click navigation back to routine details.
- Export graph as DOT, SVG, or PNG where practical.

### Likely files

- `app/widgets/database_explorer.py` — graph launch and selection synchronization.
- New `app/widgets/dependency_graph.py` — graph model and rendering.
- `app/db_accessor.py` — reusable dependency retrieval.
- `app/drivers/database_driver.py` — only if dependency DTO needs database/type fields.
- `tests/test_dependency_graph.py`
- `FEATURES.md` and `README.md`

### Requirements

- Start with Qt-native graphics (`QGraphicsView`) unless a dependency already supports a better renderer.
- Graph loading must be lazy and cancellable.
- Duplicate edges must be removed.
- Cross-schema names must be fully qualified.
- Missing or unresolved dependencies must remain visible as unresolved nodes, not disappear.

### Acceptance criteria

- Selected routine opens graph with correct direct callers and callees.
- Depth 1 does not fetch recursive levels.
- Higher depth stops at configured limit and handles cycles.
- Clicking graph node selects corresponding routine when available.
- Exported graph contains node labels and relationship direction.

---

## Task 5 — Safe procedure execution and result viewer

### Objective

Allow users to test procedures from the existing Parameters tab without creating unsafe or ambiguous execution behavior.

### Scope

- Add explicit `Execute` action beside generated SQL preview.
- Validate required input values and data types before execution.
- Support input and input/output parameters.
- Display result sets in a table, informational messages, affected-row count, duration, and errors.
- Add configurable execution timeout.
- Add read-only/confirmation mode and visible active-connection warning.
- Never execute automatically when selecting a routine.

### Likely files

- `app/drivers/database_driver.py` — add a driver-neutral execution result/request model and method.
- `app/db_accessor.py`
- `app/drivers/sqlserver_driver.py`
- `app/widgets/parameters_widget.py`
- `app/widgets/database_explorer.py`
- New `app/widgets/result_viewer.py`
- `tests/test_parameters_widget.py`
- Driver/accessor execution tests.

### Requirements

- Use parameterized execution through the DB driver. Generated preview is display/copy only, not execution input.
- Quote identifiers through a trusted helper; never trust routine names from raw SQL text.
- Output values must be visible separately from result sets.
- Avoid logging parameter values by default.
- Confirmation must state server, database, schema, routine, and whether transaction/commit behavior applies.

### Acceptance criteria

- Required values block execution with field-level errors.
- Successful execution displays all returned columns and rows without freezing the window.
- SQL errors show a readable message and preserve entered parameters.
- User can cancel or time out execution.
- Tests prove no execution occurs on selection and no raw string interpolation is used for values.

---

## Task 6 — Documentation export

### Objective

Export a useful, reproducible document instead of requiring manual copy/paste from several tabs.

### Scope

- Export selected routine as SQL, Markdown, JSON, or text.
- Include fully qualified name, database, schema, type, source, parameters, metadata, callers, and callees.
- Add export-all-visible-results option later, after selected-object export is stable.
- Use deterministic field ordering and UTF-8 encoding.
- Include export timestamp and application version.

### Likely files

- `app/widgets/database_explorer.py`
- New `app/services/export_service.py` or `app/exporters/` package.
- `tests/test_export_service.py`
- `FEATURES.md` and `README.md`

### Requirements

- Export must use already loaded data where possible and clearly label unavailable lazy data.
- SQL export must preserve source exactly except for optional trailing newline.
- JSON must be valid and machine-readable.
- File overwrite requires normal confirmation from `QFileDialog`.

### Acceptance criteria

- Each format opens successfully in its intended consumer.
- Exported Markdown is readable without the application.
- Missing source or metadata is represented explicitly.
- Export tests compare stable content, excluding or controlling timestamps.

---

## Task 7 — Favorites and recent objects

### Objective

Reduce repeated navigation for users working with the same routines.

### Scope

- Add favorite toggle for selected routine.
- Add Favorites and Recent sections in the left tree or a dedicated panel.
- Persist entries per connection profile and database.
- Store fully qualified identity: database, schema, object name, object type.
- Remove stale entries gracefully.

### Likely files

- `app/storage/settings.py` or a new `app/storage/object_state.py`
- `app/widgets/database_explorer.py`
- `app/main_window.py` only for menu/shortcut wiring.
- `tests/test_object_state.py`
- `tests/test_database_explorer.py`

### Requirements

- Never store source code or credentials in favorites.
- Profile rename/delete must not orphan sensitive data.
- Recent history has a bounded size and deduplicates by object identity.
- Navigation failure must show a non-destructive message and retain the entry for retry.

### Acceptance criteria

- Favorite survives application restart.
- Same routine in two databases remains distinct.
- Recent list updates on successful selection, not on failed lookup.
- Stale object can be removed without affecting database data.

---

## Task 8 — Table and view explorer

### Objective

Make table impact analysis two-way: routine-to-table and table-to-routine.

### Scope

- Add tables and views to schema tree, preferably as lazy-loaded object groups.
- Add table detail view with columns, types, nullability, defaults, indexes, and row estimate where available.
- Show routines referencing selected table.
- Distinguish direct SQL dependencies from unresolved/dynamic references.

### Likely files

- `app/drivers/database_driver.py`
- `app/drivers/sqlserver_driver.py`
- `app/db_accessor.py`
- `app/widgets/database_explorer.py`
- New table-details widget if current details text becomes too complex.
- Tests for driver queries, DTO conversion, and UI navigation.

### Requirements

- Metadata queries must respect current database and schema.
- Large column/index lists must be lazy-loaded or paginated.
- Do not claim a table has no references when SQL Server metadata cannot resolve dynamic SQL.

### Acceptance criteria

- User can browse tables by schema.
- Selecting table shows columns and metadata.
- References navigate to routines.
- Existing routine search and lazy-load behavior remains intact.

---

## Task 9 — Performance and query observability

### Objective

Keep the app usable on large or remote databases and make slow operations diagnosable.

### Scope

- Add per-operation timeout configuration.
- Add cancellation tokens/generation IDs for async work.
- Cache immutable metadata with explicit invalidation on refresh/reconnect.
- Show operation name, elapsed time, and row/result count in status UI.
- Avoid duplicate source, parameter, and dependency queries during repeated selection.

### Likely files

- `app/widgets/loading_spinner.py`
- `app/widgets/database_explorer.py`
- `app/db_accessor.py`
- `app/drivers/sqlserver_driver.py`
- `app/storage/settings.py`
- Tests for cache invalidation, timeout, and stale results.

### Requirements

- Cache key must include connection identity, database, schema, object, and object type.
- Refresh invalidates affected cache entries.
- No cache may contain passwords or full source unless explicitly designed and documented.
- Timing telemetry stays local; do not send data externally.

### Acceptance criteria

- Reopening an already viewed object avoids duplicate queries where cache is valid.
- Refresh causes newly changed metadata to appear.
- Timeout and cancellation do not leave loading overlay active forever.
- Status UI distinguishes loaded count from total count when lazy loading is enabled.

---

## Task 10 — Second database driver

### Objective

Validate the pluggable architecture by supporting one additional database engine.

### Recommended first target

PostgreSQL, unless project users have stronger MySQL demand. PostgreSQL has strong metadata support and clear parameter/type mappings.

### Scope

- Add enum/profile support for PostgreSQL.
- Add driver implementation and dependency.
- Implement schemas, routines, source, parameters, tables, and dependencies where semantics map cleanly.
- Update connection dialog fields and validation.
- Add driver factory coverage.
- Document feature differences.

### Likely files

- `app/models/connection_profile.py`
- `app/dialogs/connection_dialog.py`
- `app/drivers/database_driver.py`
- New `app/drivers/postgresql_driver.py`
- `app/drivers/driver_factory.py`
- `app/drivers/connection_manager.py`
- `app/db_accessor.py` only for genuinely shared behavior.
- Driver tests and integration fixtures.

### Requirements

- Do not add engine-specific conditionals throughout widgets.
- Unsupported operations must return a clear capability error or empty state with explanation.
- Keep SQL Server behavior unchanged.
- Add dependency only if packaging and CI can install it reliably.

### Acceptance criteria

- PostgreSQL connection profile can be created, saved, loaded, and connected.
- Core browse/source/parameter flows work.
- Unsupported dependency or execution semantics are clearly communicated.
- Shared contract tests run against both drivers where applicable.

---

## Definition of done for every task

- Implementation follows existing module boundaries.
- Focused unit tests cover success, empty state, and failure state.
- UI remains responsive for database operations.
- No credentials or sensitive parameter values enter logs, exports, or bug reports unintentionally.
- Documentation is updated.
- `pytest` passes.
- Packaging/build command is checked when dependencies or entry points change.
- `.wolf/STATUS.md`, `.wolf/memory.md`, and `.wolf/cerebrum.md` are updated when OpenWolf rules require it.

## Suggested first coding prompt

> Implement Task 1 from `NEXT_FEATURES.md`. Inspect existing tests, `docker-compose.yml`, and `init-db.sql` first. Add opt-in SQL Server integration tests without breaking offline unit tests. Run `pytest`, report skipped integration tests explicitly, and update documentation only after tests pass.
