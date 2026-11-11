# -*- coding: utf-8 -*-
"""v109: dowód zgodności historycznych metod po podziale; bez produkcyjnych danych."""
from __future__ import annotations
import ast
import hashlib
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
FACADE = "exp_terrain"
PACKAGE = "exp_terrain_parts_v109"
CLASS = "SessionExpTerrainMixin"
GROUPS = {'safety': ('ExpSafetyV109Mixin', 4), 'recommendations': ('ExpRecommendationsV109Mixin', 5), 'calculation': ('ExpCalculationV109Mixin', 4), 'terrain_ui': ('ExpTerrainUIV109Mixin', 5)}
AST_SHA256 = "e8d2f89aab6e8c2c42103885ec09d0d0cfa7c9caea204e2b446ab0b69e899c52"
RETAINED_COUNT = 4


def run():
    checks=0
    p=ROOT/'player/session_mixins'/f'{FACADE}.py'
    facade_ast=ast.parse(p.read_text(encoding='utf8'))
    facade_class=next(n for n in facade_ast.body if isinstance(n,ast.ClassDef) and n.name==CLASS)
    all_methods={n.name:n for n in facade_class.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    assert len(all_methods)==RETAINED_COUNT
    checks+=RETAINED_COUNT
    for group,(klass,count) in GROUPS.items():
        path=ROOT/'player/session_mixins'/PACKAGE/f'{group}.py'
        tree=ast.parse(path.read_text(encoding='utf8'))
        c=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==klass)
        methods={n.name:n for n in c.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        assert len(methods)==count
        assert not (set(methods)&set(all_methods))
        all_methods.update(methods)
        checks+=count+1
    fp=hashlib.sha256('\n'.join(ast.dump(all_methods[m],include_attributes=False) for m in sorted(all_methods)).encode()).hexdigest()
    assert fp==AST_SHA256,('Nieoczekiwana zmiana treści historycznej metody',fp)
    checks+=len(all_methods)
    from systems.v10900_activation import REQUIRED
    for relative in [f'player/session_mixins/{PACKAGE}/{n}.py' for n in ('__init__','dependencies',*GROUPS)]:
        assert relative in REQUIRED and (ROOT/relative).is_file(),relative
        checks+=1

    from player.session_mixins.exp_terrain import SessionExpTerrainMixin
    assert len([n for n in SessionExpTerrainMixin.__mro__ if n.__name__ in [row[0] for row in GROUPS.values()]])==len(GROUPS);checks+=1
    for name in all_methods:
        assert callable(getattr(SessionExpTerrainMixin,name,None)),name
        checks+=1
    class Trial(SessionExpTerrainMixin):
        def __init__(self,level):self.character=SimpleNamespace(character_level=level)
        def combat_xp_power_v023(self):return 140
        def exp_area_target_power(self,area,room_id=None):return 150
    novice=Trial(10)
    label=novice.exp_area_safety_summary_v110016({'id':'astral'})
    assert 'NIEPOLECANY' in label;checks+=1
    assert 'Orientacyjna siła bojowa: 140' in novice.combat_power_explanation_v110016();checks+=1
    assert 'Poziom postaci: 10' in novice.combat_power_explanation_v110016();checks+=1
    advanced=Trial(180)
    assert 'raczej łatwy' in advanced.exp_area_safety_summary_v110016({'id':'astral'});checks+=1
    return checks

if __name__=='__main__':
    print(f'V109 {FACADE} MODULY:',run(),'PASS; bez sieci i produkcyjnej SQLite')
