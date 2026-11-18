# -*- coding: utf-8 -*-
"""v115 combat first-clear switch: queue new Fame XP, retain ordinary kill rewards."""
from __future__ import annotations
from systems.v115.fame_combat_capture import resolve_fame_objective, stage_final_combat_reward
from systems.v115.fame_reward_snapshot import RewardSnapshot
from systems.v115.fame_repeat_rewards import stage_repeat_exp


def stage_delayed_first_clear(conn, session, mob, template, *,
                              character_xp, soul_xp, class_xp, stat_xp,
                              class_levels, class_max_level, overcap, now=None):
    """Call inside an existing kill transaction, after final reward calculations.

    True means caller must suppress all immediate EXP axes, while preserving
    standard coins and loot. False means old/duplicate/non-Fame kill.
    """
    # Transient per-kill result used only for the following text message.
    session._v115_fame_repeat_delivery = False
    identity = resolve_fame_objective(mob, template)
    if identity is None:
        return False
    region, boss_id = identity
    account = getattr(session, 'account_id', None)
    if not isinstance(account, int) or account < 1:
        raise ValueError('Authenticated Fame account required')
    # A Fame point is a one-time discovery; the combat EXP belongs to EVERY
    # real kill. Previously credited or pending objectives therefore receive
    # a separate, delayed EXP-only repeat entry. No extra Fame is minted.
    legacy = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='fame_bosses_v1702'").fetchone()
    already_credited = bool(legacy and conn.execute('''SELECT 1 FROM fame_bosses_v1702
            WHERE account_id=? AND region=? AND boss_id=?''',
            (account, region, boss_id)).fetchone())
    queue = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='v115_fame_delivery'").fetchone()
    already_pending = bool(queue and conn.execute('''SELECT 1 FROM v115_fame_delivery
            WHERE account_id=? AND region=? AND boss_id=?''',
            (account, region, boss_id)).fetchone())
    if already_credited or already_pending:
        plan = RewardSnapshot(
            character_xp=character_xp,soul_xp=soul_xp,
            class_xp=class_xp,stat_xp=stat_xp,
            class_levels=tuple(class_levels),class_max_level=class_max_level,
            overcap=overcap,character_name=getattr(getattr(session,'character',None),'name',None),
            verified_zero=True).validate()
        stage_repeat_exp(conn,account,region,boss_id,
            str(template.get('name') or boss_id),plan,now=now)
        session._v115_fame_repeat_delivery = True
        return True
    return stage_final_combat_reward(
        conn, session, mob, template,
        character_xp=character_xp, soul_xp=soul_xp,
        class_xp=class_xp, stat_xp=stat_xp,
        class_levels=class_levels, class_max_level=class_max_level,
        overcap=overcap, now=now)
