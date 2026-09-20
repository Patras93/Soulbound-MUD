# -*- coding: utf-8 -*-
"""Soulbound v0.36.10 - Every Crypt Floor Is Harder.

Final balance layer for ordinary and Mythic Crypts. Difficulty and XP increase
on every single floor starting at floor 1; boss floors remain additional spikes.
This layer deliberately replaces the flat/capped v0.36.8 Crypt multipliers while
preserving its same-room combat dungeon exit behavior and all prior milestones.
"""

V03610_CRYPT_BASE_XP = {
    "crypt_regular": (2.50, 100.0),
    "crypt_boss": (4.00, 60.0),
    "mythic_regular": (4.00, 80.0),
    "mythic_boss": (7.00, 50.0),
}


def _v03610_floor(template):
    if not isinstance(template, dict):
        return 0
    if template.get("mythic_crypt_floor") is not None:
        try:
            return max(1, int(template.get("mythic_crypt_floor") or 1))
        except Exception:
            return 1
    if template.get("crypt_floor") is not None:
        try:
            return max(1, int(template.get("crypt_floor") or 1))
        except Exception:
            return 1
    return 0


def _v03610_kind(template):
    if not isinstance(template, dict):
        return None
    if template.get("mythic_crypt_floor") is not None:
        return "mythic_boss" if template.get("mythic_crypt_boss") else "mythic_regular"
    if template.get("crypt_floor") is not None:
        return "crypt_boss" if template.get("crypt_boss") else "crypt_regular"
    return None


def _v03610_hp_mult(kind, floor):
    floor = max(1, int(floor))
    if kind.startswith("mythic_"):
        mult = 4.0 + floor / 35.0
        if kind == "mythic_boss":
            mult *= 2.0
        return mult
    mult = 2.4 + floor / 45.0
    if kind == "crypt_boss":
        mult *= 2.25
    return mult


def _v03610_damage_mult(kind, floor):
    floor = max(1, int(floor))
    if kind.startswith("mythic_"):
        mult = 2.0 + floor / 180.0
        if kind == "mythic_boss":
            mult *= 1.35
        return mult
    mult = 1.45 + floor / 250.0
    if kind == "crypt_boss":
        mult *= 1.35
    return mult


def _v03610_xp_mult(kind, floor):
    floor = max(1, int(floor))
    start, divisor = V03610_CRYPT_BASE_XP[kind]
    return float(start) + floor / float(divisor)


# Bypass the old v0.36.8 Crypt multiplier, but keep the canonical Generator Core
# refresh that v0.36.8 captured before wrapping it. This prevents multiplier
# stacking on respawn and makes the function idempotent.
def _v03610_apply_crypt_threat(template):
    kind = _v03610_kind(template)
    if kind is None:
        return template
    floor = _v03610_floor(template)

    # Canonical values are already in template at this point. Add a floor-linear
    # term after multiplication so integer rounding can NEVER make two adjacent
    # floors equal when the canonical value itself is non-decreasing.
    hp_mult = _v03610_hp_mult(kind, floor)
    dmg_mult = _v03610_damage_mult(kind, floor)

    hp = max(1, int(round(int(template.get("max_hp", 1) or 1) * hp_mult)))
    dmg = max(1, int(round(int(template.get("damage", 1) or 1) * dmg_mult)))

    # Strict per-floor component. Mythic gets a larger absolute floor term.
    if kind.startswith("mythic_"):
        hp += floor * (220 if kind == "mythic_regular" else 900)
        dmg += floor * (2 if kind == "mythic_regular" else 4)
    else:
        hp += floor * (45 if kind == "crypt_regular" else 220)
        dmg += floor
        if kind == "crypt_boss":
            dmg += floor

    # Concrete named UOSSMUD Superboss profiles retain individual identity.
    if kind == "mythic_boss" and template.get("uoss_superboss") and "uoss_superboss_profile_v0366" in globals():
        try:
            profile = uoss_superboss_profile_v0366("mythic_crypt", floor)
            hp = max(1, int(round(hp * float(profile.get("hp", 1.0) or 1.0))))
            dmg = max(1, int(round(dmg * float(profile.get("damage", 1.0) or 1.0))))
        except Exception:
            pass

    template["max_hp"] = hp
    template["base_max_hp"] = hp
    template["damage"] = dmg
    template["crypt_floor_progression_v03610"] = True
    template["crypt_floor_hp_mult_v03610"] = round(float(hp_mult), 6)
    template["crypt_floor_damage_mult_v03610"] = round(float(dmg_mult), 6)
    return template


# v0.36.8 kept the pre-Crypt canonical refresher in this symbol. Use it directly
# to replace, not stack, its old capped difficulty layer.
_v03610_canonical_combat_refresh = _v0190_apply_combat_template_before_v0368


def v0190_apply_combat_template(template):
    result = _v03610_canonical_combat_refresh(template)
    return _v03610_apply_crypt_threat(result)


# Replace the old fixed x2/x3/x3/x5 reward layer with a floor-by-floor curve.
_v03610_base_combat_reward = _v0190_combat_reward_before_v0368


def v0190_combat_reward(template, kind):
    base = int(_v03610_base_combat_reward(template, kind))
    if str(kind) == "coins":
        return base
    crypt_kind = _v03610_kind(template)
    if crypt_kind is None:
        return base
    floor = _v03610_floor(template)
    mult = _v03610_xp_mult(crypt_kind, floor)
    # +floor guarantees strict growth even if a rounded canonical reward happens
    # to remain unchanged between two adjacent generated stages.
    floor_bonus = floor * (3 if crypt_kind.startswith("mythic_") else 1)
    if crypt_kind.endswith("boss"):
        floor_bonus *= 4
    return min(V019_SAFE_INT, max(0, int(round(base * mult)) + floor_bonus))


# Rebuild every already-created Crypt template through the FINAL function.
for _v03610_tid, _v03610_template in list(MOB_TEMPLATES.items()):
    if _v03610_kind(_v03610_template):
        v0190_apply_combat_template(_v03610_template)


# The v0.36.8 lazy-floor wrapper resolves v0190_apply_combat_template globally,
# so floors 201+ automatically use this v0.36.10 curve as they are generated.

HELP_TOPICS.setdefault("krypta", []).extend([
    "v0.36.10: trudność Krypty rośnie od piętra 1 na KAŻDYM kolejnym piętrze. Nie ma płaskich przedziałów: 2 jest mocniejsze od 1, 3 od 2 itd.",
    "Na każdym piętrze rosną HP, obrażenia oraz Class/Soul/stat EXP. Boss co 10 pięter pozostaje dodatkowym skokiem ponad ciągły wzrost.",
    "Mityczna Krypta korzysta z tej samej zasady per-piętro, ale ma znacznie wyższą krzywą trudności i EXP. Skalowanie trwa także ponad 600 w nieskończonej części lochu.",
])


def crypt_every_floor_progression_audit_v03610():
    errors = []

    # Closed-form guards: all balance multipliers must strictly increase at
    # every floor from 1 through 600, for both ordinary and Mythic regular mobs.
    for kind in ("crypt_regular", "mythic_regular"):
        hp_vals = [_v03610_hp_mult(kind, f) for f in range(1, 601)]
        dmg_vals = [_v03610_damage_mult(kind, f) for f in range(1, 601)]
        xp_vals = [_v03610_xp_mult(kind, f) for f in range(1, 601)]
        if any(b <= a for a, b in zip(hp_vals, hp_vals[1:])):
            errors.append(f"{kind}: HP multiplier not strictly increasing every floor")
        if any(b <= a for a, b in zip(dmg_vals, dmg_vals[1:])):
            errors.append(f"{kind}: damage multiplier not strictly increasing every floor")
        if any(b <= a for a, b in zip(xp_vals, xp_vals[1:])):
            errors.append(f"{kind}: XP multiplier not strictly increasing every floor")

    # Real static templates 1..200 must also be strictly increasing in their
    # final runtime HP, damage and Class XP on EVERY floor.
    for prefix, label in (("crypt_floor_mob_", "crypt"), ("mythic_crypt_mob_", "mythic")):
        previous = None
        for floor in range(1, 201):
            t = MOB_TEMPLATES.get(prefix + str(floor))
            if not isinstance(t, dict):
                errors.append(f"{label}: missing regular floor {floor}")
                continue
            row = (
                int(t.get("max_hp", 0) or 0),
                int(t.get("damage", 0) or 0),
                int(v0190_combat_reward(t, "class")),
            )
            if previous is not None:
                for idx, field in enumerate(("HP", "damage", "Class XP")):
                    if row[idx] <= previous[idx]:
                        errors.append(
                            f"{label}: floor {floor} {field}={row[idx]} not above floor {floor-1}={previous[idx]}"
                        )
            previous = row

    # Boss spikes: every static boss must beat the regular mob on its floor.
    for floor in range(10, 201, 10):
        for boss_prefix, reg_prefix, label in (
            ("crypt_boss_", "crypt_floor_mob_", "crypt"),
            ("mythic_crypt_boss_", "mythic_crypt_mob_", "mythic"),
        ):
            boss = MOB_TEMPLATES.get(boss_prefix + str(floor))
            reg = MOB_TEMPLATES.get(reg_prefix + str(floor))
            if not isinstance(boss, dict) or not isinstance(reg, dict):
                errors.append(f"{label}: missing boss checkpoint {floor}")
                continue
            if int(boss.get("max_hp", 0) or 0) <= int(reg.get("max_hp", 0) or 0):
                errors.append(f"{label}: boss {floor} HP not above regular")
            if int(v0190_combat_reward(boss, "class")) <= int(v0190_combat_reward(reg, "class")):
                errors.append(f"{label}: boss {floor} XP not above regular")

    return {
        "version": "0.36.10",
        "floors_checked_per_dungeon": 200,
        "curve_guard_to_floor": 600,
        "error_count": len(errors),
        "errors": errors,
    }


CRYPT_EVERY_FLOOR_PROGRESSION_AUDIT_V03610 = crypt_every_floor_progression_audit_v03610()
if CRYPT_EVERY_FLOOR_PROGRESSION_AUDIT_V03610["error_count"]:
    raise RuntimeError(
        "Crypt Every-Floor Progression Audit v0.36.10 failed: "
        + "; ".join(CRYPT_EVERY_FLOOR_PROGRESSION_AUDIT_V03610["errors"][:100])
    )

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.36.10: Krypty rosną w trudności i EXP na każdym piętrze od 1; bossowie co 10 pozostają dodatkowymi skokami."
)
LATEST_CHANGES_TITLE = "Soulbound v0.36.10 - Every Crypt Floor Is Harder"
LATEST_CHANGES = [
    "Zwykła Krypta rośnie w HP, obrażeniach i EXP na każdym piętrze od 1, bez płaskich przedziałów.",
    "Mityczna Krypta ma osobną, wyższą ciągłą krzywą i również rośnie na każdym piętrze.",
    "Bossowie co 10 pięter są dodatkowymi skokami ponad zwykły ciągły wzrost.",
    "Skalowanie nie zatrzymuje się na 200 ani 600; nieskończone lazy-generated piętra zachowują wzrost przez numer piętra.",
    "Zachowano wszystkie wcześniejsze zmiany, w tym same-room dungeon exit podczas walki i lokalne komunikaty Soul Tier."
]
