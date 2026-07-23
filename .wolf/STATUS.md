# STATUS — procedures-visualizer

> Single source of truth for resuming work. Read this FIRST when starting a session.
> Update this file at the end of every work phase so the next `/clear` resumes in 1 read.
> Last updated: 2026-07-23 (test runner failures fixed)

---

## ✅ Done

- Lazy-load strategy with checkbox (default ON) — loads only schemas initially, procedures/functions on expand
- Schema selector for table search — filters search results to selected schema
- Task 1 integration-test foundation — opt-in SQL Server suite, guarded fixture, deterministic seed
- Test runner baseline restored — 64 passed, 4 integration skipped without SQL Server

---

## 🚀 Next phase

**Goal:** Reliable refresh, reconnect, cancellation, and stale-state handling (Task 2)

### Acceptance criteria
- Refresh, failure, cancellation, and reconnect lifecycle behavior covered by tests

### Files modified
- `tests/integration/` — SQL Server fixture and end-to-end driver tests
- `init-db.sql` — deterministic schema and data
- `README.md`, `pyproject.toml` — integration-test docs/config
- `app/widgets/sql_highlighter.py`, `app/models/connection_profile.py`, `app/dialogs/connection_dialog.py`, `app/storage/profile_manager.py` — test/runtime robustness fixes

### Decisions made
- Lazy-load ON by default (loads only schemas, procs/funcs on expand)
- Schema selector defaults to "All Schemas" for backward compat
- Checkbox + combo box added to left panel header

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
