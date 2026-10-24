# -*- coding: utf-8 -*-
"""Admin Live v55: read-only forecast for actual post-800 crafting."""
from __future__ import annotations
from core import live_level_caps_v5200 as caps
from systems.endless_crafting_v5500 import craft_stage_v5500
from systems.infinite_equipment import infinite_equipment_power_multiplier

HELP = ('ADMIN LIVE POMOC 10: eq craft POZIOM_PROFESJI POZIOM_NARZEDZIA - '
    'prognoza Rezonansu Rzemiosla >800. Receptury, materialy i jakosc dzialaja '
    'normalnie, bez darmowych przedmiotow. Ustaw limity profesje, narzedzia, eq '
    'i bieglosc powyzej 800 w admin live limity. Podglad nie tworzy EQ i nie zmienia gry.')


def craft_forecast(profession_level, tool_level):
    parts=(str(profession_level),str(tool_level))
    if any(not s.isascii() or not s.isdecimal() or len(s)>10 or not 1<=int(s)<=1_000_000_000 for s in parts):
        raise ValueError('EQ CRAFT: podaj dwa poziomy 1..1000000000.')
    prof,tool=map(int,parts)
    stage=craft_stage_v5500(prof,tool)
    if stage is None:
        return (f'EQ CRAFT: profesja {prof}, narzedzie {tool}. '
                'Bez Rezonansu: obie dziedziny musza przekroczyc 800 i limit EQ >800. '
                'Standardowa jakosc i koszty bez zmian. Nic nie stworzono.')
    rank=(stage-600)//10
    mast=caps.cap('bieglosc')
    warn=('UWAGA: limit bieglosci jest nizszy od wymagan; nie zalozysz tego EQ bez '
          'wyzszego poziomu klasy. ' if mast is not None and mast<stage else '')
    return (f'EQ CRAFT: profesja {prof}, narzedzie {tool}; etap {stage}; '
            f'wymagana bieglosc {stage}; Rezonans {rank}; '
            f'mnoznik zwykly x{infinite_equipment_power_multiplier(rank,"r"):.3f}; '
            f'mistrzowski x{infinite_equipment_power_multiplier(rank,"e"):.3f}. '
            +warn+'Wymagania, koszty materialow i jakosc craftu pozostaja bez zmian. '
            'Podglad bez zmian w ekwipunku i bazie.')


async def dispatch_v55(session,group,raw):
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return True
    args=str(raw or '').strip().split()
    try:
        if group=='pomoc' and args==['10']:
            result=HELP
        elif group=='eq' and args and args[0]=='craft':
            if len(args)==2 and args[1]=='pomoc':result=HELP
            elif len(args)==3:result=craft_forecast(args[1],args[2])
            else:raise ValueError('Uzyj: admin live eq craft 1000 930.')
        else:return False
    except (ValueError,OverflowError,TypeError) as exc:
        result='ADMIN LIVE EQ: '+str(exc)[:250]
    await session.send(result)
    return True
