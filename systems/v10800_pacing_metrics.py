# -*- coding: utf-8 -*-
"""Read-only actual session pace. Never adjusts XP, levels, bank or thresholds."""
from __future__ import annotations


def xp_per_hour(paid, elapsed_seconds):
    paid = max(0, int(paid or 0))
    elapsed_seconds = max(1.0, float(elapsed_seconds))
    return int(round(paid * 3600.0 / elapsed_seconds))


def level_eta_seconds(remaining_xp, gained_xp, elapsed_seconds):
    """Extrapolate measured session rate, not generator ideal or cached rewards.

    Reject very short or zero-gain sessions; avoid huge, misleading ETAs.
    """
    remaining = max(0, int(remaining_xp or 0))
    earned = max(0, int(gained_xp or 0))
    elapsed = max(0.0, float(elapsed_seconds))
    if remaining == 0:
        return 0
    if elapsed < 300.0 or earned <= 0:
        return None
    eta = remaining * elapsed / earned
    if eta > 3650 * 24 * 3600:
        return None
    return max(0, int(round(eta)))
