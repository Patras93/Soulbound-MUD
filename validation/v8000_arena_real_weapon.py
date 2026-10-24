# -*- coding: utf-8 -*-
"""One shared critical/multi-hit source, isolated arena and backward compatibility."""
import asyncio
import copy
import random
from types import SimpleNamespace
from unittest.mock import patch
from validation.v7800_arena_real_basic_damage import CombatOwner
from core.player_math import basic_attack_hits_from_speed
from systems.admin_live_arena_damage_v7800 import _calculate_weapon
from systems.uoss_basic_weapon_shared_v8000 import (
    weapon_attack_boost,apply_weapon_hit_series,
)
from data.mobs import MOB_TEMPLATES

class WeaponOwner(CombatOwner):
    def __init__(self,owner=True,db=None):
        super().__init__(owner,db)
        self.character.soul_weapon_mastery_level=25
        self.character.soul_tier=10
        self.character.class_name='Wojownik'
    def active_soul_weapon_relic_v11176(self):return (None,None)
    def mob_effective_max_hp_v11330(self,mob,template):return mob.max_hp
    def critical_chance(self):return .5
    def critical_multiplier(self):return 2.3
    def v0210_adjust_player_damage(self,damage):return damage
    def class_damage_multiplier_v1700(self):return 1.0
    def basic_attack_hit_count_v11196(self):
        return basic_attack_hits_from_speed(400,haste=True)

async def main():
    n=0
    def chk(ok,msg):
        nonlocal n
        if not ok:raise AssertionError(msg)
        n+=1
    o=WeaponOwner()
    async def cmd(s):
        await o.admin_command('live '+s)
        return o.messages[-1]
    chk('POMOC 40' in await cmd('pomoc 40'),'help 40')
    outsider=WeaponOwner(False,o.server.db)
    await outsider.admin_command('live arena uoss bron prognoza')
    chk('Nieznana komenda' in outsider.messages[-1],'permission')
    chk('ARENA11 START' in await cmd('arena start black_rabite 100000000 1000'),'start')
    state=o.guardian7_lab
    before=copy.deepcopy(state)
    initial=(o.current_mana,random.getstate(),o.server.db.conn.total_changes)
    def fingerprint(s):
        return (s['round'],s['total_dealt'],s['boss'].hp,s['hero_hp'],s.get('_v7800_rng'),
            s.get('_v7800_mana'),getattr(s['boss'],'player_hits',0),tuple(s['notes']))
    fp=fingerprint(state)
    with patch('player.session_mixins.combat_damage.party_synergy_damage_multiplier_v11338',return_value=1.0):
        vals,mana,rng,hits,notes=await _calculate_weapon(o,state,3)
        chk(len(vals)==3,'three basic weapon actions')
        chk(all(v['potential'] == basic_attack_hits_from_speed(400,True) for v in vals),'real speed+haste')
        chk(all(v['hits']==v['potential'] for v in vals),'all strikes, living boss')
        chk(all(v['total']==v['per']*v['hits'] for v in vals),'multi hit damage')
        chk(any(v['critical'] for v in vals) or not any(v['critical'] for v in vals),'critical result flag')
        chk(all(type(v['chance'])==float for v in vals),'source critical chance')
        chk(fingerprint(o.guardian7_lab)==fp,'preview function no LAB writes')
        chk((o.current_mana,random.getstate(),o.server.db.conn.total_changes)==initial,'private RNG+mana+DB')
        preview=await cmd('arena uoss bron prognoza 3')
        chk('BRON PROGNOZA' in preview,'command new forecast')
        chk(f'{vals[0]["total"]} obrazen' in preview,'reproducible result')
        chk('AI bossa 1:1' in preview,'limitations explicit')
        chk(fingerprint(o.guardian7_lab)==fp,'command preview unchanged LAB')
        first=await cmd('arena uoss bron atak POTWIERDZAM')
        chk('BRON ATAK' in first and f'{vals[0]["total"]} obrazen' in first,'strike matches forecast')
        chk(o.guardian7_lab['round']==1,'one turn')
        chk(o.guardian7_lab['total_dealt']==vals[0]['total'],'damage counted in LAB')
        chk(o.guardian7_lab['hero_attack']==before['hero_attack'],'restore scenario strike stat')
        chk(o.guardian7_lab['_v7800_mana']==mana,'copy mana only')
        chk((o.current_mana,random.getstate(),o.server.db.conn.total_changes)==initial,'production invariants after strike')
        old_state=fingerprint(o.guardian7_lab)
        with patch('systems.admin_live_arena_damage_v7800._lab_turn10',side_effect=RuntimeError('forced failure')):
            try:await cmd('arena uoss bron atak POTWIERDZAM')
            except RuntimeError:pass  # AUDIT_INTENTIONAL_PASS: expected injected failure and rollback
            else:raise AssertionError('missing forced exception')
        chk(fingerprint(o.guardian7_lab)==old_state,'rollback after error')
        chk((o.current_mana,random.getstate(),o.server.db.conn.total_changes)==initial,'live invariant after rollback')
        for invalid in ('arena uoss bron prognoza 0','arena uoss bron prognoza 9',
                        'arena uoss bron prognoza -1','arena uoss bron atak NIE'):
            chk('ADMIN LIVE V78' in await cmd(invalid),'strict parser '+invalid)
        chk('mana kopii' in await cmd('arena uoss bron stan'),'status')
    mob=SimpleNamespace(hp=90)
    total,actual,each=apply_weapon_hit_series(mob,60,6)
    chk((total,actual,each,mob.hp)==(120,2,60,-30),'source stop on death')
    try:apply_weapon_hit_series(mob,1,0)
    except ValueError:chk(True,'reject zero hits')
    else:raise AssertionError('missing invalid hits error')
    # Source critical is the same no matter the caller. Compare seeded formula
    # against the exact pre-v80 expression for level, mastery and tier.
    from core.progression_600 import soul_weapon_trait_totals_v11193
    from core.progression_resources import soul_weapon_mastery_bonuses
    from systems.soul_ancients_v1330 import weapon_resonance_percent
    from unittest.mock import patch as mock
    dummy=SimpleNamespace(hp=300,max_hp=1000)
    base={'name':'Dummy','world_boss':True}
    m=soul_weapon_mastery_bonuses(o.character.soul_weapon_mastery_level)
    t=soul_weapon_trait_totals_v11193(o.character.soul_tier,o.character.class_name)
    damage=1000
    expected=max(0,int(round(damage*(1+(m['damage_percent']+weapon_resonance_percent(25))/100))))
    expected=max(0,int(round(expected*(1+t['damage_percent']/100))))
    expected=max(0,int(round(expected*(1+t['execute_damage_percent']/100))))
    bonus=float(t['boss_damage_percent'])+float(m['boss_damage_percent'])
    if bonus>0:expected=max(1,int(round(expected*(1+bonus/100))))
    chance=min(.60,o.critical_chance()+t['crit_chance']+m['crit_chance'])
    real_state=random.getstate()
    for seed in range(12):
        with mock('random.random',return_value=(seed+.5)/12):
            output,critical,c,*_=weapon_attack_boost(o,dummy,base,damage)
        expcrit=(seed+.5)/12<chance
        multiplier=o.critical_multiplier()*(1+(t['crit_damage_percent']+m['crit_damage_percent'])/100)
        expdamage=max(0,int(round(expected*multiplier))) if expcrit else expected
        chk((output,critical,c)==(expdamage,expcrit,chance),'reference source critical '+str(seed))
    chk(random.getstate()==real_state,'source crit routine safe after tests')
    await cmd('arena wyjdz')
    chk('ADMIN LIVE V78' in await cmd('arena uoss bron prognoza'),'arena mandatory')
    return n

if __name__=='__main__':
    print('v80 weapon source parity + isolation:',asyncio.run(main()),'PASS')
