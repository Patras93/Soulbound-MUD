# -*- coding: utf-8 -*-
"""v69: read-only, NVDA-first index of existing Admin Live commands.
No game-state writes, dynamic execution, guessing commands or network requests.
"""
from __future__ import annotations
from data.quests import QUESTS
from core.classes_skills import CLASS_SKILLS

# Each entry is an already implemented route from v46-v68; index is help, not execution.
_ENTRIES = (
 ('Swiat', 'admin live katalog pokoj FRAZA', 'Przeglad istniejacych lokacji'),
 ('Swiat', 'admin live pokoj', 'Tworzenie nowej lokacji przez OLC'),
 ('Swiat', 'admin live polacz', 'Laczenie lokacji w OLC'),
 ('Mob', 'admin live katalog mob FRAZA', 'Znajdowanie mobow'),
 ('Mob', 'admin live edytuj mob ID POLE | WARTOSC', 'Zmiana parametrow moba w DRAFT'),
 ('Questy', 'admin live questy szukaj FRAZA', 'Znajdowanie ID questow'),
 ('Questy', 'admin live questy karta ID', 'Karta zadania'),
 ('Questy', 'admin live questy bledy', 'Audyt bledow'),
 ('Questy', 'admin live questy pakiet plan ...', 'Atomowa edycja DRAFT wielu questow'),
 ('Questy', 'admin live questy pakiet zatwierdz POTWIERDZAM', 'Zatwierdzenie planu tylko do DRAFT'),
 ('Questy', 'admin live questy pakiet cofnij POTWIERDZAM', 'Cofniecie ostatniego pakietu DRAFT'),
 ('EXP', 'admin live questy exp ID', 'Wspolny i osobny EXP statystyk'),
 ('EQ', 'admin live limity', 'Podglad limitow poziomow i EQ'),
 ('EQ', 'admin live limity ustaw eq bezlimitu POTWIERDZAM', 'Zdjecie limitu EQ'),
 ('EQ', 'admin live eq craft 1000 930', 'Prognoza rozwoju rzemiosla'),
 ('EQ', 'admin live eq drop krypta 901 leather_vest', 'Prognoza dropu'),
 ('UOSS', 'admin live arena start black_rabite 100000 2000 Primm', 'Start prywatnej areny'),
 ('UOSS', 'admin live arena uoss status Mini', 'Odpornosc EQ na status'),
 ('UOSS', 'admin live arena uoss druzyna wsparcie 5', 'Wsparcie calej testowej druzyny'),
 ('OLC', 'admin live sprawdz', 'Walidacja projektu'),
 ('OLC', 'admin live porownaj', 'Podglad zmian przed aktywacja'),
 ('OLC', 'admin live aktywuj POTWIERDZAM', 'Publikacja OLC, ostroznie'),
 ('OLC', 'admin live cofnij POTWIERDZAM', 'Cofanie aktywnego OLC'),
 ('Wydanie', 'admin live gotowosc finalna', 'Lista wymaganych kontroli; nie PASS'),
)
_PER_PAGE=6

def index(page='1'):
    if not page.isascii() or not page.isdecimal() or len(page)>3:
        raise ValueError('Strona musi byc liczba od 1 do 4.')
    n=int(page)
    pages=(len(_ENTRIES)+_PER_PAGE-1)//_PER_PAGE
    if not 1<=n<=pages:
        raise ValueError(f'Dostepne strony: 1-{pages}.')
    start=(n-1)*_PER_PAGE
    rows=[f'{start+i+1}. {kind}: {cmd} - {desc}' for i,(kind,cmd,desc) in enumerate(_ENTRIES[start:start+_PER_PAGE])]
    return f'ADMIN LIVE CENTRUM {n}/{pages}. '+'; '.join(rows)+'. Wyszukaj: admin live centrum szukaj SLOWO. Bez zmian w swiecie.'

def search(query):
    token=query.strip().casefold()
    if not 2<=len(token)<=45 or any(ord(c)<32 for c in token):
        raise ValueError('Szukaj frazy 2-45 znakow.')
    hits=[(i,cmd) for i,(kind,cmd,desc) in enumerate(_ENTRIES,1)
          if token in f'{kind} {cmd} {desc}'.casefold()]
    shown=hits[:8]
    return f'ADMIN LIVE CENTRUM SZUKAJ {token}: wynikow {len(hits)}; '+('; '.join(f'{i}. {cmd}' for i,cmd in shown) or 'brak')+'. Pokazano maksymalnie 8 wynikow, nic nie wykonano.'

def catalog_state(service):
    return (f'ADMIN LIVE CENTRUM STATUS: klas {len(CLASS_SKILLS)}, questow {len(QUESTS)}; '
            f'OLC rewizja {int(service.revision)}, sekcje {len(service.active)}, '
            f'projekt rozni sie od aktywnego: {"TAK" if service.draft != service.active else "NIE"}. '
            'Dane odczytane bez publikowania, przejdź do admin live odbior (v70).')

async def dispatch_v69(session,group,raw):
    args=str(raw or '').strip().split()
    if not ((group=='pomoc' and args==['24']) or group=='centrum'):
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if group=='pomoc':
            result='ADMIN LIVE POMOC 24: centrum [STRONA 1-4] / centrum szukaj FRAZA / centrum status. Numerowane komendy NVDA, bez wykonywania zmian.'
        elif not args:result=index()
        elif len(args)==1 and args[0]=='status':
            result=catalog_state(session.server.live_content_v1204)
        elif len(args)==1:result=index(args[0])
        elif args[0]=='szukaj':result=search(' '.join(args[1:]))
        else:raise ValueError('Uzyj: centrum [1-4], centrum szukaj FRAZA, centrum status.')
    except (ValueError,TypeError,AttributeError,OverflowError) as exc:
        result='ADMIN LIVE CENTRUM: '+str(exc)[:190]
    await session.send(result)
    return True
