# -*- coding: utf-8 -*-
"""Version-neutral regression: historical tool tiers + endless levels after 800."""
from __future__ import annotations

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import bootstrap_economy_professions as b


def run():
    checks = 0
    # No monkey-patching caps: these checks must exercise the actual game path.
    cases = ((1, 1), (800, 80), (801, 80), (809, 80), (810, 81),
             (820, 82), (1000, 100), (5010, 501), (10000, 1000))
    for level, tier in cases:
        observed = b.tool_tier(level)
        assert observed == tier, (level, tier, observed)
        checks += 1
        assert b.tool_tier_access_level(level) <= level, level
        checks += 1
        bonus = b.tool_tier_bonus_chance(level)
        assert 0 <= bonus < 1, (level, bonus)
        checks += 1
    assert b.tool_tier(810) > b.tool_tier(800)
    checks += 1
    assert b.tool_tier(10000) > b.tool_tier(5010)
    checks += 1
    for level in range(790, 850):
        assert b.tool_tier(level + 1) >= b.tool_tier(level), level
        checks += 1
    # Labels for the new tiers must not claim they are from tier 80.
    assert '81' in b.tool_tier_name('crafting', 810)
    checks += 1
    assert b.tool_tier_name('fishing', 800) != b.tool_tier_name('fishing', 810)
    checks += 1
    # Optional garbage level does not automatically qualify for Over Cap.
    from systems.experience_cap_v2009 import combat_overcap_v2009
    for invalid in ('broken', '', object(), float('nan')):
        assert not combat_overcap_v2009({'boss': True, 'generator_level': invalid}, 1000)
        checks += 1
    assert combat_overcap_v2009({'boss': True, 'generator_level': 1050}, 1000)
    checks += 1
    assert not combat_overcap_v2009({'boss': True, 'generator_level': 950}, 1000)
    checks += 1
    return checks


if __name__ == '__main__':
    print(f'CURRENT TOOL TIER / OVERCAP REGRESSION: {run()} PASS')
