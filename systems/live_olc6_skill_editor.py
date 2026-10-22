# -*- coding: utf-8 -*-
"""OLC 6.0: guarded editing of existing authored skills.

All modifications are data-only and retain historical IDs, mastery groups,
legacy aliases and skill learning progress.  No eval or arbitrary scripts.
"""
import json
import math

from core.classes_skills import CLASS_SKILLS
from systems.live_olc4_new_skills import ALLOWED_SCALES, _fold
from systems.live_content_v1204 import _integer, _text

TEXT_FIELDS = frozenset(('name', 'desc'))
INTEGER_FIELDS = {'unlock': (1, 800), 'mana': (0, 10**8),
                  'cooldown': (0, 86400), 'guard': (0, 10**12),
                  'base_power': (0, 10**12), 'duration': (0, 86400)}
FLOAT_FIELDS = {'mult': (0.01, 10**9), 'boost': (0.01, 10**9),
                'execute_mult': (0.01, 10**9), 'heal_pct': (0.0, 1.0),
                'drain_pct': (0.0, 1.0)}
CHOICE_FIELDS = frozenset(('scale', 'secondary_scale', 'element', 'kind'))
EDITABLE_FIELDS = (TEXT_FIELDS | frozenset(INTEGER_FIELDS) |
                   frozenset(FLOAT_FIELDS) | CHOICE_FIELDS | {'aliases', 'olc_status'})
# The combat engine already implements these elements; arbitrary identifiers
# are never accepted from the admin console.
ELEMENTS = frozenset(('fire','water','ice','lightning','earth','wind',
                      'light','dark','holy','shadow','arcane','poison'))


def _positive_float(value, field):
    if isinstance(value, bool):
        raise ValueError(f'{field}: wymagana liczba.')
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f'{field}: wymagana liczba.') from exc
    low, high = FLOAT_FIELDS[field]
    if not math.isfinite(number) or not low <= number <= high:
        raise ValueError(f'{field}: liczba {low}–{high}, bez NaN/Infinity.')
    return number


def parse_existing_skill_field(definition, field, raw):
    """Return strictly validated value; caller stores it in a draft only."""
    if field not in EDITABLE_FIELDS:
        raise ValueError('To pole skilla jest chronione; wpisz admin live pola skill ID.')
    if field not in definition and field != 'olc_status':
        raise ValueError(f'Skill nie posiada pola {field}; nie tworzę pozornej mechaniki.')
    if field == 'olc_status':
        if definition.get('kind') not in ('damage','aoe_damage') or any(k in definition for k in ('mec_authored','mec_special','special','active_special','aoe','target_mode','v1100_dual_elements')):
            raise ValueError('Status można dodać tylko zwykłemu atakowi bez skryptowanych mechanik.')
        from systems.live_olc19_status_skills import parse_status
        return parse_status(raw)
    if field in TEXT_FIELDS:
        return _text(raw, 100 if field == 'name' else 700, field)
    if field in INTEGER_FIELDS:
        return _integer(raw, *INTEGER_FIELDS[field], field)
    if field in FLOAT_FIELDS:
        return _positive_float(raw, field)
    if field == 'aliases':
        try:
            value = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError as exc:
            raise ValueError('Aliasy: wymagane JSON, np. ["nazwa", "inna nazwa"].') from exc
        if not isinstance(value, list) or len(value) > 30 or not all(isinstance(x, str) for x in value):
            raise ValueError('Aliasy: lista JSON maksymalnie 30 tekstów.')
        return [_text(x, 100, 'Alias skilla') for x in value]
    if not isinstance(raw, str):
        raise ValueError(f'{field}: wymagana nazwa parametru.')
    value = raw.strip().lower()
    if field in ('scale', 'secondary_scale'):
        if value not in ALLOWED_SCALES:
            raise ValueError('Statystyka: strength/dexterity/intelligence/wisdom/willpower/constitution.')
    elif field == 'element':
        if value not in ELEMENTS:
            raise ValueError('Nieznany żywioł. Dozwolone: ' + ', '.join(sorted(ELEMENTS)))
    elif field == 'kind':
        # Moving to a different target scope (healing an enemy / attacking an
        # ally) is dangerous. Only ordinary single / area damage may switch.
        if definition['kind'] not in ('damage','aoe_damage') or value not in ('damage','aoe_damage'):
            raise ValueError('Zmiana rodzaju: tylko damage ↔ aoe_damage dla zwykłego ataku.')
        if any(field in definition for field in ('mec_authored','target_mode','aoe','v1100_dual_elements')):
            raise ValueError('Skill ma specjalne zasady celowania; zmiana rodzaju jest zablokowana.')
    return value


def _catalogue():
    return {row['id']: row for rows in CLASS_SKILLS.values() for row in rows}


def validate_existing_skill_edits(edits, new_skills=None):
    """Validate patches with current runtime schemas and stable legacy names."""
    if not isinstance(edits, dict) or len(edits) > 5461:
        raise ValueError('OLC: maksymalnie 5461 istniejących skilli.')
    indexed = _catalogue()
    owned_names = {}
    for sid, row in indexed.items():
        for label in [row.get('name',''), *row.get('aliases', [])]:
            if label:
                owned_names.setdefault(_fold(label), set()).add(sid)
    for sid, meta in (new_skills or {}).items():
        for label in [meta.get('name',''), *meta.get('aliases', [])]:
            if label:
                owned_names.setdefault(_fold(label), set()).add(sid)
    for sid, fields in edits.items():
        original = indexed.get(sid)
        if original is None or not isinstance(fields, dict) or not fields:
            raise ValueError(f'Nieznana edycja skilla: {sid}.')
        if not set(fields) <= EDITABLE_FIELDS:
            raise ValueError(f'{sid}: id, klasa, mastery_choice_group oraz pola specjalne są chronione.')
        patched = dict(original, **fields)
        for field, value in fields.items():
            checked = parse_existing_skill_field(original, field, value)
            if checked != value:
                raise ValueError(f'{sid}.{field}: niewłaściwy typ wartości.')
        # Never drop historical names, IDs, or user commands on a rename.
        old_labels = {_fold(original['name']), *(_fold(a) for a in original.get('aliases', []))}
        new_labels = {_fold(patched['name']), *(_fold(a) for a in patched.get('aliases', []))}
        if not old_labels <= new_labels:
            raise ValueError(f'{sid}: nie wolno usuwać istniejących nazw/aliasów.')
        for label in new_labels - old_labels:
            owners = owned_names.get(label, set())
            if owners - {sid}:
                raise ValueError(f'{sid}: nazwa/alias zajęty przez inny skill.')
            owned_names.setdefault(label, set()).add(sid)
    return len(edits)


def stage_existing_skill(draft, key, field, raw):
    indexed = _catalogue()
    original = indexed.get(key)
    if original is None:
        raise ValueError('Nieznany identyfikator skilla.')
    staged = dict(draft['skill_edits'].get(key, {}))
    current = dict(original, **staged)
    if isinstance(raw, str) and raw.strip().casefold() in ('auto', 'oryginalne'):
        # Clear the override instead of freezing today's value. Old aliases
        # stay intact because the authored catalogue remains the fallback.
        staged.pop(field, None)
        if not staged:
            draft['skill_edits'].pop(key, None)
        else:
            draft['skill_edits'][key] = staged
        return draft
    parsed = parse_existing_skill_field(current, field, raw)
    if field == 'name':
        # Previous name is guaranteed to remain an alias after publication.
        old_name = current['name']
        aliases = list(current.get('aliases', []))
        if _fold(old_name) != _fold(parsed) and _fold(old_name) not in {_fold(x) for x in aliases}:
            aliases.append(old_name)
            staged['aliases'] = aliases
    staged[field] = parsed
    draft['skill_edits'][key] = staged
    return draft
