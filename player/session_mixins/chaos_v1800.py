# -*- coding: utf-8 -*-
"""v1.80.0: persistent summon formations, limited reactions and class masteries."""
from __future__ import annotations
import time
from data.mobs import MOB_TEMPLATES
from systems.era_chaos_v1800 import CLASS_MASTERY, compute_reaction, ELEMENT_ALIASES

FORMATIONS = {
    'szturm':('Ofensywa przywołań',1.08,0.0),
    'bastion':('Ochrona drużyny',.94,.04),
    'harmonia':('Wspomaganie i leczenie',.97,.015),
    'auto':('Inteligentne dostosowanie do zagrożenia',1.0,0.0),
}


def ensure_combat_v1800(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS summon_tactics_v1800 (
        account_id INTEGER PRIMARY KEY, formation TEXT NOT NULL DEFAULT 'szturm')''')
    conn.execute('''CREATE TABLE IF NOT EXISTS mastery_cooldown_v1800 (
        account_id INTEGER NOT NULL, class_name TEXT NOT NULL,
        ready_at INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (account_id,class_name))''')
    conn.commit()


class SessionChaosV1800Mixin:
    def _v1800_tactic(self):
        conn=self._v1700_conn()
        if not getattr(self.server.db,'_v1800_ready',False):
            ensure_combat_v1800(conn)
            self.server.db._v1800_ready=True
        if hasattr(self,'_v1800_tactic_cache'):
            return self._v1900_resolve_tactic(self._v1800_tactic_cache)
        row=conn.execute('SELECT formation FROM summon_tactics_v1800 WHERE account_id=?',(self.account_id,)).fetchone()
        result=str(row['formation']) if row else 'szturm'
        result=result if result in FORMATIONS else 'szturm'
        self._v1800_tactic_cache=result
        return self._v1900_resolve_tactic(result)

    def _v1900_resolve_tactic(self, stored):
        """Automatic, owner-level summon AI with bounded, readable decisions."""
        if stored != 'auto':
            return stored
        if not getattr(self, 'character', None):
            return 'szturm'
        maximum = max(1, int(self.max_hp()))
        if int(getattr(self, 'current_hp', maximum)) * 100 < maximum * 55:
            return 'harmonia'
        mob = (self.server.world.mobs.get(self.combat_mob_key)
               if getattr(self, 'combat_mob_key', None) else None)
        if mob and getattr(mob, 'alive', False):
            template = MOB_TEMPLATES.get(mob.template_id, {})
            if template.get('boss') or template.get('world_boss') or template.get('v1900_ancient_god'):
                return 'bastion'
        return 'szturm'

    async def tactics_v1800(self, raw=''):
        if not self.character:return
        from player.session_mixins.era_sky_v1700 import ascii_fold
        choice=ascii_fold(raw)
        if choice.startswith('formacja '):choice=choice[9:].strip()
        if choice in FORMATIONS:
            conn=self._v1700_conn();ensure_combat_v1800(conn)
            self._v1800_tactic_cache=choice
            conn.execute('INSERT INTO summon_tactics_v1800(account_id,formation) VALUES(?,?) '
                         'ON CONFLICT(account_id) DO UPDATE SET formation=excluded.formation',
                         (self.account_id,choice));conn.commit()
            await self.send(f'Formacja przywołań: {choice} — {FORMATIONS[choice][0]}.')
            return
        state=self._v1800_tactic()
        await self.send(f'TAKTYKA PRZYWOŁAŃ: {state} — {FORMATIONS[state][0]}. '
                        'taktyka szturm / bastion / harmonia / auto. Auto zmienia formację zależnie od HP i przeciwnika; nie zmienia EXP.')

    def _v1800_form_bonus(self):
        return FORMATIONS[self._v1800_tactic()][1:]

    async def _v1800_elemental_reaction(self,mob,element,amount):
        """Reaction only when an alive summon strikes the same mob with a new element.
        Monotonic window and cooldown prevent duplicate procs from fast multi-hits.
        """
        element=ELEMENT_ALIASES.get(element,element)
        if not element:return 0
        now=time.monotonic()
        last=getattr(mob,'_v1800_last_element',None)
        mob._v1800_last_element=(element,now)
        if not last or now-last[1]>12 or now<float(getattr(mob,'_v1800_reaction_until',0)):
            return 0
        name,damage=compute_reaction(last[0],element,amount)
        if not damage:return 0
        mob._v1800_reaction_until=now+8
        await self.server.party_combat_broadcast(
            self, f'Reakcja żywiołów: {name}! Dodatkowe {damage} obrażeń.',detail='essential')
        return damage

    async def chaos_boss_phase_v1800(self,mob):
        template=MOB_TEMPLATES.get(getattr(mob,'template_id',''),{})
        if not template.get('v1800_chaos_boss') or not getattr(mob,'alive',False):return
        maximum=max(1,int(self.mob_effective_max_hp_v11330(mob,template)))
        hp=max(0,int(mob.hp))
        stage=sum(hp*100<=maximum*value for value in (75,50,25))
        old=int(getattr(mob,'_v1800_chaos_phase',0) or 0)
        if stage<=old:return
        mob._v1800_chaos_phase=stage
        phases=('','Przebudzenie Furii','Złamanie Pieczęci','Ostatni Gniew')
        await self.server.party_combat_broadcast(
            self, f'{template["name"]}: {phases[stage]}! Faza {stage}/3, '
                  f'odporność na ciosy przywołań rośnie.',detail='essential')

    async def ancient_boss_phase_v1900(self, mob):
        """Phases for the new gods, respecting earlier scripted superbosses."""
        template=MOB_TEMPLATES.get(getattr(mob,'template_id',''),{})
        if not template.get('v1900_ancient_god') or not getattr(mob,'alive',False):
            return
        maximum=max(1,int(self.mob_effective_max_hp_v11330(mob,template)))
        current=max(0,int(mob.hp))
        stage=sum(current*100<=maximum*threshold for threshold in (70,40,15))
        old=int(getattr(mob,'_v1900_god_phase',0) or 0)
        if stage<=old:
            return
        mob._v1900_god_phase=stage
        names=('','Przełamanie Pierwszej Pieczęci','Gniew Pradawnych','Ostatnia Przysięga')
        await self.server.party_combat_broadcast(self,
            f'{template.get("name", "Pradawny Bóg")}: {names[stage]}! Faza {stage}/3. '
            'Potężniejsze kontrataki i odporniejsze fazowo przywołania.',
            detail='essential')

    async def underground_guide_v1900(self, raw=''):
        from systems.underground_kingdoms_v1900 import KINGDOMS,DIMENSIONS
        await self.send('PODZIEMNE KRÓLESTWA: Rozdroże Bogów Chaosu -> DÓŁ. '
                        'Z Bramy: północ, wschód, południe do krain; zachód do Wymiarów Chaosu.')
        for _,zone,element,level,*_ in KINGDOMS:
            await self.send(f'{zone}: sugerowana moc {level}, element {element}.')
        for _,zone,element,level in DIMENSIONS:
            await self.send(f'{zone}: próba poziomu {level}, element {element}.')
        await self.send('Nie ma limitów poziomów ani pułapek; stare nieskończone lochy działają jak wcześniej.')

    async def chaos_bosses_v1800(self,raw=''):
        from systems.era_chaos_v1800 import CHAOS_REALMS
        await self.send('BOGOWIE CHAOSU: wejście z Targu Osad Założycieli w ZACHÓD.')
        for slug,title,element,level,bosses in CHAOS_REALMS:
            await self.send(f'{title}, zalecana moc {level}: '+', '.join(bosses)+'.')
        await self.send('Zadania u Kronikarzy na początku każdej krainy. 3 fazy bossów: 75%, 50%, 25% HP.')

    async def reactions_info_v1800(self,raw=''):
        from systems.era_chaos_v1800 import REACTIONS
        await self.send('MAGIA ŻYWIOŁÓW 3.0: różne kolejne żywioły przywołań na jednym celu wywołują reakcję; jeden efekt nie częściej niż co 8 sekund.')
        for pair,(name,mult) in REACTIONS.items():
            await self.send(f'{" + ".join(sorted(pair))}: {name}, dodatkowe {int(mult*100)}% obrażeń kolejnego trafienia.')

    async def class_mastery_v1800(self,raw=''):
        if not self.character:return
        from player.session_mixins.era_sky_v1700 import ascii_fold
        name=str(self.character.class_name)
        ability=CLASS_MASTERY.get(name)
        if not ability:
            await self.send('Brak przypisanej mistrzowskiej umiejętności dla tej klasy.');return
        skill,kind,element=ability
        level=max(1,int(self.character.character_level))
        conn=self._v1700_conn();ensure_combat_v1800(conn)
        row=conn.execute('SELECT ready_at FROM mastery_cooldown_v1800 WHERE account_id=? AND class_name=?',
                         (self.account_id,name)).fetchone()
        remaining=max(0,int(row['ready_at'])-int(time.time())) if row else 0
        cost=0 if self.character.class_type=='physical' else 110
        command=ascii_fold(raw)
        if command not in ('uzyj','uzycie','rzuc','cast'):
            await self.send(f'MISTRZOSTWO KLASY: {name} — {skill}. Wymaga poziomu 150, koszt {cost} MP, '
                            f'odnowienie 45 s. Użycie: mistrzostwo uzyj. '
                            f'{"Pozostało "+str(remaining)+" s." if remaining else "Gotowe."}')
            return
        if level<150:
            await self.send(f'{skill} odblokowuje się od poziomu 150.');return
        if remaining:
            await self.send(f'{skill} odnowi się za {remaining} sekund.');return
        if self.current_mana<cost:
            await self.send(f'{skill}: potrzebujesz {cost} MP.');return
        mob=None
        if kind=='strike':
            mob=self.server.world.mobs.get(self.combat_mob_key) if self.combat_mob_key else None
            if not mob or not mob.alive or mob.hp<=0 or mob.room_id!=self.character.room_id:
                await self.send(f'{skill}: musisz najpierw walczyć z przeciwnikiem.');return
        if kind=='heal' and self.current_hp>=self.max_hp():
            await self.send(f'{skill}: masz pełne HP, czar nie zużywa many.');return
        if kind=='strike':
            power=max(1,int(self.spell_power() if self.character.class_type!='physical' else self.physical_power()))
            amount=max(1,int(power*.62))
            amount=await self.apply_boss_defense(mob,amount)
            amount=self.v0210_adjust_player_damage(amount)
            from world.machine_expansion import v0314_adjust_damage_vs_template
            amount,_=v0314_adjust_damage_vs_template(MOB_TEMPLATES.get(mob.template_id,{}),amount,
                                                     'magic' if cost else 'physical',skill)
            amount=min(max(0,int(mob.hp)),max(1,int(amount)))
            if amount<=0:
                await self.send('Cel obronił się. Nie pobrano many ani czasu odnowienia.');return
            mob.hp-=amount
            message=f'{skill}: {amount} obrażeń. Przeciwnik: {max(0,mob.hp)} HP.'
        elif kind=='guard':
            guard=max(1,int(self.max_hp()*.08))
            self.skill_guard=max(int(getattr(self,'skill_guard',0) or 0),guard)
            message=f'{skill}: tarcza obronna {guard}.'
        else:
            from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
            if superboss_healing_blocked_v11179(self):
                await self.send('Nullify Healing blokuje tę zdolność.');return
            amount=max(1,int(self.max_hp()*.16))
            healed=min(self.max_hp()-self.current_hp,amount)
            self.current_hp+=healed
            message=f'{skill}: odnowiono {healed} HP.'
        self.current_mana-=cost
        conn.execute('INSERT INTO mastery_cooldown_v1800(account_id,class_name,ready_at) VALUES(?,?,?) '
                     'ON CONFLICT(account_id,class_name) DO UPDATE SET ready_at=excluded.ready_at',
                     (self.account_id,name,int(time.time())+45))
        conn.commit()
        await self.send(message+(f' Mana -{cost} MP.' if cost else ''))
        if mob and mob.hp<=0:await self.mob_defeated(mob)
