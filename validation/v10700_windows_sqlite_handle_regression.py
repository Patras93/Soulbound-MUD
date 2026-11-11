# -*- coding: utf-8 -*-
"""Validate Python/SQLite handles are closed BEFORE TemporaryDirectory cleanup.

Python sqlite3 Connection.__exit__ does not close its file! Windows refuses
removing an SQLite database still open in a context-manager scope. Patching
sqlite3.connect here observes *only fake/test SQLite databases*.
"""
from __future__ import annotations
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory as RealTemporaryDirectory
from unittest.mock import patch
from validation import v10700_production_eq_cutover_regression as fixture


def run():
    opened=[]
    connect=sqlite3.connect
    temporary_dirs=[]

    def tracked_connect(*args,**kwargs):
        conn=connect(*args,**kwargs)
        if args and str(args[0]) != ':memory:':
            opened.append((str(args[0]),conn))
        return conn

    class StrictWindowsTemporaryDirectory(RealTemporaryDirectory):
        def __enter__(self):
            path=super().__enter__()
            temporary_dirs.append(str(path))
            return path

        def __exit__(self,exc_type,exc,tb):
            # Windows refuses rmtree on any open SQLite handle; explicitly
            # catch leaked connections even on Linux where unlink succeeds.
            leaked=[]
            for filename,conn in opened:
                if not filename.startswith(self.name):
                    continue
                try:
                    conn.execute('SELECT 1')
                except sqlite3.ProgrammingError:  # AUDIT_INTENTIONAL_PASS: closed connection expected
                    pass  # already closed as required
                else:
                    leaked.append(Path(filename).name)
            if leaked:
                raise AssertionError('Niezamkniete polaczenia SQLite przed usunieciem TEMP: '
                                     +str(len(leaked)))
            return super().__exit__(exc_type,exc,tb)

    with patch('sqlite3.connect',side_effect=tracked_connect), \
         patch.object(fixture,'TemporaryDirectory',StrictWindowsTemporaryDirectory):
        count=fixture.run()
    assert count==24, 'rehearsal incomplete'
    assert len(temporary_dirs)==1, 'rehearsal did not run on temporary data'
    return 3

if __name__=='__main__':
    print('V107 WINDOWS SQLITE - POLACZENIA ZAMKNIETE:',run(), 'PASS',flush=True)
