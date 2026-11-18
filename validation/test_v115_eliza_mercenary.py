# -*- coding: utf-8 -*-
import asyncio
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

class ElizaMercenaryTest(unittest.TestCase):
    def test_existing_38_unchanged_and_eliza_available(self):
        from systems.mercenary_taverns import MERCENARIES as old, mercenary_role as old_role
        from systems.v115.vampire_mercenary import MERCENARIES, VAMPIRE_CONTRACT, mercenary_role
        self.assertEqual(len(old), 38)
        self.assertEqual(len(MERCENARIES), 39)
        self.assertNotIn('wampir', old)
        self.assertEqual({k: MERCENARIES[k] for k in old}, old)
        for name in ('Eliza', 'wampir', 'Wampirzyca'):
            self.assertEqual(mercenary_role(name), 'wampir')
        self.assertEqual(mercenary_role('Morran'), old_role('Morran'))
        self.assertEqual(VAMPIRE_CONTRACT['class'], 'Nekromanta')

    def test_tavern_price_and_skills(self):
        from systems.v115.vampire_mercenary import price_silver, mercenary_skill_lines_v12211
        from systems.mercenary_taverns import price_silver as original
        char = SimpleNamespace(shop_discount_percent=lambda: 25)
        self.assertEqual(price_silver(char, 'wampir'), 18000)
        self.assertEqual(price_silver(char, 'paladyn'), original(char, 'paladyn'))
        self.assertIn('Dotyk Nocy', '\n'.join(mercenary_skill_lines_v12211('wampir')))

    def test_active_role_uses_real_necromancer_skills(self):
        from systems.mercenary_class_skills_v11334 import available_attacks
        skills = available_attacks('wampir', 800)
        self.assertTrue(skills)
        self.assertEqual(skills[0]['id'], 'v115_eliza_dotyk_nocy')
        self.assertTrue(any(skill['id'] != skills[0]['id'] for skill in skills))
        self.assertEqual(skills[0]['kind'], 'drain')

    def test_specialist_and_voice(self):
        from systems.mercenary_specialists_v1240 import specialist_description_v1240, specialist_attack_v1240, mercenary_voice_v1270
        self.assertIn('Krwiopijczyni Nocy', specialist_description_v1240('wampir'))
        mob = SimpleNamespace(hp=40, max_hp=100)
        factor, technique, combo = specialist_attack_v1240(mob, 1, 'wampir', 'magic', 800, 100.0, boss=False)
        self.assertGreater(factor, 1.0)
        self.assertTrue(technique)
        self.assertEqual(mercenary_voice_v1270('wampir', 0), 'Noc jest po naszej stronie.')

    def test_vampiric_heal_uses_dealt_damage_and_restrictions(self):
        from systems.mercenary_specialists_v1240 import specialist_support_on_strike_v1240 as support
        victim=SimpleNamespace(current_hp=50, character=SimpleNamespace(name='Postać'), max_hp=lambda:100, skill_guard=0)
        self.assertEqual(support('wampir', victim, 0, False, False), '')
        self.assertEqual(victim.current_hp, 50)
        self.assertEqual(support('wampir', victim, 80, False, True), '')
        self.assertEqual(victim.current_hp, 50)
        message = support('wampir', victim, 80, False, False)
        self.assertIn('+8 HP', message)
        self.assertEqual(victim.current_hp, 58)
        victim.current_hp=98
        support('wampir', victim, 200, False, False)
        self.assertEqual(victim.current_hp, 100)

    def test_sqlite_contract_persists_and_three_slot_limit(self):
        from storage.db_mercenaries import DatabaseMercenariesMixin
        class DB(DatabaseMercenariesMixin):
            def __init__(self, path):
                self.conn=sqlite3.connect(path)
                self.conn.row_factory=sqlite3.Row
                self.balance=100000
                self.create_mercenary_schema()
            def master_account_for_character(self,ident): return 44
            def shared_wallet_for_master(self,ident): return (self.balance,0,0)
            def set_shared_wallet_for_master(self, ident, silver, mithril, gold, commit=False):
                self.balance=silver
        with TemporaryDirectory() as temp:
            path=str(Path(temp)/'eliza.sqlite')
            db=DB(path)
            self.assertEqual(db.hire_mercenary(7,'wampir',24000),'ok')
            self.assertEqual(db.hire_mercenary(7,'wampir',24000),'duplicate')
            self.assertEqual(db.hire_mercenary(7,'nekromanta',24000),'ok')
            self.assertEqual(db.hire_mercenary(7,'paladyn',24000),'ok')
            self.assertEqual(db.hire_mercenary(7,'mag',24000),'full')
            self.assertEqual(db.mercenary_set_tactic_v1229(7,'wampir','obrona'),'ok')
            self.assertEqual(db.mercenary_progress_v1220(7,'wampir')['specialization'],'obrona')
            db.conn.close()
            db=DB(path)
            self.assertEqual(len(db.mercenary_contracts(7)),3)
            self.assertEqual(db.mercenary_progress_v1220(7,'wampir')['specialization'],'obrona')
            self.assertEqual(db.dismiss_mercenary(7,'wampir'),1)
            self.assertEqual(len(db.mercenary_contracts(7)),2)
            db.conn.close()

    def test_tactical_memory_has_three_real_vampire_abilities(self):
        from systems.mercenary_memory_v1250 import memory_choice_v1250
        session=SimpleNamespace(server=SimpleNamespace(db=None), account_id=77)
        technique, index, key = memory_choice_v1250(session, 'wampir', 'goblin', 'Dotyk Nocy', 0)
        self.assertIn(technique, ('Dotyk Nocy', 'Szept Krwi', 'Uścisk Ciemności'))
        self.assertIn(index, (0, 1, 2))
        self.assertEqual(key[0], 'wampir')

    def test_boss_finishers_tactics_for_eliza(self):
        from systems.mercenary_specialists_v1240 import specialist_attack_v1240
        mob=SimpleNamespace(hp=10,max_hp=100)
        factor, technique, combo=specialist_attack_v1240(mob, 1, 'wampir', 'magic', 800, 100, boss=True)
        self.assertGreater(factor,1.0)
        self.assertIn('Wyczute osłabienie bossa',technique)

    def test_tavern_commands_offer_hire_status_and_dismiss_eliza(self):
        from player.session_mixins.mercenary_taverns import SessionMercenaryTavernsMixin
        from storage.db_mercenaries import DatabaseMercenariesMixin
        class DB(DatabaseMercenariesMixin):
            def __init__(self):
                self.conn=sqlite3.connect(':memory:')
                self.conn.row_factory=sqlite3.Row
                self.balance=100000
                self.create_mercenary_schema()
            def master_account_for_character(self, ident): return 3
            def shared_wallet_for_master(self, ident): return (self.balance,0,0)
            def set_shared_wallet_for_master(self, ident, silver, mithril, gold, commit=False): self.balance=silver
            def apply_shared_wallet_to_character(self, character): pass
        class Session(SessionMercenaryTavernsMixin):
            def __init__(self, db):
                self.character=SimpleNamespace(room_id='soul_mercenary_tavern_v1225', character_level=800,shop_discount_percent=lambda:0)
                self.server=SimpleNamespace(db=db)
                self.account_id=8
                self.messages=[]
            async def send(self, message): self.messages.append(message)
        db=DB(); session=Session(db)
        async def flow():
            await session.handle_mercenaries_v1170('lista')
            self.assertTrue(any('Eliza' in line for line in session.messages))
            session.messages.clear()
            await session.handle_mercenaries_v1170('wynajmij Eliza')
            self.assertTrue(any('Eliza' in line and 'dołącza' in line for line in session.messages))
            self.assertEqual(db.mercenary_contracts(8)[0]['role'],'wampir')
            await session.handle_mercenaries_v1170('taktyka Eliza obrona')
            self.assertEqual(db.mercenary_progress_v1220(8,'wampir')['specialization'],'obrona')
            await session.handle_mercenaries_v1170('status')
            self.assertTrue(any('Krwiopijczyni Nocy' in line for line in session.messages))
            self.assertTrue(any('Eliza: zatrudniona i podąża' in line for line in session.messages))
            await session.handle_mercenaries_v1170('skille Eliza')
            self.assertTrue(any('Dotyk Nocy' in line for line in session.messages))
            await session.handle_mercenaries_v1170('odeslij Eliza')
            self.assertEqual(db.mercenary_contracts(8),[])
            session.messages.clear()
            await session.handle_mercenaries_v1170('status')
            self.assertTrue(any('Eliza jest niezatrudniona' in line for line in session.messages))
        try:
            asyncio.run(flow())
        finally:
            db.conn.close()

    def test_real_damage_no_free_xp(self):
        from systems.mercenary_class_skills_v11334 import execute_attack, available_attacks
        mob = SimpleNamespace(key='eliza_test', alive=True, hp=200, room_id='room', template_id='goblin')
        char = SimpleNamespace(room_id='room', name='Tester')
        class Fake:
            def __init__(self):
                self.character=char
                self.server=SimpleNamespace(party_sessions=lambda *a,**kw:[self],world=SimpleNamespace(room_mobs=lambda room:[mob]))
                self.account_id=17
                self.combat_mob_key='eliza_test'
            async def apply_boss_defense(self, target, amount): return amount
        fake=Fake()
        result=asyncio.run(execute_attack(fake,mob,65,available_attacks('wampir',1)[0],'wampir',False))
        self.assertGreater(result[0],0)
        self.assertLess(mob.hp,200)
        self.assertEqual(result[3],1)
        self.assertEqual(result[2],())  # No kills or exp generated by this test

if __name__=='__main__': unittest.main()
