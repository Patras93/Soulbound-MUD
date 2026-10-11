# -*- coding: utf-8 -*-
"""Alter-style persistent overflow applied to individual awards only."""

from systems.experience_cap_v2009 import experience_cap_v2009


def banked_experience_v2011(db, account_id, amount, kind, level, *,
                            source_key='', overcap=False):
    cap = experience_cap_v2009(kind, level) * (2 if overcap else 1)
    allocator = getattr(db, 'allocate_experience_bank_v2011', None)
    if allocator is None:
        raise RuntimeError('EXP Bank v2.00.11: SQLite schema not initialized')
    return allocator(account_id, amount, kind, source_key, cap)
