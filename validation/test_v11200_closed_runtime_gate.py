# -*- coding: utf-8 -*-
"""Self-tests: strict v112+ installed-module closure, no database, no server."""
from __future__ import annotations
from v11200_closed_runtime_gate import inspect_files


def check():
    files={
        'systems/__init__.py':b'',
        'systems/current.py':b'from . import helper\nfrom systems import helper\n',
        'systems/helper.py':b'VALUE=1\n',
        'server.py':b'from systems.current import VALUE\n',
        'systems/v11000_legacy.py':b'VALUE=2\n',
        'systems/new.py':b'from systems.v11000_legacy import VALUE\n',
        'systems/optional.py':b'import importlib\nimportlib.import_module("systems.helper")\n',
    }
    installed=set(files)-{'systems/v11000_legacy.py','systems/new.py'}
    r=inspect_files(files,installed)
    assert r['status']=='PASS',r
    r=inspect_files(files,installed | {'systems/new.py'})
    assert r['missing_import_count']>=1 and r['old_version_import_count']>=1,r
    r=inspect_files(files,installed-{'systems/helper.py'})
    assert r['missing_import_count']>=2,r
    bad=dict(files,**{'systems/current.py':b'from .missing import test\n'})
    r=inspect_files(bad,installed)
    assert r['missing_import_count']>=1,r
    bad=dict(files,**{'systems/current.py':b'from systems import v11000_legacy\n'})
    r=inspect_files(bad,installed)
    assert r['missing_import_count']>=1 and r['old_version_import_count']>=1,r
    bad=dict(files,**{'server.py':b'from systems.current import VALUE\n' ,'systems/current.py':b'\x00'})
    r=inspect_files(bad,installed)
    assert r['missing_import_count']>=1,r
    r=inspect_files(files,installed, required_files={'server.py','aktualizuj_soulbound.py'})
    assert any(x['reason']=='required_entrypoint_missing_from_installed_runtime'
               for x in r['missing_imports']),r
    r=inspect_files(files, installed, required_files={'server.py'})
    assert r['status']=='PASS',r
    print('V112 CLOSED MODULE SELFTEST: 8/8 PASS')

if __name__=='__main__': check()
