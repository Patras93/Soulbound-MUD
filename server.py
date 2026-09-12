#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Soulbound v0.6.30 Character Name Declension
Wieloosobowy tekstowy MUD TCP/Telnet dla MUSHclienta/Mudleta.

Najważniejsze zasady projektu:
- postać NIE ma levelu ani XP postaci,
- statystyki rosną automatycznie,
- każda klasa rozwija automatycznie wszystkie pięć statystyk,
- Broń Duszy ma osobny Soul Level 1-100,
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
from dataclasses import dataclass
from typing import Optional

VERSION = "0.6.30"

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

STAT_GROWTH_THRESHOLD = 100
SOUL_MAX_LEVEL = 100
TIER2_LEVEL = 25
TIER3_LEVEL = 60
RESPAWN_SECONDS = 35

# Ekonomia:
# 100 srebra = 1 złoto
# 1000 złota = 1 mithril
SILVER_PER_GOLD = 100
GOLD_PER_MITHRIL = 1000

PROFESSION_MAX_LEVEL = 100
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
}

def normalize_profession_name(profession):
    value = str(profession).strip().lower()
    if value in ("fishing", "wedkarstwo", "wędkarstwo"):
        return "Wędkarstwo"
    if value in ("mining", "gornictwo", "górnictwo"):
        return "Górnictwo"
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

TOOL_MAX_LEVEL = 100
TOOL_MAX_TIER = 8
TOOL_TIER_THRESHOLDS = (1, 15, 30, 45, 60, 75, 90, 100)
TOOL_TIER_BONUS_CHANCES = (0.00, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15)

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

FRESHWATER_FISHING_ROOMS = {"riverbank", "stone_bridge", "meadow"}
MARINE_FISHING_ROOMS = {"sea_pier"}
FISHING_ROOMS = FRESHWATER_FISHING_ROOMS | MARINE_FISHING_ROOMS
MINING_ROOMS = {"cave_entrance", "cave_tunnel", "crystal_chamber"}

FISH_RESOURCE_IDS = {
    "small_fish", "river_carp", "silver_trout",
    "golden_trout", "ancient_sturgeon", "moon_eel",
    "herring", "mackerel", "salmon", "tuna", "swordfish",
    "bluefin_tuna", "reef_shark", "hammerhead_shark",
    "great_white_shark", "ghost_marlin",
    "sardine", "anchovy", "cod", "sea_bass", "haddock",
    "pollock", "flounder", "halibut",
}
ORE_RESOURCE_IDS = {
    "stone_chunk", "copper_ore", "iron_ore",
    "silver_ore", "gold_ore",
}

RACES = [
    ("Człowiek",
     "Wszechstronny. Wszystkie statystyki startują na równym poziomie. Dobry wybór do każdej klasy.",
     10, 10, 10, 10, 10),
    ("Ogr",
     "Bardzo silny i wytrzymały. Wysoka Siła zwiększa atak fizyczny, a wysoka Kondycja maksymalne HP. Słaba Inteligencja utrudnia grę klasami magicznymi.",
     14, 8, 14, 6, 8),
    ("Elf",
     "Bardzo zręczny i inteligentny. Wysoka Zręczność daje większą szybkość i unik, a Inteligencja zwiększa Manę i moc czarów. Ma niższą Siłę i Kondycję.",
     8, 14, 9, 13, 11),
    ("Krasnolud",
     "Silny i bardzo odporny. Wysoka Kondycja daje dużo HP, Siła poprawia atak fizyczny, a Siła Woli obronę magiczną. Jest mniej zręczny.",
     12, 9, 14, 9, 12),
    ("Ork",
     "Urodzony wojownik. Wysoka Siła i Kondycja dają mocne ciosy i dużo HP. Inteligencja i Siła Woli są niższe, więc gorzej sprawdza się w magii.",
     13, 10, 13, 7, 9),
    ("Niziołek",
     "Bardzo zręczny. Wysoka Zręczność oznacza dużą szybkość i lepszy unik. Ma niską Siłę, więc zadaje słabsze obrażenia fizyczne.",
     7, 14, 10, 10, 11),
    ("Mroczny Elf",
     "Zręczny i bardzo inteligentny. Dobrze łączy szybkość z magią. Wysoka Inteligencja zwiększa Manę i moc czarów, ale Kondycja jest niższa.",
     9, 13, 9, 14, 10),
    ("Gnom",
     "Bardzo inteligentny i odporny magicznie. Inteligencja zwiększa Manę i moc czarów, a Siła Woli obronę magiczną. Ma niską Siłę.",
     7, 12, 9, 14, 13),
    ("Smoczy",
     "Silny i wytrzymały, ale bardziej zrównoważony niż Ogr. Dobra Siła i Kondycja wspierają walkę fizyczną i przeżywalność.",
     13, 9, 13, 10, 10),
    ("Troll",
     "Największa surowa Siła i Kondycja. Zadaje bardzo mocne obrażenia fizyczne i ma dużo HP. Jest bardzo wolny i słaby magicznie.",
     15, 7, 15, 5, 8),
    ("Diablę",
     "Dobre predyspozycje magiczne. Inteligencja zwiększa Manę i moc czarów, a Siła Woli obronę magiczną. Statystyki fizyczne są przeciętne.",
     9, 11, 9, 13, 13),
    ("Aasimar",
     "Bardzo silna Siła Woli i dobra Inteligencja. Ma wysoką obronę magiczną, dobrą Manę i moc czarów. Dobrze pasuje do klas magicznych.",
     10, 10, 11, 12, 14),
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
    ),
    "Berserker": (
        "Klasa fizyczna nastawiona na bardzo wysokie obrażenia. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Broń Duszy ma wysoki bazowy potencjał ofensywny."
    ),
    "Łotrzyk": (
        "Klasa fizyczna nastawiona na szybkość i zwinność. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobrze korzysta z wysokiej Zręczności i uników."
    ),
    "Łowca": (
        "Klasa fizyczna walcząca z dystansu. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Najlepiej współpracuje z rasami o wysokiej Zręczności."
    ),
    "Mnich": (
        "Klasa fizyczna oparta na szybkości i kontroli ciała. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobrze skaluje się ze Zręcznością oraz Kondycją."
    ),
    "Strażnik": (
        "Klasa fizyczna nastawiona na przetrwanie. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobrze wykorzystuje wysoką Kondycję i cięższy pancerz."
    ),
    "Mag": (
        "Klasa magiczna. Inteligencja zwiększa Manę i moc czarów, "
        "a Siła Woli obronę magiczną. Automatycznie rozwija wszystkie pięć statystyk."
    ),
    "Nekromanta": (
        "Klasa magiczna oparta na mrocznej energii i silnych czarach. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobrze korzysta z wysokiej Inteligencji."
    ),
    "Kapłan": (
        "Klasa magiczna o defensywnym charakterze. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Wysoka Siła Woli wzmacnia obronę magiczną."
    ),
    "Czarownik": (
        "Ofensywna klasa magiczna z mocną Bronią Duszy. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobrze skaluje się z Inteligencją i dużą pulą Many."
    ),
    "Druid": (
        "Wszechstronna klasa magiczna związana z naturą. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Łączy dobrą moc czarów z obroną magiczną."
    ),
    "Psionik": (
        "Klasa magiczna oparta na mocy umysłu. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Najlepiej wykorzystuje wysoką Inteligencję i Siłę Woli."
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
        "desc": "Długie molo wychodzi daleko nad słoną wodę. To główne łowisko ryb morskich.",
        "exits": {"west": "harbor"},
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
        "desc": "Trawa porusza się falami. Na zachodzie widać ciemny gaj.",
        "exits": {"north": "south_gate", "west": "whisper_grove", "east": "riverbank"},
    },
    "whisper_grove": {
        "zone": "Dzicz", "name": "Gaj Szeptów",
        "desc": "Stare drzewa szepczą pod wpływem magicznego wiatru.",
        "exits": {"east": "meadow", "south": "deep_grove"},
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
        "desc": "Kamienny trakt prowadzi między zarośniętymi słupami granicznymi.",
        "exits": {"south": "north_gate", "north": "crossroads"},
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
    "staty": "stats", "status": "stats",
    "odmiana": "declension", "przypadki": "declension", "namecases": "declension", "declension": "declension",
    "skills": "skills", "umiejętności": "skills", "umiejetnosci": "skills", "zdolności": "skills", "zdolnosci": "skills",
    "skillnames": "skillnames", "nazwyskilli": "skillnames", "nazwyumiejetnosci": "skillnames", "nazwyumiejętności": "skillnames",
    "skill": "skill", "umiejętność": "skill", "umiejetnosc": "skill", "zdolność": "skill", "zdolnosc": "skill",
    "learn": "learn", "naucz": "learn", "ucz": "learn", "uczsię": "learn", "uczsie": "learn",
    "dusza": "soul",
    "ekwipunek": "inventory", "inv": "inventory", "i": "inventory",
    "załóż": "equip", "zaloz": "equip",
    "wyposażenie": "equipment", "wyposazenie": "equipment",
    "użyj": "use", "uzyj": "use",
    "sklep": "shop", "list": "shop", "lista": "shop",
    "kup": "buy",
    "mów": "say", "mow": "say", "powiedz": "say",
    "rozmawiaj": "talk",
    "teachers": "teachers", "nauczyciele": "teachers", "trenerzy": "teachers",
    "zadania": "quests", "questy": "quests",
    "atakuj": "attack", "walcz": "attack", "zabij": "attack", "kill": "attack",
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
    "sprzedaj": "sell",
    "profesje": "professions",
    "rangi": "ranks", "ranks": "ranks", "rangiprofesji": "ranks", "professionranks": "ranks",
    "narzędzia": "tools", "narzedzia": "tools",
    "tiers": "tiers", "tiery": "tiers", "tiernazwy": "tiers", "nazwytierow": "tiers", "nazwytierów": "tiers",
    "wyjście": "quit", "wyjscie": "quit",
}

ITEMS = {
    "healing_potion": {
        "name": "Mikstura leczenia", "type": "consumable", "price": 25, "currency": "silver",
        "desc": "Przywraca 35 punktów życia podczas walki.", "heal": 35,
    },
    "soul_elixir": {
        "name": "Eliksir Duszy", "type": "consumable", "price": None,
        "desc": "Daje 80 Soul XP.", "soul_xp": 80,
    },
    "leather_vest": {
        "name": "Skórzana kamizelka", "type": "armor", "slot": "body", "defense": 2,
        "price": 80, "currency": "silver", "desc": "Lekki pancerz. Obrona +2.",
    },
    "iron_helmet": {
        "name": "Żelazny hełm", "type": "armor", "slot": "head", "defense": 2,
        "price": 1, "currency": "gold",
        "desc": "Hełm kowalskiego zestawu. Slot głowa. Obrona fizyczna +2.",
    },
    "iron_guard": {
        "name": "Żelazny napierśnik", "type": "armor", "slot": "body", "defense": 4,
        "price": 2, "currency": "gold",
        "desc": "Główna część kowalskiego zestawu. Slot korpus. Obrona fizyczna +4.",
    },
    "iron_gauntlets": {
        "name": "Żelazne rękawice", "type": "armor", "slot": "hands", "defense": 1,
        "price": 1, "currency": "gold",
        "desc": "Rękawice kowalskiego zestawu. Slot dłonie. Obrona fizyczna +1.",
    },
    "iron_leggings": {
        "name": "Żelazne nogawice", "type": "armor", "slot": "legs", "defense": 3,
        "price": 2, "currency": "gold",
        "desc": "Osłona nóg kowalskiego zestawu. Slot nogi. Obrona fizyczna +3.",
    },
    "iron_boots": {
        "name": "Żelazne buty", "type": "armor", "slot": "feet", "defense": 1,
        "price": 1, "currency": "gold",
        "desc": "Buty kowalskiego zestawu. Slot stopy. Obrona fizyczna +1.",
    },
    "forge_charm": {
        "name": "Talizman Kowala", "type": "armor", "slot": "charm", "defense": 1,
        "price": 2, "currency": "gold",
        "desc": "Hartowany talizman ochronny. Slot talizman. Obrona fizyczna +1.",
    },
    "lucky_charm": {
        "name": "Talizman Wędrowca", "type": "armor", "slot": "charm", "defense": 1,
        "price": 95, "currency": "silver", "desc": "Drobny talizman. Obrona +1.",
    },
    "fishing_rod": {
        "name": "Wędka", "type": "tool", "tool_type": "fishing",
        "price": 1, "currency": "gold",
        "desc": "Podstawowe narzędzie do Wędkarstwa. Ma własny level 1-100.",
    },
    "pickaxe": {
        "name": "Kilof", "type": "tool", "tool_type": "mining",
        "price": 2, "currency": "gold",
        "desc": "Podstawowe narzędzie do Górnictwa. Ma własny level 1-100.",
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
    "inn": ["healing_potion"],
    "forge": [
        "iron_helmet",
        "iron_guard",
        "iron_gauntlets",
        "iron_leggings",
        "iron_boots",
        "forge_charm",
        "pickaxe",
    ],
}

NPCS = {
    "fisher_tomas": {
        "name": "Rybak Tomas", "room": "fish_market",
        "dialogue": "Jeśli naprawdę chcesz zostać wędkarzem, przynieś mi trzydzieści ryb.",
        "quest": "fisher_30_fish",
    },
    "priest_elor": {
        "name": "Kapłan Elor", "room": "temple",
        "dialogue": "W piwnicy zalęgły się szczury. Zagrażają zapasom świątyni. Zabij dziesięć.",
        "quest": "temple_rats",
    },
    "captain_arven": {
        "name": "Kapitan Arven", "room": "guard_hall",
        "dialogue": "Gobliny zajęły starą strażnicę. Potrzebujemy kogoś, kto oczyści szlak.",
        "quest": "goblin_problem",
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
    "priest_elor": (
        "Kapłan Świątyni Odrodzenia. Pomaga nowym bohaterom i pilnuje bezpieczeństwa "
        "świątynnych zapasów."
    ),
    "captain_arven": (
        "Dowódca miejskiej straży. Zleca zadania związane z bezpieczeństwem dróg, "
        "strażnic i okolic Miasta Dusz."
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
        "Broń Duszy jest na stałe związana z klasą. Ma osobny Soul Level 1-100 i Soul XP. "
        "Tier 2 odblokowuje się od Soul Level 25, a Tier 3 od Soul Level 60."
    ),
    "bron duszy": "Broń Duszy ma osobny Soul Level 1-100 i trzy Tiers.",
    "soul weapon": "Broń Duszy ma osobny Soul Level 1-100 i trzy Tiers.",
    "srebro": "Srebro jest podstawową walutą. 100 srebra można wymienić na 1 złoto.",
    "silver": "Srebro jest podstawową walutą. 100 srebra = 1 złoto.",
    "złoto": "Złoto jest walutą wyższego rzędu. 1000 złota można wymienić na 1 mithril.",
    "zloto": "Złoto jest walutą wyższego rzędu. 1000 złota = 1 mithril.",
    "gold": "Złoto jest walutą wyższego rzędu. 1000 złota = 1 mithril.",
    "mithril": (
        "Mithril jest najrzadszą walutą. 1 mithril = 1000 złota. "
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


LATEST_CHANGES_TITLE = "Soulbound v0.6.30 - Character Name Declension"
LATEST_CHANGES = [
    "Dodano odmianę imienia postaci przez 7 polskich przypadków.",
    "Etap odmiany pojawia się po wyborze rasy i klasy.",
    "Mianownik jest nazwą postaci, a gracz podaje pozostałe sześć form.",
    "Zapisywane są Mianownik, Dopełniacz, Celownik, Biernik, Narzędnik, Miejscownik i Wołacz.",
    "Dodano trwałe kolumny odmiany imienia w SQLite.",
    "Stare postacie automatycznie dostają dotychczasowe imię we wszystkich przypadkach.",
    "Dodano odmiana / przypadki / namecases do podglądu zapisanych form.",
    "Powitanie po wejściu do świata używa Wołacza.",
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
    "soul": "dusza", "soulweapon": "dusza",
    "money": "pieniadze", "economy": "pieniadze",
    "equipment": "ekwipunek", "items": "ekwipunek",
    "quests": "zadania", "quest": "zadania",
    "professions": "profesje",
    "fishing": "wedkarstwo", "fish": "wedkarstwo",
    "mining": "gornictwo", "mine": "gornictwo",
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
    "changes": "zmiany", "changelog": "zmiany",
}

HELP_TOPICS = {
    "podstawy": [
        "Soulbound nie ma levelu postaci. Rozwój bohatera odbywa się przez pięć statystyk.",
        "Wszystkie klasy automatycznie rozwijają Siłę, Zręczność, Kondycję, Inteligencję i Siłę Woli.",
        "Broń Duszy ma osobny Soul Level 1-100.",
        "Najważniejsze na start: look, exits, stats, inventory, quests, help komendy.",
        "Użyj opis <nazwa>, aby uzyskać szczegółowy opis elementu świata.",
    ],
    "nawigacja": [
        "Ruch ręczny: north, south, east, west, up, down lub n, s, e, w, u, d.",
        "where albo gdzie pokazuje aktualną lokację.",
        "location albo lokalizacja pokazuje lokację, strefę i wyjścia.",
        "map albo mapa pokazuje listę lokacji.",
        "prowadz <lokacja> albo walk to <location> automatycznie znajduje najkrótszą trasę.",
        "Ruch zatrzymuje auto-łowienie i auto-kopanie.",
    ],
    "odmiana_imienia": [
        "Po wyborze rasy i klasy kreator zapisuje odmianę imienia przez 7 polskich przypadków.",
        "Mianownik jest nazwą postaci wybraną na początku kreatora.",
        "Następnie podajesz Dopełniacz, Celownik, Biernik, Narzędnik, Miejscownik i Wołacz.",
        "odmiana albo przypadki pokazuje wszystkie zapisane formy.",
        "Formy są trwale zapisane w SQLite i mogą być używane w komunikatach gry.",
        "Stare postacie bez odmiany dostają dotychczasowe imię we wszystkich przypadkach.",
    ],
    "statystyki": [
        "Siła: obrażenia fizyczne.",
        "Zręczność: Szybkość i szansa uniku.",
        "Kondycja: maksymalne HP; każdy punkt daje 5 HP.",
        "Inteligencja: Mana i Moc czarów klas magicznych.",
        "Siła Woli: obrona magiczna.",
        "Każdy pełny próg Rozwoju statystyk zwiększa wszystkie pięć statystyk o 1.",
        "Komenda stats pokazuje wartości podstawowe i pochodne.",
    ],
    "walka": [
        "Walka jest turowa: gracz wykonuje jedną akcję, potem przeciwnik wykonuje jedną akcję.",
        "Akcją może być attack, ofensywny skill, leczenie, osłona, unik, wzmocnienie albo mikstura.",
        "Rozpocznij lub kontynuuj walkę: attack, atakuj, zabij albo kill <przeciwnik>.",
        "Jeśli przeciwnik przeżyje twoją akcję, wykonuje dokładnie jedną turę odpowiedzi.",
        "Zręczność może pozwolić uniknąć ataku w turze przeciwnika.",
        "Pancerz redukuje obrażenia fizyczne; Siła Woli redukuje obrażenia magiczne.",
        "flee albo uciekaj kończy walkę.",
        "Po śmierci odradzasz się w Świątyni Odrodzenia i tracisz 10 procent każdej waluty.",
    ],
    "dusza": [
        "Każda klasa ma własną stałą Broń Duszy.",
        "Broń Duszy ma Soul Level 1-100 i osobny Soul XP.",
        "Soul Level rośnie znacznie wolniej niż zwykły rozwój statystyk.",
        "Tier 2 wymaga Soul Level 25. Tier 3 wymaga Soul Level 60.",
        "Gdy Tier jest gotowy, użyj unlock.",
        "Komenda soul pokazuje aktualny stan Broni Duszy.",
    ],
    "pieniadze": [
        "Waluty: srebro, złoto, mithril.",
        "100 srebra = 1 złoto.",
        "1000 złota = 1 mithril.",
        "money pokazuje stan portfela.",
        "exchange pokazuje kursy; exchange gold i exchange mithril wykonują wymianę.",
        "Mithril jest najrzadszą walutą.",
    ],
    "ekwipunek": [
        "inventory albo i pokazuje zwykły ekwipunek i opisy przedmiotów.",
        "equipment pokazuje założone elementy na slotach: głowa, korpus, dłonie, nogi, stopy i talizman.",
        "equip <przedmiot> zakłada wyposażenie.",
        "use <przedmiot> używa przedmiotu zużywalnego.",
        "Po wypiciu Mikstury leczenia serwer podaje aktualne i maksymalne HP.",
        "opis <przedmiot> pokazuje szczegółowe działanie oraz ceny.",
    ],
    "zadania": [
        "talk <NPC> rozpoczyna rozmowę i może przyjąć lub oddać zadanie.",
        "quests pokazuje dziennik zadań.",
        "Zadania mogą wymagać zabijania przeciwników albo przynoszenia przedmiotów i surowców.",
        "opis <nazwa zadania> pokazuje cel i nagrody zadania.",
    ],
    "profesje": [
        "Profesje mają własne poziomy 1-100 i własny XP.",
        "Wędkarstwo i Górnictwo rozwijają się niezależnie.",
        "Wędka i Kilof mają osobne od profesji poziomy 1-100 oraz osobny XP.",
        "Wędka i Kilof mają po 8 Tierów: progi level 1, 15, 30, 45, 60, 75, 90 i 100.",
        "Wędkarstwo i Górnictwo mają po 8 nazwanych rang na progach 1, 15, 30, 45, 60, 75, 90 i 100.",
        "Rangi profesji: Uczeń, Adept, Czeladnik, Specjalista, Ekspert, Mistrz, Arcymistrz, Legenda.",
        "Każdy Tier Wędki i Kilofa ma własną unikalną nazwę.",
        "professions albo profesje pokazuje profesje.",
        "tools albo narzedzia pokazuje poziomy narzędzi.",
        "tiers albo tiery pokazuje pełną listę nazw wszystkich Tierów.",
    ],
    "wedkarstwo": [
        "Do łowienia potrzebujesz Wędki.",
        "fish, wedkuj albo low wykonuje pojedynczy połów.",
        "low on albo fish on włącza auto-łowienie; low off albo fish off je wyłącza.",
        "Każda złowiona ryba trafia automatycznie do Siatki na ryby, nigdy do zwykłego ekwipunku.",
        "Łowiska słodkowodne i morskie mają osobne tabele połowów.",
        "Morskie Molo służy do połowów morskich. Śledź wymaga minimum levelu 30 Wędki.",
        "Wędka ma 8 Tierów. Wyższy Tier daje rosnącą szansę na drugi egzemplarz złowionej ryby.",
    ],
    "gornictwo": [
        "Do kopania potrzebujesz Kilofa.",
        "mine albo kop wykonuje pojedyncze wydobycie.",
        "kop on albo mine on włącza auto-kopanie; kop off albo mine off je wyłącza.",
        "Każda zwykła wydobyta ruda trafia automatycznie do Sakwy górniczej, nigdy do zwykłego ekwipunku.",
        "Kilof od levelu 80 może niezwykle rzadko wydobyć bezpośrednio czysty mithril.",
        "Czysty mithril trafia od razu do portfela, a nie do Sakwy.",
        "Kilof ma 8 Tierów. Wyższy Tier daje rosnącą szansę na dodatkową zwykłą rudę.",
        "Bonus Tieru Kilofa nigdy nie podwaja czystego mithrilu.",
    ],
    "pojemniki": [
        "Siatka na ryby i Sakwa górnicza są osobnymi trwałymi magazynami.",
        "net albo siatka pokazuje ryby.",
        "bag albo sakwa pokazuje rudy.",
        "put fish net lub wloz ryba siatka przenosi ryby ze zwykłego ekwipunku.",
        "put ore bag lub wloz ruda sakwa przenosi rudy.",
        "take <przedmiot> net/bag albo wyjmij <przedmiot> siatka/sakwa wyjmuje surowiec.",
    ],
    "sklepy": [
        "shop, sklep, list albo lista pokazuje ofertę sprzedawcy w aktualnej lokacji.",
        "buy albo kup <przedmiot> kupuje rzecz.",
        "sell albo sprzedaj <ryba lub ruda> sprzedaje surowiec.",
        "opis <przedmiot> pozwala sprawdzić działanie, cenę kupna i wartość sprzedaży.",
        "Kowal Doran w Kuźni Dusz sprzedaje pełny żelazny zestaw ochronny na sześć slotów oraz Kilof.",
    ],
    "gracze": [
        "who pokazuje graczy online.",
        "say <tekst> mówi do osób w tej samej lokacji.",
        "tell <gracz> <tekst> wysyła wiadomość prywatną.",
        "Ruch innych graczy jest ogłaszany w lokacji.",
    ],
    "smierc": [
        "Po śmierci wracasz do Świątyni Odrodzenia.",
        "Tracisz 10 procent posiadanego srebra, złota i mithrilu, liczone osobno.",
        "Licznik śmierci jest widoczny w stats.",
    ],
    "rasy": [
        "W grze jest 12 ras. Rasa ustala statystyki startowe.",
        "Wpisz opis <nazwa rasy>, np. opis Elf albo opis Troll, aby poznać dokładne wartości i zalety.",
        "Wszystkie rasy mogą wybrać każdą klasę.",
    ],
    "klasy": [
        "W grze jest 12 klas: 6 fizycznych i 6 magicznych.",
        "Każda klasa rozwija wszystkie pięć statystyk.",
        "Klasa określa typ walki i przypisaną Broń Duszy.",
        "Wpisz opis <nazwa klasy>, np. opis Mag albo opis Wojownik.",
    ],
    "umiejetnosci": [
        "Każda klasa ma własne aktywne umiejętności; Kapłan ma dodatkowo Małe Leczenie dla początkujących.",
        "Soul Level 1, 25 i 60 są wymaganiami do nauki u nauczyciela.",
        "skills albo umiejetnosci pokazuje, co znasz, czego możesz się nauczyć i gdzie jest nauczyciel.",
        "skill <nazwa lub numer> [cel] albo umiejetnosc <nazwa lub numer> [cel] używa umiejętności.",
        "Jeśli już walczysz, ofensywny skill może użyć bieżącego celu bez ponownego wpisywania nazwy.",
        "Klasy magiczne wydają Manę. Klasy fizyczne są ograniczane głównie cooldownami.",
        "Każdy nauczony skill ma własny Skill Level 1-100, osobny XP i liczbę użyć.",
        "Wyższy Skill Level wzmacnia działanie skilla i skraca jego cooldown.",
    ],
    "nazwy_skilli": [
        "skillnames albo nazwyskilli pokazuje wszystkie 37 nazw skilli pogrupowane według klas.",
        "Większość klas ma 3 skille, a Kapłan ma 4 dzięki startowemu Małemu Leczeniu.",
        "Nazwy można później podawać w skill <nazwa> oraz naucz <nazwa>.",
    ],
    "nauczyciele": [
        "W Sali Gildii jest 12 nauczycieli klasowych, po jednym dla każdej klasy.",
        "teachers albo nauczyciele pokazuje listę nauczycieli.",
        "talk <nauczyciel> uruchamia lekcję o klasie i jej umiejętnościach.",
        "Nauczyciel twojej klasy faktycznie uczy skilli po spełnieniu wymaganego Soul Level.",
        "Nauczyciele nie zmieniają klasy postaci. Nauczone skille są zapisywane w SQLite.",
    ],
    "opisy": [
        "Komenda opis bez argumentu opisuje aktualną lokację.",
        "opis <przedmiot> pokazuje działanie, typ i ceny.",
        "opis <NPC> pokazuje rolę, lokację i powiązane zadanie.",
        "opis <przeciwnik> pokazuje HP, obrażenia, typ ataku i nagrody.",
        "opis <lokacja> pokazuje strefę, opis, wyjścia i specjalne funkcje.",
        "opis <zadanie>, opis <rasa>, opis <klasa>, opis <statystyka> i opis <waluta> także działają.",
    ],
    "zmiany": [
        "changes, zmiany albo changelog pokazuje najnowszą wersję i tylko najnowsze zmiany.",
        "Pełna historia nadal znajduje się w CHANGELOG_PL.txt w paczce źródłowej.",
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
        "reward_silver": 0, "reward_gold": 200, "reward_mithril": 0,
        "reward_items": {},
    },
    "temple_rats": {
        "name": "Szczury pod świątynią",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "temple_rat", "needed": 10,
        "description": "Zejdź do piwnicy Świątyni Odrodzenia i zabij 10 szczurów.",
        "reward_stat_progress": 120,
        "reward_silver": 0, "reward_gold": 2, "reward_mithril": 0,
        "reward_items": {"healing_potion": 1},
    },
    "goblin_problem": {
        "name": "Problem goblinów",
        "giver": "Kapitan Arven",
        "kind": "kill", "target": "goblin", "needed": 3,
        "description": "Pokonaj 3 gobliny w ruinach i obozie.",
        "reward_silver": 120, "reward_gold": 1, "reward_mithril": 0,
        "reward_items": {"healing_potion": 2},
    },
    "shadow_wolves": {
        "name": "Cienie w gaju",
        "giver": "Zielarka Mira",
        "kind": "kill", "target": "shadow_wolf", "needed": 2,
        "description": "Pokonaj 2 Wilki Cienia w Gaju Szeptów.",
        "reward_silver": 90, "reward_gold": 1, "reward_mithril": 0,
        "reward_items": {"healing_potion": 1},
    },
    "soul_shards": {
        "name": "Odłamki dla kowala",
        "giver": "Kowal Doran",
        "kind": "collect", "target": "soul_shard", "needed": 3,
        "description": "Przynieś 3 Odłamki Duszy z krypty.",
        "reward_silver": 0, "reward_gold": 3, "reward_mithril": 1,
        "reward_items": {"soul_elixir": 1},
    },
}

MOB_TEMPLATES = {
    "temple_rat": {
        "name": "Szczur Świątynny", "max_hp": 28, "damage": 3, "damage_type": "physical",
        "silver": 6, "gold": 0, "mithril": 0,
        "stat_reward": 8, "soul_reward": 1,
        "drops": {}, "quest_target": "temple_rat",
    },
    "training_dummy": {
        "name": "Żywy Manekin", "max_hp": 45, "damage": 4, "damage_type": "physical",
        "silver": 12, "gold": 0, "mithril": 0, "stat_reward": 18, "soul_reward": 4,
        "drops": {}, "quest_target": None,
    },
    "goblin": {
        "name": "Goblin", "max_hp": 60, "damage": 7, "damage_type": "physical",
        "silver": 28, "gold": 0, "mithril": 0, "stat_reward": 30, "soul_reward": 7,
        "drops": {"healing_potion": 0.08}, "quest_target": "goblin",
    },
    "goblin_brute": {
        "name": "Gobliński Osiłek", "max_hp": 85, "damage": 10, "damage_type": "physical",
        "silver": 45, "gold": 1, "mithril": 0, "stat_reward": 38, "soul_reward": 9,
        "drops": {"healing_potion": 0.12}, "quest_target": "goblin",
    },
    "shadow_wolf": {
        "name": "Wilk Cienia", "max_hp": 70, "damage": 9, "damage_type": "physical",
        "silver": 32, "gold": 0, "mithril": 0, "stat_reward": 34, "soul_reward": 8,
        "drops": {"wolf_fang": 0.45}, "quest_target": "shadow_wolf",
    },
    "bandit": {
        "name": "Bandyta", "max_hp": 75, "damage": 9, "damage_type": "physical",
        "silver": 40, "gold": 0, "mithril": 0, "stat_reward": 35, "soul_reward": 8,
        "drops": {"healing_potion": 0.10}, "quest_target": None,
    },
    "skeleton": {
        "name": "Szkielet Strażnik", "max_hp": 90, "damage": 11, "damage_type": "physical",
        "silver": 30, "gold": 1, "mithril": 0, "stat_reward": 42, "soul_reward": 11,
        "drops": {"soul_shard": 0.55}, "quest_target": None,
    },
    "crypt_wraith": {
        "name": "Upiór Krypty", "max_hp": 120, "damage": 14, "damage_type": "magic",
        "silver": 0, "gold": 2, "mithril": 1, "stat_reward": 55, "soul_reward": 15,
        "drops": {"soul_shard": 0.85}, "quest_target": None,
    },
    "crystal_guardian": {
        "name": "Kryształowy Strażnik", "max_hp": 140, "damage": 15, "damage_type": "magic",
        "silver": 0, "gold": 4, "mithril": 1, "stat_reward": 60, "soul_reward": 18,
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
    ("deep_grove", "shadow_wolf"),
    ("whisper_grove", "shadow_wolf"),
    ("ruined_watchtower", "goblin"),
    ("goblin_camp", "goblin"),
    ("goblin_camp", "goblin_brute"),
    ("crypt_hall", "skeleton"),
    ("crypt_depths", "crypt_wraith"),
    ("crystal_chamber", "crystal_guardian"),
]

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
                deaths INTEGER NOT NULL DEFAULT 0,
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
            "silver": "INTEGER NOT NULL DEFAULT 250",
            "gold": "INTEGER NOT NULL DEFAULT 2",
            "mithril": "INTEGER NOT NULL DEFAULT 0",
            "deaths": "INTEGER NOT NULL DEFAULT 0",
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
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,1,0,1,'square',250,2,0,0)
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
        self.conn.commit()

    def save_character(self, c):
        self.conn.execute(
            """
            UPDATE characters SET
                strength=?, dexterity=?, constitution=?, intelligence=?, willpower=?,
                stat_progress=?, soul_level=?, soul_xp=?, soul_tier=?, room_id=?,
                silver=?, gold=?, mithril=?, deaths=?
            WHERE account_id=?
            """,
            (
                c.strength, c.dexterity, c.constitution, c.intelligence, c.willpower,
                c.stat_progress, c.soul_level, c.soul_xp, c.soul_tier, c.room_id,
                c.silver, c.gold, c.mithril, c.deaths, c.account_id,
            ),
        )
        self.conn.commit()

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
            "INSERT OR IGNORE INTO quests(account_id,quest_id,status,progress) VALUES(?,?, 'active',0)",
            (account_id, quest_id),
        )
        self.conn.commit()

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
            "UPDATE quests SET status='completed' WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
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
            deaths=row["deaths"],
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
        return 40 + self.constitution * 5

    def physical_power(self):
        # Siła odpowiada za obrażenia fizyczne.
        return self.strength

    def speed(self):
        # Zręczność odpowiada za szybkość.
        return 10 + self.dexterity * 2

    def dodge_chance(self):
        # Szybkość przekłada się na szansę uniknięcia kontrataku.
        # Limit 35%, żeby Zręczność nie dawała pełnej nietykalności.
        return min(0.35, max(0.0, (self.speed() - 20) / 300.0))

    def max_mana(self):
        if self.class_type != "magic":
            return 0
        # Inteligencja zwiększa pulę many.
        return 20 + self.intelligence * 5

    def spell_power(self):
        # Inteligencja zwiększa siłę czarów.
        return self.intelligence

    def magic_defense(self):
        # Siła Woli odpowiada wyłącznie za obronę magiczną.
        return max(0, self.willpower // 2)

    def soul_xp_to_next(self):
        if self.soul_level >= SOUL_MAX_LEVEL:
            return 0
        # Soul Level ma rozwijać się wolniej niż wcześniej.
        return 180 + (self.soul_level - 1) * 60

    def soul_power(self):
        return self.weapon_base + self.soul_level - 1 + {1: 0, 2: 12, 3: 30}[self.soul_tier]

    def can_unlock(self):
        if self.soul_tier == 1 and self.soul_level >= TIER2_LEVEL:
            return 2
        if self.soul_tier == 2 and self.soul_level >= TIER3_LEVEL:
            return 3
        return None

    def add_stat_progress(self, amount):
        messages = [f"Postęp rozwoju statystyk +{amount}."]
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
            return ["Broń Duszy ma już Soul Level 100."]
        messages = [f"Broń Duszy otrzymuje {amount} Soul XP."]
        self.soul_xp += amount
        while self.soul_level < SOUL_MAX_LEVEL:
            needed = self.soul_xp_to_next()
            if self.soul_xp < needed:
                break
            self.soul_xp -= needed
            self.soul_level += 1
            messages.append(f"Broń Duszy osiąga Soul Level {self.soul_level}.")
            if self.soul_level == TIER2_LEVEL and self.soul_tier == 1:
                messages.append("Tier 2 jest gotowy do odblokowania. Wpisz unlock.")
            if self.soul_level == TIER3_LEVEL and self.soul_tier == 2:
                messages.append("Tier 3 jest gotowy do odblokowania. Wpisz unlock.")
        if self.soul_level >= SOUL_MAX_LEVEL:
            self.soul_level = SOUL_MAX_LEVEL
            self.soul_xp = 0
            messages.append("Osiągnięto maksymalny Soul Level 100.")
        return messages


@dataclass
class MobState:
    key: str
    room_id: str
    template_id: str
    hp: int
    alive: bool = True
    respawn_at: float = 0.0
    engaged_by: Optional[str] = None


class World:
    def __init__(self):
        self.mobs = {}
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
        for mob in self.mobs.values():
            if not mob.alive and mob.respawn_at <= now:
                mob.alive = True
                mob.hp = MOB_TEMPLATES[mob.template_id]["max_hp"]
                mob.engaged_by = None

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
        self.guiding = False
        self.skill_cooldowns = {}
        self.skill_guard = 0
        self.skill_evade = False
        self.skill_damage_boost = 1.0

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
        await self.send("Na start otrzymujesz 250 srebra, 2 złota i 2 Mikstury leczenia.")
        return True

    async def enter_world(self):
        self.current_hp = self.character.max_hp()
        self.current_mana = self.character.max_mana()
        await self.server.broadcast_room(
            self.character.room_id, f"{self.character.name} pojawia się w okolicy.", exclude=self
        )
        await self.send(
            f"Witaj, {self.character.name_case('voc')}. "
            f"Soulbound v{VERSION} World Core."
        )
        await self.send("Wpisz help, aby poznać komendy.")
        await self.look()

    def defense(self):
        total = 0
        for row in self.server.db.equipment(self.account_id):
            item = ITEMS.get(row["item_id"])
            if item:
                total += item.get("defense", 0)
        return total

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

        others = [
            s.character.name for s in self.server.sessions
            if s is not self and s.character and s.character.room_id == self.character.room_id
        ]
        if others:
            await self.send("Gracze tutaj: " + ", ".join(sorted(others, key=str.lower)) + ".")
        await self.show_exits()

    async def show_exits(self):
        room = ROOMS[self.character.room_id]
        exits = ", ".join(room["exits"].keys()) if room["exits"] else "brak"
        await self.send("Wyjścia: " + exits + ".")

    async def show_map(self):
        current = self.character.room_id
        await self.send("MAPA ODKRYTEGO ŚWIATA")
        for zone in ("Miasto Dusz", "Dzicz", "Podziemia"):
            await self.send(zone + ":")
            entries = []
            for room_id, room in ROOMS.items():
                if room["zone"] == zone:
                    marker = " [TU]" if room_id == current else ""
                    entries.append(room["name"] + marker)
            await self.send("; ".join(entries) + ".")

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
            "map - lista lokacji świata",
            "where - aktualna lokacja",
            "location / lokalizacja - lokacja, strefa i wyjścia",
            "north/south/east/west/up/down lub n/s/e/w/u/d - ruch",
            "prowadz lokacja / walk to location - automatyczne prowadzenie",
            "who - gracze online",
            "say tekst - rozmowa lokalna",
            "tell gracz tekst - wiadomość prywatna",
            "stats - statystyki",
            "odmiana / przypadki - pokaż 7 form imienia postaci",
            "skills / umiejetnosci - lista umiejętności twojej klasy",
            "skillnames / nazwyskilli - wszystkie nazwy skilli wszystkich klas",
            "skill / umiejetnosc <nazwa lub numer> [cel] - użyj umiejętności",
            "learn / naucz / ucz <nazwa lub numer> - naucz się skilla u nauczyciela",
            "soul - Broń Duszy",
            "money - srebro, złoto i mithril",
            "exchange - kurs wymiany",
            "exchange gold / exchange mithril - wymiana walut",
            "professions / profesje - Wędkarstwo i Górnictwo",
            "rangi / ranks - pełna lista nazw rang Wędkarstwa i Górnictwa",
            "tools / narzedzia - level Wędki i Kilofa",
            "tiers / tiery / nazwytierow - pełna lista nazw 8 Tierów Wędki i Kilofa",
            "fish / wedkuj / low - pojedynczy połów",
            "low on / fish on - auto-łowienie",
            "low off / fish off - wyłącz auto-łowienie",
            "mine / kop - pojedyncze wydobycie",
            "kop on / mine on - auto-kopanie",
            "kop off / mine off - wyłącz auto-kopanie",
            "net / siatka - Siatka na ryby",
            "bag / sakwa - Sakwa górnicza",
            "put fish net / wloz ryba siatka - przenieś ryby do Siatki",
            "put ore bag / wloz ruda sakwa - przenieś rudy do Sakwy",
            "take przedmiot net/bag / wyjmij przedmiot siatka/sakwa - wyjmij surowiec",
            "sell / sprzedaj przedmiot - sprzedaj rybę lub rudę",
            "inventory / i - zwykły ekwipunek",
            "equipment - założone wyposażenie",
            "equip przedmiot - załóż pancerz lub talizman",
            "use przedmiot - użyj przedmiotu",
            "shop / sklep / list / lista - oferta sprzedawcy",
            "buy / kup przedmiot - kup przedmiot",
            "talk npc - rozmowa, zadania i lekcje nauczycieli klasowych",
            "teachers / nauczyciele - lista nauczycieli w Sali Gildii",
            "quests - dziennik zadań",
            "attack / atakuj / zabij / kill przeciwnik - tura walki",
            "flee / uciekaj - ucieczka",
            "unlock - odblokuj gotowy Soul Tier",
            "save - zapis",
            "quit - wyjście",
        ]

    async def show_latest_changes(self):
        await self.send(LATEST_CHANGES_TITLE)
        for line in LATEST_CHANGES:
            await self.send("- " + line)

    async def show_help(self, topic=""):
        raw = topic.strip().lower()
        key = HELP_TOPIC_ALIASES.get(raw, raw)

        if not key:
            await self.send("POMOC GŁÓWNA")
            await self.send(
                "Użyj help <temat>. Tematy: podstawy, komendy, nawigacja, statystyki, "
                "walka, dusza, pieniadze, ekwipunek, zadania, profesje, wedkarstwo, "
                "gornictwo, pojemniki, sklepy, gracze, smierc, rasy, klasy, umiejetnosci, nazwy_skilli, nauczyciele, opisy."
            )
            await self.send("help tematy - lista tematów.")
            await self.send("help wszystko - pełny przewodnik.")
            await self.send("opis <nazwa> - szczegółowy opis dowolnego elementu.")
            await self.send("changes / zmiany - najnowsza wersja i najnowsze zmiany.")
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
            parts.append(f"Slot: {item.get('slot', 'brak')}. Obrona fizyczna: +{item.get('defense', 0)}.")
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
        if room_id in FRESHWATER_FISHING_ROOMS:
            features.append("łowisko słodkowodne")
        if room_id in MARINE_FISHING_ROOMS:
            features.append("łowisko morskie")
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
        await self.send(f"{c.name}. Rasa: {c.race}. Klasa: {c.class_name}.")
        await self.send("Poziom postaci: nie istnieje.")
        await self.send(
            f"Siła {c.strength}, Zręczność {c.dexterity}, Kondycja {c.constitution}, "
            f"Inteligencja {c.intelligence}, Siła Woli {c.willpower}."
        )
        await self.send(f"Rozwój statystyk: {c.stat_progress} z {STAT_GROWTH_THRESHOLD}.")
        await self.send(
            f"Życie: {self.current_hp} z {c.max_hp()}. "
            f"Obrona fizyczna: {self.defense()}. "
            f"Obrona magiczna: {c.magic_defense()}."
        )
        await self.send(
            f"Siła ataku fizycznego: {c.physical_power()}. "
            f"Szybkość: {c.speed()}. "
            f"Unik: {int(c.dodge_chance() * 100)} procent."
        )
        if c.class_type == "magic":
            await self.send(
                f"Mana: {self.current_mana} z {c.max_mana()}. "
                f"Moc czarów: {c.spell_power()}."
            )
        await self.send(
            f"Waluta: {c.silver} srebra, {c.gold} złota, {c.mithril} mithrilu. "
            f"Śmierci: {c.deaths}."
        )

    async def show_soul(self):
        c = self.character
        await self.send(f"Broń Duszy: {c.soul_weapon}.")
        await self.send(f"Soul Level: {c.soul_level} z {SOUL_MAX_LEVEL}. Tier: {c.soul_tier} z 3.")
        if c.soul_level < SOUL_MAX_LEVEL:
            await self.send(f"Soul XP: {c.soul_xp} z {c.soul_xp_to_next()}.")
        await self.send(f"Moc Broni Duszy: {c.soul_power()}.")
        nxt = c.can_unlock()
        if nxt:
            await self.send(f"Tier {nxt} gotowy. Wpisz unlock.")
        elif c.soul_tier == 1:
            await self.send(f"Tier 2 wymaga Soul Level {TIER2_LEVEL}.")
        elif c.soul_tier == 2:
            await self.send(f"Tier 3 wymaga Soul Level {TIER3_LEVEL}.")

    async def move(self, direction):
        if self.auto_fishing or self.auto_fishing_task:
            await self.stop_auto_fishing(announce=False)
            await self.send("Auto-łowienie wyłączone z powodu ruchu.")
        if self.auto_mining or self.auto_mining_task:
            await self.stop_auto_mining(announce=False)
            await self.send("Auto-kopanie wyłączone z powodu ruchu.")
        if self.combat_mob_key:
            await self.send("Jesteś w walce. Najpierw użyj flee albo pokonaj przeciwnika.")
            return
        target = ROOMS[self.character.room_id]["exits"].get(direction)
        if not target:
            await self.send("Nie możesz iść w tym kierunku.")
            return
        old = self.character.room_id
        await self.server.broadcast_room(old, f"{self.character.name} odchodzi.", exclude=self)
        self.character.room_id = target
        self.server.db.save_character(self.character)
        await self.server.broadcast_room(target, f"{self.character.name} przychodzi.", exclude=self)
        await self.look()

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

    def tool_xp_to_next(self, level):
        if level >= TOOL_MAX_LEVEL:
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
        tool_name = "Wędka" if tool_type == "fishing" else "Kilof"
        messages.append(f"{tool_name}: +{tool_xp} XP narzędzia.")

        while tlevel < TOOL_MAX_LEVEL:
            needed = self.tool_xp_to_next(tlevel)
            if txp < needed:
                break
            txp -= needed
            tlevel += 1
            messages.append(f"{tool_name} osiąga level {tlevel}.")
        if tlevel >= TOOL_MAX_LEVEL:
            tlevel = TOOL_MAX_LEVEL
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
        raise ValueError(
            f"Przedmiot {item_id} nie jest rybą ani zwykłą rudą profesji."
        )

    def container_label(self, container):
        return "Siatka na ryby" if container == "net" else "Sakwa górnicza"

    def normalize_container(self, token):
        t = token.strip().lower()
        if t in ("net", "siatka", "siatkę", "siatke"):
            return "net"
        if t in ("bag", "sakwa", "sakwe", "sakwę", "worek"):
            return "bag"
        return None

    def category_ids(self, query, container=None):
        q = query.strip().lower()
        if q in ("fish", "ryba", "ryby"):
            return set(FISH_RESOURCE_IDS)
        if q in ("ore", "ruda", "rudy"):
            return set(ORE_RESOURCE_IDS)
        if container == "net":
            allowed = FISH_RESOURCE_IDS
        elif container == "bag":
            allowed = ORE_RESOURCE_IDS
        else:
            allowed = FISH_RESOURCE_IDS | ORE_RESOURCE_IDS

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
            await self.send("Podaj na końcu: siatka/net albo sakwa/bag.")
            return

        query = " ".join(parts[:-1])
        ids = self.category_ids(query, container)
        if not ids:
            await self.send("Nie rozpoznaję takiego surowca.")
            return

        expected = FISH_RESOURCE_IDS if container == "net" else ORE_RESOURCE_IDS
        ids &= expected
        if not ids:
            await self.send(
                "Do Siatki wkłada się ryby, a do Sakwy górniczej rudy."
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
                "Użycie: wyjmij przedmiot siatka/sakwa albo take item net/bag."
            )
            return

        container = self.normalize_container(parts[-1])
        if not container:
            await self.send("Podaj na końcu: siatka/net albo sakwa/bag.")
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

        while tlevel < TOOL_MAX_LEVEL:
            needed = self.tool_xp_to_next(tlevel)
            if txp < needed:
                break
            txp -= needed
            tlevel += 1
            await self.send(f"{tool_name} osiąga level {tlevel}.")

        if tlevel >= TOOL_MAX_LEVEL:
            tlevel = TOOL_MAX_LEVEL
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

    def find_room(self, query):
        q = query.strip().lower()
        if not q:
            return None

        # Common English aliases for important locations.
        english_aliases = {
            "fish market": "fish_market",
            "market": "market",
            "harbor": "harbor",
            "port": "harbor",
            "sea pier": "sea_pier",
            "pier": "sea_pier",
            "temple": "temple",
            "temple basement": "temple_basement",
            "square": "square",
            "forge": "forge",
            "inn": "inn",
            "riverbank": "riverbank",
            "river bank": "riverbank",
            "stone bridge": "stone_bridge",
            "crystal cave": "cave_entrance",
            "crystal tunnel": "cave_tunnel",
            "crystal chamber": "crystal_chamber",
        }
        if q in english_aliases:
            return english_aliases[q]

        exact = []
        partial = []
        for room_id, room in ROOMS.items():
            name = room["name"].lower()
            if q == room_id.lower() or q == name:
                exact.append(room_id)
            elif q in name or q in room_id.lower():
                partial.append(room_id)

        if exact:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None

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

        if not q:
            await self.send(
                "Użycie: prowadz Targ Rybny albo walk to Sea Pier."
            )
            return

        if self.combat_mob_key:
            await self.send("Nie możesz użyć prowadzenia podczas walki.")
            return

        target = self.find_room(q)
        if not target:
            await self.send(
                "Nie rozpoznaję tej lokacji. Użyj map, aby poznać nazwy miejsc."
            )
            return

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

    async def show_profession_ranks(self):
        await self.send("RANGI WĘDKARSTWA")
        for rank, minimum in enumerate(PROFESSION_RANK_THRESHOLDS, 1):
            if rank < PROFESSION_MAX_RANK:
                maximum = PROFESSION_RANK_THRESHOLDS[rank] - 1
                level_text = f"level {minimum}-{maximum}"
            else:
                level_text = f"level {minimum}"
            await self.send(
                f"Ranga {rank}: {PROFESSION_RANK_NAMES['Wędkarstwo'][rank - 1]}. "
                f"{level_text}."
            )

        await self.send("RANGI GÓRNICTWA")
        for rank, minimum in enumerate(PROFESSION_RANK_THRESHOLDS, 1):
            if rank < PROFESSION_MAX_RANK:
                maximum = PROFESSION_RANK_THRESHOLDS[rank] - 1
                level_text = f"level {minimum}-{maximum}"
            else:
                level_text = f"level {minimum}"
            await self.send(
                f"Ranga {rank}: {PROFESSION_RANK_NAMES['Górnictwo'][rank - 1]}. "
                f"{level_text}."
            )

    async def show_professions(self):
        fishing = self.server.db.profession(self.account_id, "Wędkarstwo")
        mining = self.server.db.profession(self.account_id, "Górnictwo")
        await self.send("PROFESJE")

        for name, row in (("Wędkarstwo", fishing), ("Górnictwo", mining)):
            level = int(row["level"])
            rank = profession_rank(level)
            rank_name = profession_rank_name(name, level)

            if rank < PROFESSION_MAX_RANK:
                next_rank_level = PROFESSION_RANK_THRESHOLDS[rank]
                next_text = (
                    f"Następna ranga {rank + 1} od levelu {next_rank_level}."
                )
            else:
                next_text = "Ranga maksymalna."

            if level >= PROFESSION_MAX_LEVEL:
                await self.send(
                    f"{name}: level {level} z {PROFESSION_MAX_LEVEL}. "
                    f"Ranga {rank} z {PROFESSION_MAX_RANK}: {rank_name}. "
                    f"XP: maksimum. Akcje: {row['actions']}. {next_text}"
                )
            else:
                await self.send(
                    f"{name}: level {level} z {PROFESSION_MAX_LEVEL}. "
                    f"Ranga {rank} z {PROFESSION_MAX_RANK}: {rank_name}. "
                    f"XP: {row['xp']} z {self.profession_xp_to_next(level)}. "
                    f"Akcje: {row['actions']}. {next_text}"
                )


    async def show_tool_tiers(self):
        await self.send("NAZWY TIERÓW WĘDKI")
        for tier, minimum in enumerate(TOOL_TIER_THRESHOLDS, 1):
            if tier < TOOL_MAX_TIER:
                maximum = TOOL_TIER_THRESHOLDS[tier] - 1
                level_text = f"level {minimum}-{maximum}"
            else:
                level_text = f"level {minimum}"
            bonus = int(TOOL_TIER_BONUS_CHANCES[tier - 1] * 100)
            await self.send(
                f"Tier {tier}: {TOOL_TIER_NAMES['fishing'][tier - 1]}. "
                f"{level_text}. Bonus {bonus} procent."
            )

        await self.send("NAZWY TIERÓW KILOFA")
        for tier, minimum in enumerate(TOOL_TIER_THRESHOLDS, 1):
            if tier < TOOL_MAX_TIER:
                maximum = TOOL_TIER_THRESHOLDS[tier] - 1
                level_text = f"level {minimum}-{maximum}"
            else:
                level_text = f"level {minimum}"
            bonus = int(TOOL_TIER_BONUS_CHANCES[tier - 1] * 100)
            await self.send(
                f"Tier {tier}: {TOOL_TIER_NAMES['mining'][tier - 1]}. "
                f"{level_text}. Bonus {bonus} procent."
            )

    async def show_tools(self):
        await self.send("NARZĘDZIA")
        tools = [
            ("fishing", "fishing_rod", "Wędka"),
            ("mining", "pickaxe", "Kilof"),
        ]
        for tool_type, item_id, name in tools:
            owned = self.server.db.item_qty(self.account_id, item_id) > 0
            if not owned:
                await self.send(f"{name}: brak.")
                continue

            row = self.server.db.tool(self.account_id, tool_type)
            level = int(row["level"])
            tier = tool_tier(level)
            tier_name = tool_tier_name(tool_type, level)
            bonus_percent = int(tool_tier_bonus_chance(level) * 100)

            if tier < TOOL_MAX_TIER:
                next_level = TOOL_TIER_THRESHOLDS[tier]
                next_text = f"Następny Tier {tier + 1} od levelu {next_level}."
            else:
                next_text = "Tier maksymalny."

            if level >= TOOL_MAX_LEVEL:
                await self.send(
                    f"{name}: level {level} z {TOOL_MAX_LEVEL}. "
                    f"Tier {tier} z {TOOL_MAX_TIER}: {tier_name}. "
                    f"XP: maksimum. Użycia: {row['uses']}. "
                    f"Bonus dodatkowego urobku: {bonus_percent} procent. {next_text}"
                )
            else:
                await self.send(
                    f"{name}: level {level} z {TOOL_MAX_LEVEL}. "
                    f"Tier {tier} z {TOOL_MAX_TIER}: {tier_name}. "
                    f"XP: {row['xp']} z {self.tool_xp_to_next(level)}. "
                    f"Użycia: {row['uses']}. "
                    f"Bonus dodatkowego urobku: {bonus_percent} procent. {next_text}"
                )


    def fishing_loot(self, tool_level, marine=False):
        r = random.random()

        if not marine:
            # Łowiska słodkowodne.
            if tool_level < 10:
                return "small_fish" if r < 0.72 else "river_carp"

            if tool_level < 25:
                if r < 0.52:
                    return "small_fish"
                if r < 0.90:
                    return "river_carp"
                return "silver_trout"

            if tool_level < 40:
                if r < 0.32:
                    return "river_carp"
                if r < 0.72:
                    return "silver_trout"
                if r < 0.92:
                    return "golden_trout"
                return "salmon"

            if tool_level < 60:
                if r < 0.30:
                    return "silver_trout"
                if r < 0.65:
                    return "golden_trout"
                if r < 0.90:
                    return "salmon"
                return "ancient_sturgeon"

            if tool_level < 80:
                if r < 0.38:
                    return "golden_trout"
                if r < 0.72:
                    return "salmon"
                if r < 0.94:
                    return "ancient_sturgeon"
                return "moon_eel"

            if r < 0.35:
                return "golden_trout"
            if r < 0.68:
                return "ancient_sturgeon"
            if r < 0.94:
                return "moon_eel"
            return "salmon"

        # Łowiska morskie.
        # Śledź zachowuje wymaganie minimum level 30 Wędki.
        if tool_level < 10:
            return "sardine" if r < 0.62 else "anchovy"

        if tool_level < 20:
            if r < 0.38:
                return "sardine"
            if r < 0.72:
                return "anchovy"
            return "cod"

        if tool_level < 30:
            if r < 0.25:
                return "sardine"
            if r < 0.48:
                return "anchovy"
            if r < 0.78:
                return "cod"
            return "mackerel"

        if tool_level < 40:
            if r < 0.20:
                return "cod"
            if r < 0.42:
                return "mackerel"
            if r < 0.62:
                return "herring"
            if r < 0.82:
                return "sea_bass"
            return "haddock"

        if tool_level < 50:
            if r < 0.18:
                return "herring"
            if r < 0.38:
                return "sea_bass"
            if r < 0.58:
                return "haddock"
            if r < 0.78:
                return "pollock"
            return "flounder"

        if tool_level < 60:
            if r < 0.16:
                return "haddock"
            if r < 0.34:
                return "pollock"
            if r < 0.54:
                return "flounder"
            if r < 0.78:
                return "halibut"
            return "tuna"

        if tool_level < 75:
            if r < 0.16:
                return "halibut"
            if r < 0.42:
                return "tuna"
            if r < 0.64:
                return "swordfish"
            if r < 0.82:
                return "bluefin_tuna"
            if r < 0.94:
                return "ancient_sturgeon"
            if r < 0.995:
                return "reef_shark"
            return "moon_eel"

        if tool_level < 90:
            if r < 0.18:
                return "tuna"
            if r < 0.38:
                return "swordfish"
            if r < 0.58:
                return "bluefin_tuna"
            if r < 0.74:
                return "halibut"
            if r < 0.86:
                return "reef_shark"
            if r < 0.95:
                return "hammerhead_shark"
            if r < 0.995:
                return "great_white_shark"
            return "moon_eel"

        # Level 90-100: morski end-game.
        if r < 0.15:
            return "bluefin_tuna"
        if r < 0.30:
            return "halibut"
        if r < 0.46:
            return "reef_shark"
        if r < 0.63:
            return "hammerhead_shark"
        if r < 0.79:
            return "great_white_shark"
        if r < 0.90:
            return "moon_eel"
        if r < 0.995:
            return "swordfish"
        return "ghost_marlin"


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
        # 1 mithril = 1000 złota, więc szanse są bardzo małe.
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
        marine = self.character.room_id in MARINE_FISHING_ROOMS
        item_id = self.fishing_loot(tool_level, marine=marine)
        self.store_profession_resource(item_id, 1)
        item = ITEMS[item_id]
        await self.send(
            f"Łowisz: {item['name']}. Połów trafia do Siatki na ryby."
        )

        current_tier = tool_tier(tool_level)
        bonus_chance = tool_tier_bonus_chance(tool_level)
        if bonus_chance > 0 and random.random() < bonus_chance:
            self.store_profession_resource(item_id, 1)
            await self.send(
                f"Bonus Tieru {current_tier} Wędki: wyciągasz dodatkowo {item['name']} x1."
            )

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
            bonus_chance = tool_tier_bonus_chance(tool_level)
            if bonus_chance > 0 and random.random() < bonus_chance:
                self.store_profession_resource(item_id, 1)
                await self.send(
                    f"Bonus Tieru {current_tier} Kilofa: wydobywasz dodatkowo {item['name']} x1."
                )

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

        if item_id in fish_items:
            source_container = "net"
        elif item_id in ore_items:
            source_container = "bag"
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
        self.server.db.save_character(self.character)

        rewards = []
        if silver:
            rewards.append(f"{silver} srebra")
        if gold:
            rewards.append(f"{gold} złota")
        if mithril:
            rewards.append(f"{mithril} mithrilu")
        await self.send(f"Sprzedajesz {item['name']} za " + ", ".join(rewards) + ".")

    async def inventory(self):
        rows = self.server.db.inventory(self.account_id)
        await self.send(
            f"Waluta: {self.character.silver} srebra, "
            f"{self.character.gold} złota, {self.character.mithril} mithrilu."
        )
        await self.send(
            "Siatka na ryby i Sakwa górnicza są osobnymi magazynami; "
            "użyj komend siatka/net oraz sakwa/bag."
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
            await self.send(f"{slot_name}: {name}. Obrona +{defense}.")

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
        self.server.db.equip(self.account_id, item["slot"], item_id)
        await self.send(f"Zakładasz: {item['name']}. Obrona wynosi teraz {self.defense()}.")

    async def use_item(self, query):
        found = find_by_name(ITEMS, query)
        if not found:
            await self.send("Nie rozpoznaję takiego przedmiotu.")
            return
        item_id, item = found
        if self.server.db.item_qty(self.account_id, item_id) <= 0:
            await self.send("Nie masz tego przedmiotu.")
            return
        if item.get("type") != "consumable":
            await self.send("Tego przedmiotu nie używa się w ten sposób.")
            return
        if "heal" in item:
            if self.current_hp >= self.character.max_hp():
                await self.send("Masz pełne życie.")
                return
            self.server.db.remove_item(self.account_id, item_id, 1)
            amount = min(item["heal"], self.character.max_hp() - self.current_hp)
            self.current_hp += amount
            await self.send(f"Używasz {item['name']}. Odzyskujesz {amount} życia.")
            await self.send(
                f"Masz teraz {self.current_hp} z {self.character.max_hp()} HP."
            )
            if self.combat_mob_key:
                await self.send("Zużywasz swoją turę na użycie mikstury.")
                await self.enemy_counterattack(self.server.world.mobs.get(self.combat_mob_key))
            return
        if "soul_xp" in item:
            self.server.db.remove_item(self.account_id, item_id, 1)
            for msg in self.character.add_soul_xp(item["soul_xp"]):
                await self.send(msg)
            self.server.db.save_character(self.character)

    async def shop(self):
        offers = SHOPS.get(self.character.room_id)
        if not offers:
            await self.send("W tej lokacji nie ma sklepu.")
            return
        await self.send("Oferta sklepu:")
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
            await self.send(
                f"{number}. {item['name']}: {item['price']} {currency_pl}.{extra} {item['desc']}"
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
        self.server.db.add_item(self.account_id, item_id, 1)
        if item.get("type") == "tool":
            self.server.db.ensure_tool(self.account_id, item["tool_type"])
        self.server.db.save_character(self.character)
        await self.send(f"Kupujesz {item['name']} za {price} {currency_pl}.")

    async def show_teachers(self):
        teachers = [
            (npc_id, npc) for npc_id, npc in NPCS.items()
            if npc.get("teacher_class")
        ]
        await self.send("Nauczyciele klasowi rozmieszczeni po Gildii Dusz:")
        for number, (npc_id, npc) in enumerate(teachers, 1):
            own = " Twoja klasa." if npc["teacher_class"] == self.character.class_name else ""
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
            if class_name != self.character.class_name:
                status = f"wymaga klasy {class_name} i Soul Level {skill['unlock']}"
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

        if class_name == self.character.class_name:
            await self.send(
                f"To jest nauczyciel twojej klasy. Aktualny Soul Level: {self.character.soul_level}."
            )
            await self.send(
                "Nauka: learn <numer> albo naucz <nazwa umiejętności>. "
                "Każdy nauczony skill rozwija potem własny Skill Level 1-100 przez używanie."
            )
        else:
            await self.send(
                f"Twoja obecna klasa to {self.character.class_name}. "
                "Ten nauczyciel nie może nauczyć cię umiejętności innej klasy."
            )


    async def talk(self, query):
        candidates = {
            key: npc for key, npc in NPCS.items() if npc["room"] == self.character.room_id
        }
        found = find_by_name(candidates, query)
        if not found:
            if candidates:
                await self.send("Nie rozpoznaję tego NPC.")
            else:
                await self.send("Nie ma tutaj nikogo, z kim można rozpocząć rozmowę.")
            return
        npc_id, npc = found
        await self.send(f"{npc['name']}: {npc['dialogue']}")
        if npc.get("teacher_class"):
            await self.teacher_lesson(npc)
            return
        quest_id = npc.get("quest")
        if not quest_id:
            return
        q = QUESTS[quest_id]
        row = self.server.db.quest(self.account_id, quest_id)
        if not row:
            self.server.db.start_quest(self.account_id, quest_id)
            await self.send(f"Nowe zadanie: {q['name']}. {q['description']}")
            return
        if row["status"] == "completed":
            await self.send(f"Zadanie {q['name']} jest już ukończone.")
            return

        if q["kind"] == "kill":
            progress = row["progress"]
            if progress < q["needed"]:
                await self.send(f"Postęp zadania: {progress} z {q['needed']}.")
                return
        elif q["kind"] == "collect":
            progress = self.server.db.item_qty(self.account_id, q["target"])
            if progress < q["needed"]:
                await self.send(f"Masz {progress} z {q['needed']} wymaganych przedmiotów.")
                return
            self.server.db.remove_item(self.account_id, q["target"], q["needed"])

        elif q["kind"] == "collect_category":
            if q["target"] == "fish":
                ids = FISH_RESOURCE_IDS
                container = "net"
                label = "ryb"
            elif q["target"] == "ore":
                ids = ORE_RESOURCE_IDS
                container = "bag"
                label = "rud"
            else:
                await self.send("Błąd konfiguracji zadania.")
                return

            progress = self.server.db.total_items_across_storage_and_inventory(
                self.account_id, ids, container
            )
            if progress < q["needed"]:
                await self.send(f"Masz {progress} z {q['needed']} wymaganych {label}.")
                return

            ok = self.server.db.consume_items_across_storage_and_inventory(
                self.account_id, ids, q["needed"], container
            )
            if not ok:
                await self.send("Nie udało się pobrać wymaganych surowców.")
                return

        await self.complete_quest(quest_id)

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

        # "EXP" w Soulbound nie tworzy levelu postaci.
        # To doświadczenie rozwoju zasila automatyczny wzrost statystyk.
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
                await self.send(f"{q['name']}: ukończone.")
            elif q["kind"] == "kill":
                await self.send(
                    f"{q['name']}: aktywne. {row['progress']} z {q['needed']}. {q['description']}"
                )
            elif q["kind"] == "collect":
                have = self.server.db.item_qty(self.account_id, q["target"])
                await self.send(
                    f"{q['name']}: aktywne. Masz {have} z {q['needed']}. {q['description']}"
                )
            elif q["kind"] == "collect_category":
                if q["target"] == "fish":
                    ids = FISH_RESOURCE_IDS
                    container = "net"
                else:
                    ids = ORE_RESOURCE_IDS
                    container = "bag"
                have = self.server.db.total_items_across_storage_and_inventory(
                    self.account_id, ids, container
                )
                await self.send(
                    f"{q['name']}: aktywne. Masz {have} z {q['needed']}. {q['description']}"
                )

    async def unlock(self):
        nxt = self.character.can_unlock()
        if not nxt:
            if self.character.soul_tier >= 3:
                await self.send("Broń Duszy ma już Tier 3.")
            elif self.character.soul_tier == 1:
                await self.send(f"Tier 2 wymaga Soul Level {TIER2_LEVEL}.")
            else:
                await self.send(f"Tier 3 wymaga Soul Level {TIER3_LEVEL}.")
            return
        self.character.soul_tier = nxt
        self.server.db.save_character(self.character)
        await self.send(f"Odblokowano Tier {nxt}. Moc Broni Duszy: {self.character.soul_power()}.")

    def class_skills(self):
        return CLASS_SKILLS.get(self.character.class_name, [])

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
        skills = self.class_skills()
        learned = self.server.db.learned_skill_ids(self.account_id)
        teacher_id, teacher = self.class_teacher()
        teacher_room = ROOMS[teacher["room"]]["name"] if teacher else "nieznana lokacja"

        await self.send(
            f"Umiejętności klasy {self.character.class_name}. Soul Level: {self.character.soul_level}."
        )
        for number, skill in enumerate(skills, 1):
            progress_text = ""
            skill_level = 1

            if skill["id"] in learned:
                row = self.server.db.skill_progress(self.account_id, skill["id"])
                skill_level = int(row["level"])
                if skill_level >= SKILL_MAX_LEVEL:
                    progress_text = f" Skill Level {skill_level}, maksymalny."
                else:
                    progress_text = (
                        f" Skill Level {skill_level}, XP {row['xp']} z "
                        f"{skill_xp_to_next(skill_level)}, użycia {row['uses']}."
                    )
                status = "nauczona"
            elif self.character.soul_level >= skill["unlock"]:
                status = f"gotowa do nauki u {teacher['name']} w lokacji {teacher_room}"
            else:
                status = f"zablokowana: wymaga Soul Level {skill['unlock']}"

            mana = f", Mana {skill.get('mana', 0)}" if skill.get("mana", 0) else ""
            effective_cd = self.effective_skill_cooldown(skill, skill_level)
            remaining = max(
                0,
                int(self.skill_cooldowns.get(skill["id"], 0) - time.time() + 0.999)
            )
            cd = f", pozostały cooldown {remaining} sekund" if remaining else ""

            await self.send(
                f"{number}. {skill['name']}. {status}.{progress_text} "
                f"Cooldown bazowy {skill['cooldown']} sekund, aktualny {effective_cd} sekund"
                f"{mana}{cd}. {skill['desc']}"
            )

        await self.send(
            "Każdy nauczony skill ma własny Skill Level 1-100 i własny XP. "
            "Używanie skilla rozwija właśnie ten konkretny skill."
        )
        await self.send(
            "Aby nauczyć się gotowej umiejętności, idź do nauczyciela swojej klasy "
            "i użyj learn <numer lub nazwa> albo naucz <numer lub nazwa>."
        )


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
            return self.character.dexterity
        if scale == "intelligence":
            return self.character.intelligence
        return self.character.strength

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
            mob = self.server.world.find_mob(self.character.room_id, query)
            if not mob:
                await self.send("Nie widzę tutaj takiego przeciwnika.")
                return None
            if mob.engaged_by and mob.engaged_by != self.character.name:
                await self.send(
                    f"{MOB_TEMPLATES[mob.template_id]['name']} walczy już z innym graczem."
                )
                return None
            mob.engaged_by = self.character.name
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

    async def enemy_counterattack(self, mob):
        if not mob or not mob.alive:
            return
        template = MOB_TEMPLATES[mob.template_id]

        if self.skill_evade:
            self.skill_evade = False
            await self.send(
                f"{template['name']} kontratakuje, ale aktywna umiejętność gwarantuje unik."
            )
            return

        if random.random() < self.character.dodge_chance():
            await self.send(
                f"{template['name']} kontratakuje, ale unikasz ciosu dzięki szybkości."
            )
            return

        damage_type = template.get("damage_type", "physical")
        if damage_type == "magic":
            reduction = self.character.magic_defense()
            defense_name = "obrona magiczna"
        else:
            reduction = self.defense()
            defense_name = "obrona fizyczna"

        incoming = max(1, template["damage"] + random.randint(-2, 2) - reduction)

        if self.skill_guard > 0:
            guard = self.skill_guard
            self.skill_guard = 0
            before = incoming
            incoming = max(1, incoming - guard)
            await self.send(
                f"Aktywna osłona redukuje trafienie dodatkowo o {before - incoming} obrażeń."
            )

        self.current_hp -= incoming
        await self.send(
            f"{template['name']} odpowiada. Typ obrażeń: "
            f"{'magiczne' if damage_type == 'magic' else 'fizyczne'}. "
            f"Otrzymujesz {incoming} obrażeń po redukcji przez {defense_name}. "
            f"Twoje życie: {max(0, self.current_hp)} z {self.character.max_hp()}."
        )
        if self.current_hp <= 0:
            await self.die(template["name"])

    async def learn_class_skill(self, raw):
        if self.combat_mob_key:
            await self.send("Nie możesz uczyć się umiejętności podczas walki.")
            return

        value = raw.strip()
        normalized = self.normalize_description_query(value)
        if normalized.startswith("sie "):
            value = value.split(maxsplit=1)[1] if len(value.split(maxsplit=1)) > 1 else ""
        elif normalized.startswith("się "):
            value = value.split(maxsplit=1)[1] if len(value.split(maxsplit=1)) > 1 else ""

        teacher_id, teacher = self.class_teacher()
        if not teacher:
            await self.send("Nie znaleziono nauczyciela twojej klasy.")
            return

        if self.character.room_id != teacher["room"]:
            await self.send(
                f"Musisz być przy nauczycielu swojej klasy: {teacher['name']}. "
                f"Znajdziesz go w lokacji {ROOMS[teacher['room']]['name']}."
            )
            return

        skill, unused = self.find_skill_from_input(value)
        if not skill:
            await self.send(
                "Nie rozpoznaję tej umiejętności. Wpisz talk <nauczyciel> albo skills."
            )
            return

        if self.server.db.knows_skill(self.account_id, skill["id"]):
            await self.send(f"Już znasz umiejętność {skill['name']}.")
            return

        if self.character.soul_level < skill["unlock"]:
            await self.send(
                f"Nie jesteś jeszcze gotowy. {skill['name']} wymaga Soul Level {skill['unlock']}, "
                f"a masz {self.character.soul_level}."
            )
            return

        self.server.db.learn_skill(self.account_id, skill["id"])
        await self.send(
            f"{teacher['name']} uczy cię umiejętności: {skill['name']}."
        )
        await self.send(
            f"Nauczono. {skill['name']} zaczyna na Skill Level 1. "
            f"Możesz teraz używać: skill {skill['name']}."
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
            teacher_id, teacher = self.class_teacher()
            await self.send(
                f"Nie znasz jeszcze umiejętności {skill['name']}. "
                f"Musisz nauczyć się jej u {teacher['name']} w lokacji "
                f"{ROOMS[teacher['room']]['name']}."
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
                await self.send(f"Mana: {self.current_mana} z {self.character.max_mana()}.")
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
            max_hp = self.character.max_hp()
            heal_pct = min(0.75, skill.get("heal_pct", 0.25) * skill_power)
            heal = max(1, int(max_hp * heal_pct))
            before = self.current_hp
            self.current_hp = min(max_hp, self.current_hp + heal)
            actual = self.current_hp - before
            await self.send(
                f"Używasz {skill['name']} na Skill Level {skill_level}. "
                f"Odzyskujesz {actual} HP. "
                f"Masz teraz {self.current_hp} z {max_hp} HP."
            )
            await self.grant_skill_use_xp(skill)
            if mana_cost:
                await self.send(f"Mana: {self.current_mana} z {self.character.max_mana()}.")
            if self.combat_mob_key:
                await self.enemy_counterattack(self.server.world.mobs.get(self.combat_mob_key))
            return

        template = MOB_TEMPLATES[mob.template_id]
        scale = self.skill_scale_value(skill.get("scale", "strength"))
        multiplier = skill.get("mult", 1.0) * skill_power

        if kind == "execute":
            hp_ratio = mob.hp / max(1, template["max_hp"])
            if hp_ratio <= 0.35:
                multiplier *= skill.get("execute_mult", 1.5)
                await self.send("Egzekucyjny próg aktywny: przeciwnik jest osłabiony.")

        if self.skill_damage_boost > 1.0:
            multiplier *= self.skill_damage_boost
            self.skill_damage_boost = 1.0
            await self.send("Wzmocnienie ofensywne zwiększa siłę tej umiejętności.")

        damage = max(1, int((self.character.soul_power() + scale) * multiplier) + random.randint(-2, 3))
        mob.hp -= damage
        await self.send(
            f"Używasz {skill['name']} na {template['name']}. Zadajesz {damage} obrażeń. "
            f"Przeciwnik: {max(0, mob.hp)} z {template['max_hp']} HP."
        )

        if kind == "drain":
            heal = max(1, int(damage * skill.get("drain_pct", 0.4)))
            before = self.current_hp
            self.current_hp = min(self.character.max_hp(), self.current_hp + heal)
            actual = self.current_hp - before
            await self.send(
                f"Wysysanie przywraca {actual} HP. Masz {self.current_hp} z {self.character.max_hp()} HP."
            )

        self_damage = skill.get("self_damage", 0)
        if skill.get("self_damage_pct"):
            self_damage += max(1, int(self.character.max_hp() * skill["self_damage_pct"]))
        if self_damage:
            self.current_hp -= self_damage
            await self.send(
                f"Koszt umiejętności: tracisz {self_damage} HP. "
                f"Masz {max(0, self.current_hp)} z {self.character.max_hp()} HP."
            )
            if self.current_hp <= 0:
                await self.die("własna umiejętność")
                return

        await self.grant_skill_use_xp(skill)

        if mana_cost:
            await self.send(f"Mana: {self.current_mana} z {self.character.max_mana()}.")

        if mob.hp <= 0:
            await self.mob_defeated(mob)
            return

        await self.enemy_counterattack(mob)

    def player_damage(self):
        c = self.character

        if c.class_type == "physical":
            # Siła odpowiada za atak fizyczny.
            return max(
                1,
                c.soul_power()
                + c.physical_power()
                + random.randint(-3, 4)
            )

        # Inteligencja odpowiada za moc czarów i mana.
        if self.current_mana >= 4:
            self.current_mana -= 4
            return max(
                1,
                c.soul_power()
                + c.spell_power()
                + random.randint(-3, 4)
            )

        # Bez many mag nadal może uderzyć Bronią Duszy, ale dużo słabiej.
        return max(
            1,
            c.soul_power()
            + c.spell_power() // 3
            + random.randint(-2, 2)
        )

    async def attack(self, query):
        if self.auto_fishing or self.auto_fishing_task:
            await self.stop_auto_fishing(announce=False)
            await self.send("Auto-łowienie wyłączone z powodu walki.")
        if self.auto_mining or self.auto_mining_task:
            await self.stop_auto_mining(announce=False)
            await self.send("Auto-kopanie wyłączone z powodu walki.")
        self.server.world.refresh()
        mob = None

        if self.combat_mob_key:
            mob = self.server.world.mobs.get(self.combat_mob_key)
            if not mob or not mob.alive or mob.room_id != self.character.room_id:
                self.combat_mob_key = None
                mob = None

        if mob is None:
            mob = self.server.world.find_mob(self.character.room_id, query)
            if not mob:
                await self.send("Nie widzę tutaj takiego przeciwnika.")
                return
            if mob.engaged_by and mob.engaged_by != self.character.name:
                await self.send(f"{MOB_TEMPLATES[mob.template_id]['name']} walczy już z innym graczem.")
                return
            mob.engaged_by = self.character.name
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
        mob.respawn_at = time.time() + RESPAWN_SECONDS
        mob.engaged_by = None
        self.combat_mob_key = None

        silver = template.get("silver", 0)
        gold = template.get("gold", 0)
        mithril = template.get("mithril", 0)
        self.character.silver += silver
        self.character.gold += gold
        self.character.mithril += mithril
        await self.send(f"Pokonujesz: {template['name']}.")
        if silver:
            await self.send(f"Zdobywasz {silver} srebra.")
        if gold:
            await self.send(f"Zdobywasz {gold} złota.")
        if mithril:
            await self.send(f"Zdobywasz {mithril} mithrilu.")

        for msg in self.character.add_stat_progress(template["stat_reward"]):
            await self.send(msg)
        for msg in self.character.add_soul_xp(template["soul_reward"]):
            await self.send(msg)

        for item_id, chance in template["drops"].items():
            if random.random() <= chance:
                self.server.db.add_item(self.account_id, item_id, 1)
                await self.send(f"Zdobywasz przedmiot: {ITEMS[item_id]['name']}.")

        target = template.get("quest_target")
        if target:
            changed = self.server.db.increment_quest(self.account_id, target)
            for quest_id, progress in changed:
                q = QUESTS[quest_id]
                await self.send(f"Postęp zadania {q['name']}: {progress} z {q['needed']}.")

        self.server.db.save_character(self.character)
        await self.server.broadcast_room(
            self.character.room_id,
            f"{self.character.name} pokonuje {template['name']}.",
            exclude=self,
        )

    async def flee(self):
        if not self.combat_mob_key:
            await self.send("Nie jesteś w walce.")
            return
        mob = self.server.world.mobs.get(self.combat_mob_key)
        if mob and mob.engaged_by == self.character.name:
            mob.engaged_by = None
        self.combat_mob_key = None
        self.skill_guard = 0
        self.skill_evade = False
        self.skill_damage_boost = 1.0
        await self.send("Wycofujesz się z walki.")

    async def die(self, killer):
        if self.combat_mob_key:
            mob = self.server.world.mobs.get(self.combat_mob_key)
            if mob and mob.engaged_by == self.character.name:
                mob.engaged_by = None
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
        self.current_hp = self.character.max_hp()
        self.current_mana = self.character.max_mana()
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
            elif command == "exits":
                await self.show_exits()
            elif command == "map":
                await self.show_map()
            elif command == "where":
                await self.show_where()
            elif command == "who":
                await self.who()
            elif command == "say":
                await self.say(args)
            elif command == "tell":
                await self.tell(args)
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
            elif command == "sell":
                await self.sell_resource(args)
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
        if self.auto_fishing or self.auto_fishing_task:
            await self.stop_auto_fishing(announce=False)
        if self.auto_mining or self.auto_mining_task:
            await self.stop_auto_mining(announce=False)
        self.closed = True
        if self.combat_mob_key:
            mob = self.server.world.mobs.get(self.combat_mob_key)
            if mob and self.character and mob.engaged_by == self.character.name:
                mob.engaged_by = None
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

    def account_online(self, account_id):
        return any(s.account_id == account_id and s.character for s in self.sessions)

    def find_character_session(self, name):
        for s in self.sessions:
            if s.character and s.character.name.lower() == name.lower():
                return s
        return None

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
