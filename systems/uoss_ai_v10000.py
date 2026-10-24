# -*- coding: utf-8 -*-
"""v100 bounded data-only UOSS AI: phase-triggered mana pressure.

No arbitrary scripts, no added damage, no rewards, no global status changes.
A combat action is authorised once per authoritative mob combat_turn, then
applied at most once to each selected living target.
"""
from __future__ import annotations
import copy
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134

ACTIVE = {}
_MODES = frozenset(('all', 'weakest', 'strongest', 'focus'))


def validate(profiles):
    if type(profiles) is not dict or len(profiles)>len(UOSS_SUPERBOSS_ENCOUNTERS_V11134):
        raise ValueError('UOSS AI: oczekiwany slownik superbossow.')
    for name, spec in profiles.items():
        if name not in UOSS_SUPERBOSS_ENCOUNTERS_V11134:
            raise ValueError('UOSS AI: nieznany superboss.')
        if type(spec) is not dict or set(spec)!={'phases'}:
            raise ValueError('UOSS AI: wymagane phases.')
        phases=spec['phases']
        if type(phases) is not list or not 1<=len(phases)<=5:
            raise ValueError('UOSS AI: 1-5 faz.')
        old=101
        for p in phases:
            if type(p) is not dict or set(p)!={'below_hp','every','mode','mana_percent','label'}:
                raise ValueError('UOSS AI: below_hp,every,mode,mana_percent,label.')
            if type(p['below_hp']) is not int or not 1<=p['below_hp']<old:raise ValueError('UOSS AI: malejace progi HP 1..100.')
            if type(p['every']) is not int or not 1<=p['every']<=30:raise ValueError('UOSS AI: okres 1..30 tur.')
            if type(p['mode']) is not str or p['mode'] not in _MODES:raise ValueError('UOSS AI: mode all/weakest/strongest/focus.')
            if type(p['mana_percent']) is not int or not 1<=p['mana_percent']<=10:raise ValueError('UOSS AI: 1..10 procent maksymalnej many.')
            lab=p['label']
            if type(lab) is not str or not 1<=len(lab.strip())<=70 or any(ord(c)<32 or ord(c)==127 for c in lab):
                raise ValueError('UOSS AI: nazwa 1..70 znakow bez sterowania.')
            old=p['below_hp']
    return True


def sync(profiles):
    validate(profiles)
    ACTIVE.clear()
    ACTIVE.update(copy.deepcopy(profiles))


def _target_ids(mob, mode, targets):
    eligible=[t for t in targets if t is not None and not getattr(t,'closed',False)
              and int(getattr(t,'current_hp',0) or 0)>0 and isinstance(getattr(t,'account_id',None),int)]
    if not eligible:return frozenset()
    if mode=='all':return frozenset(t.account_id for t in eligible)
    if mode=='weakest':chosen=min(eligible,key=lambda t:(int(t.current_hp),t.account_id))
    elif mode=='strongest':chosen=max(eligible,key=lambda t:(int(t.current_hp),-t.account_id))
    else:
        prior=getattr(mob,'_v100_ai_focus',None)
        chosen=next((t for t in eligible if t.account_id==prior),eligible[0])
        mob._v100_ai_focus=chosen.account_id
    return frozenset((chosen.account_id,))


def action(mob, template, targets):
    """Once each boss turn, choose a bounded group; return immutable action tuple."""
    key=template.get('uoss_unique_superboss_key','')
    profile=ACTIVE.get(key)
    if not profile or not getattr(mob,'alive',False):return None
    hp=int(getattr(mob,'hp',0) or 0)
    turn=int(getattr(mob,'combat_turn',0) or 0)
    maximum=max(1,int(getattr(mob,'adaptive_max_hp_v11330',0) or getattr(mob,'max_hp',0) or template.get('max_hp',1)))
    if hp<=0 or turn<=0 or getattr(mob,'_v100_ai_turn',None)==turn:return None
    phase=next((p for p in reversed(profile['phases']) if hp*100<=maximum*p['below_hp']),None)
    if not phase or turn%phase['every']:return None
    targets=_target_ids(mob,phase['mode'],targets)
    if not targets:return None
    mob._v100_ai_turn=turn
    return (turn,targets,phase['mana_percent'],phase['label'])


def apply(target, instruction):
    """Apply one mana drain per selected target, without touching HP/rewards."""
    if not instruction or target is None or getattr(target,'closed',False) or int(getattr(target,'current_hp',0) or 0)<=0:
        return 0
    turn,selected,pct,_=instruction
    if getattr(target,'account_id',None) not in selected:return 0
    if getattr(target,'_v100_ai_mana_event',None)==(id(instruction),turn):return 0
    maximum=max(0,int(target.max_mana()))
    current=max(0,int(getattr(target,'current_mana',0) or 0))
    drained=min(current,max(1,maximum*pct//100)) if maximum>0 else 0
    # The event only exists in the live combat action and target eligibility is checked there.
    target.current_mana=current-drained
    target._v100_ai_mana_event=(id(instruction),turn)
    return drained
