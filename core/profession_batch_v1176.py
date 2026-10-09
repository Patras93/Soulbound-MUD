"""Profession batch fairness, Soulbound v1.17.6.

Bulk smelting remains ONE action. Its difficulty is a weighted summary of
actually processed recipes (not whichever recipe happens to come first).
Its XP bonus grows with effort without multiplying by thousands of crafts:
large batches remain useful, while crafting them individually remains valuable.
"""
from __future__ import annotations

import math


def profession_batch_content_level_v1176(stages_and_weights):
    """Rounded-up XP-weighted difficulty of actually completed subrecipes."""
    total_weight = 0
    weighted_stage = 0
    for stage, weight in stages_and_weights:
        weight = max(0, int(weight))
        if not weight:
            continue
        stage = max(1, min(800, int(stage)))
        total_weight += weight
        weighted_stage += stage * weight
    if not total_weight:
        return 1
    return max(1, min(800, (weighted_stage + total_weight - 1) // total_weight))


def profession_batch_effort_v1176(crafts):
    """One craft = x1; 8 = x2; 64 = x3; no flat hard cap."""
    crafts = max(1, int(crafts))
    return 1.0 + math.log2(crafts) / 3.0
