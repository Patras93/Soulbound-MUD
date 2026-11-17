# -*- coding: utf-8 -*-
"""v114: editor removed, but v113 native behavior remains SHA-locked."""
from pathlib import Path
import ast
import copy
import hashlib
from validation.current_native_v420_contract import (
    EXPECTED, _all_methods, verify_native_method,
    _PUBLISHED_NATIVE_MIGRATIONS, _normalize_published_native_ast,
)
ROOT = Path(__file__).resolve().parents[1]


def run():
    checks = 0
    for (relative, method), modules in _PUBLISHED_NATIVE_MIGRATIONS.items():
        file = ROOT / relative
        assert verify_native_method(file, method)
        checks += 1
        node = copy.deepcopy(_all_methods(str(file.resolve()))[method])
        baseline = _normalize_published_native_ast(node, relative, method)
        fingerprint = hashlib.sha256(ast.dump(baseline, include_attributes=False).encode()).hexdigest()
        assert fingerprint == EXPECTED[relative][method]
        checks += 1
        # Deleting any approved published dependency must FAIL CLOSED.
        broken = copy.deepcopy(node)
        altered = False
        for n in ast.walk(broken):
            if isinstance(n, ast.ImportFrom) and n.module in modules:
                n.module = 'systems.missing_module'
                altered = True
                break
        assert altered
        blocked = False
        try:
            _normalize_published_native_ast(broken, relative, method)
        except AssertionError:
            blocked = True
        assert blocked, ('renamed import unnoticed', relative, method)
        checks += 1
        # Changed native gameplay is NOT accepted by the v113 historical hash.
        changed = copy.deepcopy(baseline)
        changed.body.append(ast.Pass())
        changed_hash = hashlib.sha256(ast.dump(changed, include_attributes=False).encode()).hexdigest()
        assert changed_hash != EXPECTED[relative][method]
        checks += 1
    # ALL native methods (not just the migrated ones) remain mandatory.
    total = 0
    for relative, methods in EXPECTED.items():
        for method in methods:
            assert verify_native_method(ROOT / relative, method)
            total += 1
    assert total >= 298, total
    checks += total
    print(f'V114 PUBLISHED NATIVE CONTRACT: {checks}/{checks} PASS', flush=True)
    return checks


if __name__ == '__main__':
    run()
