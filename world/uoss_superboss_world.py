# -*- coding: utf-8 -*-
"""UOSSMUD Super Boss world layer v1.11.36.

Creates one stable arena and one stationary boss spawn per encounter.
The hub is deliberately connected to Miasto Dusz; access policy remains
available as authored metadata for command/runtime gates.
"""
from data.catalogs import ROOMS, MOB_TEMPLATES, NPCS, SHOPS
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
    "culex": {"level":130,"max_hp":400000,"max_mp":200000,"xp":1000000,"resist":("Weapon","Magic"),"immune":("Status_all",),"drop":"Quartz Chunk","location":"Star Field"},
    "emerald_weapon": {"level":150,"max_hp":1000000,"max_mp":0,"xp":500000,"types":("Machine",),"weak":("Lightning",),"immune":("Status_all","Earth"),"absorb":("Ice","Water"),"drop":"Earth Harp","location":"On the Sea Floor"},
    "ruby_weapon": {"level":140,"max_hp":1000000,"max_mp":200000,"xp":500000,"types":("Machine",),"immune":("Berserk","Engulf","Silence","Poison","Sleep","Small","Noact","Gravity","Curse","Petrify","Imp","Stop","Water"),"absorb":("Fire","Ice","Lightning","Earth"),"drop":"Desert Rose","location":"Corel Prison"},
    "serpentarius": {"level":250,"max_hp":1300000,"xp":18900000,"types":("Demon",),"immune":("Curse","Poison","Silence","Stop"),"drop":"Serpentarius Emblem","location":"Deep Dungeon","round_limit":100,"no_exit_after_start":True},
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
}
for nid,(name,key) in _HELPERS.items():
    NPCS.setdefault(nid,{
        "name":name,"room":f"uoss_superboss_arena_{key}_v11136",
        "dialogue":f"{name} może wesprzeć drużynę liczącą maksymalnie 3 graczy podczas walki z {UOSS_SUPERBOSS_ENCOUNTERS_V11134[key]['name']}.",
        "uoss_superboss_helper":key,"helper_max_players":3,
    })

# Token exchange points. The generic shop UI can expose the pools; prices are
# token metadata because these currencies are items, not silver/gold.
NPCS.setdefault("uoss_watts",{
    "name":"Watts","room":"uoss_superboss_arena_black_rabite_v11136",
    "dialogue":"Wymieniam Moogle Steel na relikty Black Rabite.","shopkeeper":True,
    "uoss_token_shop":"uoss_moogle_steel",
})
NPCS.setdefault("uoss_odin_fur_trader",{
    "name":"Fur Trader — tier Odina","room":"uoss_superboss_arena_odin_v11136",
    "dialogue":"Odin's Mantle otwiera tier ośmiu reliktów Odina.","shopkeeper":True,
    "uoss_token_shop":"uoss_odins_mantle",
})
SHOPS.setdefault("uoss_superboss_arena_odin_v11136",[f"uoss_odin_unique_{i}" for i in range(1,9)])

NPCS.setdefault("uoss_yiazmat_fur_trader",{
    "name":"Kupiec Futrzarski — tier Yiazmata","room":"uoss_superboss_arena_yiazmat_v11136",
    "dialogue":"Godslayer's Badge otwiera tier nagród Yiazmata.","shopkeeper":True,
    "uoss_token_shop":"uoss_godslayers_badge",
})
SHOPS.setdefault("uoss_superboss_arena_black_rabite_v11136",[f"uoss_black_rabite_unique_{i}" for i in range(1,11)])
SHOPS.setdefault("uoss_superboss_arena_yiazmat_v11136",[f"uoss_yiazmat_unique_{i}" for i in range(1,8)])

def install_uoss_superboss_spawns_v11136(mob_spawns):
    """Idempotently install the 21 canonical boss spawns after content registry exists."""
    for key in _ORDER:
        pair=(f"uoss_superboss_arena_{key}_v11136", f"uoss_superboss_{key}_v11136")
        if pair not in mob_spawns:
            mob_spawns.append(pair)
    return 21

UOSS_SUPERBOSS_WORLD_STATE_V11136={
 "version":"1.11.36","hub":HUB,"arenas":21,"bosses":21,"helpers":tuple(_HELPERS),
 "black_rabite_shop":10,"odin_shop":8,"yiazmat_shop":7,
}
