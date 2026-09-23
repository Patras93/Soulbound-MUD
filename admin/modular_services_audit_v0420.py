# -*- coding: utf-8 -*-
"""Soulbound v0.42.0 - data/config/event modularity audit."""
from pathlib import Path

from data.catalogs import (
    ALCHEMY_RECIPES, CRAFT_RECIPES, ITEMS, MOB_TEMPLATES, NPCS, QUESTS, ROOMS, SHOPS,
)
from events.bootstrap import build_default_event_bus
from validation.catalogs import validate_catalogs
from validation.events import validate_event_bus
from validation.modularity import validate_modular_boundaries


def modular_services_audit_v0420():
    root = Path(__file__).resolve().parents[1]
    errors = []

    boundaries = validate_modular_boundaries(root)
    errors.extend(boundaries["errors"])

    catalogs = validate_catalogs(
        items=ITEMS,
        rooms=ROOMS,
        npcs=NPCS,
        quests=QUESTS,
        mobs=MOB_TEMPLATES,
        shops=SHOPS,
        craft_recipes=CRAFT_RECIPES,
        alchemy_recipes=ALCHEMY_RECIPES,
    )
    errors.extend(catalogs["errors"])

    class _AuditServer:
        def report_runtime_error(self, *args, **kwargs):
            return None

    event_bus = build_default_event_bus(_AuditServer())
    events = validate_event_bus(event_bus)
    errors.extend(events["errors"])

    return {
        "version": "0.42.0",
        "error_count": len(errors),
        "errors": errors,
        "catalog_counts": catalogs["counts"],
        "catalog_owner_count": boundaries["catalog_owner_count"],
        "event_listeners": events["listeners"],
        "balance_config_module": "config.balance",
        "data_modules": tuple(sorted({
            "data.rooms", "data.items", "data.npcs", "data.quests", "data.mobs",
            "data.shops", "data.crafting_recipes", "data.alchemy_recipes",
        })),
    }


MODULAR_SERVICES_AUDIT_V0420 = modular_services_audit_v0420()
if MODULAR_SERVICES_AUDIT_V0420["error_count"]:
    raise RuntimeError(
        "Modular Services Audit v0.42.0 failed: "
        + "; ".join(MODULAR_SERVICES_AUDIT_V0420["errors"][:100])
    )
