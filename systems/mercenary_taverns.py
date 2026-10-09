# -*- coding: utf-8 -*-
"""Tavern mercenaries independent of UOSS summon/helper selection."""
import time
from core.large_number_math import decimal_value, rounded_product

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
    if any(str(spec["room"]) == str(room_id) for spec in V0560_TAVERNS.values()):
        return True
    # v1.28.12: actual underground-city inns accept regular mercenary
    # recruitment, without duplicating the historical hourly NPC catalogs.
    from data.catalogs import ROOMS
    room = ROOMS.get(str(room_id), {})
    return bool((room.get('v12812_underground_city') or room.get('v1300_region') or room.get('v1310_campaign')) and str(room_id).endswith('_tavern'))


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


def mercenary_damage_cap_ratio_v12212(template):
    """Compatibility API: v1.22.13 removed the enemy-HP percentage cap."""
    return 1.0


def mercenary_owner_full_power_v12213(physical_power, magic_power,
                                     physical_equipment_multiplier=1.0,
                                     magic_equipment_multiplier=1.0,
                                     set_damage_multiplier=1.0):
    """100% of the stronger offensive channel, including all equipped EQ bonuses.

    physical_power/spell_power already include effective STR/INT plus flat Attack,
    Magic Attack and Weapon Power from worn gear and upgrades. Apply the proper
    damage-% bonuses, runes and set multiplier once, BEFORE choosing the strongest
    channel, so cross-class hires are not penalised or double-count the equipment.
    The mercenary still chooses its own physical/magical attack type.
    """
    physical = rounded_product(max(1, int(physical_power)),
                               max(0, decimal_value(physical_equipment_multiplier)))
    magical = rounded_product(max(1, int(magic_power)),
                              max(0, decimal_value(magic_equipment_multiplier)))
    return max(1, rounded_product(max(physical, magical),
                                  max(0, decimal_value(set_damage_multiplier))))


def mercenary_owner_real_action_power_v1231(owner, legacy_power, cadence=COOLDOWN):
    """Owner's actual *combat throughput* during one mercenary cadence.

    The old "100% power" promise only copied physical_power/spell_power. A real
    Soulbound hit also has Soul Weapon, the uncapped effective-stat build curve,
    racial/class/EQ/set bonuses and critical hits. One owner action can contain
    multiple Speed/Haste hits, and actions occur more frequently than a hire's
    five-second turn. Use the game's existing non-mutating expected-hit method to
    avoid estimating those modifiers a second, incompatible way.

    Legacy base is deliberately a FLOOR: magical and physical hires both inherit
    the strongest complete offensive channel regardless of owner's build.
    Nothing here changes owner's HP, mana, cooldowns, skills or saved contracts.
    """
    baseline = max(1, int(legacy_power))
    estimator = getattr(owner, "consider_player_expected_hit", None)
    if not callable(estimator):
        return baseline
    try:
        hit = max(1, decimal_value(estimator()))
        # Player expected hit includes Soul Power, effective-stat build growth,
        # class/race, EQ, set, party synergies and expected ordinary criticals.
        # Soul Weapon mastery + traits modify the real hit AFTER player_damage.
        from core.progression_600 import soul_weapon_trait_totals_v11193
        from core.progression_resources import soul_weapon_mastery_bonuses
        character = owner.character
        mastery = soul_weapon_mastery_bonuses(
            int(getattr(character, "soul_weapon_mastery_level", 1) or 1)
        )
        traits = soul_weapon_trait_totals_v11193(
            int(getattr(character, "soul_tier", 1) or 1),
            str(getattr(character, "class_name", "") or ""),
        )
        mastery_multiplier = 1 + decimal_value(mastery.get("damage_percent", 0)) / 100
        trait_multiplier = 1 + decimal_value(traits.get("damage_percent", 0)) / 100
        # Every owner series has Speed/Haste hits. Every hired ally deals the
        # equivalent in its OWN five-second turn: no shared companion cooldown,
        # no speed ceiling, no invented fixed damage amount.
        count_fn = getattr(owner, "basic_attack_hit_count_v11196", None)
        hits = max(1, int(count_fn())) if callable(count_fn) else 1
        interval_fn = getattr(owner, "player_action_interval_v11154", None)
        interval = float(interval_fn()) if callable(interval_fn) else float(cadence)
        interval = max(0.05, interval)
        owner_actions = max(1, decimal_value(cadence) / decimal_value(interval))
        return max(1, rounded_product(max(decimal_value(baseline), hit),
                                      mastery_multiplier, trait_multiplier, hits,
                                      owner_actions))
    except (AttributeError, TypeError, ValueError, OverflowError, KeyError):
        # Synthetic legacy test sessions / older character state retain the
        # proven old full-equipment damage; never drop combat on a missing field.
        return baseline


def mercenary_follow_notice_v12210(names):
    """One compact NVDA line; a follower belongs to the owner, not party slots."""
    names = tuple(str(name).strip() for name in names if str(name).strip())
    if not names:
        return ""
    if len(names) == 1:
        return f"{names[0]} podąża za tobą."
    return "Najemnicy podążają za tobą: " + ", ".join(names[:-1]) + " i " + names[-1] + "."


# v1.22.11: documentation of REAL combat actions; no skill control interface.
_MERCENARY_HEAL_V12211 = {
    "kaplan": (70, 18), "druid": (60, 13), "paladyn": (70, 11),
}
_MERCENARY_GUARD_V12211 = {
    "wojownik": 9, "paladyn": 6, "straznik": 13,
    "psionik": 8, "inzynier": 10,
}


def mercenary_skill_lines_v12211(role):
    """Readable, non-interactive description of the actual combat implementation."""
    spec = MERCENARIES[role]
    attack = "magiczny" if spec["attack_type"] == "magic" else "fizyczny"
    lines = [
        f"{spec['name']} ({spec['role']}): umiejętności wykonywane AUTOMATYCZNIE.",
        f"1. {spec['ability']}: atak {attack} na przeciwnika. Moc zależy od "
        "pełnej silniejszej mocy właściciela (fizycznej lub magicznej) i jego EQ. "
        "Najemnik sam dobiera umiejętności. Atak odpowiada pełnemu tempu ofensywnemu właściciela z Bronią Duszy, rozwojem statystyk, trafieniami Speed/Haste, premiami EQ i zestawów; bez limitu procentowego HP przeciwnika.",
    ]
    if role in _MERCENARY_HEAL_V12211:
        threshold, percent = _MERCENARY_HEAL_V12211[role]
        lines.append(
            f"2. Leczenie drużyny: gdy HP najsłabszego sojusznika spadnie poniżej "
            f"{threshold}%, najemnik może przywrócić do {percent}% jego maksymalnego HP. "
            "Blokada leczenia przeciwnika może uniemożliwić efekt."
        )
    if role in _MERCENARY_GUARD_V12211:
        lines.append(
            f"{3 if role in _MERCENARY_HEAL_V12211 else 2}. Osłona drużyny: "
            f"ochrona do {_MERCENARY_GUARD_V12211[role]}% maksymalnego HP "
            "wybranego sojusznika, jeśli nie ma już osłony."
        )
    from systems.mercenary_specialists_v1240 import specialist_description_v1240
    lines.append("Specjalizacja 4.0: " + specialist_description_v1240(role))
    lines.append("Najemnik sam wybiera atak, leczenie lub osłonę w walce; gracz nie wydaje poleceń użycia skilli. Każdy z wynajętych najemników działa osobno, a bonus za poziom właściciela nie ma górnego limitu. Wspólna walka najemników fizycznych i magicznych daje im premię współpracy. Leczący i obrońcy reagują na stan HP i zagrożenie od bossa.")
    return lines
