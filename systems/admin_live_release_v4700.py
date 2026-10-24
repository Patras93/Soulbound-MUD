# -*- coding: utf-8 -*-
"""v47: bounded owner-only release readiness and quest reward previews.

No combat execution, SQLite writes, publication, world mutations or reward grants.
All actions in this module are read-only, derived from the existing live OLC.
"""
from __future__ import annotations
from systems.admin_guardian6_v4000 import _combined, _signals, _matching_page
from systems.admin_guardian5_v3900 import _effective_reward, STAT_LABELS
from systems.live_quest_olc_v1209 import STAT_XP_FIELDS_V3900
from systems.admin_guardian7_v4100 import _template
from core.classes_skills import CLASS_SKILLS

HELP_4 = (
    'ADMIN LIVE POMOC 4/4: questy exp ID (aktywne i DRAFT, wszystkie 6 statystyk); '
    'questy global [STRONA] (audyt całego katalogu z numerowanymi stronami); '
    'questy preflight (kontrola DRAFT); arena zgodnosc [BOSS_ID] (uczciwy zakres symulatora); '
    'gotowosc (kontrole potrzebne przed wdrozeniem). '
    'Wszystko tylko odczyt. Stare admin live, EXP wspolny i EXP osobny zostaja.'
)

def _page(raw,total):
    value=str(raw)
    if not value.isascii() or not value.isdecimal() or len(value)>6:
        raise ValueError('Strona: liczba calkowita od 1.')
    number=int(value)
    if not 1 <= number <= max(1,(total+7)//8):
        raise ValueError(f'Dostepne strony: 1-{max(1,(total+7)//8)}.')
    return number

def _effective_olc(service,qid):
    records=_combined(service)
    if qid not in records:raise ValueError('Nieznane ID questa. Wpisz: admin live katalog quest FRAZA.')
    base=records[qid]
    published=service.active.get('quest_edits',{}).get(qid,{})
    staged=service.draft.get('quest_edits',{}).get(qid,{})
    left, lv=_effective_reward(base,published)
    right,rv=_effective_reward(base,staged)
    def row(title,common,amounts,fields):
        values='; '.join(f'{STAT_LABELS[stat]} {amounts[stat]}' +
             (' osobno' if field in fields else ' wspolnie')
             for stat,field in STAT_XP_FIELDS_V3900.items())
        return f'{title}: wspolny {common}; {values}.'
    return (f'QUEST EXP {qid}: nagrody bazowe. '
        +row('AKTYWNE',left,lv,published)+' '
        +row('DRAFT',right,rv,staged)+' '
        +'Podglad bez zmiany. Edytuj: admin live edytuj quest '+qid+' reward_stat_xp | LICZBA; '
        +'pojedyncza: reward_stat_strength | LICZBA/auto. '
        +'Zatwierdzanie: admin live sprawdz, porownaj, aktywuj POTWIERDZAM.')

def _full_quest_audit(service,page='1'):
    # Derive a fresh report each time; OLC changes cannot stale-cache results.
    catalog=_combined(service)
    problems=[];checked=0
    for qid,record in sorted(catalog.items()):
        checked+=1
        alerts=_signals(service,qid,record)
        if alerts:problems.append((qid,alerts))
    p=_page(page,len(problems))
    shown=problems[(p-1)*8:p*8]
    lines='; '.join(f'{qid}: {", ".join(alerts[:3])}' for qid,alerts in shown) or 'brak'
    return (f'QUEST GLOBAL: sprawdzono {checked} ID; sygnaly {len(problems)}; '
            f'strona {p}/{max(1,(len(problems)+7)//8)}; {lines}. '
            'Sygnal to wskazowka, nie dowod ze quest jest zepsuty. '
            'Brak automatycznej publikacji i zmian SQLite.')

def _draft_preflight(service):
    result=service.validate(service.draft)
    qchanges=service.draft.get('quest_edits',{})
    problems=[]
    catalog=_combined(service)
    for qid in sorted(qchanges):
        if qid not in catalog:
            problems.append(qid+': brak definicji')
        else:
            problems.extend(qid+': '+alert for alert in _signals(service,qid,catalog[qid]))
    return (f'OLC PREFLIGHT: walidacja {str(result)[:200]}; '
            f'questy zmienione {len(qchanges)}, sygnaly {len(problems)}; '
            +('; '.join(problems[:8]) or 'brak w sprawdzanych polach')+'. '
            'Nie publikuje; sprawdz manualnie i uzyj admin live porownaj. '
            'Pełnego Windows PREDEPLOY 60/60 PLUS nie zastępuje.')

def _arena_coverage(service,boss_id=''):
    title='bez wybranego bossa'
    if boss_id:
        if len(boss_id)>100 or not boss_id.isascii() or any(c.isspace() for c in boss_id):
            raise ValueError('Wpisz prawidlowy identyfikator bossa.')
        ident,meta,origin=_template(service,boss_id)
        title=f'{ident} ({str(meta.get("name",boss_id))[:45]})'
    return (f'ARENA ZGODNOSC {title}: klasy z katalogu {len(CLASS_SKILLS)}; '
        'symulowane: czesc faz UOSS, pomocnicy, czasowe efekty, HP, model skilli, '
        'model EQ, modelowa druzyna, oddzielny RNG, migawki i prognozy. '
        'NIEZGODNE 1:1: pelne produkcyjne AI/ticki, wszystkie 5461 skilli, '
        'rzeczywiste statystyki i przedmioty postaci, summon/mercenary credits, '
        'prawdziwe rozliczenia druzyny. Produkcyjna petla nie jest wykonywana. '
        'Nie ma nagrod ani zapisow bazy. To oznacza, ze wynik LAB nie jest '
        'gwarancja wyniku walki na serwerze.')

def _readiness():
    return ('GOTOWOSC WYDANIA: ten raport to lista kontrolna, NIE zaliczony test. '
        '1. TESTUJ_Soulbound.bat dla dokladnego ZIP i SHA256: PASS 60/60 PLUS. '
        '2. Backup soulbound.db wraz z bezpiecznym stanem WAL. '
        '3. Zweryfikuj 5 graczy TCP i ponowne logowanie. '
        '4. NVDA/MUSHclient: katalog questow, EXP osobno i wspolny, arena LAB, '
        'cofanie DRAFT i brak publikacji bez potwierdzenia. '
        '5. Dopiero wtedy WDROZ_PO_PREDEPLOY.bat. '
        'Kod silnika wymaga wdrozenia/restartu, OLC aktywuje sie przez admin live.')

async def dispatch_release(session,group,raw):
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return True
    args=str(raw or '').split()
    try:
        if group=='pomoc' and args==['4']:
            output=HELP_4
        elif group=='gotowosc' and not args:
            output=_readiness()
        elif group in ('questy','zadania'):
            if args and args[0].casefold()=='exp' and len(args)==2:
                output=_effective_olc(session.server.live_content_v1204,args[1])
            elif args and args[0].casefold()=='global' and len(args) in (1,2):
                output=_full_quest_audit(session.server.live_content_v1204,args[1] if len(args)==2 else '1')
            elif args==['preflight']:
                output=_draft_preflight(session.server.live_content_v1204)
            else:return False
        elif group=='arena' and args and args[0].casefold()=='zgodnosc' and len(args) in (1,2):
            output=_arena_coverage(session.server.live_content_v1204,args[1] if len(args)==2 else '')
        else:return False
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        output='ADMIN LIVE: '+str(exc)[:320]
    await session.send(output)
    return True
