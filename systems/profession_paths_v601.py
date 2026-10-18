# -*- coding: utf-8 -*-
"""v6.00.1: eight real-action 120-stage mentor paths; additive to v6.00.0.

No generated quest consumes an old ID, replaces a trainer, or writes a live DB.
Player quest state persists in the existing quests table.
"""
from __future__ import annotations

from collections import Counter
from config.balance import QUEST_REPEAT_COOLDOWN_SECONDS
from data.catalog_mutations import catalog_assign
from systems.new_professions import PROFESSIONS, BASE_ACTIONS, TIERS, AREAS
from systems.npc_single_room_v3101 import OPPOSITE

CHAPTERS = (
    "Pierwszy warsztat", "Droga czeladnika", "Sprawdzian rzemiosła",
    "Służba krainie", "Próba cechu", "Trudne zamówienia",
    "Rzemiosło odległych stron", "Mistrzowska precyzja", "Powołanie arcymistrza",
    "Dziedzictwo rzemiosła", "Legenda fachu", "Droga bez kresu",
)
# Each of the twelve chapters has ten different actions, with a skill / tool
# difficulty that tracks levels 1..800 and their actual material requirements.
SPEC = (
    ("Łowiectwo", "v601_hunting_master", "Łowczyni Runa", "meadow",
     "Pracownia Tropicieli", "Tropienie i oprawa prawdziwej zwierzyny.", "hunt_meat"),
    ("Rolnictwo", "v601_farming_master", "Rolniczka Mira", "mint_meadow",
     "Gospodarstwo Mistrzyni Upraw", "Siew, zbiór i przetwarzanie plonów.", "v600_seeds"),
    ("Hodowla zwierząt", "v601_husbandry_master", "Hodowczyni Leda", "lakeside_meadow",
     "Zagroda Mistrzyni Stad", "Pielęgnacja i wykorzystanie produktów zwierzęcych.", "field_grain"),
    ("Okrętownictwo", "v601_shipbuilding_master", "Szkutnik Garven", "harbor",
     "Stocznia Mistrza Okrętów", "Poszycia, wyposażenie i naprawa kadłubów.", "oak_plank"),
    ("Murarstwo", "v601_masonry_master", "Murarka Telda", "forge",
     "Warsztat Mistrzyni Kamienia", "Obróbka, fundamenty i wznoszenie ścian.", "stone_chunk"),
    ("Inżynieria", "v601_engineering_master", "Mechanik Dorven", "market",
     "Pracownia Mistrza Mechanizmów", "Montaż, projektowanie i kalibracja urządzeń.", "iron_ingot"),
    ("Kupiectwo", "v601_trading_master", "Kupczyni Selma", "fish_market",
     "Izba Mistrzyni Handlu", "Pakowanie, wycena i bezpieczne dostawy.", "trade_crate"),
    ("Żeglarstwo", "v601_sailing_master", "Nawigatorka Eryna", "sea_pier",
     "Szkoła Mistrzyni Żeglugi", "Kursy, rejsy i dzienniki wypraw.", "navigation_chart"),
)

QUEST_IDS_BY_PROFESSION = {}
ALL_QUEST_IDS = []
ROOM_IDS = {}


def _new(catalog, name, key, value):
    if key in catalog:
        raise RuntimeError(f"v6.00.1 niebezpieczna kolizja {name}: {key}")
    catalog_assign(value, name, catalog, (key,))


def _join(rooms, original, target):
    if original not in rooms:
        raise RuntimeError("v6.00.1 brak dostępnej lokacji: " + original)
    for direction in ('north','east','west','south','northeast','northwest',
                      'southeast','southwest','up','down'):
        other = OPPOSITE[direction]
        if direction not in rooms[original]['exits'] and other not in rooms[target]['exits']:
            catalog_assign(target, 'ROOMS', rooms, (original,'exits',direction))
            catalog_assign(original, 'ROOMS', rooms, (target,'exits',other))
            return direction
    raise RuntimeError("v6.00.1 brak wolnego wyjścia przy " + original)


def stage_level(index):
    """All 120 stages cover the full 1..800; endpoints are exact."""
    if not 0 <= index < 120:
        raise ValueError(index)
    return 1 + 799 * index // 119


def stage_tier(level):
    return max(t for t in TIERS if t <= level)


def install(rooms, npcs, quests, items):
    """Call once from server.py before the one-NPC-per-room pass."""
    if ALL_QUEST_IDS:
        raise RuntimeError('v6.00.1: próba podwójnej rejestracji Drogi Mistrza')
    if set(PROFESSIONS) != {row[0] for row in SPEC}:
        raise RuntimeError('v6.00.1: niezgodne katalogi nowych profesji')
    for profession, npc_id, npc_name, anchor, room_name, activity, supply in SPEC:
        tool_type, _, _ = PROFESSIONS[profession]
        actions = [a for a in BASE_ACTIONS if a.prof == profession]
        if not actions or supply not in items:
            raise RuntimeError(f'v6.00.1 brak prac/nagród dla {profession}')
        room_id = 'v601_mentor_' + tool_type
        _new(rooms,'ROOMS',room_id,{
            'zone': rooms[anchor]['zone'] if anchor in rooms else 'Miasto Dusz',
            'name': room_name,
            'desc': (f'{npc_name} prowadzi tutaj drogę mistrzowską profesji {profession}. '
                     'Każdy etap wymaga prawdziwych działań, surowców i narzędzia. '
                     'Drogę powrotną znajdziesz przez jedyne wyjście.'),
            'exits':{},'generator_level':1,'v601_profession_mentor':True,
        })
        _join(rooms, anchor, room_id)
        rows = []
        previous = None
        for idx in range(120):
            stage = idx+1
            level = stage_level(idx)
            tier = stage_tier(level)
            action = actions[(idx + idx//10) % len(actions)]
            # Real material / processing difficulty comes from work_for() in
            # profesje6; this quest demands its named action at this tier.
            count = 3 + idx//5 + (idx%10)//3
            reward_prof = 1500 + int(55 * level**1.4) + (idx%10)*250
            reward_tool = int(reward_prof*0.7)
            reward_silver = 2400 + level*320 + idx*190
            supplies = {supply: 2 + idx//10} if stage % 10 == 0 else {}
            qid = f'v601_path_{tool_type}_{stage:03d}'
            chapter = CHAPTERS[idx//10]
            quest = {
                'name': f'Droga Mistrza {profession}: {chapter}, próba {idx%10+1}',
                'giver':npc_name,
                'kind':'profession_action',
                'target':profession,
                'needed':count,
                'description':(
                    f'Etap {stage} z 120 (poziom orientacyjny {level}). '
                    f'Wykonaj {count} razy czynność „{action.title}” '
                    f'komendą profesja praca {profession} {action.code} {tier}. '
                    f'Wymagany próg pracy co najmniej {tier}; czynność wykonuj '
                    'po przyjęciu zadania, w odpowiednim terenie, zużywając rzeczywiste materiały.'
                ),
                'required_profession':profession,
                'min_profession_level':level,
                'generator_level':level,
                'specialist_tool_type':tool_type,
                'required_action_code':action.code,
                'min_action_tier':tier,
                'reward_profession':profession,
                'reward_profession_xp':reward_prof,
                'reward_tool_type':tool_type,
                'reward_tool_xp':reward_tool,
                'reward_silver':reward_silver,
                'reward_gold':0,'reward_mithril':0,
                'reward_items':supplies,
                'repeatable':False,
                'v601_profession_path':True,
                'v601_stage':stage,
            }
            if previous:
                quest['requires_quest']=previous
            _new(quests,'QUESTS',qid,quest)
            previous=qid
            rows.append(qid)
            ALL_QUEST_IDS.append(qid)
        _new(npcs,'NPCS',npc_id,{
            'name':npc_name, 'room':room_id,
            'rank_profession':profession,
            'dialogue':(
                f'{npc_name}: {activity} Prowadzę 120 etapów Drogi Mistrza '
                f'dla {profession}, od ucznia do poziomu 800. '
                'Wpisz quest list, a następnie przyjmij 1. '
                'Zadania ukończone zapisują się na stałe.'
            ),
            'specialist_tool_type':tool_type,
            'specialist_topic':'profesje6',
            'strict_profession_quests':profession,
            'specialist_quests':tuple(rows),
            'v601_profession_master':True,
        })
        QUEST_IDS_BY_PROFESSION[profession]=tuple(rows)
        ROOM_IDS[profession]=room_id
    if len(ALL_QUEST_IDS) != 960 or any(len(ids)!=120 for ids in QUEST_IDS_BY_PROFESSION.values()):
        raise RuntimeError('v6.00.1: niekompletne ścieżki')
    return {'professions':8, 'quests':len(ALL_QUEST_IDS),
            'per_profession':120,'mentors':8,'rooms':8}
