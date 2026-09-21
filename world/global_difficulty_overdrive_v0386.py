# -*- coding: utf-8 -*-
"""Soulbound v0.38.6 - Global Difficulty Overdrive II.

Final combat layer loaded after all earlier world/dungeon balance modules.
Every mob receives an additional difficulty/reward multiplier. Dedicated
Crypt/Tower/Magitek/instance content receives an extra premium so it remains
harder than ordinary open-world combat.
"""

V0386_GLOBAL_DIFFICULTY_VERSION = "0.38.6"

_V0386_RANK_HP = {
    "normal": 1.00,
    "elite": 1.15,
    "rare": 1.28,
    "mini": 1.40,
    "boss": 1.55,
    "world_boss": 1.80,
}
_V0386_RANK_DAMAGE = {
    "normal": 1.00,
    "elite": 1.08,
    "rare": 1.15,
    "mini": 1.20,
    "boss": 1.28,
    "world_boss": 1.38,
}
_V0386_RANK_REWARD = {
    "normal": 1.00,
    "elite": 1.18,
    "rare": 1.32,
    "mini": 1.48,
    "boss": 1.72,
    "world_boss": 2.00,
}

_V0386_INSTANCE = {
    "world": (1.00, 1.00, 1.00),
    "instance": (1.20, 1.10, 1.15),
    "crypt": (1.25, 1.12, 1.20),
    "mythic_crypt": (1.38, 1.20, 1.38),
    "tower": (1.30, 1.15, 1.25),
    "mythic_tower": (1.42, 1.22, 1.42),
    "magitek": (1.36, 1.19, 1.36),
}


def _v0386_stage(template):
    try:
        return max(1, int(template.get("generator_level", template.get("v019_stage", 1)) or 1))
    except Exception:
        return 1


def _v0386_rank(template):
    template = template or {}
    raw = str(template.get("rank", "") or "").strip().lower()
    if (
        template.get("world_boss") or template.get("v016_world_boss")
        or template.get("mythic_crypt_boss") or template.get("mythic_astral_boss")
        or raw == "world_boss"
    ):
        return "world_boss"
    if (
        template.get("crypt_boss") or template.get("astral_boss")
        or template.get("magitek_boss") or template.get("machine_boss")
        or template.get("giant_fortress_boss") or template.get("boss")
        or template.get("boss_mechanic") or raw == "boss"
    ):
        return "boss"
    if template.get("mini_boss") or raw in ("mini", "miniboss", "mini_boss"):
        return "mini"
    if (
        template.get("rare_mob") or template.get("rare_variant")
        or template.get("rare_troll") or template.get("v016_legendary_rare")
        or raw == "rare"
    ):
        return "rare"
    if template.get("elite_affix") or template.get("elite") or raw == "elite":
        return "elite"
    try:
        generated = str(generator_core_v027.mob_rank(template) or "normal")
        if generated in _V0386_RANK_HP:
            return generated
    except Exception:
        pass
    return "normal"


def _v0386_instance_kind(template):
    template = template or {}
    if template.get("mythic_crypt_floor") is not None:
        return "mythic_crypt"
    if template.get("crypt_floor") is not None:
        return "crypt"
    if template.get("mythic_astral_floor") is not None:
        return "mythic_tower"
    if template.get("astral_floor") is not None:
        return "tower"
    # Both authored and infinite Magitek enemies are Machine-based. This keeps
    # the unified Magitek dungeon stronger from the authored prologue onward.
    if (
        template.get("magitek_floor") is not None or template.get("magitek_infinite")
        or template.get("machine") or str(template.get("creature_type", "")).lower() == "machine"
        or "magitek" in str(template.get("boss_mechanic", "")).lower()
    ):
        return "magitek"
    if any(template.get(flag) is not None for flag in (
        "giant_fortress_floor", "profession_dungeon_floor", "v020_gauntlet",
        "v020_mega_gate", "v0140_mini_dungeon", "v0180_great_ruin",
        "v021_endless_gauntlet_round",
    )):
        return "instance"
    if any(template.get(flag) for flag in (
        "giant_fortress_boss", "v018_great_ruin_guardian", "dungeon_boss",
        "instance_boss", "profession_dungeon_boss",
    )):
        return "instance"
    return "world"


def global_difficulty_multipliers_v0386(template):
    """Return final HP/damage/reward/coin multipliers for every combat mob."""
    template = template or {}
    stage = _v0386_stage(template)
    cap = max(1, int(globals().get("CHARACTER_MAX_LEVEL", 600) or 600))
    # Keep growing past 600, but more gently, so infinite dungeons never flatten.
    capped = min(stage, cap) / float(cap)
    overflow = max(0, stage - cap)

    hp = 1.70 + 1.00 * (capped ** 0.80) + min(1.50, overflow / 1200.0)
    damage = 1.22 + 0.58 * (capped ** 0.85) + min(0.55, overflow / 2200.0)
    reward = 1.45 + 0.95 * (capped ** 0.75) + min(1.10, overflow / 1600.0)
    coin = 1.20 + 0.55 * (capped ** 0.75) + min(0.60, overflow / 2000.0)

    rank = _v0386_rank(template)
    hp *= _V0386_RANK_HP.get(rank, 1.0)
    damage *= _V0386_RANK_DAMAGE.get(rank, 1.0)
    reward *= _V0386_RANK_REWARD.get(rank, 1.0)
    coin *= _V0386_RANK_REWARD.get(rank, 1.0)

    instance = _v0386_instance_kind(template)
    ihp, idmg, ireward = _V0386_INSTANCE.get(instance, _V0386_INSTANCE["world"])
    hp *= ihp
    damage *= idmg
    reward *= ireward
    coin *= max(1.0, 1.0 + (ireward - 1.0) * 0.65)

    nemesis = bool(template.get("v029_nemesis_owner_account_id") or template.get("nemesis"))
    if nemesis:
        hp *= 1.30
        damage *= 1.16
        reward *= 1.35
        coin *= 1.35

    return {
        "hp": round(hp, 6),
        "damage": round(damage, 6),
        "reward": round(reward, 6),
        "coin": round(coin, 6),
        "rank": rank,
        "instance": instance,
        "stage": stage,
        "nemesis": nemesis,
    }


_v0386_apply_before = v0190_apply_combat_template


def v0190_apply_combat_template(template):
    """Apply every older balance layer first, then the final v0.38.6 boost.

    Infinite/authored Magitek uses deliberately hand-built depth formulas. Older
    Generator refreshes can normalize those templates downward during spawn, so
    preserve the original authored floor values once and never compound them.
    """
    if isinstance(template, dict) and _v0386_instance_kind(template) == "magitek":
        if "_v0386_authored_hp" not in template:
            template["_v0386_authored_hp"] = int(template.get("max_hp", 1) or 1)
            template["_v0386_authored_damage"] = int(template.get("damage", 1) or 1)
            for _key in ("character_xp_reward", "class_xp_reward", "soul_reward", "stat_reward", "silver"):
                template[f"_v0386_authored_{_key}"] = int(template.get(_key, 0) or 0)

    result = _v0386_apply_before(template)
    if not isinstance(result, dict):
        return result

    # Some historical templates use generic flags such as boss=True that the
    # old Generator Core did not always map to its boss rank. Enforce a
    # canonical minimum for the FINAL detected rank before applying v0.38.6.
    _rank_floor = _v0386_rank(result)
    _stage_floor = max(1, min(int(globals().get("CHARACTER_MAX_LEVEL", 600) or 600), _v0386_stage(result)))
    try:
        _canon_hp = int(generator_core_v027.mob_hp(_stage_floor, _rank_floor))
        _canon_dmg = int(generator_core_v027.mob_damage(_stage_floor, _rank_floor))
        result["max_hp"] = max(int(result.get("max_hp", 1) or 1), _canon_hp)
        result["base_max_hp"] = int(result["max_hp"])
        result["damage"] = max(int(result.get("damage", 1) or 1), _canon_dmg)
    except Exception:
        pass

    if _v0386_instance_kind(result) == "magitek":
        result["max_hp"] = max(int(result.get("max_hp", 1) or 1), int(result.get("_v0386_authored_hp", 1) or 1))
        result["base_max_hp"] = int(result["max_hp"])
        result["damage"] = max(int(result.get("damage", 1) or 1), int(result.get("_v0386_authored_damage", 1) or 1))
        for _key in ("character_xp_reward", "class_xp_reward", "soul_reward", "stat_reward", "silver"):
            _saved = int(result.get(f"_v0386_authored_{_key}", 0) or 0)
            if _saved > int(result.get(_key, 0) or 0):
                result[_key] = _saved

    mult = global_difficulty_multipliers_v0386(result)

    result["max_hp"] = max(1, min(V019_SAFE_INT, int(round(int(result.get("max_hp", 1) or 1) * mult["hp"]))))
    result["base_max_hp"] = int(result["max_hp"])
    result["damage"] = max(1, min(V019_SAFE_INT, int(round(int(result.get("damage", 1) or 1) * mult["damage"]))))

    # Keep direct-field consumers aligned with the dynamic reward wrapper below.
    for key in ("character_xp_reward", "class_xp_reward", "soul_reward", "stat_reward"):
        if key in result:
            result[key] = max(1, min(V019_SAFE_INT, int(round(int(result.get(key, 1) or 1) * mult["reward"]))))
    if "silver" in result:
        result["silver"] = max(0, min(V019_SAFE_INT, int(round(int(result.get("silver", 0) or 0) * mult["coin"]))))
        result["gold"] = 0
        result["mithril"] = 0

    result["global_difficulty_overdrive_v0386"] = True
    result["global_difficulty_hp_mult_v0386"] = mult["hp"]
    result["global_difficulty_damage_mult_v0386"] = mult["damage"]
    result["global_difficulty_reward_mult_v0386"] = mult["reward"]
    result["global_difficulty_content_v0386"] = mult["instance"]
    result["global_difficulty_rank_v0386"] = mult["rank"]
    return result


v0190_apply_combat_template._global_difficulty_overdrive_v0386 = True


_v0386_reward_before = v0190_combat_reward


def v0190_combat_reward(template, kind):
    base = int(_v0386_reward_before(template, kind))
    if not isinstance(template, dict):
        return base

    # Enforce the reward floor for the final rank too; this fixes legacy
    # boss=True templates whose old generated reward could still look normal.
    rank = _v0386_rank(template)
    stage = max(1, min(int(globals().get("CHARACTER_MAX_LEVEL", 600) or 600), _v0386_stage(template)))
    try:
        if str(kind) == "coins":
            canonical = int(generator_core_v027.currency_for_stage(stage, rank))
        else:
            axis = {"class": "class", "soul": "soul", "stat": "stat", "character": "character"}.get(str(kind))
            canonical = int(generator_core_v027.axis_gain(axis, stage, generator_core_v027.RANK_REWARD.get(rank, 1.0))) if axis else 0
        base = max(base, canonical)
    except Exception:
        pass

    # Infinite Magitek has intentionally authored depth rewards. Preserve them
    # as a minimum before applying the final v0.38.6 reward multiplier.
    if _v0386_instance_kind(template) == "magitek":
        authored_key = {
            "class": "class_xp_reward", "soul": "soul_reward",
            "stat": "stat_reward", "character": "character_xp_reward",
            "coins": "silver",
        }.get(str(kind))
        if authored_key:
            base = max(base, int(template.get(f"_v0386_authored_{authored_key}", 0) or 0))

    mult = global_difficulty_multipliers_v0386(template)
    factor = mult["coin"] if str(kind) == "coins" else mult["reward"]
    return min(V019_SAFE_INT, max(0, int(round(base * factor))))


v0190_combat_reward._global_difficulty_overdrive_v0386 = True


# New dynamic encounters created after startup are already routed through
# World._register_runtime_spawn / the v0.38.4 rebind hooks. Existing live mobs
# are refreshed on normal World.refresh/respawn through v0190_apply... .

HELP_TOPICS.setdefault("trudnosc swiata", []).extend([
    "v0.38.6: Global Difficulty Overdrive II wzmacnia końcowo KAŻDEGO moba po wszystkich wcześniejszych warstwach balansu.",
    "HP i obrażenia rosną globalnie od najniższych stref do endgame; Elite, Rare, miniboss, boss, World Boss i Nemesis dostają kolejne premie.",
    "Krypty, Mityczne Krypty, Wieża Astralna, Mityczna Wieża, Nieskończony Magitek oraz inne instancje mają dodatkową premię trudności ponad globalny wzrost.",
    "Class XP, Soul XP, Character XP, stat XP oraz waluta rosną razem z nową trudnością.",
])
HELP_TOPICS.setdefault("krypta", []).append(
    "v0.38.6: wszystkie Krypty i ich bossowie dostają dodatkowy Global Difficulty Overdrive ponad Crypt Overdrive."
)
HELP_TOPICS.setdefault("wieza", []).append(
    "v0.38.6: obie Wieże i ich bossowie/Superbossowie dostają dodatkowy Global Difficulty Overdrive ponad Tower Overdrive."
)
HELP_TOPICS.setdefault("magitek", []).append(
    "v0.38.6: cały Nieskończony Kompleks Magitek, także autorski prolog, dostaje dodatkowy Global Difficulty Overdrive."
)


def global_difficulty_overdrive_audit_v0386():
    errors = []

    # Global curves must rise continuously through the progression range.
    rows = []
    for stage in (1, 50, 100, 300, 600, 900):
        rows.append(global_difficulty_multipliers_v0386({"generator_level": stage}))
    for key in ("hp", "damage", "reward", "coin"):
        seq = [r[key] for r in rows]
        if any(b <= a for a, b in zip(seq, seq[1:])):
            errors.append(f"nonmonotonic {key}: {seq}")

    # Rank hierarchy.
    rank_hp = [
        global_difficulty_multipliers_v0386({"generator_level": 200, "rank": rank})["hp"]
        for rank in ("normal", "elite", "rare", "mini", "boss", "world_boss")
    ]
    if any(b <= a for a, b in zip(rank_hp, rank_hp[1:])):
        errors.append(f"rank HP hierarchy broken: {rank_hp}")

    # Dedicated instances must remain above equivalent world mobs.
    base = global_difficulty_multipliers_v0386({"generator_level": 200})
    crypt = global_difficulty_multipliers_v0386({"generator_level": 200, "crypt_floor": 200})
    mythic = global_difficulty_multipliers_v0386({"generator_level": 200, "mythic_crypt_floor": 200})
    tower = global_difficulty_multipliers_v0386({"generator_level": 200, "astral_floor": 200})
    mtower = global_difficulty_multipliers_v0386({"generator_level": 200, "mythic_astral_floor": 200})
    magitek = global_difficulty_multipliers_v0386({"generator_level": 200, "machine": True})
    for label, row in (("crypt", crypt), ("tower", tower), ("magitek", magitek)):
        if row["hp"] <= base["hp"] or row["damage"] <= base["damage"]:
            errors.append(f"{label} not above world")
    if mythic["hp"] <= crypt["hp"]:
        errors.append("mythic crypt not above ordinary crypt")
    if mtower["hp"] <= tower["hp"]:
        errors.append("mythic tower not above ordinary tower")

    nemesis = global_difficulty_multipliers_v0386({"generator_level": 200, "rank": "boss", "nemesis": True})
    boss = global_difficulty_multipliers_v0386({"generator_level": 200, "rank": "boss"})
    if nemesis["hp"] <= boss["hp"] or nemesis["damage"] <= boss["damage"]:
        errors.append("Nemesis bonus missing")

    if not getattr(v0190_apply_combat_template, "_global_difficulty_overdrive_v0386", False):
        errors.append("combat template hook missing")
    if not getattr(v0190_combat_reward, "_global_difficulty_overdrive_v0386", False):
        errors.append("combat reward hook missing")

    # Behavior check on isolated templates. Old layers run first, v0.38.6 last.
    import copy as _copy_v0386
    samples = {
        "world": {"name": "Audit World Mob", "generator_level": 100, "drops": {}},
        "crypt": {"name": "Audit Crypt Mob", "generator_level": 100, "crypt_floor": 100, "drops": {}},
        "mythic": {"name": "Audit Mythic Mob", "generator_level": 100, "mythic_crypt_floor": 100, "drops": {}},
        "tower": {"name": "Audit Tower Mob", "generator_level": 100, "astral_floor": 100, "drops": {}},
        "mtower": {"name": "Audit Mythic Tower Mob", "generator_level": 100, "mythic_astral_floor": 100, "drops": {}},
        "magitek": {"name": "Audit Magitek Mob", "generator_level": 100, "machine": True, "creature_type": "machine", "drops": {}},
    }
    resolved = {}
    for label, template in samples.items():
        row = v0190_apply_combat_template(_copy_v0386.deepcopy(template))
        if not row.get("global_difficulty_overdrive_v0386"):
            errors.append(f"{label}: final marker missing")
        resolved[label] = (int(row.get("max_hp", 0)), int(row.get("damage", 0)))
    # Legacy rank flags must also produce real combat hierarchy after the full
    # Generator/wrapper chain, not just larger multipliers.
    _rank_resolved = []
    for _rank in ("normal", "elite", "rare", "boss", "world_boss"):
        _probe = {"name": f"Audit {_rank}", "generator_level": 100, "rank": _rank, "drops": {}}
        if _rank == "elite": _probe["elite"] = True
        if _rank == "rare": _probe["rare_variant"] = True
        if _rank == "boss": _probe["boss"] = True
        if _rank == "world_boss": _probe["world_boss"] = True
        _row = v0190_apply_combat_template(_copy_v0386.deepcopy(_probe))
        _rank_resolved.append((int(_row.get("max_hp", 0)), int(_row.get("damage", 0))))
    if any(_rank_resolved[i+1][0] <= _rank_resolved[i][0] for i in range(len(_rank_resolved)-1)):
        errors.append(f"resolved rank HP hierarchy broken: {_rank_resolved}")

    if not (resolved["crypt"][0] > resolved["world"][0] and resolved["mythic"][0] > resolved["crypt"][0]):
        errors.append(f"crypt behavior hierarchy broken: {resolved}")
    if not (resolved["tower"][0] > resolved["world"][0] and resolved["mtower"][0] > resolved["tower"][0]):
        errors.append(f"tower behavior hierarchy broken: {resolved}")
    if resolved["magitek"][0] <= resolved["world"][0]:
        errors.append(f"magitek behavior hierarchy broken: {resolved}")

    # Hand-authored Magitek depth values must survive Generator Core refreshes.
    _magitek_probe = {
        "name": "Audit Deep Magitek", "generator_level": 600,
        "machine": True, "creature_type": "machine", "magitek_floor": 100,
        "magitek_infinite": True, "max_hp": 250000, "damage": 3000,
        "class_xp_reward": 500000, "soul_reward": 200000, "stat_reward": 50000,
        "character_xp_reward": 350000, "silver": 100000, "drops": {},
    }
    _magitek_final = v0190_apply_combat_template(_copy_v0386.deepcopy(_magitek_probe))
    if int(_magitek_final.get("max_hp", 0) or 0) <= 250000:
        errors.append("deep Magitek authored HP was normalized downward")
    if int(_magitek_final.get("damage", 0) or 0) <= 3000:
        errors.append("deep Magitek authored damage was normalized downward")

    return {
        "version": V0386_GLOBAL_DIFFICULTY_VERSION,
        "error_count": len(errors),
        "errors": errors,
        "sample_stage_100": global_difficulty_multipliers_v0386({"generator_level": 100}),
        "sample_stage_600": global_difficulty_multipliers_v0386({"generator_level": 600}),
        "resolved_stage_100": resolved,
    }


GLOBAL_DIFFICULTY_OVERDRIVE_AUDIT_V0386 = global_difficulty_overdrive_audit_v0386()
if GLOBAL_DIFFICULTY_OVERDRIVE_AUDIT_V0386["error_count"]:
    raise RuntimeError(
        "Global Difficulty Overdrive Audit v0.38.6 failed: "
        + "; ".join(GLOBAL_DIFFICULTY_OVERDRIVE_AUDIT_V0386["errors"][:100])
    )

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.38.6: Global Difficulty Overdrive II — ponownie wzmocniono wszystkie moby całej gry, wszystkie lochy, obie Wieże, Magitek, bossów, World Bossów i Nemesis; EXP rośnie razem z trudnością."
)
