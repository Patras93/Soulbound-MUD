# -*- coding: utf-8 -*-
"""Offline safety test for exact protected player-data backups."""
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aktualizuj_soulbound import UpdateError,protected
from systems.universal_release_update import verify_private_backup


def rejects(call):
    try:call()
    except UpdateError:return
    raise AssertionError('Niebezpieczny backup zostal zaakceptowany')


def main():
    cases=0
    with tempfile.TemporaryDirectory() as tmp:
        src=Path(tmp)/'src'; dst=Path(tmp)/'backup'
        src.mkdir();dst.mkdir()
        for name,content in [('soulbound.db',b'fake-db-for-backup-comparison'),
                             ('soulbound_world_seed.txt',b'seed-secret'),
                             ('admin_level_caps.json',b'{"level": 8}'),
                             ('server.py',b'# old code')]:
            (src/name).write_bytes(content);(dst/name).write_bytes(content)
        assert verify_private_backup(src,dst,protected)==3;cases+=1
        (dst/'admin_level_caps.json').write_bytes(b'{"level": 9}')
        rejects(lambda:verify_private_backup(src,dst,protected));cases+=1
        (dst/'admin_level_caps.json').write_bytes(b'{"level": 8}')
        (dst/'soulbound_world_seed.txt').unlink()
        rejects(lambda:verify_private_backup(src,dst,protected));cases+=1
        (dst/'soulbound_world_seed.txt').write_bytes(b'seed-secret')
        (src/'server.py').write_bytes(b'# changed historical code')
        assert verify_private_backup(src,dst,protected)==3;cases+=1
        (src/'soulbound.db-wal').write_bytes(b'pending-wal')
        rejects(lambda:verify_private_backup(src,dst,protected));cases+=1
        (dst/'soulbound.db-wal').write_bytes(b'pending-wal')
        assert verify_private_backup(src,dst,protected)==4;cases+=1
    print('PRIVATE BACKUP BYTE VERIFICATION: '+str(cases)+'/6 PASS')

if __name__=='__main__':main()
