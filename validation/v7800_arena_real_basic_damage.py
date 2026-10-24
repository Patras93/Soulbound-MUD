# -*- coding: utf-8 -*-
"""v78 isolated real attack method in UOSS rehearsal; no player/world/DB effects."""
import asyncio
import copy
import random
from types import SimpleNamespace
from unittest.mock import patch

from validation.v3600_admin_guardian2 import Fake
from player.session_mixins.combat_damage import SessionCombatDamageMixin
from systems.admin_live_arena_damage_v7800 import _calculate,preview,strike

class CombatOwner(SessionCombatDamageMixin, Fake):
    def __init__(self, owner=True, db=None):
        super().__init__(owner,db)
        self.character=SimpleNamespace(
            name='Tester',room_id='temple',character_level=45,
            class_type='physical',soul_power=lambda:100,
            class_physical_damage_multiplier=lambda:1.2,
            racial_physical_damage_multiplier=lambda:1.0,
            racial_all_damage_multiplier=lambda:1.0,
        )
        self.current_mana=50
    def basic_attack_build_v11196(self):return (123,15,'physical')
    def total_set_damage_multiplier(self):return 1.05
    def equipment_damage_multiplier(self,channel):return 1.1
    def basic_attack_inherent_multiplier_v1124(self):return 1.0

async def main():
    tests=0
    def check(value,msg):
        nonlocal tests
        if not value:raise AssertionError(msg)
        tests+=1
    o=CombatOwner()
    async def cmd(raw,s=o):
        await s.admin_command('live '+raw)
        return s.messages[-1]
    check('POMOC 38' in await cmd('pomoc 38'),'help')
    outsider=CombatOwner(False,o.server.db)
    check('Nieznana komenda' in await cmd('arena uoss gracz prognoza',outsider),'permissions')
    check('ADMIN LIVE V78' in await cmd('arena uoss gracz prognoza'),'requires arena')
    check('ARENA11 START' in await cmd('arena start black_rabite 100000000 1000'),'arena start')
    before_state=copy.deepcopy(o.guardian7_lab)
    def snapshot(state):
        return (state['round'],state['hero_hp'],state['hero_attack'],state['boss'].hp,
                state['total_dealt'],state['total_taken'],tuple(state['notes']),
                state.get('_v7800_mana'),state.get('_v7800_rng'))
    before_snapshot=snapshot(o.guardian7_lab)
    before_rng=random.getstate();before_mana=o.current_mana
    before_db=o.server.db.conn.total_changes
    o._read_only_equipment_cache_v1262={'nested': {'untouched': True}}
    expected_cache=copy.deepcopy(o._read_only_equipment_cache_v1262)
    # Production damage formula receives the same deterministic random rolls.
    with patch('player.session_mixins.combat_damage.party_synergy_damage_multiplier_v11338',return_value=1.0):
        hits,mana,_rng=_calculate(o,o.guardian7_lab,2)
        check(len(hits)==2 and all(v>100 for v in hits),'real basic attack hits')
        txt=await cmd('arena uoss gracz prognoza 2')
        check(str(hits[0]) in txt and str(hits[1]) in txt,'matching real formula in preview')
        check('surowe' in txt and 'nie zostaly odtworzone 1:1' in txt,'explicit limitations')
        check(snapshot(o.guardian7_lab)==before_snapshot,'preview no arena mutation')
        check(o.current_mana==before_mana and random.getstate()==before_rng,'mana and RNG rollback')
        check(o._read_only_equipment_cache_v1262==expected_cache,'equipment cache stays detached')
        for raw in ['arena uoss gracz prognoza 0','arena uoss gracz prognoza 9',
                    'arena uoss gracz prognoza -1','arena uoss gracz prognoza 2 3',
                    'arena uoss gracz atak','arena uoss gracz atak NIE']:
            check('ADMIN LIVE V78' in await cmd(raw),'invalid '+raw)
        check('ARENA UOSS GRACZ ATAK' in await cmd('arena uoss gracz atak POTWIERDZAM'),'lab strike')
        current=o.guardian7_lab
        check(current['round']==1,'exactly one lab round')
        check(current['total_dealt']==hits[0],f'uses real raw damage {current["total_dealt"]} vs {hits[0]}')
        check(current['hero_attack']==before_state['hero_attack'],'original lab attack stays')
        check(current['_v7800_mana']==50,'lab mana')
        check('mana kopii 50' in await cmd('arena uoss gracz stan'),'lab state status')
        check(o.current_mana==before_mana and random.getstate()==before_rng,'strike no live character/RNG')
        check(o.server.db.conn.total_changes==before_db,'no SQLite writes')
        # Reproducibility against same inputs and private state.
        start_snapshot=snapshot(current)
        hits2,_,_=_calculate(o,current,1)
        await cmd('arena uoss gracz prognoza')
        check(snapshot(o.guardian7_lab)==start_snapshot and str(hits2[0]) in o.messages[-1],'next strike preview deterministic')
        # A fault in the LAB turn must restore only LAB state, including its source RNG.
        from unittest.mock import patch as mock_patch
        before_error=snapshot(o.guardian7_lab)
        with mock_patch('systems.admin_live_arena_damage_v7800._lab_turn10',side_effect=ValueError('forced failure')):
            check('ADMIN LIVE V78' in await cmd('arena uoss gracz atak POTWIERDZAM'),'safe error dispatch')
        check(snapshot(o.guardian7_lab)==before_error,'rollback lab after failed turn')
        check(o.current_mana==before_mana and random.getstate()==before_rng,'rollback live state after error')
        await cmd('arena wyjdz')
        check('ADMIN LIVE V78' in await cmd('arena uoss gracz atak POTWIERDZAM'),'state removed')
    magic=CombatOwner()
    magic.character.class_type='magic'
    magic.character.class_magic_damage_multiplier=lambda:1.4
    magic.character.racial_magic_damage_multiplier=lambda:1.0
    magic.current_mana=10
    magic_rng=random.getstate()
    await cmd('arena start black_rabite 100000000 1000',magic)
    with patch('player.session_mixins.combat_damage.party_synergy_damage_multiplier_v11338',return_value=1.0):
        magic_snapshot=snapshot(magic.guardian7_lab)
        m_hits,end_mana,_=_calculate(magic,magic.guardian7_lab,3)
        check(len(m_hits)==3 and m_hits[0]>=1,'real magic method used')
        # The first two attacks consume MP; third is low-MP Soul Weapon focus.
        check(end_mana==12, f'magic cloned resource costs + regen {end_mana}')
        check('mana kopii po 3 ciosach 12' in await cmd('arena uoss gracz prognoza 3',magic),'magic preview')
        check(magic.current_mana==10 and snapshot(magic.guardian7_lab)==magic_snapshot,'magic no real mana/arena mutation')
        check(random.getstate()==magic_rng,'magic global RNG restored')
        check('ARENA UOSS GRACZ ATAK' in await cmd('arena uoss gracz atak POTWIERDZAM',magic),'magic strike')
        check(magic.guardian7_lab['_v7800_mana']==6 and magic.current_mana==10,'magic lab MP costs only')
    return tests

if __name__=='__main__':
    print('V78.00.0 REAL SOURCE BASIC ATTACK:',asyncio.run(main()),'PASS')
