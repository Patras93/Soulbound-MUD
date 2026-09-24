# -*- coding: utf-8 -*-
"""Soulbound v0.61.6 - Memory Efficiency II.

Final, post-audit runtime compaction.  This module only defines the compactor;
server.py invokes it after validation so authoring/audit structures stay intact.
Gameplay values are preserved 1:1.
"""
from __future__ import annotations

from data.catalogs import ITEMS, MOB_TEMPLATES

import gc

V0616_MEMORY_EFFICIENCY_VERSION = "0.61.6"

# These fields are startup/audit metadata for ordinary class-shop equipment.
# Runtime code either does not read them or already has the exact fallback noted
# below.  They are removed only after all startup audits have completed.
_CLASS_SHOP_DEAD_FIELDS_V0616 = (
    "class_base_stat_pair",      # no runtime readers
    "class_equipment_tier",     # Generator/audit-only after startup
    "class_equipment_style",    # HELP/audit-only after startup
    "class_set_piece",          # runtime falls back to slot
)


def _rebuild_mapping_in_place(mapping: dict, rows: dict) -> None:
    """Rebuild a dict without replacing its identity, allowing CPython to shrink it."""
    mapping.clear()
    mapping.update(rows)


def compact_runtime_memory_v0616():
    """Compact static runtime catalogs without changing gameplay-visible values.

    - identical corpse/material drop pools become shared immutable tuples;
    - ordinary class-shop EQ drops startup-only metadata and empty descriptions;
    - descriptions already covered by item_runtime_description are discarded;
    - item alias lists are changed to immutable tuples after HELP has finalized.

    The function is idempotent and intentionally runs after startup validation.
    """
    pool_cache: dict[tuple[str, tuple], tuple] = {}
    pool_rows = 0
    pool_unique = 0

    for template in MOB_TEMPLATES.values():
        for field in ("corpse_material_pool", "corpse_equipment_pool"):
            value = template.get(field)
            if not isinstance(value, (list, tuple)):
                continue
            signature = tuple(value)
            key = (field, signature)
            shared = pool_cache.get(key)
            if shared is None:
                shared = signature
                pool_cache[key] = shared
                pool_unique += 1
            template[field] = shared
            pool_rows += 1

    class_items = 0
    class_fields_removed = 0
    lazy_descriptions_removed = 0
    alias_lists_frozen = 0

    for item_id, item in ITEMS.items():
        changed = False
        compacted = dict(item)

        is_plain_class_shop = bool(
            item.get("class_shop_item")
            and not item.get("legendary_set_loot")
            and not item.get("legendary_class_relic")
        )
        if is_plain_class_shop:
            class_items += 1
            for field in _CLASS_SHOP_DEAD_FIELDS_V0616:
                if field in compacted:
                    compacted.pop(field, None)
                    class_fields_removed += 1
                    changed = True
            # Empty description was reintroduced by older compatibility/audit layers;
            # item_runtime_description builds the same player-facing text on demand.
            if not str(compacted.get("desc") or "").strip() and "desc" in compacted:
                compacted.pop("desc", None)
                lazy_descriptions_removed += 1
                changed = True

        # v0.61.2 already has exact runtime builders for these generated descriptions.
        if (
            compacted.get("crypt_set_tier")
            and compacted.get("crypt_base_item") != item_id
            and "desc" in compacted
        ):
            compacted.pop("desc", None)
            lazy_descriptions_removed += 1
            changed = True
        if compacted.get("corpse_random_variant") and "desc" in compacted:
            compacted.pop("desc", None)
            lazy_descriptions_removed += 1
            changed = True

        aliases = compacted.get("aliases")
        if isinstance(aliases, list):
            compacted["aliases"] = tuple(aliases)
            alias_lists_frozen += 1
            changed = True

        if changed:
            _rebuild_mapping_in_place(item, compacted)

    # CPython may keep freed arenas in the process heap.  Railway runs Linux/glibc,
    # where malloc_trim can return those now-unused pages to the OS/cgroup.  This is
    # only a memory-release hint; unsupported platforms simply skip it.
    gc.collect()
    malloc_trimmed = False
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6")
        malloc_trimmed = bool(libc.malloc_trim(0))
    except Exception:
        malloc_trimmed = False

    result = {
        "version": V0616_MEMORY_EFFICIENCY_VERSION,
        "item_count": len(ITEMS),
        "mob_count": len(MOB_TEMPLATES),
        "class_items_compacted": class_items,
        "class_fields_removed": class_fields_removed,
        "lazy_descriptions_removed": lazy_descriptions_removed,
        "alias_lists_frozen": alias_lists_frozen,
        "pool_rows_compacted": pool_rows,
        "pool_unique_objects": pool_unique,
        "malloc_trimmed": malloc_trimmed,
    }
    return result


def memory_efficiency_ii_audit_v0616(*, require_compacted: bool = False):
    errors = []
    plain_class = [
        (iid, item) for iid, item in ITEMS.items()
        if item.get("class_shop_item")
        and not item.get("legendary_set_loot")
        and not item.get("legendary_class_relic")
    ]
    if len(plain_class) < 30000:
        errors.append(f"unexpected plain class-shop EQ count: {len(plain_class)}")

    pool_rows = []
    for template in MOB_TEMPLATES.values():
        for field in ("corpse_material_pool", "corpse_equipment_pool"):
            value = template.get(field)
            if value is not None:
                pool_rows.append((field, value))
    if len(pool_rows) < 10000:
        errors.append(f"unexpected corpse pool row count: {len(pool_rows)}")

    if require_compacted:
        for iid, item in plain_class:
            stale = [field for field in _CLASS_SHOP_DEAD_FIELDS_V0616 if field in item]
            if stale:
                errors.append(f"{iid}: startup-only fields survived compaction: {stale}")
                if len(errors) >= 20:
                    break
            if "desc" in item and not str(item.get("desc") or "").strip():
                errors.append(f"{iid}: empty eager description survived compaction")
                if len(errors) >= 20:
                    break
        for field, value in pool_rows:
            if not isinstance(value, tuple):
                errors.append(f"{field}: pool is not immutable/shared tuple after compaction")
                if len(errors) >= 20:
                    break
        unique_ids = len({id(value) for _field, value in pool_rows})
        unique_content = len({(_field, tuple(value)) for _field, value in pool_rows})
        if unique_ids != unique_content:
            errors.append(
                f"pool interning incomplete: {unique_ids} objects for {unique_content} unique contents"
            )

    return {
        "version": V0616_MEMORY_EFFICIENCY_VERSION,
        "require_compacted": bool(require_compacted),
        "class_item_count": len(plain_class),
        "pool_row_count": len(pool_rows),
        "error_count": len(errors),
        "errors": errors,
    }


V0616_MEMORY_EFFICIENCY_AUDIT = memory_efficiency_ii_audit_v0616(require_compacted=False)
if V0616_MEMORY_EFFICIENCY_AUDIT["error_count"]:
    raise RuntimeError(
        "Memory Efficiency II Audit v0.61.6 failed: "
        + "; ".join(V0616_MEMORY_EFFICIENCY_AUDIT["errors"][:100])
    )

__all__ = [
    "V0616_MEMORY_EFFICIENCY_VERSION",
    "compact_runtime_memory_v0616",
    "memory_efficiency_ii_audit_v0616",
    "V0616_MEMORY_EFFICIENCY_AUDIT",
]
