# -*- coding: utf-8 -*-
"""Fail-closed real quest, NPC, path, SQLite and work-command regression v6.00.1."""
from __future__ import annotations
from validation.v1100_release_counts import expected_quest_total_v1100
import asyncio
import tempfile
from pathlib import Path
from collections import Counter
from types import SimpleNamespace


def run_regression(runtime=None):
    if runtime is None:
        import server as runtime
    from systems.profession_paths_v601 import (
        SPEC, CHAPTERS, QUEST_IDS_BY_PROFESSION, ALL_QUEST_IDS, ROOM_IDS,
        stage_level, stage_tier,
    )
    from systems.new_professions import PROFESSIONS, BASE_ACTIONS, TIERS, work_for
    from world.legends_v3200 import OPPOSITE, _reachable
    from storage.database import Database
    from core.classes_skills import RACES, CLASSES
    from validation.v600_professions import _Practice
    from player.session_mixins.quest_commands import SessionQuestCommandsMixin
    from player.session_mixins.profession_storage import SessionProfessionStorageMixin
    from player.session_mixins.quest_progress import SessionQuestProgressMixin
    from validation.v2400_real_quest_events import QuestEventDB
    from data.quests import QUESTS
    quests=runtime.QUESTS
    rooms=runtime.ROOMS
    npcs=runtime.NPCS
    checks=0

    def ok(condition, label):
        nonlocal checks
        assert condition, 'v6.00.1: '+str(label)
        checks+=1

    ok(len(quests)==(expected_quest_total_v1100() if getattr(runtime,'VERSION','') in ('11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12','11.00.13','11.00.14','11.00.15','11.00.16','11.00.17','11.00.18',) else 6585 if getattr(runtime,'VERSION','') in ('10.00.0','10.00.1','10.00.2','11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12','11.00.13','11.00.14','11.00.15','11.00.16','11.00.17','11.00.18',) else 6573 if getattr(runtime,'VERSION','') == '9.00.0' else 5605 if getattr(runtime,'VERSION','') == '8.00.0' else 3925 if getattr(runtime,'VERSION','') in ('7.00.0','7.10.0','7.10.1','8.00.0','9.00.0','10.00.0','10.00.1','10.00.2','11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12','11.00.13','11.00.14','11.00.15','11.00.16','11.00.17','11.00.18',) else 3861), f'expected release quest total, got {len(quests)}')
    ok(len(ALL_QUEST_IDS)==960 and len(set(ALL_QUEST_IDS))==960,'960 unique IDs')
    ok(len(QUEST_IDS_BY_PROFESSION)==8 and len(CHAPTERS)==12, '8x12 chapters')
    reachable=_reachable(rooms)
    occupied=Counter(n.get('room') for n in npcs.values())
    from player.session_mixins.profesje6 import SessionProfesje6Mixin
    class Checker(SessionProfesje6Mixin,SessionQuestCommandsMixin,SessionProfessionStorageMixin):
        pass
    checker=Checker()
    for prof,npc_id,npc_name,anchor,room_name,desc,supply in SPEC:
        ids=QUEST_IDS_BY_PROFESSION[prof]
        npc=npcs[npc_id]
        rid=ROOM_IDS[prof]
        tool_type=PROFESSIONS[prof][0]
        actions={a.code for a in BASE_ACTIONS if a.prof==prof}
        ok(len(ids)==120, prof+' length')
        ok(npc['room']==rid and npc['specialist_tool_type']==tool_type, prof+' NPC')
        ok(npc['v601_profession_master'] and npc['strict_profession_quests']==prof,prof+' offers')
        ok(rid in reachable and rid in rooms and rooms[rid]['name']==room_name,prof+' reachable')
        ok(occupied[rid]==1,prof+' only one NPC')
        ok(anchor in rooms,prof+' anchor')
        ok(any(target==rid and rooms[rid]['exits'].get(OPPOSITE[direction])==anchor
               for direction,target in rooms[anchor]['exits'].items()),prof+' two-way road')
        ok(npc['specialist_quests']==tuple(ids),prof+' 120 real offers')
        ok(supply in runtime.ITEMS,prof+' useful supply')
        for idx,qid in enumerate(ids):
            q=quests[qid]
            level=stage_level(idx)
            tier=stage_tier(level)
            ok(q['kind']=='profession_action' and q['target']==prof, qid+' action quest')
            ok(q['specialist_tool_type']==tool_type, qid+' tool')
            ok(q['required_action_code'] in actions, qid+' named action')
            ok(q['min_action_tier']==tier, qid+' real difficulty')
            ok(q['generator_level']==level, qid+' level')
            ok(q.get('requires_quest')==(ids[idx-1] if idx else None), qid+' prerequisite')
            ok(q['needed']>=3 and q['reward_profession_xp']>0 and q['reward_tool_xp']>0, qid+' rewards')
            ok(q['reward_silver']>0 and not q['repeatable'] and q['giver']==npc_name, qid+' payout')
            ok('profesja praca' in q['description'] and q['v601_profession_path'],qid+' instructions')
            ok(work_for(prof,q['required_action_code'],tier) is not None,qid+' executable action')
            ok(not checker.validate_quest_rewards_v1106(qid,q),qid+' reward guard')
        ok(stage_level(0)==1 and stage_level(119)==800,prof+' 1..800')
        ok(len(set(quests[q]['name'] for q in ids))==120,prof+' unique titles')
    # Match real DB event API, including action/tier guards and separate characters.
    db=QuestEventDB()
    try:
        for prof in PROFESSIONS:
            tool=PROFESSIONS[prof][0]
            ids=QUEST_IDS_BY_PROFESSION[prof]
            for qid in ids:
                q=quests[qid]
                # Independent one-stage scenario for every quest; second account
                # has the same quest but cannot be affected by first one's work.
                db.start_quest(10,qid)
                db.start_quest(20,qid)
                code=q['required_action_code'];tier=q['min_action_tier']
                wrong=db.increment_profession_action_quests_v0700(10,prof,tool,1,action_code='wrong',tier=tier)
                ok(all(k!=qid for k,*_ in wrong),qid+' wrong code rejected')
                if tier>1:
                    wrong=db.increment_profession_action_quests_v0700(10,prof,tool,1,action_code=code,tier=1)
                    ok(all(k!=qid for k,*_ in wrong),qid+' wrong tier rejected')
                # An older one-stage quest might also be active, so select
                # the target by its stable id instead of assuming 1 event=1 row.
                changed=db.increment_profession_action_quests_v0700(10,prof,tool,q['needed'],action_code=code,tier=tier)
                ok(any(k==qid for k,*_ in changed),qid+' real event')
                ok(db.quest(10,qid)['progress']==q['needed'],qid+' finish goal')
                ok(db.quest(20,qid)['progress']==0,qid+' no cross-player credit')
                db.complete_quest(10,qid)
                more=db.increment_profession_action_quests_v0700(10,prof,tool,4,action_code=code,tier=tier)
                ok(not any(k==qid for k,*_ in more),qid+' no repeat after completion')
                db.conn.execute('DELETE FROM quests WHERE quest_id=?',(qid,))
                db.conn.commit()
        ok(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
    finally:
        db.close()
    # New NPC gives exactly one short, numerically numbered quest (NVDA).
    class _NPC(SessionQuestProgressMixin):
        def __init__(self, database, aid):
            self.server=SimpleNamespace(db=database)
            self.account_id=aid
    with tempfile.TemporaryDirectory(prefix='soulbound_v601_') as tmp:
        db=Database(str(Path(tmp)/'quests.sqlite'))
        master=db.create_account('TestNewProfessionQuest','VeryLongTestPassword2026!')
        decl={n:'Tester' for n in ('nom','gen','dat','acc','ins','loc','voc')}
        aid,_=db.create_character_for_master(master,'TesterZawodu',RACES[0],CLASSES[0],decl)
        session=_Practice(db,aid)
        quester=_NPC(db,aid)
        npc_id=next(s[1] for s in SPEC if s[0]=='Łowiectwo')
        npc=npcs[npc_id]
        ids=QUEST_IDS_BY_PROFESSION['Łowiectwo']
        ok(quester.quest_ids_for_npc(npc_id,npc)==[ids[0]],'initial NVDA single offer')
        db.start_quest(aid,ids[0])
        session.character.room_id='market'
        db.set_shared_wallet_for_master(master,20000,0,0)
        session.character.silver=20000
        ok('Kupiono' in asyncio.run(session.do('kup Łowiectwo')),'real purchased hunting tool')
        session.character.room_id='meadow'
        before=db.quest(aid,ids[0])['progress']
        msg=asyncio.run(session.do('praca Łowiectwo trop 1'))
        ok('Łowiectwo —' in msg, 'real hunting action')
        ok(db.quest(aid,ids[0])['progress']==before+1,'real work -> quest increment')
        ok(quester.quest_ids_for_npc(npc_id,npc)==[ids[0]],'active quest remains first')
        db.complete_quest(aid,ids[0])
        ok(quester.quest_ids_for_npc(npc_id,npc)==[ids[1]],'next unlocked via first slot')
        # Player has gathered mint in `herbs` (the physical `herbbag`), not
        # regular inventory; the Lv 1 ambush consumes it and credits the mentor.
        db.start_quest(aid,ids[1])  # second mentor quest: zasadzka
        ok(quests[ids[1]]['required_action_code']=='zasadzka', 'second mentor action is ambush')
        existing_tracks = db.item_qty(aid,'v600_tracks')
        db.add_item(aid,'v600_tracks',2)
        db.add_storage_item(aid,'herbbag','mint',1)
        ok(db.item_qty(aid,'mint')==0 and db.storage_qty(aid,'herbbag','mint')==1,
           'mint only in herbs bag')
        before_progress=int(db.quest(aid,ids[1])['progress'])
        before_xp=int(db.profession(aid,'Łowiectwo')['xp'])
        response=asyncio.run(session.do('praca Łowiectwo zasadzka 1'))
        ok('Łowiectwo —' in response and 'Brak materiałów' not in response,
           'ambush accepts herbs bag mint')
        ok(db.storage_qty(aid,'herbbag','mint')==0, 'mint consumed exactly once')
        ok(db.item_qty(aid,'v600_tracks')==existing_tracks, 'ambush consumes exactly two tracks')
        ok(db.quest(aid,ids[1])['progress']==before_progress+1,
           'herb-assisted ambush advances mentor quest')
        ok(int(db.profession(aid,'Łowiectwo')['xp'])>before_xp,
           'herb-assisted ambush awards profession XP')
        # A second attempt without mint must not give a free quest step.
        db.conn.execute('DELETE FROM prof6_cooldowns WHERE account_id=? AND action=?',
                        (aid,'Łowiectwo:zasadzka'))
        db.conn.commit()
        db.add_item(aid,'v600_tracks',2)
        response=asyncio.run(session.do('praca Łowiectwo zasadzka 1'))
        ok('Brak materiałów: 1 × Mięta' in response, 'zero herbs rejects second ambush')
        ok(db.quest(aid,ids[1])['progress']==before_progress+1,
           'no duplicate mentor quest progress when mint missing')
        db.conn.close()
        restored=Database(str(Path(tmp)/'quests.sqlite'))
        ok(restored.quest(aid,ids[0])['status']=='completed','saved across restart')
        ok(restored.profession(aid,'Łowiectwo')['xp']>0,'new professional XP durable')
        restored.conn.close()
    return checks

if __name__=='__main__':
    import os
    os.environ.setdefault('SOULBOUND_HOST','127.0.0.1')
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
        os.environ['SOULBOUND_DB']=str(Path(d)/'runtime.sqlite')
        print('v6.00.1 Droga Mistrza:',run_regression(),'checks PASS')
