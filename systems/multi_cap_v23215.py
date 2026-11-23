# -*- coding: utf-8 -*-
"""Persistent, account-wide Multi Cap EXP: character, class and ascension ONLY.

Soul, soul tier, weapon mastery, stats, skills, tools and professions
never add to the cap, though their XP rewards remain separately capped.
Eligible tracks contribute their cumulative curve, not a combined level sum.

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
    from systems.published_24_revolution import extra_cap_value
    bonus = extra_cap_value(level)-extra_cap_value(level-1) if level>1 else extra_cap_value(1)
    if level <= 10:
        return 500 + bonus
    if level <= 20:
        return 1000 + bonus
    return 2500 * ((level - 1) // 10) + bonus


def multi_cap_level_value_v23217(level):
    """Cumulative EXP cap earned by having a single track at *level*.

    O(1) arithmetic even for extremely high levels.
    """
    level = max(1, int(level))
    from systems.published_24_revolution import extra_cap_value
    bonus = extra_cap_value(level)
    if level <= 10:
        return 500 * level + bonus
    if level <= 20:
        return 5000 + 1000 * (level - 10) + bonus
    full, remaining = divmod(level - 20, 10)
    # 21..30 => 5000/level, 31..40 => 7500/level, ...
    return 15000 + 12500 * full * (full + 3) + 2500 * (full + 2) * remaining + bonus


def _levels(serialized):
    """Unpack integer-only GROUP_CONCAT without JSON extension requirements."""
    if not serialized:
        return []
    return [max(1, int(value)) for value in str(serialized).split(',')]


def multi_cap_calculation_v23217(conn, account_id):
    """Return (cap, sum_levels, level_parts, cap_parts), or None.

    One indexed read per award. Never cached across XP-driven level increases.
    Unused classes, gear, skills, soul, stats, professions and tools
    are excluded. Does not mutate DB schema or account content.
    """
    account_id = int(account_id)
    try:
        row = conn.execute("""
            SELECT c.character_level,
                   (SELECT GROUP_CONCAT(MAX(COALESCE(level,1),1))
                      FROM class_progress WHERE account_id=c.account_id AND active_slot=1),
                   (SELECT GROUP_CONCAT(rank)
                      FROM ascension_progress_v021
                     WHERE account_id=c.account_id AND rank > 0
                       AND (track NOT LIKE 'class:%' OR track = 'class:' ||
                         (SELECT cp.class_name FROM class_progress cp
                          WHERE cp.account_id=c.account_id AND cp.active_slot=1 LIMIT 1))),
                   (SELECT GROUP_CONCAT(lvl) FROM (
                         SELECT MAX(COALESCE(level,1),1) AS lvl FROM class_progress
                         WHERE account_id=c.account_id GROUP BY class_name)),
                   (SELECT GROUP_CONCAT(rank) FROM ascension_progress_v021
                         WHERE account_id=c.account_id AND rank > 0 AND
                           (track NOT LIKE 'class:%' OR SUBSTR(track,7) IN
                             (SELECT class_name FROM class_progress
                              WHERE account_id=c.account_id)))
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
    # v116.00.62: exclusively the character, owned class levels and
    # earned ascension ranks may raise the CAP. All other axes are outside.
    from systems.published_22_state import WORLD_OVERRIDES
    include_owned = bool(WORLD_OVERRIDES.get('multi_cap_all_owned_classes', False))
    chunks = {
        'postać': [max(1, int(row[0] or 1))],
        'klasy': _levels(row[3] if include_owned else row[1]) or [1],
        'wzniesienia': _levels(row[4] if include_owned else row[2]),
    }
    level_parts = {name: sum(v) for name, v in chunks.items()}
    category_bonus = WORLD_OVERRIDES.get('multi_cap_category_bonus', {})
    overall_bonus = WORLD_OVERRIDES.get('multi_cap_bonus_percent',100)
    cap_parts = {name: sum(multi_cap_level_value_v23217(level) for level in v)
                 for name, v in chunks.items()}
    # Bonuses only. Never decrease baseline contribution, never discard banked XP.
    # v102.00.13: 2x the baseline Multi Cap for every earned track.
    # Published dawny edytor category/global bonuses remain multiplicative on top,
    # and setting them to AUTO cannot restore the obsolete lower default.
    cap_parts = {name: (2 * base * category_bonus.get(name,100) * overall_bonus + 9999)//10000
                 for name, base in cap_parts.items()}
    return sum(cap_parts.values()), sum(level_parts.values()), level_parts, cap_parts


def multi_cap_breakdown_v23215(conn, account_id):
    """Compatibility: (sum of owned levels, per-category level sums)."""
    result = multi_cap_calculation_v23217(conn, account_id)
    return (result[1], result[2]) if result is not None else None


def multi_cap_experience_v23215(conn, account_id):
    """Authoritative one global cap for ALL separate XP award categories."""
    result = multi_cap_calculation_v23217(conn, account_id)
    return result[0] if result is not None else None
