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
    return {"version": V11330_ADAPTIVE_COMBAT_VERSION, "errors": errors, "error_count": len(errors)}


ADAPTIVE_COMBAT_AUDIT_V11330 = adaptive_combat_audit_v11330()
