# -*- coding: utf-8 -*-
"""v116.64: uncapped payouts, retired mercenaries, castable skeletal minions."""
import asyncio
import sqlite3
import unittest
from types import SimpleNamespace
from storage.db_mercenaries import DatabaseMercenariesMixin
from systems.experience_bank_v2011 import banked_experience_v2011
from player.session_mixins.no_hires_minion_spells_v11664 import SessionNoHiresMinionSpellsV11664Mixin

class MockDB(DatabaseMercenariesMixin):
    def __init__(self):
        self.conn=sqlite3.connect(':memory:')
        self.conn.row_factory=sqlite3.Row
        self.create_mercenary_schema()
        self.conn.execute('CREATE TABLE summons_v1700(account_id INTEGER,summon_type TEXT,level INTEGER,active INTEGER,hp INTEGER,max_hp INTEGER,xp INTEGER DEFAULT 0,PRIMARY KEY(account_id,summon_type))')
        self.conn.commit()
        self._retired_mercenaries_v11664=True
        self._uncapped_awards_v11664=True

class LiveActor(SessionNoHiresMinionSpellsV11664Mixin):
    def __init__(self, db, classes=('Mag',), mana=5000):
        self.server=SimpleNamespace(db=db)
        self.character=SimpleNamespace(character_level=92)
        self.account_id=1
        self.current_hp=200
        self.current_mana=mana
        self.combat_mob_key=None
        self.classes=classes
        self.sent=[]
    def active_class_names(self):return self.classes
    def max_mana(self):return 5000
    def is_downed_v0371(self):return False
    def _v1700_conn(self):return self.server.db.conn
    def _v1702_prepare_summon_lives(self, conn):pass
    def _v1710_refresh_summon_health(self, conn):pass
    def _v1806_owner_summon_level(self, kind, fallback=1):return 92
    def _v1702_summon_max_hp(self, kind, level=1):return 12345
    async def _v1701_need_mana(self, cost):
        if self.current_mana < cost:
            await self.send('Za mało many')
            return False
        return True
    async def send(self, msg):self.sent.append(str(msg))

class NoCapMercAndCast(unittest.TestCase):
    def test_retired_contracts_not_deleted_or_usable(self):
        db=MockDB()
        try:
            db.conn.execute("INSERT INTO mercenary_contracts VALUES(1,'wampir',0)")
            db.conn.commit()
            self.assertEqual(db.mercenary_contracts(1),[])
            self.assertEqual(db.hire_mercenary(1,'mag',20000),'disabled')
            self.assertEqual(db.conn.execute('SELECT COUNT(*) FROM mercenary_contracts').fetchone()[0],1)
            self.assertEqual(db.mercenary_gain_xp_v1220(1,'wampir',100)['xp'],0)
            self.assertEqual(db.conn.execute('SELECT COUNT(*) FROM mercenary_progress_v1220').fetchone()[0],0)
            db._retired_mercenaries_v11664=False
            self.assertEqual(len(db.mercenary_contracts(1)),1)
        finally:db.conn.close()

    def test_no_hires_combat_look_or_recruit(self):
        db=MockDB()
        try:
            a=LiveActor(db)
            self.assertEqual(a.nearby_mercenaries_v1226(),[])
            self.assertIsNone(a.visible_mercenary_for_look_v1226('Eliza'))
            self.assertEqual(a.adaptive_member_mercenary_dps_v1261(a),0)
            asyncio.run(a.mercenary_combat_turn_v1170(None))
            asyncio.run(a.handle_mercenaries_v1170('wynajmij Eliza'))
            self.assertTrue(any('wycofani' in s for s in a.sent))
        finally:db.conn.close()

    def test_cast_mage_and_warrior_cost_mana_without_materials(self):
        db=MockDB()
        try:
            actor=LiveActor(db)
            asyncio.run(actor.cast_minion_spell_v11664('skeletal mage'))
            self.assertEqual(actor.current_mana,4500)
            row=db.conn.execute("SELECT active,hp,level FROM summons_v1700 WHERE summon_type='mag'").fetchone()
            self.assertEqual(tuple(row),(1,12345,92))
            self.assertTrue(actor.v11664_can_use_summon('mag','Nekromanta'))
            asyncio.run(actor.cast_minion_spell_v11664('skeletal mage'))
            self.assertEqual(actor.current_mana,4500,'repeat cast never charges mana')
            asyncio.run(actor.cast_minion_spell_v11664('skeletal warrior'))
            self.assertEqual(actor.current_mana,4000)
            self.assertEqual(db.conn.execute('SELECT COUNT(*) FROM summons_v1700').fetchone()[0],2)
            asyncio.run(actor.summons_v1700('przywolaj wojownik'))
            self.assertEqual(db.conn.execute('SELECT COUNT(*) FROM summons_v1700').fetchone()[0],2)
        finally:db.conn.close()

    def test_druid_cannot_cast_skeletons_and_insufficient_mp_is_safe(self):
        db=MockDB()
        try:
            druid=LiveActor(db,('Druid',))
            asyncio.run(druid.cast_minion_spell_v11664('skeletal mage'))
            self.assertEqual(db.conn.execute('SELECT COUNT(*) FROM summons_v1700').fetchone()[0],0)
            weak=LiveActor(db,('Nekromanta',),mana=100)
            asyncio.run(weak.cast_minion_spell_v11664('skeletal warrior'))
            self.assertEqual(weak.current_mana,100)
            self.assertEqual(db.conn.execute('SELECT COUNT(*) FROM summons_v1700').fetchone()[0],0)
            self.assertFalse(druid.v11664_can_use_summon('mag','Nekromanta'))
            self.assertTrue(weak.v11664_can_use_summon('mag','Nekromanta'))
        finally:db.conn.close()

    def test_no_cap_awards_complete_and_no_bank_mutation(self):
        db=MockDB()
        try:
            before=db.conn.total_changes
            for kind in ('character','soul','stat','class','skill','profession','tool'):
                self.assertEqual(banked_experience_v2011(db,1,10**12,kind,92),10**12)
            self.assertEqual(db.conn.total_changes,before)
        finally:db.conn.close()

def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(NoCapMercAndCast)
    result=unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('v116.64 no-cap/mercenary/cast failed')
    return result.testsRun
if __name__=='__main__':
    print('NO CAP / NO HIRES / SKELETAL CAST: %s/5 PASS'%run())
