# -*- coding: utf-8 -*-
"""One source formula for basic non-Mec single-target skill critical rolls.

A deliberately small primitive: advanced effects, AoE, on-hit procs, world
state and rewards remain solely in production use_class_skill.
"""
import random

def plain_skill_damage_roll(actor, core_power, multiplier):
    """Source critical/base damage for ordinary class skills."""
    raw = max(1, int(core_power * multiplier) + random.randint(-2, 3))
    return actor.roll_critical_hit(raw)
