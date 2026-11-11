# -*- coding: utf-8 -*-
"""Prove that running v108 PREDEPLOY cannot overwrite live v107 approval.

Only temporary synthetic files are used. No real server, player DB, GitHub,
network access, version change, or installed-game mutation.
"""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import predeploy_nowej_wersji as core_predeploy
import predeploy_v108_z_zewnatrz as bridge


def run():
    checks = 0

    def ck(value, message):
        nonlocal checks
        assert value, message
        checks += 1

    with TemporaryDirectory(prefix='sb108_safe_approval_isolation_') as temp:
        home = Path(temp)
        live = home / 'Soulbound-MUD'
        live.mkdir()
        synthetic_db = live/'soulbound.db'
        synthetic_db.write_bytes(b'ONLY SYNTHETIC TEST DB - DO NOT MODIFY')
        original_db = synthetic_db.read_bytes()
        archive = home/'Soulbound-MUD-v108.00.0-SYNTHETIC.zip'
        archive.write_bytes(b'NOT A REAL CANDIDATE - ONLY A FIXTURE')
        work = home/'Soulbound_PREDEPLOY'
        work.mkdir()
        approval107 = work/'last_result.json'
        original_approval = json.dumps({
            'status':'PASS','version':'107.00.0','sha256':'v107-PINNED-SYNTHETIC',
            'quality_gate':'ULTIMATE-60-PLUS','completed_stages':60,
        },sort_keys=True).encode('utf-8')
        approval107.write_bytes(original_approval)
        marker = live/'LIVE_CONTENT'/'v107_release_activation.json'
        marker.parent.mkdir()
        marker.write_bytes(b'V107 SYNTHETIC MARKER')
        original_marker = marker.read_bytes()
        original_globals=(core_predeploy.ROOT,core_predeploy.WORK,core_predeploy.STATE,
                          core_predeploy.INBOX)
        try:
            for outcome in ('PASS','FAIL'):
                def mocked_predeploy(args):
                    ck(args==[str(archive)],'external bridge did not pass exact candidate')
                    ck(core_predeploy.STATE == work/'last_result_v108.json',
                       'v108 bridge still targets v107 last_result.json')
                    core_predeploy.save_state({'version':'108.00.0','status':outcome})
                    return 0 if outcome=='PASS' else 1

                with patch.object(bridge,'preflight',return_value=(live,archive)), \
                     patch.object(core_predeploy,'main',side_effect=mocked_predeploy):
                    code=bridge.main(['--instalacja',str(live),'--zip',str(archive)])
                ck(code==(0 if outcome=='PASS' else 1),
                   'external bridge changed test outcome')
                state=json.loads((work/'last_result_v108.json').read_text(encoding='utf-8'))
                ck(state=={'version':'108.00.0','status':outcome},
                   'v108 state was not saved separately')
                ck(approval107.read_bytes()==original_approval,
                   'v108 PREDEPLOY overwrote v107 production approval')
                ck(marker.read_bytes()==original_marker,
                   'v108 PREDEPLOY changed installed v107 marker')
                ck(synthetic_db.read_bytes()==original_db,
                   'v108 PREDEPLOY changed a production-like DB fixture')
        finally:
            core_predeploy.ROOT,core_predeploy.WORK,core_predeploy.STATE,core_predeploy.INBOX = original_globals
    return checks


if __name__=='__main__':
    print('V108 ODDZIELENIE PREDEPLOY OD DZIALAJACEJ V107:',run(),'KONTROLI PASS; NIE WDRAZAC')
