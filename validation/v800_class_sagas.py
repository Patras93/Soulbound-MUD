# -*- coding: utf-8 -*-
"""v8.00.0: 14*120 authored class quests and real one-kill SQLite validation."""
from __future__ import annotations
from validation.v1100_release_counts import expected_quest_total_v1100
import tempfile
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

def run_regression(runtime=None):
    if runtime is None:
        import server as runtime
    from systems.class_legend_paths_v800 import CLASSES,CHAPTERS,STAGE_TYPES,QUEST_IDS,MENTOR_ROOMS,ALL_IDS,stage_level
    from storage.database import Database
    from core.classes_skills import RACES,CLASSES as GAME_CLASSES
    from player.session_mixins.quest_progress import SessionQuestProgressMixin
    from player.session_mixins.quest_offers import SessionQuestOffersMixin
    from world.legends_v3200 import _reachable,OPPOSITE
    from player.session_mixins.quest_commands import SessionQuestCommandsMixin
    from player.session_mixins.museum_bounty import SessionMuseumBountyMixin
    import asyncio
    from core.progression_resources import v0190_quest_currency_reward
    checks=0
    def ok(test,label):
        nonlocal checks
        assert test,'v8 saga: '+label
        checks+=1
    ok(runtime.VERSION in ('8.00.0','9.00.0','10.00.0','10.00.1','10.00.2','11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12'),'release number')
    ok(len(runtime.QUESTS)==(expected_quest_total_v1100() if runtime.VERSION in ('11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12') else 6585 if runtime.VERSION in ('10.00.0','10.00.1','10.00.2','11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12') else 6573 if runtime.VERSION == '9.00.0' else 5605),'3925 old + 1680 new')
    ok(len(ALL_IDS)==1680 and len(set(ALL_IDS))==1680,'unique ids')
    ok(len(CLASSES)==14 and len(CHAPTERS)==12 and len(STAGE_TYPES)==10,'14x12x10 schema')
    ok(set(QUEST_IDS).issubset({row[0] for row in GAME_CLASSES}),'all playable classes covered')
    reachable=_reachable(runtime.ROOMS)
    counts=Counter(npc['room'] for npc in runtime.NPCS.values())
    reward_guard=SessionQuestCommandsMixin()
    for name,slug,epithet,subject,material in CLASSES:
        ids=QUEST_IDS[name]
        rid=MENTOR_ROOMS[name]
        npc_id='v800_class_mentor_'+slug
        npc=runtime.NPCS[npc_id]
        ok(len(ids)==120 and len(set(ids))==120,name+' 120 distinct quests')
        ok(npc['room']==rid and npc['v800_required_class']==name,name+' NPC belongs to class')
        ok(counts[rid]==1 and rid in reachable,name+' lone and reachable mentor')
        ok((tuple(npc['specialist_quests'][:len(ids)])==tuple(ids) and
            (len(npc['specialist_quests'])==len(ids) if runtime.VERSION not in ('11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12') else
             tuple(npc['specialist_quests'][len(ids):])==tuple(
                 f'v1100_class_{[c[0] for c in GAME_CLASSES].index(name):02d}_{step}' for step in (1,2,3)))),
           name+' full old chain and v11 continuation')
        ok(len(runtime.ROOMS[rid]['exits'])==1,name+' only return road')
        back=next(iter(runtime.ROOMS[rid]['exits'].values()))
        ok(any(nxt==rid for nxt in runtime.ROOMS[back]['exits'].values()),name+' bidirectional road')
        ok(material in runtime.ITEMS,name+' supply exists')
        ok(stage_level(0)==1 and stage_level(119)==800,name+' complete 1-800 range')
        for i,qid in enumerate(ids):
            q=runtime.QUESTS[qid]
            ok(q['v800_class_saga'] and q['required_class']==name,qid+' class lock')
            ok(q['v800_stage']==i+1 and q['generator_level']==stage_level(i),qid+' stage/level')
            ok(q.get('requires_quest')==(ids[i-1] if i else None),qid+' sequential lock')
            ok(q['kind']==STAGE_TYPES[i%10],qid+' real supported event')
            ok(q['needed']>0 and q['reward_silver']>0,qid+' nonzero requirements and silver')
            ok(q['target']==('*' if q['kind']=='kill' else 'any' if q['kind']=='explore_frontier' else material),qid+' exact goal')
            ok(q['v800_enemy_rank']==('boss' if i%10==9 else 'elite' if i%10==4 else 'any'),qid+' exact encounter')
            ok(q['v800_min_enemy_level']<=600,qid+' reachable combat threshold')
            ok(not q.get('repeatable'),qid+' one-time progression')
            ok(v0190_quest_currency_reward(q)>=q['reward_silver'],qid+' reward currency')
            ok(not reward_guard.validate_quest_rewards_v1106(qid,q),qid+' reward safety')
        ok(len({runtime.QUESTS[qid]['name'] for qid in ids})==120,name+' unique names')
    class MockPlayer(SessionQuestProgressMixin,SessionQuestOffersMixin):
        def __init__(self,db,aid,klass):
            self.server=SimpleNamespace(db=db)
            self.account_id=aid
            self.character=SimpleNamespace(room_id=MENTOR_ROOMS[klass])
            self._class=klass
        def active_class_names(self):return [self._class]
        def quest_completed(self,quest_id):
            row=self.server.db.quest(self.account_id,quest_id)
            return bool(row and row['status']=='completed')
    with tempfile.TemporaryDirectory(prefix='soulbound_v800_sqlite_') as tmp:
        path=Path(tmp)/'v800.db'
        db=Database(str(path))
        master=db.create_account('TestDrogaLegendy8','VeryLongPassword_Test_8001!')
        case={k:'Wędrowiec' for k in ('nom','gen','dat','acc','ins','loc','voc')}
        a,_=db.create_character_for_master(master,'WojownikPróby8',RACES[0],next(x for x in GAME_CLASSES if x[0]=='Wojownik'),case)
        b,_=db.create_character_for_master(master,'MagPróby8',RACES[0],next(x for x in GAME_CLASSES if x[0]=='Mag'),case)
        player=MockPlayer(db,a,'Wojownik')
        warrior=QUEST_IDS['Wojownik']
        magician=QUEST_IDS['Mag']
        npc=runtime.NPCS['v800_class_mentor_wojownik']
        ok(player.quest_ids_for_npc('v800_class_mentor_wojownik',npc)==[warrior[0]],'short NVDA first offer')
        ok('wymaga aktywnej klasy Mag' in player.quest_lock_reasons(magician[0]),'foreign class locked')
        ok(player.quest_ids_for_npc('v800_class_mentor_mag',runtime.NPCS['v800_class_mentor_mag'])==[],'foreign mentor hidden')
        ok(bool(player.quest_lock_reasons(warrior[1])),'second stage waits for first')
        # One real proc-surface discovery from the existing event method.
        class Explorer(SessionMuseumBountyMixin):
            def __init__(self):
                self.account_id=a
                self.server=SimpleNamespace(db=db)
                self.messages=[]
            async def send(self,message):self.messages.append(message)
        explorer=Explorer()
        exploration=warrior[2]
        db.start_quest(a,exploration)
        changed=asyncio.run(explorer.advance_v0140_quest_progress('explore_frontier','forest',1))
        ok(any(qid==exploration for qid,*_ in changed),'real procedural discovery increments quest')
        ok(db.quest(a,exploration)['progress']==1,'exploration credit persisted')
        ok(any('Droga Legendy' in line for line in explorer.messages),'NVDA discovery message')
        # A newly acquired resource, not previously stored goods, is credited.
        supplies=warrior[3]
        db.start_quest(a,supplies)
        good=runtime.QUESTS[supplies]['target']
        ok(db.quest(a,supplies)['progress']==0,'no existing stock credit')
        db.add_item(a,good,1)
        found=db.increment_item_collect_quest(a,good,1)
        ok(any(qid==supplies for qid,*_ in found),'actual collect event')
        ok(db.quest(a,supplies)['progress']==1,'correct collected quantity')
        ok(db.quest(b,supplies) is None,'no cross-character collection')
        db.start_quest(a,warrior[0])
        db.start_quest(b,warrior[0])
        q=runtime.QUESTS[warrior[0]]
        for level in (0,):
            ok(not db.increment_class_legend_kill_v800(a,'Wojownik',level),'low-level kill rejected')
        ok(not db.increment_class_legend_kill_v800(a,'Mag',900,boss=True),'foreign-class kill rejected')
        ok(db.increment_class_legend_kill_v800(a,'Wojownik',q['v800_min_enemy_level']),'actual rewarded victory')
        ok(db.quest(a,warrior[0])['progress']==1,'one kill increments once')
        ok(db.quest(b,warrior[0])['progress']==0,'no cross-character credit')
        ok(player.quest_ids_for_npc('v800_class_mentor_wojownik',npc)==[warrior[0]],'keep active offer')
        elite=warrior[4]
        boss=warrior[9]
        db.start_quest(a,elite)
        db.start_quest(a,boss)
        e=runtime.QUESTS[elite]['v800_min_enemy_level']
        k=runtime.QUESTS[boss]['v800_min_enemy_level']
        ok(not db.increment_class_legend_kill_v800(a,'Wojownik',k,elite=False,boss=False) or db.quest(a,elite)['progress']==0,'ordinary foe not elite')
        ok(db.quest(a,boss)['progress']==0,'ordinary foe not boss')
        ok(any(qid==elite for qid,_ in db.increment_class_legend_kill_v800(a,'Wojownik',max(e,k),elite=True)),'elite qualifies')
        ok(db.quest(a,boss)['progress']==0,'elite does not count as boss')
        ok(any(qid==boss for qid,_ in db.increment_class_legend_kill_v800(a,'Wojownik',max(e,k),boss=True)),'boss qualifies')
        for _ in range(5):db.increment_class_legend_kill_v800(a,'Wojownik',600,boss=True)
        ok(db.quest(a,boss)['progress']==runtime.QUESTS[boss]['needed'],'bounded exact goal')
        db.complete_quest(a,boss)
        ok(not any(qid==boss for qid,_ in db.increment_class_legend_kill_v800(a,'Wojownik',600,boss=True)),'completed does not gain again')
        db.conn.close()
        db=Database(str(path))
        ok(db.quest(a,boss)['status']=='completed','completed state persistent after reopen')
        ok(db.quest(b,warrior[0])['progress']==0,'other character unaffected after reopen')
        ok(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','sqlite integrity')
        db.conn.close()
    return checks

if __name__=='__main__':print('DROGA LEGENDY v8.00.0:',run_regression(),'PASS')
