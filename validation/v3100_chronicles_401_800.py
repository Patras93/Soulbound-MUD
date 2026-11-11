# -*- coding: utf-8 -*-
"""v31 physical 401–800 story campaign, quest XP, NPC availability and NVDA."""
import asyncio
import sqlite3
from types import SimpleNamespace


def run():
    from world.dynamic_content import EXP_AREAS, quest_kill_targets_v0389
    from world.v3100_endgame_chronicles import CHAPTERS, install
    from data.rooms import ROOMS
    from data.mobs import MOB_TEMPLATES
    from data.npcs import NPCS
    from data.quests import QUESTS
    from systems.content_registry import MOB_SPAWNS
    from core.progression_resources import (
        v0270_quest_character_reward,v0522_combat_quest_class_reward,
        v0190_quest_soul_reward,v0190_quest_currency_reward,
    )
    from validation.v2910_dynamic_exp_areas import FakeSession
    from storage.db_quests import DatabaseQuestMixin
    checks=0
    def ok(truth,label):
        nonlocal checks
        assert truth,label
        checks+=1

    spawn_set=set(MOB_SPAWNS)
    for slug,zone,low,high,mentor,camp,titles,enemies,miniboss,theme in CHAPTERS:
        origin=f'v3000_{slug}_3'; first=f'v3100_{slug}_1'
        ok(ROOMS[origin]['exits']['east']==first, 'v31 wejscie '+slug)
        ok(ROOMS[first]['exits']['west']==origin,'v31 powrot '+slug)
        for i in range(1,7):
            rid=f'v3100_{slug}_{i}'
            room=ROOMS[rid]
            ok(room['name']==titles[i-1] and room['zone']==zone,'pokoj '+rid)
            ok(low<=room['generator_level']<=high,'poziom '+rid)
            ok(not room.get('trap'),'zero pulapek '+rid)
            if i>1:
                ok(room['exits']['south']==f'v3100_{slug}_{i-1}','powrot '+rid)
            if i<6:
                ok(room['exits']['north']==f'v3100_{slug}_{i+1}','do przodu '+rid)
        npc_id=f'v3100_{slug}_guide'
        npc=NPCS[npc_id]
        ok(npc['room']==first and npc['name']==mentor,'NPC '+slug)
        ok(sum(n.get('room')==first for n in NPCS.values())==1,'jeden NPC '+slug)
        chain=tuple(f'v3100_{slug}_quest_{j}' for j in range(1,7))
        ok(npc['specialist_quests']==chain,'lancuch NPC '+slug)
        # Simulate actual NPC offer logic and persistent SQLite quest progress.
        class FakeDB(DatabaseQuestMixin):
            pass
        conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
        conn.execute('CREATE TABLE quests(account_id INTEGER, quest_id TEXT, status TEXT, progress INTEGER, completed_at INTEGER, completion_count INTEGER, UNIQUE(account_id,quest_id))')
        conn.execute('CREATE TABLE quest_resource_progress_v0929 (account_id INTEGER,quest_id TEXT,target_id TEXT,progress INTEGER)')
        db=FakeDB();db.conn=conn
        def offered():
            # Regula flagi v700_story_npc z quest_progress.py:
            # prezentowany jest tylko pierwszy nieukonczony etap.
            for q in chain:
                row=db.quest(17,q)
                if row is None or row['status'] != 'completed':
                    return [q]
            return []
        ok(offered()==[chain[0]],'pierwsze zadanie NPC '+slug)
        for j,qid in enumerate(chain,1):
            quest=QUESTS[qid]
            ok(quest['kind']=='kill' and quest['needed']==(3 if j<=4 else 1),'prawdziwy kill quest '+qid)
            ok(quest['generator_level']<=high,'poziom questa '+qid)
            if j>1:ok(quest['requires_quest']==chain[j-2],'kolejnosc '+qid)
            target=quest['target']
            ok(target in MOB_TEMPLATES and target in quest_kill_targets_v0389(target,MOB_TEMPLATES[target]), 'real target '+qid)
            ok(any(m==target for r,m in spawn_set),'cel ma spawn '+qid)
            ok(v0270_quest_character_reward(quest)>0, 'exp postaci '+qid)
            ok(v0522_combat_quest_class_reward(quest)>0,'exp klasy '+qid)
            ok(v0190_quest_soul_reward(quest)>0,'exp duszy '+qid)
            ok(v0190_quest_currency_reward(quest)>0,'waluta '+qid)
            db.start_quest(17,qid)
            ok(offered()==[qid],'aktywny etap '+qid)
            for k in range(quest['needed']):
                changes=db.increment_quest(17,target)
                ok(changes==[(qid,k+1)],'zliczanie zabic '+qid)
            ok(db.increment_quest(17,target)==[], 'nie nabija ponad wymagania '+qid)
            row=db.quest(17,qid)
            ok(row['progress']==quest['needed'],'pelnosc postepu '+qid)
            conn.execute("UPDATE quests SET status='completed' WHERE account_id=17 AND quest_id=?",(qid,))
            conn.commit()
        ok(offered()==[],'zakonczona saga '+slug)
        conn.close()
        for j,name in enumerate(enemies,1):
            mid=f'v3100_{slug}_mob_{j}'
            ok(MOB_TEMPLATES[mid]['name']==name,'mob '+mid)
            ok(MOB_TEMPLATES[mid]['class_xp_reward']>0 and MOB_TEMPLATES[mid]['soul_reward']>0,'EXP '+mid)
        ok((f'v3100_{slug}_6',f'v3100_{slug}_boss') in spawn_set,'mini boss spawn '+slug)
        ok(MOB_TEMPLATES[f'v3100_{slug}_boss']['world_boss'],'boss '+slug)
        area=next(a for a in EXP_AREAS if a['id']=='v3000_'+slug)
        ok('12 pokojow' in area['description'],'aktualizacja katalogu '+slug)
        ok(next(a for a in FakeSession(low).recommended_exp_areas_v2910())['id']=='v3000_'+slug,'polecane '+slug)
    # The installer does not duplicate content when called a second time.
    counts=tuple(map(len,(ROOMS,MOB_TEMPLATES,MOB_SPAWNS,NPCS,QUESTS)))
    ok(install(ROOMS,MOB_TEMPLATES,MOB_SPAWNS,NPCS,QUESTS,EXP_AREAS)==(), 'idempotentny instalator')
    ok(counts==tuple(map(len,(ROOMS,MOB_TEMPLATES,MOB_SPAWNS,NPCS,QUESTS))), 'brak duplikatow')
    s=FakeSession(510)
    s.server.db=SimpleNamespace(quest=lambda *_:None)
    s.sent.clear()
    asyncio.run(s.show_exp_areas('kroniki'))
    ok(len(s.sent)==5,'NVDA max cztery kroniki i naglowek')
    ok(all('0/6' in line for line in s.sent[1:]),'licznik przy nowym graczu')
    ok('przyjmij 1' in s.sent[0], 'krotka komenda')
    return checks

if __name__=='__main__':
    print(f'V31.00.0 KRONIKI 401-800: {run()} checks PASS')
