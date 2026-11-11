# -*- coding: utf-8 -*-
"""Private bootstrap for five-player test. Only invoked with guarded TEST env."""
from __future__ import annotations
import os
import json
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
            and path.name == 'five_players.sqlite'
            and path.parent.name.startswith('soulbound-tcp5-')
            and os.environ.get('SOULBOUND_MAX_CLIENTS') == '5'):
        raise RuntimeError('Only disposable local five-player tests are allowed')
    db = Database(str(path))
    try:
        for index in range(5):
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
    # v2.32.0: obtain *runtime* room layout after NPC private-room relocation
    # and world topology generation. Static data/npcs.py locations are stale.
    from validation.v2320_autonomous_routes import shortest_route
    sol_room = server.NPCS['archivist']['room']
    doran_room = server.NPCS['doran']['room']
    journey = {
        'to_sol': shortest_route(server.ROOMS, 'temple', sol_room),
        'to_doran': shortest_route(server.ROOMS, sol_room, doran_room),
        'sol_room': sol_room,
        'doran_room': doran_room,
    }
    if journey['to_sol'] is None or journey['to_doran'] is None:
        raise RuntimeError('Runtime NPC courier route unreachable: '+repr(journey))
    if len(journey['to_sol']) > 100 or len(journey['to_doran']) > 100:
        raise RuntimeError('Courier NPC route too long; inspect world topology')
    print('TEST_AUTOPLAYER_ROUTE_JSON:'+json.dumps(journey,ensure_ascii=False),flush=True)
    print('TEST_TCP_ACCOUNTS_READY', flush=True)
    server.main()


if __name__ == '__main__':
    main()
