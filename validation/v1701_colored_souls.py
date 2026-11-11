# -*- coding: utf-8 -*-
"""Colored souls, mana and backward-compatible summoning regression."""
from __future__ import annotations
import asyncio
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace
from storage.database import _DeferredCommitConnection
from systems.soulstones_v1701 import SOULSTONE_TIERS
from player.session_mixins.era_sky_v1700 import (
    SessionSkyV1700Mixin, ensure_schema, stone_for_enemy, summon_display,
    SUMMON_MANA, summon_upgrade_stones)


async def run_actions():
    checks = 0
    with tempfile.TemporaryDirectory() as tmp:
        conn=_DeferredCommitConnection(sqlite3.connect(str(Path(tmp)/'summons.db')))
        conn.row_factory=sqlite3.Row
        # v1.70.0 schema and a real old summoned warrior: additive migration only.
        conn.execute('''CREATE TABLE summons_v1700 (
            account_id INTEGER NOT NULL, summon_type TEXT NOT NULL,
            level INTEGER NOT NULL DEFAULT 1, active INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY(account_id,summon_type))''')
        conn.execute("INSERT INTO summons_v1700 VALUES(55,'wojownik',7,1)")
        ensure_schema(conn)
        assert 'soul_rank' in {r[1] for r in conn.execute('PRAGMA table_info(summons_v1700)')}
        row=conn.execute('SELECT level,active,soul_rank FROM summons_v1700 WHERE account_id=55').fetchone()
        assert tuple(row)==(7,1,0)
        checks+=3
        class DB:
            def __init__(self):
                self.conn=conn;self._v1700_ready=True;self.inv={}
            def item_qty(self,acc,item):return self.inv.get(item,0)
            def storage_qty(self,acc,where,item):return 0
            def add_item(self,acc,item,qty=1,commit=True):self.inv[item]=self.inv.get(item,0)+qty
            def remove_item(self,acc,item,qty=1,commit=True):
                if self.inv.get(item,0)<qty:return False
                self.inv[item]-=qty;return True
            def remove_storage_item(self,acc,where,item,qty=1,commit=True):return False
        db=DB();msgs=[]
        class Session(SessionSkyV1700Mixin):
            def __init__(self):
                self.character=SimpleNamespace(class_name='Nekromanta',room_id='r')
                self.account_id=55;self.server=SimpleNamespace(db=db)
                self.current_mana=30000;self.combat_mob_key=None
            def active_class_names(self):return [self.character.class_name]
            async def send(self,t):msgs.append(t)
        s=Session()
        # Insufficient mana does not consume mats or change persistence.
        db.inv['v1700_dragon_tooth']=5
        s.current_mana=0
        await s.summons_v1700('przywolaj mag')
        assert db.inv['v1700_dragon_tooth']==5
        assert not conn.execute("SELECT 1 FROM summons_v1700 WHERE summon_type='mag'").fetchone()
        checks+=2
        s.current_mana=4000
        await s.summons_v1700('przywolaj mag')
        assert db.inv['v1700_dragon_tooth']==3 and s.current_mana==4000-SUMMON_MANA['mag']
        checks+=2
        # Legacy red stones upgrade old warrior, no migration of old item ID.
        db.inv['v1700_soul_stone']=3
        before=s.current_mana
        await s.summons_v1700('ulepsz wojownik')
        assert conn.execute("SELECT level,soul_rank FROM summons_v1700 WHERE summon_type='wojownik'").fetchone()[0]==7
        assert 0<=db.inv['v1700_soul_stone']<3 and s.current_mana<before
        checks+=2
        # Yellow stones give a modest tier; deep-blue promotes warrior to knight.
        db.inv['v1701_soul_deep_blue']=3
        mana=s.current_mana
        await s.summons_v1700('ulepsz wojownik ciemnoniebieski')
        warrior=conn.execute("SELECT level,soul_rank FROM summons_v1700 WHERE summon_type='wojownik'").fetchone()
        assert tuple(warrior)==(7,4)
        assert summon_display('wojownik',warrior['soul_rank'])=='Rycerz Szkieletów'
        assert s.current_mana<mana
        checks+=3
        # A lower color may give levels but never downgrade a knight.
        db.inv['v1701_soul_yellow']=3
        await s.summons_v1700('ulepsz wojownik zolty')
        assert conn.execute("SELECT soul_rank FROM summons_v1700 WHERE summon_type='wojownik'").fetchone()[0]==4
        checks+=1
        # No mana -> no stone disappearance and no level gain.
        db.inv['v1701_soul_black']=8
        lvl=conn.execute("SELECT level FROM summons_v1700 WHERE summon_type='wojownik'").fetchone()[0]
        s.current_mana=0
        await s.summons_v1700('ulepsz wojownik czarny')
        assert db.inv['v1701_soul_black']==8
        assert conn.execute("SELECT level FROM summons_v1700 WHERE summon_type='wojownik'").fetchone()[0]==lvl
        checks+=2
        # Forging doesn't work with zero mana or fewer than 3 stones.
        db.inv['v1700_soul_stone']=3
        await s._v1701_forge('czerwony')
        assert db.inv['v1700_soul_stone']==3
        s.current_mana=500
        previous_yellow=db.inv.get('v1701_soul_yellow',0)
        await s._v1701_forge('czerwony')
        assert db.inv['v1700_soul_stone']==0
        assert db.inv['v1701_soul_yellow']==previous_yellow+1
        assert s.current_mana==465
        checks+=4
        # Every activation after hiding needs mana, but hiding is free.
        await s.summons_v1700('schowaj mag')
        s.current_mana=0
        await s.summons_v1700('aktywuj mag')
        assert conn.execute("SELECT active FROM summons_v1700 WHERE summon_type='mag'").fetchone()[0]==0
        s.current_mana=1000
        await s.summons_v1700('aktywuj mag')
        assert conn.execute("SELECT active FROM summons_v1700 WHERE summon_type='mag'").fetchone()[0]==1
        assert s.current_mana==1000-SUMMON_MANA['mag']
        checks+=3
        await s.summons_v1700('kamienie')
        assert any('Czarny Kamień Duszy' in m for m in msgs)
        checks+=1
        conn.close()
    return checks


def run_regression(server=None):
    count=0
    assert len(SOULSTONE_TIERS)==9
    assert SOULSTONE_TIERS[0][2]=='v1700_soul_stone'
    count+=2
    assert len({x[0] for x in SOULSTONE_TIERS})==9
    assert len({x[2] for x in SOULSTONE_TIERS})==9
    assert all(SOULSTONE_TIERS[i][3]<SOULSTONE_TIERS[i+1][3] for i in range(8))
    assert all(SOULSTONE_TIERS[i][4]<SOULSTONE_TIERS[i+1][4] for i in range(8))
    count+=4
    for lvl in [1,20,99,100,180,350,450,570,670,780,800]:
        for roll in [0,0.3,0.6,0.95]:
            tier=stone_for_enemy(lvl,roll=roll)
            assert lvl>=tier[4]
            assert tier in SOULSTONE_TIERS
            count+=2
    assert stone_for_enemy(800,True,0)[0]=='czarny'
    assert stone_for_enemy(1,False,0)[0]=='czerwony'
    assert summon_display('wojownik',4)=='Rycerz Szkieletów'
    assert summon_display('mag',4)=='Szkielet Licz'
    assert summon_upgrade_stones(7)==3
    count+=5
    if server:
        for tier in SOULSTONE_TIERS:
            assert tier[2] in server.ITEMS
            count+=1
    return count + asyncio.run(run_actions())
