# -*- coding: utf-8 -*-
"""Czytelne profile na podstawie bieżącego stanu sesji lub zapisu offline.

Tylko odczyt. Nie wymusza zapisu sesji ani nie pobiera prywatnych danych.
"""
from core.live_level_caps_v5200 import cap, display

PROFILE_LIVE_FIELDS = (
    'name', 'race', 'class_name', 'active_title', 'character_level',
    'character_xp', 'soul_weapon', 'soul_level', 'soul_xp', 'soul_tier',
    'soul_weapon_mastery_level', 'soul_weapon_mastery_xp',
    'strength', 'dexterity', 'constitution', 'intelligence',
    'willpower', 'charisma', 'deaths', 'room_id',
)


def current_profile_values(saved_row, online_character=None):
    """Saved values for offline; live public fields for an online character.

    Never use float or commit/reload a live character just to display a profile.
    """
    data = dict(saved_row)
    if online_character is not None:
        for field in PROFILE_LIVE_FIELDS:
            value = getattr(online_character, field, None)
            if value is not None:
                data[field] = value
    return data


def current_cap_label(kind):
    """Read current Admin Live setting, not the historic 800 default."""
    return display(cap(kind))
