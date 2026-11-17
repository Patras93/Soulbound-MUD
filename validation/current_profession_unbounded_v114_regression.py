# -*- coding: utf-8 -*-
"""Gameplay checks for meaningful profession/tool XP past the old level 800.

Read-only, pure arithmetic: never requires or changes player data.
"""
from __future__ import annotations

import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from systems.profession_exp_pacing_v1201 import improved_work_xp
from systems.profession_xp_v1203 import quest_reward_floor_v1203, reward_xp_v1203


def run():
    checks = 0
    quest = lambda tier: {'generator_level': tier, 'needed': 10, 'repeatable': False}
    for tool in (False, True):
        for level in (801, 1000, 5000, 60000):
            required = 1_000_000_000
            tagged = reward_xp_v1203(25, required, level, level,
                                     tool=tool, content_key='genuine-high-tier')
            trivial = reward_xp_v1203(25, required, level, 1,
                                      tool=tool, content_key='genuine-high-tier')
            assert tagged > trivial >= 25, (tool, level, tagged, trivial)
            checks += 1
            low_work = improved_work_xp(25, required, level, 1, tool=tool)
            high_work = improved_work_xp(25, required, level, level, tool=tool)
            assert high_work > low_work >= 25, (tool, level, low_work, high_work)
            checks += 1
            high_quest = quest_reward_floor_v1203(25, required, level, quest(level), tool=tool)
            low_quest = quest_reward_floor_v1203(25, required, level, quest(1), tool=tool)
            assert high_quest > low_quest >= 25, (tool, level, high_quest, low_quest)
            checks += 1
            for calc in (
                lambda: reward_xp_v1203(0, required, level, level,
                                        tool=tool, content_key='genuine-high-tier'),
                lambda: improved_work_xp(0, required, level, level, tool=tool),
                lambda: quest_reward_floor_v1203(0, required, level, quest(level), tool=tool),
            ):
                assert calc() == 0, (tool, level)
                checks += 1
        # The authored 800 milestone remains unchanged and cannot fabricate
        # bonus awards by using high-level content or fake quest tags.
        assert reward_xp_v1203(25, 1_000_000, 800, 900,
                               tool=tool, content_key='x') == 25
        checks += 1
        assert quest_reward_floor_v1203(25, 1_000_000, 800, quest(900), tool=tool) == 25
        checks += 1
    return checks


if __name__ == '__main__':
    _passed=run()
    print(f'PROFESSION/TOOL XP AFTER 800: {_passed}/{_passed} PASS')
