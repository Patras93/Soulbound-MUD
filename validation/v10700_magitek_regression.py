# -*- coding: utf-8 -*-
"""Soulbound v107 Magitek stage-1 validation (no game DB or network)."""
from __future__ import annotations
import os

from core.magitek.catalogue import (
    CLASS_NAME, CLASS_INFO, CLASS_BONUSES, SOURCE_WEAPONS, SOURCE_ARMOR,
    skill_catalogue,
)
from systems.magitek.rules import (
    MagitekState, attack_power, combat_attack_stats, can_use_skill,
    damage_defense_channel, apply_ward, active_ward,
    try_charge_missile, consume_missile_charge, gravity_bomb_damage,
    bio_poison_chance, runic_interception,
)

EXPECTED = {
    'firebeam': (1000, 1), 'icebeam': (1000, 1),
    'boltbeam': (1000, 1), 'healforce': (1000, 1),
    'tekshield': (400, 1), 'tekbarrier': (400, 1),
    'gravitybomb': (750, 1), 'bioblast': (1800, 1),
    'tekmissile': (2000, 1), 'xfer': (1000, 1),
    'diffuser': (1000, 8), 'runicweapon': (800, 12),
    'magicitelink': (1200, 15), 'runic': (400, 1),
    'esperinfusion': (2000, 1), 'tekmastery': (5000, 12),
}


def run():
    checks = 0
    def ok(condition, label):
        nonlocal checks
        if not condition:
            raise AssertionError('MAGITEK: '+label)
        checks += 1

    skills = skill_catalogue()
    ok(len(skills) == 16, '16 sourced abilities')
    ok(CLASS_INFO[0] == CLASS_NAME == 'Magitek', 'name')
    ok(sum(CLASS_BONUSES.values()) == 9, 'balanced starting stat budget')
    ok(set(SOURCE_WEAPONS) == {'Greatsword','Gun','Rod','Sword'}, 'source weapons')
    ok(set(SOURCE_ARMOR) == {'Armor','Robe','Helmet','Shield'}, 'source armour')
    ok(len({s['id'] for s in skills}) == len(skills), 'unique IDs')
    ok(len({s['name'] for s in skills}) == len(skills), 'unique names')
    for s in skills:
        slug = s['v107_skill']
        ok(slug in EXPECTED, slug+' sourced')
        ok((s['source_ap_cost'],s['unlock']) == EXPECTED[slug], slug+' AP/unlock')
        ok(s['source_ap_semantics'] == 'training' and s['mana'] == 0, slug+' AP not mana')
        ok(s['v107_magitek_authored'] and s['soulbound_runtime_stage'] == 'experimental',slug+' staging')
    ok(can_use_skill('firebeam',1)[0], 'no class unlock quest / min level 95')
    ok(not can_use_skill('diffuser',7)[0] and can_use_skill('diffuser',8)[0], 'diffuser lvl8')
    ok(not can_use_skill('runicweapon',11)[0] and can_use_skill('tekmastery',12)[0], 'lvl12')
    ok(not can_use_skill('magicitelink',14)[0], 'magicite lvl15')
    ok(not can_use_skill('magicitelink',15)[0], 'magicite unique unlock')
    ok(not can_use_skill('magicitelink',15,magicite_unlocked=True)[0], 'magicite linked accessory')
    ok(can_use_skill('magicitelink',15,magicite_unlocked=True,linked_magicite='Ifrit')[0], 'valid magicite')
    ok(combat_attack_stats(99,33,55,ranged_weapon=False)==(99,55),'melee STR')
    ok(combat_attack_stats(99,33,55,ranged_weapon=True)==(33,55),'ranged AGI')
    ok(attack_power(99,33,55,ranged_weapon=True)<attack_power(99,33,55,ranged_weapon=False),'weapon not directly damage')
    ok(damage_defense_channel('tekmissile')=='physical', 'missile physical defense')
    ok(damage_defense_channel('firebeam')=='magic', 'beams magic defense')
    ok(damage_defense_channel('bioblast')=='magic', 'bio magic defense')
    state=MagitekState()
    ok(apply_ward(state,'tekshield',100.0,10)==('protect','shell'),'shield two buffs')
    ok(active_ward(state,105)=='tekshield','shield duration')
    ok(apply_ward(state,'tekbarrier',106,7)==('protect','reflect'),'shield/barrier exclusive')
    ok(active_ward(state,114) is None,'ward expiry')
    state=MagitekState()
    ok(not try_charge_missile(state,'firebeam',100,mastered=False,roll=0),'no mastery no charge')
    ok(try_charge_missile(state,'firebeam',100,mastered=True,roll=0),'mastery fire charge')
    ok(state.infused_element=='fire','fire type')
    ok(not try_charge_missile(state,'firebeam',101,mastered=True,roll=0),'same element cooldown')
    ok(not try_charge_missile(state,'icebeam',101,mastered=True,roll=.99),'failed random chance')
    ok(try_charge_missile(state,'icebeam',101,mastered=True,roll=0),'switch element')
    ok(consume_missile_charge(state,landed=False) is None and state.infused_element=='ice','miss preserved on failure')
    ok(consume_missile_charge(state,landed=True)=='ice','missile consumes charge')
    ok(state.infused_element is None,'one charge only')
    ok(try_charge_missile(state,'firebeam',120,mastered=True,roll=0),'cooldown expired')
    ok(gravity_bomb_damage(101,accuracy=.5,roll=.2)==50,'half current HP on hit')
    ok(gravity_bomb_damage(101,accuracy=.5,roll=.9)==0,'not guaranteed')
    ok(gravity_bomb_damage(0,accuracy=.5,roll=0)==0,'not hit dead')
    ok(bio_poison_chance(300,200)>bio_poison_chance(30,1),'will and level affect poison')
    ok(runic_interception(magical_attack=False,roll=0,chance=.5,wisdom=100,willpower=120,weapon_power=20)==(False,0),'runic magic only')
    success,mp=runic_interception(magical_attack=True,roll=0,chance=.5,wisdom=100,willpower=120,weapon_power=20)
    ok(success and mp>0,'runic restores mana')
    ok(runic_interception(magical_attack=True,roll=.9,chance=.5,wisdom=100,willpower=120,weapon_power=20)==(False,0),'runic random fail')
    ok(skills[[s['v107_skill'] for s in skills].index('xfer')]['soulbound_destination']=='square','X-Fer hub adaptation')
    ok('source_no_eidolon_echo' in next(s for s in skills if s['v107_skill']=='magicitelink'),'no Eidolon Echo')
    # Only load actual staged catalogs when explicitly enabled. Importing this
    # suite normally must not mutate the normal v106 runtime.
    if os.environ.get('SOULBOUND_V107_STAGING')=='1':
        # Load 22-class historical services before adding staging-only class.
        from systems.content_registry import NPCS
        import core.classes_skills as _v107_catalogue
        if not any(row[0]=='Magitek' for row in _v107_catalogue.CLASSES):
            from core.magitek.catalogue import install as _v107_install
            _v107_install(vars(_v107_catalogue))
        from core.classes_skills import CLASSES, CLASS_SKILLS
        from systems.content_registry import NPCS
        ok(len(CLASSES)==23 and CLASSES[-1]==CLASS_INFO,'real game class catalogue')
        ok(len(CLASS_SKILLS.get('Magitek',()))==16,'real game skill catalogue')
        ok(NPCS.get('teacher_magitek_v107',{}).get('teacher_class')=='Magitek','real teacher')
        from systems.equipment_crafting import GUILD_CLASS_QUEST_POOLS, install_magitek_guild_v107
        install_magitek_guild_v107()
        ok(len(GUILD_CLASS_QUEST_POOLS['Magitek'])==5,'guild quest pool')
        from player.session_mixins.combat_skills import SessionCombatSkillsMixin
        from player.session_mixins.command_registry import resolve_session_command
        from systems.elemental_combat import skill_element_v11339
        from types import SimpleNamespace
        from unittest.mock import patch
        import asyncio

        ok(resolve_session_command('mtek','firebeam')=='mtek', 'mtek command registered')
        for ability, element in (('Fire Beam','fire'),('Ice Beam','ice'),
                                 ('Bolt Beam','lightning'),('Bio Blast','poison')):
            ok(skill_element_v11339('Magitek',ability)==element,'real '+ability+' element')

        class Character:
            class_name='Magitek'; character_level=50; room_id='square'; name='Tester'
            def soul_power(self): return 120
        class Smoke:
            character=Character()
            _v107_verified_ranged_weapon=False
            def effective_strength(self): return 100
            def effective_dexterity(self): return 80
            def effective_intelligence(self): return 110
            def equipment_flat_power_totals_v11187(self):
                return {'attack':10,'magic_attack':20,'weapon_power':999999}
        smoke=Smoke()
        beam=next(row for row in CLASS_SKILLS['Magitek'] if row['v107_skill']=='firebeam')
        melee=SessionCombatSkillsMixin.offensive_skill_core_power_v11185(smoke,beam)
        smoke._v107_verified_ranged_weapon=True
        ranged=SessionCombatSkillsMixin.offensive_skill_core_power_v11185(smoke,beam)
        ok(melee>ranged>0,'hybrid real STRENGTH/AGILITY channel')
        ok(SessionCombatSkillsMixin.offensive_skill_damage_type_v11190(smoke,beam)=='magic','beam real magic-defense channel')
        missile=next(row for row in CLASS_SKILLS['Magitek'] if row['v107_skill']=='tekmissile')
        ok(SessionCombatSkillsMixin.offensive_skill_damage_type_v11190(smoke,missile)=='physical','missile real physical-defense channel')
        ok(melee<999999,'equipped weapon power not in beam')

        class FakeDB:
            def knows_skill(self,account,skill): return True
            def skill_progress(self,account,skill): return {'level':40}
        class FakeMob:
            room_id='square'; key='fake'; hp=101
            @property
            def alive(self): return self.hp>0
        class CastSession:
            character=Character(); account_id=123; current_hp=100
            server=SimpleNamespace(db=FakeDB())
            def __init__(self,skill): self.skill=skill; self.sent=[];self.xp=0;self.mob=FakeMob()
            def find_skill_from_input(self,raw): return self.skill,''
            def class_mastery_level(self,name): return 40
            def is_downed_v0371(self): return False
            def effective_willpower(self): return 150
            async def skill_combat_target(self,target): return self.mob
            async def grant_skill_use_xp(self,skill): self.xp+=1
            async def ensure_realtime_combat(self): pass
            async def mob_defeated(self,mob): pass
            async def send(self,msg): self.sent.append(msg)
        gravity=next(row for row in CLASS_SKILLS['Magitek'] if row['v107_skill']=='gravitybomb')
        async def try_gravity(roll):
            actor=CastSession(gravity)
            with patch('systems.magitek.runtime.random.random',return_value=roll):
                await SessionCombatSkillsMixin.use_class_skill(actor,'gravitybomb')
            return actor
        hit=asyncio.run(try_gravity(0))
        miss=asyncio.run(try_gravity(.99))
        ok(hit.mob.hp==51 and hit.xp==1,'real gravity: half current HP on hit')
        ok(miss.mob.hp==101 and miss.xp==1,'real gravity: resist not guaranteed')
        shield=next(row for row in CLASS_SKILLS['Magitek'] if row['v107_skill']=='tekshield')
        protected=CastSession(shield)
        protected.active_skill_buffs={}
        asyncio.run(SessionCombatSkillsMixin.use_class_skill(protected,'tekshield'))
        ok(protected.mob.hp==101 and protected.xp==1 and protected.sent, 'shield executed')
        ok(protected.active_skill_buffs.get('v107_magitek_ward',{}).get('magitek_mode')=='tekshield','shield applied to real active buff')
    print(f'V107 MAGITEK ETAP 1: {checks} kontroli PASS')
    return checks

if __name__=='__main__':
    run()
