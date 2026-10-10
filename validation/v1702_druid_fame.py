# -*- coding: utf-8 -*-
"""Regression: druid tree casting, durable gather, fame per boss and party."""
from __future__ import annotations
import asyncio
import sqlite3
from types import SimpleNamespace
from player.session_mixins.era_sky_v1700 import SessionSkyV1700Mixin,ensure_schema,SUMMONS
from systems.fame_v1702 import fame_catalog,fame_report,record_fame_kill

async def _async_case():
    checks=0
    conn=sqlite3.connect(':memory:')
    conn.row_factory=sqlite3.Row
    ensure_schema(conn)
    class DB:
        def __init__(self): self.conn=conn;self._v1700_ready=True;self.inv={}
        def item_qty(self,aid,key):return self.inv.get((aid,key),0)
        def storage_qty(self,aid,where,key):return 0
        def add_item(self,aid,key,qty=1,commit=True):self.inv[(aid,key)]=self.item_qty(aid,key)+qty
        def remove_item(self,aid,key,qty=1,commit=True):
            if self.item_qty(aid,key)<qty:return False
            self.inv[(aid,key)]-=qty;return True
        def remove_storage_item(self,*a,**k):return False
    db=DB();messages=[]
    class Dummy(SessionSkyV1700Mixin):
        def __init__(self,aid):
            self.account_id=aid;self.server=SimpleNamespace(db=db)
            self.character=SimpleNamespace(class_name='Druid',room_id='whisper_grove',character_level=250)
            self.current_mana=0;self.combat_mob_key=None
        async def send(self,message):messages.append(str(message))
        def active_class_names(self):return ('Druid',)
    druid=Dummy(42)
    cone='v1702_pinecone'
    assert SUMMONS['lifeoak'][2]=={cone:2}
    assert SUMMONS['ancientoak'][2]=={cone:5}
    checks+=2
    db.add_item(42,cone,8)
    await druid.summons_v1700('przywolaj lifeoak')
    assert db.item_qty(42,cone)==8
    assert not conn.execute("SELECT 1 FROM summons_v1700 WHERE account_id=42 AND summon_type='lifeoak'").fetchone()
    checks+=2
    druid.current_mana=500
    await druid.summons_v1700('przywolaj lifeoak')
    assert db.item_qty(42,cone)==6 and druid.current_mana==420
    checks+=2
    await druid.summons_v1700('schowaj lifeoak')
    assert conn.execute("SELECT active FROM summons_v1700 WHERE account_id=42 AND summon_type='lifeoak'").fetchone()[0]==0
    checks+=1
    druid.current_mana=0
    await druid.summons_v1700('aktywuj lifeoak')
    assert db.item_qty(42,cone)==6 and conn.execute("SELECT active FROM summons_v1700 WHERE account_id=42 AND summon_type='lifeoak'").fetchone()[0]==0
    checks+=2
    druid.current_mana=500
    await druid.summons_v1700('aktywuj lifeoak')
    assert db.item_qty(42,cone)==4 and druid.current_mana==420
    assert conn.execute("SELECT active FROM summons_v1700 WHERE account_id=42 AND summon_type='lifeoak'").fetchone()[0]==1
    checks+=2
    # Material shortage never deducts mana.
    mana=druid.current_mana
    await druid.summons_v1700('przywolaj ancientoak')
    assert db.item_qty(42,cone)==4 and druid.current_mana==mana
    checks+=2
    await druid.druid_call_v1708('squirrel')
    assert db.item_qty(42,cone)>=6
    count=db.item_qty(42,cone)
    await druid.druid_call_v1708('squirrel')
    assert db.item_qty(42,cone)==count
    checks+=2
    druid.character.room_id='square'
    conn.execute('UPDATE druid_pinecones_v1702 SET last_gather=0 WHERE account_id=42')
    druid.current_mana=0
    await druid.druid_call_v1708('squirrel')
    assert db.item_qty(42,cone)==count
    druid.current_mana=500
    checks+=1
    db.add_item(42,'v1700_nature_seed',3)
    await druid.druid_v1700('wymien')
    assert db.item_qty(42,'v1700_nature_seed')==0
    assert db.item_qty(42,cone)==count+6
    checks+=2
    druid.character.room_id='whisper_grove'
    # v1.70.10: Ancient Oak unlocks at character level 400.
    druid.character.character_level=400
    await druid.summons_v1700('przywolaj ancientoak')
    assert db.item_qty(42,cone)==count+1 and druid.current_mana==320
    checks+=2
    # Register first real kill to each of two eligible party members, never twice.
    catalog=fame_catalog()
    assert catalog
    from systems.content_registry import MOB_SPAWNS
    from data.rooms import ROOMS
    from data.mobs import MOB_TEMPLATES
    zone,targets=next((z,b) for z,b in catalog.items() if len(b)>=2)
    room,tid=next((rid,tid) for rid,tid in MOB_SPAWNS if tid in targets and ROOMS.get(rid,{}).get('zone')==zone)
    mob=SimpleNamespace(room_id=room,template_id=tid)
    peers=[SimpleNamespace(account_id=42),SimpleNamespace(account_id=43)]
    assert len(record_fame_kill(conn,peers,mob,MOB_TEMPLATES[tid]))==2
    assert not record_fame_kill(conn,peers,mob,MOB_TEMPLATES[tid])
    assert conn.execute('SELECT COUNT(*) FROM fame_bosses_v1702').fetchone()[0]==2
    checks+=3
    report=' '.join(fame_report(conn,42))
    assert zone in report and '1/' in report
    assert fame_report(conn,42,'all')
    assert fame_report(conn,42,'none')
    assert fame_report(conn,42,'some')
    assert fame_report(conn,42,'most')
    checks+=5
    conn.close()
    return checks

def run_regression():
    return asyncio.run(_async_case())
