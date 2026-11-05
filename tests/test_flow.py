import os, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ["LINKEDIN_AGENT_DB"] = str(Path(tempfile.mkdtemp()) / "t.db")

from linkedin_agent import contacts, messages, outreach
from linkedin_agent.db import connect

TXT = ("Olá, Ana. Vi no seu perfil que você lidera finanças na Acme Log. Tenho um conteúdo sobre como "
       "uma empresa pode estar faturando mais e ficando mais frágil ao mesmo tempo. Posso compartilhar com você?")
PROFILE = "Ana Souza — Diretora financeira na Acme Log. lidera finanças na Acme Log"


class Flow(unittest.TestCase):
    def setUp(self):
        p = Path(os.environ["LINKEDIN_AGENT_DB"])
        for f in p.parent.glob("t.db*"): f.unlink()
        self.con = connect()
        contacts.upsert_connection("https://www.linkedin.com/in/ana", "Ana Souza", "2026-01-10", con=self.con)
        self.cid = self.con.execute("SELECT id FROM contacts").fetchone()["id"]

    def test_unverified_not_queued(self):
        self.assertEqual(contacts.eligible_queue(self.con), [])
        with self.assertRaises(ValueError):
            outreach.save_personalized_draft(self.cid, TXT, "lidera finanças na Acme Log", PROFILE, con=self.con)

    def test_history_requires_evidence(self):
        with self.assertRaises(ValueError):
            contacts.record_history(self.cid, "zero", "", con=self.con)

    def test_text_rules(self):
        self.assertEqual(outreach.validate_text(TXT, "Ana Souza"), [])
        self.assertTrue(outreach.validate_text(TXT + " Veja https://x.com", "Ana Souza"))
        self.assertTrue(outreach.validate_text(TXT.replace("Posso compartilhar com você?", "Vamos agendar? Posso?"), "Ana Souza"))

    def test_full_flow_and_no_resend(self):
        contacts.record_history(self.cid, "zero", "conversa recarregada; 0 eventos", con=self.con)
        with self.assertRaises(ValueError):  # evidência inventada
            outreach.save_personalized_draft(self.cid, TXT, "dirige a Beta SA", PROFILE, con=self.con)
        did = outreach.save_personalized_draft(self.cid, TXT, "lidera finanças na Acme Log", PROFILE, con=self.con)
        with self.assertRaises(messages.NotEligible):  # pendente
            messages.preflight(did, con=self.con)
        with self.assertRaises(PermissionError):
            outreach.approve_draft(did, "claude", con=self.con)
        outreach.approve_draft(did, "Manoel", con=self.con)
        messages.preflight(did, con=self.con)
        with mock.patch.object(messages, "_sp_now") as n:
            from datetime import datetime
            from zoneinfo import ZoneInfo
            n.return_value = datetime(2026, 11, 5, 10, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))  # quinta
            rid = messages.reserve(did, con=self.con)
            with self.assertRaises(messages.NotEligible):
                messages.reserve(did, con=self.con)  # started bloqueia repetição
            messages.confirm_delivery(rid, "evt-1", "mensagem reencontrada", con=self.con)
        self.assertEqual(self.con.execute("SELECT status FROM drafts").fetchone()[0], "sent")

    def test_window_blocks_weekend(self):
        contacts.record_history(self.cid, "zero", "ok", con=self.con)
        did = outreach.save_personalized_draft(self.cid, TXT, "lidera finanças na Acme Log", PROFILE, con=self.con)
        outreach.approve_draft(did, "Manoel", con=self.con)
        messages.preflight(did, con=self.con)
        with mock.patch.object(messages, "_sp_now") as n:
            from datetime import datetime
            from zoneinfo import ZoneInfo
            n.return_value = datetime(2026, 11, 7, 10, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))  # sábado
            with self.assertRaises(messages.NotEligible):
                messages.reserve(did, con=self.con)

    def test_edit_resets_approval(self):
        contacts.record_history(self.cid, "zero", "ok", con=self.con)
        did = outreach.save_personalized_draft(self.cid, TXT, "lidera finanças na Acme Log", PROFILE, con=self.con)
        outreach.approve_draft(did, "Manoel", con=self.con)
        outreach.edit_draft(did, TXT.replace("Vi no seu perfil", "Li no seu perfil"), con=self.con)
        self.assertEqual(self.con.execute("SELECT status FROM drafts").fetchone()[0], "pending")


if __name__ == "__main__":
    unittest.main()
