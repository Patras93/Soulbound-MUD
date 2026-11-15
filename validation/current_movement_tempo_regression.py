# -*- coding: utf-8 -*-
"""Mandatory tempo contract for real movement code; no real user DB/port."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))


def run():
    from core.mines_threat import GUIDE_STEP_DELAY, WALK_STEP_DELAY
    from player.session_mixins.movement import SessionMovementMixin
    from player.session_mixins.guide_navigation import SessionGuideNavigationMixin
    assert GUIDE_STEP_DELAY == WALK_STEP_DELAY == 0.10
    checks=1
    obj=object.__new__(SessionMovementMixin)
    for direction in ('north','south','east','west','up','down'):
        for guided in (False,True):
            actual=obj.movement_delay(direction,guided=guided)
            assert actual == 0.10, (direction,guided,actual)
            checks+=1
    # Estimated guide time must also reflect the same real delay.
    guide=object.__new__(SessionGuideNavigationMixin)
    guide.movement_delay=obj.movement_delay
    route=[('north','a'),('down','b'),('down','c'),('west','d')]
    assert abs(guide.estimated_guide_seconds(route)-0.4)<1e-9
    checks+=1
    print(f'MOVEMENT 0.10 SECOND PER STEP: {checks}/{checks} PASS',flush=True)
    return checks

if __name__=='__main__':
    run()
