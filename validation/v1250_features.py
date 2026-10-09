# -*- coding: utf-8 -*-
"""Fast deterministic v1.25 gameplay and safety checks, no server/db writes."""
from types import SimpleNamespace as Mob
from systems.monster_ecology_v1250 import (species_v1250, ecology_turn_v1250,
    adaptive_skills_v1250, adaptive_defense_v1250, adaptive_cadence_v1250)
from systems.elite_legends_v1250 import legendary_roll_v1250, build_legendary_v1250
from systems.market_dynamics_v1250 import market_demand_v1250, material_grade_v1250, material_quality_upgrade_v1250
from systems.mercenary_memory_v1250 import memory_choice_v1250, memory_effect_v1250, memory_learn_v1250
from world.world_secrets_v1190 import secret_room_id_v1190, secret_room_identity_v1190


def audit_v1250():
    checks=0
    def chk(test, msg):
        nonlocal checks
        checks += 1
        if not test: raise AssertionError(msg)
    chk(species_v1250({'name':'Mroczny Wilk'}) == 'pack','wolf type')
    chk(species_v1250({'name':'Smok Ognia'}) == 'dragon','dragon type')
    chk(species_v1250({'name':'Szkielet wojownik'}) == 'undead','undead type')
    chk(species_v1250({'name':'Mag wojenny'}) == 'caster','caster type')
    def mob(hp=100,turn=4,key='a'):
        return Mob(key=key,template_id=key,room_id='arena',hp=hp,alive=True,
                   combat_turn=turn,engaged_by='Owner')
    wolf=mob()
    pack=mob(key='b')
    class World:
        mobs={'a':wolf,'b':pack}
        def mob_templates_for_ai_v1160(self, target):return {'name':'Wilk','max_hp':100}
    world=World()
    chk(bool(ecology_turn_v1250(world,wolf,{'name':'Wilk','max_hp':100},now=100)), 'pack support')
    chk(getattr(wolf,'monster_ai_empowered_until_v1160',0)==112,'pack empowerment')
    chk(ecology_turn_v1250(world,wolf,{'name':'Wilk','max_hp':100},now=101)=='', 'pack cooldown')
    undead=mob(40,key='z')
    chk('odrodzić' in ecology_turn_v1250(world,undead,{'name':'Szkielet','max_hp':100},now=100),'undead recover')
    chk(undead.hp==54,'undead one-time heal')
    undead.combat_turn=8
    chk(ecology_turn_v1250(world,undead,{'name':'Szkielet','max_hp':100},now=200)=='','undead once')
    dragon=mob()
    chk('żywiołową' in ecology_turn_v1250(world,dragon,{'name':'Smok','max_hp':100},now=100),'dragon prep')
    mage=mob(40)
    chk('leczy' in ecology_turn_v1250(world,mage,{'name':'Mag','max_hp':100,'damage_type':'magic'},now=100),'mage heals')
    protected=mob()
    chk(ecology_turn_v1250(world,protected,{'name':'Smok','uoss_superboss':True},now=100)=='', 'authored boss protected')
    chk(adaptive_skills_v1250(mob(), {'name':'wilk','damage':10}, 1000, 10) > adaptive_skills_v1250(mob(), {'name':'wilk','damage':10}, 10, 10),'adaptive attack')
    chk(adaptive_skills_v1250(mob(), {'uoss_superboss':True}, 1000, 10)==1,'boss rules preserved')
    adept=mob(turn=7)
    adept.adaptive_party_dps_v11330=20000
    chk('obronną' in adaptive_defense_v1250(adept,{'damage':100},now=100),'adaptive defense')
    chk(adaptive_defense_v1250(adept,{'damage':100},now=100)=='','defense cooldown')
    chk(adaptive_cadence_v1250([adept], {'a':{'damage':100}}, 2) < 2,'adapt speed')
    novice=mob()
    novice.adaptive_party_dps_v11330=300
    chk(adaptive_cadence_v1250([novice], {'a':{'damage':100}}, 2) == 2,'novice pace protected')
    ordinary={'name':'Goblin','max_hp':100,'damage':10}
    class Rng:
        def __init__(self,value):self.value=value
        def random(self):return self.value
    chk(legendary_roll_v1250(ordinary,Rng(.001))=='mythic','mythic spawn')
    chk(legendary_roll_v1250(ordinary,Rng(.008))=='legendary','legendary spawn')
    chk(legendary_roll_v1250(ordinary,Rng(.05))=='','ordinary spawn unaffected')
    chk(not legendary_roll_v1250({'name':'Boss','boss':True},Rng(0)),'boss variant protected')
    clone=build_legendary_v1250('goblin',ordinary,'mythic')
    chk(clone['elite_reward_multiplier_v11338']>3,'rare rewards')
    chk(clone['elite_drop_multiplier_v11338']>2,'rare drops')
    chk(clone['elite_base_template']=='goblin','quest species unchanged')
    dummy=Mob()
    techniques=[]
    for i in range(8):
        move,idx,key=memory_choice_v1250(dummy,'mag','goblin','Ognista Kula',i+1)
        techniques.append(idx)
        memory_learn_v1250(dummy,key,idx,(120,160,250)[idx],120,10000)
    chk(set(techniques[:6])=={0,1,2},'merc learns all techniques')
    chk(techniques[-1]==2,'merc chooses effective technique')
    chk(memory_effect_v1250('mag',2,{'boss':True}) > memory_effect_v1250('mag',2,{}),'boss-effective skill')
    chk(.9 <= market_demand_v1250('fish',now=1) <= 1.25,'market sane')
    chk(market_demand_v1250('fish',now=1)==market_demand_v1250('fish',now=100),'same price within six hours')
    chk(market_demand_v1250('unknown',now=1)==1,'no unsupported market change')
    items={'mithril_ore':{'name':'Mithril','rarity':'epic'},'iron':{'name':'Żelazo'}}
    chk(material_grade_v1250(['mithril_ore'],items)>material_grade_v1250(['iron'],items),'high material matters')
    chk(material_quality_upgrade_v1250('good',4,0)=='excellent','material raises quality')
    chk(material_quality_upgrade_v1250('good',0,0)=='good','normal material unchanged')
    chk(secret_room_identity_v1190(secret_room_id_v1190('crypt',30,'vault')) == ('vault','crypt',30),'infinite vault identity')
    return checks

if __name__=='__main__': print('SOULBOUND v1.25 FEATURE TESTS:',audit_v1250(),'checks PASS')
