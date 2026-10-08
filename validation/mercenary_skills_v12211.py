# -*- coding: utf-8 -*-
"""Read-only mercenary skills catalogue; combat skills remain AI-controlled."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace

from systems.mercenary_taverns import MERCENARIES, mercenary_role, mercenary_skill_lines_v12211


def validate_mercenary_skills_v12211():
    checks = 0

    def check(value, message=""):
        nonlocal checks
        assert value, message
        checks += 1

    check(len(MERCENARIES) == 15)
    for role, spec in MERCENARIES.items():
        lines = mercenary_skill_lines_v12211(role)
        check(lines[0].startswith(spec['name']))
        check(spec['ability'] in lines[1])
        check(('magiczny' if spec['attack_type'] == 'magic' else 'fizyczny') in lines[1])
        check('automatycznie' in ' '.join(lines).casefold())
        check('mocy właściciela' in lines[1])
        if role in ('kaplan', 'paladyn', 'druid'):
            check(any('Leczenie' in line for line in lines))
        else:
            check(not any('Leczenie drużyny:' in line for line in lines))
        if role in ('wojownik', 'paladyn', 'straznik', 'psionik', 'inzynier'):
            check(any('Osłona' in line for line in lines))
        else:
            check(not any('Osłona drużyny:' in line for line in lines))
        check(mercenary_role(spec['name']) == role)

    root = Path(__file__).resolve().parents[1]
    source = (root / 'player/session_mixins/mercenary_taverns.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'SessionMercenaryTavernsMixin')
    handler = next(node for node in cls.body if isinstance(node, ast.AsyncFunctionDef) and node.name == 'handle_mercenaries_v1170')
    ns = dict(MERCENARIES=MERCENARIES, mercenary_role=mercenary_role,
              mercenary_skill_lines_v12211=mercenary_skill_lines_v12211)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[handler], type_ignores=[])),
                 'player/session_mixins/mercenary_taverns.py', 'exec'), ns)

    class Session:
        handle_mercenaries_v1170 = ns['handle_mercenaries_v1170']
        def __init__(self):
            self.character = SimpleNamespace(character_level=150)
            self.lines = []
            self.server = SimpleNamespace(db=SimpleNamespace())
            self.account_id = 1
        async def send(self, line):
            self.lines.append(line)

    async def run_tests():
        user = Session()
        await user.handle_mercenaries_v1170('skille')
        check(len(user.lines) == 17, f'Expected title + 15 roles + footer, got {len(user.lines)}')
        check(all(spec['name'] in ' '.join(user.lines) for spec in MERCENARIES.values()))
        for name in ('Seren', 'Vael', 'Gareth'):
            user.lines.clear()
            await user.handle_mercenaries_v1170('skille ' + name)
            check(name in user.lines[0])
            check('automatycznie' in ' '.join(user.lines).casefold())
        user.lines.clear()
        await user.handle_mercenaries_v1170('umiejetnosci Kord')
        check(user.lines[0].startswith('Kord'))
        user.lines.clear()
        await user.handle_mercenaries_v1170('skills Nieznany')
        check('Nieznany najemnik' in user.lines[0])
        # No DB methods on this stub: successful calls prove read-only and no requirement to be hired.
    asyncio.run(run_tests())

    help_source = (root / 'world/equipment_help.py').read_text(encoding='utf-8')
    check('najemnik skille Seren' in help_source)
    check('Gracz może podejrzeć skille' in help_source)
    combat_source = ast.get_source_segment(source, next(node for node in cls.body if isinstance(node, ast.AsyncFunctionDef) and node.name == 'mercenary_combat_turn_v1170'))
    check('mercenary_owner_power_v1213' in combat_source)
    check('if role in ("kaplan", "paladyn", "druid")' in combat_source)
    check('if message is None and mob.hp > 1:' in combat_source)
    return checks


if __name__ == '__main__':
    print('MERCENARY SKILLS v1.22.11:', validate_mercenary_skills_v12211(), 'checks PASS')
