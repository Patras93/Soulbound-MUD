# -*- coding: utf-8 -*-
"""Runtime world integrity assertions for v11 expeditions."""

def run_regression():
    from server import ROOMS, NPCS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS
    from systems.eternal_glory_world_v1100 import REGIONS, ROOM_IDS, LANDMARK_IDS, QUEST_IDS
    from systems.exploration_point_values_v2322 import room_explorer_points_v2322, is_city_ep_excluded_v1002
    assert len(REGIONS)==12 and len(ROOM_IDS)==144 and len(LANDMARK_IDS)==36
    assert len(QUEST_IDS)==24
    from world.legends_v3200 import _reachable
    assert ROOM_IDS <= _reachable(ROOMS), 'new expeditions must be reachable'
    assert QUEST_IDS <= set(QUESTS), 'missing quests'
    checks=6
    for rid in ROOM_IDS:
        room=ROOMS[rid]
        assert not is_city_ep_excluded_v1002(room), rid
        assert room['v1000_landmark']==(rid in LANDMARK_IDS)
        assert len(room['exits'])>0
        assert room['exploration_ep']==(5 if rid in LANDMARK_IDS else 0)
        if rid in LANDMARK_IDS:
            assert room_explorer_points_v2322(room)==5
        checks+=5
    for key,zone,level,element,guide,elite,boss,places in REGIONS:
        p=f'v1100_eg_{key}'
        assert NPCS[f'{p}_guide']['room']==f'{p}_00'
        assert MOB_TEMPLATES[f'{p}_boss']['boss']
        assert MOB_TEMPLATES[f'{p}_elite']['rank']=='elite'
        assert QUESTS[f'{p}_quest_2']['requires_quest']==f'{p}_quest_1'
        assert QUESTS[f'{p}_quest_1']['target']==f'{p}_elite'
        assert QUESTS[f'{p}_quest_2']['target']==f'{p}_boss'
        assert sum(1 for npc in NPCS.values() if npc.get('room')==f'{p}_00')==1
        assert f'{p}_relic' in ITEMS
        assert sum(1 for room, mob in MOB_SPAWNS if mob == f'{p}_boss')==1
        checks+=9
    for rid in LANDMARK_IDS:
        assert room_explorer_points_v2322(ROOMS[rid])==5
        checks+=1
    return checks
if __name__=='__main__':
    print('v11 EXPEDITIONS',run_regression(),'PASS')
