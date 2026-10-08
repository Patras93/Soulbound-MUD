# -*- coding: utf-8 -*-
"""Hire permanent NPC mercenaries independently of UOSS helpers."""
from core.bootstrap_economy_professions import currency_price_text
import time
from systems.mercenary_taverns import MERCENARIES, COOLDOWN, mercenary_role, tavern_here, price_silver, pick_next_contract, mercenary_owner_power_v1213, mercenary_damage_cap_ratio_v12212, mercenary_owner_full_power_v12213, mercenary_skill_lines_v12211
from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
from world.machine_expansion import v0314_adjust_damage_vs_template
from data.mobs import MOB_TEMPLATES
from systems.mercenary_growth_v1220 import (
    mercenary_owner_level_v1228, mercenary_attack_multiplier, mercenary_unlocked, mercenary_tactic,
)

class SessionMercenaryTavernsMixin:
    def nearby_mercenaries_v1226(self):
        """Visible followers share their owner's room; they are not spawnable mobs.

        Read the persisted contracts instead of copying NPCs into the world,
        so a hire survives reconnects and never duplicates after a restart.
        """
        if not self.character:
            return []
        room_id = self.character.room_id
        visible = []
        for owner in tuple(self.server.sessions):
            if (getattr(owner, "closed", False) or
                    not getattr(owner, "character", None) or
                    owner.character.room_id != room_id or
                    getattr(owner, "account_id", None) is None):
                continue
            for row in self.server.db.mercenary_contracts(owner.account_id):
                role = row["role"]
                if role in MERCENARIES:
                    visible.append((owner, role, MERCENARIES[role]))
        return visible

    def visible_mercenary_for_look_v1226(self, query):
        wanted = self.normalize_description_query(query)
        if not wanted:
            return None
        choices = []
        for owner, role, spec in self.nearby_mercenaries_v1226():
            names = (spec["name"], spec["role"])
            if wanted in {self.normalize_description_query(name) for name in names}:
                choices.append((owner, role, spec))
        return choices[0] if len(choices) == 1 else None

    async def handle_hunters_v1225(self, raw=""):
        """NVDA-first bounty board in Soul City; no changes to legacy bounties."""
        if not self.character:
            return
        offers = {
            'zwykle': ('goblin', 6, 15000, 3600, 'Zwykłe polowanie'),
            'elitarne': ('v028_region_01_elite', 4, 140000, 4*3600, 'Elitarne polowanie'),
            'boss': ('goblin_warchief', 1, 2000000, 24*3600, 'Polowanie na bossa'),
        }
        text = str(raw or '').strip().lower()
        parts=text.split()
        action=parts[0] if parts else 'lista'
        tier=parts[1] if len(parts)>1 else ''
        aliases={'zwykłe':'zwykle','zwykly':'zwykle','elita':'elitarne','elitarne':'elitarne','bossy':'boss','bossowie':'boss','bos':'boss','bosa':'boss'}
        tier=aliases.get(tier,tier)
        now=int(time.time())
        if action in ('', 'lista','list','pomoc','help'):
            await self.send('TABLICA ŁOWCÓW NAGRÓD. Zlecenia odnawiają się osobno dla każdego gracza.')
            for key,(mob_id,needed,reward,cooldown,label) in offers.items():
                entry=self.server.db.hunter_state_v1225(self.account_id,key)
                state=(f"{entry['progress']}/{entry['needed']}; {entry['state']}" if entry else 'dostępne')
                target = 'gobliny i odmiany' if key == 'zwykle' else 'dowolni elitarni' if key == 'elitarne' else 'dowolny boss'
                await self.send(f"{key}: {label}, cel {target} x{needed}. Nagroda {currency_price_text(reward)}. Odnowienie {cooldown//3600} godz. Status: {state}.")
            await self.send('W sali: lowcy przyjmij zwykle, lowcy przyjmij elitarne, lowcy przyjmij boss; lowcy status; lowcy odbierz zwykle.')
            return
        if action in ('status','stan'):
            for key,(mob_id,needed,reward,cooldown,label) in offers.items():
                row=self.server.db.hunter_state_v1225(self.account_id,key)
                if not row: await self.send(f'{key}: nieprzyjęte.');continue
                remaining=max(0,int(row['ready_after'])-now)
                await self.send(f"{key}: {row['progress']}/{row['needed']}, {row['state']}" + (f", odnowienie za {remaining//60} minut" if remaining else '') + '.')
            return
        if tier not in offers:
            await self.send('Podaj kategorię: zwykle, elitarne lub boss.');return
        mob_id,needed,reward,cooldown,label=offers[tier]
        if action not in ('przyjmij','rozpocznij','odbierz','nagroda'):
            await self.send('Użycie: lowcy przyjmij <zwykle|elitarne|boss>, lowcy status, lowcy odbierz <kategoria>.');return
        if self.character.room_id!='soul_hunter_board_v1225':
            await self.send('Odbieranie i przyjmowanie zleceń tylko w Sali Łowców Nagród: Plac Dusz, północny wschód, wschód.');return
        if action in ('przyjmij','rozpocznij'):
            party_key = self.server.party_key_for_account(self.account_id)
            recipients = [self]
            if party_key == self.account_id:
                recipients = list(self.server.party_sessions(self.account_id)) or [self]
            accepted = []
            rejected = []
            seen = set()
            for member in recipients:
                if member.account_id in seen or not getattr(member, 'character', None):
                    continue
                seen.add(member.account_id)
                result = self.server.db.hunter_accept_v1225(member.account_id, tier, mob_id, needed, reward, now)
                if result == 'ok':
                    accepted.append(member)
                else:
                    rejected.append((member, result))
            for member in accepted:
                await member.send(f'Przyjęto {label}: ' +
                    ('pokonaj 6 goblinów i ich odmian.' if tier == 'zwykle' else
                     'pokonaj 4 elitarne potwory.' if tier == 'elitarne' else
                     'pokonaj dowolnego prawdziwego bossa.') +
                    ' Postęp: lowcy status.')
            if rejected:
                for member, reason in rejected:
                    await member.send({'active':'Zlecenie już aktywne lub gotowe. Sprawdź lowcy status.',
                                       'cooldown':'Zlecenie jeszcze się odnawia. Sprawdź lowcy status.'}.get(reason, 'Nie udało się przyjąć zlecenia.'))
            if len(recipients) > 1:
                await self.send(f'Tablica Łowców: przyjęło {len(accepted)} z {len(seen)} graczy online w drużynie. Każdy odbiera własną nagrodę.')
            return
        result=self.server.db.hunter_claim_v1225(self.account_id,tier,now,cooldown)
        if result>0:
            await self.send(f'Zlecenie rozliczone. Nagroda {currency_price_text(result)} wpłynęła do Banku Dusz. Następne za {cooldown//3600} godz.')
        elif result==-1:
            await self.send('Przekroczony limit salda banku. Zwolnij miejsce przed odbiorem nagrody.')
        else:
            row = self.server.db.hunter_state_v1225(self.account_id, tier)
            if not row:
                await self.send(f'Nie masz przyjętego zlecenia {tier}. Wpisz lowcy przyjmij {tier}.')
            elif row['state'] == 'active':
                await self.send(f'Zlecenie {tier}: postęp {row["progress"]} z {row["needed"]}. Najpierw pokonaj wymaganych przeciwników.')
            else:
                await self.send(f'Nagroda za {tier} została już odebrana. Wpisz lowcy status, aby sprawdzić odnowienie.')

    async def handle_mercenaries_v1170(self, args=""):
        if not self.character:
            return
        text = str(args or "").strip()
        parts = text.split(maxsplit=1)
        action = parts[0].lower() if parts else "lista"
        name = parts[1].strip() if len(parts)>1 else ""
        if action in ("skille", "skills", "umiejetnosci", "umiejętności", "zdolnosci", "zdolności"):
            # Read-only: mercenaries decide which abilities to use themselves.
            role = mercenary_role(name) if name else None
            if name and role is None:
                await self.send("Nieznany najemnik. Wpisz najemnik skille, aby poznać pełną listę.")
                return
            if not name:
                await self.send("UMIEJĘTNOŚCI NAJEMNIKÓW — działają automatycznie; nie musisz nimi sterować.")
                for key, spec in MERCENARIES.items():
                    extras = []
                    if key in ("kaplan", "druid", "paladyn"):
                        extras.append("leczenie")
                    if key in ("wojownik", "paladyn", "straznik", "psionik", "inzynier"):
                        extras.append("osłona")
                    label = ", ".join(extras) if extras else "atak"
                    await self.send(f"{spec['name']} ({spec['role']}): {spec['ability']}; dodatkowo: {label}.")
                await self.send("Szczegóły: najemnik skille <imię>, np. najemnik skille Seren. "
                                "Działa również przed zatrudnieniem.")
                return
            for line in mercenary_skill_lines_v12211(role):
                await self.send(line)
            return
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
            level = mercenary_owner_level_v1228(self.character)
            for key in selected:
                progress = self.server.db.mercenary_progress_v1220(self.account_id, key)
                await self.send(f"{MERCENARIES[key]['name']}: poziom {level} (równy twojemu, bez osobnego EXP), "
                                f"taktyka {mercenary_tactic(progress['specialization'])}. Umiejętność: {MERCENARIES[key]['ability']}.")
            return
        if action in ("specjalizacja", "spec", "szkol"):
            await self.send("Nie ma już specjalizacji ani szkolenia najemników. Wpisz: najemnik taktyka <imię> <automatyczna|szturm|obrona|wsparcie>.")
            return
        if action in ("taktyka", "tryb", "tactic"):
            choices = name.rsplit(maxsplit=1)
            if len(choices) != 2:
                await self.send("Użycie: najemnik taktyka <imię> <automatyczna|szturm|obrona|wsparcie>. Zmienisz ją zawsze, za darmo.")
                return
            role = mercenary_role(choices[0])
            if not role:
                await self.send("Nieznany najemnik.")
                return
            tactic = choices[1].lower()
            result = self.server.db.mercenary_set_tactic_v1229(self.account_id, role, tactic)
            messages = {
                "ok": f"{MERCENARIES[role]['name']}: ustawiono taktykę {tactic}.",
                "not_hired": "Ten najemnik nie jest zatrudniony.",
                "unknown": "Taktyki: automatyczna, szturm, obrona, wsparcie.",
            }
            await self.send(messages.get(result, "Nie udało się zmienić taktyki."))
            return
        if action in ("status", "stan", "moje"):
            active = self.server.db.mercenary_contracts(self.account_id)
            if not active:
                await self.send("Nie masz wynajętych najemników. Najemnicy: 0/3.")
                return
            level = mercenary_owner_level_v1228(self.character)
            await self.send(f"Każdy najemnik ma twój aktualny poziom {level}, bez osobnego EXP. Obrażenia: pełna silniejsza moc właściciela i jego EQ; bonus za poziom rośnie bez limitu. Każdy najemnik działa samodzielnie we własnym rytmie. Taktyki: najemnik taktyka <imię> <automatyczna|szturm|obrona|wsparcie>.")
            for row in active:
                role = row["role"]
                if role in MERCENARIES:
                    progress = self.server.db.mercenary_progress_v1220(self.account_id, role)
                    await self.send(f"{MERCENARIES[role]['name']} ({MERCENARIES[role]['role']}): zatrudniony na stałe, poziom {level}, taktyka {mercenary_tactic(progress['specialization'])}.")
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
                reasons={"duplicate":"Ten najemnik już jest zatrudniony.","full":"Możesz mieć jednocześnie najwyżej 3 najemników.","money":f"Brakuje złota. Koszt po rabacie: {currency_price_text(price)}."}
                await self.send(reasons.get(result,"Nie można zawrzeć kontraktu."))
                return
            self.server.db.apply_shared_wallet_to_character(self.character)
            spec = MERCENARIES[role]
            await self.send(f"{spec['name']} ({spec['role']}) dołącza na stałe za jednorazową opłatę {currency_price_text(price)}. Możesz odesłać najemnika komendą najemnik odeslij {spec['name']}. EXP i łupy zostają u graczy.")
            return
        if action not in ("lista", "list", "", "oferta"):
            await self.send("Komendy: najemnicy; najemnik skille [imię] (podgląd); najemnik wynajmij <imię>; najemnik status; najemnik taktyka <imię> <automatyczna|szturm|obrona|wsparcie>; najemnik odeslij <imię|wszyscy>. Najemnicy sami używają swoich umiejętności.")
            return
        if not tavern_here(self.character.room_id):
            await self.send("Ofertę i wynajem znajdziesz w miejskich tawernach. Status sprawdzisz wszędzie: najemnik status.")
            return
        level = max(1, int(getattr(self.character, "character_level", 1) or 1))
        await self.send(f"TAWERNA NAJEMNIKÓW: do 3 najemników na stałe, jednorazowy koszt, osobny pomocnik UOSS. Poziom każdego najemnika to twój poziom {level}, bez osobnego EXP; moc rośnie bez sztucznego limitu wraz z poziomem, silniejszym atakiem fizycznym lub magicznym i pełnym EQ. Każdy walczy samodzielnie.")
        for role, spec in MERCENARIES.items():
            await self.send(f"{spec['name']} — {spec['role']}; {currency_price_text(price_silver(self.character,role))} po rabacie Charyzmy. Wpisz: najemnik wynajmij {spec['name']}.")

    async def mercenary_combat_turn_v1170(self, mob):
        from systems.encounter_brain_v1230 import mercenary_combo_v1230
        if not self.character or self.current_hp <= 0 or not mob or not mob.alive or mob.room_id != self.character.room_id:
            return
        now = time.time()
        contracts = self.server.db.mercenary_contracts(self.account_id, now)
        # Every hired companion takes its own action. Previously a single shared
        # five-second timer allowed only ONE of three companions to act at all.
        roles = [row["role"] for row in contracts if row["role"] in MERCENARIES
                 and (float(row["expires_at"]) <= 0 or float(row["expires_at"]) > now)]
        if not roles:
            return
        next_actions = getattr(self, "_mercenary_next_actions_v12214", None)
        if not isinstance(next_actions, dict):
            next_actions = {}
        # Limit state to existing contracts only (no DB writes; no stale timers).
        next_actions = {role: next_actions.get(role, 0.0) for role in roles}
        self._mercenary_next_actions_v12214 = next_actions
        for role in roles:
            if not mob.alive or mob.hp <= 0 or mob.room_id != self.character.room_id:
                break
            if now < next_actions[role]:
                continue
            next_actions[role] = now + COOLDOWN
            spec = MERCENARIES[role]
            name = spec["name"]
            party = self.server.party_sessions(self.account_id, same_room=self.character.room_id) or [self]
            living = [p for p in party if getattr(p,"current_hp",0)>0 and getattr(p,"character",None)]
            if not living:
                return
            weakest = min(living,key=lambda p: p.current_hp/max(1,p.max_hp()))
            progress = self.server.db.mercenary_progress_v1220(self.account_id, role)
            merc_level = mercenary_owner_level_v1228(self.character)
            tactic = mercenary_tactic(progress["specialization"])
            message = None
            experience_action = False
            # Healers adapt to boss pressure, then keep fighting when healing
            # is prohibited; no wasted spell action or manual micro-management.
            target_template = MOB_TEMPLATES.get(mob.template_id, {})
            major_threat = bool(target_template.get('boss') or target_template.get('world_boss') or
                                target_template.get('uoss_superboss') or target_template.get('crypt_boss') or
                                target_template.get('mythic_crypt_boss'))
            heal_threshold = (.89 if major_threat else (.78 if role != 'druid' else .68))
            if role in ("kaplan", "paladyn", "druid") and (
                    weakest.current_hp < weakest.max_hp() * heal_threshold and
                    not superboss_healing_blocked_v11179(weakest)):
                heal=min(max(0,weakest.max_hp()-weakest.current_hp), max(1,int(weakest.max_hp()*(.18 if role=="kaplan" else (.13 if role=="druid" else .11)))))
                weakest.current_hp+=heal
                message=f"{name} leczy {weakest.character.name}: +{heal} HP."
                experience_action = True
            elif (role in ("wojownik", "paladyn", "straznik", "psionik", "inzynier")
                  and weakest.skill_guard <= 0 and
                  weakest.current_hp < weakest.max_hp() * (.90 if major_threat else .75)):
                guard=max(1,int(weakest.max_hp()*({"wojownik":.09, "paladyn":.06, "straznik":.13, "psionik":.08, "inzynier":.10}[role])))
                weakest.skill_guard += guard
                message=f"{name} osłania {weakest.character.name}: następny cios osłabiony o maksymalnie {guard}."
                experience_action = True
            defeated_by_mercenary = False
            if message is None and mob.hp > 0:
                magic = spec["attack_type"] == "magic"
                # 100% real equipped offense: effective STR/INT, flat item power,
                # equipment/rune damage-percent properties and active set bonuses.
                # Use the owner's strongest channel even for cross-class hiring.
                physical_eq = self.equipment_damage_multiplier("physical") if callable(getattr(self, "equipment_damage_multiplier", None)) else 1.0
                magic_eq = self.equipment_damage_multiplier("magic") if callable(getattr(self, "equipment_damage_multiplier", None)) else 1.0
                set_eq = self.total_set_damage_multiplier() if callable(getattr(self, "total_set_damage_multiplier", None)) else 1.0
                power_base = mercenary_owner_full_power_v12213(
                    self.physical_power(), self.spell_power(), physical_eq, magic_eq, set_eq
                )
                # Every hire starts at FULL owner power (never an arbitrary 42%).
                # Above-1.0 class multipliers still distinguish offensive roles.
                power = max(1, int(power_base * max(1.0, float(spec["power"]))
                                   * mercenary_attack_multiplier(merc_level, tactic)
                                   * mercenary_combo_v1230(role, roles, MERCENARIES)))
                template = MOB_TEMPLATES.get(mob.template_id, {})
                power = await self.apply_boss_defense(mob, power)
                power, _ = v0314_adjust_damage_vs_template(template, power, "magic" if magic else "physical", spec["role"])
                # No percent-of-enemy-HP cap. Clamp ONLY to real remaining HP and
                # finish through the existing kill pipeline, including party credit.
                damage = min(max(0, int(mob.hp)), max(1, int(power)))
                mob.hp -= damage
                technique = spec["ability"]
                message = f"{name} używa {technique}: {damage} obrażeń. {max(0, mob.hp)} HP przeciwnika."
                experience_action = True
                defeated_by_mercenary = mob.hp <= 0
            if message:
                # Tactics are freely selectable from level 1. Every mercenary keeps
                # their own role ability; this small extra effect is player-configured.
                if experience_action:
                    if tactic == "obrona":
                        guard = max(1, int(weakest.max_hp() * .05))
                        weakest.skill_guard += guard
                        message += f" Dodatkowa osłona: {guard}."
                    elif tactic == "wsparcie" and weakest.current_hp < weakest.max_hp():
                        heal = min(max(0, weakest.max_hp()-weakest.current_hp), max(1, int(weakest.max_hp() * .04)))
                        if heal and not superboss_healing_blocked_v11179(weakest):
                            weakest.current_hp += heal
                            message += f" Dodatkowe leczenie: +{heal} HP."
                # The owner is excluded from party_combat_broadcast by design.
                # Tell the owner directly, even in concise NVDA combat mode;
                # share the same action with party members in the same room.
                await self.send_combat(message, detail="essential")
                await self.server.party_combat_broadcast(self, message, detail="essential")
                if defeated_by_mercenary:
                    await self.mob_defeated(mob)
                # v1.22.8: no separate mercenary leveling or per-action SQLite writes.
                # The hire follows the owner's level immediately, even after reconnect.
