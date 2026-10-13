# -*- coding: utf-8 -*-
"""EP: test the actual method body and SQLite query without booting a TCP server."""
from __future__ import annotations
import ast
import asyncio
from pathlib import Path
import sqlite3
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[1]


def run_regression_fast():
    paths = (
        'player/session_mixins/exploration_progress.py',
        'player/session_mixins/command_registry.py',
        'config/command_aliases.py',
        'player/session_mixins/help_system.py',
        'network/protocol_gameplay_utils.py',
    )
    count = 0
    for filename in paths:
        ast.parse((ROOT / filename).read_text(encoding='utf-8'))
        count += 1
    a = (ROOT / paths[0]).read_text(encoding='utf-8')
    b = (ROOT / paths[1]).read_text(encoding='utf-8')
    c = (ROOT / paths[2]).read_text(encoding='utf-8')
    assert 'async def show_exploration_points_v3007(' in a
    count += 1
    assert '"explorer_points"' in a and 'lifetime_stat(' in a
    count += 1
    assert "'ep': ('show_exploration_points_v3007'" in b
    count += 1
    assert "'ep': 'ep'" in c
    count += 1
    return count


def _extract_method(relative, class_name, method_name, globals_):
    """Exercise production AST function unchanged; avoid importing server on Linux."""
    root = ast.parse((ROOT / relative).read_text(encoding='utf-8'))
    original_class = next(node for node in root.body if isinstance(node,ast.ClassDef) and node.name==class_name)
    original_method = next(node for node in original_class.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==method_name)
    wrapper = ast.ClassDef(name='TestOnly',bases=[],keywords=[],body=[original_method],decorator_list=[])
    extracted=ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[]))
    exec(compile(extracted,relative,'exec'),globals_)
    return globals_['TestOnly']


def run_regression():
    checks=run_regression_fast()
    def check(condition,message):
        nonlocal checks
        assert condition, 'EP v3.00.7: '+message
        checks += 1
    # Verify actual registry AST declarations without executing whole runtime.
    tree=ast.parse((ROOT/'player/session_mixins/command_registry.py').read_text('utf8'))
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign):
            if any(isinstance(t,ast.Name) and t.id=='COMMAND_REGISTRY' for t in node.targets):
                registry=ast.literal_eval(ast.unparse(node.value).replace('COMMAND_TEXT','"<text>"').replace('COMMAND_NAME','"<name>"'))
                check(registry['ep'][0]=='show_exploration_points_v3007','dispatch EP handler')
                break
    else:
        raise AssertionError('command registry assignment missing')
    source=(ROOT/'player/session_mixins/command_registry.py').read_text('utf8')
    for state in ('DOWNED_SAFE_COMMANDS','REST_SAFE_COMMANDS','GUIDE_SAFE_COMMANDS'):
        start=source.index(state+' = {')
        end=source.index('}',start)
        check('"ep"' in source[start:end],f'state-safe {state}')
    for path in ('player/session_mixins/help_system.py','network/protocol_gameplay_utils.py'):
        check('ep region' in (ROOT/path).read_text('utf8'),f'help {path}')

    from collections import defaultdict
    normalizer=lambda x: str(x or '').strip().lower()
    cls=_extract_method('player/session_mixins/exploration_progress.py',
        'SessionExplorationProgressMixin','show_exploration_points_v3007',
        {'normalize_lookup_text': normalizer})
    DBcls=_extract_method('storage/db_world.py','DatabaseWorldMixin','lifetime_stat',{})
    con=sqlite3.connect(':memory:');con.row_factory=sqlite3.Row
    con.executescript('''CREATE TABLE lifetime_statistics (
        account_id INTEGER NOT NULL, stat_key TEXT NOT NULL, value INTEGER,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(account_id,stat_key));
        INSERT INTO lifetime_statistics(account_id,stat_key,value) VALUES
        (10,'explorer_points',251), (11,'explorer_points',9005),
        (10,'rooms_discovered',17);''')
    db=DBcls();db.conn=con
    class Dummy(cls):
        def __init__(self,account):
            self.account_id=account;self.server=SimpleNamespace(db=db)
            self.out=[];self.delegated=[]
        async def send(self,text):self.out.append(text)
        async def show_exploration(self,args=''):self.delegated.append(args)
    a,b,empty=Dummy(10),Dummy(11),Dummy(100)
    start=con.total_changes
    asyncio.run(a.show_exploration_points_v3007())
    check(len(a.out)==1 and '251' in a.out[0],'total one line')
    check('9005' not in a.out[0],'account isolation')
    asyncio.run(b.show_exploration_points_v3007('status'))
    check(len(b.out)==1 and '9005' in b.out[0],'other account')
    asyncio.run(empty.show_exploration_points_v3007())
    check(' 0.' in empty.out[0],'zero on new account')
    asyncio.run(a.show_exploration_points_v3007('region'))
    asyncio.run(a.show_exploration_points_v3007('all'))
    check(a.delegated==['','all'],'existing summary delegated')
    asyncio.run(a.show_exploration_points_v3007('zle'))
    check('Użycie:' in a.out[-1],'invalid args show help')
    check(con.total_changes==start,'no SQLite changes')
    check(db.lifetime_stat(10,'explorer_points')==251,'EP persisted')
    con.close()
    return checks

if __name__=='__main__':
    print(f'EP v3.00.7: {run_regression()} checks PASS')
