# -*- coding: utf-8 -*-
"""Persistent 10-direction Deep Mine test without modifying player data."""
from __future__ import annotations
import os
import sqlite3
import tempfile

from core.mine_tunnels import (
    HORIZONTAL_MINE_DIRECTIONS, mine_direction, mine_tunnel_coords,
    mine_tunnel_identity, mine_tunnel_room_id,
)
from core.progression_resources import is_mining_room, mine_floor_number
from storage.db_world import DatabaseWorldMixin


def audit_mine_directions_v1251():
    checks = 0
    def check(condition, message):
        nonlocal checks
        assert condition, message
        checks += 1

    for direction in (*HORIZONTAL_MINE_DIRECTIONS, 'up', 'down'):
        check(mine_direction(direction) == direction, f'missing direction {direction}')
    for alias, expected in [('prawo','east'), ('lewo','west'),('gora','up'), ('góra','up'),
                            ('dol','down'),('dół','down'),('polnoc','north'),('południe','south'),
                            ('ne','northeast'),('nw','northwest'),('se','southeast'),('sw','southwest')]:
        check(mine_direction(alias) == expected, f'bad alias {alias}')
    check(mine_direction('never') is None, 'unknown direction accepted')

    room_id = mine_tunnel_room_id(9, 21, -7, 4)
    check(mine_tunnel_identity(room_id) == (9,21,-7,4), 'coordinates not reversible')
    check(mine_floor_number(room_id) == 9, 'level lost in tunnel')
    check(is_mining_room(room_id), 'tunnels do not count as mine rooms')
    check(mine_tunnel_coords(room_id, 21) == (9,-7,4), 'owner did not match')
    check(mine_tunnel_coords(room_id, 22) is None, 'other owner can use tunnel')
    check(mine_tunnel_coords('mine_floor_9_r5',22) == (9,0,0), 'legacy subrooms unsupported')
    check(mine_tunnel_room_id(9,21,0,0) == 'mine_floor_9', 'old root room changed')

    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'world.sqlite3')
        def open_db():
            conn = sqlite3.connect(path)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute('CREATE TABLE IF NOT EXISTS accounts(id INTEGER PRIMARY KEY)')
            conn.execute('INSERT OR IGNORE INTO accounts VALUES (21)')
            conn.execute('INSERT OR IGNORE INTO accounts VALUES (22)')
            conn.executescript('''
            CREATE TABLE IF NOT EXISTS mine_tunnel_cells_v1251(
                account_id INTEGER NOT NULL, floor INTEGER NOT NULL, x INTEGER NOT NULL, y INTEGER NOT NULL,
                PRIMARY KEY(account_id,floor,x,y),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE);
            CREATE TABLE IF NOT EXISTS mine_tunnel_walls_v1251(
                account_id INTEGER NOT NULL, floor INTEGER NOT NULL,x INTEGER NOT NULL,y INTEGER NOT NULL,
                direction TEXT NOT NULL,hits INTEGER NOT NULL DEFAULT 0,required_hits INTEGER NOT NULL,
                PRIMARY KEY(account_id,floor,x,y,direction),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE);
            ''')
            db = DatabaseWorldMixin()
            db.conn = conn
            return db
        db = open_db()
        check(db.mine_tunnel_target_v1251(21,9,0,0,'north') is None, 'new wall open before digging')
        res=db.mine_tunnel_hit_v1251(21,9,0,0,'north')
        check((res['hits'],res['opened']) == (1,False),'hit 1 wrong')
        first_required = res['required_hits']
        check(first_required > 1, 'wall threshold invalid')
        db.conn.close()
        db = open_db()
        res=db.mine_tunnel_hit_v1251(21,9,0,0,'north')
        check((res['hits'],res['required_hits'],res['opened']) == (2,first_required,False),
              f'partial wall lost on restart: {res}')
        while not res['opened']:
            res=db.mine_tunnel_hit_v1251(21,9,0,0,'north')
        check(res['opened'] and res['new'] and res['hits']==first_required, 'wall did not open after threshold')
        check(db.mine_tunnel_target_v1251(21,9,0,0,'north') == mine_tunnel_room_id(9,21,0,1), 'north passage absent')
        check(db.mine_tunnel_target_v1251(21,9,0,1,'south') == 'mine_floor_9', 'no return to central mine')
        check(db.mine_tunnel_target_v1251(22,9,0,0,'north') is None, 'other character inherited room')
        check(db.mine_tunnel_target_v1251(21,10,0,0,'north') is None, 'tunnel leaked between floors')
        check(db.mine_tunnel_hit_v1251(21,9,0,0,'north')['new'] is False, 'already dug room excavated twice')
        for direction in HORIZONTAL_MINE_DIRECTIONS:
            check(direction in db.mine_tunnel_directions_v1251(21,9,0,0)
                  if direction == 'north' else True, f'missing open direction {direction}')
        # Branch farther on same floor, then return to its first origin.
        res={'opened':False}
        for i in range(100):
            res=db.mine_tunnel_hit_v1251(21,9,0,1,'east')
            if res['opened']:
                break
        check(res['opened'] and res['target'] == mine_tunnel_room_id(9,21,1,1), 'branch failed')
        check(db.mine_tunnel_target_v1251(21,9,1,1,'west') == mine_tunnel_room_id(9,21,0,1), 'branch return failed')
        db.conn.close()
        db=open_db()
        check(db.mine_tunnel_target_v1251(21,9,1,1,'west') == mine_tunnel_room_id(9,21,0,1), 'branch lost on reload')
        check(db.mine_tunnel_target_v1251(21,9,0,1,'south') == 'mine_floor_9', 'root route lost on reload')
        check(db.mine_tunnel_target_v1251(22,9,0,0,'north') is None, 'isolation lost on reload')
        db.conn.close()
    return checks

if __name__ == '__main__':
    print('MINE DIRECTIONS v1.25.1:', audit_mine_directions_v1251(), 'checks PASS')
