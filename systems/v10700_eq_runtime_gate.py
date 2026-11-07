# -*- coding: utf-8 -*-
"""Production-proof v107 EQ gate; preserves v106 staging tests unchanged."""
from __future__ import annotations
import os


def is_enabled(db):
    live=bool(getattr(db,'_v107_eq_live_active',False))
    staging=bool(getattr(db,'_v106_shadow_slots_disposable_copy',False))
    if live:
        from systems.v10700_activation import production_approved
        if not production_approved():
            raise PermissionError('EQ v107: utracono autoryzację zatwierdzonej instalacji')
        if not staging or not isinstance(getattr(db,'_v106_shadow_item_catalog',None),dict):
            raise RuntimeError('EQ v107: aktywny serwer nie ma zainicjowanego rejestru')
        return True
    if staging:
        if os.environ.get('SOULBOUND_V106_STAGING')!='1':
            raise PermissionError('EQ v106: test fizycznych kopii wyłącznie w stagingu')
        if not isinstance(getattr(db,'_v106_shadow_item_catalog',None),dict):
            raise RuntimeError('EQ v106: brak katalogu kopii testowej')
        return True
    return False
