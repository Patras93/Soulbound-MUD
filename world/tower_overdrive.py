# -*- coding: utf-8 -*-
"""Soulbound v0.38.1 - Every Astral Tower Level Is Harder.

Final balance layer for ordinary Astral Tower and Mythic Astral Tower. It mirrors
Crypt Overdrive semantics: every consecutive tower level is strictly stronger
and more rewarding than the previous one; boss levels remain extra spikes.
"""

V0381_TOWER_OVERDRIVE_VERSION = "0.38.1"


def _v0381_tower_floor(template):
    if not isinstance(template, dict):
        return 0
    if template.get("mythic_astral_floor") is not None:
        try:
            return max(1, int(template.get("mythic_astral_floor") or 1))
        except Exception:
            return 1
    if template.get("astral_floor") is not None:
        try:
            return max(int(ASTRAL_MIN_FLOOR), int(template.get("astral_floor") or ASTRAL_MIN_FLOOR))
        except Exception:
            return int(ASTRAL_MIN_FLOOR)
    return 0


def _v0381_tower_kind(template):
    if not isinstance(template, dict):
        return None
    if template.get("mythic_astral_floor") is not None:
        return "mythic_tower_boss" if template.get("mythic_astral_boss") else "mythic_tower_regular"
    if template.get("astral_floor") is not None:
        return "tower_boss" if template.get("astral_boss") else "tower_regular"
    return None


def _v0381_tower_depth(kind, floor):
    floor = int(floor)
    if str(kind).startswith("mythic_"):
        return max(1, floor)
    return max(1, floor - int(ASTRAL_MIN_FLOOR) + 1)


def _v0381_tower_boosts(kind, floor):
    """Return HP, damage and XP multipliers; all rise every level."""
    depth = _v0381_tower_depth(kind, floor)
    mythic = str(kind).startswith("mythic_")
    boss = str(kind).endswith("boss")

    if mythic:
        # Starts near Mythic Crypt floor-1 strength, then catches up strongly.
        hp = 4.50 + depth * 0.075
        dmg = 1.80 + depth * 0.0145
        xp = 4.90 + depth * 0.033
        if boss:
            hp *= 1.35
            dmg *= 1.22
            xp *= 1.45
    else:
        # Ordinary Astral Tower starts at level 100, so level 100 itself gets a
        # full endgame-sized boost and every next level grows continuously.
        hp = 9.95 + depth * 0.050
        dmg = 3.35 + depth * 0.0033
        xp = 6.50 + depth * 0.025
        if boss:
            hp *= 2.00
            dmg *= 1.30
            xp *= 1.45
    return float(hp), float(dmg), float(xp)


_v0381_tower_apply_before = v0190_apply_combat_template


def v0190_apply_combat_template(template):
    # The previous final layer restores canonical Generator Core values first,
    # keeping this wrapper idempotent across spawn/respawn refreshes.
    result = _v0381_tower_apply_before(template)
    kind = _v0381_tower_kind(result)
    if kind is None:
        return result

    floor = _v0381_tower_floor(result)
    depth = _v0381_tower_depth(kind, floor)

    # Canonical refresh strips the numeric UOSSMUD Superbossa multiplier while
    # preserving its identity flags. Restore that individual profile before the
    # new Mythic Tower layer so named Superbosses remain distinct.
    if kind == "mythic_tower_boss" and result.get("uoss_superboss") and "uoss_superboss_profile_v0366" in globals():
        try:
            profile = uoss_superboss_profile_v0366("mythic_astral", floor)
            result["max_hp"] = max(1, int(round(int(result.get("max_hp", 1) or 1) * 2.20 * float(profile.get("hp", 1.0) or 1.0))))
            result["base_max_hp"] = int(result["max_hp"])
            result["damage"] = max(1, int(round(int(result.get("damage", 1) or 1) * 1.28 * float(profile.get("damage", 1.0) or 1.0))))
        except Exception:
            pass

    hp_boost, dmg_boost, _xp_boost = _v0381_tower_boosts(kind, floor)
    hp = max(1, int(round(int(result.get("max_hp", 1) or 1) * hp_boost)))
    dmg = max(1, int(round(int(result.get("damage", 1) or 1) * dmg_boost)))

    # Absolute depth terms guarantee strict adjacent-level growth even when the
    # canonical templates round two early levels to the same integer values.
    if kind.startswith("mythic_"):
        hp += depth * (300 if kind == "mythic_tower_regular" else 1400)
        dmg += depth * (3 if kind == "mythic_tower_regular" else 7)
    else:
        hp += depth * (90 if kind == "tower_regular" else 420)
        dmg += depth * (2 if kind == "tower_regular" else 5)

    result["max_hp"] = hp
    result["base_max_hp"] = hp
    result["damage"] = dmg
    result["tower_overdrive_v0381"] = True
    result["tower_overdrive_hp_mult_v0381"] = round(hp_boost, 6)
    result["tower_overdrive_damage_mult_v0381"] = round(dmg_boost, 6)
    return result


_v0381_tower_reward_before = v0190_combat_reward


def v0190_combat_reward(template, kind):
    base = int(_v0381_tower_reward_before(template, kind))
    if str(kind) == "coins":
        return base
    tower_kind = _v0381_tower_kind(template)
    if tower_kind is None:
        return base
    floor = _v0381_tower_floor(template)
    depth = _v0381_tower_depth(tower_kind, floor)
    _hp, _dmg, xp_boost = _v0381_tower_boosts(tower_kind, floor)
    extra = depth * (600 if tower_kind.startswith("mythic_") else 220)
    if tower_kind.endswith("boss"):
        extra *= 5
    return min(V019_SAFE_INT, max(0, int(round(base * xp_boost)) + extra))


# Refresh every already-created Astral template through the final layer.
for _v0381_tid, _v0381_template in list(MOB_TEMPLATES.items()):
    if _v0381_tower_kind(_v0381_template):
        v0190_apply_combat_template(_v0381_template)


# Lazy levels above the static range must receive exactly the same final layer.
_create_infinite_astral_floor_definition_before_v0381 = create_infinite_astral_floor_definition


def create_infinite_astral_floor_definition(floor, mythic=False):
    room_id, spawns = _create_infinite_astral_floor_definition_before_v0381(floor, mythic=mythic)
    for _room_id, template_id in list(spawns or ()):
        template = MOB_TEMPLATES.get(template_id)
        if isinstance(template, dict) and _v0381_tower_kind(template):
            v0190_apply_combat_template(template)
    return room_id, spawns


HELP_TOPICS.setdefault("wieza", []).extend([
    "v0.38.1: Wieża Astralna i Mityczna Wieża Astralna mają Tower Overdrive. Każdy kolejny poziom jest mocniejszy i bardziej nagradzający od poprzedniego.",
    "Zwykła Wieża zaczyna się od poziomu 100: 101 jest mocniejszy od 100, 102 od 101 itd. Mityczna Wieża rośnie od poziomu 1 bez płaskich przedziałów.",
    "Na każdym poziomie rosną HP, obrażenia oraz Class/Soul/stat EXP. Boss co 10 poziomów jest dodatkowym skokiem, a Mityczni Superbossowie zachowują indywidualne profile UOSSMUD.",
    "Tower Overdrive działa także dla poziomów tworzonych dynamicznie ponad 200 i nie zatrzymuje wzrostu na 600.",
])
HELP_TOPIC_ALIASES.update({
    "wieża": "wieza", "tower": "wieza", "wiezaastralna": "wieza", "astraltower": "wieza",
    "mitycznawieza": "wieza", "mythicastral": "wieza",
})


def tower_overdrive_audit_v0381():
    errors = []

    # Mathematical curves must rise at every level through 600.
    for kind, start in (("tower_regular", int(ASTRAL_MIN_FLOOR)), ("tower_boss", int(ASTRAL_MIN_FLOOR)),
                        ("mythic_tower_regular", 1), ("mythic_tower_boss", 1)):
        last = None
        for floor in range(start, 601):
            row = _v0381_tower_boosts(kind, floor)
            if last is not None:
                for idx, label in enumerate(("HP", "damage", "EXP")):
                    if row[idx] <= last[idx]:
                        errors.append(f"{kind}: {label} boost not increasing at level {floor}")
                        break
            last = row

    # Real static ordinary Tower levels 100..200 must strictly rise.
    previous = None
    for floor in range(int(ASTRAL_MIN_FLOOR), int(ASTRAL_MAX_FLOOR) + 1):
        t = MOB_TEMPLATES.get(f"astral_floor_mob_{floor}")
        if not isinstance(t, dict):
            errors.append(f"astral: missing regular level {floor}")
            continue
        if not t.get("tower_overdrive_v0381"):
            errors.append(f"astral: level {floor} missing v0.38.1 overdrive")
            continue
        row = (int(t.get("max_hp", 0) or 0), int(t.get("damage", 0) or 0), int(v0190_combat_reward(t, "class")))
        if previous is not None:
            for idx, field in enumerate(("HP", "damage", "Class XP")):
                if row[idx] <= previous[idx]:
                    errors.append(f"astral: level {floor} {field}={row[idx]} not above level {floor-1}={previous[idx]}")
        previous = row

    # Real static Mythic Tower levels 1..200 must strictly rise.
    previous = None
    for floor in range(1, int(MYTHIC_MAX_FLOOR) + 1):
        t = MOB_TEMPLATES.get(f"mythic_astral_mob_{floor}")
        if not isinstance(t, dict):
            errors.append(f"mythic_astral: missing regular level {floor}")
            continue
        if not t.get("tower_overdrive_v0381"):
            errors.append(f"mythic_astral: level {floor} missing v0.38.1 overdrive")
            continue
        row = (int(t.get("max_hp", 0) or 0), int(t.get("damage", 0) or 0), int(v0190_combat_reward(t, "class")))
        if previous is not None:
            for idx, field in enumerate(("HP", "damage", "Class XP")):
                if row[idx] <= previous[idx]:
                    errors.append(f"mythic_astral: level {floor} {field}={row[idx]} not above level {floor-1}={previous[idx]}")
        previous = row

    # Every static boss/Superboss must remain a clear spike over same-level regular mob.
    for floor in range(100, int(ASTRAL_MAX_FLOOR) + 1, 10):
        boss = MOB_TEMPLATES.get(f"astral_boss_{floor}")
        reg = MOB_TEMPLATES.get(f"astral_floor_mob_{floor}")
        if not isinstance(boss, dict) or not isinstance(reg, dict):
            errors.append(f"astral: missing boss checkpoint {floor}")
            continue
        if int(boss.get("max_hp", 0) or 0) <= int(reg.get("max_hp", 0) or 0):
            errors.append(f"astral: boss {floor} HP not above regular")
        if int(v0190_combat_reward(boss, "class")) <= int(v0190_combat_reward(reg, "class")):
            errors.append(f"astral: boss {floor} XP not above regular")

    for floor in range(10, int(MYTHIC_MAX_FLOOR) + 1, 10):
        boss = MOB_TEMPLATES.get(f"mythic_astral_boss_{floor}")
        reg = MOB_TEMPLATES.get(f"mythic_astral_mob_{floor}")
        if not isinstance(boss, dict) or not isinstance(reg, dict):
            errors.append(f"mythic_astral: missing boss checkpoint {floor}")
            continue
        if int(boss.get("max_hp", 0) or 0) <= int(reg.get("max_hp", 0) or 0):
            errors.append(f"mythic_astral: boss {floor} HP not above regular")
        if int(v0190_combat_reward(boss, "class")) <= int(v0190_combat_reward(reg, "class")):
            errors.append(f"mythic_astral: boss {floor} XP not above regular")
        if not boss.get("uoss_superboss"):
            errors.append(f"mythic_astral: boss {floor} lost UOSSMUD Superboss identity")

    return {
        "version": V0381_TOWER_OVERDRIVE_VERSION,
        "ordinary_static_levels": int(ASTRAL_MAX_FLOOR) - int(ASTRAL_MIN_FLOOR) + 1,
        "mythic_static_levels": int(MYTHIC_MAX_FLOOR),
        "curve_guard_to_level": 600,
        "error_count": len(errors),
        "errors": errors,
    }


TOWER_OVERDRIVE_AUDIT_V0381 = tower_overdrive_audit_v0381()
if TOWER_OVERDRIVE_AUDIT_V0381["error_count"]:
    raise RuntimeError(
        "Tower Overdrive Audit v0.38.1 failed: "
        + "; ".join(TOWER_OVERDRIVE_AUDIT_V0381["errors"][:100])
    )

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.38.1: Tower Overdrive — zwykła i Mityczna Wieża Astralna rosną w HP, obrażeniach i EXP na każdym kolejnym poziomie, z dodatkowymi skokami bossów/Superbossów."
)
