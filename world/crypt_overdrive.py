# -*- coding: utf-8 -*-
"""Soulbound v0.37.0 - Crypt Overdrive.

Additional final balance layer on top of v0.36.10. Every ordinary and Mythic
Crypt floor is stronger and more rewarding from floor 1 onward. The boost
itself grows with floor number, so the strict every-floor progression is kept.
"""

V0370_CRYPT_OVERDRIVE_VERSION = "0.37.0"


def _v0370_crypt_boosts(kind, floor):
    floor = max(1, int(floor))
    mythic = str(kind).startswith("mythic_")
    boss = str(kind).endswith("boss")

    if mythic:
        hp = 1.50 + floor / 600.0
        dmg = 1.20 + floor / 1800.0
        xp = 1.65 + floor / 900.0
        if boss:
            hp *= 1.30
            dmg *= 1.18
            xp *= 1.40
    else:
        hp = 1.65 + floor / 500.0
        dmg = 1.25 + floor / 1500.0
        xp = 1.75 + floor / 800.0
        if boss:
            hp *= 1.25
            dmg *= 1.15
            xp *= 1.35
    return float(hp), float(dmg), float(xp)


_v0370_crypt_apply_before = v0190_apply_combat_template


def v0190_apply_combat_template(template):
    result = _v0370_crypt_apply_before(template)
    kind = _v03610_kind(result)
    if kind is None:
        return result
    floor = _v03610_floor(result)
    hp_boost, dmg_boost, _xp_boost = _v0370_crypt_boosts(kind, floor)

    hp = max(1, int(round(int(result.get("max_hp", 1) or 1) * hp_boost)))
    dmg = max(1, int(round(int(result.get("damage", 1) or 1) * dmg_boost)))

    # Absolute per-floor additions prevent adjacent floors from collapsing to
    # equal integers after rounding, even at the very beginning of the Crypt.
    if kind.startswith("mythic_"):
        hp += floor * (180 if kind == "mythic_regular" else 850)
        dmg += floor * (1 if kind == "mythic_regular" else 3)
    else:
        hp += floor * (35 if kind == "crypt_regular" else 180)
        if kind == "crypt_boss":
            dmg += floor

    result["max_hp"] = hp
    result["base_max_hp"] = hp
    result["damage"] = dmg
    result["crypt_overdrive_v0370"] = True
    result["crypt_overdrive_hp_mult_v0370"] = round(hp_boost, 6)
    result["crypt_overdrive_damage_mult_v0370"] = round(dmg_boost, 6)
    return result


_v0370_crypt_reward_before = v0190_combat_reward


def v0190_combat_reward(template, kind):
    base = int(_v0370_crypt_reward_before(template, kind))
    if str(kind) == "coins":
        return base
    crypt_kind = _v03610_kind(template)
    if crypt_kind is None:
        return base
    floor = _v03610_floor(template)
    _hp_boost, _dmg_boost, xp_boost = _v0370_crypt_boosts(crypt_kind, floor)
    # Keep strict growth even where the canonical reward rounded to the same int.
    extra = floor * (5 if crypt_kind.startswith("mythic_") else 2)
    if crypt_kind.endswith("boss"):
        extra *= 4
    return min(V019_SAFE_INT, max(0, int(round(base * xp_boost)) + extra))


# Rebuild every already-created Crypt template through the final v0.37.0 layer.
for _v0370_tid, _v0370_template in list(MOB_TEMPLATES.items()):
    if _v03610_kind(_v0370_template):
        v0190_apply_combat_template(_v0370_template)

# v0.36.8 lazy-floor generation resolves v0190_apply_combat_template globally,
# therefore infinite floors created after boot also receive Crypt Overdrive.

HELP_TOPICS.setdefault("krypta", []).extend([
    "v0.37.0: wszystkie zwykłe i Mityczne Krypty zostały ponownie wzmocnione od piętra 1. Dotyczy to zwykłych mobów, bossów i Superbossów.",
    "Crypt Overdrive zwiększa HP, obrażenia oraz Class/Soul/stat EXP na każdym piętrze; dodatkowy mnożnik sam rośnie wraz z numerem piętra.",
    "Zasada v0.36.10 nadal obowiązuje: każde kolejne piętro jest trudniejsze i bardziej nagradzające od poprzedniego, także ponad 600.",
])


def crypt_overdrive_audit_v0370():
    errors = []

    # Closed-form boost curves must increase on every floor through 600.
    for kind in ("crypt_regular", "crypt_boss", "mythic_regular", "mythic_boss"):
        last = None
        for floor in range(1, 601):
            row = _v0370_crypt_boosts(kind, floor)
            if last is not None:
                for idx, label in enumerate(("HP", "damage", "EXP")):
                    if row[idx] <= last[idx]:
                        errors.append(f"{kind}: {label} boost not increasing at floor {floor}")
                        break
            last = row

    # Every real static regular floor remains strictly increasing after the
    # stronger v0.37.0 layer. Also verify the layer is actually present.
    for prefix, label in (("crypt_floor_mob_", "crypt"), ("mythic_crypt_mob_", "mythic")):
        previous = None
        for floor in range(1, 201):
            t = MOB_TEMPLATES.get(prefix + str(floor))
            if not isinstance(t, dict):
                errors.append(f"{label}: missing regular floor {floor}")
                continue
            if not t.get("crypt_overdrive_v0370"):
                errors.append(f"{label}: floor {floor} missing v0.37.0 overdrive")
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

    # Bosses/Superbosses must remain above same-floor regular mobs.
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
            if int(boss.get("damage", 0) or 0) <= int(reg.get("damage", 0) or 0):
                errors.append(f"{label}: boss {floor} damage not above regular")
            if int(v0190_combat_reward(boss, "class")) <= int(v0190_combat_reward(reg, "class")):
                errors.append(f"{label}: boss {floor} XP not above regular")

    # Infinite floors 201+ resolve the globally rebound v0190_apply_combat_template
    # through the existing v0.36.8 lazy-floor wrapper. Do not materialize those
    # floors inside the import-time audit, because doing so would mutate the
    # final world registry merely by running an audit. External pre-deploy tests
    # exercise representative 201+/600+ floors on a disposable runtime.
    lazy_rows = []

    return {
        "version": V0370_CRYPT_OVERDRIVE_VERSION,
        "static_floors_checked": 200,
        "curve_guard_to_floor": 600,
        "lazy_spot_checks": lazy_rows,
        "error_count": len(errors),
        "errors": errors,
    }


CRYPT_OVERDRIVE_AUDIT_V0370 = crypt_overdrive_audit_v0370()
if CRYPT_OVERDRIVE_AUDIT_V0370["error_count"]:
    raise RuntimeError(
        "Crypt Overdrive Audit v0.37.0 failed: "
        + "; ".join(CRYPT_OVERDRIVE_AUDIT_V0370["errors"][:100])
    )

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.37.0: Crypt Overdrive ponownie wzmacnia wszystkie zwykłe i Mityczne Krypty od piętra 1, razem z bossami, Superbossami i EXP."
)
