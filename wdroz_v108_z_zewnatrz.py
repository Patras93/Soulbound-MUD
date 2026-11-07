# -*- coding: utf-8 -*-
"""External Windows v107 -> v108 bridge, copied from the EXACT tested ZIP.

Run ONLY from an extracted v108 candidate folder outside C:/Soulbound-MUD.
Without an official 60/60 PLUS + v108-specific PASS this exits before STOP.
The user's current installed v107 updater intentionally cannot install v108.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parent


def check_candidate_matches_zip(zip_path, candidate_root=ROOT):
    from aktualizuj_soulbound import archive_mapping, UpdateError
    from systems.v10800_activation import REQUIRED
    with zipfile.ZipFile(zip_path) as archive:
        mapping = archive_mapping(archive)
        for rel in (*REQUIRED, 'wdroz_v108_z_zewnatrz.py'):
            installed = candidate_root / rel
            entry = mapping.get(Path(rel))
            if entry is None or not installed.is_file() or archive.read(entry) != installed.read_bytes():
                raise UpdateError('v108: kod instalatora nie zgadza sie z zatwierdzonym ZIP: ' + rel)


def preflight(live_root, zip_path):
    from aktualizuj_soulbound import (UpdateError, file_version, find_release,
                                      require_v104_official_predeploy)
    from validation.v10800_release_readiness import unmet_requirements
    live_root = Path(live_root).expanduser().resolve(strict=True)
    zip_path = Path(zip_path).expanduser().resolve(strict=True)
    if live_root == ROOT or ROOT.is_relative_to(live_root):
        raise UpdateError('v108: rozpakuj pelny ZIP poza katalogiem dzialajacej gry.')
    if (ROOT/'VERSION').read_text(encoding='utf-8-sig').strip() != '108.00.0':
        raise UpdateError('v108: wymagany zatwierdzony kandydat 108.00.0.')
    if file_version(live_root/'core/bootstrap_economy_professions.py') != '107.00.0':
        raise UpdateError('v108: sciezka aktualizacji wymaga zainstalowanej v107.00.0.')
    if unmet_requirements(ROOT):
        raise UpdateError('v108: niekompletne bramki wydania.')
    approved, version = find_release(live_root, zip_path, '107.00.0')
    if version != '108.00.0':
        raise UpdateError('v108: zly numer kandydata.')
    check_candidate_matches_zip(approved, ROOT)
    require_v104_official_predeploy(live_root, approved, version)
    return approved, version


def main(argv=None):
    parser = argparse.ArgumentParser(description='Bezpieczny pomost Soulbound v107 do v108.')
    parser.add_argument('--instalacja', default=r'C:\Soulbound-MUD')
    parser.add_argument('--zip', dest='archive')
    parser.add_argument('--sprawdz', action='store_true', help='Tylko kontrola, bez STOP.')
    args = parser.parse_args(argv)
    try:
        from aktualizuj_soulbound import UpdateError, run_update
        live = Path(args.instalacja).expanduser().resolve(strict=True)
        state_file = live.parent/'Soulbound_PREDEPLOY'/'last_result_v108.json'
        selected = (Path(args.archive).expanduser().resolve(strict=True) if args.archive else
                    Path(json.loads(state_file.read_text(encoding='utf-8'))['zip']).resolve(strict=True))
        target, version = preflight(live, selected)
        print('V108: autoryzowany kandydat, PREDEPLOY 60/60 PLUS i bramki EQ PASS.',flush=True)
        print('SHA256 i kod pomostu zgodny z przetestowanym ZIP.',flush=True)
        if args.sprawdz:
            print('Tylko sprawdzono. Serwer i bazy pozostaly bez zmian.',flush=True)
            return 0
        if os.name != 'nt':
            raise UpdateError('Wdrozenie jest dostepne tylko na Windows.')
        answer = input('Potwierdz STOP, backup i instalacje: wpisz WDRAZAM V108: ').strip()
        if answer != 'WDRAZAM V108':
            print('Anulowano. Serwer dziala bez zmian.',flush=True)
            return 2
        target, version = preflight(live, target)
        run_update(live, target, version, restart=True)
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, zipfile.BadZipFile) as exc:
        print('V108 ZABLOKOWANO PRZED STOP: '+type(exc).__name__+': '+str(exc),file=sys.stderr,flush=True)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
