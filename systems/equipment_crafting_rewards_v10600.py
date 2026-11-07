# -*- coding: utf-8 -*-
"""v106 staging: preview deterministic bonus resources before atomic crafting.

The existing OLC33/34 counters live on player session objects.  A failed
craft must not advance them.  Use original rule functions against a small
counter-only preview object, then publish their counters ONLY after a full
SQLite commit.  Does not make quest / profession XP atomic yet.
"""
from types import SimpleNamespace
from systems.live_olc33_mechanics import craft_byproduct
from systems.live_olc34_integration import profession_find


def preview_resources(session, recipe_id):
    a=dict(getattr(session,'_olc33_craft_counts',{}) or {})
    b=dict(getattr(session,'_olc34_craft_counts',{}) or {})
    shadow=SimpleNamespace(_olc33_craft_counts=a, _olc34_craft_counts=b)
    byproduct=craft_byproduct(shadow,recipe_id)
    discovery=profession_find(shadow,recipe_id)
    rewards=tuple(x for x in (byproduct,discovery) if x)
    return rewards,a,b,byproduct,discovery


def publish_success(session,preview):
    _,counts33,counts34,_,_=preview
    # Each session executes one recipe at a time in current staging tests;
    # a future concurrent crafting path needs an explicit per-session lock.
    session._olc33_craft_counts=counts33
    session._olc34_craft_counts=counts34
