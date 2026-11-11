"""Static import-closure and isolated composition checks for the current runtime.

Does not open sockets, run a game server, or access a player database.
"""
from __future__ import annotations

import ast
from collections import deque
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0,str(ROOT))

from core import native_runtime, runtime_rules
from core.runtime_manifest import EXPLICIT_RUNTIME_EXPORTS, RUNTIME_MODULES

FORBIDDEN_MODULES={
    'core.legacy_function_binding_v410','core.legacy_method_binding_v4200',
    'systems.v10700_activation','systems.v10800_activation',
    'systems.v10900_activation','systems.v10900_staging_guard',
    'systems.v11000_activation','systems.v11100_holiday_activation',
}
EXPECTED_RULES=frozenset({
    '_boss_floor_chest_spec','boss_floor_identity','boss_key_for_template',
    'create_infinite_astral_floor_definition','create_infinite_crypt_floor_definition',
    'create_infinite_magitek_floor_definition','normalize_profession_name',
    'v0100_instance_spec','v0150_environment_bonus','v0190_apply_combat_template',
    'v0190_combat_reward','v0927_guild_building_upgrade_cost',
    'v0927_guild_hall_upgrade_cost',
})


def module_name(path):
    return path[:-3].replace('/','.').removesuffix('.__init__')


def dependencies(tree,path):
    """Resolve ordinary relative imports and literal dynamic import targets."""
    own=module_name(path)
    package=own if path.endswith('/__init__.py') else own.rpartition('.')[0]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            for alias in node.names:
                yield alias.name,None,node.lineno
        elif isinstance(node,ast.ImportFrom):
            if node.level:
                parts=package.split('.') if package else []
                if node.level>len(parts):
                    yield '<invalid-relative>',None,node.lineno
                    continue
                base='.'.join(parts[:len(parts)-node.level+1])
                if node.module:
                    base+='.'+node.module
            else:
                base=node.module or ''
            for alias in node.names:
                yield base,alias.name,node.lineno
        elif isinstance(node,ast.Call):
            fn=node.func
            name=fn.id if isinstance(fn,ast.Name) else (
                fn.value.id+'.'+fn.attr if isinstance(fn,ast.Attribute)
                and isinstance(fn.value,ast.Name) else '')
            if name in {'__import__','importlib.import_module'} and node.args:
                target=node.args[0]
                if isinstance(target,ast.Constant) and isinstance(target.value,str):
                    yield target.value,None,node.lineno


def inspect_closure(files,seeds):
    modules={module_name(path):path for path in files if path.endswith('.py')}
    internal_roots={name.split('.')[0] for name in modules}
    pending=deque(seeds)
    visited=set()
    missing=[]
    forbidden=[]
    while pending:
        path=pending.popleft()
        if path in visited:
            continue
        if path not in files:
            missing.append((path,0,'missing_entrypoint'))
            continue
        visited.add(path)
        source=files[path]
        tree=ast.parse(source,filename=path)
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom) and node.module=='types':
                if any(alias.name=='FunctionType' for alias in node.names):
                    forbidden.append((path,node.lineno,'types.FunctionType_import'))
            if isinstance(node,ast.Call):
                function=node.func
                name=function.id if isinstance(function,ast.Name) else (
                    function.attr if isinstance(function,ast.Attribute) else '')
                if name in {'FunctionType','bind_legacy_method_v4200','bind_legacy_function_v410',
                            '_sb420_bind','_sb410_bind','_sb420_topbind'}:
                    forbidden.append((path,node.lineno,'function_namespace_binding:'+name))
        for target,member,line in dependencies(tree,path):
            if target in FORBIDDEN_MODULES or target.startswith('player.session_methods_v4200'):
                forbidden.append((path,line,target))
            candidates=[target]
            if member and member!='*' and target+'.'+member in modules:
                candidates.append(target+'.'+member)
            for name in candidates:
                if name in modules:
                    pending.append(modules[name])
                    parts=name.split('.')
                    for depth in range(1,len(parts)):
                        parent='.'.join(parts[:depth])
                        if parent in modules:
                            pending.append(modules[parent])
                elif name=='<invalid-relative>':
                    missing.append((path,line,name))
                elif name and name.split('.')[0] in internal_roots:
                    # Namespace packages are valid without an __init__.py.
                    if not any(known.startswith(name+'.') for known in modules):
                        missing.append((path,line,name))
    return {'modules':sorted(visited),'missing':missing,'forbidden':forbidden}


class ExplicitRuntimeRegression(unittest.TestCase):
    def test_every_active_module_declares_an_export_contract(self):
        self.assertTrue(RUNTIME_MODULES)
        self.assertEqual(len(RUNTIME_MODULES),len(set(RUNTIME_MODULES)))
        self.assertEqual(set(RUNTIME_MODULES)-set(EXPLICIT_RUNTIME_EXPORTS),set())
        for relative in RUNTIME_MODULES:
            self.assertTrue((ROOT/relative).is_file(),relative)
            exports=EXPLICIT_RUNTIME_EXPORTS[relative]
            self.assertIsInstance(exports,tuple)
            self.assertEqual(len(exports),len(set(exports)),relative)
            self.assertTrue(all(isinstance(name,str) and name.isidentifier() for name in exports),relative)

    def test_actual_loader_has_no_namespace_seeding_or_function_cloning(self):
        tree=ast.parse((ROOT/'core/native_runtime.py').read_text('utf-8-sig'))
        names={n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        self.assertFalse(names&{'_seed_module','_sync_modules','_execute_native_module'})
        for node in ast.walk(tree):
            if isinstance(node,ast.Call):
                fn=node.func
                name=fn.id if isinstance(fn,ast.Name) else fn.attr if isinstance(fn,ast.Attribute) else ''
                self.assertNotIn(name,{'exec','eval','FunctionType','exec_module','globals'})
                if isinstance(fn,ast.Attribute) and fn.attr=='update':
                    self.assertIsInstance(fn.value,ast.Name)
                    self.assertIn(fn.value.id,{'published','namespace'})

    def test_loader_publishes_exports_without_mutating_either_module(self):
        with tempfile.TemporaryDirectory(prefix='sb_explicit_composition_') as directory:
            root=Path(directory)
            first,second=ModuleType('fixture_first'),ModuleType('fixture_second')
            first.VALUE,second.VALUE=object(),object()
            first.PRIVATE=object()
            for name,module in [('first',first),('second',second)]:
                file=root/(name+'.py')
                file.write_text('VALUE = None\n',encoding='utf-8')
                module.__file__=str(file)
            original_first,original_second=dict(first.__dict__),dict(second.__dict__)
            namespace={'INJECTED_SENTINEL':object(),'VALUE':object()}
            imports={'first':first,'second':second}
            with patch.object(native_runtime,'RUNTIME_MODULES',('first.py','second.py')), \
                 patch.object(native_runtime,'EXPLICIT_RUNTIME_EXPORTS',{'first.py':('VALUE',),'second.py':('VALUE',)}), \
                 patch.object(native_runtime.importlib,'import_module',side_effect=imports.__getitem__), \
                 patch.object(runtime_rules,'rule_owners',return_value={name:'fixture.'+name for name in EXPECTED_RULES}):
                state=native_runtime.load_native_runtime(root,namespace)
            self.assertEqual(first.__dict__,original_first)
            self.assertEqual(second.__dict__,original_second)
            self.assertIs(namespace['VALUE'],second.VALUE)
            self.assertNotIn('PRIVATE',namespace)
            self.assertNotIn('INJECTED_SENTINEL',first.__dict__)
            self.assertEqual(state['runtime_mode'],'explicit-current-modules')

    def test_foreign_installation_cannot_supply_a_runtime_module(self):
        with tempfile.TemporaryDirectory(prefix='sb_explicit_origin_') as directory:
            root=Path(directory)
            (root/'first.py').write_text('VALUE = None\n',encoding='utf-8')
            module=ModuleType('first')
            module.__file__=str(root/'another_installation'/'first.py')
            module.VALUE=object()
            namespace={'unchanged':object()}
            before=dict(namespace)
            with patch.object(native_runtime,'RUNTIME_MODULES',('first.py',)), \
                 patch.object(native_runtime,'EXPLICIT_RUNTIME_EXPORTS',{'first.py':('VALUE',)}), \
                 patch.object(native_runtime.importlib,'import_module',return_value=module):
                with self.assertRaises(ImportError):
                    native_runtime.load_native_runtime(root,namespace)
            self.assertEqual(namespace,before)

    def test_rule_api_accepts_only_the_thirteen_declared_callable_slots(self):
        self.assertEqual(runtime_rules.RULE_NAMES,EXPECTED_RULES)
        with patch.object(runtime_rules,'_rules',{}):
            with self.assertRaises(ValueError):
                runtime_rules.register_rule('arbitrary_global',lambda:None)
            with self.assertRaises(ValueError):
                runtime_rules.get_rule('arbitrary_global')
            with self.assertRaises(TypeError):
                runtime_rules.register_rule('v0190_combat_reward',{'catalogue':'forbidden'})
            with self.assertRaises(RuntimeError):
                runtime_rules.get_rule('v0190_combat_reward')
            def implementation():
                return 17
            for name in EXPECTED_RULES:
                runtime_rules.register_rule(name,implementation)
            self.assertEqual(runtime_rules.get_rule('v0190_combat_reward')(),17)
            owners=runtime_rules.rule_owners()
            owners.clear()
            self.assertEqual(set(runtime_rules.rule_owners()),set(EXPECTED_RULES))

    def test_help_lifecycle_keeps_bootstrap_references_and_switches_current_catalog(self):
        from data import current_help
        with patch.object(current_help, '_topics', {'authored': ['base']}), \
             patch.object(current_help, '_aliases', {'base': 'authored'}), \
             patch.object(current_help, '_live', False):
            before_topics, before_aliases = current_help.get_help_catalogs()
            topics, aliases = current_help.begin_live_help()
            self.assertIs(current_help.get_help_catalogs()[0], topics)
            self.assertIs(current_help.get_help_catalogs()[1], aliases)
            self.assertIsNot(topics, before_topics)
            self.assertEqual(before_topics, {'authored': ['base']})
            self.assertEqual(before_aliases, {'base': 'authored'})
            with self.assertRaises(RuntimeError):
                current_help.begin_live_help()

    def test_transitive_import_closure_has_no_missing_sources_or_old_binders(self):
        files={p.relative_to(ROOT).as_posix():p.read_text('utf-8-sig')
               for p in ROOT.rglob('*.py') if '__pycache__' not in p.parts}
        report=inspect_closure(files,('server.py','core/native_runtime.py',*RUNTIME_MODULES))
        self.assertGreaterEqual(len(report['modules']),len(RUNTIME_MODULES))
        self.assertEqual(report['missing'],[])
        self.assertEqual(report['forbidden'],[])

    def test_import_closure_checks_transitive_edges_and_missing_modules(self):
        files={'server.py':'from game.entry import X\n','game/__init__.py':'',
               'game/entry.py':'from .service import X\n',
               'game/service.py':'from core.legacy_method_binding_v4200 import X\n',
               'core/legacy_method_binding_v4200.py':'X=1\n'}
        report=inspect_closure(files,('server.py',))
        self.assertEqual(len(report['forbidden']),1)
        files['game/service.py']='from game.missing import X\n'
        report=inspect_closure(files,('server.py',))
        self.assertEqual(report['missing'],[('game/service.py',1,'game.missing')])


if __name__=='__main__':
    unittest.main()
