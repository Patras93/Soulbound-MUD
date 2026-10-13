# -*- coding: utf-8 -*-
"""Persistent, account-wide Multi Cap EXP with smoothly growing ten-level steps.

Only levels actually earned/owned by this account count. Every track contributes
its own cumulative curve, NOT a curve applied to the combined level sum.

Acquired level    Contribution of that level
   1..10                 500 EXP
  11..20                1000 EXP
  21..30                5000 EXP
  31..40                7500 EXP
  41..50               10000 EXP
and +2500 to the per-level contribution every further 10 levels, unbounded.

This module only changes per-award cap, never XP requirements or base rewards.
"""


def multi_cap_level_increment_v23217(level):
    """Increment earned by reaching *this* level; unbounded integer math."""
    level = max(1, int(level))
    if level <= 10:
        return 500
    if level <= 20:
        return 1000
    return 2500 * ((level - 1) // 10)


def multi_cap_level_value_v23217(level):
    """Cumulative EXP cap earned by having a single track at *level*.

    O(1) arithmetic even for extremely high, uncapped statistic levels.
    """
    level = max(1, int(level))
    if level <= 10:
        return 500 * level
    if level <= 20:
        return 5000 + 1000 * (level - 10)
    full, remaining = divmod(level - 20, 10)
    # 21..30 => 5000/level, 31..40 => 7500/level, ...
    return 15000 + 12500 * full * (full + 3) + 2500 * (full + 2) * remaining


def _levels(serialized):
    """Unpack integer-only GROUP_CONCAT without JSON extension requirements."""
    if not serialized:
        return []
    return [max(1, int(value)) for value in str(serialized).split(',')]


def multi_cap_calculation_v23217(conn, account_id):
    """Return (cap, sum_levels, level_parts, cap_parts), or None.

    One indexed read per award. Never cached across XP-driven level increases.
    Unlearned skills, unused classes, gear, temporary buffs, mob/floor/item
    levels are excluded. Does not mutate DB schema or account content.
    """
    account_id = int(account_id)
    try:
        row = conn.execute("""
            SELECT c.character_level, c.soul_level, c.soul_tier,
                   c.soul_weapon_mastery_level,
                   c.strength, c.dexterity, c.constitution,
                   c.intelligence, c.willpower, c.charisma,
                   (SELECT GROUP_CONCAT(MAX(COALESCE(level,1),1))
                      FROM class_progress WHERE account_id=c.account_id),
                   (SELECT GROUP_CONCAT(MAX(COALESCE(level,1),1))
                      FROM professions WHERE account_id=c.account_id),
                   (SELECT GROUP_CONCAT(MAX(COALESCE(level,1),1))
                      FROM tools WHERE account_id=c.account_id),
                   (SELECT GROUP_CONCAT(MAX(COALESCE(sp.level,1),1))
                      FROM learned_skills ls
                      LEFT JOIN skill_progress sp ON sp.account_id=ls.account_id
                                                 AND sp.skill_id=ls.skill_id
                     WHERE ls.account_id=c.account_id),
                   (SELECT GROUP_CONCAT(rank)
                      FROM ascension_progress_v021
                     WHERE account_id=c.account_id AND rank > 0)
              FROM characters c WHERE c.account_id=?
        """, (account_id,)).fetchone()
    except Exception as exc:
        # Legacy isolated mocks can omit entire character schema. For real DB
        # with partial schema, reject loudly so predeploy catches damage.
        if 'no such table: characters' in str(exc).lower():
            return None
        raise
    if row is None:
        return None
    core = [max(1, int(value or 1)) for value in row[:10]]
    chunks = {
        'postać': core[:1],
        'dusza': core[1:2],
        'soul tier': core[2:3],
        'broń duszy': core[3:4],
        'statystyki': core[4:10],
        # Primary-class fallback only when no class row is present.
        'klasy': _levels(row[10]) or [1],
        'profesje': _levels(row[11]),
        'narzędzia': _levels(row[12]),
        'skille': _levels(row[13]),
        # Ascension rank 0 is not earned; ignore it.
        'wzniesienia': _levels(row[14]),
    }
    level_parts = {name: sum(v) for name, v in chunks.items()}
    cap_parts = {name: sum(multi_cap_level_value_v23217(level) for level in v)
                 for name, v in chunks.items()}
    return sum(cap_parts.values()), sum(level_parts.values()), level_parts, cap_parts


def multi_cap_breakdown_v23215(conn, account_id):
    """Compatibility: (sum of owned levels, per-category level sums)."""
    result = multi_cap_calculation_v23217(conn, account_id)
    return (result[1], result[2]) if result is not None else None


def multi_cap_experience_v23215(conn, account_id):
    """Authoritative one global cap for ALL separate XP award categories."""
    result = multi_cap_calculation_v23217(conn, account_id)
    return result[0] if result is not None else None
