# -*- coding: utf-8 -*-
"""v109: dowód zgodności historycznych metod po podziale; bez produkcyjnych danych."""
from __future__ import annotations
import ast
import hashlib
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
FACADE = "era_sky_v1700"
PACKAGE = "sky_parts_v109"
CLASS = "SessionSkyV1700Mixin"
GROUPS = {'summon_state': ('SkySummonStateV109Mixin', 11), 'companion_healing': ('SkyCompanionHealingV109Mixin', 4), 'summon_commands': ('SkySummonCommandsV109Mixin', 5),
 'summon_specializations': ('SkySummonSpecializationsV109Mixin', 6), 'summon_combat': ('SkySummonCombatV109Mixin', 4), 'cities_classes': ('SkyCitiesClassesV109Mixin', 5)}
AST_SHA256 = "c53bd938f50d92f019d4420ef8a21ead0b7c2d65c207ed6f319d6b4074d0e9d7"
RETAINED_COUNT = 0


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

    from player.session_mixins.era_sky_v1700 import (SessionSkyV1700Mixin,SUMMONS,SUMMON_MANA,
                                                     ensure_schema,ascii_fold)
    from player.session_mixins.sky_parts_v109 import dependencies
    assert SUMMONS is dependencies.SUMMONS and SUMMON_MANA is dependencies.SUMMON_MANA;checks+=2
    assert callable(ensure_schema) and ascii_fold('ŁÓDŹ')=='lodz';checks+=2
    assert len([n for n in SessionSkyV1700Mixin.__mro__ if n.__name__ in [row[0] for row in GROUPS.values()]]) == len(GROUPS);checks+=1
    for name in all_methods:
        assert callable(getattr(SessionSkyV1700Mixin,name,None)),name
        checks+=1
    assert SessionSkyV1700Mixin.class_damage_multiplier_v1700(SimpleNamespace(class_path_v1700=lambda:'ofensywa'))==1.14;checks+=1
    assert SessionSkyV1700Mixin.class_damage_multiplier_v1700(SimpleNamespace(class_path_v1700=lambda:'obrona'))==1.0;checks+=1
    s=SimpleNamespace(server=SimpleNamespace(db=SimpleNamespace(item_qty=lambda *_:2,storage_qty=lambda *_:3)),account_id=7)
    assert SessionSkyV1700Mixin._v1700_qty(s,'przykladowy_surowiec')==5;checks+=1
    return checks

if __name__=='__main__':
    print(f'V109 {FACADE} MODULY:',run(),'PASS; bez sieci i produkcyjnej SQLite')
