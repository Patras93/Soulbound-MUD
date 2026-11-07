# -*- coding: utf-8 -*-
"""All 30 raid stages: actual traversable return path to the quest giver.

Static world registry under explicit staging; no DB, login or teleport.
The same move sequence is exercised by the genuine TCP end-to-end test.
"""
from __future__ import annotations
import os


def run():
    assert os.environ.get('SOULBOUND_V106_STAGING')=='1', 'Tylko staging v106.'
    from world.dynamic_content import ROOMS,QUESTS,NPCS
    from world.v10600_raids_26_35 import RAID_ROWS
    checks=0
    for no,*_ in RAID_ROWS:
        for stage in range(1,4):
            q=QUESTS[f'v10600_raid_{no}_quest_{stage}']
            npcs=[v for v in NPCS.values() if v.get('name')==q['giver']]
            assert len(npcs)==1, (no,stage,'wielu lub zero NPC')
            location=f'v10600_raid_{no}_stage_{stage}'
            path=('south',)*(stage-1)+('west','west','west','south')
            for direction in path:
                exit_to=ROOMS[location].get('exits',{}).get(direction)
                assert exit_to and exit_to in ROOMS,(no,stage,location,direction)
                location=exit_to
            assert location==npcs[0]['room'],(no,stage,location,npcs[0]['room'])
            assert f'v10600_raid_{no}_quest_{stage}' in npcs[0]['specialist_quests']
            checks+=1
    print(f'V106 RAJDY 26-35: {checks} tras zwykłych ruchów od bossa do NPC PASS.',flush=True)
    return checks

if __name__=='__main__':
    # Preserve an already running one-click auditor which launches this
    # read-only module as a separate child without the staging flag.
    # Never permit it inside the production tree or with any local DB.
    from validation.v10600_one_package_gate import guard_root
    guard_root()
    os.environ['SOULBOUND_V106_STAGING']='1'
    run()
