# -*- coding: utf-8 -*-
"""Isolated development gate for Era Bez Granic; no real player database."""
from __future__ import annotations
from collections import deque
from pathlib import Path
import hashlib
import sqlite3
from types import SimpleNamespace


def run():
    checks=0
    def ok(value,message):
        nonlocal checks
        assert value, message
        checks+=1
    from world.v10300_era_bez_granic import ERAS, install
    from core.classes_skills import CLASSES
    from core import bootstrap_economy_professions as b
    from systems.achievements_era_v10300 import levels_reached, sync_v10300
    from player.character import Character

    old_world={'v3000_eternal_5':{'exits':{'north':'v3000_eternal_6'}},
               'v3000_eternal_6':{'exits':{'south':'v3000_eternal_5'}}}
    rooms=dict(old_world);mobs={};spawns=[];npcs={};quests={};items={};recipes={};areas=[]
    zones={};categories={};guides={};power={}
    before=dict(old_world['v3000_eternal_6']['exits'])
    result=install(rooms,mobs,spawns,npcs,quests,items,recipes,areas,zones,categories,guides,power)
    for key,expected in {'regions':11,'rooms':132,'npcs':33,'mobs':110,'story_quests':132,
        'class_quests':3*len(CLASSES),'profession_quests':154,'items':55,'recipes':22}.items():
        ok(result[key]==expected, f'count {key}: {result[key]} != {expected}')
    ok(all(level>=801 for level in (r[2] for r in ERAS)),'new levels 801+')
    ok(ERAS[-1][3]==5000,'last content 5000, NOT character cap')
    ok(len(quests)==result['quests']==sum(1 for qid in quests if qid.startswith('v10300_')),'quest count')
    ok(len({n['room'] for n in npcs.values()})==33,'separate NPC rooms')
    ok(len({row['name'] for row in rooms.values() if 'name' in row})==132,'unique authored rooms')
    ok(rooms['v3000_eternal_6']['exits']['east']=='v10300_swit_01','first gate')
    ok(rooms['v10300_tron_01']['exits']['west']=='v10300_czas_12','last inter-era return')
    directions={'north':'south','south':'north','east':'west','west':'east','up':'down','down':'up'}
    # Check all authored exit pairs and graph connectivity.
    for rid,room in rooms.items():
        for direction,dest in room.get('exits',{}).items():
            ok(dest in rooms, f'broken exit {rid}.{direction}')
            ok(rooms[dest].get('exits',{}).get(directions[direction])==rid,
               f'one way exit {rid}.{direction}')
    pending=deque(['v3000_eternal_6']);visited=set()
    while pending:
        rid=pending.popleft()
        if rid in visited:continue
        visited.add(rid)
        pending.extend(rooms[rid].get('exits',{}).values())
    ok(set(rooms)==visited,'region graph disconnected')
    spawns_ids={mid for rid,mid in spawns}
    for rid,mid in spawns:
        ok(rid in rooms and mid in mobs, f'invalid spawn {rid}/{mid}')
    for qid,q in quests.items():
        if q['kind']=='kill':
            ok(q['target'] in spawns_ids, f'kill without spawn {qid}')
        elif q['kind']=='collect':
            ok(q['target'] in items and any(q['target'] in mobs[mid]['drops'] for mid in spawns_ids),
               f'collect without source {qid}')
        elif q['kind']=='profession_action':
            ok(q.get('reward_profession') and q.get('specialist_tool_type'),f'profession reward {qid}')
        else:raise AssertionError(f'unknown quest kind {q["kind"]}')
        previous=q.get('requires_quest')
        if previous:ok(previous in quests,f'nonexistent prerequisite {qid}')
        ok(int(q.get('generator_level',1))>=801,f'new quest level {qid}')
    for npc in npcs.values():
        ok(npc['room'] in rooms,'invalid NPC room')
        for qid in npc['specialist_quests']:
            ok(qid in quests,f'NPC phantom quest {qid}')
            ok(npc['name']==quests[qid]['giver'],f'NPC mismatched giver {qid}')
    ok(set(quests)=={qid for npc in npcs.values() for qid in npc['specialist_quests']},
       'every quest offered by a real NPC')
    # Część receptur używa legalnych materiałów ze wspólnego katalogu
    # (np. steel_ingot z world.dynamic_content), nie tylko 55 nowych itemów.
    from world.dynamic_content import ITEMS as runtime_items
    for recipe in recipes.values():
        ok(recipe['output'] in items,'missing recipe output')
        ok(all(item in items or item in runtime_items for item in recipe['ingredients']),
           'missing recipe ingredients')
        ok(all(count>0 for count in recipe['ingredients'].values()),'zero-cost recipe')
    # Isolated rank comparisons: temporarily simulate runtime no-limit state.
    old=b.TOOL_MAX_LEVEL
    try:
        b.TOOL_MAX_LEVEL=10_000_000
        for level in (799,800,801,810,1000,2000,4999,5000,5001,5010,10000):
            ok(b.profession_rank(level,'Wędkarstwo')>0,f'profession rank {level}')
            ok(b.tool_tier(level)>0,f'tool tier {level}')
            ok(0<=b.tool_tier_bonus_chance(level)<1,f'tool chance {level}')
        ok(b.profession_rank(800,'Wędkarstwo')==b.PROFESSION_MAX_RANK,'legacy rank 800')
        ok(b.profession_rank(820,'Wędkarstwo')==b.PROFESSION_MAX_RANK+1,'new rank 820')
        ok(b.tool_tier(800)==80,'legacy tier 800')
        ok(b.tool_tier(810)==81,'new tier 810')
        ok(b.tool_tier(5010)==501,'beyond 5000')
        ok(b.tool_tier_access_level(810)==810,'new tier access threshold')
    finally:
        b.TOOL_MAX_LEVEL=old
    obj=object.__new__(Character)
    obj.soul_tier=1;obj.soul_xp=12345
    obj.soul_level=obj.soul_level_cap_for_current_tier()
    obj.race='Człowiek';obj._guild_bonus_percent=0
    output=obj.add_soul_xp(1000)
    ok(obj.soul_xp==13345,'soul bank preserved at gate')
    ok(obj.soul_progress_is_tier_locked(),'soul bank gate is really reached')
    ok('odłożone' in output[0],'soul bank NVDA announcement')
    obj.soul_tier=2
    obj.add_soul_xp(0)
    ok(obj.soul_xp==13345,'tier unlocked does not double XP')
    # Other milestone namespace; save repeated calls must not produce duplicates.
    ok(levels_reached(5001)[-1]==5000,'no false milestone 5001')
    ok(levels_reached(5500)[-1]==5500,'milestones continue beyond 5000')
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
    conn.executescript('CREATE TABLE achievements(account_id INTEGER,achievement_id TEXT UNIQUE,name TEXT,tier TEXT);'
        'CREATE TABLE unlocked_titles(account_id INTEGER,title_id TEXT UNIQUE,title_name TEXT);')
    db=SimpleNamespace(conn=conn)
    snap={('axis','character_level'):5010,('profession','Wędkarstwo'):2000}
    added=sync_v10300(db,1,snap)
    ok(added>0,'new achievements granted')
    ok(sync_v10300(db,1,snap)==0,'achievements idempotent')
    ok(conn.execute('SELECT COUNT(*) FROM unlocked_titles').fetchone()[0]==added,'titles idempotent')
    conn.close()
    # Nowsze wydania v104 także zawierają v103; weryfikuj zgodność
    # prawdziwego VERSION z runtime zamiast wymuszać historyczny numer.
    release=(Path(__file__).resolve().parents[1]/'VERSION').read_text().strip()
    ok(release == b.VERSION and tuple(map(int, release.split('.'))) >= (102,0,13),
       'v103 era carried by coherent release identity')
    return checks,result


if __name__=='__main__':
    total,counts=run()
    print(f'ERA BEZ GRANIC DEVELOPMENT: {total} checks PASS; '
          f'{counts["rooms"]} rooms, {counts["quests"]} quests, '
          f'{counts["mobs"]} mob templates',flush=True)
