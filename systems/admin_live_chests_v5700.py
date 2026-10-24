# -*- coding: utf-8 -*-
"""v57 owner-only NVDA-friendly chest payout preview."""
from systems.endless_chests_v5700 import preview_chest_extension_v5700

HELP=('ADMIN LIVE POMOC 12: skrzynie ZRODLO PIETRO BAZOWE_ZLOTO. '
      'Zrodla: krypta, mityczna_krypta, magitek. '
      'Prognoza zlota po premii ponad 800. Bez losowania i zapisu. '
      'Stare skrzynie, klucze, przedmioty i zasady druzyny bez zmian.')

async def dispatch_v57(session,group,raw):
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    args=str(raw or '').strip().split()
    try:
        if group=='pomoc' and args==['12']:
            result=HELP
        elif group=='skrzynie' and args==['pomoc']:
            result=HELP
        elif group=='skrzynie' and len(args)==3:
            result=preview_chest_extension_v5700(*args)
        elif group=='skrzynie':
            raise ValueError('Uzyj: admin live skrzynie krypta 901 1000.')
        else:return False
    except (ValueError,TypeError,OverflowError) as exc:
        result='ADMIN LIVE SKRZYNIA: '+str(exc)[:240]
    await session.send(result)
    return True
