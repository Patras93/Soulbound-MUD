# -*- coding: utf-8 -*-
"""Unique combat phase identities for the 12 v4.00.0 Ancient bosses.

Only v500-marked mobs are affected. Enemy offence may grow; players'
health/damage/skills are never capped or secretly reduced. No new save state.
"""
import time

# Thresholds, distinct attack rhythms and notices per Ancient boss.
PROFILES = (
    ((81, 53, 23), ('Korona Wygnańców', 'Przysięga Bezimiennych', 'Sąd Pustego Tronu'), (1.20, 1.36, 1.60), ('dark','holy','dark')),
    ((78, 43, 17), ('Popioły Ołtarza', 'Odwrócenie Światła', 'Drugie Wschodzenie'), (1.26, 1.43, 1.71), ('holy','fire','fire')),
    ((70, 48, 16), ('Nici Zapomnienia', 'Zasłona Pamięci', 'Niekończąca się Noc'), (1.19, 1.49, 1.79), ('dark','arcane','dark')),
    ((83, 56, 29), ('Runiczna Blokada', 'Pękająca Matryca', 'Pieczęć Ostateczna'), (1.17, 1.34, 1.66), ('arcane','earth','arcane')),
    ((86, 61, 31), ('Pierwszy Piorun', 'Zamieć Kryształów', 'Burza Trzech Serc'), (1.23, 1.51, 1.85), ('lightning','ice','lightning')),
    ((74, 46, 22), ('Zatrute Korzenie', 'Sąd Prastarego Boru', 'Rozkwit Końca'), (1.16, 1.39, 1.74), ('poison','earth','poison')),
    ((77, 49, 14), ('Ostrze Szronu', 'Święta Zima', 'Wieczny Wyrok'), (1.24, 1.52, 1.84), ('ice','holy','ice')),
    ((69, 39, 18), ('Sztandar Płomieni', 'Ostatnia Szarża', 'Spopielony Horyzont'), (1.30, 1.59, 1.92), ('fire','earth','fire')),
    ((84, 52, 20), ('Trzęsienie Tronów', 'Echo Zatraconych', 'Głos Pustych Królów'), (1.20, 1.46, 1.76), ('earth','dark','earth')),
    ((82, 44, 13), ('Zew Martwego Morza', 'Pochłonięte Gwiazdy', 'Bezgwiezdny Przypływ'), (1.18, 1.48, 1.91), ('water','dark','water')),
    ((73, 42, 19), ('Pierwsza Pieczęć', 'Rozdarcie Piątej Pieczęci', 'Brama Pustki'), (1.29, 1.54, 1.87), ('arcane','lightning','arcane')),
    ((80, 50, 10), ('Pamięć Dusz', 'Dwie Korony', 'Sąd Wszystkich Dusz'), (1.21, 1.57, 1.98), ('holy','dark','holy')),
)


def unique_phase(mob, template, now=None):
    """Return a single audible message on a new threshold, once per mob."""
    idx = template.get('v500_ancient_profile')
    if idx is None:
        return None
    if not mob or not getattr(mob, 'alive', False) or int(getattr(mob, 'hp', 0)) <= 0:
        return None
    thresholds, names, multipliers, elements = PROFILES[int(idx)]
    custom = template.get('olc_ancient_phases')
    if custom is not None:
        from systems.live_olc22_empire import validate_ancient
        try:
            validate_ancient(custom)
        except (ValueError,TypeError):
            custom = None  # no runtime crash from corrupted historic state
        if custom is not None:
            thresholds = tuple(stage['hp_percent'] for stage in custom)
            names = tuple(stage['name'] for stage in custom)
            multipliers = tuple(stage['attack_percent'] / 100 for stage in custom)
            elements = tuple(stage['element'] for stage in custom)
    maximum = max(1, int(getattr(mob, 'adaptive_max_hp_v11330', 0) or template.get('max_hp', 1)))
    pct = 100.0 * max(0, int(mob.hp)) / maximum
    target = sum(pct <= t for t in thresholds)
    prior = max(0, int(getattr(mob, 'v1230_boss_phase', 0) or 0))
    if target <= prior:
        return None
    mob.v1230_boss_phase = target
    mob.v1230_phase_attack_multiplier = multipliers[target - 1]
    mob.v500_phase_element = elements[target - 1]
    now = time.monotonic() if now is None else float(now)
    duration = (custom[target-1]['duration_seconds'] if custom is not None else 16.0 + target * 7.0)
    mob.monster_ai_empowered_until_v1160 = now + duration
    return (f"{template.get('name', 'Pradawny')}: FAZA {target}/3 — {names[target-1]}. "
            f"Następne ataki: {elements[target-1]}. Przygotuj obronę przed kontratakiem.")


def effective_elemental_template(mob, template):
    """Switch only a v500 Ancient's actual elemental attacks with the phase."""
    if 'v500_ancient_profile' not in template:
        return template
    active = getattr(mob, 'v500_phase_element', None)
    if not active or active == 'physical':
        return template
    out = dict(template)
    out['attack_elements_v11339'] = (active,)
    return out


def validate_profiles():
    assert len(PROFILES) == 12
    for thresholds, names, multipliers, elements in PROFILES:
        assert len(names) == len(multipliers) == len(elements) == 3
        assert 100 > thresholds[0] > thresholds[1] > thresholds[2] > 0
        assert 1.0 < multipliers[0] < multipliers[1] < multipliers[2]
    return len(PROFILES)
