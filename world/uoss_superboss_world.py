# -*- coding: utf-8 -*-
"""UOSSMUD Super Boss world layer v1.11.36.

Creates one stable arena and one stationary boss spawn per encounter.
The hub is deliberately connected to Miasto Dusz; access policy remains
available as authored metadata for command/runtime gates.
"""
from data.catalogs import ROOMS, MOB_TEMPLATES, NPCS, SHOPS
from systems.content_registry import MOB_SPAWNS
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
for idx,key in enumerate(_ORDER,1):
    spec=UOSS_SUPERBOSS_ENCOUNTERS_V11134[key]
    rid=f"uoss_superboss_arena_{key}_v11136"
    mid=f"uoss_superboss_{key}_v11136"
    level=max(1,int(spec.get("recommended_level") or spec.get("unlock_level") or 100))
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
        "name":spec["name"],"max_hp":1000,"damage":50,"damage_type":"magic" if key in {"diabolos","ozma","hades","elementals"} else "physical",
        "silver":0,"gold":0,"mithril":0,"stat_reward":0,"soul_reward":0,"drops":{},"quest_target":None,
        "world_boss":True,"stationary_mob":True,"auto_aggro":False,"generator_level":level,
        "uoss_unique_superboss_key":key,"uoss_superboss_mode":spec.get("mode","solo"),
        "boss_mechanic":f"uoss_{key}",
        "boss_mechanic_text":f"Unikalna walka Super Boss: {spec['name']}. Wymagania sprawdzisz komendą superbosses {spec['name']}.",
    })
    if (rid,mid) not in MOB_SPAWNS:
        MOB_SPAWNS.append((rid,mid))
    _prev=rid

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
NPCS.setdefault("uoss_yiazmat_fur_trader",{
    "name":"Kupiec Futrzarski — tier Yiazmata","room":"uoss_superboss_arena_yiazmat_v11136",
    "dialogue":"Godslayer's Badge otwiera tier nagród Yiazmata.","shopkeeper":True,
    "uoss_token_shop":"uoss_godslayers_badge",
})
SHOPS.setdefault("uoss_superboss_arena_black_rabite_v11136",[f"uoss_black_rabite_unique_{i}" for i in range(1,11)])
SHOPS.setdefault("uoss_superboss_arena_yiazmat_v11136",[f"uoss_yiazmat_unique_{i}" for i in range(1,8)])

UOSS_SUPERBOSS_WORLD_STATE_V11136={
 "version":"1.11.36","hub":HUB,"arenas":21,"bosses":21,"helpers":tuple(_HELPERS),
 "black_rabite_shop":10,"yiazmat_shop":7,
}
