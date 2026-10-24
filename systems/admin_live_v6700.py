# -*- coding: utf-8 -*-
"""UOSS helper-support outcomes using the Soulbound realtime balance rules.

NEVER run production realtime coroutine: it reads real DB, inventory, broadcasts,
world mobs and group. Select a real action using the runtime selector, then apply
ONLY deterministic, explicitly audited support rules on a detached single-actor
arena replica. Offense is labelled NOT simulated; no fabricated numeric damage.
"""
from __future__ import annotations
from systems.admin_live_v6500 import _replica
from systems.admin_guardian7_v4100 import _number
from world.uoss_superboss_runtime import (
    superboss_helper_profile_v11137, superboss_helper_action_v1146,
    superboss_helper_exact_utility_v11183, superboss_healing_blocked_v11179,
    superboss_helper_passives_v11174,
)

HELP = ('ADMIN LIVE POMOC 22: arena uoss pomocnik skutki [ILE] [HP MANA] - '
        'symulacja wsparcia pomocnika przez 1-12 tur na kopii. '
        'Leczenie Cure/Cure Water 23 procent, X-Ether 25 procent, '
        'Faerie Walnut 20 procent, Dryad Preach 8 procent, Bubble +50 procent max HP. '
        'Wybory akcji i wartosci uzywaja regul produkcyjnego Soulbound; '
        'ofensywa bez liczbowych obrazen (wymaga pelnej postaci i pancerza bossa). '
        'Bez zapisow, EXP, zmian areny ani globalnej losowosci.')


def _support(session, count=1, hp=None, mana=None):
    state=_replica(session)
    actor=state['actor8']; boss=state['boss']; template=state['template']
    profile=superboss_helper_profile_v11137(actor,template)
    if profile is None:
        return 'ARENA UOSS SKUTKI: brak aktywnego pomocnika. Arena bez zmian.'
    count=_number(count,1,12)
    first=max(1,int(state['round']))
    if first+count-1>250:
        raise ValueError('Maksimum 250 tur prywatnego laboratorium.')
    build=state.get('_guardian11_build',{})
    if not isinstance(build,dict):build={}
    if build.get('class'):
        max_mana=int(build.get('max_mana',0)); current_mana=int(build.get('mana',0))
    else:
        max_mana=int(actor.max_mana());current_mana=int(actor.current_mana)
    if not (0<=max_mana<=10**12 and 0<=current_mana<=max_mana):
        raise ValueError('Nieprawidlowa pula many testowej postaci.')
    actor._max_mana=max_mana;actor.current_mana=current_mana
    if hp is not None:actor.current_hp=_number(hp,1,int(state['hero_max']))
    if mana is not None:
        actor.current_mana=_number(mana,0,max_mana) if max_mana else _zero_mana(mana)
    # The production Session.max_hp respects the Bubble marker; _LabActor
    # exposes only base HP. Patch the *detached actor instance*, not its class.
    base_hp=int(state['hero_max'])
    actor.max_hp=lambda: int(round(base_hp*1.5)) if getattr(actor,'uoss_helper_bubble_v1146',False) else base_hp
    notes=[]; heal_total=0;mana_total=0; unresolved=0
    # Combat start effects had been applied in the private arena. Reapplying
    # a passive on a detached mob is idempotent and never targets the player.
    superboss_helper_passives_v11174(actor,template,boss)
    for turn in range(first,first+count):
        boss.combat_turn=turn
        action=superboss_helper_action_v1146(actor,template,boss)
        if not action:
            notes.append(f'{turn}: bez akcji');continue
        name=str(action['name']);ability=str(action['ability'])
        target=action.get('target');effect=''
        if ability in ('Cure Water','Cure') and target is actor:
            if superboss_healing_blocked_v11179(actor):
                effect='leczenie zablokowane przez Nullify Healing'
            else:
                gained=min(max(0,actor.max_hp()-actor.current_hp),max(1,int(actor.max_hp()*.23)))
                actor.current_hp+=gained;heal_total+=gained
                effect=f'+{gained} HP (regula Soulbound 23%)'
        elif ability=='Faerie Walnut' and target is actor:
            result=superboss_helper_exact_utility_v11183(actor,template,ability)
            gained=int(result['mana_restored']) if result else 0
            mana_total+=gained;effect=f'+{gained} MP (zrodlo UOSS 20%)'
        elif ability=='X-Ether' and target is actor:
            before=actor.current_mana
            actor.current_mana=min(actor.max_mana(),actor.current_mana+max(1,int(actor.max_mana()*.25)))
            gained=actor.current_mana-before;mana_total+=gained
            effect=f'+{gained} MP (regula Soulbound 25%)'
        elif ability=='Bubble':
            result=superboss_helper_exact_utility_v11183(actor,template,ability) if name=='Primm' else None
            if not getattr(actor,'uoss_helper_bubble_v1146',False):
                actor.uoss_helper_bubble_v1146=True
                effect=f'max HP {actor.max_hp()} (+50%, regula Soulbound)'
            else:effect='Bubble juz aktywny'
            if result:effect+='; potwierdzony mnoznik UOSS x1.50'
        elif ability=='Dryad Preach':
            gained=min(max(0,actor.max_mana()-actor.current_mana),max(1,int(actor.max_mana()*.08)))
            actor.current_mana+=gained;mana_total+=gained
            effect=f'+{gained} MP (regula Soulbound 8%)'
        elif ability=='Power Breakdown':
            boss.uoss_power_breakdown_v11174=True
            boss.uoss_power_breakdown_target_scope_v11196='enemy_only'
            effect='oslabienie na bossie, bez wymyslonej wartosci procentowej'
        else:
            unresolved+=1
            effect='atak: obrazenia NIEOBLICZONE (zalezne od pelnej postaci i obrony)'
        if superboss_helper_action_v1146(actor,template,boss) is not None:
            raise AssertionError('Pomocnik wykonal dwie akcje w jednej turze.')
        notes.append(f'{turn}: {name} {ability} -> {effect}')
    return (f'ARENA UOSS SKUTKI {profile["name"]}, {len(notes)} tur; '
            f'HP {actor.current_hp}/{actor.max_hp()}, MP {actor.current_mana}/{actor.max_mana()}; '
            f'leczenie {heal_total} HP, przywrocone {mana_total} MP; '
            f'ataki bez obliczen {unresolved}; '
            +'; '.join(notes)
            +'. Symulacja jednopostaciowa. Arena, RNG, SQLite, EXP i gracze BEZ ZMIAN. '
             'Nie jest to walka produkcyjna 1:1.')


def _zero_mana(value):
    if str(value)=='0':return 0
    raise ValueError('Ta postac nie ma many; tylko 0 jest dozwolone.')


async def dispatch_v67(session,group,raw):
    bits=str(raw or '').strip().split()
    matched=(group=='pomoc' and bits==['22']) or (
        group=='arena' and len(bits)>=3 and bits[:3]==['uoss','pomocnik','skutki'])
    if not matched:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if group=='pomoc':message=HELP
        elif len(bits)==3:message=_support(session)
        elif len(bits)==4:message=_support(session,bits[3])
        elif len(bits)==6:message=_support(session,bits[3],bits[4],bits[5])
        else:raise ValueError('Skladnia: arena uoss pomocnik skutki [ILE] [HP MANA].')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,AssertionError) as exc:
        message='ADMIN LIVE V67: '+str(exc)[:280]
    await session.send(message)
    return True
