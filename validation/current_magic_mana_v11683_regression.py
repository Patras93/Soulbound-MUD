# -*- coding: utf-8 -*-
"""Exact costs of every authored class; real Magitek dispatch and support effects."""
import asyncio
import time
from types import SimpleNamespace
from unittest.mock import patch


def run():
    from core.classes_skills import CLASSES, CLASS_SKILLS, PHYSICAL_MANA_FREE_CLASSES, effective_skill_mana_cost
    from core.magitek.catalogue import skill_catalogue, CLASS_INFO
    from core.archetypes import chaos, expansion
    from systems.published_27_master import skill_mana_cost
    from systems.magitek import runtime
    from systems.magitek.support import use_support_skill, active_ward, runic_weapon_active, magitek_spell_mp_cost
    from validation.v10700_magitek_support_regression import Actor, Server
    checks = 0
    def check(value, label):
        nonlocal checks
        assert value, label
        checks += 1
    rows = {name:(mode,CLASS_SKILLS[name]) for name,mode,*_ in CLASSES}
    rows.setdefault(CLASS_INFO[0],(CLASS_INFO[1],skill_catalogue()))
    for spec in (*chaos.CLASS_SPECS,*expansion.CLASS_SPECS):
        name,mode,weapon,stat,passive,value,*labels=spec
        generator=chaos._skills if spec in chaos.CLASS_SPECS else expansion._skills
        if generator is chaos._skills:labels=labels[0]
        rows.setdefault(name,(mode,generator(name,'fixture',stat,mode=='magic',labels)))
    check(len(rows)==38,'all authored class profiles')
    def legacy(skill, name):
        for field in ('uoss_mp_cost','source_mp_cost'):
            if skill.get(field) is not None:
                try:return skill_mana_cost(max(0,int(skill.get(field) or 0)))
                except (TypeError,ValueError):return 0
        if name in PHYSICAL_MANA_FREE_CLASSES or rows[name][0]=='physical':return 0
        return skill_mana_cost(max(0,int(skill.get('mana',0) or 0)))
    # Register only class identities for the test. Actual catalogue rows above
    # include all late classes even if activation has not yet loaded them.
    extra=[(name,mode,'fixture',7) for name,(mode,_) in rows.items() if not any(r[0]==name for r in CLASSES)]
    physical=magical=0
    with patch.object(__import__('core.classes_skills',fromlist=['CLASSES']),'CLASSES',list(CLASSES)+extra):
        for name,(mode,skills) in rows.items():
            for skill in skills:
                old=legacy(skill,name); new=effective_skill_mana_cost(skill,name)
                active=skill.get('kind')!='passive' and (skill.get('kind')!='boost' or skill.get('active_special') or skill.get('mec_special')=='vmax')
                magic=(mode=='magic' and skill.get('v107_skill')!='tekmissile') or (name=='Mec' and skill.get('mec_branch')=='magic')
                if not magic or not active:
                    check(new==old,(name,skill['id'],'unchanged nonmagical/passive',old,new));physical+=not magic
                else:
                    check(new>0 and (old==0 or new==old),(name,skill['id'],'positive MP; preserve existing positive',old,new));magical+=1
    skills={row['v107_skill']:row for row in skill_catalogue()}
    for slug,skill in skills.items():
        if slug=='magicitelink':check(effective_skill_mana_cost(skill,'Magitek')==24,'variable minimum, linked core charged separately')
        elif slug=='tekmissile' or skill['kind']=='passive':check(effective_skill_mana_cost(skill,'Magitek')==0,slug+' physical/passive unchanged')
        else:check(effective_skill_mana_cost(skill,'Magitek')==5+skill['unlock']//7,slug+' standard MP curve')
    class Native:
        def offensive_skill_core_power_v11185(self,*a):return 0
        def offensive_skill_damage_type_v11190(self,*a):return 'magic'
        def offensive_skill_damage_multiplier_v11186(self,*a):return 1.0
        def healing_skill_amount_v11196(self,*a):return 1
        async def use_class_skill(self,raw):raise AssertionError('unexpected baseline')
    from systems.elemental_combat import OLC_SKILL_ELEMENTS_V1500
    with patch.dict(OLC_SKILL_ELEMENTS_V1500):
        runtime.install(Native)
    class Caster(Actor,Native):
        def __init__(self,name,server):
            super().__init__(name,server);self.current_mana=100;self.target=SimpleNamespace(hp=101,alive=True);self.mult=1.0;self.resolve_calls=0
        def equipment_mp_cost_multiplier_v11176(self):return self.mult
        def find_skill_from_input(self,raw):return skills[raw],''
        async def skill_combat_target(self,query):self.resolve_calls+=1;return self.target
        async def ensure_realtime_combat(self):pass
    async def exercise():
        s=Server();a=Caster('Magitek',s);b=Actor('Sojusznik',s)
        for slug in ('tekshield','tekbarrier','runicweapon'):
            cost=magitek_spell_mp_cost(a,skills[slug]);before=a.current_mana;xp=len(a.xp)
            await use_support_skill(a,skills[slug],'')
            check(a.current_mana==before-cost and len(a.xp)==xp+1,slug+' pays exactly once')
        check(active_ward(a)=='tekbarrier' and runic_weapon_active(a),'effects unchanged')
        before=a.current_mana;xp=len(a.xp)
        await use_support_skill(a,skills['tekshield'],'Nieistniejący')
        check(a.current_mana==before and len(a.xp)==xp,'invalid ward target costs nothing')
        b.active_skill_buffs={'ward':{'beneficial':True,'until':time.time()+30}}
        a.current_mana=0
        await use_support_skill(a,skills['diffuser'],'Sojusznik')
        check(b.active_skill_buffs and a.current_mana==0 and len(a.xp)==xp,'no mana: no dispel')
        a.current_mana=100;a.mult=2.0;cost=magitek_spell_mp_cost(a,skills['diffuser'])
        await use_support_skill(a,skills['diffuser'],'Sojusznik')
        check(not b.active_skill_buffs and a.current_mana==100-cost,'EQ multiplier applied once')
        before=a.current_mana;xp=len(a.xp)
        await use_support_skill(a,skills['diffuser'],'Sojusznik')
        check(a.current_mana==before and len(a.xp)==xp,'no beneficial effect: no cost')
        s.db.fail_on='Sojusznik'
        await use_support_skill(a,skills['xfer'],'')
        check(a.current_mana==before and a.character.room_id=='temple_basement' and b.character.room_id=='temple_basement','failed xfer pays nothing')
        s.db.fail_on=None;cost=magitek_spell_mp_cost(a,skills['xfer'])
        await use_support_skill(a,skills['xfer'],'')
        check(a.current_mana==before-cost and a.character.room_id=='square' and b.character.room_id=='square','xfer once, caster only')
        a.current_mana=0;xp=len(a.xp);resolves=a.resolve_calls
        await Native.use_class_skill(a,'gravitybomb')
        check(a.target.hp==101 and a.current_mana==0 and len(a.xp)==xp and a.resolve_calls==resolves,'gravity low MP blocks before target')
        a.current_mana=100;cost=magitek_spell_mp_cost(a,skills['gravitybomb'])
        with patch.object(runtime.random,'random',return_value=0):await Native.use_class_skill(a,'gravitybomb')
        check(a.target.hp==51 and a.current_mana==100-cost and len(a.xp)==xp+1,'gravity hit pays once')
        with patch.object(runtime.random,'random',return_value=0.999):await Native.use_class_skill(a,'gravitybomb')
        check(a.target.hp==51 and a.current_mana==100-2*cost and len(a.xp)==xp+2,'gravity resist pays for valid cast')
        a.target=None;before=a.current_mana;xp=len(a.xp)
        await Native.use_class_skill(a,'gravitybomb')
        check(a.current_mana==before and len(a.xp)==xp,'gravity invalid target free')
    asyncio.run(exercise())
    print(f'MAGIC MANA v11683: {checks}/{checks} PASS; 38 profiles; {physical} nonmagical and {magical} active magical rows',flush=True)
    return checks

if __name__=='__main__':run()
