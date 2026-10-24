# -*- coding: utf-8 -*-
"""Owner-only equipment/chest previews for v58."""
from systems.endless_chest_equipment_v5800 import preview_chest_equipment_v5800
HELP=('ADMIN LIVE POMOC 13: skrzynie eq ZRODLO PIETRO - szansa na dodatkowy '
      'Rezonans Glebi w skrzyniach bossow (ponad etap 800). '
      'Zrodla: krypta, mityczna_krypta, wieza, mityczna_wieza. '
      'Bez losowania i zmian w bazie. Oryginalne nagrody pozostaja.')
async def dispatch_v58(session,group,raw):
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.');return True
    parts=str(raw or '').strip().split()
    try:
        if group=='pomoc' and parts==['13']:message=HELP
        elif group=='skrzynie' and len(parts)==1 and parts[0]=='eq':message=HELP
        elif group=='skrzynie' and len(parts)==3 and parts[0]=='eq':
            message=preview_chest_equipment_v5800(parts[1],parts[2])
        else:return False
    except (ValueError,TypeError,OverflowError) as exc:
        message='ADMIN LIVE SKRZYNIA EQ: '+str(exc)[:240]
    await session.send(message)
    return True
