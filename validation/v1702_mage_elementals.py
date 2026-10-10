# -*- coding: utf-8 -*-
"""Independent smoke/regression test for Mage summons, magic cost and defenses."""
from __future__ import annotations
import asyncio
import sqlite3
import sys
from types import SimpleNamespace, ModuleType
from unittest.mock import patch
from systems.mage_elementals_v1702 import ELEMENTALS, resolve_elemental
from player.session_mixins.era_sky_v1700 import SessionSkyV1700Mixin, SUMMONS, SUMMON_MANA, ensure_schema

async def run_async():
    checks=0
    assert len(ELEMENTALS)==12
    checks+=1
    for key,spec in ELEMENTALS.items():
        assert SUMMONS[key][1]=='Mag' and SUMMONS[key][2]=={}
        assert SUMMON_MANA[key]==spec['mana']
        checks+=3
    assert resolve_elemental(['ogien','mniejszy'])=='zywiolak_ogien_mniejszy'
    assert resolve_elemental(['lod','potezny'])=='zywiolak_lod_potezny'
    assert resolve_elemental(['blyskawice'])=='zywiolak_blyskawice_zwykly'
    assert resolve_elemental(['nieistniejacy']) is None
    checks+=4
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row;ensure_schema(conn)
    class DB:
        def __init__(self): self.conn=conn;self._v1700_ready=True
        def item_qty(self,*a):return 0
        def storage_qty(self,*a):return 0
    db=DB();msgs=[]
    class Mage(SessionSkyV1700Mixin):
        def __init__(self):
            self.character=SimpleNamespace(room_id='somewhere',class_name='Mag',name='Mag Testowy')
            self.account_id=42;self.combat_mob_key=None;self.current_mana=0
            self.current_hp=500;self.skill_guard=0
            self.server=SimpleNamespace(db=db,party_combat_broadcast=self.party)
        async def send(self,s):msgs.append(str(s))
        async def send_combat(self,s,**kw):msgs.append(str(s))
        async def party(self,*a,**kw):pass
        def active_class_names(self):return ('Mag',)
        def max_hp(self):return 1000
        def physical_power(self):return 10
        def spell_power(self):return 200
        async def apply_boss_defense(self,mob,amount):return amount
        def v0210_adjust_player_damage(self,amount):return amount
        async def mob_defeated(self,mob):raise AssertionError('mob not expected to die')
    mage=Mage()
    await mage.mage_elementals_v1702('przywolaj ogien mniejszy')
    assert not conn.execute('SELECT 1 FROM summons_v1700 WHERE account_id=42').fetchone() and mage.current_mana==0
    checks+=2
    mage.current_mana=500
    await mage.mage_elementals_v1702('przywolaj ogien mniejszy')
    assert conn.execute("SELECT active FROM summons_v1700 WHERE account_id=42 AND summon_type='zywiolak_ogien_mniejszy'").fetchone()[0]==1
    assert mage.current_mana==435
    checks+=2
    await mage.mage_elementals_v1702('schowaj ogien mniejszy')
    assert conn.execute("SELECT active FROM summons_v1700 WHERE account_id=42 AND summon_type='zywiolak_ogien_mniejszy'").fetchone()[0]==0
    checks+=1
    mage.current_mana=0
    await mage.mage_elementals_v1702('aktywuj ogien mniejszy')
    assert conn.execute("SELECT active FROM summons_v1700 WHERE account_id=42 AND summon_type='zywiolak_ogien_mniejszy'").fetchone()[0]==0
    checks+=1
    mage.current_mana=100
    await mage.mage_elementals_v1702('aktywuj ogien mniejszy')
    assert mage.current_mana==35 and conn.execute("SELECT active FROM summons_v1700 WHERE account_id=42 AND summon_type='zywiolak_ogien_mniejszy'").fetchone()[0]==1
    checks+=2
    mage.current_mana=650
    await mage.mage_elementals_v1702('przywolaj lod potezny')
    await mage.mage_elementals_v1702('przywolaj krysztal zwykly')
    assert mage.current_mana==650-185-160
    checks+=1
    before=mage.current_mana
    await mage.mage_elementals_v1702('przywolaj blyskawice potezny')
    assert conn.execute('SELECT COUNT(*) FROM summons_v1700 WHERE account_id=42 AND active=1').fetchone()[0]==3 and mage.current_mana==before
    checks+=2
    mage.skill_guard=0
    mob=SimpleNamespace(alive=True,room_id='somewhere',hp=100000,template_id='nonexistent')
    fake=ModuleType('world.machine_expansion')
    fake.v0314_adjust_damage_vs_template=lambda *a:(1,'magic')
    with patch.dict(sys.modules, {'world.machine_expansion':fake}):
        before=mage.current_mana
        await mage.summon_combat_turn_v1700(mob)
        assert mage.current_mana<before and mage.skill_guard>0 and mob.hp<100000
        checks+=3
        mage.current_mana=0;before=mob.hp
        await mage.summon_combat_turn_v1700(mob)
        assert mob.hp==before and mage.current_mana==0
        checks+=2
    # Necromancer's tooth-based summons remain restricted to Necromancer
    await mage.summons_v1700('przywolaj wojownik')
    assert conn.execute("SELECT 1 FROM summons_v1700 WHERE account_id=42 AND summon_type='wojownik'").fetchone() is None
    checks+=1
    conn.close()
    return checks

def run_regression():
    return asyncio.run(run_async())
