# -*- coding: utf-8 -*-
"""Single WDRAZAM confirmation; never invoke an actual updater in this test."""
from __future__ import annotations
import json,tempfile,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import wdroz_po_predeploy as entry


def main():
    with tempfile.TemporaryDirectory(prefix='sb110_consent_') as folder:
        root=Path(folder)/'Soulbound-MUD';root.mkdir()
        archive=root/'Soulbound-MUD-v110.00.0-CANDIDATE.zip';archive.write_bytes(b'test only')
        statefile=Path(folder)/'approved.json'
        data=dict(status='PASS',quality_gate='ULTIMATE-60-PLUS',completed_stages=60,
                  required_stages=60,version='110.00.0',installed_at_test='109.00.0',
                  returncode=0,v110_release_gates_pass=True,zip=str(archive),
                  sha256='a'*64,finished_at='synthetic')
        statefile.write_text(json.dumps(data),encoding='utf-8')
        with patch.object(entry,'STATE',statefile),patch.object(entry,'ROOT',root),\
             patch.object(entry,'sha256',return_value='a'*64),\
             patch.object(entry,'inspect_zip',return_value=('110.00.0',{})),\
             patch.object(entry,'installed_version',return_value='109.00.0'),\
             patch.object(entry.subprocess,'call',return_value=0) as invoke:
            with patch('builtins.input',return_value='WDRAZAM V110'):
                assert entry.main()==2
                invoke.assert_not_called()
            with patch('builtins.input',return_value='WDRAZAM'):
                assert entry.main()==0
                invoke.assert_called_once()
            invoke.reset_mock()
            data['sha256']='b'*64
            statefile.write_text(json.dumps(data),encoding='utf-8')
            with patch('builtins.input',side_effect=AssertionError('No prompt on failed SHA')):
                assert entry.main()==1
                invoke.assert_not_called()
        print('V110 CONSENT: 3/3 PASS; exactly WDRAZAM; changed SHA blocked; no production operation',flush=True)

if __name__=='__main__':main()
