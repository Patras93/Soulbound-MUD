# -*- coding: utf-8 -*-
"""v2.00.8: magic-owner based minimum effective elemental strikes.

The legacy formula is retained as a lower bound; active elemental minions
never lose damage from this upgrade. This module does not touch SQLite.
"""
from __future__ import annotations

# Fraction of an owner's expected ordinary magical strike; the same combat
# defense, region/world-tier and elemental reaction hooks apply afterwards.
# Ice and Crystal exchange some damage for their existing strong barriers.
ELEMENTAL_STRIKE_SHARE = {
    "ogien": (0.65, 1.00, 1.45),
    "blyskawice": (0.85, 1.25, 1.85),
    "lod": (0.50, 0.75, 1.10),
    "krysztal": (0.58, 0.88, 1.30),
}


def effective_elemental_strike_v2008(legacy_amount, elemental, owner_expected_magic,
                                     stance_factor=1.0, formation_bonus=1.0,
                                     team_bonus=1.0, workshop_bonus=1.0):
    """Boost weak hits, preserve strong old hits; do not grant free attacks."""
    old = max(1, int(legacy_amount))
    if not elemental:
        return old
    shares = ELEMENTAL_STRIKE_SHARE.get(str(elemental.get("element", "")))
    if not shares:
        return old
    rank = int(elemental.get("rank", 0))
    if rank < 0 or rank >= 3:
        return old
    expected = max(1.0, float(owner_expected_magic))
    raw = (expected * shares[rank] * float(stance_factor)
           * float(formation_bonus) * float(team_bonus)
           * float(workshop_bonus))
    return max(old, max(1, int(raw)))
