# -*- coding: utf-8 -*-
"""v93: one atomic quest repair plan across requirements and target references.

Reuses v91/v92 authoritative staging and full OLC validation. Never guesses
mappings, mutates account progress, or publishes ACTIVE implicitly.
"""
from __future__ import annotations
import copy
from types import SimpleNamespace

from systems.admin_live_v7100 import _plan, _commit, _undo
from systems.admin_live_v9100 import _active_quests, _mapping, _stage, _unresolved
from systems.admin_live_v9200 import (
    MODES, _matches, _patch, _apply_patch, _validate_new,
)
from systems.admin_live_quest_refs_v6100 import _id, _names
from systems.admin_live_integrity_v4900 import _effective

SLOT='adminlive9300_plan'
UNDO='adminlive9300_undo'
HELP=(
    'ADMIN LIVE POMOC 51: edytuj skill SKILL_ID olc_statuses | '
    '[{"kind":"poison","chance":0.5},{"kind":"burn","chance":0.4}] '
    '- dwa prawdziwe efekty trafienia dla zwyklego skilla damage/aoe_damage; '
    'dotychczasowe olc_status nadal dziala. Usun pole przez auto. '
    'questy napraw kompleks plan wymog STARE_ID NOWE_ID; kill STARE_ID NOWE_ID; '
    'collect STARE_ID NOWE_ID; talk STARE_ID NOWE_ID; surowiec STARE_ID NOWE_ID; '
    'reward STARE_ID NOWE_ID; npc STARE_ID NOWE_ID. Do 16 operacji i 64 questow, '
    'wymog oznacza NIEISTNIEJACY ID poprzednika. '
    'questy napraw kompleks zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
    'Wszystko tylko DRAFT, publikacja osobna, bez zmiany postepu i EXP graczy.'
)


def _parse(raw):
    if not isinstance(raw,str) or not 1<=len(raw)<=2500:
        raise ValueError('Plan ma miec od 1 do 2500 znakow.')
    steps=[step.strip() for step in raw.split(';')]
    if not 1<=len(steps)<=16 or any(not x for x in steps):
        raise ValueError('Wpisz 1–16 operacji TRYB STARE_ID NOWE_ID; oddziel srednikami.')
    parsed=[];seen=set()
    for step in steps:
        tokens=step.split()
        if len(tokens)!=3 or tokens[0] not in ('wymog', *MODES):
            raise ValueError('Wymagane TRYB STARE_ID NOWE_ID; tryby: wymog, kill, collect, talk, surowiec, reward, npc.')
        mode,old,new=tokens
        _id(old);_id(new)
        if old==new or (mode,old) in seen:
            raise ValueError('Stare i nowe ID musza sie roznic; bez powtarzania operacji.')
        seen.add((mode,old));parsed.append((mode,old,new))
    return parsed


def _candidate(service, steps):
    baseline=copy.deepcopy(service.draft)
    candidate=copy.deepcopy(baseline)
    changed=set()
    details=[]
    for mode,old,new in steps:
        proxy=SimpleNamespace(active=service.active, draft=candidate,
                              validate=service.validate, conn=service.conn)
        if mode=='wymog':
            catalog=_effective(proxy)
            mapping=_mapping(f'{old} | {new}',set(catalog),_unresolved(catalog))
            _previous,candidate,patches=_stage(proxy,mapping)
            matches=set(patches)
        else:
            _validate_new(proxy,mode,new)
            names=_names(proxy)
            if mode=='npc' and (old not in names or new not in names):
                raise ValueError('NPC: oba identyfikatory musza istniec.')
            catalog=_effective(proxy)
            matches={qid for qid,record in catalog.items() if _matches(record,mode,old,names)}
            if not matches:
                raise ValueError(f'{mode} {old}: brak questow z tym celem.')
            for qid in sorted(matches):
                patch=_patch(catalog[qid],mode,old,new,names)
                _apply_patch(candidate,qid,patch)
        changed.update(matches)
        if len(changed)>64:
            raise ValueError('Ponad 64 questy; podziel naprawe na mniejsze pakiety.')
        details.append(f'{mode} {old}->{new} ({len(matches)})')
    active={qid:n for qid,n in _active_quests(service,changed).items() if n}
    if active:
        raise ValueError('Przynajmniej jeden naprawiany quest jest aktywny u graczy: '+
                         ', '.join(f'{qid} ({n})' for qid,n in sorted(active.items())[:5]))
    service.validate(candidate)
    return baseline,candidate,changed,details


def plan(session,service,raw):
    setattr(session,SLOT,None)
    operations=_parse(raw)
    before,after,changed,details=_candidate(service,operations)
    _plan(session,SLOT,before,service.active,after,'QUEST NAPRAW KOMPLEKS')
    session.adminlive9300_quests=tuple(sorted(changed))
    return (f'QUEST NAPRAW KOMPLEKS PLAN: {len(operations)} operacji, {len(changed)} questow. '
            +'; '.join(details)+'. Bez zapisu. questy napraw kompleks zatwierdz POTWIERDZAM.')


async def dispatch_v9300(session,group,tail):
    parts=str(tail or '').strip().split()
    match=(group=='pomoc' and parts==['51']) or (
        group in ('questy','zadania') and parts[:2]==['napraw','kompleks'])
    if not match:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return True
    try:
        service=session.server.live_content_v1204
        if group=='pomoc':message=HELP
        elif parts[2:3]==['plan']:
            if len(parts)<6:raise ValueError('Plan: wpisz operacje TRYB STARE_ID NOWE_ID.')
            message=plan(session,service,str(tail).split('kompleks plan',1)[1].strip())
        elif parts[2:]==['zatwierdz','POTWIERDZAM']:
            if getattr(session,SLOT,None) and any(_active_quests(service,getattr(session,'adminlive9300_quests',())).values()):
                raise ValueError('Quest zostal przyjety po planie; zatwierdzenie zablokowane.')
            message=_commit(session,service,SLOT,UNDO)
        elif parts[2:]==['cofnij','POTWIERDZAM']:
            message=_undo(session,service,SLOT,UNDO)
        elif parts[2:]==['anuluj']:
            setattr(session,SLOT,None)
            message='QUEST NAPRAW KOMPLEKS: anulowano plan. DRAFT bez zmian.'
        else:raise ValueError('Wpisz admin live pomoc 51.')
    except (ValueError,KeyError,TypeError,RuntimeError,OverflowError,AttributeError) as exc:
        message='ADMIN LIVE v93: '+str(exc)[:430]
    await session.send(message)
    return True
