# -*- coding: utf-8 -*-
"""Soulbound v0.61.0 — item acquisition source finder.

Read-only, NVDA-friendly lookup over the assembled runtime catalogs.  The
command never guesses a source: every line is derived from active shops,
recipes, quests, mob templates/spawns or profession resource atlases.
"""
from __future__ import annotations

from collections import defaultdict

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
from network.protocol_gameplay_utils import normalize_lookup_text
from systems.content_registry import MOB_SPAWNS, MOB_TEMPLATES, NPCS, QUESTS
from systems.equipment_crafting import (
    ALCHEMY_RECIPES,
    COOK_RECIPES,
    CRAFT_RECIPES,
    JEWELCRAFT_RECIPES,
    SHOPS,
    SHOP_SELLERS,
)
from systems.items_resources import fish_unlock_level
from systems.professions import V03053_CRAFT_RECIPES

V0610_ITEM_SOURCE_VERSION = "0.61.0"


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


def _strip_lookup_prefix_v0610(args):
    raw = str(args or "").strip()
    words = raw.split(maxsplit=1)
    if words and normalize_lookup_text(words[0]) in {"zdobyc", "zdobadz", "get", "find"}:
        return words[1].strip() if len(words) > 1 else ""
    return raw


class SessionItemSourcesV0610Mixin:
    async def show_item_sources_v0610(self, args=""):
        query = _strip_lookup_prefix_v0610(args)
        if not query:
            await self.send(
                "Użycie: gdzie zdobyc <przedmiot>. Przykład: gdzie zdobyc Mikstura leczenia."
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
        return True


__all__ = [
    "V0610_ITEM_SOURCE_VERSION",
    "resolve_item_query_v0610",
    "item_source_entries_v0610",
    "SessionItemSourcesV0610Mixin",
]
