# -*- coding: utf-8 -*-
"""Atomically prepare a Fame first-clear from FINAL combat reward numbers.

This does not install a combat hook: combat must suppress its legacy Fame
and immediate EXP paths when this function stages a first-clear. Keeping
this contract separate avoids accidentally paying both paths during rollout.
"""
from __future__ import annotations
from systems import fame_v1702
from systems.v115.fame_reward_snapshot import RewardSnapshot
from systems.v115.fame_snapshot_delivery import stage_first_clear


def resolve_fame_objective(mob, template):
    """Reuse the full legacy Fame eligibility and objective identity."""
    if not isinstance(template, dict) or not fame_v1702._is_fame_target(template):
        return None
    if not fame_v1702._eligible_natural_fame_enemy(template):
        return None
    if fame_v1702._is_runtime_summoned_mob(mob):
        return None
    return fame_v1702._fame_target_identity(mob, fame_v1702.fame_catalog(), template)


def stage_final_combat_reward(conn, session, mob, template, *,
                              character_xp, soul_xp, class_xp, stat_xp,
                              class_levels, class_max_level, overcap, now=None):
    """Save real per-axis payout only for an eligible first Fame clear.

    Must be called inside the combat kill coordinator's transaction after
    multiplier/cap calculations and BEFORE any progression payout. Caller
    owns commit. Return True only when a new reward was staged; False for
    non-Fame and previously credited Fame. Do not alter ordinary loot/coins.
    """
    identity = resolve_fame_objective(mob, template)
    if identity is None:
        return False
    if not isinstance(getattr(session, 'account_id', None), int) or session.account_id < 1:
        raise ValueError('Authenticated Fame recipient required')
    if getattr(getattr(session,'character',None),'account_id',None) != session.account_id:
        raise ValueError('Fame character/account mismatch')
    plan=RewardSnapshot(character_xp=character_xp,soul_xp=soul_xp,
                        class_xp=class_xp,stat_xp=stat_xp,
                        class_levels=tuple(class_levels),class_max_level=class_max_level,
                        overcap=overcap,
                        character_name=getattr(session.character, 'name', None),
                        verified_zero=True).validate()
    region,boss_id=identity
    return stage_first_clear(conn, session.account_id, region, boss_id,
                             str(template.get('name') or boss_id),plan,now=now)
