# -*- coding: utf-8 -*-
"""v81: source post-hit parity, private HP/MP, preview and rollback safety."""
import asyncio
import copy
import random
from types import SimpleNamespace
from unittest.mock import patch
from systems.uoss_basic_weapon_shared_v8000 import weapon_after_hit
from systems.admin_live_arena_damage_v7800 import _calculate_weapon
from validation.v8000_arena_real_weapon import WeaponOwner

class Dummy:
    def __init__(self,hp=20,mp=10):
        self.current_hp=hp
        self.current_mana=mp
        self._recap52_dealt=0
        self._recap52_heal=0
        self.uoss_nullify_healing_rounds_v11179=0
        self.equipment={'lifesteal_percent':15,'mana_restore_percent':20}
    def equipment_property_totals(self):return dict(self.equipment)
    def max_hp(self):return 100
    def max_mana(self):return 80

class ArenaOwner(WeaponOwner):
    def __init__(self,owner=True,db=None):
        super().__init__(owner,db)
        self.current_hp=20
        self.current_mana=10
        self.character.soul_weapon_mastery_level=800
        self.character.soul_tier=100
        self._read_only_equipment_cache_v1262={'properties':{'lifesteal_percent':8.0,'mana_restore_percent':6.0}}
    def equipment_property_totals(self):
        return dict(self._read_only_equipment_cache_v1262['properties'])
    def max_hp(self):return 10000
    def max_mana(self):return 10000

async def main():
    count=0
    def check(value,label):
        nonlocal count
        if not value:raise AssertionError(label)
        count+=1
    actor=Dummy(); boss=SimpleNamespace(hp=1000)
    traits={'lifesteal_percent':5,'mana_restore_percent':4}
    mastery={'echo_chance':1.0,'echo_damage_percent':30}
    before=random.getstate()
    with patch('systems.uoss_basic_weapon_shared_v8000.random.random',return_value=0.0):
        result=weapon_after_hit(actor,boss,100,traits,mastery)
    check(result==(30,13,10),f'echo heal MP source exact {result}')
    check(boss.hp==970 and actor._recap52_dealt==30,'echo applied to detached boss')
    check(actor.current_hp==33 and actor._recap52_heal==13,'HP and healing recap')
    check(actor.current_mana==20,'mana source formula + item cap')
    check(random.getstate()==before,'explicit echo RNG isolation')
    actor=Dummy(hp=99,mp=79);boss=SimpleNamespace(hp=200)
    with patch('systems.uoss_basic_weapon_shared_v8000.random.random',return_value=0.0):
        check(weapon_after_hit(actor,boss,100,traits,mastery)==(30,1,1),'HP MP upper bounds')
    check(actor.current_hp==100 and actor.current_mana==80,'never above maximum')
    actor=Dummy();actor.uoss_nullify_healing_rounds_v11179=2;boss=SimpleNamespace(hp=100)
    with patch('systems.uoss_basic_weapon_shared_v8000.random.random',return_value=0.0):
        check(weapon_after_hit(actor,boss,100,traits,mastery)==(30,0,10),'nullify HP only')
    check(actor.current_hp==20 and actor.current_mana==20,'healing blocked; MP still restored')
    actor=Dummy();boss=SimpleNamespace(hp=0)
    check(weapon_after_hit(actor,boss,100,traits,mastery)==(0,13,10),'no echo on dead boss')
    check(boss.hp==0,'no postmortem damage')
    actor=Dummy();boss=SimpleNamespace(hp=100)
    check(weapon_after_hit(actor,boss,100,traits,mastery,disabled=True)==(0,13,10),'Zantetsuken echo disabled')
    check(boss.hp==100,'no echo with disabled weapon')
    actor=Dummy();boss=SimpleNamespace(hp=1000)
    actor.equipment={'lifesteal_percent':0,'mana_restore_percent':0}
    check(weapon_after_hit(actor,boss,0,{'lifesteal_percent':0,'mana_restore_percent':0},{'echo_chance':0,'echo_damage_percent':0})==(0,0,0),'no effects configured')

    owner=ArenaOwner()
    async def cmd(text):
        await owner.admin_command('live '+text)
        return owner.messages[-1]
    check('POMOC 41' in await cmd('pomoc 41'),'help 41')
    check('POMOC 40' in await cmd('pomoc 40'),'help 40 compatibility')
    check('ARENA11 START' in await cmd('arena start black_rabite 100000000 1000'),'lab start')
    state=owner.guardian7_lab
    db_change=owner.server.db.conn.total_changes
    global_rng=random.getstate()
    source_hp=owner.current_hp
    source_mp=owner.current_mana
    fingerprint=lambda s:(s['round'],s['total_dealt'],s['boss'].hp,s.get('_v8100_hp'),s.get('_v7800_mana'),tuple(s['notes']))
    before_lab=fingerprint(state)
    with patch('player.session_mixins.combat_damage.party_synergy_damage_multiplier_v11338',return_value=1.0):
        values,mana,_,_,_=await _calculate_weapon(owner,state,3)
        check(len(values)==3,'three source-computed weapons')
        check(all(v['total']==v['weapon_total']+v['echo'] for v in values),'echo included exactly once')
        check(all(v['copy_hp']>=20 for v in values),'healing only clone')
        check(all(v['copy_mana']>=0 for v in values),'restoration only clone')
        check(values[0]['heal']>0,'positive lifesteal integration')
        check(values[0]['mana_restore']>0,'positive MP restoration integration')
        check(values[0]['copy_hp']>=20+values[0]['heal'],'HP updated in preview clone')
        check(fingerprint(state)==before_lab,'pure preview calculator LAB')
        preview=await cmd('arena uoss bron prognoza 3')
        check('Echo' in preview and 'HP kopii' in preview,'NVDA preview details')
        check(f'{values[0]["total"]} obrazen' in preview,'repeatable preview parity')
        check(fingerprint(owner.guardian7_lab)==before_lab,'preview does not commit')
        check(owner.current_hp==source_hp and owner.current_mana==source_mp,'live HP MP untouched')
        check(random.getstate()==global_rng and owner.server.db.conn.total_changes==db_change,'no global RNG or SQLite changes')
        strike=await cmd('arena uoss bron atak POTWIERDZAM')
        check('Echo' in strike and 'odzysk MP' in strike,'NVDA strike details')
        check(owner.guardian7_lab['total_dealt']==values[0]['total'],'model receives echo+weapon once')
        check(owner.guardian7_lab['_v8100_hp']==values[0]['copy_hp'],'private HP persisted')
        check(owner.guardian7_lab['_v7800_mana']==values[0]['copy_mana'],'private MP persisted')
        check('HP kopii' in await cmd('arena uoss bron stan'),'private status')
        check(owner.current_hp==source_hp and owner.current_mana==source_mp,'strike real resources untouched')
        check(random.getstate()==global_rng and owner.server.db.conn.total_changes==db_change,'strike world invariant')
        committed=fingerprint(owner.guardian7_lab)
        with patch('systems.admin_live_arena_damage_v7800._lab_turn10',side_effect=RuntimeError('induced')):
            try:await cmd('arena uoss bron atak POTWIERDZAM')
            except RuntimeError:pass  # AUDIT_INTENTIONAL_PASS: induced rollback exception
            else:raise AssertionError('missing injected failure')
        check(fingerprint(owner.guardian7_lab)==committed,'full private resource rollback')
        check(owner.current_hp==source_hp and owner.current_mana==source_mp,'exception real resources untouched')
        check(random.getstate()==global_rng and owner.server.db.conn.total_changes==db_change,'exception world untouched')
        await cmd('arena wyjdz')
        check('ADMIN LIVE V78' in await cmd('arena uoss bron stan'),'arena must exist')
    outsider=ArenaOwner(False,owner.server.db)
    await outsider.admin_command('live arena uoss bron prognoza')
    check('Nieznana komenda' in outsider.messages[-1],'admin-only preview')
    return count

if __name__=='__main__':
    print('V81 SOURCE POST-HIT EFFECTS AND ISOLATION:',asyncio.run(main()),'PASS')
