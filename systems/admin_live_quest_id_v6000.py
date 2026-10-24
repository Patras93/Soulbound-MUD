# -*- coding: utf-8 -*-
"""v60: owner-approved quest item/target ID repairs using authoritative OLC DRAFT.

No guesses, no ACTIVE publication, no SQLite or character/reward mutations.
"""
from __future__ import annotations

import copy
import re

from data.items import ITEMS
from data.mobs import MOB_TEMPLATES
from systems.admin_live_integrity_v4900 import _effective
from systems.live_quest_olc_v1209 import parse_quest_edit

_ID = re.compile(r'[A-Za-z0-9_\-]{1,100}\Z')
_KINDS = ('nagroda', 'cel')
HELP = (
    'ADMIN LIVE POMOC 15: questy id karta QUEST_ID - aktualne cele i nagrody; '
    'questy id znajdz nagroda|cel STARE_ID [STRONA] - wyszukiwanie 8/strona; '
    'questy id plan nagroda|cel STARE_ID NOWE_ID [QUEST_ID ...] - od 1 do 8 questow; '
    'questy id zatwierdz POTWIERDZAM - walidowany zapis TYLKO DRAFT; '
    'questy id cofnij POTWIERDZAM - cofniecie bez cudzych zmian; '
    'questy id anuluj/status. Nie zgadujemy ID mobow ani przedmiotow, '
    'nie usuwamy ani nie dodajemy nagrod. Questy cele: tylko kill/collect. '
    'Zmiana ACTIVE wymaga osobnego sprawdz/porownaj/aktywuj.'
)


def _catalog_items(service):
    keys=set(ITEMS)
    for section in (service.active,service.draft):
        additions=section.get('items',{})
        if isinstance(additions,dict):keys.update(additions)
    return keys


def _catalog_mobs(service):
    keys=set(MOB_TEMPLATES)
    for section in (service.active,service.draft):
        additions=section.get('mobs',{})
        if isinstance(additions,dict):keys.update(additions)
    return keys


def _check_id(value):
    if not isinstance(value,str) or not _ID.fullmatch(value):
        raise ValueError('Nieprawidlowe ID; uzyj liter, cyfr, _ lub -.')
    return value


def _matches(catalog, kind, old):
    if kind not in _KINDS:raise ValueError('Rodzaj: nagroda lub cel.')
    if kind=='nagroda':
        return [qid for qid,q in sorted(catalog.items())
                if isinstance(q.get('reward_items'),dict) and old in q['reward_items']]
    return [qid for qid,q in sorted(catalog.items())
            if q.get('kind') in ('kill','collect') and q.get('target')==old]


def _rewrite(service, catalog, kind, old, new, ids):
    # Retains quantities and all untouched fields. Collision refuses rather
    # than silently merging/removing rewards or changing quest counts.
    candidate=copy.deepcopy(service.draft)
    changes=[]
    for qid in ids:
        quest=catalog[qid]
        if kind=='nagroda':
            loot=quest.get('reward_items')
            if not isinstance(loot,dict) or old not in loot:
                raise ValueError(qid+': brak starego przedmiotu w nagrodach.')
            if new in loot:
                raise ValueError(qid+': NOWE_ID juz istnieje; nie polacze ilosci automatycznie.')
            replacement={new if key==old else key:qty for key,qty in loot.items()}
            field,clean=parse_quest_edit('reward_items',replacement)
            detail=f'{qid}: reward_items {old} x{loot[old]} -> {new} x{loot[old]}'
        else:
            if quest.get('kind') not in ('kill','collect') or quest.get('target')!=old:
                raise ValueError(qid+': cel mozna zmieniac tylko dla kill/collect z tym ID.')
            field,clean=parse_quest_edit('target',new)
            detail=f'{qid}: target {old} -> {new} ({quest["kind"]})'
        candidate.setdefault('quest_edits',{}).setdefault(qid,{})[field]=clean
        changes.append(detail)
    service.validate(candidate)
    return candidate,tuple(changes)


def find_quest_ids(service, kind, old, page='1'):
    _check_id(old)
    catalog=_effective(service)
    matches=_matches(catalog,kind,old)
    raw=str(page)
    if not raw.isascii() or not raw.isdecimal() or len(raw)>5:
        raise ValueError('STRONA: podaj dodatnia liczbe.')
    n=int(raw)
    pages=max(1,(len(matches)+7)//8)
    if not 1<=n<=pages:raise ValueError(f'Strona od 1 do {pages}.')
    subset=matches[(n-1)*8:n*8]
    return (f'QUEST ID ZNAJDZ {kind} {old}: trafienia {len(matches)}, strona {n}/{pages}. '
            +(', '.join(subset) or 'Brak trafien.')+'. Bez zmian.')


def quest_id_card(service, qid):
    _check_id(qid)
    catalog=_effective(service)
    if qid not in catalog:raise ValueError('Nieznany quest. Uzyj admin live questy szukaj.')
    q=catalog[qid]
    reward=q.get('reward_items') or {}
    if isinstance(reward,dict):
        show=', '.join(f'{key} x{value}' for key,value in list(reward.items())[:12]) or 'brak'
    else:show='niepoprawny format'
    target=str(q.get('target') or '-')[:100]
    return (f'QUEST ID KARTA {qid}: {str(q.get("name",qid))[:65]}; typ {q.get("kind")}; '
            f'cel {target}; nagrody EQ {show}. DRAFT - podglad, bez zmian.')


def plan_quest_id_change(session, service, kind, old, new, ids=()):
    _check_id(old);_check_id(new)
    if old==new:raise ValueError('Stare i nowe ID musza sie roznic.')
    if kind not in _KINDS:raise ValueError('Rodzaj: nagroda lub cel.')
    catalog=_effective(service)
    matches=_matches(catalog,kind,old)
    if ids:
        if not 1<=len(ids)<=8 or len(set(ids))!=len(ids):
            raise ValueError('Podaj 1-8 roznych ID questow.')
        for qid in ids:_check_id(qid)
        if any(qid not in matches for qid in ids):
            raise ValueError('Quest nie istnieje lub nie uzywa starego ID. Uzyj questy id znajdz.')
        selected=list(ids)
    else:
        if len(matches)>8:
            raise ValueError(f'Znaleziono {len(matches)} questow. Wybierz maksymalnie 8 ID z listy znajdz.')
        selected=matches
    if not selected:raise ValueError('Nie znaleziono questow z podanym STARE_ID.')
    if kind=='nagroda':
        if new not in _catalog_items(service):
            raise ValueError('NOWE_ID nie istnieje w katalogu przedmiotow/OLC.')
    elif any(new not in (_catalog_mobs(service) if catalog[qid].get('kind')=='kill' else _catalog_items(service)) for qid in selected):
        raise ValueError('NOWE_ID nie istnieje w katalogu mobow lub przedmiotow odpowiedniego typu.')
    candidate,details=_rewrite(service,catalog,kind,old,new,selected)
    before=copy.deepcopy(service.draft);active=copy.deepcopy(service.active)
    session.adminlive60_plan=(before,active,candidate,details)
    return (f'QUEST ID PLAN: {len(selected)} questow; '+'; '.join(details)+'. '
            'Bez zapisu. Zatwierdz: admin live questy id zatwierdz POTWIERDZAM. '
            'Tylko DRAFT, publikacja osobno.')


def commit_quest_id_change(session,service):
    plan=getattr(session,'adminlive60_plan',None)
    if plan is None:raise ValueError('Brak planu. Uzyj questy id plan.')
    before,active,candidate,details=plan
    if service.active!=active or service.draft!=before:
        session.adminlive60_plan=None
        raise ValueError('ACTIVE/DRAFT zmieniony od planu. Przygotuj nowy plan.')
    service.validate(candidate)
    service.draft=copy.deepcopy(candidate)
    session.adminlive60_undo=(before,copy.deepcopy(candidate),active)
    session.adminlive60_plan=None
    return (f'QUEST ID DRAFT: zapisano {len(details)} zmian. '
            'Nie opublikowano, SQLite i postepy graczy bez zmian. '
            'Sprawdz/porownaj, potem osobno aktywuj.')


def undo_quest_id_change(session,service):
    record=getattr(session,'adminlive60_undo',None)
    if record is None:raise ValueError('Brak zmiany do cofniecia.')
    before,after,active=record
    if service.active!=active or service.draft!=after:
        raise ValueError('ACTIVE/DRAFT zmienione pozniej; nie cofne cudzych zmian.')
    service.draft=copy.deepcopy(before)
    session.adminlive60_plan=None;session.adminlive60_undo=None
    return 'QUEST ID COFNIETO: przywrocono DRAFT; ACTIVE i SQLite bez zmian.'


async def dispatch_v60(session,group,raw):
    bits=str(raw or '').strip().split()
    if group=='pomoc' and bits==['15'] or (group in ('questy','zadania') and bits and bits[0]=='id'):
        if not session.is_admin():
            await session.send('Nieznana komenda. Wpisz help.');return True
        try:
            if group=='pomoc':result=HELP
            elif bits[:2]==['id','karta'] and len(bits)==3:
                result=quest_id_card(session.server.live_content_v1204,bits[2])
            elif bits[:2]==['id','znajdz'] and len(bits) in (4,5):
                result=find_quest_ids(session.server.live_content_v1204,bits[2],bits[3],bits[4] if len(bits)==5 else '1')
            elif bits[:2]==['id','plan'] and len(bits)>=5:
                result=plan_quest_id_change(session,session.server.live_content_v1204,bits[2],bits[3],bits[4],bits[5:])
            elif bits==['id','zatwierdz','POTWIERDZAM']:
                result=commit_quest_id_change(session,session.server.live_content_v1204)
            elif bits==['id','cofnij','POTWIERDZAM']:
                result=undo_quest_id_change(session,session.server.live_content_v1204)
            elif bits==['id','anuluj']:
                session.adminlive60_plan=None;result='QUEST ID: plan anulowany.'
            elif bits==['id','status']:
                result=('QUEST ID STATUS: plan '+('gotowy' if getattr(session,'adminlive60_plan',None) else 'brak')+
                        '; cofanie '+('dostepne' if getattr(session,'adminlive60_undo',None) else 'brak')+'.')
            else:raise ValueError('Uzyj: questy id karta/znajdz/plan/zatwierdz/cofnij/anuluj/status; pomoc 15.')
        except (ValueError,TypeError,KeyError,OverflowError,AttributeError) as exc:
            result='ADMIN LIVE ID: '+str(exc)[:300]
        await session.send(result)
        return True
    return False
