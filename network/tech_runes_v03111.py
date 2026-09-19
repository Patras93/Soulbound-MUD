# -*- coding: utf-8 -*-
"""v0.31.13 technological runes registered after legacy rune system."""
_NEW_TECH_RUNES_V03111 = {
    "impuls": ("rune_impulse", "Runa Impulsu", {"all_damage_pct":3}),
    "bariera": ("rune_barrier_tech", "Runa Bariery Magitek", {"magic_defense_pct":3,"physical_defense_pct":1}),
    "rdzen": ("rune_core_tech", "Runa Rdzenia", {"intelligence":2,"willpower":2}),
}
for _key,_data in _NEW_TECH_RUNES_V03111.items():
    V0925_RUNES.setdefault(_key,_data)
    _rid,_name,_effects=_data
    _props={k:v for k,v in _effects.items() if k.endswith("_pct")}
    _stats={k:v for k,v in _effects.items() if not k.endswith("_pct")}
    ITEMS[_rid]={"name":_name,"type":"craft_material","price":None,"craftbox_category":"runes","rune_key":_key,
                 "rune_properties":_props,"rune_stats":_stats,"desc":"Technologiczna runa do istniejących gniazd runicznych EQ."}
    V0925_RUNE_BY_ID[_rid]=(_key,_effects)
