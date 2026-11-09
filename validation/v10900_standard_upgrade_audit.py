# -*- coding: utf-8 -*-
"""Read-only audit: can the installed v108 update tools approve v109?

This module intentionally DOES NOT modify the installed updater, databases,
PREDEPLOY state, or deployment flags. A candidate ZIP cannot authorize its own
production deployment through scripts already installed in v108.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
FILES = ('predeploy_nowej_wersji.py', 'wdroz_po_predeploy.py', 'aktualizuj_soulbound.py')


def _archive_text(archive: Path, relative: str) -> str:
    with ZipFile(archive) as z:
        names = [n for n in z.namelist() if n == relative or n == 'Soulbound-MUD/' + relative]
        if len(names) != 1:
            raise ValueError(f'Brak jednoznacznej sciezki: {relative}')
        return z.read(names[0]).decode('utf-8-sig')


def _function(source: str, name: str) -> ast.FunctionDef:
    module = ast.parse(source)
    result = [n for n in module.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    if len(result) != 1:
        raise ValueError(f'Brak funkcji {name}')
    return result[0]


def _source_block(source: str, method: str) -> str:
    node = _function(source, method)
    return ast.get_source_segment(source, node) or ''


def inspect_archives(installed_v108: Path, candidate_v109: Path) -> dict[str, bool]:
    """Hard-fail proofs; false means compatibility IS NOT available.

    No version flag is patched, no fingerprint is bypassed, no server is
    started, and no database is opened.
    """
    old = {name: _archive_text(installed_v108, name) for name in FILES}
    new = {name: _archive_text(candidate_v109, name) for name in FILES}
    try:
        assert _archive_text(installed_v108, 'VERSION').strip() == '108.00.0'
        assert _archive_text(candidate_v109, 'VERSION').strip() == '109.00.0'
    except AssertionError as exc:
        raise ValueError('Niepoprawna para archiwow v108 -> v109') from exc

    # Installed updater rejects every version >=108 except exactly 108.
    old_guard = _source_block(old['aktualizuj_soulbound.py'], 'require_v104_official_predeploy')
    old_deploy = _source_block(old['wdroz_po_predeploy.py'], 'main')
    old_predeploy = _source_block(old['predeploy_nowej_wersji.py'], 'verified_staged_pass')
    old_main = _source_block(old['predeploy_nowej_wersji.py'], 'main')
    new_guard = _source_block(new['aktualizuj_soulbound.py'], 'require_v104_official_predeploy')
    new_deploy = _source_block(new['wdroz_po_predeploy.py'], 'main')
    new_predeploy = _source_block(new['predeploy_nowej_wersji.py'], 'verified_staged_pass')

    return {
        'old_predeploy_can_read_zip_version': 'inspect_zip' in old_main,
        'old_predeploy_requires_v109_gate_text': "version == '109.00.0'" in old_predeploy,
        'old_predeploy_writes_v109_approval': "state['v109_release_gates_pass']" in old_main,
        'old_deploy_supports_v109': "ver == '109.00.0'" in old_deploy,
        'old_updater_has_v109_migration': "new_version == '109.00.0'" in old_guard,
        'new_predeploy_requires_v109_gate_text': "version == '109.00.0'" in new_predeploy,
        'new_deploy_requires_v109_approval': 'v109_release_gates_pass' in new_deploy,
        'new_updater_has_v109_migration': "new_version == '109.00.0'" in new_guard,
        'new_installer_requires_v108_auth': 'verify_v108' in new_guard,
        'new_deploy_uses_simple_WDRAZAM': "if input('Aby wdrozyc, wpisz dokladnie WDRAZAM: ').strip()!='WDRAZAM'" in new_deploy,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Audyt kompatybilnosci starego PREDEPLOY i wdrozenia v109')
    parser.add_argument('installed_v108', type=Path)
    parser.add_argument('candidate_v109', type=Path)
    args = parser.parse_args(argv)
    r = inspect_archives(args.installed_v108, args.candidate_v109)
    for k, yes in r.items():
        print(f'{k}: {"TAK" if yes else "NIE"}')
    # Never print PASS when production updater cannot handle candidate.
    if not all((r['old_predeploy_requires_v109_gate_text'], r['old_predeploy_writes_v109_approval'],
                r['old_deploy_supports_v109'], r['old_updater_has_v109_migration'])):
        print('WYNIK: BLOKADA PRZEJSCIA V108->V109, NIE WDRAZAC; '
              'nowy ZIP nie moze zmienic narzedzi juz zainstalowanej v108.')
        return 2
    print('KOD INSTALATORA ZNA V109; wymagane niezalezne testy Windows i aktywacji.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
