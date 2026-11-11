# -*- coding: utf-8 -*-
"""v109: bitowa zgodnosc AST ucieczki i smierci, zabezpieczenia bez SQLite."""
from __future__ import annotations
import ast,hashlib,asyncio
from pathlib import Path
from types import SimpleNamespace
from player.session_mixins.combat_survival import SessionCombatSurvivalMixin
from systems.v10900_activation import REQUIRED
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_AST='dfc1f54c3001dbce08bc5702b20650ebbd22792041123d20dfc144cfebfc4e1d'
PARTS={'escape':('CombatEscapeV109Mixin',('flee',)),'death':('CombatDeathV109Mixin',('die',))}

def run():
    source=ROOT/'player/session_mixins/combat_survival.py'
    cls=next(n for n in ast.parse(source.read_text('utf8')).body if isinstance(n,ast.ClassDef) and n.name=='SessionCombatSurvivalMixin')
    assert not any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) for n in cls.body)
    methods={}
    checks=1
    for filename,(classname,names) in PARTS.items():
        path=f'player/session_mixins/combat_survival_parts_v109/{filename}.py'
        assert path in REQUIRED
        tree=ast.parse((ROOT/path).read_text('utf8'))
        m=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==classname)
        found={x.name:x for x in m.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
        assert set(found)==set(names)
        methods.update(found); checks+=3
    digest=hashlib.sha256('\n'.join(ast.dump(methods[k],include_attributes=False) for k in sorted(methods)).encode()).hexdigest()
    assert digest==EXPECTED_AST,digest;checks+=1
    assert all(callable(getattr(SessionCombatSurvivalMixin,n,None)) for n in methods)
    checks+=1
    class Fake(SessionCombatSurvivalMixin):
        def __init__(self):
            self.admin_god_v35005=True;self.current_hp=0;self.combat_mob_key=None
            self._last_death_cause_v11341={'killer':'test'};self.out=[]
        def is_admin(self):return True
        def max_hp(self):return 123
        async def send(self,message):self.out.append(message)
    async def exercise():
        obj=Fake()
        await obj.die('test')
        assert obj.current_hp==123 and obj._last_death_cause_v11341=={} and any('ADMIN GOD' in x for x in obj.out)
        obj.out.clear();await obj.flee()
        assert obj.out==['Nie jesteś w walce.']
    asyncio.run(exercise());checks+=5
    return checks

if __name__=='__main__':print('V109 COMBAT SURVIVAL:',run(),'PASS')
