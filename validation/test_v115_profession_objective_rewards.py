# -*- coding: utf-8 -*-
"""Real SQLite tests: v115 authored-region profession milestones."""
import asyncio
import inspect
import sqlite3
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from validation.test_v10400_atomic_live_character_xp import fixture
from systems.v115.playable_regions import room_id
from systems.v115.high_level_world import REGIONS
from systems.v115.objective_progress import total
from systems.v115.profession_objective_bridge import (
    record_v115_profession_action, announce_v115_profession_action,
)

REGION = REGIONS[0].key


class ProfessionObjectives(unittest.TestCase):
    def setUp(self):
        self.db, self.character = fixture()
        self.character.room_id = room_id(REGION, 0, 0)
        self.messages = []
        self.errors = []
        async def send(msg): self.messages.append(msg)
        self.session = SimpleNamespace(
            account_id=1, character=self.character,
            send=send,
            server=SimpleNamespace(db=self.db,
                report_runtime_error=lambda error, **kwargs: self.errors.append(error)),
        )

    def tearDown(self):
        self.db.conn.close()

    def wallet(self):
        return self.db.conn.execute('SELECT silver FROM account_wallet').fetchone()[0]

    def test_craft_award_real_wallet(self):
        result = record_v115_profession_action(self.session, 'craft_item', 2)
        self.assertEqual(result[0], 1)
        self.assertGreater(result[1] + result[2], 0)
        self.assertEqual(self.wallet(), self.character.silver)
        self.assertGreater(self.wallet(), 100)
        self.assertEqual(total(self.db.conn, 1, REGION, 'craft_item'), 2)

    def test_gather_award_real_wallet(self):
        record_v115_profession_action(self.session, 'collect_resource', 5)
        self.assertEqual(total(self.db.conn, 1, REGION, 'collect_resource'), 5)
        self.assertGreater(self.wallet(), 100)

    def test_same_event_cannot_pay_twice(self):
        first = record_v115_profession_action(self.session, 'craft_item', 3, event_id='native-action-5')
        wallet = self.wallet()
        again = record_v115_profession_action(self.session, 'craft_item', 3, event_id='native-action-5')
        self.assertEqual(first[0], 1)
        self.assertEqual(again, (0,0,0,0))
        self.assertEqual(total(self.db.conn,1,REGION,'craft_item'),3)
        self.assertEqual(self.wallet(),wallet)

    def test_repeat_real_action_is_counted(self):
        record_v115_profession_action(self.session, 'craft_item', 1)
        record_v115_profession_action(self.session, 'craft_item', 1)
        self.assertEqual(total(self.db.conn,1,REGION,'craft_item'),2)

    def test_old_room_no_effect_no_schema(self):
        self.character.room_id = 'graveyard'
        self.assertEqual(record_v115_profession_action(self.session, 'craft_item', 2),(0,0,0,0))
        self.assertFalse(self.db.conn.execute("SELECT name FROM sqlite_master WHERE name='v115_objective_events'").fetchone())

    def test_region_validation_does_not_trust_malformed_room(self):
        self.character.room_id = REGION+'_p_99_99'
        with patch('systems.v115.profession_objective_bridge.ROOMS', {self.character.room_id: {'v115_region_key':REGION}}):
            with self.assertRaises(ValueError):
                record_v115_profession_action(self.session,'craft_item',1)

    def test_reject_wrong_account(self):
        self.character.account_id = 2
        with self.assertRaises(ValueError):
            record_v115_profession_action(self.session, 'collect_resource',1)
        self.assertEqual(self.wallet(),100)

    def test_reject_bad_quantities_and_objectives(self):
        for qty in (0,-1,1.5,True):
            with self.assertRaises(ValueError):
                record_v115_profession_action(self.session,'craft_item',qty)
        with self.assertRaises(ValueError):
            record_v115_profession_action(self.session,'defeat_enemy',1)

    def test_large_batch_bounded(self):
        record_v115_profession_action(self.session, 'craft_item', 100000)
        self.assertEqual(total(self.db.conn,1,REGION,'craft_item'),10000)

    def test_failure_restores_wallet_and_objectives(self):
        self.db.conn.execute("CREATE TRIGGER forbid_wallet BEFORE UPDATE ON account_wallet BEGIN SELECT RAISE(ABORT,'refused'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            record_v115_profession_action(self.session,'craft_item',2)
        self.assertEqual(total(self.db.conn,1,REGION,'craft_item'),0)
        self.assertEqual(self.wallet(),100)
        self.assertEqual(self.character.silver,100)
        self.db.conn.execute('DROP TRIGGER forbid_wallet')
        record_v115_profession_action(self.session,'craft_item',2)
        self.assertGreater(self.wallet(),100)

    def test_optional_failure_does_not_interrupt_native_action(self):
        self.db.conn.execute("CREATE TRIGGER forbid_wallet BEFORE UPDATE ON account_wallet BEGIN SELECT RAISE(ABORT,'refused'); END")
        asyncio.run(announce_v115_profession_action(self.session,'craft_item',2))
        self.assertEqual(len(self.errors),1)
        self.assertEqual(self.character.silver,100)
        self.assertEqual(self.messages,[])

    def test_success_sends_short_text_without_sound(self):
        asyncio.run(announce_v115_profession_action(self.session,'collect_resource',5))
        self.assertEqual(len(self.messages),1)
        self.assertIn('Profesje v115:',self.messages[0])
        import systems.v115.profession_objective_bridge as b
        self.assertNotIn('sound_events',inspect.getsource(b))

    def test_native_hooks_in_correct_places(self):
        root = Path(__file__).resolve().parents[1]
        craft = (root/'player/session_mixins/quest_progress.py').read_text('utf8')
        self.assertIn("await announce_v115_profession_action(self, 'craft_item', int(amount))",craft)
        self.assertLess(craft.index('await self.announce_crafting_order_progress_v0600(item_id, amount)'),craft.index("await announce_v115_profession_action(self, 'craft_item', int(amount))"))
        gather = (root/'events/listeners/gathering_progression.py').read_text('utf8')
        self.assertIn("await announce_v115_profession_action(session, 'collect_resource', qty)", gather)
        self.assertLess(gather.index('await session.advance_class_guild_quest_v11132("gather", qty)'),gather.index("await announce_v115_profession_action(session, 'collect_resource', qty)"))

    def test_real_native_resource_event_listener(self):
        from unittest.mock import AsyncMock
        # Load the actual listener function without unittest discover's
        # validation/events.py shadowing the runtime 'events' package.
        import ast
        root=Path(__file__).resolve().parents[1]
        file=root/'events/listeners/gathering_progression.py'
        tree=ast.parse(file.read_text('utf8'))
        method=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef)
                    and n.name=='credit_resource_progression')
        namespace={'ResourceGatheredEvent':object}
        exec(compile(ast.Module(body=[method],type_ignores=[]),str(file),'exec'),namespace)
        credit_resource_progression=namespace['credit_resource_progression']
        for attr in ('announce_resource_quest_progress',
                     'announce_collect_category_quest_progress',
                     'advance_bounty', 'advance_legendary_contract_v022',
                     'advance_dynamic_world_quest_v015',
                     'add_faction_reputation_v016', 'advance_class_guild_quest_v11132'):
            setattr(self.session, attr, AsyncMock())
        self.db.add_lifetime_stat = lambda *args, **kwargs: None
        event = SimpleNamespace(
            session=self.session, action='woodcutting', item_id='wood',
            quantity=5, category='wood', bounty_kind='wood',
            dynamic_kind='wood', legendary_kind='gather', faction='green_path',
            faction_reason='woodcutting', lifetime_stat='wood_gathered',
            distinct_category=None, distinct_item_id=None,
            secondary_category=None,rare_achievement=None,rare_lifetime_stat=None)
        asyncio.run(credit_resource_progression(event))
        self.assertEqual(total(self.db.conn,1,REGION,'collect_resource'),5)
        self.assertEqual(self.wallet(),self.character.silver)
        self.assertGreater(self.wallet(),100)
        self.assertEqual(len(self.messages),1)

    def test_real_native_craft_completion_callback(self):
        from unittest.mock import AsyncMock
        # Execute the exact authored async callback without importing
        # unrelated world catalog modules inside unittest discovery.
        import ast
        root=Path(__file__).resolve().parents[1]
        file=root/'player/session_mixins/quest_progress.py'
        tree=ast.parse(file.read_text('utf8'))
        klass=next(n for n in tree.body if isinstance(n,ast.ClassDef)
                   and n.name=='SessionQuestProgressMixin')
        method=next(n for n in klass.body if isinstance(n,ast.AsyncFunctionDef)
                    and n.name=='announce_craft_quest_progress')
        namespace={}
        exec(compile(ast.Module(body=[method],type_ignores=[]),str(file),'exec'),namespace)
        callback=namespace['announce_craft_quest_progress']
        self.db.increment_craft_quest = lambda *args: []
        self.session.announce_crafting_order_progress_v0600 = AsyncMock()
        asyncio.run(callback(self.session,'real_crafted_output',2))
        self.assertEqual(total(self.db.conn,1,REGION,'craft_item'),2)
        self.assertEqual(self.wallet(),self.character.silver)
        self.assertGreater(self.wallet(),100)
        self.session.announce_crafting_order_progress_v0600.assert_awaited_once_with('real_crafted_output',2)

if __name__=='__main__': unittest.main()
