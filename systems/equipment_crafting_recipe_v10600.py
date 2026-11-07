# -*- coding: utf-8 -*-
"""High-level recipe ingredient reservation for isolated v106 staging.

No SQL mutation happens here.  A single atomic inventory/storage + crafted
output transaction commits after the existing quality/yield calculations.
"""
from __future__ import annotations

from collections import defaultdict
from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
from systems.equipment_crafting_guard_v10600 import guard_recipe


def plan_recipe_ingredients(db, account_id, recipe, container_for_item):
    """Return (amounts, containers) or None when total stock is insufficient.

    Direct, distinct and pooled objectives compete for the same stock.  This
    reserves each item at most once, and never confuses available with unreserved
    quantity.  No mutable DB state is changed.  Caller must consume atomically.
    """
    guard_recipe(db, recipe)
    amounts = defaultdict(int)
    containers = {}

    def available(item):
        iid = str(item)
        if iid not in containers:
            container = container_for_item(iid)
            containers[iid] = container
        container = containers[iid]
        quantity = db.item_qty(account_id, iid)
        if container:
            quantity += db.storage_qty(account_id, container, iid)
        return require_sqlite_int64('v106.crafting.available', quantity)

    def add(item, quantity):
        iid = str(item)
        qty = require_sqlite_int64('v106.crafting.recipe_quantity', quantity)
        if not iid or qty <= 0:
            raise ValueError('v106: niedozwolony składnik lub ilość')
        new = require_sqlite_int64('v106.crafting.reserved', amounts[iid] + qty)
        if new > available(iid):
            return False
        amounts[iid] = new
        return True

    for item, quantity in (recipe.get('ingredients') or {}).items():
        if not add(item, quantity):
            return None

    distinct_pool = tuple(dict.fromkeys(str(x) for x in recipe.get('distinct_ingredient_pool') or ()))
    pooled_pool = tuple(dict.fromkeys(str(x) for x in recipe.get('pooled_ingredient_pool') or ()))
    # Prefer species outside the pooled objective. Selecting a pooled resource
    # for the distinct objective when a non-pooled species is available can
    # falsely report insufficient ingredients even though a valid plan exists.
    distinct_order = tuple(iid for iid in distinct_pool if iid not in pooled_pool)
    distinct_order += tuple(iid for iid in distinct_pool if iid in pooled_pool)
    distinct_count = require_sqlite_int64('v106.crafting.distinct', recipe.get('distinct_ingredient_count') or 0)
    if distinct_count < 0:
        raise ValueError('v106: ujemna liczba różnych składników')
    count = 0
    for iid in distinct_order:
        if count >= distinct_count:
            break
        if available(iid) > amounts[iid]:
            assert add(iid, 1)
            count += 1
    if count != distinct_count:
        return None

    pooled_count = require_sqlite_int64('v106.crafting.pooled', recipe.get('pooled_ingredient_count') or 0)
    if pooled_count < 0:
        raise ValueError('v106: ujemna liczba składników z puli')
    left = pooled_count
    for iid in pooled_pool:
        if left <= 0:
            break
        take = min(left, max(0, available(iid) - amounts[iid]))
        if take:
            assert add(iid, take)
            left -= take
    if left:
        return None

    # For zero-material recipes, do not mint unbounded free EQ through this
    # provisional high-level path.  They require an explicit future policy.
    if not amounts:
        raise RuntimeError('v106: receptura bez składników wymaga osobnej kontroli')
    return dict(amounts), {k: containers[k] for k in amounts}


def register_crafted_equipment_variant(db, base_item_id, crafted_item_id, items):
    """Register a runtime-created quality variant before physical minting.

    Quality/critical/infinite forge variants may not exist in the initial
    snapshot of the v106 shadow equipment catalog.  Without this bridge,
    `add_item` would silently mint a *stack* with no physical identities.
    The real ITEMS catalog is authoritative about the result's type.
    """
    from systems.equipment_crafting_guard_v10600 import active
    if not active(db):
        return False
    shadow = db._v106_shadow_item_catalog
    base = items.get(str(base_item_id)) or {}
    output = items.get(str(crafted_item_id)) or {}
    base_is_gear = (base.get('type') in ('armor', 'weapon') or
                    (shadow.get(str(base_item_id)) or {}).get('type') in ('armor','weapon'))
    output_is_gear = output.get('type') in ('armor','weapon')
    if base_is_gear and not output_is_gear:
        raise RuntimeError('v106: wynik receptury EQ nie ma poprawnego typu w katalogu')
    if not output_is_gear:
        return False
    existing = shadow.get(str(crafted_item_id))
    if existing is not None and existing.get('type') not in ('armor','weapon'):
        raise RuntimeError('v106: konflikt typu istniejącego identyfikatora EQ')
    if existing is None:
        shadow[str(crafted_item_id)] = output
    return True
