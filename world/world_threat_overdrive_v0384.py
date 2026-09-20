# -*- coding: utf-8 -*-
"""Soulbound v0.38.4 - Global World Threat Overdrive.

Raises open-world combat difficulty and rewards without flattening the stronger
bespoke Crypt/Tower/Magitek/instance balance layers.
"""
import copy as _copy_v0384

V0384_WORLD_THREAT_VERSION = "0.38.4"

_V0384_RANK_HP = {
    "normal": 1.00, "elite": 1.15, "rare": 1.30,
    "mini": 1.45, "boss": 1.65, "world_boss": 2.00,
}
_V0384_RANK_DAMAGE = {
    "normal": 1.00, "elite": 1.08, "rare": 1.15,
    "mini": 1.20, "boss": 1.25, "world_boss": 1.35,
}
_V0384_RANK_REWARD = {
    "normal": 1.00, "elite": 1.20, "rare": 1.35,
    "mini": 1.55, "boss": 1.75, "world_boss": 2.20,
}


def world_threat_multipliers_v0384(stage, rank="normal", nemesis=False):
    """Continuous open-world scaling from stage 1 through 600+.

    The old v0.36.2 terrain HP/damage boost remains underneath this layer.
    """
    try:
        stage = max(1, int(stage or 1))
    except Exception:
        stage = 1
    cap = max(1, int(globals().get("CHARACTER_MAX_LEVEL", 600) or 600))
    x = min(stage, cap) / float(cap)
    rank = str(rank or "normal")

    # ~1.55x HP / 1.18x damage at the beginning, growing continuously to
    # 2.75x HP / 1.80x damage at stage 600 before rank-specific pressure.
    hp = (1.55 + 1.20 * (x ** 0.75)) * _V0384_RANK_HP.get(rank, 1.0)
    damage = (1.18 + 0.62 * (x ** 0.78)) * _V0384_RANK_DAMAGE.get(rank, 1.0)
    reward = (1.30 + 0.90 * (x ** 0.72)) * _V0384_RANK_REWARD.get(rank, 1.0)
    coin = (1.25 + 0.75 * (x ** 0.72)) * _V0384_RANK_REWARD.get(rank, 1.0)

    if nemesis:
        hp *= 1.35
        damage *= 1.20
        reward *= 1.50
        coin *= 1.50
    return {
        "hp": round(hp, 6), "damage": round(damage, 6),
        "reward": round(reward, 6), "coin": round(coin, 6),
    }


def _v0384_instance_room(room_id):
    rid = str(room_id or "")
    room = ROOMS.get(rid, {}) or {}
    flags = (
        "crypt_floor", "mythic_crypt_floor", "astral_floor", "mythic_astral_floor",
        "magitek_floor", "giant_fortress_floor", "profession_dungeon_floor",
        "v020_gauntlet", "v020_mega_gate", "v0140_mini_dungeon", "v0180_great_ruin",
        "v021_endless_gauntlet_round",
    )
    if any(room.get(flag) is not None for flag in flags):
        return True
    zone = str(room.get("zone", "") or "").lower()
    if any(token in zone for token in (
        "krypta nieskończona", "mityczna krypta", "wieża astralna",
        "nieskończony kompleks magitek", "megadungeon", "gauntlet",
    )):
        return True
    if rid.startswith((
        "crypt_floor_", "mythic_crypt_floor_", "astral_floor_", "mythic_astral_floor_",
        "magitek_floor_", "v021_endless_gauntlet_",
    )):
        return True
    return False


_v0384_base_terrain_scaled = World._terrain_scaled_template_v0362


def _terrain_scaled_template_v0384(self, room_id, template_id):
    # Preserve the full v0.36.2 behavior first, including its stage clone.
    resolved_id = _v0384_base_terrain_scaled(self, room_id, template_id)
    resolved = MOB_TEMPLATES.get(resolved_id)
    if not isinstance(resolved, dict):
        return resolved_id
    if resolved.get("world_threat_overdrive_v0384"):
        return resolved_id
    if _v0384_instance_room(room_id):
        return resolved_id

    try:
        room = ROOMS.get(str(room_id or ""), {}) or {}
        stage = int(room.get("generator_level", room.get("recommended_mastery", resolved.get("generator_level", 1))) or 1)
    except Exception:
        stage = int(resolved.get("generator_level", 1) or 1)
    stage = max(1, min(int(globals().get("CHARACTER_MAX_LEVEL", 600) or 600), stage))
    try:
        base_stage = int(resolved.get("generator_level", 1) or 1)
    except Exception:
        base_stage = 1
    stage = max(stage, base_stage)
    rank = str(generator_core_v027.mob_rank(resolved) or "normal")
    nemesis = bool(resolved.get("v029_nemesis_owner_account_id") or resolved.get("nemesis"))
    mult = world_threat_multipliers_v0384(stage, rank, nemesis=nemesis)

    runtime_id = f"{resolved_id}__world_v0384_{stage:03d}"
    if runtime_id not in MOB_TEMPLATES:
        clone = _copy_v0384.deepcopy(resolved)
        clone["base_template"] = str(resolved.get("base_template") or template_id)
        clone["world_threat_overdrive_v0384"] = True
        clone["world_threat_stage_v0384"] = stage
        clone["world_threat_rank_v0384"] = rank
        clone["world_threat_hp_multiplier_v0384"] = mult["hp"]
        clone["world_threat_damage_multiplier_v0384"] = mult["damage"]
        clone["world_threat_reward_multiplier_v0384"] = mult["reward"]
        clone["world_threat_coin_multiplier_v0384"] = mult["coin"]
        if nemesis:
            clone["world_threat_nemesis_v0384"] = True
        MOB_TEMPLATES[runtime_id] = clone
    return runtime_id


World._terrain_scaled_template_v0362 = _terrain_scaled_template_v0384
World._terrain_scaled_template_v0362._world_threat_overdrive_v0384 = True


_v0384_base_apply_combat_template = v0190_apply_combat_template


def v0190_apply_combat_template_v0384(template):
    template = _v0384_base_apply_combat_template(template)
    if not isinstance(template, dict) or not template.get("world_threat_overdrive_v0384"):
        return template
    hp_mult = float(template.get("world_threat_hp_multiplier_v0384", 1.0) or 1.0)
    dmg_mult = float(template.get("world_threat_damage_multiplier_v0384", 1.0) or 1.0)
    reward_mult = float(template.get("world_threat_reward_multiplier_v0384", 1.0) or 1.0)
    coin_mult = float(template.get("world_threat_coin_multiplier_v0384", 1.0) or 1.0)
    template["max_hp"] = max(1, int(round(int(template.get("max_hp", 1) or 1) * hp_mult)))
    template["base_max_hp"] = template["max_hp"]
    template["damage"] = max(1, int(round(int(template.get("damage", 1) or 1) * dmg_mult)))
    for key in ("character_xp_reward", "class_xp_reward", "soul_reward", "stat_reward"):
        template[key] = min(V019_SAFE_INT, max(1, int(round(int(template.get(key, 1) or 1) * reward_mult))))
    template["silver"] = min(V019_SAFE_INT, max(0, int(round(int(template.get("silver", 0) or 0) * coin_mult))))
    template["gold"] = 0
    template["mithril"] = 0
    return template


v0190_apply_combat_template = v0190_apply_combat_template_v0384
v0190_apply_combat_template._world_threat_overdrive_v0384 = True


def _v0384_rebind_spawned_mob(world, mob):
    if mob is None:
        return mob
    room_id = str(getattr(mob, "room_id", "") or "")
    old_id = str(getattr(mob, "template_id", "") or "")
    if not old_id or old_id not in MOB_TEMPLATES:
        return mob
    new_id = world._terrain_scaled_template_v0362(room_id, old_id)
    if new_id != old_id and new_id in MOB_TEMPLATES:
        v0190_apply_combat_template(MOB_TEMPLATES[new_id])
        mob.template_id = new_id
        mob.hp = int(MOB_TEMPLATES[new_id].get("max_hp", getattr(mob, "hp", 1)) or 1)
    return mob


def _v0384_wrap_spawn_method(name):
    original = getattr(World, name, None)
    if not callable(original) or getattr(original, "_world_threat_overdrive_v0384", False):
        return
    def wrapped(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        if isinstance(result, list):
            for mob in result:
                _v0384_rebind_spawned_mob(self, mob)
        else:
            _v0384_rebind_spawned_mob(self, result)
        return result
    wrapped.__name__ = getattr(original, "__name__", name)
    wrapped.__doc__ = getattr(original, "__doc__", None)
    wrapped._world_threat_overdrive_v0384 = True
    setattr(World, name, wrapped)


for _v0384_method in (
    "_ensure_v0290_event_spawns", "ensure_v029_nemesis", "_ensure_v0160_encounters",
    "_ensure_v0200_mythic_encounters", "_ensure_v0140_event_spawn",
    "_ensure_v0180_legendary_event_spawn",
):
    _v0384_wrap_spawn_method(_v0384_method)


HELP_TOPICS["trudnosc swiata"] = [
    "v0.38.4: cały otwarty świat jest wyraźnie trudniejszy od pierwszych stref aż po endgame.",
    "Zwykłe moby, Elite, Rare, regionalni bossowie, World Bossowie, Nemesis i eventowi przeciwnicy dostają globalny wzrost HP i obrażeń zależny od etapu.",
    "Elite/Rare/boss/World Boss dostają dodatkowy mnożnik ponad zwykły świat. Nemesis jest dodatkowo wzmacniany.",
    "Class XP, Soul XP, Character XP, stat XP i waluta rosną razem z trudnością.",
    "Krypty, Wieże i Nieskończony Kompleks Magitek zachowują własne mocniejsze warstwy balansu i nie dostają drugiej kopii World Threat Overdrive.",
]
HELP_TOPIC_ALIASES.update({
    "trudnosc swiata": "trudnosc swiata", "world threat": "trudnosc swiata",
    "world difficulty": "trudnosc swiata", "trudnosc": "trudnosc swiata",
})


def world_threat_overdrive_audit_v0384():
    errors = []
    samples = (1, 50, 100, 300, 600)
    vals = [world_threat_multipliers_v0384(s, "normal") for s in samples]
    for key in ("hp", "damage", "reward", "coin"):
        seq = [v[key] for v in vals]
        if any(b <= a for a, b in zip(seq, seq[1:])):
            errors.append(f"nonmonotonic {key}: {seq}")
    if world_threat_multipliers_v0384(100, "elite")["hp"] <= world_threat_multipliers_v0384(100, "normal")["hp"]:
        errors.append("elite hp not above normal")
    if world_threat_multipliers_v0384(100, "rare")["reward"] <= world_threat_multipliers_v0384(100, "elite")["reward"]:
        errors.append("rare reward not above elite")
    if world_threat_multipliers_v0384(100, "world_boss")["damage"] <= world_threat_multipliers_v0384(100, "boss")["damage"]:
        errors.append("world boss damage not above boss")
    if world_threat_multipliers_v0384(100, "boss", True)["hp"] <= world_threat_multipliers_v0384(100, "boss", False)["hp"]:
        errors.append("nemesis hp bonus missing")
    if not getattr(World._terrain_scaled_template_v0362, "_world_threat_overdrive_v0384", False):
        errors.append("world terrain hook missing")
    if not getattr(v0190_apply_combat_template, "_world_threat_overdrive_v0384", False):
        errors.append("combat refresh hook missing")
    for method in (
        "_ensure_v0290_event_spawns", "ensure_v029_nemesis", "_ensure_v0160_encounters",
        "_ensure_v0200_mythic_encounters", "_ensure_v0140_event_spawn", "_ensure_v0180_legendary_event_spawn",
    ):
        fn = getattr(World, method, None)
        if callable(fn) and not getattr(fn, "_world_threat_overdrive_v0384", False):
            errors.append(f"dynamic spawn hook missing: {method}")
    # Dedicated instance systems must remain exempt from the NEW v0.38.4 layer.
    for rid in ("crypt_floor_1", "mythic_crypt_floor_1", "astral_floor_100", "mythic_astral_floor_1", "magitek_zero_final"):
        if rid in ROOMS and not _v0384_instance_room(rid):
            errors.append(f"instance not exempt: {rid}")
    return {
        "version": V0384_WORLD_THREAT_VERSION,
        "sample_stages": samples,
        "sample_multipliers": vals,
        "error_count": len(errors),
        "errors": errors,
    }


WORLD_THREAT_OVERDRIVE_AUDIT_V0384 = world_threat_overdrive_audit_v0384()
if WORLD_THREAT_OVERDRIVE_AUDIT_V0384["error_count"]:
    raise RuntimeError(
        "World Threat Overdrive Audit v0.38.4 failed: "
        + "; ".join(WORLD_THREAT_OVERDRIVE_AUDIT_V0384["errors"][:100])
    )

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.38.4: World Threat Overdrive — cały otwarty świat, eventy, bossowie i Nemesis są mocniejsze, a EXP/nagrody rosną razem z zagrożeniem."
)
LATEST_CHANGES_TITLE = "Soulbound v0.38.4 - Global World Threat Overdrive"
LATEST_CHANGES = [
    "Globalnie wzmocniono zwykłe moby otwartego świata od najniższych stref do endgame.",
    "Elite, Rare, bossowie, World Bossowie i Nemesis dostają dodatkowe mnożniki trudności.",
    "Zwiększono Class/Soul/Character/stat XP oraz walutę proporcjonalnie do nowej trudności.",
    "Dynamiczne eventy i Nemesis korzystają z tej samej warstwy trudności.",
    "Krypty, Wieże i Magitek zachowują własny jeszcze mocniejszy balans bez podwójnego v0.38.4.",
]
