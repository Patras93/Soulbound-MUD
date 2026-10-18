# -*- coding: utf-8 -*-
"""Regression: EP automatically on authored landmarks, never every ordinary room."""
from __future__ import annotations
from validation.v4200_virtual_source import read_actual_refactored_source_v4200 as _sb420_view
import ast
import asyncio
from contextlib import closing
from pathlib import Path
import sqlite3
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_regression():
    """v10.00.2: only selected landmarks give automatic EP; claims idempotent."""
    from systems.exploration_point_values_v2322 import zone_explorer_points_v2322, room_explorer_points_v2322, is_city_ep_excluded_v1002
    progress = (ROOT / 'player/session_mixins/exploration_progress.py').read_text('utf-8')
    profession = (ROOT / 'player/session_mixins/exploration_professions.py').read_text('utf-8')
    source = ast.parse(progress)
    cls = next(n for n in source.body if isinstance(n, ast.ClassDef) and n.name=='SessionExplorationProgressMixin')
    walk = next(n for n in cls.body if isinstance(n, ast.AsyncFunctionDef) and n.name=='discover_room')
    claim = next(n for n in cls.body if isinstance(n, ast.AsyncFunctionDef) and n.name=='claim_landmark_ep_v1002')
    wcalls = [n.func.attr for n in ast.walk(walk) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
    assert 'mark_room_discovered_with_points_v2322' in wcalls
    assert 'claim_landmark_ep_v1002' in wcalls
    assert "if room_meta.get('v1000_landmark') and not is_city_ep_excluded_v1002(room_meta):" in progress
    ccalls = [n.func.attr for n in ast.walk(claim) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
    assert 'claim_landmark_ep_v1002' in ccalls and 'multi_cap_v23215' in ccalls
    assert 'await self.claim_landmark_ep_v1002(room_id)' not in profession
    assert is_city_ep_excluded_v1002({'zone':'Miasto Dusz'})
    assert room_explorer_points_v2322({'zone':'Miasto Dusz','v1000_landmark':True,'exploration_ep':30}) == 0
    assert room_explorer_points_v2322({'zone':'Dolina Przedświtu','v1000_landmark':True,'exploration_ep':5}) == 5
    assert zone_explorer_points_v2322(('A','B'), {'A'}, {'A':0}, {'A':{},'B':{}}) == (0,0)
    assert zone_explorer_points_v2322(('A',), set(), {}, {'A':{'v1000_landmark':True,'level':100}}) == (0,2)
    dbsource = (ROOT / 'storage/methods_v4200/databaseworld_part01.py').read_text('utf-8')
    tree=ast.parse(dbsource)
    method=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='claim_landmark_ep_v1002')
    code=ast.Module(body=[method],type_ignores=[])
    ast.fix_missing_locations(code)
    ns={}
    exec(compile(code,dbsource,'exec'),ns)
    with closing(sqlite3.connect(':memory:')) as connection:
        connection.executescript("""CREATE TABLE exploration_rooms(account_id INTEGER,room_id TEXT,PRIMARY KEY(account_id,room_id));
        CREATE TABLE exploration_room_points_v2322(account_id INTEGER,room_id TEXT,ep_points INTEGER,PRIMARY KEY(account_id,room_id));
        CREATE TABLE exploration_zero_ep_v1002(account_id INTEGER,room_id TEXT,PRIMARY KEY(account_id,room_id));
        CREATE TABLE lifetime_statistics(account_id INTEGER,stat_key TEXT,value INTEGER,updated_at TEXT,PRIMARY KEY(account_id,stat_key));""")
        fake=SimpleNamespace(conn=connection)
        assert ns['claim_landmark_ep_v1002'](fake,1,'A',3) is True
        assert ns['claim_landmark_ep_v1002'](fake,1,'A',3) is False
        assert ns['claim_landmark_ep_v1002'](fake,2,'A',3) is True
        assert connection.execute("SELECT value FROM lifetime_statistics WHERE account_id=1 AND stat_key='explorer_points'").fetchone()[0] == 3
    return 10

if __name__=='__main__':
    print(f'AUTO EP v10.00.2: {run_regression()} checks PASS')
