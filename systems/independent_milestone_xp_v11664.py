# -*- coding: utf-8 -*-
"""Fame and EP source-based rebalancing, independent of removed Multi CAP.

No XP award cap, bank and no change to stored levels. Rewards follow the
new progression pace at all levels, instead of an outdated quadratic curve.
"""


def ep_xp_per_point_v11664(character_level):
    level = max(1, int(character_level))
    from core.progression_resources import character_xp_to_next
    # About 0.2% of one level for each newly discovered EP; no CAP dependency.
    return max(100, character_xp_to_next(level) // 500)


def fame_xp_per_first_v11664(character_level):
    level = max(1, int(character_level))
    from core.progression_resources import character_xp_to_next
    # First Fame reward about 0.5% of next-level threshold, not CAP.
    return max(200, character_xp_to_next(level) // 200)
