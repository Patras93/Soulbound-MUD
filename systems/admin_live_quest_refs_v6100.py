# -*- coding: utf-8 -*-
"""v61: validated replacements of NPC giver and structured quest references.

Admin-only, bounded and explicit. All modifications affect OLC DRAFT ONLY.
Existing player quest progress is never migrated or reset.
"""
from __future__ import annotations

import copy
import re

from data.items import ITEMS
from data.mobs import MOB_TEMPLATES
from data.npcs import NPCS
from systems.admin_live_integrity_v4900 import _effective
from systems.live_quest_olc_v1209 import parse_quest_edit

_ID = re.compile(r'[A-Za-z0-9_-]{1,100}\Z')
MODES = ('npc', 'surowiec', 'kill', 'collect', 'talk')
HELP = ('ADMIN LIVE POMOC 16: questy ref karta QUEST_ID; '
        'questy ref znajdz npc|surowiec|kill|collect|talk STARE_ID [STRONA]; '
        'questy ref plan TRYB STARE_ID NOWE_ID [QUEST_ID ...] - 1-8 questow; '
        'questy ref zatwierdz POTWIERDZAM - zapis tylko DRAFT; '
        'questy ref cofnij POTWIERDZAM, anuluj, status. '
        'npc: ID NPC (zamiana nazwy zleceniodawcy); surowiec: zestaw surowcow; '
        'kill/collect/talk: zadania wielocelowe. Wymagane prawdziwe ID. '
        'Nie zgadujemy zamiennikow ani nie zmieniamy postepow graczy.')


def _id(value):
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError('ID: dozwolone litery, cyfry, _ i -, od 1 do 100 znakow.')
    return value


def _npc_catalog(service):
    out = dict(NPCS)
    for section in (service.active, service.draft):
        added = section.get('npcs', {})
        if isinstance(added, dict):
            out.update(added)
        for key, patch in section.get('npc_edits', {}).items():
            if key in out and isinstance(patch, dict):
                out[key] = {**out[key], **patch}
    return out


def _valid_target(service, mode, key):
    if mode == 'npc' or mode == 'talk':
        return key in _npc_catalog(service)
    if mode == 'surowiec' or mode == 'collect':
        items = set(ITEMS)
        for section in (service.active, service.draft):
            items.update(section.get('items', {}))
        if key not in items:
            return False
        if mode == 'surowiec':
            # The legacy validator uses the static data.items item classification.
            return (ITEMS.get(key) or {}).get('type') in (
                'resource', 'material', 'craft_material', 'gem_raw', 'archaeology_find')
        return True
    if mode == 'kill':
        mobs = set(MOB_TEMPLATES)
        for section in (service.active, service.draft):
            mobs.update(section.get('mobs', {}))
        return key in mobs
    raise ValueError('TRYB: npc, surowiec, kill, collect lub talk.')


def _uses(q, mode, key, npc_names):
    if mode == 'npc':
        return str(q.get('giver') or '').casefold() == npc_names.get(key, '').casefold() and bool(npc_names.get(key))
    if mode == 'surowiec':
        return q.get('kind') == 'collect_resource_set' and key in (q.get('resource_targets') or {})
    if q.get('kind') != 'multi_objective':
        return False
    group = (q.get('objectives') or {}).get(mode, [] if mode == 'talk' else {})
    return key in group


def _names(service):
    return {key: str(n.get('name','')) for key,n in _npc_catalog(service).items() if isinstance(n,dict)}


def _matches(service, mode, key):
    if mode not in MODES:
        raise ValueError('TRYB: npc, surowiec, kill, collect lub talk.')
    catalog = _effective(service)
    names = _names(service)
    return [qid for qid, quest in sorted(catalog.items()) if _uses(quest, mode, key, names)]


def find_refs(service, mode, old, page='1'):
    _id(old)
    if mode not in MODES:
        raise ValueError('Nieprawidlowy tryb.')
    if not _valid_target(service, mode, old):
        # Faulty/removed IDs may not be in current catalogs: still allow searching.
        if mode == 'npc':
            raise ValueError('NPC ID musi istniec; dla starej nazwy uzyj edytuj quest.')
    hits = _matches(service, mode, old)
    if not isinstance(page, str) or not page.isascii() or not page.isdecimal() or len(page)>5:
        raise ValueError('STRONA: liczba dodatnia.')
    num = int(page)
    pages = max(1, (len(hits)+7)//8)
    if not 1 <= num <= pages:
        raise ValueError(f'Strona od 1 do {pages}.')
    shown = ', '.join(hits[(num-1)*8:num*8]) or 'brak'
    return f'QUEST REF {mode} {old}: {len(hits)} trafien, strona {num}/{pages}: {shown}. Bez zmian.'


def ref_card(service, qid):
    _id(qid)
    catalog = _effective(service)
    if qid not in catalog:
        raise ValueError('Nieznany quest.')
    q = catalog[qid]
    resource = q.get('resource_targets') or {}
    objectives = q.get('objectives') or {}
    parts = [f'QUEST REF KARTA {qid}',f'typ {q.get("kind","-")}',f'NPC {q.get("giver","-")}',
             f'surowce {repr(resource)[:180]}',f'cele {repr(objectives)[:240]}']
    return '; '.join(parts)+'. Podglad bez zmian.'


def _rewrite(service, mode, old, new, ids, catalog, names):
    candidate = copy.deepcopy(service.draft)
    details = []
    for qid in ids:
        q = catalog[qid]
        if not _uses(q,mode,old,names):
            raise ValueError(qid+': nie uzywa wskazanego ID.')
        if mode == 'npc':
            old_name = names[old];new_name = names[new]
            if not new_name.strip() or old_name.casefold()==new_name.casefold():
                raise ValueError('Obaj NPC maja taka sama lub pusta nazwe.')
            field,clean=parse_quest_edit('giver',new_name)
            details.append(f'{qid}: NPC {old_name} -> {new_name}')
            patches={field:clean}
        elif mode == 'surowiec':
            old_group = q.get('resource_targets') or {}
            if new in old_group:
                raise ValueError(qid+': nowy surowiec juz jest; nie sumuje ilosci.')
            replaced = {new if k==old else k:v for k,v in old_group.items()}
            field,clean=parse_quest_edit('resource_targets',replaced)
            patches={field:clean}
            if q.get('target') not in replaced:
                # A legacy resource-set quest may have no top-level target.
                # Preserve its totals, attach a real member of the new set.
                replacement_target = new if q.get('target')==old else next(iter(replaced))
                target_field,target=parse_quest_edit('target',replacement_target)
                patches[target_field]=target
            details.append(f'{qid}: surowiec {old} x{old_group[old]} -> {new} x{old_group[old]}')
        else:
            original = q.get('objectives') or {}
            group = original.get(mode, [] if mode == 'talk' else {})
            if new in group:
                raise ValueError(qid+': nowy cel juz wystepuje; brak automatycznego laczenia.')
            converted = copy.deepcopy(original)
            if mode == 'talk':
                converted[mode] = [new if x==old else x for x in group]
                qty=1
            else:
                converted[mode] = {new if k==old else k:v for k,v in group.items()}
                qty=group[old]
            field,clean=parse_quest_edit('objectives',converted)
            patches={field:clean}
            details.append(f'{qid}: {mode} {old} x{qty} -> {new} x{qty}')
        candidate.setdefault('quest_edits',{}).setdefault(qid,{}).update(patches)
    service.validate(candidate)
    return candidate,tuple(details)


def plan_refs(session,service,mode,old,new,ids=()):
    _id(old);_id(new)
    if mode not in MODES:
        raise ValueError('TRYB: npc, surowiec, kill, collect lub talk.')
    if old==new:
        raise ValueError('ID musza sie roznic.')
    if not _valid_target(service,mode,new):
        raise ValueError('NOWE_ID nie istnieje w odpowiednim katalogu NPC/mobow/przedmiotow.')
    if mode == 'npc' and not _valid_target(service,mode,old):
        raise ValueError('STARE_ID NPC nie istnieje; sprawdz katalog NPC.')
    catalog = _effective(service)
    names=_names(service)
    matches = [qid for qid,q in sorted(catalog.items()) if _uses(q,mode,old,names)]
    if ids:
        if len(ids)>8 or len(set(ids))!=len(ids):
            raise ValueError('Wybierz 1-8 roznych questow.')
        for qid in ids:_id(qid)
        if any(qid not in matches for qid in ids):
            raise ValueError('Wybrany quest nie uzywa starego ID. Uzyj ref znajdz.')
        selected=list(ids)
    else:
        if len(matches)>8:
            raise ValueError(f'Znaleziono {len(matches)} questow. Podaj maksymalnie 8 ID.')
        selected=matches
    if not selected:
        raise ValueError('Brak questow do zmiany.')
    candidate,details = _rewrite(service,mode,old,new,selected,catalog,names)
    session.adminlive61_plan=(copy.deepcopy(service.draft),copy.deepcopy(service.active),candidate,details)
    return (f'QUEST REF PLAN: {len(details)} zmian; '+ '; '.join(details)+'. '
            'Bez zapisu. Zatwierdz: admin live questy ref zatwierdz POTWIERDZAM.')


def commit_refs(session,service):
    plan=getattr(session,'adminlive61_plan',None)
    if plan is None:
        raise ValueError('Brak planu.')
    before,active,candidate,details=plan
    if service.active!=active or service.draft!=before:
        session.adminlive61_plan=None
        raise ValueError('ACTIVE lub DRAFT zmienione od utworzenia planu.')
    service.validate(candidate)
    service.draft=copy.deepcopy(candidate)
    session.adminlive61_undo=(before,copy.deepcopy(candidate),active)
    session.adminlive61_plan=None
    return f'QUEST REF DRAFT: zapisano {len(details)} zmian. Bez publikacji i bez zmiany postepow graczy.'


def undo_refs(session,service):
    record=getattr(session,'adminlive61_undo',None)
    if record is None:
        raise ValueError('Brak operacji do cofniecia.')
    before,after,active=record
    if service.draft!=after or service.active!=active:
        raise ValueError('DRAFT/ACTIVE zmienione pozniej; odmowa cofniecia.')
    service.draft=copy.deepcopy(before)
    session.adminlive61_undo=None
    session.adminlive61_plan=None
    return 'QUEST REF COFNIETO: przywrocono DRAFT, ACTIVE bez zmian.'


async def dispatch_v61(session,group,raw):
    bits=str(raw or '').strip().split()
    if not ((group=='pomoc' and bits==['16']) or (group in ('questy','zadania') and bits[:1]==['ref'])):
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return True
    try:
        service=session.server.live_content_v1204
        if group=='pomoc': out=HELP
        elif bits[:2]==['ref','karta'] and len(bits)==3:out=ref_card(service,bits[2])
        elif bits[:2]==['ref','znajdz'] and len(bits) in (4,5):
            out=find_refs(service,bits[2],bits[3],bits[4] if len(bits)==5 else '1')
        elif bits[:2]==['ref','plan'] and len(bits)>=5:
            out=plan_refs(session,service,bits[2],bits[3],bits[4],bits[5:])
        elif bits==['ref','zatwierdz','POTWIERDZAM']:out=commit_refs(session,service)
        elif bits==['ref','cofnij','POTWIERDZAM']:out=undo_refs(session,service)
        elif bits==['ref','anuluj']:
            session.adminlive61_plan=None;out='QUEST REF: plan anulowany.'
        elif bits==['ref','status']:
            out=('QUEST REF: plan '+('gotowy' if getattr(session,'adminlive61_plan',None) else 'brak')+
                 ', cofanie '+('dostepne' if getattr(session,'adminlive61_undo',None) else 'brak')+'.')
        else:raise ValueError('Uzyj questy ref karta/znajdz/plan/zatwierdz/cofnij/anuluj/status; pomoc 16.')
    except (ValueError,KeyError,TypeError,AttributeError,OverflowError) as exc:
        out='ADMIN LIVE REF: '+str(exc)[:300]
    await session.send(out)
    return True
