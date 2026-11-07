# -*- coding: utf-8 -*-
"""External 108 PREDEPLOY bridge for an installed, still-running v107 server.

Runs the unmodified predeploy_nowej_wersji.py from the exact 108 ZIP against
the OLD v107 installation with its real committed WAL snapshot. Neither the
candidate nor the original SQLite database is installed or mutated here.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parent


def preflight(live_root, zip_path):
    from aktualizuj_soulbound import UpdateError, file_version, archive_mapping
    from predeploy_nowej_wersji import inspect_zip
    from validation.v10800_release_readiness import unmet_requirements
    live_root=Path(live_root).expanduser().resolve(strict=True)
    zip_path=Path(zip_path).expanduser().resolve(strict=True)
    if live_root==ROOT or ROOT.is_relative_to(live_root):
        raise UpdateError('v108: rozpakuj kandydat poza folderem dzialajacej v107.')
    if file_version(live_root/'core/bootstrap_economy_professions.py')!='107.00.0':
        raise UpdateError('v108: test dotyczy tylko aktualizacji z 107.00.0.')
    if unmet_requirements(ROOT):
        raise UpdateError('v108: kod wymaganych modulow jest niekompletny.')
    version,_=inspect_zip(zip_path)
    if version!='108.00.0':
        raise UpdateError('v108: wymagany jeden kompletny ZIP 108.00.0.')
    # An attacker cannot swap the PREDEPLOY script or candidate EQ runner
    # between extraction and the original archive. This is a source check,
    # not a substitute for the required 60/60+ proof.
    from systems.v10800_activation import REQUIRED
    with zipfile.ZipFile(zip_path) as archive:
        mapping=archive_mapping(archive)
        for rel in (*REQUIRED, 'predeploy_v108_z_zewnatrz.py'):
            file=ROOT/rel
            entry=mapping.get(Path(rel))
            if entry is None or not file.is_file() or archive.read(entry)!=file.read_bytes():
                raise UpdateError('v108: rozpakowany PREDEPLOY rozni sie od ZIP: '+rel)
    return live_root,zip_path


def main(argv=None):
    parser=argparse.ArgumentParser(description='PREDEPLOY Soulbound v108 bez ruszania produkcji.')
    parser.add_argument('--instalacja',default=r'C:\Soulbound-MUD')
    parser.add_argument('--zip',dest='archive')
    args=parser.parse_args(argv)
    try:
        live=Path(args.instalacja).expanduser().resolve(strict=True)
        import predeploy_nowej_wersji as pd
        archive=(Path(args.archive).expanduser().resolve(strict=True) if args.archive else
                 _pick_zip_from_live(live))
        live,archive=preflight(live,archive)
        # The candidate harness is used as code, while every comparison,
        # source DB snapshot and external signed-off state remains live-rooted.
        pd.ROOT=live
        pd.WORK=live.parent/'Soulbound_PREDEPLOY'
        # v107 approval remains in last_result.json while v108 is tested.
        # One shared state would disable v107 EQ protection on its next boot.
        pd.STATE=pd.WORK/'last_result_v108.json'
        pd.INBOX=live/'NOWE_WERSJE'
        print('V108: testuje ZIP bez instalowania. Produkcja zostaje uruchomiona.',flush=True)
        return pd.main([str(archive)])
    except (OSError,ValueError,RuntimeError,KeyError,zipfile.BadZipFile) as exc:
        print('V108 PREDEPLOY ZABLOKOWANY: '+type(exc).__name__+': '+str(exc),file=sys.stderr,flush=True)
        return 3


def _pick_zip_from_live(live):
    import predeploy_nowej_wersji as pd
    box=Path(live)/'NOWE_WERSJE'
    candidates=sorted(box.glob('Soulbound-MUD-v108.00.0*.zip')) if box.is_dir() else []
    if len(candidates)!=1:
        raise RuntimeError('Umiesc jeden ZIP v108 w NOWE_WERSJE albo uzyj --zip.')
    return candidates[0].resolve()


if __name__=='__main__':
    raise SystemExit(main())
