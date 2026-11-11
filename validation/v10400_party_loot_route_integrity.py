# -*- coding: utf-8 -*-
"""Static audit: full combat loot staging, no early grants or messages."""
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run():
    source=(ROOT/'player/session_mixins/combat_rewards.py').read_text('utf-8')
    tree=ast.parse(source)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SessionCombatRewardsMixin')
    method=next(n for n in cls.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='mob_defeated')
    calls=[n for n in ast.walk(method) if isinstance(n,ast.Call)]
    batch=[n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='grant_party_loot_batch_atomic_v10400']
    assert len(batch)==1, 'Must commit all core loot types with one helper call'
    assert not any(isinstance(n.func,ast.Name) and n.func.id=='grant_party_loot_atomic_v10400' for n in calls)
    assert len(batch[0].args)==2 and isinstance(batch[0].args[1],ast.Name)
    assert batch[0].args[1].id=='_kill_loot_rolls_v104'
    # All four source types are staged, never awarded individually.
    assert all(f"('{name}'," in source for name in ('normal','legendary','trophy','legacy'))
    assert source.count('_kill_loot_rolls_v104.append(')==4
    suffix=source[source.index('                # v104: one inventory/craftbox transaction'):]
    before=suffix[:suffix.index('grant_party_loot_batch_atomic_v10400(')]
    assert 'await ' not in before, 'No async operations during RNG staging'
    assert 'record_item_collection' not in before
    helper=(ROOT/'systems/atomic_party_loot_v10400.py').read_text('utf-8')
    atom=ast.parse(helper)
    assert not any(isinstance(n,(ast.Await,ast.AsyncFunctionDef)) for n in ast.walk(atom))
    assert 'SAVEPOINT v104_atomic_kill_loot_batch' in helper
    assert 'ROLLBACK TO SAVEPOINT v104_atomic_kill_loot_batch' in helper
    assert 'require_sqlite_int64' in helper
    assert 'commit=False' in helper
    return 14

if __name__=='__main__':print('PARTY LOOT BATCH ROUTE:',run(),'PASS')
