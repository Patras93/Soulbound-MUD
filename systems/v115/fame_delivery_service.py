# -*- coding: utf-8 -*-
"""v115: bounded, reconnect-safe Fame delivery controller (NOT combat hook).

Only call from a serialized, authenticated player session with the canonical
Multi Cap calculation. EXP and Fame cannot be emitted as text/sound until DB
commit has completed. This service never requires a soundpack.
"""
from __future__ import annotations
from dataclasses import dataclass
from systems.v115 import fame_queue, fame_exp_progression, fame_legacy_bridge


@dataclass(frozen=True)
class AwardPlan:
    character_xp: int
    soul_xp: int
    class_xp: int
    stat_xp: int
    class_levels: tuple = ()
    class_max_level: int | None = None
    overcap: bool = False

    def validate(self):
        axes = (self.character_xp, self.soul_xp, self.class_xp, self.stat_xp)
        if any(type(amount) is not int or amount < 0 for amount in axes):
            raise ValueError('Invalid Multi Cap reward axis')
        if not any(axes):
            raise ValueError('Missing actual Multi Cap reward: refuse zero EXP')
        if self.class_xp and not self.class_levels:
            raise ValueError('Missing current active classes for class EXP')
        if type(self.overcap) is not bool:
            raise ValueError('Invalid overcap state')
        return self


def deliver_due_for_online_player(db, character, account_id, calculate_plan, *, now=None, limit=20):
    """Drain due phases with caller-controlled per-character serialization.

    calculate_plan(region,boss_id,boss_name) MUST recompute all canonical
    progression rewards for the authenticated character at actual payout time,
    returning AwardPlan, WITHOUT issuing game writes/network/sound events.
    This function deliberately does not start a task or fabricate a plan.

    Returned event tuples may only be announced AFTER caller confirms outer
    transaction commit. If an EXP payout fails, Fame remains pending.
    """
    if db is None or character is None or type(account_id) is not int or account_id < 1:
        raise ValueError('Invalid authenticated payout context')
    if getattr(character, 'account_id', None) != account_id:
        raise ValueError('Recipient does not own current character')
    if not callable(calculate_plan):
        raise TypeError('Canonical Multi Cap calculator required')
    if not callable(getattr(db.conn, 'deferred_commits', None)):
        raise TypeError('Deferred commit SQLite connection required')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('Invalid batch limit')
    events=[]
    rows=fame_queue.due_events(db.conn,account_id,now=now,limit=limit)
    for region,boss_id,boss_name,status,_scalar,_points in rows:
        if status in ('WAITING','EXP_READY'):
            plan=calculate_plan(region,boss_id,boss_name)
            if not isinstance(plan,AwardPlan):
                raise TypeError('Canonical Multi Cap calculator must return AwardPlan')
            plan.validate()  # Fail closed for staged records with missing EXP.
            result=fame_exp_progression.settle_fame_exp_progression(
                db,character,account_id,region,boss_id,
                character_xp=plan.character_xp,soul_xp=plan.soul_xp,
                class_xp=plan.class_xp,stat_xp=plan.stat_xp,
                class_levels=plan.class_levels,class_max_level=plan.class_max_level,
                overcap=plan.overcap,now=now)
            if result is not None:
                events.append(('exp',region,boss_id,boss_name,result))
        elif status=='FAME_READY':
            with db.conn.deferred_commits():
                granted=fame_legacy_bridge.settle_legacy_fame(
                    db.conn,account_id,region,boss_id,now=now)
            if granted:
                events.append(('fame',region,boss_id,boss_name,1))
    return events
