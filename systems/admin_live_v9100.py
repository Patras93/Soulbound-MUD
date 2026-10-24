# -*- coding: utf-8 -*-
"""v91: one atomic, explicit stale quest prerequisite ID migration.

Only replaces nonexistent prerequisite IDs; never renames a quest or reassigns
player progress. Owner-chosen replacements must exist and be acyclic.
"""
from __future__ import annotations
import copy
import re
from systems.admin_live_v7100 import _plan, _commit, _undo
from systems.admin_live_integrity_v4900 import _effective
from systems.live_olc17_quest_dependencies import validate_dependency_graph

SLOT='adminlive9100_quest_migration_plan'
UNDO='adminlive9100_quest_migration_undo'
IDENT=re.compile(r'[A-Za-z0-9_-]{1,100}\Z',re.ASCII)
HELP=('ADMIN LIVE POMOC 49: rodowod nowa klasa mieszana plan NAZWA | BAZA | SKILLE | PASYW | BRON; '
      'dowolna z 22 bazowych klas, do 32 nowych klas, bez nowych skryptow. '
      'questy zaleznosci migracja skan [STRONA] - lista nieistniejacych ID poprzednikow; '
      'questy zaleznosci migracja plan STARE_ID | NOWE_ID; STARE2 | NOWE2 - zbiorcza '
      'zamiana do 16 nieistniejacych ID w calym katalogu, po wskazaniu prawidlowych zamiennikow. '
      'questy zaleznosci migracja zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj. '
      'Plan, potwierdzenie i cofniecie modyfikuja TYLKO DRAFT; normalne opublikowanie '
      'pozostaje osobna operacja. Blokuje cykle i modyfikacje warunkow aktywnych questow.')


def _check_id(value):
    if not isinstance(value,str) or not IDENT.fullmatch(value):
        raise ValueError('Podaj ID 1-100 ASCII: litery, cyfry, minus lub podkreslenie.')
    return value


def _refs(quest):
    single=quest.get('requires_quest')
    many=quest.get('requires_quests') or []
    if many is not None and not isinstance(many,(list,tuple)):
        raise ValueError('Wykryto uszkodzona liste requires_quests; popraw ja recznie.')
    if single is not None and not isinstance(single,str):
        raise ValueError('Wykryto uszkodzone requires_quest; popraw recznie.')
    result=[]
    if single:result.append(single)
    result.extend(many)
    return result


def _unresolved(catalog):
    results={}
    for qid,record in catalog.items():
        for dep in _refs(record):
            if dep not in catalog:
                results.setdefault(dep,set()).add(qid)
    return results


def scan(service,page='1'):
    if not page.isascii() or not page.isdecimal() or not 1<=len(page)<=4:
        raise ValueError('Strona: wpisz liczbe od 1 do 9999.')
    catalog=_effective(service)
    stale=_unresolved(catalog)
    pairs=sorted(stale.items())
    page=int(page); pages=max(1,(len(pairs)+7)//8)
    if not 1<=page<=pages:raise ValueError(f'Dostepne strony: 1..{pages}.')
    shown=pairs[(page-1)*8:page*8]
    lines=[f'{old}: {len(used)} questow, np. {", ".join(sorted(used)[:3])}' for old,used in shown]
    return (f'QUEST MIGRACJA SKAN {page}/{pages}: nieistniejacych poprzednikow {len(stale)}, '
            f'lacznie odwolania {sum(len(v) for v in stale.values())}. '+
            ('; '.join(lines) or 'BRAK')+'. Bez zmian, nie zgadujemy nowych ID.')


def _active_quests(service,qids):
    if not qids:return {}
    # Count only the specific dependency owners. Avoid oversized IN clauses.
    return {qid:int(service.conn.execute(
        "SELECT COUNT(*) FROM quests WHERE quest_id=? AND status='active'",(qid,)
    ).fetchone()[0]) for qid in qids}


def _mapping(raw,valid,missing):
    if not isinstance(raw,str) or not 1<=len(raw)<=1800:
        raise ValueError('Plan: wymagane 1-1800 znakow.')
    steps=[s.strip() for s in raw.split(';')]
    if not 1<=len(steps)<=16 or any(not step for step in steps):
        raise ValueError('Uzyj od 1 do 16 par STARE_ID | NOWE_ID oddzielonych srednikiem.')
    mapping={}
    for item in steps:
        if item.count('|')!=1:raise ValueError('Format: STARE_ID | NOWE_ID.')
        old,new=(_check_id(s.strip()) for s in item.split('|'))
        if old in mapping:raise ValueError('Powtorzony stary ID: '+old)
        if old in valid:raise ValueError(f'{old}: istnieje w katalogu; to nie jest nieaktualny ID. Uzyj edytora zaleznosci konkretnego questa.')
        if old not in missing:raise ValueError(f'{old}: zaden quest nie odwoluje sie do tego ID.')
        if new not in valid:raise ValueError(f'{new}: wskazany zamiennik nie istnieje w katalogu.')
        mapping[old]=new
    return mapping


def _stage(service,mapping):
    catalog=_effective(service)
    original=copy.deepcopy(service.draft)
    candidate=copy.deepcopy(original)
    changed={}
    for qid,old in catalog.items():
        old_single=old.get('requires_quest')
        old_multi=old.get('requires_quests') or []
        single=mapping.get(old_single,old_single)
        many=[mapping.get(dep,dep) for dep in old_multi]
        if single==old_single and many==list(old_multi):continue
        if qid==single or qid in many or len(many)!=len(set(many)) or (single and single in many):
            raise ValueError(f'{qid}: po migracji powstaje wlasna lub powtorzona zaleznosc.')
        patch={}
        if single!=old_single:patch['requires_quest']=single
        if many!=list(old_multi):patch['requires_quests']=many
        if qid in candidate.get('quests',{}):
            candidate['quests'][qid].update(patch)
        else:
            candidate.setdefault('quest_edits',{}).setdefault(qid,{}).update(patch)
        # An existing quest may carry additional overrides. Preserve those in DRAFT.
        if qid in candidate.get('quest_edits',{}) and qid in candidate.get('quests',{}):
            for field in patch:
                if field in candidate['quest_edits'][qid]:candidate['quest_edits'][qid][field]=patch[field]
        catalog[qid]={**old,**patch}
        changed[qid]=patch
    if not changed:raise ValueError('Plan niczego nie zmienia.')
    validate_dependency_graph(catalog)
    service.validate(candidate)
    return original,candidate,changed


def plan(session,service,raw):
    setattr(session,SLOT,None)
    catalog=_effective(service)
    old=_unresolved(catalog)
    mapping=_mapping(raw,set(catalog),old)
    original,candidate,changed=_stage(service,mapping)
    active={qid:num for qid,num in _active_quests(service,changed).items() if num}
    if active:
        preview=', '.join(f'{qid} ({num})' for qid,num in list(active.items())[:4])
        raise ValueError('Zmieniane questy sa aktywne u graczy: '+preview+'. Poczekaj, az zakoncza je przed publikacja.')
    _plan(session,SLOT,original,service.active,candidate,'QUEST MIGRACJA ID')
    return (f'QUEST MIGRACJA PLAN: {len(mapping)} brakujacych ID, poprawionych questow {len(changed)}. '
            +'; '.join(f'{old} -> {new}' for old,new in mapping.items())+
            '. Bez zapisu, graf wymagan i caly DRAFT zweryfikowane. '
            'questy zaleznosci migracja zatwierdz POTWIERDZAM.')


async def dispatch_v9100(session,group,raw):
    parts=str(raw or '').strip().split()
    matched=(group=='pomoc' and parts==['49']) or (
        group in ('questy','zadania') and parts[:2]==['zaleznosci','migracja'])
    if not matched:return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        service=session.server.live_content_v1204
        if group=='pomoc':message=HELP
        else:
            sub=parts[2:]
            if sub[:1]==['skan'] and len(sub) in (1,2):
                message=scan(service,sub[1] if len(sub)==2 else '1')
            elif sub[:1]==['plan'] and len(sub)>1:
                content=str(raw).split('migracja plan',1)[1].strip()
                message=plan(session,service,content)
            elif sub==['zatwierdz','POTWIERDZAM']:
                data=getattr(session,SLOT,None)
                if data:
                    before,active,candidate,_label=data
                    touched=set(candidate.get('quest_edits',{}))|set(candidate.get('quests',{}))
                    # Active-account guard is rechecked at confirmation, too.
                    changed={qid for qid in touched if candidate['quest_edits'].get(qid)!=before['quest_edits'].get(qid)
                             or candidate['quests'].get(qid)!=before['quests'].get(qid)}
                    if any(_active_quests(service,changed).values()):
                        raise ValueError('Quest zostal przyjety przez gracza od przygotowania planu; zatwierdzenie zablokowane.')
                message=_commit(session,service,SLOT,UNDO)
            elif sub==['cofnij','POTWIERDZAM']:
                message=_undo(session,service,SLOT,UNDO)
            elif sub==['anuluj']:
                setattr(session,SLOT,None);message='QUEST MIGRACJA: plan anulowany; bez zmian.'
            else:
                raise ValueError('Dostepne: skan, plan, zatwierdz POTWIERDZAM, cofnij POTWIERDZAM, anuluj.')
    except (ValueError,TypeError,KeyError,RuntimeError,AttributeError,OverflowError) as exc:
        message='ADMIN LIVE v91: '+str(exc)[:440]
    await session.send(message)
    return True
