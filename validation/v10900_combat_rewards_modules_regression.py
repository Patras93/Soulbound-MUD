# -*- coding: utf-8 -*-
"""v109: nagrody setowe wydzielone, krytyczny mob_defeated nadal w starej fasadzie."""
from __future__ import annotations
import ast,hashlib,asyncio
from pathlib import Path
from types import SimpleNamespace
from systems.v10900_activation import REQUIRED
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_AST='e1a5869301eeab2e85bf3d080c3d544051e9ca82928898ebe0c6502b6eedbacd'

def run():
    facade=ROOT/'player/session_mixins/combat_rewards.py'
    cls=next(x for x in ast.parse(facade.read_text('utf8')).body if isinstance(x,ast.ClassDef) and x.name=='SessionCombatRewardsMixin')
    main=[x for x in cls.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))]
    assert len(main)==1 and main[0].name=='mob_defeated'
    assert len(main[0].decorator_list)==2
    path='player/session_mixins/combat_rewards_parts_v109/milestones.py'
    assert path in REQUIRED
    c=next(x for x in ast.parse((ROOT/path).read_text('utf8')).body if isinstance(x,ast.ClassDef))
    others={x.name:x for x in c.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
    assert set(others)=={'class_for_milestone_loot','grant_milestone_boss_loot'}
    all_methods={main[0].name:main[0],**others}
    digest=hashlib.sha256('\n'.join(ast.dump(all_methods[k],include_attributes=False) for k in sorted(all_methods)).encode()).hexdigest()
    assert digest==EXPECTED_AST,digest
    # Test without importing the world catalogue or touching a player save.
    from player.session_mixins.combat_rewards_parts_v109.milestones import CombatMilestoneV109Mixin
    class Player(CombatMilestoneV109Mixin):
        def __init__(self):self.character=SimpleNamespace(class_name='Mag');self.out=[]
        def active_class_names(self):return ['Wojownik']
        async def send(self,txt):self.out.append(txt)
    player=Player()
    assert player.class_for_milestone_loot()=='Wojownik'
    # No marker: no DB or inventory mutation, even if no server is attached.
    async def check():await player.grant_milestone_boss_loot({},0)
    asyncio.run(check());assert not player.out
    return 11
if __name__=='__main__':print('V109 COMBAT REWARDS:',run(),'PASS')
