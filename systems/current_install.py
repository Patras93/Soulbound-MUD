# -*- coding: utf-8 -*-
"""Validate and prepare a standalone current release in a NEW directory.

This is separate from the existing-player updater. `install` always executes
its fixed independent checks itself, initializes only an exclusively new
empty database, and publishes only after source hashes and manifests agree.
It never consumes an externally supplied PASS or copies old player saves.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
from systems.universal_activation import current_version
VERSION = current_version(ROOT)
QUALITY_GATE = 'STANDALONE-CURRENT-1'
MARKER = 'LIVE_CONTENT/release_current.json'
VALIDATORS = (
    'validation.current_universal_release_suite',
    'validation.current_explicit_runtime_regression',
    'validation.current_six_client_tcp',
    'validation.current_catalog_equivalence',
    'validation.current_install_regression',
)
BOOTSTRAP = 'systems.current_install_bootstrap'
OLD_AUTH = {
    'systems/v10700_activation.py', 'systems/v10800_activation.py',
    'systems/v10900_activation.py', 'systems/v10900_staging_guard.py',
    'systems/v11000_activation.py', 'systems/v11100_holiday_activation.py',
    'systems/v10800_predeploy_isolation.py',
    'systems/v11200_activation.py',
}
EXCLUDED_PARTS = {'__pycache__', '.git', 'logs', 'backups', 'LIVE_CONTENT',
                  'NOWE_WERSJE', '.pytest_cache'}
MUTABLE_SUFFIXES = ('.db', '.db-wal', '.db-shm', '.sqlite', '.sqlite-wal',
                    '.sqlite-shm', '.sqlite3', '.sqlite3-wal', '.sqlite3-shm',
                    '.pyc', '.pyo', '.log', '.pid', '.lock', '.tmp', '.new',
                    '.soulbound-new', '.bak', '.zip', '.7z', '.tar', '.tgz', '.tar.gz')
CREDENTIAL_SUFFIXES = ('.pem', '.key', '.pfx', '.p12', '.credentials')
PRIVATE_NAMES = {'.env', 'soulbound_control.json', 'admin_level_caps.json',
                 'heritage_v7100.json', 'custom_races_v7600.json',
                 'custom_classes_v7700.json', 'era_v10300.json',
                 'shop_progression_v7003.json', 'credentials.json', 'token.json',
    'id_rsa', 'id_ed25519'}


class InstallError(RuntimeError):
    pass


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def source_files(root):
    root = Path(root)
    result = {}
    for file in root.rglob('*'):
        rel = file.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in rel.parts):
            continue
        if file.is_symlink():
            raise InstallError('Source contains a symbolic link: ' + rel.as_posix())
        if not file.is_file():
            continue
        lowered = file.name.casefold()
        if (lowered in PRIVATE_NAMES or lowered.startswith('.env')
                or lowered.endswith(MUTABLE_SUFFIXES + CREDENTIAL_SUFFIXES)):
            continue
        # Include every static asset, including compressed numeric catalogs
        # and extensionless timezone databases. A suffix allowlist silently
        # omitted those required runtime inputs.
        # Offline fixtures may import their historical activators. Keep these
        # only within validation source trees; they are absent from game code.
        result[rel.as_posix()] = sha(file)
    if not {'VERSION', 'server.py', 'systems/current_install.py'} <= result.keys():
        raise InstallError('Incomplete current source tree')
    if (root / 'VERSION').read_text(encoding='utf-8-sig').strip() != VERSION:
        raise InstallError('This standalone installer supports the current release only')
    return dict(sorted(result.items()))


def _clean_env(root):
    env = os.environ.copy()
    for key in list(env):
        if key.startswith(('SOULBOUND_', 'RAILWAY_')) or key in ('PORT', 'PYTHONPATH'):
            env.pop(key, None)
    env.update(PYTHONPATH=str(root), PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
               PYTHONUNBUFFERED='1', PYTHONDONTWRITEBYTECODE='1')
    return env


def _execute(root, module, arguments=(), env=None, timeout=1800):
    began = time.monotonic()
    result = subprocess.run([sys.executable, '-m', module, *arguments],
        cwd=root, env=env or _clean_env(root), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    output = result.stdout.decode('utf-8', errors='replace')
    print(output, end='' if output.endswith('\n') else '\n', flush=True)
    proof = {'validator': module, 'returncode': result.returncode,
             'elapsed_seconds': round(time.monotonic() - began, 3),
             'output_sha256': hashlib.sha256(result.stdout).hexdigest(),
             'source_sha256': sha(Path(root) / (module.replace('.', '/') + '.py'))}
    if result.returncode != 0:
        raise InstallError('Standalone validation failed: ' + module)
    return proof


def validate(root=ROOT):
    root = Path(root).resolve()
    before = source_files(root)
    results = []
    for module in VALIDATORS:
        identity = module.replace('.', '/') + '.py'
        if identity not in before:
            raise InstallError('Missing mandatory validator: ' + identity)
        results.append(_execute(root, module))
    if source_files(root) != before:
        raise InstallError('Sources changed during validation; repeat all checks')
    installed = installed_sources(root, before)
    return {'schema': 1, 'version': VERSION, 'quality_gate': QUALITY_GATE,
            'validated_at': datetime.now(timezone.utc).isoformat(),
            'files': before, 'installed_files': installed, 'checks': results}


def installed_sources(root, files):
    # This is the CURRENT installer selection function, not code from an old
    # installed release. Share its reviewed production subset so offline
    # fixtures and obsolete activators are not published in the new game.
    from aktualizuj_soulbound import production_release_mapping
    selected = production_release_mapping({Path(rel): None for rel in files})
    return {rel.as_posix(): files[rel.as_posix()] for rel in selected}


def copy_sources(root, destination, files):
    root, destination = Path(root), Path(destination)
    for rel, expected in files.items():
        source = root / rel
        target = destination / rel
        if source.is_symlink() or target.exists() or target.is_symlink():
            raise InstallError('Unsafe or occupied source-copy entry: ' + rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if sha(target) != expected:
            raise InstallError('Source changed during copy: ' + rel)


def _bootstrap(root, output):
    with tempfile.TemporaryDirectory(prefix='sb_current_install_') as folder:
        database = Path(folder).resolve() / 'new.sqlite'
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        if port == 4000:
            raise InstallError('Private bootstrap selected production port')
        env = _clean_env(root)
        env.update(SOULBOUND_UNIVERSAL_STAGING='1', SOULBOUND_HOST='127.0.0.1',
                   SOULBOUND_PORT=str(port), SOULBOUND_DB=str(database))
        result = _execute(root, BOOTSTRAP, ('--database', str(database)), env, timeout=600)
        if output.exists() or output.is_symlink():
            raise InstallError('Refusing to overwrite a database')
        shutil.copy2(database, output)
        return result


def _valid_digest(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def verify_marker(root, data):
    """Verify this independent gate and every certified source in an install."""
    try:
        root = Path(root)
        if (type(data.get('schema')) is not int or data['schema'] != 2
                or data.get('version') != VERSION or data.get('status') != 'PASS'
                or data.get('quality_gate') != QUALITY_GATE
                or data.get('source_gate') != 'CURRENT_STANDALONE_VALIDATED'):
            return False
        checks = data.get('checks')
        if (not isinstance(checks, list) or len(checks) != len(VALIDATORS) + 1
                or any(not isinstance(check, dict) for check in checks)):
            return False
        if [c.get('validator') for c in checks] != [*VALIDATORS, BOOTSTRAP]:
            return False
        if any(type(c.get('returncode')) is not int or c['returncode'] != 0
               or not _valid_digest(c.get('output_sha256'))
               or not _valid_digest(c.get('source_sha256')) for c in checks):
            return False
        files = data.get('files')
        from systems.runtime_activation import REQUIRED
        if not isinstance(files, dict) or not set(REQUIRED) <= set(files):
            return False
        if BOOTSTRAP.replace('.', '/') + '.py' not in files:
            return False
        if not _valid_digest(data.get('validated_source_sha256')):
            return False
        for rel, digest in files.items():
            if (not isinstance(rel, str) or not rel or '\\' in rel or ':' in rel
                    or rel.startswith('/') or '..' in Path(rel).parts
                    or not _valid_digest(digest)):
                return False
            path = root / rel
            if path.is_symlink() or not path.is_file() or sha(path) != digest:
                return False
        # Reject added executable sources as well as changed/missing ones.
        if source_files(root) != files:
            return False
        return True
    except (OSError, ValueError, TypeError, KeyError, InstallError):
        return False


def install(target, root=ROOT):
    root = Path(root).resolve()
    target = Path(target).absolute()
    if target == root or root in target.parents:
        raise InstallError('New installation must be outside its source directory')
    if target.exists() or target.is_symlink():
        raise InstallError('Target must be a completely NEW absent directory')
    if not target.parent.is_dir() or target.parent.is_symlink():
        raise InstallError('Target parent must be an existing real directory')
    # No imported/external receipt is accepted: run the actual gate now.
    proof = validate(root)
    stage = Path(tempfile.mkdtemp(prefix='.Soulbound_current_install_', dir=target.parent))
    published = False
    try:
        copy_sources(root, stage, proof['installed_files'])
        if source_files(stage) != proof['installed_files']:
            raise InstallError('Copied source does not match validated source')
        bootstrap = _bootstrap(stage, stage / 'soulbound.db')
        if source_files(root) != proof['files'] or source_files(stage) != proof['installed_files']:
            raise InstallError('Sources changed after independent validation')
        marker = dict(proof, schema=2, status='PASS',
                      files=proof['installed_files'],
                      validated_source_sha256=hashlib.sha256(
                          json.dumps(proof['files'], sort_keys=True).encode()).hexdigest(),
                      source_gate='CURRENT_STANDALONE_VALIDATED',
                      checks=[*proof['checks'], bootstrap])
        marker.pop('installed_files', None)
        path = stage / MARKER
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(marker, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if not verify_marker(stage, marker):
            raise InstallError('Independent manifest verification failed')
        # os.rename never overwrites a nonempty directory; recheck absence to
        # refuse even an empty precreated target on all supported platforms.
        if target.exists() or target.is_symlink():
            raise InstallError('Target appeared during validation')
        os.rename(stage, target)
        published = True
        print('CURRENT STANDALONE INSTALL PASS: ' + str(target), flush=True)
        return target
    finally:
        if not published and stage.exists():
            shutil.rmtree(stage)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('validate')
    setup = commands.add_parser('install')
    setup.add_argument('--target', required=True)
    args = parser.parse_args(argv)
    if args.command == 'validate':
        proof = validate()
        print('CURRENT STANDALONE VALIDATION PASS: ' + str(len(proof['checks'])) + ' mandatory checks')
    else:
        install(args.target)

if __name__ == '__main__':
    main()
