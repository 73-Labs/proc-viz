# STATUS — procedures-visualizer

> Single source of truth for resuming work. Read this FIRST when starting a session.
> Update this file at the end of every work phase so the next `/clear` resumes in 1 read.
> Last updated: 2026-07-17

---

## ✅ Done

- Lazy-load strategy with checkbox (default ON) — loads only schemas initially, procedures/functions on expand
- Schema selector for table search — filters search results to selected schema

---

## 🚀 Next phase

**Goal:** Ready for testing / next feature request

### Acceptance criteria
- (waiting for user feedback on lazy-load feature)

### Files modified
- `app/widgets/database_explorer.py` — lazy-load + schema selector

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
