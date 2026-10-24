# -*- coding: utf-8 -*-
"""Declarative OLC boss mechanics executed inside the authoritative combat loop.

Only documented, bounded primitive effects are accepted. Input is data, never
Python, and the published runtime is a deep copy of a validated OLC revision.
"""
from __future__ import annotations
import copy
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134

ACTIVE = {}
TARGETS = frozenset(('all', 'weakest', 'strongest', 'focus'))
EFFECTS = frozenset(('drain_mana', 'restore_mana', 'heal_boss', 'restore_health'))


def validate(data):
    if type(data) is not dict or len(data) > len(UOSS_SUPERBOSS_ENCOUNTERS_V11134):
        raise ValueError('MECHANIKI: slownik superbossow wymagany.')
    for boss, config in data.items():
        if boss not in UOSS_SUPERBOSS_ENCOUNTERS_V11134:
            raise ValueError('MECHANIKI: nieznany superboss: '+str(boss)[:40])
        if type(config) is not dict or set(config) != {'phases'}:
            raise ValueError('MECHANIKI: tylko pole phases.')
        phases=config['phases']
        if type(phases) is not list or not 1 <= len(phases) <= 6:
            raise ValueError('MECHANIKI: wymagane 1..6 faz.')
        previous=101
        for phase in phases:
            if type(phase) is not dict or not {'below_hp','every','target','actions','label'} <= set(phase) or not set(phase) <= {'below_hp','every','target','actions','label','conditions'}:
                raise ValueError('MECHANIKI: below_hp,every,target,actions,label.')
            if type(phase['below_hp']) is not int or not 1 <= phase['below_hp'] < previous:
                raise ValueError('MECHANIKI: progi HP maja malec od 100.')
            previous=phase['below_hp']
            if type(phase['every']) is not int or not 1 <= phase['every'] <= 30:
                raise ValueError('MECHANIKI: co 1..30 tur.')
            if phase['target'] not in TARGETS:
                raise ValueError('MECHANIKI: target all/weakest/strongest/focus.')
            label=phase['label']
            if type(label) is not str or not 1 <= len(label.strip()) <= 80 or any(ord(c)<32 or ord(c)==127 for c in label):
                raise ValueError('MECHANIKI: niepoprawny opis.')
            conditions=phase.get('conditions',{})
            if type(conditions) is not dict or not set(conditions) <= {'target_hp_below','target_mana_below','min_party'}:
                raise ValueError('MECHANIKI: conditions tylko target_hp_below, target_mana_below, min_party.')
            for condition,value in conditions.items():
                maximum=20 if condition=='min_party' else 100
                if type(value) is not int or not 1 <= value <= maximum:
                    raise ValueError('MECHANIKI: niedozwolony prog warunku '+condition)
            actions=phase['actions']
            if type(actions) is not list or not 1 <= len(actions) <= 3:
                raise ValueError('MECHANIKI: od 1 do 3 efektow na faze.')
            seen=set()
            for effect in actions:
                if type(effect) is not dict or set(effect) != {'type','percent'}:
                    raise ValueError('MECHANIKI: kazdy efekt ma type i percent.')
                kind=effect['type']; percent=effect['percent']
                if kind not in EFFECTS or kind in seen:
                    raise ValueError('MECHANIKI: nieznany lub powtorzony efekt.')
                seen.add(kind)
                if type(percent) is not int or not 1 <= percent <= 15:
                    raise ValueError('MECHANIKI: procent efektu musi byc 1..15.')
    return True


def sync(data):
    validate(data)
    ACTIVE.clear();ACTIVE.update(copy.deepcopy(data))


def _select(mob, mode, targets):
    eligible=[t for t in targets if t is not None and not getattr(t,'closed',False)
        and int(getattr(t,'current_hp',0) or 0)>0 and isinstance(getattr(t,'account_id',None),int)]
    if not eligible:return frozenset()
    if mode == 'all':return frozenset(t.account_id for t in eligible)
    if mode == 'weakest':chosen=min(eligible,key=lambda t:(int(t.current_hp),t.account_id))
    elif mode == 'strongest':chosen=max(eligible,key=lambda t:(int(t.current_hp),-t.account_id))
    else:
        prior=getattr(mob,'_v101_focus',None)
        chosen=next((t for t in eligible if t.account_id==prior),eligible[0])
        mob._v101_focus=chosen.account_id
    return frozenset((chosen.account_id,))


def on_boss_turn(mob, template, targets):
    """Return per-target instructions, apply boss healing once per source boss turn."""
    key=template.get('uoss_unique_superboss_key','')
    config=ACTIVE.get(key)
    if not config or not getattr(mob,'alive',False):return None
    turn=int(getattr(mob,'combat_turn',0) or 0)
    hp=int(getattr(mob,'hp',0) or 0)
    maximum=max(1,int(getattr(mob,'adaptive_max_hp_v11330',0) or getattr(mob,'max_hp',0) or template.get('max_hp',1)))
    if turn<=0 or hp<=0 or getattr(mob,'_v101_turn',None)==turn:return None
    phase=next((p for p in reversed(config['phases']) if hp*100<=maximum*p['below_hp']),None)
    if phase is None or turn%phase['every']:return None
    condition=phase.get('conditions',{})
    living=[t for t in targets if t is not None and not getattr(t,'closed',False) and int(getattr(t,'current_hp',0) or 0)>0]
    if len(living)<condition.get('min_party',1):return None
    def eligible(t):
        if 'target_hp_below' in condition and int(t.current_hp)*100>max(1,int(t.max_hp()))*condition['target_hp_below']:
            return False
        if 'target_mana_below' in condition and int(t.current_mana)*100>max(1,int(t.max_mana()))*condition['target_mana_below']:
            return False
        return True
    chosen=_select(mob,phase['target'],[t for t in living if eligible(t)])
    if not chosen:return None
    mob._v101_turn=turn
    amounts={e['type']:e['percent'] for e in phase['actions']}
    healed=0
    if 'heal_boss' in amounts:
        healed=min(max(0, maximum-hp), max(1,maximum*amounts['heal_boss']//100))
        mob.hp=hp+healed
    return {'turn':turn,'selected':chosen,'effects':amounts,'label':phase['label'],
            'boss_healed':healed,'mob_identity':id(mob)}


def apply_to_target(target, instruction):
    if instruction is None or target is None or getattr(target,'closed',False) or int(getattr(target,'current_hp',0) or 0)<=0:
        return None
    if target.account_id not in instruction['selected']:return None
    # Each turn/event is emitted only once; prevents double target processing.
    token=(instruction['mob_identity'],instruction['turn'])
    if getattr(target,'_v101_effect_turn',None)==token:return None
    maximum=max(0,int(target.max_mana()))
    current=max(0,int(target.current_mana))
    result={}
    for name,pct in instruction['effects'].items():
        if name=='drain_mana' and maximum:
            val=min(current,max(1,maximum*pct//100));current-=val;result['drain_mana']=val
        elif name=='restore_mana' and maximum:
            val=min(maximum-current,max(1,maximum*pct//100));current+=val;result['restore_mana']=val
        elif name=='restore_health':
            maxhp=max(1,int(target.max_hp()))
            hp=max(0,int(target.current_hp))
            val=min(max(0,maxhp-hp),max(1,maxhp*pct//100))
            target.current_hp=hp+val;result['restore_health']=val
    target.current_mana=current
    target._v101_effect_turn=token
    return result
