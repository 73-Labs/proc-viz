# STATUS — procedures-visualizer

> Single source of truth for resuming work. Read this FIRST when starting a session.
> Update this file at the end of every work phase so the next `/clear` resumes in 1 read.
> Last updated: 2026-07-26 (Task 5 execution foundation completed)

---

## ✅ Done

- Lazy-load strategy with checkbox (default ON) — loads only schemas initially, procedures/functions on expand
- Schema selector for table search — filters search results to selected schema
- Task 1 integration-test foundation — opt-in SQL Server suite, guarded fixture, deterministic seed
- Test runner baseline restored — 80 passed, 4 integration skipped without SQL Server
- **Task 3: Unified search and filtering** — scope selector, schema filter for routines, exact-match mode, debounce, result count, clear button, filter preservation
- **Task 4: Dependency graph view** — PyVis interactive graphs, cycle detection, depth/direction selectors, DOT export, full cross-schema names
- **Task 5: Safe procedure execution foundation** — ExecutionRequest/Result models, parameterized SQLServerDriver.execute_procedure, async ExecutionWorker, ResultViewer widget, ParametersWidget Execute button with validation, confirmation dialog, parameterized queries (no string interpolation)

---

## 🚀 Next phase

**Goal:** Complete Task 5 integration — wire execution callback into DatabaseExplorer and MainWindow

### Acceptance criteria
- ✅ Required values block execution with field-level errors
- ✅ SQL errors show readable message and preserve entered parameters
- ✅ User can cancel or timeout execution
- ✅ Tests prove no execution occurs on selection and no raw string interpolation
- ⏳ Successful execution displays result without freezing window (ExecutionWorker async ready, needs DatabaseExplorer wiring)
- ⏳ Integration test with seed database procedure

### Files to modify
- `app/widgets/database_explorer.py` — pass execute_callback to ParametersWidget, set connection info
- `app/main_window.py` — create execute callback from accessor, pass to explorer
- `tests/integration/test_sqlserver.py` — add execution test with seed procedure

### Decisions fixed
- Async execution via QThreadPool + ExecutionWorker (prevents UI freezing)
- Parameterized queries throughout (no string interpolation for parameters or routine names)

---

## 📁 Active architecture

- **Stack:** _<frameworks, libraries, runtime>_
- **Key tables / modules:** _<list>_
- **Patterns:** _<conventions enforced project-wide>_

---

## ⚠️ External blockers (don't block coding)

- _<env vars, secrets, external accounts, manual steps>_

---

## 🔧 Useful commands

```bash
# add the most-used commands here so the next session has them ready
```

---

## 📚 References (read IF needed)

- `.wolf/cerebrum.md` — User Preferences + Do-Not-Repeat + Decision Log
- `.wolf/anatomy.md` — token-efficient file index
- `.wolf/buglog.json` — known bugs + fixes
