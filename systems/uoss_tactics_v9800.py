# -*- coding: utf-8 -*-
"""v98: Declarative UOSS combat tactics. No scripts, reward changes or new IDs.

Each phase is a real *additional* attack modifier in the existing realtime
combat loop. Only the configured focused target receives the tactical bonus;
vanilla/source abilities, resistances and party combat ownership stay intact.
"""
from __future__ import annotations
import copy
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134

ACTIVE = {}
VALID_AI = {'all','weakest','strongest','focus'}


def validate(entries):
    if type(entries) is not dict or len(entries) > len(UOSS_SUPERBOSS_ENCOUNTERS_V11134):
        raise ValueError('Taktyka UOSS: nieprawidlowa mapa superbossow.')
    for key, spec in entries.items():
        if key not in UOSS_SUPERBOSS_ENCOUNTERS_V11134:
            raise ValueError('Taktyka UOSS: nieistniejacy superboss '+str(key)[:60])
        if type(spec) is not dict or set(spec) != {'phases'}:
            raise ValueError('Taktyka UOSS: wymagane tylko phases.')
        phases = spec['phases']
        if type(phases) is not list or not 1 <= len(phases) <= 5:
            raise ValueError('Taktyka UOSS: wymagane 1-5 faz.')
        previous = 101
        for phase in phases:
            if type(phase) is not dict or set(phase) != {'below_hp','every','attack_percent','ai','label'}:
                raise ValueError('Faza: below_hp, every, attack_percent, ai, label.')
            below, every, power = phase['below_hp'],phase['every'],phase['attack_percent']
            if type(below) is not int or not 1 <= below <= 100 or below >= previous:
                raise ValueError('Progi HP 1-100 musza malec.')
            if type(every) is not int or not 1 <= every <= 30:
                raise ValueError('Co ile atakow: 1-30.')
            if type(power) is not int or not 100 <= power <= 300:
                raise ValueError('Sila taktyczna: 100-300 procent.')
            if type(phase['ai']) is not str or phase['ai'] not in VALID_AI:
                raise ValueError('AI: all, weakest, strongest, focus.')
            label=phase['label']
            if type(label) is not str or not 1 <= len(label.strip()) <= 90 or any(ord(c)<32 or ord(c)==127 for c in label):
                raise ValueError('Nazwa ataku: 1-90 znakow bez sterowania.')
            previous=below
    return True


def sync(entries):
    validate(entries)
    ACTIVE.clear()
    ACTIVE.update(copy.deepcopy(entries))


def tactic(mob, template, targets=()):
    """Return (data-only phase, selected account-id), or (None,None).

    Do not increment counters here: combat_turn is authoritative and one enemy
    action (not each member of party) activates one configured tactical attack.
    """
    key=template.get('uoss_unique_superboss_key','')
    profile=ACTIVE.get(key)
    if not profile or int(getattr(mob,'hp',0) or 0)<=0:return None,None
    maximum=max(1,int(getattr(mob,'max_hp',0) or template.get('max_hp',1)))
    hp=max(0,int(getattr(mob,'hp',0) or 0))
    phase=next((p for p in reversed(profile['phases']) if hp*100<=maximum*p['below_hp']),None)
    if not phase:return None,None
    turn=int(getattr(mob,'combat_turn',0) or 0)
    if turn<=0 or turn%phase['every']:return None,None
    eligible=[t for t in targets if t and not getattr(t,'closed',False) and int(getattr(t,'current_hp',0) or 0)>0]
    if not eligible:return None,None
    ai=phase['ai']
    if ai=='all':return phase,None
    if ai=='weakest':selected=min(eligible,key=lambda t:(int(t.current_hp),int(getattr(t,'account_id',0))))
    elif ai=='strongest':selected=max(eligible,key=lambda t:(int(t.current_hp),-int(getattr(t,'account_id',0))))
    else:
        current=getattr(mob,'_v98_focus_account',None)
        selected=next((t for t in eligible if t.account_id==current),None)
        if selected is None:
            selected=eligible[0]
            mob._v98_focus_account=selected.account_id
    return phase,selected.account_id


def modifier(phase,selected_account,target):
    if not phase:return 1.0
    if selected_account is not None and getattr(target,'account_id',None)!=selected_account:return 1.0
    return phase['attack_percent']/100.0
