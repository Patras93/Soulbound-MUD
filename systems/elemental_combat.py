# -*- coding: utf-8 -*-
"""Elemental combat helpers for Soulbound v1.13.39.

This extends existing physical/magic combat instead of replacing it. Elemental
enemy attacks use the normal magic-defense path and existing equipment
element_wards. Player elemental skills keep using the mature Machine weakness
resolver; this module adds consistent affinity, preview and chase-gear hooks.
"""

V11339_ELEMENTAL_COMBAT_VERSION = "1.13.39"

V11339_ELEMENT_LABELS = {
    "fire": "Fire",
    "ice": "Ice",
    "lightning": "Electric",
    "dark": "Dark",
    "poison": "Poison",
    "holy": "Holy",
    "water": "Water",
    "arcane": "Arcane",
}

V11339_ELEMENT_ATTACKS = {
    "fire": {
        "chance": 0.24,
        "damage_multiplier": 1.15,
        "text": "FIRE — płomienny atak przecina zwykłą obronę fizyczną.",
    },
    "ice": {
        "chance": 0.24,
        "damage_multiplier": 1.08,
        "text": "ICE — lodowy atak uderza magicznym chłodem.",
    },
    "lightning": {
        "chance": 0.24,
        "damage_multiplier": 1.12,
        "text": "ELECTRIC — wyładowanie elektryczne przeskakuje przez cel.",
    },
    "dark": {
        "chance": 0.24,
        "damage_multiplier": 1.14,
        "text": "DARK — fala mroku uderza w duszę celu.",
    },
    "poison": {
        "chance": 0.22,
        "damage_multiplier": 1.08,
        "text": "POISON — toksyczny atak przenika zwykłą ochronę.",
    },
    "holy": {
        "chance": 0.22,
        "damage_multiplier": 1.10,
        "text": "HOLY — świetlisty impuls uderza energią duchową.",
    },
    "water": {
        "chance": 0.22,
        "damage_multiplier": 1.08,
        "text": "WATER — skondensowana fala many uderza z pełną siłą.",
    },
    "arcane": {
        "chance": 0.22,
        "damage_multiplier": 1.12,
        "text": "ARCANE — czysta energia magiczna eksploduje przy trafieniu.",
    },
}

V11339_PROTECTED_ELEMENTAL_BOSS_FLAGS = (
    "uoss_superboss",
    "uoss_unique_superboss_key",
    "boss_mechanic",
    "v018_legendary_event_boss",
    "v020_mythic_world_boss",
)


def canonical_element_v11339(value):
    text = str(value or "").strip().casefold()
    aliases = {
        "electric": "lightning",
        "electricity": "lightning",
        "shock": "lightning",
        "thunder": "lightning",
        "lightning": "lightning",
        "fire": "fire",
        "flame": "fire",
        "ice": "ice",
        "frost": "ice",
        "dark": "dark",
        "shadow": "dark",
        "void": "dark",
        "poison": "poison",
        "bio": "poison",
        "biological": "poison",
        "holy": "holy",
        "light": "holy",
        "water": "water",
        "aqua": "water",
        "arcane": "arcane",
        "magic": "arcane",
    }
    return aliases.get(text, text if text in V11339_ELEMENT_ATTACKS else "")


def mob_element_affinities_v11339(template):
    template = template or {}
    explicit = template.get("attack_elements_v11339")
    if explicit:
        if isinstance(explicit, str):
            explicit = (explicit,)
        result = []
        for raw in explicit:
            element = canonical_element_v11339(raw)
            if element and element not in result:
                result.append(element)
        if result:
            return tuple(result)

    name = str(template.get("name") or "").casefold()
    creature = str(template.get("creature_type") or "").casefold()
    tokens = (
        ("lightning", ("piorun", "burz", "grom", "shock", "arc cannon", "electric", "tesla")),
        ("fire", ("ogień", "ogien", "płom", "plom", "inferno", "vulcan", "wulkan", "smok", "dragon", "ash")),
        ("ice", ("lód", "lod", "mróz", "mroz", "szron", "frost", "ice", "frozen")),
        ("dark", ("mrok", "cień", "cien", "shadow", "void", "pustk", "wraith", "nekro", "undead")),
        ("poison", ("truc", "jad", "poison", "venom", "bio", "bagno", "swamp", "zaraz")),
        ("holy", ("świat", "swiat", "świet", "swiet", "holy", "angel", "seraph", "sacred")),
        ("water", ("wod", "ocean", "tide", "fala", "morsk", "aqua")),
    )
    found = []
    if template.get("machine") and any(
        token in name for token in ("shock", "arc", "power", "reactor")
    ):
        found.append("lightning")
    for element, words in tokens:
        if any(word in name or word in creature for word in words):
            if element not in found:
                found.append(element)
    if not found and str(template.get("damage_type") or "").casefold() == "magic":
        found.append("arcane")
    return tuple(found[:2])


def elemental_attack_eligible_v11339(template):
    if not isinstance(template, dict) or not template:
        return False
    if template.get("training_dummy"):
        return False
    if any(template.get(flag) for flag in V11339_PROTECTED_ELEMENTAL_BOSS_FLAGS):
        return False
    return bool(mob_element_affinities_v11339(template))


def elemental_mob_attack_profile_v11339(template, roll, combat_turn=0):
    if not elemental_attack_eligible_v11339(template):
        return None
    elements = mob_element_affinities_v11339(template)
    if not elements:
        return None
    turn = max(0, int(combat_turn or 0))
    # Deterministic rotation for dual-affinity mobs; the chance roll remains random.
    element = elements[turn % len(elements)] if turn else elements[0]
    spec = V11339_ELEMENT_ATTACKS[element]
    chance = float(spec["chance"])
    if template.get("elite_affix"):
        chance = min(0.40, chance + 0.06)
    if float(roll) >= chance:
        return None
    return {
        "element": element,
        "label": V11339_ELEMENT_LABELS[element],
        "chance": chance,
        "damage_multiplier": float(spec["damage_multiplier"]),
        "text": str(spec["text"]),
        "defense_channel": "magic",
    }


def elemental_expected_incoming_multiplier_v11339(template):
    if not elemental_attack_eligible_v11339(template):
        return 1.0
    elements = mob_element_affinities_v11339(template)
    if not elements:
        return 1.0
    values = []
    for element in elements:
        spec = V11339_ELEMENT_ATTACKS[element]
        chance = float(spec["chance"])
        if template.get("elite_affix"):
            chance = min(0.40, chance + 0.06)
        values.append(1.0 + chance * (float(spec["damage_multiplier"]) - 1.0))
    return sum(values) / float(len(values))


def elemental_target_ward_multiplier_v11339(session, element):
    element = canonical_element_v11339(element)
    if not element or not session:
        return 1.0
    ward_getter = getattr(session, "equipment_element_ward_v11176", None)
    if not callable(ward_getter):
        return 1.0
    ward = max(0.0, min(0.80, float(ward_getter(element) or 0.0)))
    return 1.0 - ward


def elemental_target_ward_text_v11339(session, element):
    element = canonical_element_v11339(element)
    if not element or not session:
        return ""
    ward_getter = getattr(session, "equipment_element_ward_v11176", None)
    if not callable(ward_getter):
        return ""
    ward = max(0.0, min(0.80, float(ward_getter(element) or 0.0)))
    if ward <= 0.0:
        return ""
    return f" Ward {V11339_ELEMENT_LABELS[element]} redukuje ten atak o {int(round(ward * 100))}%."


def skill_element_v11339(class_name, skill_name="", explicit_element=""):
    explicit = canonical_element_v11339(explicit_element)
    if explicit:
        return explicit
    cls = str(class_name or "").strip()
    name = str(skill_name or "").casefold()

    if cls == "Czarownik":
        return "fire" if any(x in name for x in ("ogień", "ogien", "inferno", "piekiel")) else "dark"
    if cls == "Nekromanta":
        return "dark"
    if cls == "Druid":
        return "poison"
    if cls == "Kapłan":
        return "holy"
    if cls == "Mag":
        return "ice"
    if cls == "Inżynier":
        if any(x in name for x in ("shock", "piorun", "electric", "mako")):
            return "lightning"
        if any(x in name for x in ("napalm", "ogień", "ogien", "bomb")):
            return "fire"
    return ""


def player_element_bonus_multiplier_v11339(session, element):
    element = canonical_element_v11339(element)
    if not element or session is None:
        return 1.0
    total = 0.0
    try:
        from data.items import ITEMS

        for row in session.equipped_item_rows():
            item = ITEMS.get(row["item_id"], {})
            bonuses = item.get("element_damage_bonus_pct") or {}
            total += float(bonuses.get(element, 0.0) or 0.0)
        _relic_id, relic = session.active_soul_weapon_relic_v11176()
        if relic:
            bonuses = relic.get("element_damage_bonus_pct") or {}
            total += float(bonuses.get(element, 0.0) or 0.0)
    except (AttributeError, KeyError, TypeError, ValueError):
        return 1.0
    return 1.0 + max(0.0, min(40.0, total)) / 100.0


def elemental_combat_audit_v11339():
    errors = []
    required = {"fire", "ice", "lightning", "dark", "poison", "holy", "water", "arcane"}
    if set(V11339_ELEMENT_ATTACKS) != required:
        errors.append("element set differs from reviewed eight-element contract")
    if canonical_element_v11339("electric") != "lightning":
        errors.append("electric alias does not canonicalize to lightning")
    samples = {
        "fire": {"name": "Płomienny Smok"},
        "ice": {"name": "Strażnik Szronu"},
        "lightning": {"name": "Dron Shock", "machine": True},
        "dark": {"name": "Cień Pustki"},
        "poison": {"name": "Jadowity Wąż"},
        "holy": {"name": "Świetlisty Serafin"},
        "water": {"name": "Wodny Strażnik"},
        "arcane": {"name": "Arkanista", "damage_type": "magic"},
    }
    for expected, template in samples.items():
        affinities = mob_element_affinities_v11339(template)
        if expected not in affinities:
            errors.append(f"{expected}: affinity inference missing")
    if elemental_mob_attack_profile_v11339({"training_dummy": True, "attack_elements_v11339": ("fire",)}, 0.0):
        errors.append("training dummy receives elemental attack")
    if elemental_mob_attack_profile_v11339({"uoss_superboss": True, "attack_elements_v11339": ("dark",)}, 0.0):
        errors.append("UOSS authored superboss receives random elemental attack")
    if skill_element_v11339("Mag", "Lanca Arkanów") != "ice":
        errors.append("Mag Synergy 2.0 frost identity missing")
    if skill_element_v11339("Druid", "Burza Żywiołów") != "poison":
        errors.append("Druid Synergy 2.0 poison identity missing")
    if skill_element_v11339("Czarownik", "Inferno Otchłani") != "fire":
        errors.append("Czarownik fire identity missing")

    return {
        "version": V11339_ELEMENTAL_COMBAT_VERSION,
        "elements": len(V11339_ELEMENT_ATTACKS),
        "errors": errors,
        "error_count": len(errors),
    }


ELEMENTAL_COMBAT_AUDIT_V11339 = elemental_combat_audit_v11339()
