# -*- coding: utf-8 -*-
"""Maintenance map for Soulbound v0.57.1.

This module is intentionally independent from the legacy gameplay namespace.
It answers one question: where should a bug be fixed?
"""
from __future__ import annotations

from pathlib import PurePath

MAINTENANCE_AREAS = {
    "data/catalogs": {
        "files": ("data/items.py", "data/rooms.py", "data/npcs.py", "data/quests.py", "data/mobs.py", "data/shops.py", "data/crafting_recipes.py", "data/alchemy_recipes.py"),
        "purpose": "statyczne dane gry: itemy, pokoje, NPC, questy, moby, sklepy i receptury",
    },
    "data/runtime-ownership": {
        "files": ("data/catalog_mutations.py", "validation/catalog_ownership.py", "admin/catalog_ownership_audit_v0480.py"),
        "purpose": "kontrolowane zmiany runtime katalogów oraz ślad: który moduł zmienił jaki klucz",
    },
    "config/balance": {
        "files": ("config/balance.py",),
        "purpose": "centralne limity, timingi i tabele balansu bez logiki gameplayowej",
    },
    "events": {
        "files": ("events/bus.py", "events/contracts.py", "events/bootstrap.py", "events/listeners/chronicle.py", "events/listeners/kill_progression.py", "events/listeners/gathering_progression.py"),
        "purpose": "zdarzenia domenowe i reakcje questów, bounty, kontraktów, kroniki oraz zbierania",
    },
    "validation": {
        "files": ("validation/catalogs.py", "validation/events.py", "validation/modularity.py", "validation/dependencies.py", "validation/catalog_ownership.py", "admin/modular_services_audit_v0420.py", "admin/explicit_dependencies_audit_v0430.py", "admin/catalog_ownership_audit_v0480.py"),
        "purpose": "szybkie walidatory subsystemów i granic modułów przed deployem",
    },
    "architecture/dependencies": {
        "files": ("core/runtime_manifest.py", "core/native_runtime.py", "validation/dependencies.py", "admin/explicit_dependencies_audit_v0430.py"),
        "purpose": "jawne importy/eksporty, compatibility bridge i kontrola ukrytych zależności",
    },
    "architecture/maintainable-core": {
        "files": ("config/legacy_provenance.py", "validation/maintainable_core.py", "admin/maintainable_core_audit_v0500.py", "core/runtime_manifest.py"),
        "purpose": "funkcjonalne nazwy aktywnych modułów, provenance milestone i jawna kwarantanna legacy-compat",
    },
    "boot/runtime": {
        "files": ("server.py", "core/native_runtime.py", "core/runtime_manifest.py"),
        "purpose": "start serwera, kolejność runtime, kontrola nadpisań",
    },
    "accounts/characters": {
        "files": ("storage/db_accounts.py", "player/session_mixins/io_auth_character.py", "player/character.py"),
        "purpose": "logowanie, konta, postacie, zapis podstawowych danych",
    },
    "database/schema": {
        "files": ("storage/db_schema.py", "storage/schema_core.py", "storage/schema_progression.py", "storage/schema_world_quests.py", "storage/schema_social_guilds.py", "storage/schema_migrate_character.py", "storage/schema_migrate_economy.py", "storage/schema_migrate_history.py"),
        "purpose": "tabele SQLite i migracje",
    },
    "database/world": {
        "files": ("storage/db_world.py",),
        "purpose": "stan świata, instancje, eksploracja, rekordy i projekty świata",
    },
    "database/items": {
        "files": ("storage/db_inventory.py", "storage/db_crafting_extensions.py"),
        "purpose": "bank, inventory, EQ, storage, transfery oraz trwały stan craftingu bez monkey-patchy",
    },
    "database/progression": {
        "files": ("storage/db_progression.py",),
        "purpose": "klasy, skille i kolejki skilli w bazie",
    },
    "database/quests": {
        "files": ("storage/db_quests.py",),
        "purpose": "stan i progres questów w bazie",
    },
    "database/guilds": {
        "files": ("storage/db_guilds.py",),
        "purpose": "gildie i klany w bazie",
    },
    "quests": {
        "files": ("player/session_mixins/quest_progress.py", "player/session_mixins/quest_offers.py", "player/session_mixins/quest_turnin.py", "player/session_mixins/quest_npc.py", "player/session_mixins/quest_commands.py", "world/economy_quests.py", "events/listeners/kill_progression.py", "data/quests.py"),
        "purpose": "przyjmowanie, postęp, oddawanie i generowanie questów",
    },
    "combat": {
        "files": ("player/session_mixins/combat.py",),
        "purpose": "agregat publicznego API walki; nie dodawaj tu logiki gameplayowej",
    },
    "combat/skills": {
        "files": ("player/session_mixins/combat_skills.py",),
        "purpose": "używanie skilli klasowych, AoE, heal, guard, evade i boosty",
    },
    "combat/damage": {
        "files": ("player/session_mixins/combat_damage.py",),
        "purpose": "obrażenia gracza oraz consider/porównanie siły przeciwnika",
    },
    "combat/realtime": {
        "files": ("player/session_mixins/combat_realtime.py",),
        "purpose": "start/stop walki realtime, autoatak Bronią Duszy i komenda attack",
    },
    "combat/rewards": {
        "files": ("player/session_mixins/combat_rewards.py", "events/listeners/kill_progression.py", "events/listeners/chronicle.py"),
        "purpose": "pokonanie moba, EXP, loot, quest credit, kronika i nagrody drużyny",
    },
    "combat/survival": {
        "files": ("player/session_mixins/combat_survival.py",),
        "purpose": "flee, śmierć, Nemesis po śmierci i powrót postaci",
    },
    "combat/difficulty": {
        "files": ("config/balance.py", "world/world_threat_overdrive.py", "world/global_difficulty_overdrive.py", "world/crypt_floor_progression.py", "world/crypt_overdrive.py", "world/tower_overdrive.py"),
        "purpose": "końcowa trudność świata, instancji, Krypt, Wież i Magitek; v0.50.3 stroi finalne mnożniki w config/balance.py",
    },
    "skills": {
        "files": ("player/session_mixins/skill_learning.py", "player/session_mixins/skill_queue_buffs.py", "core/classes_skills.py"),
        "purpose": "nauka skilli, kolejki, buffy i definicje klas",
    },
    "inventory/equipment": {
        "files": ("player/session_mixins/inventory_equipment.py", "systems/items_resources.py", "systems/equipment_crafting.py"),
        "purpose": "inventory, zakładanie EQ, consumables, gemy i transfer przedmiotów",
    },
    "crafting": {
        "files": ("player/session_mixins/crafting.py", "player/session_mixins/crafting_expansion.py", "systems/crafting_expansion.py"),
        "purpose": "receptury i crafting",
    },
    "shops": {
        "files": ("player/session_mixins/shops_teachers.py",),
        "purpose": "sklepy, kupowanie i nauczyciele",
    },
    "professions/storage": {
        "files": ("player/session_mixins/profession_storage.py", "systems/professions.py"),
        "purpose": "profesje, narzędzia i magazyny profesyjne",
    },
    "gathering": {
        "files": ("player/session_mixins/gathering.py", "player/session_mixins/gathering_actions.py", "events/listeners/gathering_progression.py"),
        "purpose": "łowienie, kopanie, drewno, zioła i automaty zbierania",
    },
    "navigation/guide": {
        "files": ("player/session_mixins/movement.py", "player/session_mixins/guide_navigation.py", "player/session_mixins/perception_maps.py"),
        "purpose": "prowadz, trasy, wyszukiwanie lokacji i mapy",
    },
    "world": {
        "files": ("world/world_state.py", "world/generation_systems.py", "world/dynamic_content.py", "world/expansions.py", "player/session_mixins/world_events_endgame.py"),
        "purpose": "pokoje, moby, generowanie świata i zawartość dynamiczna",
    },
    "world/expansion-i": {
        "files": ("world/world_expansion_i.py", "admin/world_expansion_i_audit_v0510.py"),
        "purpose": "v0.51.0: nowe miasta, wsie, szlaki, expowiska, lokalne moby/NPC/questy i ich spójność topologiczna",
    },
    "world/expansion-ii": {
        "files": ("world/world_expansion_ii.py", "admin/world_expansion_ii_audit_v0520.py"),
        "purpose": "v0.52.0: Ardelia, Srebrna Korona, trzy osady, dziesięć expowisk, zamorskie szlaki i lokalne questy",
    },
    "dungeons": {
        "files": ("systems/dungeons_regions.py", "systems/dungeon_entry_commands.py", "world/crypt_overdrive.py", "world/tower_overdrive.py"),
        "purpose": "Krypty, Wieże, instancje i wejścia/wyjścia",
    },
    "party/social": {
        "files": ("player/session_mixins/party.py", "player/session_mixins/social_base.py", "player/session_mixins/social_expansion.py"),
        "purpose": "party, komunikacja, who/tell/kanały i funkcje społeczne",
    },
    "postal/deliveries": {
        "files": ("config/postal.py", "player/session_mixins/courier_delivery.py", "storage/db_world.py", "storage/schema_migrate_social.py", "player/session_mixins/guide_navigation.py", "admin/postal_quest_rewards_audit_v0522.py", "admin/courier_guild_audit_v0530.py", "admin/courier_achievements_audit_v0540.py"),
        "purpose": "v0.55.0: poczta co 15 minut, Gildia Kurierów 1-400, paczki prestiżowe bez ryzyka, osiągnięcia per-miasto/per-typ, statystyki i nawigacja między miastami",
    },
    "guilds": {
        "files": ("player/session_mixins/forge_guilds.py",),
        "purpose": "gildie, kuźnia gildii i klasyczne salvage",
    },
    "commands": {
        "files": (
            "core/command_catalog.py",
            "player/session_mixins/command_registry.py",
            "player/session_mixins/command_special_handlers.py",
            "player/session_mixins/command_loop.py",
            "validation/commands.py",
            "admin/command_registry_audit_v0490.py",
        ),
        "purpose": "jedno źródło aliasów/handlerów/HELP/polityki komend; parser tylko transportuje i dispatchuje",
    },
    "deployment/railway": {
        "files": ("Dockerfile", "admin/railway_packaging_audit_v0521.py", "tests/test_railway_packaging_v0521.py"),
        "purpose": "v0.52.1: kompletność obrazu Railway i COPY wszystkich pakietów modułowego runtime",
    },
    "admin/audits": {
        "files": ("admin/audits.py", "admin/architecture_audit_v0390.py", "admin/maintenance_audit_v0400.py", "admin/native_modules_audit_v0410.py", "admin/modular_services_audit_v0420.py", "admin/explicit_dependencies_audit_v0430.py"),
        "purpose": "testy integralności i bramki przed deployem",
    },
}

_EXACT_FILE_TO_AREA = {
    file_name: area
    for area, spec in MAINTENANCE_AREAS.items()
    for file_name in spec["files"]
}


def normalize_runtime_path(path: str) -> str:
    return str(PurePath(str(path or "").replace("\\", "/"))).lstrip("./")


def subsystem_for_path(path: str) -> str:
    rel = normalize_runtime_path(path)
    if rel in _EXACT_FILE_TO_AREA:
        return _EXACT_FILE_TO_AREA[rel]
    if rel.startswith("events/"):
        return "events"
    if rel.startswith("data/"):
        return "data/catalogs"
    if rel.startswith("config/"):
        return "config/balance"
    if rel.startswith("validation/"):
        return "validation"
    if rel.startswith("storage/"):
        return "database/other"
    if rel.startswith("player/session_mixins/"):
        return "session/other"
    if rel.startswith("world/"):
        return "world"
    if rel.startswith("systems/"):
        return "systems/other"
    if rel.startswith("admin/"):
        return "admin/audits"
    if rel.startswith("core/"):
        return "core/other"
    if rel.startswith("server/"):
        return "server"
    if rel.startswith("network/"):
        return "network"
    return "other"


def maintenance_hint(path: str) -> str:
    area = subsystem_for_path(path)
    purpose = MAINTENANCE_AREAS.get(area, {}).get("purpose", "pozostała logika")
    return f"{area}: {purpose}"
