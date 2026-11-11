"""Session services declare dependencies without the historical globals binder."""
import ast
import builtins
from pathlib import Path
import symtable
import unittest

ROOT=Path(__file__).resolve().parents[1]
MODULES=(
    'player/session_mixins/perception_maps.py',
    'player/session_mixins/atlas_codex.py',
    'player/session_mixins/collection_loot_records.py',
    'player/session_mixins/admin_tools.py',
    'player/session_mixins/forge_guilds.py',
    'player/session_mixins/combat_realtime.py',
    'player/session_mixins/combat_skills.py',
    'player/session_mixins/dungeon_progression.py',
    'player/session_mixins/gathering.py',
    'player/session_mixins/guide_navigation.py',
    'player/session_mixins/inventory_equipment.py',
    'player/session_mixins/io_auth_character.py',
    'player/session_mixins/party.py',
    'player/session_mixins/profession_storage.py',
    'player/session_mixins/skill_learning.py',
    'server/mud_server.py',
)


class NativeSessionDependencyTests(unittest.TestCase):
    def test_methods_do_not_depend_on_namespace_binding(self):
        for relative in MODULES:
            with self.subTest(module=relative):
                tree=ast.parse((ROOT/relative).read_text(encoding='utf-8-sig'))
                for node in ast.walk(tree):
                    if isinstance(node,ast.ImportFrom):
                        self.assertNotIn('legacy_method_binding',node.module or '')
                    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                        self.assertNotIn(node.func.id,{'globals','FunctionType','_sb420_bind'})

    def test_no_undeclared_global_names(self):
        implicit=set(dir(builtins))|{'__file__','__name__','__package__','__doc__'}
        for relative in MODULES:
            with self.subTest(module=relative):
                source=(ROOT/relative).read_text(encoding='utf-8-sig')
                module=symtable.symtable(source,relative,'exec')
                defined={s.get_name() for s in module.get_symbols()
                         if s.is_imported() or s.is_assigned() or s.is_namespace()}
                tables=[module]
                missing=set()
                while tables:
                    table=tables.pop()
                    tables.extend(table.get_children())
                    missing.update(s.get_name() for s in table.get_symbols()
                                   if s.is_global() and s.is_referenced()
                                   and s.get_name() not in implicit|defined)
                self.assertEqual(missing,set())


if __name__=='__main__':
    unittest.main()
