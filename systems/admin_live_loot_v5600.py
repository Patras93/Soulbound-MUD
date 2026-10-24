# -*- coding: utf-8 -*-
"""Admin Live v56 normal loot read-only forecast, NVDA-friendly."""
from systems.endless_loot_v5600 import source_template_v5600,preview_normal_equipment_drop_v5600

HELP = ('ADMIN LIVE POMOC 11: eq drop ZRODLO PIETRO ID_PRZEDMIOTU. '
        'Zrodla: krypta, mityczna_krypta, astral, mityczny_astral, magitek. '
        'Tylko podglad zwyklego EQ ponad etapem 600, bez tworzenia i losowania. '
        'Unikaty UOSS, materialy i klucze bez zmian.')

async def dispatch_v56(session,group,raw):
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return True
    bits=str(raw or '').strip().split()
    try:
        if group=='pomoc' and bits==['11']:
            result=HELP
        elif group=='eq' and bits and bits[0]=='drop':
            if bits==['drop','pomoc']:
                result=HELP
            elif len(bits)==4:
                result=preview_normal_equipment_drop_v5600(
                    bits[3],source_template_v5600(bits[1],bits[2]))
            else:
                raise ValueError('Uzyj: admin live eq drop krypta 901 leather_vest.')
        else:
            return False
    except (ValueError,TypeError,OverflowError) as exc:
        result='ADMIN LIVE DROP: '+str(exc)[:250]
    await session.send(result)
    return True
