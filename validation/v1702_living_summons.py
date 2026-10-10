# -*- coding: utf-8 -*-
"""Regression for summon HP, death, persistence, soul upgrades and paid revival."""
import asyncio
import random
import sqlite3
from types import SimpleNamespace
from player.session_mixins.era_sky_v1700 import (
    SessionSkyV1700Mixin,ensure_schema,SUMMONS,SUMMON_MANA
)

async def verify():
    checks=0
    dbcon=sqlite3.connect(':memory:')
    dbcon.row_factory=sqlite3.Row
    # Real old v1.70.1 schema, before per-summon HP was introduced.
    dbcon.execute('''CREATE TABLE summons_v1700 (account_id INTEGER NOT NULL,
      summon_type TEXT NOT NULL,level INTEGER NOT NULL DEFAULT 1,
      active INTEGER NOT NULL DEFAULT 1,soul_rank INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY(account_id,summon_type))''')
    dbcon.execute("INSERT INTO summons_v1700 VALUES(9,'wojownik',5,1,2)")
    ensure_schema(dbcon)
    assert {'hp','max_hp'}.issubset({r[1] for r in dbcon.execute('PRAGMA table_info(summons_v1700)')})
    checks+=1

    class DB:
        def __init__(self):
            self.conn=dbcon
            self._v1700_ready=True
            self.inv={}
        def item_qty(self, aid,item): return self.inv.get((aid,item),0)
        def storage_qty(self,aid,storage,item):return 0
        def add_item(self,aid,item,qty=1,commit=True):self.inv[(aid,item)]=self.item_qty(aid,item)+qty
        def remove_item(self,aid,item,qty=1,commit=True):
            if self.item_qty(aid,item)<qty:return False
            self.inv[(aid,item)]-=qty;return True
        def remove_storage_item(self,aid,storage,item,qty=1,commit=True):return False
    db=DB()
    messages=[]
    class Dummy(SessionSkyV1700Mixin):
        def __init__(self,aid,cls):
            self.account_id=aid
            self.current_mana=5000
            self.current_hp=1000
            self.character=SimpleNamespace(level=200,character_level=200,room_id='somewhere')
            self.combat_mob_key=None
            self.cls=cls
            self.server=SimpleNamespace(db=db,party_combat_broadcast=self.party)
        def active_class_names(self):return (self.cls,)
        def max_hp(self):return 1000
        async def send(self,text):messages.append(str(text))
        async def send_combat(self,text,**kwargs):messages.append(str(text))
        async def party(self,*a,**kw):pass
    necro=Dummy(9,'Nekromanta')
    con=dbcon
    necro._v1702_prepare_summon_lives(con)
    row=con.execute("SELECT * FROM summons_v1700 WHERE account_id=9 AND summon_type='wojownik'").fetchone()
    assert row['level']==5 and row['soul_rank']==2 and row['hp']==row['max_hp']>0
    checks+=1
    enemy=SimpleNamespace(alive=True,template_id='dummy')
    assert not await necro.summon_take_enemy_hit_v1702(enemy,raw_damage=500,roll=.99)
    assert con.execute("SELECT hp FROM summons_v1700 WHERE account_id=9").fetchone()[0]>0  # owner-level scaling refreshes HP
    checks+=2
    current_max=con.execute('SELECT max_hp FROM summons_v1700 WHERE account_id=9').fetchone()[0]
    assert await necro.summon_take_enemy_hit_v1702(enemy,raw_damage=current_max*3,roll=0)
    row=con.execute("SELECT hp,active,max_hp FROM summons_v1700 WHERE account_id=9").fetchone()
    assert row['hp']==0 and row['active']==0 and row['max_hp']>0
    checks+=2
    # Logout/login must not restore an unrevived dead minion.
    necro2=Dummy(9,'Nekromanta')
    necro2._v1702_prepare_summon_lives(con)
    assert con.execute("SELECT hp FROM summons_v1700 WHERE account_id=9").fetchone()[0]==0
    checks+=1
    prior=necro2.current_mana
    await necro2.summons_v1700('aktywuj wojownik')
    assert necro2.current_mana==prior
    assert con.execute("SELECT hp,active FROM summons_v1700 WHERE account_id=9").fetchone()['active']==0
    checks+=2
    db.add_item(9,'v1700_dragon_tooth',1)
    await necro2.summons_v1700('aktywuj wojownik')
    row=con.execute("SELECT hp,max_hp,active,level,soul_rank FROM summons_v1700 WHERE account_id=9").fetchone()
    assert row['active']==1 and row['hp']==row['max_hp'] and row['level']==200 and row['soul_rank']==2
    assert necro2.current_mana==prior-SUMMON_MANA['wojownik'] and db.item_qty(9,'v1700_dragon_tooth')==0
    checks+=2
    # Hidden *living* skeleton costs MP but no extra tooth.
    await necro2.summons_v1700('schowaj wojownik')
    prior=necro2.current_mana
    await necro2.summons_v1700('aktywuj wojownik')
    assert necro2.current_mana==prior-SUMMON_MANA['wojownik'] and con.execute("SELECT active FROM summons_v1700 WHERE account_id=9").fetchone()[0]==1
    checks+=1
    # Necro, druid, mage cannot secretly use another class's existing summons.
    fake=Dummy(9,'Mag')
    assert not await fake.summon_take_enemy_hit_v1702(enemy,raw_damage=10,roll=0)
    checks+=1
    # Mage summon: damage can kill, mana alone revives, no materials.
    mage=Dummy(22,'Mag');mage.current_mana=1000
    key='zywiolak_lod_mniejszy'
    await mage.summons_v1700('przywolaj '+key)
    assert con.execute('SELECT active FROM summons_v1700 WHERE account_id=22').fetchone()[0]==1
    await mage.summon_take_enemy_hit_v1702(enemy,raw_damage=100000,roll=0)
    assert con.execute('SELECT hp FROM summons_v1700 WHERE account_id=22').fetchone()[0]==0
    checks+=2
    old_mana=mage.current_mana
    await mage.summons_v1700('aktywuj '+key)
    assert con.execute('SELECT hp FROM summons_v1700 WHERE account_id=22').fetchone()[0]>0
    assert mage.current_mana==old_mana-SUMMON_MANA[key]
    checks+=2
    # Druid tree: resurrection requires pinecones AND MP, neither lost if insufficient.
    druid=Dummy(33,'Druid');druid.current_mana=1000
    db.add_item(33,'v1702_pinecone',2)
    await druid.summons_v1700('przywolaj lifeoak')
    assert db.item_qty(33,'v1702_pinecone')==0
    await druid.summon_take_enemy_hit_v1702(enemy,raw_damage=100000,roll=0)
    old_mp=druid.current_mana
    await druid.summons_v1700('aktywuj lifeoak')
    assert druid.current_mana==old_mp and con.execute('SELECT active FROM summons_v1700 WHERE account_id=33').fetchone()[0]==0
    checks+=3
    db.add_item(33,'v1702_pinecone',2)
    await druid.summons_v1700('aktywuj lifeoak')
    assert druid.current_mana==old_mp-SUMMON_MANA['lifeoak'] and db.item_qty(33,'v1702_pinecone')==0
    checks+=1
    # Upgrades after defeat should not resurrect an unrevived pet; materials+MP remain consistent.
    row=con.execute("SELECT level,max_hp FROM summons_v1700 WHERE account_id=9 AND summon_type='wojownik'").fetchone()
    await necro2.summon_take_enemy_hit_v1702(enemy,raw_damage=100000,roll=0)
    db.add_item(9,'v1700_soul_stone',100)
    before=necro2.current_mana
    await necro2.summons_v1700('ulepsz wojownik czerwony')
    up=con.execute("SELECT level,hp,max_hp FROM summons_v1700 WHERE account_id=9 AND summon_type='wojownik'").fetchone()
    assert up['level']==200 and up['hp']==0 and up['max_hp']==row['max_hp']  # soul stones raise rank, not XP level
    assert necro2.current_mana<before and db.item_qty(9,'v1700_soul_stone')<100
    checks+=2
    assert len(SUMMONS)>=20 and len(SUMMON_MANA)==len(SUMMONS)
    checks+=2
    con.close()
    return checks

def run_regression():
    return asyncio.run(verify())
