# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def _build_collection_v2_groups():
    class_groups = {name: set() for name in CLASS_EQUIPMENT_SETS}
    legendary_groups = {name: set() for name in CLASS_EQUIPMENT_SETS}
    legendary_groups["Ogólne"] = set()
    material_groups = {tier["key"]: set() for tier in CORPSE_MATERIAL_TIERS}
    set_groups = {}
    set_names = {}
    for item_id, item in ITEMS.items():
        if item.get("type") not in ("armor", "weapon"):
            continue
        req_class = str(item.get("required_class") or "")
        if req_class in class_groups:
            class_groups[req_class].add(item_id)
        if (
            str(item.get("rarity", "")).lower() == "legendary"
            or item.get("legendary_set_loot")
            or item.get("legendary_class_relic")
        ):
            legendary_groups[req_class if req_class in CLASS_EQUIPMENT_SETS else "Ogólne"].add(item_id)
        material = str(item.get("corpse_material") or item.get("blacksmith_material") or "")
        if material in material_groups:
            material_groups[material].add(item_id)

        group_id = None
        group_name = None
        if item.get("class_set_name"):
            mastery = int(item.get("required_mastery", 1) or 1)
            group_id = f"class:{req_class}:{item.get('class_set_name')}:{mastery}"
            group_name = f"{item.get('class_set_name')} — {req_class}, Biegłość {mastery}"
        elif item.get("regional_set"):
            sid = str(item["regional_set"])
            group_id = f"regional:{sid}"
            group_name = REGIONAL_SET_BONUSES.get(sid, {}).get("name", f"Set regionalny {sid}")
        elif item.get("crypt_set_tier"):
            tier = int(item["crypt_set_tier"])
            group_id = f"crypt:{tier}"
            group_name = f"Zestaw Krypty Tier {tier}"
        elif item.get("astral_set_tier"):
            tier = int(item["astral_set_tier"])
            group_id = f"astral:{tier}"
            group_name = f"Astralny Zestaw Kręgu {tier}"
        if group_id:
            set_groups.setdefault(group_id, set()).add(item_id)
            set_names[group_id] = group_name
    return (
        {k: frozenset(v) for k, v in class_groups.items()},
        {k: frozenset(v) for k, v in legendary_groups.items()},
        {k: frozenset(v) for k, v in material_groups.items()},
        {k: frozenset(v) for k, v in set_groups.items()},
        set_names,
    )

