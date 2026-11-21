# -*- coding: utf-8 -*-
"""Queue only first-clear Fame bonus; combat always awards ordinary kill EXP now."""
from __future__ import annotations
from systems.v115.fame_combat_capture import resolve_fame_objective
from systems.v115.fame_reward_snapshot import RewardSnapshot
from systems.v115.fame_snapshot_delivery import stage_first_clear


def stage_delayed_first_clear(conn, session, mob, template, *,
                              character_xp, soul_xp, class_xp, stat_xp,
                              class_levels, class_max_level, overcap, now=None):
    """Stage only the first Fame milestone, never the ordinary kill EXP.

    Every actual kill earns its normal Character/Soul/Class/Stat EXP immediately,
    including the first clear and all repeat kills. A first clear schedules only
    the separate one-time Multi Cap Fame bonus and Fame point. Historical
    pending v115 payouts (from before this fix) remain deliverable unchanged.
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
    # Only the Fame milestone is deferred. Ordinary EXP is paid by the
    # normal combat transaction on EVERY kill, including repeats. Do not
    # create new delayed-repeat rows; earlier queued rows remain payable.
    legacy = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='fame_bosses_v1702'").fetchone()
    already_credited = bool(legacy and conn.execute('''SELECT 1 FROM fame_bosses_v1702
            WHERE account_id=? AND region=? AND boss_id=?''',
            (account, region, boss_id)).fetchone())
    if already_credited:
        session._v115_fame_repeat_delivery = True
        return True
    queue = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='v115_fame_delivery'").fetchone()
    already_pending = bool(queue and conn.execute('''SELECT 1 FROM v115_fame_delivery
            WHERE account_id=? AND region=? AND boss_id=?''',
            (account, region, boss_id)).fetchone())
    if already_pending:
        session._v115_fame_repeat_delivery = True
        return True
    # Resolve the Fame objective only once per kill. No second catalog walk.
    # Zero is a verified marker: NORMAL EXP is awarded by combat; the later
    # settlement still generates the independent first-clear Multi Cap bonus.
    plan = RewardSnapshot(
        character_xp=0, soul_xp=0, class_xp=0, stat_xp=0,
        class_levels=tuple(class_levels),class_max_level=class_max_level,
        overcap=overcap,
        character_name=getattr(getattr(session, 'character', None), 'name', None),
        verified_zero=True).validate()
    return stage_first_clear(conn, account, region, boss_id,
                             str(template.get('name') or boss_id),plan,now=now)
