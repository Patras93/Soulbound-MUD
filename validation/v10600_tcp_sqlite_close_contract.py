# -*- coding: utf-8 -*-
"""v106 Windows regression: temporary SQLite is explicitly closed in TCP tests.

SQLite connection context manager only finalizes transactions and DOES NOT
close the handle. tempfile cleanup on Windows raises WinError 32 if a handle
stays open. This AST contract catches it on Linux as well.
"""
from __future__ import annotations
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TESTS=(
    'validation/v10600_tcp_raid_turnin_rewards.py',
    'validation/v10600_tcp_raid_natural_six.py',
    'validation/v10600_tcp_raid_party_real.py',
    'validation/v10600_raid_runtime_stage_tcp.py',
)

def _is_sqlite_connect(expr):
    return (isinstance(expr,ast.Call) and isinstance(expr.func,ast.Attribute)
            and expr.func.attr=='connect' and isinstance(expr.func.value,ast.Name)
            and expr.func.value.id=='sqlite3')

def run():
    checks=0
    for name in TESTS:
        path=ROOT/name
        tree=ast.parse(path.read_text('utf-8'),filename=str(path))
        imports=[node for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)
                 and node.module=='contextlib' and any(alias.name=='closing' for alias in node.names)]
        assert imports,'Missing contextlib.closing in '+name
        checks+=1
        seen=0
        for node in ast.walk(tree):
            if not isinstance(node,(ast.With,ast.AsyncWith)):
                continue
            for item in node.items:
                expr=item.context_expr
                if _is_sqlite_connect(expr):
                    raise AssertionError('SQLite connection manager without close: '+name)
                if (isinstance(expr,ast.Call) and isinstance(expr.func,ast.Name)
                        and expr.func.id=='closing' and len(expr.args)==1
                        and _is_sqlite_connect(expr.args[0])):
                    seen+=1
                    checks+=1
        assert seen>0,'No checked disposable SQLite connection: '+name
        checks+=1
    assert checks==15,checks
    print('V106 WINDOWS SQLITE TCP HANDLE CLOSE: '+str(checks)+' PASS',flush=True)
    return checks

if __name__=='__main__':run()
