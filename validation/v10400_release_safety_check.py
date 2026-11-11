# -*- coding: utf-8 -*-
"""Offline release guard: v104 remains NON-DEPLOYABLE until all gates pass.
Never imports TCP server or opens any user's database; ZIP inspection is separate.
"""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
MUST_EXIST = (
    'core/exact_reward_math_v10400.py',
    'storage/big_number_copy_runtime_v10400.py',
    'validation/test_v10400_big_number_copy_runtime.py',
    'core/sqlite_numeric_guard_v10400.py',
    'storage/big_number_reward_bundle_v10400.py',
    'systems/combat_kill_settlement_v10400.py',
    'systems/atomic_party_loot_v10400.py',
    'systems/atomic_kill_quest_progress_v10400.py',
    'validation/test_v10400_exact_reward_math.py',
    'validation/v10400_snapshot_preflight.py',
    'validation/test_v10400_snapshot_preflight.py',
    'validation/v10400_extended_snapshot.py',
    'validation/test_v10400_extended_snapshot.py',
    'validation/test_v10400_extended_real_schema.py',
    'validation/test_v10400_release_manifest_guard.py',
)

def inspect():
    missing = [name for name in MUST_EXIST if not (ROOT/name).is_file()]
    if missing: raise AssertionError('Brak krytycznych plikow: '+', '.join(missing))
    for name in MUST_EXIST:
        source=(ROOT/name).read_text(encoding='utf-8-sig')
        ast.parse(source, filename=name)
    release=(ROOT/'VERSION').read_text('utf-8-sig').strip()
    bat='SPRAWDZ_V104_MIGRACJE_NA_KOPII_BAZY.bat'
    if release in ('110.00.0', '111.00.0', '112.00.0'):
        if (ROOT/bat).exists():
            raise AssertionError('v110 nie moze zawierac dawnego instalatora v104')
        source=(ROOT/'validation/v10400_migration_rehearsal.py').read_text('utf-8')
        if ('open_read_only' not in source or 'source.backup(target)' not in source):
            raise AssertionError('Historyczna migracja musi pracowac na kopii tylko do odczytu')
    else:
        source=(ROOT/bat).read_text(encoding='utf-8-sig').lower()
        if ('validation.v10400_migration_rehearsal' not in source
                or '--db' not in source or 'exit /b' not in source):
            raise AssertionError('Historyczny BAT musi uruchamiac migracje na kopii')
    version=(ROOT/'VERSION').read_text('utf-8').strip()
    # Never override actual production's VERSION during an experimental release.
    if version not in ('104.00.0', '104.00.1', '104.00.2', '104.00.3', '105.00.0', '106.00.0', '107.00.0', '110.00.0', '111.00.0', '112.00.0'):
        raise AssertionError('Nieoczekiwany VERSION; przegladaj status wydania!')
    return len(MUST_EXIST)+1

def run():
    return inspect()

if __name__=='__main__': print('OFFLINE SOURCE GUARD:',run(),'PASS; WDROZENIE NADAL ZABLOKOWANE')
