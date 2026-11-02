# -*- coding: utf-8 -*-
"""Owner-gated v104 live numeric tuning with staged publish and rollback.

Scoped to existing v104 definitions; raid phases and Soul Tier trial objectives
are validated against their native runtime shape before an atomic file publish.
Never edits user SQLite, soul-level thresholds, scripts or historical content.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import re
import sqlite3
from tempfile import NamedTemporaryFile

from systems.live_olc4_boss_phases import validate_boss_phases
from systems import soul_xp_bands_v10402 as soul_bands

PATH = Path(__file__).resolve().parent.parent / 'LIVE_CONTENT' / 'era_v10400_overrides.json'
MAX_SQLITE = (1 << 63) - 1
FIELDS = {
    'mob': {'max_hp': (1, MAX_SQLITE), 'damage': (1, MAX_SQLITE),
            'gold': (0, MAX_SQLITE), 'silver': (0, MAX_SQLITE),
            'mithril': (0, MAX_SQLITE), 'class_xp_reward': (0, MAX_SQLITE),
            'soul_reward': (0, MAX_SQLITE), 'stat_reward': (0, MAX_SQLITE)},
    'quest': {'needed': (1, 100000), 'reward_gold': (0, MAX_SQLITE),
              'reward_mithril': (0, MAX_SQLITE),
              'reward_stat_progress': (0, MAX_SQLITE)},
    'item': {'defense': (0, MAX_SQLITE), 'affix_amount': (0, MAX_SQLITE)},
    'recipe': {'min_profession_level': (1, 10**9), 'quantity': (1, 100000)},
    'room': {'recommended_mastery': (1, 10**9), 'generator_level': (1, 10**9)},
    'raid_phase': {
        f'p{phase}_{field}': bounds
        for phase in range(1, 5)
        for field, bounds in (
            ('hp_percent', (1, 99)), ('attack_pct', (118, 300)),
            ('duration_seconds', (1, 120))
        )
    },
    'soul_trial': {'needed': (1, 25), 'reward_silver': (0, MAX_SQLITE),
                   'reward_gold': (0, MAX_SQLITE), 'reward_mithril': (0, MAX_SQLITE)},
    'soul_xp_band': {'required_pct': (25, 400)},
    # v105 scoped runtime coefficients; do not edit unlock requirements or player records.
    'soul_power': {'passive_pct': (0, 30), 'weakness_pct': (0, 50),
                   'impulse_pct': (0, 100), 'impulse_cooldown': (30, 600),
                   'shield_pct': (0, 50), 'shield_seconds': (5, 120),
                   'shield_cooldown': (30, 600)},
    'eq_evolution': {'stat_pct': (25, 400), 'defense_pct': (25, 400)},
}
_REGISTRY_NAMES = {'mob': 'mobs', 'quest': 'quests', 'item': 'items',
                   'recipe': 'recipes', 'room': 'rooms',
                   'raid_phase': 'mobs', 'soul_trial': 'quests',
    'soul_power': 'soul_power', 'eq_evolution': 'eq_evolution'}
_RAID_ID = re.compile(r'v10400_raid_(1[2-9]|2[0-5])_boss_([123])\Z')
_TRIAL_ID = re.compile(r'soul_tier_([0-9]+)_trial\Z')
_PHASE_FIELD = re.compile(r'p([1-4])_(hp_percent|attack_pct|duration_seconds)\Z')
Draft = None
Baseline = None
State = None


def _empty():
    return {'schema': 1, 'rev': 0, 'active': {}, 'previous': None, 'base': {}}


def _parse_key(key):
    if not isinstance(key, str) or len(key) > 150:
        raise ValueError('Nieprawidłowy klucz zmiany')
    parts = key.split('|')
    if len(parts) != 3:
        raise ValueError('Nieprawidłowy klucz zmiany')
    kind, identifier, field = parts
    if kind not in FIELDS or field not in FIELDS[kind]:
        raise ValueError('Pole spoza bezpiecznej listy v104')
    if kind == 'soul_xp_band':
        if identifier not in soul_bands.BANDS:
            raise ValueError('Nieznane pasmo Soul Level')
    elif kind == 'raid_phase':
        if not _RAID_ID.fullmatch(identifier):
            raise ValueError('Edytowalne są tylko fazy rajdów 12–25')
    elif kind in ('soul_power', 'eq_evolution'):
        if identifier != {'soul_power': 'v10500_bron_duszy',
                          'eq_evolution': 'v10500_ewolucja_eq'}[kind]:
            raise ValueError('Nieznany moduł ustawień v105')
    elif kind == 'soul_trial':
        match = _TRIAL_ID.fullmatch(identifier)
        if not match or not 501 <= int(match.group(1)) <= 3000 or (int(match.group(1)) > 1000 and int(match.group(1)) % 10 != 0):
            raise ValueError('Próby do T1000 lub obowiązkowe Próby co 10 Tierów T1010–3000')
    elif not identifier.startswith(('v10400_', 'v10500_')) or len(identifier) > 100:
        raise ValueError('Pole spoza katalogów v104/v105')
    return kind, identifier, field


def _validate(data):
    if (not isinstance(data, dict) or set(data) != {'schema', 'rev', 'active', 'previous', 'base'}
            or type(data['schema']) is not int or data['schema'] != 1):
        raise ValueError('Nieprawidłowy format override v104')
    if type(data['rev']) is not int or not 0 <= data['rev'] < 10**9:
        raise ValueError('Nieprawidłowa rewizja')
    for rows in (data['active'], data['previous'], data['base']):
        if rows is None:
            continue
        if type(rows) is not dict or len(rows) > 3000:
            raise ValueError('Niepoprawny lub za duży zestaw zmian')
        for key, val in rows.items():
            kind, _, field = _parse_key(key)
            lo, hi = FIELDS[kind][field]
            if type(val) is not int or not lo <= val <= hi:
                raise ValueError('Wartość poza dozwolonym zakresem')
    return data


def _load():
    global State
    # Read on every command so another server process cannot silently reuse a
    # cached revision after an external publication.
    State = _validate(json.loads(PATH.read_text(encoding='utf-8'))) if PATH.exists() else _empty()
    return State


def _save(state):
    _validate(state)
    PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with NamedTemporaryFile('w', encoding='utf-8', dir=PATH.parent,
                                prefix='.era_v104_', suffix='.tmp', delete=False) as f:
            temp = f.name
            json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, PATH)
    finally:
        if temp and os.path.exists(temp):
            os.unlink(temp)


def _registry(kind, registries):
    # Read/write the actual live coefficients using the same DRAFT/CAS/revert
    # journal as every v104/v105 content edit. Never mirror values in a separate file.
    if kind == 'soul_power':
        from systems.soul_weapon_elements_v10500 import LIVE_TUNING
        return LIVE_TUNING
    if kind == 'eq_evolution':
        from systems.equipment_evolution_v10500 import LIVE_TUNING
        return LIVE_TUNING
    return registries[_REGISTRY_NAMES[kind]]


def _target(key, registries):
    kind, identifier, field = _parse_key(key)
    if kind == 'soul_xp_band':
        return {'required_pct': soul_bands.current_percent(identifier)}
    obj = _registry(kind, registries).get(identifier)
    if not isinstance(obj, dict):
        raise ValueError('Brak obiektu w rejestrze: ' + identifier)
    if kind == 'raid_phase':
        phases = obj.get('olc_boss_phases')
        if (not obj.get('boss') or not isinstance(phases, list)
                or len(phases) != 4 or not _PHASE_FIELD.fullmatch(field)):
            raise ValueError('Brak czterech zwykłych faz bossa rajdowego')
        idx, attribute = _PHASE_FIELD.fullmatch(field).groups()
        if not isinstance(phases[int(idx)-1], dict):
            raise ValueError('Nieprawidłowa faza rajdu')
        native = 'attack_multiplier' if attribute == 'attack_pct' else attribute
        if native not in phases[int(idx)-1]:
            raise ValueError('Brak parametru fazy rajdu')
    else:
        if field not in obj:
            raise ValueError('Nie ma takiego pola w rejestrze v104')
        if kind == 'soul_trial':
            tier = int(_TRIAL_ID.fullmatch(identifier).group(1))
            if (obj.get('unlocks_soul_tier') != tier
                    or obj.get('required_soul_level') != tier * 10
                    or obj.get('kind') != 'kill'):
                raise ValueError('Nieprawidłowa Próba Soul Tier — ochrona odblokowania')
    return obj


def _read_value(obj, kind, field):
    if kind != 'raid_phase':
        return obj[field]
    idx, attr = _PHASE_FIELD.fullmatch(field).groups()
    phase = obj['olc_boss_phases'][int(idx)-1]
    if attr == 'attack_pct':
        return round(float(phase['attack_multiplier']) * 100)
    return phase[attr]


def _set_value(obj, kind, field, value):
    if kind != 'raid_phase':
        obj[field] = value
        return
    idx, attr = _PHASE_FIELD.fullmatch(field).groups()
    if attr == 'attack_pct':
        obj['olc_boss_phases'][int(idx)-1]['attack_multiplier'] = round(value / 100, 2)
    else:
        obj['olc_boss_phases'][int(idx)-1][attr] = value


def _preflight(registries, base, active):
    """Build a complete validated copy first; no partial live registry edits."""
    staged = {}
    for changes in (base, active):
        for key, value in changes.items():
            kind, ident, field = _parse_key(key)
            if (kind, ident) not in staged:
                staged[kind, ident] = deepcopy(_target(key, registries))
            _set_value(staged[kind, ident], kind, field, value)
    for (kind, ident), obj in staged.items():
        if kind == 'soul_power' and obj['shield_seconds'] > obj['shield_cooldown']:
            raise ValueError('Czas działania Osłony nie może przekraczać odnowienia.')
        if kind == 'raid_phase':
            validate_boss_phases(obj, obj['olc_boss_phases'])
    return staged


def apply(registries):
    data = _load()
    staged = _preflight(registries, data['base'], data['active'])
    # Prepare the entire rate table BEFORE touching live registries. Values are
    # validated in _preflight, and no player is modified.
    rates = {name: 100 for name in soul_bands.BANDS}
    for (kind, ident), fresh in staged.items():
        if kind == 'soul_xp_band':
            rates[ident] = fresh['required_pct']
    for (kind, ident), fresh in staged.items():
        if kind == 'soul_xp_band':
            continue
        original = _registry(kind, registries)[ident]
        if kind == 'raid_phase':
            # Preserve identity of the boss template used by combat handlers.
            original['olc_boss_phases'][:] = fresh['olc_boss_phases']
        else:
            for key in (data['base'], data['active']):
                for full in key:
                    k, obj_id, field = _parse_key(full)
                    if (k, obj_id) == (kind, ident):
                        original[field] = fresh[field]
    soul_bands.update_rates(rates)
    return len(data['active'])


def reset_for_tests():
    global Draft, Baseline, State
    Draft = Baseline = State = None
    soul_bands.update_rates({name: 100 for name in soul_bands.BANDS})


def command(tail, registries, *, connection=None):
    global Draft, Baseline, State
    args = str(tail or '').split()
    action = args[0].casefold() if args else ''
    helpmsg = ('V104 ADMIN: podglad TYP ID POLE / ustaw TYP ID POLE LICZBA / '
               'sprawdz / porownaj / aktywuj POTWIERDZAM / anuluj / cofnij POTWIERDZAM. '
               'Typy: mob, quest, item, recipe, room, raid_phase, soul_trial. '
               'Rajd: raid_phase v10400_raid_12_boss_1 p1_hp_percent 75; '
               'p1_attack_pct 150; p1_duration_seconds 25. '
               'Soul: soul_trial soul_tier_501_trial needed 2 lub reward_silver 1000. '
               'Progi EXP Soul Level: soul_xp_band v10400_soul_501_1000 required_pct 120 '
               '(25–400 procent bazowego EXP). Historyczne odblokowania Tierów są chronione. '
               'wydarzenia pokazuje prawdziwą wspólną rotację inwazji.')
    if action in ('', 'pomoc', 'help'):
        return helpmsg
    try:
        state = _load()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return f'V104: nie można wczytać ustawień ({type(exc).__name__}). Nic nie zapisano.'
    if action == 'wydarzenia' and len(args) == 1:
        from systems.world_invasions_v10400 import rotation, status_text, SLOT_SECONDS
        event = rotation()
        if connection is None:
            return ('V104 WSPÓLNA INWAZJA: rotacja co 6 godzin UTC, slot '
                    f'{event["slot"]}, 3 fronty; postęp wymaga aktywnego połączenia SQLite.')
        try:
            return status_text(connection)
        except (OSError, ValueError, TypeError, sqlite3.Error) as exc:
            return f'V104 INWAZJA: błąd odczytu statusu ({type(exc).__name__}).'
    if action == 'status':
        return (f'V104 Admin Live: rewizja {state["rev"]}, aktywnych pól '
                f'{len(state["active"])}, DRAFT {len(Draft) if Draft is not None else 0}.')
    if action in ('podglad', 'ustaw') and len(args) in (4, 5):
        kind, identifier, field = args[1].casefold(), args[2], args[3]
        key = '|'.join((kind, identifier, field))
        try:
            _parse_key(key)
        except ValueError:
            return 'Nieobsługiwane pole lub identyfikator. ' + helpmsg
        try:
            obj = _target(key, registries)
        except (ValueError, KeyError):
            return 'Nie istnieje takie bezpieczne pole w rejestrze v104.'
        value = _read_value(obj, kind, field)
        if action == 'podglad' and len(args) == 4:
            return (f'V104 {kind} {identifier} {field}: aktualnie {value}; '
                    f'DRAFT {Draft.get(key) if Draft and key in Draft else "brak"}.')
        if action == 'ustaw' and len(args) == 5:
            raw = args[4]
            if not raw.isascii() or not raw.isdecimal() or len(raw) > 19:
                return 'Podaj nieujemną liczbę całkowitą bez separatorów.'
            n = int(raw)
            lo, hi = FIELDS[kind][field]
            if not lo <= n <= hi:
                return f'Zakres pola {field}: {lo}–{hi}.'
            proposed = dict(Draft if Draft is not None else state['active'])
            proposed[key] = n
            # Do not stage a malformed phase order or unsafe trial change.
            try:
                _preflight(registries, state['base'], proposed)
            except (ValueError, KeyError) as exc:
                return f'V104 DRAFT odrzucony: {exc}'
            if Draft is None:
                Baseline = state['rev']
            Draft = proposed
            return f'V104 DRAFT: {identifier} {field}: {value} -> {n}; opublikuj po sprawdzeniu.'
    if action in ('sprawdz', 'porownaj') and len(args) == 1:
        if Draft is None:
            return 'V104: brak zmian DRAFT.'
        try:
            _validate({'schema': 1, 'rev': state['rev'], 'active': Draft,
                       'previous': None, 'base': dict(state['base'])})
            _preflight(registries, state['base'], Draft)
        except (ValueError, KeyError) as exc:
            return f'V104 DRAFT odrzucony: {exc}'
        return (f'V104: DRAFT {len(Draft)} pól, CAS {Baseline}->{state["rev"]}; '
                + '; '.join(f'{k}={v}' for k, v in list(Draft.items())[:5]))
    if action == 'anuluj' and len(args) == 1:
        Draft = Baseline = None
        return 'V104: DRAFT anulowany, aktywne ustawienia niezmienione.'
    if action == 'aktywuj' and args[1:] == ['POTWIERDZAM']:
        if Draft is None:
            return 'V104: brak DRAFT.'
        if Baseline != state['rev']:
            return 'V104: konflikt rewizji CAS, odśwież DRAFT.'
        base = dict(state['base'])
        try:
            for key in Draft:
                if key not in base:
                    kind, _, field = _parse_key(key)
                    base[key] = int(_read_value(_target(key, registries), kind, field))
            _preflight(registries, base, Draft)
            new = {'schema': 1, 'rev': state['rev'] + 1, 'active': dict(Draft),
                   'previous': dict(state['active']), 'base': base}
            _save(new)
        except (OSError, ValueError, KeyError) as exc:
            return f'V104: nie opublikowano ({type(exc).__name__}: {exc}).'
        State = new
        apply(registries)
        Draft = Baseline = None
        return f'V104: opublikowano rewizję {new["rev"]}, {len(new["active"])} pól. Bez restartu.'
    if action == 'cofnij' and args[1:] == ['POTWIERDZAM']:
        if Draft is not None:
            return 'V104: anuluj najpierw DRAFT.'
        if state['previous'] is None:
            return 'V104: nie ma poprzedniej rewizji.'
        previous = dict(state['previous'])
        try:
            _preflight(registries, state['base'], previous)
            new = {'schema': 1, 'rev': state['rev'] + 1, 'active': previous,
                   'previous': dict(state['active']), 'base': dict(state['base'])}
            _save(new)
        except (OSError, ValueError, KeyError) as exc:
            return f'V104: nie cofnięto ({type(exc).__name__}: {exc}).'
        State = new
        apply(registries)
        Draft = Baseline = None
        return f'V104: cofnięto wartości w pamięci; rewizja {new["rev"]}.'
    return helpmsg
