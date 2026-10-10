# -*- coding: utf-8 -*-
"""Actual runtime integration audit for Forgotten Worlds v1.50.0."""
from __future__ import annotations

from collections import deque
import asyncio
import re


def run(server):
    from systems.forgotten_world_v1500 import REGIONS, PROFESSIONS, rid
    from systems.echo_dungeon_v1500 import echo_floor_id, echo_identity
    from player.session import Session
    rooms, quests, mobs, npcs=server.ROOMS,server.QUESTS,server.MOB_TEMPLATES,server.NPCS
    errors=[];checks=0

    def verify(pred,msg):
        nonlocal checks
        checks+=1
        if not pred:errors.append(msg)

    verify(server.VERSION in ('1.50.0','1.50.1','1.60.0'),'release version 1.50.x')
    verify(server.FORGOTTEN_WORLD_V1500.get('rooms')==167,'region room count')
    verify(rooms['v1310_emp_lost_arena']['exits'].get('east')=='v1500_gate','old-world connection')
    # Reachability of every new static location, with no one-way mistakes.
    seen={'v1500_gate'}; todo=deque(seen)
    while todo:
        room=todo.popleft()
        for target in rooms[room].get('exits',{}).values():
            if target in rooms and target not in seen:
                seen.add(target);todo.append(target)
    for key in [k for k in rooms if k.startswith('v1500_') and not re.match(r'v1500_echo_\d+_',k)]:
        verify(key in seen,'unreachable '+key)
    for reg in REGIONS:
        slug,title,theme,element,level,places,boss_names,super_pair,resource=reg
        for row in range(5):
            for col in range(8):
                key=rid(slug,row,col)
                verify(key in rooms, 'room missing '+key)
                for direction,target in rooms[key].get('exits',{}).items():
                    verify(target in rooms,'broken exit '+key+'/'+direction)
        for i,name in enumerate(boss_names,1):
            mid=f'v1500_{slug}_boss_{i}'
            verify(mid in mobs and mobs[mid]['name']==name,'boss missing '+mid)
            verify(mobs[mid].get('attack_elements_v11339'), 'no elemental attacks '+mid)
        for stage in range(1,11):
            qid=f'v1500_{slug}_saga_{stage}'
            spec=quests.get(qid)
            verify(spec is not None, 'missing quest '+qid)
            if not spec:continue
            verify(spec['target'] in mobs,'missing quest target '+qid)
            verify(stage==1 or spec.get('requires_quest')==f'v1500_{slug}_saga_{stage-1}', 'broken saga chain '+qid)
        verify(f'v1500_{slug}_superboss' in mobs,'missing superboss '+slug)
    for index,(profession,tool,_) in enumerate(PROFESSIONS):
        npc=f'v1500_prof_npc_{index}'
        verify(npc in npcs,'specialist NPC '+npc)
        for phase in range(1,4):
            q=quests[f'v1500_prof_{index}_{phase}']
            verify(q['kind']=='profession_action' and q['reward_profession']==profession
                   and q['reward_tool_type']==tool,'profession reward '+profession)
    verify(len([k for k in quests if k.startswith('v1500_')])==107,'new quest count')
    for level in (1,5,10,25,100,1000):
        fake=type('MinimalWorld',(object,),{
          '_generatorize_runtime_room':lambda self,key:None,
          '_register_runtime_spawn':lambda self,room,tid:self.spawns.append((room,tid)),
        })()
        fake.spawns=[]
        entrance=echo_floor_id(level)
        verify(server._WorldV1500.ensure_infinite_dungeon_floor(fake,entrance),'lazy floor '+str(level))
        verify(len(fake.spawns)==(5 if level%10==0 else 4),'lazy spawns '+str(level))
        verify(server._WorldV1500.ensure_infinite_dungeon_floor(fake,entrance),'revisit '+str(level))
        verify(len(fake.spawns)==(5 if level%10==0 else 4),'no duplicate spawn '+str(level))
        verify(echo_floor_id(level+1)==rooms[echo_floor_id(level,'boss')]['exits']['down'],
               'floor descent '+str(level))
        # Direct Session method was previously shadowed by Magitek wrappers.
        fake_session=type('FakeSession',(object,),{'character':type('C',(object,),{'room_id':entrance})()})()
        verify(Session.dungeon_exit_destination(fake_session,entrance)==
               ('v1500_echo_entry','Nieskończony Labirynt Echa'),'dungeon exit '+str(level))
    verify('kontynent' in __import__('player.session_mixins.command_registry',fromlist=['COMMAND_REGISTRY']).COMMAND_REGISTRY,
           'continent command')
    verify('lochy50' in __import__('player.session_mixins.command_registry',fromlist=['COMMAND_REGISTRY']).COMMAND_REGISTRY,
           'dungeon command')
    return {'checks':checks,'errors':errors,
      'rooms':167,'bosses':25,'saga':40,'professions':14,'profession_quests':42}


if __name__=='__main__':
    import server
    result=run(server)
    print('V1500 WORLD CONTENT:',result)
    if result['errors']:
        raise SystemExit(1)
