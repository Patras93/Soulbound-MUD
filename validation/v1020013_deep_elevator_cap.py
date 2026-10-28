# -*- coding: utf-8 -*-
"""v102.00.13: Deep route safety and effective x2 Multi Cap on real SQLite fixtures.

No file edits, game networking or live player state.
"""
import ast
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from systems.multi_cap_v23215 import (
    multi_cap_experience_v23215, multi_cap_calculation_v23217,
    multi_cap_level_value_v23217,
)
from systems.live_olc22_state import WORLD_OVERRIDES
from systems.experience_bank_v2011 import banked_experience_v2011
from systems.experience_cap_v2009 import experience_cap_v2009
from validation.v23215_multi_cap import TestDB

_ROOT = Path(__file__).resolve().parents[1]
_ENTRY = 'uoss_deep_dungeon_entry_v11331'
_FLOOR0 = 'uoss_deep_dungeon_floor_0_v11331'


def _extract_method(part, name, scope):
    p = _ROOT / ('player/session_methods_v4200/guidenavigation_part%02d.py' % part)
    tree = ast.parse(p.read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
    code = compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(p), 'exec')
    exec(code, scope)
    return scope[name]


def run():
    checks = 0
    from core.mines_threat import GUIDE_DESTINATION_ALIASES
    from world.uoss_superboss_world import uoss_deep_dungeon_floor_number_v11331
    import unicodedata
    def norm(value):
        value = str(value or '').lower().replace('ł', 'l')
        value = unicodedata.normalize('NFKD',value)
        return ' '.join(re.sub('[^a-z0-9 ]+', ' ', ''.join(c for c in value if not unicodedata.combining(c))).split())

    scope = {
        're': re,
        'GUIDE_DESTINATION_ALIASES': GUIDE_DESTINATION_ALIASES,
        'uoss_deep_dungeon_floor_number_v11331': uoss_deep_dungeon_floor_number_v11331,
        'crypt_floor_number': lambda rid: None,
        'astral_floor_number': lambda rid: None,
        'mine_floor_number': lambda rid: None,
        'mythic_crypt_floor_number': lambda rid: None,
        'mythic_astral_floor_number': lambda rid: None,
        'giant_fortress_floor_number': lambda rid: None,
        'profession_dungeon_floor': lambda rid: (None, None),
    }
    aliases = ('deep','deep dungeon','uoss deep dungeon','deep dungeon winda',
               'deep winda','deep 0','deep dungeon 0',
               'deep dungeon floor 0','deep dungeon pietro 0',
               'floor 0 deep dungeon','deep dungeon floor zero')
    for q in aliases:
        assert GUIDE_DESTINATION_ALIASES.get(q) == _ENTRY, q
        checks += 1
    # Use extracted actual navigation logic with minimal room stubs to avoid
    # loading hundreds of unrelated world catalogs in this focused test.
    scope['ROOMS'] = {
        _ENTRY: {'name':'Deep Dungeon — Winda','zone':'UOSS Deep Dungeon','exits':{}},
        _FLOOR0: {'name':'Deep Dungeon — Floor 0','zone':'UOSS Deep Dungeon','exits':{}},
        'uoss_deep_dungeon_floor_1_v11331': {'name':'Deep Dungeon, piętro 1','zone':'UOSS Deep Dungeon','exits':{}},
        'uoss_deep_dungeon_floor_25_v11331': {'name':'Deep Dungeon, piętro 25','zone':'UOSS Deep Dungeon','exits':{}},
        'deep_grove': {'name':'Głębia Gaju','zone':'Las','exits':{}},
    }
    scope.update({'MINE_MIN_FLOOR':1, 'ASTRAL_MIN_FLOOR':1,
                  'mine_floor_id':lambda x: 'mine_floor_'+str(x)})
    safe=_extract_method(2, 'guide_exploration_safe_target',scope)
    for floor in (_FLOOR0,'uoss_deep_dungeon_floor_1_v11331','uoss_deep_dungeon_floor_25_v11331',
                  'uoss_deep_dungeon_floor_1000_v11331'):
        assert safe(None,floor) == _ENTRY, floor
        checks += 1
    assert safe(None,_ENTRY) == _ENTRY; checks+=1
    assert safe(None,'deep_grove') == 'deep_grove';checks+=1
    find=_extract_method(1,'find_room_matches',scope)
    class Navigator:
        normalize_room_query = staticmethod(norm)
        room_search_aliases = lambda self, rid, room: {norm(room['name']), norm(rid)}
        guide_exploration_safe_target = lambda self, rid: safe(None,rid)
        rooms_in_exact_zone = lambda self, query: [rid for rid, room in scope['ROOMS'].items() if norm(room['zone'])==norm(query)]
        def find_room_matches(self,q):return find(self,q)
    nav=Navigator()
    for q in aliases + ('deep dungeon 1','deep dungeon pietro 25','deep dungeon floor 1000'):
        assert nav.find_room_matches(q) == [_ENTRY], q
        checks += 1
    assert [nav.guide_exploration_safe_target(room) for room in nav.find_room_matches('deep dungeon floor 25')] == [_ENTRY]
    checks+=1
    assert all(nav.guide_exploration_safe_target(room)==_ENTRY for room in nav.find_room_matches('uoss deep dungeon'))
    checks+=1
    # Boss unlock remains a separate explicit manual command, not an alias.
    assert all('deepelevator' not in q for q in aliases);checks+=1
    return checks


def check_cap():
    checks = 0
    db = TestDB()
    try:
        with patch.dict(WORLD_OVERRIDES, {}, clear=True):
            base = multi_cap_experience_v23215(db.conn,1)
            assert base == 11000; checks+=1
            assert multi_cap_experience_v23215(db.conn,2) is None;checks+=1
            result=multi_cap_calculation_v23217(db.conn,1)
            assert result[0] == sum(result[3].values());checks+=1
            assert result[3]['statystyki'] == 6000 and all(v == 1000 for k,v in result[3].items() if v>0 and k!='statystyki');checks+=1
            assert experience_cap_v2009('character',1)==1000;checks+=1
            for level in (1,10,800,801,3000):
                assert experience_cap_v2009('stat',level) == 2 * multi_cap_level_value_v23217(level)
                checks+=1
            assert banked_experience_v2011(db,1,50_000,'character',1)==base;checks+=1
            assert db.experience_bank_rows_v2011(1)==[('character','',50_000-base)];checks+=1
            assert banked_experience_v2011(db,1,1,'character',1)==2;checks+=1
            with patch.dict(WORLD_OVERRIDES,{'multi_cap_bonus_percent':150},clear=True):
                assert multi_cap_experience_v23215(db.conn,1)==16500;checks+=1
            with patch.dict(WORLD_OVERRIDES,{'multi_cap_category_bonus':{'statystyki':200}},clear=True):
                assert multi_cap_experience_v23215(db.conn,1)==17000;checks+=1
        return checks
    finally:
        db.conn.close()


if __name__=='__main__':
    print('DEEP ELEVATOR + MULTI CAP x2 v102.00.13:',run()+check_cap(),'checks PASS',flush=True)
