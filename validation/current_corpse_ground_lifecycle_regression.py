# -*- coding: utf-8 -*-
"""Real-code lifecycle regression for corpses, ground drops and live mob views."""
import asyncio
import time
import unittest
from types import SimpleNamespace

from data.items import ITEMS
from data.mobs import MOB_TEMPLATES
from player.session_mixins.collection_loot_records import SessionCollectionLootRecordsMixin
from world.world_state import CorpseState, GroundLootState, MobState, World
from core.bootstrap_economy_professions import CORPSE_LIFETIME_SECONDS, GROUND_LOOT_LIFETIME_SECONDS


class FakeDB:
    def __init__(self):
        self.inventory = {}

    def add_item(self, account_id, item_id, quantity):
        key = (account_id, item_id)
        self.inventory[key] = self.inventory.get(key, 0) + quantity


class FakePlayer(SessionCollectionLootRecordsMixin):
    def __init__(self, world, db, account_id=1):
        self.server = SimpleNamespace(world=world, db=db)
        self.character = SimpleNamespace(room_id='test_room')
        self.account_id = account_id
        self.messages = []
        self.collections = []

    async def send(self, text, **kwargs):
        self.messages.append(text)

    async def record_item_collection(self, item_id, source, announce=True):
        self.collections.append((item_id, source))

    def loot_message_allowed(self, item_id):
        return True


class TestGroundLifecycle(unittest.TestCase):
    def setUp(self):
        self.w = World.__new__(World)
        self.w.mobs = {}
        self.w.corpses = {}
        self.w.corpse_counter = 0
        self.w.ground_loot = {}
        self.w.ground_loot_counter = 0
        self.w._last_refresh_at = 0.0
        self.w._refresh_min_interval = 0.0
        self.w._last_live_counts = {}
        self.w._last_live_by_room = {}
        self.item = next(iter(ITEMS))

    def create_corpse(self, name, items, expired_ago):
        now = time.time()
        key = f'corpse:{len(self.w.corpses)+1}'
        corpse = CorpseState(key, 'test_room', name, 'test_mob',
                            list(items), now-CORPSE_LIFETIME_SECONDS-expired_ago,
                            now-expired_ago)
        self.w.corpses[key] = corpse
        return corpse

    def test_corpse_kept_until_expiry(self):
        corpse = self.create_corpse('Upior', [self.item], -150)
        self.assertEqual(len(self.w.room_corpses('test_room')), 1)
        self.assertFalse(self.w.room_ground_loot('test_room'))
        self.assertEqual(corpse.items, [self.item])

    def test_decay_preserves_items_on_ground_then_expires(self):
        corpse = self.create_corpse('Upior', [self.item, self.item], 2)
        self.w.refresh(force=True)
        self.assertFalse(self.w.room_corpses('test_room'))
        self.assertEqual(len(self.w.room_ground_loot('test_room')), 2)
        self.assertEqual(corpse.items, [])
        self.assertEqual([x.mob_name for x in self.w.room_ground_loot('test_room')], ['Upior']*2)
        for drop in self.w.ground_loot.values():
            drop.expires_at = time.time()-1
        self.w.refresh(force=True)
        self.assertFalse(self.w.room_ground_loot('test_room'))

    def test_idle_server_does_not_revive_expired_loot(self):
        self.create_corpse('Upior', [self.item], GROUND_LOOT_LIFETIME_SECONDS+10)
        self.w.refresh(force=True)
        self.assertFalse(self.w.room_corpses('test_room'))
        self.assertFalse(self.w.room_ground_loot('test_room'))

    def test_single_claim_no_duplication_and_duplicates_separate(self):
        self.create_corpse('Potwor', [self.item, self.item], 2)
        self.w.refresh(force=True)
        a = FakePlayer(self.w, FakeDB(), 1)
        b = FakePlayer(self.w, a.server.db, 2)
        async def execute():
            await a.take_ground_loot('1')
            await a.take_ground_loot('1')
            await b.take_ground_loot('1')
            await a.take_ground_loot('1')
        asyncio.run(execute())
        self.assertEqual(a.server.db.inventory, {(1, self.item): 2})
        self.assertFalse(self.w.room_ground_loot('test_room'))
        self.assertEqual(len(a.collections), 2)
        self.assertEqual(len(b.collections), 0)

    def test_ground_names_and_numbered_selectors(self):
        self.create_corpse('Potwor', [self.item, self.item], 2)
        self.w.refresh(force=True)
        name = ITEMS[self.item]['name']
        self.assertEqual(self.w.find_ground_loot('test_room', '2').key, 'ground:2')
        self.assertEqual(self.w.find_ground_loot('test_room', '2.'+name).key, 'ground:2')
        self.assertEqual(self.w.find_ground_loot('other_room', '1'), None)

    def test_dead_mob_disappears_immediately_without_erasing_corpse(self):
        template_id = next(t for t in MOB_TEMPLATES if isinstance(MOB_TEMPLATES[t], dict)
                           and MOB_TEMPLATES[t].get('max_hp'))
        mob = MobState(key='test_mob:1', room_id='test_room', template_id=template_id,
                       hp=5, respawn_at=time.time()+120)
        self.w.mobs[mob.key] = mob
        self.w._last_live_counts = {'test_room': 1}
        self.w._last_live_by_room = {'test_room': (mob,)}
        corpse = self.create_corpse('Potwor', [self.item], -1)
        self.w.hide_defeated_mob(mob)
        self.assertEqual(mob.hp, 0)
        self.assertFalse(mob.alive)
        self.assertFalse(self.w.room_mobs('test_room'))
        self.assertEqual(self.w.room_corpses('test_room'), [corpse])

    def test_take_all_ground(self):
        self.create_corpse('Potwor', [self.item, self.item], 2)
        self.w.refresh(force=True)
        a = FakePlayer(self.w, FakeDB(), 1)
        asyncio.run(a.take_ground_loot('wszystko'))
        self.assertEqual(a.server.db.inventory[(1,self.item)],2)
        self.assertFalse(self.w.room_ground_loot('test_room'))


    def test_room_look_wrapper_preserves_native_look_and_displays_ground(self):
        # Execute the REAL assembled Session.look AST with a synthetic native
        # look implementation; no authenticated player/production DB involved.
        import ast
        from pathlib import Path
        source=Path(__file__).resolve().parents[1] / 'player/session.py'
        session=next(n for n in ast.parse(source.read_text(encoding='utf-8')).body
                     if isinstance(n, ast.ClassDef) and n.name == 'Session')
        method=next(n for n in session.body if isinstance(n, ast.AsyncFunctionDef)
                    and n.name == 'look')
        events=[]
        async def original(self, query=''):
            events.append(('native',query))
        async def display():
            events.append(('ground',None))
        namespace={'SessionPerceptionMapsMixin':type('Native',(),{'look':original})}
        code=ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[]))
        exec(compile(code,str(source),'exec'),namespace)
        current=[object()]
        actor=SimpleNamespace(character=SimpleNamespace(room_id='test_room'),
             server=SimpleNamespace(world=SimpleNamespace(room_ground_loot=lambda room:current)),
             show_ground_loot=display)
        asyncio.run(namespace['look'](actor,''))
        self.assertEqual(events,[('native',''),('ground',None)])
        events.clear()
        asyncio.run(namespace['look'](actor,'upior'))
        self.assertEqual(events,[('native','upior')])
        events.clear()
        current.clear()
        asyncio.run(namespace['look'](actor,''))
        self.assertEqual(events,[('native','')])


if __name__ == '__main__':
    unittest.main()
