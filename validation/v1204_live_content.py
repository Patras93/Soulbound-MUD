# -*- coding: utf-8 -*-
"""Hot-reload safety regression: additive rooms/mobs, persistence and guards."""
import copy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sqlite3
import json
import tempfile
from types import SimpleNamespace

from systems.live_content_v1204 import LiveContentV1204, ROOMS, MOB_TEMPLATES, MOB_SPAWNS


def run_regression():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    db = SimpleNamespace(conn=conn)
    m = LiveContentV1204(db)
    room = 'live_test_entrance_v1204'
    mob = 'live_test_guard_v1204'
    home = 'temple_basement'
    assert home in ROOMS
    assert room not in ROOMS and mob not in MOB_TEMPLATES
    initial_spawns = set(MOB_SPAWNS)
    world = SimpleNamespace(mobs={}, _last_refresh_at=123.0)
    def register(r, t):
        scaled = f'{t}__terrain_v0362_080__world_v0384_080'
        MOB_SPAWNS.append((r, scaled))
        world.mobs[f'{r}:{scaled}'] = SimpleNamespace(room_id=r, home_room_id=r, template_id=scaled, engaged_by=None, aoe_engaged_by=None)
    world._register_runtime_spawn = register
    server = SimpleNamespace(world=world, sessions=[])
    count = 0
    try:
        m.stage_room(room, 80, 'Przedsionek Żywych Kronik', 'Suche kamienie i echo kroków.', 'Żywe Kroniki'); count += 1
        m.stage_link(home, 'northeast', room); count += 1
        m.stage_link(room, 'southwest', home); count += 1
        m.stage_mob(mob, 'Strażnik Żywych Kronik', 80, 45000, 450, 50000); count += 1
        m.stage_spawn(room, mob); count += 1
        m.stage_balance('temple_rat', 'class_xp_reward', 3750); count += 1
        before = copy.deepcopy(MOB_TEMPLATES['temple_rat'])
        res = m.apply(server, 'admin'); assert 'rewizję 1' in res; count += 1
        assert ROOMS[room]['exits']['southwest'] == home and ROOMS[home]['exits']['northeast'] == room; count += 1
        assert MOB_TEMPLATES[mob]['max_hp'] == 45000 and MOB_TEMPLATES['temple_rat']['class_xp_reward'] == 3750; count += 1
        assert (room, mob) in MOB_SPAWNS and len(world.mobs) == 1; count += 1
        assert m.revision == 1 and conn.execute('SELECT COUNT(*) FROM live_content_history_v1204').fetchone()[0] == 1; count += 1
        assert any(r == room and t.startswith(mob + '__') for r, t in MOB_SPAWNS); count += 1
        next(iter(world.mobs.values())).engaged_by = 'player'
        try:
            m.apply(server, 'admin', rollback=True)
            assert False, 'Scaled mob combat should prevent rollback'
        except ValueError as exc:
            assert 'walki' in str(exc); count += 1
        next(iter(world.mobs.values())).engaged_by = None
        # A new manager started after restart sees persisted content.
        m._remove(world)
        m = LiveContentV1204(db)
        assert room in ROOMS and mob in MOB_TEMPLATES and (room, mob) in MOB_SPAWNS; count += 1
        assert m.revision == 1 and m.active['rooms'][room]['name'] == 'Przedsionek Żywych Kronik'; count += 1
        server.sessions = [SimpleNamespace(character=SimpleNamespace(room_id=room))]
        try:
            m.apply(server, 'admin', rollback=True)
            assert False, 'Occupied room rollback must fail'
        except ValueError as exc:
            assert 'Gracz' in str(exc); count += 1
        server.sessions = []
        assert 'rewizję 2' in m.apply(server, 'admin', rollback=True); count += 1
        assert room not in ROOMS and mob not in MOB_TEMPLATES; count += 1
        assert MOB_TEMPLATES['temple_rat'] == before; count += 1
        assert (room, mob) not in MOB_SPAWNS and set(MOB_SPAWNS) == initial_spawns; count += 1
        with tempfile.TemporaryDirectory(prefix='soulbound-live-') as dirname:
            from pathlib import Path
            source = Path(dirname) / 'pakiet.json'
            source.write_text(json.dumps({'rooms': {'live_test_import_v1204': {
                'name': 'Importowana lokacja', 'desc': 'Nowa droga.', 'zone': 'Kroniki', 'generator_level': 90}},
                'links': [[home, 'northeast', 'live_test_import_v1204']]}, ensure_ascii=False), encoding='utf-8')
            assert '1 lokacji' in m.stage_file(source); count += 1
            assert 'live_test_import_v1204' in m.draft['rooms']; count += 1
            m.reset_draft()
            source.write_text('To nie jest JSON', encoding='utf-8')
            try:
                m.stage_file(source)
                assert False, 'Invalid JSON must be rejected'
            except ValueError:
                count += 1
        m.stage_room('evil_room', 1, 'Niepoprawny', 'Opis', 'Region')
        assert False, 'Non-prefixed live ID must be rejected'
    except ValueError as exc:
        assert 'live_' in str(exc)
        count += 1
    finally:
        m._remove(world)
        conn.close()
    return count

if __name__ == '__main__':
    print(f'V12.00.4 HOT RELOAD LOKACJE / POTWORY / COFANIE / SQLITE: {run_regression()} checks PASS')
