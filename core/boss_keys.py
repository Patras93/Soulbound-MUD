"""Pure boss-key identifiers, independent of protocol/world initialization."""

BOSS_CHEST_KIND_NAMES = {
    "giant": "Twierdzy Gigantów",
    "crypt": "Krypty",
    "astral": "Wieży Astralnej",
    "mythic_crypt": "Mitycznej Krypty",
    "mythic_astral": "Mitycznej Wieży Astralnej",
}

def boss_floor_key_id(kind, floor):
    return f"boss_chest_key_{kind}_{int(floor)}"
