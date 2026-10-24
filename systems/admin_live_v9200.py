# -*- coding: utf-8 -*-
"""v92: atomic, explicit repair of quest targets across six reference categories.

Uses the authoritative OLC validator, rejects partial drafts and blocks changing
accepted quest objectives. No player progress, database or live world mutation.
"""
from __future__ import annotations
import copy
from systems.admin_live_v7100 import _plan, _commit, _undo
from systems.admin_live_integrity_v4900 import _effective
from systems.admin_live_quest_refs_v6100 import _id, _names, _valid_target
from systems.admin_live_v9100 import _active_quests
from systems.live_quest_olc_v1209 import parse_quest_edit
from data.items import ITEMS

SLOT='adminlive9200_targets_plan'
UNDO='adminlive9200_targets_undo'
MODES=('kill','collect','talk','surowiec','reward','npc')
HELP=(
    'ADMIN LIVE POMOC 50: questy cele znajdz TRYB STARE_ID [STRONA]; '
    'questy cele plan TRYB STARE_ID | NOWE_ID; TRYB STARE_ID | NOWE_ID (1-16 zmian). '
    'TRYBY: kill (pojedynczy i wielocelowy), collect (pojedynczy i wielocelowy), '
    'talk (rozmowy wielocelowe), surowiec (zestawy surowcow), '
    'reward (nagrody przedmiotowe), npc (zleceniodawca). '
    'questy cele zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
    'Zamienniki podaje administrator. Blokada kolizji celow i zmian questow aktywnych u graczy. '
    'Wyłącznie DRAFT; do publikacji uzyj admin live aktualizacja publikacja sprawdz i aktywuj POTWIERDZAM.'
)


def _matches(record,mode,old,names):
    kind=record.get('kind')
    if mode=='npc':return bool(names.get(old)) and str(record.get('giver','')).casefold()==names[old].casefold()
    if mode=='reward':return old in (record.get('reward_items') or {})
    if mode=='surowiec':return kind=='collect_resource_set' and old in (record.get('resource_targets') or {})
    if mode in ('kill','collect') and kind==mode and record.get('target')==old:return True
    if kind!='multi_objective' or mode not in ('kill','collect','talk'):return False
    objectives=record.get('objectives') or {}
    return old in objectives.get(mode,([] if mode=='talk' else {}))


def _validate_new(service,mode,new):
    if mode=='reward':
        if new not in ITEMS and not any(new in s.get('items',{}) for s in (service.draft,service.active)):
            raise ValueError('Nagroda: brak przedmiotu NOWE_ID.')
    elif not _valid_target(service,mode,new):
        raise ValueError('NOWE_ID nie istnieje w katalogu pasujacym do trybu.')


def _patch(record,mode,old,new,names):
    """Return a minimal patch, preserving counts and secondary objectives."""
    if mode=='npc':
        if names[old].casefold()==names[new].casefold():
            raise ValueError('NPC maja identyczne nazwy; zleceniodawca pozostanie bez zmian.')
        return {'giver':parse_quest_edit('giver',names[new])[1]}
    if mode=='reward':
        items=copy.deepcopy(record.get('reward_items') or {})
        if new in items:raise ValueError('Nagrody zawieraja juz NOWE_ID; brak bezpiecznego scalania.')
        items[new]=items.pop(old)
        return {'reward_items':parse_quest_edit('reward_items',items)[1]}
    if mode=='surowiec':
        group=copy.deepcopy(record.get('resource_targets') or {})
        if new in group:raise ValueError('Zestaw surowcow ma juz NOWE_ID.')
        group[new]=group.pop(old)
        patch={'resource_targets':parse_quest_edit('resource_targets',group)[1]}
        if record.get('target')==old:patch['target']=parse_quest_edit('target',new)[1]
        return patch
    if record.get('kind')==mode and mode in ('kill','collect'):
        return {'target':parse_quest_edit('target',new)[1]}
    objectives=copy.deepcopy(record.get('objectives') or {})
    group=objectives.get(mode, [] if mode=='talk' else {})
    if new in group:raise ValueError('Cel wielocelowy zawiera juz NOWE_ID.')
    if mode=='talk': objectives[mode]=[new if x==old else x for x in group]
    else:objectives[mode]={new if k==old else k:v for k,v in group.items()}
    return {'objectives':parse_quest_edit('objectives',objectives)[1]}


def _apply_patch(candidate,qid,patch):
    # Created quests are complete definitions, but may also have an edit record.
    if qid in candidate.get('quests',{}):
        candidate['quests'][qid].update(patch)
        if qid in candidate['quest_edits']:
            for key,val in patch.items():
                if key in candidate['quest_edits'][qid]:candidate['quest_edits'][qid][key]=val
    else:candidate.setdefault('quest_edits',{}).setdefault(qid,{}).update(patch)


def _operations(raw):
    if not isinstance(raw,str) or not 1<=len(raw)<=2400:
        raise ValueError('Plan: 1-2400 znakow.')
    parts=[x.strip() for x in raw.split(';')]
    if not 1<=len(parts)<=16 or any(not x for x in parts):
        raise ValueError('Podaj 1-16 niepustych operacji, oddzielonych srednikiem.')
    operations=[];used=set()
    for part in parts:
        if part.count('|')!=1:raise ValueError('Format: TRYB STARE_ID | NOWE_ID.')
        left,right=part.split('|',1);tokens=left.split()
        if len(tokens)!=2 or tokens[0] not in MODES:
            raise ValueError('TRYB: kill, collect, talk, surowiec, reward albo npc.')
        mode,old=tokens;old=_id(old);new=_id(right.strip())
        if old==new:raise ValueError('Stare i nowe ID musza byc rozne.')
        if (mode,old) in used:raise ValueError('Powtorzona operacja dla tego samego ID.')
        used.add((mode,old));operations.append((mode,old,new))
    return operations


def find(service,mode,old,page='1'):
    if mode not in MODES:raise ValueError('Nieznany tryb.')
    _id(old)
    if not page.isascii() or not page.isdecimal() or len(page)>4:
        raise ValueError('Niepoprawna strona.')
    names=_names(service)
    entries=[qid for qid,record in sorted(_effective(service).items()) if _matches(record,mode,old,names)]
    num=int(page);pages=max(1,(len(entries)+7)//8)
    if not 1<=num<=pages:raise ValueError('Strony 1..'+str(pages))
    return (f'QUEST CELE ZNAJDZ {mode} {old}: {len(entries)} questow, strona {num}/{pages}: '
            +(', '.join(entries[(num-1)*8:num*8]) or 'BRAK')+'. Tylko odczyt.')


def plan(session,service,raw):
    setattr(session,SLOT,None)
    operations=_operations(raw)
    original=copy.deepcopy(service.draft);candidate=copy.deepcopy(original)
    catalog=copy.deepcopy(_effective(service));names=_names(service)
    touched=set();details=[]
    for mode,old,new in operations:
        _validate_new(service,mode,new)
        if mode=='npc' and (old not in names or new not in names):
            raise ValueError('NPC: STARE_ID i NOWE_ID musza istniec.')
        matches=[qid for qid,record in catalog.items() if _matches(record,mode,old,names)]
        if not matches:raise ValueError(f'{mode} {old}: brak questow do zmiany.')
        if len(touched|set(matches))>64:raise ValueError('Pakiet dotyka ponad 64 questow; podziel na mniejsze plany.')
        for qid in matches:
            patch=_patch(catalog[qid],mode,old,new,names)
            _apply_patch(candidate,qid,patch)
            catalog[qid].update(patch)
            touched.add(qid)
        details.append(f'{mode} {old}->{new}: {len(matches)}')
    active={qid:number for qid,number in _active_quests(service,touched).items() if number}
    if active:
        raise ValueError('Zmiany dotykaja questow przyjetych przez graczy: '+
                         ', '.join(f'{key} ({count})' for key,count in sorted(active.items())[:5]))
    # One whole-world validation: no partly staged repairs, no unvalidated fields.
    service.validate(candidate)
    _plan(session,SLOT,original,service.active,candidate,'QUEST CELE PAKIET')
    session.adminlive9200_touched=tuple(sorted(touched))
    return (f'QUEST CELE PLAN: {len(operations)} operacji, {len(touched)} questow; '
            +'; '.join(details)+'. Bez zapisu. Wpisz questy cele zatwierdz POTWIERDZAM.')


async def dispatch_v9200(session,cmd,tail):
    parts=str(tail or '').strip().split()
    matched=(cmd=='pomoc' and parts==['50']) or (
        cmd in ('questy','zadania') and parts[:1]==['cele'])
    if not matched:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        service=session.server.live_content_v1204
        if cmd=='pomoc':message=HELP
        elif len(parts)>=2:
            sub=parts[1:]
            if sub[:1]==['znajdz'] and len(sub) in (3,4):
                message=find(service,sub[1],sub[2],sub[3] if len(sub)==4 else '1')
            elif sub[:1]==['plan'] and len(sub)>1:
                message=plan(session,service,str(tail).split('cele plan',1)[1].strip())
            elif sub==['zatwierdz','POTWIERDZAM']:
                if getattr(session,SLOT,None):
                    touched=getattr(session,'adminlive9200_touched',())
                    if any(_active_quests(service,touched).values()):
                        raise ValueError('Quest zostal przyjety po planie. Zatwierdzenie zablokowane.')
                message=_commit(session,service,SLOT,UNDO)
            elif sub==['cofnij','POTWIERDZAM']:
                message=_undo(session,service,SLOT,UNDO)
            elif sub==['anuluj']:
                setattr(session,SLOT,None);message='QUEST CELE: plan anulowany. Niczego nie zmieniono.'
            else:raise ValueError('Wpisz admin live pomoc 50.')
        else:raise ValueError('Wpisz admin live pomoc 50.')
    except (ValueError,TypeError,KeyError,RuntimeError,AttributeError,OverflowError) as exc:
        message='ADMIN LIVE v92: '+str(exc)[:430]
    await session.send(message)
    return True
