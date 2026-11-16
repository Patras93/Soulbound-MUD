# -*- coding: utf-8 -*-
"""v113.00.31: EXP for a NEW achievement, in its actual progression domain.

The caller owns one deferred SQLite transaction containing achievement INSERT
and every payout. No user messages or foreign-session state are touched here.
All payouts use the current Multi Cap and the manually redeemed EXP bank remains
untouched. The only eligible event is a successful INSERT of a new milestone.
"""
from __future__ import annotations

from core.progression_resources import (
    character_xp_to_next, class_mastery_xp_to_next, soul_xp_to_next,
    skill_xp_to_next, soul_weapon_mastery_xp_to_next,
)
from core.progression_600 import CHARACTER_MAX_LEVEL, SOUL_MAX_LEVEL, SOUL_WEAPON_MASTERY_MAX_LEVEL, SKILL_MAX_LEVEL
from core.bootstrap_economy_professions import profession_max_level, tool_max_level
from core.classes_skills import CLASS_SKILLS
from systems.experience_bank_v2011 import banked_experience_v2011
from systems.atomic_progression_rewards_v10400 import (
    award_soul_xp_atomic_v10400, award_stats_xp_atomic_v10400,
    award_class_xp_atomic_v10400,
)
from systems.atomic_character_experience_v10400 import award_character_xp_atomic_v10400

# A bounded fraction of the CURRENT next-level requirement, not an additional
# multiplier to existing combat, profession, quest or bank reward formulae.
_TIER_PERCENT = {'Bronze': 2, 'Silver': 4, 'Gold': 6, 'Platinum': 8, 'Mythic': 10}
_MAX_PER_AXIS = 1_000_000
# Achievements originally capped offensive skills at only 1M EXP even at
# high mastery. Skill-only, milestone-specific bounds; other axes unchanged.
_SKILL_TIER_PERCENT = {'Bronze': 10, 'Silver': 15, 'Gold': 20, 'Platinum': 25, 'Mythic': 30}
_MAX_SKILL_MILESTONE = 1_000_000_000


def skill_milestone_exp_v11332(needed, tier):
    needed = max(0, int(needed or 0))
    return (min(_MAX_SKILL_MILESTONE,
                max(1, needed * _SKILL_TIER_PERCENT[tier] // 100))
            if needed else 0)

# Explicit reward domains prevent a fishing achievement from awarding combat
# skills or a combat milestone from raising a fishing rod.
_COMBAT = frozenset({'goblin_kills', 'rare_kills', 'boss_kills', 'bestiary_unique', 'bounties_completed'})
_FISHING = frozenset({'rare_fish_caught'})
_MINING = frozenset({'gems_found'})
_EXPLORATION = frozenset({'exploration_rooms'})
_ADVENTURE = frozenset({'chests_opened'})
_CAREER = frozenset({'profession_masters', 'profession_transcendents'})
_SOUL = frozenset({'soul_level'})
_CLASS = frozenset({'multiclass_classes'})


def reward_domains_v11331(metric):
    if metric in _COMBAT:
        return ('character', 'soul', 'class', 'stats', 'combat_skill')
    if metric in _FISHING:
        return ('profession:Wędkarstwo', 'tool:fishing')
    if metric in _MINING:
        return ('profession:Górnictwo', 'tool:mining')
    if metric in _EXPLORATION:
        return ('character', 'profession:Kartografia', 'tool:cartography_profession')
    if metric in _ADVENTURE:
        return ('character', 'soul')
    if metric in _SOUL:
        return ('character', 'soul_weapon')
    if metric in _CLASS:
        return ('character', 'class', 'stats')
    if metric in _CAREER:
        return ('character', 'soul')
    return ()


def _bonus(needed, tier):
    needed = max(0, int(needed or 0))
    return min(_MAX_PER_AXIS, max(1, needed * _TIER_PERCENT[tier] // 100)) if needed else 0


def _profession_reward(session, name, tier):
    db, aid = session.server.db, session.account_id
    row = db.profession(aid, name)
    level, xp = int(row['level']), int(row['xp'])
    if level >= profession_max_level(name):
        return 0
    gain = banked_experience_v2011(db, aid,
        _bonus(session.profession_xp_to_next(level, name), tier),
        'profession', level, source_key=name)
    if not gain:
        return 0
    xp += gain
    while level < profession_max_level(name):
        needed = session.profession_xp_to_next(level, name)
        if not needed or xp < needed:
            break
        xp -= needed
        level += 1
    if level >= profession_max_level(name):
        xp = 0
    db.save_profession(aid, name, level, xp, int(row['actions']))
    return gain


def _tool_reward(session, name, tier):
    db, aid = session.server.db, session.account_id
    if not session.valid_tool_type(name):
        return 0
    row = db.tool(aid, name)
    level, xp = int(row['level']), int(row['xp'])
    if level >= tool_max_level(name):
        return 0
    gain = banked_experience_v2011(db, aid,
        _bonus(session.tool_xp_to_next(level, name), tier),
        'tool', level, source_key=name)
    if not gain:
        return 0
    xp += gain
    while level < tool_max_level(name):
        needed = session.tool_xp_to_next(level, name)
        if not needed or xp < needed:
            break
        xp -= needed
        level += 1
    if level >= tool_max_level(name):
        xp = 0
    db.save_tool(aid, name, level, xp, int(row['uses']))
    return gain


def _combat_skill_reward(session, tier):
    """One known offensive skill of the real primary class; no fake skill use."""
    c, db, aid = session.character, session.server.db, session.account_id
    learned = db.learned_skill_ids(aid)
    candidates = [s for s in CLASS_SKILLS.get(c.class_name, ())
                  if s['id'] in learned and s.get('kind') in ('damage', 'dot', 'attack')]
    if not candidates:
        return None
    skill = candidates[0]
    row = db.skill_progress(aid, skill['id'])
    level, xp = int(row['level']), int(row['xp'])
    if level >= SKILL_MAX_LEVEL:
        return None
    paid = banked_experience_v2011(db, aid,
        skill_milestone_exp_v11332(skill_xp_to_next(level), tier), 'skill', level, source_key=skill['id'])
    if not paid:
        return None
    xp += paid
    while level < SKILL_MAX_LEVEL:
        needed = skill_xp_to_next(level)
        if not needed or xp < needed:
            break
        xp -= needed
        level += 1
    if level >= SKILL_MAX_LEVEL:
        xp = 0
    db.conn.execute('UPDATE skill_progress SET level=?,xp=? WHERE account_id=? AND skill_id=?',
                    (level, xp, aid, skill['id']))
    # Critically do not increment skill_progress.uses: an achievement is not a cast.
    return skill['name'], paid


def award_achievement_experience_v11331(session, metric, tier):
    """Apply the mapped XP synchronously, inside the *caller's* SAVEPOINT.

    A failed payout raises and prevents the achievement from being unlocked.
    No extra EXP bank deposits/withdrawals are introduced.
    """
    domains = reward_domains_v11331(metric)
    if not domains or tier not in _TIER_PERCENT:
        return []
    db, c, aid = session.server.db, session.character, session.account_id
    if c is None or int(c.account_id) != int(aid):
        raise ValueError('Brak właściwej postaci odbiorcy osiągnięcia.')
    labels = []
    for domain in domains:
        if domain.startswith('profession:'):
            name = domain.split(':', 1)[1]
            paid = _profession_reward(session, name, tier)
            if paid: labels.append(f'{name} +{paid}')
        elif domain.startswith('tool:'):
            name = domain.split(':', 1)[1]
            paid = _tool_reward(session, name, tier)
            if paid: labels.append(f'{session.tool_display_name_v11343(name)} +{paid}')
        elif domain == 'character' and int(c.character_level) < CHARACTER_MAX_LEVEL:
            paid, _notes = award_character_xp_atomic_v10400(
                db, c, aid, _bonus(character_xp_to_next(c.character_level), tier))
            if paid: labels.append(f'postać +{paid}')
        elif domain == 'soul' and int(c.soul_level) < SOUL_MAX_LEVEL:
            paid, _notes = award_soul_xp_atomic_v10400(
                db, c, aid, _bonus(soul_xp_to_next(c.soul_level), tier))
            if paid: labels.append(f'Dusza +{paid}')
        elif domain == 'class':
            class_name = str(c.class_name)
            level = session.class_mastery_level(class_name)
            paid, _result = award_class_xp_atomic_v10400(
                db, aid, class_name, _bonus(class_mastery_xp_to_next(level), tier), level)
            if paid: labels.append(f'biegłość {class_name} +{paid}')
        elif domain == 'stats':
            # Individual current stat requirements and individual Multi Caps.
            reward = {name: _bonus(c.stat_growth_threshold_for(name), tier)
                      for name in c.STAT_PROGRESS_FIELDS}
            paid = award_stats_xp_atomic_v10400(db, c, aid, reward,
                                               targets=tuple(c.STAT_PROGRESS_FIELDS))
            total = sum(n for _key, n, _messages in paid)
            if total: labels.append(f'staty +{total}')
        elif domain == 'soul_weapon' and int(c.soul_weapon_mastery_level) < SOUL_WEAPON_MASTERY_MAX_LEVEL:
            gain = banked_experience_v2011(db, aid,
                _bonus(soul_weapon_mastery_xp_to_next(c.soul_weapon_mastery_level), tier),
                'skill', int(c.soul_weapon_mastery_level), source_key='soul_weapon_mastery')
            if gain:
                c.add_soul_weapon_mastery_xp(gain)
                db.save_character(c, commit=False)
                labels.append(f'Broń Duszy +{gain}')
        elif domain == 'combat_skill':
            skill_reward = _combat_skill_reward(session, tier)
            if skill_reward:
                name, paid = skill_reward
                labels.append(f'umiejętność {name} +{paid}')
    return labels
