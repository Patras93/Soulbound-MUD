# -*- coding: utf-8 -*-
"""Hire permanent NPC mercenaries independently of UOSS helpers."""
import time
from systems.mercenary_taverns import MERCENARIES, COOLDOWN, mercenary_role, tavern_here, price_silver, pick_next_contract, mercenary_owner_power_v1213
from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
from world.machine_expansion import v0314_adjust_damage_vs_template
from data.mobs import MOB_TEMPLATES
from systems.mercenary_growth_v1220 import (SPECIALIZATIONS, mercenary_level, mercenary_xp_for_level,
    mercenary_action_xp, mercenary_attack_multiplier, mercenary_unlocked)

class SessionMercenaryTavernsMixin:
    async def handle_mercenaries_v1170(self, args=""):
        if not self.character:
            return
        text = str(args or "").strip()
        parts = text.split(maxsplit=1)
        action = parts[0].lower() if parts else "lista"
        name = parts[1].strip() if len(parts)>1 else ""
        if action in ("rozwoj", "rozwój", "poziom", "exp", "talenty"):
            active = self.server.db.mercenary_contracts(self.account_id)
            role = mercenary_role(name) if name else None
            selected = [row["role"] for row in active if row["role"] in MERCENARIES and (not role or row["role"] == role)]
            if name and not role:
                await self.send("Nieznany najemnik. Wpisz najemnik rozwoj bez imienia.")
                return
            if not selected:
                await self.send("Nie masz takiego zatrudnionego najemnika.")
                return
            for key in selected:
                progress = self.server.db.mercenary_progress_v1220(self.account_id, key)
                level = mercenary_level(progress["xp"])
                next_xp = mercenary_xp_for_level(level + 1)
                await self.send(f"{MERCENARIES[key]['name']}: poziom {level}, EXP {progress['xp']} / {next_xp}, "
                                f"specjalizacja {progress['specialization'] or 'nie wybrana'}, "
                                f"technika: {mercenary_unlocked(level, progress['specialization'])}.")
            return
        if action in ("specjalizacja", "spec", "szkol"):
            choices = name.rsplit(maxsplit=1)
            if len(choices) != 2:
                await self.send("Użycie: najemnik specjalizacja <imię> <szturm|obrona|wsparcie>. Dostępne od poziomu 10.")
                return
            role = mercenary_role(choices[0])
            if not role:
                await self.send("Nieznany najemnik.")
                return
            outcome = self.server.db.mercenary_specialize_v1220(self.account_id, role, choices[1].lower())
            messages = {"ok":f"{MERCENARIES[role]['name']} wybiera specjalizację: {choices[1].lower()}.",
                "level":"Wymagany poziom najemnika: 10.", "already":"Ten najemnik wybrał już specjalizację.",
                "not_hired":"Najemnik nie jest zatrudniony.", "unknown":"Specjalizacje: szturm, obrona, wsparcie."}
            await self.send(messages[outcome])
            return
        if action in ("status", "stan", "moje"):
            active = self.server.db.mercenary_contracts(self.account_id)
            if not active:
                await self.send("Nie masz wynajętych najemników. Najemnicy: 0/3.")
                return
            level = max(1, int(getattr(self.character, "character_level", 1) or 1))
            await self.send(f"Najemnicy rozwijają własne EXP i poziom za walkę, a moc bazowa zależy od silniejszego ataku właściciela wraz z EQ. Twój poziom: {level}. Najemnik rozwoj — szczegóły.")
            for row in active:
                role = row["role"]
                if role in MERCENARIES:
                    progress = self.server.db.mercenary_progress_v1220(self.account_id, role)
                    await self.send(f"{MERCENARIES[role]['name']} ({MERCENARIES[role]['role']}): zatrudniony na stałe, poziom {mercenary_level(progress['xp'])}.")
            await self.send(f"Najemnicy: {len(active)}/3. Pomocnicy UOSS mają osobne miejsce.")
            return
        if action in ("zwolnij", "usun", "odeślij", "odeslij"):
            role = mercenary_role(name)
            if name.casefold() in ("wszyscy", "all"):
                count = self.server.db.dismiss_mercenary(self.account_id)
                await self.send(f"Odesłano najemników: {count}. Jednorazowa opłata nie jest zwracana.")
            elif role:
                count = self.server.db.dismiss_mercenary(self.account_id, role)
                await self.send(f"{MERCENARIES[role]['name']} wraca do tawerny." if count else "Ten najemnik nie jest zatrudniony.")
            else:
                await self.send("Użycie: najemnik odeslij <imię|wszyscy> (działa też zwolnij).")
            return
        if action in ("wynajmij", "hire"):
            if not tavern_here(self.character.room_id):
                await self.send("Najemników zatrudnisz tylko w karczmie. Odwiedź jedną z miejskich tawern.")
                return
            role = mercenary_role(name)
            if not role:
                await self.send("Nie rozpoznaję najemnika. Wpisz najemnicy, aby poznać listę.")
                return
            price = price_silver(self.character, role)
            result = self.server.db.hire_mercenary(self.account_id, role, price)
            if result != "ok":
                reasons={"duplicate":"Ten najemnik już jest zatrudniony.","full":"Możesz mieć jednocześnie najwyżej 3 najemników.","money":f"Brakuje złota. Koszt po rabacie: {price} srebra."}
                await self.send(reasons.get(result,"Nie można zawrzeć kontraktu."))
                return
            self.server.db.apply_shared_wallet_to_character(self.character)
            spec = MERCENARIES[role]
            await self.send(f"{spec['name']} ({spec['role']}) dołącza na stałe za jednorazową opłatę {price} srebra. Możesz odesłać najemnika komendą najemnik odeslij {spec['name']}. EXP i łupy zostają u graczy.")
            return
        if action not in ("lista", "list", "", "oferta"):
            await self.send("Komendy: najemnicy; najemnik wynajmij <imię>; najemnik status; najemnik odeslij <imię|wszyscy>.")
            return
        if not tavern_here(self.character.room_id):
            await self.send("Ofertę i wynajem znajdziesz w miejskich tawernach. Status sprawdzisz wszędzie: najemnik status.")
            return
        level = max(1, int(getattr(self.character, "character_level", 1) or 1))
        await self.send(f"TAWERNA NAJEMNIKÓW: do 3 najemników na stałe, jednorazowy koszt, osobny pomocnik UOSS. Moc skaluje się z silniejszym atakiem właściciela (fizycznym lub magicznym) i jego EQ (twój poziom: {level}); najemnicy zdobywają EXP podczas walki.")
        for role, spec in MERCENARIES.items():
            await self.send(f"{spec['name']} — {spec['role']}; {price_silver(self.character,role)} srebra po rabacie Charyzmy. Wpisz: najemnik wynajmij {spec['name']}.")

    async def mercenary_combat_turn_v1170(self, mob):
        if not self.character or self.current_hp <= 0 or not mob or not mob.alive or mob.room_id != self.character.room_id:
            return
        now = time.time()
        if now < float(getattr(self,"_mercenary_next_action_v1170", 0.0)):
            return
        contracts = self.server.db.mercenary_contracts(self.account_id, now)
        role = pick_next_contract(contracts, getattr(self,"_mercenary_last_role_v1170",None), now)
        if role is None:
            return
        self._mercenary_next_action_v1170 = now + COOLDOWN
        self._mercenary_last_role_v1170 = role
        spec = MERCENARIES[role]
        name = spec["name"]
        party = self.server.party_sessions(self.account_id, same_room=self.character.room_id) or [self]
        living = [p for p in party if getattr(p,"current_hp",0)>0 and getattr(p,"character",None)]
        if not living:
            return
        weakest = min(living,key=lambda p: p.current_hp/max(1,p.max_hp()))
        progress = self.server.db.mercenary_progress_v1220(self.account_id, role)
        merc_level = mercenary_level(progress["xp"])
        specialization = progress["specialization"]
        message = None
        experience_action = False
        if role in ("kaplan", "paladyn", "druid") and weakest.current_hp < weakest.max_hp()*(.70 if role != "druid" else .60):
            if superboss_healing_blocked_v11179(weakest):
                message = f"{name} próbuje leczyć, ale blokada leczenia nie pozwala."
            else:
                heal=min(max(0,weakest.max_hp()-weakest.current_hp), max(1,int(weakest.max_hp()*(.18 if role=="kaplan" else (.13 if role=="druid" else .11)))))
                weakest.current_hp+=heal
                message=f"{name} leczy {weakest.character.name}: +{heal} HP."
                experience_action = True
        elif role in ("wojownik", "paladyn", "straznik", "psionik", "inzynier") and (weakest.skill_guard <= 0):
            guard=max(1,int(weakest.max_hp()*({"wojownik":.09, "paladyn":.06, "straznik":.13, "psionik":.08, "inzynier":.10}[role])))
            weakest.skill_guard += guard
            message=f"{name} osłania {weakest.character.name}: następny cios osłabiony o maksymalnie {guard}."
            experience_action = True
        if message is None and mob.hp > 1:
            # Bounded support that cannot independently kill bosses or multiply XP.
            magic = spec["attack_type"] == "magic"
            # v1.21.3: use the owner's strongest effective attack channel for
            # *every* hired class. Attack type still controls enemy defenses.
            power_base = mercenary_owner_power_v1213(
                self.physical_power(), self.spell_power()
            )
            power = max(1,int(power_base*.20*spec["power"]*mercenary_attack_multiplier(merc_level,specialization)))
            template = MOB_TEMPLATES.get(mob.template_id, {})
            power = await self.apply_boss_defense(mob, power)
            power, _ = v0314_adjust_damage_vs_template(template, power, "magic" if magic else "physical", spec["role"])
            max_hp=max(1,int(self.mob_effective_max_hp_v11330(mob)))
            damage=min(mob.hp-1, max(1,min(int(power),max(1,int(max_hp*.015)))))
            mob.hp-=damage
            technique = spec["ability"]
            if specialization == "szturm" and merc_level >= 50:
                technique = f"Legendarna seria: {technique}"
            elif specialization == "szturm" and merc_level >= 25:
                technique = f"Mistrzowski atak: {technique}"
            message=f"{name} używa {technique}: {damage} obrażeń. {mob.hp} HP przeciwnika."
            experience_action = True
        if message:
            # Specializations unlock only after level 10. Support effects are
            # bounded by the receiver's HP/guard and do not alter kill rewards.
            if experience_action and merc_level >= 10:
                if specialization == "obrona":
                    # Increase an already raised shield modestly; do not create
                    # a second full shield on top of an active one.
                    percent = .03 if merc_level < 25 else .05 if merc_level < 50 else .07
                    guard = max(1, int(weakest.max_hp() * percent))
                    weakest.skill_guard += guard
                    message += f" Mistrzowska osłona: {guard}."
                elif specialization == "wsparcie" and weakest.current_hp < weakest.max_hp():
                    heal = min(max(0, weakest.max_hp()-weakest.current_hp), max(1, int(weakest.max_hp() * (.025 if merc_level < 25 else .04 if merc_level < 50 else .06))))
                    if heal and not superboss_healing_blocked_v11179(weakest):
                        weakest.current_hp += heal
                        message += f" Pomocne uzdrowienie: +{heal} HP."
            await self.server.party_combat_broadcast(self, message, detail="normal")
            if experience_action:
                template = MOB_TEMPLATES.get(mob.template_id, {})
                foe_level = template.get("level", template.get("generator_level", 1)) or 1
                xp = mercenary_action_xp(getattr(self.character, "character_level", 1), foe_level, bool(template.get("boss") or template.get("v1200_boss")))
                updated = self.server.db.mercenary_gain_xp_v1220(self.account_id,role,xp)
                new_level = mercenary_level(updated["xp"])
                if new_level > merc_level:
                    await self.send(f"AWANS NAJEMNIKA: {name}, poziom {new_level}. {mercenary_unlocked(new_level,updated['specialization'])}.")
