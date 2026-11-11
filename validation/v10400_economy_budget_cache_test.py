# -*- coding: utf-8 -*-
"""Porownanie wyjsciowych wzorow budzetu EQ z cache. Bez serwera i SQLite."""
from __future__ import annotations
import ast
from pathlib import Path
import random
import time


def _function_from_source(name):
    path=Path(__file__).resolve().parents[1]/'systems/items_resources.py'
    tree=ast.parse(path.read_text('utf-8'))
    fn=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name==name)
    # Production function must carry a real lru_cache decorator,
    # not merely a cache used by this isolated comparison.
    assert any(isinstance(dec, ast.Call) and isinstance(dec.func,ast.Name)
               and dec.func.id=='lru_cache' for dec in fn.decorator_list),name
    fn.decorator_list=[]
    mod=ast.Module(body=[fn],type_ignores=[])
    namespace={}
    exec(compile(ast.fix_missing_locations(mod),'<porownanie-wzorow>', 'exec'),namespace)
    return namespace[name]


def run():
    from functools import lru_cache
    tests=0
    for name in ('equipment_progression_budget_v1138','equipment_defense_step_v1138'):
        original=_function_from_source(name)
        optimized=lru_cache(maxsize=2048)(original)
        rng=random.Random(104)
        cases=[None,0,1,-500,800,801,100000,1.9,'10','800']+list(range(-5,1005))+[rng.randrange(-2000,2000) for _ in range(500)]
        for item in cases:
            expected=original(item)
            actual=optimized(item)
            assert type(actual)==type(expected) and actual==expected,(name,item,expected,actual)
            tests+=1
        # Verify cache actually helps repeated, ordinary 1-800 lookup values.
        for _ in range(2):
            for val in (1,50,200,500,800):
                assert optimized(val)==original(val)
                tests+=1
        assert optimized.cache_info().hits>0
    return tests

if __name__=='__main__':print('V104 EQ CACHE:',run(),'PASS')
