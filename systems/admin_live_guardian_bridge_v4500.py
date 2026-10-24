# -*- coding: utf-8 -*-
"""Stable, owner-only `admin live` aliases for Guardian 6-11 services.

This bridge intentionally calls their existing validated handlers: the live
OLC publication model and the private LAB object are not changed here.
"""

HELP = {
    '1': ('ADMIN LIVE ARENA 1/3. start BOSS HP ATAK [POMOCNIK]; '
          'klasa NAZWA BIEGLOSC MANA POTWIERDZAM; skille [STRONA]; '
          'skill ID; atak [CEL]; obrona; lecz; magia ZYW; status. '
          'Tylko test, 0 EXP, 0 nagrod i bez zmian prawdziwej postaci.'),
    '2': ('ADMIN LIVE ARENA 2/3. przedmiot ID; zaloz ID POTWIERDZAM; '
          'zdejmij SLOT POTWIERDZAM; ekwipunek; '
          'sekwencja plan AKCJE; sekwencja wykonaj AKCJE POTWIERDZAM; '
          'sekwencja porownaj AKCJE / AKCJE. '
          'Akcje po przecinku: atak, obrona, lecz, magia:ogien, skill:ID.'),
    '3': ('ADMIN LIVE ARENA 3/3. prognoza TURY; seria TURY; '
          'porownaj TURY; migawka; przywroc POTWIERDZAM; '
          'ziarno LICZBA POTWIERDZAM; dziennik [STRONA]; raport; '
          'wynik; wyjdz. Do 20 tur prognozy lub 12 akcji sekwencji. '
          'To laboratorium UOSS, nie kompletna produkcyjna walka 1:1.'),
}

# Existing handlers remain the single source of rules, validation and rights.
_OLDER_ARENA = {'prognoza','seria','porownaj','migawka','przywroc',
                'dziennik','raport','oczysc'}
_SUPPORTED_ARENA = {'start','klasa','skille','skill','atak','obrona','lecz',
                    'magia','przedmiot','zaloz','zdejmij','ekwipunek',
                    'sekwencja','ziarno','status','wynik','wyjdz'} | _OLDER_ARENA
_QUEST = {
    'audyt':6, 'zaleznosci':6, 'propozycja':6, 'popraw':6,
    'plan':7, 'zmien':7, 'skan':7, 'przeglad':7,
    'seria':8, 'cofnij':8,
    'draft':10,'nagrody':10,'diagnoza':10,'porownaj':10,
}

async def dispatch_live_arena(session, tail):
    if not session.is_admin():
        await session.send('Nieznana komenda. Wpisz help.')
        return
    raw=str(tail or '').strip()
    parts=raw.split()
    action=parts[0].casefold() if parts else ''
    if action in ('pomoc','help',''):
        page=parts[1] if len(parts)>1 else '1'
        if len(parts)>2 or page not in HELP:
            await session.send('ADMIN LIVE ARENA: pomoc 1, 2 lub 3.')
        else:
            await session.send(HELP[page])
        return
    if action not in _SUPPORTED_ARENA:
        await session.send('ADMIN LIVE ARENA: nieznana opcja. Wpisz admin live arena pomoc.')
        return
    if action in _OLDER_ARENA:
        from systems.admin_guardian10_v4400 import handle_guardian10
        await handle_guardian10(session,'guardian10 arena '+raw)
    else:
        from systems.admin_guardian11_v4500 import handle_guardian11
        await handle_guardian11(session,'guardian11 arena '+raw)

async def dispatch_live_quest(session, tail):
    parts=str(tail or '').strip().split()
    action=parts[0].casefold() if parts else ''
    version=_QUEST.get(action)
    if version is None:return False  # Keep legacy `admin live questy PROFESJA`.
    if version == 6:
        from systems.admin_guardian6_v4000 import handle_guardian6 as handle
    elif version == 7:
        from systems.admin_guardian7_v4100 import handle_guardian7 as handle
    elif version == 8:
        from systems.admin_guardian8_v4200 import handle_guardian8 as handle
    else:
        from systems.admin_guardian10_v4400 import handle_guardian10 as handle
    await handle(session,f'guardian{version} questy {tail}')
    return True
