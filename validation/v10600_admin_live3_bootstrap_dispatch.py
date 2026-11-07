# -*- coding: utf-8 -*-
"""Actual v106 bootstrap + existing admin-live-era session entry, read-only."""
import asyncio,os,sys
from types import SimpleNamespace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
if os.environ.get('SOULBOUND_V106_STAGING')!='1':
    raise RuntimeError('Ten test wymaga SOULBOUND_V106_STAGING=1 na ODDZIELNEJ kopii.')
import world.dynamic_content as d
from systems.admin_live_era_v10300 import handle

class Session:
    def __init__(self,admin):
        self.admin=admin;self.messages=[]
        self.server=SimpleNamespace(db=SimpleNamespace(conn=None))
    def is_admin(self):return self.admin
    async def send(self,message):self.messages.append(message)

async def test():
    count=0
    def ck(cond,msg):
        nonlocal count
        assert cond,msg;count+=1
    ck(bool(d.V10600_STAGING_BUILD),'real canonical bootstrap staged')
    s=Session(True)
    for command, fragment in (
        ('v106 regiony 6','6/6'), ('v106 soul 6000','soul_tier_6000_trial'),
        ('v106 rajd 35','Trzy etapy'), ('v106 audyt','krain 30'),
        ('v106 podglad mob v10600_raid_26_boss_1 max_hp','v10600_raid_26_boss_1'),
    ):
        ck(await handle(s,command) is True,'command claimed by existing era handler')
        ck(fragment in s.messages[-1],command+': '+s.messages[-1])
    deny=Session(False)
    ck(await handle(deny,'v106 regiony') is True,'nonadmin request owned by handler')
    ck('Nieznana komenda' in deny.messages[-1],'admin check works')
    return count

if __name__=='__main__':
    print('V106 ADMIN LIVE REAL WORLD DISPATCH:',asyncio.run(test()),'PASS',flush=True)
