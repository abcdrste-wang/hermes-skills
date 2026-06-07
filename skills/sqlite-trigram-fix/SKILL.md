---
name: sqlite-trigram-fix
description: Fix SQLite FTS5 trigram tokenizer missing on older systems (SQLite < 3.34.0)
category: software-development
trigger:
  - "trigram tokenizer"
  - "no such tokenizer"
  - "FTS5 trigram not working"
  - "session_search broken"
  - "CJK search broken"
---

# SQLite Trigram Tokenizer Fix

## Root Cause

The `trigram` tokenizer was added in SQLite **3.34.0** (released 2020-12-01). Ubuntu 20.04 ships SQLite 3.31.1, so `CREATE VIRTUAL TABLE ... USING fts5(x, tokenize='trigram')` fails with:

```
sqlite3.OperationalError: no such tokenizer: trigram
```

This breaks Hermes Agent's CJK session search and causes `SessionDB.__init__` to crash.

## Fix (3 parts)

### 1. Install pysqlite3-binary

```bash
pip install pysqlite3-binary
```

This bundles **SQLite 3.51.1** with all extensions (FTS5, trigram, json1, etc.).

### 2. Patch `hermes_state.py` — prefer pysqlite3

Replace:
```python
import sqlite3
```

With:
```python
try:
    import pysqlite3 as sqlite3
except ImportError:
    import sqlite3
```

### 3. Hardening — catch tokenizer errors gracefully

In `_is_fts5_unavailable_error`, extend the check:

```python
# Before:
return "no such module" in err and "fts5" in err

# After:
return ("no such module" in err and "fts5" in err) or "no such tokenizer" in err
```

This ensures graceful fallback to LIKE-based search even when trigram is unavailable.

### 4. Test compatibility

When `hermes_state.py` uses `pysqlite3`, test files that monkeypatch `hermes_state.sqlite3.connect` or create `sqlite3.Connection` subclasses must use the **same** sqlite3 module. Mixing stdlib `sqlite3` and `pysqlite3` causes C-level type errors.

Fix: import sqlite3 from hermes_state in test files:

```python
from hermes_state import sqlite3, SessionDB
```

Remove all local `import sqlite3` lines from affected tests.

## Verification

```bash
# Check SQLite version in use
python3 -c "from hermes_state import sqlite3; print(sqlite3.sqlite_version)"

# Run tests
python3 -m pytest tests/test_hermes_state.py tests/test_hermes_state_wal_fallback.py -q

# Test trigram search
python3 -c "
from hermes_state import SessionDB
db = SessionDB()
print('FTS enabled:', db._fts_enabled)
cursor = db._conn.cursor()
cursor.execute('SELECT * FROM messages_fts_trigram LIMIT 0')
print('trigram table: OK')
db.close()
"
```

## Pitfalls

- `pysqlite3-binary` must be in the Python environment BEFORE `hermes_state.py` is imported
- The try/except import order means pysqlite3 is always preferred if installed; there's no config toggle
- Other test files with `import sqlite3` at module level may need similar fixes if they interact with `hermes_state` connection objects
