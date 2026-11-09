# -*- coding: utf-8 -*-
"""v109: porownanie metod world events z niezmieniona v108 + test MRO.

Bez dostepu do bazy graczy, plikow produkcyjnych, portu 4000 i GitHub.
"""
from __future__ import annotations
import ast
import asyncio
import hashlib
from pathlib import Path
from types import SimpleNamespace
import time

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_AST_SHA256 = '25f248755ccd9fa1b9bd304912128425491cb61ee1e149557ff42a618faacc54'
PARTS = (
    ('frontier_weather', 'FrontierWeatherV109Mixin', 8),
    ('factions', 'FactionsV109Mixin', 5),
    ('expeditions_transport', 'ExpeditionsTransportV109Mixin', 7),
    ('ascension', 'AscensionV109Mixin', 9),
    ('projects_contracts', 'ProjectsContractsV109Mixin', 9),
    ('bosses_gauntlets', 'BossesGauntletsV109Mixin', 12),
    ('artifacts', 'ArtifactsV109Mixin', 3),
    ('world_rotation', 'WorldRotationV109Mixin', 3),
)

def test():
    checks = 0
    parts = ROOT / 'player/session_mixins/world_events_parts_v109'
    assert (parts / 'dependencies.py').is_file()
    checks += 1
    facade_tree = ast.parse((ROOT / 'player/session_mixins/world_events_endgame.py').read_text('utf8'))
    facade = next(n for n in facade_tree.body if isinstance(n, ast.ClassDef) and n.name == 'SessionWorldEventsEndgameMixin')
    assert [ast.unparse(n) for n in facade.bases] == [c for _,c,_ in PARTS]
    checks += len(PARTS)
    methods = {}
    classes = []
    for filename, classname, count in PARTS:
        tree = ast.parse((parts / (filename + '.py')).read_text('utf8'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        assert cls.name == classname and not cls.bases
        one = {n.name: n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        assert len(one) == count
        assert not (methods.keys() & one.keys())
        methods.update(one)
        classes.append(cls)
        checks += count + 2
    remains = {n.name: n for n in facade.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert set(remains) == {'show_ascension_v021'}
    assert not (methods.keys() & remains.keys())
    methods.update(remains)
    assert len(methods) == 57
    checks += 3
    digest = hashlib.sha256(('\n'.join(name+'='+ast.dump(methods[name],include_attributes=False) for name in sorted(methods))).encode()).hexdigest()
    assert digest == EXPECTED_AST_SHA256, (digest, 'legacy v108 methods changed')
    checks += len(methods)

    # Izolowany kod oryginalnych metod, bez importowania silnika i danych graczy.
    scope = {
        'CLASS_MASTERY_MAX_LEVEL': 400,
        'V016_FACTIONS': {'test': {'name':'Testowa frakcja','desc':'Opis'}} ,
        'v0160_faction_rank': lambda r: 'I' if r else '0',
        'normalize_lookup_text': lambda t: str(t).lower().strip(),
        'v0130_frontier_room_identity': lambda room: None,
        'v0150_time_state': lambda: {'label':'Dzien'},
        'v0180_season_state': lambda: {'expires_at':time.time()+3600,'label':'Test','desc':'Bez blokad.'},
        'MOB_TEMPLATES': {'mega':{'v020_megadungeon_boss':True}, 'ordinary':{}},
        'time': time,
    }
    module = ast.fix_missing_locations(ast.Module(body=[*classes,facade], type_ignores=[]))
    exec(compile(module, 'v109-isolated-world-endgame', 'exec'), scope)
    klass = scope['SessionWorldEventsEndgameMixin']
    assert len(klass.__mro__) == len(PARTS)+2
    checks += 1
    for name in methods:
        assert callable(getattr(klass, name, None)), name
        checks += 1
    class DB:
        def __init__(self): self.ascensions=[{'rank':2,'track':'class:Wojownik'}, {'rank':4,'track':'class:Mag'}, {'rank':11,'track':'soul'}]
        def ascension_rows_v021(self,aid): assert aid==9; return self.ascensions
        @property
        def conn(self): return self
        def execute(self,query,values): assert values==(9,); return self
        def fetchone(self): return {'mx':400}
        def faction_reputation_v016(self,aid,name): assert aid==9 and name=='test'; return 7
    class World:
        def __init__(self): self.count=0; self.mobs={'mob':SimpleNamespace(alive=True,room_id='r1',template_id='mega')}
        def refresh(self): self.count+=1
    class Session(klass):
        def __init__(self):
            self.account_id=9; self.messages=[]; self.character=SimpleNamespace(room_id='r1')
            self.server=SimpleNamespace(db=DB(),world=World())
        async def send(self,message):self.messages.append(str(message))
    user = Session()
    assert user.v0210_total_ascension_rank()==6
    checks += 1
    assert user.v0210_any_class_at_400() is True
    checks += 1
    assert user.v0200_live_blocking_boss('r1',mega=True).template_id=='mega'
    checks += 1
    assert user.v0200_live_blocking_boss('r2',mega=True) is None
    checks += 1
    asyncio.run(user.show_weather_v015())
    assert len(user.messages)==1 and 'Dzien' in user.messages[0]
    checks += 1
    user.messages.clear()
    asyncio.run(user.show_factions_v016('test'))
    assert len(user.messages)==2 and '7 pkt' in user.messages[1]
    checks += 1
    user.messages.clear()
    asyncio.run(user.show_season_v018())
    assert len(user.messages)==2 and user.messages[0].startswith('SEZON')
    checks += 1
    print(f'V109 WORLD ENDGAME MODULES: {checks} PASS; 57 method AST hash v108; isolated MRO and methods; no prod DB',flush=True)
    return checks

if __name__ == '__main__':
    test()
