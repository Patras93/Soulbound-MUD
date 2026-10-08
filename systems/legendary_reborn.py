# -*- coding: utf-8 -*-
"""Legendary Loot & Crafting Reborn v1.15.0.

Existing class sets and authored drops remain intact. This layer only adds
rare boss materials, optional chase relics and reproducible crafting perks.
"""
from __future__ import annotations

import hashlib
import random
from data import catalog_mutations as _catalog_mut
from data.items import ITEMS

VERSION = "1.15.0"
SPARK = "leg115_iskra_legendarna"
HEART = "leg115_serce_pradawne"

# ID -> (item data, recipe table, profession, tool, workshop, level, ingredients)
LEGENDARY_FORGE = {
    "leg115_aegis_pustki": (
        {"name":"Egida Serca Pustki", "type":"armor", "slot":"shield", "defense":160,
         "stats":{"strength":130,"constitution":190,"willpower":120},
         "properties":{"physical_defense_pct":12,"magic_defense_pct":10,"lifesteal_percent":1.5},
         "element_wards":{"void":0.12},"sockets":3},
        "craft", "Kowalstwo", "crafting", "crafting_hammer", "forge",400,
        {SPARK:2, HEART:1, "ingot_400_400":6, "wood_400_400":2}),
    "leg115_korona_otchlani": (
        {"name":"Korona Pradawnego Lewiatana", "type":"armor", "slot":"head", "defense":95,
         "stats":{"intelligence":160,"willpower":160,"constitution":120},
         "properties":{"magic_damage_pct":11,"max_mana_pct":14,"mana_restore_percent":1.5},
         "element_wards":{"shadow":0.12},"sockets":3},
        "jewel", "Jubilerstwo", "jewelcrafting", "jeweler_pliers", "jeweler_workshop",400,
        {SPARK:2, HEART:1, "fish_400_ocean_400":2, "ingot_400_400":2}),
    "leg115_totem_korzeni": (
        {"name":"Totem Wiecznego Korzenia", "type":"armor", "slot":"charm", "defense":80,
         "stats":{"strength":120,"dexterity":140,"constitution":160},
         "properties":{"physical_damage_pct":10,"max_hp_pct":12,"lifesteal_percent":1.0},
         "element_wards":{"holy":0.08},"sockets":3},
        "extended", "Stolarstwo", "carpentry", "carpenter_tools", "carpenter_workshop",400,
        {SPARK:2, HEART:1, "wood_400_400":5, "herb_400_400":3}),
    "leg115_plaszcz_zmierzchu": (
        {"name":"Płaszcz Pradawnego Zmierzchu", "type":"armor", "slot":"cloak", "defense":90,
         "stats":{"dexterity":150,"intelligence":150,"willpower":100},
         "properties":{"dodge_pct":8,"all_damage_pct":8,"mana_restore_percent":1.0},
         "element_wards":{"shadow":0.14},"sockets":3},
        "extended", "Krawiectwo", "tailoring", "tailor_kit", "tailor_workshop",400,
        {SPARK:2, HEART:1, "herb_400_400":4, "woven_cloth":8}),
    "leg115_pierscien_swiatla": (
        {"name":"Pierścień Zarania", "type":"armor", "slot":"ring", "defense":72,
         "stats":{"strength":120,"intelligence":120,"willpower":130},
         "properties":{"all_damage_pct":9,"magic_defense_pct":8,"mana_restore_percent":1.0},
         "element_wards":{"holy":0.14},"sockets":3},
        "jewel", "Jubilerstwo", "jewelcrafting", "jeweler_pliers", "jeweler_workshop",500,
        {SPARK:3, HEART:2, "ingot_400_500":3, "herb_400_500":3}),
}

# Loot-only relics with distinct active equipment effects.
CHASE_RELICS = {
    "leg1230_amulet_potegi": {
        "name":"Amulet Nieposkromionej Potęgi", "type":"armor", "slot":"necklace", "defense":170,
        "stats":{"strength":280,"intelligence":280,"constitution":190},
        "properties":{"all_damage_pct":18,"max_hp_pct":12}, "element_wards":{"void":0.12}, "sockets":4,
    },
    "leg1230_korona_synergii": {
        "name":"Korona Jedności Żywiołów", "type":"armor", "slot":"head", "defense":160,
        "stats":{"dexterity":220,"willpower":260,"constitution":220},
        "properties":{"physical_damage_pct":13,"magic_damage_pct":13,"dodge_pct":7},
        "element_wards":{"fire":0.10,"ice":0.10,"lightning":0.10}, "sockets":4,
    },
    "leg1230_pierscien_odnowy": {
        "name":"Pierścień Nieskończonej Odnowy", "type":"armor", "slot":"ring", "defense":190,
        "stats":{"constitution":340,"intelligence":170,"strength":170},
        "properties":{"lifesteal_percent":3.5,"mana_restore_percent":2.5,"all_damage_pct":8},
        "element_wards":{"shadow":0.15}, "sockets":4,
    },
    "leg115_relikt_wampira": {
        "name":"Relikt Krwawej Gwiazdy", "type":"armor", "slot":"charm", "defense":90,
        "stats":{"strength":110,"dexterity":110,"constitution":110},
        "properties":{"all_damage_pct":7,"lifesteal_percent":2.0},"sockets":3,
    },
    "leg115_relikt_syfonu": {
        "name":"Relikt Astralnego Syfonu", "type":"armor", "slot":"necklace", "defense":80,
        "stats":{"intelligence":145,"willpower":135},
        "properties":{"magic_damage_pct":9,"mana_restore_percent":2.0},"sockets":3,
    },
    "leg115_relikt_strazy": {
        "name":"Pieczęć Strażnika Głębi", "type":"armor", "slot":"ring", "defense":110,
        "stats":{"constitution":185,"willpower":100},
        "properties":{"max_hp_pct":12,"physical_defense_pct":9},
        "element_wards":{"void":0.10,"shadow":0.10},"sockets":3,
    },
}


_STAT_LABELS_V1150 = {"strength":"Siła", "dexterity":"Zręczność", "constitution":"Kondycja", "intelligence":"Inteligencja", "willpower":"Siła Woli"}
_PROPERTY_LABELS_V1150 = {"physical_damage_pct":"obrażenia fizyczne", "magic_damage_pct":"obrażenia magiczne", "all_damage_pct":"wszystkie obrażenia", "physical_defense_pct":"obrona fizyczna", "magic_defense_pct":"obrona magiczna", "max_hp_pct":"HP", "max_mana_pct":"Mana", "dodge_pct":"unik", "lifesteal_percent":"wysysanie życia przy ataku", "mana_restore_percent":"odzyskanie Many przy ataku"}

def legendary_description_v1150(item):
    """Human/NVDA-readable real bonuses, not just a vague legendary label."""
    parts=[f"Obrona +{int(item.get('defense',0) or 0)}"]
    for stat,amt in (item.get("stats") or {}).items():
        parts.append(f"{_STAT_LABELS_V1150.get(stat,stat)} +{int(amt)}")
    for prop,amt in (item.get("properties") or {}).items():
        parts.append(f"{_PROPERTY_LABELS_V1150.get(prop,prop)} +{float(amt):g}%")
    for element,ward in (item.get("element_wards") or {}).items():
        parts.append(f"Odporność {element} {float(ward)*100:g}%")
    parts.append(f"Gniazda: {int(item.get('sockets',0) or 0)}")
    return "; ".join(parts)+"."

def register_legendary_content_v1150(craft_recipes, jewel_recipes):
    materials = {
        SPARK: {"name":"Iskra Legendy", "type":"resource", "price":None, "sell_gold":100,
                "rarity":"legendary", "rarity_name":"Legendarna", "desc":"Rzadki łup z bossa, potrzebny do legendarnego craftingu."},
        HEART: {"name":"Pradawne Serce Bossa", "type":"resource", "price":None, "sell_gold":500,
                "rarity":"mythic", "rarity_name":"Mityczne", "desc":"Wyjątkowy katalizator do legendarnego EQ."},
    }
    for item_id, data in materials.items():
        _catalog_mut.catalog_assign(dict(data), "ITEMS", ITEMS, (item_id,))
    for item_id, data in CHASE_RELICS.items():
        item = dict(data)
        item.update({"rarity":"legendary","rarity_name":"Legendarny", "price":None,
                     "required_mastery":200, "legendary_reborn_v1150":True,
                     "desc":"Wyjątkowy relikt bossa. " + legendary_description_v1150(item)})
        _catalog_mut.catalog_assign(item, "ITEMS", ITEMS, (item_id,))
    for item_id,(source,kind,prof,tool,tool_id,room,level,materials) in LEGENDARY_FORGE.items():
        item = dict(source)
        item.update({"rarity":"legendary", "rarity_name":"Legendarny", "price":None,
                     "generator_level":level, "required_mastery":level,
                     "legendary_reborn_v1150":True,
                     "desc":f"Unikalna receptura {prof} poziom {level}. " + legendary_description_v1150(item)})
        _catalog_mut.catalog_assign(item, "ITEMS", ITEMS, (item_id,))
        if kind not in ("craft", "jewel"):
            continue
        entry = {"name":item["name"],"profession":prof, "tool_type":tool,
                 "tool_item_id":tool_id,"tool_name":ITEMS[tool_id]["name"],
                 "stations":(room,), "min_profession_level":level,
                 "min_tool_level":level,"ingredients":dict(materials),
                 "output":item_id,"quantity":1,"generator_level":level,
                 "profession_xp":level*8,"tool_xp":level*5,
                 "category":tool,"desc":item["desc"]}
        table = craft_recipes if kind == "craft" else jewel_recipes
        _catalog_mut.catalog_assign(entry,"CRAFT_RECIPES",table,(item_id,),owner="systems.legendary_reborn") if kind == "craft" else table.__setitem__(item_id,entry)


def register_extended_legendary_recipes_v1150(extended):
    for item_id,(_source, kind, prof,tool,tool_id,room,level,materials) in LEGENDARY_FORGE.items():
        if kind != "extended":
            continue
        extended[item_id] = {"name":ITEMS[item_id]["name"], "profession":prof,
            "tool_type":tool,"tool_item_id":tool_id,"tool_name":ITEMS[tool_id]["name"],
            "stations":(room,),"min_profession_level":level,"min_tool_level":level,
            "ingredients":dict(materials),"output":item_id,"quantity":1,
            "profession_xp":level*8,"tool_xp":level*5,
            "generator_level":level,"desc":ITEMS[item_id]["desc"]}


def boss_legendary_roll_v1150(template, rng=None):
    """One shared optional roll, with no modification to existing authored loot.

    Called only after confirmed boss kills. Passing rng makes tests deterministic.
    """
    rng = rng or random
    t=template or {}
    superboss=bool(t.get("uoss_unique_superboss_key") or t.get("uoss_superboss"))
    floor=max(0, *[int(t.get(k,0) or 0) for k in (
        "crypt_floor","mythic_crypt_floor","astral_floor","mythic_astral_floor","magitek_floor")])
    stage=max(1,int(t.get("generator_level",t.get("recommended_level",t.get("level",1))) or 1))
    if not superboss and not floor and stage < 50:
        return None
    depth_bonus=min(0.06, floor/20000.0)
    # A shared boss reward is rolled once, then awarded to all party members.
    if rng.random() < (0.12 if superboss else 0.06) + depth_bonus:
        return SPARK
    if (superboss or floor>=100 or stage>=200) and rng.random() < (0.05 if superboss else 0.012) + depth_bonus/3:
        return HEART
    if (superboss or floor>=100 or stage>=200) and rng.random() < (0.075 if superboss else 0.018) + depth_bonus/2:
        return rng.choice(tuple(CHASE_RELICS))
    return None


_CRAFT_PERKS = (
    ("Krwawy rezonans", "lifesteal_percent"),
    ("Splot Many", "mana_restore_percent"),
    ("Ostrze Przeznaczenia", "all_damage_pct"),
    ("Zasłona Cienia", "dodge_pct"),
    ("Pancerz Pradawnych", "physical_defense_pct"),
)

def apply_legendary_craft_perk_v1150(data, variant_id, quality_key):
    """Self-describing craftq ID deterministically restores perks after restart."""
    if quality_key not in ("masterwork","legendary"):
        return None
    stamp=hashlib.sha256(str(variant_id).encode("utf-8")).digest()
    name,key=_CRAFT_PERKS[stamp[0] % len(_CRAFT_PERKS)]
    amount=1.25 if quality_key=="masterwork" else 2.5
    props=dict(data.get("properties") or {})
    props[key]=round(float(props.get(key,0) or 0)+amount,2)
    data["properties"]=props
    data["legendary_perk_v1150"]=name
    data["desc"]=(str(data.get("desc") or "")+f" Właściwość: {name} +{amount:g}%.").strip()
    return name


def legendary_reborn_audit_v1150(craft_recipes,jewel_recipes,extended):
    errors=[]
    for item_id,(_data,kind,_p,_tool,_tool_id,_room,_lvl,needs) in LEGENDARY_FORGE.items():
        if item_id not in ITEMS: errors.append(f"missing item {item_id}")
        table={"craft":craft_recipes,"jewel":jewel_recipes,"extended":extended}[kind]
        if item_id not in table: errors.append(f"missing recipe {item_id}")
        if not all(x in ITEMS for x in needs): errors.append(f"missing materials {item_id}")
        if not (ITEMS.get(item_id) or {}).get("properties"): errors.append(f"missing properties {item_id}")
    for item_id in (*CHASE_RELICS,SPARK,HEART):
        if item_id not in ITEMS: errors.append(f"missing loot {item_id}")
    return {"checks":len(LEGENDARY_FORGE)+len(CHASE_RELICS)+2, "errors":errors}
