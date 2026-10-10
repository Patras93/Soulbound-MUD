# -*- coding: utf-8 -*-
"""Targeted 1.70 regression without weakening legacy audits."""
from __future__ import annotations
import asyncio
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace
from storage.database import _DeferredCommitConnection
from systems.sky_era_v1700 import SKY_REGIONS, install_sky_era_v1700
from player.session_mixins.era_sky_v1700 import (SessionSkyV1700Mixin, ensure_schema,
    SUMMONS, summon_upgrade_stones)


def check_world(rooms, mobs, quests, items):
    checks=0
    for slug,_,_,_,_ in SKY_REGIONS:
        for idx in range(18):
            key=f'v1700_{slug}_{idx}'
            assert key in rooms
            for d,target in rooms[key]['exits'].items():
                assert target in rooms,(key,d,target)
                assert key in rooms[target]['exits'].values(),(key,d,target)
                checks+=2
        throne=f'v1700_{slug}_throne'
        assert throne in rooms and f'v1700_{slug}_boss_2' in mobs
        for b in range(3):
            mid=f'v1700_{slug}_boss_{b}'
            assert mid in mobs and f'v1700_hunt_{slug}_{b}' in quests
            checks+=2
    assert rooms['v1600_road_2']['exits']['up']=='v1700_sky_harbor'
    assert rooms['v1700_sky_harbor']['exits']['down']=='v1600_road_2'
    checks+=2
    for idx in range(14):
        for phase in (1,2):
            assert f'v1700_prof_{idx}_{phase}' in quests
            checks+=1
    for idx in range(6):
        assert f'v1700_relic_{idx}' in items
        checks+=1
    assert len(SUMMONS)==8
    assert summon_upgrade_stones(1)==1 and summon_upgrade_stones(4)==2
    checks+=3
    return checks


async def test_sessions():
    messages=[]
    with tempfile.TemporaryDirectory() as tmp:
        class FakeDB:
            def __init__(self):
                self.conn=_DeferredCommitConnection(sqlite3.connect(str(Path(tmp)/'t.db')))
                self.conn.row_factory=sqlite3.Row
                self._v1700_ready=False
                self.inv={}
            def storage_qty(self,acct,where,item): return self.inv.get(item,0)
            def item_qty(self,acct,item): return 0
            def remove_storage_item(self,acct,where,item,qty,commit=True):
                if self.inv.get(item,0)<qty:return False
                self.inv[item]-=qty
                return True
            def remove_item(self,*args,**kwargs): return False
            def add_item(self,acct,item,qty=1,commit=True): self.inv[item]=self.inv.get(item,0)+qty
            def save_character(self,ch): return None
        db=FakeDB()
        ensure_schema(db.conn)
        class FakeSession(SessionSkyV1700Mixin):
            def __init__(self):
                self.account_id=77
                self.server=SimpleNamespace(db=db)
                self.character=SimpleNamespace(class_name='Nekromanta',room_id='room',silver=100000000)
                self.combat_mob_key=None
                self.current_mana=100000
            def active_class_names(self):return [self.character.class_name]
            async def send(self,txt):messages.append(txt)
            async def send_combat(self,txt,detail='essential'):messages.append(txt)
            def physical_power(self):return 18000
            def spell_power(self):return 26000
            async def apply_boss_defense(self,mob,damage):return damage
            def v0210_adjust_player_damage(self,damage):return damage
            async def mob_defeated(self,mob):mob.alive=False
            def max_hp(self):return 100000

        s=FakeSession()
        await s.summons_v1700('przywolaj wojownik')
        assert db.inv=={} and not db.conn.execute('SELECT * FROM summons_v1700').fetchone()
        db.inv['v1700_dragon_tooth']=3
        await s.summons_v1700('przywolaj wojownik')
        assert db.inv['v1700_dragon_tooth']==2
        await s.summons_v1700('przywolaj mag')
        assert db.inv['v1700_dragon_tooth']==0
        db.inv['v1700_soul_stone']=3
        await s.summons_v1700('ulepsz mag')
        assert db.conn.execute('SELECT level FROM summons_v1700 WHERE summon_type="mag"').fetchone()[0]==2
        assert db.inv['v1700_soul_stone']==2
        await s.summons_v1700('ulepsz pajak')
        assert db.inv['v1700_soul_stone']==2
        await s.summons_v1700('schowaj mag')
        assert db.conn.execute('SELECT active FROM summons_v1700 WHERE summon_type="mag"').fetchone()[0]==0
        await s.summons_v1700('aktywuj mag')
        assert db.conn.execute('SELECT active FROM summons_v1700 WHERE summon_type="mag"').fetchone()[0]==1
        mob=SimpleNamespace(hp=19,max_hp=100,alive=True,room_id='room',template_id='x')
        s.server.world=SimpleNamespace(mobs={'xkey':mob})
        s.combat_mob_key='xkey'
        # Monster template registry is intentionally not touched by unit doubles.
        await s._v1700_rip_soul()
        assert db.inv['v1700_soul_stone']==3 and mob.soul_extracted_v1700
        await s._v1700_rip_soul()
        assert db.inv['v1700_soul_stone']==3
        s.combat_mob_key=None
        await s.classes_v1700('ofensywa')
        assert s.class_damage_multiplier_v1700()>1.0
        await s.city_v1700('zaloz Przystan Cieni')
        assert db.conn.execute('SELECT count(*) FROM cities_v1700').fetchone()[0]==1
        before=s.character.silver
        await s.city_v1700('buduj targ')
        assert s.character.silver<before
        await s.city_v1700('zbierz')
        income=s.character.silver
        await s.city_v1700('zbierz')
        assert s.character.silver==income
        s.character.class_name='Druid'
        db.inv['v1702_pinecone']=8
        await s.summons_v1700('przywolaj lifeoak')
        assert db.inv['v1702_pinecone']==6
        assert db.conn.execute('SELECT COUNT(*) FROM summons_v1700').fetchone()[0]==3
        await s.summons_v1700('przywolaj ancientoak')
        assert db.inv['v1702_pinecone']==6 # 3 active; cannot consume
        async def fake_broadcast(*a,**kw): pass
        s.server.party_combat_broadcast=fake_broadcast
        s.character.class_name='Nekromanta'
        enemy=SimpleNamespace(hp=300000,max_hp=300000,alive=True,room_id='room',template_id='x')
        await s.summon_combat_turn_v1700(enemy)
        assert enemy.hp<300000
        assert any('Szkielet Wojownika' in text for text in messages)
        db.conn.close()
    return 28


def run_regression(rooms, mobs, quests, items):
    total=check_world(rooms,mobs,quests,items)
    total+=asyncio.run(test_sessions())
    return total
