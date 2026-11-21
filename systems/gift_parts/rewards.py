"""Skalowanie EXP i waluty, niezalezne od zapisu SQLite."""
from .policy import gift_kind

def reward_plan(day, master, character):
    """Deterministic, varying gold/EXP; every advent gift > any normal daily."""
    kind = gift_kind(day)
    master = int(master)
    if master <= 0:
        raise ValueError('Missing master account')
    level = max(1, int(character.character_level))
    needed = max(0, int(character.character_xp_to_next()))
    variant = (day.toordinal() + master % 29) % 5
    if kind == 'daily':
        coin = 3500 + variant * 2600 + min(15000, level * 8)
        exp = min(10**15, max(10000, needed // (14-variant)))
    else:
        coin = 130000 + (day.day - 1) * 5500 + variant * 17000
        exp = min(3 * 10**15, max(120000, needed // (4 if variant < 3 else 3)))
        if day.day in (6, 24):
            coin *= 2
            exp = min(3 * 10**15, exp * 2)
    return dict(kind=kind, silver=int(coin), exp=int(exp), variant=variant)


def _daily_growth_amount(needed, kind, *, stats=False):
    """Small bounded share of this axis' OWN next level; never free levels.

    Daily 1%, Advent 3%; stats need a smaller *input* since their existing
    gateway applies the established 4x/racial/stat-stage multipliers.
    """
    needed = max(0, int(needed or 0))
    if not needed:
        return 0
    percent = 3 if kind == 'advent' else 1
    value = max(1, needed * percent // (800 if stats else 100))
    return min(1_000_000, value)


def award_daily_growth(session, kind):
    """Bonus for existing progression tracks, inside caller's gift SAVEPOINT.

    One existing/learned track gets one bounded grant, never an unlock or a
    simulated action.  Magitek uses its ordinary class and known skill tracks.
    The existing Multi Cap controls each payment; the old EXP Bank is untouched.
    """
    from core.progression_resources import class_mastery_xp_to_next, skill_xp_to_next
    from core.bootstrap_economy_professions import profession_max_level, tool_max_level
    from systems.experience_bank_v2011 import banked_experience_v2011
    from systems.atomic_progression_rewards_v10400 import (
        award_soul_xp_atomic_v10400, award_stats_xp_atomic_v10400,
        award_class_xp_atomic_v10400,
    )

    db, char, aid = session.server.db, session.character, int(session.account_id)
    if char is None or int(char.account_id) != aid:
        raise ValueError('Prezent: postac nie nalezy do konta.')
    if kind not in ('daily', 'advent'):
        raise ValueError('Prezent: nieznany rodzaj nagrody.')
    gained = {}

    soul_amount = _daily_growth_amount(char.soul_xp_to_next(), kind)
    if soul_amount:
        paid, _ = award_soul_xp_atomic_v10400(db, char, aid, soul_amount)
        gained['soul'] = paid

    stat_names = tuple(char.STAT_PROGRESS_FIELDS)
    stat_amounts = {name: _daily_growth_amount(char.stat_growth_threshold_for(name), kind, stats=True)
                    for name in stat_names}
    if any(stat_amounts.values()):
        stat_results = award_stats_xp_atomic_v10400(db, char, aid, stat_amounts,
                                                    targets=stat_names)
        gained['stats'] = sum(int(paid) for _name, paid, _notes in stat_results)

    # The real, currently selected class (including Magitek); don't activate
    # or create arbitrary other classes.
    class_name = str(char.class_name)
    row = db.class_progress_row(aid, class_name)
    class_amount = _daily_growth_amount(class_mastery_xp_to_next(int(row['level'])), kind)
    if class_amount:
        paid, _ = award_class_xp_atomic_v10400(db, aid, class_name,
                                               class_amount, int(row['level']))
        gained['class'] = paid

    weapon_amount = _daily_growth_amount(char.soul_weapon_mastery_xp_to_next(), kind)
    if weapon_amount:
        paid = banked_experience_v2011(db, aid, weapon_amount, 'skill',
                                        int(char.soul_weapon_mastery_level),
                                        source_key='soul_weapon_mastery')
        if paid:
            char.add_soul_weapon_mastery_xp(paid)
            db.save_character(char, commit=False)
            gained['weapon'] = paid

    # Only genuinely learned skills, not unlearned IDs in a class catalogue.
    # A gift isn't a cast: the number of uses must stay unchanged.
    skills_paid = 0
    for skill_id in sorted(db.learned_skill_ids(aid)):
        row = db.skill_progress(aid, skill_id)
        level, xp = int(row['level']), int(row['xp'])
        amount = _daily_growth_amount(skill_xp_to_next(level), kind)
        if not amount:
            continue
        paid = banked_experience_v2011(db, aid, amount, 'skill', level,
                                        source_key=skill_id)
        if not paid:
            continue
        xp += paid
        needed = skill_xp_to_next(level)
        if needed > 0 and xp >= needed:
            xp -= needed
            level += 1  # at most one level per gift
        db.conn.execute('UPDATE skill_progress SET level=?,xp=? '
                        'WHERE account_id=? AND skill_id=?', (level, xp, aid, skill_id))
        skills_paid += paid
    gained['skills'] = skills_paid

    # Existing profession/tool records are the unlock boundary: never INSERT
    # all known professions or tools simply because a player logged in.
    for table, keyfield, track, threshold, maximum, save, countfield in (
        ('professions', 'profession', 'profession', session.profession_xp_to_next,
         profession_max_level, db.save_profession, 'actions'),
        ('tools', 'tool_type', 'tool', session.tool_xp_to_next,
         tool_max_level, db.save_tool, 'uses'),
    ):
        total = 0
        rows = db.conn.execute('SELECT * FROM ' + table + ' WHERE account_id=? '
                               'ORDER BY ' + keyfield, (aid,)).fetchall()
        for row in rows:
            key = str(row[keyfield]); level = int(row['level']); xp = int(row['xp'])
            # Ignore dormant level-one placeholders that were only created by
            # reading a help/status command; they aren't played/unlocked yet.
            if level <= 1 and xp <= 0 and int(row[countfield]) <= 0:
                continue
            if level >= maximum(key):
                continue
            amount = _daily_growth_amount(threshold(level, key), kind)
            if not amount:
                continue
            paid = banked_experience_v2011(db, aid, amount, track, level, source_key=key)
            if not paid:
                continue
            xp += paid
            needed = threshold(level, key)
            if needed > 0 and xp >= needed:
                xp -= needed
                level += 1
            save(aid, key, level, xp, int(row[countfield]))
            total += paid
        gained[track] = total
    return gained
