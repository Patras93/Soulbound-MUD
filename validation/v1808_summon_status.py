# -*- coding: utf-8 -*-
"""Cobra venom and Mage elementals: real combat status, rate limits, owner scaling."""
from __future__ import annotations
import asyncio
import sqlite3
import sys
from types import SimpleNamespace, ModuleType
from unittest.mock import patch
from systems.summon_status_v1808 import (
    apply_summon_status_v1808, summon_effect_for_v1808,
    summon_status_enemy_turn_v1808, clear_summon_status_v1808,
)
from systems.mage_elementals_v1702 import ELEMENTALS
from player.session_mixins.era_sky_v1700 import SessionSkyV1700Mixin, ensure_schema


def _mob(hp=10000):
    return SimpleNamespace(alive=True, hp=hp, template_id='goblin', room_id='arena')


def _core_checks():
    checks = 0
    expected={'ogien':'burn', 'blyskawice':'shock', 'lod':'freeze', 'krysztal':'freeze'}
    for kind, info in ELEMENTALS.items():
        assert summon_effect_for_v1808(kind, info) == expected[info['element']]
        checks += 1
    assert len(ELEMENTALS) == 12 and summon_effect_for_v1808('zw_kobra') == 'poison'
    checks += 2
    for unknown in ('zw_fenek', 'wilk', 'wojownik'):
        assert summon_effect_for_v1808(unknown) == ''
        assert not apply_summon_status_v1808(_mob(), unknown, 500, now=100, roll=0)
        checks += 2
    for effect_key, element in (('poison', None),('burn','ogien'),('shock','blyskawice'),
                                ('freeze','lod'),('freeze','krysztal')):
        m=_mob()
        spec={'element':element,'rank':2} if element else None
        kind='zywiolak_'+element+'_potezny' if element else 'zw_kobra'
        msg=apply_summon_status_v1808(m, kind, 1000, {'max_hp':10000}, spec, now=100, roll=0)
        assert msg and effect_key in m.v1808_summon_statuses
        assert not apply_summon_status_v1808(m, kind, 1000, {'max_hp':10000}, spec, now=101, roll=0)
        checks += 2
        if effect_key in ('poison', 'burn'):
            before=m.hp
            lines,skip,killed=summon_status_enemy_turn_v1808(m, now=103)
            assert lines and m.hp<before and not skip and not killed
            assert 0 < before-m.hp <= 120  # bounded DOT, not another full attack
            assert summon_status_enemy_turn_v1808(m, now=103)[0] == ()
            checks+=3
        else:
            lines,skip,killed=summon_status_enemy_turn_v1808(m, now=101)
            assert lines and skip and not killed
            assert not summon_status_enemy_turn_v1808(m, now=102)[1]
            assert not apply_summon_status_v1808(m, kind, 500, {'max_hp':10000}, spec, now=111, roll=0)
            checks+=3
    m=_mob()
    ice={'element':'lod','rank':2}
    shock={'element':'blyskawice','rank':2}
    assert apply_summon_status_v1808(m,'zywiolak_lod_potezny',800,elemental=ice,now=100,roll=0)
    assert not apply_summon_status_v1808(m,'zywiolak_blyskawice_potezny',800,elemental=shock,now=101,roll=0)
    summon_status_enemy_turn_v1808(m,now=102)
    assert not apply_summon_status_v1808(m,'zywiolak_blyskawice_potezny',800,elemental=shock,now=108,roll=0)
    checks+=3
    # A fresh spawn cannot inherit ice, venom, or status immunity.
    clear_summon_status_v1808(m)
    assert not m.v1808_summon_statuses and not m.v1808_summon_cooldowns
    assert apply_summon_status_v1808(m,'zywiolak_blyskawice_potezny',800,elemental=shock,now=109,roll=0)
    checks+=2
    # A poison tick can kill, but awarding EXP/Fame must remain the normal
    # combat callback's responsibility rather than happen inside the helper.
    m=_mob(hp=2)
    assert apply_summon_status_v1808(m,'zw_kobra',500,{'max_hp':1000},now=100,roll=0)
    lines,skip,killed=summon_status_enemy_turn_v1808(m,now=103)
    assert killed and m.hp==0 and lines and skip
    checks+=2
    # Boss controls are harder to apply and resistant to refresh loops.
    m=_mob(hp=100000)
    assert not apply_summon_status_v1808(m,'zywiolak_lod_potezny',1000,{'world_boss':True},ice,now=100,roll=.20)
    assert apply_summon_status_v1808(m,'zywiolak_lod_potezny',1000,{'world_boss':True},ice,now=101,roll=0)
    assert not apply_summon_status_v1808(m,'zywiolak_lod_potezny',1000,{'world_boss':True},ice,now=110,roll=0)
    checks+=3
    return checks


async def _integration():
    # Exercise the REAL attack hook (not just the status helper) without touching
    # a production SQLite account, network socket, or persisted character.
    conn=sqlite3.connect(':memory:'); conn.row_factory=sqlite3.Row; ensure_schema(conn)
    msgs=[]
    class Fighter(SessionSkyV1700Mixin):
        def __init__(self):
            self.character=SimpleNamespace(name='Test',room_id='arena',character_level=102,class_name='Druid')
            self.account_id=991
            self.current_mana=10000; self.current_hp=1000; self.skill_guard=0
            self.server=SimpleNamespace(db=SimpleNamespace(conn=conn,_v1700_ready=True),party_combat_broadcast=self.party)
        def active_class_names(self):return (self.character.class_name,)
        def max_hp(self):return 1000
        def physical_power(self):return 500
        def spell_power(self):return 500
        async def apply_boss_defense(self,mob,amount):return amount
        def v0210_adjust_player_damage(self,amount):return amount
        async def send_combat(self,msg,**kw):msgs.append(str(msg))
        async def party(self,*args,**kwargs):return None
        async def mob_defeated(self,mob):raise AssertionError('mob should survive')
    f=Fighter()
    fake=ModuleType('world.machine_expansion')
    fake.v0314_adjust_damage_vs_template=lambda template,damage,kind,name:(damage,kind)
    try:
        for summon_type,cl_name,expected in (
            ('zw_kobra','Druid','poison'),
            ('zywiolak_ogien_mniejszy','Mag','burn'),
            ('zywiolak_blyskawice_mniejszy','Mag','shock'),
            ('zywiolak_lod_mniejszy','Mag','freeze'),
            ('zywiolak_krysztal_mniejszy','Mag','freeze'),
        ):
            f.character.class_name=cl_name
            conn.execute('DELETE FROM summons_v1700')
            conn.execute('INSERT INTO summons_v1700 (account_id,summon_type,level,active,soul_rank,hp,max_hp,xp,stance) VALUES (?,?,102,1,0,500,500,0,?)',
                         (991,summon_type,'atakuj'))
            conn.commit()
            m=_mob(hp=1000000)
            with patch.dict(sys.modules,{'world.machine_expansion':fake}), patch('systems.summon_status_v1808.random.random', return_value=0.0):
                await f.summon_combat_turn_v1700(m)
            assert expected in m.v1808_summon_statuses, (summon_type,msgs[-1:])
            assert msgs and 'poziom 102' in msgs[-1]
            assert m.hp<1000000
        return 15
    finally:
        conn.close()


def run_regression():
    return _core_checks() + asyncio.run(_integration())

if __name__ == '__main__':
    print('SUMMON STATUS v1.80.8:',run_regression(),'PASS')
