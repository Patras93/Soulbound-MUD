# -*- coding: utf-8 -*-
"""Soulbound 6.00: eight profession systems; no account data is replaced."""
from dataclasses import dataclass
from typing import Tuple

TIERS = (1, 25, 75, 150, 300, 500, 700)
# Tier materials are genuine inputs or products of other professions, no free crafted goods.
PROFESSIONS = {
 "Łowiectwo": ("hunting", "hunting_knife", "Nóż Łowiecki"),
 "Rolnictwo": ("farming", "farming_hoe", "Motyka Rolnicza"),
 "Hodowla zwierząt": ("animal_husbandry", "husbandry_kit", "Przybory Hodowlane"),
 "Okrętownictwo": ("shipbuilding", "shipwright_hammer", "Młot Okrętowy"),
 "Murarstwo": ("masonry", "mason_trowel", "Kielnia Murarska"),
 "Inżynieria": ("engineering", "engineer_kit", "Zestaw Inżynierski"),
 "Kupiectwo": ("trading", "merchant_scale", "Waga Kupiecka"),
 "Żeglarstwo": ("sailing", "navigation_sextant", "Sekstant Nawigacyjny"),
}

# Regional roles, never require a duplicate of an existing NPC.
AREAS = {
 "wild": {"meadow", "mint_meadow", "flower_meadow", "whisper_grove", "deep_grove", "hill", "old_road", "crossroads", "riverbank", "lake_shore"},
 "field": {"meadow", "mint_meadow", "flower_meadow", "lakeside_meadow"},
 "pasture": {"meadow", "lakeside_meadow", "lumberjack_camp"},
 "harbor": {"harbor", "sea_pier", "ocean_platform"},
 "construction": {"forge", "market", "guild_hall", "ruined_watchtower", "ruin_courtyard"},
 "workshop": {"forge", "market", "goblin_bomb_workshop"},
 "market": {"market", "fish_market"},
 "sea": {"sea_pier", "ocean_platform"},
}

@dataclass(frozen=True)
class Work:
    prof: str
    code: str
    title: str
    min_level: int
    region: str
    ingredients: Tuple[Tuple[str,int], ...]
    outputs: Tuple[Tuple[str,int], ...]
    xp: int
    tool_xp: int
    cooldown: int = 0
    pending: str = ""  # start/finish for timers or transports

# Real item inputs are always consumed. Outcomes and XP scale with task stage.
BASE_ACTIONS = (
 Work("Łowiectwo", "trop", "Tropienie zwierzyny", 1,"wild", (), (("v600_tracks",1),),65,35,75),
 Work("Łowiectwo", "zasadzka", "Zasadzka wytropionej zwierzynie",1,"wild",(("v600_tracks",2),("mint",1)),(("hunt_meat",3),("v600_hunting_hide",2)),175,95,120),
 Work("Łowiectwo", "opraw", "Oprawianie tropionej zdobyczy",1,"wild",(("v600_tracks",1),),(("hunt_meat",2),("v600_hunting_hide",1)),95,52),
 Work("Rolnictwo", "siej", "Siew i uprawa pola",1,"field",(("v600_seeds",1),),(),75,45,0,"sow"),
 Work("Rolnictwo", "miel", "Mielenie zboża na mąkę",1,"field",(("field_grain",3),),(("v600_flour",2),),120,75),
 Work("Rolnictwo", "zbierz", "Zbiór dojrzałych plonów",1,"field",(),(("field_grain",3),),125,65,0,"harvest"),
 Work("Hodowla zwierząt", "nakarm", "Karmienie i pielęgnacja stada",1,"pasture",(("field_grain",2),),(),100,65,0,"feed"),
 Work("Hodowla zwierząt", "przedz", "Przędzenie wełny ze stada",1,"pasture",(("farm_wool",2),),(("v600_yarn",1),),150,80),
 Work("Hodowla zwierząt", "odbierz", "Strzyżenie i odbiór produktów",1,"pasture",(),(("farm_wool",2),("v600_milk",1)),135,85,0,"milk"),
 Work("Okrętownictwo", "buduj", "Budowa elementów poszycia",1,"harbor",(("oak_plank",2),("iron_ingot",1)),(("ship_parts",2),),145,95),
 Work("Okrętownictwo", "wyposaz", "Wyposażanie pokładu i olinowania",1,"harbor",(("ship_parts",3),("oak_plank",1)),(("v600_ship_gear",1),),215,140),
 Work("Okrętownictwo", "napraw", "Naprawa konstrukcji okrętu",1,"harbor",(("ship_parts",2),),(("v600_hull_repair",1),),180,115),
 Work("Murarstwo", "obrabiaj", "Obróbka kamienia",1,"construction",(("stone_chunk",3),),(("stone_blocks",2),),95,60),
 Work("Murarstwo", "fundament", "Osadzenie fundamentów budowli",1,"construction",(("stone_blocks",3),("iron_ingot",1)),(("v600_foundation",1),),200,130),
 Work("Murarstwo", "wznies", "Budowa muru i wzmocnienia",1,"construction",(("stone_blocks",3),),(("v600_masonry_support",1),),180,105),
 Work("Inżynieria", "montuj", "Montaż mechanizmu",1,"workshop",(("iron_ingot",1),("v600_masonry_support",1)),(("machine_gears",2),),180,105),
 Work("Inżynieria", "projektuj", "Projektowanie układu mechanicznego",1,"workshop",(("machine_gears",3),("v600_foundation",1)),(("v600_mechanism",1),),240,155),
 Work("Inżynieria", "kalibruj", "Kalibracja urządzenia nawigacyjnego",1,"workshop",(("machine_gears",2),("v600_hull_repair",1)),(("v600_nav_kit",1),),230,145),
 Work("Kupiectwo", "pakuj", "Pakowanie towarów z profesji",1,"market",(("field_grain",2),("farm_wool",1)),(("trade_crate",1),),130,80),
 Work("Kupiectwo", "wycen", "Wycena i zabezpieczenie ładunku",1,"market",(("trade_crate",1),("v600_hunting_hide",1)),(("v600_appraisal",1),),185,110),
 Work("Kupiectwo", "wyslij", "Przygotowanie konwoju towarowego",1,"harbor",(("trade_crate",1),),(),145,95,0,"dispatch"),
 Work("Kupiectwo", "dostarcz", "Dostarczenie ładunku na targ",1,"market",(),(("v600_trade_receipt",1),),175,115,0,"delivery"),
 Work("Żeglarstwo", "wyznacz", "Wyznaczanie kursu i mapa rejsu",1,"harbor",(("v600_nav_kit",1),("oak_plank",1)),(("navigation_chart",2),),160,95),
 Work("Żeglarstwo", "nawiguj", "Nawigacja według znaków morskich",1,"sea",(("navigation_chart",1),("v600_nav_kit",1)),(("v600_bearings",2),),210,130),
 Work("Żeglarstwo", "rejs", "Wyprawa morska",1,"harbor",(("navigation_chart",1),("v600_hull_repair",1)),(),180,110,0,"voyage"),
 Work("Żeglarstwo", "powrot", "Zakończenie wyprawy i dziennik",1,"sea",(),(("v600_voyage_log",1),),205,140,0,"return"),
)

# Difficulty bands require progress through game materials: no flat XP.
# At levels 25+ upgrade recipes with an explicitly additional hard-world input;
# base work remains available to preserve accessibility and gradual training.
TIER_BONUS_INPUT = {
 "Łowiectwo": ("mint", "sage", "valerian", "ginseng", "mandrake", "phoenix_leaf", "astral_lotus"),
 "Rolnictwo": ("nettle", "chamomile", "mint", "sage", "ginseng", "mandrake", "astral_lotus"),
 "Hodowla zwierząt": ("nettle", "chamomile", "mint", "sage", "ginseng", "mandrake", "astral_lotus"),
 "Okrętownictwo": ("oak_log", "ash_log", "yew_log", "ironwood_log", "runewood_log", "astralwood_log", "eternal_worldwood_log"),
 "Murarstwo": ("stone_chunk", "iron_ore", "silver_ore", "gold_ore", "runestone_ore", "astral_ore", "eternium_ore"),
 "Inżynieria": ("copper_ore", "iron_ingot", "silver_ingot", "gold_ingot", "cobalt_ingot", "astral_ingot", "eternium_ingot"),
 "Kupiectwo": ("small_fish", "silver_trout", "swordfish", "runic_sturgeon", "dragon_mahi", "abyss_tuna", "eternal_coelacanth"),
 "Żeglarstwo": ("small_fish", "silver_trout", "swordfish", "runic_sturgeon", "dragon_mahi", "abyss_tuna", "eternal_coelacanth"),
}

def work_for(prof, code, tier=1):
    base = next((x for x in BASE_ACTIONS if x.prof==prof and x.code==code), None)
    if base is None or tier not in TIERS: return None
    if tier==1: return base
    idx = TIERS.index(tier)
    material = TIER_BONUS_INPUT[prof][idx]
    # Not a generic work button: difficulty increases actual costs and XP,
    # while each profession retains its own distinct processing/action chain.
    return Work(base.prof,base.code,base.title,tier,base.region,
        base.ingredients+((material,1+idx//3),),base.outputs,
        base.xp + tier*10 + idx*85,base.tool_xp+tier*6+idx*55,
        base.cooldown,base.pending)

ITEMS_NEW = {
 "v600_tracks": ("Tropy Zwierzyny", "resource"),
 "v600_hunting_hide": ("Skóra z Polowania", "craft_material"),
 "v600_seeds": ("Nasiona Uprawne", "resource"),
 "v600_milk": ("Świeże Mleko Hodowlane", "resource"),
 "v600_hull_repair": ("Zestaw Naprawy Okrętu", "craft_material"),
 "v600_masonry_support": ("Kamienne Wzmocnienie", "craft_material"),
 "v600_nav_kit": ("Skalibrowany Przyrząd Nawigacyjny", "craft_material"),
 "v600_trade_receipt": ("Kwit Kupiecki", "resource"),
 "v600_voyage_log": ("Dziennik Wyprawy", "resource"),
 "v600_flour": ("Mąka z Własnego Zboża", "craft_material"),
 "v600_yarn": ("Przędza Hodowlana", "craft_material"),
 "v600_ship_gear": ("Wyposażenie Pokładu", "craft_material"),
 "v600_foundation": ("Fundament Budowli", "craft_material"),
 "v600_mechanism": ("Precyzyjny Układ Mechaniczny", "craft_material"),
 "v600_appraisal": ("Certyfikat Wyceny Kupieckiej", "resource"),
 "v600_bearings": ("Pomiary Nawigacyjne", "resource"),
 "v600_hunters_stew": ("Gulasz Myśliwski", "consumable"),
 "v600_field_bread": ("Chleb z Własnego Zboża", "consumable"),
 "v600_farm_cheese": ("Ser Hodowlany", "consumable"),
 "v600_wool_vest": ("Wełniana Kamizelka", "armor"),
 "v600_hide_vest": ("Kamizelka Łowiecka", "armor"),
}
ORDER_CYCLES = {p: next((i for a in BASE_ACTIONS if a.prof==p for i,q in a.outputs if i not in ('v600_tracks','v600_seeds')), None) for p in PROFESSIONS}


def install_legacy_profession_recipes(items, cook_recipes, craft_recipes):
    """Additive integration with preexisting cooking and crafting; preserve originals."""
    recipes = {
        "v600_hunters_stew": {
            "name":"Gulasz Myśliwski","stations":("inn","fish_market"),
            "ingredients":{"hunt_meat":2,"field_grain":1,"mint":1},
            "output":"v600_hunters_stew","quantity":1,
            "min_tool_level":1,"tool_xp":24,"profession_xp":32,
            "desc":"Gotowanie: mięso z Łowiectwa, zboże z Rolnictwa i mięta."},
        "v600_field_bread": {
            "name":"Chleb z Własnego Zboża","stations":("inn","fish_market"),
            "ingredients":{"v600_flour":2,"v600_milk":1},
            "output":"v600_field_bread","quantity":2,
            "min_tool_level":1,"tool_xp":32,"profession_xp":42,
            "desc":"Gotowanie: mąka rolnika i mleko hodowcy."},
        "v600_farm_cheese": {
            "name":"Ser Hodowlany","stations":("inn","fish_market"),
            "ingredients":{"v600_milk":2,"mint":1},
            "output":"v600_farm_cheese","quantity":1,
            "min_tool_level":1,"tool_xp":24,"profession_xp":34,
            "desc":"Gotowanie: mleko hodowcy i zioła."},
    }
    gear = {
        "v600_wool_vest": {
            "name":"Wełniana Kamizelka","stations":("forge",),
            "ingredients":{"v600_yarn":2,"oak_plank":1},
            "output":"v600_wool_vest","quantity":1,
            "min_tool_level":20,"profession_xp":64,"tool_xp":50,"category":"smithing",
            "desc":"Rzemiosło: trwałe ubranie z przędzy hodowcy."},
        "v600_hide_vest": {
            "name":"Kamizelka Łowiecka","stations":("forge",),
            "ingredients":{"v600_hunting_hide":3,"iron_ingot":1},
            "output":"v600_hide_vest","quantity":1,
            "min_tool_level":15,"profession_xp":58,"tool_xp":45,"category":"smithing",
            "desc":"Rzemiosło: pancerz ze skór myśliwego."},
    }
    for rid,recipe in recipes.items():
        if rid in cook_recipes: raise RuntimeError('Duplicate cooking integration '+rid)
        cook_recipes[rid]=recipe
    for rid,recipe in gear.items():
        if rid in craft_recipes: raise RuntimeError('Duplicate craft integration '+rid)
        craft_recipes[rid]=recipe
    items['v600_hunters_stew'].update(heal=85,mana=15,desc='Gulasz gotowany z plonów i dziczyzny.')
    items['v600_field_bread'].update(heal=50,desc='Chleb z plonów rolnika.')
    items['v600_farm_cheese'].update(heal=45,mana=12,desc='Ser z mleka hodowcy.')
    items['v600_wool_vest'].update(type='armor',slot='body',defense=4,desc='Kamizelka ze sprzędzonej wełny.')
    items['v600_hide_vest'].update(type='armor',slot='body',defense=5,desc='Kamizelka ze skór łowcy.')
    return len(recipes)+len(gear)
