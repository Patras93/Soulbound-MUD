"""Canonical pure drop probabilities for the gathering professions."""

# v1.14.9: individually weighted, unlock-gated rarity. Rates refer to ONE
# gathering action; a top-tier material never shares the starter-tier roll.
RESOURCE_VARIANT_CHANCES_V1149 = {
    "fish": {
        "albino": (1, 1, 0.0400, 0.0520),
        "giant": (40, 30, 0.0030, 0.0200),
        "golden": (100, 70, 0.0010, 0.0070),
        "ancient": (260, 160, 0.00010, 0.00120),
    },
    "wood": {
        "lush": (1, 1, 0.0330, 0.0430),
        "ancient": (120, 70, 0.0020, 0.0140),
        "crystal": (200, 120, 0.00050, 0.00500),
        "legendary": (360, 200, 0.00010, 0.00100),
    },
    "herb": {
        "lush": (1, 1, 0.0350, 0.0450),
        "glowing": (80, 50, 0.00200, 0.01600),
        "ancient": (200, 120, 0.00050, 0.00500),
        "legendary": (360, 200, 0.00010, 0.00100),
    },
}


def resource_variant_chances_v1149(category, tool_level, profession_level=None, resource_level=600):
    """Exclusive per-action probabilities; unlocks require skill AND material stage.

    Professions lacking an explicit level (legacy tooling) retain tool-based
    progression; actual gathering always supplies both values.
    """
    tool = max(1, min(800, int(tool_level)))
    prof = tool if profession_level is None else max(1, min(800, int(profession_level)))
    stage = min(tool, prof)
    resource = max(1, min(800, int(resource_level)))
    rates = {}
    for key, (unlock, minimum_resource, base, maximum) in RESOURCE_VARIANT_CHANCES_V1149[category].items():
        if stage < unlock or resource < minimum_resource:
            continue
        progress = (stage - unlock) / max(1, 600 - unlock)
        rates[key] = min(maximum, base + (maximum - base) * progress)
    return rates



def mining_vein_chances_v1149(tool_level, profession_level=None, floor=None):
    tool = max(1, min(800, int(tool_level)))
    prof = tool if profession_level is None else max(1, min(800, int(profession_level)))
    power = min(tool, prof)
    stage = min(power, max(1, int(floor or 1)))
    # Legendary veins no longer spawn for beginners. Even at 600: <=0.65%.
    legendary = 0.0 if stage < 180 else 0.001 + 0.0055 * (stage - 180) / 420.0
    crystal = 0.028 + 0.045 * (stage / 600.0)
    rich = 0.15 + 0.11 * (stage / 600.0)
    return {"common": 1.0 - rich - crystal - legendary,
            "rich": rich, "crystal": crystal, "legendary": legendary}



def mined_gem_quality_chances_v1149(tool_level, profession_level):
    # Both mining mastery and pickaxe are necessary for a perfect gemstone.
    power = min(max(1, int(tool_level)), max(1, int(profession_level)), 800)
    perfect = 0.0 if power < 240 else 0.0005 + (power - 240) / 360.0 * 0.0065
    excellent = 0.0 if power < 100 else 0.003 + (power - 100) / 500.0 * 0.042
    pure = 0.0 if power < 40 else 0.01 + (power - 40) / 560.0 * 0.12
    return {"perfect": perfect, "excellent": excellent, "pure": pure,
            "raw": 1.0 - perfect - excellent - pure}



def mining_geode_chances_v1149(tool_level, profession_level, floor):
    tool = max(1, min(800, int(tool_level)))
    prof = max(1, min(800, int(profession_level)))
    floor = max(1, min(800, int(floor or 1)))
    power = min(tool, prof)
    result = {}
    if power >= 20 and floor >= 10:
        result["stone_geode"] = 0.012 + 0.007 * (power / 600.0)
    if power >= 80 and floor >= 60:
        result["crystal_geode"] = 0.003 + 0.006 * ((power - 80) / 520.0)
    if power >= 200 and floor >= 150:
        result["astral_geode"] = 0.00025 + 0.00125 * ((power - 200) / 400.0)
    return result


