# -*- coding: utf-8 -*-
"""v115: regional rare materials and recipes for EXISTING professions/tools.

All acquisition flows through a successful native gather in a verified v115
room. No global loot changes, new tools, audio, or bypass of native cooldowns.
"""
from __future__ import annotations
import random
import logging
from data import catalog_mutations as mutations
from .profession_sites import site_for_room

MIN_LEVEL = 800
MATERIALS = {
    'fishing': ('v115_abyss_fish', 'v115_star_fish'),
    'mining': ('v115_aether_ore', 'v115_star_ore'),
    'woodcutting': ('v115_soulwood', 'v115_starwood'),
    'herbalism': ('v115_moonleaf', 'v115_starleaf'),
}
_NAMES = {
    'v115_abyss_fish': 'Ryba Głębin Horyzontów',
    'v115_star_fish': 'Gwiezdna Ryba Horyzontów',
    'v115_aether_ore': 'Ruda Eteru',
    'v115_star_ore': 'Ruda Gwiezdnego Serca',
    'v115_soulwood': 'Drewno Dusz Horyzontów',
    'v115_starwood': 'Gwiezdne Drewno Horyzontów',
    'v115_moonleaf': 'Księżycowy Liść Horyzontów',
    'v115_starleaf': 'Gwiezdny Liść Horyzontów',
}
_OUTPUTS = {
    'v115_soul_plank': {'name':'Deska Dusz', 'type':'craft_material', 'sell_gold':100},
    'v115_star_plank': {'name':'Deska Gwiezdnego Drzewa', 'type':'craft_material', 'sell_gold':250},
    'v115_ether_charm': {'name':'Talizman Eterycznej Straży', 'type':'armor', 'slot':'charm', 'defense':165, 'rarity':'crafted', 'rarity_name':'Rzemieślniczy', 'stats':{'constitution':100,'willpower':100}},
    'v115_star_charm': {'name':'Talizman Gwiezdnej Straży', 'type':'armor', 'slot':'charm', 'defense':300, 'rarity':'crafted', 'rarity_name':'Rzemieślniczy', 'stats':{'constitution':180,'willpower':180}},
    'v115_abyss_feast': {'name':'Uczta Głębin Horyzontów', 'type':'consumable', 'heal':5000, 'mana':3000},
    'v115_star_feast': {'name':'Gwiezdna Uczta Horyzontów', 'type':'consumable', 'heal':12000, 'mana':8000},
    'v115_moon_elixir': {'name':'Eliksir Księżycowego Liścia', 'type':'consumable', 'heal':4000, 'mana':4000},
    'v115_star_elixir': {'name':'Eliksir Gwiezdnego Liścia', 'type':'consumable', 'heal':10000, 'mana':10000},
}


def register_items(items):
    """Add definitions once via existing catalog provenance API."""
    for ident, name in _NAMES.items():
        if ident in items:
            if items[ident].get('name') != name: raise ValueError('Kolizja materiału v115: '+ident)
            continue
        mutations.catalog_assign({'name':name, 'type':'craft_material', 'price':None,
                                  'sell_gold':100 if ident.endswith(('star_ore','starwood','starleaf','star_fish')) else 35,
                                  'desc':'Rzadki surowiec z wysokopoziomowych krain v115. Wymaga istniejącego narzędzia.'},
                                 'ITEMS',items,(ident,))
    for ident, info in _OUTPUTS.items():
        if ident in items:
            if items[ident].get('name') != info['name']: raise ValueError('Kolizja wyrobu v115: '+ident)
            continue
        mutations.catalog_assign({'price':None,'desc':'Wytwarzany z nowych materiałów krain Horyzontów.',**info},
                                 'ITEMS',items,(ident,))


def _recipe(name, inputs, output, stations, level, *, tool_type=None):
    row={'name':name,'ingredients':inputs,'output':output,'quantity':1,
         'stations':stations,'min_tool_level':level,'min_profession_level':level,
         'profession_xp':max(30,level//5),'tool_xp':max(25,level//6),
         'desc':f'Receptura Horyzontów; wymaga poziomu profesji i narzędzia {level}.'}
    if tool_type: row['tool_type']=tool_type
    return row


def register_recipes(craft, cook, alchemy):
    """No new profession: native tool, station, ingredient, XP and transaction."""
    tables=(
        (craft, 'CRAFT_RECIPES', {
            'v115_soul_plank':_recipe('Deska Dusz',{'v115_soulwood':2},'v115_soul_plank',('lumberjack_camp',),800,tool_type='carpentry'),
            'v115_star_plank':_recipe('Deska Gwiezdnego Drzewa',{'v115_starwood':2},'v115_star_plank',('lumberjack_camp',),1600,tool_type='carpentry'),
            'v115_ether_charm':_recipe('Talizman Eterycznej Straży',{'v115_aether_ore':3,'v115_soul_plank':1},'v115_ether_charm',('forge',),800),
            'v115_star_charm':_recipe('Talizman Gwiezdnej Straży',{'v115_star_ore':3,'v115_star_plank':1},'v115_star_charm',('forge',),1600),
        }),
        (cook,'COOK_RECIPES',{
            'v115_abyss_feast':_recipe('Uczta Głębin Horyzontów',{'v115_abyss_fish':2,'v115_moonleaf':1},'v115_abyss_feast',('inn','fish_market'),800),
            'v115_star_feast':_recipe('Gwiezdna Uczta Horyzontów',{'v115_star_fish':2,'v115_starleaf':1},'v115_star_feast',('inn','fish_market'),1600),
        }),
        (alchemy,'ALCHEMY_RECIPES',{
            'v115_moon_elixir':_recipe('Eliksir Księżycowego Liścia',{'v115_moonleaf':2,'v115_aether_ore':1},'v115_moon_elixir',('herbalist_hut',),800),
            'v115_star_elixir':_recipe('Eliksir Gwiezdnego Liścia',{'v115_starleaf':2,'v115_star_ore':1},'v115_star_elixir',('herbalist_hut',),1600),
        }),
    )
    for catalog, key, recipes in tables:
        for ident, recipe in recipes.items():
            if ident in catalog:
                if catalog[ident] != recipe:
                    # Native recipe normalization may remove a redundant
                    # min_tool_level when min_profession_level already exists.
                    comparison = dict(recipe)
                    if 'min_tool_level' not in catalog[ident]:
                        comparison.pop('min_tool_level', None)
                    if catalog[ident] != comparison:
                        raise ValueError('Kolizja receptury v115: '+ident)
                continue
            mutations.catalog_assign(recipe,key,catalog,(ident,))


def material_for(room_id, room, profession, profession_level, roll):
    """Rare *additional* material after a successful native collection.

    First 15 regions use level 800, regions 16–30 level 1600. Early
    rooms remain open to everyone; only bonus material has a level gate.
    """
    site = site_for_room(room_id,room)
    if not site or site['kind'] != profession or profession not in MATERIALS:
        return None
    if type(profession_level) is not int or type(roll) not in (int,float):
        return None
    idx = int(str(room.get('v115_region_key')).rsplit('_',1)[-1])
    tier = 0 if idx <= 15 else 1
    if profession_level < (800 if tier==0 else 1600):
        return None
    if not 0 <= roll < 0.25:
        return None
    return MATERIALS[profession][tier]


async def grant_after_native_gather(session, profession):
    """Best-effort regional BONUS: never changes the completed native gather."""
    try:
        from core.classes_skills import ROOMS
        rid = session.character.room_id
        room = ROOMS.get(rid)
        if not isinstance(room,dict) or not site_for_room(rid,room):
            return None
        lvl = int(session.profession_level_for_tool(profession))
        item_id = material_for(rid,room,profession,lvl,random.random())
        if item_id is None:
            return None
        # add_item routes craft_material to existing craftbox and commits.
        session.server.db.add_item(session.account_id,item_id,1)
        await session.send(f'Rzadki materiał: {_NAMES[item_id]} x1 (Szkatułka Rzemieślnicza).')
        return item_id
    except Exception as exc:
        reporter=getattr(session.server,'report_runtime_error',None)
        if callable(reporter):
            try:
                reporter(exc,command='v115:regional_material',handler=profession)
            except Exception:
                logging.getLogger(__name__).exception(
                    'v115: error reporter failed while recording regional material error')
        return None
