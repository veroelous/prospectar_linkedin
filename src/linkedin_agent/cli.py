"""Comandos de dados (sem navegador): status, plano, aprovação registrada pelo Manoel."""
import argparse
from pathlib import Path

from . import contacts, outreach
from .config import ROOT
from .db import connect


def main(argv=None):
    p = argparse.ArgumentParser(prog="linkedin-agent")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("verify-list", help="lista até 60 `unverified` para conferir")
    sub.add_parser("export-plan")
    a = p.parse_args(argv)
    con = connect()
    if a.cmd == "status":
        for k, v in contacts.counts(con).items():
            print(f"{k:12} {v}")
        for r in con.execute("SELECT status, COUNT(*) n FROM drafts GROUP BY 1"):
            print(f"rascunho {r['status']:9} {r['n']}")
    elif a.cmd == "verify-list":
        for c in contacts.pending_verification(con):
            print(c["id"], c["connected_on"], c["name"], c["profile_url"])
    elif a.cmd == "export-plan":
        print(outreach.export_plan(ROOT / "data", con=con))


if __name__ == "__main__":
    main()
