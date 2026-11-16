# -*- coding: utf-8 -*-
"""Jammer Stop without Logic Bomb; UOSS Support Soul Weapon & AoE retained."""
from __future__ import annotations
from pathlib import Path
import ast
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.current_jammer_auto import select_jammer_targets


def make(key, *, alive=True, stopped=0, tid='normal'):
    return SimpleNamespace(key=key, alive=alive, template_id=tid,
                           v11196_jammer_stop_rounds=stopped)


def run():
    checks=0
    def check(ok,why):
        nonlocal checks
        checks+=1
        if not ok:raise AssertionError(f'JAMMER {checks}: {why}')
    templates={
        'normal':{'name':'Zwykły Wilk','level':5},
        'machine':{'name':'Robot','level':5,'machine':True},
        'boss':{'name':'Boss','rank':'boss'},
        'mini':{'name':'Mini','rank':'miniboss'},
    }
    wolf, robot=make('w'), make('r',tid='machine')
    boss,mini=make('b',tid='boss'),make('m',tid='mini')
    stopped,dead=make('s',stopped=3),make('d',alive=False)
    room=[wolf,robot,boss,mini,stopped,dead,wolf]

    # With Support equipped, AoE ON expands into a real room-wide Stop.
    targets,immune,already=select_jammer_targets(room,templates,support_weapon=True,aoe_enabled=True)
    check([m.key for m in targets]==['w','r','b','m'],'support expands to all eligible incl bosses')
    check(immune==0,'bosses no longer immune')
    check(already==1,'stopped counted, no refresh')
    check(len(set(x.key for x in targets))==4,'duplicate mob suppressed')
    check(all(x.alive for x in targets),'no dead targets')
    check(all(x.key!='s' for x in targets),'active stop excluded')

    for support,aoe in ((False,False),(False,True),(True,False)):
        targets,immune,already=select_jammer_targets(room,templates,support_weapon=support,
                                                       aoe_enabled=aoe,preferred_key='r')
        check([m.key for m in targets]==['r'],f'single selected support={support} aoe={aoe}')
        check(immune==0,'bosses permitted in single mode')
        check(already==1,'already stopped in single mode')
    targets,_,_=select_jammer_targets(room,templates,support_weapon=True,aoe_enabled=True,preferred_key='r')
    check([m.key for m in targets]==['w','r','b','m'],'support AoE ignores locked single target')
    targets,_,_=select_jammer_targets(room,templates,support_weapon=True,aoe_enabled=False,preferred_key='missing')
    check([m.key for m in targets]==['w'],'single auto chooses available first')
    targets,_,_=select_jammer_targets(room,templates,support_weapon=True,aoe_enabled=False,preferred_key='s')
    check([m.key for m in targets]==['w'],'single skips already stopped target')
    targets,_,_=select_jammer_targets(room,templates,support_weapon=True,aoe_enabled=False,preferred_key='b')
    check([m.key for m in targets]==['b'],'single can select preferred boss')

    # No Logic Bomb/paralysis token is set anywhere in the fixtures.
    check(not any(hasattr(m,'v1200_logic_paralyze_token') for m in room),'no Logic Bomb prerequisite')
    check(not any(hasattr(m,'v1200_jammer_attempted_token') for m in room),'no Logic Bomb lock')
    targets,_,_=select_jammer_targets([wolf,robot],templates,support_weapon=True,aoe_enabled=True)
    check(len(targets)==2,'ordinary monsters without prior Paralyze still targeted')
    targets,immune,already=select_jammer_targets([boss,mini,stopped,dead],templates,support_weapon=True,aoe_enabled=True)
    check([m.key for m in targets]==['b','m'],'bosses remain legal even if others unavailable')
    check(immune==0 and already==1,'already stopped diagnostic')
    targets,_,_=select_jammer_targets([wolf,robot],templates,support_weapon=True,aoe_enabled=True,
                                        allowed=lambda mob,template: mob.key!='w')
    check([m.key for m in targets]==['r'],'superboss/story access gate respected')
    targets,_,_=select_jammer_targets([make('x',tid='absent')],templates,support_weapon=True,aoe_enabled=True)
    check(targets==[],'unknown mob is not legal target')

    targets,immune,already=select_jammer_targets([boss,mini],templates,support_weapon=True,aoe_enabled=True,allowed=lambda mob,template:mob.key!='m')
    check([m.key for m in targets]==['b'] and immune==0,'story/engagement gate still excludes protected miniboss')
    # Room filter is defense in depth against an out-of-date world index.
    in_room=make('local')
    in_room.room_id='fight_room'
    elsewhere=make('remote',tid='boss')
    elsewhere.room_id='other_room'
    targets,_,_=select_jammer_targets([elsewhere,in_room],templates,
                                        support_weapon=True,aoe_enabled=True,
                                        room_id='fight_room')
    check([m.key for m in targets]==['local'],'room-scoped Support AoE only')
    targets,_,_=select_jammer_targets([elsewhere],templates,
                                        support_weapon=True,aoe_enabled=True,
                                        room_id='fight_room')
    check(targets==[],'remote boss cannot be selected')
    targets,_,_=select_jammer_targets([elsewhere,in_room],templates,
                                        support_weapon=False,aoe_enabled=False,
                                        preferred_key='remote',room_id='fight_room')
    check([m.key for m in targets]==['local'],'remote preferred key ignored')
    # The v4.20 historical source contract must be retained byte-for-byte.
    from validation.current_native_v420_contract import verify_native_method
    check(verify_native_method(ROOT/'player/session_mixins/combat_skills.py',
                               'SessionCombatSkillsMixin.use_class_skill'),
          'historic v4.20 class-skill body matches native SHA256')
    source=(ROOT/'player/session_mixins/combat_skills.py').read_text(encoding='utf-8')
    runtime=(ROOT/'systems/magitek/runtime.py').read_text(encoding='utf-8')
    adapter=(ROOT/'systems/current_jammer_auto.py').read_text(encoding='utf-8')
    check(isinstance(ast.parse(source),ast.Module),'original combat native parses')
    check(isinstance(ast.parse(runtime),ast.Module),'runtime dispatch parses')
    check("and skill.get('mec_special') == 'jammer'" in runtime, 'wrapper identifies Jammer')
    check('from systems.current_jammer_auto import cast_jammer' in runtime,
          'runtime adapter calls standalone Jammer')
    check('return await cast_jammer(self, skill, target_text)' in runtime,
          'Jammer bypasses native Logic Bomb branch')
    check('return await baseline_cast(self,raw)' in runtime,
          'all other skills retain original native execution')
    check("if str(skill.get('mec_special',''))=='jammer':" in source,
          'historical Jammer source remains unmodified as a legacy fallback')
    check('async def cast_jammer(' in adapter,'separate independent Jammer implementation')
    check('support_weapon=support_effect' in adapter,'Support as Soul Weapon retained')
    check('aoe_enabled=aoe_enabled' in adapter,'AoE toggle retained')
    check('from systems.summon_ai_v1200 import jammer_eligible' not in adapter,
          'new Jammer never checks Logic Bomb prerequisite')
    check('v1200_jammer_attempted_token' not in adapter,
          'new Jammer does not require Logic Bomb token')
    check('session.current_mana -= mana_cost' in adapter,'mana debit after target checks')
    check(adapter.index('if not targets:') < adapter.index('session.current_mana -= mana_cost'),
          'no target leaves mana unchanged')
    check('Support weapon obejmuje wszystkich przeciwników.' in adapter,'Support combat message')
    check('AoE jest wyłączone — Support Effect pozostaje na jednym celu.' in adapter,
          'AoE OFF combat message')
    check('session.server.engagement_allowed(session, mob)' in adapter,
          'other player engagements protected')
    check('session.apply_adaptive_mob_scale_v11330(target)' in adapter,
          'live adaptive scaling stays integrated')
    check('session.grant_skill_use_xp(skill)' in adapter,'actual skill XP retained')
    check('await session.ensure_realtime_combat()' in adapter,'combat tick retained')

    # Historical source contract remains unchanged: Support weapon expands Jammer.
    from core.classes_skills import CLASS_SKILLS
    skill=next(s for s in CLASS_SKILLS['Mec'] if s.get('mec_special')=='jammer')
    check(skill.get('target_mode')=='one_or_support_all_enemies','UOSS target mode unchanged')
    check(bool(skill.get('support_weapon_expands_to_all_enemies')),'UOSS Support expansion unchanged')
    check(skill.get('uoss_mp_cost')==20,'normal UOSS MP unchanged')
    check(skill.get('uoss_support_mp_cost')==40,'Support UOSS MP unchanged')
    print(f'CURRENT JAMMER SUPPORT/AOE: {checks}/{checks} PASS')

if __name__=='__main__':run()
