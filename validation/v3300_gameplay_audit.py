# -*- coding: utf-8 -*-
"""Soulbound 3.30.0: fail-closed gameplay regression for the Seven Legends.

Checks actual completion reward validation (all quests), story/NPC accessibility,
all v3.20 event types, isolation, persistent SQLite, and screen-reader text.
A test of a database event is not misreported as playing a quest over TCP.
"""
from __future__ import annotations
import asyncio
from collections import Counter, deque
import os
import sqlite3
import tempfile
from types import SimpleNamespace
from pathlib import Path


def run_audit(server):
    from core.classes_skills import CLASSES, CLASS_SKILLS
    from player.session_mixins.quest_commands import SessionQuestCommandsMixin
    from player.session_mixins.quest_npc import SessionQuestNpcMixin
    from player.session_mixins.profession_storage import SessionProfessionStorageMixin
    from validation.v2400_real_quest_events import QuestEventDB
    from world.legends_v3100 import CLASS_NAMES, PROFESSIONS, REALMS, PROFESSION_REWARD_TOOL_TYPES
    from world.legends_v3200 import OPPOSITE, _reachable
    from systems.mastery_crafting_v2201 import TOOL_TYPES
    from systems.equipment_crafting import JEWELCRAFT_RECIPES, SHOPS

    class QuestVerifier(SessionQuestCommandsMixin, SessionProfessionStorageMixin):
        pass
    verifier=QuestVerifier()
    quests, rooms, npcs, mobs, items = (server.QUESTS, server.ROOMS, server.NPCS,
                                      server.MOB_TEMPLATES, server.ITEMS)
    findings=[]
    def require(ok, message):
        if not ok: findings.append(message)
    require(len(quests)>=2134, f'quest count decreased: {len(quests)}')
    # This is the REAL completion reward guard used in gameplay; v3.20 catalog
    # tests never called it, letting 56 broken profession orders go unnoticed.
    for quest_id, quest in quests.items():
        for error in verifier.validate_quest_rewards_v1106(quest_id, quest):
            findings.append(f'{quest_id}: {error}')

    reward_quests=0
    for version, stages in (('v3100',('order_1','order_2')), ('v3200',('3','4'))):
        for number,(profession,_) in enumerate(PROFESSIONS):
            expected=TOOL_TYPES[profession]
            require(PROFESSION_REWARD_TOOL_TYPES[profession]==expected,
                    f'profession mapping {profession}')
            require(verifier.valid_tool_type(expected),f'unknown real tool type {expected}')
            for stage in stages:
                key=(f'{version}_prof_{number:02d}_'+stage)
                quest=quests.get(key)
                require(bool(quest), f'missing profession quest {key}')
                if quest:
                    require(quest.get('reward_profession')==profession, f'{key} wrong profession')
                    require(quest.get('reward_tool_type')==expected, f'{key} wrong tool type')
                    require(int(quest.get('reward_profession_xp',0))>0, f'{key} no profession XP')
                    reward_quests+=1
    require(reward_quests==56,f'{reward_quests} profession reward quests instead of 56')

    newquests={qid:q for qid,q in quests.items() if qid.startswith('v3200_')}
    require(len(newquests)==392, f'expected 392 new quests, got {len(newquests)}')
    # Check EVERY prerequisite from the complete quest registry for dangling
    # references and cycles (no infinitely locked chapter chain).
    for qid,q in quests.items():
        prev=q.get('requires_quest')
        if prev: require(prev in quests, f'{qid}: unknown prerequisite {prev}')
    marks={}
    def visit(start):
        stack=[]; position={}; node=start
        while node and node not in marks:
            if node in position:
                findings.append(f'prerequisite cycle: {stack[position[node]:]}');break
            position[node]=len(stack);stack.append(node)
            node=quests.get(node,{}).get('requires_quest')
        for qid in stack:marks[qid]=True
    for qid in quests:visit(qid)
    # NPC is separately routable and each new quest is actually offered by its
    # named giver. Target NPC for talk stage must also exist and be reachable.
    reachable=_reachable(rooms)
    npc_by_name={}
    for npc_id,npc in npcs.items():
        npc_by_name.setdefault(npc.get('name'),[]).append((npc_id,npc))
    offer_ids=set()
    for npc_id,npc in npcs.items():
        for qid in (npc.get('quest'), *(npc.get('quest_chain') or ()), *(npc.get('specialist_quests') or ())):
            if qid: offer_ids.add(qid)
    for qid,q in newquests.items():
        require(qid in offer_ids, f'quest missing from NPC offer list: {qid}')
        giver=q.get('giver')
        matches=npc_by_name.get(giver,())
        require(bool(matches),f'quest has no NPC giver: {qid}: {giver}')
        require(any(npc.get('room') in reachable for _,npc in matches),f'unreachable giver: {qid}')
        kind=q.get('kind'); target=q.get('target')
        if kind=='talk_npc':
            require(target in npcs,f'missing talk target NPC: {qid}')
            require(q.get('target_npc')==target,f'wrong talk target id: {qid}')
            if target in npcs: require(npcs[target].get('room') in reachable,f'NPC target unreachable: {qid}')
        elif kind=='kill':
            require(target in mobs,f'kill target undefined: {qid}')
            if target in mobs: require(any(m==target and r in reachable for r,m in server.MOB_SPAWNS),
                                        f'kill target has no accessible spawn: {qid}')
        elif kind=='collect':
            require(target in items,f'collect target undefined: {qid}')
        else: require(False,f'unexpected new quest kind: {qid}:{kind}')
        require(int(q.get('needed') or 0)>0,f'nonpositive quest target: {qid}')
        for field in ('name','description'):
            value=str(q.get(field) or '')
            require(bool(value.strip()),f'{qid} lacks player-facing {field}')
            require(not any(ord(c)<32 and c not in '\n\t' for c in value),
                    f'{qid} has control characters, breaks screen reader')
            require(len(value)<700,f'{qid} excessively long {field} for NVDA')

    for rid, room in rooms.items():
        if not rid.startswith('v3200_'):continue
        require(rid in reachable,f'new room disconnected: {rid}')
        require(not room.get('traps') and not room.get('random_traps'), f'new room has traps: {rid}')
        for direction, dst in room.get('exits',{}).items():
            require(dst in rooms,f'{rid} broken exit {direction}:{dst}')
            if dst in rooms and direction in OPPOSITE:
                require(rooms[dst].get('exits',{}).get(OPPOSITE[direction])==rid,
                        f'{rid} one-way {direction}->{dst}')
    occupied={}
    for npc_id,npc in npcs.items():
        rid=npc.get('room')
        if rid in occupied:findings.append(f'NPC room collision {npc_id},{occupied[rid]} in {rid}')
        occupied[rid]=npc_id
        require(rid in rooms,f'NPC in nonexistent room {npc_id}:{rid}')

    for class_name in CLASS_NAMES:
        skills=[x for x in CLASS_SKILLS[class_name] if str(x.get('id','')).startswith('v3200_')]
        require(len(skills)==3,f'class {class_name} has {len(skills)} master skills')
        require({int(x.get('unlock') or 0) for x in skills}=={260,420,600},f'class {class_name} wrong unlocks')
    for slug,*_ in REALMS:
        key=f'v3200_{slug}_superboss'; boss=mobs.get(key)
        require(bool(boss),f'missing superboss {key}')
        if boss:
            require(bool(boss.get('boss')) and bool(boss.get('world_boss')),f'{key} wrong boss flags')
            require(len(tuple(boss.get('attack_elements_v11339') or ()))==2,f'{key} needs 2 elements')
            require(boss.get('v017_boss_phases'),f'{key} no phase engine')
            require(any(m==key and r in reachable for r,m in server.MOB_SPAWNS),f'{key} cannot be reached')

    require('iron_ore' in SHOPS['forge'],'iron ore not sold in forge')
    require(JEWELCRAFT_RECIPES['jewel_iron_ring']['ingredients']=={'iron_ore':2},
            'iron ring recipe changed')
    if findings:raise AssertionError('v3.30.0 AUDIT FAIL (%s):\n%s' %
                                    (len(findings),'\n'.join(findings[:35])))

    # Real DatabaseQuestMixin event methods, not direct setting of progress.
    # Talk quests use the real NPC talk dispatcher; the test substitutes only
    # reward payout, which is separately guarded for EVERY quest above.
    db=QuestEventDB()
    events=Counter()
    aid=42
    class Speaker(SessionQuestNpcMixin):
        def __init__(self):
            self.account_id=aid
            self.server=SimpleNamespace(db=db)
            self.character=SimpleNamespace(class_name=CLASS_NAMES[0])
            self.completed=[]
        async def announce_active_quest_progress(self,*args):return None
        async def complete_quest(self,quest_id):
            db.complete_quest(aid,quest_id)
            self.completed.append(quest_id)
        async def send(self,*args):return None
    speaker=Speaker()
    for qid,q in newquests.items():
        db.start_quest(aid,qid)
        kind=q['kind'];target=q['target'];need=int(q['needed'])
        if kind=='kill':
            db.increment_quest(aid,'__wrong_mob_v3300__')
            require(int(db.quest(aid,qid)['progress'])==0,f'{qid} advanced from wrong kill')
            for i in range(need):db.increment_quest(aid,target)
            events['kill']+=1
        elif kind=='collect':
            db.increment_item_collect_quest(aid,'__wrong_item_v3300__',need)
            require(int(db.quest(aid,qid)['progress'])==0,f'{qid} advanced from wrong loot')
            db.increment_item_collect_quest(aid,target,need)
            events['collect']+=1
        else:
            # Calling the real NPC talk dispatcher on an active quest.
            npc=npcs[target]
            assert asyncio.run(speaker.process_starter_talk_quests(target,npc)),qid
            events['talk_npc']+=1
        row=db.quest(aid,qid)
        require(int(row['progress'])>=need,f'{qid} real event did not reach goal')
        if kind!='talk_npc': db.complete_quest(aid,qid)
        require(db.quest(aid,qid)['status']=='completed',f'{qid} did not persist completion')
        # Don't keep hundreds of completed quests from an unrelated fictional
        # character around while testing later events.
        db.conn.execute('DELETE FROM quests WHERE account_id=? AND quest_id=?',(aid,qid))
        db.conn.commit()
    db.close()
    if findings:raise AssertionError('v3.30 gameplay event failures: '+'; '.join(findings[:20]))

    # Actual SQLite durability across a DB reopen (not a mocked dictionary).
    from storage.db_quests import DatabaseQuestMixin
    with tempfile.TemporaryDirectory(prefix='soulbound-v3300-quests-') as directory:
        dbpath=os.path.join(directory,'audit.db')
        class Persistent(DatabaseQuestMixin):
            def __init__(self):
                self.conn=sqlite3.connect(dbpath)
                self.conn.row_factory=sqlite3.Row
        durable=Persistent()
        durable.conn.executescript('''CREATE TABLE IF NOT EXISTS quests
            (account_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,
             completed_at INTEGER,completion_count INTEGER,
             PRIMARY KEY (account_id,quest_id));
             CREATE TABLE IF NOT EXISTS quest_resource_progress_v0929
            (account_id INTEGER,quest_id TEXT,target_id TEXT,progress INTEGER,
             PRIMARY KEY(account_id,quest_id,target_id));''')
        qid='v3200_old_00_quest_2';q=newquests[qid]
        durable.start_quest(aid,qid)
        durable.increment_quest(aid,q['target'])
        value=durable.quest(aid,qid)['progress']
        require(value==1,'SQLite event did not commit')
        durable.conn.close();durable=Persistent()
        require(durable.quest(aid,qid)['progress']==1,'SQLite lost quest progress on reopen')
        durable.conn.close()
    if findings:raise AssertionError('v3.30 SQLite persistence: '+'; '.join(findings[:20]))
    result={'reward_quests':len(quests), 'fixed_profession_orders':reward_quests,
            'story_quests':len(newquests),'event_checks':sum(events.values()),
            'event_types':dict(events),'rooms_reachable':len(reachable),
            'npc_count':len(npcs),'classes':len(CLASS_NAMES),'superbosses':len(REALMS)}
    print('GRYWALNOSC v3.30.0 PASS:',result,flush=True)
    print('TEST COVERAGE: reward guards for all quests; v3.20 DB progress and NPC talk dispatch. '
          'NOT tested: every quest via live TCP, 6-player boss balance, screen-reader speech timing.',flush=True)
    return result


def main():
    import socket
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    os.environ['SOULBOUND_HOST']='127.0.0.1'
    os.environ['SOULBOUND_PORT']=str(port)
    import server
    run_audit(server)

if __name__=='__main__':main()
