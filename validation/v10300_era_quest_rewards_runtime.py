# -*- coding: utf-8 -*-
"""Actual SessionQuestCommandsMixin payout across all 385 authored quests,
using a real private SQLite account and inert notification/EXP sinks.
Does not claim network NPC or combat-side effects.
"""
from __future__ import annotations
import asyncio
from pathlib import Path
import tempfile
from types import SimpleNamespace


def run():
    import server
    from storage.database import Database
    from core.classes_skills import CLASSES, RACES
    from player.character import Character
    from player.session_mixins.quest_commands import SessionQuestCommandsMixin
    from systems.content_registry import QUESTS
    from systems.quest_reward_floor_v1020012 import quest_xp_plan

    class TestSession(SessionQuestCommandsMixin):
        account_id = 1
        def __init__(self,db,aid,character):
            self.server=SimpleNamespace(db=db,events=SimpleNamespace(publish=self._event))
            self.account_id=aid
            self.character=character
            self.messages=[]
            self.stats=[]
            self.classes=[]
            self.souls=[]
            self.tools=[]
            self.professions=[]
            self.characters=[]
            self.events=[]
        async def send(self,message,**kwargs):self.messages.append(str(message))
        async def _event(self,event):self.events.append(event)
        def cleanup_quest_map_artifacts_v0243(self,*a,**kw):pass
        def quest_turnin_npc_name_v098(self,q):return q.get('giver') or 'NPC'
        def quest_turnin_reaction_v098(self,q,name):return 'Nagroda przyznana.'
        def valid_tool_type(self,tool_type):
            from core.bootstrap_economy_professions import TOOL_PROFESSION_MAP
            return tool_type in TOOL_PROFESSION_MAP
        async def grant_profession_reward_xp(self,profession,xp,tool,xptool,**kwargs):
            self.professions.append((profession,xp,tool,xptool))
        async def grant_tool_reward_xp(self,tool,xp,**kwargs):self.tools.append((tool,xp))
        async def grant_combat_quest_stat_xp(self,amount,repeatable,**kwargs):
            self.stats.append(dict(amount));return [int(x) for x in amount.values()]
        async def grant_class_xp(self,amount,**kwargs):self.classes.append(amount)
        async def grant_soul_xp(self,amount,**kwargs):self.souls.append(amount)
        def add_character_xp_with_event(self,amount,**kwargs):
            self.characters.append(amount)
            return []
        async def record_item_collection(self,*a,**kw):pass

    async def inner():
        checks=0
        def check(condition,why):
            nonlocal checks
            if not condition:raise AssertionError(why)
            checks+=1
        with tempfile.TemporaryDirectory(prefix='sb103-quest-rewards-') as temp:
            db=Database(str(Path(temp)/'quest_rewards.sqlite'))
            aid=db.create_account('era103_reward_tester','private_pass')
            db.create_character(aid,'QuestRewardsEra103',RACES[0],CLASSES[0],{
                'nom':'Tester','gen':'Testera','dat':'Testerowi','acc':'Testera',
                'ins':'Testerem','loc':'Testerze','voc':'Testerze'})
            sess=TestSession(db,aid,Character.from_row(db.character_for_account(aid)))
            questids=[qid for qid in QUESTS if qid.startswith('v10300_')]
            check(len(questids)==385,f'Expected 385 quests, got {len(questids)}')
            for qid in sorted(questids):
                quest=QUESTS[qid]
                expected=quest_xp_plan(qid,quest)
                sess.messages.clear();sess.stats.clear();sess.classes.clear()
                sess.souls.clear();sess.tools.clear();sess.professions.clear()
                sess.characters.clear();sess.events.clear()
                previous_silver=int(sess.character.silver)
                before={iid:db.item_qty(aid,iid)+db.storage_qty(aid,'craftbox',iid)
                        for iid in quest.get('reward_items',{})}
                db.start_quest(aid,qid)
                db.set_quest_progress(aid,qid,int(quest.get('needed',1)))
                await sess.complete_quest(qid)
                result=db.quest(aid,qid)
                check(result is not None and result['status']=='completed',f'not completed {qid}: {sess.messages[-8:]}')
                check(len(sess.events)==1,f'completion event {qid}')
                check(sess.characters==[expected['character']],f'character xp {qid}: {sess.characters}')
                check(bool(sess.stats) and sess.stats[0]==expected['stats'],f'stat xp {qid}')
                check(sess.classes==([expected['class_xp']] if expected['class_xp'] else []),f'class xp {qid}')
                check(sess.souls==([expected['soul']] if expected['soul'] else []),f'soul xp {qid}')
                check(int(sess.character.silver)>=previous_silver,f'negative coins {qid}')
                if expected['profession']:
                    check(len(sess.professions)==1 and sess.professions[0][1]==expected['profession'],f'profession xp {qid}: {sess.professions}')
                elif expected['tool']:
                    check(bool(sess.tools),f'tool xp {qid}')
                for iid,quantity in (quest.get('reward_items') or {}).items():
                    after=db.item_qty(aid,iid)+db.storage_qty(aid,'craftbox',iid)
                    check(after-before[iid]>=quantity,f'item {qid} -> {iid}: before {before[iid]} after {after}')
            check(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','DB integrity')
            db.conn.close()
        return checks,len(questids)
    return asyncio.run(inner())

if __name__=='__main__':
    checks,quests=run()
    print(f'ERA 103 REWARD GATEWAY REAL SQLITE: {checks} PASS across {quests} quests',flush=True)
