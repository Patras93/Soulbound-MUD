# -*- coding: utf-8 -*-
"""Adaptive combat scaling for Soulbound v1.13.30.

This layer does not rewrite authored templates. It computes encounter-local
targets from the actual local party and the actual player being hit.
"""

import math
from decimal import Decimal, ROUND_CEILING, localcontext

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


# v2.32.5: Make *all* high-level hunting grounds meaningful. An authored
# depth/region/stage determines an enemy's threat; player stats remain uncapped
# and there are no entry locks or caps on companion damage.
V2325_DEEP_DUNGEON_FLOOR_KEYS = (
    "crypt_floor", "mythic_crypt_floor", "astral_floor", "mythic_astral_floor",
    "giant_fortress_floor", "magitek_floor", "profession_dungeon_floor",
    "uoss_deep_dungeon_floor",
)
V2325_HIGH_AREA_STAGE_KEYS = (
    "terrain_room_stage_v0362", "generator_level",
    "recommended_mastery", "recommended_level", "v019_stage",
)


def adaptive_dungeon_floor_v2325(template):
    """Read explicit dungeon-depth tags, if any (kept for earlier callers)."""
    if not isinstance(template, dict) or template.get("training_dummy"):
        return 0
    depths = []
    for key in V2325_DEEP_DUNGEON_FLOOR_KEYS:
        try:
            value = int(template.get(key) or 0)
        except (TypeError, ValueError, OverflowError):
            continue
        if value > 0:
            depths.append(value)
    return max(depths, default=0)


def adaptive_encounter_stage_v2325(template, room=None):
    """Authoritative threat stage for a fight in a dungeon or high-level area.

    Prefer real floor/room metadata, with template stage also covering event
    enemies, Ocean encounters, high-tier bosses and dynamically created mobs.
    A noncombat hub or training dummy never gets a threat stage. Avoid relying
    on template ``level`` (which often means a different progression system).
    """
    if not isinstance(template, dict) or template.get("training_dummy"):
        return 0
    candidates = [adaptive_dungeon_floor_v2325(template)]
    for data in (template, room):
        if not isinstance(data, dict):
            continue
        if data.get("training_dummy"):
            return 0
        candidates.append(adaptive_dungeon_floor_v2325(data))
        for key in V2325_HIGH_AREA_STAGE_KEYS:
            try:
                stage = int(data.get(key) or 0)
            except (TypeError, ValueError, OverflowError):
                continue
            if stage > 0:
                candidates.append(stage)
    return max(candidates)


def adaptive_dungeon_pressure_v2325(template, character_level, room=None):
    """Return (HP multiplier percent, incoming damage multiplier) for high areas.

    This uses the area's *actual recommended combat stage*, not the party's
    combined power or an arbitrary name. Floor/area depth may be unlimited;
    relative extra HP/damage saturates after a 600-level mismatch for sensible
    encounter timing, while the authored base difficulty keeps increasing.
    """
    if character_level is None:
        return 100, 1.0
    stage = adaptive_encounter_stage_v2325(template, room)
    # Only high-level terrain is affected; low level enemies and novice areas
    # retain their existing combat balance and beginner damage protection.
    if stage < 100:
        return 100, 1.0
    level = max(1, int(character_level))
    gap = min(600, max(0, stage - level - 25))
    if not gap:
        return 100, 1.0
    hp_percent = 100 + (60 * gap // 100) + (10 * gap * gap // 10_000)
    damage_multiplier = 1.0 + 0.38 * (gap / 100.0)
    return hp_percent, round(damage_multiplier, 4)



# v3.00.0: dangerous enemies do not become trivial merely because a lower-level
# character owns powerful gear, many classes or high-stat mercenaries. This is a
# *soft* encounter modifier: it never locks a fight, alters the player's data,
# penalizes the ally's own damage or changes experience rewards directly.
def adaptive_underlevel_pressure_v3000(template, character_level, room=None):
    """(HP percent, incoming multiplier), measured against authored stage.

    Every genuine recommended stage is covered, including level 1-99 regions.
    The first five levels of mismatch are grace; after that the challenge rises
    continuously relative to the hero's level. Large gaps saturate *only the
    relative bonus* for computational safety; authored dungeon/floor difficulty
    continues its own unbounded scaling.
    """
    if character_level is None:
        return 100, 1.0
    stage = adaptive_encounter_stage_v2325(template, room)
    if stage <= 0:
        return 100, 1.0
    level = max(1, int(character_level))
    deficit = max(0, stage - level - 5)
    if deficit == 0:
        return 100, 1.0
    # Compare as integers first: infinite floor IDs may exceed float limits.
    denominator = max(15, (level + 1) // 2)
    relative_gap = (16.0 if deficit >= 16 * denominator
                    else deficit / denominator)
    hp_percent = 100 + round(75.0 * relative_gap + 14.0 * relative_gap ** 1.5)
    incoming = 1.0 + min(3.8, 0.42 * relative_gap)
    return hp_percent, round(incoming, 4)


def adaptive_combined_pressure_v3000(template, character_level, room=None):
    """Keep previous high-area guarantees; strengthen any underleveled area."""
    old_hp, old_damage = adaptive_dungeon_pressure_v2325(template, character_level, room)
    new_hp, new_damage = adaptive_underlevel_pressure_v3000(template, character_level, room)
    return max(old_hp, new_hp), max(old_damage, new_damage)


def adaptive_target_max_hp_v11330(base_max_hp, party_dps, template, party_level=None, room=None):
    """Target enough HP for several seconds of the current party's real output."""
    base = max(1, int(base_max_hp or 1))
    # Use decimal, not a floating-point product: massive player/mercenary DPS
    # must never overflow to inf or fall back to a hard HP ceiling.
    raw_dps = Decimal(str(party_dps or 1))
    if not raw_dps.is_finite():
        raise ValueError("Encounter DPS must be finite")
    dps = max(Decimal(1), raw_dps)
    rank = adaptive_combat_rank_v11330(template)
    seconds = Decimal(str(V11330_TARGET_FIGHT_SECONDS[rank]))
    elite_multiplier = Decimal(str(
        (template or {}).get("elite_hp_multiplier_v11338", 1.0) or 1.0
    ))
    if not elite_multiplier.is_finite():
        raise ValueError("Elite HP multiplier must be finite")
    elite_multiplier = max(Decimal(1), elite_multiplier)
    with localcontext() as ctx:
        ctx.prec = max(40, len(dps.as_tuple().digits) + 18)
        target = max(base, int((dps * seconds).to_integral_value(rounding=ROUND_CEILING)))
        # Apply the elite extension to the full target, including authored HP.
        target = max(base, int(
            (Decimal(target) * elite_multiplier).to_integral_value(rounding=ROUND_CEILING)
        ))
    # Parties far below their hunting-ground stage cannot turn a stage-400
    # encounter into stage-100 farming just by grouping.
    hp_percent, _ = adaptive_combined_pressure_v3000(template, party_level, room)
    if hp_percent > 100:
        target = (target * hp_percent + 99) // 100
    return target



def adaptive_reward_multiplier_v11330(base_max_hp, scaled_max_hp):
    """Diminishing, uncapped compensation for actual extra combat effort.

    Logarithmic growth avoids exponential economy inflation; unlike the former
    3x ceiling, harder fights continue improving the reward. No changes to the
    no-party-penalty and other independent reward rules.
    """
    base = max(1, int(base_max_hp or 1))
    scaled = max(base, int(scaled_max_hp or base))
    if scaled == base:
        return 1.0
    # log2(huge_int) is supported by Python without converting the integer
    # to float first; dividing huge ints would overflow at ~1e308.
    log_ratio = max(0.0, math.log2(scaled) - math.log2(base))
    return round(1.0 + 0.5 * log_ratio, 4)



def adaptive_target_incoming_fraction_v11330(template, party_size=1, player_level=None, room=None):
    """Per-action health pressure, including high-level regions and dungeons.

    Ordinary and level-appropriate fights retain their old balance.
    """
    rank = adaptive_combat_rank_v11330(template)
    base = float(V11330_TARGET_HP_FRACTION_PER_MOB_ACTION[rank])
    party_pressure = min(1.28, 1.0 + 0.04 * max(0, int(party_size or 1) - 1))
    normal = min(0.22, base * party_pressure)
    _, underlevel_multiplier = adaptive_combined_pressure_v3000(template, player_level, room)
    return min(0.45, normal * underlevel_multiplier)


def adaptive_beginner_incoming_target_v2005(template, player_level, base_expected, desired, room=None):
    """Avoid adaptive one-shots from *ordinary* enemies against new players.

    Adaptive HP pressure remains intact for experienced players and for bosses.
    For low-level characters, never let a common enemy multiply its authored
    expected damage by an enormous factor solely because the player has high HP
    from Constitution/equipment. The raw authored strike is never reduced.
    Hires/summons neither raise nor lower this limit and remain fully effective.
    """
    base = max(1.0, float(base_expected))
    target = max(base, float(desired))
    if adaptive_combat_rank_v11330(template) != "normal":
        return target
    level = max(1, int(player_level or 1))
    # A high-level area's enemy is not a harmless beginner mob. Keeping the
    # original 1.5x novice protection here let level-1 players face level-80
    # foes without feeling the intended threat. Ordinary novice zones retain it.
    if adaptive_encounter_stage_v2325(template, room) >= level + 12:
        return target
    if level >= 65:
        return target
    # Level 1-15: up to +50% relative to the authored, defense-aware strike.
    # Smoothly release the protection as players advance; no lvl-9 cliff.
    multiplier = 1.50 * (1.10 ** max(0, level - 15))
    return max(base, min(target, base * multiplier))


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
    if not 1.0 < adaptive_reward_multiplier_v11330(1000, 16000) < 4.0:
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
