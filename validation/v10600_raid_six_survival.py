# -*- coding: utf-8 -*-
"""v106: 1–6 realnych graczy, cap AoE tylko staging i wlasciwy Soul Level."""
from __future__ import annotations
import os
from types import SimpleNamespace
from unittest.mock import patch
from world.dynamic_content import MOB_TEMPLATES,ROOMS
from systems.v106_raid_six_survival import cap_raid_incoming_v106

def run():
    check=0
    for raid in (26,35):
        for phase in (1,2,3):
            tid=f'v10600_raid_{raid}_boss_{phase}'
            rid=f'v10600_raid_{raid}_stage_{phase}'
            t=MOB_TEMPLATES[tid]
            stage=t['v106_authored_boss_stage']
            for members in range(1,7):
                mob=SimpleNamespace(template_id=tid,room_id=rid,adaptive_party_size_v11330=members)
                char=SimpleNamespace(soul_level=stage)
                hero=SimpleNamespace(character=char,max_hp=lambda: 5_000_000)
                with patch.dict(os.environ, {'SOULBOUND_V106_STAGING':'1'}):
                    assert cap_raid_incoming_v106(hero,mob,t,10_000_000)==150_000
                    assert cap_raid_incoming_v106(hero,mob,t,100)==100
                    char.soul_level=stage//2
                    assert cap_raid_incoming_v106(hero,mob,t,10_000_000)==10_000_000
                    char.soul_level=stage
                with patch.dict(os.environ, {'SOULBOUND_V106_STAGING':'0'}):
                    assert cap_raid_incoming_v106(hero,mob,t,10_000_000)==10_000_000
                check+=4
            with patch.dict(os.environ, {'SOULBOUND_V106_STAGING':'1'}):
                mob.adaptive_party_size_v11330=7
                assert cap_raid_incoming_v106(hero,mob,t,10_000_000)==10_000_000
                wrong=SimpleNamespace(template_id=tid,room_id='v10600_niepasujaca_sala',adaptive_party_size_v11330=6)
                assert cap_raid_incoming_v106(hero,wrong,t,10_000_000)==10_000_000
                check+=2
    print(f'V106 SIX SURVIVAL: {check} PASS; staging only')

if __name__=='__main__':run()
