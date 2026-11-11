# -*- coding: utf-8 -*-
"""Regression: mining progress and a miner's position survive an app restart."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3

from storage.db_world import DatabaseWorldMixin


def audit_mine_persistence_v1250():
    checks = 0

    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    # The server's startup path must only inspect mine state; no deletion or teleport.
    source = Path(__file__).resolve().parents[1].joinpath('server/mud_server.py').read_text(encoding='utf-8')
    check('self.db.mine_startup_status()' in source, 'server must read mine status')
    check('reset_mine_for_server_start' not in source, 'server must not reset mine')
    check(not hasattr(DatabaseWorldMixin, 'reset_mine_for_server_start'), 'destructive mine reset must not exist')

    with TemporaryDirectory() as tmp:
        path = str(Path(tmp) / 'world.db')
        def connect():
            c = sqlite3.connect(path)
            c.row_factory = sqlite3.Row
            return c
        c = connect()
        c.executescript('''
          CREATE TABLE mine_progress(account_id INTEGER PRIMARY KEY,
            max_floor_unlocked INTEGER, wall_hits INTEGER, wall_required_hits INTEGER);
          CREATE TABLE characters(account_id INTEGER PRIMARY KEY, room_id TEXT);
          INSERT INTO mine_progress VALUES(12,143,29,55);
          INSERT INTO mine_progress VALUES(13,22,7,45);
          INSERT INTO characters VALUES(12,'mine_floor_143_r4');
          INSERT INTO characters VALUES(13,'mine_floor_22');
        ''')
        db = DatabaseWorldMixin()
        db.conn = c
        check(db.mine_startup_status()['max_floor_unlocked'] == 143, 'status shows depth')
        check(db.mine_startup_status()['characters_inside_mine'] == 2, 'status shows miners')
        c.close()  # simulate process stopping and SQLite reopening on persistent volume
        c = connect()
        db.conn = c
        check(db.mine_startup_status()['persistent'], 'boot reports persistence')
        row = c.execute('SELECT * FROM mine_progress WHERE account_id=12').fetchone()
        check((row['max_floor_unlocked'],row['wall_hits'],row['wall_required_hits']) == (143,29,55), 'wall progress survives deploy')
        row = c.execute('SELECT * FROM mine_progress WHERE account_id=13').fetchone()
        check((row['max_floor_unlocked'],row['wall_hits'],row['wall_required_hits']) == (22,7,45), 'second miner not reset')
        row = c.execute('SELECT room_id FROM characters WHERE account_id=12').fetchone()
        check(row['room_id'] == 'mine_floor_143_r4', 'miner keeps exact subroom')
        row = c.execute('SELECT room_id FROM characters WHERE account_id=13').fetchone()
        check(row['room_id'] == 'mine_floor_22', 'second miner keeps room')
        progress = db.mine_progress(12)
        check(progress['max_floor_unlocked'] == 143 and progress['wall_hits'] == 29,
              'game reads preserved progress after reconnect')
        check(c.execute('SELECT COUNT(*) FROM characters WHERE room_id = \'crystal_chamber\'').fetchone()[0] == 0,
              'no miners teleported')
        c.close()
    return checks


if __name__ == '__main__':
    print(f'MINE PERSISTENCE v1.25.0: {audit_mine_persistence_v1250()} checks PASS')
