# -*- coding: utf-8 -*-
"""Tavern mercenaries independent of UOSS summon/helper selection."""
import time

# Prices in gold, 100 silver per gold. Roles remain distinct by design.
# Each player class has one hireable mercenary; Paladin stays as a bonus role.
# The historical key `lucznik` is retained for existing contracts in SQLite.
MERCENARIES = {
    "wojownik":   {"name": "Gareth", "role": "Wojownik",   "class": "Wojownik",   "cost": 100, "power": 1.00, "attack_type": "physical", "ability": "Ciężkie Cięcie"},
    "berserker":  {"name": "Kord",   "role": "Berserker",  "class": "Berserker",  "cost": 200, "power": 1.26, "attack_type": "physical", "ability": "Szał Topora"},
    "lotrzyk":    {"name": "Neria",  "role": "Łotrzyk",    "class": "Łotrzyk",    "cost": 145, "power": 1.14, "attack_type": "physical", "ability": "Cios z Ukrycia"},
    "lucznik":    {"name": "Riven",  "role": "Łowca",      "class": "Łowca",      "cost": 130, "power": 1.05, "attack_type": "physical", "ability": "Celny Strzał"},
    "mnich":      {"name": "Taren",  "role": "Mnich",      "class": "Mnich",      "cost": 155, "power": 1.08, "attack_type": "physical", "ability": "Uderzenie Dłoni"},
    "straznik":   {"name": "Branik", "role": "Strażnik",   "class": "Strażnik",   "cost": 165, "power": 0.84, "attack_type": "physical", "ability": "Uderzenie Tarczy"},
    "mag":        {"name": "Vael",   "role": "Mag",        "class": "Mag",        "cost": 180, "power": 1.15, "attack_type": "magic",    "ability": "Ognista Kula"},
    "nekromanta": {"name": "Morran", "role": "Nekromanta", "class": "Nekromanta", "cost": 240, "power": 1.25, "attack_type": "magic",    "ability": "Rozdarcie Cienia"},
    "kaplan":     {"name": "Elira",  "role": "Kapłanka",   "class": "Kapłan",     "cost": 160, "power": 0.65, "attack_type": "magic",    "ability": "Święty Promień"},
    "czarownik":  {"name": "Lirae",  "role": "Czarownik",  "class": "Czarownik",  "cost": 215, "power": 1.20, "attack_type": "magic",    "ability": "Klątwa Otchłani"},
    "druid":      {"name": "Elandra","role": "Druidka",    "class": "Druid",      "cost": 180, "power": 0.88, "attack_type": "magic",    "ability": "Gniew Korzeni"},
    "psionik":    {"name": "Theon",  "role": "Psionik",    "class": "Psionik",    "cost": 205, "power": 1.04, "attack_type": "magic",    "ability": "Impuls Umysłu"},
    "mec":        {"name": "Vex",    "role": "Mec",        "class": "Mec",        "cost": 245, "power": 1.16, "attack_type": "physical", "ability": "Strzał Rdzenia"},
    "inzynier":   {"name": "Odrik",  "role": "Inżynier",   "class": "Inżynier",   "cost": 190, "power": 0.93, "attack_type": "physical", "ability": "Impuls Omni-Narzędzia"},
    "paladyn":    {"name": "Seren",  "role": "Paladyn",    "class": None,        "cost": 220, "power": 0.80, "attack_type": "physical", "ability": "Święty Cios"},
}

# v1.21.2: contracts are permanent (0 is also the persisted sentinel).
# Keep DURATION for any legacy imports; it no longer limits the contract.
DURATION = 0
COOLDOWN = 5.0


def mercenary_role(raw):
    from storage.db_shared import normalize_lookup_text
    key = normalize_lookup_text(raw)
    aliases = {"kaplanka":"kaplan", "druidka":"druid", "lowca":"lucznik", "lucznik":"lucznik", "luczniczka":"lucznik"}
    key = aliases.get(key, key)
    for role, spec in MERCENARIES.items():
        names = (role, spec["name"], spec["role"])
        if spec["class"]:
            names += (spec["class"],)
        if key in {normalize_lookup_text(value) for value in names}:
            return role
    return None


def tavern_here(room_id):
    from world.living_npcs import V0560_TAVERNS
    return any(str(spec["room"]) == str(room_id) for spec in V0560_TAVERNS.values())


def price_silver(character, role):
    spec = MERCENARIES[role]
    discount = max(0, min(75, int(character.shop_discount_percent())))
    return max(1, spec["cost"]*100*(100-discount)//100)


def pick_next_contract(contracts, last_role, time_now):
    roles = [row["role"] for row in contracts
             if row["role"] in MERCENARIES and
             (float(row["expires_at"]) <= 0 or float(row["expires_at"]) > time_now)]
    if not roles:
        return None
    if last_role in roles:
        return roles[(roles.index(last_role)+1)%len(roles)]
    return roles[0]


def mercenary_owner_power_v1213(physical_power, magic_power):
    """One owner power budget for every hired class, including cross-class hires.

    Inputs must be the owner's *effective* offensive powers, including equipment.
    The mercenary's class still determines damage type and role multiplier.
    Using the stronger channel avoids punishing a physical owner for hiring a
    mage (or a magic owner for hiring a warrior), and does not double-dip EQ.
    """
    return max(1, int(physical_power), int(magic_power))
