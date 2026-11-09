"""Zasady daty i zgody na automatyczne prezenty."""
from __future__ import annotations
import datetime as dt
import os

def enabled():
    """Only an explicit private trial or an installed v109 attestation."""
    from core.bootstrap_economy_professions import VERSION
    if VERSION not in ('109.00.0','110.00.0'):
        return False
    if (os.environ.get('SOULBOUND_V109_STAGING') == '1'
            and os.environ.get('SOULBOUND_V107_STAGING') == '1'):
        return True
    if VERSION == '110.00.0':
        from systems.v11000_activation import production_approved
    else:
        from systems.v10900_activation import production_approved
    return production_approved()

def gift_kind(day):
    if not isinstance(day, dt.date) or isinstance(day, dt.datetime):
        raise TypeError('gift_kind: expected date')
    return 'advent' if day.month == 12 else 'daily'
