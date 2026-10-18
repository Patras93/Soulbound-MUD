# -*- coding: utf-8 -*-
"""v10 authored regions and nonduplicating cartography progress, read-only audits."""
from pathlib import Path
from tempfile import TemporaryDirectory


def run_regression(runtime=None):
    if runtime is None:
        import server as runtime
    from systems.forgotten_horizons_v1000 import (
        REGIONS, ROOMS_PER_REGION, LANDMARK_IDS, NEW_ROOM_IDS, QUEST_IDS,
        REVERSE, documented_landmarks)
    from systems.exploration_point_values_v2322 import (
        room_explorer_points_v2322, zone_explorer_points_v2322)
    from systems.milestone_cap_rewards_v2103 import (
        explorer_award_per_point_v4211, _fame_award_for_level_v4211)
    from world.dynamic_content import EXPLORATION_ZONE_ROOMS
    from storage.database import Database
    checks=0
    def ck(condition,label):
        nonlocal checks
        if not condition:
            raise AssertionError('v10: '+label)
        checks+=1
    ck(runtime.VERSION in ('10.00.1','10.00.2','11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12','11.00.13','11.00.14','11.00.15','11.00.16','11.00.17',),'release identity')
    ck(len(REGIONS)==6 and len(NEW_ROOM_IDS)==72 and len(LANDMARK_IDS)==18,'authored region IDs')
    ck(len(QUEST_IDS)==12,'12 additional quest IDs')
    ck(NEW_ROOM_IDS <= set(runtime.ROOMS),'all new rooms installed')
    from world.legends_v3200 import _reachable
    ck(NEW_ROOM_IDS <= _reachable(runtime.ROOMS),'all 72 new rooms reachable from main world square')
    ck(QUEST_IDS <= set(runtime.QUESTS),'all new quests installed')
    ck(len(runtime.CLASS_SKILLS)==22 and len(runtime.CLASSES)==22 and len(runtime.RACES)==22,'22 unchanged classes and races')
    ck(len(runtime.TOOL_PROFESSION_MAP)>=14,'no old profession tools removed')
    names=set()
    for region,zone,level,element,guide,elite,boss,landmarks in REGIONS:
        ck(zone not in names,'unique region '+zone)
        names.add(zone)
        ridset={f'v1000_horizon_{region}_{i:02d}' for i in range(ROOMS_PER_REGION)}
        ck(set(EXPLORATION_ZONE_ROOMS.get(zone,()))>=ridset,'all region rooms in EP map '+zone)
        visited=set()
        for idx in range(ROOMS_PER_REGION):
            rid=f'v1000_horizon_{region}_{idx:02d}'
            room=runtime.ROOMS[rid]
            ck(room['zone']==zone,'zone identity '+rid)
            ck(room_explorer_points_v2322(room)>=2,'authored EP '+rid)
            for way,dest in room['exits'].items():
                ck(runtime.ROOMS[dest]['exits'].get(REVERSE[way])==rid,'reciprocal exit '+rid)
            if room['v1000_landmark']:
                ck(rid in LANDMARK_IDS,'landmark count '+rid)
        earned,possible=zone_explorer_points_v2322(sorted(ridset),visited,{},runtime.ROOMS)
        ck(earned==0 and possible>0,'real regional EP pool '+zone)
        q1,q2=(f'v1000_{region}_quest_{i}' for i in (1,2))
        ck(runtime.QUESTS[q1]['kind']=='kill' and runtime.QUESTS[q2]['requires_quest']==q1,'real sequential quests '+zone)
        npc=runtime.NPCS[f'v1000_{region}_guide']
        ck(npc['room']==f'v1000_horizon_{region}_00','private regional guide '+zone)
        ck(runtime.MOB_TEMPLATES[f'v1000_{region}_boss']['boss'],'boss final '+zone)
        resource=f'v1000_{region}_material'
        ck(runtime.ITEMS.get(resource,{}).get('v1000_horizon_resource') is True,'unique material '+zone)
        ck(resource in runtime.MOB_TEMPLATES[f'v1000_{region}_elite']['drops'],'mob drops regional material '+zone)
        ck(resource in runtime.MOB_TEMPLATES[f'v1000_{region}_boss']['drops'],'boss drops regional material '+zone)
    for stage in (1,25,100,250,500,800):
        ck(explorer_award_per_point_v4211(stage)['character']==120+min(100,(stage-1)//8),'no EP XP inflation')
        ck(_fame_award_for_level_v4211(stage)==2500+30*stage*stage,'legacy Fame curve retained for old tests')
    with TemporaryDirectory(prefix='soulbound_v1000_') as directory:
        db=Database(str(Path(directory)/'cartographer.sqlite3'))
        a=db.create_account('KartografHoryzontow10','StrongPasswordForKartographerV10!')
        b=db.create_account('InnyKartograf10','StrongPasswordForKartographerV10!')
        point=sorted(LANDMARK_IDS)[0]
        ck(not documented_landmarks(db.conn,a,db.collection_entry_ids),'no phantom mapped landmark')
        ck(db.add_collection_entry(a,'cartography_v1100',point),'first legitimate mapping')
        ck(not db.add_collection_entry(a,'cartography_v1100',point),'one-time mapping')
        ck(point in documented_landmarks(db.conn,a,db.collection_entry_ids),'durable mapped landmark')
        ck(point not in documented_landmarks(db.conn,b,db.collection_entry_ids),'different account isolated')
        db.conn.close()
        other=Database(str(Path(directory)/'cartographer.sqlite3'))
        ck(point in documented_landmarks(other.conn,a,other.collection_entry_ids),'mapping survives SQLite reopen')
        other.conn.close()
    return checks

if __name__=='__main__':
    print('HORYZONTY 10.0:',run_regression(),'checks PASS')
