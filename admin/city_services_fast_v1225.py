# -*- coding: utf-8 -*-
"""v1.22.5 safe SQLite regression checks, no real players or network."""
from pathlib import Path
import tempfile
import time

from storage.database import Database


def city_services_fast_v1225():
    checks = 0
    def ok(condition, name):
        nonlocal checks
        if not condition:
            raise AssertionError('CITY SERVICES v1.22.5: ' + name)
        checks += 1

    base = Path(__file__).resolve().parent.parent
    equipment = (base/'player/session_mixins/inventory_equipment.py').read_text('utf8')
    ok('async def inspect_equipped_v1225' in equipment, 'equipment inspector')
    ok("mode.startswith('info ')" in equipment, 'eq info syntax')
    registry = (base/'player/session_mixins/command_registry.py').read_text('utf8')
    ok("'hunters1225': ('handle_hunters_v1225'" in registry, 'hunter routing')
    ok("('lowcy', 'łowcy'" not in registry or 'hunters1225' in registry, 'alias')
    from data.rooms import ROOMS
    ok(ROOMS['square']['exits']['northeast']=='soul_mercenary_tavern_v1225', 'tavern route')
    ok(ROOMS['soul_mercenary_tavern_v1225']['exits']['east']=='soul_hunter_board_v1225', 'hunter route')
    with tempfile.TemporaryDirectory() as tmp:
        db=Database(str(Path(tmp)/'test.db'))
        c=db.conn
        for username in ('Tester-A','Tester-B'):
            c.execute("INSERT INTO accounts(username,password_salt,password_hash) VALUES(?,?,?)", (username,'x','y'))
        a,b=[x[0] for x in c.execute('SELECT id FROM accounts ORDER BY id').fetchall()]
        for id in (a,b):c.execute('INSERT INTO account_characters(master_account_id,character_account_id,slot) VALUES(?,?,1)',(id,id))
        c.execute('INSERT INTO bank_balances(account_id,silver,gold,mithril) VALUES(?,1000000,0,0)',(a,))
        c.execute('INSERT INTO bank_balances(account_id,silver,gold,mithril) VALUES(?,0,0,0)',(b,))
        c.execute('INSERT INTO bank_items(account_id,item_id,quantity) VALUES(?,?,5)',(a,'healing_potion'))
        c.commit()
        ok(db.transfer_bank_v1225(a,'Tester-B',silver=300000)=='ok','money transfer')
        ok(c.execute('SELECT silver FROM bank_balances WHERE account_id=?',(a,)).fetchone()[0]==700000,'bank debit')
        ok(c.execute('SELECT silver FROM bank_balances WHERE account_id=?',(b,)).fetchone()[0]==300000,'bank credit')
        ok(db.transfer_bank_v1225(a,'Tester-B',silver=800000)=='funds','overdraft blocked')
        ok(db.transfer_bank_v1225(a,'NoSuchAccount',silver=1)=='recipient','recipient check')
        ok(db.transfer_bank_v1225(a,'Tester-A',silver=1)=='self','self transfer blocked')
        ok(db.transfer_bank_v1225(a,'Tester-B',item_id='healing_potion',quantity=2)=='ok','item transfer')
        ok(db.bank_item_qty(a,'healing_potion')==3,'item source kept')
        ok(db.bank_item_qty(b,'healing_potion')==2,'item destination')
        ok(db.transfer_bank_v1225(a,'Tester-B',item_id='healing_potion',quantity=10)=='funds','item overdraft blocked')
        ok(len(db.bank_transfer_history_v1225(a))==2,'bank history')
        for tier,mob,needed,reward in [('zwykle','goblin',6,15000),('elitarne','v028_region_01_elite',4,140000),('boss','goblin_warchief',1,2000000)]:
            now=int(time.time())
            ok(db.hunter_accept_v1225(a,tier,mob,needed,reward,now)=='ok','hunter accept '+tier)
            ok(db.hunter_accept_v1225(a,tier,mob,needed,reward,now)=='active','no duplicate accept '+tier)
            for _ in range(needed):db.hunter_kill_v1225(a,mob)
            ok(db.hunter_state_v1225(a,tier)['state']=='ready','hunter progress '+tier)
            ok(db.hunter_claim_v1225(a,tier,now,3600)==reward,'hunter reward '+tier)
            ok(db.hunter_claim_v1225(a,tier,now,3600)==0,'no second reward '+tier)
            ok(db.hunter_accept_v1225(a,tier,mob,needed,reward,now)=='cooldown','hunter cooldown '+tier)
        ok(db.hunter_state_v1225(b,'boss') is None,'separate character bounty')
    return checks


if __name__ == '__main__':
    from core.native_runtime import load_native_runtime
    load_native_runtime(Path(__file__).resolve().parent.parent, {})
    print(f'CITY SERVICES v1.22.5: {city_services_fast_v1225()} checks PASS')
