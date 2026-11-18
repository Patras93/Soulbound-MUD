# -*- coding: utf-8 -*-
import unittest
from pathlib import Path

class RaceMecBoardEliza(unittest.TestCase):
    def test_v110_recommendations(self):
        from systems.v115.race_recommendations import RECOMMENDED, recommendation_for
        from core.classes_skills import race_class_recommendation_text, CLASSES
        from core.archetypes.expansion import CLASS_SPECS
        from core.archetypes.chaos import CLASS_SPECS as CHAOS
        available={name for name, *_ in CLASSES} | {name for name,*_ in CLASS_SPECS} | {name for name,*_ in CHAOS}
        self.assertEqual(len(RECOMMENDED),8)
        for race in RECOMMENDED:
            result=recommendation_for(race, available)
            self.assertEqual(len(result['classes']),3, race)
            self.assertTrue(result['reason'])
        self.assertIn('Polecane klasy:',race_class_recommendation_text('Cyborg'))
        self.assertNotIn('Mec',race_class_recommendation_text('Miedzianie'))

    def test_cyborg_mec_guard(self):
        from storage.db_accounts import DatabaseAccountsMixin
        from core.classes_skills import RACES, CLASSES
        import inspect
        body=inspect.getsource(DatabaseAccountsMixin.create_character)
        self.assertIn('mec_cyborg_only',body)
        self.assertIn('if cname == "Mec" and rname != "Cyborg"',body)
        src=Path(__file__).resolve().parents[1]
        for name in ('player/session_methods_v4200/ioauthcharacter_part03.py',
                     'player/session_mixins/io_auth_character.py'):
            self.assertIn('proposed_class[0] == "Mec"', (src/name).read_text(encoding='utf-8'))

    def test_real_sqlite_create_character_and_inventory(self):
        from tempfile import TemporaryDirectory
        from storage.database import Database
        from core.classes_skills import RACES, CLASSES
        with TemporaryDirectory(prefix='soulbound_v115_mec_') as directory:
            db=Database(str(Path(directory)/'characters.sqlite'))
            try:
                account=db.create_account('TestV115Cyborg','LongPasswordForSafeTest115!')
                cases={case:'Test' for case in ('nom','gen','dat','acc','ins','loc','voc')}
                mec=next(row for row in CLASSES if row[0]=='Mec')
                human=next(row for row in RACES if row[0]=='Człowiek')
                cyborg=next(row for row in RACES if row[0]=='Cyborg')
                with self.assertRaisesRegex(ValueError, 'mec_cyborg_only'):
                    db.create_character_for_master(account,'NotACyborgMec',human,mec,cases)
                self.assertEqual(db.conn.execute('SELECT COUNT(*) FROM characters').fetchone()[0],0)
                ident,slot=db.create_character_for_master(account,'CyborgMec',cyborg,mec,cases)
                self.assertEqual(slot,1)
                self.assertEqual(db.character_for_account(ident)['class_name'],'Mec')
                self.assertEqual(db.item_qty(ident,'moogle_board'),0)
                self.assertEqual(db.item_qty(ident,'healing_potion'),2)
                self.assertEqual(db.conn.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            finally:
                db.conn.close()

    def test_moogle_not_starting(self):
        from storage.db_accounts import DatabaseAccountsMixin
        import inspect
        src=inspect.getsource(DatabaseAccountsMixin.create_character)
        self.assertNotIn('(account_id, "moogle_board", 1)',src)
        root=Path(__file__).resolve().parents[1]
        world=(root/'world/runtime_progression.py').read_text(encoding='utf-8')
        self.assertIn('"required_character_level": 150',world)
        self.assertIn('"cyborg_board_scaling": "character_level"',world)
        market=(root/'world/uoss_superboss_world.py').read_text(encoding='utf-8')
        self.assertIn('"moogle_board",  # v115: token-priced Level 150 item',market)

    def test_eliza_distinct_spec(self):
        from systems.v115.vampire_mercenary import VAMPIRE_CONTRACT
        from systems.mercenary_taverns import MERCENARIES
        self.assertEqual(VAMPIRE_CONTRACT['name'],'Eliza')
        self.assertEqual(VAMPIRE_CONTRACT['race'],'Wampir')
        self.assertNotIn('wampir',MERCENARIES)  # Not active until class-role profiles are integrated.
        self.assertEqual(len(MERCENARIES),38)

if __name__ == '__main__': unittest.main()
