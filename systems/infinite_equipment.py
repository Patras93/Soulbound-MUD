# -*- coding: utf-8 -*-
"""Post-600 equipment progression for Soulbound infinite instances.

Character/Class/Soul/profession progression remains capped at the authored
1-600 axes. Infinite content can nevertheless have an uncapped source stage.
When an equipment item drops from a source above effective stage 600, this
module creates a stable self-describing "Rezonans Glebi" variant whose power
continues to grow with depth without introducing impossible 601+ equip gates.
"""
from __future__ import annotations

import copy
import math
import re

from data import catalog_mutations as _catalog_mut
from data.items import ITEMS


INFINITE_EQUIPMENT_VERSION = "1.13.30"
INFINITE_EQUIPMENT_BASE_STAGE = 600
INFINITE_EQUIPMENT_STAGE_STEP = 10

_SOURCE_LABELS = {
    "crypt": "Krypta Nieskonczona",
    "mythiccrypt": "Mityczna Krypta",
    "tower": "Wieza Astralna",
    "mythictower": "Mityczna Wieza Astralna",
    "magitek": "Nieskonczony Kompleks Magitek",
}
_GRADE_LABELS = {
    "r": "zwykly",
    "e": "elitarny",
    "b": "boss",
}
_DEEP_ID_RE = re.compile(
    r"^deepq_(crypt|mythiccrypt|tower|mythictower|magitek)_([reb])_r([1-9]\d*)_(.+)$"
)


def infinite_source_profile(template):
    """Return uncapped source stage metadata for supported infinite content."""
    template = template or {}
    if not isinstance(template, dict):
        return None

    # UOSS rewards have their own handcrafted token/unique economy and must
    # never be converted into generic infinite-depth variants.
    if (
        template.get("uoss_superboss")
        or template.get("uoss_superboss_id")
        or template.get("uoss_unique")
    ):
        return None

    source = None
    raw_stage = 0

    if template.get("magitek_infinite") or template.get("magitek_floor") is not None:
        try:
            floor = max(1, int(template.get("magitek_floor") or 1))
        except (TypeError, ValueError, OverflowError):
            floor = 1
        source = "magitek"
        # The authored Magitek stage is 110 + floor*7, currently clamped to 600
        # for player-facing mastery. Here we deliberately retain the uncapped
        # source strength used only for reward quality.
        raw_stage = 110 + floor * 7
    elif template.get("mythic_crypt_floor") is not None:
        try:
            floor = max(1, int(template.get("mythic_crypt_floor") or 1))
        except (TypeError, ValueError, OverflowError):
            floor = 1
        source = "mythiccrypt"
        # Static floors 1..200 map naturally to source stages 401..600.
        raw_stage = 400 + floor
    elif template.get("mythic_astral_floor") is not None:
        try:
            floor = max(1, int(template.get("mythic_astral_floor") or 1))
        except (TypeError, ValueError, OverflowError):
            floor = 1
        source = "mythictower"
        raw_stage = 400 + floor
    elif template.get("crypt_floor") is not None:
        try:
            floor = max(1, int(template.get("crypt_floor") or 1))
        except (TypeError, ValueError, OverflowError):
            floor = 1
        source = "crypt"
        raw_stage = floor
    elif template.get("astral_floor") is not None:
        try:
            floor = max(1, int(template.get("astral_floor") or 1))
        except (TypeError, ValueError, OverflowError):
            floor = 1
        source = "tower"
        raw_stage = floor
    else:
        return None

    if raw_stage <= INFINITE_EQUIPMENT_BASE_STAGE:
        return None

    rank = max(
        1,
        int(math.ceil(
            (raw_stage - INFINITE_EQUIPMENT_BASE_STAGE)
            / float(INFINITE_EQUIPMENT_STAGE_STEP)
        )),
    )
    effective_stage = (
        INFINITE_EQUIPMENT_BASE_STAGE
        + rank * INFINITE_EQUIPMENT_STAGE_STEP
    )

    raw_rank = str(template.get("rank") or "").strip().lower()
    boss = bool(
        template.get("boss")
        or template.get("crypt_boss")
        or template.get("mythic_crypt_boss")
        or template.get("astral_boss")
        or template.get("mythic_astral_boss")
        or template.get("magitek_boss")
        or raw_rank in {"boss", "world_boss", "worldboss", "mini_boss", "miniboss"}
    )
    elite = bool(
        template.get("elite")
        or template.get("rare_mob")
        or raw_rank in {"elite", "rare"}
    )
    grade = "b" if boss else ("e" if elite else "r")

    return {
        "source": source,
        "raw_stage": int(raw_stage),
        "rank": int(rank),
        "effective_stage": int(effective_stage),
        "grade": grade,
    }


def infinite_equipment_power_multiplier(rank, grade="r"):
    """Gentle endless power curve; monotonic but intentionally sub-linear."""
    rank = max(1, int(rank or 1))
    grade = str(grade or "r")
    grade_bonus = {"r": 0.00, "e": 0.05, "b": 0.12}.get(grade, 0.00)
    return 1.0 + 0.035 * (rank ** 0.82) + grade_bonus


def infinite_coin_multiplier(template):
    """Post-600 coin continuation for sources whose base currency is capped.

    Infinite Magitek already authors an uncapped silver value from floor/depth,
    so it intentionally receives no second multiplier here.
    """
    profile = infinite_source_profile(template)
    if not profile or profile["source"] == "magitek":
        return 1.0
    rank = int(profile["rank"])
    return 1.0 + 0.018 * (rank ** 0.82)


def infinite_equipment_variant_id(base_item_id, source, grade, rank):
    return f"deepq_{source}_{grade}_r{max(1, int(rank))}_{base_item_id}"


def parse_infinite_equipment_variant(item_id):
    raw = str(item_id or "")
    match = _DEEP_ID_RE.fullmatch(raw)
    if not match:
        return None
    source, grade, rank, base_id = match.groups()
    if not base_id:
        return None
    return {
        "source": source,
        "grade": grade,
        "rank": int(rank),
        "base_id": base_id,
        "effective_stage": (
            INFINITE_EQUIPMENT_BASE_STAGE
            + int(rank) * INFINITE_EQUIPMENT_STAGE_STEP
        ),
    }


def _scale_positive_int(value, multiplier):
    try:
        base = int(value or 0)
    except (TypeError, ValueError, OverflowError):
        return value
    if base <= 0:
        return base
    return max(base + 1, int(round(base * float(multiplier))))


def _scale_numeric_mapping(values, multiplier, *, decimals=None):
    result = dict(values or {})
    for key, value in list(result.items()):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        if value == 0:
            continue
        scaled = float(value) * float(multiplier)
        if isinstance(value, int):
            result[key] = (
                max(int(value) + 1, int(round(scaled)))
                if value > 0
                else min(int(value) - 1, int(round(scaled)))
            )
        else:
            result[key] = round(scaled, decimals if decimals is not None else 4)
    return result


def register_infinite_equipment_variant(
    base_item_id, source, grade, rank, *, variant_id=None
):
    """Create/rebuild a stable post-600 equipment variant."""
    base_item_id = str(base_item_id or "")
    source = str(source or "")
    grade = str(grade or "r")
    rank = max(1, int(rank or 1))
    if source not in _SOURCE_LABELS or grade not in _GRADE_LABELS:
        return base_item_id

    vid = str(
        variant_id
        or infinite_equipment_variant_id(base_item_id, source, grade, rank)
    )
    if vid in ITEMS:
        return vid

    base = ITEMS.get(base_item_id)
    if not isinstance(base, dict):
        return base_item_id
    if (
        base.get("type") not in {"armor", "weapon", "equipment"}
        and not base.get("slot")
    ):
        return base_item_id

    data = copy.deepcopy(base)
    multiplier = infinite_equipment_power_multiplier(rank, grade)
    effective_stage = (
        INFINITE_EQUIPMENT_BASE_STAGE
        + rank * INFINITE_EQUIPMENT_STAGE_STEP
    )

    for key in (
        "defense", "attack", "magic_attack", "power",
        "damage", "min_damage", "max_damage", "affix_amount",
    ):
        if key in data:
            data[key] = _scale_positive_int(data.get(key), multiplier)

    if isinstance(data.get("stats"), dict):
        data["stats"] = _scale_numeric_mapping(
            data.get("stats"), multiplier
        )
    if isinstance(data.get("properties"), dict):
        data["properties"] = _scale_numeric_mapping(
            data.get("properties"), multiplier, decimals=3
        )

    base_sockets = max(0, int(data.get("sockets", 0) or 0))
    socket_bonus = min(2, rank // 25)
    if grade == "b":
        socket_bonus = max(1, socket_bonus)
    data["sockets"] = min(6, base_sockets + socket_bonus)

    base_name = str(base.get("name") or base_item_id)
    grade_suffix = ", Boss" if grade == "b" else (", Elite" if grade == "e" else "")
    data["name"] = f"{base_name} [Rezonans Głębi {rank}{grade_suffix}]"

    old_desc = str(base.get("desc") or "").strip()
    source_label = _SOURCE_LABELS[source]
    deep_desc = (
        f"Rezonans Głębi {rank}: źródło {source_label}, "
        f"efektywny etap {effective_stage}. "
        "Wymaganie założenia pozostaje w normalnej progresji 1-600; "
        "głębokość wzmacnia egzemplarz, nie podnosi limitu Biegłości."
    )
    data["desc"] = (old_desc + " " + deep_desc).strip()

    previous_identity = str(data.get("equipment_identity_label") or "").strip()
    deep_identity = (
        f"Rezonans Głębi {rank} — {_SOURCE_LABELS[source]}, "
        f"etap źródła {effective_stage}"
    )
    data["equipment_identity_label"] = (
        previous_identity + " | " + deep_identity
        if previous_identity else deep_identity
    )

    data["infinite_depth_variant"] = True
    data["infinite_depth_base_item_id"] = base_item_id
    data["infinite_depth_source"] = source
    data["infinite_depth_grade"] = grade
    data["infinite_depth_rank"] = rank
    data["infinite_depth_power_multiplier"] = round(multiplier, 6)
    data["source_progression_stage"] = effective_stage

    # Critically: never invent required_mastery > 600. The copy preserves the
    # base item's existing equip requirements exactly.
    data["price"] = base.get("price")
    _catalog_mut.catalog_assign(data, "ITEMS", ITEMS, (vid,))
    return vid


def ensure_infinite_equipment_variant(item_id):
    """Rebuild a persisted Rezonans Głębi item after restart/deploy."""
    item_id = str(item_id or "")
    if item_id in ITEMS:
        return ITEMS[item_id]
    parsed = parse_infinite_equipment_variant(item_id)
    if not parsed or parsed["base_id"] not in ITEMS:
        return None
    register_infinite_equipment_variant(
        parsed["base_id"],
        parsed["source"],
        parsed["grade"],
        parsed["rank"],
        variant_id=item_id,
    )
    return ITEMS.get(item_id)


def infinite_equipment_variant_for_drop(base_item_id, template):
    """Upgrade an equipment drop only when its source is truly post-600."""
    base_item_id = str(base_item_id or "")
    if base_item_id.startswith("deepq_"):
        ensure_infinite_equipment_variant(base_item_id)
        return base_item_id

    profile = infinite_source_profile(template)
    if not profile:
        return base_item_id

    return register_infinite_equipment_variant(
        base_item_id,
        profile["source"],
        profile["grade"],
        profile["rank"],
    )


def infinite_equipment_audit_v11330():
    """Behavior audit; diagnostic only, never a production startup gate."""
    errors = []

    boundary_cases = (
        ({"crypt_floor": 600}, False),
        ({"crypt_floor": 601}, True),
        ({"mythic_crypt_floor": 200}, False),
        ({"mythic_crypt_floor": 201}, True),
        ({"astral_floor": 600}, False),
        ({"astral_floor": 601}, True),
        ({"mythic_astral_floor": 200}, False),
        ({"mythic_astral_floor": 201}, True),
        ({"magitek_floor": 70, "magitek_infinite": True}, False),
        ({"magitek_floor": 71, "magitek_infinite": True}, True),
    )
    for template, expected in boundary_cases:
        observed = infinite_source_profile(template) is not None
        if observed != expected:
            errors.append(
                f"boundary {template}: expected post600={expected}, got {observed}"
            )

    if infinite_source_profile(
        {"crypt_floor": 900, "uoss_superboss": True}
    ) is not None:
        errors.append("UOSS must never enter generic infinite equipment")

    factors = [
        infinite_equipment_power_multiplier(rank, "r")
        for rank in (1, 2, 5, 10, 25, 50, 100)
    ]
    if any(b <= a for a, b in zip(factors, factors[1:])):
        errors.append("power multiplier is not strictly increasing")

    coin_factors = [
        infinite_coin_multiplier({"crypt_floor": floor})
        for floor in (601, 610, 650, 700, 850, 1200)
    ]
    if any(b <= a for a, b in zip(coin_factors, coin_factors[1:])):
        errors.append("infinite coin multiplier is not strictly increasing")

    test_base_id = next(
        (
            item_id for item_id, item in ITEMS.items()
            if isinstance(item, dict)
            and (
                item.get("type") in {"armor", "weapon", "equipment"}
                or item.get("slot")
            )
            and any(
                isinstance(item.get(key), (int, float))
                and float(item.get(key) or 0) > 0
                for key in (
                    "defense", "attack", "magic_attack", "power",
                    "damage", "affix_amount",
                )
            )
        ),
        None,
    )
    test_variant_id = None
    if test_base_id:
        base = ITEMS[test_base_id]
        original_req = base.get("required_mastery")
        test_variant_id = register_infinite_equipment_variant(
            test_base_id, "crypt", "b", 10
        )
        variant = ITEMS.get(test_variant_id, {})
        if not variant.get("infinite_depth_variant"):
            errors.append("test deep variant was not registered")
        if int(variant.get("source_progression_stage", 0) or 0) != 700:
            errors.append("test deep variant source stage is not 700")
        if variant.get("required_mastery") != original_req:
            errors.append("deep variant changed equip mastery requirement")
        if str(variant.get("name") or "").find("Rezonans Głębi") < 0:
            errors.append("deep variant player name missing Rezonans Głębi")
        parsed = parse_infinite_equipment_variant(test_variant_id)
        if not parsed or parsed.get("base_id") != test_base_id:
            errors.append("deep variant ID is not self-describing")
        _catalog_mut.catalog_pop_path(
            "ITEMS", ITEMS, (), test_variant_id, None
        )
    else:
        errors.append("no mechanical equipment base available for audit")

    return {
        "version": INFINITE_EQUIPMENT_VERSION,
        "boundary_count": len(boundary_cases),
        "error_count": len(errors),
        "errors": errors,
    }


INFINITE_EQUIPMENT_AUDIT_V11330 = infinite_equipment_audit_v11330()
