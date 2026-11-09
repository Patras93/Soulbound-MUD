# -*- coding: utf-8 -*-
"""v109 static release prerequisite; never substitutes Windows PREDEPLOY."""
from __future__ import annotations
from pathlib import Path
from systems.v10900_activation import REQUIRED

ROOT=Path(__file__).resolve().parents[1]

def unmet_requirements(root=ROOT):
    root=Path(root)
    missing=[]
    if not (root/'VERSION').is_file() or (root/'VERSION').read_text(encoding='utf-8-sig').strip()!='109.00.0':
        missing.append('Niezgodny numer v109')
    for rel in REQUIRED:
        if not (root/rel).is_file() or (root/rel).is_symlink():
            missing.append('Brak wymaganego kodu: '+rel)
    for rel,tokens in (
        ('server.py',('ensure_authorized_start(',)),
        ('server/mud_server.py',('ensure_authorized_start(DB_PATH)',)),
        ('predeploy_nowej_wersji.py',('V109 RELEASE GATES PASS',)),
        ('testuj_soulbound_windows.py',('V109 RELEASE GATES PASS',)),
        ('wdroz_po_predeploy.py',('v109_release_gates_pass',)),
        ('aktualizuj_soulbound.py',('v109_release_activation.json','activation_manifest',)),
        ('systems/v10900_gifts.py',('claim_once','award_after_delay')),
        ('predeploy_v109_z_zewnatrz.py',('verify_v108','_candidate_matches_zip')),
        ('wdroz_v109_z_zewnatrz.py',('WDRAZAM V109','require_v104_official_predeploy')),
        ('predeploy_v109_standard_router.py',('_stage_archive','predeploy_v109_z_zewnatrz.py')),
        ('PREDEPLOY_NOWEJ_WERSJI.bat',('predeploy_v109_standard_router.py',)),
        ('validation/v10900_modular_boundaries_regression.py',('SNAPSHOTS','fingerprint')),
        ('testuj_soulbound_windows.py',('validation/v10900_snapshot_preservation.py',)),
        ('world/dynamic_content.py',('V10900_HORIZONS_BUILD',))):
        p=root/rel
        if p.is_file() and not all(t in p.read_text(encoding='utf-8-sig') for t in tokens):
            missing.append('Brak integracji w '+rel)
    return tuple(missing)

if __name__=='__main__':
    errors=unmet_requirements()
    if errors:
        for e in errors:print('V109 BLOCK: '+e)
        raise SystemExit(3)
    print('V109: kompletne pliki i kontrolki integracji; to NIE jest zgoda na wdrozenie')
