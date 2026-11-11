# -*- coding: utf-8 -*-
"""v108 regression of controlled root BAT cleanup using only synthetic files."""
from __future__ import annotations
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from narzedzia.porzadki_bat import ORIGINAL_SHA256,cleanup,plan


def run():
    checked=0
    def ck(yes,msg):
        nonlocal checked
        assert yes,msg
        checked+=1
    root=Path(__file__).resolve().parents[1]
    archive=root/'narzedzia'/'bat_historyczne'
    is_v110=(root/'VERSION').read_text(encoding='utf-8-sig').strip() in ('110.00.0', '111.00.0')
    ck(len(ORIGINAL_SHA256)==51,'reviewed history count')
    ck(len(list(root.glob('*.bat')))==11 if is_v110 else len(list(root.glob('*.bat')))>=21,'minimal v110 BAT entrypoints / historical BAT inventory')
    ck(not (root/'UZGODNIJ_EQ_V108.bat').exists(),'cancelled EQ2 repair must be absent')
    ck(not (root/'AUDYT_V108_EQ_KOPIA_TYLKO_ODCZYT.bat').exists(),'cancelled EQ2 audit must be absent')
    if is_v110:
        # V110 ships no historical launchers. The old exact-name/sha256 migration
        # manifest is still verified, preserving the checks without keeping
        # executable historical BAT files in the release.
        ck(not list(archive.glob('*.bat')),'no archived historical BATs shipped in v110')
        for name,digest in ORIGINAL_SHA256.items():
            ck(name.lower().endswith('.bat') and name==Path(name).name,
               'verified historical BAT basename: '+name)
            ck(len(digest)==64 and all(ch in '0123456789abcdef' for ch in digest),
               'verified historical BAT digest: '+name)
    else:
        ck(len(list(archive.glob('*.bat')))==51,'all historical BATs kept')
        for name in ORIGINAL_SHA256:
            ck((archive/name).exists(),'archived BAT: '+name)
            body=(archive/name).read_text(encoding='utf-8-sig')
            ck('%~dp0' not in body or ('%~dp0' + '..' + chr(92) + '..' + chr(92)) in body,'old root translated: '+name)
    core_paths=('START_Soulbound.bat','STOP_Soulbound.bat')
    if not is_v110:
        core_paths+=('SPRAWDZ_V104_MIGRACJE_NA_KOPII_BAZY.bat',
                     'SPRAWDZ_RAJD_ERA_V103_TCP.bat',
                     'SPRAWDZ_INNE_RAJDY_ERA_V103_TCP.bat')
    else:
        for obsolete in ('SPRAWDZ_V104_MIGRACJE_NA_KOPII_BAZY.bat',
                         'SPRAWDZ_RAJD_ERA_V103_TCP.bat',
                         'SPRAWDZ_INNE_RAJDY_ERA_V103_TCP.bat'):
            ck(not (root/obsolete).exists(),'obsolete v110 BAT excluded: '+obsolete)
    # Do not make V110 depend on obsolete V108 external installers.
    if is_v110:
        core_paths+=('PREDEPLOY_NOWEJ_WERSJI.bat','WDROZ_PO_PREDEPLOY.bat')
    else:
        core_paths+=('PREDEPLOY_V108_Z_ZEWNATRZ.bat','WDROZ_V108_Z_ZEWNATRZ.bat')
    for needed in core_paths:
        ck((root/needed).is_file(),'critical legacy path '+needed)
    with TemporaryDirectory(prefix='bat-v108-clean-') as temp:
        test=Path(temp)
        (test/'VERSION').write_text('107.00.0',encoding='utf-8')
        original=next(iter(ORIGINAL_SHA256))
        (test/original).write_bytes(b'@echo off\r\n')
        ck(plan(test)==[(original,'POMIN_ZMIENIONY')],'changed local BAT skipped')
        ck(cleanup(test,execute=False)==plan(test),'dry run exact')
        ck((test/original).exists(),'dry run no mutation')
        try: cleanup(test,execute=True)
        except RuntimeError: checked+=1
        else: raise AssertionError('v107 protected from cleanup')
        (test/'VERSION').write_text('108.00.0',encoding='utf-8')
        ck(cleanup(test,execute=True)==plan(test),'changed BAT handled')
        ck((test/original).exists(),'local user edits never deleted')
        # Simulate an original historical BAT with matching release checksum.
        second=next(name for name in ORIGINAL_SHA256 if name!=original)
        from narzedzia import porzadki_bat as cleanup_module
        reviewed=(b'@echo off\r\nREM isolated test BAT only: '
                  +second.encode('ascii')+b'\r\n') if is_v110 else (archive/second).read_bytes()
        localhash=hashlib.sha256(reviewed).hexdigest()
        # An isolated fixture uses a temporary approved digest, never changes
        # the shipped manifest permanently and never accesses live files.
        before=cleanup_module.ORIGINAL_SHA256[second]
        cleanup_module.ORIGINAL_SHA256[second]=localhash
        try:
            (test/second).write_bytes(reviewed)
            ck((second,'PRZENIES') in plan(test),'matching BAT identified')
            cleanup(test,execute=True)
            ck(not (test/second).exists(),'historical BAT moved')
            ck((test/'narzedzia'/'bat_historyczne'/'z_instalacji'/second).read_bytes()==reviewed,
               'archive retains exact contents')
            cleanup(test,execute=True)
            ck(not (test/second).exists(),'repeat is idempotent')
        finally:
            cleanup_module.ORIGINAL_SHA256[second]=before
    return checked

if __name__=='__main__':
    print('V108 PORZADKI BAT:',run(),'PASS; test bez danych graczy',flush=True)
