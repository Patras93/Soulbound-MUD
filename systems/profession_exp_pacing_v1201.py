# -*- coding: utf-8 -*-
"""v12.00.1: Minimum meaningful progress for professions and tools.

Keep the historical EXP reward as a lower bound.  More demanding work
receives more EXP; trivial materials never inherit the player's full level.
No changes to progression requirements, Multi Cap, SQLite or drop rates.
"""
from __future__ import annotations


def improved_work_xp(existing, required_next, level, content_level, *, tool=False):
    """Raise only underpaid awards; result is zero for actions with zero reward.

    Level-appropriate projects still take hundreds/thousands of actions on
    late levels. Easy old materials cannot be used to farm these high awards.
    This is called before existing guild/event bonuses and EXP banking.
    """
    original = max(0, int(existing or 0))
    if original == 0:
        return 0
    level = max(1, int(level or 1))
    # Even untagged legacy actions get an uplift, but no level-scaled floor.
    minimum = original * (4 if tool else 2)
    # Preserve exact historical behavior at the authored milestone 800, but
    # never disable content-aware XP pacing for *higher* unlocked levels.
    if content_level is None or level == 800:
        return minimum
    content = max(1, min(800, int(content_level or 1)))
    # ~300-1900 meaningful profession actions / ~450-2200 tool actions.
    # Deliberate long-term progression, but not 100,000+ actions per level.
    actions = (450 + int(level * 2.1)) if tool else (300 + int(level * 1.9))
    # The quality factor is strictly based on CONTENT versus skill level.
    # A level-1 resource at level 600 is not a level-600 resource.
    ratio = (content + 15.0) / (level + 15.0)
    # Advanced content must *always* remain more rewarding even when the
    # player is below the material's tier; unlike a capped multiplier, this
    # cannot flatten high-tier work into identical payouts.
    quality = ratio ** 2.5 if ratio <= 1.0 else 1.0 + 0.65 * (ratio - 1.0)
    target = int(max(0, int(required_next or 0)) * quality / max(1, actions))
    content_bonus = (content - 1) * max(1, original // 400)
    return max(original, minimum, target) + content_bonus
