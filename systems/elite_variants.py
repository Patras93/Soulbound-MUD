# -*- coding: utf-8 -*-
"""Global random elite mob affixes for Soulbound v1.13.38.

Elite variants are runtime clones of ordinary mob templates. They preserve the
base species/quest identity and remain under Adaptive Combat; only the affix
changes fight feel and reward quality.
"""

import copy
import random

V11338_ELITE_VARIANTS_VERSION = "1.13.38"
V11338_ELITE_SPAWN_CHANCE = 0.08

# Tuned so an elite is clearly noticeable but never becomes a replacement for
# authored bosses/rares. Adaptive Combat still owns encounter scaling.
V11338_ELITE_AFFIXES = {
    "enraged": {
        "label": "Wściekły",
        "reward_multiplier": 1.45,
        "drop_multiplier": 1.35,
        "hp_multiplier": 1.00,
        "damage_multiplier": 1.18,
        "regen_fraction": 0.0,
        "storm_every": 0,
        "storm_multiplier": 1.0,
    },
    "armored": {
        "label": "Opancerzony",
        "reward_multiplier": 1.55,
        "drop_multiplier": 1.45,
        "hp_multiplier": 1.20,
        "damage_multiplier": 1.00,
        "regen_fraction": 0.0,
        "storm_every": 0,
        "storm_multiplier": 1.0,
    },
    "vampiric": {
        "label": "Wampiryczny",
        "reward_multiplier": 1.60,
        "drop_multiplier": 1.50,
        "hp_multiplier": 1.05,
        "damage_multiplier": 1.05,
        "regen_fraction": 0.025,
        "storm_every": 0,
        "storm_multiplier": 1.0,
    },
    "storm": {
        "label": "Burzowy",
        "reward_multiplier": 1.60,
        "drop_multiplier": 1.55,
        "hp_multiplier": 1.00,
        "damage_multiplier": 1.08,
        "regen_fraction": 0.0,
        "storm_every": 3,
        "storm_multiplier": 1.30,
    },
    "cursed": {
        "label": "Przeklęty",
        "reward_multiplier": 1.65,
        "drop_multiplier": 1.60,
        "hp_multiplier": 1.05,
        "damage_multiplier": 1.12,
        "regen_fraction": 0.0,
        "storm_every": 0,
        "storm_multiplier": 1.0,
    },
}

_V11338_BOSS_FLAGS = (
    "world_boss",
    "v016_world_boss",
    "v020_mythic_world_boss",
    "uoss_superboss",
    "boss",
    "boss_mechanic",
    "mini_boss",
    "crypt_boss",
    "astral_boss",
    "mythic_crypt_boss",
    "mythic_astral_boss",
    "giant_fortress_boss",
    "magitek_boss",
    "machine_boss",
    "guild_boss",
    "milestone_boss",
    "profession_dungeon_boss",
    "v018_legendary_event_boss",
    "v018_great_ruin_guardian",
    "v020_megadungeon_boss",
)


def elite_eligible_template_v11338(template):
    """Only ordinary mobs can receive a random v1.13.38 elite affix."""
    if not isinstance(template, dict) or not template:
        return False
    if template.get("training_dummy") or template.get("source_xp_exact"):
        return False
    if any(template.get(flag) for flag in _V11338_BOSS_FLAGS):
        return False
    raw_rank = str(template.get("rank", "") or "").strip().casefold()
    if raw_rank in {"elite", "rare", "mini", "miniboss", "mini_boss", "boss", "world_boss"}:
        return False
    if (
        template.get("elite")
        or template.get("elite_affix")
        or template.get("rare_mob")
        or template.get("rare_variant")
        or template.get("rare_troll")
        or template.get("v016_legendary_rare")
    ):
        return False
    return True


def elite_roll_affix_v11338(template, rng=None, chance=None):
    """Return an affix key or empty string for this spawn/respawn."""
    if not elite_eligible_template_v11338(template):
        return ""
    rng = rng or random
    chance = V11338_ELITE_SPAWN_CHANCE if chance is None else float(chance)
    chance = max(0.0, min(1.0, chance))
    if rng.random() >= chance:
        return ""
    return rng.choice(tuple(V11338_ELITE_AFFIXES))


def elite_variant_id_v11338(base_template_id, affix):
    base_template_id = str(base_template_id or "").strip()
    affix = str(affix or "").strip().casefold()
    return f"{base_template_id}__elite_v11338_{affix}"


def elite_source_template_id_v11338(template_id, template):
    """Return the actual spawn source, including terrain/depth runtime clones."""
    if not isinstance(template, dict):
        return str(template_id or "")
    return str(template.get("elite_source_template_v11338") or template_id or "")


def build_elite_variant_template_v11338(base_template_id, template, affix):
    """Build one runtime clone; caller owns registration in MOB_TEMPLATES."""
    if affix not in V11338_ELITE_AFFIXES:
        raise ValueError(f"unknown elite affix: {affix}")
    if not elite_eligible_template_v11338(template):
        raise ValueError("template is not eligible for random elite conversion")

    spec = V11338_ELITE_AFFIXES[affix]
    clone = copy.deepcopy(template)
    base_name = str(template.get("name") or base_template_id)
    clone["name"] = f"{spec['label']} {base_name}"
    clone["rank"] = "elite"
    clone["elite"] = True
    clone["elite_affix"] = affix
    # Bestiary/kill identity should collapse to the authored species even when
    # this spawn came from a terrain/depth runtime clone. Respawn needs the
    # exact source clone separately so its stage/difficulty is preserved.
    canonical_base = str(
        template.get("elite_base_template")
        or template.get("rare_base_template")
        or template.get("dense_dungeon_base_template")
        or template.get("base_template")
        or base_template_id
    )
    clone["elite_base_template"] = canonical_base
    clone["elite_source_template_v11338"] = str(base_template_id)
    clone["elite_reward_multiplier_v11338"] = float(spec["reward_multiplier"])
    clone["elite_drop_multiplier_v11338"] = float(spec["drop_multiplier"])
    clone["elite_hp_multiplier_v11338"] = float(spec["hp_multiplier"])
    clone["elite_damage_multiplier_v11338"] = float(spec["damage_multiplier"])
    clone["elite_regen_fraction_v11338"] = float(spec["regen_fraction"])
    clone["elite_storm_every_v11338"] = int(spec["storm_every"])
    clone["elite_storm_multiplier_v11338"] = float(spec["storm_multiplier"])
    # Keep the original quest_target/drops/template metadata untouched. The
    # canonical Bestiary already collapses elite_base_template to the species.
    return clone


def elite_enemy_action_multiplier_v11338(template, combat_turn=0):
    if not isinstance(template, dict) or not template.get("elite_affix"):
        return 1.0
    multiplier = max(
        1.0, float(template.get("elite_damage_multiplier_v11338", 1.0) or 1.0)
    )
    every = max(0, int(template.get("elite_storm_every_v11338", 0) or 0))
    turn = max(0, int(combat_turn or 0))
    if every and turn and turn % every == 0:
        multiplier *= max(
            1.0, float(template.get("elite_storm_multiplier_v11338", 1.0) or 1.0)
        )
    return multiplier


def elite_average_enemy_multiplier_v11338(template):
    """Average multiplier used by consider(); runtime still resolves burst turns."""
    if not isinstance(template, dict) or not template.get("elite_affix"):
        return 1.0
    base = max(
        1.0, float(template.get("elite_damage_multiplier_v11338", 1.0) or 1.0)
    )
    every = max(0, int(template.get("elite_storm_every_v11338", 0) or 0))
    burst = max(
        1.0, float(template.get("elite_storm_multiplier_v11338", 1.0) or 1.0)
    )
    if every:
        base *= 1.0 + (burst - 1.0) / float(every)
    return base


def elite_regen_amount_v11338(template, max_hp, current_hp):
    if not isinstance(template, dict) or template.get("elite_affix") != "vampiric":
        return 0
    max_hp = max(1, int(max_hp or 1))
    current_hp = max(0, int(current_hp or 0))
    if current_hp >= max_hp:
        return 0
    fraction = max(
        0.0, min(0.10, float(template.get("elite_regen_fraction_v11338", 0.0) or 0.0))
    )
    if fraction <= 0:
        return 0
    return min(max_hp - current_hp, max(1, int(round(max_hp * fraction))))


def elite_variants_audit_v11338():
    errors = []
    expected = {"enraged", "armored", "vampiric", "storm", "cursed"}
    if set(V11338_ELITE_AFFIXES) != expected:
        errors.append("elite affix set drifted from reviewed five-affix contract")
    if not 0.01 <= V11338_ELITE_SPAWN_CHANCE <= 0.20:
        errors.append("elite spawn chance left reviewed 1-20 percent band")

    labels = [str(spec.get("label") or "") for spec in V11338_ELITE_AFFIXES.values()]
    if len(labels) != len(set(labels)) or any(not label for label in labels):
        errors.append("elite display labels must be non-empty and unique")

    ordinary = {
        "name": "Goblin Testowy",
        "max_hp": 100,
        "damage": 10,
        "drops": {"healing_potion": 0.10},
        "quest_target": "goblin",
    }
    for affix in V11338_ELITE_AFFIXES:
        variant = build_elite_variant_template_v11338("goblin_test", ordinary, affix)
        if variant.get("rank") != "elite" or variant.get("elite_affix") != affix:
            errors.append(f"{affix}: clone is not classified as elite")
        if variant.get("elite_base_template") != "goblin_test":
            errors.append(f"{affix}: canonical base identity was not preserved")
        if variant.get("quest_target") != "goblin" or variant.get("drops") != ordinary["drops"]:
            errors.append(f"{affix}: authored quest/drop identity changed")
        if float(variant.get("elite_reward_multiplier_v11338", 1.0)) <= 1.0:
            errors.append(f"{affix}: reward multiplier is not better than normal")
        if float(variant.get("elite_drop_multiplier_v11338", 1.0)) <= 1.0:
            errors.append(f"{affix}: drop multiplier is not better than normal")
        if not str(variant.get("name", "")).startswith(
            str(V11338_ELITE_AFFIXES[affix]["label"]) + " "
        ):
            errors.append(f"{affix}: player-facing affix label missing")

    for blocked in (
        {"name": "Boss", "boss": True},
        {"name": "World Boss", "world_boss": True},
        {"name": "Rare", "rank": "rare"},
        {"name": "Legacy Rare Troll", "rare_troll": True},
        {"name": "Guild Boss", "guild_boss": True},
        {"name": "Legendary Event Boss", "v018_legendary_event_boss": True},
        {"name": "Old Elite", "elite": True},
        {"name": "Dummy", "training_dummy": True},
        {"name": "Source XP", "source_xp_exact": True},
    ):
        if elite_eligible_template_v11338(blocked):
            errors.append("protected authored boss/rare/special template became elite-eligible")

    terrain_source = dict(ordinary)
    terrain_source["base_template"] = "goblin_authored"
    terrain_variant = build_elite_variant_template_v11338(
        "goblin__terrain_v0362_100", terrain_source, "armored"
    )
    if terrain_variant.get("elite_base_template") != "goblin_authored":
        errors.append("terrain elite does not collapse Bestiary identity to authored species")
    if terrain_variant.get("elite_source_template_v11338") != "goblin__terrain_v0362_100":
        errors.append("terrain elite lost exact respawn source template")

    sample_vamp = build_elite_variant_template_v11338(
        "vamp_test", ordinary, "vampiric"
    )
    if elite_regen_amount_v11338(sample_vamp, 1000, 500) <= 0:
        errors.append("vampiric elite does not regenerate")
    sample_storm = build_elite_variant_template_v11338(
        "storm_test", ordinary, "storm"
    )
    if elite_enemy_action_multiplier_v11338(sample_storm, 3) <= elite_enemy_action_multiplier_v11338(sample_storm, 2):
        errors.append("storm elite has no burst cadence")

    return {
        "version": V11338_ELITE_VARIANTS_VERSION,
        "spawn_chance": V11338_ELITE_SPAWN_CHANCE,
        "affix_count": len(V11338_ELITE_AFFIXES),
        "errors": errors,
        "error_count": len(errors),
    }


ELITE_VARIANTS_AUDIT_V11338 = elite_variants_audit_v11338()
