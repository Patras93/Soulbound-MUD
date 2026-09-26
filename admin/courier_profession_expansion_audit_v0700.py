# -*- coding: utf-8 -*-
"""Soulbound v0.71.0 - Profession & City Expansion II audit."""
from __future__ import annotations

from collections import deque
import inspect

from config.postal import (
    POSTAL_CITY_HUBS_V0522, GUIDE_CITY_HUBS_V0522,
    COURIER_CITY_DELIVERY_ACHIEVEMENTS_V0550,
    CITY_REPUTATION_RANKS_V0710, CITY_REPUTATION_MAX_V0710,
)
from data.catalogs import ITEMS, ROOMS, NPCS
from data.quests import QUESTS
from world.world_expansion_iii import (
    WORLD_EXPANSION_III_SETTLEMENTS,
    WORLD_EXPANSION_III_NEW_ROOMS,
    WORLD_EXPANSION_III_NEW_NPCS,
    CITY_STORY_QUEST_IDS_V0710, CITY_STORY_QUESTS_BY_CITY_V0710,
    CITY_STORY_NPC_IDS_V0710, CITY_STORY_ITEM_IDS_V0710,
)
from player.session_mixins.crafting import SessionCraftingMixin
from player.session_mixins.inventory_equipment import SessionInventoryEquipmentMixin
from player.session_mixins.item_sources import SessionItemSourcesV0610Mixin
from player.session_mixins.courier_delivery import SessionCourierDeliveryMixin
from storage.db_world import DatabaseWorldMixin
from storage.schema_migrate_social import migrate_social_courier_schema
from world.generation_systems import V014_TREASURE_MAP_ITEM, V0243_EREN_SECRET_MAP_ITEM
from systems.profession_quest_expansion import (
    PROFESSION_QUEST_SPECS_V0700,
    PROFESSION_QUEST_STAGES_V0700,
    PROFESSION_QUEST_IDS_V0700,
    PROFESSION_QUEST_IDS_BY_PROFESSION_V0700,
    BEGINNER_PROFESSION_QUEST_SPECS_V0701,
    BEGINNER_PROFESSION_QUEST_IDS_V0701,
    PROFESSION_JOURNEY_STAGES_V0710, PROFESSION_JOURNEY_QUEST_IDS_V0710,
    PROFESSION_JOURNEY_IDS_BY_PROFESSION_V0710,
)


def _reachable_v0700(start, target):
    if start == target:
        return True
    if start not in ROOMS or target not in ROOMS:
        return False
    seen={start}; queue=deque([start])
    while queue:
        rid=queue.popleft()
        for nxt in (ROOMS[rid].get("exits") or {}).values():
            if nxt == target:
                return True
            if nxt in ROOMS and nxt not in seen:
                seen.add(nxt); queue.append(nxt)
    return False


def courier_profession_expansion_audit_v0700():
    errors=[]
    if len(WORLD_EXPANSION_III_SETTLEMENTS) != 12:
        errors.append(f"new settlements={len(WORLD_EXPANSION_III_SETTLEMENTS)}, expected 12")
    if len(WORLD_EXPANSION_III_NEW_ROOMS) != 72:
        errors.append(f"new rooms={len(WORLD_EXPANSION_III_NEW_ROOMS)}, expected 72")
    if len(WORLD_EXPANSION_III_NEW_NPCS) != 24:
        errors.append(f"new NPCs={len(WORLD_EXPANSION_III_NEW_NPCS)}, expected 24")
    if len(POSTAL_CITY_HUBS_V0522) != 21:
        errors.append(f"courier cities={len(POSTAL_CITY_HUBS_V0522)}, expected 21")
    if set(POSTAL_CITY_HUBS_V0522) != set(GUIDE_CITY_HUBS_V0522):
        errors.append("postal/guide city catalogs differ")
    for city, hub in POSTAL_CITY_HUBS_V0522.items():
        if hub not in ROOMS:
            errors.append(f"missing postal hub {city}->{hub}")
        if city not in COURIER_CITY_DELIVERY_ACHIEVEMENTS_V0550:
            errors.append(f"missing city courier achievement: {city}")
    for city, hub in GUIDE_CITY_HUBS_V0522.items():
        if hub not in ROOMS:
            errors.append(f"missing guide hub {city}->{hub}")
        elif not _reachable_v0700("square", hub):
            errors.append(f"guide city is not reachable from Miasto Dusz: {city}->{hub}")

    recipe_source = inspect.getsource(SessionCraftingMixin.show_recipes)
    available_source = inspect.getsource(SessionItemSourcesV0610Mixin.show_available_recipes_v0611)
    if "RECEPTURY — WYBIERZ PROFESJĘ" not in recipe_source:
        errors.append("recipe list does not require separate profession selection")
    for profession_cmd in (
        "receptury kowalstwo", "receptury gotowanie", "receptury alchemia",
        "receptury jubilerstwo", "receptury krawiectwo", "receptury garbarstwo",
        "receptury stolarstwo", "receptury zaklinanie",
    ):
        if profession_cmd not in recipe_source:
            errors.append(f"missing separate recipe command: {profession_cmd}")
    if "Wyniki są rozdzielone według profesji" not in available_source or "groups.setdefault" not in available_source:
        errors.append("available recipes are not grouped by profession")

    expected_quests=len(PROFESSION_QUEST_SPECS_V0700)*len(PROFESSION_QUEST_STAGES_V0700)
    if len(PROFESSION_QUEST_IDS_V0700) != expected_quests or expected_quests != 48:
        errors.append(f"profession quests={len(PROFESSION_QUEST_IDS_V0700)}, expected 48")
    for profession, tool_type, npc_id, _action in PROFESSION_QUEST_SPECS_V0700:
        ids=tuple(PROFESSION_QUEST_IDS_BY_PROFESSION_V0700.get(profession) or ())
        if len(ids) != 4:
            errors.append(f"{profession}: quest count={len(ids)}, expected 4")
        npc=NPCS.get(npc_id) or {}
        attached=set(npc.get("specialist_quests") or ())
        for qid in ids:
            q=QUESTS.get(qid)
            if not q:
                errors.append(f"missing profession quest {qid}")
                continue
            if qid not in attached:
                errors.append(f"{qid}: not attached to {npc_id}")
            if q.get("kind") != "profession_action":
                errors.append(f"{qid}: kind={q.get('kind')}")
            if q.get("required_profession") != profession or q.get("specialist_tool_type") != tool_type:
                errors.append(f"{qid}: profession/tool mismatch")
            if int(q.get("needed",0)) <= 0 or int(q.get("min_profession_level",0)) <= 0:
                errors.append(f"{qid}: invalid requirements")
            if not q.get("repeatable"):
                errors.append(f"{qid}: must be repeatable")

    # v0.70.1: every profession must have at least one real beginner quest (level 1-10).
    all_professions = tuple(spec[0] for spec in PROFESSION_QUEST_SPECS_V0700)
    beginner_by_profession = {}
    for profession in all_professions:
        beginner = []
        for qid, q in QUESTS.items():
            qprof = q.get("required_profession") or q.get("reward_profession")
            if qprof != profession:
                continue
            if int(q.get("min_profession_level", 1) or 1) <= 10:
                beginner.append(qid)
        beginner_by_profession[profession] = tuple(beginner)
        if not beginner:
            errors.append(f"{profession}: missing beginner profession quest level 1-10")

    expected_added = {spec[0] for spec in BEGINNER_PROFESSION_QUEST_SPECS_V0701}
    if len(BEGINNER_PROFESSION_QUEST_IDS_V0701) != 4:
        errors.append(f"v0.70.1 beginner quests added={len(BEGINNER_PROFESSION_QUEST_IDS_V0701)}, expected 4")
    for qid in BEGINNER_PROFESSION_QUEST_IDS_V0701:
        q = QUESTS.get(qid) or {}
        profession = q.get("required_profession")
        if profession not in expected_added:
            errors.append(f"{qid}: unexpected beginner profession={profession}")
        if q.get("kind") != "profession_action" or int(q.get("needed", 0) or 0) != 3:
            errors.append(f"{qid}: invalid beginner action contract")
        if int(q.get("min_profession_level", 0) or 0) != 1:
            errors.append(f"{qid}: beginner quest must start at profession level 1")
        if q.get("repeatable"):
            errors.append(f"{qid}: beginner quest must be one-time")
        if not q.get("starter_quest") or not q.get("v0701_beginner_profession"):
            errors.append(f"{qid}: missing beginner quest markers")

    # v0.71.0: 10 additional one-time journey stages per profession = 120 quests.
    if len(PROFESSION_JOURNEY_STAGES_V0710) != 10:
        errors.append(f"profession journey stages={len(PROFESSION_JOURNEY_STAGES_V0710)}, expected 10")
    expected_journey = len(PROFESSION_QUEST_SPECS_V0700) * len(PROFESSION_JOURNEY_STAGES_V0710)
    if len(PROFESSION_JOURNEY_QUEST_IDS_V0710) != expected_journey or expected_journey != 120:
        errors.append(f"profession journey quests={len(PROFESSION_JOURNEY_QUEST_IDS_V0710)}, expected 120")
    for profession, _tool_type, npc_id, _action in PROFESSION_QUEST_SPECS_V0700:
        ids = tuple(PROFESSION_JOURNEY_IDS_BY_PROFESSION_V0710.get(profession) or ())
        if len(ids) != 10:
            errors.append(f"{profession}: journey quest count={len(ids)}, expected 10")
        attached = set((NPCS.get(npc_id) or {}).get("specialist_quests") or ())
        previous = None
        for qid in ids:
            q = QUESTS.get(qid) or {}
            if qid not in attached:
                errors.append(f"{qid}: journey quest not attached to {npc_id}")
            if q.get("kind") != "profession_action" or q.get("required_profession") != profession:
                errors.append(f"{qid}: invalid journey profession/kind")
            if q.get("repeatable"):
                errors.append(f"{qid}: journey quest must be one-time")
            if not q.get("v0710_profession_journey"):
                errors.append(f"{qid}: missing v0.71.0 journey marker")
            if previous and q.get("requires_quest") != previous:
                errors.append(f"{qid}: journey chain broken, expected requires_quest={previous}")
            previous = qid

    # v0.71.0: every one of 21 courier cities has a 3-stage local story.
    if len(CITY_STORY_QUESTS_BY_CITY_V0710) != 21:
        errors.append(f"city stories={len(CITY_STORY_QUESTS_BY_CITY_V0710)}, expected 21")
    if len(CITY_STORY_QUEST_IDS_V0710) != 63:
        errors.append(f"city story quests={len(CITY_STORY_QUEST_IDS_V0710)}, expected 63")
    if len(CITY_STORY_NPC_IDS_V0710) != 63:
        errors.append(f"city story NPCs={len(CITY_STORY_NPC_IDS_V0710)}, expected 63")
    if len(CITY_STORY_ITEM_IDS_V0710) != 21:
        errors.append(f"city story items={len(CITY_STORY_ITEM_IDS_V0710)}, expected 21")
    for city in POSTAL_CITY_HUBS_V0522:
        ids = tuple(CITY_STORY_QUESTS_BY_CITY_V0710.get(city) or ())
        if len(ids) != 3:
            errors.append(f"{city}: local story count={len(ids)}, expected 3")
            continue
        for index, qid in enumerate(ids, 1):
            q = QUESTS.get(qid) or {}
            if q.get("reward_city_v0710") != city or int(q.get("reward_city_amount_v0710",0) or 0) <= 0:
                errors.append(f"{qid}: invalid city reputation reward")
            if not q.get("v0710_city_story") or q.get("repeatable"):
                errors.append(f"{qid}: invalid city story flags")
            if index > 1 and q.get("requires_quest") != ids[index-2]:
                errors.append(f"{qid}: city story chain broken")

    # Persistence and player-facing command/bonus must exist, not only catalog data.
    schema_source = inspect.getsource(migrate_social_courier_schema)
    db_source = inspect.getsource(DatabaseWorldMixin)
    courier_source = inspect.getsource(SessionCourierDeliveryMixin)
    if "city_reputation_v0710" not in schema_source:
        errors.append("missing city reputation SQLite schema")
    for token in ("city_reputation_v0710", "city_reputations_v0710", "add_city_reputation_v0710"):
        if token not in db_source:
            errors.append(f"missing DB city reputation helper: {token}")
    if "show_city_reputation_v0710" not in courier_source or "destination_city_reputation_at_offer" not in courier_source:
        errors.append("missing city reputation command or courier payout integration")
    if CITY_REPUTATION_MAX_V0710 != 400 or len(CITY_REPUTATION_RANKS_V0710) < 5:
        errors.append("invalid city reputation 1-400 rank configuration")

    # v0.71.4: Eren's repeatable secret quest must grant and resolve its own
    # quest map before the generic Treasure Map. This protects `użyj mapy`.
    eren_quest_id = "city_cartographer_secret_marks"
    eren_quest = QUESTS.get(eren_quest_id) or {}
    if int((eren_quest.get("accept_items") or {}).get(V0243_EREN_SECRET_MAP_ITEM, 0) or 0) != 1:
        errors.append("Eren secret quest does not grant exactly one quest map")
    if not eren_quest.get("accept_items_always"):
        errors.append("Eren secret quest must always grant its quest map on restart")
    eren_map = ITEMS.get(V0243_EREN_SECRET_MAP_ITEM) or {}
    if eren_map.get("quest_treasure_map_for") != eren_quest_id or not eren_map.get("treasure_map"):
        errors.append("Eren quest map metadata is invalid")

    class _MapAuditDB:
        def __init__(self, with_map=True, with_target=False):
            self.qty = {V0243_EREN_SECRET_MAP_ITEM: 1 if with_map else 0, V014_TREASURE_MAP_ITEM: 0}
            self.entries = {
                "quest_treasure_targets_v0243": ({f"{eren_quest_id}|dummy"} if with_target else set()),
                "quest_map_grants_v0243": set(),
            }
        def item_qty(self, _account_id, item_id):
            return int(self.qty.get(item_id, 0))
        def quest(self, _account_id, quest_id):
            return {"status":"active"} if quest_id == eren_quest_id else None
        def collection_entry_ids(self, _account_id, category):
            return set(self.entries.get(category, set()))
        def add_item(self, _account_id, item_id, qty):
            self.qty[item_id] = int(self.qty.get(item_id, 0)) + int(qty)
        def add_collection_entry(self, _account_id, category, entry):
            self.entries.setdefault(category, set()).add(entry)

    class _MapAuditServer:
        def __init__(self, db): self.db = db
    class _MapAuditSession:
        def __init__(self, db):
            self.account_id = 1
            self.server = _MapAuditServer(db)
        def normalize_description_query(self, value):
            return str(value or "").strip().casefold()

    direct_db = _MapAuditDB(with_map=True)
    direct_session = _MapAuditSession(direct_db)
    found, ambiguous = SessionInventoryEquipmentMixin.find_consumable_for_use(direct_session, "mapa")
    if ambiguous or not found or found[0] != V0243_EREN_SECRET_MAP_ITEM:
        errors.append("`użyj mapy` does not prefer Eren quest map")

    recovery_db = _MapAuditDB(with_map=False, with_target=False)
    recovery_session = _MapAuditSession(recovery_db)
    restored = SessionInventoryEquipmentMixin.restore_missing_eren_map_v0714(recovery_session)
    if not restored or recovery_db.item_qty(1, V0243_EREN_SECRET_MAP_ITEM) != 1:
        errors.append("active Eren quest does not restore one missing quest map")
    if SessionInventoryEquipmentMixin.restore_missing_eren_map_v0714(recovery_session):
        errors.append("Eren map recovery creates duplicate quest maps")

    used_db = _MapAuditDB(with_map=False, with_target=True)
    used_session = _MapAuditSession(used_db)
    if SessionInventoryEquipmentMixin.restore_missing_eren_map_v0714(used_session):
        errors.append("Eren map recovery creates a second map after a quest target already exists")

    return {
        "version":"0.71.0",
        "new_settlements":len(WORLD_EXPANSION_III_SETTLEMENTS),
        "new_rooms":len(WORLD_EXPANSION_III_NEW_ROOMS),
        "new_npcs":len(WORLD_EXPANSION_III_NEW_NPCS),
        "courier_cities":len(POSTAL_CITY_HUBS_V0522),
        "profession_quests":len(PROFESSION_QUEST_IDS_V0700),
        "beginner_professions":sum(1 for ids in beginner_by_profession.values() if ids),
        "beginner_quests_added_v0701":len(BEGINNER_PROFESSION_QUEST_IDS_V0701),
        "profession_journey_quests_v0710":len(PROFESSION_JOURNEY_QUEST_IDS_V0710),
        "city_story_quests_v0710":len(CITY_STORY_QUEST_IDS_V0710),
        "city_story_npcs_v0710":len(CITY_STORY_NPC_IDS_V0710),
        "recipe_groups":8,
        "error_count":len(errors),
        "errors":errors,
    }

COURIER_PROFESSION_EXPANSION_AUDIT_V0700=courier_profession_expansion_audit_v0700()
if COURIER_PROFESSION_EXPANSION_AUDIT_V0700["error_count"]:
    raise RuntimeError(
        "Profession & City Expansion Audit v0.71.0 failed: "
        + "; ".join(COURIER_PROFESSION_EXPANSION_AUDIT_V0700["errors"][:100])
    )

__all__=["courier_profession_expansion_audit_v0700","COURIER_PROFESSION_EXPANSION_AUDIT_V0700"]
