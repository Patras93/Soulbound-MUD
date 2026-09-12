#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Soulbound v0.6.5 Profession Containers
Wieloosobowy tekstowy MUD TCP/Telnet dla MUSHclienta/Mudleta.

Najważniejsze zasady projektu:
- postać NIE ma levelu ani XP postaci,
- statystyki rosną automatycznie,
- klasy fizyczne rozwijają Siłę, Zręczność i Kondycję,
- klasy magiczne rozwijają Inteligencję i Siłę Woli,
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

VERSION = "0.6.6"

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
TOOL_MAX_LEVEL = 100
PROFESSION_COOLDOWN = 2.0

FISHING_ROOMS = {"riverbank", "stone_bridge", "meadow"}
MINING_ROOMS = {"cave_entrance", "cave_tunnel", "crystal_chamber"}

FISH_RESOURCE_IDS = {
    "small_fish", "river_carp", "silver_trout",
    "golden_trout", "ancient_sturgeon", "moon_eel",
}
ORE_RESOURCE_IDS = {
    "stone_chunk", "copper_ore", "iron_ore",
    "silver_ore", "gold_ore", "mithril_ore",
}

RACES = [
    ("Człowiek", "Wszechstronny.", 10, 10, 10, 10, 10),
    ("Ogr", "Potężny i wytrzymały.", 14, 8, 14, 6, 8),
    ("Elf", "Bardzo zręczny i uzdolniony magicznie.", 8, 14, 9, 13, 11),
    ("Krasnolud", "Silny, odporny i uparty.", 12, 9, 14, 9, 12),
    ("Ork", "Urodzony wojownik.", 13, 10, 13, 7, 9),
    ("Niziołek", "Niewielki i bardzo zręczny.", 7, 14, 10, 10, 11),
    ("Mroczny Elf", "Zręczny i związany z mroczną magią.", 9, 13, 9, 14, 10),
    ("Gnom", "Błyskotliwy i odporny psychicznie.", 7, 12, 9, 14, 13),
    ("Smoczy", "Smocza krew, siła i odporność.", 13, 9, 13, 10, 10),
    ("Troll", "Ekstremalnie silny i wytrzymały.", 15, 7, 15, 5, 8),
    ("Diablę", "Demoniczne pochodzenie i talent magiczny.", 9, 11, 9, 13, 13),
    ("Aasimar", "Silna wola i moc światła.", 10, 10, 11, 12, 14),
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
        "zone": "Miasto Dusz", "name": "Sala Gildii",
        "desc": "Wielka sala, w której poszukiwacze przygód wymieniają informacje.",
        "exits": {"west": "library", "south": "north_street"},
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
        "exits": {"south": "market"},
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
    "pomoc": "help",
    "spójrz": "look", "spojrz": "look", "l": "look",
    "wyjścia": "exits", "wyjscia": "exits",
    "mapa": "map",
    "gdzie": "where",
    "kto": "who",
    "staty": "stats", "status": "stats",
    "dusza": "soul",
    "ekwipunek": "inventory", "inv": "inventory", "i": "inventory",
    "załóż": "equip", "zaloz": "equip",
    "wyposażenie": "equipment", "wyposazenie": "equipment",
    "użyj": "use", "uzyj": "use",
    "sklep": "shop",
    "kup": "buy",
    "mów": "say", "mow": "say", "powiedz": "say",
    "rozmawiaj": "talk",
    "zadania": "quests", "questy": "quests",
    "atakuj": "attack", "walcz": "attack",
    "uciekaj": "flee",
    "odblokuj": "unlock",
    "zapisz": "save",
    "włóż": "put", "wloz": "put", "put": "put",
    "wyjmij": "take", "wyciągnij": "take", "wyciagnij": "take", "take": "take",
    "siatka": "net", "net": "net",
    "sakwa": "bag", "worek": "bag", "bag": "bag",
    "wędkuj": "fish", "wedkuj": "fish", "łów": "fish", "low": "fish",
    "kop": "mine", "wydobywaj": "mine",
    "sprzedaj": "sell",
    "profesje": "professions",
    "narzędzia": "tools", "narzedzia": "tools",
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
    "iron_guard": {
        "name": "Żelazny napierśnik", "type": "armor", "slot": "body", "defense": 4,
        "price": 2, "currency": "gold", "desc": "Cięższy pancerz. Obrona +4.",
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
        "name": "Ruda mithrilu", "type": "resource", "price": None,
        "desc": "Niezwykle rzadka ruda. Pojawia się dopiero przy wysokim poziomie kilofa.",
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
    "forge": ["iron_guard", "pickaxe"],
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
        "dialogue": "Odłamki Duszy z krypty reagują na broń związaną z właścicielem.",
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
        "name": "Szczur Świątynny", "max_hp": 28, "damage": 3,
        "silver": 6, "gold": 0, "mithril": 0,
        "stat_reward": 8, "soul_reward": 1,
        "drops": {}, "quest_target": "temple_rat",
    },
    "training_dummy": {
        "name": "Żywy Manekin", "max_hp": 45, "damage": 4,
        "silver": 12, "gold": 0, "mithril": 0, "stat_reward": 18, "soul_reward": 4,
        "drops": {}, "quest_target": None,
    },
    "goblin": {
        "name": "Goblin", "max_hp": 60, "damage": 7,
        "silver": 28, "gold": 0, "mithril": 0, "stat_reward": 30, "soul_reward": 7,
        "drops": {"healing_potion": 0.08}, "quest_target": "goblin",
    },
    "goblin_brute": {
        "name": "Gobliński Osiłek", "max_hp": 85, "damage": 10,
        "silver": 45, "gold": 1, "mithril": 0, "stat_reward": 38, "soul_reward": 9,
        "drops": {"healing_potion": 0.12}, "quest_target": "goblin",
    },
    "shadow_wolf": {
        "name": "Wilk Cienia", "max_hp": 70, "damage": 9,
        "silver": 32, "gold": 0, "mithril": 0, "stat_reward": 34, "soul_reward": 8,
        "drops": {"wolf_fang": 0.45}, "quest_target": "shadow_wolf",
    },
    "bandit": {
        "name": "Bandyta", "max_hp": 75, "damage": 9,
        "silver": 40, "gold": 0, "mithril": 0, "stat_reward": 35, "soul_reward": 8,
        "drops": {"healing_potion": 0.10}, "quest_target": None,
    },
    "skeleton": {
        "name": "Szkielet Strażnik", "max_hp": 90, "damage": 11,
        "silver": 30, "gold": 1, "mithril": 0, "stat_reward": 42, "soul_reward": 11,
        "drops": {"soul_shard": 0.55}, "quest_target": None,
    },
    "crypt_wraith": {
        "name": "Upiór Krypty", "max_hp": 120, "damage": 14,
        "silver": 0, "gold": 2, "mithril": 1, "stat_reward": 55, "soul_reward": 15,
        "drops": {"soul_shard": 0.85}, "quest_target": None,
    },
    "crystal_guardian": {
        "name": "Kryształowy Strażnik", "max_hp": 140, "damage": 15,
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
        }
        for name, decl in additions.items():
            if name not in cols:
                self.conn.execute(f"ALTER TABLE characters ADD COLUMN {name} {decl}")
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

    def create_character(self, account_id, name, race, cls):
        rname, _, strength, dexterity, constitution, intelligence, willpower = race
        cname, ctype, soul_weapon, weapon_base = cls
        self.conn.execute(
            """
            INSERT INTO characters(
                account_id,name,race,class_name,class_type,soul_weapon,weapon_base,
                strength,dexterity,constitution,intelligence,willpower,
                stat_progress,soul_level,soul_xp,soul_tier,room_id,silver,gold,mithril,deaths
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,0,1,0,1,'square',250,2,0,0)
            """,
            (
                account_id, name, rname, cname, ctype, soul_weapon, weapon_base,
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
            account_id=row["account_id"], name=row["name"], race=row["race"],
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

    def max_hp(self):
        return 40 + self.constitution * 5

    def max_mana(self):
        if self.class_type != "magic":
            return 0
        return 20 + self.intelligence * 4 + self.willpower * 3

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
            if self.class_type == "physical":
                self.strength += 1
                self.dexterity += 1
                self.constitution += 1
                messages.append("Statystyki wzrosły: Siła +1, Zręczność +1, Kondycja +1.")
            else:
                self.intelligence += 1
                self.willpower += 1
                messages.append("Statystyki wzrosły: Inteligencja +1, Siła Woli +1.")
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
            await self.send(f"{i}. {cname}. Typ {kind}. Broń Duszy: {weapon}.")
        cls = await self.choose_number(CLASSES, "Numer klasy: ")
        if cls is None:
            return False
        self.server.db.create_character(self.account_id, name, race, cls)
        self.character = Character.from_row(self.server.db.character_for_account(self.account_id))
        await self.send(f"Utworzono postać {self.character.name}.")
        await self.send("Postać nie posiada levelu. Statystyki rosną automatycznie.")
        await self.send("Na start otrzymujesz 250 srebra, 2 złota i 2 Mikstury leczenia.")
        return True

    async def enter_world(self):
        self.current_hp = self.character.max_hp()
        self.current_mana = self.character.max_mana()
        await self.server.broadcast_room(
            self.character.room_id, f"{self.character.name} pojawia się w okolicy.", exclude=self
        )
        await self.send(f"Witaj, {self.character.name}. Soulbound v{VERSION} World Core.")
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

    async def show_help(self):
        lines = [
            "help - pomoc",
            "look lub l - opis lokacji",
            "exits - dostępne kierunki",
            "map - lista lokacji świata",
            "where - aktualna lokacja",
            "north/south/east/west/up/down lub n/s/e/w/u/d - ruch",
            "who - gracze online",
            "say tekst - rozmowa lokalna",
            "tell gracz tekst - wiadomość prywatna",
            "stats - statystyki",
            "soul - Broń Duszy",
            "money - pokaż srebro, złoto i mithril",
            "exchange - pokaż kurs wymiany",
            "exchange silver/gold/mithril - wymień niższą walutę na wyższą",
            "professions / profesje - poziomy Wędkarstwa i Górnictwa",
            "tools / narzedzia - poziom Wędki i Kilofa",
            "fish / wedkuj - łów ryby; wymaga Wędki",
            "mine / kop - wydobywaj rudę; wymaga Kilofa",
            "net / siatka - zawartość Siatki na ryby",
            "bag / sakwa - zawartość Sakwy górniczej",
            "put fish net / wloz ryba siatka - przenieś ryby do Siatki",
            "put ore bag / wloz ruda sakwa - przenieś rudy do Sakwy",
            "take przedmiot net/bag / wyjmij przedmiot siatka/sakwa - wyjmij surowiec",
            "sell / sprzedaj przedmiot - sprzedaj rybę lub rudę",
            "inventory lub i - przedmioty",
            "equipment - założone wyposażenie",
            "equip przedmiot - załóż pancerz lub talizman",
            "use przedmiot - użyj przedmiotu",
            "shop - oferta sklepu w aktualnej lokacji",
            "buy przedmiot - kup przedmiot",
            "talk npc - rozmowa i zadania",
            "quests - dziennik zadań",
            "attack przeciwnik - tura walki",
            "flee - ucieczka z walki",
            "unlock - odblokuj kolejny Soul Tier",
            "save - zapis",
            "quit - wyjście",
        ]
        await self.send("KOMENDY")
        for line in lines:
            await self.send(line)

    async def show_stats(self):
        c = self.character
        await self.send(f"{c.name}. Rasa: {c.race}. Klasa: {c.class_name}.")
        await self.send("Poziom postaci: nie istnieje.")
        await self.send(
            f"Siła {c.strength}, Zręczność {c.dexterity}, Kondycja {c.constitution}, "
            f"Inteligencja {c.intelligence}, Siła Woli {c.willpower}."
        )
        await self.send(f"Rozwój statystyk: {c.stat_progress} z {STAT_GROWTH_THRESHOLD}.")
        await self.send(f"Życie: {self.current_hp} z {c.max_hp()}. Obrona: {self.defense()}.")
        if c.class_type == "magic":
            await self.send(f"Mana: {self.current_mana} z {c.max_mana()}.")
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

        trow = self.server.db.tool(self.account_id, tool_type)
        tlevel = int(trow["level"])
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
        return messages, plevel, tlevel

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

    async def show_professions(self):
        fishing = self.server.db.profession(self.account_id, "Wędkarstwo")
        mining = self.server.db.profession(self.account_id, "Górnictwo")
        await self.send("PROFESJE")
        for name, row in (("Wędkarstwo", fishing), ("Górnictwo", mining)):
            level = int(row["level"])
            if level >= PROFESSION_MAX_LEVEL:
                await self.send(
                    f"{name}: poziom {level} z {PROFESSION_MAX_LEVEL}. XP: maksimum. "
                    f"Akcje: {row['actions']}."
                )
            else:
                await self.send(
                    f"{name}: poziom {level} z {PROFESSION_MAX_LEVEL}. "
                    f"XP: {row['xp']} z {self.profession_xp_to_next(level)}. "
                    f"Akcje: {row['actions']}."
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
            if level >= TOOL_MAX_LEVEL:
                await self.send(
                    f"{name}: level {level} z {TOOL_MAX_LEVEL}. XP: maksimum. "
                    f"Użycia: {row['uses']}."
                )
            else:
                await self.send(
                    f"{name}: level {level} z {TOOL_MAX_LEVEL}. "
                    f"XP: {row['xp']} z {self.tool_xp_to_next(level)}. "
                    f"Użycia: {row['uses']}."
                )

    def fishing_loot(self, tool_level):
        r = random.random()
        if tool_level < 10:
            return "small_fish" if r < 0.72 else "river_carp"
        if tool_level < 25:
            if r < 0.38:
                return "small_fish"
            if r < 0.88:
                return "river_carp"
            return "silver_trout"
        if tool_level < 50:
            if r < 0.28:
                return "river_carp"
            if r < 0.78:
                return "silver_trout"
            return "golden_trout"
        if tool_level < 75:
            if r < 0.45:
                return "silver_trout"
            if r < 0.88:
                return "golden_trout"
            return "ancient_sturgeon"
        if r < 0.52:
            return "golden_trout"
        if r < 0.92:
            return "ancient_sturgeon"
        return "moon_eel"

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
        if tool_level < 60:
            if r < 0.45:
                return "iron_ore"
            if r < 0.85:
                return "silver_ore"
            return "gold_ore"

        # Mithril jest celowo bardzo rzadki.
        if tool_level < 80:
            mithril_chance = 0.0025   # 0,25%
        elif tool_level < 95:
            mithril_chance = 0.005    # 0,5%
        else:
            mithril_chance = 0.01     # 1%

        if r < mithril_chance:
            return "mithril_ore"

        rr = (r - mithril_chance) / (1.0 - mithril_chance)
        if tool_level < 80:
            if rr < 0.30:
                return "iron_ore"
            if rr < 0.70:
                return "silver_ore"
            return "gold_ore"
        if tool_level < 95:
            if rr < 0.18:
                return "iron_ore"
            if rr < 0.52:
                return "silver_ore"
            return "gold_ore"
        if rr < 0.10:
            return "iron_ore"
        if rr < 0.38:
            return "silver_ore"
        return "gold_ore"

    def profession_ready(self):
        now = time.time()
        remaining = PROFESSION_COOLDOWN - (now - self.last_profession_action)
        if remaining > 0:
            return False, remaining
        self.last_profession_action = now
        return True, 0.0

    async def fish(self):
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
            await self.send("Musisz chwilę odczekać przed kolejnym zarzuceniem wędki.")
            return

        tool = self.server.db.tool(self.account_id, "fishing")
        tool_level = int(tool["level"])
        item_id = self.fishing_loot(tool_level)
        self.server.db.add_storage_item(self.account_id, "net", item_id, 1)
        item = ITEMS[item_id]
        await self.send(
            f"Łowisz: {item['name']}. Połów trafia do Siatki na ryby."
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
                "Lepsza Wędka zwiększa dostęp do rzadszych i cenniejszych ryb."
            )

    async def mine(self):
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
            await self.send("Musisz chwilę odczekać przed kolejnym uderzeniem kilofa.")
            return

        tool = self.server.db.tool(self.account_id, "mining")
        tool_level = int(tool["level"])
        item_id = self.mining_loot(tool_level)
        self.server.db.add_storage_item(self.account_id, "bag", item_id, 1)
        item = ITEMS[item_id]
        await self.send(
            f"Wydobywasz: {item['name']}. Urobek trafia do Sakwy górniczej."
        )
        if item_id == "mithril_ore":
            await self.send("To wyjątkowo rzadkie znalezisko: Ruda mithrilu!")

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
                "Lepszy Kilof zwiększa dostęp do cenniejszych rud."
            )
        if new_tool_level >= 60 and tool_level < 60:
            await self.send(
                "Twój Kilof jest już wystarczająco dobry, aby mieć minimalną szansę na Rudę mithrilu."
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
        if self.server.db.item_qty(self.account_id, item_id) <= 0:
            await self.send("Nie masz tego przedmiotu.")
            return

        fish_items = FISH_RESOURCE_IDS
        ore_items = ORE_RESOURCE_IDS

        if item_id in fish_items and self.character.room_id not in {"market", "inn", "fish_market"}:
            await self.send("Ryby możesz sprzedać na Targu Rybnym, Rynku albo w Karczmie.")
            return
        if item_id in ore_items and self.character.room_id != "forge":
            await self.send("Rudy możesz sprzedać w Kuźni Dusz.")
            return

        if item_id in fish_items:
            source_container = "net"
        elif item_id in ore_items:
            source_container = "bag"
        else:
            source_container = None

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
            await self.send(f"{row['slot']}: {name}. Obrona +{defense}.")

    async def equip_item(self, query):
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
        for item_id in offers:
            item = ITEMS[item_id]
            currency = item.get("currency", "gold")
            currency_pl = {"silver": "srebra", "gold": "złota", "mithril": "mithrilu"}[currency]
            await self.send(f"{item['name']}: {item['price']} {currency_pl}. {item['desc']}")

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

    def player_damage(self):
        c = self.character
        if c.class_type == "physical":
            return max(1, c.soul_power() + c.strength // 2 + c.dexterity // 4 + random.randint(-3, 4))
        if self.current_mana >= 4:
            self.current_mana -= 4
            return max(1, c.soul_power() + c.intelligence // 2 + c.willpower // 3 + random.randint(-3, 4))
        return max(1, c.soul_power() + c.intelligence // 4 + random.randint(-2, 2))

    async def attack(self, query):
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

        incoming = max(1, template["damage"] + random.randint(-2, 2) - self.defense())
        self.current_hp -= incoming
        await self.send(
            f"{template['name']} odpowiada. Otrzymujesz {incoming} obrażeń. "
            f"Twoje życie: {max(0, self.current_hp)} z {self.character.max_hp()}."
        )
        if self.current_hp <= 0:
            await self.die(template["name"])

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
        await self.send("Wycofujesz się z walki.")

    async def die(self, killer):
        if self.combat_mob_key:
            mob = self.server.world.mobs.get(self.combat_mob_key)
            if mob and mob.engaged_by == self.character.name:
                mob.engaged_by = None
        self.combat_mob_key = None
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
                await self.show_help()
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
            elif command == "tools":
                await self.show_tools()
            elif command == "fish":
                await self.fish()
            elif command == "mine":
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
