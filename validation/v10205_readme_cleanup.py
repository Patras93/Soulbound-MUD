# -*- coding: utf-8 -*-
"""Functional test of retire-known-README migration on isolated temp folders."""
from __future__ import annotations
from pathlib import Path
import tempfile
from release_readme_cleanup import LEGACY_READMES, ReadmeCleanupError, cleanup_legacy_readmes


def run() -> int:
    checks = 0
    def ck(flag: bool, why: str) -> None:
        nonlocal checks
        assert flag, why
        checks += 1
    with tempfile.TemporaryDirectory(prefix='sb-readme-test-') as tmp:
        parent = Path(tmp)
        root = parent / 'Soulbound-MUD'
        root.mkdir()
        (root / 'README_ADMIN_LIVE_PL.txt').write_text('NOWY', encoding='utf-8')
        (root / 'README_MOJE_NOTATKI.txt').write_text('PRYWATNE', encoding='utf-8')
        (root / 'CHANGELOG_PL.txt').write_text('HISTORIA', encoding='utf-8')
        (root / 'soulbound.db').write_text('DB', encoding='utf-8')
        (root / 'logs').mkdir()
        (root / 'logs' / 'README_v98_ADMIN_LIVE_PL.txt').write_text('LOG', encoding='utf-8')
        for name in LEGACY_READMES:
            (root / name).write_text('stara instrukcja: ' + name, encoding='utf-8')
        saved = parent / 'Soulbound_BACKUP_TEST'
        names, at = cleanup_legacy_readmes(root, saved)
        ck(set(names) == set(LEGACY_READMES), 'all old README files retired')
        ck(at == saved, 'backup location')
        for name in LEGACY_READMES:
            ck(not (root / name).exists(), 'old README removed: ' + name)
            ck((saved / name).read_text(encoding='utf-8') == 'stara instrukcja: ' + name, 'backup byte content: ' + name)
        ck((root / 'README_ADMIN_LIVE_PL.txt').read_text(encoding='utf-8') == 'NOWY', 'current README preserved')
        ck((root / 'README_MOJE_NOTATKI.txt').read_text(encoding='utf-8') == 'PRYWATNE', 'custom README preserved')
        ck((root / 'CHANGELOG_PL.txt').read_text(encoding='utf-8') == 'HISTORIA', 'changelog preserved')
        ck((root / 'soulbound.db').read_text(encoding='utf-8') == 'DB', 'database preserved')
        ck((root / 'logs' / LEGACY_READMES[0]).read_text(encoding='utf-8') == 'LOG', 'logs untouched')
        ck(cleanup_legacy_readmes(root) == ([], None), 'idempotent no-op')
        # A backup with conflicting bytes aborts without removing source.
        victim = root / LEGACY_READMES[0]
        victim.write_text('LOCAL DATA', encoding='utf-8')
        refused = False
        try:
            cleanup_legacy_readmes(root, saved)
        except ReadmeCleanupError:
            refused = True
        ck(refused, 'mismatch backup refused')
        ck(victim.read_text(encoding='utf-8') == 'LOCAL DATA', 'mismatch leaves source unchanged')
        victim.unlink()
        # No wildcard matching: custom version-style filenames are untouched.
        (root / 'README_v200_MOJ_PROJEKT.txt').write_text('MINE', encoding='utf-8')
        ck(cleanup_legacy_readmes(root) == ([], None), 'unlisted README not affected')
        ck((root / 'README_v200_MOJ_PROJEKT.txt').exists(), 'custom version README still present')
    return checks


if __name__ == '__main__':
    print(f'V102.00.5 README CLEANUP: {run()} checks PASS', flush=True)
