# -*- coding: utf-8 -*-
"""v3.31.3 fail-closed audit of all 14 profession task ladders and SQLite events.

The SQLite event simulation calls the actual gameplay DB method. It does not
claim every quest was accepted, crafted and handed in via live TCP.
"""
from __future__ import annotations
from collections import Counter


def run_regression(runtime):
    from systems.profession_quest_expansion import PROFESSION_QUEST_SPECS_V0700
    from systems.profession_apprenticeship_v3313 import (
        ADDED_IDS, QUEST_IDS_BY_PROFESSION, UNDERREPRESENTED,
        BEGINNER_STAGES, CONTINUATION_LEVELS,
    )
    from player.session_mixins.quest_commands import SessionQuestCommandsMixin
    from validation.v2400_real_quest_events import QuestEventDB
    from config.balance import QUEST_REPEAT_COOLDOWN_SECONDS

    quests, npcs = runtime.QUESTS, runtime.NPCS
    checks=0
    def check(condition,msg):
        nonlocal checks
        if not condition:
            raise AssertionError('v3.31.3: '+msg)
        checks += 1

    from core.bootstrap_economy_professions import VERSION
    expected_total = 6573 if VERSION == '9.00.0' else 5605 if VERSION == '8.00.0' else 3925 if VERSION in ('7.00.0','7.10.0','7.10.1','8.00.0','9.00.0') else 3861 if VERSION == '6.00.1' else 2901 if VERSION in ('5.00.0','5.00.1','6.00.0','6.00.1','7.00.0','7.10.0','7.10.1','8.00.0','9.00.0') else 2701 if VERSION in ('4.00.0','4.00.1','4.00.2','4.00.3','4.00.4','4.00.5','4.00.6','4.00.7','4.10.0','4.20.0','4.21.0','4.21.1','5.00.0','5.00.1','6.00.0','6.00.1','7.00.0','7.10.0','7.10.1','8.00.0','9.00.0') else 2334
    check(len(quests)==expected_total, f'expected {expected_total} quests, got {len(quests)}')
    check(len(ADDED_IDS)==200 and len(set(ADDED_IDS))==200,'200 distinct new IDs')
    check(len(QUEST_IDS_BY_PROFESSION)==14,'all 14 professions')
    check(len(BEGINNER_STAGES)==8 and len(CONTINUATION_LEVELS)==22,'stage coverage')
    from player.session_mixins.profession_storage import SessionProfessionStorageMixin
    class RewardChecker(SessionQuestCommandsMixin, SessionProfessionStorageMixin):
        pass
    checker=RewardChecker()
    for profession, tool, npc_id, _ in PROFESSION_QUEST_SPECS_V0700:
        ids=QUEST_IDS_BY_PROFESSION[profession]
        check(len(ids)==(30 if profession in UNDERREPRESENTED else 8),f'{profession}: wrong count')
        npc=npcs[npc_id]
        for stage_ix,qid in enumerate(ids):
            q=quests[qid]
            check(qid in (npc.get('specialist_quests') or ()) ,f'{qid}: no NPC offer')
            check(q.get('giver')==npc.get('name'),f'{qid}: NPC name')
            check(q.get('kind')=='profession_action' and q.get('target')==profession, f'{qid}: real action type')
            check(q.get('required_profession')==profession and q.get('specialist_tool_type')==tool,f'{qid}: profession/tool')
            check(q.get('reward_profession')==profession and q.get('reward_tool_type')==tool,f'{qid}: reward types')
            check(int(q.get('reward_profession_xp') or 0)>0 and int(q.get('reward_tool_xp') or 0)>0,f'{qid}: XP rewards')
            check(bool(q.get('repeatable')) and int(q.get('repeat_cooldown',0))==QUEST_REPEAT_COOLDOWN_SECONDS,f'{qid}: hourly cycle')
            check(int(q.get('needed') or 0)>0 and q.get('name') and q.get('description'),f'{qid}: accessible description')
            expected_previous = ids[stage_ix-1] if stage_ix else None
            check(q.get('requires_quest')==expected_previous,
                  f'{qid}: sequential progress without level hard lock')
            check(not checker.validate_quest_rewards_v1106(qid,q),f'{qid}: actual reward guard')
        check(len(set(quests[qid]['name'] for qid in ids))==len(ids),f'{profession}: duplicate player names')
    # Actual game DB progress method used by the action hooks. All 200 active
    # quest rows in one account; a second account must remain unchanged.
    db=QuestEventDB()
    try:
        for qid in ADDED_IDS:
            db.conn.executemany(
                'INSERT INTO quests(account_id,quest_id,status,progress) VALUES(?,?,?,?)',
                ((42,qid,'active',0),(84,qid,'active',0)))
        db.conn.commit()
        for profession, tool, _, _ in PROFESSION_QUEST_SPECS_V0700:
            expected=set(QUEST_IDS_BY_PROFESSION[profession])
            result=db.increment_profession_action_quests_v0700(42,profession,tool,1)
            got={qid for qid,*_ in result}
            check(got==expected,f'{profession}: real progress credited {len(got)}, expected {len(expected)}')
        for qid in ADDED_IDS:
            row_a=db.conn.execute('SELECT progress FROM quests WHERE account_id=42 AND quest_id=?',(qid,)).fetchone()
            row_b=db.conn.execute('SELECT progress FROM quests WHERE account_id=84 AND quest_id=?',(qid,)).fetchone()
            check(int(row_a['progress'])==1 and int(row_b['progress'])==0,f'{qid}: SQLite isolation')
    finally:
        db.close()
    return {'checks':checks,'quests':len(quests),'new':len(ADDED_IDS),'beginner':112,'continuation':88}

if __name__=='__main__':
    import os, tempfile, socket
    with tempfile.TemporaryDirectory(prefix='prof-v3313-') as tmp:
        os.environ['SOULBOUND_DB']=os.path.join(tmp,'test.sqlite')
        os.environ['SOULBOUND_HOST']='127.0.0.1'
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));os.environ['SOULBOUND_PORT']=str(sock.getsockname()[1])
        import server
        print('PROFESJE 14 v3.31.3',run_regression(server),'PASS')
