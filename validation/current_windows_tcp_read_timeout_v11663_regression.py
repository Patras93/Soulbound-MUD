# -*- coding: utf-8 -*-
"""Deterministic WinError 121 regression using exact shipped Session method AST.

Load the active read_line override and command_loop directly from their source;
no game world, game database, TCP server or imported heavyweight catalog.
The separate PREDEPLOY 60 PLUS keeps the mandatory real integration gates.
"""
from __future__ import annotations
import ast
import asyncio
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


class NativeReadLine:
    """Minimal transport semantics of the preserved native mixin."""
    async def read_line(self):
        try:
            while True:
                data = await self.reader.readline()
                if not data:
                    return None
                result = data.decode('utf-8').strip()
                if result:
                    return result
        except ConnectionError:
            return None


class Reader:
    def __init__(self, result):
        self.result = result
    async def readline(self):
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


def shipped_methods():
    """Compile the actual runtime methods, not a separately retyped copy."""
    source = ast.parse((ROOT / 'player/session.py').read_text(encoding='utf-8-sig'))
    cls = next(n for n in source.body if isinstance(n, ast.ClassDef) and n.name == 'Session')
    methods = [n for n in cls.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'read_line']
    assert len(methods) == 1, 'Missing Session.read_line override'
    loop = ast.parse((ROOT / 'player/session_mixins/command_loop.py').read_text(encoding='utf-8-sig'))
    loop_cls = next(n for n in loop.body if isinstance(n, ast.ClassDef) and n.name == 'SessionCommandLoopMixin')
    loop_methods = [n for n in loop_cls.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'command_loop']
    assert len(loop_methods) == 1
    body = [
        ast.ClassDef(name='Loop', bases=[], keywords=[], body=loop_methods, decorator_list=[]),
        ast.ClassDef(name='Session', bases=[ast.Name(id='NativeReadLine', ctx=ast.Load()),
                                              ast.Name(id='Loop', ctx=ast.Load())],
                     keywords=[], body=methods, decorator_list=[]),
    ]
    module = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))
    namespace = {'NativeReadLine': NativeReadLine}
    exec(compile(module, '<actual session methods>', 'exec'), namespace)
    return namespace['Session']


SESSION = shipped_methods()


def actor(result):
    a = SESSION()
    a.reader = Reader(result)
    a.closed = False
    a.server = SimpleNamespace(db=SimpleNamespace())
    a._last_command_for_diagnostics = 'fish'
    return a


class WindowsTcpTimeout(unittest.TestCase):
    def test_winerror_121_is_disconnect(self):
        error = OSError('Przekroczono limit czasu semafora')
        error.winerror = 121
        a = actor(error)
        self.assertIsNone(asyncio.run(a.read_line()))
        self.assertFalse(a.closed)  # normal server close() should still persist state

    def test_errno_121_on_windows_compat_fixtures(self):
        a = actor(OSError(121, 'Przekroczono limit czasu semafora'))
        self.assertIsNone(asyncio.run(a.read_line()))

    def test_real_command_loop_exits_cleanly_not_command_error(self):
        error = OSError('Windows TCP read timed out')
        error.winerror = 121
        a = actor(error)
        self.assertIsNone(asyncio.run(a.command_loop()))
        self.assertTrue(a.server.db._manual_bank_only_v11325)
        self.assertFalse(a.closed)

    def test_other_oserror_is_not_hidden(self):
        a = actor(OSError(13, 'Permission denied'))
        with self.assertRaises(OSError) as ctx:
            asyncio.run(a.read_line())
        self.assertEqual(ctx.exception.errno, 13)

    def test_cancelled_read_still_propagates(self):
        a = actor(asyncio.CancelledError())
        with self.assertRaises(asyncio.CancelledError):
            asyncio.run(a.read_line())

    def test_normal_command_unchanged(self):
        self.assertEqual(asyncio.run(actor(b'fish\r\n').read_line()), 'fish')

    def test_eof_and_reset_unchanged(self):
        self.assertIsNone(asyncio.run(actor(b'').read_line()))
        self.assertIsNone(asyncio.run(actor(ConnectionResetError(104, 'connection reset')).read_line()))


def run():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(WindowsTcpTimeout)
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful() or result.testsRun != 7:
        raise AssertionError('WinError 121 TCP read regression FAIL')
    return result.testsRun


if __name__ == '__main__':
    print(f'WINDOWS TCP READ TIMEOUT v116.00.63: {run()}/7 PASS')
