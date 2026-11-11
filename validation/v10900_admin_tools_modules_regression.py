# -*- coding: utf-8 -*-
"""Historyczna zgodność i bezpieczne uruchomienie wydzielonych komend admina."""
from __future__ import annotations
import ast
import asyncio
import hashlib
from pathlib import Path
from types import SimpleNamespace
from player.session_mixins.admin_tools import SessionAdminToolsMixin
from systems.v10900_activation import REQUIRED

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_AST_SHA256='d7a1f27d62ea2f2253b4d14ec242a81ec56fb776d135ff97f3148fad0e54c27b'
GROUPS={
    'guardian_controls':('AdminGuardianControlsV109Mixin',('admin_god_mode_v35005','admin_unique_strike_v35005')),
    'session_safety':('AdminSessionSafetyV109Mixin',('prepare_character_wipe','unlock_context')),
    'boss_chests':('AdminBossChestsV109Mixin',('boss_floor_chest_here','unlock_boss_floor_chest')),
    'wipe_safety':('AdminWipeSafetyV109Mixin',('wipe_command',)),
    'owner_dashboard':('AdminOwnerDashboardV109Mixin',('admin_tools_v1224',)),
}
RETAINED={'is_admin','admin_command','admin_live_v1204','admin_error_cleanup_shortcut_v1405'}


def run():
    checks=0
    facade=ROOT/'player/session_mixins/admin_tools.py'
    tree=ast.parse(facade.read_text(encoding='utf8'))
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SessionAdminToolsMixin')
    methods={n.name:n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    assert set(methods)==RETAINED
    checks+=len(methods)
    for filename,(classname,expected) in GROUPS.items():
        rel=f'player/session_mixins/admin_tools_parts_v109/{filename}.py'
        assert rel in REQUIRED;checks+=1
        module=ast.parse((ROOT/rel).read_text(encoding='utf8'))
        node=next(c for c in module.body if isinstance(c,ast.ClassDef) and c.name==classname)
        found={m.name:m for m in node.body if isinstance(m,(ast.FunctionDef,ast.AsyncFunctionDef))}
        assert set(found)==set(expected) and not (set(found)&set(methods));checks+=1
        methods.update(found)
        checks+=len(found)
    h=hashlib.sha256('\n'.join(ast.dump(methods[k],include_attributes=False) for k in sorted(methods)).encode()).hexdigest()
    assert h==EXPECTED_AST_SHA256,('Zmiana historycznego admina',h);checks+=1
    for name in methods:
        assert callable(getattr(SessionAdminToolsMixin,name,None)),name;checks+=1
    assert len([c for c in SessionAdminToolsMixin.__mro__ if c.__name__ in [x[0] for x in GROUPS.values()]])==len(GROUPS)
    checks+=1
    assert 'player/session_mixins/admin_tools_parts_v109/__init__.py' in REQUIRED;checks+=1

    class Trial(SessionAdminToolsMixin):
        def __init__(self):
            self.account_id=7
            self.character=SimpleNamespace(name='Tester')
            self.current_hp=88;self.current_mana=32
            self.resting=True
            self.auto_fishing=True;self.auto_mining=True;self.auto_woodcutting=True;self.auto_herbalism=True
            self.combat_mob_key='rat'
            self.rest_task=None;self.auto_fishing_task=None;self.auto_mining_task=None
            self.auto_woodcutting_task=None;self.auto_herbalism_task=None;self.combat_task=None
            self.unlock_calls=[];self.party_left=False
            self.have_chest=False
        def guide_task_active(self):return False
        async def leave_party(self,announce=False):self.party_left=True
        def normalize_description_query(self,raw):return str(raw).casefold().strip()
        async def unlock(self,multi=False):self.unlock_calls.append(('unlock',multi))
        async def unlock_boss_floor_chest(self):self.unlock_calls.append(('chest',False))
        def boss_floor_chest_here(self):return 'chest' if self.have_chest else None

    async def exercise():
        t=Trial()
        await t.unlock_context('max')
        assert t.unlock_calls==[('unlock',True)]
        t.have_chest=True
        await t.unlock_context('skrzynia')
        assert t.unlock_calls[-1]==('chest',False)
        await t.unlock_context('dusza')
        assert t.unlock_calls[-1]==('unlock',False)
        await t.prepare_character_wipe()
        assert t.party_left and t.character is None and t.account_id is None
        assert t.current_hp==0 and t.current_mana==0
        assert not t.resting and not t.auto_mining and not t.auto_woodcutting and not t.auto_fishing and not t.auto_herbalism
    asyncio.run(exercise());checks+=6
    return checks

if __name__=='__main__':
    print('V109 ADMIN MODULY:',run(),'PASS, dane sesji syntetyczne, bez zapisu do bazy')
