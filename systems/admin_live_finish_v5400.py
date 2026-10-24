# -*- coding: utf-8 -*-
"""Soulbound v54: one Admin Live diagnostics/repair interface.

This module deliberately never invokes the production battle loop, writes the
player database, grants rewards, or publishes OLC. Existing OLC editing remains
the only write path for proposed quest repairs.
"""
from __future__ import annotations
from collections import Counter
from core import live_level_caps_v5200 as caps
from systems.admin_live_integrity_v4900 import _effective, _issues
from systems.admin_live_final_v5000 import _fixable
from systems.admin_live_expansion_v4800 import KINDS, _page
from systems.admin_live_complete_v5100 import _class_matrix, _boss_matrix
from core.classes_skills import CLASS_SKILLS
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
from systems.infinite_equipment import infinite_source_profile, infinite_equipment_audit_v11330
from core import progression_resources as progress

HELP = (
    'ADMIN LIVE POMOC 9: questy przeglad [STRONA] - 18 typow, liczby bledow i ostrzezen; '
    'questy napraw ID - podpowiedz pewnych poprawek przed planem DRAFT; '
    'arena przeglad [1-6] [TURY 1-3] - klasy i superbossy na osobnych kopiach; '
    'eq pokrycie - rzeczywiste zrodla progresywnego EQ; '
    'limity kontrola POZIOM - ryzyko przekroczenia SQLite int64; '
    'gotowosc finalna - co trzeba potwierdzic przed wdrozeniem. '
    'DRAFT zatwierdzaj istniejacym questy edycja plan/zatwierdz; '
    'publikacja zawsze osobno. LAB nie jest walka UOSS 1:1.'
)


def quest_type_review(service, raw='1'):
    catalog=_effective(service)
    counters=Counter(str(q.get('kind','brak')) for q in catalog.values())
    errors=Counter();warnings=Counter();fixed=Counter()
    for qid,q in catalog.items():
        kind=str(q.get('kind','brak'))
        e,w=_issues(qid,q,catalog)
        if e:errors[kind]+=1
        if w:warnings[kind]+=1
        patch,_=_fixable(qid,q,catalog)
        if patch:fixed[kind]+=1
    kinds=list(KINDS)+sorted(k for k in counters if k not in KINDS)
    page,pages=_page(raw,len(kinds))
    rows=[]
    for kind in kinds[(page-1)*8:page*8]:
        rows.append(f'{kind}: razem {counters[kind]}, bledy {errors[kind]}, ostrzezenia {warnings[kind]}, pewne poprawki {fixed[kind]}')
    return (f'QUESTY PRZEGLAD: {len(catalog)} questow, {len(kinds)} typow, '
        f'strona {page}/{pages}. '+'; '.join(rows)+'. '
        'Pewne poprawki to tylko bezpieczne pola liczbowe. '
        'Wykonanie zadan i wyzwalacze NPC wymagaja testu w grze. Bez zmian.')


def quest_fix_advice(service,qid):
    catalog=_effective(service)
    if not qid or len(qid)>100 or qid not in catalog:
        raise ValueError('Nieznany ID; wyszukaj: admin live questy szukaj FRAZA.')
    q=catalog[qid]
    errors,warnings=_issues(qid,q,catalog)
    patch,_=_fixable(qid,q,catalog)
    rows=[f'{key}: {q.get(key)!r} -> {value!r}' for key,value in sorted(patch.items())]
    proposal='; '.join(rows) if rows else 'brak bezpiecznej automatycznej poprawki'
    manual='; '.join((errors+warnings)[:9]) if (errors or warnings) else 'brak strukturalnych sygnalow'
    return (f'QUEST NAPRAW {qid} typ {q.get("kind","brak")}: {proposal}. '
        f'Kontrola: {manual}. '
        'Plan bezpiecznych pol: admin live questy korekta plan '+qid+'. '
        'Zmiany pozostalych pol: admin live questy edycja plan ID | POLE | WARTOSC. '
        'Zapis tylko w DRAFT, aktywacja osobno. Nie zgadujemy ID NPC/mobow, nagrod ani fabuly.')


def arena_suite(session, page='1', turns='1'):
    p=int(page) if str(page).isascii() and str(page).isdecimal() else -1
    t=int(turns) if str(turns).isascii() and str(turns).isdecimal() else -1
    if not 1<=p<=6 or not 1<=t<=3:
        raise ValueError('ARENA PRZEGLAD: strona 1-6, tury 1-3.')
    if p<=3:
        detail=_class_matrix(session,str(t),str(p))
        category='klasy'
    else:
        detail=_boss_matrix(session,str(t),str(p-3))
        category='superbossy'
    return (f'ARENA PRZEGLAD {category} {p}/6: '+detail+
            ' Tylko bezpieczny model, bez nagrod, SQL i postaci gracza. '
            'Nie potwierdza zgodnosci calego produkcyjnego AI, wszystkich 5461 skilli i realnego czasu.')


def equipment_coverage():
    source=[('krypta',{'crypt_floor':901}),
        ('mit_krypta',{'mythic_crypt_floor':901}),
        ('wieza',{'astral_floor':901}),
        ('mit_wieza',{'mythic_astral_floor':901}),
        ('magitek',{'magitek_infinite':True,'magitek_floor':901})]
    lines=[]
    for label,template in source:
        profile=infinite_source_profile(template)
        if profile is None:raise ValueError('Brak generatora '+label)
        lines.append(label+' etap '+str(profile['effective_stage']))
    audit=infinite_equipment_audit_v11330()
    return ('EQ POKRYCIE: 5 zrodel Rezonansu Glebi: '+'; '.join(lines)+'. '
        f'Testy warunkow progowych {audit["boundary_count"]}, bledy {audit["error_count"]}. '
        'Prawdziwy loot i odzyskiwanie wariantow istnieja w silniku; '
        'nie wszystkie receptury, nagrody questow ani statyczne sklepy generuja nieskonczone EQ. '
        'Ostatnie nie zostaly sztucznie rozszerzone. Podglad bez nadawania przedmiotu.')


def progression_safety(level):
    if not str(level).isascii() or not str(level).isdecimal() or len(str(level))>7:
        raise ValueError('Podaj poziom 1..100000.')
    value=int(level)
    if not 1<=value<=100000:raise ValueError('Podaj poziom 1..100000.')
    entries=(('postac',progress.character_xp_to_next),
        ('bieglosc',progress.class_mastery_xp_to_next),
        ('dusza',progress.soul_xp_to_next),
        ('bron_duszy',progress.soul_weapon_mastery_xp_to_next),
        ('skille',progress.skill_xp_to_next))
    rows=[];risks=0
    for name,func in entries:
        try:
            n=func(value)
            safe=type(n) is int and 0<=n<=9223372036854775807
        except (OverflowError,ValueError,ArithmeticError):
            safe=False;n=None
        rows.append(name+' '+(str(n) if safe else 'RYZYKO int64'))
        if not safe:risks+=1
    display='; '.join(name+' '+caps.display(caps.cap(name)) for name in caps.KEYS)
    return (f'LIMITY KONTROLA poziom {value}: '+'; '.join(rows)+'. '
        f'Ryzyko progow SQLite int64: {risks}. Limity: {display}. '
        'Zero progu moze oznaczac blokade starego limitu. To sprawdzenie pojedynczych progow, a nie gwarancja sumowania EXP lub rekordow SQLite. '
        'Opcja bezlimitu nadal ma techniczny sufit 1 mld. Nic nie zmieniono.')


def final_readiness():
    return ('GOTOWOSC FINALNA: 22 klasy '+str(len(CLASS_SKILLS))+'; superbossy '+
        str(len(UOSS_SUPERBOSS_ENCOUNTERS_V11134))+'; typy questow '+str(len(KINDS))+'. '
        'Warunki: 1 ZIP i zgodny SHA256; 2 klon rzeczywistej SQLite, 60/60 PLUS PASS; '
        '3 testy 5 polaczen TCP i restart; 4 NVDA/MUSHclient oraz edycja/cofanie DRAFT; '
        '5 kopia produkcyjnej bazy wraz z WAL; 6 wdrozenie dopiero po PASS. '
        'UWAGA: arena nie jest produkcyjnym UOSS 1:1; generowanie EQ i EXP '
        'nie sa matematycznie nieograniczone. To pozostaja funkcjonalne ograniczenia, '
        'nie wolno ich oznaczac jako ukonczone testem PREDEPLOY.')


async def dispatch_v54(session,group,raw):
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return True
    args=str(raw or '').strip().split()
    try:
        if group=='pomoc' and args==['9']:message=HELP
        elif group in ('questy','zadania') and args and args[0]=='przeglad' and len(args) in (1,2):
            message=quest_type_review(session.server.live_content_v1204,args[1] if len(args)==2 else '1')
        elif group in ('questy','zadania') and args and args[0]=='napraw' and len(args)==2:
            message=quest_fix_advice(session.server.live_content_v1204,args[1])
        elif group=='arena' and args and args[0]=='przeglad' and len(args) in (1,2,3):
            message=arena_suite(session,*(args[1:]))
        elif group=='eq' and args==['pokrycie']:
            message=equipment_coverage()
        elif group in ('limity','limit','capy') and args and args[0]=='kontrola' and len(args)==2:
            message=progression_safety(args[1])
        elif group=='gotowosc' and args==['finalna']:
            message=final_readiness()
        else:return False
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError) as exc:
        message='ADMIN LIVE: '+str(exc)[:300]
    await session.send(message)
    return True
