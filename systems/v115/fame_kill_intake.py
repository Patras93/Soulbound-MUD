# -*- coding: utf-8 -*-
"""v115 Fame first-kill intake using the game's canonical identity.

This function stages a reward, never grants Fame/EXP or sends sound events.
It is intentionally not installed into combat until the payout scheduler,
per-character serialization and multi-cap payout have LIVE verification.
"""
from __future__ import annotations
from systems import fame_v1702
from systems.v115.fame_legacy_bridge import queue_first_clear


def stage_real_fame_kill(conn, recipients, mob, template, *, now=None):
    """Return (session, region, boss_id) for newly queued eligible recipients.

    Caller must use actual recipients co-located at the kill. This routine
    preserves canonical Fame eligibility, including rejecting summons, common
    enemies and duplicates in the old Fame ledger or the v115 queue.
    """
    if not fame_v1702._is_fame_target(template):
        return []
    if not fame_v1702._eligible_natural_fame_enemy(template):
        return []
    if fame_v1702._is_runtime_summoned_mob(mob):
        return []
    identity = fame_v1702._fame_target_identity(mob, fame_v1702.fame_catalog(), template)
    if identity is None:
        return []
    region,boss_id=identity
    boss_name=str(template.get('name') or boss_id)
    # Legacy Fame computes actual Multi Cap at payout. Do not confuse the
    # old 'reward_xp' estimate with a real per-axis Multi Cap payout.
    # The provisional scalar is zero until the EXP controller can calculate
    # all axes through canonical cap helpers at the actual payout time.
    staged=[]
    for session in recipients:
        account_id=getattr(session,'account_id',None)
        if type(account_id) is not int or account_id < 1:
            raise ValueError('Invalid Fame recipient account')
        if queue_first_clear(conn,account_id,region,boss_id,boss_name,0,now=now):
            staged.append((session,region,boss_id))
    return staged
