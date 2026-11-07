# -*- coding: utf-8 -*-
"""Early real gameplay integration of Magitek for v107 staging only.

Existing damage/kill/Xp/TCP paths stay owned by the Soulbound engine. This
adapter affects Magitek only; incomplete source-specific skills fail closed
instead of quietly behaving like unrelated generic skills.
"""
from __future__ import annotations
import random
import time
from functools import wraps

from core.player_math import character_attribute_power, character_offensive_build_multiplier
from systems.magitek_rules_v107 import (
    MagitekState, try_charge_missile, consume_missile_charge,
    gravity_bomb_damage, bio_poison_chance,
)

# The following source behaviours are not yet safe to enable in normal gameplay.
# Individual runnable skill tests and TCP integration are required first.
NOT_YET_INTEGRATED = frozenset()
SUPPORT_SKILLS = frozenset(('tekshield','tekbarrier','xfer','diffuser','runicweapon'))


def _is_magitek(self, skill):
    return bool(skill and skill.get('v107_magitek_authored') and
                getattr(getattr(self,'character',None),'class_name',None) == 'Magitek')


def _ranged(self):
    """No guessed equipment rule; an explicit verified weapon classification."""
    return bool(getattr(self, '_v107_verified_ranged_weapon', False))


def _state(self):
    state = getattr(self, '_v107_magitek_state', None)
    if not isinstance(state, MagitekState):
        state = MagitekState()
        self._v107_magitek_state = state
    return state


def install(combat_mixin):
    # Feed explicit UOSS elements to the existing weakness/reaction engine.
    from systems.elemental_combat import OLC_SKILL_ELEMENTS_V1500
    for name, element in ((
        'Fire Beam','fire'),('Ice Beam','ice'),
        ('Bolt Beam','lightning'),('Bio Blast','poison')
    ):
        key=('Magitek',name)
        old=OLC_SKILL_ELEMENTS_V1500.get(key)
        if old is not None and old!=element:
            raise RuntimeError('v107 Magitek element collision: '+name)
        OLC_SKILL_ELEMENTS_V1500[key]=element
    baseline_core = combat_mixin.offensive_skill_core_power_v11185
    baseline_damage_type = combat_mixin.offensive_skill_damage_type_v11190
    baseline_multiplier = combat_mixin.offensive_skill_damage_multiplier_v11186
    baseline_heal = combat_mixin.healing_skill_amount_v11196
    baseline_cast = combat_mixin.use_class_skill
    from systems.magitek_support_v107 import use_support_skill

    @wraps(baseline_core)
    def magitek_power(self, skill, authored_base=0):
        if not _is_magitek(self, skill):
            return baseline_core(self, skill, authored_base)
        slug = skill['v107_skill']
        if slug not in {'firebeam','icebeam','boltbeam','bioblast','tekmissile'}:
            return baseline_core(self, skill, authored_base)
        level = int(self.character.character_level)
        phys = int(self.effective_dexterity() if _ranged(self) else self.effective_strength())
        magic = int(self.effective_intelligence())
        # UOSS: two influences, weapon's own damage never enters the formula.
        # These weights are explicit, preliminary Soulbound balance values.
        base = (character_attribute_power(level,phys)+character_attribute_power(level,magic))//2
        flat = self.equipment_flat_power_totals_v11187()
        extra = (int(flat.get('attack',0)) + int(flat.get('magic_attack',0)))//2
        soul = max(0,int(self.character.soul_power()))
        build = character_offensive_build_multiplier((phys+magic)/2.0)
        return max(1,int((base+extra+soul+int(authored_base or 0))*build))

    @wraps(baseline_damage_type)
    def magitek_damage_type(self, skill):
        if _is_magitek(self,skill):
            return 'physical' if skill['v107_skill']=='tekmissile' else 'magic'
        return baseline_damage_type(self,skill)

    @wraps(baseline_multiplier)
    def magitek_damage_multiplier(self, skill, skill_class_type=None):
        mult = baseline_multiplier(self,skill,skill_class_type)
        if (_is_magitek(self,skill) and skill['v107_skill'] in
                {'firebeam','icebeam','boltbeam','bioblast','tekmissile'}
                and self.server.db.knows_skill(self.account_id,'v107_magitek_esperinfusion')):
            # Source specifies an increase but no numeric coefficient.
            mult *= 1.12  # Soulbound prototype
        return mult

    @wraps(baseline_heal)
    def magitek_heal(self, skill, target, skill_power):
        if _is_magitek(self,skill) and skill['v107_skill']=='healforce':
            # WILL-only scaling, never generic Int+Will for this source skill.
            will = max(1,int(self.effective_willpower()))
            level = int(self.character.character_level)
            core = character_attribute_power(level,will)
            return max(1,int(core*float(skill_power)*0.85))  # Soulbound tuning
        return baseline_heal(self,skill,target,skill_power)

    @wraps(baseline_cast)
    async def magitek_cast(self, raw):
        skill, target_text = self.find_skill_from_input(raw)
        if not _is_magitek(self,skill):
            return await baseline_cast(self,raw)
        slug=skill['v107_skill']
        if slug in SUPPORT_SKILLS:
            return await use_support_skill(self, skill, target_text)
        if slug == 'magicitelink':
            from systems.magitek_magicite_v107 import cast_magicite
            return await cast_magicite(self, skill, target_text)
        if slug == 'runic':
            await self.send('Runic to kontrumiejętność. Wybierz ją przez job set counter i nie rzucaj jako czaru.')
            return
        if slug in NOT_YET_INTEGRATED:
            await self.send(
                f'{skill["name"]}: mechanika jest jeszcze w budowie v107. '
                'Nie wykonano akcji ani nie pobrano zasobów.'
            )
            return
        if slug=='gravitybomb':
            # Do not substitute generic damage: the source says chance to
            # halve CURRENT HP. All gates and target checks come first.
            if self.current_hp<=0 or self.is_downed_v0371():
                await self.send('Powalona postać nie może atakować.')
                return
            if self.class_mastery_level('Magitek')<skill['unlock'] or not self.server.db.knows_skill(self.account_id,skill['id']):
                await self.send('Najpierw naucz się Gravity Bomb u nauczyciela Magiteka.')
                return
            mob=await self.skill_combat_target(target_text)
            if not mob or not mob.alive:
                return
            mastery = int(self.server.db.skill_progress(self.account_id,skill['id'])['level'])
            will = max(1,int(self.effective_willpower()))
            accuracy = min(.75,.22+min(.20,will/2500.0)+min(.20,mastery/1500.0))
            hit = gravity_bomb_damage(mob.hp,accuracy=accuracy,roll=random.random())
            if hit:
                mob.hp=max(0,int(mob.hp)-hit)
                await self.send(f'Gravity Bomb: {hit} obrażeń grawitacyjnych. HP celu {mob.hp}.')
                if mob.hp<=0:
                    await self.mob_defeated(mob)
            else:
                await self.send('Gravity Bomb: przeciwnik oparł się grawitacji.')
            await self.grant_skill_use_xp(skill)
            if mob.alive:
                await self.ensure_realtime_combat()
            return

        observe = slug in ('firebeam','icebeam','boltbeam','bioblast','tekmissile')
        if not observe:
            # Heal Force uses the canonical target validation / anti-heal guard.
            return await baseline_cast(self,raw)
        room_id = getattr(self.character,'room_id',None)
        old = {}
        if room_id is not None:
            old = {m.key:(m,int(m.hp)) for m in self.server.world.room_mobs(room_id)
                   if m.alive and m.hp>0}
        result=await baseline_cast(self,raw)
        deltas={key:max(0,hp-int(m.hp)) for key,(m,hp) in old.items()
                if m.room_id==room_id and int(m.hp)>=0}
        dealt = sum(deltas.values())
        if dealt<=0:
            return result
        state=_state(self)
        if slug=='tekmissile':
            element=consume_missile_charge(state,landed=True)
            if element:
                # Source says an elemental explosion, coefficient unspecified.
                # Extra damage uses surviving actual target, never another mob.
                key=getattr(self,'combat_mob_key',None)
                target=old.get(key,(None,0))[0]
                if target and target.alive and target.room_id==room_id and target.hp>0:
                    bonus=max(1,deltas.get(key,0)//4)  # Soulbound placeholder
                    bonus=min(int(target.hp),bonus)
                    target.hp-=bonus
                    await self.send(f'TekMissile: eksplozja {element}, dodatkowe {bonus} obrażeń.')
                    if target.hp<=0:
                        await self.mob_defeated(target)
                else:
                    await self.send(f'TekMissile: ładunek {element} rozładowany.')
        elif self.server.db.knows_skill(self.account_id,'v107_magitek_tekmastery'):
            mastery = self.server.db.skill_progress(self.account_id,'v107_magitek_tekmastery')
            if mastery is not None:
                chance=min(.55,.25+int(mastery['level'])/2500.0)
                if try_charge_missile(state,slug,time.monotonic(),mastered=True,
                                      roll=random.random(),chance=chance):
                    await self.send(f'Tek Mastery: naładowano TekMissile żywiołem {state.infused_element}.')
        return result

    combat_mixin.offensive_skill_core_power_v11185=magitek_power
    combat_mixin.offensive_skill_damage_type_v11190=magitek_damage_type
    combat_mixin.offensive_skill_damage_multiplier_v11186=magitek_damage_multiplier
    combat_mixin.healing_skill_amount_v11196=magitek_heal
    combat_mixin.use_class_skill=magitek_cast
