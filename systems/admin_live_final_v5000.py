# -*- coding: utf-8 -*-
"""v50 owner-only transaction-safe quest DRAFT corrections & UOSS LAB checks.

No real player methods, SQL mutations, reward distribution, published OLC writes,
or world spawns. Only exact, explicitly verified structural corrections are proposed.
"""
from __future__ import annotations
import copy
from collections import Counter
from types import SimpleNamespace
from systems.admin_live_integrity_v4900 import _effective, _issues, _integer
from systems.admin_live_expansion_v4800 import KINDS, _page
from systems.admin_guardian6_v4000 import _requirements
from systems.live_quest_olc_v1209 import parse_quest_edit
from systems.admin_guardian11_v4500 import _arena, _turn
from systems.admin_live_ultimate_v4600 import _party, _party_one_turn, _int

HELP7 = (
 'ADMIN LIVE POMOC 7/7: questy korekta lista [STRONA] - lista pewnych poprawek; '
 'questy korekta plan ID [ID ...] - podglad zmian 1-8 questow; '
 'questy korekta zastosuj POTWIERDZAM - atomowy zapis TYLKO DRAFT; '
 'questy korekta cofnij POTWIERDZAM - przywroc poprzedni DRAFT; '
 'questy korekta anuluj - porzuc plan; questy cykle [STRONA] - graf zaleznosci; '
 'questy pokrycie - 18 typow; arena scenariusze [1-12] - 3 warianty na kopiach. '
 'ID celu, NPC, nagrody, skill i faktyczna walka UOSS NIE sa automatycznie zgadywane. '
 'Publikacja zawsze osobno: admin live sprawdz, porownaj, aktywuj POTWIERDZAM.'
)

_COUNT_KINDS=frozenset({
 'collect','collect_category','collect_distinct_category','collect_resource',
 'collect_resource_set','craft_set','kill','party_contract','profession_action',
})

def _fixable(qid, record, catalog):
    """Conservative: repair only explicit invalid *present* numeric fields.

    No inference for missing needed, no NPC/mob guessing; on unknown IDs
    validation of a candidate is delegated to canonical OLC validator.
    """
    proposed={}
    errors,_=_issues(qid,record,catalog)
    if 'needed' in record and record.get('kind') in _COUNT_KINDS:
        num=_integer(record['needed'])
        if num is not None and num<1:
            proposed['needed']=parse_quest_edit('needed','1')[1]
    if 'repeat_cooldown' in record:
        num=_integer(record['repeat_cooldown'])
        if num is not None and num<0:
            proposed['repeat_cooldown']=parse_quest_edit('repeat_cooldown','0')[1]
    # Preserve all other errors for honest review; no automatic economy edit.
    return proposed,errors

def _fix_rows(service):
    catalog=_effective(service)
    return [(qid,q,patch,errors) for qid,q in sorted(catalog.items())
            for patch,errors in [_fixable(qid,q,catalog)] if patch]

def _fix_list(service,raw='1'):
    rows=_fix_rows(service)
    page,pages=_page(raw,len(rows))
    desc=[]
    for qid,q,patch,errors in rows[(page-1)*8:page*8]:
        changes=', '.join(f'{k}: {q[k]} -> {v}' for k,v in patch.items())
        desc.append(f'{qid}: {changes}; inne sygnaly {max(0,len(errors)-len(patch))}')
    return (f'QUEST KOREKTA LISTA: {len(rows)} kandydatow, strona {page}/{pages}; '
            +('; '.join(desc) or 'brak na tej stronie')+
            '. Bez zmian; wybierz ID w questy korekta plan. Nie poprawia nagrod/ID bez decyzji.')

def _repair_plan(session,service,ids):
    if not 1<=len(ids)<=8 or len(ids)!=len(set(ids)):
        raise ValueError('KOREKTA PLAN: podaj od 1 do 8 roznych ID questow.')
    if any(not value or len(value)>100 or not value.replace('_','').replace('-','').isalnum() for value in ids):
        raise ValueError('KOREKTA PLAN: niepoprawne ID.')
    catalog=_effective(service)
    candidate=copy.deepcopy(service.draft)
    changes=[]
    for qid in ids:
        if qid not in catalog: raise ValueError('Nie znaleziono ID '+qid)
        patch,errors=_fixable(qid,catalog[qid],catalog)
        if not patch: raise ValueError(f'{qid}: brak obslugiwanych poprawek liczbowych. Popraw recznie.')
        # DRAFT is a complete editable snapshot, no server/state mutation yet.
        for field,value in patch.items():
            candidate['quest_edits'].setdefault(qid,{})[field]=value
            changes.append((qid,field,catalog[qid][field],value))
    # Must validate ALL affected quests before storing plan; invalid legacy
    # content is rejected rather than bypassing the authoritative validator.
    service.validate(candidate)
    session.adminlive50_repair_plan=(copy.deepcopy(service.draft), copy.deepcopy(service.active),candidate,tuple(changes))
    entries='; '.join(f'{qid} {field}: {old} -> {new}' for qid,field,old,new in changes)
    return (f'QUEST KOREKTA PLAN: {len(ids)} questow, {len(changes)} pol; {entries}. '
            'Zmienia przyszle wymagania w zadaniach dopiero po osobnej publikacji OLC. '
            'Nic nie zapisano. Zastosuj: admin live questy korekta zastosuj POTWIERDZAM.')

def _repair_apply(session,service):
    record=getattr(session,'adminlive50_repair_plan',None)
    if record is None:raise ValueError('Brak planu. Uzyj questy korekta plan ID.')
    before,active,candidate,changes=record
    if service.draft!=before or service.active!=active:
        session.adminlive50_repair_plan=None
        raise ValueError('DRAFT lub ACTIVE zmienione po przygotowaniu planu. Przygotuj nowy.')
    service.validate(candidate)
    session.adminlive50_undo=(copy.deepcopy(before),copy.deepcopy(candidate),copy.deepcopy(active))
    service.draft=copy.deepcopy(candidate)
    session.adminlive50_repair_plan=None
    return (f'QUEST KOREKTA DRAFT: {len(changes)} pol w {len({x[0] for x in changes})} questach. '
            'Bez publikacji, bez zmian postepow postaci i nagrod. '
            'Sprawdz: admin live sprawdz / porownaj; publikacja oddzielnie.')

def _repair_undo(session,service):
    rec=getattr(session,'adminlive50_undo',None)
    if not rec:raise ValueError('Brak zapisanej korekty do cofniecia.')
    before,after,active=rec
    if service.draft!=after or service.active!=active:
        raise ValueError('DRAFT lub ACTIVE zmienione pozniej; odmowa cofania obcych zmian.')
    service.draft=copy.deepcopy(before)
    session.adminlive50_undo=None
    session.adminlive50_repair_plan=None
    return 'QUEST KOREKTA COFNIETA: odtworzono DRAFT. Bez zmian opublikowanej gry.'

def _graph_report(service,raw='1'):
    """Iterative whole-catalogue three-colour DFS, bounded in graph edges."""
    catalog=_effective(service)
    deps={key: tuple(d for d in _requirements(quest) if isinstance(d,str))
          for key,quest in catalog.items()}
    known=set(catalog)
    missing=sorted({(key,target) for key,refs in deps.items() for target in refs if target not in known})
    # Tarjan SCC, recursive only to depth 1000: use explicit stack two-pass Kosaraju.
    graph={key:[ref for ref in refs if ref in known] for key,refs in deps.items()}
    reversed_graph={key:[] for key in graph}
    for key,refs in graph.items():
        for ref in refs:reversed_graph[ref].append(key)
    seen=set();order=[]
    for start in sorted(graph):
        if start in seen:continue
        stack=[(start,False)]
        while stack:
            node,exit_node=stack.pop()
            if exit_node:
                order.append(node);continue
            if node in seen:continue
            seen.add(node)
            stack.append((node,True))
            for dest in graph[node]:
                if dest not in seen:stack.append((dest,False))
    visited=set();cycles=[]
    for start in reversed(order):
        if start in visited:continue
        component=[];stack=[start];visited.add(start)
        while stack:
            node=stack.pop();component.append(node)
            for dest in reversed_graph[node]:
                if dest not in visited:visited.add(dest);stack.append(dest)
        if len(component)>1 or (component and component[0] in graph[component[0]]):
            cycles.append(tuple(sorted(component)))
    cycles.sort()
    rows=['cykl '+', '.join(nodes[:8])+(' (...)' if len(nodes)>8 else '') for nodes in cycles]
    rows+=['brak ID '+src+' -> '+dest for src,dest in missing]
    p,pages=_page(raw,len(rows))
    return (f'QUEST CYKLE: {len(catalog)} questow, cykle {len(cycles)}, '
            f'brakujace ID {len(missing)}, strona {p}/{pages}; '
            +('; '.join(rows[(p-1)*8:p*8]) or 'brak problemow')+
            '. Analiza tylko wskazanych relacji requires_quest(s), nie test wykonania.')

def _coverage(service):
    catalog=_effective(service)
    counts=Counter(str(q.get('kind','brak')) for q in catalog.values())
    return (f'QUEST POKRYCIE: {len(catalog)} questow, {len(KINDS)} obslugiwanych typow w audycie; '
        +'; '.join(f'{k} {counts[k]}' for k in KINDS)+'. '
         'Strukturalny audyt nie sprawdza rzeczywistych wyzwalaczy, NPC w pokoju ani postepu na zywo.')

def _scenario(session,steps='5'):
    steps=_int(steps,1,12,'tury')
    start=_arena(session)
    if start['finished']:raise ValueError('Arena zakonczona.')
    outputs=[]
    for strategy in ('atak','obrona','druzyna'):
        clone=SimpleNamespace(guardian7_lab=copy.deepcopy(start))
        n=0
        for _ in range(steps):
            if clone.guardian7_lab['finished']:break
            if strategy=='druzyna' and _party(clone.guardian7_lab):
                _party_one_turn(clone)
            else:
                _turn(clone,'obrona' if strategy=='obrona' else 'atak','boss')
            n+=1
        end=clone.guardian7_lab
        outputs.append(f'{strategy}: {n} tur, boss HP {end["boss"].hp}, '
                       f'lider HP {end["hero_hp"]}, zadane {end["total_dealt"]}, '
                       f'otrzymane {end["total_taken"]}')
    return ('ARENA SCENARIUSZE, identyczne RNG poczatkowe: '+'; '.join(outputs)+'. '
            'Tylko izolowany LAB, bez zmian areny, postaci, SQL i RNG serwera. '
            'Nie oznacza produkcyjnej zgodnosci UOSS 1:1.')

async def dispatch_v50(session,group,raw):
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    args=str(raw or '').split()
    try:
        if group=='pomoc' and args==['7']:answer=HELP7
        elif group in ('questy','zadania') and args:
            service=session.server.live_content_v1204
            if args[:2]==['korekta','lista'] and len(args) in (2,3):
                answer=_fix_list(service,args[2] if len(args)==3 else '1')
            elif args[:2]==['korekta','plan'] and len(args)>=3:
                answer=_repair_plan(session,service,args[2:])
            elif args==['korekta','zastosuj','POTWIERDZAM']:
                answer=_repair_apply(session,service)
            elif args==['korekta','cofnij','POTWIERDZAM']:
                answer=_repair_undo(session,service)
            elif args==['korekta','anuluj']:
                session.adminlive50_repair_plan=None
                answer='QUEST KOREKTA: plan anulowany. Zero zmian.'
            elif args and args[0]=='korekta':
                raise ValueError('Korekta: lista [STRONA] / plan ID ... / zastosuj POTWIERDZAM / cofnij POTWIERDZAM / anuluj.')
            elif args[0]=='cykle' and len(args) in (1,2):
                answer=_graph_report(service,args[1] if len(args)==2 else '1')
            elif args==['pokrycie']:answer=_coverage(service)
            else:return False
        elif group=='arena' and args and args[0]=='scenariusze' and len(args) in (1,2):
            answer=_scenario(session,args[1] if len(args)==2 else '5')
        else:return False
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError) as exc:
        answer='ADMIN LIVE: '+str(exc)[:350]
    await session.send(answer)
    return True
