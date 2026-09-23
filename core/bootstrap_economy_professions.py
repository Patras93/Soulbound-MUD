# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Soulbound v0.30.29 Deploy Startup Hotfix Edition
Wieloosobowy tekstowy MUD TCP/Telnet dla MUSHclienta/Mudleta.

Najważniejsze zasady projektu:
- postać ma generowany Level 1-400 i XP postaci,
- każda z sześciu statystyk ma własny automatyczny EXP i własny próg,
- liczbowy balans gry jest wyliczany przez Generator Core; nazwy, progi, wymagania i semantyka są ręcznie projektowane,
- Broń Duszy ma osobny Soul Level 1-400,
- Soul Tier 1-40 odblokowuje się osobno,
- wszystkie trwałe dane gracza są zapisywane w SQLite.
"""

import asyncio
import json
import hashlib
import hmac
import math
import os
import random
import re
import secrets
import sqlite3
import time
import unicodedata
from collections import deque
from dataclasses import dataclass
from typing import Optional

from config.balance import BLACKSMITH_QUEST_COOLDOWN_SECONDS, QUEST_REPEAT_COOLDOWN_SECONDS

# v0.40.0: formerly embedded runtime engines are real importable modules.
from core import generator_core as generator_core_v027
from world import topology_generator as world_topology_generator_v0281
from world import dynamic_world_generator as dynamic_world_v029
from world import logic_validator as world_logic_validator_v030

VERSION = "0.58.2"
GLOBAL_SKILL_BUFF_DURATION_SECONDS = 30
HISTORY_BUFFER_LIMIT = 100
HISTORY_BUFFER_DEFAULT_SHOW = 20

# v0.30.10: cykliczny Happy Hour EXP. Każda pełna godzina zegarowa
# zaczyna 15-minutowe okno x2 EXP. Jedna funkcja jest źródłem prawdy dla
# statusu, komunikatów oraz wszystkich kanałów progresji.
DOUBLE_XP_EVENT_INTERVAL_SECONDS = 60 * 60
DOUBLE_XP_EVENT_DURATION_SECONDS = 15 * 60
DOUBLE_XP_EVENT_MULTIPLIER = 2

def double_xp_event_state(now=None):
    now = time.time() if now is None else float(now)
    elapsed = now % DOUBLE_XP_EVENT_INTERVAL_SECONDS
    active = elapsed < DOUBLE_XP_EVENT_DURATION_SECONDS
    if active:
        remaining = max(0, int(math.ceil(DOUBLE_XP_EVENT_DURATION_SECONDS - elapsed)))
        next_start = max(0, int(math.ceil(DOUBLE_XP_EVENT_INTERVAL_SECONDS - elapsed)))
    else:
        remaining = 0
        next_start = max(0, int(math.ceil(DOUBLE_XP_EVENT_INTERVAL_SECONDS - elapsed)))
    return {
        "active": active,
        "multiplier": DOUBLE_XP_EVENT_MULTIPLIER if active else 1,
        "remaining_seconds": remaining,
        "next_start_seconds": next_start,
        "duration_seconds": DOUBLE_XP_EVENT_DURATION_SECONDS,
    }

# v0.8.72: właścicielskie komendy administracyjne. Nazwy kont podaje się
# po stronie serwera, np. SOULBOUND_ADMIN_ACCOUNTS=Patryk. Nigdy nie są
# przyznawane na podstawie nazwy postaci.
ADMIN_ACCOUNT_NAMES = {
    name.strip().casefold()
    for name in os.environ.get("SOULBOUND_ADMIN_ACCOUNTS", "").split(",")
    if name.strip()
}
MAX_CHARACTERS_PER_ACCOUNT = 14

HOST = os.getenv("SOULBOUND_HOST", "0.0.0.0")
_RAILWAY_TCP_PORT = os.getenv("RAILWAY_TCP_APPLICATION_PORT", "").strip()
_SOULBOUND_PORT = os.getenv("SOULBOUND_PORT", "").strip()
_GENERIC_PORT = os.getenv("PORT", "").strip()

def _valid_port(raw, fallback=None):
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return fallback
    return value if 1 <= value <= 65535 else fallback

# Railway raw-TCP proxy has the strongest signal when configured. Otherwise
# Railway's injected PORT must win over any legacy Soulbound override.
if _RAILWAY_TCP_PORT:
    PORT = _valid_port(_RAILWAY_TCP_PORT, 4000)
    PORT_SOURCE = "RAILWAY_TCP_APPLICATION_PORT"
elif _GENERIC_PORT:
    PORT = _valid_port(_GENERIC_PORT, 4000)
    PORT_SOURCE = "PORT"
elif _SOULBOUND_PORT:
    PORT = _valid_port(_SOULBOUND_PORT, 4000)
    PORT_SOURCE = "SOULBOUND_PORT"
else:
    PORT = 4000
    PORT_SOURCE = "default"

_VOLUME_PATH = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "").strip()
_DEFAULT_DB = os.path.join(_VOLUME_PATH, "soulbound.db") if _VOLUME_PATH else "soulbound.db"
DB_PATH = os.getenv("SOULBOUND_DB", _DEFAULT_DB)

# ============================================================
# v0.25.2 - ORE ATLAS THRESHOLD HOTFIX
# Atlas podstawowych rud pokazuje dokładnie te same minimalne progi Kilofa i piętra,
# których używa realna logika Kopalni Głębinowej: Żelazo 10/10, Srebro 25/25, Złoto 50/50.

# v0.25.1 - UNIFIED DEEP MINE
# Wszystkie normalne rudy/minerały, geody i klejnoty pochodzą z jednej
# Kopalni Głębinowej. Dawne źródła terenowe i Kopalnia Kryształów nie są
# już aktywnymi miejscami Górnictwa.
#
# v0.25.0 - GLOBAL GENERATOR 2.0
# Jeden trwały seed serwera dla nowych warstw proceduralnych. Nie zmieniamy
# historycznych seedów v0.11-v0.21, dzięki czemu istniejące mapy i save'y
# zachowują dawny układ. Seed v0.25 steruje nowymi profilami świata,
# hotspotami profesji, geologią Kopalni oraz opisami proceduralnych pięter.
# ============================================================
def _v0250_world_seed_path():
    override = os.getenv("SOULBOUND_WORLD_SEED_FILE", "").strip()
    if override:
        return override
    base_dir = os.path.dirname(os.path.abspath(DB_PATH)) or "."
    return os.path.join(base_dir, "soulbound_world_seed.txt")


def _v0250_load_or_create_world_seed():
    explicit = os.getenv("SOULBOUND_WORLD_SEED", "").strip()
    if explicit:
        return explicit
    path = _v0250_world_seed_path()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            value = handle.read().strip()
            if value:
                return value
    except OSError:
        pass
    value = secrets.token_hex(24)
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            handle.write(value + "\n")
        os.replace(tmp, path)
    except OSError:
        # Read-only deployment: seed remains stable for the lifetime of process.
        pass
    return value


V0250_WORLD_SEED = _v0250_load_or_create_world_seed()
V0250_WORLD_SEED_ID = hashlib.sha256(V0250_WORLD_SEED.encode("utf-8")).hexdigest()[:12]
V0250_HOTSPOT_SECONDS = 60 * 60


def v0250_seed_int(*parts):
    payload = ":".join(str(part) for part in (V0250_WORLD_SEED,) + parts)
    return int(hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16], 16)


def v0250_rng(*parts):
    return random.Random(v0250_seed_int(*parts))


V0250_WORLD_AMBIENCE = (
    "spokojne echo terenu", "ślady niedawnej wędrówki", "zmienny wiatr",
    "stare ślady na ziemi", "nietypowa cisza", "odległe odgłosy świata",
    "świeże tropy", "lekka mgła", "wyraźny zapach roślin", "suchy pył w powietrzu",
)
V0250_WORLD_FEATURES = (
    "stary kamienny znak", "wąskie boczne przejście", "naturalna nisza",
    "porzucone ognisko", "ślady dawnego obozu", "niewielkie rumowisko",
    "wyróżniająca się formacja terenu", "stara ścieżka", "ukryty zakątek",
    "miejsce osłonięte od wiatru",
)
V0250_CITY_AMBIENCE = (
    "ruch mieszkańców", "dźwięk pracy rzemieślników", "przechodzący patrol",
    "gwar rozmów", "odgłos wozów", "spokojny ruch kupców",
)
V0250_GATHER_HOTSPOT_LABELS = {
    "fishing": ("Ławica", "Żerowisko", "Dobry prąd"),
    "mining": ("Bogata żyła", "Świeże odsłonięcie", "Gęsta mineralizacja"),
    "woodcutting": ("Gęsty drzewostan", "Dobre drewno", "Stary zagajnik"),
    "herbalism": ("Rozkwit ziół", "Żyzna gleba", "Skupisko roślin"),
}


def v0250_room_generator_profile(room_id):
    room = globals().get("ROOMS", {}).get(str(room_id), {})
    zone = str(room.get("zone", "Nieznana strefa"))
    rng = v0250_rng("room-profile", room_id, zone)
    city = "miasto" in zone.casefold() or "świątynia" in zone.casefold()
    ambience_pool = V0250_CITY_AMBIENCE if city else V0250_WORLD_AMBIENCE
    return {
        "seed_id": V0250_WORLD_SEED_ID,
        "ambience": rng.choice(ambience_pool),
        "feature": rng.choice(V0250_WORLD_FEATURES),
        "variant": 1 + rng.randrange(9999),
        "city": city,
    }


def v0250_gather_hotspot(room_id, tool_type=None, now=None):
    tool = str(tool_type or "").strip().casefold()
    labels = V0250_GATHER_HOTSPOT_LABELS.get(tool)
    if not labels:
        return {"label":"", "quantity_bonus":0, "xp_mult":1.0, "slot":0}
    room = globals().get("ROOMS", {}).get(str(room_id), {})
    zone = str(room.get("zone", ""))
    slot = int((time.time() if now is None else float(now)) // V0250_HOTSPOT_SECONDS)
    roll = v0250_seed_int("hotspot", slot, zone, tool)
    # Około 1/4 stref profesyjnych ma aktywny bonus w danej godzinie.
    if roll % 4 != 0:
        return {"label":"", "quantity_bonus":0, "xp_mult":1.0, "slot":slot}
    label = labels[(roll // 4) % len(labels)]
    return {
        "label": f"Global Generator: {label}",
        "quantity_bonus": 0,
        "xp_mult": 1.05,
        "slot": slot,
    }


def v0250_mine_floor_profile(floor):
    floor = max(1, int(floor))
    rng = v0250_rng("deep-mine-profile", floor)
    strata = (
        "granitowa warstwa", "ciemny bazalt", "łupek z metalicznymi żyłami",
        "kwarcowa skała", "żelazisty kamień", "kryształowa warstwa",
        "stary wulkaniczny przekop", "zbita skała głębinowa",
    )
    shapes = (
        "szeroka komora", "wąski chodnik", "pęknięta galeria", "naturalna grota",
        "stary szyb", "rozgałęziony przekop", "komora podparta filarami",
    )
    signs = (
        "ślady dawnych górników", "świeże pęknięcia skały", "drobne kryształy w ścianach",
        "stare stemple górnicze", "wilgoć spływającą po skale", "pył mineralny w powietrzu",
    )
    return {
        "strata": rng.choice(strata),
        "shape": rng.choice(shapes),
        "sign": rng.choice(signs),
        "profile_id": v0250_seed_int("mine-profile-id", floor) % 100000,
    }


def v0250_instance_floor_profile(kind, floor):
    rng = v0250_rng("instance-profile", kind, int(floor))
    motifs = (
        "echo dawnych walk", "ślady starego rytuału", "niestabilne sklepienie",
        "gęsta mgła przy ziemi", "stare runy na ścianach", "rozbite posągi",
        "zimny przeciąg", "ciemne boczne nisze", "pozostałości dawnego obozu",
    )
    layouts = (
        "liczne pętle", "dwie główne odnogi", "wąskie łączniki", "szerokie galerie",
        "krótkie ślepe odnogi", "kilka alternatywnych przejść",
    )
    return {"motif": rng.choice(motifs), "layout": rng.choice(layouts)}

MAX_CLIENTS = int(os.getenv("SOULBOUND_MAX_CLIENTS", "100"))
PBKDF2_ROUNDS = 210_000

STAT_GROWTH_THRESHOLD = 100

def stat_quality_label(value):
    """Czytelna słowna ocena statystyki bez fałszywego capu po 200."""
    value = max(0, int(value))
    if value <= 5: return "bardzo słabo"
    if value <= 9: return "słabo"
    if value <= 13: return "poniżej przeciętnej"
    if value <= 19: return "przeciętnie"
    if value <= 29: return "dobrze"
    if value <= 44: return "bardzo dobrze"
    if value <= 64: return "świetnie"
    if value <= 89: return "wybitnie"
    if value <= 119: return "mistrzowsko"
    if value <= 159: return "nadludzko"
    if value <= 199: return "legendarnie"
    if value <= 399: return "mitycznie"
    if value <= 999: return "transcendentalnie"
    if value <= 4999: return "bosko"
    if value <= 9999: return "kosmicznie"
    if value <= 19999: return "absolutnie"
    return "poza skalą"

SOUL_MAX_LEVEL = 400
SOUL_TIER_THRESHOLDS = (
    1, 10, 20, 25, 35, 45, 60, 70, 80, 90,
    100, 110, 120, 130, 140, 150, 160, 170, 180, 200,
) + tuple(range(210, 401, 10))
SOUL_MAX_TIER = 40

# Pierwsze pięć progów zachowane jako aliasy kompatybilności.
TIER2_LEVEL = SOUL_TIER_THRESHOLDS[1]
TIER3_LEVEL = SOUL_TIER_THRESHOLDS[2]
TIER4_LEVEL = SOUL_TIER_THRESHOLDS[3]
TIER5_LEVEL = SOUL_TIER_THRESHOLDS[4]

# v0.8.53: każdy awans Soul Tier od 2 do 20 wymaga jednorazowej
# Próby Broni Duszy u Kapłana Elora. Cztery stare quest_id pozostają
# bez zmian, aby istniejące save'y zachowały ukończone Próby.
SOUL_TRIAL_QUEST_IDS = {
    2: "soul_tier_02_trial",
    3: "soul_tier_03_trial",
    4: "soul_tier_2_trial",
    5: "soul_tier_05_trial",
    6: "soul_tier_06_trial",
    7: "soul_tier_3_trial",
    8: "soul_tier_08_trial",
    9: "soul_tier_09_trial",
    10: "soul_tier_10_trial",
    11: "soul_tier_11_trial",
    12: "soul_tier_12_trial",
    13: "soul_tier_4_trial",
    14: "soul_tier_14_trial",
    15: "soul_tier_15_trial",
    16: "soul_tier_16_trial",
    17: "soul_tier_17_trial",
    18: "soul_tier_18_trial",
    19: "soul_tier_5_trial",
    20: "soul_tier_20_trial",
}
SOUL_TIER_POWER_BONUSES = (
    0, 4, 8, 12, 18, 24, 30, 34, 38, 42,
    46, 50, 55, 60, 65, 70, 75, 80, 85, 100,
) + tuple(102 + i * 2 for i in range(20))
SOUL_TIER_CLASS_BONUS_PERCENT = (
    5, 7, 8, 10, 12, 13, 15, 16, 17, 18,
    19, 19, 20, 21, 22, 23, 24, 24, 25, 30,
) + tuple(30 + (i + 1) // 2 for i in range(20))
# v0.9.0: specjalizacja Łotrzyka nie może marnować progresji na hard capie
# 35% uniku. Sam Soul Weapon daje teraz maks. +5 pp uniku; pozostała część
# jego budżetu specjalizacji przechodzi w umiarkowane obrażenia fizyczne.
SOUL_TIER_DODGE_BONUS = (
    0.01, 0.01, 0.015, 0.015, 0.02, 0.02, 0.025, 0.025, 0.03, 0.03,
    0.03, 0.035, 0.035, 0.04, 0.04, 0.04, 0.045, 0.045, 0.05, 0.05,
) + (0.05,) * 20
SOUL_TIER_GUARDIAN_REDUCTION = (
    3, 4, 5, 6, 7, 8, 9, 9, 10, 10,
    11, 11, 12, 12, 13, 13, 14, 14, 15, 18,
) + tuple(18 + (i + 1) // 2 for i in range(20))

# v0.34.1: Weapon Traits per class. Każda klasa ma własny profil cech
# Broni Duszy na Soul Tierach 1-40. Cechy są pasywne i dotyczą wyłącznie
# zwykłego ataku Broni Duszy; nie są skillami ani spellami.
_SOUL_TRAIT_BASE_NAMES = (
    "Przebudzenie", "Instynkt", "Rezonans", "Krwiobieg", "Wyrok",
    "Zapłon", "Przenikliwość", "Harmonia", "Puls", "Łowy",
    "Furia", "Wizja", "Echo", "Szkarłat", "Egzekucja",
    "Transcendencja", "Gwiezdny Znak", "Podwójny Rezonans", "Tętno", "Zagłada",
    "Żar", "Pustka", "Wieczność", "Strumień", "Pieczęć",
    "Astralny Płomień", "Otchłań", "Nieskończoność", "Krew Gwiazd", "Ostateczność",
    "Przeznaczenie", "Absolut", "Kosmos", "Nieśmiertelność", "Sąd",
    "Apoteoza", "Wieczyste Oko", "Echo Absolutu", "Serce", "Korona Duszy",
)

# effect, base value. Poszczególne klasy mają inne cykle, więc ich Broń Duszy
# rozwija się inaczej nawet przy tym samym Tierze.
_SOUL_TRAIT_CLASS_PROFILES = {
    "Wojownik":   {"theme":"Przysięgi", "cycle":(("damage_percent",1.20),("crit_damage_percent",3.0),("lifesteal_percent",0.35),("crit_chance",0.004),("execute_damage_percent",1.2))},
    "Berserker":  {"theme":"Krwi", "cycle":(("damage_percent",1.45),("lifesteal_percent",0.55),("crit_damage_percent",3.5),("execute_damage_percent",1.8),("damage_percent",0.85))},
    "Łotrzyk":    {"theme":"Cienia", "cycle":(("crit_chance",0.006),("crit_damage_percent",3.4),("execute_damage_percent",1.8),("damage_percent",0.85),("lifesteal_percent",0.30))},
    "Łowca":      {"theme":"Tropu", "cycle":(("crit_chance",0.005),("damage_percent",1.05),("execute_damage_percent",1.6),("crit_damage_percent",3.0),("boss_damage_percent",1.2))},
    "Mnich":      {"theme":"Ducha", "cycle":(("damage_percent",0.95),("lifesteal_percent",0.45),("crit_chance",0.004),("mana_restore_percent",0.40),("crit_damage_percent",2.6))},
    "Strażnik":   {"theme":"Bastionu", "cycle":(("lifesteal_percent",0.55),("boss_damage_percent",1.0),("damage_percent",0.85),("crit_damage_percent",2.3),("execute_damage_percent",1.0))},
    "Mag":        {"theme":"Arkanów", "cycle":(("mana_restore_percent",0.65),("damage_percent",1.0),("crit_damage_percent",3.1),("crit_chance",0.004),("boss_damage_percent",1.1))},
    "Nekromanta": {"theme":"Żniwa", "cycle":(("lifesteal_percent",0.70),("execute_damage_percent",1.7),("damage_percent",0.95),("mana_restore_percent",0.40),("crit_damage_percent",2.6))},
    "Kapłan":     {"theme":"Światła", "cycle":(("lifesteal_percent",0.55),("mana_restore_percent",0.55),("damage_percent",0.85),("boss_damage_percent",1.0),("crit_chance",0.0035))},
    "Czarownik":  {"theme":"Otchłani", "cycle":(("damage_percent",1.15),("crit_damage_percent",3.2),("mana_restore_percent",0.50),("execute_damage_percent",1.5),("crit_chance",0.004))},
    "Druid":      {"theme":"Dziczy", "cycle":(("lifesteal_percent",0.55),("damage_percent",0.90),("mana_restore_percent",0.50),("boss_damage_percent",1.0),("execute_damage_percent",1.2))},
    "Psionik":    {"theme":"Umysłu", "cycle":(("crit_chance",0.0045),("mana_restore_percent",0.60),("crit_damage_percent",3.0),("damage_percent",0.95),("execute_damage_percent",1.3))},
    "Mec":        {"theme":"Rdzenia", "cycle":(("boss_damage_percent",1.35),("damage_percent",1.10),("crit_damage_percent",2.7),("lifesteal_percent",0.35),("execute_damage_percent",1.2))},
    "Inżynier":   {"theme":"Omni-Narzędzia", "cycle":(("crit_chance",0.0045),("boss_damage_percent",1.25),("damage_percent",1.0),("mana_restore_percent",0.45),("crit_damage_percent",2.8))},
}

_SOUL_TRAIT_EFFECT_DESCRIPTIONS = {
    "damage_percent": lambda v: f"+{v:g} procent obrażeń zwykłego ataku Broni Duszy",
    "crit_chance": lambda v: f"+{v*100:g} punktu procentowego szansy na krytyk zwykłego ataku Broni Duszy",
    "crit_damage_percent": lambda v: f"+{v:g} procent obrażeń krytycznych zwykłego ataku Broni Duszy",
    "lifesteal_percent": lambda v: f"leczy za {v:g} procent obrażeń zadanych zwykłym atakiem Broni Duszy",
    "execute_damage_percent": lambda v: f"+{v:g} procent obrażeń zwykłego ataku przeciw celom z 35 procent HP lub mniej",
    "mana_restore_percent": lambda v: f"odzyskuje Manę równą {v:g} procent obrażeń zwykłego ataku Broni Duszy",
    "boss_damage_percent": lambda v: f"+{v:g} procent obrażeń zwykłego ataku przeciw bossom",
}

SOUL_TIER_TRAITS_BY_CLASS = {}
for _class_name, _profile in _SOUL_TRAIT_CLASS_PROFILES.items():
    _rows = {}
    _cycle = _profile["cycle"]
    for _tier, _base_name in enumerate(_SOUL_TRAIT_BASE_NAMES, start=1):
        _effect, _value = _cycle[(_tier - 1) % len(_cycle)]
        _name = f"{_base_name} {_profile['theme']}"
        _rows[_tier] = {
            "name": _name,
            "effect": _effect,
            "value": float(_value),
            "description": _SOUL_TRAIT_EFFECT_DESCRIPTIONS[_effect](float(_value)),
        }
    SOUL_TIER_TRAITS_BY_CLASS[_class_name] = _rows

def soul_weapon_trait_for_tier(tier, class_name=None):
    tier = max(1, min(SOUL_MAX_TIER, int(tier)))
    class_name = class_name or "Wojownik"
    rows = SOUL_TIER_TRAITS_BY_CLASS.get(class_name) or SOUL_TIER_TRAITS_BY_CLASS["Wojownik"]
    return rows.get(tier)

def soul_weapon_trait_totals(tier, class_name=None):
    tier = max(1, min(SOUL_MAX_TIER, int(tier)))
    class_name = class_name or "Wojownik"
    rows = SOUL_TIER_TRAITS_BY_CLASS.get(class_name) or SOUL_TIER_TRAITS_BY_CLASS["Wojownik"]
    totals = {
        "damage_percent": 0.0, "crit_chance": 0.0, "crit_damage_percent": 0.0,
        "lifesteal_percent": 0.0, "execute_damage_percent": 0.0,
        "mana_restore_percent": 0.0, "boss_damage_percent": 0.0,
    }
    for _t in range(1, tier + 1):
        row = rows[_t]
        totals[row["effect"]] += float(row["value"])
    return totals

SOUL_MILESTONE_TIERS = (5, 10, 15, 20)
SOUL_MILESTONE_NAMES = {
    5: "Przebudzenie Broni Duszy",
    10: "Wzmocnienie Broni Duszy",
    15: "Transcendencja Broni Duszy",
    20: "Apoteoza Broni Duszy",
}
SOUL_MILESTONE_SPECIALIZATION_BONUS = {5: 2, 10: 4, 15: 7, 20: 10}
SOUL_MILESTONE_DODGE_BONUS = {5: 0.0, 10: 0.0, 15: 0.0, 20: 0.0}
SOUL_MILESTONE_GUARDIAN_REDUCTION = {5: 2, 10: 4, 15: 6, 20: 8}
# Tiery 21-40 mają dalszą moc bazową, ale nie dodają nowych globalnych
# milestone buffów; dzięki temu zakres 201-400 nie podwaja buildów klasowych.
SOUL_TRIAL_QUEST_IDS.update({
    tier: f"soul_tier_{tier:02d}_trial" for tier in range(21, 41)
})

# v0.26.1: Próby Broni Duszy mają czytelne pasma trudności.
# Początek nie wymaga już bossów Krypty o dziesiątkach tysięcy HP.
def soul_trial_difficulty_band(tier):
    tier = int(tier)
    if tier <= 4:
        return "Początkująca"
    if tier <= 7:
        return "Poszukiwacza"
    if tier <= 12:
        return "Weterana"
    if tier <= 20:
        return "Mistrzowska"
    if tier <= 30:
        return "Endgame"
    return "Ekstremalna"
REGULAR_MOB_RESPAWN_SECONDS = 120
BOSS_RESPAWN_SECONDS = 300
TRAINING_DUMMY_RESPAWN_SECONDS = 60
GLOBAL_MOB_RESPAWN_MULTIPLIER = 2.0
CORPSE_LIFETIME_SECONDS = 600
GLOBAL_MOB_HP_MULTIPLIER = 2.0

# Ekonomia v0.8.60: jedno wspólne saldo z trzema nominałami.
# Wewnętrznie saldo jest przechowywane jako łączna liczba srebra.
# 100 srebra = 1 złoto.
# 1 000 000 złota = 1 mithril.
# Zatem 1 mithril = 100 000 000 srebra.
SILVER_PER_GOLD = 100
GOLD_PER_MITHRIL = 1_000_000
SILVER_PER_MITHRIL = SILVER_PER_GOLD * GOLD_PER_MITHRIL
COINS_PER_OLD_GOLD = SILVER_PER_GOLD
COINS_PER_OLD_MITHRIL = SILVER_PER_MITHRIL
# v0.19: ekonomia startuje mało i czytelnie. Globalny generator rośnie dopiero
# wraz z postępem; nowa postać nadal zaczyna dokładnie z 2 zł i 30 srebra.
STARTING_SILVER = 30
STARTING_GOLD = 2
STARTING_MITHRIL = 0
CURRENCY_SQLITE_SAFE_TOTAL = 8_000_000_000_000_000_000

def legacy_currency_to_coins(silver=0, gold=0, mithril=0):
    """Zwraca jedno wspólne saldo w najmniejszym nominale: srebrze."""
    return (
        max(0, int(silver))
        + max(0, int(gold)) * SILVER_PER_GOLD
        + max(0, int(mithril)) * SILVER_PER_MITHRIL
    )

def normalize_currency_values(silver, gold, mithril):
    """Normalizuje trzy nominały do jednego salda przechowywanego w silver."""
    total = legacy_currency_to_coins(silver, gold, mithril)
    # SQLite INTEGER jest 64-bitowy. Pozwalamy na gospodarkę w bilionach i
    # wyżej, ale chronimy zapis przed przepełnieniem przy ekstremalnym endgame.
    total = min(CURRENCY_SQLITE_SAFE_TOTAL, max(0, int(total)))
    return total, 0, 0

def currency_denominations(total_silver):
    """Rozkłada wspólne saldo na mithril, złoto i srebro tylko do prezentacji."""
    total_silver = max(0, int(total_silver))
    mithril, remainder = divmod(total_silver, SILVER_PER_MITHRIL)
    gold, silver = divmod(remainder, SILVER_PER_GOLD)
    return mithril, gold, silver

def currency_unit_multiplier(raw):
    """Mnożnik nominału dla komend. Wszystkie trafiają do jednego salda."""
    value = normalize_lookup_text(raw) if 'normalize_lookup_text' in globals() else str(raw or '').strip().lower()
    if value in ('silver','srebro','srebra','srebrnych','s'):
        return 1
    if value in ('gold','zloto','złoto','zlota','złota','g','zl','zł'):
        return SILVER_PER_GOLD
    if value in ('mithril','mithrilu','m'):
        return SILVER_PER_MITHRIL
    if value in ('moneta','monety','monet','coin','coins'):
        return 1
    return None

def currency_reading_text(silver=0, gold=0, mithril=0, *, full_names=False, include_zero=False):
    """Czytelny dla NVDA zapis jednego salda w nominałach mithril/złoto/srebro."""
    total = legacy_currency_to_coins(silver, gold, mithril)
    mithril_count, gold_count, silver_count = currency_denominations(total)
    parts = []
    if mithril_count or include_zero:
        parts.append(f"{mithril_count} mithril")
    if gold_count or include_zero:
        parts.append(f"{gold_count} złota")
    if silver_count or include_zero or not parts:
        parts.append(f"{silver_count} srebra")
    return ", ".join(parts)


PROFESSION_MAX_LEVEL = 400
BLACKSMITHING_MAX_LEVEL = 400
JEWELCRAFTING_MAX_LEVEL = 400

# v0.8.66: wszystkie umiejętności profesyjne rozwijają się 1-200.
# Poziom PROFESJI odpowiada za tempo pracy i wymagania receptur/zleceń.
# Poziom NARZĘDZIA nie skraca czasu: odblokowuje lepsze surowce oraz
# zwiększa jakość/rare roll i szansę dodatkowego urobku/produktu.
PROFESSION_XP_GAIN_MULTIPLIER = 2
PROFESSION_XP_REQUIREMENT_MULTIPLIER = 1

CHARISMA_DISCOUNT_STEP = 4
CHARISMA_MAX_DISCOUNT = 25
PARTY_BASE_CAPACITY = 8
PARTY_CHARISMA_STEP = 25
PARTY_AUTO_HEAL_THRESHOLD = 0.85

PROFESSION_RANK_THRESHOLDS = (
    1, 15, 30, 45, 60, 75, 90,
    100, 120, 140, 160, 180, 200,
) + tuple(range(220, 401, 20))
PROFESSION_MAX_RANK = len(PROFESSION_RANK_THRESHOLDS)
BLACKSMITHING_MAX_RANK = PROFESSION_MAX_RANK
BLACKSMITHING_RANK_THRESHOLDS = PROFESSION_RANK_THRESHOLDS

PROFESSION_RANK_NAMES = {
    "Wędkarstwo": (
        "Uczeń Wędkarstwa", "Adept Wędkarstwa", "Czeladnik Wędkarstwa",
        "Specjalista Wędkarstwa", "Ekspert Wędkarstwa", "Mistrz Wędkarstwa",
        "Arcymistrz Wędkarstwa", "Legenda Wędkarstwa", "Runiczny Wędkarz",
        "Wędkarz Smoczych Głębin", "Astralny Wędkarz", "Wędkarz Pustki",
        "Wieczny Mistrz Wędkarstwa",
    ),
    "Górnictwo": (
        "Uczeń Górnictwa", "Adept Górnictwa", "Czeladnik Górnictwa",
        "Specjalista Górnictwa", "Ekspert Górnictwa", "Mistrz Górnictwa",
        "Arcymistrz Górnictwa", "Legenda Górnictwa", "Górnik Runiczny",
        "Górnik Smoczej Stali", "Górnik Astralny", "Górnik Pustki",
        "Wieczny Mistrz Górnictwa",
    ),
    "Drwalstwo": (
        "Uczeń Drwalstwa", "Adept Drwalstwa", "Czeladnik Drwalstwa",
        "Specjalista Drwalstwa", "Ekspert Drwalstwa", "Mistrz Drwalstwa",
        "Arcymistrz Drwalstwa", "Legenda Drwalstwa", "Runiczny Drwal",
        "Drwal Smoczego Drewna", "Astralny Drwal", "Drwal Pustki",
        "Wieczny Mistrz Drwalstwa",
    ),
    "Zielarstwo": (
        "Uczeń Zielarstwa", "Adept Zielarstwa", "Czeladnik Zielarstwa",
        "Specjalista Zielarstwa", "Ekspert Zielarstwa", "Mistrz Zielarstwa",
        "Arcymistrz Zielarstwa", "Legenda Zielarstwa", "Runiczny Zielarz",
        "Zielarz Smoczego Szałwii", "Astralny Zielarz", "Zielarz Pustki",
        "Wieczny Mistrz Zielarstwa",
    ),
    "Gotowanie": (
        "Uczeń Gotowania", "Adept Gotowania", "Czeladnik Gotowania",
        "Specjalista Gotowania", "Ekspert Gotowania", "Mistrz Gotowania",
        "Arcymistrz Gotowania", "Legenda Gotowania", "Runiczny Kuchmistrz",
        "Kuchmistrz Smoczego Ognia", "Astralny Kuchmistrz", "Kuchmistrz Pustki",
        "Wieczny Mistrz Gotowania",
    ),
    "Alchemia": (
        "Uczeń Alchemii", "Adept Alchemii", "Czeladnik Alchemii",
        "Specjalista Alchemii", "Ekspert Alchemii", "Mistrz Alchemii",
        "Arcymistrz Alchemii", "Legenda Alchemii", "Alchemik Runiczny",
        "Alchemik Smoczej Stali", "Alchemik Astralny", "Alchemik Pustki",
        "Wieczny Mistrz Alchemii",
    ),
    "Kowalstwo": (
        "Uczeń Kowalstwa", "Adept Kowalstwa", "Czeladnik Kowalstwa",
        "Specjalista Kowalstwa", "Ekspert Kowalstwa", "Mistrz Kowalstwa",
        "Arcymistrz Kowalstwa", "Legenda Kowalstwa", "Kowal Runiczny",
        "Kowal Smoczej Stali", "Kowal Astralny", "Kowal Pustki",
        "Wieczny Mistrz Kowalstwa",
    ),
    "Jubilerstwo": (
        "Uczeń Jubilerstwa", "Adept Jubilerstwa", "Czeladnik Jubilerstwa",
        "Specjalista Jubilerstwa", "Ekspert Jubilerstwa", "Mistrz Jubilerstwa",
        "Arcymistrz Jubilerstwa", "Legenda Jubilerstwa", "Jubiler Runiczny",
        "Jubiler Smoczej Stali", "Jubiler Astralny", "Jubiler Pustki",
        "Wieczny Mistrz Jubilerstwa",
    ),
}

# v0.9.12: prestiżowe rangi 201-400. Nie dają dodatkowej mocy same z siebie;
# pokazują dalszą progresję profesji i są czytane przez NVDA/NPC.
_PROFESSION_400_RANK_SUFFIXES = (
    "Paragon", "Transcendentny Mistrz", "Mistrz Horyzontu",
    "Mistrz Otchłani", "Mistrz Gwiezdnego Szlaku",
    "Mistrz Pierwotnej Sztuki", "Mistrz Nieskończoności",
    "Mistrz Korony Świata", "Mistrz Ponadczasowy", "Arcylegenda",
)
for _profession_name, _names in list(PROFESSION_RANK_NAMES.items()):
    PROFESSION_RANK_NAMES[_profession_name] = tuple(_names) + tuple(
        f"{suffix} {_profession_name}" for suffix in _PROFESSION_400_RANK_SUFFIXES
    )

TOOL_PROFESSION_MAP = {
    "fishing": "Wędkarstwo",
    "mining": "Górnictwo",
    "woodcutting": "Drwalstwo",
    "crafting": "Kowalstwo",
    "cooking": "Gotowanie",
    "herbalism": "Zielarstwo",
    "alchemy": "Alchemia",
    "jewelcrafting": "Jubilerstwo",
}

def profession_for_tool_type(tool_type):
    return TOOL_PROFESSION_MAP.get(str(tool_type or ""))

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
    if value in ("cooking", "gotowanie", "kucharz"):
        return "Gotowanie"
    if value in ("alchemy", "alchemia"):
        return "Alchemia"
    if value in (
        "blacksmithing", "smithing", "kowalstwo",
        "kowal", "rzemioslo", "rzemiosło",
    ):
        return "Kowalstwo"
    if value in (
        "jewelcrafting", "jewelry", "jubilerstwo",
        "jubiler", "bizuteria", "biżuteria",
    ):
        return "Jubilerstwo"
    return str(profession)

def profession_max_level(profession):
    return PROFESSION_MAX_LEVEL

def profession_rank_thresholds(profession):
    return PROFESSION_RANK_THRESHOLDS

def profession_max_rank(profession):
    return PROFESSION_MAX_RANK

def profession_rank(level, profession=None):
    thresholds = profession_rank_thresholds(profession)
    level = max(1, int(level or 1))
    rank = 1
    for index, threshold in enumerate(thresholds, start=1):
        if level >= int(threshold):
            rank = index
        else:
            break
    return min(rank, profession_max_rank(profession))

def profession_rank_name(profession, level):
    profession = normalize_profession_name(profession)
    names = PROFESSION_RANK_NAMES.get(profession)
    if not names:
        return f"Ranga {profession_rank(level, profession)}"
    rank = profession_rank(level, profession)
    return names[min(rank - 1, len(names) - 1)]

# v0.9.7: NPC profesyjni reagują na realną rangę danej profesji.
# Warstwa jest wyłącznie dialogowa/prestiżowa: nie zmienia cen, XP ani statystyk.
def profession_npc_reaction_stage(rank):
    rank = max(1, min(PROFESSION_MAX_RANK, int(rank or 1)))
    if rank == 1:
        return "uczen"
    if rank <= 3:
        return "adept"
    if rank <= 5:
        return "specjalista"
    if rank <= 7:
        return "mistrz"
    if rank <= 12:
        return "legenda"
    return "wieczny"


PROFESSION_NPC_RANK_REACTIONS = {
    "fisher_tomas": {
        "uczen": "Dopiero zaczynasz, więc ucz się czytać wodę i nie śpiesz się z wielkimi połowami.",
        "adept": "Masz już pewną rękę. Teraz zacznij rozpoznawać łowiska po tym, co naprawdę w nich żyje.",
        "specjalista": "Widać doświadczenie. Takiego wędkarza można już wysłać na trudniejsze wody.",
        "mistrz": "Nie muszę ci tłumaczyć podstaw. Twoje połowy mówią same za siebie.",
        "legenda": "Ha! Taką rangę widuje się rzadziej niż legendarne ryby. Dobrze cię widzieć przy moim targu.",
        "wieczny": "Wieczny Mistrz przy moim straganie. Dziś to raczej ja powinienem słuchać twoich opowieści z wody.",
    },
    "miner_toren": {
        "uczen": "Na początku najważniejsze jest pewne uderzenie i powrót z kopalni w jednym kawałku.",
        "adept": "Już odróżniasz zwykły kamień od żyły wartej pracy.",
        "specjalista": "Masz oko do skały. Głębsze poziomy nie powinny cię już zaskakiwać.",
        "mistrz": "Twojego kilofa nie trzeba przedstawiać. W kopalni zostawiasz po sobie porządną robotę.",
        "legenda": "Górnicy mówią o takich jak ty przy ognisku. Rzadko widuję kogoś z taką rangą.",
        "wieczny": "Wieczny Mistrz Górnictwa. Przy tobie nawet stara kopalnia ma jeszcze coś do odkrycia.",
    },
    "lumberjack_bran": {
        "uczen": "Najpierw naucz się prowadzić Piłę równo. Las nie wybacza pośpiechu.",
        "adept": "Już słyszysz różnicę między młodym drewnem a porządnym pniem.",
        "specjalista": "Masz dobre tempo i oko do gatunków drewna.",
        "mistrz": "Twojej pracy nie trzeba poprawiać. Tak tnie ktoś, kto zna las.",
        "legenda": "O twoich ścinkach słyszałem, zanim dotarłeś do obozu. To już poziom legendy.",
        "wieczny": "Wieczny Mistrz Drwalstwa. Niewielu zna drewno tak dobrze jak ty.",
    },
    "herbalist_liora": {
        "uczen": "Zbieraj ostrożnie. Uczeń najwięcej traci wtedy, gdy pomyli podobne zioła.",
        "adept": "Coraz lepiej rozpoznajesz rośliny. Zaczynasz patrzeć na nie jak zielarz, nie jak przechodzień.",
        "specjalista": "Masz już wprawę w zbiorze i potrafisz znaleźć wartościowe okazy.",
        "mistrz": "Twoja wiedza o ziołach jest solidna. Mogę mówić z tobą jak z fachowcem.",
        "legenda": "Nieczęsto trafia do mnie Zielarz tej klasy. Twoja reputacja wyprzedza kroki.",
        "wieczny": "Wieczny Mistrz Zielarstwa. Przy takim doświadczeniu ogród sam staje się podręcznikiem.",
    },
    "specialist_cooking": {
        "uczen": "Na razie pilnuj temperatury i kolejności składników. Dobra kuchnia zaczyna się od podstaw.",
        "adept": "Masz już wyczucie smaku. Teraz ucz się powtarzalności.",
        "specjalista": "Twoje potrawy mają charakter. To już nie jest przypadkowe gotowanie.",
        "mistrz": "W kuchni możesz pracować obok mnie bez instrukcji na każdym kroku.",
        "legenda": "Legenda Gotowania w Błękitnym Płomieniu? Dzisiaj goście będą mieli o czym mówić.",
        "wieczny": "Wieczny Mistrz Gotowania. Nawet ja chętnie spróbuję tego, co przygotujesz.",
    },
    "specialist_alchemy": {
        "uczen": "Odmierzaj wszystko dwa razy. W Alchemii pomyłka pachnie znacznie gorzej niż w kuchni.",
        "adept": "Twoje mikstury są już stabilniejsze. To dobry znak.",
        "specjalista": "Potrafisz kontrolować reakcję zamiast tylko na nią patrzeć.",
        "mistrz": "Możemy rozmawiać o trudnych recepturach bez wracania do podstaw.",
        "legenda": "Legenda Alchemii nie pojawia się tu codziennie. Twoje eliksiry mają już własną reputację.",
        "wieczny": "Wieczny Mistrz Alchemii. Niewiele zostało rzeczy, których mógłbym cię nauczyć.",
    },
    "specialist_crafting": {
        "uczen": "Najpierw naucz się szanować materiał. Młot nie naprawi złego przygotowania.",
        "adept": "Twoje wykonanie jest coraz równiejsze. To podstawa dobrego Kowalstwa.",
        "specjalista": "Masz już rękę do trudniejszych zamówień.",
        "mistrz": "Przy twojej randze możemy mówić o rzemiośle bez tłumaczenia podstaw.",
        "legenda": "Legenda Kowalstwa w mojej Kuźni. Takie nazwisko przyciąga zamówienia samo.",
        "wieczny": "Wieczny Mistrz Kowalstwa. Twój młot ma większy autorytet niż niejeden mistrz.",
    },
    "jeweler_mirella": {
        "uczen": "Przy kamieniach liczy się cierpliwość. Jeden zły ruch potrafi zmarnować dobry materiał.",
        "adept": "Twoje dłonie są już pewniejsze. Możesz myśleć o trudniejszych oprawach.",
        "specjalista": "Masz oko do jakości i coraz lepiej dobierasz kamień do metalu.",
        "mistrz": "Twoje wyroby można już stawiać obok pracy doświadczonych jubilerów.",
        "legenda": "Legenda Jubilerstwa w mojej pracowni. Rzadkie kamienie trafiają w dobre ręce.",
        "wieczny": "Wieczny Mistrz Jubilerstwa. Przy takim kunszcie to klejnot ma zaszczyt trafić do twojej oprawy.",
    },
}

# Mistrzowie zbierackich profesji używają tego samego tonu co ich lokalni fachowcy.
PROFESSION_NPC_RANK_REACTION_ALIASES = {
    "specialist_fishing": "fisher_tomas",
    "specialist_mining": "miner_toren",
    "specialist_woodcutting": "lumberjack_bran",
    "specialist_herbalism": "herbalist_liora",
}

TOOL_MAX_LEVEL = 400
TOOL_MAX_TIER = 40
# Progi 1-200 pozostają dokładnie takie jak wcześniej. 201-400 dopisuje
# kolejne Tiery co 10 leveli bez przesuwania starych odblokowań.
TOOL_TIER_THRESHOLDS = (
    1, 10, 20, 30, 40, 50, 60, 70, 80, 90,
    100, 110, 120, 130, 140, 150, 160, 170, 180, 200,
) + tuple(range(210, 401, 10))
TOOL_TIER_BONUS_CHANCES = (
    0.00, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18,
    0.20, 0.22, 0.24, 0.26, 0.28, 0.30, 0.32, 0.34, 0.37, 0.40,
) + tuple(round(0.40 + step * 0.01, 2) for step in range(1, 21))

def tool_max_level(tool_type):
    return TOOL_MAX_LEVEL

TOOL_TIER_NAMES = {
    "fishing": (
        "Wędka Ucznia",
        "Wędka Strumienia",
        "Wędka Jeziora",
        "Wędka Rzeki",
        "Wędka Wybrzeża",
        "Wędka Głębin",
        "Wędka Srebrnej Łuski",
        "Wędka Złotej Łuski",
        "Wędka Sztormu",
        "Wędka Mistrza",
        "Wędka Runiczna",
        "Wędka Smoczej Toni",
        "Wędka Kryształowa",
        "Wędka Astralnego Prądu",
        "Wędka Otchłani",
        "Wędka Pustki",
        "Wędka Gwiezdnego Morza",
        "Wędka Wiecznych Głębin",
        "Wędka Mitycznego Lewiatana",
        "Wędka Wiecznego Oceanu",
    ),
    "mining": (
        "Kilof Ucznia",
        "Kilof Miedzi",
        "Kilof Żelaza",
        "Kilof Srebra",
        "Kilof Złota",
        "Kilof Hartowanej Skały",
        "Kilof Głębinowy",
        "Kilof Kryształowy",
        "Kilof Kobaltu",
        "Kilof Mistrza",
        "Kilof Runiczny",
        "Kilof Smoczej Stali",
        "Kilof Obsydianowy",
        "Kilof Astralny",
        "Kilof Gwiezdnego Rdzenia",
        "Kilof Pustki",
        "Kilof Otchłani",
        "Kilof Eternium",
        "Kilof Mitycznego Złoża",
        "Kilof Wiecznej Góry",
    ),
    "woodcutting": (
        "Piła Ucznia",
        "Piła Brzozowa",
        "Piła Sosnowa",
        "Piła Dębowa",
        "Piła Bukowa",
        "Piła Jesionowa",
        "Piła Cedrowa",
        "Piła Cisowa",
        "Piła Żelaznego Drewna",
        "Piła Mistrza",
        "Piła Runicznego Drewna",
        "Piła Smoczego Drewna",
        "Piła Kryształowego Pnia",
        "Piła Astralnego Drewna",
        "Piła Gwiezdnego Serca",
        "Piła Pustki",
        "Piła Pradawnego Drzewa",
        "Piła Eternium",
        "Piła Drzewa Świata",
        "Piła Wiecznego Lasu",
    ),
    "crafting": (
        "Młot Rzemieślniczy Ucznia",
        "Młot Miedzi",
        "Młot Żelaza",
        "Młot Srebra",
        "Młot Złota",
        "Młot Hartowanej Stali",
        "Młot Precyzji",
        "Młot Kryształowy",
        "Młot Kobaltu",
        "Młot Mistrza",
        "Młot Runiczny",
        "Młot Smoczej Stali",
        "Młot Obsydianowy",
        "Młot Astralny",
        "Młot Gwiezdnej Kuźni",
        "Młot Pustki",
        "Młot Otchłani",
        "Młot Eternium",
        "Młot Mitycznej Kuźni",
        "Młot Wiecznego Kowala",
    ),
    "cooking": (
        "Nóż Kucharski Ucznia",
        "Nóż Spiżarni",
        "Nóż Targowy",
        "Nóż Karczemny",
        "Nóż Srebrnego Ostrza",
        "Nóż Złotego Ostrza",
        "Nóż Precyzji",
        "Nóż Szefa Kuchni",
        "Nóż Kryształowy",
        "Nóż Mistrza",
        "Nóż Runiczny",
        "Nóż Smoczego Ognia",
        "Nóż Uczty Bohaterów",
        "Nóż Astralny",
        "Nóż Gwiezdnej Uczty",
        "Nóż Pustki",
        "Nóż Otchłani",
        "Nóż Eternium",
        "Nóż Mitycznej Uczty",
        "Nóż Wiecznego Kucharza",
    ),
    "herbalism": (
        "Sierp Zielarski Ucznia",
        "Sierp Łąki",
        "Sierp Ziół Polnych",
        "Sierp Leśny",
        "Sierp Księżycowych Ziół",
        "Sierp Głębokiego Gaju",
        "Sierp Rzadkich Ziół",
        "Sierp Mistrzowskiego Zbioru",
        "Sierp Kryształowy",
        "Sierp Mistrza",
        "Sierp Runiczny",
        "Sierp Smoczych Ziół",
        "Sierp Słonecznego Kwiatu",
        "Sierp Astralny",
        "Sierp Gwiezdnego Mchu",
        "Sierp Pustki",
        "Sierp Otchłani",
        "Sierp Eternium",
        "Sierp Mitycznego Ogrodu",
        "Sierp Wiecznego Zielarza",
    ),
    "alchemy": (
        "Moździerz Ucznia",
        "Moździerz Kamienny",
        "Moździerz Żelazny",
        "Moździerz Srebrny",
        "Moździerz Złoty",
        "Moździerz Precyzji",
        "Moździerz Zielonego Szkła",
        "Moździerz Kryształowy",
        "Moździerz Kobaltu",
        "Moździerz Mistrza",
        "Moździerz Runiczny",
        "Moździerz Smoczej Esencji",
        "Moździerz Słonecznej Esencji",
        "Moździerz Astralny",
        "Moździerz Gwiezdnej Esencji",
        "Moździerz Pustki",
        "Moździerz Otchłani",
        "Moździerz Eternium",
        "Moździerz Mitycznej Esencji",
        "Moździerz Wiecznego Alchemika",
    ),
    "jewelcrafting": (
        "Szczypce Jubilerskie Ucznia",
        "Szczypce Miedzianego Drutu",
        "Szczypce Srebrnego Drutu",
        "Szczypce Złotego Splotu",
        "Szczypce Precyzyjnego Szlifu",
        "Szczypce Kryształowej Oprawy",
        "Szczypce Szmaragdowej Oprawy",
        "Szczypce Diamentowej Oprawy",
        "Szczypce Kobaltowej Oprawy",
        "Szczypce Mistrza Jubilerstwa",
        "Szczypce Runicznej Oprawy",
        "Szczypce Smoczej Stali",
        "Szczypce Słonecznego Klejnotu",
        "Szczypce Astralnego Splotu",
        "Szczypce Gwiezdnej Oprawy",
        "Szczypce Pustki",
        "Szczypce Otchłani",
        "Szczypce Eternium",
        "Szczypce Mitycznego Klejnotu",
        "Szczypce Wiecznego Klejnotu",
    ),
}

# v0.30.33: Tiery 21-40 mają pełne, unikalne nazwy zamiast powtarzania
# nazwy Tieru 20 z dopiskiem +210/+220 itd. Progi i mechanika pozostają bez zmian.
V03033_TOOL_TIER_NAMES_21_40 = {
    "fishing": (
        "Wędka Przebudzonej Rafy",
        "Wędka Transcendentnego Strumienia",
        "Wędka Horyzontu",
        "Wędka Niebiańskiego Prądu",
        "Wędka Pierwotnego Morza",
        "Wędka Echa Lewiatana",
        "Wędka Korony Fal",
        "Wędka Serca Oceanu",
        "Wędka Nieskończonego Sztormu",
        "Wędka Pradawnej Toni",
        "Wędka Zorzy Głębin",
        "Wędka Smoczego Prądu",
        "Wędka Tajemnicy Rafy",
        "Wędka Gwiezdnej Otchłani",
        "Wędka Wiecznego Horyzontu",
        "Wędka Korony Lewiatana",
        "Wędka Przeznaczenia Mórz",
        "Wędka Ponadczasowej Fali",
        "Wędka Końca Głębin",
        "Wędka Absolutnych Głębin",
    ),
    "mining": (
        "Kilof Przebudzonego Kamienia",
        "Kilof Transcendentnej Rudy",
        "Kilof Horyzontu Skał",
        "Kilof Niebiańskiego Kryształu",
        "Kilof Pierwotnej Góry",
        "Kilof Echa Głębin",
        "Kilof Korony Minerałów",
        "Kilof Serca Ziemi",
        "Kilof Nieskończonego Złoża",
        "Kilof Pradawnego Granitu",
        "Kilof Zorzy Kryształów",
        "Kilof Smoczej Skały",
        "Kilof Tajemnicy Podziemi",
        "Kilof Gwiezdnej Żyły",
        "Kilof Wiecznego Masywu",
        "Kilof Korony Gór",
        "Kilof Przeznaczenia Rudy",
        "Kilof Ponadczasowej Skały",
        "Kilof Końca Złoża",
        "Kilof Absolutnej Góry",
    ),
    "woodcutting": (
        "Piła Przebudzonego Gaju",
        "Piła Transcendentnego Pnia",
        "Piła Horyzontu Koron",
        "Piła Niebiańskiej Kory",
        "Piła Pierwotnego Lasu",
        "Piła Echa Drzew",
        "Piła Korony Konarów",
        "Piła Serca Puszczy",
        "Piła Nieskończonego Boru",
        "Piła Pradawnego Dębu",
        "Piła Zorzy Liści",
        "Piła Smoczego Pnia",
        "Piła Tajemnicy Kniei",
        "Piła Gwiezdnej Kory",
        "Piła Wiecznej Puszczy",
        "Piła Korony Drzewa Świata",
        "Piła Przeznaczenia Lasu",
        "Piła Ponadczasowego Drewna",
        "Piła Końca Boru",
        "Piła Absolutnego Drzewa",
    ),
    "crafting": (
        "Młot Przebudzonej Kuźni",
        "Młot Transcendentnego Kowala",
        "Młot Horyzontu Metalu",
        "Młot Niebiańskiej Stali",
        "Młot Pierwotnego Ognia",
        "Młot Echa Kowadła",
        "Młot Korony Kuźni",
        "Młot Serca Metalu",
        "Młot Nieskończonego Żaru",
        "Młot Pradawnego Kowadła",
        "Młot Zorzy Stali",
        "Młot Smoczego Żaru",
        "Młot Tajemnicy Metalu",
        "Młot Gwiezdnego Kowadła",
        "Młot Wiecznej Kuźni",
        "Młot Korony Kowali",
        "Młot Przeznaczenia Stali",
        "Młot Ponadczasowego Metalu",
        "Młot Końca Kuźni",
        "Młot Absolutnego Kowala",
    ),
    "cooking": (
        "Nóż Przebudzonej Kuchni",
        "Nóż Transcendentnego Smaku",
        "Nóż Horyzontu Uczty",
        "Nóż Niebiańskiej Potrawy",
        "Nóż Pierwotnego Paleniska",
        "Nóż Echa Przypraw",
        "Nóż Korony Szefów",
        "Nóż Serca Uczty",
        "Nóż Nieskończonego Smaku",
        "Nóż Pradawnej Receptury",
        "Nóż Zorzy Aromatów",
        "Nóż Smoczego Paleniska",
        "Nóż Tajemnicy Kuchni",
        "Nóż Gwiezdnej Receptury",
        "Nóż Wiecznej Uczty",
        "Nóż Korony Kucharzy",
        "Nóż Przeznaczenia Smaku",
        "Nóż Ponadczasowej Potrawy",
        "Nóż Końca Uczty",
        "Nóż Absolutnego Kucharza",
    ),
    "herbalism": (
        "Sierp Przebudzonej Łąki",
        "Sierp Transcendentnych Ziół",
        "Sierp Horyzontu Kwiatów",
        "Sierp Niebiańskiego Ogrodu",
        "Sierp Pierwotnego Gaju",
        "Sierp Echa Natury",
        "Sierp Korony Zielarzy",
        "Sierp Serca Ogrodu",
        "Sierp Nieskończonej Łąki",
        "Sierp Pradawnego Zielnika",
        "Sierp Zorzy Kwiatów",
        "Sierp Smoczych Korzeni",
        "Sierp Tajemnicy Natury",
        "Sierp Gwiezdnego Zielnika",
        "Sierp Wiecznego Ogrodu",
        "Sierp Korony Kwiatów",
        "Sierp Przeznaczenia Ziół",
        "Sierp Ponadczasowego Gaju",
        "Sierp Końca Łąki",
        "Sierp Absolutnego Zielarza",
    ),
    "alchemy": (
        "Moździerz Przebudzonej Esencji",
        "Moździerz Transcendentnego Eliksiru",
        "Moździerz Horyzontu Mikstur",
        "Moździerz Niebiańskiej Esencji",
        "Moździerz Pierwotnej Substancji",
        "Moździerz Echa Alchemii",
        "Moździerz Korony Alchemików",
        "Moździerz Serca Eliksiru",
        "Moździerz Nieskończonej Mikstury",
        "Moździerz Pradawnej Formuły",
        "Moździerz Zorzy Esencji",
        "Moździerz Smoczego Eliksiru",
        "Moździerz Tajemnicy Alchemii",
        "Moździerz Gwiezdnej Formuły",
        "Moździerz Wiecznej Esencji",
        "Moździerz Korony Mikstur",
        "Moździerz Przeznaczenia Eliksiru",
        "Moździerz Ponadczasowej Substancji",
        "Moździerz Końca Formuły",
        "Moździerz Absolutnego Alchemika",
    ),
    "jewelcrafting": (
        "Szczypce Przebudzonego Klejnotu",
        "Szczypce Transcendentnej Oprawy",
        "Szczypce Horyzontu Kryształów",
        "Szczypce Niebiańskiego Szlifu",
        "Szczypce Pierwotnego Kamienia",
        "Szczypce Echa Klejnotów",
        "Szczypce Korony Jubilerów",
        "Szczypce Serca Kryształu",
        "Szczypce Nieskończonej Oprawy",
        "Szczypce Pradawnego Szlifu",
        "Szczypce Zorzy Klejnotów",
        "Szczypce Smoczego Kryształu",
        "Szczypce Tajemnicy Oprawy",
        "Szczypce Gwiezdnego Kamienia",
        "Szczypce Wiecznej Korony",
        "Szczypce Korony Kryształów",
        "Szczypce Przeznaczenia Szlifu",
        "Szczypce Ponadczasowej Oprawy",
        "Szczypce Końca Klejnotu",
        "Szczypce Absolutnego Jubilera",
    ),
}
for _tool_type, _names in list(TOOL_TIER_NAMES.items()):
    _base_names = tuple(_names)
    TOOL_TIER_NAMES[_tool_type] = _base_names + V03033_TOOL_TIER_NAMES_21_40[_tool_type]

def tool_tier(level):
    level = max(1, min(TOOL_MAX_LEVEL, int(level)))
    tier = 1
    for number, minimum in enumerate(TOOL_TIER_THRESHOLDS, 1):
        if level >= minimum:
            tier = number
        else:
            break
    return tier

def tool_tier_access_level(level):
    """Najwyższy próg zasobów/receptur odblokowany przez aktualny Tier narzędzia.

    Dostęp do nowej zawartości zmienia się wyłącznie przy awansie Tieru,
    a nie przy każdym pojedynczym levelu narzędzia.
    """
    tier = tool_tier(level)
    return int(TOOL_TIER_THRESHOLDS[tier - 1])


def required_tool_tier_for_level(required_level):
    return tool_tier(max(1, int(required_level or 1)))

def tool_tier_name(tool_type, level):
    tier = tool_tier(level)
    names = TOOL_TIER_NAMES.get(tool_type, TOOL_TIER_NAMES["mining"])
    return names[tier - 1]

def tool_tier_bonus_chance(level):
    return TOOL_TIER_BONUS_CHANCES[tool_tier(level) - 1]

# ============================================================
# v0.19.0 - GLOBAL PROGRESSION & REWARD GENERATOR
# Duże nagrody pozostają duże. Tempo gry kontrolują rosnące wymagania.
# Wszystkie krzywe używają wspólnej interpolacji logarytmicznej z mocnymi
# kamieniami milowymi co około 10-50 poziomów. Początek pozostaje szybki,
# endgame może operować milionami, miliardami i bilionami.
# ============================================================
V019_SAFE_INT = 8_000_000_000_000_000_000
