# -*- coding: utf-8 -*-
"""Adaptive combat scaling for Soulbound v1.13.30.

This layer does not rewrite authored templates. It computes encounter-local
targets from the actual local party and the actual player being hit.
"""

import math

V11330_ADAPTIVE_COMBAT_VERSION = "1.13.30"

V11330_TARGET_FIGHT_SECONDS = {
    "normal": 8.0,
    "elite": 10.0,
    "rare": 12.0,
    "mini": 18.0,
    "boss": 28.0,
    "world_boss": 45.0,
}

V11330_TARGET_HP_FRACTION_PER_MOB_ACTION = {
    "normal": 0.07,
    "elite": 0.085,
    "rare": 0.10,
    "mini": 0.12,
    "boss": 0.14,
    "world_boss": 0.16,
}


def adaptive_combat_rank_v11330(template):
    template = template or {}
    raw = str(template.get("rank", "") or "").strip().casefold()
    if (
        template.get("world_boss")
        or template.get("v016_world_boss")
        or template.get("mythic_crypt_boss")
        or template.get("mythic_astral_boss")
        or template.get("uoss_superboss")
        or raw == "world_boss"
    ):
        return "world_boss"
    if (
        template.get("crypt_boss")
        or template.get("astral_boss")
        or template.get("magitek_boss")
        or template.get("machine_boss")
        or template.get("giant_fortress_boss")
        or template.get("boss")
        or template.get("boss_mechanic")
        or raw == "boss"
    ):
        return "boss"
    if template.get("mini_boss") or raw in ("mini", "miniboss", "mini_boss"):
        return "mini"
    if (
        template.get("rare_mob")
        or template.get("rare_variant")
        or template.get("rare_troll")
        or template.get("v016_legendary_rare")
        or raw == "rare"
    ):
        return "rare"
    if template.get("elite_affix") or template.get("elite") or raw == "elite":
        return "elite"
    return "normal"


def adaptive_target_max_hp_v11330(base_max_hp, party_dps, template):
    """Target enough HP for several seconds of the current party's real output."""
    base = max(1, int(base_max_hp or 1))
    dps = max(1.0, float(party_dps or 1.0))
    rank = adaptive_combat_rank_v11330(template)
    seconds = float(V11330_TARGET_FIGHT_SECONDS[rank])
    target = max(base, int(math.ceil(dps * seconds)))
    # v1.13.38: an Armored/Vampiric/etc. elite may deliberately extend the
    # reviewed elite fight target without bypassing Adaptive Combat.
    elite_hp_multiplier = max(
        1.0, float((template or {}).get("elite_hp_multiplier_v11338", 1.0) or 1.0)
    )
    target = max(base, int(math.ceil(target * elite_hp_multiplier)))
    # Python can handle larger ints, but keeping a very high sanity ceiling avoids
    # accidental runaway values while remaining effectively uncapped for gameplay.
    return min(target, 9_000_000_000_000_000)


def adaptive_reward_multiplier_v11330(base_max_hp, scaled_max_hp):
    """Modest anti-sponge compensation; party full-reward rules stay unchanged."""
    base = max(1.0, float(base_max_hp or 1))
    scaled = max(base, float(scaled_max_hp or base))
    ratio = max(1.0, scaled / base)
    return round(min(3.0, 1.0 + 0.25 * math.log2(ratio)), 4)


def adaptive_target_incoming_fraction_v11330(template, party_size=1):
    """Desired average HP pressure per one mob action against one player."""
    rank = adaptive_combat_rank_v11330(template)
    base = float(V11330_TARGET_HP_FRACTION_PER_MOB_ACTION[rank])
    party_pressure = min(1.28, 1.0 + 0.04 * max(0, int(party_size or 1) - 1))
    return min(0.22, base * party_pressure)


def adaptive_combat_audit_v11330():
    errors = []
    ranks = ("normal", "elite", "rare", "mini", "boss", "world_boss")
    seconds = [V11330_TARGET_FIGHT_SECONDS[r] for r in ranks]
    pressure = [V11330_TARGET_HP_FRACTION_PER_MOB_ACTION[r] for r in ranks]
    if any(b < a for a, b in zip(seconds, seconds[1:])):
        errors.append("fight seconds are not monotonic by rank")
    if any(b < a for a, b in zip(pressure, pressure[1:])):
        errors.append("incoming pressure is not monotonic by rank")

    sample = {"rank": "normal"}
    if adaptive_target_max_hp_v11330(1000, 1000, sample) < 8000:
        errors.append("solo DPS does not raise ordinary mob HP enough")
    if adaptive_target_max_hp_v11330(1000, 4000, sample) <= adaptive_target_max_hp_v11330(1000, 1000, sample):
        errors.append("party DPS does not increase encounter HP")
    if adaptive_target_incoming_fraction_v11330({"rank": "boss"}, 4) <= adaptive_target_incoming_fraction_v11330({"rank": "normal"}, 1):
        errors.append("boss/party incoming pressure does not exceed solo normal pressure")
    if adaptive_reward_multiplier_v11330(1000, 1000) != 1.0:
        errors.append("base reward multiplier must remain 1.0")
    if not 1.0 < adaptive_reward_multiplier_v11330(1000, 16000) <= 3.0:
        errors.append("adaptive reward multiplier out of bounds")

    # v1.13.37 production tuning matrix. Simulate local parties of 1-4 with
    # proportional real DPS. This protects both sides of the game-feel target:
    # ordinary mobs cannot collapse back to one-hit paper and cannot turn into
    # runaway sponges just because more players stand in the room.
    party_profiles = {}
    previous_normal_hp = 0
    for party_size in range(1, 5):
        party_dps = 1200.0 * party_size
        normal_hp = adaptive_target_max_hp_v11330(
            1000, party_dps, {"rank": "normal"}
        )
        boss_hp = adaptive_target_max_hp_v11330(
            5000, party_dps, {"rank": "boss"}
        )
        normal_seconds = normal_hp / party_dps
        boss_seconds = boss_hp / party_dps
        normal_pressure = adaptive_target_incoming_fraction_v11330(
            {"rank": "normal"}, party_size
        )
        boss_pressure = adaptive_target_incoming_fraction_v11330(
            {"rank": "boss"}, party_size
        )
        party_profiles[party_size] = {
            "party_dps": int(party_dps),
            "normal_hp": int(normal_hp),
            "normal_seconds": round(normal_seconds, 3),
            "boss_hp": int(boss_hp),
            "boss_seconds": round(boss_seconds, 3),
            "normal_pressure": round(normal_pressure, 5),
            "boss_pressure": round(boss_pressure, 5),
        }
        if normal_hp <= previous_normal_hp and previous_normal_hp:
            errors.append(
                f"party {party_size}: ordinary mob HP did not grow with local DPS"
            )
        previous_normal_hp = normal_hp
        if not 7.95 <= normal_seconds <= 8.05:
            errors.append(
                f"party {party_size}: ordinary target drifted from ~8s to {normal_seconds:.3f}s"
            )
        if not 27.95 <= boss_seconds <= 28.05:
            errors.append(
                f"party {party_size}: boss target drifted from ~28s to {boss_seconds:.3f}s"
            )
        if not 0.0 < normal_pressure < boss_pressure <= 0.22:
            errors.append(
                f"party {party_size}: incoming pressure ordering/cap invalid"
            )

    if adaptive_combat_rank_v11330({"uoss_superboss": True}) != "world_boss":
        errors.append("UOSS Super Boss is not classified as world_boss")
    elite_base = adaptive_target_max_hp_v11330(
        1000, 1200, {"rank": "elite"}
    )
    armored_elite = adaptive_target_max_hp_v11330(
        1000, 1200, {"rank": "elite", "elite_hp_multiplier_v11338": 1.20}
    )
    if armored_elite <= elite_base:
        errors.append("v1.13.38 armored elite HP multiplier is not respected")
    if not 7.0 <= V11330_TARGET_FIGHT_SECONDS["normal"] <= 10.0:
        errors.append("ordinary mob fight target left reviewed 7-10 second band")
    if not 24.0 <= V11330_TARGET_FIGHT_SECONDS["boss"] <= 32.0:
        errors.append("boss fight target left reviewed 24-32 second band")
    if not 40.0 <= V11330_TARGET_FIGHT_SECONDS["world_boss"] <= 55.0:
        errors.append("world boss fight target left reviewed 40-55 second band")

    return {
        "version": V11330_ADAPTIVE_COMBAT_VERSION,
        "production_matrix_version": "1.13.38",
        "party_profiles": party_profiles,
        "errors": errors,
        "error_count": len(errors),
    }


ADAPTIVE_COMBAT_AUDIT_V11330 = adaptive_combat_audit_v11330()
