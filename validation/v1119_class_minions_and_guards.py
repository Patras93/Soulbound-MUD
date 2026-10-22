# -*- coding: utf-8 -*-
"""Regression: class minions and death/full-HP action guards."""
import asyncio
import ast
import sqlite3
from pathlib import Path
from types import SimpleNamespace

from core.classes_skills import CLASSES
from systems.class_minions_v1119 import CLASS_MINIONS_V1119, CLASS_MINIONS_BY_CLASS_V1119
from player.session_mixins.era_sky_v1700 import SessionSkyV1700Mixin, SUMMONS, SUMMON_MANA, ensure_schema, ascii_fold
from player.session_mixins.session_runtime_state import SessionRuntimeStateMixin
from player.session_methods_v4200 import dungeonprogression_part03 as portals
from player.session_methods_v4200.combatskills_part02 import use_class_skill


def _check_source_guards():
    # Ensure the source methods reject full HP before any mana/cooldown deduction.
    src = Path(__file__).parents[1] / 'player/session_methods_v4200/combatskills_part02.py'
    tree = ast.parse(src.read_text('utf8'))
    fn = next(x for x in tree.body if isinstance(x, ast.AsyncFunctionDef) and x.name == 'use_class_skill')
    code = ast.unparse(fn)
    checks = 0
    for marker in ('_regen_target.current_hp >= _regen_target.max_hp()',
                   '_cure_beam_target.current_hp >= _cure_beam_target.max_hp()',
                   '_heal_target.current_hp >= _heal_target.max_hp()',
                   'sess.current_hp < sess.max_hp()',
                   '_generic_heal_target.current_hp >= _generic_heal_target.max_hp()',
                   'if not injured and (not summon_injured):'):
        if marker == 'if not injured and (not summon_injured):':
            assert 'if not injured and (not summon_injured):' in code
        else:
            assert marker in code, marker
        checks += 1
    assert code.index('_cure_beam_target.current_hp >= _cure_beam_target.max_hp()') < code.index('self.current_mana -= mana_cost', code.index('_cure_beam_target.current_hp >= _cure_beam_target.max_hp()'))
    assert code.index('_heal_target.current_hp >= _heal_target.max_hp()') < code.index('self.current_mana -= mana_cost', code.index('_heal_target.current_hp >= _heal_target.max_hp()'))
    return checks + 2


async def _run():
    checks = 0
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    class Db:
        _v1700_ready = True
        def __init__(self): self.conn = conn
        def item_qty(self,*a): return 0
        def storage_qty(self,*a): return 0
    db = Db()
    class Summoner(SessionSkyV1700Mixin):
        def __init__(self, aid, cls, level=18, mana=400):
            self.account_id=aid
            self.cls=cls
            self.character=SimpleNamespace(character_level=level,room_id='temple',name=cls)
            self.current_mana=mana
            self.current_hp=1000
            self.combat_mob_key=None
            self.server=SimpleNamespace(db=db)
            self.messages=[]
        def max_hp(self): return 1000
        def physical_power(self): return 100
        def spell_power(self): return 100
        def active_class_names(self): return (self.cls,)
        async def send(self, txt): self.messages.append(str(txt))
    names={name for name,*_ in CLASSES}
    for klass in names:
        assert any(spec[1] == klass for spec in SUMMONS.values()), klass
        checks+=1
    assert len(CLASS_MINIONS_V1119)==95 and len(CLASS_MINIONS_BY_CLASS_V1119)==19
    checks+=2
    for idx, klass in enumerate(sorted(CLASS_MINIONS_BY_CLASS_V1119), 1):
        rows=CLASS_MINIONS_BY_CLASS_V1119[klass]
        assert len(rows)==5 and [r[3] for r in rows]==[1,90,200,400,600]
        hero=Summoner(idx,klass)
        low,high=rows[:2]
        mp=hero.current_mana
        await hero.summons_v1700('przywolaj '+low[0])
        dbrow=conn.execute('SELECT summon_type,active,hp,max_hp FROM summons_v1700 WHERE account_id=?',(idx,)).fetchone()
        assert dbrow and dbrow['summon_type']==low[0] and dbrow['active']==1 and dbrow['hp']==dbrow['max_hp']>0
        assert hero.current_mana==mp-SUMMON_MANA[low[0]]
        await hero.summons_v1700('przywolaj '+high[0])
        assert conn.execute('SELECT COUNT(*) FROM summons_v1700 WHERE account_id=?',(idx,)).fetchone()[0]==1
        assert 'wymaga poziomu postaci 90' in hero.messages[-1]
        hero.character.character_level=90
        mp=hero.current_mana
        await hero.summons_v1700('przywolaj '+high[0])
        assert conn.execute('SELECT COUNT(*) FROM summons_v1700 WHERE account_id=? AND active=1',(idx,)).fetchone()[0]==2
        assert hero.current_mana==mp-SUMMON_MANA[high[0]]
        assert hero._v1703_dismiss_summons_on_login()==2
        assert conn.execute('SELECT COUNT(*) FROM summons_v1700 WHERE account_id=? AND active=1',(idx,)).fetchone()[0]==0
        hero.current_hp=0
        mp=hero.current_mana
        await hero.summons_v1700('aktywuj '+low[0])
        assert conn.execute('SELECT COUNT(*) FROM summons_v1700 WHERE account_id=? AND active=1',(idx,)).fetchone()[0]==0 and hero.current_mana==mp
        hero.current_hp=100
        await hero.summons_v1700('aktywuj '+low[0])
        assert conn.execute('SELECT COUNT(*) FROM summons_v1700 WHERE account_id=? AND active=1',(idx,)).fetchone()[0]==1
        checks+=12
    assert all(ascii_fold(k)==k for k in CLASS_MINIONS_V1119)
    checks+=1
    class Teleport(SessionRuntimeStateMixin):
        def __init__(self, down=False):
            self.character=SimpleNamespace(room_id='cave',name='Bohater')
            self.current_hp=0 if not down else 10
            self.down=down
            self.closed=False
            self.messages=[]
        def is_downed_v0371(self):return self.down
        async def send(self,text):self.messages.append(str(text))
    for down in (False,True):
        test=Teleport(down)
        assert await test._teleport_self_to_temple_v0354() is False
        await test.teleport_to_temple_command()
        assert test.character.room_id=='cave' and len(test.messages)==2
        assert any('teleport' in x.lower() for x in test.messages)
        assert await portals.use_crypt_portal(test,'10') is None
        assert await portals.use_astral_portal(test,'10') is None
        assert test.character.room_id=='cave'
        checks+=5
    class DeadCaster:
        current_hp=0
        def is_downed_v0371(self):return False
        def __init__(self):self.messages=[];self.current_mana=99
        async def send(self,msg):self.messages.append(str(msg))
    caster=DeadCaster()
    await use_class_skill(caster,'dowolne leczenie')
    assert caster.current_mana==99 and 'Martwa' in caster.messages[-1]
    checks+=2
    conn.close()
    return checks

def run_regression():
    return _check_source_guards() + asyncio.run(_run())

if __name__=='__main__':
    print(f'LECZENIE / TELEPORT / 22 KLASY v11.00.19: {run_regression()} checks PASS')
