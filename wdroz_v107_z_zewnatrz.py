# -*- coding: utf-8 -*-
"""Windows bridge for v106 -> v107 without executing the OLD v106 updater.

The candidate MUST be extracted to a separate directory first. This script
is shipped inside the candidate ZIP but is never a predeploy bypass: it
refuses to touch the live server until v107 source readiness AND the exact
official 60/60+ candidate checksum are both positive. No implicit --yes.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
REQUIRED_CANDIDATE_FILES = (
    'wdroz_v107_z_zewnatrz.py',
    'aktualizuj_soulbound.py',
    'validation/v10700_release_readiness.py',
    'systems/v10700_activation.py',
    'core/live_level_caps_v5200.py',
    'testuj_soulbound_windows.py',
    'VERSION',
)


def check_candidate_matches_zip(zip_path, candidate_root=ROOT):
    """Require running the unmodified scripts contained in the approved ZIP."""
    from aktualizuj_soulbound import archive_mapping, UpdateError
    with zipfile.ZipFile(zip_path) as archive:
        mapping = archive_mapping(archive)
        for rel in REQUIRED_CANDIDATE_FILES:
            path = candidate_root / rel
            info = mapping.get(Path(rel))
            if info is None or not path.is_file() or archive.read(info) != path.read_bytes():
                raise UpdateError('Kod instalatora poza ZIP nie zgadza sie z zatwierdzona paczka: '+rel)


def preflight(live_root, zip_path):
    """No writes and no STOP. Return an approved target/version only on PASS."""
    from aktualizuj_soulbound import (
        file_version, find_release, require_v104_official_predeploy, UpdateError,
    )
    from validation.v10700_release_readiness import unmet_requirements
    live_root = Path(live_root).expanduser().resolve(strict=True)
    zip_path = Path(zip_path).expanduser().resolve(strict=True)
    if live_root == ROOT or ROOT.is_relative_to(live_root):
        raise UpdateError('Rozpakuj kandydat v107 POZA folderem produkcyjnym.')
    if not (live_root/'core/bootstrap_economy_professions.py').is_file():
        raise UpdateError('Brak pelnej instalacji gry w podanym folderze.')
    if (ROOT/'VERSION').read_text(encoding='utf-8-sig').strip() != '107.00.0':
        raise UpdateError('Ten pomost dziala tylko z kodem kandydata v107.00.0.')
    current = file_version(live_root/'core/bootstrap_economy_professions.py')
    if current not in ('105.00.0', '106.00.0'):
        raise UpdateError('Migracja nie ma certyfikowanej sciezki z v'+current+' do v107.')
    reasons = unmet_requirements()
    if reasons:
        raise UpdateError('v107 nadal ma '+str(len(reasons))+' blokad produkcyjnych: '+ '; '.join(reasons))
    choice, version = find_release(live_root, zip_path, current)
    if version != '107.00.0':
        raise UpdateError('Niedozwolony kandydat: '+version)
    check_candidate_matches_zip(choice, ROOT)
    require_v104_official_predeploy(live_root, choice, version)
    return choice, version


def main(argv=None):
    parser = argparse.ArgumentParser(description='Bezpieczny pomost v106 do Soulbound v107.')
    parser.add_argument('--instalacja', default=r'C:\Soulbound-MUD',
                        help='Aktualna instalacja produkcyjna Soulbound na Windows.')
    parser.add_argument('--zip', dest='archive', default=None,
                        help='Sciezka do tego samego ZIP, ktory przeszedl PREDEPLOY.')
    parser.add_argument('--sprawdz', action='store_true',
                        help='Tylko sprawdz warunki, niczego nie instaluj.')
    args = parser.parse_args(argv)
    try:
        from aktualizuj_soulbound import run_update, UpdateError
        live = Path(args.instalacja).expanduser().resolve(strict=True)
        if args.archive:
            selected = Path(args.archive).expanduser().resolve(strict=True)
        else:
            # Read only an external approval file; it is verified by SHA256
            # against the exact ZIP later. Never pick an arbitrary newest ZIP.
            import json
            state_path = live.parent/'Soulbound_PREDEPLOY'/'last_result.json'
            state = json.loads(state_path.read_text(encoding='utf-8'))
            selected = Path(state['zip']).resolve(strict=True)
        approved, version = preflight(live, selected)
        print('PREDEPLOY i suma SHA256 tego ZIP: PASS.', flush=True)
        print('Wersja docelowa: v'+version+'. Baza graczy pozostaje chroniona.',flush=True)
        if args.sprawdz:
            print('Tylko sprawdzono. Nie zatrzymano serwera.', flush=True)
            return 0
        if os.name != 'nt':
            raise UpdateError('Instalacja dostepna tylko na Windows.')
        print('Zostanie wykonany backup, STOP, aktualizacja i restart gry.',flush=True)
        answer=input('Aby wdrozyc, wpisz dokladnie WDRAZAM V107: ').strip()
        if answer != 'WDRAZAM V107':
            print('Anulowano, nie zatrzymano serwera.', flush=True)
            return 2
        # Recheck approval after the confirmation and once again in run_update.
        approved, version = preflight(live, approved)
        run_update(live, approved, version, restart=True)
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, zipfile.BadZipFile) as exc:
        print('ZABLOKOWANO PRZED WDROZENIEM: '+str(exc), file=sys.stderr, flush=True)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
