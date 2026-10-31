# -*- coding: utf-8 -*-
"""v104 stage 10: conservative gate against loss/overflow in legacy INTEGER writes.

This is NOT the final TEXT-based persistence conversion. Rejecting a write is
safer than truncating a balance or partially updating a character. Do not
change schema or player data from this module.
"""
from __future__ import annotations

from core.big_numbers_v10400 import SQLITE_INT64_MIN, SQLITE_INT64_MAX


class SQLiteNumericLimitV104(OverflowError):
    """A value cannot be committed losslessly to the legacy INTEGER columns."""


def require_sqlite_int64(axis: str, value: int) -> int:
    if type(value) is not int:
        raise TypeError(f'{axis}: wymagany int bez float i bez bool.')
    if value < SQLITE_INT64_MIN or value > SQLITE_INT64_MAX:
        raise SQLiteNumericLimitV104(
            f'{axis}: poza bezpiecznym zakresem INTEGER SQLite; '
            'zapis wstrzymany, nie obcinam EXP ani salda.'
        )
    return value


def preflight_character_v104(c, *, exact_text_axes=frozenset()) -> None:
    """Run before *any* character wallet or progression SQL write."""
    axes = (
        'account_id', 'strength', 'dexterity', 'constitution',
        'intelligence', 'willpower', 'charisma', 'stat_progress',
        'strength_progress', 'dexterity_progress',
        'constitution_progress', 'intelligence_progress',
        'willpower_progress', 'charisma_progress', 'soul_level', 'soul_xp',
        'soul_tier', 'soul_weapon_mastery_level', 'soul_weapon_mastery_xp',
        'silver', 'gold', 'mithril', 'character_level', 'character_xp',
        'deaths',
    )
    for axis in axes:
        if axis in exact_text_axes:
            # The exact number is verified by the isolated TEXT rehearsal writer.
            # All other INTEGER fields retain their strict preflight guard.
            from core.big_numbers_v10400 import canonical_uint
            canonical_uint(getattr(c, axis))
            continue
        require_sqlite_int64('characters.' + axis, getattr(c, axis))
