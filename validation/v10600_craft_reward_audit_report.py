# -*- coding: utf-8 -*-
"""Read-only NVDA-friendly list of pending v106 craft rewards on an OFFLINE COPY.

Usage: py -3 -B -m validation.v10600_craft_reward_audit_report --db KOPIA.sqlite
This tool does NOT settle, grant, unlock, or modify anything.
"""
from __future__ import annotations
import argparse
from contextlib import closing
import os
from pathlib import Path
import sqlite3


def inspect_copy(path):
    candidate = Path(path).expanduser().resolve(strict=True)
    if not candidate.is_file() or candidate.suffix.lower() not in ('.db', '.db3', '.sqlite', '.sqlite3'):
        raise ValueError('Podaj plik SQLite z bezpiecznej kopii testowej.')
    if os.name == 'nt':
        production = Path('C:/Soulbound-MUD').resolve()
        if candidate == production or production in candidate.parents:
            raise PermissionError('ODMAWIAM: to jest produkcyjne C:\\Soulbound-MUD. Zrob osobna kopie SQLite.')
    # mode=ro / query_only: even a mistake in the implementation cannot write.
    with closing(sqlite3.connect(candidate.as_uri()+'?mode=ro', uri=True, timeout=20)) as conn:
        conn.execute('PRAGMA query_only=ON')
        present=conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                             "AND name='v106_craft_reward_journal'").fetchone()
        if not present:
            return ['Brak tabeli dziennika v106. Nic nie zmieniono.']
        rows=conn.execute('''SELECT account_id,run_id,recipe_id,output_id,
                   output_qty,stage,created_at FROM v106_craft_reward_journal
                   WHERE stage!='complete' ORDER BY account_id,created_at,run_id''').fetchall()
        if not rows:
            return ['Dziennik v106: nie ma przerwanych rozliczen. Nic nie zmieniono.']
        lines=[f'Dziennik v106: {len(rows)} przerwanych rozliczen. TYLKO ODCZYT.']
        for account,run_id,recipe,item,qty,stage,created in rows:
            lines.append(f'Konto {account}; kod {run_id}; receptura {recipe}; '
                         f'produkt {item} x{qty}; ostatni etap {stage}; zapis {created}.')
        lines.append('UWAGA: etap nie potwierdza wyplaty. Nie powtarzaj nagrod bez audytu.')
        return lines


def main(argv=None):
    parser=argparse.ArgumentParser(description='V106: tylko odczyt przerwanych nagrod z KOPII SQLite')
    parser.add_argument('--db',required=True,help='SCIEZKA DO ODDZIELNEJ KOPII SQLite')
    args=parser.parse_args(argv)
    try:
        for line in inspect_copy(args.db):print(line,flush=True)
        return 0
    except (OSError, ValueError, PermissionError, sqlite3.DatabaseError) as exc:
        print('ODMOWA: '+str(exc),flush=True)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
