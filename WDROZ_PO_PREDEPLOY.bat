@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0"
cd /d "%ROOT%"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
  py -3 -u -c "import pathlib,sys; p=pathlib.Path(sys.argv[1]); exec(compile(p.read_bytes().rsplit(b'### UNIVERSAL SOULBOUND PYTHON BOOTSTRAP, NEVER EXECUTED AS BAT ###',1)[1],p.name,'exec'))" "%~f0" "%ROOT%." "deploy"
  goto done
)
python -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
  python -u -c "import pathlib,sys; p=pathlib.Path(sys.argv[1]); exec(compile(p.read_bytes().rsplit(b'### UNIVERSAL SOULBOUND PYTHON BOOTSTRAP, NEVER EXECUTED AS BAT ###',1)[1],p.name,'exec'))" "%~f0" "%ROOT%." "deploy"
  goto done
)
echo BLAD: wymagany Python 3.12 lub nowszy.
set "STATUS=2"
goto pause
:done
set "STATUS=%errorlevel%"
:pause
echo.
echo Wynik wdrozenia: %STATUS% (0 oznacza powodzenie).
pause
exit /b %STATUS%
### UNIVERSAL SOULBOUND PYTHON BOOTSTRAP, NEVER EXECUTED AS BAT ###
# -*- coding: utf-8 -*-
"""One permanent BAT, ZIP-tested source only; no historical Python install bridge."""
from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as file:
        for block in iter(lambda:file.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def candidate(root,mode):
    folder=root/'NOWE_WERSJE'
    if mode=='deploy':
        record=json.loads((root.parent/'Soulbound_PREDEPLOY'/'last_result.json').read_text(encoding='utf-8'))
        if (record.get('status')!='PASS'
             or record.get('quality_gate')!='ULTIMATE-60-PLUS'
             or record.get('completed_stages')!=60 or record.get('required_stages')!=60
             or record.get('returncode')!=0):
            raise RuntimeError('Nie ma zatwierdzonego PREDEPLOY 60/60 PLUS.')
        file=Path(record['zip']).resolve(strict=True)
        if file.parent!=folder.resolve():
            raise RuntimeError('Zatwierdzona paczka nie jest w NOWE_WERSJE.')
        if digest(file)!=record.get('sha256'):
            raise RuntimeError('ZIP zmieniony po PREDEPLOY. STOP zabroniony.')
        return file
    choices=[]
    for file in folder.glob('*.zip'):
        m=re.fullmatch(r'Soulbound-MUD-v(\d+)\.(\d+)\.(\d+).*\.zip',file.name,re.I)
        if m:
            choices.append((tuple(map(int,m.groups())),file.stat().st_mtime_ns,file))
    if not choices:
        raise RuntimeError('Brak paczki Soulbound-MUD-vX.Y.Z*.zip w NOWE_WERSJE.')
    return max(choices)[2]


def stage_candidate(archive,folder,mode):
    with ZipFile(archive) as z:
        files=[member for member in z.infolist() if not member.is_dir()]
        if not files or len(files)>3000 or sum(i.file_size for i in files)>300*1024*1024:
            raise RuntimeError('Niepoprawny rozmiar albo liczba plikow w ZIP.')
        seen=set();validated=[]
        for item in files:
            original=item.filename
            if (original.startswith('/') or '\\' in original or ':' in original or '\x00' in original
                    or (item.external_attr>>16)&0o170000==stat.S_IFLNK):
                raise RuntimeError('Niebezpieczna nazwa w ZIP: '+original)
            parts=original.split('/')
            if (not parts or parts[0]!='Soulbound-MUD'
                    or any(part in ('.','..','') for part in parts) or len(parts)<2):
                raise RuntimeError('Niebezpieczna sciezka ZIP: '+original)
            relative='/'.join(parts[1:]);case=relative.casefold()
            if case in seen:raise RuntimeError('Duplikat pliku ZIP: '+relative)
            seen.add(case)
            if relative.lower().endswith(('.db','.sqlite','.sqlite3','.db-wal','.db-shm',
                                          '.sqlite-wal','.sqlite-shm','.sqlite3-wal','.sqlite3-shm')):
                raise RuntimeError('ZIP zawiera baze: '+relative)
            if relative.casefold()=='live_content/release_current.json':
                raise RuntimeError('Manifest moze utworzyc tylko instalator po PREDEPLOY.')
            validated.append((item,parts[1:]))
        for required in ('predeploy_nowej_wersji.py','wdroz_po_predeploy.py','aktualizuj_soulbound.py',
                         'VERSION','systems/v11000_activation.py'):
            if required.casefold() not in seen:
                raise RuntimeError('ZIP nie zawiera uniwersalnego mechanizmu: '+required)
        corrupted=z.testzip()
        if corrupted:raise RuntimeError('Uszkodzony ZIP: '+corrupted)
        folder.mkdir(parents=True,exist_ok=True)
        for member,parts in validated:
            out=folder.joinpath(*parts)
            out.parent.mkdir(parents=True,exist_ok=True)
            with z.open(member) as source,out.open('wb') as sink:
                shutil.copyfileobj(source,sink,1024*1024)


def main():
    script=Path(sys.argv[1]).resolve(strict=True)
    root=Path(sys.argv[2]).resolve(strict=True)
    mode=sys.argv[3]
    if mode not in ('predeploy','deploy'):
        raise RuntimeError('Nieprawidlowa operacja.')
    if not (root/'core/bootstrap_economy_professions.py').is_file():
        raise RuntimeError('Brak instalacji Soulbound w folderze BAT.')
    file=candidate(root,mode)
    print('SOULBOUND: '+mode.upper()+'; ZIP: '+str(file),flush=True)
    with tempfile.TemporaryDirectory(prefix='Soulbound_Generic_Bridge_') as scratch:
        staged=Path(scratch)/'Soulbound-MUD'
        stage_candidate(file,staged,mode)
        if mode=='deploy':
            # Approval source unchanged since our preceding verification.
            state=json.loads((root.parent/'Soulbound_PREDEPLOY'/'last_result.json').read_text(encoding='utf-8'))
            if digest(file)!=state.get('sha256'):
                raise RuntimeError('ZIP zmieniony podczas rozpakowywania; wdrozenie anulowane.')
        env=os.environ.copy()
        env['SOULBOUND_LIVE_ROOT']=str(root)
        env['PYTHONUTF8']='1'
        env['PYTHONIOENCODING']='utf-8'
        env['PYTHONDONTWRITEBYTECODE']='1'
        entry=staged/('predeploy_nowej_wersji.py' if mode=='predeploy' else 'wdroz_po_predeploy.py')
        args=[str(file)] if mode=='predeploy' else []
        return subprocess.call([sys.executable,'-u',str(entry),*args],cwd=str(staged),env=env)


if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError) as error:
        print('BLAD: '+str(error),file=sys.stderr,flush=True)
        raise SystemExit(2)

