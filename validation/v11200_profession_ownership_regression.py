# -*- coding: utf-8 -*-
"""v112: 16 professions owned by current runtime; save IDs and atomicity preserved.

Runs against memory-only SQLite fixtures, never user data or an old server.
"""
from __future__ import annotations
import ast
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
DIGESTS = {
    'chaos':'6b3be1ef1753a07766c74b34a6d2a88896683279189bf587532ac652e7013e05',
    'expansion':'5f7f4c69913b7f715e8c98199adccedc8ae31acd2e447dbe730f3e259de4a70e',
}
OLD = ('systems/v10700_profession_work.py','systems/v11000_profession_work.py')
NEW = ('systems/profession_generations/__init__.py',
       'systems/profession_generations/chaos.py',
       'systems/profession_generations/expansion.py')


def logic_digest(path):
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    relevant = [n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))
                and not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant)
                         and isinstance(n.value.value,str))]
    return hashlib.sha256(ast.dump(ast.Module(body=relevant,type_ignores=[]),
                           include_attributes=False).encode('utf8')).hexdigest()


def check():
    from aktualizuj_soulbound import v111_live_release_mapping
    from systems.v11200_activation import REQUIRED, enabled
    from core.archetypes.chaos import PROFESSION_SPECS as CHAOS
    from core.archetypes.expansion import PROFESSION_SPECS as EXPANSION
    from systems.profession_generations import chaos, expansion
    from validation.v11000_profession_atomic_regression import DB, run as atomic_110

    installed = {x.as_posix() for x in v111_live_release_mapping(
        {p.relative_to(ROOT):None for p in ROOT.rglob('*') if p.is_file()})}
    checks=0
    for rel in OLD:
        assert not (ROOT/rel).exists() and rel not in installed, rel
        checks += 1
    for rel in NEW:
        path=ROOT/rel
        assert path.is_file() and not path.is_symlink() and rel in installed and rel in REQUIRED, rel
        checks += 1
    for key,digest in DIGESTS.items():
        assert logic_digest(ROOT/f'systems/profession_generations/{key}.py') == digest,key
        checks+=1
    handlers=(ROOT/'player/session_mixins/command_special_handlers.py').read_text('utf8')
    tree=ast.parse(handlers)
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in (
                'command_profesja107','command_profesja110'):
            src=ast.get_source_segment(handlers,n)
            assert 'systems.v11200_activation' in src, n.name
            assert 'systems.v11000_activation' not in src, n.name
            assert 'systems.v10700_profession_work' not in src, n.name
            assert 'systems.v11000_profession_work' not in src, n.name
            checks+=1
    assert len(CHAOS)==8 and len(EXPANSION)==8
    assert {chaos.product_id(i) for i in range(8)} == {
        f'v10700_prof_product_{i}' for i in range(1,9)}
    assert {expansion.product_id(i) for i in range(8)} == {
        f'v11000_prof_product_{i}' for i in range(1,9)}
    assert {expansion.tool_item_id(i) for i in range(8)} == {
        f'v11000_prof_tool_{i}' for i in range(1,9)}
    assert chaos.COOLDOWN==expansion.COOLDOWN==12
    checks+=4
    with tempfile.TemporaryDirectory(prefix='sb112_prof_ownership_') as td:
        env={'SOULBOUND_HOST':'127.0.0.1','SOULBOUND_PORT':'48176',
             'SOULBOUND_DB':str(Path(td)/'test.sqlite')}
        with patch.dict(os.environ,{**env,'SOULBOUND_V112_STAGING':'0',
                     'SOULBOUND_V107_STAGING':'1','SOULBOUND_V110_STAGING':'1'}):
            assert not enabled(), 'stare flagi odblokowuja produkcje'
            checks+=1
        with patch.dict(os.environ,{**env,'SOULBOUND_V112_STAGING':'1'}):
            assert enabled(), 'izolowana baza v112 musi byc dopuszczona'
            checks+=1
    # Test real material usage, independent cooldown and atomic v107 rewards.
    db=DB()
    for index,(_,tool,_,ingredient) in enumerate(CHAOS):
        aid=200+index
        db.add_item(aid,ingredient,2)
        def grant(*args,**kwargs):
            return (['OK'],1,1)
        messages,changed,item=chaos.process(db,aid,index,grant,now=100)
        assert messages==['OK'] and item==chaos.product_id(index)
        assert db.item_qty(aid,ingredient)==1 and db.item_qty(aid,item)==1
        stopped,why,_=chaos.process(db,aid,index,grant,now=101)
        assert stopped is None and '11 sekund' in why
        assert db.item_qty(aid,ingredient)==1 and db.item_qty(aid,item)==1
        checks+=1
    # Both old and new transaction paths run against ephemeral DBs only.
    atomic_110()
    test=subprocess.run([sys.executable,'-u',str(ROOT/'validation/v11000_profession_tools_regression.py')],
        cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT)},capture_output=True,text=True,
        timeout=90,stdin=subprocess.DEVNULL)
    assert test.returncode==0, test.stdout+'\n'+test.stderr
    assert 'V110 PROFESSION TOOLS PASS' in test.stdout
    checks+=2
    print(f'V112 PROFESJE: {checks} PASS; 16 profesji, ID SQLite i wyrobow stale, '
          '12s cooldown, transakcje i izolacja autoryzacji',flush=True)
    return checks

if __name__=='__main__':check()
