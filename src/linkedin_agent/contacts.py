"""Fila de contatos e conferência de histórico. Inventariar ≠ verificar."""
from datetime import datetime, timezone

from . import config
from .db import connect, operation_lock

STATES = ("unverified", "zero", "has_history", "contacted")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def upsert_connection(profile_url, name, connected_on, headline=None, company=None, con=None):
    """Incorpora conexão sem duplicar; nunca altera estado de histórico existente."""
    con = con or connect()
    with operation_lock():
        con.execute(
            """INSERT INTO contacts(profile_url,name,headline,company,connected_on)
               VALUES(?,?,?,?,?)
               ON CONFLICT(profile_url) DO UPDATE SET
                 headline=COALESCE(excluded.headline,headline),
                 company=COALESCE(excluded.company,company)""",
            (profile_url.rstrip("/") + "/", name, headline, company, connected_on),
        )
        con.commit()


def pending_verification(con=None, limit=None):
    """Até N (padrão 60) `unverified` por execução, mais antigos primeiro."""
    con = con or connect()
    limit = limit or config.load()["limits"]["history_checks_per_run"]
    return con.execute(
        "SELECT * FROM contacts WHERE history_state='unverified' ORDER BY connected_on, id LIMIT ?",
        (min(limit, config.load()["limits"]["history_checks_per_run"]),),
    ).fetchall()


def record_history(contact_id, state, evidence, con=None):
    """Registra estado com evidência obrigatória. Em dúvida, mantenha `unverified`."""
    if state not in STATES:
        raise ValueError(f"estado inválido: {state}")
    if not evidence or not evidence.strip():
        raise ValueError("evidência obrigatória (ex.: 'conversa aberta e recarregada; 0 eventos')")
    con = con or connect()
    with operation_lock():
        con.execute(
            "UPDATE contacts SET history_state=?, history_evidence=?, history_checked_at=? WHERE id=?",
            (state, evidence.strip(), _now(), contact_id),
        )
        con.commit()


def eligible_queue(con=None):
    """Só `zero`, conexões desde a data configurada, sem rascunho já enviado/aprovado ativo,
    das mais antigas para as mais novas."""
    con = con or connect()
    since = config.load()["queue"]["connected_since"]
    return con.execute(
        """SELECT c.* FROM contacts c
           WHERE c.history_state='zero' AND c.connected_on>=?
             AND NOT EXISTS (SELECT 1 FROM drafts d WHERE d.contact_id=c.id
                             AND d.status IN ('sent','approved','blocked'))
           ORDER BY c.connected_on, c.id""",
        (since,),
    ).fetchall()


def counts(con=None) -> dict:
    con = con or connect()
    out = {s: 0 for s in STATES}
    for r in con.execute("SELECT history_state s, COUNT(*) n FROM contacts GROUP BY 1"):
        out[r["s"]] = r["n"]
    return out
