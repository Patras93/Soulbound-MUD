# -*- coding: utf-8 -*-
"""Production-mode v107 catalogue bootstrap using a synthetic certified ZIP.

No real approval file, installed server, player DB, TCP or live directory is read
or changed. Verifies that release gating is not an empty string/regex check.
"""
from __future__ import annotations
import hashlib
import ast
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems import v10700_activation as activation


def run():
    checks=0
    def ck(state,reason):
        nonlocal checks
        assert state,reason
        checks+=1
    prior_stage=os.environ.pop('SOULBOUND_V107_STAGING',None)
    try:
        with tempfile.TemporaryDirectory(prefix='v107-authorized-boot-') as home:
            home=Path(home);live=home/'Soulbound-MUD';live.mkdir()
            (live/'VERSION').write_text('107.00.0\n',encoding='utf-8')
            for rel in activation.REQUIRED:
                file=live/rel;file.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/rel,file)
            ck(not activation.verify_root_for_test(live),'Unapproved VERSION=107 enabled')
            archive=home/'Soulbound-MUD-v107.00.0-AUTH-FIXTURE.zip'
            with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
                for rel in activation.REQUIRED:z.write(live/rel,rel)
            sha=hashlib.sha256(archive.read_bytes()).hexdigest()
            approval=home/'Soulbound_PREDEPLOY'/'last_result.json'
            approval.parent.mkdir()
            marker=live/activation.MARKER
            marker.parent.mkdir(exist_ok=True)
            marker.write_text(json.dumps(dict(schema=1,version='107.00.0',sha256=sha)),encoding='utf-8')
            ck(not activation.verify_root_for_test(live),'Marker without full PASS enabled')
            payload=dict(status='PASS',quality_gate='ULTIMATE-60-PLUS',
                         completed_stages=59,required_stages=60,returncode=0,
                         version='107.00.0',installed_at_test='106.00.0',
                         zip=str(archive),sha256=sha)
            approval.write_text(json.dumps(payload),encoding='utf-8')
            ck(not activation.verify_root_for_test(live),'59/60 enabled production')
            payload['completed_stages']=60
            payload['sha256']='f'*64
            approval.write_text(json.dumps(payload),encoding='utf-8')
            ck(not activation.verify_root_for_test(live),'Altered approval SHA enabled production')
            payload['sha256']=sha
            approval.write_text(json.dumps(payload),encoding='utf-8')
            ck(activation.verify_root_for_test(live),'Valid fixture rejected')
            with (live/'core/archetypes/chaos.py').open('ab') as fp:fp.write(b'\n# altered\n')
            ck(not activation.verify_root_for_test(live),'Modified source code enabled production')
            shutil.copyfile(ROOT/'core/archetypes/chaos.py',live/'core/archetypes/chaos.py')
            ck(activation.verify_root_for_test(live),'Restored exact source rejected')
            previous_root=activation.ROOT
            activation.ROOT=live
            activation._approved.cache_clear()
            try:
                ck(activation.enabled(),'Normal mode did not enable approved v107')
                # NEVER import server.py here: its import opens TCP and loads the
                # entire game, making a unit regression hang and bind port 4000.
                # Assert the actual server bootstrap hooks the certified-only
                # function, then exercise the *same* cap migration on the fixture.
                source=(ROOT/'server.py').read_text(encoding='utf-8')
                tree=ast.parse(source)
                hooks=[node for node in tree.body if isinstance(node,ast.If)
                       and isinstance(node.test,ast.Call)
                       and isinstance(node.test.func,ast.Name)
                       and node.test.func.id=='_sb107_runtime_enabled']
                ck(any(any(
                    isinstance(stmt,ast.Expr) and isinstance(stmt.value,ast.Call)
                    and isinstance(stmt.value.func,ast.Name)
                    and stmt.value.func.id=='_v107_uncap'
                    for stmt in hook.body) for hook in hooks),
                    'Certified v107 cap activation is no longer wired into server bootstrap')
                from core import live_level_caps_v5200 as caps
                caps_path=live/'LIVE_CONTENT'/'admin_level_caps.json'
                caps.load(path=caps_path,apply=False)
                ck(caps.activate_v107_uncapped_defaults(path=caps_path) is True,
                   'Certified caps migration not executed on disposable fixture')
                ck(caps.cap('postac') is None and caps.cap('profesje') is None
                   and caps.cap('narzedzia') is None and caps.cap('eq') is None,
                   'Old 800 caps did not migrate on certified live bootstrap')
                ck(caps.cap('ulepszenia_eq')==10,
                   'EQ +10 smithing cap incorrectly removed')
                from core.progression_resources import character_xp_to_next
                ck(character_xp_to_next(801)>0,
                   'Character progression still stops at 800 after migration')
                persisted=json.loads((live/'LIVE_CONTENT'/'admin_level_caps.json').read_text(encoding='utf-8'))
                ck(persisted.get('caps',{}).get('postac') is None,
                   'Caps migration not persisted atomically')
                # A previously customized administrator config MUST NOT change.
                custom=live/'LIVE_CONTENT'/'admin_custom_caps.json'
                customized=dict(caps.DEFAULTS,postac=1200)
                caps._atomic_write(customized,custom)
                caps.load(path=custom,apply=False)
                ck(caps.activate_v107_uncapped_defaults(path=custom) is False,
                   'An owner-defined level cap was overwritten')
                ck(caps.cap('postac')==1200 and caps.cap('profesje')==800,
                   'Preserving a customized cap unexpectedly changed data')
                # The full 30-class / 2000-quest bootstrap is validated by
                # v10700_consolidated_content_regression; this test only
                # exercises certification, the actual caps hook, and rollback
                # behavior without opening a TCP listener on port 4000.
                ck(any(any(isinstance(stmt,ast.Import) and any(
                    alias.name=='core.classes_skills' for alias in stmt.names)
                    for stmt in hook.body) for hook in hooks),
                    'Production catalogue installer is not wired to certified bootstrap')
            finally:
                activation.ROOT=previous_root
                activation._approved.cache_clear()
    finally:
        if prior_stage is not None:os.environ['SOULBOUND_V107_STAGING']=prior_stage
    return checks

if __name__=='__main__':print('V107 AUTORYZOWANY BOOTSTRAP:',run(),'PASS',flush=True)
