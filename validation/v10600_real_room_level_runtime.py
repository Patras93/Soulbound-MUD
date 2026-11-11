# -*- coding: utf-8 -*-
"""Test naprawy historycznego cap800 na poziomie POKOJU v106, nie postaci.

Odczytuje realny bootstrap serwera i World(). Nie potrzebuje bazy produkcyjnej.
"""
from __future__ import annotations
import os
import socket
from unittest.mock import patch


def run():
    assert os.getenv('SOULBOUND_V106_STAGING')=='1', 'tylko staging'
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    os.environ['SOULBOUND_HOST']='127.0.0.1'
    os.environ['SOULBOUND_PORT']=str(port)
    os.environ.pop('SOULBOUND_DB',None)
    import server
    from core.balance_math import runtime_room_level
    from world.dynamic_content import ROOMS,MOB_TEMPLATES
    from world.v10600_region_index import REGIONS
    from world.v10600_raids_26_35 import RAID_ROWS
    from systems.v106_combat_encounter_level import effective_encounter_level_v106
    from types import SimpleNamespace
    count=0
    world=server.World()
    checks=0
    def ck(value,msg):
        nonlocal checks
        assert value,msg
        checks+=1
    for slug,*_ in REGIONS:
        for i in range(1,25):
            room_id=f'v10600_{slug}_{i:02d}'
            room=ROOMS[room_id]
            stage=int(room.get('generator_level',0))
            ck(30001<=stage<=60000,'utracony poziom pokoju '+room_id)
            count+=1
    for no,*_ in RAID_ROWS:
        for s in (1,2,3):
            room_id=f'v10600_raid_{no}_stage_{s}'
            mob_id=f'v10600_raid_{no}_boss_{s}'
            room=ROOMS[room_id]
            mob=MOB_TEMPLATES[mob_id]
            ck(room['generator_level']==mob['generator_level'],
               'pokój i boss mają inne poziomy '+room_id)
            ck(30001<=room['generator_level']<=60000,
               'rajd poziom poza erą '+room_id)
            for soul in (1,int(room['generator_level'])):
                c=SimpleNamespace(character_level=800,soul_level=soul)
                actor=SimpleNamespace(template_id=mob_id,room_id=room_id)
                effective=effective_encounter_level_v106(c,actor,mob,room)
                ck(effective==int(room['generator_level']) if soul==room['generator_level']
                   else effective<int(room['generator_level']),
                   'Soul Level zły '+room_id)
            count+=1
    ck(count==750,'720 zwykłych pokoi i 30 sal rajdowych')
    # Stary świat i wyłączone v106 nadal używają historycznego cap=800.
    fake={'generator_level':34001,'recommended_mastery':34001,'zone':'test'}
    with patch.dict(os.environ,{'SOULBOUND_V106_STAGING':'0'}):
        ck(runtime_room_level('v10600_raid_test',fake)==800,
           'stary tryb ma zachować cap800')
    ck(runtime_room_level('v10500_test',{'generator_level':34001})==800,
       'v105 nie może zmienić limitu')
    ck(runtime_room_level('v10600_fake',{'generator_level':4})==4,
       'małe pokoje nie mogą otrzymać 30001')
    print(f'V106 POKOJE PRAWDZIWY BOOTSTRAP: {checks} PASS, {count} pokoi',flush=True)
    return checks
if __name__=='__main__':run()
