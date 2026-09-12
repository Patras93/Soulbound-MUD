#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Soulbound v0.6.72 Temple Login Spawn
Wieloosobowy tekstowy MUD TCP/Telnet dla MUSHclienta/Mudleta.

Najważniejsze zasady projektu:
- postać NIE ma levelu ani XP postaci,
- statystyki rosną automatycznie,
- każda klasa rozwija automatycznie wszystkie pięć statystyk,
- Broń Duszy ma osobny Soul Level 1-200,
- Soul Tier 1-3 odblokowuje się osobno,
- wszystkie trwałe dane gracza są zapisywane w SQLite.
"""

import asyncio
import hashlib
import hmac
import os
import random
import re
import secrets
import sqlite3
import sys
import time
import unicodedata
from dataclasses import dataclass
from typing import Optional

VERSION = "0.6.72"

HOST = os.getenv("SOULBOUND_HOST", "0.0.0.0")
_RAILWAY_TCP_PORT = os.getenv("RAILWAY_TCP_APPLICATION_PORT", "").strip()
_SOULBOUND_PORT = os.getenv("SOULBOUND_PORT", "").strip()
_GENERIC_PORT = os.getenv("PORT", "").strip()

if _RAILWAY_TCP_PORT:
    PORT = int(_RAILWAY_TCP_PORT)
elif _SOULBOUND_PORT:
    PORT = int(_SOULBOUND_PORT)
elif _GENERIC_PORT:
    PORT = int(_GENERIC_PORT)
else:
    PORT = 4000

_VOLUME_PATH = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "").strip()
_DEFAULT_DB = os.path.join(_VOLUME_PATH, "soulbound.db") if _VOLUME_PATH else "soulbound.db"
DB_PATH = os.getenv("SOULBOUND_DB", _DEFAULT_DB)

MAX_CLIENTS = int(os.getenv("SOULBOUND_MAX_CLIENTS", "100"))
PBKDF2_ROUNDS = 210_000

STAT_GROWTH_THRESHOLD = 50
SOUL_MAX_LEVEL = 200
TIER2_LEVEL = 25
TIER3_LEVEL = 60
REGULAR_MOB_RESPAWN_SECONDS = 120
BOSS_RESPAWN_SECONDS = 300
TRAINING_DUMMY_RESPAWN_SECONDS = 60
CORPSE_LIFETIME_SECONDS = 600
QUEST_REPEAT_COOLDOWN_SECONDS = 30 * 60

# Ekonomia:
# 1000 srebra = 1 złoto
# 1 000 000 złota = 1 mithril
SILVER_PER_GOLD = 1000
GOLD_PER_MITHRIL = 1000000

PROFESSION_MAX_LEVEL = 100
CHARISMA_DISCOUNT_STEP = 4
CHARISMA_MAX_DISCOUNT = 25
PARTY_BASE_CAPACITY = 8
PARTY_CHARISMA_STEP = 25

PROFESSION_MAX_RANK = 8
PROFESSION_RANK_THRESHOLDS = (1, 15, 30, 45, 60, 75, 90, 100)

PROFESSION_RANK_NAMES = {
    "Wędkarstwo": (
        "Uczeń Wędkarstwa",
        "Adept Wędkarstwa",
        "Czeladnik Wędkarstwa",
        "Specjalista Wędkarstwa",
        "Ekspert Wędkarstwa",
        "Mistrz Wędkarstwa",
        "Arcymistrz Wędkarstwa",
        "Legenda Wędkarstwa",
    ),
    "Górnictwo": (
        "Uczeń Górnictwa",
        "Adept Górnictwa",
        "Czeladnik Górnictwa",
        "Specjalista Górnictwa",
        "Ekspert Górnictwa",
        "Mistrz Górnictwa",
        "Arcymistrz Górnictwa",
        "Legenda Górnictwa",
    ),
    "Drwalstwo": (
        "Uczeń Drwalstwa",
        "Adept Drwalstwa",
        "Czeladnik Drwalstwa",
        "Specjalista Drwalstwa",
        "Ekspert Drwalstwa",
        "Mistrz Drwalstwa",
        "Arcymistrz Drwalstwa",
        "Legenda Drwalstwa",
    ),
    "Zielarstwo": (
        "Uczeń Zielarstwa",
        "Adept Zielarstwa",
        "Czeladnik Zielarstwa",
        "Specjalista Zielarstwa",
        "Ekspert Zielarstwa",
        "Mistrz Zielarstwa",
        "Arcymistrz Zielarstwa",
        "Legenda Zielarstwa",
    ),
    "Alchemia": (
        "Uczeń Alchemii",
        "Adept Alchemii",
        "Czeladnik Alchemii",
        "Specjalista Alchemii",
        "Ekspert Alchemii",
        "Mistrz Alchemii",
        "Arcymistrz Alchemii",
        "Legenda Alchemii",
    ),
}

def normalize_profession_name(profession):
    value = str(profession).strip().lower()
    if value in ("fishing", "wedkarstwo", "wędkarstwo"):
        return "Wędkarstwo"
    if value in ("mining", "gornictwo", "górnictwo"):
        return "Górnictwo"
    if value in ("woodcutting", "drwalstwo", "drwal"):
        return "Drwalstwo"
    if value in ("herbalism", "zielarstwo", "zielarz"):
        return "Zielarstwo"
    if value in ("alchemy", "alchemia"):
        return "Alchemia"
    return str(profession)

def profession_rank(level):
    level = max(1, min(PROFESSION_MAX_LEVEL, int(level)))
    rank = 1
    for number, minimum in enumerate(PROFESSION_RANK_THRESHOLDS, 1):
        if level >= minimum:
            rank = number
        else:
            break
    return rank

def profession_rank_name(profession, level):
    profession = normalize_profession_name(profession)
    rank = profession_rank(level)
    return PROFESSION_RANK_NAMES[profession][rank - 1]

TOOL_MAX_LEVEL = 200
TOOL_MAX_TIER = 13
TOOL_TIER_THRESHOLDS = (
    1, 15, 30, 45, 60, 75, 90, 100,
    120, 140, 160, 180, 200,
)
TOOL_TIER_BONUS_CHANCES = (
    0.00, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12,
    0.15, 0.18, 0.21, 0.24, 0.27, 0.30,
)

def tool_max_level(tool_type):
    return TOOL_MAX_LEVEL

TOOL_TIER_NAMES = {
    "fishing": (
        "Wędka Ucznia",
        "Wędka Rzeczna",
        "Wędka Srebrnego Haczyka",
        "Wędka Morskiego Wiatru",
        "Wędka Głębin",
        "Wędka Mistrza Połowu",
        "Wędka Legendarnego Wędkarza",
        "Wędka Mitycznych Głębin",
        "Wędka Otchłannego Łowcy",
        "Wędka Władcy Oceanów",
        "Wędka Astralnego Połowu",
        "Wędka Pradawnych Głębin",
        "Wędka Wiecznego Oceanu",
    ),
    "mining": (
        "Kilof Ucznia",
        "Kilof Górnika",
        "Kilof Stalowego Ostrza",
        "Kilof Hartowanego Rdzenia",
        "Kilof Kryształowej Żyły",
        "Kilof Mistrza Kopalni",
        "Kilof Legendarnych Złóż",
        "Kilof Mitycznego Rdzenia",
        "Kilof Runicznej Żyły",
        "Kilof Smoczego Kruszcu",
        "Kilof Astralnej Rudy",
        "Kilof Pradawnego Mithrilu",
        "Kilof Serca Świata",
    ),
    "woodcutting": (
        "Piła Ucznia",
        "Piła Leśna",
        "Piła Stalowych Zębów",
        "Piła Hartowanego Ostrza",
        "Piła Żelaznego Dębu",
        "Piła Mistrza Drwali",
        "Piła Legendarnych Pni",
        "Piła Mitycznego Gaju",
        "Piła Runicznego Lasu",
        "Piła Smoczego Drewna",
        "Piła Astralnego Gaju",
        "Piła Pradawnego Drzewa",
        "Piła Drzewa Świata",
    ),
    "crafting": (
        "Młot Rzemieślnika Ucznia",
        "Młot Żelaznego Kowadła",
        "Młot Stalowego Rzemiosła",
        "Młot Hartowanego Rdzenia",
        "Młot Runicznego Kowadła",
        "Młot Mistrza Rzemiosła",
        "Młot Legendarnego Twórcy",
        "Młot Mitycznego Kowadła",
        "Młot Arcyrzemieślnika",
        "Młot Smoczej Kuźni",
        "Młot Astralnego Twórcy",
        "Młot Pradawnej Kuźni",
        "Młot Wiecznego Kowadła",
    ),
    "cooking": (
        "Nóż Kucharski Ucznia",
        "Nóż Karczemnej Kuchni",
        "Nóż Stalowego Ostrza",
        "Nóż Szefa Kuchni",
        "Nóż Mistrza Smaku",
        "Nóż Wielkiego Kucharza",
        "Nóż Legendarnej Uczty",
        "Nóż Mitycznego Szefa",
        "Nóż Królewskiej Uczty",
        "Nóż Smoczej Kuchni",
        "Nóż Astralnego Smaku",
        "Nóż Pradawnej Uczty",
        "Nóż Wiecznego Szefa",
    ),
    "herbalism": (
        "Sierp Zielarski Ucznia",
        "Sierp Łąkowy",
        "Sierp Leśnych Ziół",
        "Sierp Srebrnego Ostrza",
        "Sierp Głębokiego Gaju",
        "Sierp Mistrza Zielarstwa",
        "Sierp Legendarnych Ziół",
        "Sierp Mitycznego Ogrodu",
        "Sierp Runicznego Zielnika",
        "Sierp Smoczego Ogrodu",
        "Sierp Astralnych Ziół",
        "Sierp Pradawnej Flory",
        "Sierp Wiecznego Ogrodu",
    ),
    "alchemy": (
        "Moździerz Alchemika Ucznia",
        "Moździerz Kamienny",
        "Moździerz Srebrnego Pyłu",
        "Moździerz Runiczny",
        "Moździerz Mistycznej Esencji",
        "Moździerz Mistrza Alchemii",
        "Moździerz Legendarnego Eliksiru",
        "Moździerz Mitycznej Transmutacji",
        "Moździerz Arcyalchemika",
        "Moździerz Smoczej Esencji",
        "Moździerz Astralnej Transmutacji",
        "Moździerz Pradawnego Eliksiru",
        "Moździerz Wiecznej Alchemii",
    ),
}

def tool_tier(level):
    level = max(1, min(TOOL_MAX_LEVEL, int(level)))
    tier = 1
    for number, minimum in enumerate(TOOL_TIER_THRESHOLDS, 1):
        if level >= minimum:
            tier = number
        else:
            break
    return tier

def tool_tier_name(tool_type, level):
    tier = tool_tier(level)
    names = TOOL_TIER_NAMES.get(tool_type, TOOL_TIER_NAMES["mining"])
    return names[tier - 1]

def tool_tier_bonus_chance(level):
    return TOOL_TIER_BONUS_CHANCES[tool_tier(level) - 1]

CLASS_MASTERY_MAX_LEVEL = 100
CLASS_MASTERY_XP_BASE = 1000
CLASS_MASTERY_XP_STEP = 250
MULTICLASS_MAX_ACTIVE = 3

def class_mastery_xp_to_next(level):
    level = max(1, min(CLASS_MASTERY_MAX_LEVEL, int(level)))
    if level >= CLASS_MASTERY_MAX_LEVEL:
        return 0
    return CLASS_MASTERY_XP_BASE + (level - 1) * CLASS_MASTERY_XP_STEP

def class_type_for_name(class_name):
    for cname, ctype, weapon, base in CLASSES:
        if cname == class_name:
            return ctype
    return "physical"

SKILL_MAX_LEVEL = 100
SKILL_XP_BASE = 50
SKILL_XP_STEP = 25

def skill_xp_to_next(level):
    if level >= SKILL_MAX_LEVEL:
        return 0
    return SKILL_XP_BASE + (level - 1) * SKILL_XP_STEP

def skill_power_multiplier(level):
    # L1 = 1.0, L100 ~= 1.7425
    return 1.0 + max(0, level - 1) * 0.0075

def skill_cooldown_multiplier(level):
    # Do 30% krótszego cooldownu na L100.
    reduction = min(0.30, max(0, level - 1) * 0.003)
    return 1.0 - reduction

PROFESSION_COOLDOWN = 2.0
REST_TICK_SECONDS = 5.0
REST_REGEN_PERCENT = 10

RIVER_FISHING_ROOMS = {"riverbank", "stone_bridge"}
LAKE_FISHING_ROOMS = {"lake_shore"}
SEA_FISHING_ROOMS = {"sea_pier"}
OCEAN_FISHING_ROOMS = {"ocean_platform"}
FRESHWATER_FISHING_ROOMS = RIVER_FISHING_ROOMS | LAKE_FISHING_ROOMS
MARINE_FISHING_ROOMS = SEA_FISHING_ROOMS | OCEAN_FISHING_ROOMS
FISHING_ROOMS = FRESHWATER_FISHING_ROOMS | MARINE_FISHING_ROOMS
MINING_ROOMS = {"cave_entrance", "cave_tunnel", "crystal_chamber"}
WOODCUTTING_ROOMS = {"lumberjack_camp", "meadow", "whisper_grove", "deep_grove", "old_road"}
HERBALISM_ROOMS = {
    "herbalist_hut", "meadow", "whisper_grove", "deep_grove",
    "riverbank", "lake_shore", "old_road"
}

FISH_RESOURCE_IDS = {
    # Rzeka
    "small_fish", "river_carp", "river_perch", "dace", "chub", "common_nase",
    "barbel", "ide", "asp", "grayling", "burbot", "pike", "zander",
    "silver_trout", "golden_trout", "salmon", "river_catfish",
    "ancient_sturgeon", "moon_eel",
    # Jezioro
    "lake_roach", "rudd", "crucian_carp", "bream", "tench", "lake_perch",
    "vendace", "whitefish", "lake_char", "lake_trout", "pike", "zander",
    "giant_pike", "freshwater_eel",
    # Morze
    "sprat", "sardine", "anchovy", "herring", "mackerel", "whiting",
    "cod", "hake", "sea_bass", "red_mullet", "haddock", "pollock",
    "flounder", "sole", "halibut", "turbot", "monkfish",
    # Ocean
    "tuna", "albacore", "bigeye_tuna", "mahi_mahi", "wahoo",
    "barracuda", "cobia", "amberjack", "sailfish", "swordfish",
    "bluefin_tuna", "ocean_sunfish", "reef_shark", "mako_shark",
    "tiger_shark", "hammerhead_shark", "great_white_shark", "ghost_marlin",
}
ORE_RESOURCE_IDS = {
    "stone_chunk", "copper_ore", "iron_ore",
    "silver_ore", "gold_ore",
}
WOOD_RESOURCE_IDS = {
    "fallen_branch", "birch_log", "alder_log", "pine_log", "poplar_log",
    "willow_log", "linden_log", "oak_log", "beech_log", "maple_log",
    "ash_log", "chestnut_log", "walnut_log", "cedar_log", "yew_log",
    "mahogany_log", "teak_log", "redwood_log", "ironwood_log", "ebony_log",
    "silverwood_log", "spiritwood_log", "ancient_heartwood", "worldtree_wood",
}

HERB_RESOURCE_IDS = {
    "nettle", "chamomile", "mint", "sage", "lavender", "yarrow",
    "lemon_balm", "valerian", "ginseng", "nightshade", "mandrake",
    "moonflower", "soulroot", "phoenix_leaf", "star_moss", "astral_lotus",
}
HERB_MEADOW_ATLAS = {"nettle", "chamomile", "mint", "yarrow", "lemon_balm", "lavender"}
HERB_FOREST_ATLAS = {"sage", "valerian", "ginseng", "nightshade", "mandrake", "moonflower", "soulroot"}
HERB_WATER_ATLAS = {"mint", "lemon_balm", "star_moss", "moonflower"}
HERB_DEEP_ATLAS = {"mandrake", "moonflower", "soulroot", "phoenix_leaf", "star_moss", "astral_lotus"}

RIVER_FISH_ATLAS = {
    "small_fish", "dace", "river_perch", "chub", "common_nase",
    "river_carp", "barbel", "ide", "asp", "grayling", "burbot",
    "silver_trout", "golden_trout", "pike", "zander", "salmon",
    "river_catfish", "ancient_sturgeon", "moon_eel",
}
LAKE_FISH_ATLAS = {
    "lake_roach", "rudd", "crucian_carp", "bream", "tench",
    "lake_perch", "vendace", "whitefish", "lake_char", "lake_trout",
    "pike", "zander", "giant_pike", "freshwater_eel",
}
SEA_FISH_ATLAS = {
    "sprat", "sardine", "anchovy", "herring", "mackerel", "whiting",
    "cod", "hake", "sea_bass", "red_mullet", "haddock", "pollock",
    "flounder", "sole", "halibut", "turbot", "monkfish",
}
OCEAN_FISH_ATLAS = {
    "mackerel", "mahi_mahi", "albacore", "wahoo", "barracuda", "tuna",
    "sailfish", "bigeye_tuna", "cobia", "amberjack", "swordfish",
    "bluefin_tuna", "ocean_sunfish", "reef_shark", "mako_shark",
    "tiger_shark", "hammerhead_shark", "great_white_shark", "ghost_marlin",
}

WOOD_BEGINNER_ATLAS = {
    "fallen_branch", "birch_log", "alder_log", "pine_log", "poplar_log",
    "willow_log", "linden_log", "oak_log", "beech_log", "maple_log",
}
WOOD_FOREST_ATLAS = {
    "linden_log", "oak_log", "beech_log", "maple_log", "ash_log",
    "chestnut_log", "walnut_log", "cedar_log", "yew_log",
    "mahogany_log", "teak_log", "redwood_log", "ironwood_log",
}
WOOD_DEEP_ATLAS = {
    "ash_log", "chestnut_log", "walnut_log", "cedar_log", "yew_log",
    "mahogany_log", "teak_log", "redwood_log", "ironwood_log",
    "ebony_log", "silverwood_log", "spiritwood_log",
    "ancient_heartwood", "worldtree_wood",
}

ORE_ATLAS_LEVELS = {
    "stone_chunk": 1,
    "copper_ore": 1,
    "iron_ore": 1,
    "silver_ore": 10,
    "gold_ore": 25,
}

RACES = [
    ("Człowiek",
     "Wszechstronny. Wszystkie statystyki startują na równym poziomie. "
     "Pasyw rasowy: +10 procent do zdobywanego Postępu Rozwoju statystyk.",
     10, 10, 10, 10, 10),
    ("Ogr",
     "Bardzo silny i wytrzymały. Wysoka Siła i Kondycja wspierają walkę wręcz. "
     "Pasyw rasowy: +12 procent obrażeń fizycznych.",
     14, 8, 14, 6, 8),
    ("Elf",
     "Bardzo zręczny i inteligentny. Dobrze łączy szybkość z magią. "
     "Pasyw rasowy: +5 punktów procentowych do szansy uniku.",
     8, 14, 9, 13, 11),
    ("Krasnolud",
     "Silny i bardzo odporny. Wysoka Kondycja daje dużo HP, a Siła Woli dobrą obronę magiczną. "
     "Pasyw rasowy: 10 procent redukcji wszystkich otrzymywanych obrażeń.",
     12, 9, 14, 9, 12),
    ("Ork",
     "Urodzony wojownik. Wysoka Siła i Kondycja dają mocne ciosy i dużo HP. "
     "Pasyw rasowy: +10 procent maksymalnego HP.",
     13, 10, 13, 7, 9),
    ("Niziołek",
     "Zręczny i szczęśliwy poszukiwacz. "
     "Pasyw rasowy: +3 punkty procentowe do szansy na bonusowy połów, dodatkową rudę lub dodatkowe drewno.",
     7, 14, 10, 10, 11),
    ("Mroczny Elf",
     "Zręczny i bardzo inteligentny. Dobrze łączy szybkość z magią. "
     "Pasyw rasowy: +10 procent obrażeń magicznych.",
     9, 13, 9, 14, 10),
    ("Gnom",
     "Bardzo inteligentny i odporny magicznie. "
     "Pasyw rasowy: +15 procent maksymalnej Many dla klas magicznych.",
     7, 12, 9, 14, 13),
    ("Smoczy",
     "Silny, wytrzymały i wszechstronny w walce. "
     "Pasyw rasowy: +8 procent wszystkich zadawanych obrażeń, fizycznych i magicznych.",
     13, 9, 13, 10, 10),
    ("Troll",
     "Największa surowa Siła i Kondycja. Jest wolny, ale bardzo trudny do powalenia. "
     "Pasyw rasowy: 12 procent redukcji otrzymywanych obrażeń fizycznych.",
     15, 7, 15, 5, 8),
    ("Diablę",
     "Dobre predyspozycje magiczne i silna więź z energią dusz. "
     "Pasyw rasowy: +10 procent zdobywanego Soul XP Broni Duszy.",
     9, 11, 9, 13, 13),
    ("Aasimar",
     "Bardzo silna Siła Woli i dobra Inteligencja. "
     "Pasyw rasowy: +12 procent obrony magicznej.",
     10, 10, 11, 12, 14),
    ("Driada",
     "Rasa natury nastawiona na życie i odnowę. "
     "Pasyw rasowy: +15 procent mocy wszystkich klasowych umiejętności leczących. "
     "Szczególnie dobrze pasuje do Kapłana i Druida.",
     7, 10, 11, 15, 15),
]

CLASSES = [
    ("Wojownik", "physical", "Miecz Przysięgi", 7),
    ("Berserker", "physical", "Topór Krwi", 9),
    ("Łotrzyk", "physical", "Sztylety Cienia", 6),
    ("Łowca", "physical", "Łuk Echa", 7),
    ("Mnich", "physical", "Rękawice Ducha", 6),
    ("Strażnik", "physical", "Młot Bastionu", 7),
    ("Mag", "magic", "Kostur Arkanów", 7),
    ("Nekromanta", "magic", "Kosa Dusz", 8),
    ("Kapłan", "magic", "Młot Światła", 6),
    ("Czarownik", "magic", "Ostrze Otchłani", 8),
    ("Druid", "magic", "Kostur Korzeni", 6),
    ("Psionik", "magic", "Kryształ Umysłu", 7),
]


CLASS_DESCRIPTIONS = {
    "Wojownik": (
        "Klasa fizyczna. Stabilny wojownik do walki wręcz. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobra dla graczy chcących mocnych ciosów, szybkości i dużej ilości HP."
        "Pasyw klasowy: +10 procent obrażeń fizycznych."
    ),
    "Berserker": (
        "Klasa fizyczna nastawiona na bardzo wysokie obrażenia. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Broń Duszy ma wysoki bazowy potencjał ofensywny."
        "Pasyw klasowy: +12 procent obrażeń fizycznych."
    ),
    "Łotrzyk": (
        "Klasa fizyczna nastawiona na szybkość i zwinność. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobrze korzysta z wysokiej Zręczności i uników."
        "Pasyw klasowy: +5 punktów procentowych do szansy uniku."
    ),
    "Łowca": (
        "Klasa fizyczna walcząca z dystansu. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Najlepiej współpracuje z rasami o wysokiej Zręczności."
        "Pasyw klasowy: +8 procent obrażeń fizycznych."
    ),
    "Mnich": (
        "Klasa fizyczna oparta na szybkości i kontroli ciała. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobrze skaluje się ze Zręcznością oraz Kondycją."
        "Pasyw klasowy: +8 procent mocy klasowych umiejętności leczących."
    ),
    "Strażnik": (
        "Klasa fizyczna nastawiona na przetrwanie. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobrze wykorzystuje wysoką Kondycję i cięższy pancerz."
        "Pasyw klasowy: 10 procent redukcji wszystkich otrzymywanych obrażeń."
    ),
    "Mag": (
        "Klasa magiczna. Inteligencja zwiększa Manę i moc czarów, "
        "a Siła Woli obronę magiczną. Automatycznie rozwija wszystkie pięć statystyk."
        "Pasyw klasowy: +10 procent obrażeń magicznych."
    ),
    "Nekromanta": (
        "Klasa magiczna oparta na mrocznej energii i silnych czarach. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobrze korzysta z wysokiej Inteligencji."
        "Pasyw klasowy: +15 procent leczenia z umiejętności wysysających życie."
    ),
    "Kapłan": (
        "Klasa magiczna o defensywnym charakterze. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Wysoka Siła Woli wzmacnia obronę magiczną."
        "Pasyw klasowy: +10 procent mocy klasowych umiejętności leczących."
    ),
    "Czarownik": (
        "Ofensywna klasa magiczna z mocną Bronią Duszy. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobrze skaluje się z Inteligencją i dużą pulą Many."
        "Pasyw klasowy: +12 procent obrażeń magicznych."
    ),
    "Druid": (
        "Wszechstronna klasa magiczna związana z naturą. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Łączy dobrą moc czarów z obroną magiczną."
        "Pasyw klasowy: +10 procent mocy klasowych umiejętności leczących."
    ),
    "Psionik": (
        "Klasa magiczna oparta na mocy umysłu. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Najlepiej wykorzystuje wysoką Inteligencję i Siłę Woli."
        "Pasyw klasowy: +10 procent obrony magicznej."
    ),
}


CLASS_SKILLS = {'Wojownik': [{'id': 'warrior_power_slash',
               'name': 'Potężne Cięcie',
               'aliases': ['potezne ciecie', 'potężne cięcie', 'power slash'],
               'unlock': 1,
               'kind': 'damage',
               'cooldown': 4,
               'mana': 0,
               'desc': 'Mocny fizyczny cios skalowany Siłą.',
               'scale': 'strength',
               'mult': 1.35},
              {'id': 'warrior_war_cry',
               'name': 'Okrzyk Wojenny',
               'aliases': ['okrzyk wojenny', 'war cry'],
               'unlock': 25,
               'kind': 'boost',
               'cooldown': 12,
               'mana': 0,
               'desc': 'Wzmacnia następną ofensywną umiejętność o 35 procent.',
               'boost': 1.35},
              {'id': 'warrior_unbreakable',
               'name': 'Niezłomność',
               'aliases': ['niezlomnosc', 'niezłomność', 'unbreakable'],
               'unlock': 60,
               'kind': 'guard',
               'cooldown': 15,
               'mana': 0,
               'desc': 'Zmniejsza obrażenia następnego trafienia o dodatkowe 18.',
               'guard': 18}],
 'Berserker': [{'id': 'berserker_blood_swing',
                'name': 'Krwawy Zamach',
                'aliases': ['krwawy zamach', 'blood swing'],
                'unlock': 1,
                'kind': 'damage',
                'cooldown': 5,
                'mana': 0,
                'desc': 'Bardzo mocny cios Siłą, ale kosztuje 4 HP.',
                'scale': 'strength',
                'mult': 1.5,
                'self_damage': 4},
               {'id': 'berserker_blood_fury',
                'name': 'Szał Krwi',
                'aliases': ['szal krwi', 'szał krwi', 'blood fury'],
                'unlock': 25,
                'kind': 'boost',
                'cooldown': 13,
                'mana': 0,
                'desc': 'Wzmacnia następną ofensywną umiejętność o 55 procent.',
                'boost': 1.55},
               {'id': 'berserker_execution',
                'name': 'Egzekucja',
                'aliases': ['egzekucja', 'execution'],
                'unlock': 60,
                'kind': 'execute',
                'cooldown': 10,
                'mana': 0,
                'desc': 'Silny cios, wyjątkowo mocny poniżej 35 procent HP celu.',
                'scale': 'strength',
                'mult': 1.45,
                'execute_mult': 1.9}],
 'Łotrzyk': [{'id': 'rogue_shadow_strike',
              'name': 'Cios z Cienia',
              'aliases': ['cios z cienia', 'shadow strike'],
              'unlock': 1,
              'kind': 'damage',
              'cooldown': 4,
              'mana': 0,
              'desc': 'Szybki atak skalowany Zręcznością.',
              'scale': 'dexterity',
              'mult': 1.38},
             {'id': 'rogue_double_blade',
              'name': 'Podwójne Ostrze',
              'aliases': ['podwojne ostrze', 'podwójne ostrze', 'double blade'],
              'unlock': 25,
              'kind': 'damage',
              'cooldown': 8,
              'mana': 0,
              'desc': 'Seria dwóch cięć jako jeden silny atak.',
              'scale': 'dexterity',
              'mult': 1.68},
             {'id': 'rogue_vanish',
              'name': 'Zniknięcie',
              'aliases': ['znikniecie', 'zniknięcie', 'vanish'],
              'unlock': 60,
              'kind': 'evade',
              'cooldown': 12,
              'mana': 0,
              'desc': 'Gwarantuje unik następnego kontrataku.'}],
 'Łowca': [{'id': 'hunter_precise_shot',
            'name': 'Celny Strzał',
            'aliases': ['celny strzal', 'celny strzał', 'precise shot'],
            'unlock': 1,
            'kind': 'damage',
            'cooldown': 4,
            'mana': 0,
            'desc': 'Precyzyjny atak dystansowy skalowany Zręcznością.',
            'scale': 'dexterity',
            'mult': 1.42},
           {'id': 'hunter_echo_volley',
            'name': 'Salwa Echa',
            'aliases': ['salwa echa', 'echo volley'],
            'unlock': 25,
            'kind': 'damage',
            'cooldown': 8,
            'mana': 0,
            'desc': 'Potężna salwa z Łuku Echa.',
            'scale': 'dexterity',
            'mult': 1.72},
           {'id': 'hunter_instinct',
            'name': 'Instynkt Łowcy',
            'aliases': ['instynkt lowcy', 'instynkt łowcy', 'hunter instinct'],
            'unlock': 60,
            'kind': 'evade',
            'cooldown': 10,
            'mana': 0,
            'desc': 'Gwarantuje unik następnego kontrataku.'}],
 'Mnich': [{'id': 'monk_spirit_punch',
            'name': 'Uderzenie Ducha',
            'aliases': ['uderzenie ducha', 'spirit punch'],
            'unlock': 1,
            'kind': 'damage',
            'cooldown': 3,
            'mana': 0,
            'desc': 'Szybkie uderzenie skalowane Zręcznością.',
            'scale': 'dexterity',
            'mult': 1.32},
           {'id': 'monk_combo',
            'name': 'Seria Ciosów',
            'aliases': ['seria ciosow', 'seria ciosów', 'combo'],
            'unlock': 25,
            'kind': 'damage',
            'cooldown': 7,
            'mana': 0,
            'desc': 'Szybka kombinacja kilku uderzeń.',
            'scale': 'dexterity',
            'mult': 1.65},
           {'id': 'monk_meditation',
            'name': 'Medytacja',
            'aliases': ['medytacja', 'meditation'],
            'unlock': 60,
            'kind': 'heal',
            'cooldown': 16,
            'mana': 0,
            'desc': 'Przywraca 28 procent maksymalnego HP.',
            'heal_pct': 0.28}],
 'Strażnik': [{'id': 'guardian_crushing_blow',
               'name': 'Miażdżący Cios',
               'aliases': ['miazdzacy cios', 'miażdżący cios', 'crushing blow'],
               'unlock': 1,
               'kind': 'damage',
               'cooldown': 4,
               'mana': 0,
               'desc': 'Ciężki fizyczny cios Młotem Bastionu.',
               'scale': 'strength',
               'mult': 1.28},
              {'id': 'guardian_bastion',
               'name': 'Bastion',
               'aliases': ['bastion'],
               'unlock': 25,
               'kind': 'guard',
               'cooldown': 11,
               'mana': 0,
               'desc': 'Zmniejsza obrażenia następnego trafienia o dodatkowe 22.',
               'guard': 22},
              {'id': 'guardian_soul_wall',
               'name': 'Mur Duszy',
               'aliases': ['mur duszy', 'soul wall'],
               'unlock': 60,
               'kind': 'guard',
               'cooldown': 18,
               'mana': 0,
               'desc': 'Potężna osłona redukująca następne trafienie o 35.',
               'guard': 35}],
 'Mag': [{'id': 'mage_arcane_bolt',
          'name': 'Pocisk Arkanów',
          'aliases': ['pocisk arkanow', 'pocisk arkanów', 'arcane bolt'],
          'unlock': 1,
          'kind': 'damage',
          'cooldown': 3,
          'mana': 6,
          'desc': 'Podstawowy czar ofensywny skalowany Inteligencją.',
          'scale': 'intelligence',
          'mult': 1.42},
         {'id': 'mage_chain_energy',
          'name': 'Łańcuch Energii',
          'aliases': ['lancuch energii', 'łańcuch energii', 'chain energy'],
          'unlock': 25,
          'kind': 'damage',
          'cooldown': 7,
          'mana': 12,
          'desc': 'Silny impuls energii magicznej.',
          'scale': 'intelligence',
          'mult': 1.78},
         {'id': 'mage_arcane_barrier',
          'name': 'Bariera Arkanów',
          'aliases': ['bariera arkanow', 'bariera arkanów', 'arcane barrier'],
          'unlock': 60,
          'kind': 'guard',
          'cooldown': 13,
          'mana': 10,
          'desc': 'Magiczna bariera redukująca następne trafienie o 24.',
          'guard': 24}],
 'Nekromanta': [{'id': 'necro_death_touch',
                 'name': 'Dotyk Śmierci',
                 'aliases': ['dotyk smierci', 'dotyk śmierci', 'death touch'],
                 'unlock': 1,
                 'kind': 'damage',
                 'cooldown': 4,
                 'mana': 6,
                 'desc': 'Mroczny atak magiczny skalowany Inteligencją.',
                 'scale': 'intelligence',
                 'mult': 1.38},
                {'id': 'necro_soul_drain',
                 'name': 'Wysysanie Duszy',
                 'aliases': ['wysysanie duszy', 'soul drain'],
                 'unlock': 25,
                 'kind': 'drain',
                 'cooldown': 8,
                 'mana': 10,
                 'desc': 'Zadaje obrażenia i leczy za 45 procent zadanych obrażeń.',
                 'scale': 'intelligence',
                 'mult': 1.45,
                 'drain_pct': 0.45},
                {'id': 'necro_soul_reaping',
                 'name': 'Żniwo Dusz',
                 'aliases': ['zniwo dusz', 'żniwo dusz', 'soul reaping'],
                 'unlock': 60,
                 'kind': 'execute',
                 'cooldown': 11,
                 'mana': 16,
                 'desc': 'Potężny czar silniejszy poniżej 35 procent HP celu.',
                 'scale': 'intelligence',
                 'mult': 1.65,
                 'execute_mult': 1.75}],
 'Kapłan': [{'id': 'priest_small_heal',
             'name': 'Małe Leczenie',
             'aliases': ['male leczenie', 'małe leczenie', 'small heal'],
             'unlock': 1,
             'kind': 'heal',
             'cooldown': 6,
             'mana': 3,
             'desc': 'Podstawowe leczenie dla początkujących Kapłanów. Przywraca 12 procent maksymalnego HP i rośnie wraz ze Skill Level.',
             'heal_pct': 0.12},
            {'id': 'priest_holy_hammer',
             'name': 'Święty Młot',
             'aliases': ['swiety mlot', 'święty młot', 'holy hammer'],
             'unlock': 1,
             'kind': 'damage',
             'cooldown': 4,
             'mana': 5,
             'desc': 'Święty atak magiczny skalowany Inteligencją.',
             'scale': 'intelligence',
             'mult': 1.28},
            {'id': 'priest_great_heal',
             'name': 'Wielkie Leczenie',
             'aliases': ['wielkie leczenie', 'great heal'],
             'unlock': 25,
             'kind': 'heal',
             'cooldown': 14,
             'mana': 10,
             'desc': 'Przywraca 38 procent maksymalnego HP.',
             'heal_pct': 0.38},
            {'id': 'priest_divine_shield',
             'name': 'Boska Tarcza',
             'aliases': ['boska tarcza', 'divine shield'],
             'unlock': 60,
             'kind': 'guard',
             'cooldown': 17,
             'mana': 12,
             'desc': 'Silna tarcza redukująca następne trafienie o 32.',
             'guard': 32}],
 'Czarownik': [{'id': 'warlock_void_blade',
                'name': 'Ostrze Otchłani',
                'aliases': ['ostrze otchlani', 'ostrze otchłani', 'void blade'],
                'unlock': 1,
                'kind': 'damage',
                'cooldown': 4,
                'mana': 7,
                'desc': 'Ofensywny czar Ostrza Otchłani.',
                'scale': 'intelligence',
                'mult': 1.48},
               {'id': 'warlock_void_flame',
                'name': 'Płomień Otchłani',
                'aliases': ['plomien otchlani', 'płomień otchłani', 'void flame'],
                'unlock': 25,
                'kind': 'damage',
                'cooldown': 8,
                'mana': 13,
                'desc': 'Bardzo mocny magiczny atak.',
                'scale': 'intelligence',
                'mult': 1.85},
               {'id': 'warlock_blood_pact',
                'name': 'Pakt Krwi',
                'aliases': ['pakt krwi', 'blood pact'],
                'unlock': 60,
                'kind': 'damage',
                'cooldown': 12,
                'mana': 8,
                'desc': 'Ekstremalnie silny czar kosztujący dodatkowo 10 procent maksymalnego HP.',
                'scale': 'intelligence',
                'mult': 2.15,
                'self_damage_pct': 0.1}],
 'Druid': [{'id': 'druid_thorns',
            'name': 'Ciernie',
            'aliases': ['ciernie', 'thorns'],
            'unlock': 1,
            'kind': 'damage',
            'cooldown': 4,
            'mana': 5,
            'desc': 'Magiczny atak natury skalowany Inteligencją.',
            'scale': 'intelligence',
            'mult': 1.32},
           {'id': 'druid_nature_heal',
            'name': 'Uzdrowienie Natury',
            'aliases': ['uzdrowienie natury', 'nature heal'],
            'unlock': 25,
            'kind': 'heal',
            'cooldown': 13,
            'mana': 9,
            'desc': 'Przywraca 32 procent maksymalnego HP.',
            'heal_pct': 0.32},
           {'id': 'druid_storm_wrath',
            'name': 'Gniew Burzy',
            'aliases': ['gniew burzy', 'storm wrath'],
            'unlock': 60,
            'kind': 'damage',
            'cooldown': 10,
            'mana': 15,
            'desc': 'Potężny czar burzy.',
            'scale': 'intelligence',
            'mult': 1.92}],
 'Psionik': [{'id': 'psion_mind_pulse',
              'name': 'Impuls Umysłu',
              'aliases': ['impuls umyslu', 'impuls umysłu', 'mind pulse'],
              'unlock': 1,
              'kind': 'damage',
              'cooldown': 3,
              'mana': 5,
              'desc': 'Szybki psioniczny atak skalowany Inteligencją.',
              'scale': 'intelligence',
              'mult': 1.38},
             {'id': 'psion_psionic_wave',
              'name': 'Fala Psioniczna',
              'aliases': ['fala psioniczna', 'psionic wave'],
              'unlock': 25,
              'kind': 'damage',
              'cooldown': 7,
              'mana': 11,
              'desc': 'Silna fala energii umysłu.',
              'scale': 'intelligence',
              'mult': 1.75},
             {'id': 'psion_mind_barrier',
              'name': 'Bariera Umysłu',
              'aliases': ['bariera umyslu', 'bariera umysłu', 'mind barrier'],
              'unlock': 60,
              'kind': 'guard',
              'cooldown': 14,
              'mana': 10,
              'desc': 'Psioniczna bariera redukująca następne obrażenia o 28.',
              'guard': 28}]}


# 28 trwałych lokacji. Opisy są krótkie i przyjazne czytnikom ekranu.
ROOMS = {
    "square": {
        "zone": "Miasto Dusz", "name": "Plac Dusz",
        "desc": "Centralny plac osady. Nad kamienną fontanną płonie błękitny ogień.",
        "exits": {"north": "north_street", "south": "south_street", "east": "market", "west": "temple"},
    },
    "temple": {
        "zone": "Miasto Dusz", "name": "Świątynia Odrodzenia",
        "desc": "Spokojna świątynia. Polegli bohaterowie odzyskują tutaj świadomość.",
        "exits": {"east": "square", "north": "library", "down": "temple_basement"},
    },
    "temple_basement": {
        "zone": "Podziemia", "name": "Piwnica Świątyni",
        "desc": "Wilgotna piwnica pod Świątynią Odrodzenia. Między skrzyniami słychać piski szczurów.",
        "exits": {"up": "temple"},
    },
    "library": {
        "zone": "Miasto Dusz", "name": "Biblioteka Kronik",
        "desc": "Kamienne regały przechowują kroniki o duszach, rasach i dawnych wojnach.",
        "exits": {"south": "temple", "east": "guild_hall"},
    },
    "guild_hall": {
        "zone": "Gildia Dusz", "name": "Sala Główna Gildii",
        "desc": "Centralny hol Gildii Dusz. Korytarze prowadzą do wyspecjalizowanych sal nauczycieli.",
        "exits": {
            "west": "library",
            "south": "north_street",
            "north": "guild_martial_hall",
            "east": "guild_arcane_chamber",
            "up": "guild_shadow_gallery",
            "down": "guild_sanctuary",
        },
    },
    "guild_martial_hall": {
        "zone": "Gildia Dusz", "name": "Sala Oręża Gildii",
        "desc": "Ciężkie manekiny i stojaki treningowe służą Wojownikom i Berserkerom.",
        "exits": {"south": "guild_hall", "east": "guild_body_hall"},
    },
    "guild_body_hall": {
        "zone": "Gildia Dusz", "name": "Sala Dyscypliny Gildii",
        "desc": "Spokojna sala ćwiczeń ciała i obrony przeznaczona dla Mnichów i Strażników.",
        "exits": {"west": "guild_martial_hall"},
    },
    "guild_arcane_chamber": {
        "zone": "Gildia Dusz", "name": "Komnata Arkanów Gildii",
        "desc": "Runy świecą na ścianach. Tutaj Magowie i Psionicy ćwiczą kontrolę energii.",
        "exits": {"west": "guild_hall", "east": "guild_dark_chamber"},
    },
    "guild_dark_chamber": {
        "zone": "Gildia Dusz", "name": "Komnata Mrocznych Sztuk",
        "desc": "Zabezpieczona sala do nauki Nekromantów i Czarowników.",
        "exits": {"west": "guild_arcane_chamber"},
    },
    "guild_shadow_gallery": {
        "zone": "Gildia Dusz", "name": "Galeria Cieni Gildii",
        "desc": "Wąskie przejścia i cele treningowe służą Łotrzykom i Łowcom.",
        "exits": {"down": "guild_hall"},
    },
    "guild_sanctuary": {
        "zone": "Gildia Dusz", "name": "Sanktuarium Gildii",
        "desc": "Cicha sala natury i światła, w której szkolą się Kapłani i Druidzi.",
        "exits": {"up": "guild_hall"},
    },
    "north_street": {
        "zone": "Miasto Dusz", "name": "Ulica Północna",
        "desc": "Szeroka ulica prowadząca ku dziedzińcowi i północnej bramie.",
        "exits": {"south": "square", "north": "training", "east": "guard_hall", "west": "guild_hall"},
    },
    "guard_hall": {
        "zone": "Miasto Dusz", "name": "Strażnica",
        "desc": "Siedziba miejskiej straży. Na ścianach wiszą mapy okolicznych szlaków.",
        "exits": {"west": "north_street"},
    },
    "training": {
        "zone": "Miasto Dusz", "name": "Dziedziniec Treningowy",
        "desc": "Plac do ćwiczeń. Drewniane manekiny stoją obok północnej bramy.",
        "exits": {"south": "north_street", "north": "north_gate"},
    },
    "north_gate": {
        "zone": "Miasto Dusz", "name": "Północna Brama",
        "desc": "Za ciężką bramą zaczyna się Stary Trakt.",
        "exits": {"south": "training", "north": "old_road"},
    },
    "market": {
        "zone": "Miasto Dusz", "name": "Rynek",
        "desc": "Kupcy sprzedają prowiant, mikstury i podstawowe wyposażenie.",
        "exits": {"west": "square", "east": "forge", "south": "inn", "north": "fish_market"},
    },
    "fish_market": {
        "zone": "Miasto Dusz", "name": "Targ Rybny",
        "desc": "Stragany pachną świeżą rybą i mokrymi sieciami. Tutaj sprzedaje się sprzęt wędkarski.",
        "exits": {"south": "market", "east": "harbor"},
    },
    "harbor": {
        "zone": "Miasto Dusz", "name": "Port Dusz",
        "desc": "Drewniane pomosty, kutry i skrzynie rybackie wypełniają miejski port.",
        "exits": {"west": "fish_market", "east": "sea_pier"},
    },
    "sea_pier": {
        "zone": "Wybrzeże", "name": "Morskie Molo",
        "desc": "Długie molo wychodzi nad morze. To łowisko typowych ryb morskich.",
        "exits": {"west": "harbor", "east": "ocean_platform"},
    },
    "ocean_platform": {
        "zone": "Wybrzeże", "name": "Oceaniczna Platforma",
        "desc": "Daleka platforma nad otwartym oceanem. Trafiają się tu wielkie ryby oceaniczne i rekiny.",
        "exits": {"west": "sea_pier"},
    },
    "forge": {
        "zone": "Miasto Dusz", "name": "Kuźnia Dusz",
        "desc": "Młoty uderzają o metal, a Broń Duszy odpowiada cichym rezonansem.",
        "exits": {"west": "market"},
    },
    "inn": {
        "zone": "Miasto Dusz", "name": "Karczma Pod Błękitnym Płomieniem",
        "desc": "Ciepła karczma pełna rozmów podróżników.",
        "exits": {"north": "market", "west": "south_street"},
    },
    "south_street": {
        "zone": "Miasto Dusz", "name": "Ulica Południowa",
        "desc": "Cichsza część miasta prowadząca do południowej bramy.",
        "exits": {"north": "square", "east": "inn", "south": "south_gate"},
    },
    "south_gate": {
        "zone": "Miasto Dusz", "name": "Południowa Brama",
        "desc": "Brama otwiera się na łąki i Gaj Szeptów.",
        "exits": {"north": "south_street", "south": "meadow"},
    },
    "meadow": {
        "zone": "Dzicz", "name": "Srebrna Łąka",
        "desc": "Trawa porusza się falami. Na zachodzie widać ciemny gaj, a na południu ścieżkę do jeziora.",
        "exits": {"north": "south_gate", "west": "whisper_grove", "east": "riverbank", "south": "lake_shore"},
    },
    "lake_shore": {
        "zone": "Dzicz", "name": "Brzeg Srebrnego Jeziora",
        "desc": "Spokojne jezioro jest osobnym łowiskiem dla ryb jeziorowych.",
        "exits": {"north": "meadow"},
    },
    "whisper_grove": {
        "zone": "Dzicz", "name": "Gaj Szeptów",
        "desc": "Stare drzewa szepczą pod wpływem magicznego wiatru.",
        "exits": {"east": "meadow", "south": "deep_grove", "west": "lumberjack_camp", "north": "herbalist_hut"},
    },
    "herbalist_hut": {
        "zone": "Dzicz", "name": "Chata Zielarki",
        "desc": "Półki są pełne suszonych ziół, fiolek i alchemicznych naczyń.",
        "exits": {"south": "whisper_grove"},
    },
    "lumberjack_camp": {
        "zone": "Dzicz", "name": "Obóz Drwala",
        "desc": "Przy stosach drewna stoi warsztat Drwala Brana. Tutaj kupuje się Piłę.",
        "exits": {"east": "whisper_grove"},
    },
    "deep_grove": {
        "zone": "Dzicz", "name": "Głębia Gaju",
        "desc": "Światło prawie nie dociera między gęste konary.",
        "exits": {"north": "whisper_grove", "east": "hill"},
    },
    "hill": {
        "zone": "Dzicz", "name": "Wzgórze Kamiennych Znaków",
        "desc": "Na szczycie stoją stare kamienie pokryte nieczytelnymi runami.",
        "exits": {"west": "deep_grove", "north": "shrine"},
    },
    "shrine": {
        "zone": "Dzicz", "name": "Zapomniana Kapliczka",
        "desc": "Mała kapliczka poświęcona dawnym strażnikom dusz.",
        "exits": {"south": "hill"},
    },
    "riverbank": {
        "zone": "Dzicz", "name": "Brzeg Rzeki",
        "desc": "Szybka rzeka oddziela łąki od ruin starego pogranicza.",
        "exits": {"west": "meadow", "east": "stone_bridge"},
    },
    "stone_bridge": {
        "zone": "Dzicz", "name": "Kamienny Most",
        "desc": "Popękany most prowadzi na wschodni brzeg.",
        "exits": {"west": "riverbank", "east": "ruined_watchtower"},
    },
    "ruined_watchtower": {
        "zone": "Dzicz", "name": "Ruiny Strażnicy",
        "desc": "Zawalona wieża obserwacyjna została opanowana przez gobliny.",
        "exits": {"west": "stone_bridge", "south": "goblin_camp", "east": "graveyard"},
    },
    "goblin_camp": {
        "zone": "Dzicz", "name": "Obóz Goblinów",
        "desc": "Prymitywne namioty stoją wokół dymiącego ogniska.",
        "exits": {"north": "ruined_watchtower", "south": "cave_entrance"},
    },
    "cave_entrance": {
        "zone": "Podziemia", "name": "Wejście do Kryształowej Jaskini",
        "desc": "Z wnętrza jaskini dochodzi chłód i niebieska poświata.",
        "exits": {"north": "goblin_camp", "down": "cave_tunnel"},
    },
    "cave_tunnel": {
        "zone": "Podziemia", "name": "Kryształowy Tunel",
        "desc": "Ściany tunelu przecinają blade żyły kryształów.",
        "exits": {"up": "cave_entrance", "east": "crystal_chamber"},
    },
    "crystal_chamber": {
        "zone": "Podziemia", "name": "Kryształowa Komnata",
        "desc": "Wysokie kryształy pulsują energią przypominającą energię Broni Duszy.",
        "exits": {"west": "cave_tunnel"},
    },
    "graveyard": {
        "zone": "Dzicz", "name": "Stary Cmentarz",
        "desc": "Pęknięte nagrobki otaczają zejście do zapomnianej krypty.",
        "exits": {"west": "ruined_watchtower", "down": "crypt_entrance"},
    },
    "crypt_entrance": {
        "zone": "Podziemia", "name": "Przedsionek Krypty",
        "desc": "Kamienne schody prowadzą w ciemność.",
        "exits": {"up": "graveyard", "south": "crypt_hall"},
    },
    "crypt_hall": {
        "zone": "Podziemia", "name": "Sala Krypty",
        "desc": "W ścianach znajdują się stare nisze grobowe.",
        "exits": {"north": "crypt_entrance", "down": "crypt_depths"},
    },
    "crypt_depths": {
        "zone": "Podziemia", "name": "Głębia Krypty",
        "desc": "Najstarsza część podziemi. Powietrze drży od niespokojnej energii.",
        "exits": {"up": "crypt_hall"},
    },
    "old_road": {
        "zone": "Dzicz", "name": "Stary Trakt",
        "desc": "Kamienny trakt prowadzi między zarośniętymi słupami granicznymi. Na wschodzie widać wartownię straży.",
        "exits": {"south": "north_gate", "north": "crossroads", "east": "north_watchpost"},
    },
    "north_watchpost": {
        "zone": "Dzicz", "name": "Wartownia Północna",
        "desc": "Drewniana wartownia pilnuje północnego szlaku. Strażnicy obserwują ruch na Starym Trakcie.",
        "exits": {"west": "old_road", "east": "frontier_watchpost"},
    },
    "frontier_watchpost": {
        "zone": "Dzicz", "name": "Wartownia Pogranicza",
        "desc": "Kamienno-drewniany posterunek stoi na granicy bezpiecznych ziem. Dalej zaczyna się teren bandytów.",
        "exits": {"west": "north_watchpost", "east": "bandit_camp"},
    },
    "bandit_camp": {
        "zone": "Dzicz", "name": "Obozowisko Bandytów",
        "desc": "Brudne namioty, skrzynie z łupami i wygasające ogniska tworzą rozległy obóz bandytów.",
        "exits": {"west": "frontier_watchpost"},
    },
    "crossroads": {
        "zone": "Dzicz", "name": "Rozdroże",
        "desc": "Stary drogowskaz wskazuje zachód ku lasom i wschód ku ruinom.",
        "exits": {"south": "old_road", "west": "deep_grove", "east": "ruined_watchtower"},
    },
}

DIRECTION_ALIASES = {
    "n": "north", "north": "north", "północ": "north", "polnoc": "north",
    "s": "south", "south": "south", "południe": "south", "poludnie": "south",
    "e": "east", "east": "east", "wschód": "east", "wschod": "east",
    "w": "west", "west": "west", "zachód": "west", "zachod": "west",
    "u": "up", "up": "up", "góra": "up", "gora": "up",
    "d": "down", "down": "down", "dół": "down", "dol": "down",
}

COMMAND_ALIASES = {
    "pomoc": "help", "pomoce": "help",
    "opis": "describe", "opisz": "describe", "describe": "describe", "description": "describe",
    "changes": "changes", "zmiany": "changes", "changelog": "changes",
    "spójrz": "look", "spojrz": "look", "l": "look",
    "wyjścia": "exits", "wyjscia": "exits",
    "mapa": "map",
    "gdzie": "where",
    "kto": "who",
    "atlas": "atlas", "atlasy": "atlas",
    "charyzma": "charisma", "haryzma": "charisma", "charisma": "charisma",
    "drużyna": "party", "druzyna": "party", "party": "party",
    "pc": "partychat", "dczat": "partychat", "partychat": "partychat",
    "multiclass": "multiclass", "multiklasa": "multiclass",
    "multiklas": "multiclass", "klasy": "multiclass",
    "odpoczywaj": "rest", "odpocznij": "rest", "odpoczynek": "rest",
    "rest": "rest", "regen": "rest", "regeneruj": "rest",
    "staty": "stats", "status": "stats",
    "odmiana": "declension", "przypadki": "declension", "namecases": "declension", "declension": "declension",
    "skills": "skills", "umiejętności": "skills", "umiejetnosci": "skills", "zdolności": "skills", "zdolnosci": "skills",
    "skillnames": "skillnames", "nazwyskilli": "skillnames", "nazwyumiejetnosci": "skillnames", "nazwyumiejętności": "skillnames",
    "skill": "skill", "umiejętność": "skill", "umiejetnosc": "skill", "zdolność": "skill", "zdolnosc": "skill",
    "cast": "skill", "rzuc": "skill", "rzuć": "skill",
    "learn": "learn", "naucz": "learn", "ucz": "learn", "uczsię": "learn", "uczsie": "learn",
    "dusza": "soul",
    "ekwipunek": "inventory", "inv": "inventory", "i": "inventory",
    "załóż": "equip", "zaloz": "equip",
    "wyposażenie": "equipment", "wyposazenie": "equipment",
    "użyj": "use", "uzyj": "use", "use": "use",
    "sklep": "shop", "list": "shop", "lista": "shop",
    "kup": "buy",
    "mów": "say", "mow": "say", "powiedz": "say",
    "rozmawiaj": "talk",
    "teachers": "teachers", "nauczyciele": "teachers", "trenerzy": "teachers",
    "zadania": "quests", "questy": "quests",
    "atakuj": "attack", "walcz": "attack", "zabij": "attack", "kill": "attack",
    "ciało": "corpse", "cialo": "corpse", "zwłoki": "corpse", "zwloki": "corpse",
    "body": "corpse", "corpse": "corpse",
    "przeszukaj": "lootcorpse", "loot": "lootcorpse", "ograb": "lootcorpse",
    "krypta": "cryptinfo", "crypt": "cryptinfo",
    "portal": "portal", "portale": "portal",
    "portalkrypty": "portal", "portalekrypty": "portal",
    "cryptportal": "portal",
    "checkpoint": "portal", "check": "portal",
    "checkpointkrypty": "portal", "punktkrypty": "portal",
    "punktykrypty": "portal", "cryptcheckpoint": "portal",
    "uciekaj": "flee",
    "odblokuj": "unlock",
    "zapisz": "save",
    "włóż": "put", "wloz": "put", "put": "put",
    "wyjmij": "take", "wyciągnij": "take", "wyciagnij": "take", "take": "take",
    "siatka": "net", "net": "net",
    "sakwa": "bag", "worek": "bag", "bag": "bag",
    "wędkuj": "fish", "wedkuj": "fish", "łów": "fish", "low": "fish",
    "prowadź": "guide", "prowadz": "guide", "guide": "guide",
    "walkto": "guide",
    "lokalizacja": "location", "lokacja": "location", "location": "location",
    "kop": "mine", "wydobywaj": "mine",
    "tnij": "woodcut", "drwal": "woodcut", "woodcut": "woodcut", "saw": "woodcut",
    "drewno": "woodpile", "stos": "woodpile", "woodpile": "woodpile",
    "zbieraj": "herb", "zbierz": "herb", "zielarstwo": "herb", "herbalism": "herb",
    "zioła": "herbbag", "ziola": "herbbag", "herbs": "herbbag", "herbbag": "herbbag",
    "alchemia": "alchemy", "alchemy": "alchemy", "warz": "alchemy", "warzenie": "alchemy",
    "sprzedaj": "sell",
    "receptury": "recipes", "przepisy": "recipes", "recipes": "recipes",
    "rzemiosło": "recipes", "rzemioslo": "recipes",
    "stwórz": "craft", "stworz": "craft", "wytwórz": "craft", "wytworz": "craft", "craft": "craft",
    "gotuj": "cook", "ugotuj": "cook", "cook": "cook",
    "profesje": "professions",
    "rangi": "ranks", "ranks": "ranks", "rangiprofesji": "ranks", "professionranks": "ranks",
    "narzędzia": "tools", "narzedzia": "tools",
    "wędka": "toolinfo_fishing", "wedka": "toolinfo_fishing", "rod": "toolinfo_fishing",
    "kilof": "toolinfo_mining", "pickaxe": "toolinfo_mining",
    "piła": "toolinfo_woodcutting", "pila": "toolinfo_woodcutting",
    "młot": "toolinfo_crafting", "mlot": "toolinfo_crafting", "hammer": "toolinfo_crafting",
    "nóż": "toolinfo_cooking", "noz": "toolinfo_cooking", "knife": "toolinfo_cooking",
    "sierp": "toolinfo_herbalism", "sickle": "toolinfo_herbalism",
    "moździerz": "toolinfo_alchemy", "mozdzierz": "toolinfo_alchemy", "mortar": "toolinfo_alchemy",
    "tiers": "tiers", "tiery": "tiers", "tiernazwy": "tiers", "nazwytierow": "tiers", "nazwytierów": "tiers",
    "wyjście": "quit", "wyjscie": "quit",
}

ITEMS = {
    "healing_potion": {
        "name": "Mikstura leczenia", "type": "consumable", "price": 24, "currency": "silver",
        "desc": "Przywraca 35 punktów życia podczas walki.", "heal": 35,
    },
    "soul_elixir": {
        "name": "Eliksir Duszy", "type": "consumable", "price": None,
        "desc": "Daje 80 Soul XP.", "soul_xp": 80,
    },
    "leather_vest": {
        "name": "Skórzana kamizelka", "type": "armor", "slot": "body", "defense": 2,
        "price": 48, "currency": "silver", "desc": "Lekki pancerz. Obrona +2.",
    },
    "iron_helmet": {
        "name": "Żelazny hełm", "type": "armor", "slot": "head", "defense": 2,
        "price": 90, "currency": "silver",
        "desc": "Hełm kowalskiego zestawu. Slot głowa. Obrona fizyczna +2.",
    },
    "iron_guard": {
        "name": "Żelazny napierśnik", "type": "armor", "slot": "body", "defense": 4,
        "price": 180, "currency": "silver",
        "desc": "Główna część kowalskiego zestawu. Slot korpus. Obrona fizyczna +4.",
    },
    "iron_gauntlets": {
        "name": "Żelazne rękawice", "type": "armor", "slot": "hands", "defense": 1,
        "price": 70, "currency": "silver",
        "desc": "Rękawice kowalskiego zestawu. Slot dłonie. Obrona fizyczna +1.",
    },
    "iron_leggings": {
        "name": "Żelazne nogawice", "type": "armor", "slot": "legs", "defense": 3,
        "price": 130, "currency": "silver",
        "desc": "Osłona nóg kowalskiego zestawu. Slot nogi. Obrona fizyczna +3.",
    },
    "iron_boots": {
        "name": "Żelazne buty", "type": "armor", "slot": "feet", "defense": 1,
        "price": 70, "currency": "silver",
        "desc": "Buty kowalskiego zestawu. Slot stopy. Obrona fizyczna +1.",
    },
    "forge_charm": {
        "name": "Talizman Kowala", "type": "armor", "slot": "charm", "defense": 1,
        "price": 110, "currency": "silver",
        "desc": "Hartowany talizman ochronny. Slot talizman. Obrona fizyczna +1.",
    },
    "lucky_charm": {
        "name": "Talizman Wędrowca", "type": "armor", "slot": "charm", "defense": 1,
        "price": 72, "currency": "silver", "desc": "Drobny talizman. Obrona +1.",
    },
    "fishing_rod": {
        "name": "Wędka", "type": "tool", "tool_type": "fishing",
        "price": 10, "currency": "silver",
        "desc": "Podstawowe narzędzie do Wędkarstwa. Ma własny level 1-100.",
    },
    "pickaxe": {
        "name": "Kilof", "type": "tool", "tool_type": "mining",
        "price": 10, "currency": "silver",
        "desc": "Podstawowe narzędzie do Górnictwa. Ma własny level 1-100.",
    },
    "saw": {
        "name": "Piła", "type": "tool", "tool_type": "woodcutting",
        "price": 10, "currency": "silver",
        "desc": "Podstawowe narzędzie do Drwalstwa. Ma własny level 1-100 i 8 Tierów.",
    },
    "crafting_hammer": {
        "name": "Młot Rzemieślniczy", "type": "tool", "tool_type": "crafting",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie wymagane do Rzemiosła. Ma własny level 1-100, XP i 8 Tierów.",
    },
    "chef_knife": {
        "name": "Nóż Kucharski", "type": "tool", "tool_type": "cooking",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie wymagane do Gotowania. Ma własny level 1-100, XP i 8 Tierów.",
    },
    "herbalist_sickle": {
        "name": "Sierp Zielarski", "type": "tool", "tool_type": "herbalism",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie do Zielarstwa. Ma własny level 1-100, XP i 8 Tierów.",
    },
    "alchemy_mortar": {
        "name": "Moździerz Alchemiczny", "type": "tool", "tool_type": "alchemy",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie do Alchemii. Ma własny level 1-100, XP i 8 Tierów.",
    },
    "nettle": {"name": "Pokrzywa", "type": "resource", "price": None, "sell_silver": 5, "desc": "Pospolite zioło lecznicze."},
    "chamomile": {"name": "Rumianek", "type": "resource", "price": None, "sell_silver": 7, "desc": "Łagodne zioło lecznicze."},
    "mint": {"name": "Mięta", "type": "resource", "price": None, "sell_silver": 8, "desc": "Aromatyczne zioło."},
    "sage": {"name": "Szałwia", "type": "resource", "price": None, "sell_silver": 12, "desc": "Silne zioło alchemiczne."},
    "lavender": {"name": "Lawenda", "type": "resource", "price": None, "sell_silver": 14, "desc": "Pachnące zioło."},
    "yarrow": {"name": "Krwawnik", "type": "resource", "price": None, "sell_silver": 16, "desc": "Zioło lecznicze."},
    "lemon_balm": {"name": "Melisa", "type": "resource", "price": None, "sell_silver": 18, "desc": "Zioło przydatne w miksturach Many."},
    "valerian": {"name": "Kozłek", "type": "resource", "price": None, "sell_silver": 25, "desc": "Leśne zioło."},
    "ginseng": {"name": "Żeń-szeń", "type": "resource", "price": None, "sell_silver": 40, "desc": "Cenny korzeń alchemiczny."},
    "nightshade": {"name": "Wilcza jagoda", "type": "resource", "price": None, "sell_silver": 55, "desc": "Rzadkie zioło alchemiczne."},
    "mandrake": {"name": "Mandragora", "type": "resource", "price": None, "sell_gold": 1, "desc": "Rzadki magiczny korzeń."},
    "moonflower": {"name": "Kwiat księżycowy", "type": "resource", "price": None, "sell_gold": 2, "desc": "Magiczny kwiat."},
    "soulroot": {"name": "Korzeń duszy", "type": "resource", "price": None, "sell_gold": 3, "desc": "Korzeń nasycony energią dusz."},
    "phoenix_leaf": {"name": "Liść feniksa", "type": "resource", "price": None, "sell_gold": 5, "desc": "Bardzo rzadki liść."},
    "star_moss": {"name": "Gwiezdny mech", "type": "resource", "price": None, "sell_gold": 8, "desc": "Rzadki magiczny mech."},
    "astral_lotus": {"name": "Astralny lotos", "type": "resource", "price": None, "sell_gold": 15, "desc": "Mityczne zioło."},
    "mana_potion": {"name": "Mikstura Many", "type": "consumable", "price": None, "mana": 35, "desc": "Przywraca do 35 Many."},
    "greater_healing_potion": {"name": "Wielka Mikstura Leczenia", "type": "consumable", "price": None, "heal": 70, "desc": "Przywraca do 70 HP."},
    "greater_mana_potion": {"name": "Wielka Mikstura Many", "type": "consumable", "price": None, "mana": 70, "desc": "Przywraca do 70 Many."},
    "vitality_elixir": {"name": "Eliksir Witalności", "type": "consumable", "price": None, "heal": 55, "mana": 30, "desc": "Przywraca do 55 HP i 30 Many."},
    "fallen_branch": {"name": "Suche gałęzie", "type": "resource", "price": None, "sell_silver": 6, "desc": "Najprostszy materiał drwala."},
    "birch_log": {"name": "Pień brzozy", "type": "resource", "price": None, "sell_silver": 10, "desc": "Lekkie drewno brzozowe."},
    "pine_log": {"name": "Pień sosny", "type": "resource", "price": None, "sell_silver": 15, "desc": "Pospolite drewno sosnowe."},
    "willow_log": {"name": "Pień wierzby", "type": "resource", "price": None, "sell_silver": 22, "desc": "Miękkie drewno wierzby."},
    "oak_log": {"name": "Pień dębu", "type": "resource", "price": None, "sell_silver": 40, "desc": "Twarde drewno dębowe."},
    "beech_log": {"name": "Pień buku", "type": "resource", "price": None, "sell_silver": 55, "desc": "Mocne drewno bukowe."},
    "maple_log": {"name": "Pień klonu", "type": "resource", "price": None, "sell_silver": 70, "desc": "Cenne drewno klonowe."},
    "ash_log": {"name": "Pień jesionu", "type": "resource", "price": None, "sell_silver": 90, "desc": "Sprężyste drewno jesionowe."},
    "cedar_log": {"name": "Pień cedru", "type": "resource", "price": None, "sell_silver": 130, "desc": "Aromatyczne drewno cedrowe."},
    "yew_log": {"name": "Pień cisu", "type": "resource", "price": None, "sell_gold": 2, "desc": "Rzadkie drewno cisu."},
    "ironwood_log": {"name": "Pień żelaznego drzewa", "type": "resource", "price": None, "sell_gold": 5, "desc": "Niezwykle twarde drewno."},
    "ebony_log": {"name": "Pień hebanu", "type": "resource", "price": None, "sell_gold": 8, "desc": "Ciężkie i bardzo cenne drewno."},
    "silverwood_log": {"name": "Pień srebrnego drzewa", "type": "resource", "price": None, "sell_gold": 10, "desc": "Magiczne srebrzyste drewno."},
    "spiritwood_log": {"name": "Pień drzewa duchów", "type": "resource", "price": None, "sell_gold": 15, "desc": "Drewno nasycone energią dusz."},
    "ancient_heartwood": {"name": "Pradawna twardziel", "type": "resource", "price": None, "sell_gold": 30, "desc": "Rdzeń bardzo starego drzewa."},
    "worldtree_wood": {"name": "Drewno Drzewa Świata", "type": "resource", "price": None, "sell_gold": 75, "desc": "Mityczny materiał dla najlepszych drwali."},
    "iron_ingot": {
        "name": "Żelazna sztabka", "type": "craft_material", "price": None,
        "desc": "Przetopione żelazo używane w recepturach rzemieślniczych.",
    },
    "silver_ingot": {
        "name": "Srebrna sztabka", "type": "craft_material", "price": None,
        "desc": "Przetopione srebro używane w lepszych recepturach.",
    },
    "gold_ingot": {
        "name": "Złota sztabka", "type": "craft_material", "price": None,
        "desc": "Przetopione złoto używane w zaawansowanych recepturach.",
    },
    "oak_plank": {
        "name": "Deska dębowa", "type": "craft_material", "price": None,
        "desc": "Obrobiona deska z drewna dębowego.",
    },
    "ash_plank": {
        "name": "Deska jesionowa", "type": "craft_material", "price": None,
        "desc": "Sprężysta deska jesionowa.",
    },
    "yew_plank": {
        "name": "Deska cisowa", "type": "craft_material", "price": None,
        "desc": "Rzadka deska z drewna cisu.",
    },
    "ironwood_plank": {
        "name": "Deska żelaznego drzewa", "type": "craft_material", "price": None,
        "desc": "Bardzo twarda deska z żelaznego drzewa.",
    },
    "spiritwood_plank": {
        "name": "Deska drzewa duchów", "type": "craft_material", "price": None,
        "desc": "Magiczna deska nasycona energią dusz.",
    },
    "oak_iron_charm": {
        "name": "Talizman Dębu i Żelaza", "type": "armor", "slot": "charm",
        "defense": 2, "price": None,
        "desc": "Wytwarzany talizman. Slot talizman. Obrona fizyczna +2.",
    },
    "yew_silver_charm": {
        "name": "Talizman Cisu i Srebra", "type": "armor", "slot": "charm",
        "defense": 3, "price": None,
        "desc": "Rzadki wytwarzany talizman. Slot talizman. Obrona fizyczna +3.",
    },
    "spiritwood_gold_charm": {
        "name": "Talizman Drzewa Dusz", "type": "armor", "slot": "charm",
        "defense": 5, "price": None,
        "desc": "Zaawansowany talizman z magicznego drewna i złota. Obrona fizyczna +5.",
    },
    "grilled_river_fish": {
        "name": "Pieczona ryba rzeczna", "type": "consumable", "price": None,
        "heal": 30,
        "desc": "Prosta potrawa. Przywraca do 30 HP.",
    },
    "river_fish_stew": {
        "name": "Gulasz rzeczny", "type": "consumable", "price": None,
        "heal": 45,
        "desc": "Syta potrawa z ryb rzecznych. Przywraca do 45 HP.",
    },
    "lake_fish_stew": {
        "name": "Potrawka jeziorowa", "type": "consumable", "price": None,
        "heal": 50, "mana": 10,
        "desc": "Potrawa z ryb jeziorowych. Przywraca do 50 HP i 10 Many.",
    },
    "sea_chowder": {
        "name": "Zupa morska", "type": "consumable", "price": None,
        "heal": 60, "mana": 15,
        "desc": "Gęsta zupa morska. Przywraca do 60 HP i 15 Many.",
    },
    "ocean_steak": {
        "name": "Stek oceaniczny", "type": "consumable", "price": None,
        "heal": 75, "mana": 25,
        "desc": "Potężna potrawa z ryb oceanu. Przywraca do 75 HP i 25 Many.",
    },
    "master_fisher_feast": {
        "name": "Uczta Mistrza Rybaka", "type": "consumable", "price": None,
        "heal": 100, "mana": 40,
        "desc": "Wielka uczta z czterech środowisk. Przywraca do 100 HP i 40 Many.",
    },

    "small_fish": {
        "name": "Mała ryba", "type": "resource", "price": None,
        "desc": "Pospolity połów z płytkiej wody.", "sell_silver": 8,
    },
    "river_carp": {
        "name": "Karp rzeczny", "type": "resource", "price": None,
        "desc": "Solidna ryba rzeczna.", "sell_silver": 20,
    },
    "silver_trout": {
        "name": "Srebrny pstrąg", "type": "resource", "price": None,
        "desc": "Rzadsza ryba o srebrzystych łuskach.", "sell_silver": 55,
    },
    "golden_trout": {
        "name": "Złoty pstrąg", "type": "resource", "price": None,
        "desc": "Cenny połów dostępny przy lepszej wędce.", "sell_gold": 1,
    },
    "ancient_sturgeon": {
        "name": "Pradawny jesiotr", "type": "resource", "price": None,
        "desc": "Bardzo duża i cenna ryba.", "sell_gold": 3,
    },
    "moon_eel": {
        "name": "Księżycowy węgorz", "type": "resource", "price": None,
        "desc": "Niezwykle rzadki połów z wysokiego poziomu Wędkarstwa.", "sell_gold": 8,
    },
    "herring": {
        "name": "Śledź", "type": "resource", "price": None,
        "desc": "Morska ryba dostępna dopiero od levelu 30 Wędki.", "sell_gold": 1,
    },
    "mackerel": {
        "name": "Makrela", "type": "resource", "price": None,
        "desc": "Szybka ryba morska.", "sell_gold": 2,
    },
    "salmon": {
        "name": "Łosoś", "type": "resource", "price": None,
        "desc": "Cenny połów z rozwiniętego Wędkarstwa.", "sell_gold": 5,
    },
    "tuna": {
        "name": "Tuńczyk", "type": "resource", "price": None,
        "desc": "Duży i cenny połów dla wysokiego levelu Wędki.", "sell_gold": 15,
    },
    "swordfish": {
        "name": "Miecznik", "type": "resource", "price": None,
        "desc": "Rzadki i silny morski okaz.", "sell_gold": 30,
    },
    "bluefin_tuna": {
        "name": "Tuńczyk błękitnopłetwy", "type": "resource", "price": None,
        "desc": "Bardzo rzadki tuńczyk dostępny na wysokim levelu Wędki.", "sell_gold": 75,
    },
    "reef_shark": {
        "name": "Rekin rafowy", "type": "resource", "price": None,
        "desc": "Rzadki rekin możliwy do złowienia dopiero bardzo dobrą Wędką.", "sell_gold": 125,
    },
    "hammerhead_shark": {
        "name": "Rekin młot", "type": "resource", "price": None,
        "desc": "Bardzo rzadki rekin dla mistrzów Wędkarstwa.", "sell_gold": 250,
    },
    "great_white_shark": {
        "name": "Żarłacz biały", "type": "resource", "price": None,
        "desc": "Ekstremalnie rzadki okaz dla najwyższych leveli Wędki.", "sell_gold": 500,
    },
    "ghost_marlin": {
        "name": "Widmowy marlin", "type": "resource", "price": None,
        "desc": "Legendarny połów dostępny jedynie mistrzom Wędkarstwa.", "sell_mithril": 1,
    },
    "sardine": {
        "name": "Sardynka", "type": "resource", "price": None,
        "desc": "Niewielka morska ryba ławicowa.", "sell_silver": 35,
    },
    "anchovy": {
        "name": "Sardela", "type": "resource", "price": None,
        "desc": "Mała ryba morska spotykana w dużych ławicach.", "sell_silver": 45,
    },
    "cod": {
        "name": "Dorsz", "type": "resource", "price": None,
        "desc": "Cenna ryba morska o jasnym mięsie.", "sell_gold": 3,
    },
    "sea_bass": {
        "name": "Labraks", "type": "resource", "price": None,
        "desc": "Drapieżna ryba morska ceniona przez kupców.", "sell_gold": 4,
    },
    "haddock": {
        "name": "Plamiak", "type": "resource", "price": None,
        "desc": "Krewniak dorsza, trudniejszy do złowienia.", "sell_gold": 6,
    },
    "pollock": {
        "name": "Mintaj", "type": "resource", "price": None,
        "desc": "Silna ryba morska z chłodnych wód.", "sell_gold": 8,
    },
    "flounder": {
        "name": "Flądra", "type": "resource", "price": None,
        "desc": "Płaska ryba denna wymagająca lepszej Wędki.", "sell_gold": 10,
    },
    "halibut": {
        "name": "Halibut", "type": "resource", "price": None,
        "desc": "Duża i droga ryba denna.", "sell_gold": 20,
    },
    "river_perch": {"name": "Okoń rzeczny", "type": "resource", "price": None, "sell_silver": 14, "desc": "Pospolity drapieżnik rzeczny."},
    "barbel": {"name": "Brzana", "type": "resource", "price": None, "sell_silver": 25, "desc": "Silna ryba nurtu rzecznego."},
    "pike": {"name": "Szczupak", "type": "resource", "price": None, "sell_silver": 60, "desc": "Duży słodkowodny drapieżnik."},
    "zander": {"name": "Sandacz", "type": "resource", "price": None, "sell_silver": 85, "desc": "Cenny drapieżnik słodkowodny."},
    "river_catfish": {"name": "Sum rzeczny", "type": "resource", "price": None, "sell_gold": 3, "desc": "Wielki mieszkaniec głębokiej rzeki."},
    "lake_roach": {"name": "Płoć jeziorowa", "type": "resource", "price": None, "sell_silver": 10, "desc": "Pospolita ryba jeziorowa."},
    "bream": {"name": "Leszcz", "type": "resource", "price": None, "sell_silver": 20, "desc": "Popularna ryba jezior."},
    "tench": {"name": "Lin", "type": "resource", "price": None, "sell_silver": 35, "desc": "Ryba spokojnych, zarośniętych jezior."},
    "lake_perch": {"name": "Okoń jeziorowy", "type": "resource", "price": None, "sell_silver": 45, "desc": "Drapieżnik jeziorowy."},
    "lake_trout": {"name": "Troć jeziorowa", "type": "resource", "price": None, "sell_gold": 2, "desc": "Rzadka duża ryba chłodnych jezior."},
    "giant_pike": {"name": "Olbrzymi szczupak", "type": "resource", "price": None, "sell_gold": 6, "desc": "Bardzo stary szczupak."},
    "freshwater_eel": {"name": "Węgorz jeziorowy", "type": "resource", "price": None, "sell_gold": 8, "desc": "Rzadki węgorz z głębin jeziora."},
    "turbot": {"name": "Turbot", "type": "resource", "price": None, "sell_gold": 6, "desc": "Cenna ryba denna morza."},
    "mahi_mahi": {"name": "Mahi-mahi", "type": "resource", "price": None, "sell_gold": 10, "desc": "Szybka ryba oceaniczna."},
    "wahoo": {"name": "Wahoo", "type": "resource", "price": None, "sell_gold": 15, "desc": "Bardzo szybki drapieżnik oceanu."},
    "sailfish": {"name": "Żaglica", "type": "resource", "price": None, "sell_gold": 25, "desc": "Ekstremalnie szybka ryba oceaniczna."},
    "ocean_sunfish": {"name": "Samogłów oceaniczny", "type": "resource", "price": None, "sell_gold": 40, "desc": "Ogromna ryba otwartego oceanu."},
    # Dodatkowe ryby rzeczne
    "dace": {"name": "Jelec", "type": "resource", "price": None, "sell_silver": 12, "desc": "Mała szybka ryba rzeczna."},
    "chub": {"name": "Kleń", "type": "resource", "price": None, "sell_silver": 18, "desc": "Pospolita, silna ryba rzeczna."},
    "common_nase": {"name": "Świnka", "type": "resource", "price": None, "sell_silver": 22, "desc": "Ryba czystych, płynących wód."},
    "ide": {"name": "Jaź", "type": "resource", "price": None, "sell_silver": 32, "desc": "Cenna ryba większych rzek."},
    "asp": {"name": "Boleń", "type": "resource", "price": None, "sell_silver": 70, "desc": "Szybki drapieżnik rzeczny."},
    "grayling": {"name": "Lipień", "type": "resource", "price": None, "sell_silver": 90, "desc": "Cenna ryba chłodnych rzek."},
    "burbot": {"name": "Miętus", "type": "resource", "price": None, "sell_gold": 2, "desc": "Rzadki denny drapieżnik rzeczny."},

    # Dodatkowe ryby jeziorowe
    "rudd": {"name": "Wzdręga", "type": "resource", "price": None, "sell_silver": 14, "desc": "Kolorowa ryba spokojnych jezior."},
    "crucian_carp": {"name": "Karaś", "type": "resource", "price": None, "sell_silver": 18, "desc": "Wytrzymała ryba jeziorowa."},
    "vendace": {"name": "Sielawa", "type": "resource", "price": None, "sell_silver": 55, "desc": "Ryba chłodnych, czystych jezior."},
    "whitefish": {"name": "Sieja", "type": "resource", "price": None, "sell_gold": 1, "desc": "Cenna ryba głębokich jezior."},
    "lake_char": {"name": "Palia jeziorowa", "type": "resource", "price": None, "sell_gold": 3, "desc": "Rzadki drapieżnik zimnych jezior."},

    # Dodatkowe ryby morskie
    "sprat": {"name": "Szprot", "type": "resource", "price": None, "sell_silver": 8, "desc": "Mała ryba morska żyjąca w ławicach."},
    "whiting": {"name": "Witlinek", "type": "resource", "price": None, "sell_silver": 32, "desc": "Pospolita ryba morska."},
    "hake": {"name": "Morszczuk", "type": "resource", "price": None, "sell_silver": 85, "desc": "Drapieżna ryba morska."},
    "red_mullet": {"name": "Barwena", "type": "resource", "price": None, "sell_gold": 2, "desc": "Cenna morska ryba przydenna."},
    "sole": {"name": "Sola", "type": "resource", "price": None, "sell_gold": 4, "desc": "Cenna płaska ryba morska."},
    "monkfish": {"name": "Żabnica", "type": "resource", "price": None, "sell_gold": 9, "desc": "Duży morski drapieżnik głębinowy."},

    # Dodatkowe ryby oceaniczne
    "albacore": {"name": "Albakora", "type": "resource", "price": None, "sell_gold": 12, "desc": "Oceaniczny gatunek tuńczyka."},
    "bigeye_tuna": {"name": "Tuńczyk wielkooki", "type": "resource", "price": None, "sell_gold": 20, "desc": "Cenny tuńczyk głębokiego oceanu."},
    "barracuda": {"name": "Barakuda", "type": "resource", "price": None, "sell_gold": 18, "desc": "Szybki oceaniczny drapieżnik."},
    "cobia": {"name": "Kobia", "type": "resource", "price": None, "sell_gold": 22, "desc": "Duża ryba otwartego morza i oceanu."},
    "amberjack": {"name": "Seriola", "type": "resource", "price": None, "sell_gold": 28, "desc": "Silna oceaniczna ryba sportowa."},
    "mako_shark": {"name": "Rekin mako", "type": "resource", "price": None, "sell_gold": 180, "desc": "Bardzo szybki i rzadki rekin oceaniczny."},
    "tiger_shark": {"name": "Rekin tygrysi", "type": "resource", "price": None, "sell_gold": 300, "desc": "Wielki, bardzo rzadki drapieżnik oceaniczny."},

    # Dodatkowe gatunki drewna
    "alder_log": {"name": "Pień olchy", "type": "resource", "price": None, "sell_silver": 12, "desc": "Drewno lubiące wilgotne tereny."},
    "poplar_log": {"name": "Pień topoli", "type": "resource", "price": None, "sell_silver": 18, "desc": "Lekkie i łatwe w obróbce drewno."},
    "linden_log": {"name": "Pień lipy", "type": "resource", "price": None, "sell_silver": 28, "desc": "Miękkie drewno cenione przez rzemieślników."},
    "chestnut_log": {"name": "Pień kasztana", "type": "resource", "price": None, "sell_silver": 110, "desc": "Twarde, trwałe drewno."},
    "walnut_log": {"name": "Pień orzecha", "type": "resource", "price": None, "sell_gold": 2, "desc": "Cenne ciemne drewno orzechowe."},
    "mahogany_log": {"name": "Pień mahoniu", "type": "resource", "price": None, "sell_gold": 6, "desc": "Szlachetne, ciemnoczerwone drewno."},
    "teak_log": {"name": "Pień teku", "type": "resource", "price": None, "sell_gold": 9, "desc": "Bardzo trwałe i odporne drewno."},
    "redwood_log": {"name": "Pień sekwoi", "type": "resource", "price": None, "sell_gold": 18, "desc": "Ogromne i rzadkie drewno ze starych drzew."},

    "stone_chunk": {
        "name": "Odłamek skały", "type": "resource", "price": None,
        "desc": "Pospolity urobek.", "sell_silver": 3,
    },
    "copper_ore": {
        "name": "Ruda miedzi", "type": "resource", "price": None,
        "desc": "Podstawowa ruda górnicza.", "sell_silver": 12,
    },
    "iron_ore": {
        "name": "Ruda żelaza", "type": "resource", "price": None,
        "desc": "Użyteczna ruda metalu.", "sell_silver": 35,
    },
    "silver_ore": {
        "name": "Ruda srebra", "type": "resource", "price": None,
        "desc": "Cenniejsza ruda wydobywana lepszym kilofem.", "sell_gold": 1,
    },
    "gold_ore": {
        "name": "Ruda złota", "type": "resource", "price": None,
        "desc": "Rzadka i cenna ruda.", "sell_gold": 4,
    },
    "mithril_ore": {
        "name": "Ruda mithrilu (stary przedmiot)", "type": "resource", "price": None,
        "desc": "Przedmiot zgodności ze starszych wersji. Nie można go już wydobyć.",
        "sell_gold": 120,
    },
    "soul_shard": {
        "name": "Odłamek Duszy", "type": "quest", "price": None,
        "desc": "Niestabilny odłamek znaleziony przy istotach z krypty.",
    },
    "wolf_fang": {
        "name": "Kieł Wilka Cienia", "type": "loot", "price": None,
        "desc": "Ciemny kieł pulsujący słabą energią.",
    },
}

SHOPS = {
    "fish_market": ["fishing_rod"],
    "market": ["healing_potion", "leather_vest", "lucky_charm"],
    "inn": ["healing_potion", "chef_knife"],
    "forge": [
        "iron_helmet",
        "iron_guard",
        "iron_gauntlets",
        "iron_leggings",
        "iron_boots",
        "forge_charm",
        "pickaxe",
        "crafting_hammer",
    ],
    "lumberjack_camp": ["saw"],
    "herbalist_hut": ["herbalist_sickle", "alchemy_mortar"],
}

CRAFT_RECIPES = {
    "iron_ingot": {
        "name": "Żelazna sztabka", "stations": ("forge",),
        "ingredients": {"iron_ore": 2}, "output": "iron_ingot", "quantity": 1,
        "desc": "Przetop 2 Rudy żelaza w 1 Żelazną sztabkę.",
    },
    "silver_ingot": {
        "name": "Srebrna sztabka", "stations": ("forge",),
        "ingredients": {"silver_ore": 2}, "output": "silver_ingot", "quantity": 1,
        "desc": "Przetop 2 Rudy srebra w 1 Srebrną sztabkę.",
    },
    "gold_ingot": {
        "name": "Złota sztabka", "stations": ("forge",),
        "ingredients": {"gold_ore": 2}, "output": "gold_ingot", "quantity": 1,
        "desc": "Przetop 2 Rudy złota w 1 Złotą sztabkę.",
    },
    "oak_plank": {
        "name": "Deska dębowa", "stations": ("lumberjack_camp",),
        "ingredients": {"oak_log": 2}, "output": "oak_plank", "quantity": 1,
        "desc": "Obrób 2 Pnie dębu w 1 Deskę dębową.",
    },
    "ash_plank": {
        "name": "Deska jesionowa", "stations": ("lumberjack_camp",),
        "ingredients": {"ash_log": 2}, "output": "ash_plank", "quantity": 1,
        "desc": "Obrób 2 Pnie jesionu w 1 Deskę jesionową.",
    },
    "yew_plank": {
        "name": "Deska cisowa", "stations": ("lumberjack_camp",),
        "ingredients": {"yew_log": 2}, "output": "yew_plank", "quantity": 1,
        "desc": "Obrób 2 Pnie cisu w 1 Deskę cisową.",
    },
    "ironwood_plank": {
        "name": "Deska żelaznego drzewa", "stations": ("lumberjack_camp",),
        "ingredients": {"ironwood_log": 2}, "output": "ironwood_plank", "quantity": 1,
        "desc": "Obrób 2 Pnie żelaznego drzewa w 1 Deskę.",
    },
    "spiritwood_plank": {
        "name": "Deska drzewa duchów", "stations": ("lumberjack_camp",),
        "ingredients": {"spiritwood_log": 2}, "output": "spiritwood_plank", "quantity": 1,
        "desc": "Obrób 2 Pnie drzewa duchów w 1 magiczną Deskę.",
    },
    "oak_iron_charm": {
        "name": "Talizman Dębu i Żelaza", "stations": ("forge",),
        "ingredients": {"oak_plank": 2, "iron_ingot": 1},
        "output": "oak_iron_charm", "quantity": 1,
        "desc": "Talizman obronny +2 z drewna dębowego i żelaza.",
    },
    "yew_silver_charm": {
        "name": "Talizman Cisu i Srebra", "stations": ("forge",),
        "ingredients": {"yew_plank": 2, "silver_ingot": 1},
        "output": "yew_silver_charm", "quantity": 1,
        "desc": "Rzadki talizman obronny +3.",
    },
    "spiritwood_gold_charm": {
        "name": "Talizman Drzewa Dusz", "stations": ("forge",),
        "ingredients": {"spiritwood_plank": 2, "gold_ingot": 1},
        "output": "spiritwood_gold_charm", "quantity": 1,
        "desc": "Zaawansowany talizman obronny +5.",
    },
}

ALCHEMY_RECIPES = {
    "healing_potion": {
        "name": "Mikstura leczenia", "stations": ("herbalist_hut",),
        "ingredients": {"nettle": 1, "chamomile": 1},
        "output": "healing_potion", "quantity": 1,
        "desc": "Pokrzywa + Rumianek. Przywraca 35 HP.",
    },
    "mana_potion": {
        "name": "Mikstura Many", "stations": ("herbalist_hut",),
        "ingredients": {"mint": 1, "lemon_balm": 1},
        "output": "mana_potion", "quantity": 1,
        "desc": "Mięta + Melisa. Przywraca 35 Many.",
    },
    "greater_healing_potion": {
        "name": "Wielka Mikstura Leczenia", "stations": ("herbalist_hut",),
        "ingredients": {"yarrow": 1, "ginseng": 1, "mandrake": 1},
        "output": "greater_healing_potion", "quantity": 1,
        "desc": "Krwawnik + Żeń-szeń + Mandragora. Przywraca 70 HP.",
    },
    "greater_mana_potion": {
        "name": "Wielka Mikstura Many", "stations": ("herbalist_hut",),
        "ingredients": {"sage": 1, "moonflower": 1, "star_moss": 1},
        "output": "greater_mana_potion", "quantity": 1,
        "desc": "Szałwia + Kwiat księżycowy + Gwiezdny mech. Przywraca 70 Many.",
    },
    "vitality_elixir": {
        "name": "Eliksir Witalności", "stations": ("herbalist_hut",),
        "ingredients": {"ginseng": 1, "soulroot": 1, "phoenix_leaf": 1},
        "output": "vitality_elixir", "quantity": 1,
        "desc": "Przywraca 55 HP i 30 Many.",
    },
    "soul_elixir": {
        "name": "Eliksir Duszy", "stations": ("herbalist_hut",),
        "ingredients": {"soulroot": 2, "astral_lotus": 1},
        "output": "soul_elixir", "quantity": 1,
        "desc": "Daje 80 Soul XP.",
    },
}

COOK_RECIPES = {
    "grilled_river_fish": {
        "name": "Pieczona ryba rzeczna", "stations": ("inn", "fish_market"),
        "ingredients": {"small_fish": 2},
        "output": "grilled_river_fish", "quantity": 1,
        "desc": "2 Małe ryby. Przywraca do 30 HP.",
    },
    "river_fish_stew": {
        "name": "Gulasz rzeczny", "stations": ("inn", "fish_market"),
        "ingredients": {"river_carp": 1, "chub": 1},
        "output": "river_fish_stew", "quantity": 1,
        "desc": "Karp rzeczny + Kleń. Przywraca do 45 HP.",
    },
    "lake_fish_stew": {
        "name": "Potrawka jeziorowa", "stations": ("inn", "fish_market"),
        "ingredients": {"bream": 1, "tench": 1},
        "output": "lake_fish_stew", "quantity": 1,
        "desc": "Leszcz + Lin. Przywraca do 50 HP i 10 Many.",
    },
    "sea_chowder": {
        "name": "Zupa morska", "stations": ("inn", "fish_market"),
        "ingredients": {"cod": 1, "herring": 1},
        "output": "sea_chowder", "quantity": 1,
        "desc": "Dorsz + Śledź. Przywraca do 60 HP i 15 Many.",
    },
    "ocean_steak": {
        "name": "Stek oceaniczny", "stations": ("inn", "fish_market"),
        "ingredients": {"tuna": 1, "mahi_mahi": 1},
        "output": "ocean_steak", "quantity": 1,
        "desc": "Tuńczyk + Mahi-mahi. Przywraca do 75 HP i 25 Many.",
    },
    "master_fisher_feast": {
        "name": "Uczta Mistrza Rybaka", "stations": ("inn", "fish_market"),
        "ingredients": {"salmon": 1, "lake_trout": 1, "turbot": 1, "albacore": 1},
        "output": "master_fisher_feast", "quantity": 1,
        "desc": "Łosoś + Troć jeziorowa + Turbot + Albakora. Przywraca do 100 HP i 40 Many.",
    },
}

NPCS = {
    "fisher_tomas": {
        "name": "Rybak Tomas", "room": "fish_market",
        "dialogue": "Jeśli naprawdę chcesz zostać wędkarzem, przynieś mi trzydzieści ryb.",
        "quest": "fisher_30_fish",
    },
    "lumberjack_bran": {
        "name": "Drwal Bran", "room": "lumberjack_camp",
        "dialogue": "Piłę kupisz tylko tutaj. Jeśli chcesz sprawdzić się jako drwal, przynieś mi trzydzieści sztuk dowolnego drewna.",
        "quest": "lumberjack_30_wood",
    },
    "herbalist_liora": {
        "name": "Zielarka Liora", "room": "herbalist_hut",
        "dialogue": "Kupisz u mnie Sierp Zielarski i Moździerz Alchemiczny. Przynieś mi trzydzieści dowolnych ziół, a wynagrodzę twoją pracę.",
        "quest": "herbalist_30_herbs",
    },
    "miner_toren": {
        "name": "Górnik Toren", "room": "cave_entrance",
        "dialogue": "Dobra ruda nie wydobędzie się sama. Przynieś mi trzydzieści sztuk dowolnej rudy z kopalni.",
        "quest": "miner_30_ore",
    },
    "priest_elor": {
        "name": "Kapłan Elor", "room": "temple",
        "dialogue": (
            "Świątynia prowadzi próby Broni Duszy. Tier 2 wymaga Soul Level 25 "
            "i Próby Szkieletów, a Tier 3 Soul Level 60 i Próby Upiorów. "
            "Jeśli nie jesteś jeszcze gotowy, w piwnicy nadal potrzebujemy pomocy ze szczurami."
        ),
        "quest": "temple_rats",
    },
    "captain_arven": {
        "name": "Kapitan Arven", "room": "guard_hall",
        "dialogue": "Gobliny zajęły starą strażnicę. Potrzebujemy kogoś, kto oczyści szlak.",
        "quest": "goblin_problem",
    },
    "watch_commander_roderik": {
        "name": "Dowódca Roderik", "room": "north_watchpost",
        "dialogue": (
            "Bandyci znów zbierają się w obozowisku za Wartownią Pogranicza. "
            "Potrzebujemy regularnych patroli, które ograniczą ich napady."
        ),
        "quest": "bandit_patrol",
    },
    "frontier_guard_anna": {
        "name": "Strażniczka Anna", "room": "frontier_watchpost",
        "dialogue": (
            "Za tą wartownią zaczyna się Obozowisko Bandytów. "
            "Jeśli masz zlecenie od Dowódcy Roderika, trzymaj się na baczności."
        ),
        "quest": None,
    },
    "mira": {
        "name": "Zielarka Mira", "room": "whisper_grove",
        "dialogue": "Wilki Cienia zakłócają równowagę gaju. Ich obecność jest coraz silniejsza.",
        "quest": "shadow_wolves",
    },
    "doran": {
        "name": "Kowal Doran", "room": "forge",
        "dialogue": "Mam pełny żelazny zestaw ochronny. Wpisz list, aby przejrzeć ofertę. Odłamki Duszy z krypty też mnie interesują.",
        "quest": "soul_shards",
    },
    "innkeeper": {
        "name": "Karczmarka Elia", "room": "inn",
        "dialogue": "Witaj w Błękitnym Płomieniu. Na rynku i tutaj kupisz podstawowe mikstury.",
        "quest": None,
    },
    "archivist": {
        "name": "Archiwista Sol", "room": "library",
        "dialogue": "Poziom bohatera jest iluzją. Tutaj mierzymy rozwój czynami i statystykami.",
        "quest": None,
    },
    "teacher_warrior": {
        "name": "Mistrz Garran", "room": "guild_martial_hall",
        "dialogue": "Uczę Wojowników kontroli Miecza Przysięgi i walki frontowej.",
        "teacher_class": "Wojownik",
    },
    "teacher_berserker": {
        "name": "Mistrzyni Brynja", "room": "guild_martial_hall",
        "dialogue": "Uczę Berserkerów kierować furią, zanim furia zacznie kierować nimi.",
        "teacher_class": "Berserker",
    },
    "teacher_rogue": {
        "name": "Mistrz Kael", "room": "guild_shadow_gallery",
        "dialogue": "Uczę Łotrzyków szybkości, precyzji i ataku z cienia.",
        "teacher_class": "Łotrzyk",
    },
    "teacher_hunter": {
        "name": "Mistrzyni Eira", "room": "guild_shadow_gallery",
        "dialogue": "Uczę Łowców wykorzystywać dystans, tempo i Łuk Echa.",
        "teacher_class": "Łowca",
    },
    "teacher_monk": {
        "name": "Mistrz Shen", "room": "guild_body_hall",
        "dialogue": "Uczę Mnichów panowania nad ciałem, oddechem i Rękawicami Ducha.",
        "teacher_class": "Mnich",
    },
    "teacher_guardian": {
        "name": "Mistrz Borin", "room": "guild_body_hall",
        "dialogue": "Uczę Strażników, jak przetrwać uderzenie, które złamałoby innych.",
        "teacher_class": "Strażnik",
    },
    "teacher_mage": {
        "name": "Arcymag Vaelis", "room": "guild_arcane_chamber",
        "dialogue": "Uczę Magów kontroli Many i energii Arkanów.",
        "teacher_class": "Mag",
    },
    "teacher_necromancer": {
        "name": "Mistrzyni Morwen", "room": "guild_dark_chamber",
        "dialogue": "Uczę Nekromantów bezpiecznego obchodzenia się z energią śmierci.",
        "teacher_class": "Nekromanta",
    },
    "teacher_priest": {
        "name": "Mistrz Aureon", "room": "guild_sanctuary",
        "dialogue": "Uczę Kapłanów łączyć świętą moc, leczenie i obronę.",
        "teacher_class": "Kapłan",
    },
    "teacher_warlock": {
        "name": "Mistrzyni Nyra", "room": "guild_dark_chamber",
        "dialogue": "Uczę Czarowników wykorzystywać Otchłań bez oddawania jej całej kontroli.",
        "teacher_class": "Czarownik",
    },
    "teacher_druid": {
        "name": "Mistrz Thalen", "room": "guild_sanctuary",
        "dialogue": "Uczę Druidów czerpać moc z natury, leczenia i burzy.",
        "teacher_class": "Druid",
    },
    "teacher_psion": {
        "name": "Mistrzyni Ilyra", "room": "guild_arcane_chamber",
        "dialogue": "Uczę Psioników dyscypliny umysłu i kontroli energii psionicznej.",
        "teacher_class": "Psionik",
    },
}


NPC_DESCRIPTIONS = {
    "fisher_tomas": (
        "Doświadczony rybak z Targu Rybnego. Uczy podstaw Wędkarstwa i nagradza "
        "graczy, którzy udowodnią cierpliwość przy połowie."
    ),
    "lumberjack_bran": (
        "Doświadczony drwal prowadzący Obóz Drwala. "
        "Jako jedyny sprzedaje Piłę potrzebną do Drwalstwa."
    ),
    "miner_toren": (
        "Doświadczony górnik stojący przy wejściu do Kryształowej Jaskini. "
        "Zleca próbę Górnictwa polegającą na dostarczeniu 30 dowolnych rud."
    ),
    "herbalist_liora": (
        "Zielarka i alchemiczka mieszkająca w Chacie Zielarki. "
        "Sprzedaje Sierp Zielarski i Moździerz Alchemiczny oraz zleca próbę Zielarstwa na 30 ziół."
    ),
    "priest_elor": (
        "Kapłan Świątyni Odrodzenia. Prowadzi próby odblokowania Tier 2 i Tier 3 "
        "Broni Duszy oraz pilnuje bezpieczeństwa świątynnych zapasów."
    ),
    "captain_arven": (
        "Dowódca miejskiej straży. Zleca zadania związane z bezpieczeństwem dróg, "
        "strażnic i okolic Miasta Dusz."
    ),
    "watch_commander_roderik": (
        "Dowódca Wartowni Północnej. Organizuje powtarzalne patrole przeciw bandytom "
        "z Obozowiska Bandytów."
    ),
    "frontier_guard_anna": (
        "Strażniczka z Wartowni Pogranicza. Ostrzega podróżnych przed bandytami "
        "i wskazuje drogę do ich obozowiska."
    ),
    "mira": (
        "Zielarka mieszkająca w Gaju Szeptów. Zna dzicz i reaguje na zagrożenia "
        "naruszające równowagę natury."
    ),
    "doran": (
        "Kowal z Kuźni Dusz. Sprzedaje pełny żelazny zestaw ochronny na głowę, korpus, "
        "dłonie, nogi, stopy i slot talizmanu, a także Kilof. Interesuje się Odłamkami Duszy."
    ),
    "innkeeper": (
        "Karczmarka prowadząca Błękitny Płomień. Sprzedaje podstawowe zapasy i "
        "udziela prostych informacji podróżnym."
    ),
    "archivist": (
        "Archiwista Biblioteki Kronik. Wyjaśnia zasady świata, w którym rozwój "
        "postaci odbywa się przez statystyki, a nie przez level bohatera."
    ),
    "teacher_warrior": "Nauczyciel klasy Wojownik w Sali Gildii.",
    "teacher_berserker": "Nauczycielka klasy Berserker w Sali Gildii.",
    "teacher_rogue": "Nauczyciel klasy Łotrzyk w Sali Gildii.",
    "teacher_hunter": "Nauczycielka klasy Łowca w Sali Gildii.",
    "teacher_monk": "Nauczyciel klasy Mnich w Sali Gildii.",
    "teacher_guardian": "Nauczyciel klasy Strażnik w Sali Gildii.",
    "teacher_mage": "Nauczyciel klasy Mag w Sali Gildii.",
    "teacher_necromancer": "Nauczycielka klasy Nekromanta w Sali Gildii.",
    "teacher_priest": "Nauczyciel klasy Kapłan w Sali Gildii.",
    "teacher_warlock": "Nauczycielka klasy Czarownik w Sali Gildii.",
    "teacher_druid": "Nauczyciel klasy Druid w Sali Gildii.",
    "teacher_psion": "Nauczycielka klasy Psionik w Sali Gildii.",
}

MOB_DESCRIPTIONS = {
    "temple_rat": "Mały, szybki szkodnik z piwnicy świątyni. Dobry pierwszy przeciwnik.",
    "training_dummy": "Magicznie ożywiony manekin przeznaczony do bezpiecznego treningu walki.",
    "goblin": "Lekko uzbrojony goblin nękający drogi i ruiny poza miastem.",
    "goblin_brute": "Silniejszy goblin nastawiony na ciężkie, fizyczne uderzenia.",
    "shadow_wolf": "Drapieżnik skażony energią cienia. Szybszy i groźniejszy od zwykłej bestii.",
    "bandit": "Rozbójnik czatujący na podróżnych na Starym Trakcie.",
    "skeleton": "Nieumarły strażnik krypty. Wytrzymały przeciwnik walczący fizycznie.",
    "crypt_wraith": "Magiczny nieumarły z głębi krypty. Jego ataki sprawdzają obronę magiczną.",
    "crystal_guardian": "Potężny magiczny strażnik Kryształowej Komnaty. Zadaje obrażenia magiczne.",
}

STAT_DESCRIPTIONS = {
    "siła": "Siła zwiększa obrażenia fizyczne postaci.",
    "sila": "Siła zwiększa obrażenia fizyczne postaci.",
    "strength": "Siła zwiększa obrażenia fizyczne postaci.",
    "zręczność": (
        "Zręczność zwiększa Szybkość. Wyższa Szybkość zwiększa szansę uniknięcia "
        "kontrataku. Aktualny limit uniku wynosi 35 procent."
    ),
    "zrecznosc": (
        "Zręczność zwiększa Szybkość. Wyższa Szybkość zwiększa szansę uniknięcia "
        "kontrataku. Aktualny limit uniku wynosi 35 procent."
    ),
    "dexterity": (
        "Zręczność zwiększa Szybkość. Wyższa Szybkość zwiększa szansę uniknięcia kontrataku."
    ),
    "kondycja": "Kondycja zwiększa maksymalne HP. Każdy punkt Kondycji daje 5 maksymalnego HP.",
    "constitution": "Kondycja zwiększa maksymalne HP. Każdy punkt Kondycji daje 5 maksymalnego HP.",
    "inteligencja": "Inteligencja zwiększa maksymalną Manę klas magicznych oraz ich Moc czarów.",
    "intelligence": "Inteligencja zwiększa maksymalną Manę klas magicznych oraz ich Moc czarów.",
    "siła woli": "Siła Woli zwiększa obronę magiczną.",
    "sila woli": "Siła Woli zwiększa obronę magiczną.",
    "willpower": "Siła Woli zwiększa obronę magiczną.",
}

SYSTEM_DESCRIPTIONS = {
    "wędkarstwo": (
        "Wędkarstwo ma własny poziom 1-100. Do połowu potrzebna jest Wędka, która ma "
        "osobny level i osobny XP. Użyj fish albo low. Auto-łowienie: low on i low off."
    ),
    "wedkarstwo": (
        "Wędkarstwo ma własny poziom 1-100. Do połowu potrzebna jest Wędka, która ma "
        "osobny level i osobny XP. Użyj fish albo low. Auto-łowienie: low on i low off."
    ),
    "fishing": "Wędkarstwo ma własny poziom 1-100, a Wędka własny niezależny level 1-100.",
    "górnictwo": (
        "Górnictwo ma własny poziom 1-100. Kilof ma osobny level 1-100. "
        "Użyj mine albo kop. Auto-kopanie: kop on i kop off. "
        "Czysty mithril może zostać wydobyty bezpośrednio dopiero od levelu 80 Kilofa."
    ),
    "gornictwo": (
        "Górnictwo ma własny poziom 1-100. Kilof ma osobny level 1-100. "
        "Czysty mithril może zostać wydobyty bezpośrednio dopiero od levelu 80 Kilofa."
    ),
    "mining": "Górnictwo ma własny poziom 1-100, a Kilof własny niezależny level 1-100.",
    "broń duszy": (
        "Broń Duszy jest na stałe związana z klasą. Ma osobny Soul Level 1-200 i Soul XP. "
        "Tier 2 odblokowuje się od Soul Level 25, a Tier 3 od Soul Level 60."
    ),
    "bron duszy": "Broń Duszy ma osobny Soul Level 1-200 i trzy Tiers.",
    "soul weapon": "Broń Duszy ma osobny Soul Level 1-200 i trzy Tiers.",
    "srebro": "Srebro jest podstawową walutą. 1000 srebra można wymienić na 1 złoto.",
    "silver": "Srebro jest podstawową walutą. 1000 srebra = 1 złoto.",
    "złoto": "Złoto jest walutą wyższego rzędu. 1000000 złota można wymienić na 1 mithril.",
    "zloto": "Złoto jest walutą wyższego rzędu. 1000000 złota = 1 mithril.",
    "gold": "Złoto jest walutą wyższego rzędu. 1000000 złota = 1 mithril.",
    "mithril": (
        "Mithril jest najrzadszą walutą. 1 mithril = 1000000 złota. "
        "Może być nagrodą lub bardzo rzadkim bezpośrednim wydobyciem wysokopoziomowym Kilofem."
    ),
    "siatka": "Siatka na ryby jest osobnym trwałym magazynem profesji i nie zajmuje zwykłego ekwipunku.",
    "net": "Siatka na ryby jest osobnym magazynem wszystkich złowionych ryb.",
    "sakwa": "Sakwa górnicza jest osobnym trwałym magazynem profesji i przechowuje zwykłe rudy.",
    "bag": "Sakwa górnicza jest osobnym magazynem wydobytych rud.",
    "śmierć": (
        "Po śmierci postać odradza się w Świątyni Odrodzenia i traci 10 procent "
        "każdej posiadanej waluty osobno."
    ),
    "smierc": "Po śmierci postać odradza się w Świątyni Odrodzenia i traci 10 procent każdej waluty.",
    "death": "Po śmierci postać odradza się w Świątyni Odrodzenia i traci część waluty.",
}


LATEST_CHANGES_TITLE = "Soulbound v0.6.72 - Temple Login Spawn"
LATEST_CHANGES = [
    "Po każdym zalogowaniu postać rozpoczyna sesję w Świątyni Odrodzenia.",
    "Miejsce wylogowania nie jest już miejscem startowym kolejnej sesji.",
    "Nowe postacie również wchodzą do świata w Świątyni Odrodzenia.",
    "Przy logowaniu zapisywana lokacja postaci zostaje ustawiona na Świątynię Odrodzenia.",
    "Zachowano synchronizację starych Portali Krypty przed przeniesieniem do Świątyni.",
    "Questy, ekwipunek, waluty, Soul Level i pozostała progresja pozostają bez zmian.",
    "Pełne HP po awansie Soul Level pozostaje bez zmian.",
    "Soul Level 1-200 pozostaje bez zmian.",
    "Próg statystyk 50 pozostaje bez zmian.",
    "Narzędzia 1-200 i 13 Tierów pozostają bez zmian.",
    "Soulbound nadal nie ma levelu postaci.",
    "Nie wymaga migracji SQLite.",
    "Zaktualizowano help logowanie, README, RAILWAY_PL i pełny changelog.",
]

HELP_TOPIC_ALIASES = {
    "temat": "tematy", "topics": "tematy",
    "all": "wszystko",
    "commands": "komendy", "command": "komendy",
    "basics": "podstawy", "start": "podstawy",
    "movement": "nawigacja", "navigation": "nawigacja",
    "stats": "statystyki", "stat": "statystyki",
    "odmiana": "odmiana_imienia", "przypadki": "odmiana_imienia", "namecases": "odmiana_imienia", "declension": "odmiana_imienia",
    "combat": "walka", "fight": "walka",
    "login": "logowanie", "logowanie": "logowanie", "spawn": "logowanie", "start": "logowanie",
    "critical": "krytyki", "crit": "krytyki",
    "statgrowth": "rozwoj_statystyk", "rozwojstatystyk": "rozwoj_statystyk", "rozwoj": "rozwoj_statystyk",
    "uzyjskill": "uzywanie_umiejetnosci", "uzywanieumiejetnosci": "uzywanie_umiejetnosci", "useskill": "uzywanie_umiejetnosci",
    "criticalhits": "krytyki", "krytyk": "krytyki",
    "krytyki": "krytyki",
    "respawn": "respawn", "odrodzenie": "respawn",
    "odradzanie": "respawn",
    "bosses": "bossowie", "boss": "bossowie", "bossowie": "bossowie", "herszt": "bossowie",
    "soul": "dusza", "soulweapon": "dusza",
    "money": "pieniadze", "economy": "pieniadze",
    "equipment": "ekwipunek", "items": "ekwipunek",
    "rarity": "loot_krypty", "rzadkosc": "loot_krypty", "rzadkość": "loot_krypty", "set": "loot_krypty", "sety": "loot_krypty", "lootkrypty": "loot_krypty",
    "quests": "zadania", "quest": "zadania",
    "professions": "profesje",
    "fishing": "wedkarstwo", "fish": "wedkarstwo",
    "mining": "gornictwo", "mine": "gornictwo",
    "woodcutting": "drwalstwo", "drwal": "drwalstwo",
    "crafting": "rzemioslo", "craft": "rzemioslo", "rzemiosło": "rzemioslo",
    "cooking": "gotowanie", "cook": "gotowanie",
    "herbalism": "zielarstwo", "zielarstwo": "zielarstwo",
    "alchemy": "alchemia", "alchemia": "alchemia",
    "recipes": "receptury", "recipe": "receptury", "przepisy": "receptury",
    "containers": "pojemniki",
    "shops": "sklepy", "shop": "sklepy",
    "multiplayer": "gracze", "players": "gracze",
    "death": "smierc",
    "races": "rasy", "race": "rasy",
    "classes": "klasy", "class": "klasy",
    "descriptions": "opisy", "describe": "opisy",
    "skills": "umiejetnosci", "abilities": "umiejetnosci",
    "skillnames": "nazwy_skilli", "nazwyskilli": "nazwy_skilli",
    "teachers": "nauczyciele", "trainers": "nauczyciele",
    "multiclass": "multiclass", "multiklasa": "multiclass",
    "multiklas": "multiclass", "klasy": "multiclass",
    "changes": "zmiany", "changelog": "zmiany",
    "corpse": "zwloki", "body": "zwloki", "cialo": "zwloki", "ciało": "zwloki",
    "loot": "zwloki", "zwloki": "zwloki", "zwłoki": "zwloki",
    "crypt": "krypta", "krypta": "krypta",
    "portal": "portale", "portals": "portale", "portale": "portale",
    "portalkrypty": "portale", "cryptportal": "portale",
    "checkpoint": "portale", "checkpoints": "portale",
    "punktkrypty": "portale", "punktykrypty": "portale",
    "atlas": "atlas", "atlasy": "atlas",
    "party": "druzyny", "parties": "druzyny", "druzyna": "druzyny", "drużyna": "druzyny",
    "charisma": "charyzma", "charyzma": "charyzma", "haryzma": "charyzma",
}

HELP_TOPICS = {
    "logowanie": [
        "Po każdym zalogowaniu postać rozpoczyna sesję w Świątyni Odrodzenia.",
        "Nie ma znaczenia, gdzie postać wylogowała się poprzednio.",
        "Zapisana lokacja z poprzedniej sesji nie jest miejscem startowym następnego logowania.",
        "Po wejściu do świata HP i Mana są ustawiane jak dotychczas przy logowaniu.",
        "Portale Krypty, questy, ekwipunek i cała trwała progresja pozostają zapisane.",
    ],
    "soul_level_hp": [
        "Każdy awans Soul Level Broni Duszy natychmiast odnawia postać do 100 procent HP.",
        "Działa niezależnie od źródła Soul XP, między innymi z przeciwników oraz Eliksiru Duszy.",
        "Jeżeli Soul XP nie wbije nowego Soul Levelu, HP nie jest odnawiane.",
        "Odnowienie dotyczy tylko HP. Mana nie jest automatycznie odnawiana.",
        "Soul Level nadal ma zakres 1-200.",
    ],
    "rozwoj_statystyk": [
        "Statystyki rosną automatycznie przez Postęp Rozwoju.",
        "Próg wzrostu został zmniejszony do 50 Postępu Rozwoju.",
        "Każde pełne 50 Postępu Rozwoju daje jednocześnie: Siła +1, Zręczność +1, Kondycja +1, Inteligencja +1 i Siła Woli +1.",
        "To oznacza dwa razy szybszy wzrost statystyk niż przy starym progu 100.",
        "Nie ma ręcznego rozdawania punktów.",
        "Levelu postaci nadal nie ma.",
        "Bonus rasy Człowiek do Postępu Rozwoju nadal działa.",
    ],
    "uzywanie_umiejetnosci": [
        "Umiejętności można używać dotychczasową komendą skill <nazwa lub numer> [cel].",
        "Działa też umiejętność <nazwa> [cel], zdolność <nazwa> [cel] oraz cast <nazwa> [cel].",
        "Dodano składnię użyj umiejętność <nazwa> [cel].",
        "Angielska wersja to use skill <name> [target].",
        "Jeżeli po use/użyj podasz bezpośrednio rozpoznawalną nazwę skilla, gra także spróbuje go użyć.",
        "Ofensywne umiejętności nadal rozpoczynają walkę tylko na wyraźną akcję gracza.",
        "Cooldown, Mana, Skill Level i zdobywanie Skill XP działają dokładnie tak jak przy komendzie skill.",
    ],
    "soul200": [
        "Broń Duszy ma teraz Soul Level 1-200.",
        "Soul XP i wzór progresji pozostają takie jak wcześniej.",
        "Tier 2 nadal odblokowuje się przez próbę od Soul Level 25.",
        "Tier 3 nadal odblokowuje się przez próbę od Soul Level 60.",
        "Po Soul Level 100 Broń Duszy rozwija się dalej aż do 200.",
        "Soul Level nadal zwiększa bazową moc Broni Duszy.",
        "Nie ma levelu postaci.",
    ],
    "narzedzia200": [
        "Wszystkie 7 narzędzi ma level 1-200 i 13 Tierów.",
        "Wędka, Kilof, Piła, Młot Rzemieślniczy, Nóż Kucharski, Sierp Zielarski i Moździerz Alchemiczny rozwijają się do 200.",
        "Tier 8: level 100-119, bonus 15 procent.",
        "Tier 9: level 120-139, bonus 18 procent.",
        "Tier 10: level 140-159, bonus 21 procent.",
        "Tier 11: level 160-179, bonus 24 procent.",
        "Tier 12: level 180-199, bonus 27 procent.",
        "Tier 13: level 200, bonus 30 procent.",
        "Każdy Tier 9-13 ma osobną nazwę dla każdego rodzaju narzędzia.",
        "tools, tiers oraz bezpośrednie komendy narzędzi pokazują aktualny Tier i następny próg.",
    ],
    "krytyki": [
        "Trafienia krytyczne zależą od efektywnej Zręczności, czyli także od bonusów ekwipunku.",
        "Przy Zręczności 10 bazowa szansa na krytyk wynosi 5 procent.",
        "Każdy punkt Zręczności ponad 10 dodaje 0,5 punktu procentowego szansy.",
        "Zręczność poniżej 10 obniża szansę o 0,5 punktu procentowego za punkt.",
        "Minimalna szansa wynosi 1 procent, maksymalna 35 procent.",
        "Trafienie krytyczne zadaje 150 procent normalnych obrażeń.",
        "Krytyki działają dla zwykłego ataku i ofensywnych umiejętności klasowych.",
        "Mechaniki obronne bossów nadal mogą zredukować albo anulować krytyk.",
        "stats pokazuje aktualną szansę na krytyk i mnożnik.",
    ],
    "respawn": [
        "Zwykłe moby odradzają się po 120 sekundach od śmierci.",
        "Bossowie Krypty i Herszt Bandytów odradzają się po 300 sekundach.",
        "Żywy Manekin treningowy odradza się po 60 sekundach.",
        "Po respawnie boss Krypty ponownie blokuje zejście na następne piętro.",
    ],
    "bossowie": [
        "Bossowie nadal działają w walce turowej: jedna akcja gracza, potem jedna odpowiedź przeciwnika.",
        "Bossowie i zwykłe moby nie są agresywne; nie zaczynają walki sami.",
        "Kościany Egzekutor: co trzeci kontratak używa Kościanego Miażdżenia.",
        "Krwawy Kurator: co trzeci kontratak używa Krwawego Drenażu i leczy się częścią zadanych obrażeń.",
        "Rycerz Grobowca: co trzecie trafienie gracza redukuje Tarczą Grobowca o połowę.",
        "Wiedźma Popiołu: co trzeci kontratak używa Klątwy Popiołu, która omija połowę obrony magicznej.",
        "Pan Katakumb: co czwarty kontratak używa Echa Katakumb.",
        "Widmowy Tytan: naprzemiennie zmienia kontratak fizyczny i magiczny.",
        "Nekromantyczny Kolos: co czwarty kontratak regeneruje 7 procent maksymalnego HP.",
        "Arcyupiór Otchłani: ma 25 procent szansy na eteryczny unik przeciw trafieniu gracza.",
        "Król Kości: poniżej 50 procent HP zadaje 50 procent więcej obrażeń.",
        "Władca Stu Pięter: poniżej połowy HP wchodzi w drugą fazę; co trzeci kontratak używa Załamania Duszy, a co czwarte trafienie gracza osłabia Pieczęcią Stu Pięter.",
        "Każdy boss Krypty ma własny unikalny relikt. Boss piętra 100 gwarantuje relikt, pozostałe mają 45 procent szansy.",
        "W Obozowisku Bandytów pojawia się Herszt Bandytów. Co trzeci kontratak wykonuje Brutalną Kombinację.",
        "Herszt Bandytów może upuścić unikalny Sygnet Herszta Bandytów.",
        "Król Goblinów pojawia się w Obozie Goblinów i co trzeci kontratak wykonuje Królewską Szarżę.",
        "Alfa Wilków Cienia pojawia się w Głębi Gaju i poniżej połowy HP wpada w Szał Cienia.",
        "Strażnik Ruin pojawia się przy Zrujnowanej Wieży i co czwarty kontratak używa Runicznego Wybuchu.",
        "Kryształowy Władca pojawia się w Kryształowej Komnacie; używa Kryształowego Promienia i Kryształowej Bariery.",
        "Każdy z nowych bossów świata ma własny unikalny przedmiot z 45 procent szansy.",
    ],
    "loot_krypty": [
        "Ekwipunek z Krypty ma 5 rzadkości: Zwykły, Rzadki, Epicki, Legendarny i Mityczny.",
        "Wyższa rzadkość daje większą obronę i mocniejszy losowy affix.",
        "Losowe affixy to: Siła, Zręczność, Kondycja, Inteligencja, Siła Woli, HP albo Mana.",
        "Zwykłe moby częściej dają Zwykły lub Rzadki loot.",
        "Bossowie mają dużo lepszą szansę na Epicki, Legendarny i Mityczny loot.",
        "Każdy element Krypty należy do Zestawu Krypty swojego Tieru 1-10.",
        "Dominujący set to Tier, którego masz założonych najwięcej części; przy remisie wygrywa wyższy Tier.",
        "2 części jednego setu: +10 procent maksymalnego HP i Many.",
        "4 części jednego setu: dodatkowo +10 procent wszystkich zadawanych obrażeń.",
        "6 części jednego setu: dodatkowo +15 procent obrony fizycznej i magicznej.",
        "Komenda equipment pokazuje rarity, affix oraz aktywny bonus setu.",
        "Komenda stats pokazuje statystyki bazowe, statystyki z wyposażeniem oraz bonusy setu.",
        "Stare przedmioty Krypty pozostają działające i liczą się do odpowiedniego setu jako Zwykłe bez affixu.",
    ],
    "portale": [
        "Portal Krypty odblokowuje się po pokonaniu bossa co 10 pięter.",
        "Portale prowadzą na piętra 10, 20, 30, 40, 50, 60, 70, 80, 90 i 100.",
        "Odblokowanie portalu zapisuje się trwale w SQLite.",
        "portal pokazuje wszystkie odblokowane cele.",
        "portal 30 przenosi z Sali Krypty lub Przedsionka Krypty bezpośrednio na piętro 30.",
        "Portal służy tylko do szybkiego powrotu i nie wyłącza bossa.",
        "Jeśli boss na piętrze portalu żyje, nadal blokuje zejście na następne piętro.",
        "Po zabiciu bossa przejście jest otwarte do respawnu; po respawnie boss znowu blokuje.",
        "Portalu nie można używać podczas walki.",
        "Stare komendy checkpoint nadal działają jako alias portalu dla zgodności.",
    ],
    "krypta": [
        "Loot Krypty ma rarity, losowe affixy statystyk i bonusy setowe 2/4/6 części.",
        "Wpisz help loot_krypty, help rarity albo help sety po szczegóły.",
        "Krypta ma 100 realnych pięter połączonych up i down.",
        "Na każdym piętrze znajduje się skalowany przeciwnik.",
        "Moby nie są agresywne i nie rozpoczynają walki same.",
        "Bossowie są na piętrach 10, 20, 30, 40, 50, 60, 70, 80, 90 i 100.",
        "Każdy żywy boss zawsze blokuje zejście na następne piętro.",
        "Po zabiciu bossa przejście jest otwarte do czasu jego respawnu.",
        "Po respawnie boss ponownie blokuje przejście.",
        "Pokonanie bossa odblokowuje trwały Portal Krypty do jego piętra.",
        "portal pokazuje odblokowane cele; portal 50 przenosi na piętro 50.",
        "Portal nie omija żywego bossa.",
        "Zwykły mob Krypty daje 100 + piętro*10 Soul XP.",
        "Boss Krypty daje 600 + piętro*20 Soul XP.",
        "Zwykły mob zostawia 1 element ekwipunku na ciele, boss 3.",
        "prowadz krypta 25 prowadzi normalną trasą i zatrzyma się na żywym bossie.",
        "Co 10 pięter zmienia się Tier ekwipunku znajdowanego na ciałach.",
    ],
    "multiclass": [
        "Multiclass jest całkowicie opcjonalny.",
        "Każda postać ma jedną klasę główną i może włączyć maksymalnie dwie dodatkowe klasy, czyli 3 aktywne łącznie.",
        "multiclass pokazuje aktywne klasy i ich Biegłość.",
        "multiclass add <klasa> włącza klasę dodatkową.",
        "multiclass remove <klasa> wyłącza klasę dodatkową. Klasy głównej nie można wyłączyć.",
        "Klasa główna zachowuje swoją Broń Duszy. Jej bonus klasowy także zawsze wzmacnia klasę główną; dodatkowe klasy nie dostają osobnej Broni Duszy.",
        "Dodatkowe klasy aktywują swoje pasywy i dają dostęp do własnych nauczycieli oraz skilli.",
        "Class XP z zabitego moba jest jedną pulą dzieloną równo między wszystkie aktywne klasy.",
        "Każda klasa ma własną Biegłość 1-100 i własny Class XP. To nie jest level postaci.",
        "Wyłączenie klasy nie kasuje jej Biegłości ani wcześniej nauczonych skilli, ale skilli nie można używać, gdy klasa jest nieaktywna.",
        "Jeśli włączysz klasę magiczną jako dodatkową, postać otrzymuje pulę Many i może używać jej magicznych skilli.",
    ],
    "opisy": [
        "Komenda opis bez argumentu opisuje aktualną lokację.",
        "opis <przedmiot> pokazuje działanie, typ i ceny.",
        "opis <NPC> pokazuje rolę, lokację i powiązane zadanie.",
        "NPC-e pomocni, handlowi, zadaniowi i nauczyciele są pokojowi oraz chronieni przed walką.",
        "opis <przeciwnik> pokazuje HP, obrażenia, typ ataku i nagrody.",
        "opis <lokacja> pokazuje strefę, opis, wyjścia i specjalne funkcje.",
        "opis <zadanie>, opis <rasa>, opis <klasa>, opis <statystyka> i opis <waluta> także działają.",
    ],
    "zmiany": [
        "changes, zmiany albo changelog pokazuje pełną historię wszystkich wersji.",
        "Najnowsza wersja jest na górze, starsze wersje są niżej.",
        "Historia jest czytana z CHANGELOG_PL.txt linia po linii dla NVDA.",
    ],
}

QUESTS = {
    "fisher_30_fish": {
        "name": "Próba Rybaka",
        "giver": "Rybak Tomas",
        "kind": "collect_category", "target": "fish", "needed": 30,
        "description": "Przynieś Rybakowi Tomasowi 30 dowolnych ryb.",
        "reward_profession": "Wędkarstwo",
        "reward_profession_xp": 1000,
        "reward_tool_type": "fishing",
        "reward_tool_xp": 1000,
        "reward_silver": 50, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "miner_30_ore": {
        "name": "Próba Górnika",
        "giver": "Górnik Toren",
        "kind": "collect_category", "target": "ore", "needed": 30,
        "description": "Przynieś Górnikowi Torenowi 30 dowolnych rud.",
        "reward_profession": "Górnictwo",
        "reward_profession_xp": 1000,
        "reward_tool_type": "mining",
        "reward_tool_xp": 1000,
        "reward_silver": 50, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "lumberjack_30_wood": {
        "name": "Próba Drwala",
        "giver": "Drwal Bran",
        "kind": "collect_category", "target": "wood", "needed": 30,
        "description": "Przynieś Drwalowi Branowi 30 sztuk dowolnego drewna.",
        "reward_profession": "Drwalstwo",
        "reward_profession_xp": 1000,
        "reward_tool_type": "woodcutting",
        "reward_tool_xp": 1000,
        "reward_silver": 50, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "herbalist_30_herbs": {
        "name": "Próba Zielarki",
        "giver": "Zielarka Liora",
        "kind": "collect_category", "target": "herb", "needed": 30,
        "description": "Przynieś Zielarce Liorze 30 dowolnych ziół.",
        "reward_profession": "Zielarstwo",
        "reward_profession_xp": 1000,
        "reward_tool_type": "herbalism",
        "reward_tool_xp": 1000,
        "reward_silver": 50, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "soul_tier_2_trial": {
        "name": "Próba Broni Duszy: Tier 2",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "skeleton", "needed": 5,
        "description": (
            "Pokonaj 5 Szkieletów Strażników, wróć do Kapłana Elora "
            "w Świątyni Odrodzenia i potwierdź gotowość Broni Duszy."
        ),
        "required_soul_level": 25,
        "required_soul_tier": 1,
        "unlocks_soul_tier": 2,
        "reward_silver": 100, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_3_trial": {
        "name": "Próba Broni Duszy: Tier 3",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_wraith", "needed": 3,
        "description": (
            "Pokonaj 3 Upiory Krypty, wróć do Kapłana Elora "
            "w Świątyni Odrodzenia i potwierdź pełnię mocy Broni Duszy."
        ),
        "required_soul_level": 60,
        "required_soul_tier": 2,
        "unlocks_soul_tier": 3,
        "reward_silver": 250, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
    },
    "temple_rats": {
        "name": "Szczury pod świątynią",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "temple_rat", "needed": 10,
        "description": "Zejdź do piwnicy Świątyni Odrodzenia i zabij 10 szczurów.",
        "reward_stat_progress": 120,
        "reward_silver": 75, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"healing_potion": 1},
    },
    "goblin_problem": {
        "name": "Problem goblinów",
        "giver": "Kapitan Arven",
        "kind": "kill", "target": "goblin", "needed": 3,
        "description": "Pokonaj 3 gobliny w ruinach i obozie.",
        "reward_silver": 100, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"healing_potion": 2},
    },
    "bandit_patrol": {
        "name": "Patrol przeciw bandytom",
        "giver": "Dowódca Roderik",
        "kind": "kill", "target": "bandit", "needed": 10,
        "description": (
            "Pokonaj 10 bandytów w Obozowisku Bandytów i wróć "
            "do Dowódcy Roderika w Wartowni Północnej."
        ),
        "reward_stat_progress": 150,
        "reward_silver": 250, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"healing_potion": 2},
        "repeatable": True,
        "repeat_cooldown": 60 * 60,
    },
    "shadow_wolves": {
        "name": "Cienie w gaju",
        "giver": "Zielarka Mira",
        "kind": "kill", "target": "shadow_wolf", "needed": 2,
        "description": "Pokonaj 2 Wilki Cienia w Gaju Szeptów.",
        "reward_silver": 120, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"healing_potion": 1},
    },
    "soul_shards": {
        "name": "Odłamki dla kowala",
        "giver": "Kowal Doran",
        "kind": "collect", "target": "soul_shard", "needed": 3,
        "description": "Przynieś 3 Odłamki Duszy z krypty.",
        "reward_silver": 300, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"soul_elixir": 1},
    },
}

MOB_TEMPLATES = {
    "temple_rat": {
        "name": "Szczur Świątynny", "max_hp": 28, "damage": 3, "damage_type": "physical",
        "silver": 6, "gold": 0, "mithril": 0,
        "stat_reward": 8, "soul_reward": 80,
        "drops": {}, "quest_target": "temple_rat",
    },
    "training_dummy": {
        "name": "Żywy Manekin", "max_hp": 45, "damage": 4, "damage_type": "physical",
        "silver": 12, "gold": 0, "mithril": 0, "stat_reward": 18, "soul_reward": 100,
        "drops": {}, "quest_target": None,
        "training_dummy": True,
    },
    "goblin": {
        "name": "Goblin", "max_hp": 60, "damage": 7, "damage_type": "physical",
        "silver": 28, "gold": 0, "mithril": 0, "stat_reward": 30, "soul_reward": 140,
        "drops": {"healing_potion": 0.08}, "quest_target": "goblin",
    },
    "goblin_brute": {
        "name": "Gobliński Osiłek", "max_hp": 85, "damage": 10, "damage_type": "physical",
        "silver": 45, "gold": 1, "mithril": 0, "stat_reward": 38, "soul_reward": 180,
        "drops": {"healing_potion": 0.12}, "quest_target": "goblin",
    },
    "shadow_wolf": {
        "name": "Wilk Cienia", "max_hp": 70, "damage": 9, "damage_type": "physical",
        "silver": 32, "gold": 0, "mithril": 0, "stat_reward": 34, "soul_reward": 160,
        "drops": {"wolf_fang": 0.45}, "quest_target": "shadow_wolf",
    },
    "bandit": {
        "name": "Bandyta", "max_hp": 75, "damage": 9, "damage_type": "physical",
        "silver": 40, "gold": 0, "mithril": 0, "stat_reward": 35, "soul_reward": 170,
        "drops": {"healing_potion": 0.10}, "quest_target": "bandit",
    },
    "bandit_marauder": {
        "name": "Bandycki Maruder", "max_hp": 105, "damage": 12, "damage_type": "physical",
        "silver": 65, "gold": 0, "mithril": 0, "stat_reward": 48, "soul_reward": 220,
        "drops": {"healing_potion": 0.14}, "quest_target": "bandit",
    },
    "bandit_chief": {
        "name": "Herszt Bandytów",
        "max_hp": 320,
        "damage": 24,
        "damage_type": "physical",
        "silver": 420,
        "gold": 0,
        "mithril": 0,
        "stat_reward": 180,
        "class_xp_reward": 2200,
        "soul_reward": 650,
        "drops": {
            "healing_potion": 0.60,
            "bandit_chief_signet": 0.45,
        },
        "quest_target": "bandit",
        "boss_mechanic": "bandit_combo",
        "world_boss": True,
        "corpse_equipment_pool": [
            "iron_helmet", "iron_guard", "iron_gauntlets",
            "iron_leggings", "iron_boots", "lucky_charm"
        ],
        "corpse_equipment_guaranteed": 2,
    },
    "goblin_king": {
        "name": "Król Goblinów",
        "max_hp": 360,
        "damage": 25,
        "damage_type": "physical",
        "silver": 500,
        "gold": 1,
        "mithril": 0,
        "stat_reward": 200,
        "class_xp_reward": 2600,
        "soul_reward": 720,
        "drops": {
            "healing_potion": 0.65,
            "goblin_king_crown": 0.45,
        },
        "quest_target": "goblin",
        "boss_mechanic": "goblin_king",
        "world_boss": True,
        "corpse_equipment_pool": [
            "iron_helmet", "iron_gauntlets", "iron_boots", "lucky_charm"
        ],
        "corpse_equipment_guaranteed": 2,
    },
    "shadow_alpha": {
        "name": "Alfa Wilków Cienia",
        "max_hp": 390,
        "damage": 27,
        "damage_type": "physical",
        "silver": 480,
        "gold": 1,
        "mithril": 0,
        "stat_reward": 215,
        "class_xp_reward": 2900,
        "soul_reward": 780,
        "drops": {
            "wolf_fang": 1.0,
            "shadow_alpha_fang": 0.45,
        },
        "quest_target": "shadow_wolf",
        "boss_mechanic": "shadow_alpha",
        "world_boss": True,
        "corpse_equipment_pool": [
            "leather_vest", "lucky_charm", "iron_boots"
        ],
        "corpse_equipment_guaranteed": 2,
    },
    "ruin_warden": {
        "name": "Strażnik Ruin",
        "max_hp": 430,
        "damage": 29,
        "damage_type": "physical",
        "silver": 550,
        "gold": 2,
        "mithril": 0,
        "stat_reward": 235,
        "class_xp_reward": 3300,
        "soul_reward": 860,
        "drops": {
            "soul_shard": 0.80,
            "ruin_warden_plate": 0.45,
        },
        "quest_target": None,
        "boss_mechanic": "ruin_warden",
        "world_boss": True,
        "corpse_equipment_pool": [
            "iron_helmet", "iron_guard", "iron_gauntlets",
            "iron_leggings", "iron_boots"
        ],
        "corpse_equipment_guaranteed": 2,
    },
    "crystal_lord": {
        "name": "Kryształowy Władca",
        "max_hp": 500,
        "damage": 32,
        "damage_type": "magic",
        "silver": 0,
        "gold": 8,
        "mithril": 1,
        "stat_reward": 270,
        "class_xp_reward": 4000,
        "soul_reward": 1000,
        "drops": {
            "soul_elixir": 0.35,
            "crystal_lord_core": 0.45,
        },
        "quest_target": None,
        "boss_mechanic": "crystal_lord",
        "world_boss": True,
        "corpse_equipment_pool": [
            "iron_guard", "iron_leggings", "forge_charm", "lucky_charm"
        ],
        "corpse_equipment_guaranteed": 2,
    },
    "skeleton": {
        "name": "Szkielet Strażnik", "max_hp": 90, "damage": 11, "damage_type": "physical",
        "silver": 30, "gold": 1, "mithril": 0, "stat_reward": 42, "soul_reward": 240,
        "drops": {"soul_shard": 0.55}, "quest_target": "skeleton",
    },
    "crypt_wraith": {
        "name": "Upiór Krypty", "max_hp": 120, "damage": 14, "damage_type": "magic",
        "silver": 0, "gold": 2, "mithril": 1, "stat_reward": 55, "soul_reward": 280,
        "drops": {"soul_shard": 0.85}, "quest_target": "crypt_wraith",
    },
    "crystal_guardian": {
        "name": "Kryształowy Strażnik", "max_hp": 140, "damage": 15, "damage_type": "magic",
        "silver": 0, "gold": 4, "mithril": 1, "stat_reward": 60, "soul_reward": 320,
        "drops": {"soul_elixir": 0.08}, "quest_target": None,
    },
}

# room_id, template_id
MOB_SPAWNS = [
    ("temple_basement", "temple_rat"),
    ("temple_basement", "temple_rat"),
    ("temple_basement", "temple_rat"),
    ("temple_basement", "temple_rat"),
    ("training", "training_dummy"),
    ("old_road", "bandit"),
    ("bandit_camp", "bandit"),
    ("bandit_camp", "bandit"),
    ("bandit_camp", "bandit"),
    ("bandit_camp", "bandit"),
    ("bandit_camp", "bandit_marauder"),
    ("bandit_camp", "bandit_marauder"),
    ("bandit_camp", "bandit_chief"),
    ("goblin_camp", "goblin_king"),
    ("deep_grove", "shadow_alpha"),
    ("ruined_watchtower", "ruin_warden"),
    ("crystal_chamber", "crystal_lord"),
    ("deep_grove", "shadow_wolf"),
    ("whisper_grove", "shadow_wolf"),
    ("ruined_watchtower", "goblin"),
    ("goblin_camp", "goblin"),
    ("goblin_camp", "goblin_brute"),
    ("crypt_hall", "skeleton"),
    ("crypt_depths", "crypt_wraith"),
    ("crystal_chamber", "crystal_guardian"),
]


CRYPT_MAX_FLOOR = 100
CRYPT_BOSS_FLOORS = tuple(range(10, 101, 10))
CRYPT_BOSS_NAMES = {
    10: "Kościany Egzekutor", 20: "Krwawy Kurator",
    30: "Rycerz Grobowca", 40: "Wiedźma Popiołu",
    50: "Pan Katakumb", 60: "Widmowy Tytan",
    70: "Nekromantyczny Kolos", 80: "Arcyupiór Otchłani",
    90: "Król Kości", 100: "Władca Stu Pięter",
}

CRYPT_BOSS_MECHANICS = {
    10: "bone_crush",
    20: "blood_drain",
    30: "grave_shield",
    40: "ash_curse",
    50: "catacomb_echo",
    60: "spectral_shift",
    70: "necro_regen",
    80: "ethereal_evade",
    90: "bone_rage",
    100: "hundred_lord",
}

CRYPT_BOSS_MECHANIC_TEXT = {
    10: "Co trzeci kontratak: Kościane Miażdżenie, mocniejszy cios fizyczny.",
    20: "Co trzeci kontratak: Krwawy Drenaż, mocniejszy cios leczący bossa.",
    30: "Co trzecie trafienie gracza: Tarcza Grobowca redukuje obrażenia o połowę.",
    40: "Co trzeci kontratak: Klątwa Popiołu, magiczny atak ignorujący połowę obrony magicznej.",
    50: "Co czwarty kontratak: Echo Katakumb, jedna potężna seria liczona jako pojedyncza odpowiedź bossa.",
    60: "Widmowy Tytan zmienia typ obrażeń między fizycznym i magicznym co turę.",
    70: "Co czwarty kontratak: Nekroregeneracja odnawia 7 procent maksymalnego HP bossa.",
    80: "Arcyupiór ma 25 procent szansy na eteryczny unik przeciw trafieniu gracza.",
    90: "Poniżej połowy HP Król Kości wpada w furię i zadaje 50 procent więcej obrażeń.",
    100: "Poniżej połowy HP Władca Stu Pięter wzmacnia się; co trzeci kontratak używa Załamania Duszy.",
}

CRYPT_REGULAR_NAMES = (
    "Szkielet Krypty", "Upiór Krypty",
    "Strażnik Sarkofagu", "Cień Katakumb",
)

def crypt_floor_id(floor):
    return f"crypt_floor_{int(floor)}"

def crypt_floor_number(room_id):
    m = re.fullmatch(r"crypt_floor_(\d+)", str(room_id))
    if not m: return None
    floor=int(m.group(1))
    return floor if 1 <= floor <= CRYPT_MAX_FLOOR else None


CRYPT_RARITIES = {
    "common": {
        "name": "Zwykły",
        "defense_bonus": 0,
        "stat_base": 1,
        "regular_weight": 60,
        "boss_weight": 10,
    },
    "rare": {
        "name": "Rzadki",
        "defense_bonus": 1,
        "stat_base": 2,
        "regular_weight": 25,
        "boss_weight": 30,
    },
    "epic": {
        "name": "Epicki",
        "defense_bonus": 2,
        "stat_base": 3,
        "regular_weight": 10,
        "boss_weight": 30,
    },
    "legendary": {
        "name": "Legendarny",
        "defense_bonus": 3,
        "stat_base": 4,
        "regular_weight": 4,
        "boss_weight": 20,
    },
    "mythic": {
        "name": "Mityczny",
        "defense_bonus": 4,
        "stat_base": 6,
        "regular_weight": 1,
        "boss_weight": 10,
    },
}

CRYPT_AFFIXES = {
    "strength": "Siła",
    "dexterity": "Zręczność",
    "constitution": "Kondycja",
    "intelligence": "Inteligencja",
    "willpower": "Siła Woli",
    "hp": "HP",
    "mana": "Mana",
}

BOSS_RELICS = {
    10: ("relic_bone_executioner", "Odłamek Kościanego Egzekutora", 2, "strength", 2),
    20: ("relic_blood_curator", "Krwawy Medalion Kuratora", 2, "constitution", 2),
    30: ("relic_tomb_knight", "Pieczęć Rycerza Grobowca", 3, "willpower", 2),
    40: ("relic_ash_witch", "Popielny Amulet Wiedźmy", 3, "intelligence", 3),
    50: ("relic_catacomb_lord", "Znak Pana Katakumb", 4, "hp", 40),
    60: ("relic_spectral_titan", "Widmowy Rdzeń Tytana", 4, "mana", 32),
    70: ("relic_necro_colossus", "Runiczna Kość Kolosa", 5, "constitution", 4),
    80: ("relic_archwraith", "Eteryczny Talizman Arcyupiora", 5, "dexterity", 4),
    90: ("relic_bone_king", "Korona Króla Kości", 6, "strength", 5),
    100: ("relic_hundred_lord", "Pieczęć Władcy Stu Pięter", 7, "willpower", 6),
}

for _floor, (_item_id, _name, _defense, _affix, _amount) in BOSS_RELICS.items():
    ITEMS[_item_id] = {
        "name": _name,
        "type": "armor",
        "slot": "charm",
        "defense": _defense,
        "price": None,
        "desc": (
            f"Unikalny relikt bossa Krypty z piętra {_floor}. "
            f"Obrona +{_defense}. "
            f"Bonus: {CRYPT_AFFIXES.get(_affix, _affix)} +{_amount}."
        ),
        "rarity": "unique",
        "rarity_name": "Unikalny",
        "affix": _affix,
        "affix_amount": _amount,
        "boss_relic_floor": _floor,
    }

ITEMS["bandit_chief_signet"] = {
    "name": "Sygnet Herszta Bandytów",
    "type": "armor",
    "slot": "charm",
    "defense": 3,
    "price": None,
    "desc": (
        "Unikalny sygnet Herszta Bandytów. Obrona +3. "
        "Bonus: Zręczność +3."
    ),
    "rarity": "unique",
    "rarity_name": "Unikalny",
    "affix": "dexterity",
    "affix_amount": 3,
}

WORLD_BOSS_UNIQUES = {
    "goblin_king_crown": {
        "name": "Korona Króla Goblinów",
        "type": "armor",
        "slot": "head",
        "defense": 4,
        "price": None,
        "desc": "Unikalna korona Króla Goblinów. Obrona +4. Zręczność +3.",
        "rarity": "unique",
        "rarity_name": "Unikalny",
        "affix": "dexterity",
        "affix_amount": 3,
    },
    "shadow_alpha_fang": {
        "name": "Kieł Alfy Cienia",
        "type": "armor",
        "slot": "charm",
        "defense": 3,
        "price": None,
        "desc": "Unikalny kieł Alfy Wilków Cienia. Obrona +3. Siła +4.",
        "rarity": "unique",
        "rarity_name": "Unikalny",
        "affix": "strength",
        "affix_amount": 4,
    },
    "ruin_warden_plate": {
        "name": "Płyta Strażnika Ruin",
        "type": "armor",
        "slot": "body",
        "defense": 6,
        "price": None,
        "desc": "Unikalny pancerz Strażnika Ruin. Obrona +6. Siła Woli +4.",
        "rarity": "unique",
        "rarity_name": "Unikalny",
        "affix": "willpower",
        "affix_amount": 4,
    },
    "crystal_lord_core": {
        "name": "Rdzeń Kryształowego Władcy",
        "type": "armor",
        "slot": "charm",
        "defense": 5,
        "price": None,
        "desc": "Unikalny rdzeń Kryształowego Władcy. Obrona +5. Inteligencja +5.",
        "rarity": "unique",
        "rarity_name": "Unikalny",
        "affix": "intelligence",
        "affix_amount": 5,
    },
}
ITEMS.update(WORLD_BOSS_UNIQUES)

def crypt_variant_id(base_item_id, rarity_key, affix_key):
    return f"{base_item_id}__{rarity_key}__{affix_key}"

def crypt_affix_amount(tier, rarity_key, affix_key):
    rarity = CRYPT_RARITIES[rarity_key]
    stat_value = int(rarity["stat_base"]) + (max(1, int(tier)) - 1) // 4
    if affix_key == "hp":
        return stat_value * 10
    if affix_key == "mana":
        return stat_value * 8
    return stat_value

def build_crypt_loot_variants():
    base_ids = [
        item_id
        for item_id, item in list(ITEMS.items())
        if re.fullmatch(r"crypt_t\d+_(?:head|body|hands|legs|feet|charm)", item_id)
    ]

    for base_item_id in base_ids:
        base_item = ITEMS[base_item_id]
        m = re.fullmatch(
            r"crypt_t(\d+)_(head|body|hands|legs|feet|charm)",
            base_item_id,
        )
        if not m:
            continue

        tier = int(m.group(1))
        slot = m.group(2)

        # Stary item bazowy pozostaje kompatybilny i jest zwykłym
        # elementem setu bez affixu.
        base_item["rarity"] = "common"
        base_item["rarity_name"] = "Zwykły"
        base_item["crypt_set_tier"] = tier
        base_item["crypt_base_item"] = base_item_id
        base_item["affix"] = None
        base_item["affix_amount"] = 0

        for rarity_key, rarity in CRYPT_RARITIES.items():
            for affix_key, affix_name in CRYPT_AFFIXES.items():
                amount = crypt_affix_amount(
                    tier, rarity_key, affix_key
                )
                variant_id = crypt_variant_id(
                    base_item_id, rarity_key, affix_key
                )
                defense = (
                    int(base_item.get("defense", 0))
                    + int(rarity["defense_bonus"])
                )
                variant_name = (
                    f"{base_item['name']} "
                    f"[{rarity['name']}, {affix_name} +{amount}]"
                )
                ITEMS[variant_id] = {
                    "name": variant_name,
                    "type": "armor",
                    "slot": slot,
                    "defense": defense,
                    "price": None,
                    "desc": (
                        f"Ekwipunek z Krypty. Tier {tier}. "
                        f"Rzadkość: {rarity['name']}. "
                        f"Obrona +{defense}. "
                        f"Bonus: {affix_name} +{amount}. "
                        f"Zestaw Krypty Tier {tier}."
                    ),
                    "rarity": rarity_key,
                    "rarity_name": rarity["name"],
                    "crypt_set_tier": tier,
                    "crypt_base_item": base_item_id,
                    "affix": affix_key,
                    "affix_amount": amount,
                }

def roll_crypt_rarity(is_boss=False):
    keys = list(CRYPT_RARITIES)
    weight_key = "boss_weight" if is_boss else "regular_weight"
    weights = [
        CRYPT_RARITIES[key][weight_key]
        for key in keys
    ]
    return random.choices(keys, weights=weights, k=1)[0]

def roll_crypt_loot_item(base_item_id, is_boss=False):
    item = ITEMS.get(base_item_id)
    if not item or not item.get("crypt_set_tier"):
        return base_item_id

    rarity_key = roll_crypt_rarity(is_boss=is_boss)
    affix_key = random.choice(tuple(CRYPT_AFFIXES))
    variant_id = crypt_variant_id(
        base_item_id, rarity_key, affix_key
    )
    return variant_id if variant_id in ITEMS else base_item_id

def build_crypt_100_floors():
    ROOMS["crypt_hall"]["exits"]["down"] = crypt_floor_id(1)
    ROOMS["crypt_hall"]["exits"]["east"] = "crypt_depths"
    ROOMS["crypt_depths"]["exits"] = {"west": "crypt_hall"}

    for tier in range(1, 11):
        defs=(
            ("head","Hełm Krypty",1+tier//2),
            ("body","Napierśnik Krypty",2+tier),
            ("hands","Rękawice Krypty",1+tier//3),
            ("legs","Nogawice Krypty",2+tier//2),
            ("feet","Buty Krypty",1+tier//3),
        )
        for slot,label,defense in defs:
            item_id=f"crypt_t{tier}_{slot}"
            ITEMS[item_id]={
                "name":f"{label} Tier {tier}","type":"armor","slot":slot,
                "defense":defense,"price":None,
                "desc":f"Ekwipunek z Krypty. Tier {tier}. Obrona +{defense}.",
            }
        charm=f"crypt_t{tier}_charm"; defense=1+tier//2
        ITEMS[charm]={
            "name":f"Talizman Bossa Krypty Tier {tier}","type":"armor","slot":"charm",
            "defense":defense,"price":None,
            "desc":f"Talizman po bossie Krypty. Tier {tier}. Obrona +{defense}.",
        }

    for floor in range(1, CRYPT_MAX_FLOOR+1):
        room_id=crypt_floor_id(floor); exits={}
        exits["up"]="crypt_hall" if floor==1 else crypt_floor_id(floor-1)
        if floor<CRYPT_MAX_FLOOR: exits["down"]=crypt_floor_id(floor+1)
        if floor in CRYPT_BOSS_FLOORS and floor<100:
            note=" Przy zejściu czeka boss blokujący drogę niżej."
        elif floor==100:
            note=" To ostatnie piętro. Czeka tutaj finałowy boss Krypty."
        else: note=""
        ROOMS[room_id]={
            "zone":"Krypta 1-100","name":f"Krypta, piętro {floor}",
            "desc":f"Piętro {floor} ze 100. Kamienne korytarze stają się coraz bardziej niebezpieczne.{note}",
            "exits":exits,
        }
        tier=min(10,(floor-1)//10+1)
        gear=[f"crypt_t{tier}_{x}" for x in ("head","body","hands","legs","feet")]
        tid=f"crypt_floor_mob_{floor}"
        name=CRYPT_REGULAR_NAMES[(floor-1)%len(CRYPT_REGULAR_NAMES)]
        MOB_TEMPLATES[tid]={
            "name":f"{name}, piętro {floor}",
            "max_hp":70+floor*9,"damage":6+floor//3,
            "damage_type":"magic" if (floor%3==0 or floor%4==0) else "physical",
            "silver":8+floor,"gold":0,"mithril":0,
            "stat_reward":20+floor*2,
            "class_xp_reward":450+floor*60,
            "soul_reward":100+floor*10,
            "drops":{"soul_shard":min(0.30,0.08+floor*0.002)},"quest_target":None,
            "crypt_floor":floor,"corpse_equipment_pool":gear,"corpse_equipment_guaranteed":1,
        }
        MOB_SPAWNS.append((room_id,tid))
        if floor in CRYPT_BOSS_FLOORS:
            bid=f"crypt_boss_{floor}"; pool=gear+[f"crypt_t{tier}_charm"]
            MOB_TEMPLATES[bid]={
                "name":CRYPT_BOSS_NAMES[floor],"max_hp":350+floor*25,
                "damage":16+floor//2,"damage_type":"magic" if floor%20==0 else "physical",
                "silver":300+floor*12,"gold":0,"mithril":0,
                "stat_reward":350+floor*6,
                "class_xp_reward":3000+floor*160,
                "soul_reward":600+floor*20,
                "drops":{
                    "soul_shard":1.0,
                    "soul_elixir":min(0.50,0.15+floor*0.003),
                    BOSS_RELICS[floor][0]: 1.0 if floor == 100 else 0.45,
                },
                "quest_target":None,
                "crypt_floor":floor,
                "crypt_boss":True,
                "boss_mechanic":CRYPT_BOSS_MECHANICS[floor],
                "boss_mechanic_text":CRYPT_BOSS_MECHANIC_TEXT[floor],
                "corpse_equipment_pool":pool,"corpse_equipment_guaranteed":3,
            }
            MOB_SPAWNS.append((room_id,bid))

def configure_base_mob_corpse_equipment():
    MOB_TEMPLATES["training_dummy"]["leave_corpse"] = False
    configs={
        "goblin":["leather_vest","lucky_charm"],
        "goblin_brute":["leather_vest","iron_gauntlets","iron_boots"],
        "bandit":["leather_vest","lucky_charm"],
        "bandit_marauder":["leather_vest","iron_gauntlets","iron_boots","lucky_charm"],
        "skeleton":["iron_helmet","iron_gauntlets","iron_boots"],
        "crypt_wraith":["forge_charm","lucky_charm"],
        "crystal_guardian":["iron_guard","iron_leggings","forge_charm"],
    }
    for tid,pool in configs.items():
        MOB_TEMPLATES[tid]["corpse_equipment_pool"]=pool
        MOB_TEMPLATES[tid]["corpse_equipment_guaranteed"]=1

build_crypt_100_floors()
build_crypt_loot_variants()
configure_base_mob_corpse_equipment()

IAC = 255
DONT = 254
DO = 253
WONT = 252
WILL = 251
SB = 250
SE = 240


def clean_telnet(data: bytes) -> str:
    out = bytearray()
    i = 0
    while i < len(data):
        b = data[i]
        if b != IAC:
            out.append(b)
            i += 1
            continue
        i += 1
        if i >= len(data):
            break
        cmd = data[i]
        i += 1
        if cmd in (DO, DONT, WILL, WONT):
            if i < len(data):
                i += 1
        elif cmd == SB:
            while i < len(data):
                if data[i] == IAC and i + 1 < len(data) and data[i + 1] == SE:
                    i += 2
                    break
                i += 1
        elif cmd == IAC:
            out.append(IAC)
    return out.decode("utf-8", errors="ignore")



def mob_respawn_seconds(template):
    if template.get("respawn_seconds") is not None:
        return max(1, int(template["respawn_seconds"]))
    if template.get("crypt_boss") or template.get("world_boss"):
        return BOSS_RESPAWN_SECONDS
    if template.get("training_dummy"):
        return TRAINING_DUMMY_RESPAWN_SECONDS
    return REGULAR_MOB_RESPAWN_SECONDS

def safe_name(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9_-]{3,20}", name))


def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return salt.hex(), digest.hex()


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    _, candidate = hash_password(password, salt)
    return hmac.compare_digest(candidate, hash_hex)


def find_by_name(mapping, query, name_field="name"):
    q = query.strip().lower()
    if not q:
        return None
    exact = []
    partial = []
    for key, value in mapping.items():
        name = value[name_field].lower()
        if q == key.lower() or q == name:
            exact.append((key, value))
        elif q in name or q in key.lower():
            partial.append((key, value))
    if exact:
        return exact[0]
    if len(partial) == 1:
        return partial[0]
    return None


class Database:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.create_schema()
        self.migrate_schema()

    def create_schema(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS characters (
                account_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                name_nom TEXT NOT NULL DEFAULT '',
                name_gen TEXT NOT NULL DEFAULT '',
                name_dat TEXT NOT NULL DEFAULT '',
                name_acc TEXT NOT NULL DEFAULT '',
                name_ins TEXT NOT NULL DEFAULT '',
                name_loc TEXT NOT NULL DEFAULT '',
                name_voc TEXT NOT NULL DEFAULT '',
                race TEXT NOT NULL,
                class_name TEXT NOT NULL,
                class_type TEXT NOT NULL,
                soul_weapon TEXT NOT NULL,
                weapon_base INTEGER NOT NULL,
                strength INTEGER NOT NULL,
                dexterity INTEGER NOT NULL,
                constitution INTEGER NOT NULL,
                intelligence INTEGER NOT NULL,
                willpower INTEGER NOT NULL,
                stat_progress INTEGER NOT NULL DEFAULT 0,
                soul_level INTEGER NOT NULL DEFAULT 1,
                soul_xp INTEGER NOT NULL DEFAULT 0,
                soul_tier INTEGER NOT NULL DEFAULT 1,
                room_id TEXT NOT NULL DEFAULT 'square',
                silver INTEGER NOT NULL DEFAULT 250,
                gold INTEGER NOT NULL DEFAULT 2,
                mithril INTEGER NOT NULL DEFAULT 0,
                charisma INTEGER NOT NULL DEFAULT 0,
                deaths INTEGER NOT NULL DEFAULT 0,
                crypt_checkpoint INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS inventory (
                account_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, item_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS equipment (
                account_id INTEGER NOT NULL,
                slot TEXT NOT NULL,
                item_id TEXT NOT NULL,
                PRIMARY KEY(account_id, slot),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS quests (
                account_id INTEGER NOT NULL,
                quest_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                progress INTEGER NOT NULL DEFAULT 0,
                completed_at INTEGER NOT NULL DEFAULT 0,
                completion_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, quest_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS professions (
                account_id INTEGER NOT NULL,
                profession TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                xp INTEGER NOT NULL DEFAULT 0,
                actions INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, profession),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tools (
                account_id INTEGER NOT NULL,
                tool_type TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                xp INTEGER NOT NULL DEFAULT 0,
                uses INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, tool_type),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS profession_storage (
                account_id INTEGER NOT NULL,
                container TEXT NOT NULL,
                item_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, container, item_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS class_progress (
                account_id INTEGER NOT NULL,
                class_name TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                xp INTEGER NOT NULL DEFAULT 0,
                active_slot INTEGER,
                PRIMARY KEY(account_id, class_name),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS learned_skills (
                account_id INTEGER NOT NULL,
                skill_id TEXT NOT NULL,
                learned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, skill_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS skill_progress (
                account_id INTEGER NOT NULL,
                skill_id TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                xp INTEGER NOT NULL DEFAULT 0,
                uses INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, skill_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );
            """
        )
        self.conn.commit()

    def migrate_schema(self):
        cols = {r["name"] for r in self.conn.execute("PRAGMA table_info(characters)")}
        additions = {
            "silver": "INTEGER NOT NULL DEFAULT 30",
            "gold": "INTEGER NOT NULL DEFAULT 2",
            "mithril": "INTEGER NOT NULL DEFAULT 0",
            "charisma": "INTEGER NOT NULL DEFAULT 0",
            "deaths": "INTEGER NOT NULL DEFAULT 0",
            "crypt_checkpoint": "INTEGER NOT NULL DEFAULT 0",
            "name_nom": "TEXT NOT NULL DEFAULT ''",
            "name_gen": "TEXT NOT NULL DEFAULT ''",
            "name_dat": "TEXT NOT NULL DEFAULT ''",
            "name_acc": "TEXT NOT NULL DEFAULT ''",
            "name_ins": "TEXT NOT NULL DEFAULT ''",
            "name_loc": "TEXT NOT NULL DEFAULT ''",
            "name_voc": "TEXT NOT NULL DEFAULT ''",
        }
        for name, decl in additions.items():
            if name not in cols:
                self.conn.execute(f"ALTER TABLE characters ADD COLUMN {name} {decl}")

        # Zgodność ze starymi postaciami: jeśli nie mają jeszcze odmiany,
        # dotychczasowe imię staje się bezpieczną formą we wszystkich przypadkach.
        for column in (
            "name_nom", "name_gen", "name_dat", "name_acc",
            "name_ins", "name_loc", "name_voc",
        ):
            self.conn.execute(
                f"UPDATE characters SET {column}=name "
                f"WHERE {column} IS NULL OR TRIM({column})=''"
            )
        quest_cols = {
            r["name"] for r in self.conn.execute("PRAGMA table_info(quests)")
        }
        quest_additions = {
            "completed_at": "INTEGER NOT NULL DEFAULT 0",
            "completion_count": "INTEGER NOT NULL DEFAULT 0",
        }
        for name, decl in quest_additions.items():
            if name not in quest_cols:
                self.conn.execute(
                    f"ALTER TABLE quests ADD COLUMN {name} {decl}"
                )

        self.conn.commit()

    def account_by_name(self, username):
        return self.conn.execute(
            "SELECT * FROM accounts WHERE username=? COLLATE NOCASE", (username,)
        ).fetchone()

    def create_account(self, username, password):
        salt, digest = hash_password(password)
        cur = self.conn.execute(
            "INSERT INTO accounts(username,password_salt,password_hash) VALUES(?,?,?)",
            (username, salt, digest),
        )
        self.conn.commit()
        return cur.lastrowid

    def character_for_account(self, account_id):
        return self.conn.execute(
            "SELECT * FROM characters WHERE account_id=?", (account_id,)
        ).fetchone()

    def character_name_exists(self, name):
        return self.conn.execute(
            "SELECT 1 FROM characters WHERE name=? COLLATE NOCASE", (name,)
        ).fetchone() is not None

    def create_character(self, account_id, name, race, cls, name_cases):
        rname, _, strength, dexterity, constitution, intelligence, willpower = race
        cname, ctype, soul_weapon, weapon_base = cls
        self.conn.execute(
            """
            INSERT INTO characters(
                account_id,name,
                name_nom,name_gen,name_dat,name_acc,name_ins,name_loc,name_voc,
                race,class_name,class_type,soul_weapon,weapon_base,
                strength,dexterity,constitution,intelligence,willpower,
                stat_progress,soul_level,soul_xp,soul_tier,room_id,silver,gold,mithril,deaths
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,1,0,1,'square',30,2,0,0)
            """,
            (
                account_id, name,
                name_cases["nom"], name_cases["gen"], name_cases["dat"],
                name_cases["acc"], name_cases["ins"], name_cases["loc"],
                name_cases["voc"],
                rname, cname, ctype, soul_weapon, weapon_base,
                strength, dexterity, constitution, intelligence, willpower,
            ),
        )
        self.conn.execute(
            "INSERT OR REPLACE INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)",
            (account_id, "healing_potion", 2),
        )
        self.conn.execute(
            "INSERT OR IGNORE INTO class_progress(account_id,class_name,level,xp,active_slot) "
            "VALUES(?,?,1,0,1)",
            (account_id, cname),
        )
        self.conn.execute(
            "UPDATE class_progress SET active_slot=1 "
            "WHERE account_id=? AND class_name=?",
            (account_id, cname),
        )
        self.conn.commit()

    def save_character(self, c):
        self.conn.execute(
            """
            UPDATE characters SET
                strength=?, dexterity=?, constitution=?, intelligence=?, willpower=?,
                stat_progress=?, soul_level=?, soul_xp=?, soul_tier=?, room_id=?,
                silver=?, gold=?, mithril=?, charisma=?, deaths=?
            WHERE account_id=?
            """,
            (
                c.strength, c.dexterity, c.constitution, c.intelligence, c.willpower,
                c.stat_progress, c.soul_level, c.soul_xp, c.soul_tier, c.room_id,
                c.silver, c.gold, c.mithril, c.charisma, c.deaths, c.account_id,
            ),
        )
        self.conn.commit()

    def crypt_checkpoint(self, account_id):
        row = self.conn.execute(
            "SELECT crypt_checkpoint FROM characters WHERE account_id=?",
            (account_id,),
        ).fetchone()
        return int(row["crypt_checkpoint"] or 0) if row else 0

    def unlock_crypt_checkpoint(self, account_id, floor):
        floor = int(floor)
        if floor not in CRYPT_BOSS_FLOORS:
            return self.crypt_checkpoint(account_id)

        current = self.crypt_checkpoint(account_id)
        new_value = max(current, floor)
        if new_value != current:
            self.conn.execute(
                "UPDATE characters SET crypt_checkpoint=? "
                "WHERE account_id=?",
                (new_value, account_id),
            )
            self.conn.commit()
        return new_value

    def sync_legacy_crypt_checkpoint(self, account_id, room_id):
        floor = crypt_floor_number(room_id)
        if floor is None:
            return self.crypt_checkpoint(account_id)

        # Stara postać stojąca na piętrze N musiała wcześniej przejść
        # wszystkie bossy poniżej N. Nie zaliczamy bossa bieżącego piętra.
        safe_floor = ((max(1, floor) - 1) // 10) * 10
        if safe_floor >= 10:
            return self.unlock_crypt_checkpoint(account_id, safe_floor)
        return self.crypt_checkpoint(account_id)

    def crypt_portal(self, account_id):
        return self.crypt_checkpoint(account_id)

    def unlock_crypt_portal(self, account_id, floor):
        return self.unlock_crypt_checkpoint(account_id, floor)

    def inventory(self, account_id):
        return self.conn.execute(
            "SELECT item_id,quantity FROM inventory WHERE account_id=? AND quantity>0 ORDER BY item_id",
            (account_id,),
        ).fetchall()

    def item_qty(self, account_id, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM inventory WHERE account_id=? AND item_id=?",
            (account_id, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def add_item(self, account_id, item_id, qty=1):
        self.conn.execute(
            """
            INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)
            ON CONFLICT(account_id,item_id)
            DO UPDATE SET quantity=quantity+excluded.quantity
            """,
            (account_id, item_id, qty),
        )
        self.conn.commit()

    def remove_item(self, account_id, item_id, qty=1):
        current = self.item_qty(account_id, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM inventory WHERE account_id=? AND item_id=?",
                (account_id, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE inventory SET quantity=? WHERE account_id=? AND item_id=?",
                (new_qty, account_id, item_id),
            )
        self.conn.commit()
        return True

    def ensure_class_progress(self, account_id, class_name):
        self.conn.execute(
            "INSERT OR IGNORE INTO class_progress(account_id,class_name,level,xp,active_slot) "
            "VALUES(?,?,1,0,NULL)",
            (account_id, class_name),
        )
        self.conn.commit()

    def ensure_primary_class(self, account_id, class_name):
        self.ensure_class_progress(account_id, class_name)
        self.conn.execute(
            "UPDATE class_progress SET active_slot=NULL "
            "WHERE account_id=? AND active_slot=1 AND class_name<>?",
            (account_id, class_name),
        )
        self.conn.execute(
            "UPDATE class_progress SET active_slot=1 "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        )
        self.conn.commit()

    def class_progress_row(self, account_id, class_name):
        self.ensure_class_progress(account_id, class_name)
        return self.conn.execute(
            "SELECT class_name,level,xp,active_slot FROM class_progress "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        ).fetchone()

    def active_class_rows(self, account_id, primary_class):
        self.ensure_primary_class(account_id, primary_class)
        return self.conn.execute(
            "SELECT class_name,level,xp,active_slot FROM class_progress "
            "WHERE account_id=? AND active_slot IS NOT NULL "
            "ORDER BY active_slot",
            (account_id,),
        ).fetchall()

    def active_class_names(self, account_id, primary_class):
        return [
            row["class_name"]
            for row in self.active_class_rows(account_id, primary_class)
        ]

    def activate_secondary_class(self, account_id, primary_class, class_name):
        self.ensure_primary_class(account_id, primary_class)
        rows = self.active_class_rows(account_id, primary_class)
        active_names = [row["class_name"] for row in rows]

        if class_name in active_names:
            return False, "Ta klasa jest już aktywna."
        if len(active_names) >= MULTICLASS_MAX_ACTIVE:
            return False, "Masz już maksymalnie 3 aktywne klasy."

        used_slots = {
            int(row["active_slot"])
            for row in rows
            if row["active_slot"] is not None
        }
        slot = next(
            number for number in range(2, MULTICLASS_MAX_ACTIVE + 1)
            if number not in used_slots
        )

        self.ensure_class_progress(account_id, class_name)
        self.conn.execute(
            "UPDATE class_progress SET active_slot=? "
            "WHERE account_id=? AND class_name=?",
            (slot, account_id, class_name),
        )
        self.conn.commit()
        return True, slot

    def deactivate_secondary_class(self, account_id, primary_class, class_name):
        self.ensure_primary_class(account_id, primary_class)
        if class_name == primary_class:
            return False, "Nie można wyłączyć klasy głównej."

        row = self.conn.execute(
            "SELECT active_slot FROM class_progress "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        ).fetchone()
        if not row or row["active_slot"] is None:
            return False, "Ta klasa nie jest aktywna."

        self.conn.execute(
            "UPDATE class_progress SET active_slot=NULL "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        )
        self.conn.commit()
        return True, None

    def add_class_mastery_xp(self, account_id, class_name, amount):
        self.ensure_class_progress(account_id, class_name)
        row = self.class_progress_row(account_id, class_name)
        level = int(row["level"])
        xp = int(row["xp"])
        gain = max(0, int(amount))
        xp += gain
        level_ups = 0

        while level < CLASS_MASTERY_MAX_LEVEL:
            needed = class_mastery_xp_to_next(level)
            if needed <= 0 or xp < needed:
                break
            xp -= needed
            level += 1
            level_ups += 1

        if level >= CLASS_MASTERY_MAX_LEVEL:
            level = CLASS_MASTERY_MAX_LEVEL
            xp = 0

        self.conn.execute(
            "UPDATE class_progress SET level=?,xp=? "
            "WHERE account_id=? AND class_name=?",
            (level, xp, account_id, class_name),
        )
        self.conn.commit()
        return {
            "class_name": class_name,
            "level": level,
            "xp": xp,
            "level_ups": level_ups,
            "next_xp": class_mastery_xp_to_next(level),
            "gain": gain,
        }

    def learned_skill_ids(self, account_id):
        rows = self.conn.execute(
            "SELECT skill_id FROM learned_skills WHERE account_id=? ORDER BY learned_at, skill_id",
            (account_id,),
        ).fetchall()
        return {row["skill_id"] for row in rows}

    def knows_skill(self, account_id, skill_id):
        return self.conn.execute(
            "SELECT 1 FROM learned_skills WHERE account_id=? AND skill_id=?",
            (account_id, skill_id),
        ).fetchone() is not None

    def learn_skill(self, account_id, skill_id):
        before = self.conn.total_changes
        self.conn.execute(
            "INSERT OR IGNORE INTO learned_skills(account_id,skill_id) VALUES(?,?)",
            (account_id, skill_id),
        )
        self.conn.commit()
        learned_now = self.conn.total_changes > before
        self.ensure_skill_progress(account_id, skill_id)
        return learned_now

    def ensure_skill_progress(self, account_id, skill_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO skill_progress(account_id,skill_id,level,xp,uses) VALUES(?,?,1,0,0)",
            (account_id, skill_id),
        )
        self.conn.commit()

    def skill_progress(self, account_id, skill_id):
        self.ensure_skill_progress(account_id, skill_id)
        return self.conn.execute(
            "SELECT level,xp,uses FROM skill_progress WHERE account_id=? AND skill_id=?",
            (account_id, skill_id),
        ).fetchone()

    def add_skill_xp(self, account_id, skill_id, amount):
        self.ensure_skill_progress(account_id, skill_id)
        row = self.skill_progress(account_id, skill_id)
        level = int(row["level"])
        xp = int(row["xp"]) + max(0, int(amount))
        uses = int(row["uses"]) + 1
        level_ups = 0

        while level < SKILL_MAX_LEVEL:
            needed = skill_xp_to_next(level)
            if needed <= 0 or xp < needed:
                break
            xp -= needed
            level += 1
            level_ups += 1

        if level >= SKILL_MAX_LEVEL:
            level = SKILL_MAX_LEVEL
            xp = 0

        self.conn.execute(
            "UPDATE skill_progress SET level=?,xp=?,uses=? WHERE account_id=? AND skill_id=?",
            (level, xp, uses, account_id, skill_id),
        )
        self.conn.commit()
        return {
            "level": level,
            "xp": xp,
            "uses": uses,
            "level_ups": level_ups,
            "next_xp": skill_xp_to_next(level),
        }

    def equipment(self, account_id):
        return self.conn.execute(
            "SELECT slot,item_id FROM equipment WHERE account_id=? ORDER BY slot",
            (account_id,),
        ).fetchall()

    def equipped_item(self, account_id, slot):
        row = self.conn.execute(
            "SELECT item_id FROM equipment WHERE account_id=? AND slot=?",
            (account_id, slot),
        ).fetchone()
        return row["item_id"] if row else None

    def equip(self, account_id, slot, item_id):
        self.conn.execute(
            """
            INSERT INTO equipment(account_id,slot,item_id) VALUES(?,?,?)
            ON CONFLICT(account_id,slot) DO UPDATE SET item_id=excluded.item_id
            """,
            (account_id, slot, item_id),
        )
        self.conn.commit()

    def ensure_profession(self, account_id, profession):
        self.conn.execute(
            "INSERT OR IGNORE INTO professions(account_id,profession,level,xp,actions) VALUES(?,?,1,0,0)",
            (account_id, profession),
        )
        self.conn.commit()

    def profession(self, account_id, profession):
        self.ensure_profession(account_id, profession)
        return self.conn.execute(
            "SELECT * FROM professions WHERE account_id=? AND profession=?",
            (account_id, profession),
        ).fetchone()

    def save_profession(self, account_id, profession, level, xp, actions):
        self.conn.execute(
            "UPDATE professions SET level=?,xp=?,actions=? WHERE account_id=? AND profession=?",
            (level, xp, actions, account_id, profession),
        )
        self.conn.commit()

    def ensure_tool(self, account_id, tool_type):
        self.conn.execute(
            "INSERT OR IGNORE INTO tools(account_id,tool_type,level,xp,uses) VALUES(?,?,1,0,0)",
            (account_id, tool_type),
        )
        self.conn.commit()

    def tool(self, account_id, tool_type):
        self.ensure_tool(account_id, tool_type)
        return self.conn.execute(
            "SELECT * FROM tools WHERE account_id=? AND tool_type=?",
            (account_id, tool_type),
        ).fetchone()

    def save_tool(self, account_id, tool_type, level, xp, uses):
        self.conn.execute(
            "UPDATE tools SET level=?,xp=?,uses=? WHERE account_id=? AND tool_type=?",
            (level, xp, uses, account_id, tool_type),
        )
        self.conn.commit()

    def storage_rows(self, account_id, container):
        return self.conn.execute(
            "SELECT item_id,quantity FROM profession_storage "
            "WHERE account_id=? AND container=? AND quantity>0 ORDER BY item_id",
            (account_id, container),
        ).fetchall()

    def storage_qty(self, account_id, container, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM profession_storage "
            "WHERE account_id=? AND container=? AND item_id=?",
            (account_id, container, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def add_storage_item(self, account_id, container, item_id, qty=1):
        self.conn.execute(
            """
            INSERT INTO profession_storage(account_id,container,item_id,quantity)
            VALUES(?,?,?,?)
            ON CONFLICT(account_id,container,item_id)
            DO UPDATE SET quantity=quantity+excluded.quantity
            """,
            (account_id, container, item_id, qty),
        )
        self.conn.commit()

    def remove_storage_item(self, account_id, container, item_id, qty=1):
        current = self.storage_qty(account_id, container, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM profession_storage "
                "WHERE account_id=? AND container=? AND item_id=?",
                (account_id, container, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE profession_storage SET quantity=? "
                "WHERE account_id=? AND container=? AND item_id=?",
                (new_qty, account_id, container, item_id),
            )
        self.conn.commit()
        return True

    def total_items_across_storage_and_inventory(self, account_id, item_ids, container=None):
        total = 0
        for item_id in item_ids:
            total += self.item_qty(account_id, item_id)
            if container:
                total += self.storage_qty(account_id, container, item_id)
        return total

    def consume_items_across_storage_and_inventory(self, account_id, item_ids, needed, container=None):
        remaining = needed

        if container:
            for item_id in sorted(item_ids):
                if remaining <= 0:
                    break
                qty = self.storage_qty(account_id, container, item_id)
                take = min(qty, remaining)
                if take > 0:
                    self.remove_storage_item(account_id, container, item_id, take)
                    remaining -= take

        for item_id in sorted(item_ids):
            if remaining <= 0:
                break
            qty = self.item_qty(account_id, item_id)
            take = min(qty, remaining)
            if take > 0:
                self.remove_item(account_id, item_id, take)
                remaining -= take

        return remaining == 0

    def quest(self, account_id, quest_id):
        return self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        ).fetchone()

    def start_quest(self, account_id, quest_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO quests("
            "account_id,quest_id,status,progress,completed_at,completion_count"
            ") VALUES(?,?, 'active',0,0,0)",
            (account_id, quest_id),
        )
        self.conn.commit()

    def restart_quest(self, account_id, quest_id):
        self.conn.execute(
            "UPDATE quests SET status='active',progress=0 "
            "WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.commit()

    def repeat_quest_seconds_remaining(self, account_id, quest_id, cooldown):
        row = self.quest(account_id, quest_id)
        if not row or row["status"] != "completed":
            return 0
        completed_at = int(row["completed_at"] or 0)
        if completed_at <= 0:
            return 0
        elapsed = max(0, int(time.time()) - completed_at)
        return max(0, int(cooldown) - elapsed)

    def quest_rows(self, account_id):
        return self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? ORDER BY status,quest_id",
            (account_id,),
        ).fetchall()

    def increment_quest(self, account_id, target):
        rows = self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()
        changed = []
        for row in rows:
            q = QUESTS.get(row["quest_id"])
            if not q or q["kind"] != "kill" or q["target"] != target:
                continue
            new_progress = min(q["needed"], row["progress"] + 1)
            self.conn.execute(
                "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
                (new_progress, account_id, row["quest_id"]),
            )
            changed.append((row["quest_id"], new_progress))
        self.conn.commit()
        return changed

    def complete_quest(self, account_id, quest_id):
        self.conn.execute(
            "UPDATE quests SET status='completed',completed_at=?,"
            "completion_count=completion_count+1 "
            "WHERE account_id=? AND quest_id=?",
            (int(time.time()), account_id, quest_id),
        )
        self.conn.commit()


@dataclass
class Character:
    account_id: int
    name: str
    name_nom: str
    name_gen: str
    name_dat: str
    name_acc: str
    name_ins: str
    name_loc: str
    name_voc: str
    race: str
    class_name: str
    class_type: str
    soul_weapon: str
    weapon_base: int
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    willpower: int
    stat_progress: int
    soul_level: int
    soul_xp: int
    soul_tier: int
    room_id: str
    silver: int
    gold: int
    mithril: int
    charisma: int
    deaths: int

    @classmethod
    def from_row(cls, row):
        return cls(
            account_id=row["account_id"], name=row["name"],
            name_nom=row["name_nom"], name_gen=row["name_gen"],
            name_dat=row["name_dat"], name_acc=row["name_acc"],
            name_ins=row["name_ins"], name_loc=row["name_loc"],
            name_voc=row["name_voc"], race=row["race"],
            class_name=row["class_name"], class_type=row["class_type"],
            soul_weapon=row["soul_weapon"], weapon_base=row["weapon_base"],
            strength=row["strength"], dexterity=row["dexterity"],
            constitution=row["constitution"], intelligence=row["intelligence"],
            willpower=row["willpower"], stat_progress=row["stat_progress"],
            soul_level=row["soul_level"], soul_xp=row["soul_xp"],
            soul_tier=row["soul_tier"], room_id=row["room_id"],
            silver=row["silver"], gold=row["gold"], mithril=row["mithril"],
            charisma=row["charisma"], deaths=row["deaths"],
        )

    def name_case(self, case):
        mapping = {
            "nom": self.name_nom, "mianownik": self.name_nom,
            "gen": self.name_gen, "dopelniacz": self.name_gen, "dopełniacz": self.name_gen,
            "dat": self.name_dat, "celownik": self.name_dat,
            "acc": self.name_acc, "biernik": self.name_acc,
            "ins": self.name_ins, "narzednik": self.name_ins, "narzędnik": self.name_ins,
            "loc": self.name_loc, "miejscownik": self.name_loc,
            "voc": self.name_voc, "wolacz": self.name_voc, "wołacz": self.name_voc,
        }
        return mapping.get(str(case).strip().lower(), self.name_nom or self.name)

    def max_hp(self):
        # Kondycja bezpośrednio zwiększa maksymalne HP.
        base = 40 + self.constitution * 5
        return max(1, int(round(base * self.racial_max_hp_multiplier())))

    def physical_power(self):
        # Siła odpowiada za obrażenia fizyczne.
        return self.strength

    def speed(self):
        # Zręczność odpowiada za szybkość.
        return 10 + self.dexterity * 2

    def dodge_chance(self):
        # Szybkość przekłada się na szansę uniknięcia kontrataku.
        # Bonusy klasy i rasy mogą się łączyć.
        base = max(0.0, (self.speed() - 20) / 300.0)
        return min(
            0.45,
            base + self.class_dodge_bonus() + self.racial_dodge_bonus()
        )

    def active_class_names(self):
        names = list(getattr(self, "_active_classes", []) or [])
        if self.class_name not in names:
            names.insert(0, self.class_name)
        result = []
        for name in names:
            if name not in result:
                result.append(name)
        return result[:MULTICLASS_MAX_ACTIVE]

    def has_active_class(self, class_name):
        return class_name in self.active_class_names()

    def max_mana(self):
        if not any(
            class_type_for_name(name) == "magic"
            for name in self.active_class_names()
        ):
            return 0
        # Multiclass fizyczny może korzystać z Many, jeśli ma aktywną klasę magiczną.
        base = 20 + self.intelligence * 5
        return max(0, int(round(base * self.racial_max_mana_multiplier())))

    def spell_power(self):
        return self.intelligence

    def class_passive_text_for(self, class_name):
        return {
            "Wojownik": "+10 procent obrażeń fizycznych",
            "Berserker": "+12 procent obrażeń fizycznych",
            "Łotrzyk": "+5 punktów procentowych do uniku",
            "Łowca": "+8 procent obrażeń fizycznych",
            "Mnich": "+8 procent mocy klasowego leczenia",
            "Strażnik": "10 procent redukcji wszystkich otrzymywanych obrażeń",
            "Mag": "+10 procent obrażeń magicznych",
            "Nekromanta": "+15 procent leczenia z wysysania życia",
            "Kapłan": "+10 procent mocy klasowego leczenia",
            "Czarownik": "+12 procent obrażeń magicznych",
            "Druid": "+10 procent mocy klasowego leczenia",
            "Psionik": "+10 procent obrony magicznej",
        }.get(class_name, "brak")

    def class_passive_text(self):
        return self.class_passive_text_for(self.class_name)

    def class_physical_damage_multiplier(self):
        multiplier = 1.0
        bonuses = {"Wojownik": 1.10, "Berserker": 1.12, "Łowca": 1.08}
        for name in self.active_class_names():
            multiplier *= bonuses.get(name, 1.0)

        if self.class_name in ("Wojownik", "Berserker", "Łowca"):
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        return multiplier

    def class_magic_damage_multiplier(self):
        multiplier = 1.0
        bonuses = {"Mag": 1.10, "Czarownik": 1.12}
        for name in self.active_class_names():
            multiplier *= bonuses.get(name, 1.0)

        if self.class_name in ("Mag", "Czarownik"):
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        return multiplier

    def class_healing_multiplier(self):
        multiplier = 1.0
        bonuses = {"Mnich": 1.08, "Kapłan": 1.10, "Druid": 1.10}
        for name in self.active_class_names():
            multiplier *= bonuses.get(name, 1.0)

        if self.class_name in ("Mnich", "Kapłan", "Druid"):
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        return multiplier

    def class_drain_healing_multiplier(self):
        multiplier = 1.15 if self.has_active_class("Nekromanta") else 1.0
        if self.class_name == "Nekromanta":
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        return multiplier

    def class_dodge_bonus(self):
        bonus = 0.05 if self.has_active_class("Łotrzyk") else 0.0
        if self.class_name == "Łotrzyk":
            bonus += self.soul_weapon_dodge_bonus()
        return bonus

    def class_damage_reduction_percent(self):
        percent = 10 if self.has_active_class("Strażnik") else 0
        if self.class_name == "Strażnik":
            percent += self.soul_weapon_guardian_reduction_percent()
        return percent

    def class_magic_defense_multiplier(self):
        multiplier = 1.10 if self.has_active_class("Psionik") else 1.0
        if self.class_name == "Psionik":
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        return multiplier

    def apply_class_damage_reduction(self, damage):
        damage = max(1, int(damage))
        percent = self.class_damage_reduction_percent()
        if percent <= 0:
            return damage, 0
        reduced = max(1, int(round(damage * (1.0 - percent / 100.0))))
        return reduced, max(0, damage - reduced)

    def racial_passive_text(self):
        return {
            "Człowiek": "+10 procent Postępu Rozwoju statystyk",
            "Ogr": "+12 procent obrażeń fizycznych",
            "Elf": "+5 punktów procentowych do uniku",
            "Krasnolud": "10 procent redukcji wszystkich otrzymywanych obrażeń",
            "Ork": "+10 procent maksymalnego HP",
            "Niziołek": "+3 punkty procentowe szansy na bonusowy połów, rudę lub drewno",
            "Mroczny Elf": "+10 procent obrażeń magicznych",
            "Gnom": "+15 procent maksymalnej Many",
            "Smoczy": "+8 procent wszystkich zadawanych obrażeń",
            "Troll": "12 procent redukcji otrzymywanych obrażeń fizycznych",
            "Diablę": "+10 procent zdobywanego Soul XP",
            "Aasimar": "+12 procent obrony magicznej",
            "Driada": "+15 procent mocy klasowego leczenia",
        }.get(self.race, "brak")

    def racial_stat_progress_multiplier(self):
        return 1.10 if self.race == "Człowiek" else 1.0

    def racial_physical_damage_multiplier(self):
        return 1.12 if self.race == "Ogr" else 1.0

    def racial_dodge_bonus(self):
        return 0.05 if self.race == "Elf" else 0.0

    def racial_max_hp_multiplier(self):
        return 1.10 if self.race == "Ork" else 1.0

    def racial_profession_bonus_chance(self):
        return 0.03 if self.race == "Niziołek" else 0.0

    def racial_magic_damage_multiplier(self):
        return 1.10 if self.race == "Mroczny Elf" else 1.0

    def racial_max_mana_multiplier(self):
        return 1.15 if self.race == "Gnom" else 1.0

    def racial_all_damage_multiplier(self):
        return 1.08 if self.race == "Smoczy" else 1.0

    def racial_physical_damage_reduction_percent(self):
        return 12 if self.race == "Troll" else 0

    def racial_soul_xp_multiplier(self):
        return 1.10 if self.race == "Diablę" else 1.0

    def racial_magic_defense_multiplier(self):
        return 1.12 if self.race == "Aasimar" else 1.0

    def racial_healing_multiplier(self):
        # Driada jest rasą specjalizującą się w leczeniu.
        if self.race == "Driada":
            return 1.15
        return 1.0

    def racial_healing_bonus_percent(self):
        return int(round((self.racial_healing_multiplier() - 1.0) * 100))

    def racial_damage_reduction_percent(self):
        # Krasnolud ma stałą rasową odporność na każde otrzymane trafienie.
        if self.race == "Krasnolud":
            return 10
        return 0

    def apply_racial_damage_reduction(self, damage):
        damage = max(1, int(damage))
        percent = self.racial_damage_reduction_percent()
        if percent <= 0:
            return damage, 0
        reduced = max(1, int(round(damage * (1.0 - percent / 100.0))))
        prevented = max(0, damage - reduced)
        return reduced, prevented

    def magic_defense(self):
        # Siła Woli odpowiada wyłącznie za obronę magiczną.
        base = max(0, self.willpower // 2)
        return max(
            0,
            int(
                round(
                    base
                    * self.class_magic_defense_multiplier()
                    * self.racial_magic_defense_multiplier()
                )
            )
        )

    def shop_discount_percent(self):
        return min(
            CHARISMA_MAX_DISCOUNT,
            max(0, self.charisma // CHARISMA_DISCOUNT_STEP),
        )

    def party_capacity(self):
        # Startowo 8 osób łącznie z liderem.
        # Co 25 Charyzmy lider otrzymuje jedno kolejne miejsce.
        return PARTY_BASE_CAPACITY + max(0, self.charisma // PARTY_CHARISMA_STEP)

    def charisma_to_next_discount(self):
        if self.shop_discount_percent() >= CHARISMA_MAX_DISCOUNT:
            return 0
        next_value = (self.shop_discount_percent() + 1) * CHARISMA_DISCOUNT_STEP
        return max(0, next_value - self.charisma)

    def charisma_to_next_party_slot(self):
        next_value = (
            (max(0, self.charisma) // PARTY_CHARISMA_STEP) + 1
        ) * PARTY_CHARISMA_STEP
        return max(0, next_value - self.charisma)

    def soul_xp_to_next(self):
        if self.soul_level >= SOUL_MAX_LEVEL:
            return 0
        # Soul Level ma rozwijać się wolniej niż wcześniej.
        return 180 + (self.soul_level - 1) * 60

    def soul_weapon_bonus_percent(self):
        # Broń Duszy klasy głównej wzmacnia jej specjalizację.
        # Tier 1 / 2 / 3: 5 / 10 / 15 procent.
        return {1: 5, 2: 10, 3: 15}.get(self.soul_tier, 5)

    def soul_weapon_dodge_bonus(self):
        # Unik jest liczony w punktach procentowych i ma globalny cap 45%.
        return {1: 0.02, 2: 0.04, 3: 0.06}.get(self.soul_tier, 0.02)

    def soul_weapon_guardian_reduction_percent(self):
        # Redukcja Strażnika jest celowo mniejsza niż standardowe 5/10/15.
        return {1: 3, 2: 6, 3: 9}.get(self.soul_tier, 3)

    def soul_weapon_class_bonus_text(self):
        percent = self.soul_weapon_bonus_percent()
        if self.class_name in ("Wojownik", "Berserker", "Łowca"):
            return (
                f"+{percent} procent obrażeń fizycznych z Broni Duszy "
                f"klasy {self.class_name}"
            )
        if self.class_name == "Łotrzyk":
            pp = int(round(self.soul_weapon_dodge_bonus() * 100))
            return f"+{pp} punkty procentowe uniku z Broni Duszy Łotrzyka"
        if self.class_name in ("Mag", "Czarownik"):
            return (
                f"+{percent} procent obrażeń magicznych z Broni Duszy "
                f"klasy {self.class_name}"
            )
        if self.class_name in ("Mnich", "Kapłan", "Druid"):
            return (
                f"+{percent} procent mocy leczenia z Broni Duszy "
                f"klasy {self.class_name}"
            )
        if self.class_name == "Nekromanta":
            return (
                f"+{percent} procent leczenia z wysysania życia "
                "z Broni Duszy Nekromanty"
            )
        if self.class_name == "Strażnik":
            return (
                f"+{self.soul_weapon_guardian_reduction_percent()} procent "
                "redukcji wszystkich obrażeń z Broni Duszy Strażnika"
            )
        if self.class_name == "Psionik":
            return (
                f"+{percent} procent obrony magicznej "
                "z Broni Duszy Psionika"
            )
        return f"+{percent} procent do specjalizacji klasy głównej"

    def soul_power(self):
        return self.weapon_base + self.soul_level - 1 + {1: 0, 2: 12, 3: 30}[self.soul_tier]

    def can_unlock(self):
        if self.soul_tier == 1 and self.soul_level >= TIER2_LEVEL:
            return 2
        if self.soul_tier == 2 and self.soul_level >= TIER3_LEVEL:
            return 3
        return None

    def add_stat_progress(self, amount):
        base_amount = max(0, int(amount))
        amount = max(
            0,
            int(round(base_amount * self.racial_stat_progress_multiplier()))
        )
        messages = [f"Postęp rozwoju statystyk +{amount}."]
        if amount > base_amount:
            messages.append(
                f"Bonus rasy {self.race}: +{amount - base_amount} Postępu Rozwoju."
            )
        self.stat_progress += amount
        while self.stat_progress >= STAT_GROWTH_THRESHOLD:
            self.stat_progress -= STAT_GROWTH_THRESHOLD

            # Każda klasa rozwija wszystkie pięć statystyk.
            self.strength += 1
            self.dexterity += 1
            self.constitution += 1
            self.intelligence += 1
            self.willpower += 1

            messages.append(
                "Statystyki wzrosły: Siła +1, Zręczność +1, Kondycja +1, "
                "Inteligencja +1, Siła Woli +1."
            )
        return messages

    def add_soul_xp(self, amount):
        if self.soul_level >= SOUL_MAX_LEVEL:
            return [f"Broń Duszy ma już Soul Level {SOUL_MAX_LEVEL}."]
        base_amount = max(0, int(amount))
        amount = max(
            0,
            int(round(base_amount * self.racial_soul_xp_multiplier()))
        )
        messages = [f"Broń Duszy otrzymuje {amount} Soul XP."]
        if amount > base_amount:
            messages.append(
                f"Bonus rasy {self.race}: +{amount - base_amount} Soul XP."
            )
        self.soul_xp += amount
        while self.soul_level < SOUL_MAX_LEVEL:
            needed = self.soul_xp_to_next()
            if self.soul_xp < needed:
                break
            self.soul_xp -= needed
            self.soul_level += 1
            messages.append(f"Broń Duszy osiąga Soul Level {self.soul_level}.")
            if self.soul_level == TIER2_LEVEL and self.soul_tier == 1:
                messages.append("Osiągnięto Soul Level 25. Idź do Kapłana Elora w Świątyni Odrodzenia po Próbę Broni Duszy na Tier 2.")
            if self.soul_level == TIER3_LEVEL and self.soul_tier == 2:
                messages.append("Osiągnięto Soul Level 60. Idź do Kapłana Elora w Świątyni Odrodzenia po Próbę Broni Duszy na Tier 3.")
        if self.soul_level >= SOUL_MAX_LEVEL:
            self.soul_level = SOUL_MAX_LEVEL
            self.soul_xp = 0
            messages.append(f"Osiągnięto maksymalny Soul Level {SOUL_MAX_LEVEL}.")
        return messages


@dataclass
class CorpseState:
    key: str
    room_id: str
    mob_name: str
    items: list
    created_at: float
    expires_at: float


@dataclass
class MobState:
    key: str
    room_id: str
    template_id: str
    hp: int
    alive: bool = True
    respawn_at: float = 0.0
    engaged_by: Optional[str] = None
    combat_turn: int = 0
    player_hits: int = 0


class World:
    def __init__(self):
        self.mobs = {}
        self.corpses = {}
        self.corpse_counter = 0
        counts = {}
        for room_id, template_id in MOB_SPAWNS:
            counts[(room_id, template_id)] = counts.get((room_id, template_id), 0) + 1
            n = counts[(room_id, template_id)]
            key = f"{room_id}:{template_id}:{n}"
            self.mobs[key] = MobState(
                key=key, room_id=room_id, template_id=template_id,
                hp=MOB_TEMPLATES[template_id]["max_hp"],
            )

    def refresh(self):
        now = time.time()
        for corpse_key, corpse in list(self.corpses.items()):
            if corpse.expires_at <= now:
                self.corpses.pop(corpse_key, None)
        for mob in self.mobs.values():
            if not mob.alive and mob.respawn_at <= now:
                mob.alive = True
                mob.hp = MOB_TEMPLATES[mob.template_id]["max_hp"]
                mob.engaged_by = None
                mob.combat_turn = 0
                mob.player_hits = 0

    def live_crypt_boss(self, room_id):
        self.refresh()
        for mob in self.mobs.values():
            if mob.alive and mob.room_id == room_id and MOB_TEMPLATES[mob.template_id].get("crypt_boss"):
                return mob
        return None

    def crypt_descent_blocked(self, room_id, direction="down"):
        if direction != "down": return False
        floor=crypt_floor_number(room_id)
        if floor is None or floor not in CRYPT_BOSS_FLOORS: return False
        return self.live_crypt_boss(room_id) is not None

    def create_corpse(self, mob):
        template=MOB_TEMPLATES[mob.template_id]
        if template.get("leave_corpse", True) is False: return None
        pool=list(template.get("corpse_equipment_pool",()))
        guaranteed=min(len(pool),max(0,int(template.get("corpse_equipment_guaranteed",0))))
        items=random.sample(pool,guaranteed) if guaranteed else []
        if items:
            is_crypt_boss = bool(template.get("crypt_boss"))
            items = [
                roll_crypt_loot_item(
                    item_id, is_boss=is_crypt_boss
                )
                for item_id in items
            ]
        self.corpse_counter += 1; now=time.time()
        corpse=CorpseState(
            key=f"corpse:{self.corpse_counter}", room_id=mob.room_id,
            mob_name=template["name"], items=items, created_at=now,
            expires_at=now+CORPSE_LIFETIME_SECONDS,
        )
        self.corpses[corpse.key]=corpse
        return corpse

    def room_corpses(self, room_id):
        self.refresh()
        return [c for c in self.corpses.values() if c.room_id==room_id]

    def find_corpse(self, room_id, query=""):
        corpses=self.room_corpses(room_id); q=str(query).strip().lower()
        for prefix in ("ciało ","cialo ","zwłoki ","zwloki ","body ","corpse "):
            if q.startswith(prefix): q=q[len(prefix):].strip(); break
        if not q: return corpses[0] if len(corpses)==1 else None
        exact=[c for c in corpses if q==c.mob_name.lower()]
        if exact: return exact[0]
        partial=[c for c in corpses if q in c.mob_name.lower()]
        return partial[0] if partial else None

    def room_mobs(self, room_id):
        self.refresh()
        return [m for m in self.mobs.values() if m.room_id == room_id and m.alive]

    def find_mob(self, room_id, query):
        mobs = self.room_mobs(room_id)
        q = query.strip().lower()
        if not q and len(mobs) == 1:
            return mobs[0]
        exact = []
        partial = []
        for mob in mobs:
            name = MOB_TEMPLATES[mob.template_id]["name"].lower()
            if q == name or q == mob.template_id:
                exact.append(mob)
            elif q and (q in name or q in mob.template_id):
                partial.append(mob)
        if exact:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None


class Session:
    def __init__(self, server, reader, writer):
        self.server = server
        self.reader = reader
        self.writer = writer
        self.account_id = None
        self.character = None
        self.closed = False
        self.current_hp = 0
        self.current_mana = 0
        self.combat_mob_key = None
        self.last_profession_action = 0.0
        self.auto_fishing = False
        self.auto_fishing_task = None
        self.auto_mining = False
        self.auto_mining_task = None
        self.auto_woodcutting = False
        self.auto_woodcutting_task = None
        self.auto_herbalism = False
        self.auto_herbalism_task = None
        self.guiding = False
        self.skill_cooldowns = {}
        self.skill_guard = 0
        self.skill_evade = False
        self.skill_damage_boost = 1.0
        self.resting = False
        self.rest_task = None

    def crypt_portal(self):
        return self.server.db.crypt_portal(self.account_id)

    def crypt_portal_floors(self):
        highest = self.crypt_portal()
        return [
            floor for floor in CRYPT_BOSS_FLOORS
            if floor <= highest
        ]

    def crypt_descent_blocked_for_player(self, room_id, direction="down"):
        # Żywy boss zawsze blokuje zejście.
        # Portal tylko skraca podróż i nie zmienia tej zasady.
        return self.server.world.crypt_descent_blocked(
            room_id, direction
        )

    async def grant_soul_xp(self, amount):
        old_level = self.character.soul_level

        messages = self.character.add_soul_xp(amount)
        for message in messages:
            await self.send(message)

        if self.character.soul_level > old_level:
            self.current_hp = self.max_hp()
            await self.send(
                f"Awans Soul Level odnawia całe HP. "
                f"HP: {self.current_hp} z {self.max_hp()}."
            )

        return self.character.soul_level > old_level

    async def show_portal_status(self):
        highest = self.crypt_portal()
        unlocked = self.crypt_portal_floors()
        if not unlocked:
            await self.send(
                "Portale Krypty: brak. "
                "Pokonaj bossa piętra 10, aby odblokować pierwszy portal."
            )
            return

        await self.send(
            f"Najwyższy odblokowany Portal Krypty: piętro {highest}."
        )
        await self.send(
            "Odblokowane Portale Krypty: "
            + ", ".join(str(floor) for floor in unlocked)
            + "."
        )
        await self.send(
            "Użycie: portal <10/20/.../100>. "
            "Portal można uruchomić w Sali Krypty albo w Przedsionku Krypty."
        )

    async def use_crypt_portal(self, raw):
        if self.combat_mob_key:
            await self.send(
                "Nie możesz użyć Portalu Krypty podczas walki."
            )
            return

        value = self.normalize_room_query(raw)
        if not value or value in ("status", "lista", "list"):
            await self.show_portal_status()
            return

        match = re.search(r"(\d+)", value)
        if not match:
            await self.send(
                "Użycie: portal 10, portal 20, ... portal 100."
            )
            return

        floor = int(match.group(1))
        if floor not in CRYPT_BOSS_FLOORS:
            await self.send(
                "Portale są tylko na piętrach 10, 20, 30, 40, 50, "
                "60, 70, 80, 90 i 100."
            )
            return

        highest = self.crypt_portal()
        if floor > highest:
            await self.send(
                f"Portal piętra {floor} jest jeszcze zablokowany. "
                f"Najwyższy odblokowany portal: "
                f"{highest if highest else 'brak'}."
            )
            return

        if self.character.room_id not in ("crypt_hall", "crypt_entrance"):
            await self.send(
                "Portal Krypty można uruchomić tylko w Sali Krypty "
                "albo w Przedsionku Krypty. Użyj prowadz Sala Krypty."
            )
            return

        if self.resting or self.rest_task:
            await self.stop_rest(announce=False)
        if self.auto_fishing or self.auto_fishing_task:
            await self.stop_auto_fishing(announce=False)
        if self.auto_mining or self.auto_mining_task:
            await self.stop_auto_mining(announce=False)
        if self.auto_woodcutting or self.auto_woodcutting_task:
            await self.stop_auto_woodcutting(announce=False)
        if self.auto_herbalism or self.auto_herbalism_task:
            await self.stop_auto_herbalism(announce=False)

        target = crypt_floor_id(floor)
        old = self.character.room_id

        await self.server.broadcast_room(
            old,
            f"{self.character.name} wchodzi w Portal Krypty.",
            exclude=self,
        )
        self.character.room_id = target
        self.server.db.save_character(self.character)
        await self.server.broadcast_room(
            target,
            f"{self.character.name} wychodzi z Portalu Krypty.",
            exclude=self,
        )
        await self.send(
            f"Portal Krypty przenosi cię na piętro {floor}."
        )
        await self.look()


    def rest_status_text(self):
        if not self.character:
            return "Brak postaci."
        max_hp = self.max_hp()
        max_mana = self.max_mana()
        if max_mana > 0:
            return (
                f"HP {self.current_hp} z {max_hp}. "
                f"Mana {self.current_mana} z {max_mana}. "
                f"Odpoczynek: {'aktywny' if self.resting else 'wyłączony'}."
            )
        return (
            f"HP {self.current_hp} z {max_hp}. "
            f"Odpoczynek: {'aktywny' if self.resting else 'wyłączony'}."
        )

    def rest_needs_regeneration(self):
        if not self.character:
            return False
        if self.current_hp < self.max_hp():
            return True
        max_mana = self.max_mana()
        return max_mana > 0 and self.current_mana < max_mana

    async def rest_tick(self):
        if not self.character:
            return False

        max_hp = self.max_hp()
        max_mana = self.max_mana()

        hp_gain = max(
            1,
            (max_hp * REST_REGEN_PERCENT + 99) // 100,
        )
        hp_before = self.current_hp
        self.current_hp = min(max_hp, self.current_hp + hp_gain)

        mana_before = self.current_mana
        if max_mana > 0:
            mana_gain = max(
                1,
                (max_mana * REST_REGEN_PERCENT + 99) // 100,
            )
            self.current_mana = min(
                max_mana, self.current_mana + mana_gain
            )
        else:
            self.current_mana = 0

        if (
            self.current_hp != hp_before
            or self.current_mana != mana_before
        ):
            if max_mana > 0:
                await self.send(
                    f"Regeneracja: HP {self.current_hp} z {max_hp}. "
                    f"Mana {self.current_mana} z {max_mana}."
                )
            else:
                await self.send(
                    f"Regeneracja: HP {self.current_hp} z {max_hp}."
                )

        return self.rest_needs_regeneration()

    async def rest_loop(self):
        try:
            while self.resting and not self.closed:
                await asyncio.sleep(REST_TICK_SECONDS)
                if (
                    not self.resting
                    or self.closed
                    or self.combat_mob_key
                ):
                    break

                needs_more = await self.rest_tick()
                if not needs_more:
                    self.resting = False
                    await self.send(
                        "Odpoczynek zakończony. HP i Mana są pełne."
                    )
                    break
        except asyncio.CancelledError:
            pass
        finally:
            self.resting = False
            if self.rest_task is asyncio.current_task():
                self.rest_task = None

    async def stop_rest(self, announce=True, reason=None):
        was_resting = self.resting or (
            self.rest_task is not None
            and not self.rest_task.done()
        )
        self.resting = False
        task = self.rest_task
        self.rest_task = None

        if (
            task
            and task is not asyncio.current_task()
            and not task.done()
        ):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        if announce and was_resting:
            if reason:
                await self.send(
                    f"Odpoczynek przerwany: {reason}."
                )
            else:
                await self.send("Odpoczynek przerwany.")
        return was_resting

    async def start_rest(self):
        if self.combat_mob_key:
            await self.send(
                "Nie możesz odpoczywać podczas walki. "
                "Najpierw pokonaj przeciwnika albo użyj flee."
            )
            return

        if self.resting:
            await self.send(self.rest_status_text())
            return

        if not self.rest_needs_regeneration():
            await self.send(
                "Nie musisz odpoczywać. HP i Mana są już pełne."
            )
            return

        if self.auto_fishing or self.auto_fishing_task:
            await self.stop_auto_fishing(announce=False)
        if self.auto_mining or self.auto_mining_task:
            await self.stop_auto_mining(announce=False)
        if self.auto_woodcutting or self.auto_woodcutting_task:
            await self.stop_auto_woodcutting(announce=False)
        if self.auto_herbalism or self.auto_herbalism_task:
            await self.stop_auto_herbalism(announce=False)

        self.resting = True
        self.rest_task = asyncio.create_task(self.rest_loop())
        await self.send(
            "Rozpoczynasz odpoczynek. Regeneracja działa co 5 sekund."
        )
        await self.send(self.rest_status_text())

    async def handle_rest(self, raw):
        action = raw.strip().lower()

        if action in ("status", "stan"):
            await self.send(self.rest_status_text())
            return

        if action in ("off", "stop", "koniec", "przerwij"):
            if not await self.stop_rest(announce=True):
                await self.send("Nie odpoczywasz.")
            return

        if action in ("", "on", "start"):
            await self.start_rest()
            return

        await self.send(
            "Użycie: odpoczywaj, odpoczywaj status, "
            "odpoczywaj stop."
        )

    def refresh_active_classes(self):
        if not self.character or not self.account_id:
            return []
        names = self.server.db.active_class_names(
            self.account_id, self.character.class_name
        )
        self.character._active_classes = list(names)
        return list(names)

    def active_class_names(self):
        self.refresh_active_classes()
        return self.character.active_class_names()

    def find_class_name(self, query):
        wanted = self.normalize_description_query(query)
        if not wanted:
            return None
        exact = []
        partial = []
        for class_name, class_type, weapon, base_power in CLASSES:
            normalized = self.normalize_description_query(class_name)
            if wanted == normalized:
                exact.append(class_name)
            elif wanted in normalized:
                partial.append(class_name)
        if exact:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None

    def skill_class_name(self, skill):
        skill_id = skill["id"] if isinstance(skill, dict) else str(skill)
        for class_name, skills in CLASS_SKILLS.items():
            if any(entry["id"] == skill_id for entry in skills):
                return class_name
        return self.character.class_name

    def teacher_here_for_active_class(self):
        active = set(self.active_class_names())
        for npc_id, npc in NPCS.items():
            if (
                npc.get("room") == self.character.room_id
                and npc.get("teacher_class") in active
            ):
                return npc_id, npc
        return None, None

    async def show_multiclass(self):
        active = self.active_class_names()
        await self.send(
            f"MULTICLASS: {len(active)} z {MULTICLASS_MAX_ACTIVE} aktywnych klas."
        )
        await self.send(
            f"Klasa główna: {self.character.class_name}. "
            f"Broń Duszy pozostaje: {self.character.soul_weapon}."
        )
        rows = self.server.db.active_class_rows(
            self.account_id, self.character.class_name
        )
        for row in rows:
            level = int(row["level"])
            xp = int(row["xp"])
            slot = int(row["active_slot"])
            role = "główna" if slot == 1 else f"dodatkowa, slot {slot}"
            if level >= CLASS_MASTERY_MAX_LEVEL:
                progress = "Biegłość 100, maksimum."
            else:
                needed = class_mastery_xp_to_next(level)
                progress = (
                    f"Biegłość {level}, XP {xp} z {needed}, "
                    f"brakuje {max(0, needed - xp)} XP."
                )
            await self.send(
                f"{row['class_name']}: {role}. {progress} "
                f"Pasyw: {self.character.class_passive_text_for(row['class_name'])}."
            )

        await self.send(
            "Dodanie klas jest opcjonalne. Użyj: multiclass add <klasa>. "
            "Usunięcie: multiclass remove <klasa>."
        )
        await self.send(
            "Maksymalnie 3 klasy łącznie. Class XP z każdego zabitego moba "
            "jest dzielony równo między wszystkie aktywne klasy."
        )
        await self.send(
            "Klasa główna i jej Broń Duszy nie zmieniają się. "
            "Dodatkowe klasy dają swoje pasywy i dostęp do skilli ich nauczycieli."
        )

    async def handle_multiclass(self, raw):
        if self.combat_mob_key:
            await self.send("Nie możesz zmieniać multiclass podczas walki.")
            return

        parts = raw.strip().split(maxsplit=1)
        if not parts:
            await self.show_multiclass()
            return

        action = self.normalize_description_query(parts[0])
        query = parts[1] if len(parts) > 1 else ""

        if action in ("status", "show", "lista", "list"):
            await self.show_multiclass()
            return

        if action in ("add", "dodaj", "wlacz", "włącz"):
            class_name = self.find_class_name(query)
            if not class_name:
                await self.send(
                    "Nie rozpoznaję klasy. Dostępne: "
                    + ", ".join(cls[0] for cls in CLASSES) + "."
                )
                return
            if class_name == self.character.class_name:
                await self.send("To już jest twoja klasa główna.")
                return

            old_max_mana = self.max_mana()
            ok, result = self.server.db.activate_secondary_class(
                self.account_id, self.character.class_name, class_name
            )
            if not ok:
                await self.send(str(result))
                return

            self.refresh_active_classes()
            new_max_mana = self.max_mana()
            if new_max_mana > old_max_mana:
                self.current_mana = new_max_mana
            else:
                self.current_mana = min(self.current_mana, new_max_mana)

            await self.send(
                f"Aktywowano dodatkową klasę: {class_name}. "
                f"Masz teraz {len(self.active_class_names())} aktywne klasy."
            )
            await self.send(
                "Jej pasyw działa od razu. Skilli nauczysz się u nauczyciela "
                f"klasy {class_name}."
            )
            return

        if action in ("remove", "usun", "usuń", "wylacz", "wyłącz"):
            class_name = self.find_class_name(query)
            if not class_name:
                await self.send("Nie rozpoznaję klasy do wyłączenia.")
                return

            old_max_mana = self.max_mana()
            ok, result = self.server.db.deactivate_secondary_class(
                self.account_id, self.character.class_name, class_name
            )
            if not ok:
                await self.send(str(result))
                return

            self.refresh_active_classes()
            new_max_mana = self.max_mana()
            self.current_mana = min(self.current_mana, new_max_mana)

            await self.send(
                f"Wyłączono dodatkową klasę: {class_name}. "
                "Jej Biegłość i nauczenie skille pozostają zapisane, "
                "ale nie można ich używać, dopóki klasa znów nie będzie aktywna."
            )
            return

        await self.send(
            "Użycie: multiclass, multiclass add <klasa>, "
            "multiclass remove <klasa>."
        )

    async def grant_class_xp(self, total_xp):
        active = self.active_class_names()
        if not active:
            return
        total_xp = max(0, int(total_xp))
        if total_xp <= 0:
            return

        base_share, remainder = divmod(total_xp, len(active))
        await self.send(
            f"EXP klas: {total_xp}. Aktywne klasy: {len(active)}. "
            "Pula jest dzielona między aktywne klasy."
        )

        for index, class_name in enumerate(active):
            share = base_share + (1 if index < remainder else 0)
            result = self.server.db.add_class_mastery_xp(
                self.account_id, class_name, share
            )
            if result["level_ups"]:
                await self.send(
                    f"{class_name}: Biegłość rośnie do {result['level']}."
                )
            if result["level"] >= CLASS_MASTERY_MAX_LEVEL:
                await self.send(
                    f"{class_name}: +{share} EXP klasy. "
                    "Biegłość 100, maksimum."
                )
            else:
                await self.send(
                    f"{class_name}: +{share} EXP klasy. "
                    f"Biegłość {result['level']}, XP {result['xp']} z "
                    f"{result['next_xp']}."
                )

    async def send(self, text=""):
        if self.closed:
            return
        try:
            self.writer.write((text + "\r\n").encode("utf-8"))
            await self.writer.drain()
        except (ConnectionError, BrokenPipeError):
            self.closed = True

    async def prompt(self, text):
        if self.closed:
            return
        try:
            self.writer.write(text.encode("utf-8"))
            await self.writer.drain()
        except (ConnectionError, BrokenPipeError):
            self.closed = True

    async def read_line(self):
        try:
            while True:
                data = await self.reader.readline()
                if not data:
                    return None
                text = clean_telnet(data).replace("\r", "").replace("\n", "").strip()
                if text:
                    return text
        except (ConnectionError, asyncio.IncompleteReadError):
            return None

    async def ask(self, text):
        await self.prompt(text)
        return await self.read_line()

    async def login_flow(self):
        await self.send(f"SOULBOUND ONLINE v{VERSION}")
        await self.send("Wpisz: login albo new")
        while True:
            cmd = await self.ask("> ")
            if cmd is None:
                return False
            cmd = cmd.lower()
            if cmd in ("login", "zaloguj"):
                if await self.do_login():
                    return True
            elif cmd in ("new", "nowe", "konto"):
                if await self.do_new_account():
                    return True
            elif cmd in ("quit", "wyjdz", "wyjdź"):
                return False
            else:
                await self.send("Dostępne: login, new, quit")

    async def do_login(self):
        username = await self.ask("Nazwa konta: ")
        if username is None:
            return False
        row = self.server.db.account_by_name(username)
        if not row:
            await self.send("Nie ma takiego konta.")
            return False
        password = await self.ask("Hasło: ")
        if password is None:
            return False
        if not verify_password(password, row["password_salt"], row["password_hash"]):
            await self.send("Nieprawidłowe hasło.")
            return False
        if self.server.account_online(row["id"]):
            await self.send("To konto jest już zalogowane.")
            return False
        self.account_id = row["id"]
        char_row = self.server.db.character_for_account(self.account_id)
        if char_row:
            self.character = Character.from_row(char_row)
            if self.character.room_id not in ROOMS:
                self.character.room_id = "square"
        else:
            if not await self.character_creator():
                return False
        return True

    async def do_new_account(self):
        await self.send("Tworzenie nowego konta.")
        while True:
            username = await self.ask("Nazwa konta, 3-20 znaków: ")
            if username is None:
                return False
            username = username.strip()
            if not safe_name(username):
                await self.send("Dozwolone są litery, cyfry, _ i -. Długość 3-20.")
                continue
            if self.server.db.account_by_name(username):
                await self.send("Taka nazwa konta już istnieje.")
                continue
            break
        while True:
            password = await self.ask("Hasło, minimum 6 znaków: ")
            if password is None:
                return False
            if len(password) < 6:
                await self.send("Hasło jest za krótkie.")
                continue
            confirm = await self.ask("Powtórz hasło: ")
            if confirm is None:
                return False
            if password != confirm:
                await self.send("Hasła się różnią.")
                continue
            break
        self.account_id = self.server.db.create_account(username, password)
        await self.send("Konto utworzone.")
        return await self.character_creator()

    async def choose_number(self, items, prompt_text):
        while True:
            raw = await self.ask(prompt_text)
            if raw is None:
                return None
            try:
                n = int(raw)
                if 1 <= n <= len(items):
                    return items[n - 1]
            except ValueError:
                pass
            await self.send("Nieprawidłowy numer.")

    def valid_name_case_form(self, value):
        value = value.strip()
        if not (1 <= len(value) <= 40):
            return False
        return not any(ord(ch) < 32 for ch in value)

    async def ask_name_declension(self, base_name):
        await self.send("ODMIANA IMIENIA POSTACI")
        await self.send(
            "Mianownik jest nazwą wybraną na początku kreatora. "
            "Teraz podaj pozostałe sześć form."
        )
        result = {"nom": base_name}
        await self.send(f"Mianownik. Kto? Co?: {base_name}.")

        prompts = (
            ("gen", "Dopełniacz. Kogo? Czego?"),
            ("dat", "Celownik. Komu? Czemu?"),
            ("acc", "Biernik. Kogo? Co?"),
            ("ins", "Narzędnik. Z kim? Z czym?"),
            ("loc", "Miejscownik. O kim? O czym?"),
            ("voc", "Wołacz. O!"),
        )
        for key, label in prompts:
            while True:
                raw = await self.ask(f"{label}: ")
                if raw is None:
                    return None
                value = raw.strip()
                if self.valid_name_case_form(value):
                    result[key] = value
                    break
                await self.send("Nieprawidłowa forma. Użyj od 1 do 40 znaków.")

        await self.send("Zapisana odmiana imienia:")
        await self.send(f"Mianownik: {result['nom']}.")
        await self.send(f"Dopełniacz: {result['gen']}.")
        await self.send(f"Celownik: {result['dat']}.")
        await self.send(f"Biernik: {result['acc']}.")
        await self.send(f"Narzędnik: {result['ins']}.")
        await self.send(f"Miejscownik: {result['loc']}.")
        await self.send(f"Wołacz: {result['voc']}.")
        return result

    async def character_creator(self):
        await self.send("KREATOR POSTACI")
        while True:
            name = await self.ask("Nazwa postaci, 3-20 znaków: ")
            if name is None:
                return False
            name = name.strip()
            if not safe_name(name) or self.server.db.character_name_exists(name):
                await self.send("Nieprawidłowa lub zajęta nazwa.")
                continue
            break
        await self.send("Wybierz rasę:")
        await self.send(
            "Znaczenie statystyk: Siła zwiększa atak fizyczny; "
            "Zręczność zwiększa szybkość i unik; Kondycja zwiększa HP; "
            "Inteligencja zwiększa Manę i moc czarów; "
            "Siła Woli zwiększa obronę magiczną."
        )
        for i, race in enumerate(RACES, 1):
            rname, desc, s, d, c, inte, w = race
            await self.send(
                f"{i}. {rname}. {desc} Siła {s}, Zręczność {d}, Kondycja {c}, "
                f"Inteligencja {inte}, Siła Woli {w}."
            )
        race = await self.choose_number(RACES, "Numer rasy: ")
        if race is None:
            return False
        await self.send("Wybierz klasę:")
        for i, cls in enumerate(CLASSES, 1):
            cname, ctype, weapon, _ = cls
            kind = "fizyczna" if ctype == "physical" else "magiczna"
            desc = CLASS_DESCRIPTIONS.get(cname, "")
            growth = (
                "Rozwój: wszystkie statystyki automatycznie: Siła, Zręczność, "
                "Kondycja, Inteligencja i Siła Woli."
            )
            skills = CLASS_SKILLS.get(cname, [])
            skill_text = "; ".join(
                f"{s['name']} do nauki od Soul Level {s['unlock']}" for s in skills
            )
            await self.send(
                f"{i}. {cname}. Typ {kind}. {desc} "
                f"{growth} Broń Duszy: {weapon}. Umiejętności: {skill_text}."
            )
        cls = await self.choose_number(CLASSES, "Numer klasy: ")
        if cls is None:
            return False

        name_cases = await self.ask_name_declension(name)
        if name_cases is None:
            return False

        self.server.db.create_character(
            self.account_id, name, race, cls, name_cases
        )
        self.character = Character.from_row(
            self.server.db.character_for_account(self.account_id)
        )
        await self.send(f"Utworzono postać {self.character.name}.")
        await self.send(
            "Postać nie posiada levelu. Wszystkie pięć statystyk rośnie automatycznie."
        )
        await self.send("Na start otrzymujesz 30 srebra, 2 złota i 2 Mikstury leczenia.")
        return True

    async def enter_world(self):
        self.refresh_active_classes()

        # Najpierw zachowaj zgodność starego mechanizmu portali Krypty
        # na podstawie lokacji zapisanej przy poprzednim wylogowaniu.
        self.server.db.sync_legacy_crypt_checkpoint(
            self.account_id, self.character.room_id
        )

        # Każde wejście do świata zaczyna się w Świątyni Odrodzenia.
        # Nie ma znaczenia, gdzie postać wylogowała się poprzednio.
        self.character.room_id = "temple"
        self.server.db.save_character(self.character)

        self.current_hp = self.max_hp()
        self.current_mana = self.max_mana()

        await self.server.broadcast_room(
            self.character.room_id,
            f"{self.character.name} pojawia się w Świątyni Odrodzenia.",
            exclude=self,
        )
        await self.send(
            f"Witaj, {self.character.name_case('voc')}. "
            f"Soulbound v{VERSION} World Core."
        )
        await self.send(
            "Rozpoczynasz sesję w Świątyni Odrodzenia."
        )
        await self.send("Wpisz help, aby poznać komendy.")
        await self.look()

    def equipped_item_rows(self):
        return list(self.server.db.equipment(self.account_id))

    def equipment_bonus_totals(self):
        totals = {
            "strength": 0,
            "dexterity": 0,
            "constitution": 0,
            "intelligence": 0,
            "willpower": 0,
            "hp": 0,
            "mana": 0,
        }
        for row in self.equipped_item_rows():
            item = ITEMS.get(row["item_id"])
            if not item:
                continue
            affix = item.get("affix")
            if affix in totals:
                totals[affix] += int(item.get("affix_amount", 0))
        return totals

    def dominant_crypt_set(self):
        counts = {}
        for row in self.equipped_item_rows():
            item = ITEMS.get(row["item_id"])
            if not item:
                continue
            tier = item.get("crypt_set_tier")
            if tier:
                tier = int(tier)
                counts[tier] = counts.get(tier, 0) + 1

        if not counts:
            return 0, 0

        tier, count = sorted(
            counts.items(),
            key=lambda entry: (entry[1], entry[0]),
            reverse=True,
        )[0]
        return tier, count

    def crypt_set_hp_mana_multiplier(self):
        _tier, count = self.dominant_crypt_set()
        return 1.10 if count >= 2 else 1.0

    def crypt_set_damage_multiplier(self):
        _tier, count = self.dominant_crypt_set()
        return 1.10 if count >= 4 else 1.0

    def crypt_set_defense_multiplier(self):
        _tier, count = self.dominant_crypt_set()
        return 1.15 if count >= 6 else 1.0

    def crypt_set_bonus_text(self):
        tier, count = self.dominant_crypt_set()
        if not tier:
            return "Brak aktywnego zestawu Krypty."

        active = []
        if count >= 2:
            active.append("2 części: +10 procent maksymalnego HP i Many")
        if count >= 4:
            active.append("4 części: +10 procent wszystkich obrażeń")
        if count >= 6:
            active.append("6 części: +15 procent obrony fizycznej i magicznej")

        if not active:
            active_text = "brak aktywnego progu; potrzeba 2 części"
        else:
            active_text = "; ".join(active)

        return (
            f"Zestaw Krypty Tier {tier}: {count} z 6 części. "
            f"{active_text}."
        )

    def effective_strength(self):
        return (
            self.character.strength
            + self.equipment_bonus_totals()["strength"]
        )

    def effective_dexterity(self):
        return (
            self.character.dexterity
            + self.equipment_bonus_totals()["dexterity"]
        )

    def critical_chance(self):
        dexterity = self.effective_dexterity()
        chance = 0.05 + (dexterity - 10) * 0.005
        return max(0.01, min(0.35, chance))

    def critical_multiplier(self):
        return 1.50

    def roll_critical_hit(self, damage):
        damage = max(0, int(damage))
        if damage <= 0:
            return damage, False
        if random.random() < self.critical_chance():
            return (
                max(
                    1,
                    int(round(
                        damage * self.critical_multiplier()
                    )),
                ),
                True,
            )
        return damage, False

    def effective_constitution(self):
        return (
            self.character.constitution
            + self.equipment_bonus_totals()["constitution"]
        )

    def effective_intelligence(self):
        return (
            self.character.intelligence
            + self.equipment_bonus_totals()["intelligence"]
        )

    def effective_willpower(self):
        return (
            self.character.willpower
            + self.equipment_bonus_totals()["willpower"]
        )

    def max_hp(self):
        bonuses = self.equipment_bonus_totals()
        base = 40 + self.effective_constitution() * 5
        value = int(
            round(
                (base + bonuses["hp"])
                * self.character.racial_max_hp_multiplier()
                * self.crypt_set_hp_mana_multiplier()
            )
        )
        return max(1, value)

    def max_mana(self):
        if not any(
            class_type_for_name(name) == "magic"
            for name in self.active_class_names()
        ):
            return 0

        bonuses = self.equipment_bonus_totals()
        base = 20 + self.effective_intelligence() * 5
        value = int(
            round(
                (base + bonuses["mana"])
                * self.character.racial_max_mana_multiplier()
                * self.crypt_set_hp_mana_multiplier()
            )
        )
        return max(0, value)

    def physical_power(self):
        return self.effective_strength()

    def speed(self):
        return 10 + self.effective_dexterity() * 2

    def dodge_chance(self):
        base = max(0.0, (self.speed() - 20) / 300.0)
        return min(
            0.45,
            base
            + self.character.class_dodge_bonus()
            + self.character.racial_dodge_bonus(),
        )

    def spell_power(self):
        return self.effective_intelligence()

    def magic_defense(self):
        base = max(0, self.effective_willpower() // 2)
        value = int(
            round(
                base
                * self.character.class_magic_defense_multiplier()
                * self.character.racial_magic_defense_multiplier()
                * self.crypt_set_defense_multiplier()
            )
        )
        return max(0, value)

    def defense(self):
        total = 0
        for row in self.server.db.equipment(self.account_id):
            item = ITEMS.get(row["item_id"])
            if item:
                total += int(item.get("defense", 0))
        return max(
            0,
            int(round(total * self.crypt_set_defense_multiplier()))
        )

    async def look(self):
        room = ROOMS[self.character.room_id]
        await self.send(f"{room['name']}. Strefa: {room['zone']}.")
        await self.send(room["desc"])

        npcs = [v["name"] for v in NPCS.values() if v["room"] == self.character.room_id]
        if npcs:
            await self.send("NPC: " + ", ".join(npcs) + ".")

        mobs = self.server.world.room_mobs(self.character.room_id)
        if mobs:
            names = [MOB_TEMPLATES[m.template_id]["name"] for m in mobs]
            await self.send("Przeciwnicy: " + ", ".join(names) + ".")

        corpses = self.server.world.room_corpses(self.character.room_id)
        if corpses:
            await self.send(
                "Ciała: " + ", ".join(c.mob_name for c in corpses)
                + ". Wpisz ciało, aby sprawdzić ekwipunek."
            )

        if self.crypt_descent_blocked_for_player(self.character.room_id):
            boss = self.server.world.live_crypt_boss(self.character.room_id)
            if boss:
                await self.send(
                    f"Zejście niżej blokuje boss: "
                    f"{MOB_TEMPLATES[boss.template_id]['name']}."
                )

        others = [
            s.character.name for s in self.server.sessions
            if s is not self and s.character and s.character.room_id == self.character.room_id
        ]
        if others:
            await self.send("Gracze tutaj: " + ", ".join(sorted(others, key=str.lower)) + ".")
        await self.show_exits()

    async def show_exits(self):
        room = ROOMS[self.character.room_id]
        if not room["exits"]:
            await self.send("Wyjścia: brak.")
            return
        exits=[]
        for direction in room["exits"].keys():
            if self.crypt_descent_blocked_for_player(self.character.room_id,direction):
                exits.append(f"{direction}, zablokowane przez bossa")
            else:
                exits.append(direction)
        await self.send("Wyjścia: " + ", ".join(exits) + ".")

    async def show_map(self):
        current = self.character.room_id
        await self.send("MAPA ODKRYTEGO ŚWIATA")

        zones = {}
        for room_id, room in ROOMS.items():
            if room_id.startswith("crypt_floor_"):
                continue
            zones.setdefault(room["zone"], []).append(
                (room_id, room["name"])
            )

        for zone in sorted(zones):
            await self.send(zone + ":")
            entries = []
            for room_id, name in sorted(
                zones[zone], key=lambda entry: entry[1].lower()
            ):
                marker = " [TU]" if room_id == current else ""
                entries.append(name + marker)
            await self.send("; ".join(entries) + ".")

        floor = crypt_floor_number(current)
        marker = f" [TU: piętro {floor}]" if floor else ""
        await self.send(
            f"Krypta 1-100: piętra 1-100{marker}."
        )
        await self.send(
            "Każdą nazwę z mapy można podać do prowadz. "
            "Wpisz prowadz lista, aby dostać pełną listę celów."
        )


    async def show_crypt_info(self):
        floor = crypt_floor_number(self.character.room_id)
        await self.send(
            "KRYPTA: 100 pięter. Bossowie: 10, 20, 30, 40, 50, "
            "60, 70, 80, 90 i 100."
        )
        await self.send(
            "Żywy boss zawsze blokuje zejście na następne piętro."
        )
        await self.send(
            "Po zabiciu bossa przejście jest otwarte tylko do jego respawnu. "
            "Gdy boss odrodzi się, ponownie blokuje zejście."
        )
        await self.send(
            "Pokonanie bossa odblokowuje trwały Portal Krypty do jego piętra. "
            "Portal skraca podróż, ale nie wyłącza żywego bossa."
        )
        await self.send(
            "Portal uruchamiasz komendą portal <piętro> w Sali Krypty "
            "albo w Przedsionku Krypty."
        )
        await self.send(
            "Zwykłe moby Krypty zostawiają 1 element ekwipunku na ciele, "
            "bossowie 3."
        )
        await self.send(
            "Moby nie są agresywne. Nie atakują gracza same."
        )

        highest = self.crypt_portal()
        if highest:
            await self.send(
                f"Najwyższy odblokowany Portal Krypty: piętro {highest}."
            )
        else:
            await self.send("Portale Krypty: jeszcze brak.")

        if floor:
            await self.send(
                f"Aktualne piętro Krypty: {floor} ze 100."
            )
            boss = self.server.world.live_crypt_boss(
                self.character.room_id
            )
            if boss:
                await self.send(
                    f"Boss żyje i blokuje zejście: "
                    f"{MOB_TEMPLATES[boss.template_id]['name']}."
                )
            elif floor in CRYPT_BOSS_FLOORS:
                await self.send(
                    "Boss tego piętra jest obecnie pokonany. "
                    "Możesz zejść niżej do czasu jego respawnu."
                )


    async def show_corpses(self, query=""):
        corpses=self.server.world.room_corpses(self.character.room_id)
        if not corpses:
            await self.send("Nie ma tutaj żadnych ciał."); return
        if query.strip():
            corpse=self.server.world.find_corpse(self.character.room_id,query)
            if not corpse: await self.send("Nie widzę takiego ciała."); return
            corpses=[corpse]
        for number,corpse in enumerate(corpses,1):
            names=", ".join(ITEMS[i]["name"] for i in corpse.items) if corpse.items else "brak ekwipunku"
            await self.send(f"{number}. Ciało: {corpse.mob_name}. Ekwipunek na ciele: {names}.")
        await self.send("Aby zabrać ekwipunek wpisz: przeszukaj ciało albo przeszukaj <nazwa moba>.")

    async def loot_corpse(self, query=""):
        corpses=self.server.world.room_corpses(self.character.room_id)
        if not corpses:
            await self.send("Nie ma tutaj żadnych ciał do przeszukania."); return
        corpse=self.server.world.find_corpse(self.character.room_id,query)
        if corpse is None:
            if not query.strip() and len(corpses)>1:
                await self.send("Jest tutaj kilka ciał. Wpisz ciało, potem przeszukaj <nazwa moba>.")
            else: await self.send("Nie widzę takiego ciała.")
            return
        if not corpse.items:
            await self.send(f"Przeszukujesz ciało: {corpse.mob_name}. Nie ma już na nim ekwipunku."); return
        looted=list(corpse.items); corpse.items.clear()
        for item_id in looted: self.server.db.add_item(self.account_id,item_id,1)
        await self.send(f"Przeszukujesz ciało: {corpse.mob_name}. Zabierasz: " + ", ".join(ITEMS[i]["name"] for i in looted) + ".")

    async def show_where(self):
        room = ROOMS[self.character.room_id]
        await self.send(f"Jesteś tutaj: {room['name']}. Strefa: {room['zone']}.")

    def help_commands(self):
        return [
            "help [temat] / pomoc [temat] - pomoc; help tematy pokazuje działy",
            "changes / zmiany / changelog - pokaż najnowsze zmiany",
            "opis [nazwa] / describe [name] - szczegółowy opis elementu świata",
            "look lub l - opis aktualnej lokacji",
            "exits - dostępne kierunki",
            "map - lista lokacji świata; Krypta 1-100 jest pokazana skrótowo",
            "krypta / crypt - informacje o Krypcie 1-100, bossach i checkpointach",
            "portal [piętro] - pokaż lub uruchom odblokowany Portal Krypty",
            "atlas [ryby|drewno|rudy|surowiec] - atlas pozyskiwania surowców",
            "where - aktualna lokacja",
            "location / lokalizacja - lokacja, strefa i wyjścia",
            "north/south/east/west/up/down lub n/s/e/w/u/d - ruch",
            "prowadz lokacja / walk to location - automatyczne prowadzenie do każdej lokacji świata",
            "prowadz lista - wszystkie dostępne cele prowadzenia",
            "who - gracze online",
            "say tekst - rozmowa lokalna",
            "tell gracz tekst - wiadomość prywatna",
            "druzyna / party - zarządzanie drużyną",
            "pc tekst - czat drużyny",
            "charyzma / charisma - rabat sklepowy i limit drużyny",
            "multiclass / klasy - opcjonalne 1-3 aktywne klasy i Biegłość klas",
            "multiclass add klasa / remove klasa - dodaj lub wyłącz klasę dodatkową",
            "stats - statystyki",
            "odmiana / przypadki - pokaż 7 form imienia postaci",
            "skills / umiejetnosci - lista umiejętności twojej klasy",
            "skillnames / nazwyskilli - wszystkie nazwy skilli wszystkich klas",
            "skill / umiejetnosc / cast <nazwa lub numer> [cel] - użyj umiejętności",
            "użyj umiejętność <nazwa> [cel] / use skill <name> [target] - alternatywne użycie skilla",
            "learn / naucz / ucz <nazwa lub numer> - naucz się skilla u nauczyciela",
            "soul - Broń Duszy, Soul Level 1-200",
            "money - srebro, złoto i mithril",
            "exchange - kurs wymiany",
            "exchange gold / exchange mithril - wymiana walut",
            "professions / profesje - Wędkarstwo, Górnictwo i Drwalstwo",
            "rangi / ranks - pełna lista rang trzech profesji",
            "tools / narzedzia - skrót wszystkich 7 narzędzi",
            "wedka / kilof / pila / mlot / noz / sierp / mozdzierz - pełne informacje o wybranym narzędziu",
            "tiers / tiery / nazwytierow - pełna lista Tierów wszystkich 7 narzędzi",
            "fish / wedkuj / low - pojedynczy połów",
            "low on / fish on - auto-łowienie",
            "low off / fish off - wyłącz auto-łowienie",
            "mine / kop - pojedyncze wydobycie",
            "kop on / mine on - auto-kopanie",
            "kop off / mine off - wyłącz auto-kopanie",
            "tnij / drwal / woodcut - pojedyncze pozyskanie drewna",
            "tnij on / woodcut on - auto-Drwalstwo",
            "tnij off / woodcut off - wyłącz auto-Drwalstwo",
            "zbieraj / zielarstwo - pojedynczy zbiór ziół",
            "zbieraj on / zbieraj off - auto-Zielarstwo",
            "ziola / herbs - Torba Zielarska",
            "alchemia / warz receptura - warzenie mikstur",
            "net / siatka - Siatka na ryby",
            "bag / sakwa - Sakwa górnicza",
            "drewno / stos / woodpile - Stos drewna",
            "put fish net / wloz ryba siatka - przenieś ryby do Siatki",
            "put ore bag / wloz ruda sakwa - przenieś rudy do Sakwy",
            "take przedmiot net/bag / wyjmij przedmiot siatka/sakwa - wyjmij surowiec",
            "sell / sprzedaj przedmiot - sprzedaj rybę, rudę lub drewno",
            "receptury / przepisy / recipes [craft|cook] - lista receptur",
            "craft / stworz / wytworz receptura - rzemiosło z rud i drewna",
            "cook / gotuj receptura - przygotuj potrawę z ryb",
            "inventory / i - zwykły ekwipunek",
            "equipment - założone wyposażenie, rarity, affix i bonus setu",
            "help loot_krypty - rarity, losowe statystyki i sety Krypty",
            "equip przedmiot - załóż pancerz lub talizman",
            "use / użyj przedmiot - użyj przedmiotu; komenda obsługuje też umiejętności",
            "shop / sklep / list / lista - oferta sprzedawcy",
            "buy / kup przedmiot - kup przedmiot",
            "talk npc - rozmowa, zadania i lekcje nauczycieli klasowych",
            "teachers / nauczyciele - lista nauczycieli w Sali Gildii",
            "quests - dziennik zadań",
            "attack / atakuj / zabij / kill przeciwnik - tura walki",
            "ciało / zwloki / corpse - pokaż ciała i ich ekwipunek",
            "przeszukaj ciało / loot - zabierz ekwipunek z ciała moba",
            "flee / uciekaj - ucieczka",
            "unlock - odblokuj gotowy Soul Tier",
            "save - zapis",
            "quit - wyjście",
        ]

    def full_changelog_lines(self):
        module_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = (
            os.path.join(module_dir, "CHANGELOG_PL.txt"),
            os.path.join(os.getcwd(), "CHANGELOG_PL.txt"),
        )

        for changelog_path in candidates:
            try:
                if not os.path.exists(changelog_path):
                    continue
                with open(changelog_path, "r", encoding="utf-8") as handle:
                    lines = [line.rstrip("\r\n") for line in handle]
                if any(line.strip() for line in lines):
                    return lines
            except (OSError, UnicodeError):
                continue

        lines = [LATEST_CHANGES_TITLE]
        lines.extend("- " + line for line in LATEST_CHANGES)
        return lines

    async def show_latest_changes(self):
        await self.send("PEŁNA HISTORIA ZMIAN SOULBOUND")
        await self.send(
            "Najnowsze wersje są na górze. Poniżej znajduje się "
            "cały dostępny CHANGELOG_PL.txt."
        )
        for line in self.full_changelog_lines():
            if line.strip():
                await self.send(line)

    async def show_help(self, topic=""):
        raw = topic.strip().lower()
        key = HELP_TOPIC_ALIASES.get(raw, raw)

        if not key:
            await self.send("POMOC GŁÓWNA")
            await self.send(
                "Użyj help <temat>. Tematy: podstawy, komendy, nawigacja, statystyki, "
                "walka, krytyki, bossowie, respawn, odpoczynek, dusza, pieniadze, ekwipunek, loot_krypty, zadania, profesje, wedkarstwo, "
                "gornictwo, drwalstwo, zielarstwo, alchemia, rzemioslo, gotowanie, receptury, atlas, "
                "charyzma, druzyny, multiclass, krypta, portale, zwloki, pojemniki, sklepy, gracze, smierc, rasy, klasy, "
                "umiejetnosci, nazwy_skilli, nauczyciele, opisy, zmiany."
            )
            await self.send("help tematy - lista tematów.")
            await self.send("help wszystko - pełny przewodnik.")
            await self.send("opis <nazwa> - szczegółowy opis dowolnego elementu.")
            await self.send("changes / zmiany / changelog - pełna historia wszystkich wersji i zmian, najnowsze na górze.")
            await self.send("Na start: look, exits, stats, inventory, quests, help podstawy.")
            return

        if key == "tematy":
            await self.send("TEMATY POMOCY")
            for name in HELP_TOPICS:
                await self.send(name)
            await self.send("Dodatkowo: komendy, wszystko.")
            return

        if key == "komendy":
            await self.send("WSZYSTKIE KOMENDY")
            for line in self.help_commands():
                await self.send(line)
            return

        if key == "wszystko":
            await self.send("PEŁNY PRZEWODNIK SOULBOUND")
            for name, lines in HELP_TOPICS.items():
                await self.send(name.upper())
                for line in lines:
                    await self.send(line)
            await self.send("KOMENDY")
            for line in self.help_commands():
                await self.send(line)
            return

        lines = HELP_TOPICS.get(key)
        if not lines:
            await self.send("Nie znam takiego tematu pomocy. Wpisz help tematy albo help komendy.")
            return

        await self.send("POMOC: " + key.upper())
        for line in lines:
            await self.send(line)



    def format_item_description(self, item_id, item):
        parts = [f"{item['name']}. Typ: {item.get('type', 'przedmiot')}.", item.get("desc", "")]

        if item.get("type") == "armor":
            parts.append(
                f"Slot: {item.get('slot', 'brak')}. "
                f"Obrona fizyczna: +{item.get('defense', 0)}."
            )
            if item.get("rarity_name"):
                parts.append(
                    f"Rzadkość: {item['rarity_name']}."
                )
            if item.get("affix"):
                affix_name = CRYPT_AFFIXES.get(
                    item["affix"], item["affix"]
                )
                parts.append(
                    f"Losowy bonus: {affix_name} "
                    f"+{item.get('affix_amount', 0)}."
                )
            if item.get("crypt_set_tier"):
                parts.append(
                    f"Zestaw Krypty Tier "
                    f"{item['crypt_set_tier']}."
                )
        elif item.get("type") == "tool":
            tool = "Wędka" if item.get("tool_type") == "fishing" else "Kilof"
            parts.append(f"Narzędzie profesji: {tool}. Ma własny level 1-100 i osobny XP.")
        elif "heal" in item:
            parts.append(f"Leczenie: {item['heal']} HP.")
        elif "soul_xp" in item:
            parts.append(f"Po użyciu daje {item['soul_xp']} Soul XP.")

        if item.get("price") is not None:
            currency = item.get("currency", "gold")
            names = {"silver": "srebra", "gold": "złota", "mithril": "mithrilu"}
            parts.append(f"Cena kupna: {item['price']} {names.get(currency, currency)}.")

        sell_parts = []
        if item.get("sell_silver"):
            sell_parts.append(f"{item['sell_silver']} srebra")
        if item.get("sell_gold"):
            sell_parts.append(f"{item['sell_gold']} złota")
        if item.get("sell_mithril"):
            sell_parts.append(f"{item['sell_mithril']} mithrilu")
        if sell_parts:
            parts.append("Wartość sprzedaży: " + ", ".join(sell_parts) + ".")

        return " ".join(p for p in parts if p)

    def room_special_features(self, room_id):
        features = []
        if room_id in RIVER_FISHING_ROOMS:
            features.append("łowisko rzeczne")
        if room_id in LAKE_FISHING_ROOMS:
            features.append("łowisko jeziorowe")
        if room_id in SEA_FISHING_ROOMS:
            features.append("łowisko morskie")
        if room_id in OCEAN_FISHING_ROOMS:
            features.append("łowisko oceaniczne")
        if room_id in MINING_ROOMS:
            features.append("miejsce wydobycia")
        if room_id in SHOPS:
            features.append("sklep")
        if any(npc["room"] == room_id for npc in NPCS.values()):
            features.append("NPC")
        if any(spawn_room == room_id for spawn_room, _ in MOB_SPAWNS):
            features.append("przeciwnicy")
        return features

    def normalize_description_query(self, value):
        table = str.maketrans(
            "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ",
            "acelnoszzACELNOSZZ"
        )
        return value.strip().lower().translate(table)

    def find_description_entry(self, mapping, query, name_field="name"):
        q = self.normalize_description_query(query)
        if not q:
            return None
        exact = []
        partial = []
        for key, value in mapping.items():
            name = value[name_field] if isinstance(value, dict) else str(value)
            nk = self.normalize_description_query(str(key))
            nn = self.normalize_description_query(name)
            if q == nk or q == nn:
                exact.append((key, value))
            elif q in nk or q in nn:
                partial.append((key, value))
        if exact:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None

    def atlas_item_locations(self, item_id):
        locations = []

        if item_id in RIVER_FISH_ATLAS:
            locations.extend(ROOMS[r]["name"] for r in sorted(RIVER_FISHING_ROOMS))
        if item_id in LAKE_FISH_ATLAS:
            locations.extend(ROOMS[r]["name"] for r in sorted(LAKE_FISHING_ROOMS))
        if item_id in SEA_FISH_ATLAS:
            locations.extend(ROOMS[r]["name"] for r in sorted(SEA_FISHING_ROOMS))
        if item_id in OCEAN_FISH_ATLAS:
            locations.extend(ROOMS[r]["name"] for r in sorted(OCEAN_FISHING_ROOMS))

        if item_id in WOOD_BEGINNER_ATLAS:
            locations.extend(
                ROOMS[r]["name"] for r in ("lumberjack_camp", "meadow")
            )
        if item_id in WOOD_FOREST_ATLAS:
            locations.extend(
                ROOMS[r]["name"] for r in ("whisper_grove", "old_road")
            )
        if item_id in WOOD_DEEP_ATLAS:
            locations.append(ROOMS["deep_grove"]["name"])

        if item_id in ORE_RESOURCE_IDS:
            locations.extend(ROOMS[r]["name"] for r in sorted(MINING_ROOMS))
        if item_id in HERB_MEADOW_ATLAS:
            locations.extend(ROOMS[r]["name"] for r in ("herbalist_hut", "meadow"))
        if item_id in HERB_FOREST_ATLAS:
            locations.extend(ROOMS[r]["name"] for r in ("whisper_grove", "old_road"))
        if item_id in HERB_WATER_ATLAS:
            locations.extend(ROOMS[r]["name"] for r in ("riverbank", "lake_shore"))
        if item_id in HERB_DEEP_ATLAS:
            locations.append(ROOMS["deep_grove"]["name"])

        result = []
        seen = set()
        for value in locations:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result

    def atlas_names(self, item_ids):
        return ", ".join(
            sorted(
                (ITEMS[item_id]["name"] for item_id in item_ids),
                key=str.lower,
            )
        )

    async def show_atlas(self, query=""):
        q = self.normalize_description_query(query)

        if not q:
            await self.send("ATLAS SUROWCÓW")
            await self.send("Działy: ryby, drewno, rudy, zioła.")
            await self.send(
                "Użycie: atlas ryby, atlas drewno, atlas rudy "
                "albo atlas <nazwa surowca>."
            )
            return

        if q in ("ryby", "fish", "wedkarstwo"):
            await self.send("ATLAS RYB")
            groups = (
                ("Rzeka", RIVER_FISHING_ROOMS, RIVER_FISH_ATLAS),
                ("Jezioro", LAKE_FISHING_ROOMS, LAKE_FISH_ATLAS),
                ("Morze", SEA_FISHING_ROOMS, SEA_FISH_ATLAS),
                ("Ocean", OCEAN_FISHING_ROOMS, OCEAN_FISH_ATLAS),
            )
            for title, rooms, items in groups:
                places = ", ".join(ROOMS[r]["name"] for r in sorted(rooms))
                await self.send(f"{title}. Łowiska: {places}.")
                await self.send("Gatunki: " + self.atlas_names(items) + ".")
            return

        fish_groups = {
            "rzeka": ("Rzeka", RIVER_FISHING_ROOMS, RIVER_FISH_ATLAS),
            "river": ("Rzeka", RIVER_FISHING_ROOMS, RIVER_FISH_ATLAS),
            "jezioro": ("Jezioro", LAKE_FISHING_ROOMS, LAKE_FISH_ATLAS),
            "lake": ("Jezioro", LAKE_FISHING_ROOMS, LAKE_FISH_ATLAS),
            "morze": ("Morze", SEA_FISHING_ROOMS, SEA_FISH_ATLAS),
            "sea": ("Morze", SEA_FISHING_ROOMS, SEA_FISH_ATLAS),
            "ocean": ("Ocean", OCEAN_FISHING_ROOMS, OCEAN_FISH_ATLAS),
        }
        if q in fish_groups:
            title, rooms, items = fish_groups[q]
            await self.send(f"ATLAS: {title.upper()}")
            await self.send(
                "Łowiska: "
                + ", ".join(ROOMS[r]["name"] for r in sorted(rooms))
                + "."
            )
            await self.send("Gatunki: " + self.atlas_names(items) + ".")
            return

        if q in ("drewno", "wood", "drwalstwo"):
            await self.send("ATLAS DREWNA")
            await self.send(
                "Obóz Drwala i Srebrna Łąka: "
                + self.atlas_names(WOOD_BEGINNER_ATLAS) + "."
            )
            await self.send(
                "Gaj Szeptów i Stary Trakt: "
                + self.atlas_names(WOOD_FOREST_ATLAS) + "."
            )
            await self.send(
                "Głębia Gaju: "
                + self.atlas_names(WOOD_DEEP_ATLAS) + "."
            )
            return

        if q in ("rudy", "ruda", "ore", "gornictwo"):
            await self.send("ATLAS RUD")
            await self.send(
                "Miejsca wydobycia: "
                + ", ".join(ROOMS[r]["name"] for r in sorted(MINING_ROOMS))
                + "."
            )
            for item_id, minimum in ORE_ATLAS_LEVELS.items():
                await self.send(
                    f"{ITEMS[item_id]['name']}: możliwa od około levelu "
                    f"{minimum} Kilofa."
                )
            await self.send(
                "Czysty mithril: możliwy od levelu 80 Kilofa. "
                "Trafia bezpośrednio do portfela."
            )
            return

        if q in ("ziola", "zioła", "herbs", "herb", "zielarstwo"):
            await self.send("ATLAS ZIÓŁ")
            await self.send("Chata Zielarki i Srebrna Łąka: " + self.atlas_names(HERB_MEADOW_ATLAS) + ".")
            await self.send("Gaj Szeptów i Stary Trakt: " + self.atlas_names(HERB_FOREST_ATLAS) + ".")
            await self.send("Brzeg Rzeki i Brzeg Srebrnego Jeziora: " + self.atlas_names(HERB_WATER_ATLAS) + ".")
            await self.send("Głębia Gaju: " + self.atlas_names(HERB_DEEP_ATLAS) + ".")
            return

        resources = {
            item_id: ITEMS[item_id]
            for item_id in (
                FISH_RESOURCE_IDS | ORE_RESOURCE_IDS | WOOD_RESOURCE_IDS | HERB_RESOURCE_IDS
            )
        }
        found = find_by_name(resources, query)
        if not found:
            await self.send(
                "Atlas nie rozpoznaje tego surowca. "
                "Wpisz atlas ryby, atlas drewno albo atlas rudy."
            )
            return

        item_id, item = found
        await self.send(f"ATLAS: {item['name']}.")
        if item_id in FISH_RESOURCE_IDS:
            await self.send("Typ: ryba. Trafia do Siatki na ryby.")
        elif item_id in WOOD_RESOURCE_IDS:
            await self.send("Typ: drewno. Trafia na Stos drewna.")
        elif item_id in HERB_RESOURCE_IDS:
            await self.send("Typ: zioło. Trafia do Torby Zielarskiej.")
        else:
            await self.send("Typ: ruda. Trafia do Sakwy górniczej.")

        places = self.atlas_item_locations(item_id)
        if places:
            await self.send("Występowanie: " + ", ".join(places) + ".")

        if item_id in ORE_ATLAS_LEVELS:
            await self.send(
                f"Orientacyjny minimalny level Kilofa: "
                f"{ORE_ATLAS_LEVELS[item_id]}."
            )

    async def describe_target(self, query):
        q = query.strip()

        if not q:
            room = ROOMS[self.character.room_id]
            await self.send(f"{room['name']}. Strefa: {room['zone']}. {room['desc']}")
            features = self.room_special_features(self.character.room_id)
            if features:
                await self.send("Funkcje lokacji: " + ", ".join(features) + ".")
            await self.show_exits()
            return

        normalized = self.normalize_description_query(q)

        normalized_systems = {
            self.normalize_description_query(k): v
            for k, v in SYSTEM_DESCRIPTIONS.items()
        }
        normalized_stats = {
            self.normalize_description_query(k): v
            for k, v in STAT_DESCRIPTIONS.items()
        }
        if normalized in normalized_stats:
            await self.send(normalized_stats[normalized])
            return
        if normalized in normalized_systems:
            await self.send(normalized_systems[normalized])
            return

        found = self.find_description_entry(ITEMS, q)
        if found:
            item_id, item = found
            await self.send(self.format_item_description(item_id, item))
            return

        found = self.find_description_entry(NPCS, q)
        if found:
            npc_id, npc = found
            room = ROOMS[npc["room"]]
            desc = NPC_DESCRIPTIONS.get(npc_id, npc.get("dialogue", ""))
            await self.send(f"{npc['name']}. {desc}")
            await self.send(f"Stała lokacja: {room['name']}.")
            if npc.get("quest"):
                quest = QUESTS[npc["quest"]]
                await self.send(f"Powiązane zadanie: {quest['name']}. {quest['description']}")
            return

        found = self.find_description_entry(MOB_TEMPLATES, q)
        if found:
            mob_id, mob = found
            dtype = "magiczne" if mob.get("damage_type") == "magic" else "fizyczne"
            await self.send(f"{mob['name']}. {MOB_DESCRIPTIONS.get(mob_id, '')}")
            await self.send(
                f"HP: {mob['max_hp']}. Bazowe obrażenia: {mob['damage']}. Typ obrażeń: {dtype}."
            )
            await self.send(
                f"Nagroda podstawowa: {mob.get('silver',0)} srebra, "
                f"{mob.get('gold',0)} złota, {mob.get('mithril',0)} mithrilu; "
                f"Rozwój statystyk +{mob.get('stat_reward',0)}; "
                f"Soul XP +{mob.get('soul_reward',0)}."
            )
            drops = []
            for item_id, chance in mob.get("drops", {}).items():
                item = ITEMS.get(item_id, {"name": item_id})
                drops.append(f"{item['name']} około {int(chance * 100)} procent")
            if drops:
                await self.send("Możliwe dropy: " + ", ".join(drops) + ".")
            return

        found = self.find_description_entry(ROOMS, q)
        if found:
            room_id, room = found
            await self.send(f"{room['name']}. Strefa: {room['zone']}. {room['desc']}")
            exits = ", ".join(room["exits"].keys()) if room["exits"] else "brak"
            await self.send("Wyjścia: " + exits + ".")
            features = self.room_special_features(room_id)
            if features:
                await self.send("Funkcje lokacji: " + ", ".join(features) + ".")
            return

        found = self.find_description_entry(QUESTS, q)
        if found:
            quest_id, quest = found
            await self.send(
                f"Zadanie: {quest['name']}. Zleca: {quest['giver']}. {quest['description']}"
            )
            rewards = []
            if quest.get("reward_stat_progress"):
                rewards.append(f"{quest['reward_stat_progress']} EXP rozwoju")
            if quest.get("reward_profession_xp"):
                rewards.append(
                    f"{quest['reward_profession_xp']} XP profesji {quest.get('reward_profession','')}"
                )
            if quest.get("reward_tool_xp"):
                tool = "Wędki" if quest.get("reward_tool_type") == "fishing" else "Kilofa"
                rewards.append(f"{quest['reward_tool_xp']} XP {tool}")
            if quest.get("reward_silver"):
                rewards.append(f"{quest['reward_silver']} srebra")
            if quest.get("reward_gold"):
                rewards.append(f"{quest['reward_gold']} złota")
            if quest.get("reward_mithril"):
                rewards.append(f"{quest['reward_mithril']} mithrilu")
            for item_id, qty in quest.get("reward_items", {}).items():
                rewards.append(f"{ITEMS.get(item_id, {'name': item_id})['name']} x{qty}")
            if rewards:
                await self.send("Nagrody: " + ", ".join(rewards) + ".")
            return

        race_map = {
            race[0]: {
                "name": race[0], "desc": race[1],
                "strength": race[2], "dexterity": race[3],
                "constitution": race[4], "intelligence": race[5],
                "willpower": race[6],
            }
            for race in RACES
        }
        found = self.find_description_entry(race_map, q)
        if found:
            _, race = found
            await self.send(f"Rasa: {race['name']}. {race['desc']}")
            await self.send(
                f"Startowe statystyki: Siła {race['strength']}, "
                f"Zręczność {race['dexterity']}, Kondycja {race['constitution']}, "
                f"Inteligencja {race['intelligence']}, Siła Woli {race['willpower']}."
            )
            return

        class_map = {
            cls[0]: {"name": cls[0], "type": cls[1], "weapon": cls[2], "base": cls[3]}
            for cls in CLASSES
        }
        found = self.find_description_entry(class_map, q)
        if found:
            _, cls = found
            kind = "fizyczna" if cls["type"] == "physical" else "magiczna"
            await self.send(
                f"Klasa: {cls['name']}. Typ: {kind}. {CLASS_DESCRIPTIONS.get(cls['name'], '')}"
            )
            await self.send(
                f"Broń Duszy: {cls['weapon']}. Bazowa moc Broni Duszy: {cls['base']}."
            )
            await self.send("Rozwój klasy: wszystkie pięć statystyk rośnie automatycznie.")
            skills = CLASS_SKILLS.get(cls["name"], [])
            if skills:
                await self.send(
                    "Umiejętności: " + "; ".join(
                        f"{s['name']} do nauki od Soul Level {s['unlock']}" for s in skills
                    ) + "."
                )
            return

        help_key = HELP_TOPIC_ALIASES.get(normalized, normalized)
        if help_key in HELP_TOPICS:
            await self.show_help(help_key)
            return

        await self.send(
            "Nie znalazłem takiego opisu. Spróbuj dokładniejszej nazwy albo wpisz help opisy."
        )


    async def show_name_declension(self):
        await self.send(f"ODMIANA IMIENIA: {self.character.name_nom}")
        await self.send(f"Mianownik: {self.character.name_nom}.")
        await self.send(f"Dopełniacz: {self.character.name_gen}.")
        await self.send(f"Celownik: {self.character.name_dat}.")
        await self.send(f"Biernik: {self.character.name_acc}.")
        await self.send(f"Narzędnik: {self.character.name_ins}.")
        await self.send(f"Miejscownik: {self.character.name_loc}.")
        await self.send(f"Wołacz: {self.character.name_voc}.")

    async def show_stats(self):
        c = self.character
        active_classes = self.active_class_names()
        await self.send(
            f"{c.name}. Rasa: {c.race}. Klasa główna: {c.class_name}. "
            f"Aktywne klasy: {', '.join(active_classes)}."
        )
        await self.send("Poziom postaci: nie istnieje.")
        bonuses = self.equipment_bonus_totals()
        await self.send(
            f"Statystyki bazowe: Siła {c.strength}, Zręczność {c.dexterity}, "
            f"Kondycja {c.constitution}, Inteligencja {c.intelligence}, "
            f"Siła Woli {c.willpower}."
        )
        await self.send(
            f"Z wyposażeniem: Siła {self.effective_strength()}, "
            f"Zręczność {self.effective_dexterity()}, "
            f"Kondycja {self.effective_constitution()}, "
            f"Inteligencja {self.effective_intelligence()}, "
            f"Siła Woli {self.effective_willpower()}."
        )
        if any(bonuses.values()):
            await self.send(
                "Bonusy ekwipunku: "
                f"Siła +{bonuses['strength']}, "
                f"Zręczność +{bonuses['dexterity']}, "
                f"Kondycja +{bonuses['constitution']}, "
                f"Inteligencja +{bonuses['intelligence']}, "
                f"Siła Woli +{bonuses['willpower']}, "
                f"HP +{bonuses['hp']}, Mana +{bonuses['mana']}."
            )
        await self.send(f"Rozwój statystyk: {c.stat_progress} z {STAT_GROWTH_THRESHOLD}.")
        await self.send(
            f"Życie: {self.current_hp} z {self.max_hp()}. "
            f"Obrona fizyczna: {self.defense()}. "
            f"Obrona magiczna: {self.magic_defense()}."
        )
        await self.send(
            f"Siła ataku fizycznego: {self.physical_power()}. "
            f"Szybkość: {self.speed()}. "
            f"Unik: {int(self.dodge_chance() * 100)} procent. "
            f"Krytyk: {int(round(self.critical_chance() * 100))} procent. "
            f"Mnożnik krytyka: "
            f"{int(self.critical_multiplier() * 100)} procent."
        )
        await self.send(
            f"Pasyw rasy {c.race}: {c.racial_passive_text()}."
        )
        for class_name in active_classes:
            await self.send(
                f"Pasyw klasy {class_name}: "
                f"{c.class_passive_text_for(class_name)}."
            )
        await self.send(
            f"Bonus klasowy Broni Duszy klasy głównej: "
            f"{c.soul_weapon_class_bonus_text()}."
        )
        if self.max_mana() > 0:
            await self.send(
                f"Mana: {self.current_mana} z {self.max_mana()}. "
                f"Moc czarów: {self.spell_power()}."
            )
        await self.send(self.crypt_set_bonus_text())
        await self.send(
            f"Waluta: {c.silver} srebra, {c.gold} złota, {c.mithril} mithrilu. "
            f"Śmierci: {c.deaths}."
        )
        await self.send(
            f"Charyzma handlowa: {c.charisma}. "
            f"Rabat: {c.shop_discount_percent()} procent. "
            f"Limit drużyny jako lider: {c.party_capacity()}."
        )

    async def show_soul(self):
        c = self.character
        await self.send(f"Broń Duszy: {c.soul_weapon}.")
        await self.send(f"Soul Level: {c.soul_level} z {SOUL_MAX_LEVEL}. Tier: {c.soul_tier} z 3.")
        if c.soul_level < SOUL_MAX_LEVEL:
            await self.send(f"Soul XP: {c.soul_xp} z {c.soul_xp_to_next()}.")
        await self.send(f"Moc Broni Duszy: {c.soul_power()}.")
        await self.send(
            f"Bonus klasowy Broni Duszy: {c.soul_weapon_class_bonus_text()}."
        )
        nxt = c.can_unlock()
        if nxt:
            if self.soul_tier_quest_completed(nxt):
                await self.send(
                    f"Tier {nxt}: wymagany Soul Level i Próba Broni Duszy "
                    "ukończone. Wpisz unlock."
                )
            else:
                await self.send(
                    f"Tier {nxt}: wymagany Soul Level osiągnięty. "
                    "Idź do Kapłana Elora w Świątyni Odrodzenia "
                    "i ukończ Próbę Broni Duszy."
                )
        elif c.soul_tier == 1:
            await self.send(
                f"Tier 2 wymaga Soul Level {TIER2_LEVEL} oraz Próby "
                "Broni Duszy w Świątyni Odrodzenia."
            )
        elif c.soul_tier == 2:
            await self.send(
                f"Tier 3 wymaga Soul Level {TIER3_LEVEL} oraz Próby "
                "Broni Duszy w Świątyni Odrodzenia."
            )

    async def move(self, direction):
        if self.resting or self.rest_task:
            await self.stop_rest(
                announce=True, reason="ruszasz się"
            )
        if self.auto_fishing or self.auto_fishing_task:
            await self.stop_auto_fishing(announce=False)
            await self.send("Auto-łowienie wyłączone z powodu ruchu.")
        if self.auto_mining or self.auto_mining_task:
            await self.stop_auto_mining(announce=False)
            await self.send("Auto-kopanie wyłączone z powodu ruchu.")
        if self.auto_woodcutting or self.auto_woodcutting_task:
            await self.stop_auto_woodcutting(announce=False)
            await self.send("Auto-Drwalstwo wyłączone z powodu ruchu.")
        if self.auto_herbalism or self.auto_herbalism_task:
            await self.stop_auto_herbalism(announce=False)
            await self.send("Auto-Zielarstwo wyłączone z powodu ruchu.")
        if self.combat_mob_key:
            await self.send("Jesteś w walce. Najpierw użyj flee albo pokonaj przeciwnika.")
            return
        target = ROOMS[self.character.room_id]["exits"].get(direction)
        if not target:
            await self.send("Nie możesz iść w tym kierunku.")
            return
        if self.crypt_descent_blocked_for_player(
            self.character.room_id, direction
        ):
            boss = self.server.world.live_crypt_boss(
                self.character.room_id
            )
            boss_name = (
                MOB_TEMPLATES[boss.template_id]["name"]
                if boss else "boss Krypty"
            )
            await self.send(
                f"Nie możesz zejść niżej. Drogę blokuje {boss_name}. "
                "Najpierw pokonaj bossa."
            )
            return
        old = self.character.room_id
        await self.server.broadcast_room(old, f"{self.character.name} odchodzi.", exclude=self)
        self.character.room_id = target
        self.server.db.save_character(self.character)
        await self.server.broadcast_room(target, f"{self.character.name} przychodzi.", exclude=self)
        await self.look()

    def party_key(self):
        return self.server.party_key_for_account(self.account_id)

    async def show_party(self):
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            await self.send(
                f"Twój limit jako przyszłego lidera: "
                f"{self.character.party_capacity()} osób."
            )
            return

        leader = self.server.session_by_account(key)
        leader_name = leader.character.name if leader else f"konto {key}"
        capacity = (
            leader.character.party_capacity()
            if leader else PARTY_BASE_CAPACITY
        )
        members = sorted(
            self.server.party_sessions(self.account_id),
            key=lambda s: s.character.name.lower(),
        )
        await self.send(
            f"DRUŻYNA. Lider: {leader_name}. "
            f"Członkowie: {len(members)} z {capacity}."
        )
        for number, session in enumerate(members, 1):
            marker = " Lider." if session.account_id == key else ""
            await self.send(
                f"{number}. {session.character.name}. "
                f"Lokacja: {ROOMS[session.character.room_id]['name']}.{marker}"
            )

    async def leave_party(self, announce=True):
        key = self.party_key()
        if key is None:
            if announce:
                await self.send("Nie należysz do drużyny.")
            return False

        members = self.server.parties.get(key, set())
        members.discard(self.account_id)

        if self.account_id == key:
            if members:
                candidates = [
                    self.server.session_by_account(member_id)
                    for member_id in members
                ]
                candidates = [s for s in candidates if s]
                if candidates:
                    new_leader = sorted(
                        candidates,
                        key=lambda s: s.character.name.lower(),
                    )[0]
                    self.server.parties[new_leader.account_id] = set(members)
                    self.server.parties.pop(key, None)
                    await self.server.party_broadcast(
                        new_leader.account_id,
                        f"{new_leader.character.name} zostaje nowym liderem drużyny."
                    )
                else:
                    self.server.parties.pop(key, None)
            else:
                self.server.parties.pop(key, None)
        else:
            self.server.parties[key] = members
            await self.server.party_broadcast(
                key,
                f"{self.character.name} opuszcza drużynę.",
                exclude=self,
            )

        for target_id, leader_id in list(self.server.party_invites.items()):
            if target_id == self.account_id or leader_id == self.account_id:
                self.server.party_invites.pop(target_id, None)

        if announce:
            await self.send("Opuszczasz drużynę.")
        return True

    async def disband_party(self):
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            return
        if key != self.account_id:
            await self.send("Tylko lider może rozwiązać drużynę.")
            return

        members = list(self.server.parties.get(key, set()))
        for member_id in members:
            session = self.server.session_by_account(member_id)
            if session:
                await session.send(
                    "Drużyna została rozwiązana przez lidera."
                )
        self.server.parties.pop(key, None)
        for target_id, leader_id in list(self.server.party_invites.items()):
            if leader_id == key:
                self.server.party_invites.pop(target_id, None)

    async def party_invite(self, name):
        target = self.server.find_character_session(name.strip())
        if not target:
            await self.send("Ten gracz nie jest online.")
            return
        if target is self:
            await self.send("Nie możesz zaprosić samego siebie.")
            return
        if self.server.party_key_for_account(target.account_id) is not None:
            await self.send("Ten gracz już należy do drużyny.")
            return

        key = self.party_key()
        if key is None:
            key = self.account_id
            self.server.parties[key] = {self.account_id}
        elif key != self.account_id:
            await self.send("Tylko lider drużyny może zapraszać.")
            return

        capacity = self.character.party_capacity()
        if len(self.server.parties[key]) >= capacity:
            await self.send(
                f"Drużyna jest pełna. Limit lidera: {capacity} osób."
            )
            return

        self.server.party_invites[target.account_id] = key
        await target.send(
            f"{self.character.name} zaprasza cię do drużyny. "
            f"Wpisz druzyna dolacz albo druzyna odrzuc."
        )
        await self.send(
            f"Zapraszasz {target.character.name} do drużyny."
        )

    async def party_accept(self):
        leader_id = self.server.party_invites.get(self.account_id)
        if leader_id is None:
            await self.send("Nie masz aktywnego zaproszenia do drużyny.")
            return

        leader = self.server.session_by_account(leader_id)
        members = self.server.parties.get(leader_id)
        if not leader or members is None:
            self.server.party_invites.pop(self.account_id, None)
            await self.send("Ta drużyna nie jest już dostępna.")
            return
        if self.party_key() is not None:
            self.server.party_invites.pop(self.account_id, None)
            await self.send("Już należysz do drużyny.")
            return

        capacity = leader.character.party_capacity()
        if len(members) >= capacity:
            self.server.party_invites.pop(self.account_id, None)
            await self.send("Drużyna osiągnęła limit lidera.")
            return

        members.add(self.account_id)
        self.server.party_invites.pop(self.account_id, None)
        await self.server.party_broadcast(
            leader_id,
            f"{self.character.name} dołącza do drużyny."
        )

    async def party_decline(self):
        leader_id = self.server.party_invites.pop(self.account_id, None)
        if leader_id is None:
            await self.send("Nie masz aktywnego zaproszenia.")
            return
        leader = self.server.session_by_account(leader_id)
        if leader:
            await leader.send(
                f"{self.character.name} odrzuca zaproszenie do drużyny."
            )
        await self.send("Odrzucasz zaproszenie do drużyny.")

    async def party_kick(self, name):
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            return
        if key != self.account_id:
            await self.send("Tylko lider może wyrzucać członków.")
            return

        target = self.server.find_character_session(name.strip())
        if not target or target.account_id not in self.server.parties[key]:
            await self.send("Nie ma takiego członka w twojej drużynie.")
            return
        if target is self:
            await self.send(
                "Lider używa druzyna opusc albo druzyna rozwiaz."
            )
            return

        self.server.parties[key].discard(target.account_id)
        await target.send(
            f"{self.character.name} usuwa cię z drużyny."
        )
        await self.server.party_broadcast(
            key,
            f"{target.character.name} zostaje usunięty z drużyny.",
            exclude=target,
        )

    async def party_chat(self, message):
        if not message.strip():
            await self.send("Użycie: pc <tekst>.")
            return
        if self.party_key() is None:
            await self.send("Nie należysz do drużyny.")
            return
        await self.server.party_broadcast(
            self.account_id,
            f"[Drużyna] {self.character.name}: {message.strip()}"
        )

    async def handle_party(self, args):
        parts = args.strip().split(maxsplit=1)
        if not parts:
            await self.show_party()
            return

        action = self.normalize_description_query(parts[0])
        value = parts[1] if len(parts) > 1 else ""

        if action in ("status", "lista", "list", "sklad"):
            await self.show_party()
        elif action in ("zapros", "invite"):
            if not value:
                await self.send("Użycie: druzyna zapros <gracz>.")
            else:
                await self.party_invite(value)
        elif action in ("dolacz", "accept"):
            await self.party_accept()
        elif action in ("odrzuc", "decline"):
            await self.party_decline()
        elif action in ("opusc", "leave"):
            await self.leave_party(announce=True)
        elif action in ("wyrzuc", "kick"):
            if not value:
                await self.send("Użycie: druzyna wyrzuc <gracz>.")
            else:
                await self.party_kick(value)
        elif action in ("rozwiaz", "disband"):
            await self.disband_party()
        elif action in ("limit", "capacity"):
            key = self.party_key()
            leader = self.server.session_by_account(key) if key else self
            leader = leader or self
            await self.send(
                f"Limit drużyny: {leader.character.party_capacity()} osób. "
                f"Startowo 8; +1 miejsce co 25 Charyzmy lidera."
            )
        else:
            await self.send(
                "Drużyna: status, zapros <gracz>, dolacz, odrzuc, "
                "opusc, wyrzuc <gracz>, rozwiaz, limit. Czat: pc <tekst>."
            )

    async def who(self):
        players = sorted(
            [s.character.name for s in self.server.sessions if s.character], key=str.lower
        )
        await self.send(f"Gracze online: {len(players)}.")
        if players:
            await self.send(", ".join(players) + ".")

    async def say(self, text):
        if not text:
            await self.send("Użycie: say tekst")
            return
        await self.send(f"Mówisz: {text}")
        await self.server.broadcast_room(
            self.character.room_id, f"{self.character.name} mówi: {text}", exclude=self
        )

    async def tell(self, args):
        parts = args.split(maxsplit=1)
        if len(parts) != 2:
            await self.send("Użycie: tell gracz tekst")
            return
        target = self.server.find_character_session(parts[0])
        if not target:
            await self.send("Ten gracz nie jest online.")
            return
        await target.send(f"{self.character.name} mówi ci prywatnie: {parts[1]}")
        await self.send(f"Do {target.character.name}: {parts[1]}")

    def shop_item_base_value_silver(self, item):
        price = int(item.get("price") or 0)
        currency = item.get("currency", "gold")
        if currency == "silver":
            return price
        if currency == "gold":
            return price * SILVER_PER_GOLD
        if currency == "mithril":
            return price * GOLD_PER_MITHRIL * SILVER_PER_GOLD
        return 0

    def shop_cashback_silver(self, item):
        base = self.shop_item_base_value_silver(item)
        return (base * self.character.shop_discount_percent()) // 100

    async def show_charisma(self):
        c = self.character
        await self.send(f"Charyzma handlowa: {c.charisma}.")
        await self.send(
            f"Rabat sklepowy: {c.shop_discount_percent()} procent "
            f"z maksymalnych {CHARISMA_MAX_DISCOUNT} procent."
        )
        if c.shop_discount_percent() < CHARISMA_MAX_DISCOUNT:
            await self.send(
                f"Do następnego 1 procent rabatu: "
                f"{c.charisma_to_next_discount()} Charyzmy."
            )
        else:
            await self.send("Rabat sklepowy osiągnął maksimum.")
        await self.send(
            f"Limit drużyny jako lider: {c.party_capacity()} osób."
        )
        await self.send(
            f"Do następnego miejsca w drużynie: "
            f"{c.charisma_to_next_party_slot()} Charyzmy."
        )
        await self.send(
            "Każda udana sprzedaż surowca zwiększa Charyzmę o 1."
        )

    async def gain_charisma_from_sale(self):
        old_discount = self.character.shop_discount_percent()
        old_capacity = self.character.party_capacity()
        self.character.charisma += 1
        await self.send(
            f"Charyzma handlowa +1. Masz teraz {self.character.charisma}."
        )
        new_discount = self.character.shop_discount_percent()
        new_capacity = self.character.party_capacity()
        if new_discount > old_discount:
            await self.send(
                f"Nowy rabat sklepowy: {new_discount} procent."
            )
        if new_capacity > old_capacity:
            await self.send(
                f"Nowy limit drużyny jako lider: {new_capacity} osób."
            )

    async def show_money(self):
        c = self.character
        await self.send(
            f"Masz {c.silver} srebra, {c.gold} złota i {c.mithril} mithrilu."
        )

    async def exchange(self, target):
        target = target.strip().lower()
        if not target:
            await self.send(
                f"Kurs: {SILVER_PER_GOLD} srebra = 1 złoto; "
                f"{GOLD_PER_MITHRIL} złota = 1 mithril."
            )
            await self.send("Użycie: exchange gold albo exchange mithril.")
            return

        if target in ("gold", "złoto", "zloto"):
            if self.character.silver < SILVER_PER_GOLD:
                await self.send(f"Potrzebujesz {SILVER_PER_GOLD} srebra na 1 złoto.")
                return
            self.character.silver -= SILVER_PER_GOLD
            self.character.gold += 1
            self.server.db.save_character(self.character)
            await self.send(
                f"Wymieniasz {SILVER_PER_GOLD} srebra na 1 złoto."
            )
            return

        if target in ("mithril", "mithryl"):
            if self.character.gold < GOLD_PER_MITHRIL:
                await self.send(f"Potrzebujesz {GOLD_PER_MITHRIL} złota na 1 mithril.")
                return
            self.character.gold -= GOLD_PER_MITHRIL
            self.character.mithril += 1
            self.server.db.save_character(self.character)
            await self.send(
                f"Wymieniasz {GOLD_PER_MITHRIL} złota na 1 mithril."
            )
            return

        await self.send("Możesz wymieniać na: gold albo mithril.")

    def profession_xp_to_next(self, level):
        if level >= PROFESSION_MAX_LEVEL:
            return 0
        return 80 + (level - 1) * 35

    def tool_xp_to_next(self, level, tool_type=None):
        max_level = tool_max_level(tool_type)
        if level >= max_level:
            return 0
        return 60 + (level - 1) * 30

    def grant_profession_progress(self, profession, prof_xp, tool_type, tool_xp):
        prow = self.server.db.profession(self.account_id, profession)
        plevel = int(prow["level"])
        old_profession_rank = profession_rank(plevel)
        pxp = int(prow["xp"]) + prof_xp
        actions = int(prow["actions"]) + 1
        messages = [f"{profession}: +{prof_xp} XP."]

        while plevel < PROFESSION_MAX_LEVEL:
            needed = self.profession_xp_to_next(plevel)
            if pxp < needed:
                break
            pxp -= needed
            plevel += 1
            messages.append(f"{profession} osiąga poziom {plevel}.")
        if plevel >= PROFESSION_MAX_LEVEL:
            plevel = PROFESSION_MAX_LEVEL
            pxp = 0
        self.server.db.save_profession(
            self.account_id, profession, plevel, pxp, actions
        )

        new_profession_rank = profession_rank(plevel)
        if new_profession_rank > old_profession_rank:
            messages.append(
                f"{profession}: awansujesz na Rangę {new_profession_rank} "
                f"z {PROFESSION_MAX_RANK}: "
                f"{profession_rank_name(profession, plevel)}."
            )

        trow = self.server.db.tool(self.account_id, tool_type)
        tlevel = int(trow["level"])
        old_tool_tier = tool_tier(tlevel)
        txp = int(trow["xp"]) + tool_xp
        uses = int(trow["uses"]) + 1
        tool_name = {
            "fishing": "Wędka",
            "mining": "Kilof",
            "woodcutting": "Piła",
            "crafting": "Młot Rzemieślniczy",
            "cooking": "Nóż Kucharski",
            "herbalism": "Sierp Zielarski",
            "alchemy": "Moździerz Alchemiczny",
        }.get(tool_type, tool_type)
        messages.append(f"{tool_name}: +{tool_xp} XP narzędzia.")

        tool_level_cap = tool_max_level(tool_type)
        while tlevel < tool_level_cap:
            needed = self.tool_xp_to_next(tlevel, tool_type)
            if txp < needed:
                break
            txp -= needed
            tlevel += 1
            messages.append(f"{tool_name} osiąga level {tlevel}.")
        if tlevel >= tool_level_cap:
            tlevel = tool_level_cap
            txp = 0
        self.server.db.save_tool(
            self.account_id, tool_type, tlevel, txp, uses
        )

        new_tool_tier = tool_tier(tlevel)
        if new_tool_tier > old_tool_tier:
            messages.append(
                f"{tool_name} awansuje na Tier {new_tool_tier} z {TOOL_MAX_TIER}: "
                f"{tool_tier_name(tool_type, tlevel)}. "
                f"Szansa na dodatkowy urobek: "
                f"{int(tool_tier_bonus_chance(tlevel) * 100)} procent."
            )

        return messages, plevel, tlevel

    def grant_tool_progress(self, tool_type, tool_xp):
        row = self.server.db.tool(self.account_id, tool_type)
        level = int(row["level"])
        old_tier = tool_tier(level)
        xp = int(row["xp"]) + max(0, int(tool_xp))
        uses = int(row["uses"]) + 1

        tool_name = {
            "fishing": "Wędka",
            "mining": "Kilof",
            "woodcutting": "Piła",
            "crafting": "Młot Rzemieślniczy",
            "cooking": "Nóż Kucharski",
            "herbalism": "Sierp Zielarski",
            "alchemy": "Moździerz Alchemiczny",
        }.get(tool_type, tool_type)

        messages = [f"{tool_name}: +{tool_xp} XP narzędzia."]

        tool_level_cap = tool_max_level(tool_type)
        while level < tool_level_cap:
            needed = self.tool_xp_to_next(level, tool_type)
            if xp < needed:
                break
            xp -= needed
            level += 1
            messages.append(f"{tool_name} osiąga level {level}.")

        if level >= tool_level_cap:
            level = tool_level_cap
            xp = 0

        self.server.db.save_tool(
            self.account_id, tool_type, level, xp, uses
        )

        new_tier = tool_tier(level)
        if new_tier > old_tier:
            if tool_type == "cooking":
                bonus_name = "dodatkową potrawę"
            elif tool_type == "crafting":
                bonus_name = "dodatkowy produkt receptury"
            else:
                bonus_name = "dodatkowy urobek"
            messages.append(
                f"{tool_name} awansuje na Tier {new_tier} z {TOOL_MAX_TIER}: "
                f"{tool_tier_name(tool_type, level)}. "
                f"Szansa na {bonus_name}: "
                f"{int(tool_tier_bonus_chance(level) * 100)} procent."
            )

        return messages, level

    def store_profession_resource(self, item_id, quantity=1):
        quantity = max(1, int(quantity))
        if item_id in FISH_RESOURCE_IDS:
            self.server.db.add_storage_item(
                self.account_id, "net", item_id, quantity
            )
            return "net"
        if item_id in ORE_RESOURCE_IDS:
            self.server.db.add_storage_item(
                self.account_id, "bag", item_id, quantity
            )
            return "bag"
        if item_id in WOOD_RESOURCE_IDS:
            self.server.db.add_storage_item(
                self.account_id, "woodpile", item_id, quantity
            )
            return "woodpile"
        if item_id in HERB_RESOURCE_IDS:
            self.server.db.add_storage_item(
                self.account_id, "herbbag", item_id, quantity
            )
            return "herbbag"
        raise ValueError(
            f"Przedmiot {item_id} nie jest surowcem obsługiwanej profesji."
        )

    def container_label(self, container):
        return {
            "net": "Siatka na ryby",
            "bag": "Sakwa górnicza",
            "woodpile": "Stos drewna",
            "herbbag": "Torba Zielarska",
        }.get(container, container)

    def normalize_container(self, token):
        t = token.strip().lower()
        if t in ("net", "siatka", "siatkę", "siatke"):
            return "net"
        if t in ("bag", "sakwa", "sakwe", "sakwę", "worek"):
            return "bag"
        if t in ("woodpile", "stos", "drewno", "sterta"):
            return "woodpile"
        if t in ("herbbag", "ziola", "zioła", "herbs", "torba"):
            return "herbbag"
        return None

    def category_ids(self, query, container=None):
        q = query.strip().lower()
        if q in ("fish", "ryba", "ryby"):
            return set(FISH_RESOURCE_IDS)
        if q in ("ore", "ruda", "rudy"):
            return set(ORE_RESOURCE_IDS)
        if q in ("wood", "drewno", "pnie", "pień", "pien"):
            return set(WOOD_RESOURCE_IDS)
        if q in ("herb", "herbs", "ziolo", "zioło", "ziola", "zioła"):
            return set(HERB_RESOURCE_IDS)
        if container == "net":
            allowed = FISH_RESOURCE_IDS
        elif container == "bag":
            allowed = ORE_RESOURCE_IDS
        elif container == "woodpile":
            allowed = WOOD_RESOURCE_IDS
        elif container == "herbbag":
            allowed = HERB_RESOURCE_IDS
        else:
            allowed = FISH_RESOURCE_IDS | ORE_RESOURCE_IDS | WOOD_RESOURCE_IDS | HERB_RESOURCE_IDS

        found = find_by_name(
            {item_id: ITEMS[item_id] for item_id in allowed},
            query
        )
        return {found[0]} if found else set()

    async def show_container(self, container):
        label = self.container_label(container)
        rows = self.server.db.storage_rows(self.account_id, container)
        await self.send(label + ":")
        if not rows:
            await self.send("Pusto.")
            return
        for row in rows:
            item = ITEMS.get(row["item_id"], {"name": row["item_id"]})
            await self.send(f"{item['name']} x{row['quantity']}.")

    async def put_in_container(self, args):
        # Przykłady:
        # wloz ryba siatka
        # put fish net
        # wloz ruda sakwa
        parts = args.split()
        if len(parts) < 2:
            await self.send(
                "Użycie: wloz ryba siatka / put fish net / "
                "wloz ruda sakwa / put ore bag."
            )
            return

        container = self.normalize_container(parts[-1])
        if not container:
            await self.send("Podaj na końcu: siatka/net, sakwa/bag, stos/woodpile albo ziola/herbbag.")
            return

        query = " ".join(parts[:-1])
        ids = self.category_ids(query, container)
        if not ids:
            await self.send("Nie rozpoznaję takiego surowca.")
            return

        expected = {
            "net": FISH_RESOURCE_IDS,
            "bag": ORE_RESOURCE_IDS,
            "woodpile": WOOD_RESOURCE_IDS,
            "herbbag": HERB_RESOURCE_IDS,
        }[container]
        ids &= expected
        if not ids:
            await self.send(
                "Do Siatki wkłada się ryby, do Sakwy rudy, na Stos drewno, a do Torby Zielarskiej zioła."
            )
            return

        moved = []
        for item_id in sorted(ids):
            qty = self.server.db.item_qty(self.account_id, item_id)
            if qty <= 0:
                continue
            self.server.db.remove_item(self.account_id, item_id, qty)
            self.server.db.add_storage_item(
                self.account_id, container, item_id, qty
            )
            moved.append((item_id, qty))

        if not moved:
            await self.send("Nie masz takich surowców w zwykłym ekwipunku.")
            return

        for item_id, qty in moved:
            await self.send(
                f"Wkładasz {ITEMS[item_id]['name']} x{qty} do "
                f"{self.container_label(container)}."
            )

    async def take_from_container(self, args):
        parts = args.split()
        if len(parts) < 2:
            await self.send(
                "Użycie: wyjmij przedmiot siatka/sakwa/stos albo take item net/bag/woodpile."
            )
            return

        container = self.normalize_container(parts[-1])
        if not container:
            await self.send("Podaj na końcu: siatka/net, sakwa/bag, stos/woodpile albo ziola/herbbag.")
            return

        query = " ".join(parts[:-1])
        ids = self.category_ids(query, container)
        if not ids:
            await self.send("Nie rozpoznaję takiego surowca.")
            return

        moved = []
        for item_id in sorted(ids):
            qty = self.server.db.storage_qty(
                self.account_id, container, item_id
            )
            if qty <= 0:
                continue
            self.server.db.remove_storage_item(
                self.account_id, container, item_id, qty
            )
            self.server.db.add_item(self.account_id, item_id, qty)
            moved.append((item_id, qty))

        if not moved:
            await self.send("Nie ma tego surowca w tym pojemniku.")
            return

        for item_id, qty in moved:
            await self.send(
                f"Wyjmujesz {ITEMS[item_id]['name']} x{qty} z "
                f"{self.container_label(container)}."
            )

    async def grant_profession_reward_xp(self, profession, profession_xp, tool_type, tool_xp):
        prow = self.server.db.profession(self.account_id, profession)
        plevel = int(prow["level"])
        pxp = int(prow["xp"]) + profession_xp
        actions = int(prow["actions"])

        await self.send(f"{profession}: nagroda +{profession_xp} XP.")

        while plevel < PROFESSION_MAX_LEVEL:
            needed = self.profession_xp_to_next(plevel)
            if pxp < needed:
                break
            pxp -= needed
            plevel += 1
            await self.send(f"{profession} osiąga poziom {plevel}.")

        if plevel >= PROFESSION_MAX_LEVEL:
            plevel = PROFESSION_MAX_LEVEL
            pxp = 0

        self.server.db.save_profession(
            self.account_id, profession, plevel, pxp, actions
        )

        trow = self.server.db.tool(self.account_id, tool_type)
        tlevel = int(trow["level"])
        txp = int(trow["xp"]) + tool_xp
        uses = int(trow["uses"])
        tool_name = "Wędka" if tool_type == "fishing" else "Kilof"

        await self.send(f"{tool_name}: nagroda +{tool_xp} XP.")

        tool_level_cap = tool_max_level(tool_type)
        while tlevel < tool_level_cap:
            needed = self.tool_xp_to_next(tlevel, tool_type)
            if txp < needed:
                break
            txp -= needed
            tlevel += 1
            await self.send(f"{tool_name} osiąga level {tlevel}.")

        if tlevel >= tool_level_cap:
            tlevel = tool_level_cap
            txp = 0

        self.server.db.save_tool(
            self.account_id, tool_type, tlevel, txp, uses
        )

    async def show_location(self):
        room = ROOMS[self.character.room_id]
        await self.send(
            f"Lokalizacja: {room['name']}. Strefa: {room['zone']}."
        )
        await self.show_exits()

    def normalize_room_query(self, value):
        text = str(value or "").strip().lower()
        text = text.replace("ł", "l").replace("Ł", "l")
        text = unicodedata.normalize("NFKD", text)
        text = "".join(
            ch for ch in text
            if not unicodedata.combining(ch)
        )
        text = text.replace("_", " ").replace("-", " ")
        text = re.sub(r"[^a-z0-9 ]+", " ", text)
        return " ".join(text.split())

    def room_search_aliases(self, room_id, room):
        aliases = {
            self.normalize_room_query(room_id),
            self.normalize_room_query(room_id.replace("_", " ")),
            self.normalize_room_query(room["name"]),
        }

        zone = self.normalize_room_query(room.get("zone", ""))
        name = self.normalize_room_query(room["name"])
        if zone and name:
            aliases.add(f"{zone} {name}")

        floor = crypt_floor_number(room_id)
        if floor:
            aliases.update({
                f"krypta {floor}",
                f"crypt {floor}",
                f"pietro {floor}",
                f"pietro krypty {floor}",
                f"krypta pietro {floor}",
                f"crypt floor {floor}",
            })

        # Krótkie, naturalne warianty popularnych nazw.
        words = name.split()
        if len(words) > 1:
            aliases.add(" ".join(words[1:]))

        return {alias for alias in aliases if alias}

    def find_room_matches(self, query):
        q = self.normalize_room_query(query)
        if not q:
            return []

        # Krypta 1-100 ma specjalne naturalne skróty.
        crypt_match = re.fullmatch(
            r"(?:krypta|crypt|pietro|pietro krypty|krypta pietro|crypt floor)\s*(\d+)",
            q,
        )
        if crypt_match:
            floor = int(crypt_match.group(1))
            if 1 <= floor <= CRYPT_MAX_FLOOR:
                return [crypt_floor_id(floor)]
            return []

        exact = []
        partial = []

        for room_id, room in ROOMS.items():
            aliases = self.room_search_aliases(room_id, room)
            if q in aliases:
                exact.append(room_id)
                continue
            if any(q in alias for alias in aliases):
                partial.append(room_id)

        if exact:
            return sorted(
                set(exact),
                key=lambda rid: ROOMS[rid]["name"].lower(),
            )

        return sorted(
            set(partial),
            key=lambda rid: ROOMS[rid]["name"].lower(),
        )

    def find_room(self, query):
        matches = self.find_room_matches(query)
        return matches[0] if len(matches) == 1 else None

    async def show_guide_destinations(self):
        await self.send("CELE PROWADZENIA")
        await self.send(
            f"Dostępne są wszystkie lokacje świata: {len(ROOMS)} celów."
        )

        zones = {}
        for room_id, room in ROOMS.items():
            if room_id.startswith("crypt_floor_"):
                continue
            zones.setdefault(room["zone"], []).append(room["name"])

        for zone in sorted(zones):
            names = sorted(set(zones[zone]), key=str.lower)
            await self.send(
                f"{zone}: " + "; ".join(names) + "."
            )

        await self.send(
            "Krypta: wszystkie piętra od 1 do 100. "
            "Przykłady: prowadz krypta 1, prowadz krypta 37, "
            "prowadz krypta 100."
        )
        await self.send(
            "Możesz używać pełnej nazwy, identyfikatora lokacji ze spacjami "
            "albo wersji bez polskich znaków."
        )


    def shortest_path(self, start_room, target_room):
        if start_room == target_room:
            return []

        queue = [(start_room, [])]
        visited = {start_room}

        while queue:
            room_id, path = queue.pop(0)
            for direction, next_room in ROOMS[room_id]["exits"].items():
                if next_room in visited:
                    continue
                new_path = path + [(direction, next_room)]
                if next_room == target_room:
                    return new_path
                visited.add(next_room)
                queue.append((next_room, new_path))
        return None

    async def stop_auto_fishing(self, announce=True):
        self.auto_fishing = False
        task = self.auto_fishing_task
        self.auto_fishing_task = None

        if task and task is not asyncio.current_task() and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        if announce:
            await self.send("Auto-łowienie wyłączone.")

    async def auto_fishing_loop(self):
        try:
            while self.auto_fishing and not self.closed:
                if self.combat_mob_key:
                    await self.send("Auto-łowienie zatrzymane: rozpoczęła się walka.")
                    self.auto_fishing = False
                    break

                if self.character.room_id not in FISHING_ROOMS:
                    await self.send("Auto-łowienie zatrzymane: opuściłeś łowisko.")
                    self.auto_fishing = False
                    break

                if self.server.db.item_qty(self.account_id, "fishing_rod") <= 0:
                    await self.send("Auto-łowienie zatrzymane: nie masz Wędki.")
                    self.auto_fishing = False
                    break

                await self.fish(from_auto=True)

                # PROFESSION_COOLDOWN wynosi 2 sekundy; dodajemy margines,
                # żeby auto-łowienie nie generowało komunikatów o cooldownie.
                await asyncio.sleep(PROFESSION_COOLDOWN + 0.35)

        except asyncio.CancelledError:
            pass
        finally:
            self.auto_fishing = False
            if self.auto_fishing_task is asyncio.current_task():
                self.auto_fishing_task = None

    async def set_auto_fishing(self, enabled):
        if enabled:
            if self.auto_fishing:
                await self.send("Auto-łowienie jest już włączone.")
                return
            if self.combat_mob_key:
                await self.send("Nie możesz rozpocząć auto-łowienia podczas walki.")
                return
            if self.character.room_id not in FISHING_ROOMS:
                await self.send("Tutaj nie ma odpowiedniego łowiska.")
                return
            if self.server.db.item_qty(self.account_id, "fishing_rod") <= 0:
                await self.send("Do auto-łowienia potrzebujesz Wędki.")
                return

            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
                await self.send("Auto-kopanie wyłączone.")
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
                await self.send("Auto-Drwalstwo wyłączone.")
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)
                await self.send("Auto-Zielarstwo wyłączone.")

            self.auto_fishing = True
            self.auto_fishing_task = asyncio.create_task(
                self.auto_fishing_loop()
            )
            await self.send(
                "Auto-łowienie włączone. Wpisz low off albo fish off, aby je zatrzymać."
            )
            return

        if not self.auto_fishing and not self.auto_fishing_task:
            await self.send("Auto-łowienie jest już wyłączone.")
            return
        await self.stop_auto_fishing(announce=True)

    async def guide_to(self, query):
        q = query.strip()
        if q.lower().startswith("to "):
            q = q[3:].strip()

        if self.normalize_room_query(q) in (
            "lista", "list", "cele", "destinations", "lokacje", "locations"
        ):
            await self.show_guide_destinations()
            return

        if not q:
            await self.send(
                "Użycie: prowadz <lokacja>. "
                "Wpisz prowadz lista, aby usłyszeć wszystkie cele."
            )
            return

        if self.combat_mob_key:
            await self.send("Nie możesz użyć prowadzenia podczas walki.")
            return

        matches = self.find_room_matches(q)
        if not matches:
            await self.send(
                "Nie rozpoznaję tej lokacji. "
                "Wpisz prowadz lista, aby usłyszeć wszystkie cele."
            )
            return

        if len(matches) > 1:
            names = "; ".join(ROOMS[rid]["name"] for rid in matches[:12])
            extra = (
                f" oraz jeszcze {len(matches) - 12}"
                if len(matches) > 12 else ""
            )
            await self.send(
                f"Nazwa pasuje do kilku lokacji: {names}{extra}. "
                "Podaj pełniejszą nazwę."
            )
            return

        target = matches[0]

        if target == self.character.room_id:
            await self.send(f"Już jesteś tutaj: {ROOMS[target]['name']}.")
            return

        path = self.shortest_path(self.character.room_id, target)
        if path is None:
            await self.send("Nie udało się znaleźć drogi do tej lokacji.")
            return

        if self.auto_fishing or self.auto_fishing_task:
            await self.stop_auto_fishing(announce=False)
            await self.send("Auto-łowienie wyłączone z powodu rozpoczęcia podróży.")
        if self.auto_mining or self.auto_mining_task:
            await self.stop_auto_mining(announce=False)
            await self.send("Auto-kopanie wyłączone z powodu rozpoczęcia podróży.")
        if self.auto_woodcutting or self.auto_woodcutting_task:
            await self.stop_auto_woodcutting(announce=False)
            await self.send("Auto-Drwalstwo wyłączone z powodu rozpoczęcia podróży.")
        if self.auto_herbalism or self.auto_herbalism_task:
            await self.stop_auto_herbalism(announce=False)
            await self.send("Auto-Zielarstwo wyłączone z powodu rozpoczęcia podróży.")

        self.guiding = True
        await self.send(
            f"Prowadzę do: {ROOMS[target]['name']}. "
            f"Liczba przejść: {len(path)}."
        )

        try:
            for direction, next_room in path:
                if self.closed:
                    break
                if self.combat_mob_key:
                    await self.send("Prowadzenie przerwane przez walkę.")
                    break

                old = self.character.room_id
                if self.crypt_descent_blocked_for_player(old, direction):
                    boss = self.server.world.live_crypt_boss(old)
                    boss_name = (
                        MOB_TEMPLATES[boss.template_id]["name"]
                        if boss else "boss Krypty"
                    )
                    await self.send(
                        f"Prowadzenie zatrzymane. Zejście niżej blokuje "
                        f"{boss_name}. Pokonaj bossa."
                    )
                    break
                await self.server.broadcast_room(
                    old, f"{self.character.name} odchodzi.", exclude=self
                )
                self.character.room_id = next_room
                self.server.db.save_character(self.character)
                await self.server.broadcast_room(
                    next_room, f"{self.character.name} przychodzi.", exclude=self
                )
                await self.send(
                    f"{direction}: {ROOMS[next_room]['name']}."
                )
                await asyncio.sleep(0.12)

            if self.character.room_id == target:
                await self.send(f"Dotarłeś do: {ROOMS[target]['name']}.")
                await self.look()
        finally:
            self.guiding = False

    async def stop_auto_mining(self, announce=True):
        self.auto_mining = False
        task = self.auto_mining_task
        self.auto_mining_task = None

        if task and task is not asyncio.current_task() and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        if announce:
            await self.send("Auto-kopanie wyłączone.")

    async def auto_mining_loop(self):
        try:
            while self.auto_mining and not self.closed:
                if self.combat_mob_key:
                    await self.send("Auto-kopanie zatrzymane: rozpoczęła się walka.")
                    self.auto_mining = False
                    break

                if self.character.room_id not in MINING_ROOMS:
                    await self.send("Auto-kopanie zatrzymane: opuściłeś kopalnię.")
                    self.auto_mining = False
                    break

                if self.server.db.item_qty(self.account_id, "pickaxe") <= 0:
                    await self.send("Auto-kopanie zatrzymane: nie masz Kilofa.")
                    self.auto_mining = False
                    break

                await self.mine(from_auto=True)
                await asyncio.sleep(PROFESSION_COOLDOWN + 0.35)

        except asyncio.CancelledError:
            pass
        finally:
            self.auto_mining = False
            if self.auto_mining_task is asyncio.current_task():
                self.auto_mining_task = None

    async def set_auto_mining(self, enabled):
        if enabled:
            if self.auto_mining:
                await self.send("Auto-kopanie jest już włączone.")
                return
            if self.combat_mob_key:
                await self.send("Nie możesz rozpocząć auto-kopania podczas walki.")
                return
            if self.character.room_id not in MINING_ROOMS:
                await self.send("Tutaj nie ma odpowiedniego złoża.")
                return
            if self.server.db.item_qty(self.account_id, "pickaxe") <= 0:
                await self.send("Do auto-kopania potrzebujesz Kilofa.")
                return

            # Auto fishing i auto mining nie mogą działać jednocześnie.
            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
                await self.send("Auto-łowienie wyłączone.")
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
                await self.send("Auto-Drwalstwo wyłączone.")
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)
                await self.send("Auto-Zielarstwo wyłączone.")

            self.auto_mining = True
            self.auto_mining_task = asyncio.create_task(
                self.auto_mining_loop()
            )
            await self.send(
                "Auto-kopanie włączone. Wpisz kop off albo mine off, aby je zatrzymać."
            )
            return

        if not self.auto_mining and not self.auto_mining_task:
            await self.send("Auto-kopanie jest już wyłączone.")
            return

        await self.stop_auto_mining(announce=True)

    async def stop_auto_woodcutting(self, announce=True):
        self.auto_woodcutting = False
        task = self.auto_woodcutting_task
        self.auto_woodcutting_task = None
        if task and task is not asyncio.current_task() and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        if announce:
            await self.send("Auto-Drwalstwo wyłączone.")

    async def auto_woodcutting_loop(self):
        try:
            while self.auto_woodcutting and not self.closed:
                if self.combat_mob_key:
                    await self.send("Auto-Drwalstwo zatrzymane: rozpoczęła się walka.")
                    break
                if self.character.room_id not in WOODCUTTING_ROOMS:
                    await self.send("Auto-Drwalstwo zatrzymane: opuściłeś obszar drzew.")
                    break
                if self.server.db.item_qty(self.account_id, "saw") <= 0:
                    await self.send("Auto-Drwalstwo zatrzymane: nie masz Piły.")
                    break
                await self.woodcut(from_auto=True)
                await asyncio.sleep(PROFESSION_COOLDOWN + 0.35)
        except asyncio.CancelledError:
            pass
        finally:
            self.auto_woodcutting = False
            if self.auto_woodcutting_task is asyncio.current_task():
                self.auto_woodcutting_task = None

    async def set_auto_woodcutting(self, enabled):
        if enabled:
            if self.auto_woodcutting:
                await self.send("Auto-Drwalstwo jest już włączone.")
                return
            if self.combat_mob_key:
                await self.send("Nie możesz rozpocząć auto-Drwalstwa podczas walki.")
                return
            if self.character.room_id not in WOODCUTTING_ROOMS:
                await self.send("Tutaj nie ma odpowiednich drzew.")
                return
            if self.server.db.item_qty(self.account_id, "saw") <= 0:
                await self.send("Do auto-Drwalstwa potrzebujesz Piły od Drwala Brana.")
                return
            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)
            self.auto_woodcutting = True
            self.auto_woodcutting_task = asyncio.create_task(self.auto_woodcutting_loop())
            await self.send("Auto-Drwalstwo włączone. Wpisz tnij off albo woodcut off, aby je zatrzymać.")
            return

        if not self.auto_woodcutting and not self.auto_woodcutting_task:
            await self.send("Auto-Drwalstwo jest już wyłączone.")
            return
        await self.stop_auto_woodcutting(announce=True)

    async def stop_auto_herbalism(self, announce=True):
        self.auto_herbalism = False
        task = self.auto_herbalism_task
        self.auto_herbalism_task = None
        if task and task is not asyncio.current_task() and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        if announce:
            await self.send("Auto-Zielarstwo wyłączone.")

    async def auto_herbalism_loop(self):
        try:
            while self.auto_herbalism and not self.closed:
                if self.combat_mob_key:
                    await self.send("Auto-Zielarstwo zatrzymane: rozpoczęła się walka.")
                    break
                if self.character.room_id not in HERBALISM_ROOMS:
                    await self.send("Auto-Zielarstwo zatrzymane: opuściłeś obszar ziół.")
                    break
                if self.server.db.item_qty(self.account_id, "herbalist_sickle") <= 0:
                    await self.send("Auto-Zielarstwo zatrzymane: nie masz Sierpa Zielarskiego.")
                    break
                await self.gather_herb(from_auto=True)
                await asyncio.sleep(PROFESSION_COOLDOWN + 0.35)
        except asyncio.CancelledError:
            pass
        finally:
            self.auto_herbalism = False
            if self.auto_herbalism_task is asyncio.current_task():
                self.auto_herbalism_task = None

    async def set_auto_herbalism(self, enabled):
        if enabled:
            if self.auto_herbalism:
                await self.send("Auto-Zielarstwo jest już włączone.")
                return
            if self.combat_mob_key:
                await self.send("Nie możesz rozpocząć auto-Zielarstwa podczas walki.")
                return
            if self.character.room_id not in HERBALISM_ROOMS:
                await self.send("Tutaj nie ma odpowiednich ziół.")
                return
            if self.server.db.item_qty(self.account_id, "herbalist_sickle") <= 0:
                await self.send("Do auto-Zielarstwa potrzebujesz Sierpa Zielarskiego.")
                return
            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
            self.auto_herbalism = True
            self.auto_herbalism_task = asyncio.create_task(self.auto_herbalism_loop())
            await self.send("Auto-Zielarstwo włączone. Wpisz zbieraj off, aby je zatrzymać.")
            return
        if not self.auto_herbalism and not self.auto_herbalism_task:
            await self.send("Auto-Zielarstwo jest już wyłączone.")
            return
        await self.stop_auto_herbalism(announce=True)

    async def show_profession_ranks(self):
        for profession in ("Wędkarstwo", "Górnictwo", "Drwalstwo", "Zielarstwo", "Alchemia"):
            await self.send(f"RANGI: {profession.upper()}")
            for rank, minimum in enumerate(PROFESSION_RANK_THRESHOLDS, 1):
                if rank < PROFESSION_MAX_RANK:
                    maximum = PROFESSION_RANK_THRESHOLDS[rank] - 1
                    level_text = f"level {minimum}-{maximum}"
                else:
                    if tool_type == "crafting":
                        level_text = (
                            f"level {minimum}-{TOOL_MAX_LEVEL}"
                        )
                    else:
                        level_text = f"level {minimum}-{TOOL_MAX_LEVEL}"
                await self.send(
                    f"Ranga {rank}: {PROFESSION_RANK_NAMES[profession][rank - 1]}. "
                    f"{level_text}."
                )


    async def show_professions(self):
        await self.send("PROFESJE")
        for name in ("Wędkarstwo", "Górnictwo", "Drwalstwo", "Zielarstwo", "Alchemia"):
            row = self.server.db.profession(self.account_id, name)
            level = int(row["level"])
            rank = profession_rank(level)
            rank_name = profession_rank_name(name, level)
            if rank < PROFESSION_MAX_RANK:
                next_text = f"Następna ranga {rank + 1} od levelu {PROFESSION_RANK_THRESHOLDS[rank]}."
            else:
                next_text = "Ranga maksymalna."
            xp_text = "maksimum" if level >= PROFESSION_MAX_LEVEL else f"{row['xp']} z {self.profession_xp_to_next(level)}"
            await self.send(
                f"{name}: level {level} z {PROFESSION_MAX_LEVEL}. "
                f"Ranga {rank} z {PROFESSION_MAX_RANK}: {rank_name}. "
                f"XP: {xp_text}. Akcje: {row['actions']}. {next_text}"
            )


    async def show_tool_tiers(self):
        for tool_type, title in (
            ("fishing", "WĘDKI"),
            ("mining", "KILOFA"),
            ("woodcutting", "PIŁY"),
            ("crafting", "MŁOTA RZEMIEŚLNICZEGO"),
            ("cooking", "NOŻA KUCHARSKIEGO"),
            ("herbalism", "SIERPA ZIELARSKIEGO"),
            ("alchemy", "MOŹDZIERZA ALCHEMICZNEGO"),
        ):
            await self.send(f"NAZWY TIERÓW {title}")
            for tier, minimum in enumerate(TOOL_TIER_THRESHOLDS, 1):
                if tier < TOOL_MAX_TIER:
                    maximum = TOOL_TIER_THRESHOLDS[tier] - 1
                    level_text = f"level {minimum}-{maximum}"
                else:
                    level_text = f"level {minimum}"
                bonus = int(TOOL_TIER_BONUS_CHANCES[tier - 1] * 100)
                await self.send(
                    f"Tier {tier}: {TOOL_TIER_NAMES[tool_type][tier - 1]}. "
                    f"{level_text}. Bonus {bonus} procent."
                )


    def tool_info_definition(self, tool_type):
        definitions = {
            "fishing": ("fishing_rod", "Wędka"),
            "mining": ("pickaxe", "Kilof"),
            "woodcutting": ("saw", "Piła"),
            "crafting": ("crafting_hammer", "Młot Rzemieślniczy"),
            "cooking": ("chef_knife", "Nóż Kucharski"),
            "herbalism": ("herbalist_sickle", "Sierp Zielarski"),
            "alchemy": ("alchemy_mortar", "Moździerz Alchemiczny"),
        }
        return definitions.get(tool_type)

    def tool_bonus_label(self, tool_type):
        if tool_type == "cooking":
            return "Szansa na dodatkową potrawę"
        if tool_type == "crafting":
            return "Szansa na dodatkowy produkt receptury"
        if tool_type == "alchemy":
            return "Szansa na dodatkową miksturę"
        if tool_type == "herbalism":
            return "Szansa na dodatkowe zioło"
        return "Bonus dodatkowego urobku"

    def tool_xp_remaining_to_level(self, level, xp, tool_type=None):
        max_level = tool_max_level(tool_type)
        if level >= max_level:
            return 0
        return max(
            0,
            self.tool_xp_to_next(level, tool_type) - int(xp),
        )

    def tool_xp_remaining_to_next_tier(self, level, xp, tool_type=None):
        tier = tool_tier(level)
        if tier >= TOOL_MAX_TIER:
            return 0, 0

        target_level = TOOL_TIER_THRESHOLDS[tier]
        levels_remaining = max(0, target_level - level)

        total_xp = self.tool_xp_remaining_to_level(level, xp, tool_type)
        for current_level in range(level + 1, target_level):
            total_xp += self.tool_xp_to_next(current_level, tool_type)

        return levels_remaining, total_xp

    async def show_single_tool(self, tool_type):
        definition = self.tool_info_definition(tool_type)
        if not definition:
            await self.send("Nieznane narzędzie.")
            return

        item_id, name = definition
        owned = self.server.db.item_qty(self.account_id, item_id) > 0
        if not owned:
            await self.send(f"{name}: nie posiadasz tego narzędzia.")
            if tool_type == "fishing":
                await self.send("Wędkę kupisz na Targu Rybnym.")
            elif tool_type == "mining":
                await self.send("Kilof kupisz u Kowala Dorana w Kuźni Dusz.")
            elif tool_type == "woodcutting":
                await self.send("Piłę kupisz u Drwala Brana w Obozie Drwala.")
            elif tool_type == "crafting":
                await self.send("Młot Rzemieślniczy kupisz u Kowala Dorana w Kuźni Dusz.")
            elif tool_type == "cooking":
                await self.send("Nóż Kucharski kupisz w Karczmie Pod Błękitnym Płomieniem.")
            elif tool_type in ("herbalism", "alchemy"):
                await self.send(
                    f"{name} kupisz u Zielarki Liory w Chacie Zielarki."
                )
            return

        row = self.server.db.tool(self.account_id, tool_type)
        level = int(row["level"])
        xp = int(row["xp"])
        uses = int(row["uses"])
        tier = tool_tier(level)
        max_level = tool_max_level(tool_type)
        tier_name = tool_tier_name(tool_type, level)
        bonus_percent = int(tool_tier_bonus_chance(level) * 100)
        bonus_label = self.tool_bonus_label(tool_type)

        await self.send(f"NARZĘDZIE: {name}.")
        await self.send(
            f"Level: {level} z {max_level}. "
            f"Użycia: {uses}."
        )

        if level >= max_level:
            await self.send("XP: maksimum. Do następnego levelu: maksimum.")
        else:
            needed = self.tool_xp_to_next(level, tool_type)
            remaining = self.tool_xp_remaining_to_level(level, xp, tool_type)
            await self.send(
                f"XP obecnego levelu: {xp} z {needed}. "
                f"Do następnego levelu brakuje {remaining} XP."
            )

        await self.send(
            f"Obecny Tier: {tier} z {TOOL_MAX_TIER}. "
            f"Nazwa: {tier_name}. "
            f"{bonus_label}: {bonus_percent} procent."
        )

        if tier >= TOOL_MAX_TIER:
            await self.send("Tier maksymalny. Nie ma następnego Tieru.")
        else:
            target_level = TOOL_TIER_THRESHOLDS[tier]
            next_tier = tier + 1
            next_name = TOOL_TIER_NAMES[tool_type][next_tier - 1]
            levels_remaining, xp_remaining = (
                self.tool_xp_remaining_to_next_tier(
                    level, xp, tool_type
                )
            )
            await self.send(
                f"Następny Tier: {next_tier}, {next_name}, "
                f"od levelu {target_level}. "
                f"Brakuje {levels_remaining} leveli i łącznie "
                f"{xp_remaining} XP narzędzia."
            )

        await self.send(f"TIERY NARZĘDZIA: {name}.")
        for tier_number, minimum in enumerate(TOOL_TIER_THRESHOLDS, 1):
            if tier_number < TOOL_MAX_TIER:
                maximum = TOOL_TIER_THRESHOLDS[tier_number] - 1
                level_text = f"level {minimum}-{maximum}"
            else:
                if tool_type == "crafting":
                    level_text = (
                        f"level {minimum}-{TOOL_MAX_LEVEL}"
                    )
                else:
                    level_text = f"level {minimum}-{TOOL_MAX_LEVEL}"

            tier_bonus = int(
                TOOL_TIER_BONUS_CHANCES[tier_number - 1] * 100
            )
            marker = " Obecny." if tier_number == tier else ""
            await self.send(
                f"Tier {tier_number}: "
                f"{TOOL_TIER_NAMES[tool_type][tier_number - 1]}. "
                f"{level_text}. Bonus {tier_bonus} procent.{marker}"
            )

    async def show_tools(self):
        await self.send("NARZĘDZIA")
        tools = [
            ("fishing", "fishing_rod", "Wędka"),
            ("mining", "pickaxe", "Kilof"),
            ("woodcutting", "saw", "Piła"),
            ("crafting", "crafting_hammer", "Młot Rzemieślniczy"),
            ("cooking", "chef_knife", "Nóż Kucharski"),
            ("herbalism", "herbalist_sickle", "Sierp Zielarski"),
            ("alchemy", "alchemy_mortar", "Moździerz Alchemiczny"),
        ]
        for tool_type, item_id, name in tools:
            owned = self.server.db.item_qty(self.account_id, item_id) > 0
            if not owned:
                await self.send(f"{name}: brak.")
                continue

            row = self.server.db.tool(self.account_id, tool_type)
            level = int(row["level"])
            max_level = tool_max_level(tool_type)
            tier = tool_tier(level)
            tier_name = tool_tier_name(tool_type, level)
            bonus_percent = int(tool_tier_bonus_chance(level) * 100)
            bonus_label = self.tool_bonus_label(tool_type)

            if tier < TOOL_MAX_TIER:
                next_level = TOOL_TIER_THRESHOLDS[tier]
                next_text = f"Następny Tier {tier + 1} od levelu {next_level}."
            else:
                next_text = "Tier maksymalny."

            if level >= max_level:
                await self.send(
                    f"{name}: level {level} z {max_level}. "
                    f"Tier {tier} z {TOOL_MAX_TIER}: {tier_name}. "
                    f"XP: maksimum. Użycia: {row['uses']}. "
                    f"{bonus_label}: {bonus_percent} procent. {next_text}"
                )
            else:
                await self.send(
                    f"{name}: level {level} z {max_level}. "
                    f"Tier {tier} z {TOOL_MAX_TIER}: {tier_name}. "
                    f"XP: {row['xp']} z {self.tool_xp_to_next(level, tool_type)}. "
                    f"Użycia: {row['uses']}. "
                    f"{bonus_label}: {bonus_percent} procent. {next_text}"
                )


    def fishing_habitat(self, room_id=None):
        room_id = room_id or self.character.room_id
        if room_id in RIVER_FISHING_ROOMS: return "river"
        if room_id in LAKE_FISHING_ROOMS: return "lake"
        if room_id in SEA_FISHING_ROOMS: return "sea"
        if room_id in OCEAN_FISHING_ROOMS: return "ocean"
        return None

    def fishing_loot(self, tool_level, habitat="river"):
        r = random.random()

        if habitat == "river":
            if tool_level < 10:
                return random.choice(("small_fish", "dace", "river_perch"))
            if tool_level < 25:
                pool = ("dace", "chub", "common_nase", "river_perch", "river_carp", "barbel")
                return random.choice(pool)
            if tool_level < 45:
                pool = ("chub", "common_nase", "barbel", "ide", "silver_trout", "pike", "zander")
                return random.choice(pool)
            if tool_level < 70:
                pool = ("ide", "asp", "grayling", "silver_trout", "golden_trout", "pike", "zander", "salmon", "burbot")
                return random.choice(pool)
            pool = (
                "asp", "grayling", "burbot", "golden_trout", "salmon",
                "river_catfish", "ancient_sturgeon", "moon_eel", "zander"
            )
            return random.choice(pool)

        if habitat == "lake":
            if tool_level < 10:
                return random.choice(("lake_roach", "rudd", "crucian_carp", "bream"))
            if tool_level < 25:
                pool = ("lake_roach", "rudd", "crucian_carp", "bream", "tench", "lake_perch")
                return random.choice(pool)
            if tool_level < 45:
                pool = ("bream", "tench", "lake_perch", "vendace", "pike", "zander")
                return random.choice(pool)
            if tool_level < 70:
                pool = ("tench", "vendace", "whitefish", "pike", "zander", "lake_trout", "giant_pike")
                return random.choice(pool)
            pool = (
                "whitefish", "lake_char", "lake_trout", "giant_pike",
                "freshwater_eel", "pike", "zander"
            )
            return random.choice(pool)

        if habitat == "sea":
            if tool_level < 10:
                return random.choice(("sprat", "sardine", "anchovy"))
            if tool_level < 20:
                return random.choice(("sprat", "sardine", "anchovy", "whiting", "cod"))
            if tool_level < 30:
                return random.choice(("anchovy", "whiting", "cod", "mackerel", "flounder"))
            if tool_level < 50:
                pool = ("herring", "mackerel", "whiting", "cod", "hake", "sea_bass", "haddock", "pollock")
                return random.choice(pool)
            if tool_level < 75:
                pool = ("herring", "hake", "sea_bass", "red_mullet", "haddock", "pollock", "flounder", "sole", "halibut")
                return random.choice(pool)
            pool = (
                "cod", "hake", "red_mullet", "sole", "halibut",
                "turbot", "monkfish", "sea_bass", "haddock", "pollock"
            )
            return random.choice(pool)

        # Ocean
        if tool_level < 20:
            return random.choice(("mackerel", "mahi_mahi", "albacore"))
        if tool_level < 40:
            pool = ("mahi_mahi", "albacore", "wahoo", "barracuda", "tuna", "sailfish")
            return random.choice(pool)
        if tool_level < 60:
            pool = ("tuna", "albacore", "bigeye_tuna", "wahoo", "barracuda", "cobia", "sailfish", "swordfish", "reef_shark")
            return random.choice(pool)
        if tool_level < 80:
            pool = (
                "tuna", "bigeye_tuna", "cobia", "amberjack", "swordfish",
                "bluefin_tuna", "reef_shark", "mako_shark", "hammerhead_shark",
                "ocean_sunfish"
            )
            return random.choice(pool)
        pool = (
            "bluefin_tuna", "bigeye_tuna", "amberjack", "ocean_sunfish",
            "mako_shark", "tiger_shark", "hammerhead_shark",
            "great_white_shark", "ghost_marlin", "swordfish"
        )
        return random.choice(pool)


    def mining_loot(self, tool_level):
        r = random.random()

        if tool_level < 10:
            if r < 0.30:
                return "stone_chunk"
            if r < 0.95:
                return "copper_ore"
            return "iron_ore"

        if tool_level < 25:
            if r < 0.45:
                return "copper_ore"
            if r < 0.95:
                return "iron_ore"
            return "silver_ore"

        if tool_level < 50:
            if r < 0.55:
                return "iron_ore"
            if r < 0.90:
                return "silver_ore"
            return "gold_ore"

        if tool_level < 80:
            if r < 0.42:
                return "iron_ore"
            if r < 0.82:
                return "silver_ore"
            return "gold_ore"

        # Mithril jest bezpośrednio walutą, nie rudą.
        # 1 mithril = 1 000 000 złota, więc szanse pozostają bardzo małe.
        if tool_level < 90:
            mithril_chance = 0.001      # 0,10%
        elif tool_level < 100:
            mithril_chance = 0.0025     # 0,25%
        else:
            mithril_chance = 0.005      # 0,50% na levelu 100

        if r < mithril_chance:
            return "__mithril_currency__"

        rr = (r - mithril_chance) / (1.0 - mithril_chance)
        if tool_level < 90:
            if rr < 0.30:
                return "iron_ore"
            if rr < 0.68:
                return "silver_ore"
            return "gold_ore"

        if rr < 0.18:
            return "iron_ore"
        if rr < 0.52:
            return "silver_ore"
        return "gold_ore"


    def woodcutting_loot(self, tool_level, room_id=None):
        room_id = room_id or self.character.room_id

        # Obóz Drwala i Łąka: gatunki lekkie i pospolite.
        if room_id in {"lumberjack_camp", "meadow"}:
            if tool_level < 15:
                return random.choice(("fallen_branch", "birch_log", "alder_log", "pine_log"))
            if tool_level < 35:
                return random.choice(("birch_log", "alder_log", "pine_log", "poplar_log", "willow_log", "linden_log"))
            return random.choice(("pine_log", "poplar_log", "willow_log", "linden_log", "oak_log", "beech_log", "maple_log"))

        # Gaj Szeptów i Stary Trakt: drewna użytkowe i szlachetne.
        if room_id in {"whisper_grove", "old_road"}:
            if tool_level < 25:
                return random.choice(("oak_log", "beech_log", "maple_log", "linden_log"))
            if tool_level < 50:
                return random.choice(("oak_log", "beech_log", "maple_log", "ash_log", "chestnut_log", "walnut_log"))
            if tool_level < 75:
                return random.choice(("maple_log", "ash_log", "chestnut_log", "walnut_log", "cedar_log", "yew_log", "mahogany_log"))
            return random.choice(("ash_log", "walnut_log", "cedar_log", "yew_log", "mahogany_log", "teak_log", "redwood_log", "ironwood_log"))

        # Głębia Gaju: najrzadsze drewna naturalne i magiczne.
        if tool_level < 40:
            return random.choice(("ash_log", "chestnut_log", "cedar_log", "walnut_log"))
        if tool_level < 60:
            return random.choice(("cedar_log", "yew_log", "mahogany_log", "teak_log", "ironwood_log", "ebony_log"))
        if tool_level < 80:
            return random.choice(("yew_log", "mahogany_log", "teak_log", "redwood_log", "ironwood_log", "ebony_log", "silverwood_log"))
        if tool_level < 100:
            return random.choice((
                "redwood_log", "ironwood_log", "ebony_log", "silverwood_log",
                "spiritwood_log", "ancient_heartwood", "worldtree_wood"
            ))
        return random.choice((
            "teak_log", "redwood_log", "silverwood_log", "spiritwood_log",
            "ancient_heartwood", "worldtree_wood"
        ))


    def herbalism_loot(self, tool_level, room_id=None):
        room_id = room_id or self.character.room_id
        if room_id in {"herbalist_hut", "meadow"}:
            if tool_level < 15:
                return random.choice(("nettle", "chamomile", "mint"))
            if tool_level < 35:
                return random.choice(("nettle", "chamomile", "mint", "yarrow", "lemon_balm", "lavender"))
            return random.choice(("mint", "yarrow", "lemon_balm", "lavender", "sage", "valerian"))
        if room_id in {"riverbank", "lake_shore"}:
            if tool_level < 25:
                return random.choice(("mint", "lemon_balm", "chamomile"))
            if tool_level < 55:
                return random.choice(("mint", "lemon_balm", "star_moss", "sage", "yarrow"))
            return random.choice(("star_moss", "moonflower", "sage", "valerian", "ginseng"))
        if room_id in {"whisper_grove", "old_road"}:
            if tool_level < 25:
                return random.choice(("sage", "valerian", "lavender"))
            if tool_level < 50:
                return random.choice(("sage", "valerian", "ginseng", "nightshade"))
            if tool_level < 75:
                return random.choice(("ginseng", "nightshade", "mandrake", "moonflower", "soulroot"))
            return random.choice(("mandrake", "moonflower", "soulroot", "phoenix_leaf", "star_moss"))
        if tool_level < 40:
            return random.choice(("ginseng", "nightshade", "mandrake"))
        if tool_level < 70:
            return random.choice(("nightshade", "mandrake", "moonflower", "soulroot", "star_moss"))
        if tool_level < 90:
            return random.choice(("mandrake", "moonflower", "soulroot", "phoenix_leaf", "star_moss"))
        return random.choice(("moonflower", "soulroot", "phoenix_leaf", "star_moss", "astral_lotus"))

    def profession_ready(self):
        now = time.time()
        remaining = PROFESSION_COOLDOWN - (now - self.last_profession_action)
        if remaining > 0:
            return False, remaining
        self.last_profession_action = now
        return True, 0.0

    async def fish(self, from_auto=False):
        if self.combat_mob_key:
            await self.send("Nie możesz łowić podczas walki.")
            return
        if self.character.room_id not in FISHING_ROOMS:
            await self.send("Tutaj nie ma odpowiedniego łowiska.")
            return
        if self.server.db.item_qty(self.account_id, "fishing_rod") <= 0:
            await self.send("Do Wędkarstwa potrzebujesz Wędki. Kup ją na Rynku.")
            return
        ready, remaining = self.profession_ready()
        if not ready:
            if not from_auto:
                await self.send("Musisz chwilę odczekać przed kolejnym zarzuceniem wędki.")
            return

        tool = self.server.db.tool(self.account_id, "fishing")
        tool_level = int(tool["level"])
        habitat = self.fishing_habitat()
        item_id = self.fishing_loot(tool_level, habitat=habitat)
        self.store_profession_resource(item_id, 1)
        item = ITEMS[item_id]
        await self.send(
            f"Łowisz: {item['name']}. Połów trafia do Siatki na ryby."
        )

        current_tier = tool_tier(tool_level)
        bonus_chance = min(
            0.50,
            tool_tier_bonus_chance(tool_level)
            + self.character.racial_profession_bonus_chance()
        )
        if bonus_chance > 0 and random.random() < bonus_chance:
            self.store_profession_resource(item_id, 1)
            await self.send(
                f"Bonus Tieru {current_tier} Wędki: wyciągasz dodatkowo {item['name']} x1."
            )

        await self.announce_collect_category_quest_progress("fish")

        messages, profession_level, new_tool_level = self.grant_profession_progress(
            "Wędkarstwo",
            10 + random.randint(0, 5),
            "fishing",
            8 + random.randint(0, 4),
        )
        for msg in messages:
            await self.send(msg)
        if new_tool_level != tool_level:
            await self.send(
                f"Wędka ma teraz level {new_tool_level}, Tier "
                f"{tool_tier(new_tool_level)}: "
                f"{tool_tier_name('fishing', new_tool_level)}."
            )

    async def mine(self, from_auto=False):
        if self.combat_mob_key:
            await self.send("Nie możesz wydobywać podczas walki.")
            return
        if self.character.room_id not in MINING_ROOMS:
            await self.send("Tutaj nie ma odpowiedniego złoża.")
            return
        if self.server.db.item_qty(self.account_id, "pickaxe") <= 0:
            await self.send("Do Górnictwa potrzebujesz Kilofa. Kup go w Kuźni Dusz.")
            return
        ready, remaining = self.profession_ready()
        if not ready:
            if not from_auto:
                await self.send("Musisz chwilę odczekać przed kolejnym uderzeniem kilofa.")
            return

        tool = self.server.db.tool(self.account_id, "mining")
        tool_level = int(tool["level"])
        item_id = self.mining_loot(tool_level)

        if item_id == "__mithril_currency__":
            self.character.mithril += 1
            self.server.db.save_character(self.character)
            await self.send(
                "Trafiasz na żyłę czystego mithrilu! Wydobywasz 1 mithril bezpośrednio do portfela."
            )
        else:
            self.store_profession_resource(item_id, 1)
            item = ITEMS[item_id]
            await self.send(
                f"Wydobywasz: {item['name']}. Urobek trafia do Sakwy górniczej."
            )

            current_tier = tool_tier(tool_level)
            bonus_chance = min(
            0.50,
            tool_tier_bonus_chance(tool_level)
            + self.character.racial_profession_bonus_chance()
        )
            if bonus_chance > 0 and random.random() < bonus_chance:
                self.store_profession_resource(item_id, 1)
                await self.send(
                    f"Bonus Tieru {current_tier} Kilofa: wydobywasz dodatkowo {item['name']} x1."
                )

        if item_id != "__mithril_currency__":
            await self.announce_collect_category_quest_progress("ore")

        messages, profession_level, new_tool_level = self.grant_profession_progress(
            "Górnictwo",
            10 + random.randint(0, 5),
            "mining",
            8 + random.randint(0, 4),
        )
        for msg in messages:
            await self.send(msg)
        if new_tool_level != tool_level:
            await self.send(
                f"Kilof ma teraz level {new_tool_level}, Tier "
                f"{tool_tier(new_tool_level)}: "
                f"{tool_tier_name('mining', new_tool_level)}."
            )
        if new_tool_level >= 80 and tool_level < 80:
            await self.send(
                "Twój Kilof osiągnął level 80. Od teraz masz minimalną szansę wydobyć czysty mithril."
            )

    async def woodcut(self, from_auto=False):
        if self.combat_mob_key:
            await self.send("Nie możesz ścinać drzew podczas walki.")
            return
        if self.character.room_id not in WOODCUTTING_ROOMS:
            await self.send("Tutaj nie ma odpowiednich drzew do Drwalstwa.")
            return
        if self.server.db.item_qty(self.account_id, "saw") <= 0:
            await self.send("Do Drwalstwa potrzebujesz Piły. Kup ją u Drwala Brana w Obozie Drwala.")
            return
        ready, remaining = self.profession_ready()
        if not ready:
            if not from_auto:
                await self.send("Musisz chwilę odczekać przed kolejnym cięciem.")
            return

        tool = self.server.db.tool(self.account_id, "woodcutting")
        tool_level = int(tool["level"])
        item_id = self.woodcutting_loot(tool_level, self.character.room_id)
        self.store_profession_resource(item_id, 1)
        item = ITEMS[item_id]
        await self.send(
            f"Pozyskujesz: {item['name']}. Drewno trafia na Stos drewna."
        )

        current_tier = tool_tier(tool_level)
        bonus_chance = min(
            0.50,
            tool_tier_bonus_chance(tool_level)
            + self.character.racial_profession_bonus_chance()
        )
        if bonus_chance > 0 and random.random() < bonus_chance:
            self.store_profession_resource(item_id, 1)
            await self.send(
                f"Bonus Tieru {current_tier} Piły: pozyskujesz dodatkowo {item['name']} x1."
            )

        await self.announce_collect_category_quest_progress("wood")

        messages, profession_level, new_tool_level = self.grant_profession_progress(
            "Drwalstwo",
            10 + random.randint(0, 5),
            "woodcutting",
            8 + random.randint(0, 4),
        )
        for msg in messages:
            await self.send(msg)
        if new_tool_level != tool_level:
            await self.send(
                f"Piła ma teraz level {new_tool_level}, Tier "
                f"{tool_tier(new_tool_level)}: "
                f"{tool_tier_name('woodcutting', new_tool_level)}."
            )

    async def gather_herb(self, from_auto=False):
        if self.combat_mob_key:
            await self.send("Nie możesz zbierać ziół podczas walki.")
            return
        if self.character.room_id not in HERBALISM_ROOMS:
            await self.send("Tutaj nie ma odpowiednich ziół.")
            return
        if self.server.db.item_qty(self.account_id, "herbalist_sickle") <= 0:
            await self.send("Do Zielarstwa potrzebujesz Sierpa Zielarskiego. Kup go w Chacie Zielarki.")
            return
        ready, remaining = self.profession_ready()
        if not ready:
            if not from_auto:
                await self.send("Musisz chwilę odczekać przed kolejnym zbiorem.")
            return

        tool = self.server.db.tool(self.account_id, "herbalism")
        old_level = int(tool["level"])
        item_id = self.herbalism_loot(old_level, self.character.room_id)
        self.store_profession_resource(item_id, 1)
        await self.send(f"Zbierasz: {ITEMS[item_id]['name']}. Zioło trafia do Torby Zielarskiej.")

        bonus_chance = min(
            0.50,
            tool_tier_bonus_chance(old_level) + self.character.racial_profession_bonus_chance()
        )
        if bonus_chance > 0 and random.random() < bonus_chance:
            self.store_profession_resource(item_id, 1)
            await self.send(
                f"Bonus Tieru {tool_tier(old_level)} Sierpa Zielarskiego: "
                f"zbierasz dodatkowo {ITEMS[item_id]['name']} x1."
            )

        await self.announce_collect_category_quest_progress("herb")

        messages, prof_level, new_tool_level = self.grant_profession_progress(
            "Zielarstwo",
            10 + random.randint(0, 5),
            "herbalism",
            8 + random.randint(0, 4),
        )
        for msg in messages:
            await self.send(msg)
        if new_tool_level != old_level:
            await self.send(
                f"Sierp Zielarski ma teraz level {new_tool_level}, Tier "
                f"{tool_tier(new_tool_level)}: {tool_tier_name('herbalism', new_tool_level)}."
            )

    async def sell_resource(self, query):
        found = find_by_name(ITEMS, query)
        if not found:
            await self.send("Nie rozpoznaję takiego przedmiotu.")
            return
        item_id, item = found
        if item.get("type") != "resource":
            await self.send("Tego przedmiotu nie sprzedaje się tutaj jako surowca.")
            return

        fish_items = FISH_RESOURCE_IDS
        ore_items = ORE_RESOURCE_IDS
        wood_items = WOOD_RESOURCE_IDS
        herb_items = HERB_RESOURCE_IDS

        if item_id in fish_items:
            source_container = "net"
        elif item_id in ore_items:
            source_container = "bag"
        elif item_id in wood_items:
            source_container = "woodpile"
        elif item_id in herb_items:
            source_container = "herbbag"
        else:
            source_container = None

        storage_quantity = (
            self.server.db.storage_qty(self.account_id, source_container, item_id)
            if source_container else 0
        )
        inventory_quantity = self.server.db.item_qty(self.account_id, item_id)
        if storage_quantity <= 0 and inventory_quantity <= 0:
            await self.send("Nie masz tego przedmiotu.")
            return

        if item_id in fish_items and self.character.room_id not in {"market", "inn", "fish_market"}:
            await self.send("Ryby możesz sprzedać na Targu Rybnym, Rynku albo w Karczmie.")
            return
        if item_id in ore_items and self.character.room_id != "forge":
            await self.send("Rudy możesz sprzedać w Kuźni Dusz.")
            return
        if item_id in wood_items and self.character.room_id not in {"market", "forge"}:
            await self.send("Drewno możesz sprzedać na Rynku albo w Kuźni Dusz.")
            return
        if item_id in herb_items and self.character.room_id not in {"market", "herbalist_hut"}:
            await self.send("Zioła możesz sprzedać na Rynku albo w Chacie Zielarki.")
            return

        removed = False
        if source_container and self.server.db.storage_qty(
            self.account_id, source_container, item_id
        ) > 0:
            removed = self.server.db.remove_storage_item(
                self.account_id, source_container, item_id, 1
            )
        elif self.server.db.item_qty(self.account_id, item_id) > 0:
            removed = self.server.db.remove_item(
                self.account_id, item_id, 1
            )

        if not removed:
            await self.send("Nie masz tego surowca.")
            return

        silver = item.get("sell_silver", 0)
        gold = item.get("sell_gold", 0)
        mithril = item.get("sell_mithril", 0)
        self.character.silver += silver
        self.character.gold += gold
        self.character.mithril += mithril
        await self.gain_charisma_from_sale()
        self.server.db.save_character(self.character)

        rewards = []
        if silver:
            rewards.append(f"{silver} srebra")
        if gold:
            rewards.append(f"{gold} złota")
        if mithril:
            rewards.append(f"{mithril} mithrilu")
        await self.send(f"Sprzedajesz {item['name']} za " + ", ".join(rewards) + ".")

    def recipe_container_for_item(self, item_id):
        if item_id in FISH_RESOURCE_IDS:
            return "net"
        if item_id in ORE_RESOURCE_IDS:
            return "bag"
        if item_id in WOOD_RESOURCE_IDS:
            return "woodpile"
        if item_id in HERB_RESOURCE_IDS:
            return "herbbag"
        return None

    def available_recipe_item(self, item_id):
        container = self.recipe_container_for_item(item_id)
        storage = (
            self.server.db.storage_qty(self.account_id, container, item_id)
            if container else 0
        )
        return storage + self.server.db.item_qty(self.account_id, item_id)

    def consume_recipe_item(self, item_id, quantity):
        remaining = max(0, int(quantity))
        container = self.recipe_container_for_item(item_id)

        if container and remaining > 0:
            stored = self.server.db.storage_qty(
                self.account_id, container, item_id
            )
            take = min(stored, remaining)
            if take > 0:
                if not self.server.db.remove_storage_item(
                    self.account_id, container, item_id, take
                ):
                    return False
                remaining -= take

        if remaining > 0:
            if not self.server.db.remove_item(
                self.account_id, item_id, remaining
            ):
                return False
            remaining = 0

        return True

    def recipe_station_text(self, stations):
        return " lub ".join(ROOMS[room_id]["name"] for room_id in stations)

    def recipe_ingredients_text(self, recipe):
        return ", ".join(
            f"{ITEMS[item_id]['name']} x{quantity}"
            for item_id, quantity in recipe["ingredients"].items()
        )

    async def show_recipes(self, mode=""):
        mode = mode.strip().lower()
        show_craft = mode not in ("cook", "gotuj", "gotowanie", "alchemy", "alchemia")
        show_cook = mode not in ("craft", "stworz", "stwórz", "rzemioslo", "rzemiosło", "alchemy", "alchemia")
        show_alchemy = mode not in ("craft", "stworz", "stwórz", "rzemioslo", "rzemiosło", "cook", "gotuj", "gotowanie")

        if show_craft:
            await self.send("RECEPTURY RZEMIOSŁA")
            for recipe in CRAFT_RECIPES.values():
                await self.send(
                    f"{recipe['name']}. Składniki: "
                    f"{self.recipe_ingredients_text(recipe)}. "
                    f"Miejsce: {self.recipe_station_text(recipe['stations'])}. "
                    f"{recipe['desc']}"
                )

        if show_cook:
            await self.send("RECEPTURY GOTOWANIA")
            for recipe in COOK_RECIPES.values():
                await self.send(
                    f"{recipe['name']}. Składniki: "
                    f"{self.recipe_ingredients_text(recipe)}. "
                    f"Miejsce: {self.recipe_station_text(recipe['stations'])}. "
                    f"{recipe['desc']}"
                )

        if show_alchemy:
            await self.send("RECEPTURY ALCHEMII")
            for recipe in ALCHEMY_RECIPES.values():
                await self.send(
                    f"{recipe['name']}. Składniki: "
                    f"{self.recipe_ingredients_text(recipe)}. "
                    f"Miejsce: {self.recipe_station_text(recipe['stations'])}. "
                    f"{recipe['desc']}"
                )

    def recipe_tool_info(self, recipes):
        if recipes is CRAFT_RECIPES:
            return "crafting", "crafting_hammer", "Młot Rzemieślniczy"
        if recipes is ALCHEMY_RECIPES:
            return "alchemy", "alchemy_mortar", "Moździerz Alchemiczny"
        return "cooking", "chef_knife", "Nóż Kucharski"

    async def perform_recipe(self, query, recipes, action_name):
        if self.combat_mob_key:
            await self.send(
                f"Nie możesz wykonywać akcji {action_name} podczas walki."
            )
            return False

        tool_type, tool_item_id, tool_name = self.recipe_tool_info(recipes)
        if self.server.db.item_qty(self.account_id, tool_item_id) <= 0:
            if tool_type == "crafting":
                await self.send(
                    "Do Rzemiosła potrzebujesz Młota Rzemieślniczego. "
                    "Kup go u Kowala Dorana w Kuźni Dusz."
                )
            elif tool_type == "alchemy":
                await self.send(
                    "Do Alchemii potrzebujesz Moździerza Alchemicznego. "
                    "Kup go w Chacie Zielarki."
                )
            else:
                await self.send(
                    "Do Gotowania potrzebujesz Noża Kucharskiego. "
                    "Kup go w Karczmie Pod Błękitnym Płomieniem."
                )
            return False

        found = find_by_name(recipes, query)
        if not found:
            await self.send("Nie rozpoznaję tej receptury. Wpisz receptury.")
            return False

        recipe_id, recipe = found

        if self.character.room_id not in recipe["stations"]:
            await self.send(
                f"Tę recepturę wykonasz w: "
                f"{self.recipe_station_text(recipe['stations'])}."
            )
            return False

        missing = []
        for item_id, quantity in recipe["ingredients"].items():
            have = self.available_recipe_item(item_id)
            if have < quantity:
                missing.append(
                    f"{ITEMS[item_id]['name']}: masz {have}, potrzeba {quantity}"
                )

        if missing:
            await self.send("Brakuje składników:")
            for line in missing:
                await self.send(line + ".")
            return False

        for item_id, quantity in recipe["ingredients"].items():
            if not self.consume_recipe_item(item_id, quantity):
                await self.send(
                    "Nie udało się pobrać składników. Receptura przerwana."
                )
                return False

        output_id = recipe["output"]
        quantity = int(recipe.get("quantity", 1))

        tool_row = self.server.db.tool(self.account_id, tool_type)
        old_tool_level = int(tool_row["level"])
        tier = tool_tier(old_tool_level)
        bonus_chance = tool_tier_bonus_chance(old_tool_level)

        bonus_quantity = 0
        if bonus_chance > 0 and random.random() < bonus_chance:
            bonus_quantity = quantity

        total_quantity = quantity + bonus_quantity
        self.server.db.add_item(
            self.account_id, output_id, total_quantity
        )

        await self.send(
            f"{action_name.capitalize()}: {ITEMS[output_id]['name']} "
            f"x{quantity}. Przedmiot trafia do zwykłego ekwipunku."
        )

        if bonus_quantity > 0:
            if tool_type == "cooking":
                await self.send(
                    f"Bonus Tieru {tier} Noża Kucharskiego: "
                    f"przygotowujesz dodatkowo {ITEMS[output_id]['name']} "
                    f"x{bonus_quantity}."
                )
            elif tool_type == "alchemy":
                await self.send(
                    f"Bonus Tieru {tier} Moździerza Alchemicznego: "
                    f"warzysz dodatkowo {ITEMS[output_id]['name']} "
                    f"x{bonus_quantity}."
                )
            else:
                await self.send(
                    f"Bonus Tieru {tier} Młota Rzemieślniczego: "
                    f"wytwarzasz dodatkowo {ITEMS[output_id]['name']} "
                    f"x{bonus_quantity}."
                )

        tool_xp = 8 + random.randint(0, 4)
        if tool_type == "alchemy":
            messages, alchemy_level, new_tool_level = self.grant_profession_progress(
                "Alchemia", 10 + random.randint(0, 5), "alchemy", tool_xp
            )
        else:
            messages, new_tool_level = self.grant_tool_progress(tool_type, tool_xp)
        for message in messages:
            await self.send(message)

        if new_tool_level != old_tool_level:
            await self.send(
                f"{tool_name} ma teraz level {new_tool_level}, "
                f"Tier {tool_tier(new_tool_level)}: "
                f"{tool_tier_name(tool_type, new_tool_level)}."
            )

        return True

    async def craft_item(self, query):
        return await self.perform_recipe(query, CRAFT_RECIPES, "rzemiosło")

    async def cook_item(self, query):
        return await self.perform_recipe(query, COOK_RECIPES, "gotowanie")

    async def alchemy_item(self, query):
        return await self.perform_recipe(query, ALCHEMY_RECIPES, "alchemia")

    async def inventory(self):
        rows = self.server.db.inventory(self.account_id)
        await self.send(
            f"Waluta: {self.character.silver} srebra, "
            f"{self.character.gold} złota, {self.character.mithril} mithrilu."
        )
        await self.send(
            "Siatka na ryby, Sakwa górnicza, Stos drewna i Torba Zielarska "
            "są osobnymi magazynami; użyj siatka/net, sakwa/bag, drewno/stos "
            "oraz ziola/herbs."
        )
        if not rows:
            await self.send("Ekwipunek jest pusty.")
            return
        await self.send("Ekwipunek:")
        for row in rows:
            item = ITEMS.get(row["item_id"], {"name": row["item_id"], "desc": ""})
            await self.send(f"{item['name']} x{row['quantity']}. {item.get('desc','')}")

    async def equipment(self):
        rows = self.server.db.equipment(self.account_id)
        if not rows:
            await self.send("Nie masz założonego dodatkowego wyposażenia.")
            return
        await self.send("Założone wyposażenie:")
        for row in rows:
            item = ITEMS.get(row["item_id"])
            name = item["name"] if item else row["item_id"]
            defense = item.get("defense", 0) if item else 0
            slot_names = {
                "head": "Głowa",
                "body": "Korpus",
                "hands": "Dłonie",
                "legs": "Nogi",
                "feet": "Stopy",
                "charm": "Talizman",
            }
            slot_name = slot_names.get(row["slot"], row["slot"])
            extra = ""
            if item and item.get("rarity_name"):
                extra += f" Rzadkość: {item['rarity_name']}."
            if item and item.get("affix"):
                affix_name = CRYPT_AFFIXES.get(
                    item["affix"], item["affix"]
                )
                extra += (
                    f" Bonus: {affix_name} "
                    f"+{item.get('affix_amount', 0)}."
                )
            await self.send(
                f"{slot_name}: {name}. Obrona +{defense}.{extra}"
            )
        await self.send(self.crypt_set_bonus_text())

    async def equip_item(self, query):
        if self.combat_mob_key:
            await self.send(
                "Nie możesz zmieniać ekwipunku podczas walki turowej. "
                "Najpierw użyj flee albo zakończ walkę."
            )
            return
        found = find_by_name(ITEMS, query)
        if not found:
            await self.send("Nie rozpoznaję takiego przedmiotu.")
            return
        item_id, item = found
        if item.get("type") != "armor":
            await self.send("Tego przedmiotu nie można założyć.")
            return
        if self.server.db.item_qty(self.account_id, item_id) <= 0:
            await self.send("Nie masz tego przedmiotu.")
            return
        self.server.db.equip(
            self.account_id, item["slot"], item_id
        )
        self.current_hp = min(self.current_hp, self.max_hp())
        self.current_mana = min(
            self.current_mana, self.max_mana()
        )
        await self.send(
            f"Zakładasz: {item['name']}. "
            f"Obrona fizyczna wynosi teraz {self.defense()}."
        )
        await self.send(self.crypt_set_bonus_text())

    def find_consumable_for_use(self, query):
        q = self.normalize_description_query(query)
        if not q:
            return None, []

        # Celowe krótkie aliasy wymagane dla szybkiej obsługi NVDA.
        direct_aliases = {
            "mikstura": "healing_potion",
            "miksture": "healing_potion",
            "miksturę": "healing_potion",
            "potion": "healing_potion",
            "eliksir": "soul_elixir",
            "elixir": "soul_elixir",
            "eliksir duszy": "soul_elixir",
            "soul elixir": "soul_elixir",
            "mana": "mana_potion",
            "mikstura many": "mana_potion",
            "mana potion": "mana_potion",
        }
        item_id = direct_aliases.get(q)
        if item_id:
            return (item_id, ITEMS[item_id]), []

        consumables = {
            item_id: item
            for item_id, item in ITEMS.items()
            if item.get("type") == "consumable"
        }

        exact = []
        partial = []
        for item_id, item in consumables.items():
            names = (
                item_id,
                item.get("name", ""),
            )
            normalized_names = [
                self.normalize_description_query(name)
                for name in names
            ]
            if q in normalized_names:
                exact.append((item_id, item))
            elif any(q in name for name in normalized_names):
                partial.append((item_id, item))

        if exact:
            return exact[0], []
        if len(partial) == 1:
            return partial[0], []
        if len(partial) > 1:
            return None, partial
        return None, []

    async def use_item(self, query):
        raw_query = str(query or "").strip()
        lowered = raw_query.lower()

        # Wygodna składnia dla umiejętności:
        # użyj umiejętność <nazwa> [cel]
        # use skill <name> [target]
        skill_prefixes = (
            "skill ",
            "umiejętność ",
            "umiejetnosc ",
            "zdolność ",
            "zdolnosc ",
        )
        for prefix in skill_prefixes:
            if lowered.startswith(prefix):
                skill_query = raw_query[len(prefix):].strip()
                if not skill_query:
                    await self.send(
                        "Użycie: użyj umiejętność <nazwa> [cel] "
                        "albo use skill <name> [target]."
                    )
                    return
                await self.use_class_skill(skill_query)
                return

        found, ambiguous = self.find_consumable_for_use(raw_query)

        if ambiguous:
            names = ", ".join(item["name"] for _, item in ambiguous)
            await self.send(
                f"Nazwa pasuje do kilku przedmiotów: {names}. "
                "Podaj dokładniejszą nazwę."
            )
            return

        if not found:
            skill, _target = self.find_skill_from_input(raw_query)
            if skill:
                await self.use_class_skill(raw_query)
                return

            await self.send(
                "Nie rozpoznaję przedmiotu ani umiejętności. "
                "Przykłady: użyj mikstura; użyj umiejętność <nazwa> [cel]; "
                "use skill <name> [target]."
            )
            return

        item_id, item = found

        if self.server.db.item_qty(self.account_id, item_id) <= 0:
            await self.send(f"Nie masz przedmiotu: {item['name']}.")
            return

        if item.get("type") != "consumable":
            await self.send("Tego przedmiotu nie używa się w ten sposób.")
            return

        if "heal" in item or "mana" in item:
            max_hp = self.max_hp()
            max_mana = self.max_mana()

            missing_hp = max(0, max_hp - self.current_hp)
            missing_mana = max(0, max_mana - self.current_mana)

            can_restore_hp = (
                item.get("heal", 0) > 0
                and missing_hp > 0
            )
            can_restore_mana = (
                item.get("mana", 0) > 0
                and max_mana > 0
                and missing_mana > 0
            )

            if not can_restore_hp and not can_restore_mana:
                if max_mana > 0:
                    await self.send("Masz pełne HP i Manę.")
                else:
                    await self.send("Masz pełne życie.")
                return

            self.server.db.remove_item(
                self.account_id, item_id, 1
            )

            healed = 0
            restored_mana = 0

            if can_restore_hp:
                healed = min(
                    item.get("heal", 0), missing_hp
                )
                self.current_hp += healed

            if can_restore_mana:
                restored_mana = min(
                    item.get("mana", 0), missing_mana
                )
                self.current_mana += restored_mana

            parts = []
            if healed:
                parts.append(f"{healed} HP")
            if restored_mana:
                parts.append(f"{restored_mana} Many")

            await self.send(
                f"Używasz {item['name']}. Odzyskujesz "
                + " i ".join(parts) + "."
            )
            await self.send(
                f"HP {self.current_hp} z {max_hp}."
            )
            if max_mana > 0:
                await self.send(
                    f"Mana {self.current_mana} z {max_mana}."
                )

            if self.combat_mob_key:
                await self.send(
                    "Zużywasz swoją turę na użycie przedmiotu."
                )
                await self.enemy_counterattack(
                    self.server.world.mobs.get(
                        self.combat_mob_key
                    )
                )
            return

        if "soul_xp" in item:
            self.server.db.remove_item(
                self.account_id, item_id, 1
            )
            await self.send(
                f"Używasz {item['name']}."
            )
            await self.grant_soul_xp(
                item["soul_xp"]
            )
            self.server.db.save_character(self.character)

            if self.combat_mob_key:
                await self.send(
                    "Zużywasz swoją turę na użycie przedmiotu."
                )
                await self.enemy_counterattack(
                    self.server.world.mobs.get(
                        self.combat_mob_key
                    )
                )
            return

        await self.send(
            "Ten przedmiot nie ma efektu do użycia."
        )


    async def shop(self):
        offers = SHOPS.get(self.character.room_id)
        if not offers:
            await self.send("W tej lokacji nie ma sklepu.")
            return
        await self.send(
            f"Oferta sklepu. Rabat Charyzmy: "
            f"{self.character.shop_discount_percent()} procent."
        )
        for number, item_id in enumerate(offers, 1):
            item = ITEMS[item_id]
            currency = item.get("currency", "gold")
            currency_pl = {"silver": "srebra", "gold": "złota", "mithril": "mithrilu"}[currency]
            extra = ""
            if item.get("type") == "armor":
                extra = (
                    f" Slot: {item.get('slot', 'brak')}. "
                    f"Obrona +{item.get('defense', 0)}."
                )
            cashback = self.shop_cashback_silver(item)
            discount_text = (
                f" Zwrot z rabatu: {cashback} srebra."
                if cashback > 0 else ""
            )
            await self.send(
                f"{number}. {item['name']}: {item['price']} {currency_pl}."
                f"{discount_text}{extra} {item['desc']}"
            )

    async def buy(self, query):
        offers = SHOPS.get(self.character.room_id)
        if not offers:
            await self.send("W tej lokacji nie ma sklepu.")
            return
        possible = {item_id: ITEMS[item_id] for item_id in offers}
        found = find_by_name(possible, query)
        if not found:
            await self.send("Tego przedmiotu nie ma w ofercie.")
            return
        item_id, item = found
        price = item["price"]
        currency = item.get("currency", "gold")
        currency_pl = {"silver": "srebra", "gold": "złota", "mithril": "mithrilu"}[currency]
        current = getattr(self.character, currency)
        if current < price:
            await self.send(f"Masz za mało waluty: {currency_pl}.")
            return
        setattr(self.character, currency, current - price)
        cashback = self.shop_cashback_silver(item)
        if cashback > 0:
            self.character.silver += cashback
        self.server.db.add_item(self.account_id, item_id, 1)
        if item.get("type") == "tool":
            self.server.db.ensure_tool(self.account_id, item["tool_type"])
        self.server.db.save_character(self.character)
        await self.send(f"Kupujesz {item['name']} za {price} {currency_pl}.")
        if cashback > 0:
            await self.send(
                f"Rabat Charyzmy: sprzedawca zwraca ci "
                f"{cashback} srebra."
            )

    async def show_teachers(self):
        teachers = [
            (npc_id, npc) for npc_id, npc in NPCS.items()
            if npc.get("teacher_class")
        ]
        await self.send("Nauczyciele klasowi rozmieszczeni po Gildii Dusz:")
        for number, (npc_id, npc) in enumerate(teachers, 1):
            own = (
                " Aktywna klasa."
                if npc["teacher_class"] in self.active_class_names()
                else ""
            )
            room_name = ROOMS[npc["room"]]["name"]
            await self.send(
                f"{number}. {npc['name']}. Klasa: {npc['teacher_class']}. "
                f"Lokacja: {room_name}.{own}"
            )
        await self.send(
            "Użyj prowadz <nazwa lokacji>, aby dojść do odpowiedniej sali, "
            "potem talk <nauczyciel>."
        )


    async def teacher_lesson(self, npc):
        class_name = npc["teacher_class"]
        learned = self.server.db.learned_skill_ids(self.account_id)

        await self.send(
            f"Lekcja klasy {class_name}. {CLASS_DESCRIPTIONS.get(class_name, '')}"
        )

        for number, skill in enumerate(CLASS_SKILLS.get(class_name, []), 1):
            progress = ""
            if class_name not in self.active_class_names():
                status = f"wymaga aktywnej klasy {class_name} i Soul Level {skill['unlock']}"
            elif skill["id"] in learned:
                row = self.server.db.skill_progress(self.account_id, skill["id"])
                status = "już nauczona"
                if int(row["level"]) >= SKILL_MAX_LEVEL:
                    progress = " Skill Level 100, maksymalny."
                else:
                    progress = (
                        f" Skill Level {row['level']}, XP {row['xp']} z "
                        f"{skill_xp_to_next(int(row['level']))}."
                    )
            elif self.character.soul_level >= skill["unlock"]:
                status = "możesz nauczyć się teraz"
            else:
                status = f"zablokowana do Soul Level {skill['unlock']}"

            mana = f" Mana {skill.get('mana', 0)}." if skill.get("mana", 0) else ""
            await self.send(
                f"{number}. {skill['name']}. {status}.{progress} "
                f"Cooldown bazowy {skill['cooldown']} sekund.{mana} {skill['desc']}"
            )

        if class_name in self.active_class_names():
            role = (
                "głównej" if class_name == self.character.class_name
                else "dodatkowej aktywnej"
            )
            await self.send(
                f"To jest nauczyciel twojej {role} klasy {class_name}. "
                f"Aktualny Soul Level: {self.character.soul_level}."
            )
            await self.send(
                "Nauka: learn <numer> albo naucz <nazwa umiejętności>. "
                "Każdy nauczony skill rozwija własny Skill Level 1-100."
            )
        else:
            await self.send(
                f"Klasa {class_name} nie jest teraz aktywna. "
                "Dodaj ją przez multiclass add <klasa>, aby móc się uczyć."
            )


    def quest_collect_category_info(self, target):
        mapping = {
            "fish": (FISH_RESOURCE_IDS, "net", "ryb"),
            "ore": (ORE_RESOURCE_IDS, "bag", "rud"),
            "wood": (WOOD_RESOURCE_IDS, "woodpile", "sztuk drewna"),
            "herb": (HERB_RESOURCE_IDS, "herbbag", "ziół"),
        }
        return mapping.get(target)

    def quest_progress_value(self, quest_id):
        q = QUESTS.get(quest_id)
        if not q:
            return None

        row = self.server.db.quest(self.account_id, quest_id)
        if not row or row["status"] != "active":
            return None

        if q["kind"] == "kill":
            return min(int(row["progress"]), int(q["needed"]))

        if q["kind"] == "collect":
            return min(
                self.server.db.item_qty(self.account_id, q["target"]),
                int(q["needed"]),
            )

        if q["kind"] == "collect_category":
            category = self.quest_collect_category_info(q["target"])
            if not category:
                return None
            ids, container, label = category
            return min(
                self.server.db.total_items_across_storage_and_inventory(
                    self.account_id, ids, container
                ),
                int(q["needed"]),
            )

        return None

    async def announce_active_quest_progress(self, quest_id):
        q = QUESTS.get(quest_id)
        if not q:
            return

        progress = self.quest_progress_value(quest_id)
        if progress is None:
            return

        needed = int(q["needed"])
        if progress >= needed:
            await self.send(
                f"Quest aktywny: {q['name']}. "
                f"Postęp {progress} z {needed}. Cel wykonany, wróć do NPC."
            )
        else:
            await self.send(
                f"Quest aktywny: {q['name']}. "
                f"Postęp {progress} z {needed}."
            )

    async def announce_collect_category_quest_progress(self, target):
        for row in self.server.db.quest_rows(self.account_id):
            if row["status"] != "active":
                continue
            q = QUESTS.get(row["quest_id"])
            if (
                not q
                or q.get("kind") != "collect_category"
                or q.get("target") != target
            ):
                continue
            await self.announce_active_quest_progress(row["quest_id"])

    def format_duration_short(self, seconds):
        seconds = max(0, int(seconds))
        minutes, sec = divmod(seconds, 60)
        if minutes and sec:
            return f"{minutes} min {sec} sek"
        if minutes:
            return f"{minutes} min"
        return f"{sec} sek"

    def soul_tier_quest_for_current_state(self):
        if self.character.soul_tier == 1 and self.character.soul_level >= TIER2_LEVEL:
            return "soul_tier_2_trial"
        if self.character.soul_tier == 2 and self.character.soul_level >= TIER3_LEVEL:
            return "soul_tier_3_trial"
        return None

    def soul_tier_quest_completed(self, tier):
        quest_id = {
            2: "soul_tier_2_trial",
            3: "soul_tier_3_trial",
        }.get(int(tier))
        if not quest_id:
            return False
        row = self.server.db.quest(self.account_id, quest_id)
        return bool(row and row["status"] == "completed")

    async def handle_quest_interaction(self, quest_id):
        q = QUESTS[quest_id]
        row = self.server.db.quest(self.account_id, quest_id)

        if not row:
            self.server.db.start_quest(self.account_id, quest_id)
            await self.send(f"Nowe zadanie: {q['name']}. {q['description']}")
            await self.announce_active_quest_progress(quest_id)
            return

        if row["status"] == "completed":
            if q.get("repeatable"):
                cooldown = int(
                    q.get(
                        "repeat_cooldown",
                        QUEST_REPEAT_COOLDOWN_SECONDS,
                    )
                )
                remaining = self.server.db.repeat_quest_seconds_remaining(
                    self.account_id, quest_id, cooldown
                )
                if remaining > 0:
                    await self.send(
                        f"Zadanie {q['name']} jest na odnowieniu. "
                        f"Możesz powtórzyć je za "
                        f"{self.format_duration_short(remaining)}."
                    )
                    return

                self.server.db.restart_quest(self.account_id, quest_id)
                cooldown_minutes = max(1, int(cooldown) // 60)
                await self.send(
                    f"Zadanie ponownie dostępne po {cooldown_minutes} minutach: "
                    f"{q['name']}. {q['description']}"
                )
                await self.announce_active_quest_progress(quest_id)
                return

            if q.get("unlocks_soul_tier"):
                await self.send(
                    f"Próba ukończona: {q['name']}. "
                    f"Możesz użyć unlock, aby odblokować Tier "
                    f"{q['unlocks_soul_tier']} Broni Duszy."
                )
                return

            await self.send(f"Zadanie {q['name']} jest już ukończone.")
            return

        if q["kind"] == "kill":
            progress = int(row["progress"])
            if progress < q["needed"]:
                await self.send(
                    f"Quest aktywny: {q['name']}. "
                    f"Postęp {progress} z {q['needed']}. "
                    f"{q['description']}"
                )
                return

        elif q["kind"] == "collect":
            progress = self.server.db.item_qty(
                self.account_id, q["target"]
            )
            if progress < q["needed"]:
                await self.send(
                    f"Quest aktywny: {q['name']}. "
                    f"Postęp {progress} z {q['needed']}."
                )
                return
            self.server.db.remove_item(
                self.account_id, q["target"], q["needed"]
            )

        elif q["kind"] == "collect_category":
            category = self.quest_collect_category_info(q["target"])
            if not category:
                await self.send("Błąd konfiguracji zadania.")
                return

            ids, container, label = category
            progress = (
                self.server.db.total_items_across_storage_and_inventory(
                    self.account_id, ids, container
                )
            )
            if progress < q["needed"]:
                await self.send(
                    f"Quest aktywny: {q['name']}. "
                    f"Postęp {progress} z {q['needed']} wymaganych {label}."
                )
                return

            ok = (
                self.server.db.consume_items_across_storage_and_inventory(
                    self.account_id, ids, q["needed"], container
                )
            )
            if not ok:
                await self.send(
                    "Nie udało się pobrać wymaganych surowców."
                )
                return

        await self.complete_quest(quest_id)

    async def talk(self, query):
        candidates = {
            key: npc
            for key, npc in NPCS.items()
            if npc["room"] == self.character.room_id
        }
        found = find_by_name(candidates, query)
        if not found:
            if candidates:
                await self.send("Nie rozpoznaję tego NPC.")
            else:
                await self.send(
                    "Nie ma tutaj nikogo, z kim można rozpocząć rozmowę."
                )
            return

        npc_id, npc = found
        await self.send(f"{npc['name']}: {npc['dialogue']}")

        if npc.get("teacher_class"):
            await self.teacher_lesson(npc)
            return

        # Kapłan Elor najpierw obsługuje aktualną próbę Broni Duszy.
        if npc_id == "priest_elor":
            tier_quest_id = self.soul_tier_quest_for_current_state()
            if tier_quest_id:
                await self.handle_quest_interaction(tier_quest_id)
                return

        quest_id = npc.get("quest")
        if not quest_id:
            return
        await self.handle_quest_interaction(quest_id)


    async def complete_quest(self, quest_id):
        q = QUESTS[quest_id]
        self.server.db.complete_quest(self.account_id, quest_id)

        if q.get("reward_profession_xp", 0) or q.get("reward_tool_xp", 0):
            await self.grant_profession_reward_xp(
                q.get("reward_profession", "Wędkarstwo"),
                q.get("reward_profession_xp", 0),
                q.get("reward_tool_type", "fishing"),
                q.get("reward_tool_xp", 0),
            )

        # EXP rozwoju statystyk nie tworzy levelu postaci.
        # Nadal zasila wyłącznie automatyczny wzrost pięciu statystyk.
        reward_exp = q.get("reward_stat_progress", 0)
        if reward_exp:
            for msg in self.character.add_stat_progress(reward_exp):
                await self.send(msg)

        self.character.silver += q.get("reward_silver", 0)
        self.character.gold += q.get("reward_gold", 0)
        self.character.mithril += q.get("reward_mithril", 0)
        for item_id, qty in q["reward_items"].items():
            self.server.db.add_item(self.account_id, item_id, qty)
        self.server.db.save_character(self.character)
        await self.send(f"Zadanie ukończone: {q['name']}.")
        if q.get("unlocks_soul_tier"):
            await self.send(
                f"Próba Broni Duszy zakończona. Tier "
                f"{q['unlocks_soul_tier']} jest gotowy do odblokowania "
                "komendą unlock."
            )
        if q.get("repeatable"):
            cooldown = int(
                q.get("repeat_cooldown", QUEST_REPEAT_COOLDOWN_SECONDS)
            )
            await self.send(
                "To zadanie jest powtarzalne. Będzie ponownie dostępne "
                f"za {max(1, cooldown // 60)} minut."
            )
        if q.get("reward_stat_progress", 0):
            await self.send(
                f"Nagroda EXP rozwoju: {q['reward_stat_progress']}."
            )
        if q.get("reward_silver", 0):
            await self.send(f"Nagroda: {q['reward_silver']} srebra.")
        if q.get("reward_gold", 0):
            await self.send(f"Nagroda: {q['reward_gold']} złota.")
        if q.get("reward_mithril", 0):
            await self.send(f"Nagroda: {q['reward_mithril']} mithrilu.")
        for item_id, qty in q["reward_items"].items():
            await self.send(f"Nagroda: {ITEMS[item_id]['name']} x{qty}.")

    async def quests(self):
        rows = self.server.db.quest_rows(self.account_id)
        if not rows:
            await self.send("Nie masz jeszcze żadnych zadań. Porozmawiaj z NPC.")
            return
        await self.send("DZIENNIK ZADAŃ")
        for row in rows:
            q = QUESTS.get(row["quest_id"])
            if not q:
                continue
            if row["status"] == "completed":
                if q.get("repeatable"):
                    remaining = (
                        self.server.db.repeat_quest_seconds_remaining(
                            self.account_id,
                            row["quest_id"],
                            int(
                                q.get(
                                    "repeat_cooldown",
                                    QUEST_REPEAT_COOLDOWN_SECONDS,
                                )
                            ),
                        )
                    )
                    if remaining > 0:
                        await self.send(
                            f"{q['name']}: ukończone. Powtórka za "
                            f"{self.format_duration_short(remaining)}."
                        )
                    else:
                        await self.send(
                            f"{q['name']}: gotowe do ponownego przyjęcia."
                        )
                elif q.get("unlocks_soul_tier"):
                    await self.send(
                        f"{q['name']}: ukończone. Tier "
                        f"{q['unlocks_soul_tier']} gotowy. Użyj unlock."
                    )
                else:
                    await self.send(f"{q['name']}: ukończone.")
            elif q["kind"] == "kill":
                await self.send(
                    f"{q['name']}: aktywne. Postęp {row['progress']} z {q['needed']}. {q['description']}"
                )
            elif q["kind"] == "collect":
                have = self.server.db.item_qty(self.account_id, q["target"])
                await self.send(
                    f"{q['name']}: aktywne. Postęp {have} z {q['needed']}. {q['description']}"
                )
            elif q["kind"] == "collect_category":
                category = self.quest_collect_category_info(q["target"])
                if not category:
                    continue
                ids, container, label = category
                have = self.server.db.total_items_across_storage_and_inventory(
                    self.account_id, ids, container
                )
                await self.send(
                    f"{q['name']}: aktywne. Postęp {have} z {q['needed']} wymaganych {label}. "
                    f"{q['description']}"
                )

    async def unlock(self):
        nxt = self.character.can_unlock()
        if not nxt:
            if self.character.soul_tier >= 3:
                await self.send("Broń Duszy ma już Tier 3.")
            elif self.character.soul_tier == 1:
                await self.send(
                    f"Tier 2 wymaga Soul Level {TIER2_LEVEL}, a następnie "
                    "ukończenia Próby Broni Duszy u Kapłana Elora "
                    "w Świątyni Odrodzenia."
                )
            else:
                await self.send(
                    f"Tier 3 wymaga Soul Level {TIER3_LEVEL}, a następnie "
                    "ukończenia Próby Broni Duszy u Kapłana Elora "
                    "w Świątyni Odrodzenia."
                )
            return

        required_quest = {
            2: "soul_tier_2_trial",
            3: "soul_tier_3_trial",
        }[nxt]
        if not self.soul_tier_quest_completed(nxt):
            await self.send(
                f"Masz wymagany Soul Level, ale Tier {nxt} wymaga jeszcze "
                f"zadania {QUESTS[required_quest]['name']}. "
                "Idź do Kapłana Elora w Świątyni Odrodzenia."
            )
            return

        self.character.soul_tier = nxt
        self.server.db.save_character(self.character)
        await self.send(
            f"Odblokowano Tier {nxt}. Moc Broni Duszy: "
            f"{self.character.soul_power()}."
        )
        await self.send(
            f"Nowy bonus klasowy Broni Duszy: "
            f"{self.character.soul_weapon_class_bonus_text()}."
        )

    def class_skills(self):
        skills = []
        for class_name in self.active_class_names():
            skills.extend(CLASS_SKILLS.get(class_name, []))
        return skills

    def class_teacher(self, class_name=None):
        wanted = class_name or self.character.class_name
        for npc_id, npc in NPCS.items():
            if npc.get("teacher_class") == wanted:
                return npc_id, npc
        return None, None

    def normalized_skill_text(self, value):
        return self.normalize_description_query(value)

    def find_skill_from_input(self, raw):
        skills = self.class_skills()
        raw = raw.strip()
        if not raw:
            return None, ""

        first = raw.split(maxsplit=1)
        if first[0].isdigit():
            number = int(first[0])
            if 1 <= number <= len(skills):
                return skills[number - 1], first[1] if len(first) > 1 else ""

        normalized = self.normalized_skill_text(raw)
        matches = []
        for skill in skills:
            for name in [skill["name"], skill["id"]] + skill.get("aliases", []):
                n = self.normalized_skill_text(name)
                if normalized == n:
                    matches.append((len(n), skill, ""))
                elif normalized.startswith(n + " "):
                    word_count = len(name.split())
                    target = " ".join(raw.split()[word_count:])
                    matches.append((len(n), skill, target))
        if not matches:
            return None, ""
        matches.sort(key=lambda x: x[0], reverse=True)
        return matches[0][1], matches[0][2]

    async def show_all_skill_names(self):
        await self.send("NAZWY SKILLI WSZYSTKICH KLAS")
        for class_name in [cls[0] for cls in CLASSES]:
            skills = CLASS_SKILLS.get(class_name, [])
            names = ", ".join(
                f"{index}. {skill['name']}"
                for index, skill in enumerate(skills, 1)
            )
            await self.send(f"{class_name}: {names}.")
        await self.send(
            "Nazw możesz używać w komendach skill <nazwa> oraz naucz <nazwa>."
        )

    async def show_skills(self):
        active = self.active_class_names()
        learned = self.server.db.learned_skill_ids(self.account_id)
        await self.send(
            f"UMIEJĘTNOŚCI AKTYWNYCH KLAS. Klasy: {', '.join(active)}. "
            f"Soul Level: {self.character.soul_level}."
        )

        global_number = 0
        for class_name in active:
            teacher_id, teacher = self.class_teacher(class_name)
            teacher_room = (
                ROOMS[teacher["room"]]["name"] if teacher else "nieznana lokacja"
            )
            await self.send(f"Klasa {class_name}:")
            for skill in CLASS_SKILLS.get(class_name, []):
                global_number += 1
                progress_text = ""
                skill_level = 1

                if skill["id"] in learned:
                    row = self.server.db.skill_progress(
                        self.account_id, skill["id"]
                    )
                    skill_level = int(row["level"])
                    if skill_level >= SKILL_MAX_LEVEL:
                        progress_text = (
                            f" Skill Level {skill_level}, maksymalny."
                        )
                    else:
                        progress_text = (
                            f" Skill Level {skill_level}, XP {row['xp']} z "
                            f"{skill_xp_to_next(skill_level)}, użycia {row['uses']}."
                        )
                    status = "nauczona"
                elif self.character.soul_level >= skill["unlock"]:
                    status = (
                        f"gotowa do nauki u {teacher['name']} "
                        f"w lokacji {teacher_room}"
                    )
                else:
                    status = (
                        f"zablokowana: wymaga Soul Level {skill['unlock']}"
                    )

                mana = (
                    f", Mana {skill.get('mana', 0)}"
                    if skill.get("mana", 0) else ""
                )
                effective_cd = self.effective_skill_cooldown(
                    skill, skill_level
                )
                remaining = max(
                    0,
                    int(
                        self.skill_cooldowns.get(skill["id"], 0)
                        - time.time() + 0.999
                    ),
                )
                cd = (
                    f", pozostały cooldown {remaining} sekund"
                    if remaining else ""
                )

                await self.send(
                    f"{global_number}. {skill['name']}. {status}."
                    f"{progress_text} Cooldown bazowy {skill['cooldown']} sekund, "
                    f"aktualny {effective_cd} sekund{mana}{cd}. "
                    f"{skill['desc']}"
                )

        await self.send(
            "Numery dotyczą wspólnej listy aktywnych klas. "
            "Przy nauczycielu komenda learn <numer> używa lokalnej listy jego klasy."
        )
        await self.send(
            "Każdy nauczony skill zachowuje własny Skill Level 1-100 i XP."
        )


    def protected_friendly_npc(self, query):
        room_id = self.character.room_id
        candidates = {
            npc_id: npc
            for npc_id, npc in NPCS.items()
            if npc.get("room") == room_id
        }
        if not candidates:
            return None

        found = find_by_name(candidates, query)
        if not found:
            return None
        return found[1]

    async def reject_friendly_npc_attack(self, query):
        npc = self.protected_friendly_npc(query)
        if not npc:
            return False

        await self.send(
            f"{npc['name']} jest pokojowym i chronionym NPC-em. "
            "Sprzedawców, nauczycieli, postaci zadaniowych i innych "
            "pomocnych NPC-ów nie można atakować ani zabijać."
        )
        return True

    def skill_progress_data(self, skill):
        if not self.server.db.knows_skill(self.account_id, skill["id"]):
            return {"level": 0, "xp": 0, "uses": 0}
        row = self.server.db.skill_progress(self.account_id, skill["id"])
        return {
            "level": int(row["level"]),
            "xp": int(row["xp"]),
            "uses": int(row["uses"]),
        }

    def effective_skill_cooldown(self, skill, skill_level):
        return max(
            1,
            int(round(skill["cooldown"] * skill_cooldown_multiplier(skill_level)))
        )

    async def grant_skill_use_xp(self, skill):
        gain = 8 + random.randint(0, 4)
        result = self.server.db.add_skill_xp(
            self.account_id, skill["id"], gain
        )
        if result["level_ups"]:
            await self.send(
                f"{skill['name']} awansuje na Skill Level {result['level']}."
            )
        if result["level"] >= SKILL_MAX_LEVEL:
            await self.send(
                f"{skill['name']}: Skill Level 100. Maksymalny poziom."
            )
        else:
            await self.send(
                f"{skill['name']}: Skill XP +{gain}. "
                f"Level {result['level']}, XP {result['xp']} z {result['next_xp']}."
            )
        return result

    def skill_scale_value(self, scale):
        if scale == "dexterity":
            return self.effective_dexterity()
        if scale == "intelligence":
            return self.effective_intelligence()
        return self.effective_strength()

    async def skill_combat_target(self, query):
        self.server.world.refresh()
        mob = None
        if self.combat_mob_key:
            mob = self.server.world.mobs.get(self.combat_mob_key)
            if not mob or not mob.alive or mob.room_id != self.character.room_id:
                self.combat_mob_key = None
                mob = None

        if mob is None:
            if not query.strip():
                await self.send("Ta umiejętność wymaga celu. Podaj nazwę przeciwnika.")
                return None
            if await self.reject_friendly_npc_attack(query):
                return None
            mob = self.server.world.find_mob(self.character.room_id, query)
            if not mob:
                await self.send("Nie widzę tutaj takiego przeciwnika.")
                return None
            if not self.server.engagement_allowed(self, mob):
                await self.send(
                    f"{MOB_TEMPLATES[mob.template_id]['name']} walczy już "
                    f"z graczem spoza twojej drużyny."
                )
                return None
            if not mob.engaged_by:
                mob.engaged_by = self.character.name
                mob.combat_turn = 0
                mob.player_hits = 0
            self.combat_mob_key = mob.key
            await self.server.broadcast_room(
                self.character.room_id,
                f"{self.character.name} rozpoczyna walkę umiejętnością klasową.",
                exclude=self,
            )
            await self.send(
                "Rozpoczyna się walka turowa. Po każdej twojej akcji przeciwnik wykonuje jedną turę."
            )
        return mob

    async def apply_boss_defense(self, mob, damage):
        if not mob or not mob.alive:
            return max(0, int(damage))

        template = MOB_TEMPLATES[mob.template_id]
        mechanic = template.get("boss_mechanic")
        if not mechanic:
            return max(0, int(damage))

        mob.player_hits += 1
        damage = max(0, int(damage))

        if mechanic == "grave_shield" and mob.player_hits % 3 == 0:
            reduced = max(1, damage // 2) if damage > 0 else 0
            await self.send(
                f"{template['name']} aktywuje Tarczę Grobowca. "
                f"Twoje obrażenia spadają z {damage} do {reduced}."
            )
            return reduced

        if mechanic == "ethereal_evade" and random.random() < 0.25:
            await self.send(
                f"{template['name']} rozpływa się w eterze i całkowicie unika trafienia."
            )
            return 0

        if mechanic == "hundred_lord" and mob.player_hits % 4 == 0:
            reduced = max(1, int(round(damage * 0.60))) if damage > 0 else 0
            await self.send(
                f"{template['name']} tworzy Pieczęć Stu Pięter. "
                f"Obrażenia zostają zredukowane z {damage} do {reduced}."
            )
            return reduced

        if mechanic == "crystal_lord" and mob.player_hits % 4 == 0:
            reduced = max(1, damage // 2) if damage > 0 else 0
            await self.send(
                f"{template['name']} aktywuje Kryształową Barierę. "
                f"Obrażenia spadają z {damage} do {reduced}."
            )
            return reduced

        return damage

    async def boss_attack_profile(self, mob, template):
        mob.combat_turn += 1
        turn = mob.combat_turn
        mechanic = template.get("boss_mechanic")
        profile = {
            "damage_type": template.get("damage_type", "physical"),
            "damage_multiplier": 1.0,
            "defense_factor": 1.0,
            "drain_pct": 0.0,
        }

        if mechanic == "bone_crush" and turn % 3 == 0:
            profile["damage_multiplier"] = 1.60
            await self.send(f"{template['name']} używa Kościanego Miażdżenia.")

        elif mechanic == "blood_drain" and turn % 3 == 0:
            profile["damage_multiplier"] = 1.25
            profile["drain_pct"] = 0.50
            await self.send(f"{template['name']} używa Krwawego Drenażu.")

        elif mechanic == "ash_curse" and turn % 3 == 0:
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] = 1.25
            profile["defense_factor"] = 0.50
            await self.send(
                f"{template['name']} rzuca Klątwę Popiołu. "
                "Połowa twojej obrony magicznej zostaje pominięta."
            )

        elif mechanic == "catacomb_echo" and turn % 4 == 0:
            profile["damage_multiplier"] = 1.70
            await self.send(
                f"{template['name']} wyzwala Echo Katakumb. "
                "To jedna, ale wyjątkowo silna odpowiedź bossa."
            )

        elif mechanic == "spectral_shift":
            profile["damage_type"] = "magic" if turn % 2 else "physical"
            await self.send(
                f"{template['name']} zmienia widmową fazę. "
                f"Ten kontratak jest "
                f"{'magiczny' if profile['damage_type'] == 'magic' else 'fizyczny'}."
            )

        elif mechanic == "necro_regen" and turn % 4 == 0:
            heal = max(1, int(round(template["max_hp"] * 0.07)))
            before = mob.hp
            mob.hp = min(template["max_hp"], mob.hp + heal)
            actual = mob.hp - before
            if actual > 0:
                await self.send(
                    f"{template['name']} używa Nekroregeneracji "
                    f"i odzyskuje {actual} HP. "
                    f"Boss: {mob.hp} z {template['max_hp']} HP."
                )

        elif mechanic == "bone_rage":
            if mob.hp <= template["max_hp"] // 2:
                profile["damage_multiplier"] = 1.50
                await self.send(
                    f"{template['name']} walczy w Furii Króla Kości."
                )

        elif mechanic == "hundred_lord":
            if mob.hp <= template["max_hp"] // 2:
                profile["damage_multiplier"] *= 1.25
            if turn % 3 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] *= 1.50
                profile["defense_factor"] = 0.75
                await self.send(
                    f"{template['name']} używa Załamania Duszy."
                )
            elif mob.hp <= template["max_hp"] // 2:
                await self.send(
                    f"{template['name']} walczy w drugiej fazie."
                )

        elif mechanic == "goblin_king" and turn % 3 == 0:
            profile["damage_multiplier"] = 1.50
            await self.send(
                f"{template['name']} wykonuje Królewską Szarżę."
            )

        elif mechanic == "shadow_alpha":
            if mob.hp <= template["max_hp"] // 2:
                profile["damage_multiplier"] = 1.40
                await self.send(
                    f"{template['name']} wpada w Szał Cienia."
                )

        elif mechanic == "ruin_warden" and turn % 4 == 0:
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] = 1.35
            profile["defense_factor"] = 0.75
            await self.send(
                f"{template['name']} uwalnia Runiczny Wybuch."
            )

        elif mechanic == "crystal_lord" and turn % 3 == 0:
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] = 1.45
            await self.send(
                f"{template['name']} wyzwala Kryształowy Promień."
            )

        elif mechanic == "bandit_combo" and turn % 3 == 0:
            profile["damage_multiplier"] = 1.40
            await self.send(
                f"{template['name']} wykonuje Brutalną Kombinację."
            )

        return profile

    async def enemy_counterattack(self, mob):
        if not mob or not mob.alive:
            return
        template = MOB_TEMPLATES[mob.template_id]
        profile = await self.boss_attack_profile(mob, template)

        if self.skill_evade:
            self.skill_evade = False
            await self.send(
                f"{template['name']} kontratakuje, ale aktywna umiejętność gwarantuje unik."
            )
            return

        if random.random() < self.dodge_chance():
            await self.send(
                f"{template['name']} kontratakuje, ale unikasz ciosu dzięki szybkości."
            )
            return

        damage_type = profile["damage_type"]
        if damage_type == "magic":
            full_reduction = self.magic_defense()
            defense_name = "obrona magiczna"
        else:
            full_reduction = self.defense()
            defense_name = "obrona fizyczna"

        reduction = max(
            0,
            int(round(full_reduction * profile["defense_factor"]))
        )
        raw_damage = int(round(
            template["damage"] * profile["damage_multiplier"]
        ))
        incoming = max(
            1,
            raw_damage + random.randint(-2, 2) - reduction
        )

        if self.skill_guard > 0:
            guard = self.skill_guard
            self.skill_guard = 0
            before = incoming
            incoming = max(1, incoming - guard)
            await self.send(
                f"Aktywna osłona redukuje trafienie dodatkowo o "
                f"{before - incoming} obrażeń."
            )

        if damage_type == "physical":
            physical_race_percent = (
                self.character.racial_physical_damage_reduction_percent()
            )
            if physical_race_percent > 0:
                before_physical_race = incoming
                incoming = max(
                    1,
                    int(round(
                        incoming
                        * (1.0 - physical_race_percent / 100.0)
                    ))
                )
                prevented = max(
                    0, before_physical_race - incoming
                )
                if prevented > 0:
                    await self.send(
                        f"Rasowa odporność Trolla redukuje obrażenia "
                        f"fizyczne o {physical_race_percent} procent, "
                        f"czyli o {prevented} obrażeń."
                    )

        incoming, racial_prevented = (
            self.character.apply_racial_damage_reduction(incoming)
        )
        if racial_prevented > 0:
            await self.send(
                f"Rasowa odporność Krasnoluda redukuje trafienie o "
                f"{self.character.racial_damage_reduction_percent()} procent, "
                f"czyli o {racial_prevented} obrażeń."
            )

        incoming, class_prevented = (
            self.character.apply_class_damage_reduction(incoming)
        )
        if class_prevented > 0:
            await self.send(
                f"Pasyw klasy {self.character.class_name} redukuje trafienie o "
                f"{self.character.class_damage_reduction_percent()} procent, "
                f"czyli o {class_prevented} obrażeń."
            )

        self.current_hp -= incoming
        await self.send(
            f"{template['name']} odpowiada. Typ obrażeń: "
            f"{'magiczne' if damage_type == 'magic' else 'fizyczne'}. "
            f"Otrzymujesz {incoming} obrażeń po redukcji przez {defense_name}. "
            f"Twoje życie: {max(0, self.current_hp)} z {self.max_hp()}."
        )

        drain_pct = float(profile.get("drain_pct", 0.0))
        if drain_pct > 0 and mob.alive:
            heal = max(1, int(round(incoming * drain_pct)))
            before = mob.hp
            mob.hp = min(template["max_hp"], mob.hp + heal)
            actual = mob.hp - before
            if actual > 0:
                await self.send(
                    f"{template['name']} wysysa życie i odzyskuje "
                    f"{actual} HP. Boss: {mob.hp} z "
                    f"{template['max_hp']} HP."
                )

        if self.current_hp <= 0:
            await self.die(template["name"])


    async def learn_class_skill(self, raw):
        if self.combat_mob_key:
            await self.send("Nie możesz uczyć się umiejętności podczas walki.")
            return

        teacher_id, teacher = self.teacher_here_for_active_class()
        if not teacher:
            await self.send(
                "Musisz być przy nauczycielu jednej ze swoich aktywnych klas. "
                "Wpisz teachers, aby sprawdzić lokacje."
            )
            return

        class_name = teacher["teacher_class"]
        class_skills = CLASS_SKILLS.get(class_name, [])
        value = raw.strip()
        normalized = self.normalize_description_query(value)
        if normalized.startswith("sie ") or normalized.startswith("się "):
            split = value.split(maxsplit=1)
            value = split[1] if len(split) > 1 else ""

        skill = None
        if value.strip().isdigit():
            number = int(value.strip())
            if 1 <= number <= len(class_skills):
                skill = class_skills[number - 1]
        else:
            wanted = self.normalize_description_query(value)
            for candidate in class_skills:
                names = [
                    candidate["name"], candidate["id"]
                ] + candidate.get("aliases", [])
                if any(
                    wanted == self.normalize_description_query(name)
                    for name in names
                ):
                    skill = candidate
                    break

        if not skill:
            await self.send(
                f"Nie rozpoznaję umiejętności klasy {class_name}. "
                f"Wpisz talk {teacher['name']}."
            )
            return

        if self.server.db.knows_skill(self.account_id, skill["id"]):
            await self.send(f"Już znasz umiejętność {skill['name']}.")
            return

        if self.character.soul_level < skill["unlock"]:
            await self.send(
                f"{skill['name']} wymaga Soul Level {skill['unlock']}, "
                f"a masz {self.character.soul_level}."
            )
            return

        self.server.db.learn_skill(self.account_id, skill["id"])
        await self.send(
            f"{teacher['name']} uczy cię umiejętności klasy "
            f"{class_name}: {skill['name']}."
        )
        await self.send(
            f"Nauczono. {skill['name']} zaczyna na Skill Level 1."
        )


    async def use_class_skill(self, raw):
        skill, target_text = self.find_skill_from_input(raw)
        if not skill:
            await self.send("Nie rozpoznaję tej umiejętności. Wpisz skills albo umiejetnosci.")
            return

        if self.character.soul_level < skill["unlock"]:
            await self.send(
                f"{skill['name']} wymaga Soul Level {skill['unlock']}."
            )
            return

        if not self.server.db.knows_skill(self.account_id, skill["id"]):
            skill_class = self.skill_class_name(skill)
            teacher_id, teacher = self.class_teacher(skill_class)
            await self.send(
                f"Nie znasz jeszcze umiejętności {skill['name']} klasy "
                f"{skill_class}. Musisz nauczyć się jej u {teacher['name']} "
                f"w lokacji {ROOMS[teacher['room']]['name']}."
            )
            return

        progress = self.server.db.skill_progress(self.account_id, skill["id"])
        skill_level = int(progress["level"])
        skill_power = skill_power_multiplier(skill_level)
        effective_cooldown = self.effective_skill_cooldown(skill, skill_level)

        now = time.time()
        ready_at = self.skill_cooldowns.get(skill["id"], 0)
        if ready_at > now:
            await self.send(
                f"{skill['name']} jest na cooldownie jeszcze {int(ready_at - now + 0.999)} sekund."
            )
            return

        mana_cost = skill.get("mana", 0)
        if mana_cost > self.current_mana:
            await self.send(
                f"Za mało Many. {skill['name']} wymaga {mana_cost}, a masz {self.current_mana}."
            )
            return

        kind = skill["kind"]
        offensive = kind in ("damage", "drain", "execute")
        mob = None
        if offensive:
            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
                await self.send("Auto-łowienie wyłączone z powodu walki.")
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
                await self.send("Auto-kopanie wyłączone z powodu walki.")
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
                await self.send("Auto-Drwalstwo wyłączone z powodu walki.")
            mob = await self.skill_combat_target(target_text)
            if not mob:
                return

        self.current_mana -= mana_cost
        self.skill_cooldowns[skill["id"]] = now + effective_cooldown

        if kind == "boost":
            base_boost = skill.get("boost", 1.0)
            scaled_boost = 1.0 + (base_boost - 1.0) * skill_power
            self.skill_damage_boost = max(self.skill_damage_boost, scaled_boost)
            await self.send(
                f"Używasz {skill['name']} na Skill Level {skill_level}. "
                f"Następna ofensywna umiejętność zostaje wzmocniona."
            )
            await self.grant_skill_use_xp(skill)
            if self.combat_mob_key:
                await self.enemy_counterattack(self.server.world.mobs.get(self.combat_mob_key))
            return

        if kind == "guard":
            scaled_guard = max(1, int(round(skill.get("guard", 0) * skill_power)))
            self.skill_guard = max(self.skill_guard, scaled_guard)
            await self.send(
                f"Używasz {skill['name']} na Skill Level {skill_level}. "
                f"Następne trafienie zostanie dodatkowo zredukowane o {self.skill_guard}."
            )
            await self.grant_skill_use_xp(skill)
            if mana_cost:
                await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
            if self.combat_mob_key:
                await self.enemy_counterattack(self.server.world.mobs.get(self.combat_mob_key))
            return

        if kind == "evade":
            self.skill_evade = True
            await self.send(
                f"Używasz {skill['name']} na Skill Level {skill_level}. "
                f"Następny kontratak zostanie uniknięty."
            )
            await self.grant_skill_use_xp(skill)
            if self.combat_mob_key:
                await self.enemy_counterattack(self.server.world.mobs.get(self.combat_mob_key))
            return

        if kind == "heal":
            max_hp = self.max_hp()
            heal_pct = min(
                0.75,
                skill.get("heal_pct", 0.25)
                * skill_power
                * self.character.racial_healing_multiplier()
                * self.character.class_healing_multiplier()
            )
            heal = max(1, int(max_hp * heal_pct))
            before = self.current_hp
            self.current_hp = min(max_hp, self.current_hp + heal)
            actual = self.current_hp - before
            await self.send(
                f"Używasz {skill['name']} na Skill Level {skill_level}. "
                f"Odzyskujesz {actual} HP. "
                f"Masz teraz {self.current_hp} z {max_hp} HP."
            )
            if self.character.racial_healing_bonus_percent() > 0:
                await self.send(
                    f"Bonus rasy {self.character.race}: "
                    f"+{self.character.racial_healing_bonus_percent()} procent mocy leczenia."
                )
            class_heal_bonus = int(
                round((self.character.class_healing_multiplier() - 1.0) * 100)
            )
            if class_heal_bonus > 0:
                await self.send(
                    f"Bonus aktywnych klas: +{class_heal_bonus} procent "
                    "mocy leczenia."
                )
            await self.grant_skill_use_xp(skill)
            if mana_cost:
                await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
            if self.combat_mob_key:
                await self.enemy_counterattack(self.server.world.mobs.get(self.combat_mob_key))
            return

        template = MOB_TEMPLATES[mob.template_id]
        scale = self.skill_scale_value(skill.get("scale", "strength"))
        multiplier = skill.get("mult", 1.0) * skill_power
        skill_class = self.skill_class_name(skill)
        skill_class_type = class_type_for_name(skill_class)
        if skill_class_type == "physical":
            multiplier *= self.character.class_physical_damage_multiplier()
            multiplier *= self.character.racial_physical_damage_multiplier()
        else:
            multiplier *= self.character.class_magic_damage_multiplier()
            multiplier *= self.character.racial_magic_damage_multiplier()
        multiplier *= self.character.racial_all_damage_multiplier()
        multiplier *= self.crypt_set_damage_multiplier()

        if kind == "execute":
            hp_ratio = mob.hp / max(1, template["max_hp"])
            if hp_ratio <= 0.35:
                multiplier *= skill.get("execute_mult", 1.5)
                await self.send("Egzekucyjny próg aktywny: przeciwnik jest osłabiony.")

        if self.skill_damage_boost > 1.0:
            multiplier *= self.skill_damage_boost
            self.skill_damage_boost = 1.0
            await self.send("Wzmocnienie ofensywne zwiększa siłę tej umiejętności.")

        damage = max(
            1,
            int(
                (self.character.soul_power() + scale) * multiplier
            ) + random.randint(-2, 3),
        )
        damage, critical = self.roll_critical_hit(damage)
        if critical:
            await self.send(
                f"TRAFIENIE KRYTYCZNE umiejętnością "
                f"{skill['name']}! Zręczność "
                f"{self.effective_dexterity()}. "
                f"Szansa: "
                f"{int(round(self.critical_chance() * 100))} procent."
            )
        damage = await self.apply_boss_defense(mob, damage)
        mob.hp -= damage
        await self.send(
            f"Używasz {skill['name']} na {template['name']}. Zadajesz {damage} obrażeń. "
            f"Przeciwnik: {max(0, mob.hp)} z {template['max_hp']} HP."
        )

        if kind == "drain":
            heal = max(
                1,
                int(damage * skill.get("drain_pct", 0.4) * self.character.class_drain_healing_multiplier())
            )
            before = self.current_hp
            self.current_hp = min(self.max_hp(), self.current_hp + heal)
            actual = self.current_hp - before
            await self.send(
                f"Wysysanie przywraca {actual} HP. Masz {self.current_hp} z {self.max_hp()} HP."
            )

        self_damage = skill.get("self_damage", 0)
        if skill.get("self_damage_pct"):
            self_damage += max(1, int(self.max_hp() * skill["self_damage_pct"]))
        if self_damage:
            self.current_hp -= self_damage
            await self.send(
                f"Koszt umiejętności: tracisz {self_damage} HP. "
                f"Masz {max(0, self.current_hp)} z {self.max_hp()} HP."
            )
            if self.current_hp <= 0:
                await self.die("własna umiejętność")
                return

        await self.grant_skill_use_xp(skill)

        if mana_cost:
            await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")

        if mob.hp <= 0:
            await self.mob_defeated(mob)
            return

        await self.enemy_counterattack(mob)

    def player_damage(self):
        c = self.character

        if c.class_type == "physical":
            # Siła odpowiada za atak fizyczny.
            base_damage = c.soul_power() + self.physical_power() + random.randint(-3, 4)
            return max(
                1,
                int(
                    round(
                        base_damage
                        * c.class_physical_damage_multiplier()
                        * c.racial_physical_damage_multiplier()
                        * c.racial_all_damage_multiplier()
                        * self.crypt_set_damage_multiplier()
                    )
                )
            )

        # Inteligencja odpowiada za moc czarów i mana.
        if self.current_mana >= 4:
            self.current_mana -= 4
            base_damage = c.soul_power() + self.spell_power() + random.randint(-3, 4)
            return max(
                1,
                int(
                    round(
                        base_damage
                        * c.class_magic_damage_multiplier()
                        * c.racial_magic_damage_multiplier()
                        * c.racial_all_damage_multiplier()
                        * self.crypt_set_damage_multiplier()
                    )
                )
            )

        # Bez many mag nadal może uderzyć Bronią Duszy, ale dużo słabiej.
        base_damage = c.soul_power() + self.spell_power() // 3 + random.randint(-2, 2)
        return max(
                1,
                int(
                    round(
                        base_damage
                        * c.class_magic_damage_multiplier()
                        * c.racial_magic_damage_multiplier()
                        * c.racial_all_damage_multiplier()
                        * self.crypt_set_damage_multiplier()
                    )
                )
            )

    async def attack(self, query):
        if self.auto_fishing or self.auto_fishing_task:
            await self.stop_auto_fishing(announce=False)
            await self.send("Auto-łowienie wyłączone z powodu walki.")
        if self.auto_mining or self.auto_mining_task:
            await self.stop_auto_mining(announce=False)
            await self.send("Auto-kopanie wyłączone z powodu walki.")
        if self.auto_woodcutting or self.auto_woodcutting_task:
            await self.stop_auto_woodcutting(announce=False)
            await self.send("Auto-Drwalstwo wyłączone z powodu walki.")
        self.server.world.refresh()
        mob = None

        if self.combat_mob_key:
            mob = self.server.world.mobs.get(self.combat_mob_key)
            if not mob or not mob.alive or mob.room_id != self.character.room_id:
                self.combat_mob_key = None
                mob = None

        if mob is None:
            if await self.reject_friendly_npc_attack(query):
                return
            mob = self.server.world.find_mob(self.character.room_id, query)
            if not mob:
                await self.send("Nie widzę tutaj takiego przeciwnika.")
                return
            if not self.server.engagement_allowed(self, mob):
                await self.send(
                    f"{MOB_TEMPLATES[mob.template_id]['name']} walczy już "
                    f"z graczem spoza twojej drużyny."
                )
                return
            if not mob.engaged_by:
                mob.engaged_by = self.character.name
                mob.combat_turn = 0
                mob.player_hits = 0
            self.combat_mob_key = mob.key
            await self.server.broadcast_room(
                self.character.room_id,
                f"{self.character.name} atakuje {MOB_TEMPLATES[mob.template_id]['name']}.",
                exclude=self,
            )
            await self.send(
                "Rozpoczyna się walka turowa. Po każdej twojej akcji przeciwnik wykonuje jedną turę."
            )

        template = MOB_TEMPLATES[mob.template_id]
        damage = self.player_damage()
        damage, critical = self.roll_critical_hit(damage)
        if critical:
            await self.send(
                f"TRAFIENIE KRYTYCZNE! Zręczność "
                f"{self.effective_dexterity()}. "
                f"Szansa: "
                f"{int(round(self.critical_chance() * 100))} procent."
            )
        damage = await self.apply_boss_defense(mob, damage)
        mob.hp -= damage
        await self.send(
            f"Atakujesz {template['name']}. Zadajesz {damage} obrażeń. "
            f"Przeciwnik: {max(0, mob.hp)} z {template['max_hp']} życia."
        )

        if mob.hp <= 0:
            await self.mob_defeated(mob)
            return

        await self.enemy_counterattack(mob)

    async def mob_defeated(self, mob):
        template = MOB_TEMPLATES[mob.template_id]
        mob.alive = False
        respawn_seconds = mob_respawn_seconds(template)
        mob.respawn_at = time.time() + respawn_seconds
        mob.engaged_by = None
        corpse=self.server.world.create_corpse(mob)
        if corpse:
            if corpse.items:
                await self.send(f"Pozostaje ciało: {corpse.mob_name}. Ma na sobie {len(corpse.items)} elementów ekwipunku. Wpisz ciało albo przeszukaj ciało.")
            else:
                await self.send(f"Pozostaje ciało: {corpse.mob_name}. Nie widać na nim ekwipunku.")

        for session in list(self.server.sessions):
            if session.combat_mob_key == mob.key:
                session.combat_mob_key = None

        recipients = self.server.party_sessions(
            self.account_id, same_room=self.character.room_id
        )
        if not recipients:
            recipients = [self]
        recipients = sorted(
            recipients, key=lambda s: s.character.name.lower()
        )
        count = len(recipients)

        boss_floor = (
            int(template.get("crypt_floor", 0))
            if template.get("crypt_boss")
            else 0
        )
        if boss_floor in CRYPT_BOSS_FLOORS:
            for session in recipients:
                before_checkpoint = (
                    self.server.db.crypt_portal(session.account_id)
                )
                after_checkpoint = (
                    self.server.db.unlock_crypt_portal(
                        session.account_id, boss_floor
                    )
                )
                if after_checkpoint > before_checkpoint:
                    await session.send(
                        f"Odblokowano Portal Krypty do piętra "
                        f"{boss_floor}."
                    )
                    if boss_floor < CRYPT_MAX_FLOOR:
                        await session.send(
                            "Portal odblokowany. Gdy boss się odrodzi, "
                            "znów będzie blokował zejście z tego piętra."
                        )
                    else:
                        await session.send(
                            "Odblokowano finałowy Portal Krypty do piętra 100."
                        )

        for session in recipients:
            if count > 1:
                await session.send(
                    f"Drużyna pokonuje: {template['name']}. "
                    f"Nagrody obejmują {count} obecnych członków."
                )
            else:
                await session.send(f"Pokonujesz: {template['name']}.")

        currency_rewards = {}
        for currency in ("silver", "gold", "mithril"):
            total = int(template.get(currency, 0))
            shares = {s.account_id: 0 for s in recipients}
            if total > 0:
                base_share, remainder = divmod(total, count)
                for session in recipients:
                    shares[session.account_id] = base_share
                shares[self.account_id] += remainder
            currency_rewards[currency] = shares

        for session in recipients:
            silver = currency_rewards["silver"][session.account_id]
            gold = currency_rewards["gold"][session.account_id]
            mithril = currency_rewards["mithril"][session.account_id]
            session.character.silver += silver
            session.character.gold += gold
            session.character.mithril += mithril

            if silver or gold or mithril:
                await session.send(
                    f"Twój udział waluty: {silver} srebra, "
                    f"{gold} złota, {mithril} mithrilu."
                )

            for msg in session.character.add_stat_progress(
                template["stat_reward"]
            ):
                await session.send(msg)
            await session.grant_soul_xp(
                template["soul_reward"]
            )

            class_xp_reward = int(
                template.get(
                    "class_xp_reward",
                    max(50, int(template["stat_reward"]) * 10),
                )
            )


            await session.grant_class_xp(class_xp_reward)

            target = template.get("quest_target")
            if target:
                changed = self.server.db.increment_quest(
                    session.account_id, target
                )
                for quest_id, progress in changed:
                    q = QUESTS[quest_id]
                    if progress >= q["needed"]:
                        await session.send(
                            f"Quest aktywny: {q['name']}. "
                            f"Postęp {progress} z {q['needed']}. "
                            "Cel wykonany, wróć do NPC."
                        )
                    else:
                        await session.send(
                            f"Quest aktywny: {q['name']}. "
                            f"Postęp {progress} z {q['needed']}."
                        )

            self.server.db.save_character(session.character)

        for item_id, chance in template["drops"].items():
            if random.random() <= chance:
                winner = random.choice(recipients)
                self.server.db.add_item(
                    winner.account_id, item_id, 1
                )
                await winner.send(
                    f"Drop drużyny trafia do ciebie: "
                    f"{ITEMS[item_id]['name']}."
                )
                if count > 1:
                    await self.server.party_broadcast(
                        self.account_id,
                        f"Drop: {ITEMS[item_id]['name']} otrzymuje "
                        f"{winner.character.name}.",
                        exclude=winner,
                    )

        await self.server.broadcast_room(
            self.character.room_id,
            (
                f"{self.character.name} i drużyna pokonują "
                f"{template['name']}."
                if count > 1
                else f"{self.character.name} pokonuje {template['name']}."
            ),
            exclude=self,
        )


    async def flee(self):
        if not self.combat_mob_key:
            await self.send("Nie jesteś w walce.")
            return
        mob = self.server.world.mobs.get(self.combat_mob_key)
        if mob:
            self.server.reassign_mob_engagement(mob, self)
        self.combat_mob_key = None
        self.skill_guard = 0
        self.skill_evade = False
        self.skill_damage_boost = 1.0
        await self.send("Wycofujesz się z walki.")

    async def die(self, killer):
        if self.resting or self.rest_task:
            await self.stop_rest(announce=False)
        if self.combat_mob_key:
            mob = self.server.world.mobs.get(self.combat_mob_key)
            if mob:
                self.server.reassign_mob_engagement(mob, self)
        self.combat_mob_key = None
        self.skill_guard = 0
        self.skill_evade = False
        self.skill_damage_boost = 1.0
        loss_silver = self.character.silver // 10
        loss_gold = self.character.gold // 10
        loss_mithril = self.character.mithril // 10
        self.character.silver -= loss_silver
        self.character.gold -= loss_gold
        self.character.mithril -= loss_mithril
        self.character.deaths += 1
        old_room = self.character.room_id
        self.character.room_id = "temple"
        self.current_hp = self.max_hp()
        self.current_mana = self.max_mana()
        self.server.db.save_character(self.character)
        await self.server.broadcast_room(
            old_room, f"{self.character.name} pada w walce.", exclude=self
        )
        await self.send(f"Pokonuje cię {killer}.")
        if loss_silver or loss_gold or loss_mithril:
            await self.send(
                f"Tracisz: {loss_silver} srebra, {loss_gold} złota, "
                f"{loss_mithril} mithrilu."
            )
        await self.send("Twoja dusza odradza się w Świątyni Odrodzenia.")
        await self.look()

    async def command_loop(self):
        while not self.closed:
            raw = await self.ask("> ")
            if raw is None:
                break
            parts = raw.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            command = COMMAND_ALIASES.get(command, command)
            direction = DIRECTION_ALIASES.get(command)

            rest_safe_commands = {
                "rest", "help", "describe", "changes", "look",
                "corpse", "cryptinfo", "exits", "map", "atlas",
                "where", "who", "stats", "declension", "skills",
                "skillnames", "soul", "money", "net", "bag",
                "woodpile", "herbbag", "professions", "ranks",
                "tools", "toolinfo_fishing", "toolinfo_mining",
                "toolinfo_woodcutting", "toolinfo_crafting",
                "toolinfo_cooking", "toolinfo_herbalism",
                "toolinfo_alchemy", "tiers", "location",
                "recipes", "inventory", "equipment", "shop",
                "teachers", "quests", "charisma", "multiclass",
            }

            if (
                self.resting
                and not direction
                and command not in rest_safe_commands
            ):
                await self.stop_rest(
                    announce=True,
                    reason="wykonujesz inną akcję",
                )

            if direction:
                await self.move(direction)
            elif command == "help":
                await self.show_help(args)
            elif command == "describe":
                await self.describe_target(args)
            elif command == "changes":
                await self.show_latest_changes()
            elif command == "look":
                await self.look()
            elif command == "corpse":
                await self.show_corpses(args)
            elif command == "lootcorpse":
                await self.loot_corpse(args)
            elif command == "cryptinfo":
                await self.show_crypt_info()
            elif command == "portal":
                await self.use_crypt_portal(args)
            elif command == "exits":
                await self.show_exits()
            elif command == "map":
                await self.show_map()
            elif command == "atlas":
                await self.show_atlas(args)
            elif command == "where":
                await self.show_where()
            elif command == "who":
                await self.who()
            elif command == "say":
                await self.say(args)
            elif command == "tell":
                await self.tell(args)
            elif command == "party":
                await self.handle_party(args)
            elif command == "partychat":
                await self.party_chat(args)
            elif command == "charisma":
                await self.show_charisma()
            elif command == "multiclass":
                await self.handle_multiclass(args)
            elif command == "rest":
                await self.handle_rest(args)
            elif command == "stats":
                await self.show_stats()
            elif command == "declension":
                await self.show_name_declension()
            elif command == "skills":
                await self.show_skills()
            elif command == "skillnames":
                await self.show_all_skill_names()
            elif command == "skill":
                await self.use_class_skill(args)
            elif command == "learn":
                await self.learn_class_skill(args)
            elif command == "soul":
                await self.show_soul()
            elif command == "money":
                await self.show_money()
            elif command == "exchange":
                await self.exchange(args)
            elif command == "net":
                await self.show_container("net")
            elif command == "bag":
                await self.show_container("bag")
            elif command == "woodpile":
                await self.show_container("woodpile")
            elif command == "herbbag":
                await self.show_container("herbbag")
            elif command == "put":
                await self.put_in_container(args)
            elif command == "take":
                await self.take_from_container(args)
            elif command == "professions":
                await self.show_professions()
            elif command == "ranks":
                await self.show_profession_ranks()
            elif command == "tools":
                await self.show_tools()
            elif command == "toolinfo_fishing":
                await self.show_single_tool("fishing")
            elif command == "toolinfo_mining":
                await self.show_single_tool("mining")
            elif command == "toolinfo_woodcutting":
                await self.show_single_tool("woodcutting")
            elif command == "toolinfo_crafting":
                await self.show_single_tool("crafting")
            elif command == "toolinfo_cooking":
                await self.show_single_tool("cooking")
            elif command == "toolinfo_herbalism":
                await self.show_single_tool("herbalism")
            elif command == "toolinfo_alchemy":
                await self.show_single_tool("alchemy")
            elif command == "tiers":
                await self.show_tool_tiers()
            elif command == "fish":
                mode = args.strip().lower()
                if mode in ("on", "start", "1"):
                    await self.set_auto_fishing(True)
                elif mode in ("off", "stop", "0"):
                    await self.set_auto_fishing(False)
                elif mode:
                    await self.send(
                        "Użycie: fish, fish on, fish off, low on albo low off."
                    )
                else:
                    await self.fish()
            elif command == "guide":
                await self.guide_to(args)
            elif command == "walk":
                if args.strip().lower().startswith("to "):
                    await self.guide_to(args)
                else:
                    await self.send("Użycie: walk to <location>.")
            elif command == "location":
                await self.show_location()
            elif command == "mine":
                mode = args.strip().lower()
                if mode in ("on", "start", "1"):
                    await self.set_auto_mining(True)
                elif mode in ("off", "stop", "0"):
                    await self.set_auto_mining(False)
                elif mode:
                    await self.send(
                        "Użycie: mine, mine on, mine off, kop on albo kop off."
                    )
                else:
                    await self.mine()
            elif command == "woodcut":
                mode = args.strip().lower()
                if mode in ("on", "start", "1"):
                    await self.set_auto_woodcutting(True)
                elif mode in ("off", "stop", "0"):
                    await self.set_auto_woodcutting(False)
                elif mode:
                    await self.send("Użycie: tnij, tnij on, tnij off, woodcut on albo woodcut off.")
                else:
                    await self.woodcut()
            elif command == "herb":
                mode = args.strip().lower()
                if mode in ("on", "start", "1"):
                    await self.set_auto_herbalism(True)
                elif mode in ("off", "stop", "0"):
                    await self.set_auto_herbalism(False)
                elif mode:
                    await self.send("Użycie: zbieraj, zbieraj on albo zbieraj off.")
                else:
                    await self.gather_herb()
            elif command == "sell":
                await self.sell_resource(args)
            elif command == "recipes":
                await self.show_recipes(args)
            elif command == "craft":
                if not args.strip():
                    await self.send("Użycie: craft <receptura>. Wpisz receptury.")
                else:
                    await self.craft_item(args)
            elif command == "cook":
                if not args.strip():
                    await self.send("Użycie: cook <potrawa>. Wpisz receptury cook.")
                else:
                    await self.cook_item(args)
            elif command == "alchemy":
                if not args.strip():
                    await self.send("Użycie: alchemia <mikstura>. Wpisz receptury alchemia.")
                else:
                    await self.alchemy_item(args)
            elif command == "inventory":
                await self.inventory()
            elif command == "equipment":
                await self.equipment()
            elif command == "equip":
                await self.equip_item(args)
            elif command == "use":
                await self.use_item(args)
            elif command == "shop":
                await self.shop()
            elif command == "buy":
                await self.buy(args)
            elif command == "talk":
                await self.talk(args)
            elif command == "teachers":
                await self.show_teachers()
            elif command == "quests":
                await self.quests()
            elif command == "attack":
                await self.attack(args)
            elif command == "flee":
                await self.flee()
            elif command == "unlock":
                await self.unlock()
            elif command == "save":
                self.server.db.save_character(self.character)
                await self.send("Postać zapisana.")
            elif command == "quit":
                await self.send("Do zobaczenia.")
                break
            else:
                await self.send("Nieznana komenda. Wpisz help.")

    async def close(self):
        if self.closed:
            return
        if self.resting or self.rest_task:
            await self.stop_rest(announce=False)
        if self.auto_fishing or self.auto_fishing_task:
            await self.stop_auto_fishing(announce=False)
        if self.auto_mining or self.auto_mining_task:
            await self.stop_auto_mining(announce=False)
        if self.auto_woodcutting or self.auto_woodcutting_task:
            await self.stop_auto_woodcutting(announce=False)
        if self.auto_herbalism or self.auto_herbalism_task:
            await self.stop_auto_herbalism(announce=False)
        if self.character:
            await self.leave_party(announce=False)
        self.closed = True
        if self.combat_mob_key:
            mob = self.server.world.mobs.get(self.combat_mob_key)
            if mob and self.character:
                self.server.reassign_mob_engagement(mob, self)
        if self.character:
            self.server.db.save_character(self.character)
            await self.server.broadcast_room(
                self.character.room_id, f"{self.character.name} opuszcza grę.", exclude=self
            )
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
            pass


class MudServer:
    def __init__(self):
        self.db = Database(DB_PATH)
        self.world = World()
        self.sessions = set()
        self.parties = {}
        self.party_invites = {}

    def account_online(self, account_id):
        return any(s.account_id == account_id and s.character for s in self.sessions)

    def find_character_session(self, name):
        for s in self.sessions:
            if s.character and s.character.name.lower() == name.lower():
                return s
        return None

    def session_by_account(self, account_id):
        for session in self.sessions:
            if session.account_id == account_id and session.character:
                return session
        return None

    def party_key_for_account(self, account_id):
        for leader_id, members in self.parties.items():
            if account_id in members:
                return leader_id
        return None

    def same_party(self, account_a, account_b):
        key_a = self.party_key_for_account(account_a)
        key_b = self.party_key_for_account(account_b)
        return key_a is not None and key_a == key_b

    def party_sessions(self, account_id, same_room=None):
        key = self.party_key_for_account(account_id)
        if key is None:
            session = self.session_by_account(account_id)
            if (
                session
                and (
                    same_room is None
                    or session.character.room_id == same_room
                )
            ):
                return [session]
            return []

        result = []
        for member_id in self.parties.get(key, set()):
            session = self.session_by_account(member_id)
            if not session:
                continue
            if (
                same_room is not None
                and session.character.room_id != same_room
            ):
                continue
            result.append(session)
        return result

    async def party_broadcast(self, account_id, message, exclude=None):
        for session in self.party_sessions(account_id):
            if session is not exclude:
                await session.send(message)

    def engagement_allowed(self, session, mob):
        if not mob.engaged_by or mob.engaged_by == session.character.name:
            return True
        owner = self.find_character_session(mob.engaged_by)
        return bool(
            owner
            and self.same_party(session.account_id, owner.account_id)
        )

    def reassign_mob_engagement(self, mob, leaving_session):
        if not mob or not mob.alive:
            return
        if mob.engaged_by != leaving_session.character.name:
            return
        candidates = [
            session
            for session in self.party_sessions(
                leaving_session.account_id, same_room=mob.room_id
            )
            if (
                session is not leaving_session
                and session.combat_mob_key == mob.key
            )
        ]
        mob.engaged_by = (
            candidates[0].character.name if candidates else None
        )

    async def broadcast_room(self, room_id, text, exclude=None):
        for s in list(self.sessions):
            if s is not exclude and s.character and s.character.room_id == room_id:
                await s.send(text)

    async def handle_client(self, reader, writer):
        if len(self.sessions) >= MAX_CLIENTS:
            writer.write(b"Serwer jest pelny.\r\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return
        session = Session(self, reader, writer)
        self.sessions.add(session)
        try:
            if await session.login_flow():
                await session.enter_world()
                await session.command_loop()
        except Exception as exc:
            print(f"[SESSION ERROR] {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
            try:
                await session.send("Wystąpił błąd sesji. Połączenie zostanie zamknięte.")
            except Exception:
                pass
        finally:
            await session.close()
            self.sessions.discard(session)

    async def run(self):
        server = await asyncio.start_server(self.handle_client, HOST, PORT)
        addresses = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
        print(f"Soulbound v{VERSION} World Core nasłuchuje: {addresses}", flush=True)
        print(f"HOST={HOST}", flush=True)
        print(f"PORT={PORT}", flush=True)
        print(
            "Railway TCP application port="
            + (os.getenv("RAILWAY_TCP_APPLICATION_PORT") or "brak"),
            flush=True,
        )
        print(f"Baza danych: {DB_PATH}", flush=True)
        print(f"Lokacje: {len(ROOMS)}", flush=True)
        print(f"Limit klientów: {MAX_CLIENTS}", flush=True)
        async with server:
            await server.serve_forever()


def main():
    try:
        asyncio.run(MudServer().run())
    except KeyboardInterrupt:
        print("\nSerwer zatrzymany.")


if __name__ == "__main__":
    main()
