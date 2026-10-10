# -*- coding: utf-8 -*-
"""Read-only v1.60 gameplay topology, loot, quests and command regression."""
from collections import deque
from systems.era_legends_v1600 import UNDERGROUND, FRONTS, HUNTS, INVASIONS, active_invasion_v1600, INVASION_SECONDS
from systems import ocean4_v1350
from player.session_mixins.guide_navigation import SessionGuideNavigationMixin
from player.session_mixins.command_registry import COMMAND_REGISTRY, resolve_session_command


def run_era_legends_v1600(server):
    rooms,mobs,quests,npcs=server.ROOMS,server.MOB_TEMPLATES,server.QUESTS,server.NPCS
    checks=0;errors=[]
    def check(value,message):
        nonlocal checks
        checks+=1
        if not value:errors.append(message)
    def connected(start):
        done={start};queue=deque([start])
        while queue:
            for nxt in rooms[queue.popleft()].get('exits',{}).values():
                if nxt in rooms and nxt not in done:
                    done.add(nxt);queue.append(nxt)
        return done
    start=connected('temple')
    for rid in ('v1300_lost_border','v1300_orc_border','v1300_orc_throne','v1500_gate'):
        check(rid in start,'missing connection from temple to '+rid)
    check(tuple(int(n) for n in server.VERSION.split('.')[:3]) >= (1,60,0),'release version 1.60+')
    nav=SessionGuideNavigationMixin()
    for alias in ('orki','orkowie','gor khaz','kraina orkow'):
        check(nav.find_room_matches(alias)==['v1300_orc_border'],'orc alias '+alias)
    p=nav.shortest_path('temple','v1300_orc_border')
    check(p is not None and len(p)<=20,'actual walk to orcs missing')
    for rid,room in rooms.items():
        if not rid.startswith('v1600_'):continue
        check(rid in start,'unreachable from temple: '+rid)
        for direction,target in room.get('exits',{}).items():
            check(target in rooms,'dangling exit '+rid+'/'+direction)
            if target not in rooms:continue
            opp={'north':'south','south':'north','east':'west','west':'east',
                 'up':'down','down':'up','northeast':'southwest','southwest':'northeast'}.get(direction)
            if opp:check(rooms[target]['exits'].get(opp)==rid,'one way '+rid+'/'+direction)
    for realm,*_ in UNDERGROUND:
        for i in range(24):check(f'v1600_{realm}_{i}' in rooms,'underground '+realm+' '+str(i))
        for j in range(1,7):
            tid=f'v1600_{realm}_patrol_{j}'
            check(tid in mobs and any(mid==tid for _,mid in server.MOB_SPAWNS),'live patrol '+tid)
        for x in ('guard','monarch'):
            tid=f'v1600_{realm}_{x}'
            check(tid in mobs and any(mid==tid for _,mid in server.MOB_SPAWNS),'boss '+tid)
        for i in (1,2):
            quest=quests.get(f'v1600_{realm}_quest_{i}',{})
            check(quest.get('target') in mobs,'quest target '+realm+'/'+str(i))
    for slug,_,room,target,quest_id in FRONTS:
        check(room in rooms and target in mobs and quest_id in quests,'front '+slug)
        check(npcs.get('v1600_war_npc_'+slug,{}).get('room')==room,'front NPC '+slug)
    for slug,target,_ in HUNTS:
        check(target in mobs and f'v1600_hunt_{slug}' in quests,'hunt '+slug)
    for k in ('glebiny','meduzy','cesarz'):
        check(k in ocean4_v1350.ENEMIES and k in ocean4_v1350.MATERIALS,'naval battle '+k)
    for slot in range(8):
        event=active_invasion_v1600(now=INVASION_SECONDS*slot+1)
        check(event['room_id'] in rooms and event['template_id'] in mobs,'invasion '+str(slot))
    check(len(INVASIONS)==4,'invasions 4')
    check(resolve_session_command('era60')=='era60','era60 dispatch')
    check('era60' in COMMAND_REGISTRY,'era60 registry')
    return {'checks':checks,'errors':errors,'error_count':len(errors),
            'road_steps':len(p) if p else None,'underground_realm_count':len(UNDERGROUND)}
