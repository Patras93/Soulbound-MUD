# -*- coding: utf-8 -*-
"""v1.21.0: authored topology, real quest persistence, combat drops, NVDA commands."""
from __future__ import annotations

import asyncio
import os
import tempfile
from collections import deque
from types import SimpleNamespace


def audit_legendary_expeditions_v1210():
    import server
    from data.catalogs import ROOMS, ITEMS, MOB_TEMPLATES, NPCS, QUESTS, CRAFT_RECIPES
    from player.session_mixins.command_registry import resolve_session_command
    from systems.content_registry import MOB_SPAWNS
    from world.expansions import TREASURE_CHESTS
    from world.great_world import V1200_REGIONAL_INDEX, V1210_EXPEDITIONS, V1210_EXPEDITION_INDEX, v1210_register_expeditions
    from storage.database import Database
    errors=[]
    checks=0

    def check(ok, label):
        nonlocal checks
        checks+=1
        if not ok:
            errors.append(label)

    check(tuple(map(int, server.VERSION.split('.'))) >= (1, 21, 0), 'release version')
    check(len(V1210_EXPEDITIONS)==4 and len(V1210_EXPEDITION_INDEX)==4,'four expedition indexes')
    check(resolve_session_command('legendarnewyprawy')=='legendaryexpeditions1210','alias registration')
    check(resolve_session_command('wyprawylegendarne')=='legendaryexpeditions1210','second alias')
    check(callable(getattr(server.Session,'legendary_expeditions_v1210',None)),'session command available')
    old_spawn_count=len(MOB_SPAWNS)
    old_quest_count=len(QUESTS)
    v1210_register_expeditions()
    check(len(MOB_SPAWNS)==old_spawn_count and len(QUESTS)==old_quest_count,'repeat catalog import idempotent')
    reachable={'square'}
    pending=deque(['square'])
    while pending:
        source=pending.popleft()
        for target in ROOMS[source].get('exits',{}).values():
            if target in ROOMS and target not in reachable:
                reachable.add(target)
                pending.append(target)
    opposite={'east':'west','west':'east','north':'south','south':'north','up':'down','down':'up'}
    room_ids=set()
    for key, title, mini, final, element, material in V1210_EXPEDITIONS:
        spec=V1210_EXPEDITION_INDEX[key]
        region=V1200_REGIONAL_INDEX[key]
        rooms=spec['rooms']
        room_ids.update(rooms)
        check(len(rooms)==5 and all(r in ROOMS for r in rooms),key+' five rooms')
        check(all(r in reachable for r in rooms),key+' reachable by ordinary movement')
        check(ROOMS[region['archive']]['exits'].get('east')==rooms[0],key+' region entrance')
        check(all(ROOMS[r]['exits'].get('west') == (region['archive'] if i==0 else rooms[i-1]) for i,r in enumerate(rooms)),key+' return routes')
        check(all(ROOMS[r]['exits'].get('east')==rooms[i+1] for i,r in enumerate(rooms[:-1])),key+' forward routes')
        check(all(ROOMS[other]['exits'].get(opposite[d])==r for r in rooms for d,other in ROOMS[r]['exits'].items() if d in opposite),key+' bidirectional links')
        check(all(ROOMS[r].get('v1210_expedition')==key for r in rooms),key+' expedition room metadata')
        check(all(r not in TREASURE_CHESTS for r in rooms[:-1]),key+' no path chests')
        check(rooms[-1] in TREASURE_CHESTS and spec['gear'] in TREASURE_CHESTS[rooms[-1]]['set_pool'],key+' boss chest')
        check(TREASURE_CHESTS[rooms[-1]]['respawn']==86400,key+' chest cooldown')
        for suffix in ('scout','keeper','boss'):
            tid=spec[suffix]
            check(tid in MOB_TEMPLATES,key+f' {suffix} enemy')
            check(any(mid==tid and room in rooms for room,mid in MOB_SPAWNS),key+f' {suffix} spawns')
            check(MOB_TEMPLATES[tid]['quest_target']==tid,key+f' {suffix} quest target')
        check(MOB_TEMPLATES[spec['boss']].get('v017_boss_phases') is True,key+' boss phase runtime flag')
        check(MOB_TEMPLATES[spec['keeper']].get('v017_boss_phases') is True,key+' miniboss phase runtime flag')
        check(MOB_TEMPLATES[spec['boss']]['attack_elements_v11339']==(element,),key+' elemental combat')
        check(bool(MOB_TEMPLATES[spec['boss']]['boss_mechanic']),key+' authored boss mechanic')
        check(MOB_TEMPLATES[spec['boss']]['drops'].get(spec['heart'])==1.0,key+' boss guaranteed ingredient')
        check(MOB_TEMPLATES[spec['keeper']]['drops'].get(spec['seal'])==1.0,key+' miniboss guaranteed ingredient')
        check(all(not MOB_TEMPLATES[spec[a]].get('auto_aggro') for a in ('scout','keeper','boss')),key+' solo-friendly passive mobs')
        for item_id in (spec['heart'],spec['seal'],spec['gear']):
            check(item_id in ITEMS,key+' real item '+item_id)
        check(ITEMS[spec['gear']].get('type')=='armor' and bool(ITEMS[spec['gear']].get('stats')),key+' usable gear')
        recipe=CRAFT_RECIPES.get(spec['gear'])
        check(bool(recipe) and recipe.get('output')==spec['gear'],key+' craft recipe')
        if recipe:
            check(all(item_id in ITEMS and qty>0 for item_id,qty in recipe.get('ingredients',{}).items()),key+' craft ingredient IDs')
            check('forge' in recipe.get('stations',()) and recipe.get('tool_item_id')=='crafting_hammer',key+' valid station and tool')
        check(NPCS[spec['giver']]['room']==rooms[0] and NPCS[spec['witness']]['room']==rooms[1],key+' narrative NPC location')
        check(NPCS[spec['contractor']]['room']==rooms[2],key+' contractor location')
        check(NPCS[spec['giver']]['quest_chain']==spec['quests'],key+' quest chain indexed')
        check(all(q in QUESTS for q in spec['quests']),key+' quest definitions')
        check(tuple(QUESTS[q]['kind'] for q in spec['quests'])==('talk_npc','kill','kill','kill'),key+' 4 stage variety')
        check(QUESTS[spec['quests'][0]]['target_npc']==spec['witness'],key+' actual dialogue target')
        check(tuple(QUESTS[q]['target'] for q in spec['quests'][1:]) == (spec['scout'],spec['keeper'],spec['boss']),key+' combat objectives')
        check(all(QUESTS[spec['quests'][i]].get('requires_quest')==spec['quests'][i-1] for i in range(1,4)),key+' quest gates')
        check(QUESTS[spec['quests'][3]]['reward_items'].get(spec['heart'])==1,key+' final reward')
        check(QUESTS[spec['contract']]['repeatable'] is True and QUESTS[spec['contract']]['repeat_cooldown']==3600,key+' renewable contract')
        check(QUESTS[spec['contract']]['target']==spec['scout'],key+' contract actual enemy')
        check(all(q.get('reward_gold',0)==0 and q.get('reward_mithril',0)==0 for q in (QUESTS[qid] for qid in (*spec['quests'],spec['contract']))),key+' currency representation')
        check(QUESTS[spec['contract']]['reward_silver']>0 and QUESTS[spec['quests'][0]]['reward_silver']>0,key+' positive scaled rewards')
    check(len(room_ids)==20,'exactly 20 unique expedition rooms')
    check(len({ROOMS[r]['name'] for r in room_ids})==20,'unique NVDA location names')

    with tempfile.TemporaryDirectory() as tmp:
        db=Database(os.path.join(tmp,'expeditions.sqlite'))
        aid=db.create_account('exp121_a','test123')
        bid=db.create_account('exp121_b','test123')
        key='aurora'
        spec=V1210_EXPEDITION_INDEX[key]
        qid=spec['quests'][1]
        bounty=spec['contract']
        db.start_quest(aid,qid)
        db.start_quest(aid,bounty)
        check(db.quest(aid,qid)['status']=='active' and db.quest(bid,qid) is None,'account-specific quest start')
        for _ in range(2):
            changes=db.increment_quest(aid,spec['scout'])
        check(db.quest(aid,qid)['progress']==2 and db.quest(aid,bounty)['progress']==2,'shared kill advances two active missions')
        check(db.quest(bid,qid) is None,'kills isolated between accounts')
        for _ in range(20):
            db.increment_quest(aid,spec['scout'])
        check(db.quest(aid,qid)['progress']==4 and db.quest(aid,bounty)['progress']==7,'progress capped to quest target')
        db.complete_quest(aid,bounty)
        check(db.repeat_quest_seconds_remaining(aid,bounty,3600)>0,'renewable contract cooldown')
        db.restart_quest(aid,bounty)
        check(db.quest(aid,bounty)['progress']==0 and db.quest(aid,bounty)['status']=='active','renewed contract reset')
        check(db.quest(aid,qid)['progress']==4,'other active quest unaffected by reset')
        # Execute NVDA commands on actual session class, with no database writes.
        sess=object.__new__(server.Session)
        sess.account_id=aid
        sess.character=SimpleNamespace(room_id='square')
        sess.server=SimpleNamespace(db=db)
        lines=[]
        async def send(line):
            lines.append(str(line))
        sess.send=send
        changes_before=db.conn.total_changes
        async def execute():
            await sess.legendary_expeditions_v1210('')
            await sess.legendary_expeditions_v1210('Pielgrzymka Pierwszego Światła')
            await sess.legendary_expeditions_v1210('postep')
        asyncio.run(execute())
        check(any('LEGENDARNE WYPRAWY' in line for line in lines),'NVDA clear list')
        check(any('Pierwszy krok:' in line for line in lines),'NVDA route navigation')
        check(any('etapy 1' in line for line in lines),'NVDA persistent journal')
        check(db.conn.total_changes==changes_before,'NVDA commands read-only')
        db.conn.close()
    return {'checks':checks,'error_count':len(errors),'errors':errors,'regions':len(V1210_EXPEDITION_INDEX),'rooms':len(room_ids)}


if __name__=='__main__':
    result=audit_legendary_expeditions_v1210()
    print(result)
    if result['error_count']:
        raise SystemExit(1)
