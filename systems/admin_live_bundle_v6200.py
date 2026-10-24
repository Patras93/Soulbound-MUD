# -*- coding: utf-8 -*-
"""Multi-mode OLC quest reference transactions and high-level EQ/skill previews.

All edits are validated against the canonical LIVE OLC; writes are DRAFT only.
No wildcard mass edits, arbitrary Python, production DB writes or publication.
"""
from __future__ import annotations
import copy
import re
from types import SimpleNamespace
from systems.admin_live_integrity_v4900 import _effective
from systems.admin_live_quest_refs_v6100 import _rewrite as _ref_rewrite, _names, _valid_target
from systems.admin_live_quest_id_v6000 import _rewrite as _id_rewrite, _catalog_items, _catalog_mobs
from systems.admin_live_v5900 import _dependency_field, _creates_cycle
from systems.quest_equipment_v6200 import preview_quest_equipment_v6200
from core.classes_skills import CLASS_SKILLS
from systems.live_quest_olc_v1209 import parse_quest_edit, QUEST_EDIT_FIELDS

VALID=('npc','surowiec','kill','collect','talk','nagroda','cel','zaleznosc','pole')
_RX=re.compile(r'[A-Za-z0-9_-]{1,100}\Z')
HELP=('ADMIN LIVE POMOC 17: questy pakiet plan TRYB STARE NOWE ID [ID..] ; TRYB STARE NOWE ID. '
      'Tryby npc, surowiec, kill, collect, talk, nagroda, cel, zaleznosc. '
      'Do 16 operacji i 8 questow w jednym planie; ID sa obowiazkowe. '
      'NOWE: pole QUEST_ID POLE WARTOSC (np. pole temple_rats needed 3; pole temple_rats reward_stat_xp 500). '
      'questy pakiet zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj / status. '
      'eq quest ID_QUEST ID_PRZEDMIOTU - bez tworzenia przedmiotu. '
      'arena skille poziom BIEGLOSC [STRONA] - odblokowanie skilli wszystkich 22 klas; '
      'tylko odczyt, bez postaci i EXP. Arena walk nadal jest MODELEM, nie 1:1.')


def _id(value):
    if not _RX.fullmatch(str(value or '')):raise ValueError('ID: tylko litery, cyfry, _ i -, do 100 znakow.')
    return value


def _temporary(service,draft,defer_validation=False):
    # Staging cannot be required to be valid midway through a multi-field fix.
    # The COMPLETE plan is always validated before it becomes actionable.
    validator=(lambda _candidate: None) if defer_validation else service.validate
    return SimpleNamespace(active=service.active,draft=draft,validate=validator)


def _patch_one(service,draft,mode,old,new,qids,defer_validation=False):
    temp=_temporary(service,draft,defer_validation)
    catalog=_effective(temp)
    for qid in qids:
        _id(qid)
        if qid not in catalog:raise ValueError('Nieznany quest: '+qid)
    if mode not in ('pole','dopasuj') and old==new:raise ValueError('STARE i NOWE ID sa takie same.')
    if mode=='dopasuj':
        qid=qids[0]
        quest=catalog[qid]
        kind=quest.get('kind')
        if kind=='multi_objective':
            # Same source validator that gameplay/OLC uses for this quest kind.
            from systems.live_olc18_multi_objective import validate_objectives
            from data.mobs import MOB_TEMPLATES
            from data.items import ITEMS
            from systems.admin_live_quest_refs_v6100 import _npc_catalog
            mobs=set(MOB_TEMPLATES)|set(draft.get('mobs',{}))|set(service.active.get('mobs',{}))
            items=set(ITEMS)|set(draft.get('items',{}))|set(service.active.get('items',{}))
            npcs=set(_npc_catalog(temp))
            _,needed=validate_objectives(quest.get('objectives'),mobs,items,npcs)
        elif kind=='collect_resource_set':
            values=quest.get('resource_targets')
            if not isinstance(values,dict) or not 2<=len(values)<=8:
                raise ValueError('Zestaw musi miec od 2 do 8 surowcow.')
            if any(type(v) is not int or not 1<=v<=10000 for v in values.values()):
                raise ValueError('Nieprawidlowe ilosci surowcow.')
            if quest.get('target') not in values:
                raise ValueError('Najpierw wskaz docelowy surowiec przez pole ID target ID.')
            needed=sum(values.values())
        else:
            raise ValueError('Dopasuj: tylko multi_objective lub collect_resource_set.')
        if quest.get('needed')==needed:
            raise ValueError('Licznik juz jest prawidlowy.')
        candidate=copy.deepcopy(draft)
        candidate.setdefault('quest_edits',{}).setdefault(qid,{})['needed']=needed
        details=[f'{qid} needed: {quest.get("needed")} -> {needed}']
        temp.validate(candidate)
    elif mode=='pole':
        candidate=copy.deepcopy(draft);details=[]
        # Only fields already supported by the canonical live quest editor.
        field,value=parse_quest_edit(old,new)
        if field not in QUEST_EDIT_FIELDS:raise ValueError('Pole niedozwolone.')
        for qid in qids:
            before=catalog[qid].get(field)
            if before==value:raise ValueError(qid+': pole juz ma wskazana wartosc.')
            candidate.setdefault('quest_edits',{}).setdefault(qid,{})[field]=copy.deepcopy(value)
            details.append(f'{qid} {field}: {str(before)[:50]} -> {str(value)[:50]}')
        temp.validate(candidate)
    elif mode in ('npc','surowiec','kill','collect','talk'):
        if not _valid_target(temp,mode,new):
            raise ValueError('NOWE_ID nie istnieje lub ma nieodpowiedni typ.')
        if mode=='npc' and not _valid_target(temp,mode,old):
            raise ValueError('STARE_ID NPC nie istnieje; uzyj edycji pola giver.')
        candidate, details=_ref_rewrite(temp,mode,old,new,qids,catalog,_names(temp))
    elif mode in ('nagroda','cel'):
        for qid in qids:
            if (mode=='nagroda' and new not in _catalog_items(temp)) or (mode=='cel' and new not in (_catalog_mobs(temp) if catalog[qid].get('kind')=='kill' else _catalog_items(temp))):
                raise ValueError('NOWE_ID nie istnieje w katalogu dla: '+qid)
        candidate,details=_id_rewrite(temp,catalog,mode,old,new,qids)
    elif mode=='zaleznosc':
        if new not in catalog:raise ValueError('Nowa zaleznosc nie istnieje.')
        candidate=copy.deepcopy(draft);details=[];effective=copy.deepcopy(catalog)
        for qid in qids:
            patch=_dependency_field(temp,qid,old,new,catalog)
            if not patch:raise ValueError(qid+': brak wskazanej zaleznosci.')
            effective[qid].update(patch)
            candidate.setdefault('quest_edits',{}).setdefault(qid,{}).update(patch)
            for field,value in patch.items():
                details.append(f'{qid} {field}: {str(catalog[qid].get(field))[:60]} -> {str(value)[:60]}')
        for qid in qids:
            if _creates_cycle(effective,qid):raise ValueError('Cykl zaleznosci: '+qid)
        temp.validate(candidate)
    else:raise ValueError('Tryb: '+', '.join(VALID))
    return candidate,list(details)


def plan_bundle(session,service,spec):
    # Failed attempts must invalidate any previously prepared, potentially stale plan.
    session.adminlive62_plan=None
    spec=str(spec or '').strip()
    if not spec or len(spec)>2700:raise ValueError('Podaj plan, maks. 2700 znakow.')
    commands=[x.strip() for x in spec.split(';')]
    if not 1<=len(commands)<=16 or any(not x for x in commands):
        raise ValueError('Plan: 1-16 operacji oddzielonych srednikiem.')
    instructions=[];unique=set()
    for ordinal,command in enumerate(commands):
        parts=command.split()
        if parts and parts[0]=='dopasuj':
            if len(parts)!=2:raise ValueError('Dopasuj: dopasuj QUEST_ID.')
            if ordinal != len(commands)-1:raise ValueError('Dopasuj umiesc na koncu planu.')
            qid=_id(parts[1]);unique.add(qid)
            if len(unique)>8:raise ValueError('Maksymalnie 8 questow.')
            instructions.append(('dopasuj','', '',[qid]))
            continue
        if len(parts)<4:raise ValueError('Format: TRYB STARE NOWE QUEST_ID [QUEST_ID..].')
        mode,old,new,*qids=parts
        if mode not in VALID:raise ValueError('Nieznany tryb: '+mode)
        # Human-friendly order: pole QUEST_ID POLE WARTOSC.
        if mode=='pole':
            if len(qids)!=1:raise ValueError('pole wymaga QUEST_ID POLE WARTOSC.')
            qid,field,value=old,new,qids[0]
            _id(qid);_id(field)
            old,new,qids=field,value,[qid]
        else:
            _id(old);_id(new)
        if len(qids)>8 or len(set(qids))!=len(qids):raise ValueError('1-8 roznych ID w operacji.')
        for qid in qids:_id(qid)
        unique.update(qids)
        if len(unique)>8:raise ValueError('Plan moze obejmowac maksymalnie 8 roznych questow.')
        instructions.append((mode,old,new,qids))
    before=copy.deepcopy(service.draft);active=copy.deepcopy(service.active)
    candidate=copy.deepcopy(before);changes=[]
    for mode,old,new,qids in instructions:
        candidate,details=_patch_one(service,candidate,mode,old,new,qids,defer_validation=True)
        changes.extend(details)
    # Verify the FINAL state in one canonical OLC validation: no intermediate
    # invalid state is ever committed, even when count and goals change together.
    service.validate(candidate)
    # Canonical OLC checks direct self-references, but multiple valid IDs may
    # still make a cycle. Reject cycles INTRODUCED by this plan.
    from systems.admin_live_v5900 import _creates_cycle
    state=_effective(_temporary(service,candidate))
    old_state=_effective(service)
    for qid in unique:
        before_q,after_q=old_state[qid],state[qid]
        depfields=('requires_quest','requires_quests')
        if any(before_q.get(key)!=after_q.get(key) for key in depfields):
            if _creates_cycle(state,qid):
                raise ValueError('Plan wprowadza cykl zaleznosci: '+qid)

    session.adminlive62_plan=(before,active,copy.deepcopy(candidate),tuple(changes))
    return (f'QUEST PAKIET PLAN: {len(instructions)} operacji, {len(unique)} questow, '
        f'{len(changes)} pol; '+'; '.join(changes)[:1600]+'. '
        'NIC NIE ZAPISANO. questy pakiet zatwierdz POTWIERDZAM. Tylko DRAFT.')


def commit_bundle(session,service):
    plan=getattr(session,'adminlive62_plan',None)
    if plan is None:raise ValueError('Brak planu pakietu.')
    before,active,candidate,changes=plan
    if service.active!=active or service.draft!=before:
        session.adminlive62_plan=None
        raise ValueError('DRAFT/ACTIVE zmieniony po planie. Nie nadpisze cudzych zmian.')
    service.validate(candidate)
    service.draft=copy.deepcopy(candidate)
    session.adminlive62_undo=(copy.deepcopy(before),copy.deepcopy(candidate),copy.deepcopy(active))
    session.adminlive62_plan=None
    return f'QUEST PAKIET: {len(changes)} zmian zapisano tylko DRAFT. Bez publikacji, SQLite i postepow.'


def undo_bundle(session,service):
    record=getattr(session,'adminlive62_undo',None)
    if record is None:raise ValueError('Brak pakietu do cofniecia.')
    before,after,active=record
    if service.draft!=after or service.active!=active:
        raise ValueError('DRAFT/ACTIVE zmieniono pozniej; odmowa cofniecia.')
    service.draft=copy.deepcopy(before)
    session.adminlive62_plan=None;session.adminlive62_undo=None
    return 'QUEST PAKIET COFNIETO: przywrocono DRAFT. LIVE, SQLite i postepy bez zmian.'


def skill_unlock_audit(raw,page='1'):
    raw=str(raw or '')
    if not raw.isascii() or not raw.isdecimal() or len(raw)>10 or not 1<=int(raw)<=1_000_000_000:
        raise ValueError('Bieglosc: poziom od 1 do 1000000000.')
    from core.live_level_caps_v5200 import cap,effective_number
    mastery=int(raw)
    limit=effective_number(cap('bieglosc'))
    if mastery>limit:raise ValueError(f'Bieglosc ponad obecny limit {limit}. Zmien admin live limity.')
    if not str(page).isascii() or not str(page).isdecimal() or len(str(page))>3:
        raise ValueError('STRONA: 1-3.')
    p=int(page)
    if not 1<=p<=3:raise ValueError('STRONA: 1-3.')
    lines=[];total=0;unlocked=0
    for name in sorted(CLASS_SKILLS):
        skills=CLASS_SKILLS[name];available=sum(int(s.get('unlock',1) or 1)<=mastery for s in skills)
        total+=len(skills);unlocked+=available
        lines.append(f'{name} {available}/{len(skills)}')
    return (f'ARENA SKILLE POZIOM {mastery}: {unlocked}/{total} skilli z {len(lines)} klas; '
            f'strona {p}/3; '+'; '.join(lines[(p-1)*8:p*8])+'. '
            'Katalog produkcyjny, nie symulacja skutkow walki. Bez zmian HP, EXP i SQL.')


async def dispatch_v62(session,group,raw):
    bits=str(raw or '').strip().split()
    if not ((group=='pomoc' and bits==['17']) or
            (group in ('questy','zadania') and bits[:1]==['pakiet']) or
            (group=='eq' and bits[:1]==['quest']) or
            (group=='arena' and bits[:2]==['skille','poziom'])):
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        service=session.server.live_content_v1204
        if group=='pomoc':out=HELP
        elif group in ('questy','zadania'):
            if bits[:2]==['pakiet','plan']:
                out=plan_bundle(session,service,str(raw).split(None,2)[2] if len(bits)>2 else '')
            elif bits==['pakiet','zatwierdz','POTWIERDZAM']:
                out=commit_bundle(session,service)
            elif bits==['pakiet','cofnij','POTWIERDZAM']:
                out=undo_bundle(session,service)
            elif bits==['pakiet','anuluj']:
                session.adminlive62_plan=None;out='QUEST PAKIET: plan anulowany.'
            elif bits==['pakiet','status']:
                out=('QUEST PAKIET: '+('plan przygotowany' if getattr(session,'adminlive62_plan',None) else 'brak planu')+
                     '; cofanie '+('mozliwe' if getattr(session,'adminlive62_undo',None) else 'niedostepne')+'.')
            else:raise ValueError(HELP)
        elif group=='eq':
            if len(bits)!=3:raise ValueError('Uzyj eq quest QUEST_ID PRZEDMIOT_ID.')
            catalog=_effective(service)
            if bits[1] not in catalog:raise ValueError('Quest o podanym ID nie istnieje.')
            out=preview_quest_equipment_v6200(bits[2],catalog[bits[1]])
        else:
            if len(bits) not in (3,4):raise ValueError('arena skille poziom POZIOM [STRONA].')
            out=skill_unlock_audit(bits[2],bits[3] if len(bits)==4 else '1')
    except (ValueError,TypeError,KeyError,OverflowError,AttributeError) as exc:
        out='ADMIN LIVE V62: '+str(exc)[:280]
    await session.send(out)
    return True
