# -*- coding: utf-8 -*-
"""Predeploy test-root guard rejects recursively nested real DB save files."""
from __future__ import annotations
import tempfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from validation.v10600_one_package_gate import has_game_database

def run():
    checks=0
    def ck(v,m):
        nonlocal checks
        assert v,m;checks+=1
    with tempfile.TemporaryDirectory(prefix='sb106_guard_') as tmp:
        root=Path(tmp)
        ck(not has_game_database(root),'Pusta kopia bez bazy')
        inner=root/'data'/'save'/'characters';inner.mkdir(parents=True)
        ck(not has_game_database(root),'Katalogi bez bazy')
        for ext in ('.db','.db3','.sqlite','.sqlite3','.SQLITE'):
            path=inner/('player_data'+ext)
            path.write_bytes(b'')
            ck(has_game_database(root),'Baza w zagnieżdżonym katalogu '+ext)
            path.unlink()
            ck(not has_game_database(root),'Usunięcie bazy '+ext)
        (root/'CHANGELOG_PL.txt').write_text('a')
        ck(not has_game_database(root),'Zwykłe pliki z changelogiem są bezpieczne')
    return checks

if __name__=='__main__':print('V106 ONE-PACKAGE DB SAFETY GUARD:',run(),'PASS',flush=True)
