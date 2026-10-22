# -*- coding: utf-8 -*-
"""Focused OLC15 regression on a real in-memory SQLite database.

The test does not require running a TCP server, and never touches real players.
"""
import sqlite3
from systems.live_olc18_multi_objective import (
    validate_objectives, objective_status, objective_key,
)


def run():
    from storage import db_quests
    original = db_quests.QUESTS
    checks = 0
    def check(expr):
        nonlocal checks
        assert expr, f'OLC15 test failed on check #{checks + 1}'
        checks += 1
    try:
        objs, total = validate_objectives(
            {'kill':{'bandit':2}, 'collect':{'iron_ore':3}, 'talk':['elder']},
            {'bandit'}, {'iron_ore'}, {'elder'},
        )
        check(total == 6)
        check(len(objs) == 3)
        check(objective_key('kill','bandit') != objective_key('talk','bandit'))
        bad = [
            {}, {'kill': {'bandit':1}},
            {'kill':{'missing':1}, 'talk':['elder']},
            {'kill':{'bandit':0},'collect':{'iron_ore':1}},
            {'kill':{'bandit':True},'collect':{'iron_ore':1}},
            {'kill':{'bandit':1},'talk':['missing']},
            {'kill':{'bandit':1},'talk':['elder','elder']},
            {'kill':{'bandit':1},'collect':{'iron_ore':'3'}},
            {'kill':{'bandit':1},'collect':{'iron_ore':1},'code':'print(1)'},
        ]
        for b in bad:
            try:
                validate_objectives(b, {'bandit'},{'iron_ore'},{'elder'})
            except ValueError:
                check(True)
            else:
                check(False)
        from types import SimpleNamespace
        from systems.live_olc18_multi_objective import describe_goals
        active={'quests':{'live_demo':{'kind':'multi_objective','objectives':objs}},
                'quest_edits':{}}
        draft={'quests':{'live_demo':{'kind':'multi_objective',
                    'objectives':{'kill':{'bandit':5},'talk':['elder']}}},
                'quest_edits':{}}
        service=SimpleNamespace(active=active,draft=draft)
        before=repr(service.active)+repr(service.draft)
        preview=describe_goals(service,'live_demo',{})
        check('Aktualnie:' in preview and 'Po zmianie:' in preview)
        check('WYMAGA ZATWIERDZENIA' in preview)
        check(before == repr(service.active)+repr(service.draft))
        try:
            describe_goals(service,'missing',{})
            check(False)
        except ValueError:
            check(True)
        class DB(db_quests.DatabaseQuestMixin):
            pass
        db=DB()
        db.conn=sqlite3.connect(':memory:')
        db.conn.row_factory=sqlite3.Row
        db.conn.executescript('''
           CREATE TABLE quests(account_id INTEGER,quest_id TEXT,status TEXT,
               progress INTEGER DEFAULT 0,completed_at INTEGER DEFAULT 0,
               completion_count INTEGER DEFAULT 0,
               PRIMARY KEY(account_id,quest_id));
           CREATE TABLE quest_resource_progress_v0929(account_id INTEGER,
               quest_id TEXT,target_id TEXT,progress INTEGER,
               PRIMARY KEY(account_id,quest_id,target_id));
        ''')
        qid='live_bandit_multi'
        db_quests.QUESTS={qid:{'kind':'multi_objective','objectives':objs,'needed':total}}
        db.start_quest(1,qid)
        db.start_quest(2,qid)
        state=lambda acc,stock: objective_status(db,acc,qid,objs,lambda k:stock)
        check(state(1,0)[:3]==(0,6,False))
        check(db.increment_multi_objective_v1800(1,'kill','bandit',aliases=['bandit','other']))
        check(state(1,0)[0] == 1)
        check(state(2,0)[0] == 0)
        check(len(db.increment_multi_objective_v1800(1,'kill','bandit',aliases=['bandit'])) == 1)
        check(db.increment_multi_objective_v1800(1,'kill','bandit') == [])
        check(state(1,0)[0] == 2)
        check(len(db.increment_multi_objective_v1800(1,'talk','elder')) == 1)
        check(db.increment_multi_objective_v1800(1,'talk','elder') == [])
        check(state(1,0)[:3] == (3,6,False))
        check(state(1,2)[:3] == (5,6,False))
        check(state(1,3)[:3] == (6,6,True))
        check(state(1,9)[0] == 6)
        check(state(2,3)[:3] == (3,6,False))
        check(db.increment_multi_objective_v1800(1,'kill','other') == [])
        check(db.increment_multi_objective_v1800(1,'talk','not_elder') == [])
        check(db.increment_multi_objective_v1800(1,'kill','bandit',amount=0) == [])
        # A repeated quest resets event counters by the existing native code.
        db.restart_quest(1,qid)
        check(state(1,3)[:3] == (3,6,False))
        db.increment_multi_objective_v1800(1,'kill','bandit')
        db.abandon_quest(1,qid)
        check(db.increment_multi_objective_v1800(1,'kill','bandit') == [])
        check(db.conn.execute('SELECT COUNT(*) c FROM quest_resource_progress_v0929 WHERE account_id=1').fetchone()['c'] == 0)
        # Exercise the actual game turn-in method with controlled player stock.
        import asyncio
        from types import SimpleNamespace
        from player.session_mixins import quest_turnin as turnin
        previous = getattr(turnin, 'QUESTS', None)
        turnin.QUESTS = {qid: {'name':'Patrol i dostawa',
            'kind':'multi_objective','needed':6,'objectives':objs}}
        class Session(turnin.SessionQuestTurninMixin):
            def __init__(self):
                self.account_id = 1
                self.server = SimpleNamespace(db=db)
                self.stock = 3
                self.messages = []
                self.completed = []
                self.consumed = []
            async def send(self, line):
                self.messages.append(line)
            async def complete_quest(self, quest_id):
                self.completed.append(quest_id)
                db.complete_quest(self.account_id, quest_id)
            def validate_quest_rewards_v1106(self, quest_id, quest):
                return []
            def multi_objective_status_v1800(self, quest_id):
                return objective_status(db,self.account_id,quest_id,objs,lambda _:self.stock)
            def quest_crafted_item_have_v0333(self, item_id):
                return self.stock
            def consume_quest_crafted_items_v0333(self, item_id, quantity):
                if self.stock < quantity:
                    return False
                self.stock -= quantity
                self.consumed.append((item_id,quantity))
                return True
        try:
            db.restart_quest(1,qid)
            session=Session()
            asyncio.run(session.handle_quest_interaction(qid))
            check(not session.completed and session.stock == 3)
            db.increment_multi_objective_v1800(1,'kill','bandit')
            db.increment_multi_objective_v1800(1,'kill','bandit')
            asyncio.run(session.handle_quest_interaction(qid))
            check(not session.completed and session.stock == 3)
            db.increment_multi_objective_v1800(1,'talk','elder')
            session.stock = 2
            asyncio.run(session.handle_quest_interaction(qid))
            check(not session.completed and session.stock == 2)
            session.stock = 3
            asyncio.run(session.handle_quest_interaction(qid))
            check(session.completed == [qid])
            check(session.consumed == [('iron_ore',3)] and session.stock == 0)
            check(db.quest(1,qid)['status'] == 'completed')
        finally:
            if previous is None:
                delattr(turnin,'QUESTS')
            else:
                turnin.QUESTS = previous
        db.conn.close()
    finally:
        db_quests.QUESTS = original
    return checks

if __name__ == '__main__':
    print('V18.00.0 MULTI OBJECTIVE:', run(), 'PASS')
