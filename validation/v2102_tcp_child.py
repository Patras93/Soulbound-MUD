# -*- coding: utf-8 -*-
"""Private bootstrap for six-player test. Only invoked with guarded TEST env."""
from __future__ import annotations
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
from core.classes_skills import CLASSES, RACES
from storage.database import Database


def main():
    path = Path(os.environ['SOULBOUND_DB']).resolve()
    if not (os.environ.get('SOULBOUND_TCP_TEST_CHILD') == '1'
            and os.environ.get('SOULBOUND_HOST') == '127.0.0.1'
            and path.name == 'six_players.sqlite'
            and path.parent.name.startswith('soulbound-tcp6-')
            and os.environ.get('SOULBOUND_MAX_CLIENTS') == '6'):
        raise RuntimeError('Only disposable local six-player tests are allowed')
    db = Database(str(path))
    try:
        for index in range(6):
            account = f'tcpcheck{index+1}'
            name = f'Testtcp{index+1}'
            existing = db.account_by_name(account)
            if existing is None:
                aid = db.create_account(account, 'test_only_tcp_2026_password')
                cases = dict.fromkeys(('nom','gen','dat','acc','ins','loc','voc'), name)
                db.create_character_for_master(aid, name, RACES[0], CLASSES[index], cases)
            else:
                aid = int(existing['id'])
                rows = db.characters_for_master(aid)
                if len(rows) != 1 or rows[0]['name'] != name:
                    raise RuntimeError('Unexpected test account state: '+account)
        db.conn.commit()
    finally:
        db.conn.close()
    print('TEST_TCP_ACCOUNTS_READY', flush=True)
    server.main()


if __name__ == '__main__':
    main()
