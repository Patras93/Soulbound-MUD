# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def _register_gem_system():
    for definition in GEM_DEFINITIONS:
        raw_id = f"raw_gem_{definition['key']}"
        cut_id = f"cut_gem_{definition['key']}"
        RAW_GEM_IDS.add(raw_id)
        CUT_GEM_IDS.add(cut_id)

        # v0.8.67: surowe klejnoty są częścią urobku Górnictwa.
        # Trafiają do Sakwy Górnika i mogą zostać sprzedane wyłącznie Dagnie.
        raw_gem_sell_gold = {
            "ruby": 1,
            "sapphire": 3,
            "emerald": 6,
            "amethyst": 12,
            "diamond": 25,
            "soul_topaz": 45,
            "mana_opal": 75,
            "dragon_garnet": 120,
            "astral_crystal": 180,
            "void_onyx": 280,
            "eternium_prism": 450,
        }
        _catalog_mut.catalog_assign({
            "name": definition["raw_name"],
            "type": "gem_raw",
            "price": None,
            "sell_gold": raw_gem_sell_gold[definition["key"]],
            "gem_key": definition["key"],
            "gem_level": definition["level"],
            "mining_bag_resource": True,
            "desc": (
                f"Surowy kamień szlachetny z Górnictwa. "
                f"Trafia do Sakwy Górnika. Dagna skupuje go na Górskim Targu Minerałów. "
                f"Szlifowanie wymaga Jubilerstwa i Szczypiec "
                f"Jubilerskich level {definition['level']}."
            ),
        }, 'ITEMS', ITEMS, (raw_id,))
        _catalog_mut.catalog_assign({
            "name": definition["cut_name"],
            "type": "gem",
            "price": None,
            "gem_key": definition["key"],
            "gem_level": definition["level"],
            "affix": definition["affix"],
            "affix_amount": definition["amount"],
            "desc": (
                f"Osadzany klejnot jubilerski. "
                f"Bonus po osadzeniu: "
                f"{GEM_AFFIX_NAMES.get(definition['affix'], definition['affix'])} "
                f"+{definition['amount']}."
            ),
        }, 'ITEMS', ITEMS, (cut_id,))

        JEWELCRAFT_RECIPES[f"cut_{definition['key']}"] = {
            "name": definition["cut_name"],
            "aliases": (
                definition["raw_name"],
                definition["key"],
            ),
            "stations": ("jeweler_workshop",),
            "ingredients": {raw_id: 1},
            "output": cut_id,
            "quantity": 1,
            "min_tool_level": definition["level"],
            "min_profession_level": definition["level"],
            "profession_xp": 10 + definition["level"] // 5,
            "tool_xp": 8 + definition["level"] // 6,
            "gem_cut_recipe": True,
            "desc": (
                f"Szlifowanie kamienia. Jubilerstwo level "
                f"{definition['level']}."
            ),
        }


def _register_gem_quality_variants():
    for definition in GEM_DEFINITIONS:
        key = definition["key"]
        base_raw_id = f"raw_gem_{key}"
        base_sell = int(ITEMS[base_raw_id].get("sell_gold", 0) or 0)
        base_name = definition["raw_name"].replace("Surowy ", "", 1)
        cut_base_name = definition["cut_name"].replace("Szlifowany ", "", 1)
        for quality in GEM_QUALITY_ORDER[1:]:
            info = GEM_QUALITY_INFO[quality]
            raw_id = gem_quality_item_id("raw", key, quality)
            cut_id = gem_quality_item_id("cut", key, quality)
            raw_name = f"{info['label']} {base_name}"
            cut_name = f"{info['cut_label']} {cut_base_name}"
            RAW_GEM_IDS.add(raw_id)
            CUT_GEM_IDS.add(cut_id)
            _catalog_mut.catalog_assign({
                "name": raw_name, "type": "gem_raw", "price": None,
                "sell_gold": max(1, int(round(base_sell * info["sell_mult"]))),
                "gem_key": key, "gem_level": definition["level"],
                "gem_quality": quality, "mining_bag_resource": True,
                "desc": (
                    f"{info['label']} wariant kamienia z Górnictwa. Trafia do Sakwy Górnika. "
                    f"Szlifowanie wymaga Jubilerstwa level {definition['level']}."
                ),
            }, 'ITEMS', ITEMS, (raw_id,))
            amount = gem_quality_amount(definition["amount"], quality)
            _catalog_mut.catalog_assign({
                "name": cut_name, "type": "gem", "price": None,
                "gem_key": key, "gem_level": definition["level"],
                "gem_quality": quality, "affix": definition["affix"],
                "affix_amount": amount,
                "desc": (
                    f"Klejnot jakości {info['label'].lower()}. Bonus po osadzeniu: "
                    f"{GEM_AFFIX_NAMES.get(definition['affix'], definition['affix'])} +{amount}."
                ),
            }, 'ITEMS', ITEMS, (cut_id,))
            recipe_id = f"cut_{key}_{quality}"
            JEWELCRAFT_RECIPES[recipe_id] = {
                "name": cut_name,
                "aliases": (raw_name, cut_name, f"{quality} {key}"),
                "stations": ("jeweler_workshop",),
                "ingredients": {raw_id: 1},
                "output": cut_id, "quantity": 1,
                "min_tool_level": definition["level"],
                "min_profession_level": definition["level"],
                "profession_xp": 12 + definition["level"] // 5 + GEM_QUALITY_ORDER.index(quality) * 3,
                "tool_xp": 10 + definition["level"] // 6 + GEM_QUALITY_ORDER.index(quality) * 2,
                "gem_cut_recipe": True,
                "desc": f"Szlifowanie jakości {info['label'].lower()}. Jubilerstwo level {definition['level']}.",
            }

