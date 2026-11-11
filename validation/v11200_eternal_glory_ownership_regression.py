# -*- coding: utf-8 -*-
"""v112: obowiązkowa własność kodu Wiecznej Chwały i zachowanie mechanik.

Ten test jest wykonywany wyłącznie na kopii kodu. Dane SQLite i zapisy graczy
nie są dotykane. Historyczne identyfikatory 'v1100_*' pozostają bez zmian.
"""
from __future__ import annotations
import ast
import hashlib
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from aktualizuj_soulbound import v111_live_release_mapping
from systems.v11200_activation import REQUIRED
from validation.v11200_closed_runtime_gate import inspect_files,source_files

DIGESTS={
    'world': '5dd81ab4779b66175c683845b59b0f6e15ccb7852a55f644ea111f92a85fdb62',
    'companions': '0ce39eb02f180d8bcea3948894c199914a34157c638025832932f6329f65029b',
    'depths': '9e947d58157f0cea70753c441bb3a95c713903754e803c8324fae6247c812333',
    'infinite': '92b934601f1a699068da081491b35b4f5fbebcadd1c710fdf2b24d4aa605bb84',
    'crafting': '50da558b74d5d205aa5bf664231e85c7b0582ce5462b39b49ea59f09fcf2e7c8',
    'class_guild': '24d348aabe0e232dba2cb7cd5f509358854fbc4344414981b42ffa412036f85d',
    'story': '8db35ea6b6616b605bf501e378b57bbc62007af76c99ef6da911e10f7da20d1b',
}

def logic_digest(source):
    tree=ast.parse(source)
    relevant=[n for n in tree.body
              if not isinstance(n,(ast.Import,ast.ImportFrom))
              and not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant)
                       and isinstance(n.value.value,str))]
    return hashlib.sha256(ast.dump(ast.Module(body=relevant,type_ignores=[]),include_attributes=False).encode()).hexdigest()

def check():
    names=list(DIGESTS)
    files={p.relative_to(ROOT):None for p in ROOT.rglob('*')
           if p.is_file() and not p.is_symlink()
           and '__pycache__' not in p.parts and p.suffix.lower() not in ('.db','.sqlite','.sqlite3','.pyc')}
    installed={p.as_posix() for p in v111_live_release_mapping(files)}
    result=inspect_files(source_files(ROOT),installed)
    assert result['missing_import_count']==0, result['missing_imports'][:20]
    checks=1
    for key in names:
        rel=f'systems/eternal_glory/{key}.py'
        old=f'systems/eternal_glory_{key}_v1100.py'
        path=ROOT/rel
        assert path.is_file() and rel in installed and rel in REQUIRED, rel
        checks+=1
        assert not (ROOT/old).exists() and old not in installed, old
        checks+=1
        assert logic_digest(path.read_text(encoding='utf-8-sig'))==DIGESTS[key],rel
        checks+=1
        assert not any(item['module']==f'systems.eternal_glory_{key}_v1100'
                       for item in result['old_version_imports']),key
        checks+=1
    import systems.eternal_glory.companions as companions
    assert companions.run_regression()==80
    checks+=1
    from systems.eternal_glory.world import REGIONS,ROOM_IDS,LANDMARK_IDS,QUEST_IDS
    from systems.eternal_glory.infinite import ENDLESS, floor_id,gate_id
    assert len(REGIONS)==12 and len(ROOM_IDS)==144 and len(LANDMARK_IDS)==36 and len(QUEST_IDS)==24
    checks+=1
    assert len(ENDLESS)==3 and floor_id('wieza',10)=='v1100_inf_wieza_floor_10' and gate_id('chaos')=='v1100_inf_chaos_gate'
    checks+=1
    # Fail closed if any source still references a removed path (including a lazy branch).
    for p in ROOT.rglob('*.py'):
        if '__pycache__' in p.parts:continue
        for oldkey in names:
            assert f'systems.eternal_glory_{oldkey}_v1100' not in p.read_text(encoding='utf-8-sig'),p
    checks+=1
    print(f'V112 WIECZNA CHWALA: {checks} kontroli PASS; 7 modulow, 80 testow towarzyszy, niezmienne ID')

if __name__=='__main__':check()
