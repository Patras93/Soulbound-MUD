# -*- coding: utf-8 -*-
"""Admin Guardian 9.0: private, reversible UOSS rehearsal and read-only OLC comparisons.

Safety contract:
- no live Session/world/combat/database/reward calls;
- preview works on an independent clone and restores Python PRNG state;
- snapshot/restore operate only on session-local test data;
- quest checks are read-only, never publish DRAFT.
A simulation using selected sourced mechanics is NOT a production fight replay.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter
from types import SimpleNamespace

from systems.admin_guardian7_v4100 import _id, _number, _MAX_TURNS, _lab_status, _lab_log, _lab_report
from systems.admin_guardian8_v4200 import _turn, _start, _snapshot_status, _batch_preview
from systems.admin_guardian6_v4000 import _combined

_MAX_BATCH = 20  # session-only UI safety bound, not a damage or live combat cap
_HELP = {
 '1': ('GUARDIAN9 pomoc 1/3 ARENA: arena start BOSS_ID HP ATAK [HELPER]; '
       'arena atak [CEL]; arena magia ELEMENT [CEL]; arena obrona; arena lecz; arena oczysc; '
       'arena prognoza ILE [atak/obrona/lecz]; arena seria ILE [atak/obrona/lecz]; '
       'arena migawka; arena przywroc POTWIERDZAM; arena status; arena raport; arena wyjdz. '
       'Prognoza nie zmienia areny; seria zmienia tylko prywatna kopie walki.'),
 '2': ('GUARDIAN9 pomoc 2/3 QUESTY: questy seria roznice ID | POLE | WARTOSC ; ID | POLE | WARTOSC; '
       'questy draft STRONA; questy zaleznosci ID. Zmiany wprowadzaj przez guardian8 seria '
       'zmien ... | POTWIERDZAM. Publikacja tylko admin live sprawdz/porownaj/aktywuj POTWIERDZAM.'),
 '3': ('GUARDIAN9 pomoc 3/3: arena pracuje na kopiach bez nagrod, SQLite i prawdziwego HP. '
       'Prognoza przywraca losowosc silnika, ale przyszla gra moze sie roznic. '
       'Brak pelnego AI produkcyjnego, skilli postaci, EQ i interwalow czasowych. '
       'Maksymalnie 20 tur jednym poleceniem, max 250 tur LAB, bez limitow w grze.'),
}


def _state(session):
    state=getattr(session,'guardian7_lab',None)
    if not isinstance(state,dict) or 'actor8' not in state:
        raise ValueError('Brak areny9. Wpisz arena start BOSS_ID HP ATAK.')
    return state


def _sync_actor(state):
    """v42 kept actor.current_hp at starting HP; keep sourced handlers coherent."""
    actor=state['actor8']
    actor.current_hp=int(state['hero_hp'])
    actor._max_hp=int(state['hero_max'])
    # v65: exact catalog item IDs selected with admin live arena zaloz.
    # A detached actor cannot read real player inventory, by design.
    from data.items import ITEMS
    selected=state.get('_guardian11_build',{}).get('items',{})
    if not isinstance(selected,dict):selected={}
    actor._lab_equipped_rows_v6500=tuple(
        {'item_id':value} for slot,value in sorted(selected.items())
        if isinstance(value,str) and value in ITEMS
    )
    # Deepcopy cannot rebind lambda closures: never let a preview resolve
    # party members through an actor from the original test session.
    actor.server.party_sessions=lambda *_a, **_kw:[actor]
    return actor


def _private_turn(session,action='atak',target='boss',element=None):
    state=_state(session)
    _sync_actor(state)
    before=copy.deepcopy(state)
    try:
        message=_turn(session,action=action,element=element,target=target)
        _sync_actor(state)
        return message.replace('ARENA8','ARENA9')
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError):
        # Rehearsal remains consistent after any rejected action.
        session.guardian7_lab=before
        raise


def _ticks(value):
    return _number(value,1,_MAX_BATCH)


def _simulation(session,count,action='atak',preview=False):
    if action not in ('atak','obrona','lecz'):
        raise ValueError('Tylko akcje atak, obrona, lecz; max 20 tur.')
    count=_ticks(count)
    current=_state(session)
    if current.get('finished'):
        raise ValueError('Arena zakonczona. Wybierz arena start lub wyjdz.')
    if preview:
        fake=SimpleNamespace(guardian7_lab=copy.deepcopy(current))
        # The source has a random Emerald Weapon summon. Do not consume
        # production PRNG just to calculate a hypothetical result.
        saved_rng=random.getstate()
    else:
        fake=session
        saved_rng=None
    messages=[]
    try:
        for _ in range(count):
            if fake.guardian7_lab['finished'] or fake.guardian7_lab['round']>=_MAX_TURNS:
                break
            messages.append(_private_turn(fake,action=action))
        after=fake.guardian7_lab
        boss=after['boss']
        result=(f'ARENA9 {"PROGNOZA" if preview else "SERIA"} {len(messages)}/{count} tur {action}; '
                f'runda {after["round"]}; boss HP {boss.hp}/{boss.max_hp}; '
                f'postac HP {after["hero_hp"]}/{after["hero_max"]}; '
                f'pomocnicy aktywni {sum(e["hp"]>0 for e in after["adds"])}; '
                f'{"KONIEC" if after["finished"] else "TRWA"}. '
                +('Biezaca arena BEZ ZMIAN. Prognoza warunkowa; nie gwarantuje RNG przyszlych tur.'
                  if preview else 'Zmiany wylacznie w prywatnym laboratorium.'))
        return result
    finally:
        if saved_rng is not None:
            random.setstate(saved_rng)


def _snapshot(session):
    state=_state(session)
    session.guardian9_snapshot=copy.deepcopy(state)
    return (f'ARENA9 MIGAWKA runda {state["round"]}; zapisano TYLKO prywatna symulacje. '
            'Przywracanie: arena przywroc POTWIERDZAM.')


def _restore(session):
    state=getattr(session,'guardian9_snapshot',None)
    if state is None:
        raise ValueError('Nie ma migawki areny9.')
    _state(session)
    session.guardian7_lab=copy.deepcopy(state)
    _sync_actor(session.guardian7_lab)
    return f'ARENA9 PRZYWROCONO migawke rundy {state["round"]}; bez zmiany prawdziwej postaci.'


def _compare_batch(service,payload):
    before,after,ids,_notes=_batch_preview(service,payload)
    result=[]
    for qid in ids:
        old=before.get('quest_edits',{}).get(qid,{})
        new=after.get('quest_edits',{}).get(qid,{})
        for key in sorted(new):
            if new[key]!=old.get(key):
                prev=old.get(key,'(dziedziczone)')
                result.append(f'{qid}.{key}: {str(prev)[:35]} -> {str(new[key])[:35]}')
    return (f'QUEST9 SERIA ROZNICE: {len(ids)} questow, {len(result)} pol. '
            +('; '.join(result[:18]) or 'Brak zmiany wartosci DRAFT')+'. '
            +'Tylko podglad, bez zmian.')


def _draft_page(service,page):
    p=_number(page,1,10000)
    active=service.active.get('quest_edits',{})
    draft=service.draft.get('quest_edits',{})
    ids=sorted(q for q in (set(active)|set(draft)) if active.get(q,{})!=draft.get(q,{}))
    total=max(1,(len(ids)+7)//8)
    if p>total:raise ValueError(f'Nie ma strony {p}; dostepne 1-{total}.')
    names=[]
    for qid in ids[(p-1)*8:p*8]:
        diffs=[key for key in sorted(set(active.get(qid,{}))|set(draft.get(qid,{})))
               if active.get(qid,{}).get(key)!=draft.get(qid,{}).get(key)]
        names.append(f'{qid} ({len(diffs)} pol: {", ".join(diffs[:4])})')
    return (f'QUEST9 DRAFT {p}/{total}; questy ze zmianami {len(ids)}; '
            +('; '.join(names) or 'brak')+'. Bez zmian i bez publikacji.')


def _dependencies(service,qid):
    qid=_id(qid)
    catalog=_combined(service)
    if qid not in catalog:raise ValueError('Nieznane ID questa.')
    staged=service.draft.get('quest_edits',{})
    # This is a bounded DFS of the quest-to-quest dependency tree.
    visiting=set();done=set();edges=0;missing=set();cycles=[]
    def walk(node,ancestors):
        nonlocal edges
        if node in visiting:
            cycles.append(' -> '.join((ancestors+[node])[-8:]));return
        if node in done:return
        if len(done)+len(visiting)>300 or len(ancestors)>300:
            raise ValueError('Graf zaleznosci za duzy, zatrzymano skan.')
        visiting.add(node)
        d=dict(catalog[node]);d.update(staged.get(node,{}))
        requested=[]
        if d.get('requires_quest'):requested.append(d['requires_quest'])
        multi=d.get('requires_quests') or []
        if isinstance(multi,(list,tuple)):
            requested.extend(multi)
        for dependency in requested:
            edges+=1
            if edges>20000:raise ValueError('Za wiele zaleznosci w grafie.')
            if dependency not in catalog:missing.add(str(dependency))
            else:walk(dependency,ancestors+[node])
        visiting.remove(node);done.add(node)
    walk(qid,[])
    return (f'QUEST9 ZALEZNOSCI {qid}: {len(done)} odwiedzonych, {edges} laczy; '
            f'brakujace {len(missing)} [{", ".join(sorted(missing)[:6]) or "brak"}]; '
            f'cykle {len(cycles)} [{"; ".join(cycles[:3]) or "brak"}]. '
            'Diagnostyka, bez automatycznych zmian.')


async def handle_guardian9(session,raw):
    parts=str(raw or '').strip().split(maxsplit=1)
    if not parts or parts[0].casefold()!='guardian9':return False
    if not session.is_admin():
        await session.send('GUARDIAN9: tylko wlasciciel-administrator.');return True
    service=session.server.live_content_v1204
    rest=parts[1].strip() if len(parts)>1 else 'pomoc 1'
    args=rest.split();mode=args[0].casefold() if args else 'pomoc'
    try:
        if mode=='pomoc':
            n=args[1] if len(args)>1 else '1'
            if len(args)>2 or n not in _HELP:raise ValueError('Pomoc: 1, 2, 3.')
            msg=_HELP[n]
        elif mode=='status':
            msg='GUARDIAN9: bez produkcyjnych nagrod i zapisow; '+('arena aktywna' if getattr(session,'guardian7_lab',None) and 'actor8' in session.guardian7_lab else 'arena nieaktywna')+'.'
        elif mode=='arena':
            op=args[1].casefold() if len(args)>1 else ''
            if op=='start' and len(args) in (5,6):
                msg=_start(session,service,args[2],args[3],args[4],args[5] if len(args)==6 else 'brak').replace('ARENA8','ARENA9')
                session.guardian9_snapshot=None
                _sync_actor(_state(session))
            elif op in ('atak','obrona','lecz','oczysc') and len(args) in (2,3) and (len(args)==2 or op=='atak'):
                msg=_private_turn(session,action=op,target=args[2] if len(args)==3 else 'boss')
            elif op=='magia' and len(args) in (3,4):
                msg=_private_turn(session,action='magia',element=args[2],target=args[3] if len(args)==4 else 'boss')
            elif op in ('prognoza','seria') and len(args) in (3,4):
                msg=_simulation(session,args[2],args[3].casefold() if len(args)==4 else 'atak',op=='prognoza')
            elif op=='migawka' and len(args)==2:msg=_snapshot(session)
            elif op=='przywroc' and len(args)==3 and args[2]=='POTWIERDZAM':msg=_restore(session)
            elif op=='status' and len(args)==2:
                a=_state(session)
                msg=_lab_status(session).replace('ARENA7','ARENA9')+' '+_snapshot_status(a)
            elif op=='dziennik' and len(args) in (2,3):
                _state(session)
                msg=_lab_log(session,args[2] if len(args)==3 else '1').replace('ARENA7','ARENA9')
            elif op=='raport' and len(args)==2:
                _state(session)
                msg=_lab_report(session).replace('ARENA7','ARENA9')
            elif op=='wyjdz' and len(args)==2:
                session.guardian7_lab=None;session.guardian9_snapshot=None
                msg='ARENA9: usunieto prywatna symulacje i migawke; brak zmian w grze.'
            else:raise ValueError(_HELP['1'])
        elif mode=='questy':
            op=args[1].casefold() if len(args)>1 else ''
            if op=='seria' and len(args)>2:
                restparts=rest.split(None,3)
                if len(restparts)!=4 or restparts[2].casefold()!='roznice':raise ValueError(_HELP['2'])
                msg=_compare_batch(service,restparts[3])
            elif op=='draft' and len(args) in (2,3):msg=_draft_page(service,args[2] if len(args)==3 else '1')
            elif op=='zaleznosci' and len(args)==3:msg=_dependencies(service,args[2])
            else:raise ValueError(_HELP['2'])
        else:raise ValueError('Wpisz admin guardian9 pomoc 1, 2 lub 3.')
        await session.send(msg)
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        await session.send('GUARDIAN9: '+str(exc)[:350])
    return True
