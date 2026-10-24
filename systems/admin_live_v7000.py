# -*- coding: utf-8 -*-
"""v70: read-only operator acceptance audit, explicitly NOT a predeploy pass.
Avoid touching production fights/EXP or claiming Windows/NVDA checks succeeded.
"""
from __future__ import annotations
from copy import deepcopy
from core.classes_skills import CLASS_SKILLS
from data.quests import QUESTS


def _count(section):
    if isinstance(section,(dict,list,set,tuple)):return len(section)
    return 0

def differences(service,page='1'):
    if not page.isascii() or not page.isdecimal() or len(page)>3:
        raise ValueError('Podaj numer strony od 1.')
    rows=[]
    for name in sorted(set(service.active)|set(service.draft)):
        before=service.active.get(name);after=service.draft.get(name)
        if before!=after:
            rows.append(f'{name}: aktywne {_count(before)}, DRAFT {_count(after)}')
    p=int(page);pages=max(1,(len(rows)+5)//6)
    if not 1<=p<=pages:raise ValueError(f'Dostepne strony: 1-{pages}.')
    shown=rows[(p-1)*6:p*6]
    return (f'ADMIN LIVE ODBIOR ROZNICE: sekcji zmienionych {len(rows)}, strona {p}/{pages}; '
            +('; '.join(shown) or 'brak zmian OLC')+'. Niczego nie publikuje.')

def readiness(service):
    # Exactly the same validated OLC draft format as the real publishing path.
    issue='BRAK'
    try:
        service.validate(deepcopy(service.draft))
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        issue='BLAD '+str(exc)[:140]
    dirty=service.active!=service.draft
    return (f'ADMIN LIVE ODBIOR v70: 22 klasy oczekiwane; wykryto {len(CLASS_SKILLS)}; '
            f'questow {len(QUESTS)}; rewizja OLC {int(service.revision)}; '
            f'walidacja DRAFT: {issue}; DRAFT rozni sie od aktywnego: {"TAK" if dirty else "NIE"}. '
            'Windows PREDEPLOY 60/60 PLUS: NIEPOTWIERDZONY. '
            'NVDA/MUSHclient: NIEPOTWIERDZONY. Backup SQLite: NIEPOTWIERDZONY. '
            'ARENA UOSS 1:1: NIEUKONCZONA. Pelna progresja EQ i kazdy blad questa: NIEUKONCZONE. '
            'Ten raport NIE zatwierdza wdrozenia i nie wykonuje zmian.')

def gates():
    return ('ADMIN LIVE ODBIOR BRAMKI: 1. wykonaj PREDEPLOY_NOWEJ_WERSJI.bat i zachowaj log z wynikiem 60/60 PLUS; '
            '2. sprawdz pod NVDA pomoc, katalog, questy i arene; '
            '3. wykonaj kopie soulbound.db wraz z bezpiecznie zamknietym WAL; '
            '4. zatrzymaj serwer i sesje graczy; '
            '5. WDROZ_PO_PREDEPLOY.bat tylko po PASS; '
            '6. sprawdz logowanie i postepy po restarcie. '
            'Zaden punkt nie zostal automatycznie zaliczony.')

async def dispatch_v70(session,group,raw):
    args=str(raw or '').strip().split()
    if not ((group=='pomoc' and args==['25']) or group=='odbior'):
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        service=session.server.live_content_v1204
        if group=='pomoc':result=('ADMIN LIVE POMOC 25: odbior / odbior roznice [STRONA] / '
                                  'odbior bramki. To raport przyjecia wersji 70, tylko odczyt.')
        elif not args or args==['sprawdz']:result=readiness(service)
        elif args==['bramki']:result=gates()
        elif args and args[0]=='roznice' and len(args)<=2:
            result=differences(service,args[1] if len(args)==2 else '1')
        else:raise ValueError('Wpisz: odbior / odbior roznice [STRONA] / odbior bramki.')
    except (ValueError,TypeError,AttributeError,OverflowError,KeyError) as exc:
        result='ADMIN LIVE ODBIOR: '+str(exc)[:200]
    await session.send(result)
    return True
