"""Current mixins work without compatibility namespace seeding or a database."""
from __future__ import annotations

from pathlib import Path
import sys
import sqlite3
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from player.session_mixins import rest_mana, session_runtime_state, tech_crafting, milestone, quest_turnin
from storage.database import _DeferredCommitConnection


def finish(coroutine):
    """Complete database-free coroutines without opening an event-loop socket."""
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    finally:
        coroutine.close()
    raise AssertionError("Fixture unexpectedly suspended on external I/O")


class RestSession(rest_mana.SessionRestManaMixin):
    def __init__(self, hp=50, mana=10, max_mana=50):
        self.character = object()
        self.closed = self.resting = self.moving = self.guiding = False
        self.combat_mob_key = None
        self.current_hp, self.current_mana = hp, mana
        self.max_hp = lambda: 100
        self.max_mana = lambda: max_mana
        self.send = AsyncMock()
        for name in ("fishing", "mining", "woodcutting", "herbalism"):
            setattr(self, "auto_" + name, False)
            setattr(self, "auto_" + name + "_task", None)


class ExplicitMixinTests(unittest.TestCase):
    def quest_session(self, stock):
        session = quest_turnin.SessionQuestTurninMixin()
        conn = _DeferredCommitConnection(sqlite3.connect(":memory:"))
        self.addCleanup(conn.close)
        conn.execute("CREATE TABLE inventory (id TEXT PRIMARY KEY, qty INTEGER)")
        conn.executemany("INSERT INTO inventory VALUES (?,?)", stock.items())
        conn.commit()

        def consume(account, ids, qty, container, *, purpose):
            self.assertEqual(purpose, "quest_turnin")
            item_id = ids[0]
            row = conn.execute("SELECT qty FROM inventory WHERE id=?", (item_id,)).fetchone()
            if not row or row[0] < qty:
                return False
            conn.execute("UPDATE inventory SET qty=qty-? WHERE id=?", (qty, item_id))
            conn.commit()
            return True

        db = SimpleNamespace(conn=conn, consume_items_across_storage_and_inventory=consume)
        session.server, session.account_id = SimpleNamespace(db=db), 7
        return session, conn

    def test_quest_batch_failure_restores_consumed_items(self):
        session, conn = self.quest_session({"a": 2, "b": 0})
        requirements = [(["a"], 1, "resource_ids", None), (["b"], 1, "resource_ids", None)]
        self.assertFalse(session.consume_quest_items_batch_v10800(requirements))
        self.assertEqual(dict(conn.execute("SELECT id,qty FROM inventory")), {"a": 2, "b": 0})

    def test_quest_batch_success_commits_both_items(self):
        session, conn = self.quest_session({"a": 2, "b": 2})
        requirements = [(["a"], 1, "resource_ids", None), (["b"], 1, "resource_ids", None)]
        self.assertTrue(session.consume_quest_items_batch_v10800(requirements))
        self.assertEqual(dict(conn.execute("SELECT id,qty FROM inventory")), {"a": 1, "b": 1})
        self.assertFalse(conn.in_transaction)

    def test_rest_percentage_and_message(self):
        session = RestSession()
        with patch.object(rest_mana, "superboss_healing_blocked_v11179", return_value=False):
            self.assertTrue(finish(session.rest_tick()))
        self.assertEqual((session.current_hp, session.current_mana), (60, 15))
        session.send.assert_awaited_once_with("Regeneracja: HP 60 z 100. Mana 15 z 50.")

    def test_standing_percentage_is_silent_and_caps(self):
        session = RestSession(hp=99, mana=49)
        with patch.object(rest_mana, "superboss_healing_blocked_v11179", return_value=False):
            self.assertFalse(finish(session.standing_regen_tick_v1124()))
        self.assertEqual((session.current_hp, session.current_mana), (100, 50))
        session.send.assert_not_awaited()

    def test_boss_blocks_health_but_not_mana(self):
        session = RestSession()
        with patch.object(rest_mana, "superboss_healing_blocked_v11179", return_value=True):
            finish(session.rest_tick())
        self.assertEqual((session.current_hp, session.current_mana), (50, 15))

    def test_standing_disabled_in_combat_and_when_gathering(self):
        session = RestSession()
        session.combat_mob_key = "mob"
        self.assertFalse(finish(session.standing_regen_tick_v1124()))
        session.combat_mob_key = None
        session.auto_mining = True
        self.assertFalse(session.standing_regen_allowed_v1124())
        self.assertEqual((session.current_hp, session.current_mana), (50, 10))

    def test_mana_less_character(self):
        session = RestSession(mana=20, max_mana=0)
        with patch.object(rest_mana, "superboss_healing_blocked_v11179", return_value=False):
            finish(session.rest_tick())
        self.assertEqual(session.current_mana, 0)
        session.send.assert_awaited_once_with("Regeneracja: HP 60 z 100.")

    def test_commands_use_normalized_text(self):
        session = RestSession()
        session.start_rest = AsyncMock()
        finish(session.handle_rest("  MANA-REGEN  "))
        session.start_rest.assert_awaited_once_with()
        session.stop_rest = AsyncMock(return_value=True)
        finish(session.handle_mana_command("  PRZERWIJ  "))
        session.stop_rest.assert_awaited_once_with(announce=True)

    def test_session_initialization_and_independent_cooldowns(self):
        session = session_runtime_state.SessionRuntimeStateMixin(None, None, None)
        self.assertEqual(session.input_encoding, "utf-8")
        self.assertEqual(session.history_buffers["combat"].maxlen, 100)
        self.assertEqual(session.start_skill_cooldown_v0364("a", 4, now=10), 14)
        session.start_skill_cooldown_v0364("b", 9, now=10)
        self.assertEqual(session.skill_cooldown_remaining_v0364("a", now=12), 2)
        self.assertEqual(session.skill_cooldown_remaining_v0364("b", now=12), 7)

    def test_double_xp_and_safe_integer_boundary(self):
        session = session_runtime_state.SessionRuntimeStateMixin(None, None, None)
        self.assertEqual(session.apply_double_xp(12, now=0), 24)
        self.assertEqual(session.apply_double_xp(12, now=1800), 12)
        self.assertEqual(session.apply_double_xp(-1, now=0), 0)
        self.assertEqual(session.apply_double_xp(8_000_000_000_000_000_000, now=0),
                         8_000_000_000_000_000_000)

    def test_tech_salvage_consumes_once_and_awards_recipe(self):
        session = tech_crafting.SessionTechCraftingV03111Mixin()
        storage = Mock()
        session.server = SimpleNamespace(db=storage)
        session.account_id = 7
        session.send = AsyncMock()
        session.available_recipe_item = Mock(return_value=1)
        session.consume_recipe_item = Mock(return_value=True)
        session.grant_profession_progress = Mock(return_value=([], None, None))
        items = {"component": {"name": "Component", "required_character_level": 200},
                 "part": {"name": "Part"}}
        with patch.object(tech_crafting, "ITEMS", items), \
                patch.object(tech_crafting, "TECH_SALVAGE_RECIPES", {"component": {"part": 2}}):
            finish(session.tech_salvage_v03111("Component"))
        session.consume_recipe_item.assert_called_once_with("component", 1)
        storage.add_storage_item.assert_called_once_with(7, "craftbox", "part", 2)
        session.grant_profession_progress.assert_called_once_with(
            "Kowalstwo", 32, "crafting", 0, content_level=200)

    def test_milestone_equipment_marks(self):
        session = milestone.SessionMilestoneV0320Mixin()
        db = Mock()
        db.equipment.return_value = [{"item_id": "a"}, {"item_id": "b"}]
        db.tech_set_mark_v0320.side_effect = [2, 3]
        session.server, session.account_id = SimpleNamespace(db=db), 7
        with patch.object(milestone, "TECH_SET_ITEMS_V03114", {"set": ["a", "b"]}):
            self.assertAlmostEqual(session.tech_set_equipped_mark_multiplier_v0320(), 1.0175)


if __name__ == "__main__":
    unittest.main()
