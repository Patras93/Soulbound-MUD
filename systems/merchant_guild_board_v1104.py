# -*- coding: utf-8 -*-
"""v11.00.4: all eight v6 profession tools available in mentor shops;
physical bounty board in the Guild Hall, without new NPCs or changed quests.
"""
import unicodedata
from data.catalog_mutations import catalog_assign
from core.mines_threat import TOOL_SHOP_ROOMS, TOOL_BUY_ALIASES
from systems.new_professions import PROFESSIONS
from systems.profession_paths_v601 import SPEC


def _norm(name):
    return ''.join(ch for ch in unicodedata.normalize('NFKD', name.casefold())
                   if not unicodedata.combining(ch)).strip()


def install(rooms, npcs, shops, shop_sellers, items, topics, aliases):
    registered = {}
    assert 'guild_hall' in rooms
    for prof, (tool_type, item_id, name) in PROFESSIONS.items():
        room_id = 'v601_mentor_' + tool_type
        npc_id = next(row[1] for row in SPEC if row[0] == prof)
        assert room_id in rooms and npc_id in npcs, (prof, room_id, npc_id)
        assert npcs[npc_id]['room'] == room_id
        assert items[item_id]['tool_type'] == tool_type
        assert items[item_id]['type'] == 'tool'
        assert items[item_id]['price'] == 1200
        current = list(shops.get(room_id, ()))
        if item_id not in current:
            catalog_assign(current + [item_id], 'SHOPS', shops, (room_id,))
        shop_sellers[room_id] = npc_id
        npcs[npc_id]['shopkeeper'] = True
        notice = f' Sprzedaję {name} (1200 srebra); wpisz shop, kup <numer> lub kup {name.lower()}. Jedno narzędzie na postać.'
        if notice not in str(npcs[npc_id].get('dialogue', '')):
            npcs[npc_id]['dialogue'] = str(npcs[npc_id].get('dialogue', '')) + notice
        TOOL_SHOP_ROOMS[item_id] = room_id
        # Proper names with and without diacritics; do not shadow generic words
        for alias in (name.casefold(), _norm(name)):
            existing = TOOL_BUY_ALIASES.get(alias)
            if existing is not None and existing != item_id:
                raise RuntimeError(f'Kolizja nazwy narzędzia: {alias}')
            TOOL_BUY_ALIASES[alias] = item_id
        registered[prof] = (room_id, item_id)
    old = str(rooms['guild_hall']['desc'])
    board_text = (' W sali znajduje się Tablica Zleceń Gildii Dusz. '
                  'Wpisz bounty, aby przeczytać oferty; '
                  'bounty przyjmij 1, bounty odbierz, bounty odswiez. '
                  'Dostępne są również zadania bojowe: guildbounty.')
    if 'Tablica Zleceń Gildii Dusz' not in old:
        catalog_assign(old + board_text, 'ROOMS', rooms, ('guild_hall', 'desc'))
    topics['tablica_zlecen'] = [
        'Tablica Zleceń znajduje się w Sali Głównej Gildii Dusz.',
        'W gildii: bounty — lista; bounty przyjmij 1 — przyjęcie; bounty odbierz — nagroda; bounty odswiez — nowe oferty.',
        'Z dowolnego miejsca: bounty aktywne — postęp; bounty porzuc — porzucenie. Zlecenia bojowe: guildbounty.',
        'Zamówienia profesji nadal są na rynku i w porcie: profesja zamowienie <profesja> i profesja oddaj <profesja>.',
    ]
    aliases.update({'tablica':'tablica_zlecen','tablica zlecen':'tablica_zlecen','tablica zleceń':'tablica_zlecen'})
    return {'shop_tools': registered, 'board_room':'guild_hall'}
