# -*- coding: utf-8 -*-
"""v63 Admin Live: single help page plus cap-aware 22-class lab comparison.

Never executes real combat callbacks or grants XP/EQ; the full production
realtime engine is intentionally not started here.
"""
from __future__ import annotations
from core.live_level_caps_v5200 import cap,effective_number
from systems.admin_live_complete_v5100 import _class_matrix

HELP = ('ADMIN LIVE POMOC 18: questy pakiet plan pole QUEST_ID POLE WARTOSC; '
        'mozna laczyc przez ; ze zmianami ID z pomoc 17. Przyklady: '
        'questy pakiet plan pole temple_rats needed 3 ; pole temple_rats reward_stat_xp 500. '
        'Plan sprawdzany w calosci. Zatwierdz POTWIERDZAM tylko DRAFT, cofnij POTWIERDZAM. '
        'arena klasy porownaj [TURY 1-3] [STRONA 1-3] [BIEGLOSC] - '        '22 klasy na prywatnych kopiach, zgodnie z limitem admin live limity. '
        'Druzyna gotowy/dodaj rowniez respektuje ten limit. '
        'Arena nadal jest modelem, nie pelna walka produkcyjna 1:1.')


def class_comparison(session, turns='1',page='1',mastery='800'):
    raw=str(mastery)
    if not raw.isascii() or not raw.isdecimal() or len(raw)>10:
        raise ValueError('Bieglosc: liczba dodatnia.')
    value=int(raw)
    limit=effective_number(cap('bieglosc'))
    if not 1<=value<=limit:
        raise ValueError(f'Bieglosc: poziom 1-{limit}; zmien przez admin live limity.')
    return _class_matrix(session,turns,page,mastery=value)


async def dispatch_v63(session,group,raw):
    bits=str(raw or '').strip().split()
    if not ((group=='pomoc' and bits==['18']) or
            (group=='arena' and bits[:2]==['klasy','porownaj'])):
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    try:
        if group=='pomoc':answer=HELP
        elif 2<=len(bits)<=5:answer=class_comparison(session,*(bits[2:]))
        else:raise ValueError('arena klasy porownaj [TURY] [STRONA] [BIEGLOSC]')
    except (ValueError,KeyError,OverflowError,TypeError,AttributeError,ZeroDivisionError) as exc:
        answer='ADMIN LIVE V63: '+str(exc)[:300]
    await session.send(answer)
    return True
