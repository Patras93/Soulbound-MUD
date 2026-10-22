# -*- coding: utf-8 -*-
"""Soulbound OLC17: safe, declarative ordinary-boss tactical profiles.

Templates hold validated JSON only; no scripts and no authored-UOSS rewrites.
The absence of any field means use the v19 combat behaviour unchanged.
"""
ELEMENTS = frozenset(('fire','ice','lightning','dark','poison','shadow','holy'))
ROLES = frozenset(('zbrojny','arkaniczny','obronca','furia','uzdrowiciel'))


def validate_stage_map(value, allowed, title):
    if not isinstance(value, dict) or not 1 <= len(value) <= 6:
        raise ValueError(f'{title}: wymagany słownik JSON faz 0–5 (1–6 wpisów).')
    result = {}
    for stage, seq in value.items():
        if type(stage) is not str or stage not in {'0','1','2','3','4','5'}:
            raise ValueError(f'{title}: faza musi mieć klucz tekstowy "0"–"5".')
        if (not isinstance(seq, list) or not 1 <= len(seq) <= 12
                or any(type(v) is not str or v not in allowed for v in seq)):
            raise ValueError(f'{title}: każda faza to lista 1–12 poprawnych wartości.')
        result[stage] = list(seq)
    return result


def boss_stage_cycle(template, stage, key, allowed):
    value = template.get(key)
    if not isinstance(value, dict):
        return None
    seq = value.get(str(max(0, min(5, int(stage)))))
    if not isinstance(seq, list) or not 1 <= len(seq) <= 12:
        return None
    return seq if all(type(x) is str and x in allowed for x in seq) else None
