# -*- coding: utf-8 -*-
"""Admin Guardian 6.0: bounded owner-only review and atomic DRAFT authoring.

Never issues rewards, touches player progress, spawns monsters or publishes OLC.
All mutations go through the existing LiveContentV1204 validation pipeline.
"""
import copy
import re
from collections import deque, Counter
from data.quests import QUESTS
from data.mobs import MOB_TEMPLATES
from data.items import ITEMS
from systems.live_quest_olc_v1209 import parse_quest_edit, STAT_XP_FIELDS_V3900
from systems.admin_guardian5_v3900 import _quest, _effective_reward, _boss_metadata, STAT_LABELS
from systems.admin_guardian4_v3800 import _area_rooms, _area_report, _REVERSE, _arena_projection
from systems.admin_guardian2_v3600 import resolve_mob, _audit

FIELDS = ('reward_stat_xp', 'reward_stat_strength', 'reward_stat_dexterity',
          'reward_stat_constitution', 'reward_stat_intelligence',
          'reward_stat_willpower', 'reward_stat_charisma')
HELP = (
    'GUARDIAN6 v40: nagrody plan ID | WSPOLNY | SILA | ZRECZNOSC | KONDYCJA | INTELIGENCJA | WOLA | CHARYZMA; '
    'nagrody zestaw ID | WSPOLNY | SILA | ZRECZNOSC | KONDYCJA | INTELIGENCJA | WOLA | CHARYZMA | POTWIERDZAM; '
    'nagrody katalog FRAZA [STRONA]; questy audyt FRAZA [STRONA]; '
    'questy zaleznosci ID; questy propozycja ID; '
    'questy popraw ID needed LICZBA POTWIERDZAM; '
    'kraina dostepnosc ID; arena analiza MOB_ID HP_GRACZA ATAK [MAX_TUR]; '
    'olc preflight; status; pomoc. '
    'Zmiany tylko DRAFT, publikacja osobno: admin live sprawdz / porownaj / aktywuj POTWIERDZAM. '
    'Wszystkie kwoty sa bazowe, EXP Bank i skalowanie pozostaja. '
    'Arena: statyczna prognoza, nie prawdziwe AI/UOSS. '
    'Wpisz auto w miejscu dowolnej liczby, aby usunac nadpisanie tego pola.'
)


def _combined(service):
    result = dict(QUESTS)
    result.update(service.draft.get('quests', {}))
    return result


def _match(quests, phrase):
    if not 1 <= len(phrase) <= 70 or any(ord(x) < 32 for x in phrase):
        raise ValueError('Wpisz fraze 1-70 znakow bez znakow sterujacych.')
    folded=phrase.casefold()
    return [(k,v) for k,v in quests.items() if folded in k.casefold() or folded in str(v.get('name','')).casefold()]


def _page(value):
    if not re.fullmatch(r'[0-9]{1,5}',str(value)):
        raise ValueError('Strona musi byc dodatnia liczba calkowita.')
    number=int(value)
    if not 1 <= number <= 10000: raise ValueError('Strona 1-10000.')
    return number


def _matching_page(service,phrase,page):
    matches=sorted(_match(_combined(service),phrase))
    p=_page(page)
    if matches and (p-1)*12>=len(matches):raise ValueError('Strona poza zakresem.')
    return matches[(p-1)*12:p*12],len(matches),p


def _reward_catalog(service,phrase,page):
    rows,total,p=_matching_page(service,phrase,page)
    if not rows:return 'NAGRODY KATALOG: brak questow dla tej frazy.'
    output=[]
    for qid,base in rows:
        active=service.active.get('quest_edits',{}).get(qid,{})
        common,values=_effective_reward(base,active)
        individual=sum(k in active for k in STAT_XP_FIELDS_V3900.values())
        output.append(f'{qid}: {str(base.get("name",qid))[:65]}; wspolny {common}, osobne {individual}/6')
    return (f'NAGRODY KATALOG: {total} wynikow, strona {p}/{max(1,(total+11)//12)}. '
            +'; '.join(output)+'. Tylko odczyt; wartosci bazowe.')


def _batch_fields(spec):
    bits=[v.strip() for v in spec.split('|')]
    if len(bits)!=8:raise ValueError('Uzycie: QUEST_ID | WSPOLNY | SILA | ZRE | KON | INT | WOLA | CHAR.')
    qid=bits[0]
    if not re.fullmatch(r'[A-Za-z0-9_\-]{1,100}',qid):
        raise ValueError('Nieprawidlowy identyfikator questa.')
    changes=[]
    for field,value in zip(FIELDS,bits[1:]):
        if value.casefold() in ('auto','automatyczny'):
            changes.append((field,'auto'))
        else:
            canonical,amount=parse_quest_edit(field,value)
            changes.append((field,str(amount)))
    return qid,changes


def _batch_candidate(service, qid, changes):
    _quest(service,qid)
    candidate=copy.deepcopy(service.draft)
    active_record=candidate['quest_edits'].get(qid)
    for alias, value in changes:
        field,_=parse_quest_edit(alias,'0')
        if value=='auto':
            if active_record is not None:
                active_record.pop(field,None)
                if not active_record:
                    candidate['quest_edits'].pop(qid,None)
        else:
            _field,parsed=parse_quest_edit(alias,value)
            active_record=candidate['quest_edits'].setdefault(qid,{})
            active_record[_field]=parsed
    service.validate(candidate)
    return candidate


def _batch(service,spec,commit=False):
    qid,changes=_batch_fields(spec)
    candidate=_batch_candidate(service,qid,changes)
    base=_quest(service,qid)
    before_common,before=_effective_reward(base,service.draft.get('quest_edits',{}).get(qid,{}))
    after_common,after=_effective_reward(base,candidate['quest_edits'].get(qid,{}))
    if commit:
        service.draft=candidate  # validated complete snapshot, atomic on success
    difference=[f'wspolny {before_common}->{after_common}']
    difference.extend(f'{STAT_LABELS[k]} {before[k]}->{after[k]}' for k in STAT_XP_FIELDS_V3900)
    return (f'NAGRODY {"DRAFT USTAWIONY" if commit else "PLAN BEZ ZMIAN"} {qid}: '
            +'; '.join(difference)+'. Bazowe EXP. '
            +('Nie opublikowano. Sprawdz i aktywuj przez admin live.' if commit
              else 'Wpisz nagrody zestaw z ta sama lista i POTWIERDZAM.'))


def _requirements(q):
    edges=[]
    simple=q.get('requires_quest')
    if isinstance(simple,str) and simple: edges.append(simple)
    more=q.get('requires_quests') or []
    if isinstance(more,(list,tuple)):
        edges.extend(v for v in more if isinstance(v,str) and v)
    return list(dict.fromkeys(edges))


def _dependencies(service,qid):
    quests=_combined(service)
    _quest(service,qid)
    qid=str(qid)
    visited=set();stack=[(qid,(qid,))];missing=[];cycles=[];edges=0
    while stack and len(visited)<200:
        current,path=stack.pop()
        visited.add(current)
        for nxt in _requirements(quests[current]):
            edges+=1
            if nxt not in quests:missing.append(f'{current}->{nxt}')
            elif nxt in path:cycles.append(' -> '.join((path+(nxt,))[-12:]))
            elif nxt not in visited and len(path)<32:
                stack.append((nxt,path+(nxt,)))
    first=_requirements(quests[qid]);short=', '.join(first[:15]) or 'brak'
    return (f'QUEST ZALEZNOSCI {qid}: bezposrednie {len(first)} [{short}]; '
            f'sprawdzono {len(visited)} questow, {edges} relacji; '
            f'brakujace {len(missing)} '+('; '.join(missing[:5]) or 'brak')+'; '
            f'cykle {len(cycles)} '+('; '.join(cycles[:3]) or 'brak')+'. '
            'Tylko statyczne pola requires_quest/requires_quests; bez zmian.')


def _signals(service,qid,base):
    q=dict(base)
    q.update(service.draft.get('quest_edits',{}).get(qid,{}))
    known=_combined(service)
    results=[]
    kind=q.get('kind')
    target=q.get('target')
    if kind=='kill' and target not in MOB_TEMPLATES and target not in service.draft.get('mobs',{}) and target!='*':
        results.append('cel mob nieznany')
    elif kind=='collect' and target not in ITEMS and target not in service.draft.get('items',{}):
        results.append('cel przedmiot nieznany')
    if kind in ('kill','collect'):
        try:
            if int(q.get('needed') or 0)<1:results.append('needed ponizej 1')
        except (ValueError,TypeError,OverflowError):results.append('needed nie jest liczba')
    for req in _requirements(q):
        if req==qid:results.append('zaleznosc z samym soba')
        elif req not in known:results.append('brak wymaganego questa '+req[:35])
    return results[:8]


def _quest_audit(service,phrase,page):
    rows,total,p=_matching_page(service,phrase,page)
    if not rows:return 'QUEST AUDYT: brak wynikow.'
    issues=[];clean=0; clean_ids=[]
    for qid,base in rows:
        found=_signals(service,qid,base)
        if found:issues.append(qid+': '+', '.join(found))
        else:clean+=1;clean_ids.append(qid)
    return (f'QUEST AUDYT: {total} dopasowan, strona {p}/{max(1,(total+11)//12)}; '
            f'{len(issues)} z sygnalami, {clean} bez sygnalow na stronie. '
            +('; '.join(issues) if issues else 'Brak oczywistych anomalii na tej stronie.')+'; ID bez sygnalow: '+(', '.join(clean_ids) or 'brak')
            +' Weryfikacja czesci pol, nie pełen audyt wykonania NPC. Brak zmian.')


def _suggestion(service,qid):
    q=_quest(service,qid)
    alerts=_signals(service,qid,q)
    if not alerts:return f'QUEST PROPOZYCJA {qid}: brak prostych problemow w sprawdzanych polach. Brak zmian.'
    note='; '.join(alerts)
    if 'needed ponizej 1' in alerts or 'needed nie jest liczba' in alerts:
        return (f'QUEST PROPOZYCJA {qid}: {note}. Mozliwa korekta: admin guardian6 questy popraw '
                f'{qid} needed 1 POTWIERDZAM. Zmiana tylko DRAFT, sprawdz wymagania przed publikacja.')
    return (f'QUEST PROPOZYCJA {qid}: {note}. Nie da sie bezpiecznie odgadnac poprawnego ID. '
            'Znajdz poprawne cele/dependencje w katalogu i uzyj admin live edytuj quest. Brak zmian.')


def _fix_needed(service,qid,value):
    _quest(service,qid)
    _field,n=parse_quest_edit('needed',value)
    candidate=copy.deepcopy(service.draft)
    candidate['quest_edits'].setdefault(qid,{})['needed']=n
    service.validate(candidate)
    service.draft=candidate
    return (f'QUEST DRAFT {qid}: needed={n} przygotowano. '
            'Bez zmian aktywnych questow ani postepu graczy. '
            'admin live sprawdz / porownaj / aktywuj POTWIERDZAM.')


def _region_access(service,key):
    rooms=_area_rooms(service,key)
    graph={r:[] for r in rooms}
    all_links=service.draft['links']
    for src,direction,dst in all_links:
        if src in rooms and dst in rooms:graph[src].append(dst)
    entrance=[dst for src,dr,dst in all_links if dst in rooms and src not in rooms]
    starts=sorted(set(entrance)) or [min(rooms)]
    seen=set(starts);queue=deque(starts)
    while queue:
        node=queue.popleft()
        for nxt in graph[node]:
            if nxt not in seen:seen.add(nxt);queue.append(nxt)
    missing=sorted(rooms-seen)
    all_npcs={}
    for ident,npc in service.draft.get('npcs',{}).items():
        rid=npc.get('room')
        if rid in rooms:all_npcs.setdefault(rid,[]).append(ident)
    collisions=[rid for rid,members in all_npcs.items() if len(members)>1]
    missing_reverse=[]
    found={(src,dr,dst) for src,dr,dst in all_links}
    for src,dr,dst in found:
        if src in rooms and dst in rooms and (dst,_REVERSE.get(dr),src) not in found:
            missing_reverse.append(src+':'+dr)
    return (f'KRAINA DOSTEPNOSC {key}: {len(seen)}/{len(rooms)} pokoi dostepnych '
            f'od wejscia zewn. (lub najnizszego ID, jezeli wejscia brak); '
            f'odciete {len(missing)}: '+(', '.join(missing[:10]) or 'brak')+'; '
            f'brak powrotow {len(missing_reverse)}: '+(', '.join(sorted(missing_reverse)[:10]) or 'brak')+'; '
            f'kolizje nowych NPC {len(collisions)}: '+(', '.join(sorted(collisions)[:10]) or 'brak')+'. '
            'Brak zmian; nie sprawdza blokad fabularnych.')


def _arena_analysis(service,mid,hp,attack,cap='1000'):
    projection=_arena_projection(service,mid,hp,attack,cap)
    metadata=_boss_metadata(service,mid)
    return 'GUARDIAN6: '+metadata+' '+projection+' To NIE jest test rzeczywistego AI/UOSS.'


def _preflight(service):
    summary=service.validate(service.draft)
    changes=service.draft.get('quest_edits',{})
    ids=sorted(set(changes)|set(service.draft.get('quests',{})))
    findings=[]
    for qid in ids:
        q=_combined(service).get(qid)
        if q:
            issues=_signals(service,qid,q)
            if issues:findings.append(qid+': '+', '.join(issues))
    return (f'OLC PREFLIGHT: walidacja PASS, {summary}; questow w DRAFT {len(ids)}, '
            f'sygnalow {len(findings)}. '+('; '.join(findings[:12]) if findings else 'Brak oczywistych anomalii w badanych polach.')
            +(' Dalsze sygnaly pominieto.' if len(findings)>12 else '')
            +' Odczyt; NIE opublikowano. Przy sygnalach zweryfikuj recznie.')


async def handle_guardian6(session,raw):
    parts=str(raw or '').strip().split(maxsplit=1)
    if not parts or parts[0].casefold()!='guardian6':return False
    if not session.is_admin():
        await session.send('GUARDIAN6: tylko wlasciciel-administrator.');return True
    service=session.server.live_content_v1204
    arguments=parts[1].strip() if len(parts)>1 else 'pomoc'
    split=arguments.split()
    command=split[0].casefold() if split else 'pomoc'
    try:
        if command in ('pomoc','help'): msg=HELP
        elif command=='status': msg='GUARDIAN6 v40: edycja nagrod i needed tylko DRAFT; audyt questow, krainy, statyczna analiza bossow. Bez prawdziwej areny AI/UOSS.'
        elif command=='nagrody':
            action=split[1].casefold() if len(split)>1 else ''
            if action in ('plan','zestaw'):
                rest=arguments.split(None,2)
                if len(rest)<3:raise ValueError('nagrody plan/zestaw ID | 7 WARTOSCI [| POTWIERDZAM]')
                payload=rest[2]
                if action=='zestaw':
                    pieces=payload.split('|')
                    if not pieces or pieces[-1].strip()!='POTWIERDZAM':
                        raise ValueError('Wymagane POTWIERDZAM jako ostatni segment po |.')
                    payload='|'.join(pieces[:-1])
                    msg=_batch(service,payload,True)
                    _audit(session,'guardian6_rewards_draft',payload.split('|',1)[0].strip())
                else:msg=_batch(service,payload,False)
            elif action=='katalog' and len(split)>=3:
                page=split[-1] if len(split)>3 and split[-1].isdigit() else '1'
                phrase=' '.join(split[2:-1] if page!='1' or (len(split)>3 and split[-1].isdigit()) else split[2:])
                msg=_reward_catalog(service,phrase,page)
            else:raise ValueError('nagrody plan/zestaw/katalog - zobacz admin guardian6 pomoc')
        elif command=='questy':
            action=split[1].casefold() if len(split)>1 else ''
            if action=='audyt' and len(split)>=3:
                page=split[-1] if len(split)>3 and split[-1].isdigit() else '1'
                phrase=' '.join(split[2:-1] if len(split)>3 and split[-1].isdigit() else split[2:])
                msg=_quest_audit(service,phrase,page)
            elif action=='zaleznosci' and len(split)==3:msg=_dependencies(service,split[2])
            elif action=='propozycja' and len(split)==3:msg=_suggestion(service,split[2])
            elif action=='popraw' and len(split)==6 and split[3]=='needed' and split[5]=='POTWIERDZAM':
                msg=_fix_needed(service,split[2],split[4]);_audit(session,'guardian6_needed_draft',split[2])
            else:raise ValueError('questy audyt FRAZA [STRONA] / zaleznosci ID / propozycja ID / popraw ID needed ILOSC POTWIERDZAM')
        elif command=='kraina' and len(split)==3 and split[1].casefold()=='dostepnosc':msg=_region_access(service,split[2])
        elif command=='arena' and len(split) in (5,6) and split[1].casefold()=='analiza':
            msg=_arena_analysis(service,split[2],split[3],split[4],split[5] if len(split)==6 else '1000')
        elif command=='olc' and len(split)==2 and split[1].casefold()=='preflight':msg=_preflight(service)
        else:raise ValueError(HELP)
        await session.send(msg)
    except (ValueError,TypeError,OverflowError,KeyError,AttributeError) as exc:
        await session.send('GUARDIAN6: '+str(exc)[:350])
    return True
