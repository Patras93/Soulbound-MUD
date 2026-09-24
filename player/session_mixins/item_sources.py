# -*- coding: utf-8 -*-
"""Soulbound v0.61.0 — item acquisition source finder.

Read-only, NVDA-friendly lookup over the assembled runtime catalogs.  The
command never guesses a source: every line is derived from active shops,
recipes, quests, mob templates/spawns or profession resource atlases.
"""
from __future__ import annotations

from collections import defaultdict

from core.bootstrap_economy_professions import required_tool_tier_for_level, tool_tier
from core.classes_skills import (
    HERB_ATLAS_ROOM_MIN_LEVELS,
    ORE_ATLAS_LEVELS,
    ORE_MINE_FLOOR_MINIMUMS,
    ROOMS,
    WOOD_ATLAS_ROOM_MIN_LEVELS,
)
from core.mines_threat import ITEMS
from core.progression_resources import (
    FISH_RESOURCE_IDS,
    HERB_RESOURCE_IDS,
    LAKE_FISH_ATLAS,
    OCEAN_FISH_ATLAS,
    ORE_RESOURCE_IDS,
    RIVER_FISH_ATLAS,
    SEA_FISH_ATLAS,
    WOOD_RESOURCE_IDS,
)
from network.protocol_gameplay_utils import V0925_RUNES, normalize_lookup_text
from systems.crafting_expansion import RUNE_CRAFT_COSTS_V03114
from systems.content_registry import MOB_SPAWNS, MOB_TEMPLATES, NPCS, QUESTS
from systems.equipment_crafting import (
    ALCHEMY_RECIPES,
    COOK_RECIPES,
    CRAFT_RECIPES,
    JEWELCRAFT_RECIPES,
    SHOPS,
    SHOP_SELLERS,
)
from systems.items_resources import BLACKSMITH_TIERS, fish_unlock_level
from systems.milestone import TECH_SET_UPGRADE_COSTS_V0320
from systems.professions import V03053_CRAFT_RECIPES, V03053_ENCHANTS

V0610_ITEM_SOURCE_VERSION = "0.61.0"
V0611_CRAFT_GUIDANCE_VERSION = "0.61.1"
V0614_CRAFTING_LOGISTICS_VERSION = "0.61.4"


def _item_search_terms_v0610(item_id, item):
    terms = {normalize_lookup_text(item_id), normalize_lookup_text(item.get("name", ""))}
    for alias in item.get("aliases") or ():
        terms.add(normalize_lookup_text(alias))
    return {term for term in terms if term}


def resolve_item_query_v0610(query):
    """Return (item_id, item, suggestions) from the live ITEMS catalog."""
    q = normalize_lookup_text(query)
    if not q:
        return None, None, []

    exact = []
    partial = []
    for item_id, item in ITEMS.items():
        terms = _item_search_terms_v0610(item_id, item)
        if q in terms:
            exact.append((item_id, item))
        elif any(q in term for term in terms):
            partial.append((item_id, item))

    if exact:
        exact.sort(key=lambda row: (normalize_lookup_text(row[1].get("name", "")), row[0]))
        return exact[0][0], exact[0][1], []
    if len(partial) == 1:
        return partial[0][0], partial[0][1], []
    if partial:
        partial.sort(key=lambda row: (normalize_lookup_text(row[1].get("name", "")), row[0]))
        return None, None, partial[:10]
    return None, None, []


def _room_names_v0610(room_ids, limit=4):
    names = []
    for room_id in room_ids:
        name = str(ROOMS.get(room_id, {}).get("name") or room_id)
        if name not in names:
            names.append(name)
    if len(names) <= limit:
        return ", ".join(names)
    return ", ".join(names[:limit]) + f" i jeszcze {len(names) - limit}"


def _mob_locations_v0610(template_id):
    return [room_id for room_id, mob_id in MOB_SPAWNS if mob_id == template_id]


def _is_boss_v0610(template_id, template):
    return bool(
        template.get("world_boss")
        or template.get("boss")
        or template.get("superboss")
        or template.get("boss_mechanic")
        or template.get("boss_floor")
        or "boss" in str(template_id)
    )


def _recipe_sources_v0610(item_id):
    rows = []
    seen = set()
    tables = (
        ("Rzemiosło", CRAFT_RECIPES),
        ("Gotowanie", COOK_RECIPES),
        ("Alchemia", ALCHEMY_RECIPES),
        ("Jubilerstwo", JEWELCRAFT_RECIPES),
        ("Rzemiosło rozszerzone", V03053_CRAFT_RECIPES),
    )
    for default_label, recipes in tables:
        for recipe_id, recipe in recipes.items():
            if str(recipe.get("output") or "") != item_id:
                continue
            signature = (recipe_id, tuple(recipe.get("stations") or ()), str(recipe.get("profession") or default_label))
            if signature in seen:
                continue
            seen.add(signature)
            profession = str(recipe.get("profession") or default_label)
            stations = tuple(recipe.get("stations") or ())
            station_text = _room_names_v0610(stations) if stations else "dowolna właściwa stacja"
            req = int(recipe.get("min_profession_level", recipe.get("min_tool_level", 0)) or 0)
            req_text = f" Wymagany poziom: {req}." if req > 0 else ""
            rows.append(
                f"Receptura: {recipe.get('name') or ITEMS.get(item_id, {}).get('name', item_id)}. "
                f"{profession}. Miejsce: {station_text}.{req_text}"
            )
    return rows


def _shop_sources_v0610(item_id):
    rows = []
    for room_id, offers in SHOPS.items():
        if item_id not in offers:
            continue
        room_name = str(ROOMS.get(room_id, {}).get("name") or room_id)
        seller_id = SHOP_SELLERS.get(room_id)
        seller = str(NPCS.get(seller_id, {}).get("name") or "") if seller_id else ""
        if seller:
            rows.append(f"Sklep: {room_name}. Sprzedawca: {seller}.")
        else:
            rows.append(f"Sklep: {room_name}.")
    return rows


def _quest_sources_v0610(item_id):
    rows = []
    for quest_id, quest in QUESTS.items():
        reward_items = quest.get("reward_items") or {}
        accept_items = quest.get("accept_items") or {}
        quest_item = str(quest.get("quest_item") or "")
        reasons = []
        if isinstance(reward_items, dict) and int(reward_items.get(item_id, 0) or 0) > 0:
            reasons.append("nagroda")
        if isinstance(accept_items, dict) and int(accept_items.get(item_id, 0) or 0) > 0:
            reasons.append("otrzymujesz przy przyjęciu")
        if quest_item == item_id:
            reasons.append("przedmiot zadania")
        if not reasons:
            continue
        giver = str(quest.get("giver") or "")
        suffix = f" NPC: {giver}." if giver else ""
        rows.append(
            f"Quest: {quest.get('name') or quest_id} — {', '.join(reasons)}.{suffix}"
        )
    return rows


def _drop_sources_v0610(item_id):
    rows = []
    for template_id, template in MOB_TEMPLATES.items():
        reasons = []
        chance = None
        drops = template.get("drops") or {}
        if isinstance(drops, dict) and item_id in drops:
            chance = drops.get(item_id)
            reasons.append("drop")
        if item_id in (template.get("corpse_equipment_pool") or ()):
            reasons.append("EQ z ciała")
        if item_id in (template.get("corpse_material_pool") or ()):
            reasons.append("materiałowe EQ z ciała")
        material_chances = template.get("corpse_material_chances") or {}
        if isinstance(material_chances, dict) and item_id in material_chances:
            chance = material_chances.get(item_id)
            reasons.append("materiał z ciała")
        if not reasons:
            continue

        label = "Boss" if _is_boss_v0610(template_id, template) else "Drop"
        mob_name = str(template.get("name") or template_id)
        chance_text = ""
        if isinstance(chance, (int, float)):
            chance_text = f" Szansa: {float(chance) * 100:.1f}%."
        locations = _mob_locations_v0610(template_id)
        location_text = f" Lokacje: {_room_names_v0610(locations)}." if locations else ""
        rows.append(
            f"{label}: {mob_name} ({', '.join(reasons)}).{chance_text}{location_text}"
        )
    return rows


def _gathering_sources_v0610(item_id):
    rows = []
    if item_id in FISH_RESOURCE_IDS:
        habitats = []
        for label, atlas in (
            ("rzeka", RIVER_FISH_ATLAS),
            ("jezioro", LAKE_FISH_ATLAS),
            ("morze", SEA_FISH_ATLAS),
            ("ocean", OCEAN_FISH_ATLAS),
        ):
            if item_id in atlas:
                habitats.append(label)
        level = max(1, int(fish_unlock_level(item_id) or 1))
        rows.append(
            f"Wędkarstwo: {', '.join(habitats) if habitats else 'łowiska zgodne z atlasem'}. "
            f"Wędka od poziomu {level}."
        )

    if item_id in ORE_RESOURCE_IDS:
        tool = max(1, int(ORE_ATLAS_LEVELS.get(item_id, 1) or 1))
        floor = max(1, int(ORE_MINE_FLOOR_MINIMUMS.get(item_id, tool) or tool))
        rows.append(f"Górnictwo: Kilof od poziomu {tool}; Kopalnia Głębinowa od piętra {floor}.")

    if item_id in WOOD_RESOURCE_IDS:
        found = []
        for room_id, mapping in WOOD_ATLAS_ROOM_MIN_LEVELS.items():
            if item_id in mapping:
                found.append((room_id, int(mapping[item_id] or 1)))
        if found:
            min_level = min(level for _room, level in found)
            rows.append(
                f"Drwalstwo: Piła od poziomu {min_level}. Miejsca: "
                f"{_room_names_v0610([room for room, _level in found])}."
            )
        else:
            rows.append("Drwalstwo: zasób znajduje się w aktywnej puli Drwalstwa.")

    if item_id in HERB_RESOURCE_IDS:
        found = []
        for room_id, mapping in HERB_ATLAS_ROOM_MIN_LEVELS.items():
            if item_id in mapping:
                found.append((room_id, int(mapping[item_id] or 1)))
        if found:
            min_level = min(level for _room, level in found)
            rows.append(
                f"Zielarstwo: Sierp od poziomu {min_level}. Miejsca: "
                f"{_room_names_v0610([room for room, _level in found])}."
            )
        else:
            rows.append("Zielarstwo: zasób znajduje się w aktywnej puli Zielarstwa.")
    return rows


def item_source_entries_v0610(item_id):
    """Return grouped, deduplicated source text for a live item ID."""
    item = ITEMS.get(item_id) or {}
    if not item:
        return []

    # Quality variants are created by crafting a base output.  Rare profession
    # resources are created only while gathering their base resource.
    crafted_base = str(item.get("crafted_base_id_v03054") or "")
    rare_base = str(item.get("base_resource_id") or "")

    entries = []
    if crafted_base and crafted_base in ITEMS:
        entries.append((
            "wariant",
            f"Wariant jakości craftu: powstaje podczas wykonania bazowego przedmiotu "
            f"{ITEMS[crafted_base].get('name', crafted_base)}.",
        ))
        for text in _recipe_sources_v0610(crafted_base):
            entries.append(("receptura", text))
    elif rare_base and rare_base in ITEMS:
        entries.append((
            "wariant",
            f"Rzadki wariant zasobu: może powstać podczas zdobywania bazowego zasobu "
            f"{ITEMS[rare_base].get('name', rare_base)}.",
        ))
        for text in _gathering_sources_v0610(rare_base):
            entries.append(("profesja", text))
    else:
        for text in _shop_sources_v0610(item_id):
            entries.append(("sklep", text))
        for text in _recipe_sources_v0610(item_id):
            entries.append(("receptura", text))
        for text in _quest_sources_v0610(item_id):
            entries.append(("quest", text))
        for text in _drop_sources_v0610(item_id):
            entries.append(("boss" if text.startswith("Boss:") else "drop", text))
        for text in _gathering_sources_v0610(item_id):
            entries.append(("profesja", text))

    # Preserve source priority but remove exact duplicate lines produced by
    # overlapping recipe tables.
    seen = set()
    unique = []
    for kind, text in entries:
        signature = normalize_lookup_text(text)
        if signature in seen:
            continue
        seen.add(signature)
        unique.append((kind, text))
    return unique


def _recipe_tables_v0611():
    """Live recipe tables used by the real crafting handlers."""
    return (
        ("Rzemiosło/Kowalstwo", CRAFT_RECIPES),
        ("Gotowanie", COOK_RECIPES),
        ("Alchemia", ALCHEMY_RECIPES),
        ("Jubilerstwo", JEWELCRAFT_RECIPES),
        ("Rzemiosła rozszerzone", V03053_CRAFT_RECIPES),
    )


def live_recipe_rows_v0611():
    """Yield deduplicated (label, table, recipe_id, recipe) tuples."""
    seen = set()
    for label, table in _recipe_tables_v0611():
        for recipe_id, recipe in table.items():
            signature = (
                str(recipe_id),
                str(recipe.get("output") or ""),
                str(recipe.get("name") or ""),
                str(recipe.get("profession") or label),
                tuple(sorted((str(k), int(v)) for k, v in (recipe.get("ingredients") or {}).items())),
                tuple(recipe.get("distinct_ingredient_pool") or ()),
                int(recipe.get("distinct_ingredient_count", 0) or 0),
                tuple(recipe.get("pooled_ingredient_pool") or ()),
                int(recipe.get("pooled_ingredient_count", 0) or 0),
            )
            if signature in seen:
                continue
            seen.add(signature)
            yield label, table, str(recipe_id), recipe


def _crafted_base_v0611(item_id):
    item = ITEMS.get(item_id) or {}
    base = str(item.get("crafted_base_id_v03054") or "")
    return base if base in ITEMS else str(item_id)


def _resource_base_v0611(item_id):
    item = ITEMS.get(item_id) or {}
    base = str(item.get("base_resource_id") or "")
    return base if base in ITEMS else str(item_id)


def recipe_rows_for_output_v0611(item_id):
    output_id = _crafted_base_v0611(item_id)
    return [row for row in live_recipe_rows_v0611() if str(row[3].get("output") or "") == output_id]


def _recipe_use_entries_v0611(item_id):
    rows = []
    for label, _table, _recipe_id, recipe in live_recipe_rows_v0611():
        uses = []
        direct = recipe.get("ingredients") or {}
        if item_id in direct:
            uses.append(f"x{int(direct[item_id])}")
        if item_id in tuple(recipe.get("distinct_ingredient_pool") or ()):
            uses.append("jako jeden z różnych składników")
        if item_id in tuple(recipe.get("pooled_ingredient_pool") or ()):
            uses.append("jako składnik z puli")
        if not uses:
            continue
        output_id = str(recipe.get("output") or "")
        output_name = str(ITEMS.get(output_id, {}).get("name") or output_id or recipe.get("name") or "produkt")
        rows.append(
            f"Receptura: {recipe.get('name') or output_name}. Produkt: {output_name}. "
            f"Zużycie: {', '.join(uses)}. System: {recipe.get('profession') or label}."
        )
    return rows


def _item_matches_quest_category_v0611(item_id, category):
    base = _resource_base_v0611(item_id)
    if category == "fish":
        return base in FISH_RESOURCE_IDS
    if category == "fish_river":
        return base in RIVER_FISH_ATLAS
    if category == "ore":
        return base in ORE_RESOURCE_IDS
    if category == "wood":
        return base in WOOD_RESOURCE_IDS
    if category == "herb":
        return base in HERB_RESOURCE_IDS
    return False


def _quest_use_entries_v0611(item_id):
    rows = []
    resource_base = _resource_base_v0611(item_id)
    crafted_base = _crafted_base_v0611(item_id)
    for quest_id, quest in QUESTS.items():
        kind = str(quest.get("kind") or "")
        needed = max(1, int(quest.get("needed", 1) or 1))
        reason = None
        if kind == "collect" and str(quest.get("target") or "") == crafted_base:
            reason = f"oddanie {needed} szt."
        elif kind == "collect_resource" and str(quest.get("target") or "") == resource_base:
            reason = f"oddanie {needed} szt. surowca"
        elif kind == "collect_resource_set":
            req = dict(quest.get("resource_targets") or {})
            if resource_base in req:
                reason = f"oddanie {int(req[resource_base])} szt. jako część zestawu surowców"
        elif kind == "craft_set" and crafted_base in tuple(quest.get("targets") or ()):
            reason = "oddanie 1 szt. jako element zestawu"
        elif kind == "deliver_npc" and str(quest.get("quest_item") or "") == item_id:
            reason = f"dostarczenie {needed} szt. do NPC"
        elif kind in ("collect_category", "collect_distinct_category") and _item_matches_quest_category_v0611(
            item_id, str(quest.get("target") or "")
        ):
            if kind == "collect_distinct_category":
                reason = f"może być jednym z {needed} różnych wymaganych gatunków"
            else:
                reason = f"może wejść do wspólnej puli {needed} szt. do oddania"
        if reason:
            rows.append(f"Quest: {quest.get('name') or quest_id}. Zastosowanie: {reason}. NPC: {quest.get('giver') or 'brak' }.")
    return rows


def _special_use_entries_v0611(item_id):
    """Non-recipe systems that really consume the item."""
    rows = []
    item = ITEMS.get(item_id) or {}

    # Standard +1..+10 EQ upgrade consumes the canonical smithing ingot ladder.
    smithing_ingots = {
        str(tier.get("ingot"))
        for tier in BLACKSMITH_TIERS
        if tier.get("ingot")
    }
    if item_id in smithing_ingots:
        rows.append(
            "Ulepszanie EQ +1..+10 u Haldora: sztabka jest zużywana jako podstawowy materiał "
            "dla przedmiotów z odpowiedniego przedziału Kowalstwa."
        )

    milestone_upgrade = {
        "hardened_steel_ingot": "+4",
        "astral_alloy": "+7",
        "eternium_alloy": "+10",
    }
    if item_id in milestone_upgrade:
        rows.append(
            f"Ulepszanie EQ: materiał dodatkowy wymagany przy przejściu na {milestone_upgrade[item_id]}."
        )

    if item_id == "reforge_essence":
        rows.append("Przekuwanie EQ u Haldora: Esencja Przekucia jest pobierana przy każdym reforge.")

    rune_uses = []
    for rune_key, costs in RUNE_CRAFT_COSTS_V03114.items():
        if item_id in costs:
            rune_uses.append(f"{rune_key} x{int(costs[item_id])}")
    if rune_uses:
        rows.append("Rune Crafting: materiał zużywają runy: " + ", ".join(rune_uses) + ".")

    rune_ids = {str(data[0]) for data in V0925_RUNES.values()}
    if item_id in rune_ids:
        rows.append("Gniazdo runiczne EQ: jedna runa jest pobierana ze Szkatułki przy komendzie `runa <typ> <EQ>`." )

    if str(item.get("type") or "") == "gem":
        rows.append("Gniazdo klejnotu EQ: jeden oszlifowany klejnot jest zużywany przy `osadz <klejnot> <slot>`." )

    if item_id == "socket_core_v03114":
        rows.append("Socket Crafting: Rdzeń Gniazda x1 lub x2 dodaje trwałe dodatkowe gniazdo do EQ.")
    if item_id in ("hardened_steel_ingot", "astral_alloy", "eternium_alloy"):
        rows.append("Socket Crafting: jeden taki stop jest zużywany razem z Rdzeniem Gniazda, zależnie od poziomu EQ.")

    for target_mark, costs in sorted(TECH_SET_UPGRADE_COSTS_V0320.items()):
        if item_id in costs:
            rows.append(
                f"Tech Set Upgrade do Mk-{'II' if int(target_mark) == 2 else 'III'}: zużywa x{int(costs[item_id])}."
            )

    if item_id == "engineer_upgrade_kit":
        rows.append("Upgrade narzędzia Inżyniera: zużywa 1 Zestaw Upgrade Inżyniera na trwałe ulepszenie narzędzia.")
    if item_id == "vmax_duration_module":
        rows.append("V-MAX Upgrade: moduł jest zużywany do trwałego zwiększenia czasu działania V-MAX.")
    if item_id == "vmax_cooling_module":
        rows.append("V-MAX Upgrade: moduł jest zużywany do trwałego skrócenia chłodzenia V-MAX.")

    enchant_uses = []
    for key, data in V03053_ENCHANTS.items():
        label, _stat, _base, mats = data
        if item_id in mats:
            enchant_uses.append(f"{label} x{int(mats[item_id])}")
    if enchant_uses:
        rows.append("Zaklinanie EQ: materiał zużywają zaklęcia: " + ", ".join(enchant_uses) + ".")

    return rows


def item_use_entries_v0611(item_id):
    entries = []
    for text in _recipe_use_entries_v0611(item_id):
        entries.append(("receptura", text))
    for text in _quest_use_entries_v0611(item_id):
        entries.append(("quest", text))
    for text in _special_use_entries_v0611(item_id):
        entries.append(("system", text))
    seen = set()
    result = []
    for kind, text in entries:
        sig = normalize_lookup_text(text)
        if sig in seen:
            continue
        seen.add(sig)
        result.append((kind, text))
    return result


def _extract_full_source_mode_v0611(query):
    words = str(query or "").strip().split()
    if words and normalize_lookup_text(words[-1]) in {"pelne", "pelny", "full", "details", "szczegoly"}:
        return " ".join(words[:-1]).strip(), True
    return str(query or "").strip(), False


def _strip_use_prefix_v0611(args):
    raw = str(args or "").strip()
    words = raw.split(maxsplit=1)
    if words and normalize_lookup_text(words[0]) in {"czego", "what", "uses", "use"}:
        return words[1].strip() if len(words) > 1 else ""
    return raw


def _strip_recipe_gap_prefix_v0611(args):
    raw = str(args or "").strip()
    words = raw.split(maxsplit=1)
    if words and normalize_lookup_text(words[0]) in {"receptura", "recipe", "przepis"}:
        return words[1].strip() if len(words) > 1 else ""
    return raw


def _strip_recipe_route_prefix_v0614(args):
    raw = str(args or "").strip()
    words = raw.split(maxsplit=1)
    if words and normalize_lookup_text(words[0]) in {"droga", "route", "path", "sciezka", "ścieżka"}:
        return words[1].strip() if len(words) > 1 else ""
    return raw


def _recipe_search_terms_v0611(recipe_id, recipe):
    terms = {
        normalize_lookup_text(recipe_id),
        normalize_lookup_text(recipe.get("name", "")),
        normalize_lookup_text(ITEMS.get(str(recipe.get("output") or ""), {}).get("name", "")),
    }
    for alias in recipe.get("aliases") or ():
        terms.add(normalize_lookup_text(alias))
    return {term for term in terms if term}


def resolve_recipe_query_v0611(query):
    """Resolve an output item first, then fall back to recipe name/alias."""
    item_id, item, item_suggestions = resolve_item_query_v0610(query)
    if item_id:
        rows = recipe_rows_for_output_v0611(item_id)
        if rows:
            return rows, []
    q = normalize_lookup_text(query)
    exact = []
    partial = []
    for row in live_recipe_rows_v0611():
        terms = _recipe_search_terms_v0611(row[2], row[3])
        if q in terms:
            exact.append(row)
        elif q and any(q in term for term in terms):
            partial.append(row)
    if exact:
        return exact, []
    if len(partial) == 1:
        return partial, []
    if partial:
        return [], partial[:10]
    # If the item resolver had ambiguous results, surface those as recipe hints.
    hints = []
    for sid, candidate in item_suggestions[:10]:
        for row in recipe_rows_for_output_v0611(sid):
            hints.append(row)
    return [], hints[:10]


def _strip_lookup_prefix_v0610(args):
    raw = str(args or "").strip()
    words = raw.split(maxsplit=1)
    if words and normalize_lookup_text(words[0]) in {"zdobyc", "zdobadz", "get", "find"}:
        return words[1].strip() if len(words) > 1 else ""
    return raw


class SessionItemSourcesV0610Mixin:
    def _recipe_readiness_v0611(self, table, recipe):
        profession = self.recipe_profession_name(table, recipe)
        required = max(
            1,
            int(recipe.get("min_profession_level", recipe.get("min_tool_level", 1)) or 1),
        )
        profession_level = int(self.server.db.profession(self.account_id, profession)["level"])
        tool_type, tool_item_id, tool_name = self.recipe_tool_info(table, recipe)
        tool_owned = self.server.db.item_qty(self.account_id, tool_item_id) > 0
        tool_level = int(self.server.db.tool(self.account_id, tool_type)["level"])
        current_tier = int(tool_tier(tool_level))
        required_tier = int(required_tool_tier_for_level(required))
        stations = tuple(recipe.get("stations") or ())
        station_ok = not stations or self.character.room_id in stations

        missing = []
        ingredient_rows = []
        for ingredient_id, quantity in (recipe.get("ingredients") or {}).items():
            quantity = max(1, int(quantity))
            have = max(0, int(self.available_recipe_item(ingredient_id)))
            lack = max(0, quantity - have)
            ingredient_rows.append((ingredient_id, have, quantity, lack))
            if lack:
                missing.append(f"{ITEMS.get(ingredient_id, {}).get('name', ingredient_id)} {have}/{quantity}")

        distinct_pool = tuple(recipe.get("distinct_ingredient_pool") or ())
        distinct_needed = max(0, int(recipe.get("distinct_ingredient_count", 0) or 0))
        distinct_have_ids = [iid for iid in distinct_pool if self.available_recipe_item(iid) > 0]
        distinct_have = len(distinct_have_ids)
        if distinct_pool and distinct_have < distinct_needed:
            missing.append(
                f"{recipe.get('distinct_ingredient_label', 'różne składniki')} {distinct_have}/{distinct_needed}"
            )

        pooled_pool = tuple(recipe.get("pooled_ingredient_pool") or ())
        pooled_needed = max(0, int(recipe.get("pooled_ingredient_count", 0) or 0))
        pooled_have = sum(max(0, int(self.available_recipe_item(iid))) for iid in pooled_pool)
        if pooled_pool and pooled_have < pooled_needed:
            missing.append(
                f"{recipe.get('pooled_ingredient_label', 'składniki z puli')} {pooled_have}/{pooled_needed}"
            )

        ready = bool(
            not self.combat_mob_key
            and profession_level >= required
            and tool_owned
            and current_tier >= required_tier
            and station_ok
            and not missing
        )
        return {
            "ready": ready,
            "profession": profession,
            "profession_level": profession_level,
            "required_profession": required,
            "tool_type": tool_type,
            "tool_item_id": tool_item_id,
            "tool_name": tool_name,
            "tool_owned": tool_owned,
            "tool_level": tool_level,
            "tool_tier": current_tier,
            "required_tool_tier": required_tier,
            "stations": stations,
            "station_ok": station_ok,
            "ingredient_rows": ingredient_rows,
            "distinct_pool": distinct_pool,
            "distinct_needed": distinct_needed,
            "distinct_have": distinct_have,
            "pooled_pool": pooled_pool,
            "pooled_needed": pooled_needed,
            "pooled_have": pooled_have,
            "missing": missing,
        }

    async def _show_full_source_chain_v0611(self, item_id):
        rows = recipe_rows_for_output_v0611(item_id)
        if not rows:
            await self.send("PEŁNY ŁAŃCUCH: ten przedmiot nie ma aktywnej receptury w katalogu gry.")
            return

        await self.send("PEŁNY ŁAŃCUCH CRAFTINGU — SKŁADNIKI I ICH ŹRÓDŁA")
        for recipe_index, (_label, _table, _recipe_id, recipe) in enumerate(rows[:5], 1):
            output_id = str(recipe.get("output") or item_id)
            output_name = ITEMS.get(output_id, {}).get("name", output_id)
            await self.send(f"Receptura {recipe_index}: {recipe.get('name') or output_name} -> {output_name}.")

            ingredient_no = 0
            for ingredient_id, quantity in (recipe.get("ingredients") or {}).items():
                ingredient_no += 1
                ingredient_name = ITEMS.get(ingredient_id, {}).get("name", ingredient_id)
                await self.send(f"Składnik {ingredient_no}: {ingredient_name} x{int(quantity)}.")
                sources = item_source_entries_v0610(ingredient_id)
                if not sources:
                    await self.send("  Źródło: brak jawnego źródła w aktywnych katalogach.")
                    continue
                for _kind, source_text in sources[:4]:
                    await self.send("  Źródło: " + source_text)
                if len(sources) > 4:
                    await self.send(f"  Dalsze źródła: {len(sources) - 4}.")

            distinct_pool = tuple(recipe.get("distinct_ingredient_pool") or ())
            distinct_needed = max(0, int(recipe.get("distinct_ingredient_count", 0) or 0))
            if distinct_pool and distinct_needed:
                await self.send(
                    f"Pula różnych składników: potrzeba {distinct_needed}. "
                    + ", ".join(ITEMS.get(iid, {}).get("name", iid) for iid in distinct_pool[:8])
                    + (f" i jeszcze {len(distinct_pool) - 8}." if len(distinct_pool) > 8 else ".")
                )
            pooled_pool = tuple(recipe.get("pooled_ingredient_pool") or ())
            pooled_needed = max(0, int(recipe.get("pooled_ingredient_count", 0) or 0))
            if pooled_pool and pooled_needed:
                await self.send(
                    f"Wspólna pula składników: potrzeba łącznie {pooled_needed}. "
                    + ", ".join(ITEMS.get(iid, {}).get("name", iid) for iid in pooled_pool[:8])
                    + (f" i jeszcze {len(pooled_pool) - 8}." if len(pooled_pool) > 8 else ".")
                )
        if len(rows) > 5:
            await self.send(f"Dodatkowe receptury tego przedmiotu: {len(rows) - 5}.")

    async def show_item_sources_v0610(self, args=""):
        query = _strip_lookup_prefix_v0610(args)
        query, full_mode = _extract_full_source_mode_v0611(query)
        if not query:
            await self.send(
                "Użycie: gdzie zdobyc <przedmiot>. Pełny łańcuch: gdzie zdobyc <przedmiot> pelne."
            )
            return False

        item_id, item, suggestions = resolve_item_query_v0610(query)
        if item_id is None:
            if suggestions:
                await self.send("Nazwa jest niejednoznaczna. Pasujące przedmioty:")
                for number, (_sid, candidate) in enumerate(suggestions, 1):
                    await self.send(f"{number}. {candidate.get('name', _sid)}.")
                await self.send("Wpisz dokładniejszą nazwę: gdzie zdobyc <przedmiot>.")
            else:
                await self.send("Nie znalazłem takiego przedmiotu w aktualnym katalogu gry.")
            return False

        name = str(item.get("name") or item_id)
        entries = item_source_entries_v0610(item_id)
        await self.send(f"GDZIE ZDOBYĆ: {name}.")
        if not entries:
            await self.send(
                "Gra nie ma jawnego źródła tego przedmiotu w aktywnych sklepach, recepturach, "
                "questach, dropach ani pulach profesji. Może to być przedmiot techniczny, startowy "
                "albo przyznawany przez wyspecjalizowaną mechanikę."
            )
            return True

        grouped = defaultdict(list)
        for kind, text in entries:
            grouped[kind].append(text)
        order = ("wariant", "sklep", "receptura", "quest", "boss", "drop", "profesja")
        emitted = 0
        for kind in order:
            rows = grouped.get(kind, [])
            if not rows:
                continue
            for text in rows[:8]:
                emitted += 1
                await self.send(f"{emitted}. {text}")
            if len(rows) > 8:
                emitted += 1
                await self.send(f"{emitted}. Dodatkowe źródła tej kategorii: {len(rows) - 8}.")
        if full_mode:
            await self._show_full_source_chain_v0611(item_id)
        return True

    async def show_item_uses_v0611(self, args=""):
        query = _strip_use_prefix_v0611(args)
        if not query:
            await self.send("Użycie: do czego <przedmiot>. Przykład: do czego Odłamek Duszy.")
            return False
        item_id, item, suggestions = resolve_item_query_v0610(query)
        if item_id is None:
            if suggestions:
                await self.send("Nazwa jest niejednoznaczna. Pasujące przedmioty:")
                for number, (_sid, candidate) in enumerate(suggestions, 1):
                    await self.send(f"{number}. {candidate.get('name', _sid)}.")
                await self.send("Wpisz dokładniejszą nazwę: do czego <przedmiot>.")
            else:
                await self.send("Nie znalazłem takiego przedmiotu w aktualnym katalogu gry.")
            return False

        name = str(item.get("name") or item_id)
        entries = item_use_entries_v0611(item_id)
        await self.send(f"DO CZEGO: {name}.")
        if not entries:
            await self.send(
                "Nie znalazłem aktywnej receptury, questa ani specjalnego systemu, który zużywa ten przedmiot."
            )
            return True
        grouped = defaultdict(list)
        for kind, text in entries:
            grouped[kind].append(text)
        labels = (("receptura", "RECEPTURY"), ("quest", "QUESTY"), ("system", "ULEPSZENIA I INNE SYSTEMY"))
        for kind, label in labels:
            rows = grouped.get(kind, [])
            if not rows:
                continue
            await self.send(label + f": {len(rows)}.")
            for number, text in enumerate(rows[:20], 1):
                await self.send(f"{number}. {text}")
            if len(rows) > 20:
                await self.send(f"Dalsze zastosowania tej kategorii: {len(rows) - 20}.")
        return True

    async def show_recipe_gaps_v0611(self, args=""):
        query = _strip_recipe_gap_prefix_v0611(args)
        if not query:
            await self.send("Użycie: braki receptura <przedmiot lub nazwa receptury>.")
            return False

        rows, suggestions = resolve_recipe_query_v0611(query)
        if not rows:
            if suggestions:
                await self.send("Nazwa jest niejednoznaczna. Pasujące receptury:")
                for number, (_label, _table, _recipe_id, recipe) in enumerate(suggestions, 1):
                    await self.send(f"{number}. {recipe.get('name') or _recipe_id}.")
            else:
                await self.send("Nie znalazłem aktywnej receptury dla podanej nazwy.")
            return False

        await self.send(f"BRAKI RECEPTURY: znaleziono {len(rows)}.")
        for idx, (_label, table, _recipe_id, recipe) in enumerate(rows[:6], 1):
            state = self._recipe_readiness_v0611(table, recipe)
            output_id = str(recipe.get("output") or "")
            output_name = ITEMS.get(output_id, {}).get("name", output_id or recipe.get("name", "produkt"))
            await self.send(f"RECEPTURA {idx}: {recipe.get('name') or output_name}. Produkt: {output_name}.")
            for ingredient_id, have, needed, missing in state["ingredient_rows"]:
                name = ITEMS.get(ingredient_id, {}).get("name", ingredient_id)
                await self.send(
                    f"{name}: masz {have}/{needed}; "
                    + (f"brakuje {missing}." if missing else "wystarcza.")
                )
            if state["distinct_pool"] and state["distinct_needed"]:
                missing = max(0, state["distinct_needed"] - state["distinct_have"])
                await self.send(
                    f"{recipe.get('distinct_ingredient_label', 'Różne składniki')}: masz "
                    f"{state['distinct_have']}/{state['distinct_needed']}; "
                    + (f"brakuje {missing} różnych rodzajów." if missing else "wystarcza.")
                )
            if state["pooled_pool"] and state["pooled_needed"]:
                missing = max(0, state["pooled_needed"] - state["pooled_have"])
                await self.send(
                    f"{recipe.get('pooled_ingredient_label', 'Składniki z puli')}: masz "
                    f"{state['pooled_have']}/{state['pooled_needed']}; "
                    + (f"brakuje {missing}." if missing else "wystarcza.")
                )
            await self.send(
                f"Profesja: {state['profession']} {state['profession_level']}/{state['required_profession']} — "
                + ("OK." if state["profession_level"] >= state["required_profession"] else "ZA NISKO.")
            )
            await self.send(
                f"Narzędzie: {state['tool_name']}; "
                + ("masz" if state["tool_owned"] else "BRAK")
                + f"; Tier {state['tool_tier']}/{state['required_tool_tier']} — "
                + ("OK." if state["tool_owned"] and state["tool_tier"] >= state["required_tool_tier"] else "NIE GOTOWE.")
            )
            station_text = _room_names_v0610(state["stations"]) if state["stations"] else "dowolne miejsce"
            await self.send(
                f"Miejsce: {station_text} — " + ("JESTEŚ NA MIEJSCU." if state["station_ok"] else "MUSISZ DOJŚĆ DO STACJI.")
            )
            if self.combat_mob_key:
                await self.send("Stan: walczysz — crafting jest teraz zablokowany.")
            await self.send("GOTOWOŚĆ: " + ("MOŻESZ WYKONAĆ TERAZ." if state["ready"] else "NIE MOŻESZ JESZCZE WYKONAĆ."))
        if len(rows) > 6:
            await self.send(f"Dodatkowe pasujące receptury: {len(rows) - 6}.")
        return True

    def _primary_recipe_row_v0614(self, item_id):
        rows = list(recipe_rows_for_output_v0611(item_id))
        if not rows:
            return None, []
        rows.sort(key=lambda row: (
            max(1, int(row[3].get("min_profession_level", row[3].get("min_tool_level", 1)) or 1)),
            normalize_lookup_text(str(row[3].get("name") or row[2])),
        ))
        return rows[0], rows[1:]

    async def _emit_recipe_route_v0614(self, item_id, needed, depth, stack, state):
        if state["nodes"] >= 80:
            if not state.get("limit_announced"):
                state["limit_announced"] = True
                await self.send("Dalsza droga została skrócona po 80 węzłach, żeby raport pozostał czytelny dla NVDA.")
            return
        state["nodes"] += 1
        item_id = _crafted_base_v0611(str(item_id))
        name = str(ITEMS.get(item_id, {}).get("name") or item_id)
        needed = max(1, int(needed))
        indent = "  " * max(0, depth - 1)
        if item_id in stack:
            await self.send(f"{indent}Poziom {depth}: {name} x{needed} — CYKL RECEPTUR, dalsze rozwijanie zatrzymane.")
            return
        if depth > 8:
            await self.send(f"{indent}Poziom {depth}: {name} x{needed} — osiągnięto limit głębokości 8.")
            return

        row, alternatives = self._primary_recipe_row_v0614(item_id)
        if row is None:
            sources = item_source_entries_v0610(item_id)
            await self.send(f"{indent}Poziom {depth}: {name} x{needed} — materiał końcowy / bez dalszej aktywnej receptury.")
            if sources:
                for _kind, source in sources[:3]:
                    await self.send(f"{indent}Źródło: {source}")
                if len(sources) > 3:
                    await self.send(f"{indent}Dodatkowe źródła: {len(sources)-3}.")
            else:
                await self.send(f"{indent}Źródło: brak jawnego źródła w aktywnych katalogach.")
            return

        _label, _table, _recipe_id, recipe = row
        output_qty = max(1, int(recipe.get("quantity", 1) or 1))
        crafts = (needed + output_qty - 1) // output_qty
        profession = str(recipe.get("profession") or self.recipe_profession_name(_table, recipe))
        await self.send(
            f"{indent}Poziom {depth}: {name} x{needed}. Receptura: {recipe.get('name') or name}; "
            f"wykonaj {crafts} razy; daje x{output_qty} na wykonanie; system: {profession}."
            + (f" Alternatywnych receptur: {len(alternatives)}." if alternatives else "")
        )
        next_stack = tuple(stack) + (item_id,)
        for ingredient_id, quantity in (recipe.get("ingredients") or {}).items():
            await self._emit_recipe_route_v0614(
                ingredient_id, max(1, int(quantity)) * crafts, depth + 1, next_stack, state
            )

        distinct_pool = tuple(recipe.get("distinct_ingredient_pool") or ())
        distinct_needed = max(0, int(recipe.get("distinct_ingredient_count", 0) or 0))
        if distinct_pool and distinct_needed:
            total = distinct_needed * crafts
            names = ", ".join(ITEMS.get(iid, {}).get("name", iid) for iid in distinct_pool[:10])
            await self.send(
                f"{indent}  Pula różnych składników: potrzeba {distinct_needed} różnych na craft, "
                f"czyli {total} wyborów dla {crafts} wykonań. Opcje: {names}"
                + (f" i jeszcze {len(distinct_pool)-10}." if len(distinct_pool)>10 else ".")
            )
        pooled_pool = tuple(recipe.get("pooled_ingredient_pool") or ())
        pooled_needed = max(0, int(recipe.get("pooled_ingredient_count", 0) or 0))
        if pooled_pool and pooled_needed:
            total = pooled_needed * crafts
            names = ", ".join(ITEMS.get(iid, {}).get("name", iid) for iid in pooled_pool[:10])
            await self.send(
                f"{indent}  Wspólna pula składników: potrzeba łącznie {total}. Opcje: {names}"
                + (f" i jeszcze {len(pooled_pool)-10}." if len(pooled_pool)>10 else ".")
            )

    async def show_recipe_route_v0614(self, args=""):
        query = _strip_recipe_route_prefix_v0614(args)
        if not query:
            await self.send("Użycie: receptura droga <przedmiot>. Pokazuje wielopoziomowy łańcuch produkcji aż do materiałów źródłowych.")
            return False
        item_id, item, suggestions = resolve_item_query_v0610(query)
        if item_id is None:
            rows, recipe_suggestions = resolve_recipe_query_v0611(query)
            if rows:
                item_id = str(rows[0][3].get("output") or "")
                item = ITEMS.get(item_id, {"name": item_id})
            else:
                suggestions = suggestions or [(str(r[3].get("output") or r[2]), ITEMS.get(str(r[3].get("output") or ""), {"name": r[3].get("name") or r[2]})) for r in recipe_suggestions]
        if not item_id:
            if suggestions:
                await self.send("Nazwa jest niejednoznaczna. Doprecyzuj przedmiot lub recepturę:")
                for number, (_sid, candidate) in enumerate(suggestions[:10], 1):
                    await self.send(f"{number}. {candidate.get('name', _sid)}.")
            else:
                await self.send("Nie znalazłem takiego produktu ani receptury w aktywnych danych gry.")
            return False
        name = str((item or ITEMS.get(item_id, {})).get("name") or item_id)
        await self.send(f"DROGA RECEPTURY: {name}. Cel: 1 sztuka produktu końcowego.")
        await self._emit_recipe_route_v0614(item_id, 1, 1, (), {"nodes":0})
        return True

    async def show_available_recipes_v0611(self, args=""):
        if self.combat_mob_key:
            await self.send("RECEPTURY MOŻLIWE: podczas walki nie możesz rozpocząć craftingu.")
            return True

        raw = normalize_lookup_text(str(args or "").strip())
        words = raw.split()
        if words and words[0] in ("mozliwe", "możliwe", "possible", "available"):
            words = words[1:]
        profession_filter = normalize_lookup_text(" ".join(words)) if words else ""
        profession_aliases = {
            "kowalstwo": "kowalstwo", "smithing": "kowalstwo", "blacksmithing": "kowalstwo",
            "gotowanie": "gotowanie", "cook": "gotowanie", "cooking": "gotowanie",
            "alchemia": "alchemia", "alchemy": "alchemia",
            "jubilerstwo": "jubilerstwo", "jewelcrafting": "jubilerstwo", "jewelry": "jubilerstwo",
            "krawiectwo": "krawiectwo", "tailoring": "krawiectwo",
            "garbarstwo": "garbarstwo", "leatherworking": "garbarstwo",
            "stolarstwo": "stolarstwo", "carpentry": "stolarstwo",
            "zaklinanie": "zaklinanie", "enchanting": "zaklinanie",
        }
        requested_profession = profession_aliases.get(profession_filter, "") if profession_filter else ""
        if profession_filter and not requested_profession:
            await self.send("Nie rozpoznaję profesji. Użyj: receptury mozliwe <kowalstwo|gotowanie|alchemia|jubilerstwo|krawiectwo|garbarstwo|stolarstwo|zaklinanie>.")
            return True

        ready = []
        for label, table, recipe_id, recipe in live_recipe_rows_v0611():
            state = self._recipe_readiness_v0611(table, recipe)
            if state["ready"]:
                profession = str(state["profession"])
                if requested_profession and normalize_lookup_text(profession) != requested_profession:
                    continue
                ready.append((profession, state["required_profession"], str(recipe.get("name") or recipe_id), label, recipe))
        ready.sort(key=lambda row: (normalize_lookup_text(row[0]), int(row[1]), normalize_lookup_text(row[2])))
        room_name = str(ROOMS.get(self.character.room_id, {}).get("name") or self.character.room_id)
        if requested_profession:
            await self.send(f"RECEPTURY MOŻLIWE TERAZ — {requested_profession.upper()}. Lokacja: {room_name}. Liczba: {len(ready)}.")
        else:
            await self.send(f"RECEPTURY MOŻLIWE TERAZ. Lokacja: {room_name}. Łącznie: {len(ready)}. Wyniki są rozdzielone według profesji.")
        if not ready:
            await self.send(
                "Nie masz tutaj receptury, dla której jednocześnie spełniasz składniki, poziom profesji, narzędzie, Tier narzędzia i wymaganą stację."
            )
            return True

        groups = {}
        for row in ready:
            groups.setdefault(row[0], []).append(row)
        shown_total = 0
        for profession in sorted(groups, key=normalize_lookup_text):
            rows = groups[profession]
            await self.send(f"{profession.upper()} — możliwe receptury: {len(rows)}.")
            # Zachowujemy ochronę przed ogromnym spamem NVDA, ale limit liczymy
            # osobno dla profesji, żeby jedna duża grupa nie ukrywała innych.
            for number, (_profession, required, name, _label, recipe) in enumerate(rows[:20], 1):
                output_id = str(recipe.get("output") or "")
                output_name = ITEMS.get(output_id, {}).get("name", output_id or name)
                await self.send(f"{number}. {name} -> {output_name}. Wymagany poziom {required}.")
                shown_total += 1
            if len(rows) > 20:
                await self.send(f"Dalsze możliwe receptury {profession}: {len(rows) - 20}. Użyj receptury lub nazwy profesji, aby zawęzić listę.")
        return True


__all__ = [
    "V0610_ITEM_SOURCE_VERSION",
    "V0611_CRAFT_GUIDANCE_VERSION",
    "V0614_CRAFTING_LOGISTICS_VERSION",
    "resolve_item_query_v0610",
    "item_source_entries_v0610",
    "live_recipe_rows_v0611",
    "recipe_rows_for_output_v0611",
    "item_use_entries_v0611",
    "resolve_recipe_query_v0611",
    "SessionItemSourcesV0610Mixin",
]
