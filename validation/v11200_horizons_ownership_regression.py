# -*- coding: utf-8 -*-
"""v112: independently owned v109 horizons; immutable persistent identifiers."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = (
    'world/horizons_v109', 'world/v10900_horizons.py',
    'world/v10900_horizon_index.py',
)
OWNED = (
    'world/horizons/__init__.py',
    'world/horizons/entry.py',
    'world/horizons/przebudzenie.py',
    'world/horizons/zapomniani.py',
    'world/horizons/wiecznosc.py',
    'world/horizon_index.py',
    'world/horizons_engine.py',
)
IDS_SHA256 = 'f8d8f677736e8ec52553c756ffe492fb30cfc285793e7a97d9147dbd14e77c3f'


def fingerprint(regions, id_sets):
    canonical = json.dumps({'regions': regions,
        'ids': {k: sorted(v) for k, v in id_sets.items()}},
        ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()


def run():
    from aktualizuj_soulbound import v111_live_release_mapping
    from systems.v11200_activation import REQUIRED
    from world.horizons_engine import REGIONS, planned_ids
    from validation.v10900_horizons_regression import run as verify_gameplay

    installed = {r.as_posix() for r in v111_live_release_mapping(
        {p.relative_to(ROOT): None for p in ROOT.rglob('*') if p.is_file()})}
    checks = 0
    for rel in LEGACY:
        assert not (ROOT/rel).exists(), 'Historyczny kod Horyzontow w v112: ' + rel
        assert rel not in installed, 'Historyczny kod w instalacji: ' + rel
        checks += 2
    for rel in OWNED:
        file = ROOT/rel
        assert file.is_file() and not file.is_symlink(), 'Brak modulu: ' + rel
        assert rel in installed, 'Pominiety modul instalacyjny: ' + rel
        assert rel in REQUIRED, 'Modul nie jest obowiazkowy: ' + rel
        ast.parse(file.read_text('utf-8-sig'), filename=rel)
        checks += 4
    assert len(REGIONS)==12 and len({r[0] for r in REGIONS})==12
    ids=planned_ids()
    assert {k:len(v) for k,v in ids.items()} == {
        'rooms':288,'mobs':168,'npcs':48,'quests':360,'items':60,'recipes':12}
    assert fingerprint(REGIONS,ids)==IDS_SHA256, 'Persistent horizon IDs changed'
    checks += 3
    # The original deep regression is still mandatory: verifies exact topology,
    # all quest targets, spawns, drop sources, rollback and repeat installation.
    gameplay_checks=verify_gameplay()
    assert gameplay_checks >= 2962, gameplay_checks
    checks += 1
    print(f'V112 HORYZONTY: {checks} ownership PASS + {gameplay_checks} gameplay PASS; '
          '12 krain; 288 pokoi; 360 questow; 0 zaleznosci od starego pakietu',flush=True)
    return checks

if __name__=='__main__':
    run()
