# -*- coding: utf-8 -*-
"""v4.00.7: preserved authored expansion AST + stable legacy entry points."""
import ast
from hashlib import sha256
from pathlib import Path

ORIGINAL = {
    'build_world_expansion_i': ('world/expansion_frontier_north_v407.py','3969090cfcd8dbaf358c88877459f65945f1e1cb36639e7b46650c324c77b265'),
    'build_world_expansion_ii': ('world/expansion_frontier_fields_v407.py','6ca419e3501bcd98f486587cda10a7d711a117bb96edf4488edab3c25bb164d6'),
    'build_forest_wolves_and_quest_balance': ('world/expansion_frontier_forest_v407.py','00ae64f05a48fc9186f842f923f29280e64e2ccf7f8f37b3ed901707b8fa328e'),
}

def run_regression():
    root = Path(__file__).resolve().parents[1]
    checks = 0
    for name, (path, original_hash) in ORIGINAL.items():
        tree = ast.parse((root/path).read_text(encoding='utf-8'))
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
        assert len(functions) == 1, (name,'missing original function')
        assert sha256(ast.dump(functions[0], include_attributes=False).encode()).hexdigest() == original_hash, (name,'authored logic changed')
        checks += 3
    # All facades must propagate rebindings of the original shared EXP_AREAS.
    facade = (root/'world/expansion_frontiers.py').read_text(encoding='utf-8')
    tree = ast.parse(facade)
    for name in ORIGINAL:
        functions = [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name]
        assert len(functions)==1, (name,'missing compatibility facade')
        body = ast.get_source_segment(facade, functions[0])
        assert '_impl.EXP_AREAS = EXP_AREAS' in body, name
        assert 'EXP_AREAS = _impl.EXP_AREAS' in body, name
        checks += 3
    import server
    from core.bootstrap_economy_professions import VERSION
    import world.expansion_frontiers as facade_module
    assert VERSION in ('4.00.7','4.10.0','4.20.0','4.21.0','4.21.1','5.00.0','5.00.1','6.00.0','6.00.1')
    for name in ORIGINAL:
        assert callable(getattr(facade_module, name)), name
        checks += 1
    # Real wrapper invocation, but never call world builders or mutate world content.
    import importlib
    for name, (path, _) in ORIGINAL.items():
        module = importlib.import_module(path.replace('/', '.')[:-3])
        original_callable = getattr(module, name)
        original_impl_areas = module.EXP_AREAS
        original_facade_areas = facade_module.EXP_AREAS
        source = {'source': name}
        replacement = {'replacement': name}
        observed = []
        def controlled_builder():
            observed.append(module.EXP_AREAS is source)
            module.EXP_AREAS = replacement
            return 'facade-compatible'
        try:
            setattr(module, name, controlled_builder)
            facade_module.EXP_AREAS = source
            assert getattr(facade_module, name)() == 'facade-compatible', name
            assert observed == [True], (name, 'input propagation failed')
            assert facade_module.EXP_AREAS is replacement, (name, 'output propagation failed')
            checks += 3
        finally:
            setattr(module, name, original_callable)
            module.EXP_AREAS = original_impl_areas
            facade_module.EXP_AREAS = original_facade_areas
    assert len(server.QUESTS) == (3861 if VERSION == '6.00.1' else 2901 if VERSION in ('5.00.0','5.00.1','6.00.0','6.00.1') else 2701)
    assert len(server.CLASS_SKILLS) == 14
    checks += 3
    return checks

if __name__ == '__main__':
    print(f'MODULY ROZBUDOWY SWIATA v4.00.7: {run_regression()} checks PASS')
