# -*- coding: utf-8 -*-
"""Real SQLite checks for v104 per-kill regular + OLC objective credit."""
import sqlite3
import copy
import unittest
from unittest.mock import patch
from storage.database import _DeferredCommitConnection
from storage.db_quests import DatabaseQuestMixin
from systems.atomic_kill_quest_progress_v10400 import (
    settle_kill_quest_progress_v10400, settle_all_kill_quests_v10400)


class DB(DatabaseQuestMixin):
    def __init__(self):
        self.conn = _DeferredCommitConnection(sqlite3.connect(':memory:'))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript('''
            CREATE TABLE quests(account_id INTEGER, quest_id TEXT,
                status TEXT, progress INTEGER, PRIMARY KEY(account_id,quest_id));
            CREATE TABLE quest_resource_progress_v0929(account_id INTEGER,
                quest_id TEXT, target_id TEXT, progress INTEGER,
                PRIMARY KEY(account_id,quest_id,target_id));
        ''')


Q={
  'goblin': {'kind':'kill', 'target':'goblin', 'needed':4},
  'tribe': {'kind':'kill', 'target':'goblin_tribe', 'needed':4},
  'all': {'kind':'kill', 'target':'*', 'needed':3},
  'saga': {'kind':'kill','target':'*','needed':3,'v800_class_saga':True},
  'olc': {'kind':'multi_objective','objectives': {'kill':{'goblin':2,'goblin_tribe':2}}},
}

class AtomicKillQuestTests(unittest.TestCase):
    def setUp(self):
        self.db = DB()
        self.patcher = patch.dict('data.quests.QUESTS',copy.deepcopy(Q),clear=True)
        self.patcher.start()
        for acc in (1,2):
            for qid in Q:
                self.db.conn.execute("INSERT INTO quests VALUES (?,?, 'active', 0)",(acc,qid))
        self.db.conn.commit()
    def tearDown(self):
        self.patcher.stop()
        self.db.conn.close()
    def progress(self,account=1):
        return dict(self.db.conn.execute('SELECT quest_id,progress FROM quests WHERE account_id=?',(account,)).fetchall())
    def resources(self,account=1):
        return [tuple(row) for row in self.db.conn.execute('SELECT quest_id,target_id,progress FROM quest_resource_progress_v0929 WHERE account_id=?',(account,)).fetchall()]
    def settle(self,account=1,aliases=('goblin','goblin_tribe')):
        return settle_kill_quest_progress_v10400(self.db,account,'goblin',aliases=aliases)

    def test_ordinary_and_wildcard_credit_once_for_multiple_aliases(self):
        simple, multi = self.settle()
        self.assertEqual({x[0] for x in simple},{'goblin','tribe','all'})
        self.assertEqual(self.progress(), {'goblin':1,'tribe':1,'all':1,'saga':0,'olc':0})
        self.assertEqual(len(multi),1)
        self.assertEqual(len(self.resources()),1)

    def test_two_kills_and_cap(self):
        for _ in range(8): self.settle()
        self.assertEqual(self.progress()['all'],3)
        self.assertEqual(self.progress()['goblin'],4)
        self.assertEqual(self.progress()['tribe'],4)
        self.assertEqual(self.resources()[0][2],2)

    def test_other_account_unchanged(self):
        self.settle(1)
        self.assertEqual(self.progress(2),{qid:0 for qid in Q})
        self.assertEqual(self.resources(2),[])

    def test_fails_second_system_and_rolls_back_regular_quests(self):
        self.db.conn.execute('''CREATE TRIGGER reject_olc BEFORE INSERT ON quest_resource_progress_v0929
           BEGIN SELECT RAISE(ABORT,'failure in olc'); END''')
        with self.assertRaises(sqlite3.IntegrityError): self.settle()
        self.assertEqual(self.progress(),{qid:0 for qid in Q})
        self.assertEqual(self.resources(),[])
        self.db.conn.execute('DROP TRIGGER reject_olc')
        self.settle()
        self.assertEqual(self.progress()['goblin'],1)

    def test_regular_failure_rolls_back_prior_aliases(self):
        self.db.conn.execute('''CREATE TRIGGER reject_last BEFORE UPDATE ON quests
          WHEN NEW.quest_id='all' BEGIN SELECT RAISE(ABORT,'last'); END''')
        with self.assertRaises(sqlite3.IntegrityError): self.settle()
        self.assertEqual(self.progress(),{qid:0 for qid in Q})
        self.assertEqual(self.resources(),[])

    def test_existing_unrelated_transaction_preserved(self):
        self.db.conn.execute("UPDATE quests SET progress=1 WHERE account_id=2 AND quest_id='all'")
        self.db.conn.execute('''CREATE TRIGGER reject_olc BEFORE INSERT ON quest_resource_progress_v0929
           BEGIN SELECT RAISE(ABORT,'failure'); END''')
        with self.assertRaises(sqlite3.IntegrityError): self.settle()
        self.assertEqual(self.progress(2)['all'],1)
        self.assertEqual(self.progress(1)['all'],0)

    def test_bad_alias_rejected_before_any_writes(self):
        for aliases in ((123,),('',),('goblin',None)):
            with self.assertRaises(ValueError): self.settle(aliases=aliases)
        self.assertEqual(self.progress(),{qid:0 for qid in Q})

    def test_corrupted_counter_no_silent_clamp(self):
        self.db.conn.execute("UPDATE quests SET progress=-5 WHERE account_id=1 AND quest_id='goblin'")
        with self.assertRaises(ValueError): self.settle()
        self.assertEqual(self.progress()['goblin'],-5)
        self.assertEqual(self.progress()['all'],0)

    def test_cap_cannot_overflow_int64(self):
        from data.quests import QUESTS
        QUESTS['goblin']['needed']=2**64
        self.db.conn.execute("UPDATE quests SET progress=? WHERE account_id=1 AND quest_id='goblin'",((1<<63)-1,))
        with self.assertRaises(OverflowError): self.settle()
        self.assertEqual(self.progress()['all'],0)

    def add_party_class(self):
        from data.quests import QUESTS
        QUESTS['saga'].update(required_class='Wojownik', v800_min_enemy_level=1,
                             v800_enemy_rank='any')
        QUESTS['party']={'kind':'party_contract','target':'boss','needed':2}
        for acc in (1,2):
            self.db.conn.execute("INSERT INTO quests VALUES (?,?, 'active', 0)", (acc,'party'))
        self.db.conn.commit()

    def test_all_four_credit_types_one_settlement(self):
        self.add_party_class()
        basic, multi, saga, party = settle_all_kill_quests_v10400(
            self.db,1,'goblin',aliases=('goblin_tribe',),
            active_classes=('Wojownik',),mob_level=100,boss=True,
            party_categories=('boss',))
        self.assertEqual(len(basic),3)
        self.assertEqual(len(multi),1)
        self.assertEqual(saga,[('saga',1)])
        self.assertEqual(party,[('party',1,2)])
        self.assertEqual(self.progress()['saga'],1)
        self.assertEqual(self.progress()['party'],1)
        self.assertEqual(self.progress(2)['party'],0)

    def test_party_failure_rolls_back_all_four(self):
        self.add_party_class()
        self.db.conn.execute("CREATE TRIGGER fail_party BEFORE UPDATE ON quests WHEN NEW.quest_id='party' BEGIN SELECT RAISE(ABORT,'party blocked'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            settle_all_kill_quests_v10400(
                self.db,1,'goblin',aliases=('goblin_tribe',),
                active_classes=('Wojownik',),mob_level=100,boss=True,
                party_categories=('boss',))
        self.assertEqual(self.progress(),{qid:0 for qid in ('goblin','tribe','all','saga','olc','party')})
        self.assertEqual(self.resources(),[])

    def test_class_failure_rolls_back_basic_and_multi(self):
        self.add_party_class()
        self.db.conn.execute("CREATE TRIGGER fail_saga BEFORE UPDATE ON quests WHEN NEW.quest_id='saga' BEGIN SELECT RAISE(ABORT,'class blocked'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            settle_all_kill_quests_v10400(
                self.db,1,'goblin',aliases=('goblin_tribe',),
                active_classes=('Wojownik',),mob_level=100,boss=True,
                party_categories=('boss',))
        self.assertEqual(self.progress()['goblin'],0)
        self.assertEqual(self.resources(),[])

    def test_no_quest_changes_no_spurious_messages(self):
        self.db.conn.execute("UPDATE quests SET status='completed' WHERE account_id=1")
        self.assertEqual(self.settle(),([],[]))


def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(AtomicKillQuestTests)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('Quest settlement regression')
    return result.testsRun

if __name__=='__main__':
    print('QUEST SETTLEMENT:',run(),'PASS')
