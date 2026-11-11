# -*- coding: utf-8 -*-
"""Regression: persisted Admin Live level caps remain active after release upgrades."""
import ast
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from core import live_level_caps_v5200 as caps


def run():
    root = Path(__file__).resolve().parents[1]
    server_src = (root / 'server.py').read_text(encoding='utf-8')
    ast_tree = ast.parse(server_src)
    candidates = [n for n in ast_tree.body if isinstance(n, ast.If) and
                  any(isinstance(inner, ast.ImportFrom) and inner.module == 'core.live_level_caps_v5200'
                      for inner in ast.walk(n)) and
                  any(isinstance(inner, ast.Name) and inner.id == '_load_caps_v5200'
                      for inner in ast.walk(n))]
    assert len(candidates) == 1, 'Exactly one persistent caps bootstrap branch required'
    branch = ast.fix_missing_locations(ast.Module(body=[candidates[0]], type_ignores=[]))
    ck = 1

    # Execute exactly the bootstrap AST from server.py in an isolated namespace
    # with an observed load() (without importing server or modifying player DB).
    for version, expected in [('51.99.9', 0), ('52.00.0', 1), ('97.00.0', 1),
                              ('98.00.0', 1), ('102.00.11', 1), ('102.00.12', 1),
                              ('105.00.0', 1), ('120.00.3', 1)]:
        calls = []
        def fake_load():calls.append(1)
        with patch.object(caps, 'load', fake_load):
            exec(compile(branch, 'server.py', 'exec'), {'VERSION':version})
        assert len(calls) == expected, f'{version}: expected {expected} loads, got {len(calls)}'
        ck += 1

    # On-disk 'null' is genuine unlimited, and each recorded axis survives reload.
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / 'LIVE_CONTENT' / 'admin_level_caps.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        expected = dict(caps.DEFAULTS)
        expected.update({'postac': None, 'bieglosc': None, 'dusza': None,
                         'bron_duszy': None, 'skille': None,
                         'profesje': None, 'narzedzia': None, 'gildia': None})
        path.write_text(json.dumps({'schema':1,'caps':expected}),encoding='utf-8')
        assert caps.read_file(path) == expected
        ck += 1
        assert caps.effective_number(expected['postac']) == 1_000_000_000
        ck += 1
        # The updater must not overwrite the preserved level caps config.
        updater = (root / 'aktualizuj_soulbound.py').read_text(encoding='utf-8')
        updater_tree=ast.parse(updater)
        names={n.value for n in ast.walk(updater_tree) if isinstance(n, ast.Constant) and isinstance(n.value,str)}
        assert 'admin_level_caps.json' in names
        ck += 1
        zips = list(root.glob('*.db')) + list(root.glob('*.sqlite'))
        assert not zips, 'No database should be in release root'
        ck += 1

    # The restored configuration is NOT a direct database or player-level write.
    branch_names={n.id for n in ast.walk(branch) if isinstance(n,ast.Name)}
    assert '_load_caps_v5200' in branch_names and 'VERSION' in branch_names
    ck += 1
    return ck


if __name__ == '__main__':
    print('PERSISTENT LEVEL CAPS v102.00.12:', run(),'checks PASS', flush=True)
