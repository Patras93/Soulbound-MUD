# -*- coding: utf-8 -*-
"""Static audit: normal kill uses one atomic five-axis payout."""
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run():
    source=(ROOT/'player/session_mixins/combat_rewards.py').read_text('utf-8')
    tree=ast.parse(source)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SessionCombatRewardsMixin')
    method=next(n for n in cls.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='mob_defeated')
    calls=[n for n in ast.walk(method) if isinstance(n,ast.Call)]
    simple=[n.func.id for n in calls if isinstance(n.func,ast.Name)]
    assert simple.count('settle_combat_full_progression_v10400')==1, 'Normal kill must settle all five axes once per recipient'
    assert 'award_stats_xp_atomic_v10400' in source, 'Summoned helper retains its existing XP path'
    source_core=(ROOT/'systems/combat_kill_settlement_v10400.py').read_text('utf-8')
    core=ast.parse(source_core)
    coro=[n for n in ast.walk(core) if isinstance(n,(ast.Await,ast.AsyncFunctionDef))]
    assert not coro, 'No await/network I/O during SQLite SAVEPOINT'
    assert 'ROLLBACK TO SAVEPOINT v104_combat_currency_stats' in source_core
    assert 'RELEASE SAVEPOINT v104_combat_currency_stats' in source_core
    assert 'require_sqlite_int64' in source_core
    assert 'db.save_character(character, commit=False)' in source_core
    assert 'deferred_commits' in source_core
    assert 'settle_combat_full_progression_v10400' in source
    assert 'SAVEPOINT v104_full_kill_reward' in source_core
    assert 'ROLLBACK TO SAVEPOINT v104_full_kill_reward' in source_core
    assert 'award_soul_xp_atomic_v10400' in source_core
    assert 'award_class_xp_batch_atomic_v10400' in source_core
    assert 'session.character.silver += silver' not in source, 'No uncommitted coin assignment'
    return 14

if __name__=='__main__':print('AKTYWNA TRASA WALI: ',run(),'PASS')
