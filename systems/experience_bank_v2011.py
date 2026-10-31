# -*- coding: utf-8 -*-
"""Alter-style persistent overflow applied to individual awards only."""

from systems.experience_cap_v2009 import experience_cap_v2009


def banked_experience_v2011(db, account_id, amount, kind, level, *,
                            source_key='', overcap=False):
    # Unified real-character cap; old per-axis cap remains only for old
    # isolated test databases without characters/progression schema.
    resolver = getattr(db, 'multi_cap_v23215', None)
    total_cap = resolver(account_id) if callable(resolver) else None
    cap = (total_cap if total_cap is not None else experience_cap_v2009(kind, level)) * (2 if overcap else 1)
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
    allocator = getattr(db, 'allocate_experience_bank_v2011', None)
    if allocator is None:
        raise RuntimeError('EXP Bank v2.00.11: SQLite schema not initialized')
    return allocator(account_id, amount, kind, source_key, cap)
