# -*- coding: utf-8 -*-
"""Safety gate: runtime kill credits four quest systems inside one SAVEPOINT."""
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def run():
    source=(ROOT/'player/session_mixins/combat_rewards.py').read_text(encoding='utf-8')
    module=(ROOT/'systems/atomic_kill_quest_progress_v10400.py').read_text(encoding='utf-8')
    tree=ast.parse(source)
    klass=next(node for node in tree.body if isinstance(node,ast.ClassDef)
               and node.name=='SessionCombatRewardsMixin')
    method=next(node for node in klass.body if isinstance(node,ast.AsyncFunctionDef)
                and node.name=='mob_defeated')
    calls=[node.func.id for node in ast.walk(method)
           if isinstance(node,ast.Call) and isinstance(node.func,ast.Name)]
    assert calls.count('settle_all_kill_quests_v10400')==1
    assert 'increment_quest' not in calls, 'Do not count wildcard quest once per alias'
    assert 'increment_multi_objective_v1800' not in calls
    assert 'increment_class_legend_kill_v800' not in calls
    assert 'increment_party_contract_v11339' not in calls
    helper=ast.parse(module)
    assert not any(isinstance(node,ast.Await) for node in ast.walk(helper))
    assert 'ROLLBACK TO SAVEPOINT v104_all_kill_quests' in module
    assert 'ROLLBACK TO SAVEPOINT v104_atomic_kill_quests' in module
    return 8

if __name__=='__main__':
    print('QUEST ROUTE:',run(),'PASS')
