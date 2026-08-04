# Memory

> Chronological action log. Hooks and AI append to this file automatically.
> Old sessions are consolidated by the daemon weekly.

## Session: 2026-07-17 22:35

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

| 00:00 | Implemented Task 1 integration-test foundation; added guarded SQL Server fixture, driver coverage, seed schema/data, docs | tests/integration/, init-db.sql, README.md, pyproject.toml, NEXT_FEATURES.md | Complete; integration tests skip without server | ~1800 |
| 00:00 | Added shell test runner with venv fallback and offscreen Qt default | run_tests.sh, README.md | Ready | ~300 |
| 00:00 | Fixed reported test failures: partial syntax colors, trusted certificate kwargs, connection error wording, unavailable keyring cleanup | app/widgets/sql_highlighter.py, app/models/connection_profile.py, app/dialogs/connection_dialog.py, app/storage/profile_manager.py | 64 passed, 4 skipped | ~700 |

## Session: 2026-07-17 07:35

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-17 16:46

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-18 21:13

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-21 19:51

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-23 21:54

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-25 09:57

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-25 09:58

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-25 11:07

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-25 11:19

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 11:45 | Task 3: Unified search and filtering — added scope selector, schema filter for routines, exact-match toggle, debounce, result count, clear button, state preservation, 16 new tests | app/widgets/database_explorer.py, tests/test_database_explorer.py | 80 passed; fixed pre-existing connection profile test failures | ~2500 |
| 12:00 | Updated FEATURES.md with advanced search documentation; updated README.md features; updated STATUS.md | FEATURES.md, README.md, .wolf/STATUS.md | Task 3 documented | ~400 |

## Session: 2026-07-25 11:57

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-25 13:00

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 13:00 | Task 4: Dependency graph view — implemented PyVis interactive graphs with cycle detection, depth/direction selectors, DOT export, cross-schema names | app/widgets/dependency_graph.py (new), app/widgets/database_explorer.py, requirements.txt, tests/test_dependency_graph.py (new) | 98 passed, 4 skipped; graph loads on routine selection; cycle edges highlighted red; DOT export ready | ~3500 |
| 13:15 | Updated STATUS.md (Task 4 done), FEATURES.md (graph feature docs), memory.md | STATUS.md, FEATURES.md, .wolf/memory.md | Task 4 documented | ~400 |

## Session: 2026-07-25 12:16

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-25 19:35

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-25 19:40

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-25 19:45

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-26 15:30

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 15:30 | Task 5 execution foundation: added ExecutionRequest/Result models, parameterized SQLServerDriver.execute_procedure with validation/cancellation/error handling | app/drivers/database_driver.py, app/drivers/sqlserver_driver.py, app/db_accessor.py | Execution layer complete; 11 new tests all pass | ~2000 |
| 15:45 | Task 5 UI layer: ResultViewer widget for result sets/messages/errors, ExecutionWorker for async QThreadPool execution, ParametersWidget Execute button with validation/confirmation | app/widgets/result_viewer.py (new), app/widgets/execution_worker.py (new), app/widgets/parameters_widget.py | UI layer complete; async execution ready; 109 passed, 4 skipped | ~1500 |
| 16:00 | Updated anatomy.md (new files, token estimates), STATUS.md (Task 5 foundation done, next: integration), memory.md | .wolf/anatomy.md, .wolf/STATUS.md, .wolf/memory.md | Foundation phase complete; awaiting DatabaseExplorer wiring | ~600 |

## Session: 2026-07-26 13:40

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-29 10:39

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-29 10:44

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-29 10:51

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-29 10:51

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-29 12:37

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-29 12:42

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-29 12:42

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-07-31 13:47

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-01 11:56

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-03 09:09

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-03 18:28

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-03 18:28

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-03 18:28

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:15

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:15

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:18

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:18

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:18

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:18

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:22

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:22

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:22

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:22

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:22

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:34

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:34

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:34

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:35

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:35

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-08-04 19:52

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
