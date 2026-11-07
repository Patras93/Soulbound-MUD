# -*- coding: utf-8 -*-
"""v106 source-stage compatibility check against the actual v105 catalog.

Runs in memory ONLY; does not open, edit or migrate an account database.
"""
from __future__ import annotations
from pathlib import Path
import sys
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from world import dynamic_content as historic
from core.mines_threat import EXP_AREA_TARGET_POWER
from world.v10600_krainy_30001_60000 import install as regions_install
from world.v10600_raids_26_35 import install as raids_install
from world.v10600_soul_trials import register as trials_register
from world.v10600_calendar_contracts import install as contracts_install


def run():
    before=(len(historic.ROOMS),len(historic.MOB_TEMPLATES),
            len(historic.QUESTS),len(historic.NPCS))
    original_exit=deepcopy(historic.ROOMS['v10500_przelom_14']['exits'])
    # Same registries, but shallow stage dictionaries: the new installer only
    # ADDS entries, and changes the one historical exit which is deep-copied.
    # Deepcopying all existing 15k monster templates caused slow interpreter
    # shutdown on Windows/Linux and added no new coverage.
    rooms=dict(historic.ROOMS)
    rooms['v10500_przelom_14']=deepcopy(historic.ROOMS['v10500_przelom_14'])
    state=(rooms,dict(historic.MOB_TEMPLATES),
           list(historic.MOB_SPAWNS),dict(historic.NPCS),dict(historic.QUESTS),
           dict(historic.ITEMS),dict(historic.CRAFT_RECIPES),
           list(historic.EXP_AREAS),dict(historic.EXP_ZONE_AREA_ID),
           dict(historic.EXP_AREA_BASE_CATEGORY),
           dict(historic.GUIDE_DESTINATION_ALIASES),dict(EXP_AREA_TARGET_POWER))
    first=regions_install(*state)
    second=raids_install(*state[:7])
    third=trials_register(state[4],state[1])
    fourth=contracts_install(state[4],state[3],state[1],state[5])
    assert (first['regions'],first['quests'],second['raids'],third,fourth['contracts'])==(30,1800,10,300,60)
    assert len(state[0])==before[0]+750
    assert len(state[1])==before[1]+390
    assert len(state[4])==before[2]+2190
    assert len(state[3])==before[3]+120
    assert historic.ROOMS['v10500_przelom_14']['exits']==original_exit
    assert (len(historic.ROOMS),len(historic.MOB_TEMPLATES),
            len(historic.QUESTS),len(historic.NPCS))==before
    return {'historic_unchanged':True,'new_regions':30,'new_quests':2190,
            'new_rooms_with_raids':750,'new_mobs_with_raids':390}

if __name__=='__main__':print('V106 VS V105 REAL WORLD: '+str(run())+' PASS',flush=True)
