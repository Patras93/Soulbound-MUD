# -*- coding: utf-8 -*-
"""Reproduce production crash: a published v12 world revision with non-empty edits.

Uses isolated SQLite in memory and restores globally shared catalogue records;
never connects to a production database, server or network.
"""
from __future__ import annotations
import copy
import json
import sqlite3
from types import SimpleNamespace

from data.mobs import MOB_TEMPLATES
from data.rooms import ROOMS
from systems.published_world_content import PublishedWorldContent, blank


def run():
    checked = 0
    # The former smoke tests used only blank(), which did not run _remember().
    mob_id = next(key for key, meta in MOB_TEMPLATES.items() if isinstance(meta, dict) and isinstance(meta.get('damage'), (int, float)) and meta['damage'] < 10 ** 12 - 1)
    room_id = next(key for key, meta in ROOMS.items() if isinstance(meta, dict) and isinstance(meta.get('name'), str) and meta['name'])
    original_mob = copy.deepcopy(MOB_TEMPLATES[mob_id])
    original_room = copy.deepcopy(ROOMS[room_id])
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    db.execute('CREATE TABLE live_content_v1204 (id INTEGER PRIMARY KEY, revision INTEGER, payload TEXT)')
    data = blank()
    data['mob_edits'][mob_id] = {'damage': int(original_mob['damage']) + 1}
    data['room_edits'][room_id] = {'name': original_room['name'] + ' test'}
    db.execute('INSERT INTO live_content_v1204 VALUES(1,42,?)', (json.dumps(data, ensure_ascii=False),))
    original_changes = db.total_changes
    try:
        saved = PublishedWorldContent(SimpleNamespace(conn=db))
        assert saved.revision == 42
        checked += 1
        assert MOB_TEMPLATES[mob_id]['damage'] == int(original_mob['damage']) + 1
        checked += 1
        assert ROOMS[room_id]['name'] == original_room['name'] + ' test'
        checked += 1
        assert saved.active == data
        checked += 1
        assert db.total_changes == original_changes
        checked += 1
        assert not any(hasattr(saved, method) for method in ('stage_edit', 'apply', 'export', 'stage_file'))
        checked += 1
        assert not hasattr(saved, 'draft') and not hasattr(saved, 'history')
        checked += 1
        assert hasattr(saved, '_undo') and len(saved._undo) >= 2
        checked += 1
    finally:
        MOB_TEMPLATES[mob_id] = original_mob
        ROOMS[room_id] = original_room
        db.close()
    print(f'PUBLISHED PERSISTED STARTUP v114: {checked}/{checked} PASS', flush=True)


if __name__ == '__main__':
    run()
