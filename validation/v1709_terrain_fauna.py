# -*- coding: utf-8 -*-
"""Regression: biome fauna, rarity, squirrel restriction, safe mana, SQL/pet orders."""
import asyncio
import sqlite3
from types import SimpleNamespace
from systems.druid_call_v1708 import ANIMALS, BIOMES, terrain_animals, biome_for_room, normalize_animal
from player.session_mixins.era_sky_v1700 import SessionSkyV1700Mixin, SUMMONS, SUMMON_MANA, ensure_schema


def static_check():
    n=0
    assert len(ANIMALS)==59, len(ANIMALS);n+=1
    assert len(BIOMES)==10;n+=1
    assert len(set(ANIMALS))==len(ANIMALS);n+=1
    for biome, pool in BIOMES.items():
        assert len(pool)>=4, (biome,len(pool));n+=1
        assert len(set(pool))==len(pool);n+=1
        assert set(pool)<=set(ANIMALS);n+=1
        for key in pool:
            spec=ANIMALS[key]
            assert spec['role'] in ('atak','obrona','wsparcie');n+=1
            assert 25<=spec['mana']<=290;n+=1
            assert spec['min_level'] in (0,100,300);n+=1
            assert spec['damage_kind'] in ('physical','magic');n+=1
            assert SUMMONS[key][1]=='Druid' and SUMMON_MANA[key]==spec['mana'];n+=1
            assert normalize_animal(spec['call'])==key;n+=1
        assert any(ANIMALS[k]['min_level']==100 for k in pool),biome;n+=1
        assert any(ANIMALS[k]['min_level']==300 for k in pool),biome;n+=1
        assert terrain_animals(biome,1)==terrain_animals(biome,99);n+=1
        assert all(k=='squirrel' or ANIMALS[k]['min_level']==0 for k in terrain_animals(biome,1));n+=1
        assert all(k=='squirrel' or ANIMALS[k]['min_level']<=100 for k in terrain_animals(biome,100));n+=1
        assert set(terrain_animals(biome,300))==set(pool)|({'squirrel'} if biome in ('las','łąka') else set());n+=1
        assert ('squirrel' in terrain_animals(biome))==(biome in ('las','łąka'));n+=1
    for id_, zone, expected in (
        ('whisper_grove','Gaj Szeptów','las'),
        ('meadow','Łąka Słoneczna','łąka'),
        ('square','Miasto Dusz','miasto'),
        ('mine_depth_20','Kopalnia Głębinowa','jaskinia'),
        ('v1700_sky_storm_1','Kraina Burz','niebo'),
        ('arid','Pustynia Burz','pustynia'),
        ('deepwater','Wielki Ocean','woda'),
        ('ice','Tundra','śnieg'),
        ('hill','Górskie Szczyty','góry'),
        ('marsh','Bagna','bagno'),
    ):
        assert biome_for_room({'zone':zone,'name':zone},id_)==expected,(id_,zone);n+=1
    return n


async def async_check():
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row;ensure_schema(conn)
    class DB:
        _v1700_ready=True
        def __init__(self):self.conn=conn;self.inv={}
        def item_qty(self,a,k):return self.inv.get((a,k),0)
        def storage_qty(self,a,k,item):return 0
        def add_item(self,a,k,qty=1,commit=True):
            self.inv[a,k]=self.item_qty(a,k)+qty
            if commit:self.conn.commit()
        def remove_item(self,a,k,qty=1,commit=True):
            if self.item_qty(a,k)<qty:return False
            self.inv[a,k]-=qty
            if commit:self.conn.commit()
            return True
        def remove_storage_item(self,*args,**kw):return False
    class D(SessionSkyV1700Mixin):
        def __init__(self):
            self.account_id=65;self.server=SimpleNamespace(db=DB())
            self.character=SimpleNamespace(room_id='whisper_grove',character_level=50)
            self.current_mana=3000;self.combat_mob_key=None;self.messages=[]
        def active_class_names(self):return ('Druid',)
        async def send(self,m):self.messages.append(str(m))
        def max_hp(self):return 10000
    d=D();n=0
    await d.druid_call_v1708('list')
    text='\n'.join(d.messages)
    assert 'Pradawny Duch Lasu' in text and '300' in text and 'squirrel' in text;n+=1
    d.current_mana=100
    await d.druid_call_v1708('gryf')
    assert d.current_mana==100 and 'nie przywołasz' in d.messages[-1];n+=1
    await d.druid_call_v1708('bialy jelen')
    assert d.current_mana==100 and '100' in d.messages[-1];n+=1
    await d.summons_v1700('przywolaj zw_bialy_jelen')
    assert d.current_mana==100 and '100' in d.messages[-1];n+=1
    d.character.room_id='square';d.current_mana=300
    await d.druid_call_v1708('squirrel')
    assert d.current_mana==300 and d.server.db.item_qty(65,'v1702_pinecone')==0;n+=1
    await d.druid_call_v1708('list')
    assert 'squirrel' not in '\n'.join(d.messages[-8:]);n+=1
    await d.summons_v1700('przywolaj zw_bialy_jelen')
    assert d.current_mana==300 and 'bieżącym terenie' in d.messages[-1];n+=1
    d.character.room_id='whisper_grove';d.character.character_level=400;d.current_mana=800
    await d.druid_call_v1708('duch lasu')
    a=conn.execute("SELECT active,level,hp,max_hp FROM summons_v1700 WHERE account_id=65 AND summon_type='zw_duch_lasu'").fetchone()
    assert a and a['active']==1 and a['hp']>0 and d.current_mana==550;n+=1
    await d.druid_order_v1708('duch lasu bron')
    assert conn.execute("SELECT stance FROM summons_v1700 WHERE account_id=65 AND summon_type='zw_duch_lasu'").fetchone()[0]=='bron';n+=1
    d._v1703_dismiss_summons_on_login()
    assert conn.execute("SELECT active,hp FROM summons_v1700 WHERE account_id=65 AND summon_type='zw_duch_lasu'").fetchone()[0]==0;n+=1
    await d.druid_call_v1708('duch lasu')
    assert d.current_mana==300 and conn.execute("SELECT active,hp FROM summons_v1700 WHERE account_id=65 AND summon_type='zw_duch_lasu'").fetchone()['hp']>0;n+=1
    await d.druid_call_v1708('squirrel')
    assert d.current_mana==280 and d.server.db.item_qty(65,'v1702_pinecone')==4;n+=1
    d.character.room_id='square'
    before=d.current_mana
    await d.druid_call_v1708('squirrel')
    assert d.current_mana==before;n+=1
    conn.close()
    return n


def run_regression():
    return static_check()+asyncio.run(async_check())

if __name__=='__main__':
    print(f'TERRAIN FAUNA v1.70.9: {run_regression()} checks PASS')
