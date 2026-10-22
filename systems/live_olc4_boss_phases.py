# -*- coding: utf-8 -*-
"""v12.00.12: declarative phase tuning for ordinary existing bosses.

Stored phase payloads contain only simple JSON; no Python, callbacks, skills or
arbitrary scripts. Authored encounters and UOSS remain unchanged.
"""
from systems.encounter_brain_v1230 import _BOSS_FLAGS
from systems.monster_ai import PROTECTED_FLAGS

_ALLOWED_PROTECTED = frozenset({
    'mini_boss', 'world_boss', 'crypt_boss', 'astral_boss',
    'mythic_crypt_boss', 'mythic_astral_boss',
})


def eligible_boss(template):
    if not isinstance(template, dict) or template.get('v500_ancient_profile') is not None:
        return False
    if any(template.get(flag) for flag in PROTECTED_FLAGS if flag not in _ALLOWED_PROTECTED):
        return False
    return (any(template.get(flag) for flag in _BOSS_FLAGS)
            or str(template.get('rank', '')).lower() in ('boss', 'world_boss', 'mini_boss'))


def validate_boss_phases(template, phases):
    """Validate full (not incremental) three-stage policy, including JSON imports."""
    if not eligible_boss(template):
        raise ValueError('OLC boss: ten przeciwnik nie ma zwykłego AI faz; skryptowane bossy są chronione.')
    if not isinstance(phases, list) or not 3 <= len(phases) <= 5:
        raise ValueError('Fazy bossa: wymagane 3–5 etapów JSON.')
    previous = 100
    for index, phase in enumerate(phases, 1):
        if not isinstance(phase, dict) or set(phase) != {
            'hp_percent', 'attack_multiplier', 'duration_seconds', 'message'
        }:
            raise ValueError(f'Faza {index}: wymagane hp_percent, attack_multiplier, duration_seconds, message.')
        threshold = phase['hp_percent']
        if type(threshold) is not int or not 1 <= threshold < previous:
            raise ValueError('Progi HP muszą być liczbami całkowitymi 1–99, malejącymi.')
        previous = threshold
        mult = phase['attack_multiplier']
        if type(mult) not in (float, int) or not 1.18 <= mult <= 3.0:
            raise ValueError('Mnożnik ataku: liczba 1.18–3.0 (zachowany limit silnika AI).')
        duration = phase['duration_seconds']
        if type(duration) is not int or not 1 <= duration <= 120:
            raise ValueError('Czas fazy: od 1 do 120 sekund.')
        message = phase['message']
        if (not isinstance(message, str) or not 1 <= len(message.strip()) <= 140
                or any(ord(ch) < 32 or ord(ch) == 127 for ch in message)):
            raise ValueError('Opis fazy: od 1 do 140 znaków, bez znaków sterujących.')
    return True


def default_boss_phases(template):
    """Return the true stock phase thresholds and timings for an eligible boss."""
    if not eligible_boss(template):
        raise ValueError('Ten przeciwnik nie ma edytowalnych faz zwykłego bossa.')
    from systems.adventure_codex_v1270 import boss_phase_identity_v1270
    labels = ('', 'mobilizuje się i zmienia rytm ataku',
              'przechodzi do kontrataku i wzmacnia ofensywę',
              'walczy desperacko i uderza ze zdwojoną determinacją')
    return [dict(hp_percent=threshold, attack_multiplier=round(1.12 + 0.12 * stage, 2),
                 duration_seconds=18 + 5 * stage,
                 message=boss_phase_identity_v1270(template, stage) or labels[stage])
            for stage, threshold in enumerate((75, 50, 25), 1)]
