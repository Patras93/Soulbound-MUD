# -*- coding: utf-8 -*-
"""Immutable historical 21 UOSS encounter keys; later additions are allowed."""
from __future__ import annotations

HISTORICAL_UOSS_IDS = frozenset({
    'spekkio', 'asterisks', 'dad', 'diabolos', 'harle', 'culex',
    'ruby_weapon', 'emerald_weapon', 'ozma', 'four_fiends', 'grahf',
    'hades', 'lunar_trial', 'elementals', 'gilgamesh', 'war_machines',
    'black_rabite', 'serpentarius', 'odin', 'yiazmat', 'sephiroth',
})
assert len(HISTORICAL_UOSS_IDS) == 21


def verify_historical_uoss_ids(registered):
    """Verify the old 21 IDs without restricting new v107/v110 bosses."""
    missing = HISTORICAL_UOSS_IDS.difference(registered)
    if missing:
        raise AssertionError('Brak historycznych bossow UOSS: '+', '.join(sorted(missing)))
    return len(HISTORICAL_UOSS_IDS)
