from core.progression_600 import CLASS_MASTERY_MAX_LEVEL

V0861_BASE_SHOP_PRICES_SILVER = {
    "healing_potion": 100,
    "leather_vest": 600,
    "lucky_charm": 750,
    "iron_gauntlets": 900,
    "iron_boots": 900,
    "iron_helmet": 1_200,
    "forge_charm": 1_500,
    "iron_leggings": 1_800,
    "iron_guard": 2_800,
    "fishing_rod": 1200,
    "pickaxe": 1200,
    "saw": 1200,
    "crafting_hammer": 1200,
    "chef_knife": 1200,
    "herbalist_sickle": 1200,
    "alchemy_mortar": 1200,
    "jeweler_pliers": 1200,
}


V1138_CLASS_TIER_PRICE_ANCHORS = (
    # Internal silver. A regular piece should cost roughly a handful of useful
    # quests at the same progression point; a full set is a goal, not a wall.
    (1, 1_000),
    (10, 5_000),
    (20, 10_000),
    (30, 20_000),
    (40, 40_000),
    (50, 75_000),
    (100, 500_000),
    (150, 1_750_000),
    (200, 6_250_000),
    (300, 37_500_000),
    (400, 150_000_000),
    (500, 300_000_000),
    (600, 500_000_000),
)


def _v1138_class_tier_price(master):
    master = max(1, min(CLASS_MASTERY_MAX_LEVEL, int(master or 1)))
    if master <= V1138_CLASS_TIER_PRICE_ANCHORS[0][0]:
        return V1138_CLASS_TIER_PRICE_ANCHORS[0][1]
    if master >= V1138_CLASS_TIER_PRICE_ANCHORS[-1][0]:
        return V1138_CLASS_TIER_PRICE_ANCHORS[-1][1]
    for (m0, p0), (m1, p1) in zip(
        V1138_CLASS_TIER_PRICE_ANCHORS,
        V1138_CLASS_TIER_PRICE_ANCHORS[1:],
    ):
        if m0 <= master <= m1:
            ratio = (master - m0) / float(m1 - m0)
            return max(1, int(round(p0 + (p1 - p0) * ratio)))
    return V1138_CLASS_TIER_PRICE_ANCHORS[-1][1]


V0861_CLASS_TIER_BASE_SILVER = {
    mastery: _v1138_class_tier_price(mastery)
    for mastery in (1, *range(10, CLASS_MASTERY_MAX_LEVEL + 1, 10))
}


V0861_CLASS_SLOT_PRICE_FACTOR = {
    "head": 1.00,
    "body": 1.60,
    "hands": 0.85,
    "legs": 1.30,
    "feet": 0.85,
    "charm": 1.10,
    "ring": 1.20,
    "necklace": 1.40,
}
