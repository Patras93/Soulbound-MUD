# -*- coding: utf-8 -*-
"""Wlasne czasy akcji nowych profesji v110; stare 22 narzedzia nietkniete.

Ten katalog jest jedynym zrodlem czasow nowo dodanych narzedzi.
"""
from __future__ import annotations

# Wartosci autorskie w sekundach: czas poziomu 1 oraz minimalny czas.
V110_TIMINGS = {
    "alchemy_sound": (20, 6),
    "mirrorcraft": (22, 7),
    "paleoecology": (25, 7),
    "phytoarch": (24, 6),
    "hydrochart": (18, 5),
    "technometeo": (28, 8),
    "matterlore": (21, 6),
    "stormtech": (26, 7),
}


# Dokladne wartosci starego zachowania v107: v1.13.16 stosuje
# get(tool, 20) / get(tool, 5), gdy v107 nie ma jawnych wpisow.
# Rejestrowanie ich jawnie NIE zmienia gry; pozwala audytowac wszystkie 38.
V107_FALLBACK_TIMING = (20, 5)


def register_timing(specs, base_times, minimum_times):
    """Rejestracja pelnego katalogu bez zmiany historycznych parametrow."""
    from core.archetypes.chaos import PROFESSION_SPECS as legacy_v107
    new_tools = {spec[1] for spec in specs}
    legacy_tools = {spec[1] for spec in legacy_v107}
    if (len(specs) != 8 or new_tools != set(V110_TIMINGS)
        or len(legacy_v107) != 8 or len(legacy_tools) != 8
        or legacy_tools & new_tools):
        raise ValueError('v110: niezgodne identyfikatory nowych i starych narzedzi')
    updates = dict(V110_TIMINGS)
    for tool in legacy_tools:
        if tool not in base_times and tool not in minimum_times:
            updates[tool] = V107_FALLBACK_TIMING
        elif base_times.get(tool) != V107_FALLBACK_TIMING[0] or minimum_times.get(tool) != V107_FALLBACK_TIMING[1]:
            raise ValueError('v110: wykryto nietypowy czas profesji v107: ' + tool)
    if new_tools & (set(base_times) | set(minimum_times)):
        raise ValueError('v110: nadpisanie historycznego narzedzia zabronione')
    if any(type(base) is not int or type(minimum) is not int or
           not (0 < minimum < base <= 120) for base, minimum in updates.values()):
        raise ValueError('v110: nieprawidlowy czas narzedzia')
    # All preflight checks are complete. No old timing values are overwritten.
    base_times.update({tool: vals[0] for tool, vals in updates.items()})
    minimum_times.update({tool: vals[1] for tool, vals in updates.items()})
    return len(new_tools)
