# -*- coding: utf-8 -*-
"""Execute the genuine Mec runtime wrapper and standalone Jammer handler."""
from __future__ import annotations
import asyncio
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.magitek.runtime import install
from core.classes_skills import CLASS_SKILLS

JAMMER=next(x for x in CLASS_SKILLS['Mec'] if x.get('mec_special')=='jammer')
NORMAL=next(x for x in CLASS_SKILLS['Mec'] if x.get('mec_special')=='logic_bomb')
CHECKS=0

def check(ok, msg):
    global CHECKS
    CHECKS+=1
    if not ok:
        raise AssertionError(f'JAMMER LIVE {CHECKS}: {msg}')

class Combat:
    def offensive_skill_core_power_v11185(self, skill, authored_base=0): return 100
    def offensive_skill_damage_type_v11190(self, skill): return 'magic'
    def offensive_skill_damage_multiplier_v11186(self, skill, skill_class_type=None):return 1.0
    def healing_skill_amount_v11196(self, skill, target, power):return 100
    async def use_class_skill(self, raw):
        self.baseline_calls+=1
        return 'BASELINE'

install(Combat)

class Game(Combat):
    def __init__(self, mobs, *, support=True, aoe=True, known=True, mana=100):
        self.character=SimpleNamespace(name='JammerTester',class_name='Mec',room_id='room')
        self.account_id=123
        self.current_hp=100
        self.current_mana=mana
        self.auto_fishing=self.auto_fishing_task=False
        self.auto_mining=self.auto_mining_task=False
        self.auto_woodcutting=self.auto_woodcutting_task=False
        self.combat_mob_key=None
        self._support=support
        self._aoe=aoe
        self._known=known
        self.baseline_calls=0
        self.xp=0
        self.realtime=0
        self.adaptive=[]
        self.assists=[]
        self.sent=[]
        self.party_sent=[]
        self.mobs=mobs
        self.server=SimpleNamespace(
            db=SimpleNamespace(knows_skill=lambda aid,sid:self._known,
                               skill_progress=lambda aid,sid:{'level':600}),
            world=SimpleNamespace(refresh=lambda:None,room_mobs=lambda rid:self.mobs),
            engagement_allowed=lambda sess,mob:mob.key!='foreign',
            sanitize_mob_engagement=lambda mob: None,
            auto_assist_party_combat=self._assist,
            party_combat_broadcast=self._party_announce,
        )
    def find_skill_from_input(self,raw):
        if 'logic bomb' in str(raw).lower():return NORMAL,''
        return JAMMER,''
    def is_downed_v0371(self):return False
    def skill_class_name(self,skill):return 'Mec'
    def class_mastery_level(self, cls):return 1000
    async def mec_refresh_vmax_v0319(self):pass
    def equipment_mp_cost_multiplier_v11176(self):return 1.0
    def combat_skill_mana_cost_v11191(self,skill,cls):return 40 if self._support else 20
    def mec_support_effect_v11149(self):return self._support
    def offensive_aoe_enabled_v11120(self):return self._aoe
    def effective_willpower(self):return 200
    async def _assist(self, session, mob):self.assists.append(mob.key)
    def apply_adaptive_mob_scale_v11330(self,mob):self.adaptive.append(mob.key)
    async def grant_skill_use_xp(self,skill):self.xp+=1
    async def ensure_realtime_combat(self):self.realtime+=1
    async def send(self, msg):self.sent.append(msg)
    async def _party_announce(self, actor, msg, detail='normal'):
        assert actor is self and detail=='essential'
        self.party_sent.append(msg)

def mob(name, tid='test_jammer_normal', **flags):
    result=SimpleNamespace(key=name,template_id=tid,alive=True,room_id='room',
                           engaged_by='',engaged_at=0,
                           v11196_jammer_stop_rounds=0)
    for key,value in flags.items():setattr(result,key,value)
    return result

async def scenarios():
    wolf=mob('wolf')
    robot=mob('robot', 'test_jammer_machine')
    boss=mob('boss','test_jammer_boss')
    foreign=mob('foreign')
    game=Game([wolf,robot,boss,foreign],support=True,aoe=True)
    with patch('random.random',return_value=0.0):
        result=await game.use_class_skill('Jammer')
    check(result is None,'cast returns normally')
    check(wolf.v11196_jammer_stop_rounds>0,'wolf stopped without Logic Bomb')
    check(robot.v11196_jammer_stop_rounds>0,'robot stopped without Logic Bomb')
    check(getattr(boss,'v11196_jammer_stop_rounds')==0,'boss immune')
    check(foreign.v11196_jammer_stop_rounds==0,'foreign engagement remains protected')
    check(game.current_mana==60,'Support costs 40 mana')
    check(game.xp==1,'grants skill XP')
    check(game.realtime==1,'starts normal realtime combat')
    check(game.baseline_calls==0,'actual wrapper intercepted before protected native')
    check(game.adaptive==['wolf','robot'],'adaptive scaling on eligible targets')
    check(game.assists==['wolf','robot'],'party combat begins on both targets')
    check(len(game.party_sent)==1 and '2 zatrzymanych' in game.party_sent[0],
          'one brief party announcement for AoE Jammer')
    check(any('Support weapon obejmuje wszystkich' in s for s in game.sent),'Support summary')
    check(not any(hasattr(m,'v11196_logic_bomb_rounds') for m in (wolf,robot)),
          'no Logic Bomb markers needed')
    check(all(x.v11196_jammer_stop_rounds for x in (wolf,robot)),'durations positive')
    check(wolf.v11196_jammer_stop_cleanseable and robot.v11196_jammer_stop_cleanseable,
          'Stop is cleanseable')

    # No refresh of active Stop and no mana loss on a second request.
    before=(wolf.v11196_jammer_stop_rounds,robot.v11196_jammer_stop_rounds)
    await game.use_class_skill('Jammer')
    check(game.current_mana==60,'no mana consumed on all targets already stopped')
    check(len(game.party_sent)==1,'no party announcement on a blocked repeat')
    check(before==(wolf.v11196_jammer_stop_rounds,robot.v11196_jammer_stop_rounds),
          'recast does not extend Stop')

    # AoE OFF chooses single monster even with Support weapon active.
    a,b=mob('a'),mob('b')
    g=Game([a,b],support=True,aoe=False)
    g.combat_mob_key='b'
    with patch('random.random',return_value=0):await g.use_class_skill('Jammer')
    check(a.v11196_jammer_stop_rounds==0,'AoE off leaves other monster')
    check(b.v11196_jammer_stop_rounds>0,'AoE off auto-selects engaged monster')
    check(g.current_mana==60,'Support mp cost retained with AoE off')
    check(any('AoE jest wyłączone' in s for s in g.sent),'AoE off announcement')

    # No Support weapon: only one target with AoE ON.
    a,b=mob('a'),mob('b')
    g=Game([a,b],support=False,aoe=True)
    with patch('random.random',return_value=0):await g.use_class_skill('Jammer')
    check(a.v11196_jammer_stop_rounds>0 and b.v11196_jammer_stop_rounds==0,
          'No Support limits to one target')
    check(g.current_mana==80,'Mec normal mp cost 20')

    # Misses can be tried again without Logic Bomb token, but cost mana.
    a=mob('miss')
    g=Game([a],support=False)
    with patch('random.random',return_value=0.999):await g.use_class_skill('Jammer')
    check(a.v11196_jammer_stop_rounds==0,'high roll resists Stop')
    check(g.current_mana==80,'failed attempt costs mana')
    with patch('random.random',return_value=0.0):await g.use_class_skill('Jammer')
    check(a.v11196_jammer_stop_rounds>0,'after resisted cast Jammer can retry')
    check(g.current_mana==60,'second attempted cast costs mana')

    # Boss only, foreign engagement only, or no mobs: no mana or XP spent.
    for candidates in ([mob('boss','test_jammer_boss')],[mob('foreign')],[]):
        g=Game(candidates,support=True)
        await g.use_class_skill('Jammer')
        check(g.current_mana==100,'no legal targets: unchanged mana')
        check(g.xp==0,'no legal targets: unchanged skill XP')
        check(any('brak dostępnych przeciwników' in x for x in g.sent),
              'clear no-target message')

    # Authentication, HP and mana guards (no expense).
    for kw in ({'known':False},{'mana':1}):
        g=Game([mob('w')],support=True,**kw)
        await g.use_class_skill('Jammer')
        check(g.current_mana==kw.get('mana',100),'blocked skill: mana unchanged')
        check(g.xp==0,'blocked skill: no XP')
    g=Game([mob('w')])
    g.current_hp=0
    await g.use_class_skill('Jammer')
    check(g.current_mana==100,'dead: no mana')

    # The wrapper must leave all other skills alone.
    g=Game([mob('w')])
    result=await g.use_class_skill('Logic Bomb')
    check(result=='BASELINE','non Jammer uses original method')
    check(g.baseline_calls==1,'baseline actually invoked once')

    # Two active players both in same room but foreign engaged target excluded.
    check(all('parali' not in x.casefold() for x in game.sent),'no Logic Bomb guidance')

if __name__=='__main__':
    from data.mobs import MOB_TEMPLATES
    fixtures={
        'test_jammer_normal':{'name':'Wilk Testowy','level':5},
        'test_jammer_machine':{'name':'Robot Testowy','level':5,'machine':True},
        'test_jammer_boss':{'name':'Boss Testowy','rank':'boss','level':5},
    }
    with patch.dict(MOB_TEMPLATES,fixtures):
        asyncio.run(scenarios())
    print(f'CURRENT JAMMER LIVE CAST: {CHECKS}/{CHECKS} PASS')
