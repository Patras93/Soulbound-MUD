# -*- coding: utf-8 -*-
"""Eliza: optional v115 vampire mercenary, distinct from the 38 legacy contracts.

The original 38-class catalogue and its IDs stay unchanged.  This module only
extends the runtime tavern/AI roster. All hired contracts still use the native
SQLite schema, owner-scaled combat, default 3-mercenary limit and existing tactics.
"""
from systems.mercenary_taverns import (
    MERCENARIES as LEGACY_MERCENARIES,
    mercenary_role as _legacy_role,
    price_silver as _legacy_price,
    mercenary_skill_lines_v12211 as _legacy_skill_lines,
)
from storage.db_shared import normalize_lookup_text

VAMPIRE_CONTRACT = {
    'id': 'wampir',
    'name': 'Eliza',
    'role': 'Wampirzyca',
    'race': 'Wampir',
    'class': 'Nekromanta',  # A REAL existing combat class, not a new player class.
    'cost': 240,
    'power': 1.18,
    'attack_type': 'magic',
    'ability': 'Dotyk Nocy',
}

VAMPIRE_SPECIALIST = (
    'Krwiopijczyni Nocy',
    'wybiera osłabione cele i odzyskuje życie dla drużyny zadanymi obrażeniami',
    'Dotyk Nocy',
    'Szept Krwi',
    'Uścisk Ciemności',
)
VAMPIRE_VOICE = 'Noc jest po naszej stronie.'

# This is an independent runtime overlay; NEVER append to the old 38 dictionary.
MERCENARIES = dict(LEGACY_MERCENARIES)
MERCENARIES[VAMPIRE_CONTRACT['id']] = VAMPIRE_CONTRACT


def mercenary_role(raw):
    """Recognize Eliza/vampire, otherwise retain native legacy matching."""
    key = normalize_lookup_text(raw)
    if key in {'wampir', 'wampirzyca', 'eliza'}:
        return 'wampir'
    return _legacy_role(raw)


def price_silver(character, role):
    if role != 'wampir':
        return _legacy_price(character, role)
    discount = max(0, min(75, int(character.shop_discount_percent())))
    return max(1, VAMPIRE_CONTRACT['cost'] * 100 * (100 - discount) // 100)


def specialist_profile(role):
    if role == 'wampir':
        return VAMPIRE_SPECIALIST
    from systems.mercenary_specialists_v1240 import SPECIALISTS
    return SPECIALISTS[role]


def mercenary_skill_lines_v12211(role):
    if role != 'wampir':
        return _legacy_skill_lines(role)
    return [
        'Eliza (Wampirzyca): umiejętności wykonywane AUTOMATYCZNIE.',
        '1. Dotyk Nocy i ofensywne zaklęcia Nekromanty: magia skaluje się '
        'z pełną mocą i poziomem właściciela. Ataki wybiera sama Eliza.',
        '2. Wampiryczne odnowienie: część rzeczywiście zadanych obrażeń '
        'leczy najbardziej rannego sojusznika; blokada leczenia działa normalnie.',
        '3. Krwiopijczyni Nocy: Szept Krwi i Uścisk Ciemności. '
        'Walka, taktyki i limit trzech najemników jak u pozostałych.',
    ]
