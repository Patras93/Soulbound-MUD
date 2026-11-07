# -*- coding: utf-8 -*-
"""v108 single integration regression: signed candidate and v107 EQ compatibility.

No real user data, network, service, or Windows STOP. The installed marker
and runtime hashes are verified exactly as on a real Windows deployment.
"""
from __future__ import annotations
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import shutil
import tempfile
from unittest.mock import patch
import zipfile

from systems import v10800_activation as activation
from aktualizuj_soulbound import UpdateError, archive_mapping, run_update
from wdroz_v108_z_zewnatrz import preflight
from validation.v10700_production_eq_cutover_regression import DB, seed, CAT
from systems.v10700_live_equipment import activate_production_ledger
from validation.v10800_eq_rebuild_copy_regression import model
from world.dynamic_content import ITEMS

ROOT = Path(__file__).resolve().parents[1]


def run():
    checks = 0
    def ck(value, label):
        nonlocal checks
        assert value,label
        checks += 1

    ck(not activation.production_approved(), 'working tree authorized without external approval')
    with tempfile.TemporaryDirectory(prefix='soulbound108_real_cutdown_test_') as d:
        home = Path(d)
        live = home/'Soulbound-MUD'
        (live/'core').mkdir(parents=True)
        (live/'core/bootstrap_economy_professions.py').write_text('VERSION="107.00.0"\n',encoding='utf-8')
        (live/'VERSION').write_text('107.00.0\n',encoding='utf-8')
        # Synthetic but physically valid v107 SQLite, including an old
        # pre-cutover baseline and an intentionally stale worn slot.
        (live/'backups').mkdir()
        now, before = model()
        real_ids = [k for k,v in ITEMS.items() if isinstance(v,dict) and
                    v.get('type') in ('armor','weapon')][:3]
        assert len(real_ids)==3
        replacements = {'old':real_ids[0], 'new':real_ids[1], 'other':real_ids[2]}
        for connection in (now,before):
            for original_item, actual_item in replacements.items():
                for table in ('inventory','equipment'):
                    connection.execute(f'UPDATE {table} SET item_id=? WHERE item_id=?',
                                       (actual_item,original_item))
            if connection is now:
                for original_item, actual_item in replacements.items():
                    connection.execute('UPDATE v106_item_instances SET item_id=? WHERE item_id=?',
                                       (actual_item,original_item))
            connection.commit()
        with closing(sqlite3.connect(live/'soulbound.db')) as destination:
            now.backup(destination)
        with closing(sqlite3.connect(live/'backups'/'old.sqlite')) as destination:
            before.backup(destination)
        now.close();before.close()
        original = (live/'soulbound.db').read_bytes()
        new_zip = home/'Soulbound-MUD-v108.00.0-ONE-CANDIDATE-TEST.zip'
        from predeploy_nowej_wersji import REQUIRED as REQUIRED_PREDEPLOY
        names = set(activation.REQUIRED)|set(REQUIRED_PREDEPLOY)|{
            'server.py','CHANGELOG_PL.txt','START_Soulbound.bat',
            'STOP_Soulbound.bat','predeploy_check.py', 'VERSION',
            'validation/v10800_offline_suite.py'}
        with zipfile.ZipFile(new_zip,'w',zipfile.ZIP_DEFLATED) as z:
            for name in sorted(names):
                z.write(ROOT/name,name)
        approved = home/'Soulbound_PREDEPLOY'/'last_result_v108.json'
        approved.parent.mkdir()
        digest = hashlib.sha256(new_zip.read_bytes()).hexdigest()
        state = {'schema':1,'status':'PASS','quality_gate':'ULTIMATE-60-PLUS',
                 'completed_stages':60,'required_stages':60,'returncode':0,
                 'version':'108.00.0','installed_at_test':'107.00.0',
                 'zip':str(new_zip),'sha256':digest,'v108_release_gates_pass':True,
                 'v108_eq_rebuild_trial_pass':True}
        ck(not activation.verify_root_for_test(live),'uninstalled candidate authorized')
        for bad in ({}, {'v108_eq_rebuild_trial_pass':False},
                    {'v108_release_gates_pass':False},
                    {'completed_stages':59}, {'sha256':'f'*64},
                    {'installed_at_test':'106.00.0'}):
            approved.write_text(json.dumps({**state,**bad}),encoding='utf-8')
            if not bad:continue
            with patch('aktualizuj_soulbound.stop_local_server',side_effect=AssertionError('STOP before approval')):
                try:
                    preflight(live,new_zip)
                except UpdateError:
                    checks += 1
                else:raise AssertionError('preflight accepted forged proof')
            ck((live/'soulbound.db').read_bytes()==original,'failed preflight touched SQLite')
        approved.write_text(json.dumps(state),encoding='utf-8')
        from predeploy_v108_z_zewnatrz import preflight as preflight_test
        source, candidate_file = preflight_test(live,new_zip)
        ck(source==live and candidate_file==new_zip,'new external Windows PREDEPLOY rejected candidate')
        candidate, ver = preflight(live,new_zip)
        ck(candidate == new_zip and ver == '108.00.0','bridge rejected full candidate')
        from aktualizuj_soulbound import stage_release
        # The installer must reject a mutated/extraneous staging file before STOP,
        # even though the original official ZIP checksum and proof still pass.
        with tempfile.TemporaryDirectory(prefix='sb108_stage_consistency_') as staging_dir:
            staged=Path(staging_dir)
            with zipfile.ZipFile(new_zip) as approved_zip:
                stage_release(new_zip,staged,archive_mapping(approved_zip))
            ck(activation.activation_manifest(state,new_zip,staged)['schema']==2,
               'verified stage could not issue durable manifest')
            forged=staged/'server.py'
            actual=forged.read_bytes()
            forged.write_bytes(actual+b'\n# unexpected staged modification\n')
            try:activation.activation_manifest(state,new_zip,staged)
            except ValueError:checks+=1
            else:raise AssertionError('modified staged server was approved')
            forged.write_bytes(actual)
            extra=staged/'INJECTED_NOT_IN_ARCHIVE.txt'
            extra.write_text('not in verified ZIP',encoding='utf-8')
            try:activation.activation_manifest(state,new_zip,staged)
            except ValueError:checks+=1
            else:raise AssertionError('extra staged code accepted')
        with patch('aktualizuj_soulbound.stop_local_server',return_value=False) as stopped:
            backup = run_update(live,new_zip,'108.00.0',restart=False)
            ck(stopped.call_count == 1,'authorized installer did not stop once')
        ck((live/'VERSION').read_text().strip()=='108.00.0','updater did not install v108 version')
        ck((live/activation.MARKER).is_file(),'v108 marker missing after authorized install')
        ck(activation.verify_root_for_test(live),'installed exact source and ZIP refused')
        ck((live/'soulbound.db').read_bytes()!=original,
           'approved rebuild not committed to stopped production clone')
        with closing(sqlite3.connect(live/'soulbound.db')) as repaired_db:
            ck(repaired_db.execute('PRAGMA integrity_check').fetchone()[0]=='ok',
               'post-install SQLite integrity failed')
            ck(repaired_db.execute('SELECT COUNT(*) FROM v106_item_instances').fetchone()[0]==4,
               'expected two generated stage-zero copies after cutover')
        ck((backup/'soulbound.db').read_bytes()==original,'install backup lost SQLite')
        ck((backup/'VERSION').read_text().strip()=='107.00.0','backup does not preserve v107')
        # Fail AFTER new code has already been installed and AFTER a simulated
        # partial SQLite write. Both code and player data must revert to v107.
        rollback_live=home/'Rollback-Soulbound-MUD'
        shutil.copytree(backup,rollback_live)
        with closing(sqlite3.connect(rollback_live/'soulbound.db')) as before_fail:
            old_state=tuple(before_fail.iterdump())
        def simulated_write_failure(source, target):
            with closing(sqlite3.connect(target)) as modified:
                modified.execute('UPDATE inventory SET quantity=5000 WHERE account_id=1')
                modified.commit()
            raise RuntimeError('SYNTETYCZNY_BŁĄD_ZAPISU_SQLITE')
        with patch('aktualizuj_soulbound.stop_local_server',return_value=False), \
             patch('systems.v10800_eq_cutover_bridge.commit_verified_copy',
                   side_effect=simulated_write_failure):
            try:run_update(rollback_live,new_zip,'108.00.0',restart=False)
            except RuntimeError:checks+=1
            else:raise AssertionError('Simulator did not refuse failed database write')
        ck((rollback_live/'VERSION').read_text().strip()=='107.00.0',
           'SQLite failure did not roll back v107 code')
        with closing(sqlite3.connect(rollback_live/'soulbound.db')) as after_fail:
            ck(tuple(after_fail.iterdump())==old_state,
               'SQLite failure did not restore exact old data')
        ck(not (rollback_live/activation.MARKER).exists(),
           'Failed install left v108 approval manifest in old installation')
        # Tampering must revoke startup even with prior 60/60 PASS.
        modified = live/'server/mud_server.py'
        intact = modified.read_bytes()
        modified.write_bytes(intact+b'\n# unauthorised delta\n')
        ck(not activation.verify_root_for_test(live),'modified runtime source approved')
        modified.write_bytes(intact)
        ck(activation.verify_root_for_test(live),'restored source refused')
        # Once the installer commits, temporary PREDEPLOY output and ZIP are
        # no longer runtime dependencies. The durable manifest still binds
        # every critical source to the exact files installed from tested ZIP.
        approved.unlink()
        ck(activation.verify_root_for_test(live),'removed temporary PREDEPLOY blocked a certified restart')
        new_zip.unlink()
        ck(activation.verify_root_for_test(live),'deleted downloaded ZIP blocked a certified restart')
        # v107 worlds, classes and quests use the SAME activation gate as EQ.
        # They must stay enabled by a certified v108 installation after cleanup.
        from systems import v10700_activation as v107_auth
        with patch('systems.v10700_activation._approved',return_value=False), \
             patch('systems.v10800_activation.production_approved',
                   side_effect=lambda: activation.verify_root_for_test(live)):
            ck(v107_auth.enabled(), 'v107 quests/classes disabled after v108 PREDEPLOY cleanup')
        marker_file = live/activation.MARKER
        marker_json = json.loads(marker_file.read_text(encoding='utf-8'))
        ck(marker_json.get('schema') == 2,'installer did not install permanent versioned manifest')
        marker_json['completed_stages'] = 59
        marker_file.write_text(json.dumps(marker_json),encoding='utf-8')
        ck(not activation.verify_root_for_test(live),'corrupted permanent approval was accepted')
        marker_json['completed_stages'] = 60
        marker_json['files'].pop('server.py')
        marker_file.write_text(json.dumps(marker_json),encoding='utf-8')
        ck(not activation.verify_root_for_test(live),'missing source attestation was accepted')
        marker_json['files']['server.py'] = hashlib.sha256((live/'server.py').read_bytes()).hexdigest()
        marker_file.write_text(json.dumps(marker_json),encoding='utf-8')
        ck(activation.verify_root_for_test(live),'restored permanent manifest was rejected')
        marker_file.unlink()
        ck(not activation.verify_root_for_test(live),'missing permanent release manifest was accepted')
        marker_file.write_text(json.dumps(marker_json),encoding='utf-8')
        # Existing v107 EQ must be preserved by v108; never create a new v108
        # marker or new physical instances. Synthetic fixture and patched
        # approval ONLY: no actual game installation or source DB is accessed.
        with patch('systems.v10800_activation.production_approved',return_value=True):
            sample=home/'existing_v107_equipment.sqlite'
            db=DB(sample)
            seed(db)
            # The synthetic v107 fixture is initialized under v107 approval,
            # prior to the v108 production compatibility start.
            with patch('systems.v10700_activation.production_approved',return_value=True):
                ck(activate_production_ledger(db,CAT),'legacy v107 EQ test seed failed')
            physical={r[0] for r in db.conn.execute('SELECT instance_id FROM v106_item_instances')}
            ck(len(physical)==2,'legacy physical instances not initialized')
            ck(db.conn.execute("SELECT count(*) FROM sqlite_master WHERE name='v108_eq_production_cutover'").fetchone()[0]==0,
               'cancelled v108 migration was executed')
            db.conn.close()
            new_db=DB(sample)
            ck(activate_production_ledger(new_db,CAT),'v108 could not continue existing v107 EQ')
            ck({r[0] for r in new_db.conn.execute('SELECT instance_id FROM v106_item_instances')}==physical,
               'v108 restart changed v107 instance IDs')
            ck(new_db.conn.execute("SELECT count(*) FROM sqlite_master WHERE name='v108_eq_production_cutover'").fetchone()[0]==0,
               'v108 created a forbidden new EQ2 table')
            try: new_db.conn.execute("UPDATE inventory SET quantity=10 WHERE item_id='helm'")
            except sqlite3.DatabaseError: checks+=1
            else: raise AssertionError('raw v107 EQ write barrier bypassed')
            new_db.conn.close()
    return checks


if __name__=='__main__':
    print('V108 AKTYWACJA+INSTALATOR+ZACHOWANE EQ V107:',run(),'KONTROLI PASS',flush=True)
