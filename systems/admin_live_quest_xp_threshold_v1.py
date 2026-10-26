# -*- coding: utf-8 -*-
"""Safe OLC DRAFT-only bulk editing of *existing positive* quest XP rewards.

Does not write SQLite, publish a revision, change quest goals or grant any XP.
Uses the same canonical OLC fields, aliases and full service.validate as single
edits; cannot create a new XP axis on a quest that did not pay that axis.
"""
import copy
import time

from data.quests import QUESTS
from systems.live_quest_olc_v1209 import parse_quest_edit, QUEST_XP_ALIASES
from systems.quest_combat_salvage_v102007 import is_combat_salvage_quest
from core.progression_resources import (
    v0270_quest_character_reward,
    v0190_quest_stat_reward,
    v0190_quest_soul_reward,
    v0522_combat_quest_class_reward,
    v0522_is_profession_quest,
)

FIELDS = {
    'xp_postaci': 'olc_reward_xp',
    'xp_bieglosci': 'olc_reward_class_xp',
    'xp_duszy': 'olc_reward_soul_xp',
    'xp_statystyk': 'olc_reward_stat_xp',
    'xp_profesji': 'reward_profession_xp',
    'xp_narzedzia': 'reward_tool_xp',
    'xp_sila': 'olc_reward_stat_strength',
    'xp_zrecznosc': 'olc_reward_stat_dexterity',
    'xp_kondycja': 'olc_reward_stat_constitution',
    'xp_inteligencja': 'olc_reward_stat_intelligence',
    'xp_wola': 'olc_reward_stat_willpower',
    'xp_charyzma': 'olc_reward_stat_charisma',
}
BASIC_FIELDS = tuple(FIELDS[name] for name in (
    'xp_postaci', 'xp_bieglosci', 'xp_duszy', 'xp_statystyk',
    'xp_profesji', 'xp_narzedzia'))
STAT_INDIVIDUAL = tuple(v for k, v in FIELDS.items() if k in (
    'xp_sila', 'xp_zrecznosc', 'xp_kondycja',
    'xp_inteligencja', 'xp_wola', 'xp_charyzma'))
CANONICAL = {**{k: v for k, v in FIELDS.items()}, **{
    v: v for v in FIELDS.values()}, **{
    k: v for k, v in QUEST_XP_ALIASES.items() if v in FIELDS.values()
}}
MAX_QUEST_OVERRIDES = 8000
MAX_VALUE = 10**15


def _amount(raw, label, minimum=1):
    # Strictly integers; reject 1.5, scientific notation, negative and bool.
    s = str(raw)
    if not s.isascii() or not s.isdigit() or len(s) > 16:
        raise ValueError(f'{label}: wpisz dodatnia liczbe calkowita.')
    result = int(s)
    if not minimum <= result <= MAX_VALUE:
        raise ValueError(f'{label}: zakres {minimum}–{MAX_VALUE}.')
    return result


def _fields(name):
    key = str(name).strip().lower()
    if key == 'wszystkie':
        return BASIC_FIELDS
    if key not in CANONICAL:
        raise ValueError('Pole EXP: xp_postaci, xp_bieglosci, xp_duszy, '
                         'xp_statystyk, xp_profesji, xp_narzedzia, '
                         'xp_sila, xp_zrecznosc, xp_kondycja, '
                         'xp_inteligencja, xp_wola, xp_charyzma lub wszystkie.')
    return (CANONICAL[key],)


def _available(quest, qid, field):
    combat = (str(quest.get('kind') or '') in (
        'kill', 'legendary_rare', 'world_boss', 'party_contract')
        or is_combat_salvage_quest(quest, qid))
    if field == 'olc_reward_class_xp':
        return combat
    if field == 'olc_reward_soul_xp':
        return combat or not v0522_is_profession_quest(quest)
    if field == 'reward_profession_xp':
        return bool(quest.get('reward_profession') or
                    quest.get('required_profession') or
                    quest.get('reward_profession_xp'))
    if field == 'reward_tool_xp':
        return bool(quest.get('reward_tool_type') or
                    quest.get('specialist_tool_type') or
                    quest.get('reward_tool_xp'))
    return True


def _base(quest, field):
    # A source absent for profession/tool XP is NOT a zero-value reward to fill.
    if field in quest:
        return quest[field]
    if field == 'olc_reward_xp':
        return v0270_quest_character_reward(quest)
    if field == 'olc_reward_class_xp':
        return v0522_combat_quest_class_reward(quest)
    if field == 'olc_reward_soul_xp':
        return v0190_quest_soul_reward(quest)
    if field == 'olc_reward_stat_xp' or field in STAT_INDIVIDUAL:
        return v0190_quest_stat_reward(quest)
    return 0


def _current(quest, draft_patch, field):
    if field in draft_patch:
        return draft_patch[field]
    if field in STAT_INDIVIDUAL:
        # A shared override applies to all six statistics unless overridden.
        if 'olc_reward_stat_xp' in draft_patch:
            return draft_patch['olc_reward_stat_xp']
        if field in quest:
            return quest[field]
        if 'olc_reward_stat_xp' in quest:
            return quest['olc_reward_stat_xp']
    return _base(quest, field)


def _eligible(service, field, threshold, catalog=None, ordered_ids=None):
    if catalog is None:
        catalog = {**QUESTS, **service.draft.get('quests', {})}
    if ordered_ids is None:
        ordered_ids = sorted(catalog)
    selected = []
    zeros, inapplicable, already_high, protected = 0, 0, 0, 0
    for qid in ordered_ids:
        quest = catalog[qid]
        if not _available(quest, qid, field):
            inapplicable += 1
            continue
        draft_patch = service.draft['quest_edits'].get(qid, {})
        active_patch = service.active['quest_edits'].get(qid, {})
        if (field == 'olc_reward_stat_xp' and any(
                k in draft_patch or k in quest for k in STAT_INDIVIDUAL)):
            protected += 1  # A shared setting cannot overwrite individual overrides.
            continue
        value = _current(quest, draft_patch, field)
        try:
            amount = int(value)
        except (ValueError, TypeError, OverflowError):
            protected += 1
            continue
        if amount <= 0:
            zeros += 1
            continue
        if amount >= threshold:
            already_high += 1
            continue
        # Existing unsaved edits are explicit decisions, not bulk targets.
        if field in draft_patch and draft_patch.get(field) != active_patch.get(field):
            protected += 1
            continue
        selected.append((qid, amount))
    return selected, (zeros, inapplicable, already_high, protected)


def plan(service, name, threshold_raw):
    threshold = _amount(threshold_raw, 'Prog EXP')
    fields = _fields(name)
    rows = []
    examples = []
    totals = [0, 0, 0, 0]
    # One consistent catalog/order for all axes in the same bulk operation.
    catalog = {**QUESTS, **service.draft.get('quests', {})}
    ordered_ids = sorted(catalog)
    for field in fields:
        matched, skipped = _eligible(service, field, threshold, catalog, ordered_ids)
        rows.extend((qid, field, old) for qid, old in matched)
        for i, value in enumerate(skipped):
            totals[i] += value
        if matched:
            examples.extend(f'{qid}/{field}: {value}' for qid, value in matched[:3])
    count = len({qid for qid, _, _ in rows} | set(service.draft['quest_edits']))
    if count > MAX_QUEST_OVERRIDES:
        raise ValueError(f'Za duzo questow do edycji: {count} (limit {MAX_QUEST_OVERRIDES}).')
    info = (f'EXPPROGI: pole {name}; próg {threshold}; '
            f'do zmiany {len(rows)} nagród w {len(set(qid for qid, _, _ in rows))} questach; '
            f'pominięto: zero/brak {totals[0]}, niedozwolone {totals[1]}, '
            f'co najmniej próg {totals[2]}, szczególne/ręczne {totals[3]}. '
            f'Przykłady: {"; ".join(examples[:9]) or "brak"}.')
    return rows, info


def preview(service, name, threshold):
    _, info = plan(service, name, threshold)
    return info + ' Podgląd bez zapisu. Użyj: admin live expprogi ustaw POLE PRÓG NOWY_EXP.'


def stage(service, name, threshold_raw, target_raw):
    threshold = _amount(threshold_raw, 'Prog EXP')
    target = _amount(target_raw, 'Docelowy EXP')
    if target < threshold:
        raise ValueError('Nowy EXP musi byc >= progowi, aby podnosic za niskie nagrody.')
    _started = time.perf_counter()
    rows, info = plan(service, name, threshold)
    _planned = time.perf_counter()
    if not rows:
        return info + ' Brak zmian; DRAFT pozostaje bez zmian.'
    draft = copy.deepcopy(service.draft)
    for qid, field, old in rows:
        canonical, value = parse_quest_edit(field, target)
        draft['quest_edits'].setdefault(qid, {})[canonical] = value
    _copied = time.perf_counter()
    validated = service.validate(draft)
    _validated = time.perf_counter()
    # Privacy: log only phase duration, never quest IDs or input values.
    if (_validated - _started) >= 0.25:
        print('[PERF ADMIN EXPPROGI] plan_ms=%d, draft_ms=%d, validate_ms=%d' % (
            round((_planned - _started) * 1000),
            round((_copied - _planned) * 1000),
            round((_validated - _copied) * 1000),
        ), flush=True)
    # No partial updates, all changes go into the same validated DRAFT.
    service.draft = draft
    return (info + f' Przygotowano ustawienie na {target}; {validated}. '
            'Nie opublikowano. Uzyj admin live porownaj i admin live aktywuj POTWIERDZAM.')
