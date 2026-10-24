# -*- coding: utf-8 -*-
"""v59: high-level world gear preview and explicit quest dependency ID repair.

Actual world monster gear scaling runs through the existing v56 post-roll hook.
No quest is published here; the existing OLC validator is authoritative.
"""
from __future__ import annotations
import copy
import re
from systems.admin_live_integrity_v4900 import _effective
from systems.live_quest_olc_v1209 import parse_quest_edit
from systems.endless_loot_v5600 import preview_normal_equipment_drop_v5600

_ID=re.compile(r"[a-zA-Z0-9_\-]{1,100}\Z")
HELP=("ADMIN LIVE POMOC 14: eq swiat POZIOM ID_PRZEDMIOTU [boss/elite] "
      "- prognoza zwyklego dropu EQ z moba ponad poziomem 800; "
      "questy zamien plan STARE_ID NOWE_ID [QUEST_ID ...] "
      "- wskaz poprawne ID poprzedniego zadania; maksymalnie 8 questow. "
      "questy zamien zatwierdz POTWIERDZAM - tylko DRAFT; "
      "questy zamien cofnij POTWIERDZAM; questy zamien anuluj/status. "
      "Nie zgadujemy ID, nie publikujemy automatycznie. "
      "UOSS/unikaty i stare szanse dropu pozostaja bez zmian.")

def world_equipment_preview(level,item_id,rank=''):
    raw=str(level)
    if not raw.isascii() or not raw.isdecimal() or len(raw)>10 or not 1<=int(raw)<=1_000_000_000:
        raise ValueError('Poziom swiata: liczba 1..1000000000.')
    if not _ID.fullmatch(str(item_id)):raise ValueError('Nieprawidlowy identyfikator EQ.')
    if rank not in ('','boss','elite'):raise ValueError('Typ: boss lub elite.')
    template={'level':int(raw)}
    if rank:template[rank]=True
    result=preview_normal_equipment_drop_v5600(item_id,template)
    return 'EQ SWIAT '+result+(' Poziom moba '+raw+'.' if int(raw)>800 else ' Wymagany poziom moba ponad 800.')

def _dependency_field(service,qid,old,new,catalog=None):
    quest=(catalog if catalog is not None else _effective(service))[qid]
    updates={}
    if quest.get('requires_quest')==old:
        updates['requires_quest']=parse_quest_edit('requires_quest',new)[1]
    more=quest.get('requires_quests')
    if isinstance(more,(list,tuple)) and old in more:
        values=[new if x==old else x for x in more]
        updates['requires_quests']=parse_quest_edit('requires_quests',values)[1]
    return updates

def _creates_cycle(catalog,qid):
    # Check only whether updated qid can reach itself through prerequisites.
    waiting=[qid];seen=set()
    while waiting:
        node=waiting.pop()
        if node in seen:continue
        seen.add(node)
        rec=catalog.get(node,{})
        edges=[]
        if isinstance(rec.get('requires_quest'),str):edges.append(rec['requires_quest'])
        if isinstance(rec.get('requires_quests'),(list,tuple)):edges.extend(rec['requires_quests'])
        for dest in edges:
            if dest==qid:return True
            if dest in catalog and dest not in seen:waiting.append(dest)
    return False

def plan_replace_dependency(session,service,old,new,ids=()):
    if not _ID.fullmatch(old) or not _ID.fullmatch(new) or old==new:
        raise ValueError('Podaj dwa rozne ID: STARE_ID NOWE_ID.')
    catalog=_effective(service)
    if new not in catalog:raise ValueError('NOWE_ID nie istnieje. Znajdz w admin live questy szukaj.')
    matches=[qid for qid in sorted(catalog) if _dependency_field(service,qid,old,new,catalog)]
    if ids:
        if len(ids)>8 or len(set(ids))!=len(ids) or any(not _ID.fullmatch(x) for x in ids):
            raise ValueError('Podaj 1..8 roznych, poprawnych ID questow.')
        if any(qid not in matches for qid in ids):
            raise ValueError('Wskazany quest nie uzywa STARE_ID w zaleznosciach.')
        selected=list(ids)
    else:
        if len(matches)>8:
            raise ValueError(f'Znaleziono {len(matches)} questow. Podaj maksymalnie 8 ID na jedna operacje.')
        selected=matches
    if not selected:raise ValueError('Nie znaleziono zadan zależnych od STARE_ID.')
    before=copy.deepcopy(service.draft);active=copy.deepcopy(service.active)
    candidate=copy.deepcopy(before);effective=copy.deepcopy(catalog)
    changed=[]
    for qid in selected:
        patch=_dependency_field(service,qid,old,new,catalog)
        updated=dict(effective[qid]);updated.update(patch);effective[qid]=updated
        for field,value in patch.items():
            candidate.setdefault('quest_edits',{}).setdefault(qid,{})[field]=value
            changed.append(f'{qid} {field}: {str(catalog[qid].get(field))[:95]} -> {str(value)[:95]}')
    for qid in selected:
        if _creates_cycle(effective,qid):raise ValueError('Nowa zaleznosc utworzylaby cykl dla '+qid)
    service.validate(candidate)
    # Reuse v51 transaction with isolation; do NOT overwrite user's separate v51 plan.
    session.adminlive59_plan=(before,active,candidate,tuple(changed))
    return (f'QUEST ZAMIEN PLAN: {len(selected)} questow, {len(changed)} pol. '+
            '; '.join(changed)+'. Bez zapisu. Zatwierdz: admin live questy zamien zatwierdz POTWIERDZAM.')

def commit_replace_dependency(session,service):
    plan=getattr(session,'adminlive59_plan',None)
    if not plan:raise ValueError('Brak planu zamiany.')
    before,active,candidate,changed=plan
    if service.active!=active or service.draft!=before:
        session.adminlive59_plan=None
        raise ValueError('ACTIVE/DRAFT zmienil sie od planu. Ponow planowanie.')
    service.validate(candidate)
    service.draft=copy.deepcopy(candidate)
    session.adminlive59_undo=(before,copy.deepcopy(candidate),active)
    session.adminlive59_plan=None
    return f'QUEST ZAMIEN DRAFT: zmieniono {len(changed)} pol. Bez publikacji i SQLite. Sprawdz / porownaj / aktywuj osobno.'

def undo_replace_dependency(session,service):
    record=getattr(session,'adminlive59_undo',None)
    if not record:raise ValueError('Nie ma zamiany do cofniecia.')
    before,after,active=record
    if service.draft!=after or service.active!=active:
        raise ValueError('DRAFT/ACTIVE zmieniony pozniej; odmowa cofania cudzych zmian.')
    service.draft=copy.deepcopy(before)
    session.adminlive59_undo=None
    session.adminlive59_plan=None
    return 'QUEST ZAMIEN COFNIETO: DRAFT przywrocony; ACTIVE i SQLite bez zmian.'

async def dispatch_v59(session,group,raw):
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    bits=str(raw or '').strip().split()
    try:
        if group=='pomoc' and bits==['14']:
            result=HELP
        elif group=='eq' and bits and bits[0]=='swiat':
            if len(bits) not in (3,4):raise ValueError('Uzyj: admin live eq swiat 901 leather_vest [boss/elite].')
            result=world_equipment_preview(bits[1],bits[2],bits[3] if len(bits)==4 else '')
        elif group in ('questy','zadania') and bits and bits[0]=='zamien':
            if len(bits)>=4 and bits[1]=='plan':
                result=plan_replace_dependency(session,session.server.live_content_v1204,bits[2],bits[3],bits[4:])
            elif bits==['zamien','zatwierdz','POTWIERDZAM']:
                result=commit_replace_dependency(session,session.server.live_content_v1204)
            elif bits==['zamien','cofnij','POTWIERDZAM']:
                result=undo_replace_dependency(session,session.server.live_content_v1204)
            elif bits==['zamien','anuluj']:
                session.adminlive59_plan=None;result='QUEST ZAMIEN: plan anulowany.'
            elif bits==['zamien','status']:
                result=('QUEST ZAMIEN: plan '+('gotowy' if getattr(session,'adminlive59_plan',None) else 'brak')+
                        ', cofanie '+('dostepne' if getattr(session,'adminlive59_undo',None) else 'brak')+'.')
            else:raise ValueError('Uzyj: zamien plan STARE NOWE [ID..] / zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj / status.')
        else:return False
    except (ValueError,TypeError,AttributeError,OverflowError) as exc:
        result='ADMIN LIVE V59: '+str(exc)[:280]
    await session.send(result)
    return True
