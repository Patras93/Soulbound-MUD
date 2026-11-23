# -*- coding: utf-8 -*-
"""Complete, NVDA-readable progression overview and separately computed CAP.

All rows are read from the account's real progression tables.  The final cap
comes from the same authoritative calculator as the EXP reward pipeline.
"""
from systems.multi_cap_v23215 import multi_cap_calculation_v23217, multi_cap_level_increment_v23217


_STAT_LABELS = (
    ('strength', 'Siła'),
    ('dexterity', 'Zręczność'),
    ('constitution', 'Kondycja'),
    ('intelligence', 'Inteligencja'),
    ('willpower', 'Siła Woli'),
    ('charisma', 'Charyzma'),
)


def _level(value):
    return max(1, int(value or 1))


def _section(lines, title, entries):
    """No truncation: pack small groups of entries for NVDA/TCP efficiency."""
    lines.append(title)
    if not entries:
        lines.append('Brak odblokowanych poziomów w tej kategorii.')
        return
    for i in range(0, len(entries), 8):
        lines.append('; '.join(entries[i:i + 8]) + '.')


def level_overview_lines_v23216(conn, account_id, main_class='', *, uncapped=False):
    """Read-only, complete level list with the global EXP cap as the LAST line.

    Primary character level and its progress are emitted by level command;
    this function lists the other permanent levels, never mobs/floors/items.
    """
    aid = int(account_id)
    if not uncapped:
        result = multi_cap_calculation_v23217(conn, aid)
        if result is None:
            return ['Nie można odczytać Multi Cap z bazy postaci.']
        cap, levels, parts, cap_parts = result
    character = conn.execute('''
        SELECT soul_level, soul_tier, soul_weapon_mastery_level,
               strength, dexterity, constitution, intelligence, willpower, charisma
          FROM characters WHERE account_id=?
    ''', (aid,)).fetchone()
    if character is None:
        return ['Nie można odczytać poziomów postaci.']

    lines = ['WSZYSTKIE POZIOMY POSTACI — ' + ('bez CAP i EXP Banku' if uncapped else 'MULTI CAP: postać, klasy, wzniesienia')]
    lines.append('DUSZA — ' + ('niezależny rozwój' if uncapped else 'poza Multi CAP') + '. Dusza: poziom {}. Soul Tier: poziom {}. Broń Duszy — biegłość: poziom {}.'.format(
        _level(character['soul_level']), _level(character['soul_tier']),
        _level(character['soul_weapon_mastery_level'])))

    classes = conn.execute('''
        SELECT class_name, level, active_slot FROM class_progress
         WHERE account_id=? ORDER BY CASE WHEN active_slot=0 THEN 0
             WHEN active_slot IS NOT NULL THEN 1 ELSE 2 END,
             active_slot, class_name COLLATE NOCASE
    ''', (aid,)).fetchall()
    if classes:
        active_count = sum(r['active_slot'] == 1 for r in classes)
        class_entries = [
            '{}: poziom {}{}'.format(str(r['class_name']), _level(r['level']),
                ' (główna)' if r['active_slot'] == 1 else ' (archiwalna, bez umiejętności klasy)')
            for r in classes
        ]
        _section(lines, f'KLASY — odblokowanych {len(classes)}, aktywnych {active_count}:', class_entries)
    else:
        # Matches the +1 primary-class fallback in multi_cap_breakdown_v23215.
        _section(lines, 'KLASY:', [f'{main_class or "Klasa główna"}: poziom 1 (główna)'])

    _section(lines, 'STATYSTYKI — niezależny rozwój, poziomy bazowe bez EQ:' if uncapped else 'STATYSTYKI — poza Multi CAP, poziomy bazowe bez EQ:', [
        f'{label}: poziom {_level(character[key])}' for key, label in _STAT_LABELS
    ])

    skills = conn.execute('''
        SELECT ls.skill_id AS name, COALESCE(sp.level, 1) AS level
          FROM learned_skills ls
          LEFT JOIN skill_progress sp ON sp.account_id=ls.account_id
               AND sp.skill_id=ls.skill_id
         WHERE ls.account_id=? ORDER BY ls.skill_id COLLATE NOCASE
    ''', (aid,)).fetchall()
    _section(lines, f'SKILLE — {"niezależny rozwój" if uncapped else "poza Multi CAP"}, nauczonych {len(skills)}:', [
        f'{r["name"]}: poziom {_level(r["level"])}' for r in skills
    ])

    professions = conn.execute('''
        SELECT profession AS name, level FROM professions
         WHERE account_id=? ORDER BY profession COLLATE NOCASE
    ''', (aid,)).fetchall()
    _section(lines, f'PROFESJE — {"niezależny rozwój" if uncapped else "poza Multi CAP"}, rozwijanych {len(professions)}:', [
        f'{r["name"]}: poziom {_level(r["level"])}' for r in professions
    ])

    tools = conn.execute('''
        SELECT tool_type AS name, level FROM tools
         WHERE account_id=? ORDER BY tool_type COLLATE NOCASE
    ''', (aid,)).fetchall()
    _section(lines, f'NARZĘDZIA — {"niezależny rozwój" if uncapped else "poza Multi CAP"}, rozwijanych {len(tools)}:', [
        f'{r["name"]}: poziom {_level(r["level"])}' for r in tools
    ])

    ascensions = conn.execute('''
        SELECT track AS name, rank FROM ascension_progress_v021
         WHERE account_id=? AND rank > 0 ORDER BY track COLLATE NOCASE
    ''', (aid,)).fetchall()
    _section(lines, f'WZNIESIENIA — rozwijanych {len(ascensions)}:', [
        f'{r["name"]}: poziom {int(r["rank"])}' for r in ascensions
    ])

    if uncapped:
        lines.append('EXP bez limitu pojedynczej nagrody i bez nowych wpłat do EXP Banku.')
        lines.append('Soul XP jest wstrzymany do unlock następnego Soul Tieru.')
    else:
        lines.append(f'Łączna suma poziomów wliczanych do Multi CAP: {levels}. CAP rośnie tylko z poziomem postaci, klas i wzniesień.')
        lines.append('Przyrost poziomu 1-10: +500 EXP; 11-20: +1000; 21-30 +5000; od 31 co 10 poziomów stawka rośnie o +2500 EXP.')
        lines.append(f'Your experience cap is {cap} EXP.')
    return lines
