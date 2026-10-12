# -*- coding: utf-8 -*-
"""Regression for automatic tunnel mining across Session.move wrappers."""
from __future__ import annotations

import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace

_ROOT = Path(__file__).resolve().parent.parent


def run_static_regression():
    """Fast audit without importing the runtime or opening user databases."""
    checks = 0
    for relpath, name, delegate in (
        ("world/party_combo_ultimate_summary.py", "_move_v0380", "_move_before_v0380"),
        ("world/magitek_infinite.py", "_move_v0382", "_move_before_v0382"),
    ):
        tree = ast.parse((_ROOT / relpath).read_text(encoding="utf-8"))
        fn = next((node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == name), None)
        assert fn is not None, (relpath, name)
        assert fn.args.vararg and fn.args.vararg.arg == 'args', (relpath, 'missing *args')
        assert fn.args.kwarg and fn.args.kwarg.arg == 'kwargs', (relpath, 'missing **kwargs')
        calls = [node for node in ast.walk(fn) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == delegate]
        assert len(calls) == 1, (relpath, 'expected one delegated move')
        call = calls[0]
        assert any(isinstance(a, ast.Starred) and isinstance(a.value, ast.Name) and a.value.id == 'args' for a in call.args)
        assert any(k.arg is None and isinstance(k.value, ast.Name) and k.value.id == 'kwargs' for k in call.keywords)
        checks += 5
    return checks


def run_runtime_regression():
    """Exercise both actual async wrappers with a stub underlying movement."""
    from world import party_combo_ultimate_summary as summary
    from world import magitek_infinite as magitek

    saved_summary = summary._move_before_v0380
    saved_magitek = magitek._move_before_v0382
    calls = []

    async def underlying(session, direction, *args, **kwargs):
        calls.append((direction, args, dict(kwargs)))
        assert session.character is not None
        return 'moved'

    session = SimpleNamespace(
        character=SimpleNamespace(room_id='no_crypt_room'),
        magitek_descent_blocked_for_player=lambda room, direction: False,
    )

    async def scenario():
        try:
            # magitek -> crypt -> original movement
            summary._move_before_v0380 = underlying
            magitek._move_before_v0382 = summary._move_v0380
            result = await magitek._move_v0382(session, 'east', preserve_auto_mining=True)
            assert result == 'moved'
            assert calls[-1] == ('east', (), {'preserve_auto_mining': True})
            result = await magitek._move_v0382(session, 'north')
            assert result == 'moved'
            assert calls[-1] == ('north', (), {})

            # crypt -> magitek -> original movement (normal runtime import order)
            summary._move_before_v0380 = magitek._move_v0382
            magitek._move_before_v0382 = underlying
            result = await summary._move_v0380(session, 'west', preserve_auto_mining=True)
            assert result == 'moved'
            assert calls[-1] == ('west', (), {'preserve_auto_mining': True})
            result = await summary._move_v0380(session, 'south')
            assert result == 'moved'
            assert calls[-1] == ('south', (), {})

            # crypt wrapper alone, preserving automatic descent and auto mining.
            summary._move_before_v0380 = underlying
            result = await summary._move_v0380(session, 'down', preserve_auto_mining=True)
            assert result == 'moved'
            assert calls[-1] == ('down', (), {'preserve_auto_mining': True})
        finally:
            summary._move_before_v0380 = saved_summary
            magitek._move_before_v0382 = saved_magitek

    asyncio.run(scenario())
    assert len(calls) == 5
    return 11


if __name__ == '__main__':
    print('AUTO MINING MOVE STATIC:', run_static_regression(), 'PASS')
