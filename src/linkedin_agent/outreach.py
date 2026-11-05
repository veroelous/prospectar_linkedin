"""Rascunhos individuais, validação de texto, aprovação, lotes e exportação."""
import hashlib
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import config
from .contacts import eligible_queue
from .db import connect, operation_lock


def text_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def validate_text(text: str, name: str) -> list[str]:
    """Devolve lista de problemas; vazia = texto aceitável para ir a aprovação."""
    cfg = config.load()["text"]
    problems = []
    low = text.lower()
    if name.split()[0].lower() not in low:
        problems.append("sem saudação pelo nome")
    if text.count("?") > cfg["max_questions"]:
        problems.append(f"mais de {cfg['max_questions']} pergunta")
    if text.count("?") < 1:
        problems.append("falta o pedido de permissão (uma pergunta)")
    if re.search(r"https?://|www\.", low):
        problems.append("contém link")
    if len(text) > cfg["max_chars"]:
        problems.append("texto longo demais")
    for t in cfg["blocked_terms"] + cfg["forbidden_claims"]:
        if t in low:
            problems.append(f"termo bloqueado: {t!r}")
    if "faturando mais" not in low or "frágil" not in low and "fragil" not in low:
        problems.append("falta referência ao conteúdo (faturar mais e ficar mais frágil)")
    return problems


def save_personalized_draft(contact_id, text, evidence, profile_text, planned_date=None, con=None):
    """Salva como `pending`. Exige que a evidência seja trecho real do perfil lido e
    que apareça (ao menos em parte) na mensagem. Nunca aprova."""
    con = con or connect()
    c = con.execute("SELECT * FROM contacts WHERE id=?", (contact_id,)).fetchone()
    if c is None:
        raise ValueError("contato inexistente")
    if c["history_state"] != "zero":
        raise ValueError(f"contato não está `zero` ({c['history_state']})")
    if len(evidence.strip()) < 8 or _norm(evidence) not in _norm(profile_text):
        raise ValueError("evidência não encontrada no texto do perfil informado")
    problems = validate_text(text, c["name"])
    if problems:
        raise ValueError("texto reprovado: " + "; ".join(problems))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with operation_lock():
        cur = con.execute(
            """INSERT INTO drafts(contact_id,text,text_hash,evidence,planned_date,created_at)
               VALUES(?,?,?,?,?,?)""",
            (contact_id, text.strip(), text_hash(text), evidence.strip(), planned_date, now),
        )
        con.commit()
    return cur.lastrowid


def approve_draft(draft_id, approved_by, con=None):
    """Registra aprovação do Manoel para destinatário e texto exatos. Só chamar após
    aprovação explícita dele; a IA não aprova em nome dele."""
    if approved_by.strip().lower() not in ("manoel", "manoel gonçalves", "manoel goncalves"):
        raise PermissionError("somente o Manoel aprova mensagens")
    con = con or connect()
    d = con.execute("SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone()
    if d is None or d["status"] != "pending":
        raise ValueError("rascunho inexistente ou não pendente")
    with operation_lock():
        con.execute(
            "UPDATE drafts SET status='approved',approved_by=?,approved_at=?,approved_hash=? WHERE id=?",
            (approved_by, datetime.now(timezone.utc).isoformat(timespec="seconds"), d["text_hash"], draft_id),
        )
        con.commit()


def edit_draft(draft_id, new_text, con=None):
    """Qualquer alteração volta o rascunho a `pending` (nova aprovação)."""
    con = con or connect()
    d = con.execute("SELECT d.*, c.name FROM drafts d JOIN contacts c ON c.id=d.contact_id WHERE d.id=?",
                    (draft_id,)).fetchone()
    if d is None or d["status"] in ("sent",):
        raise ValueError("rascunho inexistente ou já enviado")
    problems = validate_text(new_text, d["name"])
    if problems:
        raise ValueError("texto reprovado: " + "; ".join(problems))
    with operation_lock():
        con.execute(
            "UPDATE drafts SET text=?,text_hash=?,status='pending',approved_by=NULL,approved_at=NULL,approved_hash=NULL WHERE id=?",
            (new_text.strip(), text_hash(new_text), draft_id),
        )
        con.commit()


def _next_business_day(d: date) -> date:
    wd = config.load()["schedule"]["weekdays"]
    while d.weekday() not in wd:
        d += timedelta(days=1)
    return d


def plan_batches(start: date | None = None, con=None):
    """Distribui a fila elegível (mais antigos primeiro) em lotes de até 15 por dia útil.
    A data planejada NÃO autoriza envio."""
    con = con or connect()
    per_day = config.load()["queue"]["per_day"]
    day = _next_business_day(start or date.today())
    batches, current = [], []
    for c in eligible_queue(con):
        current.append(c)
        if len(current) == per_day:
            batches.append((day, current))
            current, day = [], _next_business_day(day + timedelta(days=1))
    if current:
        batches.append((day, current))
    return batches


def export_plan(out_dir: Path, start: date | None = None, con=None) -> Path:
    """Gera plano-contatos-2026.md com mensagem integral, ID do rascunho e situação.
    Saída deve ficar em data/ (fora do git)."""
    con = con or connect()
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# Plano de primeiras abordagens — 2026", "",
             "> Data planejada não autoriza envio. Aprovação vale para destinatário e texto exatos.", ""]
    for day, contacts in plan_batches(start, con):
        lines += [f"## {day.isoformat()} ({len(contacts)} contatos)", ""]
        for c in contacts:
            d = con.execute("SELECT * FROM drafts WHERE contact_id=? ORDER BY id DESC LIMIT 1", (c["id"],)).fetchone()
            lines += [f"### {c['name']} — {c['profile_url']}",
                      f"- Contexto: {c['headline'] or '—'} / {c['company'] or '—'}",
                      f"- Conectado em: {c['connected_on']}"]
            if d:
                lines += [f"- Personalização observada: {d['evidence']}",
                          f"- Rascunho #{d['id']} — situação: **{d['status']}**", "", f"> {d['text']}", ""]
            else:
                lines += ["- Sem rascunho (ler perfil e redigir antes de apresentar)", ""]
    path = out_dir / "plano-contatos-2026.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
