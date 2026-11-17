# -*- coding: utf-8 -*-
"""One-time safe retirement of the obsolete Admin Live storage directory.

Never runs on a live server; called only after the exact 60/60 approval,
full verified backup, code publication and manifest checks. The backup must
retain every source byte. Published JSON read by modern gameplay is moved to
existing config/; all other legacy material remains in the full backup only.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import os
import shutil

PUBLISHED = frozenset({
    'adaptive_combat_global_v102006.json', 'shop_progression_v7003.json',
    'heritage_v7100.json', 'custom_races_v7600.json',
    'custom_classes_v7700.json', 'era_v10300.json',
    'era_v10400_overrides.json',
})

class RetirementError(RuntimeError):
    pass


def _sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(1024*1024), b''):h.update(part)
    return h.hexdigest()


def retire(root, backup):
    """Remove LIVE_CONTENT only after an exact full copy and safe relocation.

    Unknown historical files are retained in the separate complete backup,
    never silently translated into gameplay configuration. Refuse symlinks,
    conflicting destination files, or missing/changed backup bytes. Atomic
    per-file writes and a rollback of newly copied destinations on failure.
    """
    root, backup = Path(root), Path(backup)
    legacy=root/'LIVE_CONTENT'
    if not legacy.exists() and not legacy.is_symlink():return 0
    if legacy.is_symlink() or not legacy.is_dir() or backup.is_symlink():
        raise RetirementError('Niebezpieczny katalog LIVE_CONTENT lub backup')
    source_files=[p for p in sorted(legacy.rglob('*')) if p.is_file()]
    for item in legacy.rglob('*'):
        if item.is_symlink():raise RetirementError('Dowiazanie symboliczne w starych ustawieniach')
    for src in source_files:
        relative=src.relative_to(root)
        copied=backup/relative
        if copied.is_symlink() or not copied.is_file() or _sha(src)!=_sha(copied):
            raise RetirementError('Brak kompletnego backupu LIVE_CONTENT: '+str(relative))
    target=root/'config'
    if target.is_symlink() or not target.is_dir():
        raise RetirementError('Brak bezpiecznego katalogu config')
    sources={p.name:p for p in source_files if p.parent==legacy and p.name in PUBLISHED}
    new_files=[]
    try:
        for name,src in sorted(sources.items()):
            dest=target/name
            if dest.is_symlink():raise RetirementError('Dowiazanie przy docelowych ustawieniach')
            if dest.exists():
                if not dest.is_file() or _sha(src)!=_sha(dest):
                    raise RetirementError('Konflikt starej konfiguracji: '+name)
                continue
            pending=target/(name+'.soulbound-new')
            if pending.exists() or pending.is_symlink():
                raise RetirementError('Niezakonczona operacja: '+name)
            try:
                shutil.copy2(src,pending)
                if _sha(src)!=_sha(pending):
                    raise RetirementError('Bledna kopia opublikowanej konfiguracji: '+name)
                os.replace(pending,dest)
                new_files.append(dest)
            finally:
                pending.unlink(missing_ok=True)
        for name,src in sources.items():
            if _sha(src)!=_sha(target/name):
                raise RetirementError('Zmodyfikowano opublikowane ustawienia: '+name)
        # The complete source remains in backup; the old folder may disappear.
        # Rename first so the old path is removed atomically on one volume.
        retired=root/'.retired_LIVE_CONTENT_cleanup'
        if retired.exists() or retired.is_symlink():
            raise RetirementError('Nieukonczone porzadki LIVE_CONTENT')
        legacy.rename(retired)
        try:
            shutil.rmtree(retired)
        except OSError:
            # If deletion failed partway, recover from the already verified
            # full backup, never discard the only remaining user copy.
            if retired.exists():
                shutil.rmtree(retired,ignore_errors=True)
            if legacy.exists():shutil.rmtree(legacy)
            shutil.copytree(backup/'LIVE_CONTENT',legacy)
            raise
        return len(source_files)
    except BaseException:
        for dest in new_files:
            dest.unlink(missing_ok=True)
        raise


def carry_published_to_staging(stage, code_backup):
    """Linux: migrate old published settings into the new release, not old root.

    The old release directory is immutable and already fully backed up; the
    temporary new release must not inherit a LIVE_CONTENT directory at all.
    """
    stage, code_backup = Path(stage), Path(code_backup)
    legacy = code_backup/'LIVE_CONTENT'
    if not legacy.exists():
        if (stage/'LIVE_CONTENT').exists():
            raise RetirementError('Kandydat wciaz zawiera LIVE_CONTENT bez kopii')
        return 0
    if legacy.is_symlink() or not legacy.is_dir():
        raise RetirementError('Niebezpieczne zrodlo dawnej konfiguracji Linux')
    target = stage/'config'
    if target.is_symlink() or not target.is_dir():
        raise RetirementError('Brak katalogu config w kandydacie Linux')
    files=[p for p in legacy.rglob('*') if p.is_file()]
    if any(p.is_symlink() for p in legacy.rglob('*')):
        raise RetirementError('Dowiazanie w historycznej konfiguracji')
    copied=[]
    try:
        for source in files:
            if source.parent != legacy or source.name not in PUBLISHED:
                continue
            dest=target/source.name
            if dest.is_symlink() or (dest.exists() and _sha(dest)!=_sha(source)):
                raise RetirementError('Konflikt ustawien Linux: '+source.name)
            if not dest.exists():
                tmp=target/(source.name+'.soulbound-new')
                if tmp.exists() or tmp.is_symlink():
                    raise RetirementError('Pozostalosc po aktualizacji ustawien Linux')
                try:
                    shutil.copy2(source,tmp)
                    if _sha(source)!=_sha(tmp):
                        raise RetirementError('Niezgodne bajty ustawien Linux')
                    os.replace(tmp,dest)
                    copied.append(dest)
                finally:
                    tmp.unlink(missing_ok=True)
        # The stage may contain protected files copied from the previous
        # release, but must never publish the old folder to new installations.
        folder=stage/'LIVE_CONTENT'
        if folder.is_symlink():
            raise RetirementError('Dowiazanie w LIVE_CONTENT stage Linux')
        if folder.is_dir():
            for item in folder.rglob('*'):
                if item.is_symlink():raise RetirementError('Dowiazanie w LIVE_CONTENT stage Linux')
            shutil.rmtree(folder)
        return len(copied)
    except BaseException:
        for path in copied:path.unlink(missing_ok=True)
        raise
