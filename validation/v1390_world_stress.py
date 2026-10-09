# -*- coding: utf-8 -*-
"""Four simulated players against real Soulbound persistence and encounter math.

No sockets or production accounts are accessed. Requires the usual world bootstrap
(import server) before a fresh Database can be opened. This is a regression and
bounded synthetic stress test, NOT a claim about Railway network latency.
"""
from __future__ import annotations

import asyncio
import os
import sqlite3
import statistics
import tempfile
import time
from pathlib import Path


def run_stress_v1390(*, players: int = 4, rounds: int = 80) -> dict:
    if not (1 <= players <= 4 and 1 <= rounds <= 500):
        raise ValueError("test boundary: 1–4 players, 1–500 rounds")
    from core.classes_skills import CLASSES, RACES
    from core.progression_resources import character_xp_to_next
    from systems.adaptive_combat import (adaptive_target_max_hp_v11330,
                                         adaptive_reward_multiplier_v11330)
    from systems.dungeon_experience_v1285 import dungeon_recipient_xp_v1286
    from storage.database import Database

    failures: list[str] = []
    checks = 0
    timings_ms: list[float] = []
    op_count = 0
    ids: list[int] = []
    def verify(ok, description):
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(description)

    with tempfile.TemporaryDirectory(prefix='soulbound-v1390-stress-') as directory:
        path = os.path.join(directory, 'stress.sqlite')
        db = Database(path)
        try:
            for index in range(players):
                aid = db.create_account(f'stresstest_{index}', 'synthetic_only_not_live')
                name = f'Stresstest{index}'
                cases = dict.fromkeys(('nom', 'gen', 'dat', 'acc', 'ins', 'loc', 'voc'), name)
                db.create_character(aid, name, RACES[0], CLASSES[0], cases)
                db.ensure_profession(aid, 'Wędkarstwo')
                db.ensure_profession(aid, 'Górnictwo')
                ids.append(aid)
            baseline_items = {aid: db.item_qty(aid, 'healing_potion') for aid in ids}
            baseline_progress = {aid: db.class_progress_row(aid, CLASSES[0][0]) for aid in ids}
            class_before = {aid: (int(x['level']), int(x['xp'])) for aid, x in baseline_progress.items()}
            loops_completed = [0] * players
            # Same DB object and interleaved event-loop workloads as the production
            # asyncio server; NOT four independent SQLite writer threads.
            async def actor(index):
                nonlocal op_count
                aid = ids[index]
                for step in range(rounds):
                    tick = time.perf_counter()
                    # Periodic award and crafting-resource operations via real APIs.
                    db.add_item(aid, 'healing_potion', 2)
                    verify(db.remove_item(aid, 'healing_potion', 1),
                           f'player {index} inventory removal at {step}')
                    db.add_storage_item(aid, 'bag', 'iron_ore', 3)
                    verify(db.remove_storage_item(aid, 'bag', 'iron_ore', 1),
                           f'player {index} ore bag removal at {step}')
                    fishing = db.profession(aid, 'Wędkarstwo')
                    db.save_profession(aid, 'Wędkarstwo', int(fishing['level']),
                                       int(fishing['xp']) + 25, int(fishing['actions']) + 1)
                    mining = db.profession(aid, 'Górnictwo')
                    db.save_profession(aid, 'Górnictwo', int(mining['level']),
                                       int(mining['xp']) + 40, int(mining['actions']) + 1)
                    # Test-only invocation through the storage facade; do not add a
                    # production bypass around player XP reward caps.
                    getattr(db, 'add_class_mastery_xp')(aid, CLASSES[0][0], 1)
                    timings_ms.append((time.perf_counter() - tick) * 1000)
                    loops_completed[index] += 1
                    op_count += 7
                    await asyncio.sleep(0)
            t0 = time.perf_counter()
            async def drive():
                await asyncio.gather(*(actor(i) for i in range(players)))
            asyncio.run(drive())
            elapsed = time.perf_counter() - t0
            for index, aid in enumerate(ids):
                verify(loops_completed[index] == rounds, f'player {index} interrupted')
                verify(db.item_qty(aid, 'healing_potion') == baseline_items[aid] + rounds,
                       f'player {index} item count')
                verify(db.storage_qty(aid, 'bag', 'iron_ore') == 2 * rounds,
                       f'player {index} mining inventory')
                verify(int(db.profession(aid, 'Wędkarstwo')['xp']) == 25 * rounds,
                       f'player {index} fishing XP')
                verify(int(db.profession(aid, 'Górnictwo')['xp']) == 40 * rounds,
                       f'player {index} mining XP')
                verify(int(db.profession(aid, 'Wędkarstwo')['actions']) == rounds,
                       f'player {index} fishing actions')
                verify(int(db.profession(aid, 'Górnictwo')['actions']) == rounds,
                       f'player {index} mining actions')
                row = db.class_progress_row(aid, CLASSES[0][0])
                before_lvl, before_xp = class_before[aid]
                verify((int(row['level']), int(row['xp'])) == (before_lvl, before_xp + rounds),
                       f'player {index} class XP')
            verify(db.conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok',
                   'SQLite integrity before close')
        finally:
            db.conn.close()
        # Re-open a second, independent connection to prove on-disk persistence.
        with sqlite3.connect(path) as conn:
            verify(conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok',
                   'SQLite integrity after restart')
            for index, aid in enumerate(ids):
                verify(conn.execute('SELECT quantity FROM inventory WHERE account_id=? '
                                    'AND item_id=?', (aid, 'healing_potion')).fetchone()[0]
                       == baseline_items[aid] + rounds, f'player {index} relog inventory')
                verify(conn.execute('SELECT xp FROM professions WHERE account_id=? '
                                    'AND profession=?', (aid, 'Wędkarstwo')).fetchone()[0]
                       == 25 * rounds, f'player {index} relog fishing')
        # Stress adaptive math for 1–4 players, 0–12 mercenaries and
        # 4 encounter tiers, without making any balancing changes.
        for party_size in range(1, 5):
            for mercenaries in (0, 4, 12):
                dps = 100000 * party_size + 65000 * mercenaries
                for rank in ('normal', 'elite', 'boss', 'world_boss'):
                    hp = adaptive_target_max_hp_v11330(100000, dps, {'rank': rank})
                    multiplier = adaptive_reward_multiplier_v11330(100000, hp)
                    verify(hp >= 100000 and multiplier >= 1, f'combat {party_size}/{mercenaries}/{rank}')
                    if mercenaries:
                        lesser_hp = adaptive_target_max_hp_v11330(
                            100000, 100000 * party_size, {'rank': rank})
                        verify(hp >= lesser_hp, f'mercenary not counted {party_size}/{mercenaries}/{rank}')
        for level in (1, 50, 100, 150, 400, 600, 799):
            for floor in (10, 100, 600, 800):
                xp = dungeon_recipient_xp_v1286(
                    {'crypt_floor': floor, 'crypt_boss': False}, 'character', 10**30,
                    level, combat_multiplier=1.75, downstream_multiplier=4)
                verify(0 < xp * 4 <= character_xp_to_next(level) * 0.42 + 4,
                       f'excessive XP level={level}/floor={floor}')
    metrics = {
        'players': players, 'rounds_per_player': rounds,
        'simulated_operations': op_count, 'checks': checks, 'failures': failures,
        'errors': len(failures), 'elapsed_seconds': round(elapsed, 3),
        'ops_per_second': round(op_count / max(elapsed, 0.0001), 1),
        'mean_actor_batch_ms': round(statistics.mean(timings_ms), 3),
        'p95_actor_batch_ms': round(sorted(timings_ms)[int((len(timings_ms)-1)*0.95)], 3),
        'max_actor_batch_ms': round(max(timings_ms), 3),
        'scope': '4 virtual asyncio actors; disposable real SQLite; no live TCP clients',
    }
    return metrics


if __name__ == '__main__':
    import socket
    # Follow the release bootstrap order; never start the external service.
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        os.environ['SOULBOUND_PORT'] = str(probe.getsockname()[1])
        os.environ['SOULBOUND_HOST'] = '127.0.0.1'
    import server  # noqa: F401
    import json
    result = run_stress_v1390(rounds=int(os.environ.get('SOULBOUND_STRESS_ROUNDS', '250')))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result['errors']:
        raise SystemExit(1)
