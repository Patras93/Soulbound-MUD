# -*- coding: utf-8 -*-
"""Soulbound v0.31.12 — Machine Salvage 2.0 + Tech Crafting + Runes/Sockets 2.0."""

TECH_COMPONENT_IDS = {
    "machine_servo", "machine_plating", "machine_circuit", "machine_sensor",
    "machine_power_cell", "machine_targeting_chip", "machine_actuator",
    "machine_cooling_unit", "machine_drone_core", "machine_magitek_core",
    "machine_moogle_alloy", "machine_warmech_core",
}
for _iid in TECH_COMPONENT_IDS:
    if _iid in ITEMS:
        ITEMS[_iid]["type"] = "craft_material"
        ITEMS[_iid]["craftbox_category"] = "technology"
        ITEMS[_iid]["machine_component"] = True
        ITEMS[_iid]["desc"] = ITEMS[_iid].get("desc", "") + " Trafia do Szkatułki -> Technologia i służy do Tech Crafting/Salvage."

# Craftable technology products.
_TECH_ITEMS = {
    "cyborg_power_board": {
        "name":"Power Board", "type":"armor", "slot":"board", "defense":0, "price":None,
        "required_race":"Cyborg", "stats":{"strength":6,"dexterity":3}, "rarity":"tech",
        "rarity_name":"Technologiczny", "desc":"Board Cyborga: +6 Siła, +3 Zręczność. Jeden aktywny Board naraz."
    },
    "cyborg_guard_board": {
        "name":"Guard Board", "type":"armor", "slot":"board", "defense":5, "price":None,
        "required_race":"Cyborg", "stats":{"constitution":6,"willpower":3}, "rarity":"tech",
        "rarity_name":"Technologiczny", "desc":"Board Cyborga: +6 Kondycja, +3 Siła Woli, obrona +5."
    },
    "cyborg_target_board": {
        "name":"Targeting Board", "type":"armor", "slot":"board", "defense":1, "price":None,
        "required_race":"Cyborg", "stats":{"dexterity":6,"intelligence":3},
        "properties":{"all_damage_pct":2}, "rarity":"tech", "rarity_name":"Technologiczny",
        "desc":"Board Cyborga: +6 Zręczność, +3 Inteligencja i +2% obrażeń."
    },
    "mec_cooling_matrix": {
        "name":"Matryca Chłodząca Meca", "type":"craft_material", "price":None,
        "craftbox_category":"technology", "desc":"Komponent Meca do stabilizacji rdzenia i technologicznych receptur."
    },
    "engineer_upgrade_kit": {
        "name":"Zestaw Upgrade Inżyniera", "type":"craft_material", "price":None,
        "craftbox_category":"technology", "desc":"Zużywany przy trwałym Upgrade narzędzia Inżyniera."
    },
    "tech_magitek_chest": {
        "name":"Pancerz Magitek", "type":"armor", "slot":"body", "defense":22, "price":None,
        "required_mastery":180, "affix":"constitution", "affix_amount":7,
        "sockets":2, "rarity":"tech", "rarity_name":"Technologiczny",
        "desc":"Technologiczny pancerz z gniazdami na klejnoty/runy. Wymaga Biegłości 180."
    },
    "tech_targeting_bracers": {
        "name":"Karwasze Celownicze Magitek", "type":"armor", "slot":"bracers", "defense":11, "price":None,
        "required_mastery":160, "affix":"dexterity", "affix_amount":6,
        "sockets":1, "rarity":"tech", "rarity_name":"Technologiczny",
        "desc":"Technologiczne karwasze z gniazdem. Wymaga Biegłości 160."
    },
}
ITEMS.update(_TECH_ITEMS)

TECH_CRAFT_RECIPES = {
    "power_board": {
        "name":"Power Board", "aliases":("power board","board mocy"), "stations":("forge",),
        "ingredients":{"machine_servo":2,"machine_circuit":2,"machine_power_cell":1},
        "output":"cyborg_power_board","quantity":1,"min_tool_level":120,"min_profession_level":120,
        "profession_xp":55,"tool_xp":45,"category":"technology","desc":"Technologiczny Board dla Cyborga."
    },
    "guard_board": {
        "name":"Guard Board", "aliases":("guard board","board ochrony"), "stations":("forge",),
        "ingredients":{"machine_plating":3,"machine_circuit":1,"machine_power_cell":1},
        "output":"cyborg_guard_board","quantity":1,"min_tool_level":140,"min_profession_level":140,
        "profession_xp":62,"tool_xp":50,"category":"technology","desc":"Defensywny Board dla Cyborga."
    },
    "targeting_board": {
        "name":"Targeting Board", "aliases":("targeting board","board celowniczy"), "stations":("forge",),
        "ingredients":{"machine_sensor":2,"machine_targeting_chip":1,"machine_circuit":2},
        "output":"cyborg_target_board","quantity":1,"min_tool_level":160,"min_profession_level":160,
        "profession_xp":70,"tool_xp":56,"category":"technology","desc":"Ofensywny Board dla Cyborga."
    },
    "mec_cooling_matrix": {
        "name":"Matryca Chłodząca Meca", "aliases":("cooling matrix","matryca chlodzaca","matryca chłodząca"),
        "stations":("forge",),"ingredients":{"machine_cooling_unit":2,"machine_magitek_core":1,"machine_moogle_alloy":1},
        "output":"mec_cooling_matrix","quantity":1,"min_tool_level":180,"min_profession_level":180,
        "profession_xp":78,"tool_xp":62,"category":"technology","desc":"Komponent technologiczny Meca."
    },
    "engineer_upgrade_kit": {
        "name":"Zestaw Upgrade Inżyniera", "aliases":("engineer upgrade kit","upgrade kit","zestaw upgrade"),
        "stations":("forge",),"ingredients":{"machine_circuit":2,"machine_targeting_chip":1,"machine_power_cell":2},
        "output":"engineer_upgrade_kit","quantity":1,"min_tool_level":120,"min_profession_level":120,
        "profession_xp":55,"tool_xp":45,"category":"technology","desc":"Materiał wymagany przez trwały Upgrade narzędzia Inżyniera."
    },
    "magitek_chest": {
        "name":"Pancerz Magitek", "aliases":("magitek armor","pancerz magitek"), "stations":("forge",),
        "ingredients":{"machine_plating":5,"machine_actuator":2,"machine_power_cell":2,"machine_magitek_core":1},
        "output":"tech_magitek_chest","quantity":1,"min_tool_level":180,"min_profession_level":180,
        "profession_xp":90,"tool_xp":72,"category":"technology","desc":"Technologiczny pancerz z dwoma gniazdami."
    },
    "targeting_bracers": {
        "name":"Karwasze Celownicze Magitek", "aliases":("targeting bracers","karwasze celownicze"), "stations":("forge",),
        "ingredients":{"machine_plating":2,"machine_targeting_chip":1,"machine_servo":2},
        "output":"tech_targeting_bracers","quantity":1,"min_tool_level":160,"min_profession_level":160,
        "profession_xp":72,"tool_xp":58,"category":"technology","desc":"Technologiczne karwasze z jednym gniazdem."
    },
}
for _rid,_recipe in TECH_CRAFT_RECIPES.items():
    CRAFT_RECIPES[f"tech_{_rid}"] = _recipe

TECH_SALVAGE_RECIPES = {
    "machine_sensor": {"machine_circuit":2},
    "machine_targeting_chip": {"machine_circuit":2,"machine_power_cell":1},
    "machine_actuator": {"machine_servo":2,"machine_plating":1},
    "machine_cooling_unit": {"machine_plating":1,"machine_circuit":2},
    "machine_drone_core": {"machine_circuit":2,"machine_power_cell":2,"machine_servo":1},
    "machine_magitek_core": {"machine_circuit":3,"machine_power_cell":3,"machine_plating":1},
    "machine_moogle_alloy": {"machine_plating":3,"machine_servo":2},
    "machine_warmech_core": {"machine_circuit":5,"machine_power_cell":5,"machine_plating":4,"machine_servo":3},
}

# General gem socket capacity: jewelry keeps legacy rules, crafted/endgame armor gains sockets too.
def equipment_gem_socket_capacity_v03111(item):
    if not item or item.get("type") != "armor":
        return 0
    explicit=item.get("sockets")
    if explicit is not None:
        return max(0,int(explicit))
    if item.get("slot") in ("ring","necklace","earring"):
        return jewelry_socket_capacity(item)
    mastery=int(item.get("required_mastery",0) or 0)
    if mastery>=400: return 3
    if mastery>=300: return 2
    if mastery>=200: return 1
    return 0
