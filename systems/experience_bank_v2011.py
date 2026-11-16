# -*- coding: utf-8 -*-
"""Alter-style persistent overflow applied to individual awards only."""

from systems.experience_cap_v2009 import experience_cap_v2009


def banked_experience_v2011(db, account_id, amount, kind, level, *,
                            source_key='', overcap=False):
    # Unified real-character cap; old per-axis cap remains only for old
    # isolated test databases without characters/progression schema.
    resolver = getattr(db, 'multi_cap_v23215', None)
    total_cap = resolver(account_id) if callable(resolver) else None
    from systems.v10800_seasonal_events import overcap_event_state
    # The scheduled v108 multiplier belongs to an active, authorized game
    # server, NOT offline historical fixtures or standalone database repairs.
    # Explicit boss overcap remains available to both real and test databases.
    effective_overcap = bool(overcap) or (
        getattr(db, '_v108_live_event_caps', False) is True
        and overcap_event_state()['active'])
    cap = (total_cap if total_cap is not None else experience_cap_v2009(kind, level)) * (2 if effective_overcap else 1)
    # Only real character rows have authoritative live level caps.  Minimal
    # historical EXP-bank fixtures have no characters table and must retain
    # their documented standalone-cap behavior.
    if kind in ('character', 'soul'):
        try:
            row = db.conn.execute('SELECT 1 FROM characters WHERE account_id=?',
                                  (account_id,)).fetchone()
        except Exception as exc:
            if 'no such table: characters' in str(exc).lower():
                row = None
            else:
                raise
        if row is not None:
            if kind == 'character':
                from core.progression_resources import character_xp_to_next
                if character_xp_to_next(level) <= 0:
                    cap = 0
            else:
                from core.progression_resources import soul_xp_to_next
                if soul_xp_to_next(level) <= 0:
                    cap = 0
    # v113.00.25 (live sessions only): old bank balances are held until
    # an explicit "expbank odbierz". Do not silently transfer fresh XP into
    # the bank, nor draw down past balances on subsequent kills.
    if getattr(db, '_manual_bank_only_v11325', False):
        from core.big_numbers_v10400 import number
        fresh = number(amount if amount is not None else 0)
        if getattr(db, '_v108_live_event_caps', False) is True and overcap_event_state()['active']:
            # Over Cap EVENT is unlimited; boss double-cap is a different rule.
            paid = fresh
        else:
            paid = min(fresh, cap)
        # v113.00.29: the old bank allocator is intentionally bypassed here.
        # Observe the actual payout only; never create EXP_BANK on fresh XP.
        from systems.sound_events_v1208 import record_paid_exp_event_v11329
        record_paid_exp_event_v11329(db, account_id, paid, cap, kind=kind)
        return paid
    allocator = getattr(db, 'allocate_experience_bank_v2011', None)
    if allocator is None:
        raise RuntimeError('EXP Bank v2.00.11: SQLite schema not initialized')
    return allocator(account_id, amount, kind, source_key, cap)
