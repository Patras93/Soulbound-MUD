# -*- coding: utf-8 -*-
"""v112: independent ownership of holidays, Magitek and archetypes.

No old executable modules, full current installation, durable IDs and
zero legacy staging bypass. Runs only on disposable SQLite fixtures.
"""
from __future__ import annotations
import ast,hashlib,json,os,sqlite3,tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'validation/v11200_big_batch_manifest.json'

def logic_digest(path):
    tree=ast.parse(path.read_text(encoding='utf-8-sig'))
    selected=[node for node in tree.body if not isinstance(node,(ast.Import,ast.ImportFrom))
        and not (isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant)
        and isinstance(node.value.value,str))]
    return hashlib.sha256(ast.dump(ast.Module(body=selected,type_ignores=[]),
        include_attributes=False).encode()).hexdigest()

def run():
    from aktualizuj_soulbound import v111_live_release_mapping
    from systems.v11200_activation import REQUIRED, enabled
    from systems.magitek.magicite import CORES, _require_stage
    from core.magitek.catalogue import skill_catalogue
    from core.archetypes.chaos import CLASS_SPECS as C107, RACE_SPECS as R107, PROFESSION_SPECS as P107
    from core.archetypes.expansion import CLASS_SPECS as C110, RACE_SPECS as R110, PROFESSION_SPECS as P110
    from systems.holiday.calendar import MONTHS, WARSAW, easter
    from systems.holiday.schedule import active_schedule
    from world.holiday_expareas import install
    manifest=json.loads(MANIFEST.read_text('utf8'))
    installed={x.as_posix() for x in v111_live_release_mapping(
        {p.relative_to(ROOT):None for p in ROOT.rglob('*') if p.is_file()})}
    checks=0
    assert len(manifest)==44, len(manifest)
    for new,entry in manifest.items():
        old=entry['old']; file=ROOT/new
        assert not (ROOT/old).exists() and old not in installed,old
        assert file.is_file() and not file.is_symlink() and new in installed and new in REQUIRED,new
        assert logic_digest(file)==entry['ast_logic_sha256'],new
        checks+=3
    assert len(C107)==7 and len(R107)==8 and len(P107)==8
    assert len(C110)==len(R110)==len(P110)==8
    assert len({x[0] for x in (*C107,*C110)})==15
    assert len({x[0] for x in (*R107,*R110)})==16
    assert len(MONTHS)==12 and easter(2027)==date(2027,3,28)
    assert 'active' in active_schedule(date(2027,12,25))
    assert len(skill_catalogue())==16 and len(CORES)==4
    checks+=7
    with tempfile.TemporaryDirectory(prefix='sb112_bigbatch_') as td:
        db=Path(td)/'stage.sqlite'
        lab={'SOULBOUND_HOST':'127.0.0.1','SOULBOUND_PORT':'48471',
             'SOULBOUND_DB':str(db)}
        with patch.dict(os.environ,{**lab,'SOULBOUND_V112_STAGING':'0',
                                    'SOULBOUND_V107_STAGING':'1',
                                    'SOULBOUND_V110_STAGING':'1',
                                    'SOULBOUND_V111_STAGING':'1'}):
            assert not enabled(), 'historyczne flagi odblokowaly aktualna gre'
            denied=False
            try:_require_stage()
            except RuntimeError as exc:
                denied='v112' in str(exc)
            assert denied, 'Magicite bypasses authorization or reported wrong gate'
            checks+=2
        with patch.dict(os.environ,{**lab,'SOULBOUND_V112_STAGING':'1',
                                    'SOULBOUND_V107_STAGING':'0',
                                    'SOULBOUND_V110_STAGING':'0'}):
            assert enabled(), 'isolated staging v112 denied'
            _require_stage()
            checks+=2
    # Never rewrite durable v107/v110 SQL/quest identifiers during package move.
    sql=(ROOT/'systems/magitek/magicite.py').read_text('utf8')
    assert 'magitek_magicite_link_v107' in sql
    holiday=(ROOT/'world/holiday_expareas.py').read_text('utf8')
    assert "PREFIX = 'v11100_holiday'" in holiday and "PREFIX = 'v11100_holiday_'" in (ROOT/'systems/holiday/challenges.py').read_text('utf8')
    assert 'core.archetypes_v110' not in (ROOT/'core/archetypes/expansion.py').read_text('utf8')
    assert 'systems.v10700_activation' not in sql
    assert 'systems.v11100_holiday_activation' not in (ROOT/'systems/holiday/combat.py').read_text('utf8')
    checks+=5
    print(f'V112 ZBIORCZA MODERNIZACJA: {checks} PASS; 44 moduly, dane 1:1, '
          'instalacja samodzielna, autoryzacja v112, bez starego kodu',flush=True)
    return checks

if __name__=='__main__':run()
