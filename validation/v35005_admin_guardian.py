# -*- coding: utf-8 -*-
"""Admin-only rescue commands: session GOD and canonical party kill flow."""
import asyncio
from types import SimpleNamespace

from data.mobs import MOB_TEMPLATES
from player.session_mixins.admin_tools import SessionAdminToolsMixin
from player.session_mixins.combat_survival import SessionCombatSurvivalMixin


class _FakeDb:
    def __init__(self):
        self.audit = []

    def account_name(self, _id):
        return 'owner'

    def record_admin_action_v1224(self, *args):
        self.audit.append(args)


class _FakeWorld:
    def __init__(self):
        self.mobs = {}
        self.mob = None

    def find_mob(self, room, query):
        if room == 'test' and query and self.mob and self.mob.alive:
            return self.mob
        return None


class _FakeServer:
    def __init__(self):
        self.world = _FakeWorld()
        self.db = _FakeDb()
        self.broadcasts = []
        self.allow = True

    def engagement_allowed(self, session, mob):
        return self.allow

    async def party_combat_broadcast(self, session, message, detail='normal'):
        self.broadcasts.append(message)


class _FakeSession(SessionAdminToolsMixin, SessionCombatSurvivalMixin):
    def __init__(self, owner=True):
        self.owner = owner
        self.server = _FakeServer()
        self.master_account_id = 1
        self.character = SimpleNamespace(name='Tester', room_id='test')
        self.current_hp = 10
        self.admin_god_v35005 = False
        self.combat_mob_key = None
        self._recap52_dealt = 0
        self.messages = []
        self.kills = []

    def is_admin(self):
        return self.owner

    def normalize_description_query(self, raw):
        return str(raw).casefold()

    def max_hp(self):
        return 1000

    async def send(self, message, **kw):
        self.messages.append(message)

    async def attack(self, query):
        self.combat_mob_key = self.server.world.mob.key

    def mob_effective_max_hp_v11330(self, mob, template):
        return 1000

    def engagement_block_message(self, mob):
        return 'Cel niedostepny.'

    async def mob_defeated(self, mob):
        self.kills.append(mob.key)
        mob.alive = False


async def _test_async():
    c = 0
    owner = _FakeSession()
    await owner.admin_command('god status')
    assert 'WYLACZONA' in owner.messages[-1]
    c += 1
    await owner.admin_command('god on')
    assert owner.admin_god_v35005 and owner.current_hp == 1000
    c += 1
    owner.current_hp = 0
    await owner.die('Black Rabite')
    assert owner.current_hp == 1000 and not owner.kills
    c += 1
    await owner.admin_command('god off')
    assert not owner.admin_god_v35005
    c += 1
    mob = SimpleNamespace(template_id='temple_rat', room_id='test', alive=True,
                          hp=1000, key='m1')
    assert 'temple_rat' in MOB_TEMPLATES
    c += 1
    owner.server.world.mob = mob
    owner.server.world.mobs[mob.key] = mob
    await owner.admin_command('cios grom rat')
    assert mob.hp == 850 and owner._recap52_dealt == 150
    c += 1
    await owner.admin_command('cios nawalnica rat')
    assert mob.hp == 500 and owner._recap52_dealt == 500
    c += 1
    await owner.admin_command('cios wyrok rat')
    assert mob.hp == 0 and owner.kills == [mob.key]
    c += 1
    assert len(owner.server.broadcasts) == 3
    c += 1
    assert len(owner.server.db.audit) == 5
    c += 1
    nonowner = _FakeSession(False)
    await nonowner.admin_command('god on')
    assert not nonowner.admin_god_v35005
    c += 1
    await nonowner.admin_command('cios wyrok rat')
    assert not nonowner.kills
    c += 1
    await nonowner.admin_god_mode_v35005('on')
    assert not nonowner.admin_god_v35005
    c += 1
    await nonowner.admin_unique_strike_v35005('wyrok rat')
    assert not nonowner.kills
    c += 1
    blocked = _FakeSession()
    blocked.server.world.mob = SimpleNamespace(template_id='temple_rat',room_id='test',
                                              alive=True,hp=1000,key='locked')
    blocked.server.allow = False
    await blocked.admin_command('cios grom rat')
    assert blocked.server.world.mob.hp == 1000
    c += 1
    return c


def run():
    return asyncio.run(_test_async())


if __name__ == '__main__':
    print(f'ADMIN GUARDIAN v35.00.5: {run()} checks PASS')
