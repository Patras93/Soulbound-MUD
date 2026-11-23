# -*- coding: utf-8 -*-
"""v116.67: cast/c remain ordinary skill aliases, not player summons.

Catch command-catalog collisions before the costly 60/60 PLUS phase.
"""
import asyncio
from core.command_catalog import COMMAND_CATALOG
from core.mines_threat import COMMAND_ALIASES
from player.session_mixins.command_registry import (
    COMMAND_REGISTRY, SessionCommandRegistryMixin, resolve_session_command,
)


class _SkillActor(SessionCommandRegistryMixin):
    def __init__(self):
        self.used = []

    async def command_skill_v0490(self, args):
        self.used.append(args)

    async def cast_minion_spell_v11664(self, args):
        raise AssertionError('Retired minion handler must not receive cast/c')


def run():
    checks = 0
    assert COMMAND_ALIASES.get('cast') == 'skill'
    assert COMMAND_ALIASES.get('c') == 'skill'
    checks += 2
    assert resolve_session_command('cast') == 'skill'
    assert resolve_session_command('c') == 'skill'
    assert resolve_session_command('skill') == 'skill'
    checks += 3
    assert 'cast' not in COMMAND_REGISTRY and 'c' not in COMMAND_REGISTRY
    checks += 1
    assert COMMAND_REGISTRY['skill'][0] == 'command_skill_v0490'
    assert COMMAND_CATALOG.definition('cast').handler == 'command_skill_v0490'
    assert COMMAND_CATALOG.definition('c').handler == 'command_skill_v0490'
    checks += 3
    assert not any(v['alias'] in ('cast', 'c') for v in COMMAND_CATALOG.conflicts())
    checks += 1
    actor = _SkillActor()
    for raw in ('skill', 'cast', 'c'):
        assert asyncio.run(actor.dispatch_registered_command(resolve_session_command(raw), 'jammer')) is True
        checks += 1
    assert actor.used == ['jammer', 'jammer', 'jammer']
    checks += 1
    print(f'CAST/C SKILL ROUTING v116.67: {checks}/{checks} PASS', flush=True)
    return checks


if __name__ == '__main__':
    run()
