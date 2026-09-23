# -*- coding: utf-8 -*-
"""Soulbound v0.31.14 — Forge & Materials 3.0."""
from data import catalog_mutations as _catalog_mut
from data.crafting_recipes import CRAFT_RECIPES
from data.items import ITEMS
from systems.tech_crafting import TECH_CRAFT_RECIPES
from network.protocol_gameplay_utils import CRAFT_MATERIAL_STORAGE_IDS
from world.expansions import REGIONAL_SET_BONUSES

# Refined materials.
_REFINED = {
    "hardened_steel_ingot": ("Hartowana Stal", "steel_ingot", 3, 80),
    "magitek_alloy": ("Stop Magitek", "hardened_steel_ingot", 2, 140),
    "astral_alloy": ("Astralny Stop", "astral_ingot", 3, 220),
    "eternium_alloy": ("Stop Eternium", "eternium_ingot", 3, 300),
}
for iid,(name,base,qty,level) in _REFINED.items():
    _catalog_mut.catalog_assign({"name":name,"type":"craft_material","price":None,"craftbox_category":"refining",
                "desc":f"Materiał Refining 2.0. Powstaje z {ITEMS.get(base,{}).get('name',base)} x{qty}."}, 'ITEMS', ITEMS, (iid,))
    _catalog_mut.catalog_assign({
        "name":name,"aliases":(name.lower(), iid.replace('_',' '), "refine "+name.lower()),
        "stations":("forge",),"ingredients":{base:qty},"output":iid,"quantity":1,
        "min_profession_level":level,"profession_xp":max(30,level//2),"tool_xp":max(24,level//3),
        "category":"refining","desc":"Refining 2.0 — zaawansowany stop do Forge/Tech Crafting."
    }, 'CRAFT_RECIPES', CRAFT_RECIPES, (f"refine_{iid}",))

# Socket consumable used by Socket Crafting.
_catalog_mut.catalog_assign({"name":"Rdzeń Gniazda","type":"craft_material","price":None,
    "craftbox_category":"runes","desc":"Zużywany przez Socket Crafting do dodania trwałego gniazda EQ."}, 'ITEMS', ITEMS, ("socket_core_v03114",))
_catalog_mut.catalog_assign({
    "name":"Rdzeń Gniazda","aliases":("rdzen gniazda","rdzeń gniazda","socket core"),"stations":("forge",),
    "ingredients":{"runestone_ingot":1,"reforge_essence":1,"soul_shard":5},"output":"socket_core_v03114","quantity":1,
    "min_profession_level":180,"profession_xp":80,"tool_xp":60,"category":"socketcraft",
    "desc":"Materiał do komendy socketcraft <EQ>."
}, 'CRAFT_RECIPES', CRAFT_RECIPES, ("socket_core_v03114",))

# Rune Crafting 2.0 costs: rune dust + a cut gem or technology component.
RUNE_CRAFT_COSTS_V03114={
    "moc":{"rune_dust":3,"cut_gem_ruby":1,"soul_shard":2},
    "ochrona":{"rune_dust":3,"cut_gem_sapphire":1,"soul_shard":2},
    "zycie":{"rune_dust":3,"cut_gem_diamond":1,"soul_shard":2},
    "mana":{"rune_dust":3,"cut_gem_amethyst":1,"soul_shard":2},
    "unik":{"rune_dust":3,"cut_gem_emerald":1,"soul_shard":2},
    "hart":{"rune_dust":4,"hardened_steel_ingot":1,"soul_shard":4},
    "impuls":{"rune_dust":4,"machine_power_cell":1,"soul_shard":4},
    "bariera":{"rune_dust":4,"magitek_alloy":1,"soul_shard":4},
    "rdzen":{"rune_dust":5,"machine_magitek_core":1,"soul_shard":6},
}
# Keep only gem IDs that actually exist in this build; fallback to rune dust for unknown legacy gem names.
for _key,_cost in list(RUNE_CRAFT_COSTS_V03114.items()):
    RUNE_CRAFT_COSTS_V03114[_key]={iid:q for iid,q in _cost.items() if iid in ITEMS}
    if "rune_dust" not in RUNE_CRAFT_COSTS_V03114[_key]: RUNE_CRAFT_COSTS_V03114[_key]["rune_dust"]=5

# Salvage 3.0: non-EQ technological products, boards, upgrade kits and boss components.
SALVAGE3_V03114={
    "cyborg_power_board":{"machine_circuit":2,"machine_power_cell":1},
    "cyborg_guard_board":{"machine_plating":2,"machine_circuit":1},
    "cyborg_target_board":{"machine_sensor":1,"machine_circuit":1},
    "mec_cooling_matrix":{"machine_cooling_unit":1,"machine_magitek_core":1},
    "engineer_upgrade_kit":{"machine_circuit":1,"machine_power_cell":1},
    "tech_magitek_chest":{"machine_plating":3,"machine_actuator":1},
    "tech_targeting_bracers":{"machine_plating":1,"machine_servo":1},
    "machine_magitek_core":{"machine_circuit":3,"machine_power_cell":2},
    "machine_moogle_alloy":{"machine_plating":2,"machine_servo":2},
    "machine_warmech_core":{"machine_circuit":4,"machine_power_cell":4,"machine_plating":3},
}

# Tech EQ sets: 8 unique slots each; regional_set engine is reused and extended to an 8/8 threshold.
TECH_SET_SPECS_V03114={
    "tech_mec":("Set Rdzenia Meca","Mec",None,{"hp":1.08,"damage":1.10,"defense":1.08,"complete":1.08}),
    "tech_engineer":("Set Inżyniera Magitek","Inżynier",None,{"hp":1.06,"damage":1.12,"defense":1.07,"complete":1.08}),
    "tech_cyborg":("Set Cyborga Omega",None,"Cyborg",{"hp":1.10,"damage":1.08,"defense":1.10,"complete":1.08}),
}
TECH_SET_SLOTS_V03114=("head","body","hands","legs","feet","shoulders","belt","bracers")
TECH_SET_SLOT_NAMES_V03114={"head":"Hełm","body":"Pancerz","hands":"Rękawice","legs":"Nogawice","feet":"Buty","shoulders":"Naramienniki","belt":"Pas","bracers":"Karwasze"}
TECH_SET_ITEMS_V03114={}
for set_id,(set_name,req_class,req_race,bonus) in TECH_SET_SPECS_V03114.items():
    REGIONAL_SET_BONUSES[set_id]={"name":set_name,**bonus}
    rows=[]
    for idx,slot in enumerate(TECH_SET_SLOTS_V03114):
        iid=f"{set_id}_{slot}"
        item={"name":f"{TECH_SET_SLOT_NAMES_V03114[slot]} — {set_name}","type":"armor","slot":slot,
              "defense":20+idx,"price":None,"required_mastery":220,"rarity":"tech","rarity_name":"Technologiczny",
              "regional_set":set_id,"sockets":1 if idx<4 else 2,
              "desc":f"Część technologicznego zestawu {set_name}. Bonusy aktywują się przy 2/4/6/8 częściach."}
        if req_class:
            item["required_class"]=req_class
            item["class_set_name"]=set_name
            item["stats"]={"strength":6,"constitution":6,"willpower":4} if req_class=="Mec" else {"strength":5,"constitution":5,"dexterity":6}
        if req_race: item["required_race"]=req_race
        _catalog_mut.catalog_assign(item, 'ITEMS', ITEMS, (iid,)); rows.append(iid)
        ingredients={"magitek_alloy":2,"machine_plating":2,"machine_circuit":1}
        if set_id=="tech_mec": ingredients["mec_cooling_matrix"]=1
        elif set_id=="tech_engineer": ingredients["engineer_upgrade_kit"]=1
        else: ingredients["machine_moogle_alloy"]=1
        _catalog_mut.catalog_assign({"name":item["name"],"aliases":(iid.replace('_',' '),),"stations":("forge",),
            "ingredients":ingredients,"output":iid,"quantity":1,"min_profession_level":220,
            "profession_xp":120,"tool_xp":80,"category":"tech_set","desc":f"Tech EQ Set — {set_name}."}, 'CRAFT_RECIPES', CRAFT_RECIPES, (f"craft_{iid}",))
    TECH_SET_ITEMS_V03114[set_id]=tuple(rows)

# V-MAX upgrade modules crafted through Tech Crafting.
for iid,name,desc in (
    ("vmax_duration_module","Moduł V-MAX: Przedłużenie","Wydłuża V-MAX o 10 sekund."),
    ("vmax_cooling_module","Moduł V-MAX: Chłodzenie","Skraca Overheat po V-MAX o 8 sekund."),
):
    _catalog_mut.catalog_assign({"name":name,"type":"craft_material","price":None,"craftbox_category":"technology","desc":desc}, 'ITEMS', ITEMS, (iid,))
TECH_CRAFT_RECIPES.update({
    "vmax_duration_module":{"name":"Moduł V-MAX: Przedłużenie","aliases":("vmax duration module","modul vmax przedluzenie"),"stations":("forge",),
      "ingredients":{"mec_cooling_matrix":1,"machine_power_cell":2,"magitek_alloy":1},"output":"vmax_duration_module","quantity":1,"min_profession_level":220,"profession_xp":110,"tool_xp":75,"category":"technology","desc":"Stały upgrade V-MAX: +10 s czasu."},
    "vmax_cooling_module":{"name":"Moduł V-MAX: Chłodzenie","aliases":("vmax cooling module","modul vmax chlodzenie"),"stations":("forge",),
      "ingredients":{"mec_cooling_matrix":1,"machine_cooling_unit":2,"astral_alloy":1},"output":"vmax_cooling_module","quantity":1,"min_profession_level":260,"profession_xp":130,"tool_xp":85,"category":"technology","desc":"Stały upgrade V-MAX: -8 s Overheat."},
})
for _rid,_r in TECH_CRAFT_RECIPES.items(): _catalog_mut.catalog_assign(_r, 'CRAFT_RECIPES', CRAFT_RECIPES, (f"tech_{_rid}",))

# Ensure all newly registered materials are routed to the Craftbox.
CRAFT_MATERIAL_STORAGE_IDS = frozenset(set(CRAFT_MATERIAL_STORAGE_IDS) | {iid for iid,item in ITEMS.items() if item.get("type")=="craft_material"})
