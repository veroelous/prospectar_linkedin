"""Elegibilidade, preflight, reserva e confirmação de envio. O clique é feito fora (Chrome do Manoel)."""
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from . import config
from .db import connect, operation_lock
from .outreach import text_hash

COUNTED = ("started", "confirmed", "uncertain")


class NotEligible(Exception):
    pass


def _sp_now() -> datetime:
    return datetime.now(ZoneInfo(config.load()["schedule"]["timezone"]))


def check_eligibility(draft_id, con=None):
    con = con or connect()
    d = con.execute(
        "SELECT d.*, c.history_state, c.name FROM drafts d JOIN contacts c ON c.id=d.contact_id WHERE d.id=?",
        (draft_id,)).fetchone()
    if d is None:
        raise NotEligible("rascunho inexistente")
    if d["status"] != "approved":
        raise NotEligible(f"rascunho não aprovado (situação: {d['status']})")
    if d["approved_hash"] != text_hash(d["text"]) or d["approved_hash"] != d["text_hash"]:
        raise NotEligible("texto difere do aprovado — nova aprovação necessária")
    if d["history_state"] != "zero":
        raise NotEligible(f"contato não está `zero` ({d['history_state']})")
    prior = con.execute("SELECT status FROM message_deliveries WHERE draft_id=?", (draft_id,)).fetchall()
    if prior:
        raise NotEligible("já existe tentativa registrada (" + ", ".join(r["status"] for r in prior) + ") — não reenviar")
    return d


def preflight(draft_id, notes="", con=None):
    """Simulação: não digita nem clica. Valida e registra (validade 24 h)."""
    con = con or connect()
    d = check_eligibility(draft_id, con)
    with operation_lock():
        con.execute("INSERT INTO preflights(draft_id,text_hash,created_at,notes) VALUES(?,?,?,?)",
                    (draft_id, d["text_hash"], time.time(), notes))
        con.commit()
    return True


def _window_and_limit(con):
    cfg = config.load()
    now = _sp_now()
    sch = cfg["schedule"]
    if now.weekday() not in sch["weekdays"] or not (sch["start_hour"] <= now.hour < sch["end_hour"]):
        raise NotEligible("fora da janela (dias úteis, 8h–18h São Paulo)")
    day = now.date().isoformat()
    used = con.execute(
        f"SELECT COUNT(*) n FROM message_deliveries WHERE day=? AND status IN ({','.join('?'*len(COUNTED))})",
        (day, *COUNTED)).fetchone()["n"]
    if used >= cfg["limits"]["daily_max_attempts"]:
        raise NotEligible(f"limite diário atingido ({used})")
    return day, now


def reserve(draft_id, con=None):
    """Reserva ANTES do clique (status `started`, conta no limite). Exige preflight válido."""
    con = con or connect()
    with operation_lock():
        d = check_eligibility(draft_id, con)
        day, now = _window_and_limit(con)
        valid = config.load()["limits"]["preflight_valid_hours"] * 3600
        pf = con.execute("SELECT * FROM preflights WHERE draft_id=? AND text_hash=? ORDER BY id DESC LIMIT 1",
                         (draft_id, d["text_hash"])).fetchone()
        if pf is None or time.time() - pf["created_at"] > valid:
            raise NotEligible("preflight ausente ou expirado (24 h)")
        cur = con.execute(
            "INSERT INTO message_deliveries(draft_id,contact_id,status,day,started_at) VALUES(?,?,'started',?,?)",
            (draft_id, d["contact_id"], day, now.isoformat(timespec="seconds")))
        con.commit()
    return cur.lastrowid


def confirm_delivery(delivery_id, event_id, evidence, con=None):
    """Só com evidência: mensagem reencontrada na conversa (texto exato, remetente Manoel, id do evento)."""
    if not event_id or not evidence:
        raise ValueError("confirmação exige identificador do evento e evidência")
    con = con or connect()
    with operation_lock():
        r = con.execute("SELECT * FROM message_deliveries WHERE id=?", (delivery_id,)).fetchone()
        if r is None or r["status"] != "started":
            raise ValueError("entrega inexistente ou não está `started`")
        now = _sp_now().isoformat(timespec="seconds")
        con.execute("UPDATE message_deliveries SET status='confirmed',finished_at=?,event_id=?,evidence=? WHERE id=?",
                    (now, event_id, evidence, delivery_id))
        con.execute("UPDATE drafts SET status='sent' WHERE id=?", (r["draft_id"],))
        con.execute("UPDATE contacts SET history_state='contacted' WHERE id=?", (r["contact_id"],))
        con.commit()


def mark_uncertain(delivery_id, reason, con=None):
    """Falha após reserva/clique sem confirmação: preservar, parar, NÃO reenviar."""
    con = con or connect()
    with operation_lock():
        con.execute("UPDATE message_deliveries SET status='uncertain',finished_at=?,note=? WHERE id=? AND status='started'",
                    (_sp_now().isoformat(timespec="seconds"), reason, delivery_id))
        con.commit()
