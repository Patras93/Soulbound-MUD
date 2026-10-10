# -*- coding: utf-8 -*-
"""Druid call animal and squirrel: durable, paid, terrain-aware and controllable."""
import asyncio
import sqlite3
from types import SimpleNamespace
from systems.druid_call_v1708 import biome_for_room,terrain_animals,normalize_animal,ANIMALS
from player.session_mixins.era_sky_v1700 import SessionSkyV1700Mixin,ensure_schema,SUMMONS

def _sync_check():
    checks=0
    for room_id, room, expected in (
        ('whisper_grove',{'zone':'Gaj Szeptów','name':'Stary Las'},'las'),
        ('some_port',{'zone':'Wielki Ocean','name':'Przystań'},'woda'),
        ('cavern_floor_10',{'zone':'Mityczna Krypta','name':'Komnata'},'jaskinia'),
        ('square',{'zone':'Miasto Dusz','name':'Plac Dusz'},'miasto'),
        ('volcano',{'zone':'Góry','name':'Szczyt'},'góry'),
    ):
        assert biome_for_room(room,room_id)==expected
        assert ('squirrel' in terrain_animals(expected)) == (expected in ('las','łąka'))
        checks+=2
    assert normalize_animal('wiewiórka')=='squirrel';checks+=1
    assert 'v1700_bond_token' not in repr({k:v[2] for k,v in SUMMONS.items() if k in ANIMALS});checks+=1
    return checks

async def _async_check():
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row;ensure_schema(conn)
    class DB:
        _v1700_ready=True
        def __init__(self):self.conn=conn;self.inv={}
        def item_qty(self,aid,key):return self.inv.get((aid,key),0)
        def storage_qty(self,aid,box,key):return 0
        def add_item(self,aid,key,qty=1,commit=True):
            self.inv[aid,key]=self.item_qty(aid,key)+qty
            if commit:self.conn.commit()
        def remove_item(self,aid,key,qty=1,commit=True):
            if self.item_qty(aid,key)<qty:return False
            self.inv[aid,key]-=qty
            if commit:self.conn.commit()
            return True
        def remove_storage_item(self,*a,**k):return False
    class D(SessionSkyV1700Mixin):
        def __init__(self):
            self.account_id=1;self.server=SimpleNamespace(db=DB())
            self.character=SimpleNamespace(room_id='whisper_grove',character_level=250)
            self.current_mana=500;self.combat_mob_key=None;self.messages=[]
        def active_class_names(self):return ('Druid',)
        async def send(self,msg):self.messages.append(str(msg))
        def max_hp(self):return 2000
    d=D();checks=0
    await d.druid_call_v1708('list')
    assert 'wilk' in ' '.join(d.messages).lower() and 'squirrel' in ' '.join(d.messages).lower();checks+=1
    d.current_mana=0
    await d.druid_call_v1708('squirrel')
    assert d.server.db.item_qty(1,'v1702_pinecone')==0;checks+=1
    d.current_mana=500
    await d.druid_call_v1708('squirrel')
    assert d.server.db.item_qty(1,'v1702_pinecone')==3 and d.current_mana==480;checks+=1
    assert not conn.execute('SELECT 1 FROM summons_v1700 WHERE summon_type=?',('squirrel',)).fetchone();checks+=1
    await d.druid_call_v1708('squirrel')
    assert d.server.db.item_qty(1,'v1702_pinecone')==3 and d.current_mana==480;checks+=1
    await d.druid_call_v1708('wilk')
    wolf=conn.execute('SELECT active,stance,hp FROM summons_v1700 WHERE account_id=1 AND summon_type=?',('wilk',)).fetchone()
    assert wolf and wolf['active']==1 and wolf['hp']>0 and d.current_mana==430;checks+=1
    await d.druid_order_v1708('wilk bron')
    assert conn.execute('SELECT stance FROM summons_v1700 WHERE account_id=1 AND summon_type=?',('wilk',)).fetchone()['stance']=='bron';checks+=1
    await d.druid_order_v1708('all wspieraj')
    assert conn.execute('SELECT stance FROM summons_v1700 WHERE account_id=1 AND summon_type=?',('wilk',)).fetchone()['stance']=='wspieraj';checks+=1
    mana=d.current_mana
    await d.druid_call_v1708('delfin')
    assert d.current_mana==mana and 'Tego zwierzęcia' in d.messages[-1];checks+=1
    d.character.room_id='square'
    await d.druid_call_v1708('list')
    assert 'Kot' in ' '.join(d.messages[-8:]);checks+=1
    await d.druid_call_v1708('kot')
    assert conn.execute("SELECT active FROM summons_v1700 WHERE summon_type='zw_kot'").fetchone()['active']==1;checks+=1
    before=d.current_mana
    d.combat_mob_key='mob'
    await d.druid_call_v1708('golab')
    assert d.current_mana==before and not conn.execute("SELECT 1 FROM summons_v1700 WHERE summon_type='zw_golab'").fetchone();checks+=1
    d.combat_mob_key=None
    old=conn.execute("SELECT level,hp,max_hp FROM summons_v1700 WHERE summon_type='wilk'").fetchone()
    assert d._v1703_dismiss_summons_on_login()>=1;checks+=1
    now=conn.execute("SELECT active,level,hp,max_hp FROM summons_v1700 WHERE summon_type='wilk'").fetchone()
    assert now['active']==0 and now['level']==old['level'] and now['hp']==0;checks+=1
    d.character.room_id='whisper_grove'
    await d.summons_v1700('aktywuj wilk')
    assert conn.execute("SELECT active,hp FROM summons_v1700 WHERE summon_type='wilk'").fetchone()['active']==1;checks+=1
    conn.close();return checks

def run_regression():
    return _sync_check()+asyncio.run(_async_check())
if __name__=='__main__':print('DRUID CALL v1.70.8:',run_regression(),'PASS')
