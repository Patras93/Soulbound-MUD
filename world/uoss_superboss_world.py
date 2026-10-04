# -*- coding: utf-8 -*-
"""UOSSMUD Super Boss world layer v1.11.36.

Creates one stable arena and one stationary boss spawn per encounter.
The hub is deliberately connected to Miasto Dusz; access policy remains
available as authored metadata for command/runtime gates.
"""
from data.catalogs import ROOMS, MOB_TEMPLATES, NPCS, SHOPS
from data.items import ITEMS
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134


HUB="uoss_superboss_hall_v11136"
if HUB not in ROOMS:
    ROOMS[HUB]={
        "zone":"Sala Super Bossów","name":"Sala Wyzwań Super Bossów",
        "desc":"Kamienny krąg portali prowadzi do unikalnych wyzwań. Użyj superbosses, aby sprawdzić wymagania i zaliczenia.",
        "exits":{"south":"square"},"uoss_superboss_hub":True,
    }
ROOMS.setdefault("square",{}).setdefault("exits",{}).setdefault("northwest",HUB)

_ORDER=tuple(UOSS_SUPERBOSS_ENCOUNTERS_V11134)
_DIRS=("north","northeast","east","southeast","southwest","west","up","down")
_prev=HUB

# Exact Scanner Data supplied from UOSSMUD. Unknown source fields are omitted
# rather than inferred. XP is authored source XP and must not be regenerated.
SOURCE_SCANNER_V11156 = {
    "black_rabite": {"level":300,"max_hp":3300000,"max_mp":800000,"xp":18900000,"immune":("Status_all",),"location":"Rabite Field"},
    "culex": {"level":130,"max_hp":400000,"max_mp":200000,"xp":1000000,"resist":("Weapon","Magic"),"immune":("Status_all",),"drop":"Quartz Chunk","drop_item_id":"quartz_chunk","location":"Star Field"},
    "emerald_weapon": {"level":150,"max_hp":1000000,"max_mp":0,"xp":500000,"types":("Machine",),"weak":("Lightning",),"immune":("Status_all","Earth"),"absorb":("Ice","Water"),"drop":"Earth Harp","location":"On the Sea Floor"},
    "ruby_weapon": {"level":140,"max_hp":1000000,"max_mp":200000,"xp":500000,"types":("Machine",),"immune":("Berserk","Engulf","Silence","Poison","Sleep","Small","Noact","Gravity","Curse","Petrify","Imp","Stop","Water"),"absorb":("Fire","Ice","Lightning","Earth"),"drop":"Desert Rose","location":"Corel Prison"},
    "serpentarius": {"level":250,"max_hp":1300000,"xp":18900000,"types":("Demon",),"immune":("Curse","Poison","Silence","Stop"),"drop":"Serpentarius Emblem","location":"Deep Dungeon","round_limit":100,"no_exit_after_start":True},
    "odin": {"level":300,"max_hp":3000000,"max_mp":300000,"xp":18900000,"types":("Humanoid","Magical"),"resist":("Drain",),"immune":("Status_all","Launch"),"drop":"Odin's Mantle","location":"A Clearing in a Misty Forest"},
    "yiazmat": {"level":300,"max_hp":4000000,"max_mp":300000,"xp":18900000,"types":("Dragon",),"weak":("Dark",),"resist":("Earth","Fire","Ice","Lightning","Water","Wind"),"immune":("Status_all",),"absorb":("Holy",),"drop":"Godslayer's Badge","location":"Ridorana Cataract Colosseum"},
}
for idx,key in enumerate(_ORDER,1):
    spec=UOSS_SUPERBOSS_ENCOUNTERS_V11134[key]
    rid=f"uoss_superboss_arena_{key}_v11136"
    mid=f"uoss_superboss_{key}_v11136"
    scanner=SOURCE_SCANNER_V11156.get(key,{})
    level=max(1,int(scanner.get("level") or spec.get("recommended_level") or spec.get("unlock_level") or 100))
    ROOMS.setdefault(rid,{
        "zone":"Super Bossowie UOSSMUD","name":f"Arena — {spec['name']}",
        "desc":f"Unikalna arena wyzwania {spec['name']}. Boss jest pasywny do chwili rozpoczęcia walki.",
        "exits":{"back":_prev},"recommended_level":level,"generator_level":level,
        "uoss_superboss_key":key,"uoss_mode":spec.get("mode","solo"),
        "uoss_unlock_level":int(spec.get("unlock_level",0) or 0),
        "uoss_unlock":spec.get("unlock"),
    })
    # Chain arenas so all are reachable without consuming 21 directions in hub.
    ROOMS.setdefault(_prev,{}).setdefault("exits",{}).setdefault("forward",rid)
    MOB_TEMPLATES.setdefault(mid,{
        "name":spec["name"],"max_hp":int(scanner.get("max_hp") or max(5000, level*250)),
        "max_mp":scanner.get("max_mp"),"source_xp":scanner.get("xp"),"source_xp_exact":bool(scanner.get("xp") is not None),
        "damage":max(75, level*3),"damage_type":"magic" if key in {"diabolos","ozma","hades","elementals"} else "physical",
        "silver":0,"gold":0,"mithril":0,"stat_reward":0,"soul_reward":0,"drops":{},"quest_target":None,
        "combat_types":scanner.get("types",()),"weak":scanner.get("weak",()),"resist":scanner.get("resist",()),
        "immune":scanner.get("immune",()),"absorb":scanner.get("absorb",()),"source_drop":scanner.get("drop"),
        "source_location":scanner.get("location"),"round_limit":scanner.get("round_limit"),"no_exit_after_start":bool(scanner.get("no_exit_after_start",False)),
        "world_boss":True,"stationary_mob":True,"auto_aggro":False,"generator_level":level,
        "uoss_unique_superboss_key":key,"uoss_superboss_mode":spec.get("mode","solo"),
        "boss_mechanic":f"uoss_{key}",
        "boss_mechanic_text":f"Unikalna walka Super Boss: {spec['name']}. Wymagania sprawdzisz komendą superbosses {spec['name']}.",
    })
    _prev=rid


# Source location names remain encounter metadata, but Soulbound does not create
# duplicate foreign cities/continents or a second chain of source-only rooms.
# Source-backed bosses use the existing Soulbound superboss arenas.
_SOURCE_ROOMS_V11160 = {
 "black_rabite":("uoss_superboss_arena_black_rabite_v11136","Rabite Field"),
 "culex":("uoss_superboss_arena_culex_v11136","Star Field"),
 "emerald_weapon":("uoss_superboss_arena_emerald_weapon_v11136","On the Sea Floor"),
 "ruby_weapon":("uoss_superboss_arena_ruby_weapon_v11136","Back of Corel Prison"),
 "serpentarius":("uoss_superboss_arena_serpentarius_v11136","Deep Dungeon"),
 "yiazmat":("uoss_superboss_arena_yiazmat_v11136","Ridorana Cataract Colosseum"),
 "odin":("uoss_superboss_arena_odin_v11136","A Clearing in a Misty Forest"),
}

# Exact summoned/companion combatants belonging to sourced encounters.
_SOURCE_ADDS_V11156 = {
 "greater_demon":{"name":"Greater Demon","level":175,"max_hp":325000,"max_mp":65000,"source_xp":300000,"source_xp_exact":True,"parent":"black_rabite","location":"Black Rabite","abilities":(),"elements":("Fire","Dark")},
 "culex_wind_crystal":{"name":"Wind Crystal","level":130,"max_hp":100000,"max_mp":20000,"source_xp":74000,"source_xp_exact":True,"parent":"culex","weak":("Earth",),"resist":("Weapon","Magic"),"immune":("Status_all",),"absorb":("Wind","Lightning"),"abilities":("Petal Blast","Electroshock","Static Electricity","Light Beam")},
 "culex_water_crystal":{"name":"Water Crystal","level":130,"max_hp":100000,"max_mp":20000,"source_xp":74000,"source_xp_exact":True,"parent":"culex","weak":("Fire",),"resist":("Weapon","Magic"),"immune":("Status_all",),"absorb":("Water","Ice"),"abilities":("Diamond Saw","Ice Rock","Blizzard","Crystal")},
 "culex_fire_crystal":{"name":"Fire Crystal","level":130,"max_hp":100000,"max_mp":20000,"source_xp":74000,"source_xp_exact":True,"parent":"culex","weak":("Ice","Water"),"resist":("Weapon","Magic"),"immune":("Status_all",),"absorb":("Fire",),"abilities":("Corona","Flame","Flame Wall","Mega Drain")},
 "culex_earth_crystal":{"name":"Earth Crystal","level":130,"max_hp":100000,"max_mp":20000,"source_xp":74000,"source_xp_exact":True,"parent":"culex","weak":("Wind","Lightning"),"resist":("Weapon","Magic"),"immune":("Status_all",),"absorb":("Earth",),"abilities":("Storm","Blast","Water Blast","Sand Storm")},
 "emerald_white_eye":{"name":"White Eye","level":140,"max_hp":80000,"max_mp":0,"source_xp":100000,"source_xp_exact":True,"parent":"emerald_weapon","combat_types":("Machine",),"weak":("Fire",),"immune":("Noact","Engulf","Earth","Silence","Stop","Berserk","Sleep"),"absorb":("Ice","Water"),"abilities":("Emerald Absorber","Emerald Cure","Blessing of the Planet")},
 "emerald_blue_eye":{"name":"Blue Eye","level":140,"max_hp":80000,"max_mp":3000,"source_xp":100000,"source_xp_exact":True,"parent":"emerald_weapon","combat_types":("Machine",),"weak":("Fire",),"immune":("Noact","Engulf","Earth","Silence","Stop","Berserk","Sleep"),"absorb":("Ice","Water"),"abilities":("Osmose","Gather MP","The Planet's Cleansing")},
 "emerald_red_eye":{"name":"Red Eye","level":140,"max_hp":80000,"max_mp":0,"source_xp":100000,"source_xp_exact":True,"parent":"emerald_weapon","combat_types":("Machine",),"weak":("Fire",),"immune":("Noact","Engulf","Earth","Silence","Stop","Berserk","Sleep"),"absorb":("Ice","Water"),"abilities":("Emerald Laser","Emerald Torpedo")},
 "emerald_torpedo":{"name":"Emerald Torpedo","level":83,"max_hp":12000,"max_mp":0,"source_xp":0,"source_xp_exact":True,"parent":"emerald_red_eye","combat_types":("Machine",),"immune":("Status_all",),"explode_round":3,"abilities":("Emerald Torpedo",)},
 "ruby_right_tentacle":{"name":"Right Tentacle","level":140,"max_hp":150000,"max_mp":30000,"source_xp":0,"source_xp_exact":True,"parent":"ruby_weapon","combat_types":("Machine",),"immune":("Small","Noact","Gravity","Petrify","Imp","Stop","Berserk","Water","Engulf","Silence","Sleep"),"abilities":("Right Thrust",)},
 "odin_gungnir":{"name":"Gungnir","level":120,"max_hp":250000,"max_mp":0,"source_xp":0,"source_xp_exact":True,"parent":"odin","combat_types":("Magical",),"immune":("Status_all","Gravity"),"abilities":("melee",)},
 "ruby_left_tentacle":{"name":"Left Tentacle","level":140,"max_hp":150000,"max_mp":30000,"source_xp":0,"source_xp_exact":True,"parent":"ruby_weapon","combat_types":("Machine",),"immune":("Small","Noact","Gravity","Petrify","Imp","Stop","Berserk","Water","Engulf","Silence","Sleep"),"abilities":("Left Revenge",)},
}
for _add_key,_add in _SOURCE_ADDS_V11156.items():
    _mid=f"uoss_add_{_add_key}_v11156"
    _row=dict(_add)
    _row.update({"silver":0,"gold":0,"mithril":0,"stat_reward":0,"soul_reward":0,"drops":{},"quest_target":None,"stationary_mob":True,"auto_aggro":False,"uoss_superboss_add":True})
    MOB_TEMPLATES.setdefault(_mid,_row)

# Source-authored boss ability contracts. Numeric effects are included only
# where the supplied source gives an exact value.
SOURCE_BOSS_ABILITIES_V11156 = {
 "black_rabite":{"summons":"greater_demon","elements":("Fire","Dark"),"status_immunity":"all","special_status_exception":"Vanish a Paralyze attack may inflict Don't Act"},
 "culex":{"abilities":("Crash Strike","Dark Star","Meteor Blast","Flame Stone","Dispel"),"summons":("culex_wind_crystal","culex_water_crystal","culex_fire_crystal","culex_earth_crystal")},
 "emerald_weapon":{"abilities":("Stamp","Dissolving Ray","Emerald Beam","Aqua Beam","Deep Life Water","Open Eye","Revenge Stamp"),"open_eye_random":("emerald_white_eye","emerald_blue_eye","emerald_red_eye")},
 "ruby_weapon":{"abilities":("Big Claw","Big Swing","Comet2","Ruby Ray","Ruby Flame","Shadow Flare","Ultima","Wrap","Imp","Mini"),"summons":("ruby_right_tentacle","ruby_left_tentacle"),"wrap_removes_player_when_party_gt":1},
 "serpentarius":{"abilities":("Snake Carrier","Poison Frog","Resisted Gravija","Gravija","Midgar Swarm","Banish Ray","Firaja","Blizzaja","Thundaja","Comet","Light Pillar","Necrotic Energy","Nullify Healing","Zodiac"),"banish_ray_damage":9999,"light_pillar_damage":9999,"resisted_gravija_fraction":"1/10","gravija_fraction":"1/3","necrotic_energy_rounds":8,"nullify_healing_rounds":3},
 "odin":{"abilities":("Valknut","Zantetsuken","Einherjar","Gungnir","#-Gungnir Pulse of Magic","Hall of Stone","Hall of Lead","Disease","Shin-Zantetsuken"),"zantetsuken_current_hp_fraction":"2/3","einherjar_attack_multiplier":3,"gungnir_attack_multiplier":3,"gungnir_summon_count":3,"summons":"odin_gungnir","hall_of_stone_status":"Petrify","hall_of_lead_status":"Slow","shin_zantetsuken_instant_death_rounds":10},
 "yiazmat":{"abilities":("Rake","Death Strike","Magnetic Lysis","Dust Storm","Ice Breath","Gust Front","Cyclone","Stone Breath"),"death_strike_hp_fraction":0.80,"death_strike_gravityproof_fraction":0.50},
}
for _boss_key,_contract in SOURCE_BOSS_ABILITIES_V11156.items():
    _mid=f"uoss_superboss_{_boss_key}_v11136"
    if _mid in MOB_TEMPLATES:
        MOB_TEMPLATES[_mid]["source_ability_contract"]=dict(_contract)

# Helpers are real NPCs in the relevant arenas. Hiring behavior is represented
# explicitly and can be consumed by combat-party logic without inventing dialogue.
_HELPERS={
 "uoss_helper_primm":("Primm","black_rabite"),
 "uoss_helper_popoi":("Popoi","black_rabite"),
 "uoss_helper_byblos":("Byblos","serpentarius"),
 "uoss_helper_montblanc":("Montblanc","yiazmat"),
 "uoss_helper_seifer":("Seifer","odin"),
}
for nid,(name,key) in _HELPERS.items():
    NPCS.setdefault(nid,{
        "name":name,"room":_SOURCE_ROOMS_V11160.get(key,(f"uoss_superboss_arena_{key}_v11136",""))[0],
        "dialogue":f"{name} może wesprzeć drużynę liczącą maksymalnie 3 graczy podczas walki z {UOSS_SUPERBOSS_ENCOUNTERS_V11134[key]['name']}.",
        "uoss_superboss_helper":key,"helper_max_players":3,
    })

# Exact Black Rabite helper contracts supplied by the source.
if "uoss_helper_popoi" in NPCS:
    NPCS["uoss_helper_popoi"].update({
        "helper_cost_mithril":1,
        "join_phrase":"Join me, Popoi",
        "abilities":("Air Blast","Earth Slide","Acid Storm","Vine Hell","Luna","Faerie Walnut"),
        "aoe_abilities":("Air Blast","Earth Slide","Acid Storm"),
        "vine_hell_status_all":"Slow",
        "luna_status_all":"Mini",
        "faerie_walnut_mp_restore_fraction":0.20,
    })
if "uoss_helper_primm" in NPCS:
    NPCS["uoss_helper_primm"].update({
        "helper_cost_mithril":1,
        "join_phrase":"Join me, Primm",
        "abilities":("Lucent Beam","Cure Water","Bubble","Lumina","Dryad"),
        "lucent_beam_target":"single",
        "cure_water":"restores HP",
        "bubble_max_hp_multiplier":1.50,
        "lumina":"holy strike",
        "dryad":"preach",
    })

# Exact helper ability metadata where supplied by the source.
if "uoss_helper_seifer" in NPCS:
    NPCS["uoss_helper_seifer"].update({
        "helper_cost_mithril":1,
        "join_phrase":"Join me, Seifer.",
        "abilities":("Power Breakdown","No Mercy","Zantetsuken Reverse"),
        "power_breakdown":"physical attack reduced at beginning of fight",
        "no_mercy_frequency":"once per round",
        "zantetsuken_reverse_damage":1500000,
        "zantetsuken_reverse_timing":"towards half way of fight",
    })

if "uoss_helper_montblanc" in NPCS:
    NPCS["uoss_helper_montblanc"].update({
        "helper_cost_mithril":1,
        "join_phrase":"Join me",
        "abilities":("Firaga","Blizzaga","Thundaga","Darkra","Bioga","Flare","Drain","Syphon","Bubble"),
        "ability_elements":{"Firaga":"Fire","Blizzaga":"Ice","Thundaga":"Lightning","Darkra":"Dark","Bioga":"Poison"},
        "bubble":"source ability; numeric effect not supplied in this excerpt",
    })

# Token exchange points. The generic shop UI can expose the pools; prices are
# token metadata because these currencies are items, not silver/gold.

# Soulbound adaptation: source reward shops live in existing Soulbound locations.
# We preserve source currencies/catalogs without creating foreign cities only to host vendors.
NPCS.setdefault("uoss_watts",{
    "name":"Kupiec nagród Black Rabite","room":"market",
    "dialogue":"Wymieniam Moogle Steel i złoto na nagrody Black Rabite.","shopkeeper":True,
    "uoss_token_shop":"uoss_moogle_steel",
})
NPCS.setdefault("uoss_culex_fur_trader",{
    "name":"Kupiec nagród Culexa","room":"market",
    "dialogue":"Wymieniam Quartz Chunk i złoto na nagrody Culexa.","shopkeeper":True,
    "uoss_token_shop":"quartz_chunk",
})
NPCS.setdefault("uoss_odin_fur_trader",{
    "name":"Kupiec nagród Odina","room":"market",
    "dialogue":"Wymieniam Odin's Mantle i złoto na nagrody Odina.","shopkeeper":True,
    "uoss_token_shop":"uoss_odins_mantle",
})
NPCS.setdefault("uoss_yiazmat_fur_trader",{
    "name":"Kupiec nagród Yiazmata","room":"market",
    "dialogue":"Godslayer's Badge otwiera tier nagród Yiazmata.","shopkeeper":True,
    "uoss_token_shop":"uoss_godslayers_badge",
})
SHOPS.setdefault("market",[])
for _iid in (
    "culex_quartz_charm","culex_hermes_shoes","culex_hyper_wrist","culex_hypno_crown","culex_solomon_ring","culex_tough_ring",
    *(f"uoss_odin_unique_{i}" for i in range(1,9)),
    *(f"uoss_yiazmat_unique_{i}" for i in range(1,8)),
):
    if _iid not in SHOPS["market"]:
        SHOPS["market"].append(_iid)
SHOPS.setdefault("market",[])
_UNIVERSAL_UOSS_ENDGAME_SHOP_ITEMS_V11194 = (
    "uoss_behemoth_suit",
    "uoss_venetian_shield",
    "uoss_ziedrich",
    "uoss_thief_hat",
    "uoss_oborozuki",
)
for _iid in _UNIVERSAL_UOSS_ENDGAME_SHOP_ITEMS_V11194:
    if _iid not in SHOPS["market"]:
        SHOPS["market"].append(_iid)

_BLACK_RABITE_SHOP_ITEMS_V11190 = (
    *(f"uoss_black_rabite_unique_{i}" for i in range(1,10)),
    "moogle_board",
)
for _iid in _BLACK_RABITE_SHOP_ITEMS_V11190:
    if _iid not in SHOPS["market"]:
        SHOPS["market"].append(_iid)

_UNIVERSAL_UOSS_ACCESSORIES_V11195 = (
    "uoss_black_rabite_unique_5",
    "uoss_odin_unique_4",
    "uoss_yiazmat_unique_3",
    "uoss_yiazmat_unique_7",
    "uoss_ziedrich",
    "culex_quartz_charm",
    "culex_hermes_shoes",
    "culex_hyper_wrist",
    "culex_hypno_crown",
    "culex_solomon_ring",
    "culex_tough_ring",
)
for _iid in _UNIVERSAL_UOSS_ACCESSORIES_V11195:
    _item = ITEMS.get(_iid)
    if not _item:
        raise RuntimeError(f"UOSS accessory audit failed: missing item {_iid}")
    if _iid not in SHOPS["market"]:
        SHOPS["market"].append(_iid)
    if _item.get("required_class"):
        raise RuntimeError(f"UOSS accessory audit failed: {_iid} must be available to every class")
    if not _item.get("universal_all_classes"):
        raise RuntimeError(f"UOSS accessory audit failed: {_iid} missing universal_all_classes marker")

def install_uoss_superboss_spawns_v11136(mob_spawns):
    """Install bosses; sourced encounters spawn in their canonical named rooms."""
    for key in _ORDER:
        room_id=_SOURCE_ROOMS_V11160.get(key,(f"uoss_superboss_arena_{key}_v11136",""))[0]
        pair=(room_id, f"uoss_superboss_{key}_v11136")
        if pair not in mob_spawns:
            mob_spawns.append(pair)
    # Source-backed encounter adds that are present from the start.
    for boss_key, add_keys in {
        "culex":("culex_wind_crystal","culex_water_crystal","culex_fire_crystal","culex_earth_crystal"),
        "ruby_weapon":("ruby_right_tentacle","ruby_left_tentacle"),
    }.items():
        room_id=_SOURCE_ROOMS_V11160[boss_key][0]
        for add_key in add_keys:
            pair=(room_id,f"uoss_add_{add_key}_v11156")
            if pair not in mob_spawns:
                mob_spawns.append(pair)
    return 27

UOSS_SUPERBOSS_WORLD_STATE_V11136={
 "version":"1.11.36","hub":HUB,"arenas":21,"bosses":21,"helpers":tuple(_HELPERS),
 "black_rabite_shop":10,"odin_shop":8,"yiazmat_shop":7,
}
