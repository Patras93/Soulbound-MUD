# -*- coding: utf-8 -*-
"""Regression: checkpoint chest stands next to its live boss; key stays in corpse.

Exercises the actual World, boss-room lookup and Session helper with an isolated
fake collection ledger. Never modifies players' real SQLite database.
"""
from datetime import datetime, timezone
from types import SimpleNamespace

from player.session_mixins.admin_tools import SessionAdminToolsMixin
from world.magitek_infinite import boss_floor_identity


def check_chest_lifecycle_v1288(ns, world, room_map):
    errors = []
    checks = 0
    rooms = ns['ROOMS']
    templates = ns['MOB_TEMPLATES']

    for (kind, floor), boss_room in sorted(room_map.items()):
        if kind not in ('crypt', 'mythic_crypt'):
            continue
        room_prefix = 'crypt_floor_' if kind == 'crypt' else 'mythic_crypt_floor_'
        landing = room_prefix + str(floor)
        boss = next((m for m in world.mobs.values()
                     if m.room_id == boss_room
                     and boss_floor_identity(templates.get(m.template_id, {})) == (kind, floor)), None)
        if boss is None:
            errors.append(f'{kind}/{floor}: boss missing from real room')
            continue
        chest_spec = ns['_boss_floor_chest_spec'](boss_room)
        checks += 1
        if not chest_spec or tuple(chest_spec[:2]) != (kind, floor):
            errors.append(f'{kind}/{floor}: chest missing while boss alive')

        # Guarantee key is inside the boss corpse rather than player inventory.
        key_id = ns['boss_floor_key_id'](kind, floor)
        corpse = world.create_corpse(boss)
        checks += 1
        if corpse is None or key_id not in corpse.items:
            errors.append(f'{kind}/{floor}: key missing from boss corpse')
        if corpse is not None:
            world.corpses.pop(corpse.key, None)

        state_id = ns['boss_floor_chest_state_id'](kind, floor)
        class Ledger:
            def __init__(self):
                self.opened = True
                self.when = '2026-01-01 12:00:00'
                self.resets = 0
            def collection_entry_ids(self, account_id, category):
                return {state_id} if self.opened else set()
            def collection_entry_discovered_at(self, account_id, category, entry_id):
                return self.when
            def remove_collection_entry(self, account_id, category, entry_id):
                self.opened = False
                self.resets += 1

        db = Ledger()
        test_session = SessionAdminToolsMixin()
        test_session.character = SimpleNamespace(room_id=boss_room)
        test_session.account_id = -123
        test_session.server = SimpleNamespace(db=db, world=world)
        # An old claim marker cannot hide a chest once the boss has respawned.
        checks += 1
        if test_session.boss_floor_chest_here() is None or db.resets != 1:
            errors.append(f'{kind}/{floor}: stale opened state did not recover')

        # Once opened in the current cycle, the chest must disappear.
        db.opened = True
        db.when = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        checks += 1
        if test_session.boss_floor_chest_here() is not None:
            errors.append(f'{kind}/{floor}: opened chest remains visible')

        # Killing the boss never reveals a SPENT chest; real victory code resets
        # the marker, and the next respawn resets it automatically as well.
        original_alive, original_respawn = boss.alive, boss.respawn_at
        try:
            boss.alive = False
            boss.respawn_at = world.boss_chest_world_started_v1288 + 30
            checks += 1
            if test_session.boss_floor_chest_here() is not None:
                errors.append(f'{kind}/{floor}: spent chest visible while boss dead')
            boss.alive = True
            checks += 1
            if test_session.boss_floor_chest_here() is None:
                errors.append(f'{kind}/{floor}: chest failed to return after respawn')
        finally:
            boss.alive = original_alive
            boss.respawn_at = original_respawn
            world._last_refresh_at = 0

        # Old floors lacking the v1.28.6 marker must recover boss room anyway.
        landing_meta, boss_meta = rooms[landing], rooms[boss_room]
        marker = landing_meta.pop('v1286_boss_chest_room', None)
        parent = boss_meta.pop('v1286_boss_chest_parent', None)
        try:
            checks += 1
            if ns['boss_floor_chest_room_id'](kind, floor) != boss_room:
                errors.append(f'{kind}/{floor}: historical floor lookup broken')
        finally:
            if marker is not None:
                landing_meta['v1286_boss_chest_room'] = marker
            if parent is not None:
                boss_meta['v1286_boss_chest_parent'] = parent

    return {'checks': checks, 'error_count': len(errors), 'errors': errors}
