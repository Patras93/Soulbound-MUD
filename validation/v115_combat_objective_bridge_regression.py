# -*- coding: utf-8 -*-
import sqlite3, unittest
from types import SimpleNamespace
from systems.v115.combat_objective_bridge import record_v115_victory
from systems.v115.objective_progress import total
from systems.v115.high_level_world import REGIONS

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(':memory:')
        self.region=REGIONS[0].key
        a=SimpleNamespace(account_id=1,character=SimpleNamespace(room_id='r'))
        b=SimpleNamespace(account_id=2,character=SimpleNamespace(room_id='r'))
        self.members=[a,b]
        self.server=SimpleNamespace(db=SimpleNamespace(conn=self.conn),party_sessions=lambda *a,**kw:self.members)
        a.server=self.server
        self.session=a
        self.mob=SimpleNamespace(alive=False)
    def tearDown(self):self.conn.close()
    def test_legacy_noop(self):
        self.assertEqual(record_v115_victory(self.session,self.mob,{},event_id='x'),0)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM sqlite_master WHERE name LIKE 'v115_objective_%'").fetchone()[0],0)
    def test_enemy_party(self):
        self.assertEqual(record_v115_victory(self.session,self.mob,{'v115_region_key':self.region},event_id='e1'),2)
        for aid in (1,2):self.assertEqual(total(self.conn,aid,self.region,'defeat_enemy'),1)
    def test_retry_deduplicated(self):
        d={'v115_region_key':self.region}
        self.assertEqual(record_v115_victory(self.session,self.mob,d,event_id='retry'),2)
        self.assertEqual(record_v115_victory(self.session,self.mob,d,event_id='retry'),0)
    def test_boss_both_metrics(self):
        self.assertEqual(record_v115_victory(self.session,self.mob,{'v115_region_key':self.region,'boss':True},event_id='boss'),4)
        self.assertEqual(total(self.conn,1,self.region,'defeat_boss'),1)
    def test_invalid_region_fail_closed(self):
        with self.assertRaises(ValueError):record_v115_victory(self.session,self.mob,{'v115_region_key':'BAD'},event_id='b')
    def test_living_mob_rejected(self):
        with self.assertRaises(ValueError):record_v115_victory(self.session,SimpleNamespace(alive=True),{'v115_region_key':self.region},event_id='b')
    def test_other_room_excluded(self):
        self.members[1].character.room_id='elsewhere'
        self.assertEqual(record_v115_victory(self.session,self.mob,{'v115_region_key':self.region},event_id='other'),1)
    def test_soundpack_not_imported(self):
        import inspect
        import systems.v115.combat_objective_bridge as bridge
        self.assertNotIn('sound_events',inspect.getsource(bridge))
    def test_transaction_rollback(self):
        self.conn.execute('BEGIN')
        record_v115_victory(self.session,self.mob,{'v115_region_key':self.region},event_id='abort')
        self.conn.rollback()
        self.assertEqual(total(self.conn,1,self.region,'defeat_enemy'),0)

if __name__=='__main__':unittest.main()
