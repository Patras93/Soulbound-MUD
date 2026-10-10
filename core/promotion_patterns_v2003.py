# -*- coding: utf-8 -*-
"""Precompiled advancement message recognizer, used by NVDA history."""
import re

_PROMOTIONS = tuple(re.compile(pattern, re.IGNORECASE) for pattern in (
    r"^Level postaci wzrasta do \d+",
    r"^Broń Duszy osiąga Soul Level \d+",
    r"^.+: Biegłość rośnie do \d+",
    r"^.+: Wzniesienie rośnie do rangi \d+",
    r"^.+ osiąga poziom \d+",
    r"^.+ awansuje na Tier \d+",
    r"^.+: awansujesz na Rangę \d+",
    r"^.+ awansuje na Skill Level \d+",
    r"^Soul Weapon Mastery wzrasta do \d+",
))


def is_level_promotion_v2003(message):
    return any(pattern.match(message) for pattern in _PROMOTIONS)
