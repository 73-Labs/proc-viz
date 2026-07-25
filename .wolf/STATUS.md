# STATUS — procedures-visualizer

> Single source of truth for resuming work. Read this FIRST when starting a session.
> Update this file at the end of every work phase so the next `/clear` resumes in 1 read.
> Last updated: 2026-07-25 (Task 3 unified search completed)

---

## ✅ Done

- Lazy-load strategy with checkbox (default ON) — loads only schemas initially, procedures/functions on expand
- Schema selector for table search — filters search results to selected schema
- Task 1 integration-test foundation — opt-in SQL Server suite, guarded fixture, deterministic seed
- Test runner baseline restored — 80 passed, 4 integration skipped without SQL Server
- **Task 3: Unified search and filtering** — scope selector, schema filter for routines, exact-match mode, debounce, result count, clear button, filter preservation

---

## 🚀 Next phase

**Goal:** Reliable refresh, reconnect, cancellation, and stale-state handling (Task 2)

### Acceptance criteria
- Refresh, failure, cancellation, and reconnect lifecycle behavior covered by tests

### Files to modify
- `app/widgets/database_explorer.py` — refresh logic and state preservation
- `app/main_window.py` — reconnection and error handling
- `tests/test_database_explorer.py` — lifecycle tests

### Decisions pending
- Cancellation token generation strategy (UUID vs counter)
- Retry UI behavior (automatic vs manual)
- State preservation scope (full tree vs metadata only)

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
