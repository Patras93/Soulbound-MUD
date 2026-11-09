# -*- coding: utf-8 -*-
"""Soulbound v109: oryginalne metody, wydzielone bez zmiany kodu."""
from __future__ import annotations
from .dependencies import *

class SkySummonCombatV109Mixin:
    async def summon_take_enemy_hit_v1702(self,mob,raw_damage=None,roll=None):
        """An enemy can attack and destroy a real summon instead of its master.

        Only replaces an ordinary hit. Source-authored scripted boss mechanics
        and phases are still resolved by the main combat loop.
        """
        if not self.character or not mob or not mob.alive:return False
        # No pets? Skip all work. A class change never keeps another class's
        # minions active in combat even if the database remembers them.
        conn=self._v1700_conn()
        self._v1702_prepare_summon_lives(conn)
        self._v1710_refresh_summon_health(conn)
        pets=[r for r in conn.execute('SELECT summon_type,level,hp,max_hp,stance FROM summons_v1700 '
                'WHERE account_id=? AND active=1 AND hp>0',(self.account_id,)).fetchall()
              if r['summon_type'] in SUMMONS and self._v1700_class(SUMMONS[r['summon_type']][1])]
        if not pets:return False
        from systems.live_olc27_master import summon_may_intercept
        pets=[r for r in pets if summon_may_intercept(r['summon_type'],r['hp'],r['max_hp'])]
        if not pets:return False
        from systems.live_olc26_world import summon_intercept_chance, summon_incoming_damage
        guarding = any(r['stance']=='bron' for r in pets)
        # An active summoned protector contributes its authored intercept chance.
        chance = max(summon_intercept_chance(r['summon_type'],guarding) for r in pets)
        if (random.random() if roll is None else roll)>=chance:return False
        chosen=random.choice(pets)
        hp=int(chosen['hp']);maximum=max(1,int(chosen['max_hp']))
        # A real monster hit. The percentage floor prevents companions from
        # surviving forever on enormous late-game HP while mobs deal tiny hits.
        base=max(1,int(raw_damage if raw_damage is not None else
                       MOB_TEMPLATES.get(mob.template_id,{}).get('damage',1)))
        pressure=max(1,int(maximum*.10))
        hit=max(base,pressure)
        # Vitality roles endure longer, but every summon can eventually fall.
        kind=chosen['summon_type']
        if kind in ('ancientoak','niedzwiedz') or kind.startswith(('zywiolak_lod','zywiolak_krysztal')):
            hit=max(1,int(hit*.75))
        if kind in NECRO_MINIONS and NECRO_MINIONS[kind][7]=='obrona':
            hit=max(1,int(hit*.72))
        if kind in ANIMALS and ANIMALS[kind]['role']=='obrona':
            hit=max(1,int(hit*.80))
        # Veteran guardians learn to brace, but damage reduction never exceeds 40%.
        if kind in NECRO_MINIONS or kind in ANIMALS:
            reduction=min(.15,max(0,int(chosen['level'])-1)*.002)
            hit=max(1,int(hit*(1-reduction)))
        hit=min(hp,summon_incoming_damage(kind,hit))
        remaining=max(0,hp-hit)
        conn.execute('UPDATE summons_v1700 SET hp=?,active=? '
                     'WHERE account_id=? AND summon_type=? AND hp=? AND active=1',
                     (remaining,1 if remaining>0 else 0,self.account_id,kind,hp))
        conn.commit()
        name=SUMMONS[kind][0]
        enemy_name=MOB_TEMPLATES.get(mob.template_id,{}).get('name','Przeciwnik')
        if remaining:
            msg=f'{enemy_name} atakuje {name} za {hit} obrażeń. {name}: {remaining}/{maximum} HP.'
        else:
            msg=f'{enemy_name} rozbija {name}! Pomocnik traci całe HP i znika. Aby przywołać go ponownie, użyj chowaniec aktywuj {kind} (mana i materiały).'
        await self.send_combat(msg,detail='essential')
        await self.server.party_combat_broadcast(self,msg,detail='essential')
        return True

    @measure_async("summon.combat_turn", report_every=50)
    async def summon_combat_turn_v1700(self,mob):
        if not self.character or not mob or not mob.alive or mob.room_id!=self.character.room_id:return
        conn=self._v1700_conn()
        self._v1702_prepare_summon_lives(conn)
        self._v1710_refresh_summon_health(conn)
        rows=conn.execute('SELECT summon_type,level,soul_rank,stance FROM summons_v1700 WHERE account_id=? AND active=1 AND hp>0',(self.account_id,)).fetchall()
        if not rows:return
        from systems.summon_ai_v1200 import (plan_for_class, profession_amulet_bonus)
        _ai_pref=conn.execute('SELECT enabled FROM summon_ai_prefs_v1200 WHERE account_id=?',(self.account_id,)).fetchone()
        _ai_enabled=(_ai_pref is None or bool(_ai_pref['enabled']))
        _ai_step=int(getattr(self,'_v1200_ai_step',0) or 0)+1
        self._v1200_ai_step=_ai_step
        _amulet_bonus=profession_amulet_bonus(self.server.db,self.account_id) if _ai_enabled else 0.0
        # Mixed assault/guard/support orders produce a small tactical synergy.
        # Calculated from the existing active summon rows: no new timers or tables.
        _v1800_team_roles={str(r['stance']) for r in rows if r['summon_type'] in SUMMONS}
        _v1800_team_bonus=1.06 if len(rows)>=2 and len(_v1800_team_roles)>=2 else 1.0
        # No loss of mercenary damage. Summons use their own extra attacks.
        # Costs common to the whole summon volley are not recalculated for
        # each hit. Tactic/formation stays per-hit because HP can change.
        spell_power = max(1, int(self.spell_power()))
        raw_power=max(1,int(max(self.physical_power(), spell_power)))
        _walls,_workshop,_infirmary=self._v1700_city_bonuses()
        # Owner maximum HP is invariant over the volley; avoid rebuilding
        # equipment, professions and buffs for each animal/elemental hit.
        owner_max_hp=max(1,int(self.max_hp()))
        # Use the Mage's real expected magical attack as a reference. Old
        # summon scaling remains a damage floor. One calculation per volley,
        # rather than recomputing equipment and criticals for each elemental.
        owner_expected_magic = spell_power
        if any(r['summon_type'] in ELEMENTALS for r in rows):
            expected_attack = getattr(self, 'consider_player_expected_hit', None)
            if callable(expected_attack):
                owner_expected_magic = max(spell_power, float(expected_attack()))
        for row in rows:
            if not mob.alive or mob.hp<=0:break
            spec=SUMMONS.get(row['summon_type'])
            if not spec or not self._v1700_class(spec[1]):continue
            name,_,_,kind,factor=spec
            stance=row['stance'] if 'stance' in row.keys() else 'atakuj'
            if stance=='czekaj':continue
            _ai_plan=None
            _ai_message=''
            if _ai_enabled:
                _injured=[]
                # Legacy combat fixtures have no party lookup; ordinary solo
                # summons still run their full AI. Real party servers expose
                # party_sessions and continue to share heals with teammates.
                _party_sessions=getattr(self.server,'party_sessions',None)
                if callable(_party_sessions):
                    for _ally in (_party_sessions(self.account_id,same_room=self.character.room_id) or []):
                        if (not getattr(_ally,'closed',False) and getattr(_ally,'character',None)
                                and getattr(_ally,'current_hp',0)>0
                                and _ally.current_hp<_ally.max_hp()):
                            _injured.append(_ally)
                if (self.current_hp>0 and self.current_hp<self.max_hp()
                        and self not in _injured):
                    _injured.append(self)
                from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
                _injured=[a for a in _injured if not superboss_healing_blocked_v11179(a)]
                _injured.sort(key=lambda a:a.current_hp/max(1,a.max_hp()))
                _ai_plan=plan_for_class(
                    spec[1],owner_hp=self.current_hp,owner_max=owner_max_hp,
                    ally_needs_heal=bool(_injured),guarded=int(getattr(self,'skill_guard',0) or 0)>0,
                    enemy_hp=mob.hp,enemy_max=max(1,getattr(mob,'max_hp',mob.hp)),
                    boss=bool(MOB_TEMPLATES.get(mob.template_id,{}).get('boss') or
                              MOB_TEMPLATES.get(mob.template_id,{}).get('is_boss')),
                    marked=float(getattr(mob,'_v1200_marked_until',0) or 0)>time.monotonic(),
                    controlled=max(0,int(getattr(mob,'v11196_logic_bomb_rounds',0) or 0))>0,
                    step=_ai_step)
                if _ai_plan['action']=='heal' and _injured:
                    _ally=_injured[0]
                    _missing=max(0,_ally.max_hp()-_ally.current_hp)
                    if _missing>0:
                        _healed=min(_missing,max(1,int(_ally.max_hp()*(.018+_ai_plan['bonus']*.32+_amulet_bonus*.20))))
                        _ally.current_hp+=_healed
                        _ai_message=f"{_ai_plan['ability']}: {_ally.character.name} +{_healed} HP."
                        if _ally is not self:
                            await _ally.send(f'{name} leczy cię o {_healed} HP.')
                elif _ai_plan['action']=='guard':
                    _guard=max(1,int(owner_max_hp*(.018+_ai_plan['bonus']*.25+_amulet_bonus*.20)))
                    self.skill_guard=max(int(getattr(self,'skill_guard',0) or 0),_guard)
                    _ai_message=f"{_ai_plan['ability']}: osłona +{_guard}."
                elif _ai_plan['action']=='mark':
                    mob._v1200_marked_until=time.monotonic()+12.0
                    _ai_message=f"{_ai_plan['ability']}: cel oznaczony."
                elif _ai_plan['action'] in ('curse','slow'):
                    _template=MOB_TEMPLATES.get(mob.template_id,{})
                    from systems.boss_companions_v1281 import boss_jammer_immune_v1281
                    if not boss_jammer_immune_v1281(_template):
                        mob.v11196_logic_bomb_rounds=max(2,int(getattr(mob,'v11196_logic_bomb_rounds',0) or 0))
                        mob.v11196_logic_bomb_effects=set(getattr(mob,'v11196_logic_bomb_effects',set()) or set())|({'slow'} if _ai_plan['action']=='slow' else {'curse'})
                        mob.v11196_logic_bomb_cleanseable=True
                        _ai_message=f"{_ai_plan['ability']}: {_ai_plan['action']} na 2 akcje."

            elemental=ELEMENTALS.get(row['summon_type'])
            if elemental:
                # Alter Aeon-style sustaining energy: no mana means no elemental strike.
                upkeep=elemental['upkeep']
                if self.current_mana<upkeep:
                    continue
                self.current_mana-=upkeep
            necro=NECRO_MINIONS.get(row['summon_type'])
            if necro:
                upkeep=necro[8]
                if self.current_mana<upkeep:
                    continue
                self.current_mana-=upkeep
            grade=max(0,min(8,int(row['soul_rank'] or 0)))
            name=summon_display(row['summon_type'],grade)
            factor*=SOULSTONE_TIERS[grade][3] if row['summon_type'] in ('wojownik','mag') else 1.0
            mastery=self._v1806_owner_summon_level(row['summon_type'],row['level'])
            # Elementals always scale with the Mage's spell power (INT/WIS and
            # equipment), NOT physical strength or their obsolete summon XP.
            caster_power=(spell_power if elemental or (row['summon_type'] in CLASS_MINIONS_V1119 and kind=='magic') else max(1,int(self.physical_power())) if row['summon_type'] in CLASS_MINIONS_V1119 else raw_power)
            stance_factor=.8 if stance=='bron' else (.7 if stance=='wspieraj' else 1.0)
            formation_bonus,formation_guard=self._v1800_form_bonus()
            workshop_bonus=(1+min(.28,.008*_workshop))
            amount=max(1,int(caster_power*factor*stance_factor*formation_bonus*_v1800_team_bonus*(1+mastery*.07)*workshop_bonus))
            from systems.live_olc24_revolution import summon_factor
            amount=max(1,int(amount*summon_factor(row['summon_type'],'damage_percent')/100))
            from systems.live_olc28_expansion import summon_outgoing
            amount=summon_outgoing(row['summon_type'],amount)
            from systems.live_olc32_finale import summon_combo
            amount=summon_combo(self, row['summon_type'], amount)
            from systems.live_olc34_integration import summon_finisher
            amount=summon_finisher(row['summon_type'],mob,amount)
            from systems.live_olc33_mechanics import summon_support
            _heal33=summon_support(self,row['summon_type'])
            if _heal33:
                await self.send(f'Przywołanie {name} leczy cię o {_heal33} HP.')
            if _ai_plan:
                amount=max(1,int(amount*(1+_ai_plan['bonus']+_amulet_bonus)))
                if float(getattr(mob,'_v1200_marked_until',0) or 0)>time.monotonic():
                    amount=max(1,int(amount*1.06))
            if elemental:
                amount=effective_elemental_strike_v2008(
                    amount, elemental, owner_expected_magic, stance_factor,
                    formation_bonus, _v1800_team_bonus, workshop_bonus,
                )
            if formation_guard and self.skill_guard<=0:
                self.skill_guard=max(1,int(owner_max_hp*formation_guard))
            if self._v1800_tactic()=='harmonia' and self.current_hp<owner_max_hp:
                from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
                if not superboss_healing_blocked_v11179(self):
                    self.current_hp=min(owner_max_hp,self.current_hp+max(1,int(owner_max_hp*.003)))
            if stance=='bron':
                self.skill_guard=max(int(getattr(self,'skill_guard',0) or 0),max(1,int(owner_max_hp*.02)))
            if stance=='wspieraj':
                self.current_hp=min(owner_max_hp,self.current_hp+max(1,int(owner_max_hp*.015)))
            if elemental and elemental['element'] in ('lod','krysztal'):
                # Ice and crystal specialize in shielding. Use the preexisting guard
                # contract, consumed on the next incoming hit; don't overwrite buffs.
                guard_base=(.025,.05,.085)[elemental['rank']] if elemental['element']=='lod' else (.02,.035,.06)[elemental['rank']]
                barrier=max(1,int(owner_max_hp * min(.12,guard_base+min(.015,mastery*.0004))))
                self.skill_guard=max(int(getattr(self,'skill_guard',0) or 0),barrier)
            from systems.eternal_glory_companions_v1100 import companion_coordination_v1100
            amount = max(amount, int(amount * companion_coordination_v1100(
                MOB_TEMPLATES.get(mob.template_id, {}), is_summon=True)))
            amount=await self.apply_boss_defense(mob,amount)
            amount=self.v0210_adjust_player_damage(amount)
            from world.machine_expansion import v0314_adjust_damage_vs_template
            amount,_=v0314_adjust_damage_vs_template(MOB_TEMPLATES.get(mob.template_id,{}),amount,kind,name)
            # Chaos God phases suppress summoned blows only; old bosses unchanged.
            amount=max(1,int(amount*(1.0-.05*int(getattr(mob,'_v1800_chaos_phase',0) or 0))))
            # Ancient Gods grow more resistant to summon swarms as their seals fall.
            amount=max(1,int(amount*(1.0-.06*min(3,int(getattr(mob,'_v1900_god_phase',0) or 0)))))
            elemental_key=ELEMENT_ALIASES.get(elemental['element']) if elemental else ('dark' if necro and spec[3]=='magic' else None)
            damage=min(max(0,int(mob.hp)),max(1,int(amount)))
            if elemental_key:
                bonus=await self._v1800_elemental_reaction(mob,elemental_key,damage)
                damage=min(max(0,int(mob.hp)),damage+bonus)
            mob.hp-=damage
            # Apply a REAL finite status only on a surviving target. Its DOT and
            # one-action controls are processed by the shared enemy combat loop.
            summon_status_text = apply_summon_status_v1808(
                mob, row['summon_type'], damage,
                MOB_TEMPLATES.get(mob.template_id, {}), elemental=elemental)
            if row['summon_type'] in ('lifeoak','ancientoak'):
                from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
                if not superboss_healing_blocked_v11179(self):
                    heal=min(max(0,owner_max_hp-self.current_hp),max(1,int(damage*.06)))
                    self.current_hp+=heal
            target_name=str(MOB_TEMPLATES.get(mob.template_id, {}).get('name') or mob.template_id)
            msg=(f'{name} (przywołanie {getattr(self.character, "name", None) or "gracza"}, poziom {mastery}) '
                 f'trafia {target_name} za {damage} obrażeń. '
                 f'{target_name}: {max(0,mob.hp)} HP.')
            if elemental:
                msg+=f' Mana -{elemental["upkeep"]} MP.'
            if necro:
                msg+=f' Mana utrzymania -{necro[8]} MP.'
            if _ai_message:
                msg += ' AI: ' + _ai_message
            if summon_status_text:
                msg += ' ' + summon_status_text
            await self.send_combat(msg,detail='essential')
            await self.server.party_combat_broadcast(self,msg,detail='essential')
            if mob.hp<=0:
                await self.mob_defeated(mob)
                return

    def class_damage_multiplier_v1700(self):
        return 1.14 if self.class_path_v1700()=='ofensywa' else 1.0

    async def class_support_turn_v1700(self):
        path=self.class_path_v1700()
        walls,workshop,infirmary=self._v1700_city_bonuses()
        if walls and self.skill_guard<=0:
            self.skill_guard=max(1,int(self.max_hp()*min(.20,.01*walls)))
        if infirmary and self.current_hp<self.max_hp():
            from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
            if not superboss_healing_blocked_v11179(self):
                self.current_hp=min(self.max_hp(),self.current_hp+max(1,int(self.max_hp()*min(.12,.005*infirmary))))
        if path=='obrona' and self.skill_guard<=0:
            self.skill_guard=max(1,int(self.max_hp()*.04))
        if path=='wsparcie' and self.current_hp<self.max_hp():
            from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
            if not superboss_healing_blocked_v11179(self):
                self.current_hp=min(self.max_hp(),self.current_hp+max(1,int(self.max_hp()*.02)))

