# -*- coding: utf-8 -*-
"""Pure two-element and persistent SQLite smoke; does not imply combat integration."""
from pathlib import Path
import sqlite3,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.soul_weapon_astral_v10600 import (
    normalize_secondary,select_secondary,get_secondary,resonance_profile)

def run():
    conn=sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE player_records_v03051('
       'account_id INTEGER,record_key TEXT,value INTEGER NOT NULL DEFAULT 0,'
       'text_value TEXT NOT NULL DEFAULT "",updated_at TEXT DEFAULT CURRENT_TIMESTAMP,'
       'PRIMARY KEY(account_id,record_key))')
    conn.execute('INSERT INTO player_records_v03051(account_id,record_key,text_value) '
       "VALUES(3,'soul_weapon_element_v10500','lightning')")
    conn.execute('INSERT INTO player_records_v03051(account_id,record_key,value) '
       "VALUES(3,'soul_weapon_impulse_cooldown_v10500',123456)")
    checks=0
    def ok(cond,msg):
        nonlocal checks
        assert cond,msg
        checks+=1
    ok(not select_secondary(conn,3,3099,'astral')[0],'unlock too early')
    ok(not select_secondary(conn,3,3100,'unknown')[0],'invalid element')
    ok(not select_secondary(conn,2,3100,'astral')[0],'primary required')
    ok(select_secondary(conn,3,3100,'próżnia')[0],'valid new element')
    ok(get_secondary(conn,3)=='void','saved secondary')
    ok(conn.execute("SELECT value FROM player_records_v03051 WHERE record_key='soul_weapon_impulse_cooldown_v10500'").fetchone()[0]==123456,'original cooldown untouched')
    ok(conn.execute("SELECT text_value FROM player_records_v03051 WHERE record_key='soul_weapon_element_v10500'").fetchone()[0]=='lightning','original primary untouched')
    ok(normalize_secondary('Próżnia')[0]=='void','Polish alias')
    profiles=[resonance_profile('lightning',s,boss=boss)
           for s in ('astral','nature','void') for boss in (False,True)]
    ok(all(.9<=q['damage']<=1.12 and .9<=q['regeneration']<=1.12 for q in profiles),'effect bounds')
    ok(resonance_profile('lightning','void',boss=True)['damage']>
       resonance_profile('lightning','void',boss=False)['damage'],'context dependent')
    ok(resonance_profile('lightning','natura')['regeneration']>
       resonance_profile('lightning','astral')['regeneration'],'different tradeoff')
    ok(resonance_profile('unknown','void')['damage']==1,'no unknown primary boost')
    return checks
if __name__=='__main__':print('V106 SOUL WEAPON STAGING:',run(),'PASS',flush=True)
