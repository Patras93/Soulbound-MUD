# -*- coding: utf-8 -*-
"""Hire multiple independent, timed NPC mercenaries from existing inns."""
import time
from systems.mercenary_taverns import MERCENARIES, DURATION, COOLDOWN, mercenary_role, tavern_here, price_silver, pick_next_contract
from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
from world.machine_expansion import v0314_adjust_damage_vs_template
from data.mobs import MOB_TEMPLATES

class SessionMercenaryTavernsMixin:
    async def handle_mercenaries_v1170(self, args=""):
        if not self.character:
            return
        text = str(args or "").strip()
        parts = text.split(maxsplit=1)
        action = parts[0].lower() if parts else "lista"
        name = parts[1].strip() if len(parts)>1 else ""
        if action in ("status", "stan", "moje"):
            active = self.server.db.mercenary_contracts(self.account_id)
            if not active:
                await self.send("Nie masz wynajętych najemników.")
            for row in active:
                role = row["role"]
                if role in MERCENARIES:
                    remaining = max(0, int(row["expires_at"] - time.time()))
                    await self.send(f"{MERCENARIES[role]['name']} ({MERCENARIES[role]['role']}): pozostało {remaining//60} minut {remaining%60} sekund.")
            await self.send(f"Najemnicy: {len(active)}/3. Pomocnicy UOSS mają osobne miejsce.")
            return
        if action in ("zwolnij", "usun", "odeślij", "odeslij"):
            role = mercenary_role(name)
            if name in ("wszyscy", "all"):
                self.server.db.dismiss_mercenary(self.account_id)
                await self.send("Zwolniono wszystkich najemników. Opłaty za rozpoczęty kontrakt nie są zwracane.")
            elif role:
                self.server.db.dismiss_mercenary(self.account_id, role)
                await self.send(f"{MERCENARIES[role]['name']} wraca do tawerny.")
            else:
                await self.send("Użycie: najemnik zwolnij <imię> albo najemnik zwolnij wszyscy.")
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
            result = self.server.db.hire_mercenary(self.account_id, role, price, DURATION)
            if result != "ok":
                reasons={"duplicate":"Ten najemnik już jest zatrudniony.","full":"Możesz mieć jednocześnie najwyżej 3 najemników.","money":f"Brakuje złota. Koszt po rabacie: {price} srebra."}
                await self.send(reasons.get(result,"Nie można zawrzeć kontraktu."))
                return
            self.server.db.apply_shared_wallet_to_character(self.character)
            spec = MERCENARIES[role]
            await self.send(f"{spec['name']} ({spec['role']}) dołącza na 45 minut za {price} srebra. Towarzyszy ci w walce; EXP i loot zostają u graczy.")
            return
        if action not in ("lista", "list", "", "oferta"):
            await self.send("Komendy: najemnicy; najemnik wynajmij <imię>; najemnik status; najemnik zwolnij <imię|wszyscy>.")
            return
        if not tavern_here(self.character.room_id):
            await self.send("Ofertę i wynajem znajdziesz w miejskich tawernach. Status sprawdzisz wszędzie: najemnik status.")
            return
        await self.send("TAWERNA NAJEMNIKÓW: do 3 najemników na 45 minut, razem z osobnym pomocnikiem UOSS.")
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
        message = None
        if role in ("kaplan", "paladyn", "druid") and weakest.current_hp < weakest.max_hp()*(.70 if role != "druid" else .60):
            if superboss_healing_blocked_v11179(weakest):
                message = f"{name} próbuje leczyć, ale blokada leczenia nie pozwala."
            else:
                heal=min(max(0,weakest.max_hp()-weakest.current_hp), max(1,int(weakest.max_hp()*(.18 if role=="kaplan" else (.13 if role=="druid" else .11)))))
                weakest.current_hp+=heal
                message=f"{name} leczy {weakest.character.name}: +{heal} HP."
        elif role in ("wojownik", "paladyn", "straznik", "psionik", "inzynier") and (weakest.skill_guard <= 0):
            guard=max(1,int(weakest.max_hp()*({"wojownik":.09, "paladyn":.06, "straznik":.13, "psionik":.08, "inzynier":.10}[role])))
            weakest.skill_guard += guard
            message=f"{name} osłania {weakest.character.name}: następny cios osłabiony o maksymalnie {guard}."
        if message is None and mob.hp > 1:
            # Bounded support that cannot independently kill bosses or multiply XP.
            magic = spec["attack_type"] == "magic"
            power_base = self.spell_power() if magic else self.physical_power()
            power = max(1,int(power_base*.20*spec["power"]))
            template = MOB_TEMPLATES.get(mob.template_id, {})
            power = await self.apply_boss_defense(mob, power)
            power, _ = v0314_adjust_damage_vs_template(template, power, "magic" if magic else "physical", spec["role"])
            max_hp=max(1,int(self.mob_effective_max_hp_v11330(mob)))
            damage=min(mob.hp-1, max(1,min(int(power),max(1,int(max_hp*.015)))))
            mob.hp-=damage
            message=f"{name} używa {spec['ability']}: {damage} obrażeń. {mob.hp} HP przeciwnika."
        if message:
            await self.server.party_combat_broadcast(self, message, detail="normal")
