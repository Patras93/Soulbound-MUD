# -*- coding: utf-8 -*-
"""Exact shared production Soul Weapon post-hit method, with disposable SQLite."""
from __future__ import annotations
import os,sqlite3,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.soul_weapon_astral_v10600 import SECONDARY_KEY
from systems.soul_weapon_elements_v10500 import SELECT_KEY
import systems.uoss_basic_weapon_shared_v8000 as shared

def run():
    original=os.environ.get('SOULBOUND_V106_STAGING')
    db=sqlite3.connect(':memory:')
    db.execute('CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,text_value TEXT,PRIMARY KEY(account_id,record_key))')
    db.execute('INSERT INTO player_records_v03051 VALUES(7,?,?)',(SELECT_KEY,'lightning'))
    db.execute('INSERT INTO player_records_v03051 VALUES(7,?,?)',(SECONDARY_KEY,'nature'))
    checks=0
    class A:
        account_id=7
        server=SimpleNamespace(db=SimpleNamespace(conn=db))
        character=SimpleNamespace(soul_tier=3100)
        def max_hp(self):return 5000
        def max_mana(self):return 1000
        def equipment_property_totals(self):return {}
    actor=A()
    traits={'lifesteal_percent':10,'mana_restore_percent':5}
    mastery={'echo_chance':0,'echo_damage_percent':0}
    mob=SimpleNamespace(hp=10000)
    try:
        for staging,element,heal,mp in [
            (False,'nature',100,50),
            (True,'nature',108,54),
            (True,'void',96,48),
            (True,'astral',100,50),
        ]:
            os.environ['SOULBOUND_V106_STAGING']='1' if staging else ''
            db.execute('UPDATE player_records_v03051 SET text_value=? WHERE account_id=7 AND record_key=?',(element,SECONDARY_KEY))
            actor.current_hp=1000;actor.current_mana=500;actor._recap52_heal=0
            with patch('world.uoss_superboss_runtime.superboss_healing_blocked_v11179',return_value=False):
                output=shared.weapon_after_hit(actor,mob,1000,traits,mastery)
            assert output==(0,heal,mp),(staging,element,output);checks+=1
            assert actor.current_hp==1000+heal and actor.current_mana==500+mp,(staging,element);checks+=1
            assert actor._recap52_heal==heal,(staging,element);checks+=1
        os.environ['SOULBOUND_V106_STAGING']='1'
        actor.character.soul_tier=3099
        db.execute('UPDATE player_records_v03051 SET text_value=? WHERE account_id=7 AND record_key=?',('nature',SECONDARY_KEY))
        actor.current_hp=1000;actor.current_mana=500
        with patch('world.uoss_superboss_runtime.superboss_healing_blocked_v11179',return_value=False):
            output=shared.weapon_after_hit(actor,mob,1000,traits,mastery)
        assert output==(0,100,50);checks+=1
        actor.character.soul_tier=3100
        actor.current_hp=1000;actor.current_mana=500
        with patch('world.uoss_superboss_runtime.superboss_healing_blocked_v11179',return_value=True):
            output=shared.weapon_after_hit(actor,mob,1000,traits,mastery)
        assert output[1]==0 and actor.current_hp==1000;checks+=1
        assert db.execute('SELECT text_value FROM player_records_v03051 WHERE account_id=7 AND record_key=?',(SELECT_KEY,)).fetchone()[0]=='lightning';checks+=1
        return checks
    finally:
        if original is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=original
        db.close()
if __name__=='__main__':print('V106 SOUL WEAPON REGENERATION: '+str(run())+' PASS',flush=True)
