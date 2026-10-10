# -*- coding: utf-8 -*-
"""Focused v1.90.0 release gates for Windows and Railway. No production SQLite."""
from __future__ import annotations
import asyncio
import sqlite3
from types import SimpleNamespace
from systems.underground_kingdoms_v1900 import KINGDOMS, DIMENSIONS
from systems.era_chaos_v1800 import compute_reaction
from systems.fame_v1702 import fame_catalog, fame_report
from player.session_mixins.chaos_v1800 import SessionChaosV1800Mixin


def run_regression(server=None):
    if server is None:
        import server
    rooms=server.ROOMS; mobs=server.MOB_TEMPLATES
    items=server.ITEMS; quests=server.QUESTS; spawns=server.MOB_SPAWNS
    checks=0
    def check(condition, message):
        nonlocal checks
        assert condition, f'v1.90.0: {message}'
        checks+=1
    report=server.UNDERGROUND_V1900
    check(report['rooms']==116, 'authored rooms count')
    check(report['new_mob_templates']==66, 'new mobs count')
    check(report['profession_trials']==14, 'profession quests count')
    check(report['legendary_recipes']==6, 'artifact recipes count')
    check(rooms['v1800_portal']['exits']['down']=='v1900_nexus','portal attached')
    check(rooms['v1900_nexus']['exits']['up']=='v1800_portal','safe return')
    new_rooms={key for key in rooms if key.startswith('v1900_')}
    check(len(new_rooms)==116,'all 116 runtime rooms unique')
    graph={key:set(room['exits'].values()) for key,room in rooms.items() if key in new_rooms}
    reached={'v1900_nexus'}
    frontier=['v1900_nexus']
    while frontier:
        for other in graph[frontier.pop()]:
            if other in new_rooms and other not in reached:
                reached.add(other);frontier.append(other)
    check(reached==new_rooms,'all new rooms reachable from nexus')
    for key in sorted(new_rooms):
        room=rooms[key]
        check(all(dest in rooms for dest in room['exits'].values()),f'{key} exits exist')
        check(room.get('zone') and room.get('name') and room.get('desc'),f'{key} NVDA details')
        check(not room.get('trap'),f'{key} safe exploration')
    for slug,zone,_,_,names,enemies,bosses in KINGDOMS:
        check(len(names)==22 and len(enemies)==12 and len(bosses)==3,f'{slug} diversity')
        for j in range(12):
            tid=f'v1900_{slug}_mob_{j}'
            check(tid in mobs and mobs[tid]['fame_target'],f'{tid} Fame')
            check(sum(mid==tid for _,mid in spawns)>=2,f'{tid} spawns')
        for j in range(3):
            tid=f'v1900_{slug}_god_{j}'
            check(tid in mobs and mobs[tid]['v1900_ancient_god'],f'{tid} boss script')
            check(quests[f'v1900_god_quest_{slug}_{j}']['target']==tid,f'{tid} quest credit')
    for slug,_,_,_ in DIMENSIONS:
        for j in range(6):
            check(f'v1900_dim_{slug}_mob_{j}' in mobs, f'{slug} enemy {j}')
        check(f'v1900_dim_{slug}_keeper' in mobs,f'{slug} guardian')
    for idx in range(14):
        q=quests[f'v1900_profession_{idx}']
        check(q['kind']=='profession_action' and q['repeatable'] and q['needed']==45,
              f'profession contract {idx}')
        check(f'v1900_prof_master_{idx}' in server.NPCS,f'profession NPC {idx}')
    for slug in ('korona','tarcza','plaszcz','buty','amulet','zbroja'):
        key=f'v1900_artifact_{slug}'
        item=items[key]
        recipe=server.CRAFT_RECIPES[key]
        check(recipe['output']==key and all(k in items for k in recipe['ingredients']),
              f'craftable {key}')
        check(item['rarity']=='legendary' and item['type']=='armor',f'{key} equipment')
        check(all(0<=float(ward)<=1 for ward in item['element_wards'].values()),
              f'{key} elemental wards within 0-100%')
    catalogue=fame_catalog()
    check(sum(len(v) for v in catalogue.values())>=800,'800 or more world Fame targets')
    for slug,zone,_,_,_,_,_ in KINGDOMS:
        check(len(catalogue[zone])==15,f'{zone} natural Fame targets')
    for _,zone,_,_ in DIMENSIONS:
        check(len(catalogue[zone])==7,f'{zone} Fame targets')
    con=sqlite3.connect(':memory:')
    try:
        entry=fame_report(con,1,'bestiariusz',room_id='v1900_miedz_0')
        check('15' in entry[0] and 'Nieodkryty przeciwnik' in ' '.join(entry),
              'bestiary hides unknown species')
        con.execute("INSERT INTO fame_bosses_v1702(account_id,region,boss_id) VALUES(?,?,?)",
                    (1,KINGDOMS[0][1],catalogue[KINGDOMS[0][1]][0]))
        lines=fame_report(con,1,'bestiariusz',room_id='v1900_miedz_0')
        check('1/15' in lines[0],'first kill persisted')
        check('Fame: 1' in fame_report(con,1,'',room_id='v1900_miedz_0')[0],
              'world count unchanged semantics')
    finally:
        con.close()
    for pair in (('water','lightning'),('water','ice'),('poison','ice'),
                 ('dark','lightning'),('fire','water')):
        name, bonus=compute_reaction(*pair,1000)
        check(name and 0<bonus<=100, f'{pair} finite elemental reaction')
    owner=SimpleNamespace(character=SimpleNamespace(),max_hp=lambda:100,
                          current_hp=100,combat_mob_key=None,
                          server=SimpleNamespace(world=SimpleNamespace(mobs={})))
    check(SessionChaosV1800Mixin._v1900_resolve_tactic(owner,'auto')=='szturm',
          'summons assault by default')
    owner.current_hp=40
    check(SessionChaosV1800Mixin._v1900_resolve_tactic(owner,'auto')=='harmonia',
          'summons aid injured owner')
    owner.current_hp=100;owner.combat_mob_key='test'
    owner.server.world.mobs['test']=SimpleNamespace(alive=True,template_id='v1900_miedz_god_2')
    check(SessionChaosV1800Mixin._v1900_resolve_tactic(owner,'auto')=='bastion',
          'summons defend against bosses')
    messages=[]
    async def broadcast(*a,**k):messages.append(a[1])
    combat=SimpleNamespace(server=SimpleNamespace(party_combat_broadcast=broadcast),
                            mob_effective_max_hp_v11330=lambda mob,t:1000)
    god=SimpleNamespace(alive=True,template_id='v1900_miedz_god_2',hp=1000)
    async def simulate():
        await SessionChaosV1800Mixin.ancient_boss_phase_v1900(combat,god)
        for current in (700,400,150):
            god.hp=current
            await SessionChaosV1800Mixin.ancient_boss_phase_v1900(combat,god)
        await SessionChaosV1800Mixin.ancient_boss_phase_v1900(combat,god)
    asyncio.run(simulate())
    check(int(god._v1900_god_phase)==3 and len(messages)==3,
          'three one-time god phases')
    return checks


if __name__=='__main__':
    print('ANCIENT KINGDOMS v1.90.0:',run_regression(),'PASS')
