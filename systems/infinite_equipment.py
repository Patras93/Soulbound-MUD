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
from core.equipment_growth_v5300 import infinite_equipment_requirement


INFINITE_EQUIPMENT_VERSION = "1.13.30"
INFINITE_EQUIPMENT_BASE_STAGE = 600
INFINITE_EQUIPMENT_STAGE_STEP = 10

_SOURCE_LABELS = {
    "crypt": "Krypta Nieskonczona",
    "mythiccrypt": "Mityczna Krypta",
    "tower": "Wieza Astralna",
    "mythictower": "Mityczna Wieza Astralna",
    "magitek": "Nieskonczony Kompleks Magitek",
    "forge": "Rzemioslo Mistrzow",
    "world": "Potwory i Bossowie Swiata",
    "quest": "Nagroda wysokopoziomowego questa",
    "shop": "Oferta sklepu kontrolowana przez Admin Live",
}
_GRADE_LABELS = {
    "r": "zwykly",
    "e": "elitarny",
    "b": "boss",
}
_DEEP_ID_RE = re.compile(
    r"^deepq_(crypt|mythiccrypt|tower|mythictower|magitek|forge|world|quest|shop)_([reb])_r([1-9]\d*)_(.+)$"
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
        # Existing authored formula, but without its player-facing cap.
        raw_stage = 110 + floor * 7
    elif template.get("mythic_crypt_floor") is not None:
        try:
            floor = max(1, int(template.get("mythic_crypt_floor") or 1))
        except (TypeError, ValueError, OverflowError):
            floor = 1
        source = "mythiccrypt"
        # Extend the existing mythic Crypt gear formula:
        # tier = 20 + (floor-1)//10, required mastery = tier*10.
        raw_stage = max(200, (20 + (floor - 1) // 10) * 10)
    elif template.get("mythic_astral_floor") is not None:
        try:
            floor = max(1, int(template.get("mythic_astral_floor") or 1))
        except (TypeError, ValueError, OverflowError):
            floor = 1
        source = "mythictower"
        # Mythic Astral uses the highest ordinary Astral gear as its baseline.
        # Continue from effective stage 200 by +10 every 10 mythic floors.
        raw_stage = 200 + max(0, (floor - 1) // 10) * 10
    elif template.get("crypt_floor") is not None:
        try:
            floor = max(1, int(template.get("crypt_floor") or 1))
        except (TypeError, ValueError, OverflowError):
            floor = 1
        source = "crypt"
        # Existing Crypt gear is one tier per 10 floors, tier*10 mastery.
        raw_stage = max(10, ((floor - 1) // 10 + 1) * 10)
    elif template.get("astral_floor") is not None:
        try:
            floor = max(1, int(template.get("astral_floor") or 1))
        except (TypeError, ValueError, OverflowError):
            floor = 1
        source = "tower"
        # Ordinary Astral starts at floor/mastery 100 and advances one gear
        # circle every 10 floors: 100..109 => 100, 110..119 => 110, etc.
        raw_stage = 100 + max(0, (floor - 100) // 10) * 10
    elif template.get("level") is not None or template.get("generator_level") is not None:
        # v59: ordinary high-level world mobs/elite/bosses only. Existing
        # loot tables remain the sole source of drops; no extra RNG rolls.
        # Skip malformed/out-of-range levels instead of treating them as 801+.
        value=template.get("level", template.get("generator_level"))
        if isinstance(value,bool):return None
        try:
            raw_stage=int(value)
        except (TypeError,ValueError,OverflowError):return None
        if not 801<=raw_stage<=1_000_000_000:return None
        source="world"
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


def _v53_refresh_requirement_description(item, requirement):
    desc=str(item.get('desc') or '')
    # Both historical v1.13 and newly generated v53 Rezonans descriptions.
    desc=re.sub(r'Wymaganie założenia wynosi Biegłość 600 \(próg wariantu Rezonansu Głębi\);',
                f'Wymaganie założenia: Biegłość {requirement}.',desc)
    desc=re.sub(r'Wymaganie założenia: Biegłość \d+\.',
                f'Wymaganie założenia: Biegłość {requirement}.',desc)
    desc=desc.replace('głębokość wzmacnia egzemplarz, ale Biegłość klasy nadal rozwija się do 800.',
                      'Poziom Biegłości jest konfigurowany przez admin live.')
    item['desc']=desc


def refresh_infinite_equipment_requirements_v5300():
    """Update only staged eligibility fields for already built Rezonans items."""
    count=0
    for item in ITEMS.values():
        if not isinstance(item,dict) or not item.get('infinite_depth_variant'):
            continue
        stage=int(item.get('source_progression_stage') or 600)
        # Forge variants need their authored proficiency even when limits later
        # decrease; no downgrade that lets an inexperienced player equip them.
        req=(stage if item.get('infinite_depth_source')=='forge'
             else infinite_equipment_requirement(stage))
        item['required_mastery']=req
        _v53_refresh_requirement_description(item,req)
        if 'required_character_level' in item:
            item['required_character_level']=req
        count+=1
    return count


def shop_variant_price_v7003(base_item_id, rank):
    """Deterministic silver price; stays stable on inventory restoration."""
    from core.bootstrap_economy_professions import V019_SAFE_INT
    from core.progression_resources import v0190_economy_sink
    from systems.legacy_value_sweep import shop_money_price_v11325
    base = ITEMS.get(str(base_item_id))
    if not isinstance(base, dict):
        raise ValueError('Nieznany bazowy przedmiot wariantu sklepowego.')
    rank = max(1, int(rank))
    full_stage = 600 + rank * 10
    original = shop_money_price_v11325(base)
    return min(V019_SAFE_INT//100, max(
        1000, original * (20 + rank * 10),
        v0190_economy_sink(min(1000000, full_stage), 'equipment'),
    ))


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
        old=ITEMS.get(vid)
        if isinstance(old,dict) and old.get('infinite_depth_variant'):
            req=(int(old.get('source_progression_stage',600)) if source=='forge'
                 else infinite_equipment_requirement(old.get('source_progression_stage',600)))
            old['required_mastery']=req
            _v53_refresh_requirement_description(old,req)
            if 'required_character_level' in old:old['required_character_level']=req
            if source == 'shop':
                old['currency']='silver'
                old['price']=shop_variant_price_v7003(base_item_id,rank)
                old['shop_tier_v7003']=True
        return vid

    base = ITEMS.get(base_item_id)
    if base is None and base_item_id.startswith('craftq_'):
        # An item may only exist inside a deepq_forge ID in SQLite. Restore
        # its crafted quality first; keep this lazy to avoid import cycles.
        from systems.crafting_quality import ensure_crafting_quality_variant_v0332
        base = ensure_crafting_quality_variant_v0332(base_item_id)
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
        f"Wymaganie założenia: Biegłość {effective_stage if source=='forge' else infinite_equipment_requirement(effective_stage)}. "
        + ("Wymaganie tego rzemieślniczego przedmiotu jest trwałe."
         if source=="forge" else "Wymaganie rośnie przy rozszerzeniu limitu EQ i Biegłości w admin live.")
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

    # At default 800 retain the historical 600 gate. When the owner raises EQ
    # cap, stage unlocks real mastery requirements up to attainable class cap.
    # Do not give low-level characters access via a stale character gate.
    mastery_requirement=(effective_stage if source=='forge' else infinite_equipment_requirement(effective_stage))
    data["required_mastery"] = mastery_requirement
    if 'required_character_level' in data:
        data['required_character_level'] = mastery_requirement
    data.setdefault("mastery_requirement_scope", "active_class")
    data["price"] = base.get("price")
    if source == "shop":
        # Inventory restoration must NOT depend on shop configuration: the
        # user can keep an acquired item after the admin disables the vendor.
        data['currency'] = 'silver'
        data['price'] = shop_variant_price_v7003(base_item_id,rank)
        data['shop_tier_v7003'] = True
    _catalog_mut.catalog_assign(data, "ITEMS", ITEMS, (vid,))
    return vid


def ensure_infinite_equipment_variant(item_id):
    """Rebuild a persisted Rezonans Głębi item after restart/deploy."""
    item_id = str(item_id or "")
    if item_id in ITEMS:
        return ITEMS[item_id]
    parsed = parse_infinite_equipment_variant(item_id)
    if not parsed:
        return None
    if parsed["base_id"] not in ITEMS and parsed["base_id"].startswith('craftq_'):
        from systems.crafting_quality import ensure_crafting_quality_variant_v0332
        ensure_crafting_quality_variant_v0332(parsed["base_id"])
    if parsed["base_id"] not in ITEMS:
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
    if base_item_id.startswith('uoss_'):
        return base_item_id
    _base = ITEMS.get(base_item_id, {})
    if isinstance(_base, dict) and (_base.get('fur_shop_token') or _base.get('uoss_unique') or _base.get('uoss_superboss_id')):
        return base_item_id
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
        ({"mythic_crypt_floor": 401}, False),
        ({"mythic_crypt_floor": 411}, True),
        ({"astral_floor": 600}, False),
        ({"astral_floor": 610}, True),
        ({"mythic_astral_floor": 401}, False),
        ({"mythic_astral_floor": 411}, True),
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
        for floor in (601, 611, 651, 701, 851, 1201)
    ]
    if any(b <= a for a, b in zip(coin_factors, coin_factors[1:])):
        errors.append("infinite coin multiplier is not strictly increasing")

    # Pure self-describing-ID/mechanical checks. Runtime diagnostics must not
    # mutate the global ITEMS catalog, even temporarily.
    test_base_id = "audit_base_item"
    test_variant_id = infinite_equipment_variant_id(
        test_base_id, "crypt", "b", 10
    )
    parsed = parse_infinite_equipment_variant(test_variant_id)
    if not parsed or parsed.get("base_id") != test_base_id:
        errors.append("deep variant ID is not self-describing")
    elif int(parsed.get("effective_stage", 0) or 0) != 700:
        errors.append("deep variant parsed source stage is not 700")

    test_mult = infinite_equipment_power_multiplier(10, "b")
    if _scale_positive_int(100, test_mult) <= 100:
        errors.append("deep variant mechanical scaling is not positive")

    return {
        "version": INFINITE_EQUIPMENT_VERSION,
        "boundary_count": len(boundary_cases),
        "error_count": len(errors),
        "errors": errors,
    }


INFINITE_EQUIPMENT_AUDIT_V11330 = infinite_equipment_audit_v11330()
