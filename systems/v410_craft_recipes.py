# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def _register_blacksmith_recipes():
    # Existing first three ingot recipes become proper
    # Kowalstwo recipes without changing their output IDs.
    basic_requirements = {
        "iron_ingot": (1, 1, 10),
        "silver_ingot": (20, 20, 14),
        "gold_ingot": (40, 40, 18),
    }
    for recipe_id, (
        tool_level, profession_level, profession_xp
    ) in basic_requirements.items():
        recipe = CRAFT_RECIPES[recipe_id]
        recipe["category"] = "smithing"
        recipe["min_tool_level"] = tool_level
        recipe["min_profession_level"] = profession_level
        recipe["profession_xp"] = profession_xp
        recipe["tool_xp"] = max(
            8, int(profession_xp * 0.8)
        )

    for tier_number, tier in enumerate(BLACKSMITH_TIERS, 1):
        ingot_id = tier["ingot"]

        if ingot_id not in {
            "iron_ingot", "silver_ingot", "gold_ingot"
        }:
            _catalog_mut.catalog_assign({
                "name": ITEMS[ingot_id]["name"],
                "stations": ("forge",),
                "ingredients": {
                    tier["ore"]: 1,
                },
                "output": ingot_id,
                "quantity": 1,
                "min_tool_level": tier["tool_level"],
                "min_profession_level": tier[
                    "profession_level"
                ],
                "profession_xp": (
                    16 + tier_number * 4
                ),
                "tool_xp": (
                    12 + tier_number * 4
                ),
                "category": "smithing",
                "desc": (
                    f"Przetop 1 sztukę surowca "
                    f"{ITEMS[tier['ore']]['name']} "
                    f"w 1 sztabkę."
                ),
            }, 'CRAFT_RECIPES', CRAFT_RECIPES, (ingot_id,))

        for slot, (
            slot_name, _def_delta, ingot_cost
        ) in BLACKSMITH_SLOT_DEFS.items():
            output_id = (
                f"smith_{tier['key']}_{slot}"
            )
            recipe_id = (
                f"forge_{tier['key']}_{slot}"
            )
            _catalog_mut.catalog_assign({
                "name": ITEMS[output_id]["name"],
                "stations": ("forge",),
                "ingredients": {
                    ingot_id: ingot_cost,
                },
                "output": output_id,
                "quantity": 1,
                "min_tool_level": tier["tool_level"],
                "min_profession_level": tier[
                    "profession_level"
                ],
                "profession_xp": (
                    20 + tier_number * 6
                ),
                "tool_xp": (
                    15 + tier_number * 5
                ),
                "category": "smithing",
                "desc": (
                    f"Wykuj {slot_name.lower()} z materiału "
                    f"{tier['name']}. "
                    f"Wymaga Kowalstwa level "
                    f"{tier['profession_level']}."
                ),
            }, 'CRAFT_RECIPES', CRAFT_RECIPES, (recipe_id,))


def _register_jewelcrafting_recipes():
    for tier in JEWELCRAFTING_TIERS:
        ring_id = f"jewel_{tier['key']}_ring"
        necklace_id = f"jewel_{tier['key']}_necklace"
        earring_id = f"jewel_{tier['key']}_earring"
        socket_count = 3 if tier["level"] >= 180 else 2 if tier["level"] >= 100 else 1
        earring_sockets = 2 if tier["level"] >= 180 else 1

        _catalog_mut.catalog_assign({
            "name": f"{tier['label']} Pierścień Jubilerski", "type": "armor", "slot": "ring",
            "defense": tier["defense"], "price": None, "rarity": "crafted", "rarity_name": "Jubilerski",
            "equipment_identity_source": "jewelcraft",
            "equipment_identity_role": "sockets_and_affix",
            "equipment_identity_label": "Jubilerstwo — gniazda i precyzyjny affix",
            "affix": tier["affix"], "affix_amount": tier["affix_amount"], "jewelcraft_level": tier["level"],
            "sockets": socket_count,
            "desc": f"Pierścień wykonany przez Jubilerstwo. Wymaga Jubilerstwa level {tier['level']}. Obrona +{tier['defense']}.",
        }, 'ITEMS', ITEMS, (ring_id,))
        _catalog_mut.catalog_assign({
            "name": f"{tier['label']} Naszyjnik Jubilerski", "type": "armor", "slot": "necklace",
            "defense": tier["defense"] + 1, "price": None, "rarity": "crafted", "rarity_name": "Jubilerski",
            "equipment_identity_source": "jewelcraft",
            "equipment_identity_role": "sockets_and_affix",
            "equipment_identity_label": "Jubilerstwo — gniazda i precyzyjny affix",
            "affix": tier["affix"], "affix_amount": tier["affix_amount"] + 1, "jewelcraft_level": tier["level"],
            "sockets": socket_count,
            "desc": f"Naszyjnik wykonany przez Jubilerstwo. Wymaga Jubilerstwa level {tier['level']}. Obrona +{tier['defense'] + 1}.",
        }, 'ITEMS', ITEMS, (necklace_id,))
        # Kolczyk ma inny profil: mniej obrony, więcej ofensywnego affixu. Dwie sztuki można nosić naraz.
        _catalog_mut.catalog_assign({
            "name": f"{tier['label']} Kolczyk Jubilerski", "type": "armor", "slot": "earring",
            "defense": max(0, tier["defense"] - 1), "price": None, "rarity": "crafted", "rarity_name": "Jubilerski",
            "equipment_identity_source": "jewelcraft",
            "equipment_identity_role": "sockets_and_affix",
            "equipment_identity_label": "Jubilerstwo — gniazda i precyzyjny affix",
            "affix": tier["affix"], "affix_amount": tier["affix_amount"] + 1, "jewelcraft_level": tier["level"],
            "sockets": earring_sockets,
            "desc": f"Kolczyk wykonany przez Jubilerstwo. Można nosić dwie sztuki. Wymaga Jubilerstwa level {tier['level']}.",
        }, 'ITEMS', ITEMS, (earring_id,))

        base_xp = 12 + tier["level"] // 8
        JEWELCRAFT_RECIPES[ring_id] = {
            "name": ITEMS[ring_id]["name"], "stations": ("jeweler_workshop",), "ingredients": {tier["material"]: 2},
            "output": ring_id, "quantity": 1, "min_tool_level": tier["level"], "min_profession_level": tier["level"],
            "profession_xp": base_xp, "tool_xp": max(8, base_xp - 2),
            "desc": f"Jubilerstwo level {tier['level']}. Wykonuje pierścień z 2 sztuk materiału.",
        }
        JEWELCRAFT_RECIPES[necklace_id] = {
            "name": ITEMS[necklace_id]["name"], "stations": ("jeweler_workshop",), "ingredients": {tier["material"]: 3},
            "output": necklace_id, "quantity": 1, "min_tool_level": tier["level"], "min_profession_level": tier["level"],
            "profession_xp": base_xp + 3, "tool_xp": max(9, base_xp),
            "desc": f"Jubilerstwo level {tier['level']}. Wykonuje naszyjnik z 3 sztuk materiału.",
        }
        JEWELCRAFT_RECIPES[earring_id] = {
            "name": ITEMS[earring_id]["name"], "stations": ("jeweler_workshop",), "ingredients": {tier["material"]: 2},
            "output": earring_id, "quantity": 1, "min_tool_level": tier["level"], "min_profession_level": tier["level"],
            "profession_xp": base_xp + 1, "tool_xp": max(8, base_xp - 1),
            "desc": f"Jubilerstwo level {tier['level']}. Wykonuje jeden kolczyk z 2 sztuk materiału; do obu uszu potrzebujesz dwóch sztuk.",
        }

