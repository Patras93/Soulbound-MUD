# -*- coding: utf-8 -*-
"""Persistent class summons, soul upgrades, sky discovery and personal PvE cities."""
from __future__ import annotations
import time
import random
import unicodedata
from data.mobs import MOB_TEMPLATES

SUMMONS={
 'pajak':('Szkielet Pająka','Nekromanta',{'v1700_common_tooth':2},'physical',.40),
 'wojownik':('Szkielet Wojownika','Nekromanta',{'v1700_dragon_tooth':1},'physical',.67),
 'mag':('Szkielet Maga','Nekromanta',{'v1700_dragon_tooth':2},'magic',.72),
 'lifeoak':('Life Oak','Druid',{'v1702_pinecone':2},'magic',.52),
 'ancientoak':('Ancient Oak','Druid',{'v1702_pinecone':5},'magic',.85),
 'wilk':('Wilk Runiczny','Druid',{},'physical',.44),
 'sowa':('Sowa Gwiezdna','Druid',{},'magic',.46),
 'niedzwiedz':('Niedźwiedź Runiczny','Druid',{},'physical',.66),
}


# Tiers are inspired by Alter Aeon's colored soulstones, but Soulbound
# calculates its own rarity, mana expenditure and combat scaling.
# The original uncolored v1.70.0 stone is the red tier: NO DATA LOSS.
from systems.soulstones_v1701 import SOULSTONE_TIERS, STONE_ALIASES, STONE_BY_KEY
from systems.mage_elementals_v1702 import ELEMENTALS, ELEMENTS, RANKS, resolve_elemental
from systems.druid_call_v1708 import ANIMALS, terrain_animals, biome_for_room, normalize_animal
from systems.necro_constructs_v1710 import NECRO_MINIONS, summon_key
from systems.class_minions_v1119 import CLASS_MINIONS_V1119, CLASS_MINIONS_BY_CLASS_V1119
SUMMONS.update({key:(spec['name'],'Mag',{},'magic',spec['damage']) for key,spec in ELEMENTALS.items()})
SUMMONS.update({key:(spec['name'],'Druid',{},spec['damage_kind'],spec['damage']) for key,spec in ANIMALS.items() if key not in SUMMONS})
SUMMONS.update({key:(spec[0],'Nekromanta',spec[3],spec[4],spec[5]) for key,spec in NECRO_MINIONS.items()})
SUMMONS.update({key:(row[1],row[2],{},row[5],row[6]) for key,row in CLASS_MINIONS_V1119.items()})
SUMMON_MANA = {'pajak':45,'wojownik':90,'mag':120,'lifeoak':80,
               'ancientoak':180,'wilk':50,'sowa':55,'niedzwiedz':110}
SUMMON_MANA.update({key: spec['mana'] for key,spec in ELEMENTALS.items()})
SUMMON_MANA.update({key: spec['mana'] for key,spec in ANIMALS.items()})
SUMMON_MANA.update({key: spec[2] for key,spec in NECRO_MINIONS.items()})
SUMMON_MANA.update({key: row[4] for key,row in CLASS_MINIONS_V1119.items()})
# Druids unlock living oaks much later than ordinary woodland calls.
DRUID_OAK_MIN_LEVEL={'lifeoak':150, 'ancientoak':400}


def stone_for_enemy(enemy_level, is_boss=False, roll=None):
    """Only sufficiently mighty enemies may yield rarer colors."""
    level = max(1, int(enemy_level))
    ceiling = max(i for i, tier in enumerate(SOULSTONE_TIERS) if level >= tier[4])
    r = random.random() if roll is None else max(0.0, min(0.999999, float(roll)))
    drop = 0 if r < 0.15 else (1 if r < 0.48 else (2 if r < 0.78 else 3))
    return SOULSTONE_TIERS[max(0, ceiling - max(0, drop - int(bool(is_boss))))]


def summon_display(kind, grade):
    grade = max(0, min(8, int(grade)))
    if grade >= 4 and kind == 'wojownik': return 'Rycerz Szkieletów'
    if grade >= 4 and kind == 'mag': return 'Szkielet Licz'
    return SUMMONS[kind][0]


def ascii_fold(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(text).casefold()) if not unicodedata.combining(c)).replace('ł','l').strip()


def ensure_schema(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS summons_v1700 (
      account_id INTEGER NOT NULL, summon_type TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 1,
      active INTEGER NOT NULL DEFAULT 1, soul_rank INTEGER NOT NULL DEFAULT 0,
      hp INTEGER NOT NULL DEFAULT 0, max_hp INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY(account_id,summon_type))''')
    conn.execute('''CREATE TABLE IF NOT EXISTS summon_ai_prefs_v1200 (
      account_id INTEGER PRIMARY KEY, enabled INTEGER NOT NULL DEFAULT 1)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS cities_v1700 (
      account_id INTEGER PRIMARY KEY, title TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 1,
      walls INTEGER NOT NULL DEFAULT 0, market INTEGER NOT NULL DEFAULT 0,
      workshop INTEGER NOT NULL DEFAULT 0, infirmary INTEGER NOT NULL DEFAULT 0,
      market_claim INTEGER NOT NULL DEFAULT 0)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS druid_pinecones_v1702 (
      account_id INTEGER PRIMARY KEY, last_gather INTEGER NOT NULL DEFAULT 0)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS class_paths_v1700 (
      account_id INTEGER NOT NULL, class_name TEXT NOT NULL, path TEXT NOT NULL,
      PRIMARY KEY(account_id,class_name))''')
    # Durable migration for databases created during preview/testing.
    city_cols={r[1] for r in conn.execute('PRAGMA table_info(cities_v1700)')}
    summon_cols={r[1] for r in conn.execute('PRAGMA table_info(summons_v1700)')}
    if 'soul_rank' not in summon_cols:
        conn.execute('ALTER TABLE summons_v1700 ADD COLUMN soul_rank INTEGER NOT NULL DEFAULT 0')
    if 'hp' not in summon_cols:
        conn.execute('ALTER TABLE summons_v1700 ADD COLUMN hp INTEGER NOT NULL DEFAULT 0')
    if 'max_hp' not in summon_cols:
        conn.execute('ALTER TABLE summons_v1700 ADD COLUMN max_hp INTEGER NOT NULL DEFAULT 0')
    if 'xp' not in summon_cols:
        conn.execute('ALTER TABLE summons_v1700 ADD COLUMN xp INTEGER NOT NULL DEFAULT 0')
    if 'stance' not in summon_cols:
        conn.execute("ALTER TABLE summons_v1700 ADD COLUMN stance TEXT NOT NULL DEFAULT 'atakuj'")
    if 'market_claim' not in city_cols:
        conn.execute('ALTER TABLE cities_v1700 ADD COLUMN market_claim INTEGER NOT NULL DEFAULT 0')
    conn.commit()


def summon_upgrade_stones(level):
    return max(1,1+(max(1,int(level))-1)//3)


from player.session_mixins.chaos_v1800 import SessionChaosV1800Mixin
from systems.era_chaos_v1800 import ELEMENT_ALIASES
from systems.summon_status_v1808 import apply_summon_status_v1808
from systems.elemental_damage_v2008 import effective_elemental_strike_v2008

from core.performance_v2002 import measure_async


# Jawny eksport wspólnych globali, w tym pomocniczych nazw z podkreślnikiem.
__all__ = tuple(k for k in globals() if not k.startswith("__"))
