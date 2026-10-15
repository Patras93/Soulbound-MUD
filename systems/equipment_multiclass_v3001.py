# -*- coding: utf-8 -*-
"""Compatibility API for the removed v3.00.1 cross-class EQ bonuses.

Soulbound v7.10.1 restores the original distinction:
* physical classes use physical, class-authored equipment;
* magic classes use magic, class-authored equipment;
* Mec alone has an authored five-stat and dual-attack hybrid kit.

Legacy gear, item identifiers, sockets, and modifications remain untouched.
"""


def crossover_bonus_v3001(item):
    """Never generate opposite-class stats/power from unrelated equipment."""
    return {}, {}


def crossover_text_v3001(item):
    """Do not advertise obsolete MultiClass EQ bonuses to screen readers."""
    return ''
