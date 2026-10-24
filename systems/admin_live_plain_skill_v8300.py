# -*- coding: utf-8 -*-
"""Detached execution of one conservative, ordinary direct damage skill.

Never invokes use_class_skill, whose normal implementation can update live
world/quests/parties/XP. It reuses production stat, cost, critical and defense
methods on copied actor/boss objects, and the v83 common damage primitive.
No claim of full UOSS skill parity: elemental reactions, AI, party procs, Mec,
AoE, drain, debuffs, DOT and on-hit specials are explicitly disallowed.
"""
from __future__ import annotations
import copy
import random
from systems.admin_live_arena_damage_v7800 import _arena, _rng_initial
from systems.admin_live_queue_v8200 import isolated_queue_selection
from systems.uoss_queue_choice_shared_v8200 import QUEUE_TYPES
from systems.uoss_plain_skill_shared_v8300 import plain_skill_damage_roll
from core.progression_resources import skill_power_multiplier
from systems.soul_ancients_v1330 import evolution_power_multiplier
from systems.soul_evolutions_v1332 import role_evolution
from systems.elemental_combat import skill_element_v11339
from world.machine_expansion import v0314_adjust_damage_vs_template
from player.session_mixins.skill_learning import SessionSkillLearningMixin
from data.mobs import MOB_TEMPLATES
from systems.admin_guardian10_v4400 import _lab_turn10
from systems.admin_guardian9_v4300 import _state

HELP = ('ADMIN LIVE POMOC 43: arena uoss kolejka prosty prognoza - podglad wykonania '
        'nastepnego zwyklego pojedynczego skilla damage; arena uoss kolejka prosty '
        'rzuc POTWIERDZAM - zuzyj prywatna mane, nalicz realne obrazenia bazowe '
        'i obrone na kopii bossa oraz przesun prywatny kursor kolejki. '
        'Zablokowane: AoE, Mec, specjalne efekty, zywiolowe reakcje, '
        'drain, execute, grupa, nagrody i zapis swiata. Kontratak bossa nadal MODELOWY.')

_REJECT_FIELDS = ('mec_authored','mec_special','engineer_special','element',
                  'v1100_dual_elements','enemy_debuffs','soulbound_harmful_debuff',
                  'self_damage','self_damage_pct','feedback_damage',
                  'active_special','carries_soul_weapon_elements','mechanic_cooldown')

_ALLOWED_FIELDS = frozenset((
    'id', 'name', 'aliases', 'natural_tags', 'unlock', 'kind', 'cooldown',
    'mana', 'desc', 'scale', 'mult', 'mastery_choice_group',
    'legacy_soul_unlock', 'soulbound_kind_target_scope_v11196',
    'pre_v1110_skill_name', 'legacy_display_name_v03013',
))

def _ordinary(skill, actor):
    # Whitelist rather than blacklist: future skill effect metadata must not
    # silently become eligible for isolated casting.
    if set(skill) - _ALLOWED_FIELDS:
        raise ValueError('Kolejka LAB: skill ma nieobslugiwane efekty; bezpieczne wykonanie zablokowane.')
    if skill.get('kind') != 'damage' or any(skill.get(k) for k in _REJECT_FIELDS):
        raise ValueError('Kolejka LAB: wybrany skill ma efekty specjalne; bezpieczne wykonanie zablokowane.')
    if skill_element_v11339(actor.skill_class_name(skill),skill.get('name',''),''):
        raise ValueError('Kolejka LAB: reakcja zywiolowa wymaga pelnej izolacji; skill zablokowany.')
    if int(skill.get('unlock',0))>int(actor.class_mastery_level(actor.skill_class_name(skill))):
        raise ValueError('Kolejka LAB: za mala bieglosc klasy.')

async def _calculate(session,state):
    actor,boss,choice,enabled = isolated_queue_selection(session,state)
    if not enabled:raise ValueError('Kolejka LAB jest wylaczona.')
    if choice is None:raise ValueError('Kolejka LAB: brak gotowego skilla.')
    channel,index,length,skill=choice
    _ordinary(skill,actor)
    if not boss.alive or boss.hp<=0:raise ValueError('Prywatny boss juz pokonany.')
    template=MOB_TEMPLATES.get(boss.template_id)
    if not template:raise ValueError('Brak produkcyjnego szablonu bossa.')
    progress=actor.server.db.skill_progress(actor.account_id,skill['id'])
    if not isinstance(progress,dict) and not hasattr(progress,'keys'):
        raise ValueError('Nieprawidlowy odczyt poziomu skilla.')
    level=int(progress['level'])
    if level<1:raise ValueError('Skill nie ma poprawnego poziomu.')
    class_name=actor.skill_class_name(skill)
    cost=int(actor.combat_skill_mana_cost_v11191(skill,class_name))
    if cost>0:cost=int(round(cost*actor.equipment_mp_cost_multiplier_v11176()))
    if cost<0 or cost>actor.current_mana:
        raise ValueError('Kolejka LAB: za malo many w kopii.')
    # Rehydrate only private combo/counter state between rehearsed casts.
    for key in ('_olc32_skill_combo','_olc33_previous_skill','_olc34_last_skill'):
        if key in state.get('_v8300_actor_state',{}):
            setattr(actor,key,copy.deepcopy(state['_v8300_actor_state'][key]))
    private_rng=copy.deepcopy(state.get('_v7800_rng',_rng_initial(session,state)))
    world_rng=random.getstate()
    notes=[]
    async def quiet(message,*args,**kwargs):notes.append(str(message)[:120])
    actor.send_combat=quiet
    try:
        random.setstate(private_rng)
        power=skill_power_multiplier(level)*evolution_power_multiplier(level,actor.character.soul_level)
        power*=role_evolution(skill,level,actor.character.soul_level,'offense')
        class_type=actor.offensive_skill_damage_type_v11190(skill)
        multiplier=actor.offensive_skill_damage_multiplier_v11186(skill,class_type)*power
        core=actor.offensive_skill_core_power_v11185(skill)
        damage,critical=plain_skill_damage_roll(actor,core,multiplier)
        actor.current_mana-=cost
        boss.player_hits=max(0,int(getattr(boss,'player_hits',0) or 0))
        damage=await SessionSkillLearningMixin.apply_boss_defense(actor,boss,damage)
        damage=actor.v0210_adjust_player_damage(damage)
        damage,machine_note=v0314_adjust_damage_vs_template(template,damage,class_type,skill.get('name',''))
        damage=max(0,int(damage))
        boss.hp-=damage
        next_rng=random.getstate()
    finally:
        random.setstate(world_rng)
    snapshot={key:copy.deepcopy(getattr(actor,key)) for key in
              ('_olc32_skill_combo','_olc33_previous_skill','_olc34_last_skill')
              if hasattr(actor,key)}
    return {'skill':str(skill.get('name',skill['id']))[:90], 'channel':channel,
            'index':index,'length':length,'damage':damage,'critical':critical,
            'cost':cost,'mana':actor.current_mana,'hits':boss.player_hits,
            'rng':next_rng,'actor_state':snapshot,'note':machine_note,
            'notes':notes,'kind':class_type}

async def preview(session):
    state=_arena(session)
    result=await _calculate(session,state)
    return (f'ARENA UOSS KOLEJKA PROSTY PROGNOZA: {result["skill"]}; '
            f'{result["damage"]} obrazen po obronie, '
            +('krytyk; ' if result['critical'] else 'bez krytyka; ')
            +f'mana koszt {result["cost"]}, pozostanie {result["mana"]}. '
             'Bez zmian w LAB i postaci. Efekty specjalne i AI 1:1 NIE sa wykonywane.')

async def cast(session):
    state=_arena(session)
    before=copy.deepcopy(state)
    try:
        result=await _calculate(session,state)
        previous=state['hero_attack']
        state['hero_attack']=result['damage']
        report=_lab_turn10(session,'atak')
        state=_state(session)
        state['hero_attack']=previous
        state['boss'].player_hits=result['hits']
        state['_v7800_mana']=result['mana']
        state['_v7800_rng']=result['rng']
        state['_v8300_actor_state']=result['actor_state']
        # Production skill cursor rotation, but ONLY in private state.
        cursors=copy.deepcopy(state.get('_v8300_queue_cursors',getattr(session,'skill_queue_cursors',{}) or {}))
        cursors[result['channel']]=(result['index']+1)%result['length']
        state['_v8300_queue_cursors']=cursors
        state['_v8300_queue_next_type']=QUEUE_TYPES[(QUEUE_TYPES.index(result['channel'])+1)%len(QUEUE_TYPES)]
        return (f'ARENA UOSS KOLEJKA PROSTY RZUC: {result["skill"]}; '
                f'{result["damage"]} obrazen, koszt {result["cost"]} many, '
                f'mana LAB {result["mana"]}. {report} '
                'Kontratak bossa nadal MODELOWY. Brak XP, zlota i lootow.')
    except BaseException:
        session.guardian7_lab=before
        raise
