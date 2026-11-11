# -*- coding: utf-8 -*-
"""Production must not retain historical PREDEPLOY modules or need obsolete files."""
from __future__ import annotations
import hashlib
import ast
import json
from pathlib import Path
import tempfile
import zipfile

from aktualizuj_soulbound import (
    v111_live_release_mapping, retire_certified_v111_test_files,
    V111_CANDIDATE_ONLY_ROOT_FILES, V111_CANDIDATE_ONLY_PYTHON_FILES,
)
from systems.v11000_activation import CORE
from core.runtime_manifest import FULL_AUDIT_ONLY_MODULES
from systems.v11100_holiday_activation import REQUIRED


def main():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='sb111_minimal_runtime_') as td:
        tmp=Path(td)
        archive=tmp/'all.zip'
        with zipfile.ZipFile(archive,'w') as z:
            for rel in ('VERSION','server.py','predeploy_check.py',
                        'START_Soulbound.bat','STOP_Soulbound.bat',
                        'core/bootstrap_economy_professions.py',
                        'validation/v11100_server_smoke.py',
                        'validation/v4200_virtual_source.py',
                        'validation/__init__.py',
                        'world/runtime_gameplay_finalize.py',
                        'admin/architecture_audit_v0390.py',
                        'systems/v11000_retired_installers.py',
                        'world/quests/__init__.py',
                        'world/quests/base_01.py',
                        'world/quests/base_02.py',
                        'world/quests/base_03.py',
                        'world/quests/classes.py',
                        'world/quests/races.py',
                        'world/quests/events.py',
                        'world/quests/regional.py',
                        *(rel for rel in sorted(V111_CANDIDATE_ONLY_PYTHON_FILES)
                          if rel not in ('admin/audits.py',
                             'admin/v410_equipment_audits.py',
                             'systems/full_systems_audit_v03062.py')
                          and (root/rel).is_file())):
                z.write(root/rel,'Soulbound-MUD/'+rel)
        from aktualizuj_soulbound import archive_mapping
        with zipfile.ZipFile(archive) as z:
            mapping=archive_mapping(z)
        subset=v111_live_release_mapping(mapping)
        assert Path('server.py') in subset
        assert Path('predeploy_check.py') not in subset
        assert Path('validation/v11100_server_smoke.py') not in subset
        assert Path('validation/v4200_virtual_source.py') not in subset
        assert Path('validation/__init__.py') not in subset
        assert all(p.parts[0]!='validation' for p in subset)
        assert V111_CANDIDATE_ONLY_PYTHON_FILES
        assert all(Path(rel) in mapping and Path(rel) not in subset
                   for rel in V111_CANDIDATE_ONLY_PYTHON_FILES
                   if rel not in ('admin/audits.py',
                       'admin/v410_equipment_audits.py',
                       'systems/full_systems_audit_v03062.py')
                   and (root/rel).is_file())
        # Candidate-only audit/rehearsal modules must not enter the server's
        # runtime graph (including the historical-compatibility module lane).
        from core.runtime_manifest import RUNTIME_MODULES, FULL_RUNTIME_MODULES
        assert not V111_CANDIDATE_ONLY_PYTHON_FILES.intersection(RUNTIME_MODULES)
        assert not (V111_CANDIDATE_ONLY_PYTHON_FILES - {'admin/audits.py','systems/full_systems_audit_v03062.py'}).intersection(FULL_RUNTIME_MODULES)
        # No duplicate historical quest modules may enter the live install.
        for name in ('base_01','base_02','base_03','classes','races','events','regional'):
            assert Path(f'world/quests/{name}.py') in subset
        # Verify the *current* canonical quest catalogue directly.
        # The PREDEPLOY fixture has deliberately omitted all v109/v110
        # historical copies; neither the installer nor this gate may need them.
        from world.quests import base_01, base_02, base_03
        catalogs=[part.build_catalog() for part in (base_01,base_02,base_03)]
        assert sum(len(rows) for rows in catalogs)==46
        all_keys=[key for rows in catalogs for key in rows]
        assert len(all_keys)==len(set(all_keys))
        assert 'mirella_jewel_iron' in all_keys
        for rows in catalogs:
            assert all(isinstance(key,str) and isinstance(quest,dict)
                       and quest.get('name') and quest.get('giver')
                       for key,quest in rows.items())
        from world.quests import classes,races,events,regional
        assert all(callable(getattr(part,'rows',None))
                   for part in (classes,races,events))
        assert callable(getattr(regional,'produce_regional',None))
        for obsolete in ('data/catalogs_v109/quests_01.py',
                         'data/catalogs_v109/quests_02.py',
                         'data/catalogs_v109/quests_03.py',
                         'world/quests_v110/classes.py',
                         'world/quests_v110/races.py',
                         'world/quests_v110/events.py',
                         'world/quests_v110/regional.py'):
            assert Path(obsolete) not in mapping
        assert Path('world/quests/__init__.py') in subset
        assert Path('world/runtime_gameplay_finalize.py') in subset
        assert Path('admin/runtime_gameplay_v111.py') not in subset
        for obsolete in ('core/source_contracts.py',
                         'storage/big_number_events_v10400.py',
                         'storage/big_number_ledger_v10400.py'):
            assert Path(obsolete) in mapping
            assert Path(obsolete) not in subset
        assert Path('admin/audits.py') not in subset
        assert Path('systems/full_systems_audit_v03062.py') not in subset
        assert Path('admin/audit_rules_v406.py') not in subset
        # These four gameplay functions are now native v111; baseline
        # fingerprints and live shop-smoke tests replace comparisons against
        # a historical admin/v410 audit file.
        current=ast.parse((root/'world/runtime_gameplay_finalize.py').read_text(encoding='utf8'))
        required_functions={'refresh_help_v03021_full': '793d59d8179320859d91de10991088b5fb1d93b4b2a4cb2597d9895dccc140ec', 'apply_separate_class_shops_v03036': '2ded2ef4f70b5f8c3843a5d70cc78449a1a43a0f859bbbe9b94a5a19ebad4333', 'class_shop_audit_v03036': '8c7527ddd2097d74824f11946169537f56811e93c816fd75418dda99baa6712a', 'refresh_material_stat_profiles_v03037': '2e87c2a6c39f9035843bcb4e88667fee72aa4f24ed2c0e9378f5456034b5bb41'}
        for name,expected in required_functions.items():
            found=[node for node in current.body
                   if isinstance(node,ast.FunctionDef) and node.name==name]
            assert len(found)==1,name
            assert hashlib.sha256(ast.dump(found[0],include_attributes=False).encode()).hexdigest()==expected,name
        assert 'admin.v410_equipment_audits' not in (root/'world/runtime_gameplay_finalize.py').read_text('utf8')
        assert Path('admin/v410_equipment_audits.py') not in mapping
        assert Path('admin/v410_release_audits.py') not in subset
        # Every production gameplay-side effect from the historical mixed
        # audit module must remain in the slim runtime in its original order.
        # This guards HELP writers, quest/reward changes, class-shop updates,
        # and the final HELP truth pass without retaining obsolete audits.
        from core.runtime_manifest import AUDIT_RUNTIME_MODULES
        assert 'world/runtime_gameplay_finalize.py' in RUNTIME_MODULES
        assert 'admin/audits.py' not in RUNTIME_MODULES
        assert 'systems/full_systems_audit_v03062.py' not in RUNTIME_MODULES
        assert 'admin/audits.py' in AUDIT_RUNTIME_MODULES
        assert 'systems/full_systems_audit_v03062.py' in AUDIT_RUNTIME_MODULES
        # No dependency on admin/audits.py: current world mutations are
        # checked against a review-locked v111 source contract.  The server
        # smoke separately verifies their actual effects on classes/NPC/HELP.
        projected = ast.parse((root/'world/runtime_gameplay_finalize.py').read_text(encoding='utf8'))
        def gameplay_statement(node):
            if isinstance(node,(ast.For,ast.While,ast.If)):
                return True
            if isinstance(node,ast.Assign):
                targets=[name.id for target in node.targets for name in ast.walk(target)
                         if isinstance(name,ast.Name)]
                return not targets or all('AUDIT' not in name.upper()
                    and not name.startswith('_FINAL_HELP_ERRORS') for name in targets)
            if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call):
                return not (isinstance(node.value.func,ast.Attribute) and
                    isinstance(node.value.func.value,ast.Name) and
                    node.value.func.value.id=='_FINAL_HELP_ERRORS_V11197')
            return False
        effects=[ast.dump(node,include_attributes=False)
                 for node in projected.body if gameplay_statement(node)]
        assert len(effects)==259
        assert hashlib.sha256('\n'.join(effects).encode()).hexdigest()=='e7fc9db869fd465523af97aa5cf6403dd6759e1fbcb2edc06d7c8f6056ede937'
        assert not any(isinstance(node,ast.Import) and
                       any(alias.name=='admin.v410_release_audits' for alias in node.names)
                       for node in projected.body)
        assert Path('admin/architecture_audit_v0390.py') not in subset
        assert Path('systems/v11000_retired_installers.py') not in subset
        assert all(p.as_posix() not in FULL_AUDIT_ONLY_MODULES for p in subset)
        # Current code lives with its owning system, not in test modules.
        imports = {
            'core/source_contracts.py',
            'systems/eq_migration/ledger_copy.py',
            'systems/eq_migration/locations.py',
        }
        for rel in imports:
            assert (root/rel).is_file(), ('missing current runtime source', rel)
        # v111's production-neutral test must inspect live sources rather
        # than require retired administrative audit files to be present.
        for rel in ('world/runtime_gameplay_finalize.py',
                    'admin/city_services_fast_v1225.py',
                    'admin/fast_predeploy_audit_v0571.py',
                    'systems/v10700_live_equipment.py',
                    *sorted(imports)):
            tree=ast.parse((root/rel).read_text(encoding='utf8'))
            assert not any(isinstance(n,ast.ImportFrom) and n.module and
                           n.module.startswith('validation') for n in ast.walk(tree)),rel


        # A properly certified v110 installation may retire an unchanged
        # obsolete audit; a locally edited file must never be deleted.
        previous=tmp/'previous'; previous.mkdir()
        (previous/'LIVE_CONTENT').mkdir()
        approved={}
        for name in CORE:
            path=previous/name;path.parent.mkdir(parents=True,exist_ok=True)
            data=b'110.00.0\n' if name=='VERSION' else (name+'\n').encode()
            path.write_bytes(data)
            approved[name]=hashlib.sha256(data).hexdigest()
        for name in ('validation/old_certified_test.py', 'validation/modified_test.py'):
            path=previous/name;path.parent.mkdir(parents=True,exist_ok=True)
            data=(name+'\n').encode();path.write_bytes(data)
            approved[name]=hashlib.sha256(data).hexdigest()
        record=dict(schema=1,version='110.00.0',status='PASS',
                    quality_gate='ULTIMATE-60-PLUS',source_gate='WINDOWS_PREDEPLOY_APPROVED',
                    archive_sha256='a'*64,files=approved)
        (previous/'LIVE_CONTENT/release_current.json').write_text(json.dumps(record),encoding='utf8')
        installed=tmp/'live';installed.mkdir()
        for name in approved:
            p=installed/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes((previous/name).read_bytes())
        changed=installed/'validation/modified_test.py'
        changed.write_bytes(changed.read_bytes()+b'# local owner change\n')
        stage=tmp/'stage';stage.mkdir()
        (stage/'VERSION').write_text('111.00.0',encoding='utf8')
        assert retire_certified_v111_test_files(installed,stage,previous)==2
        assert not (installed/'systems/v11000_retired_installers.py').exists()
        assert not (installed/'validation/old_certified_test.py').exists()
        assert changed.is_file()
        # Missing or forged historical approval cannot authorize deletion.
        (installed/'validation/old_certified_test.py').write_bytes(b'old\n')
        record['archive_sha256']='bad'
        (previous/'LIVE_CONTENT/release_current.json').write_text(json.dumps(record),encoding='utf8')
        assert retire_certified_v111_test_files(installed,stage,previous)==0
        assert (installed/'validation/old_certified_test.py').exists()
    # An already-approved v111 install may also safely retire 9 recently
    # classified PREDEPLOY-only modules, without touching local edits.
    with tempfile.TemporaryDirectory(prefix='sb111_upgrade_retirement_') as td:
        tmp=Path(td); previous=tmp/'previous';installed=tmp/'live';stage=tmp/'stage'
        previous.mkdir();installed.mkdir();stage.mkdir()
        (stage/'VERSION').write_text('111.00.0',encoding='utf8')
        from systems.v11100_holiday_activation import REQUIRED as v111_required
        from systems.v11100_holiday_activation import verify as verify_v111
        approved={}
        for name in (*v111_required,
                     'admin/cross_system_audit_v1001.py',
                     'systems/v106_raid_combat_forecast.py',
                     'core/generator_core.py'):
            path=previous/name;path.parent.mkdir(parents=True,exist_ok=True)
            data=b'111.00.0\n' if name=='VERSION' else (name+'\n').encode()
            path.write_bytes(data)
            live=installed/name;live.parent.mkdir(parents=True,exist_ok=True)
            live.write_bytes(data)
            approved[name]=hashlib.sha256(data).hexdigest()
        locally_modified=installed/'systems/v106_raid_combat_forecast.py'
        locally_modified.write_bytes(locally_modified.read_bytes()+b'# user edit\n')
        record=dict(schema=1,version='111.00.0',status='PASS',
                    quality_gate='ULTIMATE-60-PLUS',source_gate='WINDOWS_PREDEPLOY_APPROVED',
                    archive_sha256='a'*64,files=approved)
        for base in (previous,installed):
            marker=base/'LIVE_CONTENT/release_current.json'
            marker.parent.mkdir(parents=True,exist_ok=True)
            marker.write_text(json.dumps(record),encoding='utf8')
        assert verify_v111(previous)
        assert retire_certified_v111_test_files(installed,stage,previous)==2
        assert not (installed/'admin/cross_system_audit_v1001.py').exists()
        assert not (installed/'core/generator_core.py').exists()
        assert locally_modified.is_file()
        # Both a missing and a forged prior manifest must reject cleanup.
        (installed/'admin/cross_system_audit_v1001.py').write_text('old',encoding='utf8')
        (previous/'LIVE_CONTENT/release_current.json').unlink()
        assert retire_certified_v111_test_files(installed,stage,previous)==0
        assert (installed/'admin/cross_system_audit_v1001.py').is_file()
    # The production manifest never demands an offline test module.
    assert not any(rel.startswith('validation/') for rel in REQUIRED)
    assert not V111_CANDIDATE_ONLY_PYTHON_FILES.intersection(REQUIRED)
    assert 'systems/v11000_retired_installers.py' not in REQUIRED
    assert not any(Path(rel).name in V111_CANDIDATE_ONLY_ROOT_FILES for rel in REQUIRED)
    # Only v111 live assembly remains in the launch path, not version 40/50.
    code=(root/'server.py').read_text(encoding='utf8')
    assert "if VERSION == '40.00.0':" not in code
    assert "if VERSION == '101.00.0':" not in code
    assert 'if _sb107_runtime_enabled():' in code
    print(f'V111 MINIMAL LIVE GATE PASS: zero validation runtime files, {len(V111_CANDIDATE_ONLY_PYTHON_FILES)} candidate-only Python files excluded, production profile, certified cleanup, '
          'modified-file preservation, invalid manifest refusal, no obsolete source branches')

if __name__=='__main__':main()
