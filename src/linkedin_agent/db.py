import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from .config import ROOT

SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
  id INTEGER PRIMARY KEY,
  profile_url TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  headline TEXT,
  company TEXT,
  connected_on TEXT NOT NULL,              -- AAAA-MM-DD
  history_state TEXT NOT NULL DEFAULT 'unverified'
    CHECK (history_state IN ('unverified','zero','has_history','contacted')),
  history_evidence TEXT,
  history_checked_at TEXT
);
CREATE TABLE IF NOT EXISTS drafts (
  id INTEGER PRIMARY KEY,
  contact_id INTEGER NOT NULL REFERENCES contacts(id),
  text TEXT NOT NULL,
  text_hash TEXT NOT NULL,
  evidence TEXT NOT NULL,                  -- trecho real do perfil
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending','approved','sent','blocked')),
  planned_date TEXT,
  approved_by TEXT,
  approved_at TEXT,
  approved_hash TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS message_deliveries (
  id INTEGER PRIMARY KEY,
  draft_id INTEGER NOT NULL REFERENCES drafts(id),
  contact_id INTEGER NOT NULL REFERENCES contacts(id),
  status TEXT NOT NULL CHECK (status IN ('started','confirmed','uncertain')),
  day TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  event_id TEXT,
  evidence TEXT,
  note TEXT
);
CREATE TABLE IF NOT EXISTS preflights (
  id INTEGER PRIMARY KEY,
  draft_id INTEGER NOT NULL REFERENCES drafts(id),
  text_hash TEXT NOT NULL,
  created_at REAL NOT NULL,
  notes TEXT
);
"""


def db_path() -> Path:
    return Path(os.environ.get("LINKEDIN_AGENT_DB", ROOT / "data" / "agent.db"))


def connect(path: Path | None = None) -> sqlite3.Connection:
    p = Path(path or db_path())
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


@contextmanager
def operation_lock(path: Path | None = None, timeout: float = 30.0):
    """Lock de arquivo para escritas. Não coordena outros computadores."""
    lock = Path(str(path or db_path()) + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + timeout
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            if time.time() > deadline:
                raise TimeoutError(f"Lock ocupado: {lock}")
            time.sleep(0.2)
    try:
        yield
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass
