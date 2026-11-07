# -*- coding: utf-8 -*-
"""v108: offline regression suite never uses the caller's live DB or tokens."""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from validation.v10800_offline_suite import _private_test_environment


def run():
    checks=0
    def ok(value,label):
        nonlocal checks
        assert value,label
        checks+=1
    poisoned={
        'SOULBOUND_DB':'C:/Soulbound-MUD/production.db',
        'SOULBOUND_ULTRA_SOURCE_DB':'C:/Soulbound-MUD/live-copy.db',
        'SOULBOUND_CONTROL_TOKEN':'should-not-escape',
        'SOULBOUND_PORT':'4000',
        'SOULBOUND_WORLD_SEED_FILE':'C:/Soulbound-MUD/seed.txt',
        'RAILWAY_VOLUME_MOUNT_PATH':'C:/production',
        'DATABASE_URL':'postgres://live',
        'SMTP_PASSWORD':'secret',
        'PYTHONPATH':'C:/live-modules',
        'USER':'local-synthetic',
    }
    with TemporaryDirectory(prefix='soulbound108_safe_') as td:
        safe=_private_test_environment(poisoned,td)
        ok(safe['SOULBOUND_DB']==str(Path(td)/'offline_synthetic.sqlite'),
           'private database instead of live')
        ok(safe['SOULBOUND_WORLD_SEED_FILE']==str(Path(td)/'offline_seed.txt'),
           'private seed instead of live')
        ok(safe['SOULBOUND_HOST']=='127.0.0.1','only loopback permitted')
        ok('SOULBOUND_ULTRA_SOURCE_DB' not in safe,'real backup source not inherited')
        ok('SOULBOUND_CONTROL_TOKEN' not in safe,'live control token not inherited')
        ok('SOULBOUND_PORT' not in safe,'live listening port not inherited')
        ok('DATABASE_URL' not in safe,'database connector not inherited')
        ok('SMTP_PASSWORD' not in safe,'mail password not inherited')
        ok('PYTHONPATH' not in safe,'live import override not inherited')
        ok('RAILWAY_VOLUME_MOUNT_PATH' not in safe,'remote volume not inherited')
        ok(safe['PYTHONDONTWRITEBYTECODE']=='1','no pycache files created')
        ok(safe['PYTHONIOENCODING']=='utf-8','Polish logs Unicode')
        ok(safe['USER']=='local-synthetic','unrelated safe environment preserved')
        ok(poisoned['SOULBOUND_DB']=='C:/Soulbound-MUD/production.db',
           'caller variables never modified')
        with TemporaryDirectory(prefix='soulbound108_safe_other_') as other:
            safe2=_private_test_environment(poisoned,other)
            ok(safe2['SOULBOUND_DB']!=safe['SOULBOUND_DB'],'no shared SQLite fixture')
    return checks

if __name__=='__main__':
    print('V108 IZOLACJA TESTOW OD PRODUKCJI:',run(),'PASS - NIE WDRAZAC',flush=True)
