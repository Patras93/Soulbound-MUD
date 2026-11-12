# -*- coding: utf-8 -*-
"""Regression for safe v112 recovery bridge, without touching any user DB."""
from __future__ import annotations
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def check():
    checks=0
    bat=(ROOT/'PREDEPLOY_NOWEJ_WERSJI.bat').read_text(encoding='utf-8')
    deploy=(ROOT/'WDROZ_PO_PREDEPLOY.bat').read_text(encoding='utf-8')
    marker='### UNIVERSAL SOULBOUND PYTHON BOOTSTRAP, NEVER EXECUTED AS BAT ###'
    for source in (bat,deploy):
        assert source.count(marker)==3
        tree=ast.parse(source.rsplit(marker,1)[1])
        assert tree
        required='systems/runtime_activation.py'
        assert required in source
        assert "'VERSION','systems/v11200_activation.py'" not in source
        assert "'VERSION','systems/v11000_activation.py'" not in source
        checks+=4
    pre=(ROOT/'predeploy_nowej_wersji.py').read_text(encoding='utf-8')
    assert "if active not in ('110.00.0', '111.00.0'):" in pre
    assert 'v112_base_preflight(ROOT)' in pre
    assert "if version_tuple(version) < version_tuple(active):" in pre
    checks+=3
    update=(ROOT/'aktualizuj_soulbound.py').read_text(encoding='utf-8')
    assert "installed not in ('110.00.0','111.00.0')" in update
    assert "if new_version != '112.00.0':" in update
    assert 'v112_base_preflight(root)' in update
    assert 'require_v104_official_predeploy(root, archive_path, new_version)' in update
    checks+=4
    deploypy=(ROOT/'wdroz_po_predeploy.py').read_text(encoding='utf-8')
    assert "s.get('installed_at_test') not in ('110.00.0','111.00.0')" in deploypy
    assert "input('Aby wdrozyc, wpisz dokladnie WDRAZAM: ')" in deploypy
    checks+=2
    return checks

if __name__=='__main__':
    print(f'V112 UPGRADE BRIDGE: {check()} checks PASS')
