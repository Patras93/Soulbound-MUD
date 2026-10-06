# -*- coding: utf-8 -*-
"""Soulbound v1.13.24 - Global "O Kurde" Game Feel helpers.

Small, activity-specific surprise moments. These helpers do not replace authored
rewards and do not create new progression gates. Random rolls are supplied by
callers so the rules stay deterministic and auditable.
"""
from __future__ import annotations

from core.economy_curve import economy_stage_anchor

V11324_GAME_FEEL_VERSION = "1.13.24"


def _clamp_stage(value) -> int:
    try:
        return max(1, min(600, int(value or 1)))
    except (TypeError, ValueError, OverflowError):
        return 1


def gather_jackpot_v11324(tool_level, profession_level, roll):
    """Rare double-yield moment for the four core gathering professions."""
    stage = max(_clamp_stage(tool_level), _clamp_stage(profession_level))
    chance = 0.04 + 0.04 * (stage / 600.0)
    if float(roll) >= chance:
        return None
    return {
        "chance": chance,
        "bonus_quantity_multiplier": 1.0,  # add one extra base haul
        "xp_multiplier": 1.75,
    }


def craft_inspiration_v11324(profession_level, tool_level, mastery_level, roll):
    """Rare craft inspiration: progression jackpot, never free duplicate EQ."""
    p = _clamp_stage(profession_level) / 600.0
    t = _clamp_stage(tool_level) / 600.0
    try:
        m = max(0.0, min(1.0, float(mastery_level or 0) / 100.0))
    except (TypeError, ValueError, OverflowError):
        m = 0.0
    chance = 0.03 + 0.015 * p + 0.010 * t + 0.005 * m
    if float(roll) >= chance:
        return None
    return {"chance": chance, "xp_multiplier": 2.0}


def quest_completion_bonus_v11324(quest, quest_coins, roll) -> int:
    """Occasional bonus envelope, outside the authored quest reward itself."""
    quest = quest or {}
    coins = max(0, int(quest_coins or 0))
    if coins <= 0:
        return 0
    # Exact/manual authored payouts stay exact.
    if (
        quest.get("manual_currency_reward_coins") is not None
        or quest.get("currency_reward_mode") == "manual"
    ):
        return 0

    kind = str(quest.get("kind") or "").strip().lower()
    repeatable = bool(quest.get("repeatable"))
    if repeatable:
        chance = 0.02
        bonus_mult = 0.25
    elif kind in {"legendary_rare", "world_boss", "mini_dungeon"}:
        chance = 0.08
        bonus_mult = 0.75
    else:
        chance = 0.06
        bonus_mult = 0.50

    if float(roll) >= chance:
        return 0
    return max(100, int(round(coins * bonus_mult)))


def exploration_find_v11324(room, character_level, roll):
    """Rare cache found only on a genuinely new room discovery."""
    room = room or {}
    candidates = [character_level]
    for key in ("generator_level", "recommended_mastery", "recommended_level", "level"):
        candidates.append(room.get(key))
    stage = max(_clamp_stage(value) for value in candidates)

    hidden = bool(
        room.get("hidden")
        or room.get("secret")
        or room.get("v0140_secret")
        or room.get("v018_ruin_final")
    )
    chance = 0.08 if hidden else 0.025
    if float(roll) >= chance:
        return None

    multiplier = 0.03 if hidden else 0.015
    coins = max(100, int(round(economy_stage_anchor(stage) * multiplier)))
    return {
        "stage": stage,
        "chance": chance,
        "coins": coins,
        "hidden": hidden,
    }


def mob_attack_flavor_v11324(template, roll):
    """Occasional identity strike for ordinary/Elite/Rare mobs.

    Bosses keep their authored mechanics; this layer is for everyday enemies.
    """
    template = template or {}
    if template.get("training_dummy"):
        return None
    if any(template.get(flag) for flag in (
        "world_boss", "boss", "mini_boss", "boss_mechanic", "crypt_boss",
        "astral_boss", "magitek_boss", "machine_boss", "mythic_crypt_boss",
        "mythic_astral_boss", "giant_fortress_boss", "dungeon_boss",
        "instance_boss",
    )):
        return None

    name = str(template.get("name") or "").casefold()
    damage_type = str(template.get("damage_type") or "").casefold()

    if damage_type == "magic":
        archetype, chance, multiplier, text = (
            "caster", 0.18, 1.35, "MAGICZNY ZRYW — atak przeciwnika jest wzmocniony."
        )
    elif any(token in name for token in (
        "wilk", "łucz", "lucz", "kusz", "zwiadow", "rzezim", "bomber",
        "skrytob", "assassin",
    )):
        archetype, chance, multiplier, text = (
            "skirmisher", 0.20, 1.25, "SZYBKI ATAK — przeciwnik wykorzystuje tempo."
        )
    elif any(token in name for token in (
        "osił", "osil", "wojownik", "egzekutor", "włócz", "wlocz",
        "tarcz", "garg", "strażnik", "straznik", "brute",
    )):
        archetype, chance, multiplier, text = (
            "bruiser", 0.15, 1.45, "CIĘŻKIE UDERZENIE — ten cios jest wyraźnie mocniejszy."
        )
    else:
        archetype, chance, multiplier, text = (
            "fighter", 0.10, 1.30, "MOCNY CIOS — przeciwnik trafia z większą siłą."
        )

    if float(roll) >= chance:
        return None
    return {
        "archetype": archetype,
        "chance": chance,
        "damage_multiplier": multiplier,
        "text": text,
    }


def game_feel_audit_v11324():
    errors = []

    if gather_jackpot_v11324(1, 1, 0.0)["xp_multiplier"] != 1.75:
        errors.append("gather jackpot missing")
    if gather_jackpot_v11324(600, 600, 0.99) is not None:
        errors.append("gather jackpot chance too high")

    if craft_inspiration_v11324(600, 600, 100, 0.0)["xp_multiplier"] != 2.0:
        errors.append("craft inspiration missing")

    if quest_completion_bonus_v11324(
        {"manual_currency_reward_coins": 1000}, 1000, 0.0
    ) != 0:
        errors.append("manual quest reward lost exactness")
    if quest_completion_bonus_v11324({"kind": "kill"}, 1000, 0.0) != 500:
        errors.append("one-time quest bonus mismatch")
    if quest_completion_bonus_v11324(
        {"kind": "kill", "repeatable": True}, 1000, 0.0
    ) != 250:
        errors.append("repeatable quest bonus mismatch")

    cache = exploration_find_v11324({"generator_level": 100}, 1, 0.0)
    if not cache or cache["coins"] <= 0:
        errors.append("exploration cache missing")

    if mob_attack_flavor_v11324({"training_dummy": True}, 0.0) is not None:
        errors.append("training dummy receives attack flavor")
    if mob_attack_flavor_v11324({"world_boss": True}, 0.0) is not None:
        errors.append("boss authored mechanics polluted")
    magic = mob_attack_flavor_v11324({"name": "Szaman", "damage_type": "magic"}, 0.0)
    if not magic or magic["archetype"] != "caster":
        errors.append("caster identity missing")

    return {
        "version": V11324_GAME_FEEL_VERSION,
        "error_count": len(errors),
        "errors": errors,
    }


GAME_FEEL_AUDIT_V11324 = game_feel_audit_v11324()
if GAME_FEEL_AUDIT_V11324["error_count"]:
    raise RuntimeError(
        "Global O Kurde Game Feel Audit v1.13.24 failed: "
        + "; ".join(GAME_FEEL_AUDIT_V11324["errors"][:50])
    )
