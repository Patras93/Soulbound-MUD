# -*- coding: utf-8 -*-
"""Adversarial upgrade bridge tests. Temporary fake installation, never STOP."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import wdroz_v107_z_zewnatrz as bridge
from aktualizuj_soulbound import UpdateError, file_version


def run():
    checks=0
    def ck(condition, message):
        nonlocal checks
        assert condition, message
        checks += 1
    with tempfile.TemporaryDirectory(prefix='soulbound107-upgrade-test-') as temp:
        parent=Path(temp)
        live=parent/'Soulbound-MUD'
        (live/'core').mkdir(parents=True)
        (live/'core/bootstrap_economy_professions.py').write_text("VERSION='106.00.0'\n",encoding='utf-8')
        (live/'VERSION').write_text('106.00.0',encoding='utf-8')
        (live/'soulbound.db').write_bytes(b'PRIVATE_PLAYER_DATA_SHOULD_NEVER_CHANGE')
        before=(live/'soulbound.db').read_bytes()
        approved=parent/'Soulbound_PREDEPLOY'/'last_result.json'
        approved.parent.mkdir()
        archive=parent/'Soulbound-MUD-v107.00.0-TESTY-POMOSTU.zip'
        # v108 carries the historical v107 bridge to prevent regressions. A
        # separate, synthetic v107 candidate is required for this old test.
        candidate_root=parent/'candidate107'
        candidate_root.mkdir()
        entries=set(bridge.REQUIRED_CANDIDATE_FILES)|{
            'core/bootstrap_economy_professions.py','server.py','CHANGELOG_PL.txt',
            'START_Soulbound.bat','STOP_Soulbound.bat','predeploy_check.py'}
        for rel in sorted(entries):
            target=candidate_root/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            if rel == 'VERSION':
                target.write_text('107.00.0\n',encoding='utf-8')
            elif rel == 'core/bootstrap_economy_professions.py':
                txt=(ROOT/rel).read_text(encoding='utf-8-sig').replace(
                    'VERSION = "108.00.0"','VERSION = "107.00.0"')
                target.write_text(txt,encoding='utf-8')
            else:
                target.write_bytes((ROOT/rel).read_bytes())
        bridge.ROOT=candidate_root
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for rel in sorted(entries):
                z.write(candidate_root/rel,rel)
        sha=hashlib.sha256(archive.read_bytes()).hexdigest()
        payload=dict(status='PASS',quality_gate='ULTIMATE-60-PLUS',
            completed_stages=60,required_stages=60,returncode=0,
            version='107.00.0',installed_at_test='106.00.0',zip=str(archive),sha256=sha)
        with patch('validation.v10700_release_readiness.unmet_requirements',return_value=()):
            try:
                bridge.preflight(live,archive)
            except (UpdateError,FileNotFoundError):
                checks+=1
            else:raise AssertionError('Absent approval accepted')
            approved.write_text(json.dumps(payload),encoding='utf-8')
            chosen,version=bridge.preflight(live,archive)
            ck(chosen==archive and version=='107.00.0','legitimate authorized test fixture rejected')
            altered=dict(payload,sha256='0'*64)
            approved.write_text(json.dumps(altered),encoding='utf-8')
            try:bridge.preflight(live,archive)
            except UpdateError:checks+=1
            else:raise AssertionError('wrong SHA accepted')
            altered=dict(payload,completed_stages=59)
            approved.write_text(json.dumps(altered),encoding='utf-8')
            try:bridge.preflight(live,archive)
            except UpdateError:checks+=1
            else:raise AssertionError('partial 59/60 accepted')
            altered=dict(payload,zip=str(parent/'different.zip'))
            approved.write_text(json.dumps(altered),encoding='utf-8')
            try:bridge.preflight(live,archive)
            except UpdateError:checks+=1
            else:raise AssertionError('another ZIP accepted')
            altered=dict(payload,installed_at_test='105.00.0')
            approved.write_text(json.dumps(altered),encoding='utf-8')
            try:bridge.preflight(live,archive)
            except UpdateError:checks+=1
            else:raise AssertionError('wrong installed version accepted')
            approved.write_text(json.dumps(payload),encoding='utf-8')
            with patch.object(bridge,'REQUIRED_CANDIDATE_FILES',
                              bridge.REQUIRED_CANDIDATE_FILES+('nonexistent_file.py',)):
                try:bridge.preflight(live,archive)
                except UpdateError:checks+=1
                else:raise AssertionError('external unverified source file accepted')
            # An injected *real* blocker must still stop even a cryptographically
        # correct approval. The tested code may now legitimately be ready.
        with patch('validation.v10700_release_readiness.unmet_requirements',
                   return_value=('symulowany nierozwiazany blad EQ',)):
            try:bridge.preflight(live,archive)
            except UpdateError as exc:
                ck('blokad produkcyjnych' in str(exc),
                   'production blocker was not respected')
            else:raise AssertionError('a known blocker was bypassed by 60/60 result')
        ck(file_version(live/'core/bootstrap_economy_professions.py')=='106.00.0',
           'installation changed')
        ck((live/'soulbound.db').read_bytes()==before,'private database changed')
        ck(not any(live.glob('*BACKUP*')),'unwanted backup attempt')
    return checks

if __name__=='__main__':
    print('V107 INSTALATOR POMOST WINDOWS:',run(),'PASS',flush=True)
