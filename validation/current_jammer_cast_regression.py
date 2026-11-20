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
        raw=str(raw).strip()
        return JAMMER, (raw[10:].strip() if raw.casefold().startswith('jammer at ') else '')
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
    check(getattr(boss,'v11196_jammer_stop_rounds')>0,'boss receives real Stop')
    check(foreign.v11196_jammer_stop_rounds==0,'foreign engagement remains protected')
    check(game.current_mana==60,'Support costs 40 mana')
    check(game.xp==1,'grants skill XP')
    check(game.realtime==1,'starts normal realtime combat')
    check(game.baseline_calls==0,'actual wrapper intercepted before protected native')
    check(game.adaptive==['wolf','robot','boss'],'adaptive hook on eligible targets')
    check(game.assists==['wolf','robot','boss'],'party combat begins on eligible targets')
    check(len(game.party_sent)==1 and '3 zatrzymanych' in game.party_sent[0],
          'one brief party announcement for AoE Jammer')
    check(any('Dusza Meca: Jammer obejmuje wszystkich' in s for s in game.sent),'Soul summary')
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
    check(g.current_mana==80,'single target uses 20 MP despite permanent Soul')
    check(any('AoE wyłączone' in s for s in g.sent),'AoE off announcement')

    # Named target must override the current focus in single-target mode.
    a,b=mob('a'),mob('b')
    g=Game([a,b],support=True,aoe=False)
    g.combat_mob_key='a'
    with patch('random.random',return_value=0):await g.use_class_skill('Jammer at b')
    check(a.v11196_jammer_stop_rounds==0,'named target leaves previous focus untouched')
    check(b.v11196_jammer_stop_rounds>0,'named target receives Stop without Logic Bomb')
    check(g.current_mana==80,'named target costs 20 MP')
    a,b=mob('a'),mob('b')
    g=Game([a,b],support=True,aoe=False)
    await g.use_class_skill('Jammer at missing')
    check(a.v11196_jammer_stop_rounds==0 and b.v11196_jammer_stop_rounds==0,
          'unknown named target cannot accidentally Stop a different enemy')
    check(g.current_mana==100 and g.xp==0,'unknown target spends no mana or XP')
    # Explicit intent to use the Soul-wide mode still hits all in local room.
    a,b=mob('a'),mob('b')
    g=Game([a,b],support=True,aoe=True)
    with patch('random.random',return_value=0):await g.use_class_skill('Jammer at b')
    check(a.v11196_jammer_stop_rounds>0 and b.v11196_jammer_stop_rounds>0,
          'Soul AoE mode reaches all local enemies even with a named target')
    check(g.current_mana==60,'wide Jammer costs 40 MP')

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

    # A lone boss is a valid target; private engagements are not.
    single_boss=mob('boss_only','test_jammer_boss')
    g=Game([single_boss],support=False)
    with patch('random.random',return_value=0):await g.use_class_skill('Jammer')
    check(single_boss.v11196_jammer_stop_rounds>0,'Jammer succeeds against lone boss')
    check(g.current_mana==80 and g.xp==1,'boss Stop costs normal mana and grants real skill XP')
    for candidates in ([mob('foreign')],[]):
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
    # A stale world cache can contain mobs from other rooms. AoE and boss
    # targeting must never apply Stop/engagement/EXP outside the fight room.
    local_wolf=mob('local_wolf')
    remote_boss=mob('remote_boss', 'test_jammer_boss', room_id='other_room')
    remote_wolf=mob('remote_wolf', room_id='other_room')
    g=Game([remote_boss,local_wolf,remote_wolf],support=True,aoe=True)
    with patch('random.random',return_value=0):await g.use_class_skill('Jammer')
    check(local_wolf.v11196_jammer_stop_rounds>0,'current room combat target stopped')
    check(remote_boss.v11196_jammer_stop_rounds==0,'remote boss never stopped')
    check(remote_wolf.v11196_jammer_stop_rounds==0,'remote normal mob never stopped')
    check(g.assists==['local_wolf'],'assistance only for current room')
    check(g.adaptive==['local_wolf'],'no remote mob scale/engagement updates')
    check(g.current_mana==60 and g.xp==1,'valid local cast gets normal cost and XP')
    g=Game([remote_boss,remote_wolf],support=True,aoe=True)
    await g.use_class_skill('Jammer')
    check(g.current_mana==100 and g.xp==0,'remote-only targets cannot spend mana or give XP')
    check(remote_boss.v11196_jammer_stop_rounds==0,'remote-only boss untouched')

    # The caster can move during an awaited auto-task shutdown. No mana or
    # target flags may change in that case.
    moving=mob('moving')
    g=Game([moving],support=True,aoe=True)
    g.auto_fishing=True
    async def move_while_stopping(*,announce):
        g.character.room_id='next_room'
        g.auto_fishing=False
    g.stop_auto_fishing=move_while_stopping
    with patch('random.random',return_value=0):await g.use_class_skill('Jammer')
    check(moving.v11196_jammer_stop_rounds==0,'movement cancels remote Stop')
    check(g.current_mana==100 and g.xp==0,'movement before cast costs no mana or XP')
    check(not g.adaptive and not g.assists,'movement does not start foreign-room combat')

    # Move after the first hit, during an awaited reply. Other targets and
    # the caster's combat target must not leak to the next location.
    left,right=mob('left'),mob('right',tid='test_jammer_boss')
    g=Game([left,right],support=True,aoe=True)
    original_send=g.send
    async def move_on_stop_message(message):
        await original_send(message)
        if 'zostaje jednorazowo wyłączony' in message:
            g.character.room_id='adjacent_room'
    g.send=move_on_stop_message
    with patch('random.random',return_value=0):await g.use_class_skill('Jammer')
    check(left.v11196_jammer_stop_rounds>0,'first same-room hit is valid')
    check(right.v11196_jammer_stop_rounds==0,'second target skipped after movement')
    check(g.combat_mob_key is None and g.realtime==0,
          'next-room session never resumes previous room combat')


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
