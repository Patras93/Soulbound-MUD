# -*- coding: utf-8 -*-
"""Reject untracked housing/bank transfers before a physical-EQ ledger can drift."""
from __future__ import annotations
import os
from pathlib import Path
from types import SimpleNamespace
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from storage.db_inventory import DatabaseInventoryMixin


def run():
    checks=0
    def ck(ok,message):
        nonlocal checks
        assert ok,message
        checks+=1
    fake=SimpleNamespace(
        master_account_for_character=lambda aid:aid,
        master_account_by_name=lambda name:{'id':2},
        _v106_shadow_slots_disposable_copy=True,
        _v106_shadow_item_catalog={'helm':{'type':'armor'}},
    )
    previous=os.environ.get('SOULBOUND_V106_STAGING')
    try:
        os.environ['SOULBOUND_V106_STAGING']='1'
        result=DatabaseInventoryMixin.transfer_bank_v1225(
            fake,1,'other',item_id='helm',quantity=1)
        ck(result=='invalid','raw bank transfer of tracked gear was not rejected')
        ck(not hasattr(fake,'conn'),'rejected raw bank path tried to access SQLite')
        os.environ.pop('SOULBOUND_V106_STAGING',None)
        try:
            DatabaseInventoryMixin.transfer_bank_v1225(
                fake,1,'other',item_id='helm',quantity=1)
        except PermissionError:
            ck(True,'unapproved staging must fail closed')
        else:
            raise AssertionError('test marker bypassed via legacy bank transfer')
    finally:
        if previous is not None:
            os.environ['SOULBOUND_V106_STAGING']=previous
        else:
            os.environ.pop('SOULBOUND_V106_STAGING',None)
    source=(ROOT/'player/session_mixins/social_expansion.py').read_text(encoding='utf-8-sig')
    store=source.index("iid,name,have=candidates[0]")
    guard1=source.index('if _sb106_phys(self.server.db, iid):',store)
    write1=source.index('box[iid] = int(box.get(iid, 0)) + qty',store)
    ck(store<guard1<write1,'house deposit protection is after the SQL mutation')
    take=source.index('iid, have = found',write1)
    guard2=source.index('if _sb106_phys(self.server.db, iid):',take)
    write2=source.index('self.server.db.add_item(self.account_id, iid, qty, commit=False)',take)
    ck(take<guard2<write2,'house withdraw protection is after minting equipment')
    return checks

if __name__=='__main__':
    print('V107 OCHRONA TRAS EQ:',run(),'PASS',flush=True)
