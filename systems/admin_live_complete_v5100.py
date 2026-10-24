# -*- coding: utf-8 -*-
"""v51 Admin Live: transactional multi-field editing + detached 22-class audit.

No live-combat player sessions, reward grants, SQL writes, publication or RNG
consumption. Each staged change is delegated to the authoritative OLC validator.
"""
from __future__ import annotations
import copy
import re
from types import SimpleNamespace
from core.classes_skills import CLASS_SKILLS, effective_skill_mana_cost
from systems.admin_live_integrity_v4900 import _effective
from systems.admin_guardian11_v4500 import _arena, _turn
from systems.admin_guardian10_v4400 import _lab_start10, _lab_turn10
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
from systems.live_quest_olc_v1209 import parse_quest_edit
from systems.admin_live_ultimate_v4600 import _int

_HELP = ('ADMIN LIVE POMOC 8/8: questy edycja plan ID | POLE | WARTOSC ; '
         'ID | POLE | WARTOSC (1-12 pol w najwyzej 8 questach); '
         'questy edycja zatwierdz POTWIERDZAM - tylko DRAFT; '
         'questy edycja cofnij POTWIERDZAM - cofnij wlasne zmiany; '
         'questy edycja anuluj / status; arena klasy test [1-3] [STRONA]; arena bossy test [1-3] [STRONA] '
         '- 22 klasy i 21 superbossow na odizolowanych kopiach. '
         'Arena nadal NIE jest rzeczywista walka UOSS 1:1. '
         'Zwykle publikowanie questow pozostaje osobno w admin live.')
_ID = re.compile(r'[A-Za-z0-9_\-]{1,100}\Z')


def _planned_edits(session, service, text):
    raw=str(text).strip()
    if not raw or len(raw)>2400:
        raise ValueError('EDYCJA PLAN: podaj ID | POLE | WARTOSC ; ... (do 12 zmian).')
    clauses=[part.strip() for part in raw.split(';')]
    if not 1 <= len(clauses) <= 12 or any(not x for x in clauses):
        raise ValueError('EDYCJA PLAN: wymagane 1-12 pelnych zmian.')
    original=copy.deepcopy(service.draft)
    active=copy.deepcopy(service.active)
    candidate=copy.deepcopy(original)
    catalog=_effective(service)
    changed=[]
    visited=set()
    for line in clauses:
        triplet=[x.strip() for x in line.split('|')]
        if len(triplet)!=3:
            raise ValueError('EDYCJA PLAN: kazda zmiana to ID | POLE | WARTOSC.')
        qid, field, raw_value=triplet
        if not _ID.fullmatch(qid):raise ValueError('EDYCJA PLAN: niepoprawne ID.')
        if qid not in catalog:raise ValueError('EDYCJA PLAN: nieznane ID '+qid)
        normalized,value=parse_quest_edit(field,raw_value)
        key=(qid,normalized)
        if key in visited:raise ValueError('EDYCJA PLAN: to samo pole podano dwukrotnie: '+qid+' '+normalized)
        visited.add(key)
        if len({x[0] for x in visited})>8:
            raise ValueError('EDYCJA PLAN: maksymalnie 8 roznych questow.')
        previous=catalog[qid].get(normalized)
        if previous==value:raise ValueError('EDYCJA PLAN: identyczna wartosc '+qid+' '+normalized)
        candidate['quest_edits'].setdefault(qid,{})[normalized]=value
        # Show old effective value, then new value, without leaking any secrets.
        show=lambda val:repr(val)[:110]
        changed.append(f'{qid} {normalized}: {show(previous)} -> {show(value)}')
    # Canonical full-world DRAFT validation rejects unsupported quest types,
    # invalid prerequisites, non-existent item IDs, overflowed rewards, etc.
    service.validate(candidate)
    session.adminlive51_plan=(original,active,candidate,tuple(changed))
    return ('QUEST EDYCJA PLAN: '+str(len(changed))+' pol, '
            +str(len({q for q,_ in visited}))+' questow; '
            +'; '.join(changed)+'. NIC NIE ZAPISANO. '
            'Zatwierdz: admin live questy edycja zatwierdz POTWIERDZAM. '
            'Zmiana tylko w DRAFT, publikacja osobno.')


def _commit(session,service):
    plan=getattr(session,'adminlive51_plan',None)
    if plan is None:raise ValueError('EDYCJA: brak planu; uzyj questy edycja plan.')
    before,active,candidate,changed=plan
    if service.active!=active or service.draft!=before:
        session.adminlive51_plan=None
        raise ValueError('EDYCJA: ACTIVE lub DRAFT zmienily sie po planie; przygotuj nowy.')
    service.validate(candidate)
    service.draft=copy.deepcopy(candidate)
    session.adminlive51_undo=(copy.deepcopy(before),copy.deepcopy(candidate),copy.deepcopy(active))
    session.adminlive51_plan=None
    return (f'QUEST EDYCJA DRAFT: {len(changed)} pol zapisano tylko w DRAFT. '
            'Bez publikacji, zapisow SQLite i zmian postepu postaci. '
            'Wpisz admin live sprawdz / porownaj, potem osobno aktywuj.')


def _undo(session,service):
    record=getattr(session,'adminlive51_undo',None)
    if record is None:raise ValueError('EDYCJA: brak zmian do cofniecia.')
    previous,current,active=record
    if service.draft!=current or service.active!=active:
        raise ValueError('EDYCJA: ktos pozniej zmienil DRAFT lub ACTIVE. Nie cofne cudzych zmian.')
    service.draft=copy.deepcopy(previous)
    session.adminlive51_plan=None
    session.adminlive51_undo=None
    return 'QUEST EDYCJA COFNIETA: przywrocono poprzedni DRAFT. ACTIVE i SQLite bez zmian.'


def _status(session):
    plan=getattr(session,'adminlive51_plan',None)
    undo=getattr(session,'adminlive51_undo',None)
    return ('QUEST EDYCJA STATUS: plan '+(str(len(plan[3]))+' pol' if plan else 'brak')+
            '; mozna cofnac ostatnie zatwierdzenie: '+('tak' if undo else 'nie')+
            '. Brak automatycznego publikowania.')


def _class_matrix(session,turns='1',page='1',mastery=800):
    turns=_int(turns,1,3,'tury')
    p=_int(page,1,3,'strona')
    source=_arena(session)
    if source['finished']:raise ValueError('Arena zakonczona. Rozpocznij nowa.')
    # 22 independently detached, identically seeded experiments. Only supported
    # damage skills; absence is shown explicitly instead of fabricated effects.
    classes=sorted(CLASS_SKILLS)
    if len(classes)!=22:
        raise ValueError('Nieoczekiwana liczba klas: '+str(len(classes))+'. Test wymaga 22.')
    if not isinstance(mastery,int) or not 1<=mastery<=1_000_000_000:
        raise ValueError('Nieprawidlowa bieglosc testu.')
    outputs=[]
    for name in classes:
        skills=[]
        for row in CLASS_SKILLS[name]:
            if row.get('kind')!='damage' or int(row.get('unlock',1) or 1)>mastery:continue
            try:
                cost=effective_skill_mana_cost(row,name)
                mult=float(row.get('mult',1) or 1)
                if 0<=cost<=10**12 and 0<=mult<=10**6:skills.append((cost,int(row.get('unlock',1) or 1),str(row.get('id')),row))
            except (ValueError,TypeError,OverflowError):continue
        skills.sort(key=lambda x:(x[1],x[0],x[2]))
        if not skills:
            outputs.append(f'{name}: brak wspieranego ofensywnego skilla');continue
        row=skills[0][3]
        clone=SimpleNamespace(guardian7_lab=copy.deepcopy(source))
        s=clone.guardian7_lab
        b=s['_guardian11_build']
        b.update({'class':name,'mastery':mastery,'mana':10**12,'max_mana':10**12,'items':{}})
        # Prevent formula/model errors from aborting the full per-class report.
        err=None;done=0
        for _ in range(turns):
            if s['finished']:break
            try:
                _turn(clone,'skill',row['id'])
                done+=1
            except (ValueError,TypeError,KeyError,OverflowError,AttributeError,ZeroDivisionError) as exc:
                err=str(exc)[:70];break
        change=s['total_dealt']-source['total_dealt']
        outputs.append(f'{name}: {row["id"]}; tur {done}; obrazenia +{change}'+(f'; model odmowil: {err}' if err else ''))
    lo=(p-1)*8;hi=p*8
    return (f'ARENA TEST KLAS: {len(classes)} klas; {turns} tur na klase; strona {p}/3. '
            +'; '.join(outputs[lo:hi])+'. '
            f'Wyniki z tych samych danych bossa i prywatnego RNG; bieglosc TESTOWA {mastery}, MP 10^12; '
            'nie modyfikuje aktualnej areny, postaci, SQL ani RNG serwera. '
            'Uzywa katalogowych skilli, ale obrazenia i AI sa MODELEM, nie UOSS 1:1.')


def _boss_matrix(session,turns='1',page='1'):
    turns=_int(turns,1,3,'tury')
    keys=sorted(UOSS_SUPERBOSS_ENCOUNTERS_V11134)
    pages=max(1,(len(keys)+7)//8)
    p=_int(page,1,pages,'strona')
    service=session.server.live_content_v1204
    outputs=[]
    for key in keys[(p-1)*8:p*8]:
        # Each encounter gets a detached actor, mob and RNG. Production session,
        # real party, account, SQLite and world spawning are never called.
        detached=SimpleNamespace(guardian7_lab=None,guardian9_snapshot=None)
        try:
            _lab_start10(detached,service,key,'1000000','20000')
            before=detached.guardian7_lab
            count=0
            for _ in range(turns):
                if before['finished']:break
                _lab_turn10(detached,'atak')
                count+=1
            after=detached.guardian7_lab
            outputs.append(f'{key}: {count} tur, boss HP {after["boss"].hp}, '
                           f'lider HP {after["hero_hp"]}, dodatki {len(after["adds"])}')
        except (ValueError,TypeError,KeyError,OverflowError,AttributeError,ZeroDivisionError) as exc:
            outputs.append(f'{key}: model odmowil - {str(exc)[:90]}')
    return (f'ARENA TEST BOSSY UOSS: {len(keys)} unikalnych starc, '
            f'tur na bossa {turns}, strona {p}/{pages}. '+'; '.join(outputs)+'. '
            'Test wykorzystuje funkcje zrodlowe wybranych regul UOSS na kopiach; '
            'nie sprawdza pelnego AI, wszystkich czarow, nagrod ani czasu rzeczywistego. '
            'Bez zmian aktualnej areny, SQLite, HP i RNG serwera.')


async def dispatch_v51(session,group,raw):
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    args=str(raw or '').strip().split()
    try:
        if group=='pomoc' and args==['8']:
            response=_HELP
        elif group in ('questy','zadania') and args[:2]==['edycja','plan']:
            response=_planned_edits(session,session.server.live_content_v1204,' '.join(args[2:]))
        elif group in ('questy','zadania') and args[:2]==['edycja','zatwierdz'] and args[2:]==['POTWIERDZAM']:
            response=_commit(session,session.server.live_content_v1204)
        elif group in ('questy','zadania') and args[:2]==['edycja','cofnij'] and args[2:]==['POTWIERDZAM']:
            response=_undo(session,session.server.live_content_v1204)
        elif group in ('questy','zadania') and args==['edycja','anuluj']:
            session.adminlive51_plan=None
            response='QUEST EDYCJA: plan anulowany, bez zmian.'
        elif group in ('questy','zadania') and args==['edycja','status']:
            response=_status(session)
        elif group in ('questy','zadania') and args and args[0]=='edycja':
            raise ValueError('EDYCJA: plan ID | POLE | WARTOSC ; ... / zatwierdz POTWIERDZAM / cofnij POTWIERDZAM / anuluj / status.')
        elif group=='arena' and args[:2]==['klasy','test'] and len(args) in (2,3,4):
            response=_class_matrix(session,*args[2:])
        elif group=='arena' and args[:2]==['bossy','test'] and len(args) in (2,3,4):
            response=_boss_matrix(session,*args[2:])
        else:return False
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError) as exc:
        response='ADMIN LIVE: '+str(exc)[:400]
    await session.send(response)
    return True
