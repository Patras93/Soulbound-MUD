# -*- coding: utf-8 -*-
"""v83: ordinary direct skill cast is real source formula on detached copies.

Covers queue rotation, insufficient MP, unsupported skills, rollback, critical
parity, SQLite/global RNG protection and unchanged live account state.
"""
import asyncio
import copy
import random
from unittest.mock import patch
from validation.v8200_uoss_queue_source_choice import Owner
from systems.admin_live_plain_skill_v8300 import _calculate, _ordinary
from systems.uoss_plain_skill_shared_v8300 import plain_skill_damage_roll
from systems.admin_live_queue_v8200 import _ReadOnlyQueueDB

class SkillOwner(Owner):
    def __init__(self,owner=True,db=None):
        super().__init__(owner,db)
        self.character.soul_level=10
        self.character.class_name='Wojownik'
        self.character.character_level=50
        self.queue_rows={'physical':[{'skill_id':'s_low'}], 'magic':[], 'feedback':[]}
        self.queue_skills={'s_low':{'id':'s_low','name':'Potężne Cięcie','kind':'damage','unlock':1,
                                    'mana':8,'scale':'strength','mult':1.4}}
        self.queue_skills['s_aoe']={'id':'s_aoe','name':'Wir','kind':'aoe_damage','unlock':1,'mana':5}
        self.queue_skills['s_fire']={'id':'s_fire','name':'Ogień','kind':'damage','unlock':1,
                                     'mana':5,'element':'fire'}
        self.server.db.skill_progress=lambda account,sid: {'level':20}
        self.current_mana=50
    def class_mastery_level(self,name):return 40
    def combat_skill_mana_cost_v11191(self,skill,cl):return int(skill.get('mana',0))
    def equipment_mp_cost_multiplier_v11176(self):return 1.0
    def offensive_skill_damage_type_v11190(self,skill):return 'physical'
    def offensive_skill_damage_multiplier_v11186(self,skill,typ):return float(skill.get('mult',1.0))
    def offensive_skill_core_power_v11185(self,skill):return 900
    def roll_critical_hit(self,damage):return (damage,False)

async def main():
    passes=0
    def check(ok,detail):
        nonlocal passes
        if not ok:raise AssertionError(detail)
        passes+=1
    actor=SkillOwner()
    async def cmd(text):
        await actor.admin_command('live '+text)
        return actor.messages[-1]
    check('POMOC 43' in await cmd('pomoc 43'),'help registered')
    check('ARENA11 START' in await cmd('arena start black_rabite 100000000 1000'),'arena start')
    state=actor.guardian7_lab
    original=copy.deepcopy(state)
    real=(actor.current_hp,actor.current_mana,copy.deepcopy(actor.skill_queue_cursors),
          actor.server.db.conn.total_changes,random.getstate())
    fingerprint=lambda d:(d['round'],d['boss'].hp,d['total_dealt'],d.get('_v7800_mana'),
                          d.get('_v8300_queue_cursors'),d.get('_v8300_queue_next_type'),
                          d.get('_v7800_rng'),tuple(d['notes']))
    start=fingerprint(state)
    from core.progression_resources import skill_power_multiplier
    from systems.soul_ancients_v1330 import evolution_power_multiplier
    from systems.soul_evolutions_v1332 import role_evolution
    skill=actor.queue_skills['s_low']
    power=skill_power_multiplier(20)*evolution_power_multiplier(20,10)*role_evolution(skill,20,10,'offense')
    baseline=random.getstate()
    for seed in range(12):
        random.seed(seed)
        old=max(1,int(900*skill['mult']*power)+random.randint(-2,3))
        random.seed(seed)
        computed,crit=plain_skill_damage_roll(actor,900,skill['mult']*power)
        check(computed==old and not crit,'production primitive parity '+str(seed))
    random.seed(1)
    negative_expected=max(1,int(900*-0.5)+random.randint(-2,3))
    random.seed(1)
    check(plain_skill_damage_roll(actor,900,-0.5)[0]==negative_expected,
          'legacy negative multiplier also preserves source result')
    for bad in ({'kind':'damage','mec_authored':True},
                {'kind':'damage','future_world_effect':1},
                {'kind':'damage','mechanic_cooldown':True}):
        try:_ordinary(dict(skill,**bad),actor)
        except ValueError:check(True,'unsupported effects fail closed')
        else:raise AssertionError('Unsafe metadata accepted')
    random.setstate(baseline)
    with patch('player.session_mixins.combat_damage.party_synergy_damage_multiplier_v11338',return_value=1.0):
        preview=await cmd('arena uoss kolejka prosty prognoza')
        check('Potężne Cięcie' in preview and 'mana koszt 8' in preview,'preview source direct damage')
        check(fingerprint(actor.guardian7_lab)==start,'preview never commits private state')
        check((actor.current_hp,actor.current_mana,copy.deepcopy(actor.skill_queue_cursors),
               actor.server.db.conn.total_changes,random.getstate())==real,'preview real DB RNG player untouched')
        expected=await _calculate(actor,actor.guardian7_lab)
        check(expected['damage']>0 and expected['cost']==8,'source execution')
        check('ADMIN LIVE V78' in await cmd('arena uoss kolejka prosty rzuc NIE'),'commit token required')
        cast=await cmd('arena uoss kolejka prosty rzuc POTWIERDZAM')
        check('PROSTY RZUC' in cast and f'{expected["damage"]} obrazen' in cast,'cast matches preview')
        check(actor.guardian7_lab['total_dealt']==expected['damage'],'actual private boss damage once')
        check(actor.guardian7_lab['_v7800_mana']==42,'source mana cost committed to LAB')
        check(actor.guardian7_lab['_v8300_queue_cursors']['physical']==0,'private queue cursor rotated')
        check(actor.guardian7_lab['_v8300_queue_next_type']=='magic','private queue channel rotated')
        check((actor.current_hp,actor.current_mana,copy.deepcopy(actor.skill_queue_cursors),
               actor.server.db.conn.total_changes,random.getstate())==real,'commit real DB RNG player untouched')
        committed=fingerprint(actor.guardian7_lab)
        with patch('systems.admin_live_plain_skill_v8300._lab_turn10',side_effect=RuntimeError('fault')):
            try:await cmd('arena uoss kolejka prosty rzuc POTWIERDZAM')
            except RuntimeError:pass  # AUDIT_INTENTIONAL_PASS: deliberate fault-injection test
            else:raise AssertionError('fault must propagate for rollback')
        check(fingerprint(actor.guardian7_lab)==committed,'rollback all LAB fields after exception')
        check(actor.server.db.conn.total_changes==real[3] and random.getstate()==real[4],'exception no real side effects')
        actor.queue_rows={'physical':[{'skill_id':'s_aoe'}], 'magic':[], 'feedback':[]}
        check('brak gotowego' in await cmd('arena uoss kolejka prosty prognoza'),'AoE fail closed')
        actor.queue_rows={'physical':[{'skill_id':'s_fire'}], 'magic':[], 'feedback':[]}
        check('brak gotowego' in await cmd('arena uoss kolejka prosty prognoza'),'elemental queue fail closed')
        actor.queue_rows={'physical':[{'skill_id':'s_low'}], 'magic':[], 'feedback':[]}
        actor.guardian7_lab['_v7800_mana']=1
        check('za malo many' in await cmd('arena uoss kolejka prosty rzuc POTWIERDZAM') or 
              actor.guardian7_lab['_v7800_mana']==1,'insufficient mana fail closed')
    try:_ReadOnlyQueueDB(actor.server.db).save_character(None)
    except ValueError:check(True,'writable DB methods blocked')
    else:raise AssertionError('Writable DB method leaked')
    outsider=SkillOwner(False,actor.server.db)
    await outsider.admin_command('live arena uoss kolejka prosty prognoza')
    check('Nieznana komenda' in outsider.messages[-1],'admin authorization')
    await cmd('arena wyjdz')
    check('ADMIN LIVE V78' in await cmd('arena uoss kolejka prosty prognoza'),'arena required')
    return passes

if __name__=='__main__':
    print('v83 DETACHED PLAIN SKILL CAST:',asyncio.run(main()),'PASS')
