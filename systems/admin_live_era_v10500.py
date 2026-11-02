# -*- coding: utf-8 -*-
"""v105 owner-only façade over the existing durable Admin Live DRAFT/CAS engine.

Edits the *same* v104 journal/revision, so cross-version rollbacks remain
atomic and old admin commands cannot silently overwrite a newer draft.
"""
from world.v10500_region_index import REGIONS
from systems import admin_live_era_v10400 as native

HELP = ('V105 ADMIN LIVE: regiony / region SLUG / status / podglad TYP ID POLE / '
        'ustaw TYP ID POLE LICZBA / sprawdz / porownaj / aktywuj POTWIERDZAM / '
        'anuluj / cofnij POTWIERDZAM. Typy: mob, quest, room, recipe, item, soul_trial. '
        'Przykład: ustaw mob v10500_przesmyk_boss_1 max_hp 500000000. '
        'Próby: ustaw soul_trial soul_tier_1010_trial needed 2. '
        'Broń Duszy: ustaw soul_power v10500_bron_duszy shield_pct 20; '
        'pola passive_pct, weakness_pct, impulse_pct, impulse_cooldown, '
        'shield_pct, shield_seconds, shield_cooldown. '
        'EQ: ustaw eq_evolution v10500_ewolucja_eq stat_pct 120 '
        'lub defense_pct 120. Wspólny dziennik DRAFT/CAS z v104; brak restartu.')


def command(tail, registries, *, connection=None):
    words = str(tail or '').strip().split()
    if not words or words[0].casefold() in ('help', 'pomoc'):
        return HELP
    if words[0].casefold() in ('regiony', 'krainy') and len(words) == 1:
        return ('V105 KRAINY: ' + '; '.join(f'{slug} {low}–{high}'
                for slug, name, low, high, *_ in REGIONS) + '.')
    if words[0].casefold() == 'region' and len(words) >= 2:
        token = ' '.join(words[1:]).casefold()
        found = next((r for r in REGIONS if token in (r[0], r[1].casefold())), None)
        if found is None:
            return 'Nieznany region. Użyj admin live era v105 regiony.'
        slug, name, low, high, *_ = found
        key = 'v10500_' + slug + '_'
        return (f'V105 {name}, poziomy {low}–{high}: '
                f'{sum(r.startswith(key) for r in registries["rooms"])} pomieszczeń; '
                f'{sum(r.startswith(key) for r in registries["mobs"])} potworów; '
                f'{sum(r.startswith(key) for r in registries["quests"])} questów. '
                'Zmiany liczbowe: admin live era v105 ustaw ...')
    return native.command(tail, registries, connection=connection).replace('V104', 'V105').replace('v104)', 'v105)')
