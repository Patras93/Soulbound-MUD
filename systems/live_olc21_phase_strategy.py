# -*- coding: utf-8 -*-
"""OLC18/v21: declarative phase-by-phase ordinary-boss strategies.

Values are inert JSON mappings from phase 0..5 to one integer/enum. Missing
phase means inherit the unchanged global OLC setting or native AI default.
No source-authored UOSS/ancient encounters, player statistics, or SQL schema.
"""

PHASE_STRATEGY_FIELDS = {
    'olc_boss_phase_tactic_intervals': (2, 12),
    'olc_boss_phase_guardian_intervals': (2, 12),
    'olc_boss_phase_guard_thresholds': (5, 95),
    'olc_boss_phase_support_intervals': (2, 12),
    'olc_boss_phase_support_durations': (1, 30),
    'olc_boss_phase_support_priorities': ('weakest', 'strongest'),
    'olc_boss_phase_rally_hp_thresholds': (5, 95),
    'olc_boss_phase_rally_intervals': (2, 12),
    'olc_boss_phase_rally_durations': (1, 30),
}

# Display only genuine runtime fallbacks; a numeric auto interval depends on HP.
PHASE_FALLBACKS = {
    'olc_boss_phase_tactic_intervals': 'olc_boss_tactic_interval',
    'olc_boss_phase_guardian_intervals': 'olc_boss_guardian_interval',
    'olc_boss_phase_guard_thresholds': 'olc_boss_guard_threshold',
    'olc_boss_phase_support_intervals': 'olc_boss_support_interval',
    'olc_boss_phase_support_durations': 'olc_boss_support_duration',
    'olc_boss_phase_support_priorities': 'olc_boss_support_priority',
    'olc_boss_phase_rally_hp_thresholds': 'olc_boss_rally_hp_threshold',
    'olc_boss_phase_rally_intervals': 'olc_boss_rally_interval',
    'olc_boss_phase_rally_durations': 'olc_boss_rally_duration',
}


def validate_phase_strategy(field, value):
    """Reject booleans, floating-point numbers, extra keys and unknown phases."""
    rule = PHASE_STRATEGY_FIELDS.get(field)
    if rule is None:
        raise ValueError('Nieznane ustawienie strategii fazowej.')
    if type(value) is not dict or not 1 <= len(value) <= 6:
        raise ValueError('Fazy: wymagany niepusty obiekt JSON (maksymalnie 6 faz).')
    for phase, setting in value.items():
        if type(phase) is not str or phase not in ('0', '1', '2', '3', '4', '5'):
            raise ValueError('Fazy: klucze muszą mieć postać "0" do "5".')
        if isinstance(rule[0], str):
            if type(setting) is not str or setting not in rule:
                raise ValueError('Priorytet: weakest albo strongest.')
        elif type(setting) is not int or not rule[0] <= setting <= rule[1]:
            raise ValueError(f'{field}: liczba całkowita {rule[0]}–{rule[1]}.')
    return True


def phase_setting(template, stage, field, fallback):
    """Resolve active phase override; invalid legacy data safely falls back."""
    if field not in PHASE_STRATEGY_FIELDS:
        return fallback
    try:
        phase = str(int(stage))
    except (ValueError, TypeError, OverflowError):
        return fallback
    if phase not in ('0', '1', '2', '3', '4', '5'):
        return fallback
    mapping = template.get(field)
    if type(mapping) is not dict:
        return fallback
    value = mapping.get(phase)
    rule = PHASE_STRATEGY_FIELDS[field]
    if isinstance(rule[0], str):
        return value if type(value) is str and value in rule else fallback
    return value if type(value) is int and rule[0] <= value <= rule[1] else fallback
