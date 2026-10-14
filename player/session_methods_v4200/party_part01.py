# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
def clean_party_player_argument(self, value, relation=None):
        """Usuń naturalne końcówki typu `do drużyny` / `z drużyny`."""
        raw = str(value or "").strip()
        if not raw:
            return ""
        parts = raw.split()
        normalized = [self.normalize_description_query(part) for part in parts]
        endings = []
        if relation == "to":
            endings = [("do", "druzyny"), ("do", "party")]
        elif relation == "from":
            endings = [("z", "druzyny"), ("z", "party")]
        else:
            endings = [
                ("do", "druzyny"), ("do", "party"),
                ("z", "druzyny"), ("z", "party"),
            ]
        if len(parts) >= 2 and tuple(normalized[-2:]) in endings:
            raw = " ".join(parts[:-2]).strip()
        return raw


def auto_priest_heal_option(self, injured_members):
        if getattr(self, "_party_auto_heal_busy", False):
            return None
        if not self.character or self.current_hp <= 0 or "Kapłan" not in self.active_class_names():
            return None
        injured = [
            member for member in injured_members
            if member and not member.closed and member.character and member.current_hp > 0
            and member.current_hp < member.max_hp()
        ]
        if not injured:
            return None
        known = self.server.db.learned_skill_ids(self.account_id)
        now = time.time()
        options = []
        for skill in CLASS_SKILLS.get("Kapłan", []):
            if skill.get("kind") not in ("heal", "group_heal"):
                continue
            if skill.get("id") not in known or not self.skill_mastery_unlocked(skill):
                continue
            if self.skill_cooldown_ready_at_v0364(skill) > now:
                continue
            mana_cost = int(skill.get("mana", 0) or 0)
            if mana_cost > self.current_mana:
                continue
            progress = self.server.db.skill_progress(self.account_id, skill["id"])
            if not progress:
                continue
            skill_level = int(progress["level"])
            skill_power = skill_power_multiplier(skill_level)
            if skill.get("kind") == "group_heal":
                heal_pct = min(
                    0.45,
                    float(skill.get("heal_pct", 0.20)) * skill_power
                    * self.character.racial_healing_multiplier()
                    * self.character.class_healing_multiplier()
                    * party_synergy_healing_multiplier_v11338(self),
                )
                heal_pct = min(0.60, heal_pct * self.skill_buff_multiplier())
                expected = 0
                for target in injured:
                    amount = max(1, int(target.max_hp() * heal_pct))
                    expected += min(target.max_hp() - target.current_hp, amount)
                target = min(injured, key=lambda x: (x.current_hp / max(1, x.max_hp()), x.current_hp))
            else:
                target = min(injured, key=lambda x: (x.current_hp / max(1, x.max_hp()), x.current_hp))
                heal_pct = min(
                    0.65,
                    float(skill.get("heal_pct", 0.25)) * skill_power
                    * self.character.racial_healing_multiplier()
                    * self.character.class_healing_multiplier()
                    * party_synergy_healing_multiplier_v11338(self),
                )
                heal_pct = min(0.80, heal_pct * self.skill_buff_multiplier())
                amount = max(1, int(target.max_hp() * heal_pct))
                expected = min(target.max_hp() - target.current_hp, amount)
            if expected > 0:
                options.append((expected, skill_level, int(skill.get("unlock", 1)), skill, target, heal_pct))
        if not options:
            return None
        options.sort(key=lambda row: (row[0], row[1], row[2]), reverse=True)
        expected, skill_level, _unlock, skill, target, heal_pct = options[0]
        return {
            "score": expected, "skill": skill, "target": target,
            "heal_pct": heal_pct, "skill_level": skill_level,
        }


async def perform_auto_priest_heal(self, option, injured_members):
        if not option or self._party_auto_heal_busy:
            return False
        self._party_auto_heal_busy = True
        try:
            skill = option["skill"]
            now = time.time()
            if self.skill_cooldown_ready_at_v0364(skill) > now:
                return False
            mana_cost = int(skill.get("mana", 0) or 0)
            if mana_cost > self.current_mana:
                return False
            progress = self.server.db.skill_progress(self.account_id, skill["id"])
            if not progress:
                return False
            skill_level = int(progress["level"])
            effective_cooldown = self.effective_skill_cooldown(skill, skill_level)
            self.current_mana -= mana_cost
            self.start_skill_cooldown_v0364(skill, effective_cooldown, now)

            if skill.get("kind") == "group_heal":
                recipients = [
                    member for member in self.server.party_sessions(
                        self.account_id, same_room=self.character.room_id
                    )
                    if member.character and member.current_hp > 0
                ]
                total = 0
                healed_count = 0
                for target in recipients:
                    target_max = target.max_hp()
                    amount = max(1, int(target_max * float(option["heal_pct"])))
                    before = target.current_hp
                    target.current_hp = min(target_max, target.current_hp + amount)
                    actual = target.current_hp - before
                    if actual <= 0:
                        continue
                    total += actual
                    healed_count += 1
                    if target is not self:
                        await target.send(
                            f"{self.character.name} automatycznie używa {skill['name']}. "
                            f"Odzyskujesz {actual} HP. Masz {target.current_hp} z {target_max} HP."
                        )
                await self.send(
                    f"Auto-leczenie drużyny: {skill['name']}. "
                    f"Wyleczono {healed_count} osób, łącznie {total} HP."
                )
            else:
                target = min(
                    [m for m in injured_members if m.character and not m.closed and m.current_hp > 0 and m.current_hp < m.max_hp()],
                    key=lambda x: (x.current_hp / max(1, x.max_hp()), x.current_hp),
                    default=None,
                )
                if target is None:
                    return False
                target_max = target.max_hp()
                amount = max(1, int(target_max * float(option["heal_pct"])))
                before = target.current_hp
                target.current_hp = min(target_max, target.current_hp + amount)
                actual = target.current_hp - before
                if actual <= 0:
                    return False
                if target is self:
                    await self.send(
                        f"Auto-leczenie: używasz {skill['name']} i odzyskujesz {actual} HP. "
                        f"Masz {target.current_hp} z {target_max} HP."
                    )
                else:
                    await target.send(
                        f"{self.character.name} automatycznie używa {skill['name']} na tobie. "
                        f"Odzyskujesz {actual} HP. Masz {target.current_hp} z {target_max} HP."
                    )
                    await self.send(
                        f"Auto-leczenie: {skill['name']} na {target.character.name}. "
                        f"Przywrócono {actual} HP."
                    )
            await self.grant_skill_use_xp(skill)
            return True
        finally:
            self._party_auto_heal_busy = False


async def begin_downed_v0371(self, killer, seconds=180):
        if not self.character:
            return False
        self.clear_downed_v0371(cancel_task=True)
        self.current_hp = 0
        self.current_mana = 0
        self.combat_mob_key = None
        self.skill_guard = 0
        self.skill_evade = False
        self.skill_evade_lockout_until = 0.0
        deadline = time.time() + max(1, int(seconds or 180))
        self.party_downed_until_v0371 = deadline
        self.party_downed_killer_v0371 = str(killer or "")
        self.party_downed_room_v0371 = self.character.room_id
        self.party_downed_task_v0371 = asyncio.create_task(
            self._party_downed_timeout_v0371(deadline, self.character.room_id)
        )
        seconds_left=max(1,int(deadline-time.time()))
        await self.send(
            "Jesteś POWALONY. Każdy żywy gracz, który dotrze do tej samej "
            "lokacji, może użyć: wskrzes <twoja nazwa>. "
            f"Czas na ratunek: około {seconds_left} sekund. "
            "Możesz też wpisać odrodz, aby natychmiast wrócić do "
            "Świątyni Odrodzenia."
        )
        return True


async def respawn_from_downed_v0371(self, auto=False):
        if not self.character:
            return False
        if not self.is_downed_v0371() and self.current_hp > 0:
            await self.send("Nie jesteś powalony.")
            return False
        old_room = self.character.room_id
        name = self.character.name
        self.clear_downed_v0371(cancel_task=True)
        self.server.release_all_engagements_for_session(self)
        self.combat_mob_key = None
        await self.stop_realtime_combat()
        self.character.room_id = "temple"
        self.current_hp = self.max_hp()
        self.current_mana = self.max_mana()
        self.server.db.save_character(self.character)
        await self.server.broadcast_room(
            old_room, f"Dusza {name} opuszcza pole walki i wraca do Świątyni Odrodzenia.", exclude=self
        )
        await self.server.broadcast_room(
            "temple", f"{name} odradza się w Świątyni Odrodzenia.", exclude=self
        )
        if auto:
            await self.send("Nikt nie zdążył cię wskrzesić. Twoja dusza wraca do Świątyni Odrodzenia.")
        else:
            await self.send("Rezygnujesz z oczekiwania na wskrzeszenie i odradzasz się w Świątyni Odrodzenia.")
        await self.look()
        return True


async def revive_party_member_v0371(self, name):
        # v1.13.43: ratunek jest światowy, nie tylko party. Każdy żywy
        # gracz może wskrzesić powalonego, ale musi fizycznie dotrzeć do
        # tej samej lokacji.
        if not self.character or self.current_hp <= 0:
            await self.send("Powalona postać nie może wskrzeszać innych.")
            return False
        target_name = self.clean_party_player_argument(name)
        if not target_name:
            await self.send("Użycie: wskrzes <gracz>.")
            return False
        target = self.server.find_character_session(target_name)
        if not target or not target.character or target.closed:
            await self.send("Nie ma teraz takiego gracza online.")
            return False
        if target is self:
            await self.send("Nie możesz wskrzesić własnej postaci.")
            return False
        if target.character.room_id != self.character.room_id:
            await self.send("Wskrzeszana postać musi leżeć w tej samej lokacji.")
            return False
        if not target.is_downed_v0371():
            await self.send(f"{target.character.name} nie jest teraz powalony albo czas na wskrzeszenie minął.")
            return False

        target.clear_downed_v0371(cancel_task=True)
        target.server.release_all_engagements_for_session(target)
        target.combat_mob_key = None
        await target.stop_realtime_combat()
        target.current_hp = max(1, int(target.max_hp() * 0.35))
        target.current_mana = max(0, int(target.max_mana() * 0.35))
        target.skill_guard = 0
        target.skill_evade = False
        target.skill_evade_lockout_until = 0.0
        target.server.db.save_character(target.character)

        await target.send(
            f"{self.character.name} wskrzesza cię. Wracasz do walki z {target.current_hp} HP "
            f"i {target.current_mana} many."
        )
        await self.send(
            f"Wskrzeszasz {target.character.name}. Wraca z 35 procent HP i many."
        )
        for observer in list(self.server.sessions):
            if (
                observer not in (self, target) and not observer.closed and observer.character
                and observer.character.room_id == self.character.room_id
            ):
                await observer.send(
                    f"{self.character.name} wskrzesza {target.character.name}.",
                    history_category="combat",
                )
        _revive_room_name=str(
            ROOMS.get(self.character.room_id,{}).get("name")
            or self.character.room_id
        )
        await self.server.broadcast_all(
            f"ŚWIAT: {self.character.name} wskrzesił {target.character.name} "
            f"w lokacji {_revive_room_name}.",
            history_category="system",
        )
        return True


async def respawn_downed_player_v11343(self, name):
        """Odeślij powalonego gracza do Świątyni, stojąc przy jego ciele."""
        if not self.character or self.current_hp <= 0:
            await self.send("Powalona postać nie może odradzać innych.")
            return False
        target_name=self.clean_party_player_argument(name)
        if not target_name:
            await self.send("Użycie: resp <gracz>.")
            return False
        target=self.server.find_character_session(target_name)
        if not target or not target.character or target.closed:
            await self.send("Nie ma teraz takiego gracza online.")
            return False
        if target is self:
            await self.send("Aby odrodzić własną postać, użyj: odrodz.")
            return False
        if target.character.room_id != self.character.room_id:
            await self.send(
                "Powalona postać musi leżeć w tej samej lokacji."
            )
            return False
        if not target.is_downed_v0371():
            await self.send(
                f"{target.character.name} nie jest teraz powalony albo "
                "czas na ratunek minął."
            )
            return False

        target_name_display=target.character.name
        old_room=target.character.room_id
        target.clear_downed_v0371(cancel_task=True)
        target.server.release_all_engagements_for_session(target)
        target.combat_mob_key=None
        await target.stop_realtime_combat()
        target.character.room_id="temple"
        target.current_hp=target.max_hp()
        target.current_mana=target.max_mana()
        target.server.db.save_character(target.character)

        await target.send(
            f"{self.character.name} odsyła twoją duszę do Świątyni "
            "Odrodzenia. Odradzasz się z pełnym HP i maną."
        )
        await self.send(
            f"Odsyłasz duszę {target_name_display} do Świątyni Odrodzenia."
        )
        await self.server.broadcast_room(
            old_room,
            f"Dusza {target_name_display} opuszcza pole walki.",
            exclude=target,
        )
        await self.server.broadcast_room(
            "temple",
            f"{target_name_display} odradza się w Świątyni Odrodzenia.",
            exclude=target,
        )
        await self.server.broadcast_all(
            f"ŚWIAT: {self.character.name} odesłał duszę "
            f"{target_name_display} do Świątyni Odrodzenia.",
            history_category="system",
        )
        await target.look()
        return True


async def create_party(self):
        key = self.party_key()
        if key is not None:
            await self.send("Już należysz do drużyny.")
            await self.show_party()
            return False
        self.server.parties[self.account_id] = {self.account_id}
        self.server.party_goals.pop(self.account_id, None)
        self.server.party_ready_checks.pop(self.account_id, None)
        self.server.party_routes_v1193.pop(self.account_id, None)
        await self.send(
            f"Zakładasz drużynę. Jesteś liderem. "
            f"Limit: {self.character.party_capacity()} osób."
        )
        return True


async def transfer_party_leader(self, name):
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            return False
        if key != self.account_id:
            await self.send("Tylko lider może przekazać dowodzenie drużyną.")
            return False

        target_name = self.clean_party_player_argument(name)
        if not target_name:
            await self.send("Użycie: lider <gracz>.")
            return False
        target = self.server.find_character_session(target_name)
        members = self.server.parties.get(key, set())
        if not target or target.account_id not in members:
            await self.send("Nie ma takiego członka w twojej drużynie.")
            return False
        if target is self:
            await self.send("Już jesteś liderem drużyny.")
            return False

        protector_id = self.server.party_protectors.pop(key, None)
        goal = self.server.party_goals.pop(key, None)
        route = self.server.party_routes_v1193.pop(key, None)
        ready = self.server.party_ready_checks.pop(key, None)
        self.server.parties.pop(key, None)
        self.server.parties[target.account_id] = set(members)
        if protector_id in members:
            self.server.party_protectors[target.account_id] = protector_id
        if goal:
            self.server.party_goals[target.account_id] = goal
        if route:
            self.server.party_routes_v1193[target.account_id] = route
        if ready is not None:
            self.server.party_ready_checks[target.account_id] = {
                member_id for member_id in ready if member_id in members
            }

        for invited_id, leader_id in list(self.server.party_invites.items()):
            if leader_id == key:
                self.server.party_invites[invited_id] = target.account_id

        await self.server.party_broadcast(
            target.account_id,
            f"{target.character.name} zostaje nowym liderem drużyny."
        )
        return True


async def stop_party_protection(self, announce=True):
        key = self.party_key()
        if key is None:
            # Przy wyjściu/rozłączeniu klucz może już nie istnieć; usuń po wartości.
            removed = self.server.clear_party_protector_for_account(self.account_id)
            if announce and removed:
                await self.send("Wyłączasz osłonę drużyny.")
            return bool(removed)

        if self.server.party_protectors.get(key) != self.account_id:
            if announce:
                protector = self.server.party_protector_session(self.account_id)
                if protector:
                    await self.send(
                        f"Osłonę drużyny utrzymuje {protector.character.name}."
                    )
                else:
                    await self.send("Osłona drużyny nie jest aktywna.")
            return False

        self.server.party_protectors.pop(key, None)

        # Jeżeli tank wyłącza osłonę w trwającym starciu, oddaj aggro innemu
        # członkowi drużyny walczącemu z tym samym przeciwnikiem.
        for mob in self.server.world.mobs.values():
            if not mob.alive or mob.engaged_by != self.character.name:
                continue
            candidates = [
                session for session in self.server.party_sessions(
                    self.account_id, same_room=mob.room_id
                )
                if session is not self and session.combat_mob_key == mob.key
            ]
            if candidates:
                mob.engaged_by = sorted(
                    candidates, key=lambda session: session.character.name.lower()
                )[0].character.name

        if announce:
            await self.server.party_broadcast(
                self.account_id,
                f"{self.character.name} przestaje zasłaniać drużynę."
            )
        return True


async def protect_party(self, args=""):
        mode = self.normalize_description_query(str(args or "").strip())
        if mode in ("off", "stop", "wylacz", "koniec", "0", "nie"):
            return await self.stop_party_protection(announce=True)

        key = self.party_key()
        if key is None:
            await self.send(
                "Najpierw załóż drużynę: załóż drużynę / zaloz druzyne."
            )
            return False
        if not self.character.has_active_class("Strażnik"):
            await self.send(
                "Zasłoń jest drużynową mechaniką tanka i wymaga aktywnej klasy Strażnik."
            )
            return False

        old = self.server.party_protector_session(self.account_id)
        if old is self:
            await self.send(
                "Już zasłaniasz drużynę. Użyj zasłoń off, aby wyłączyć osłonę."
            )
        else:
            self.server.party_protectors[key] = self.account_id
            await self.server.party_broadcast(
                self.account_id,
                f"{self.character.name} jako Strażnik zasłania całą drużynę i przejmuje aggro wspólnego przeciwnika."
            )

        # Jeśli drużyna już walczy z jednym wspólnym celem, wolny tank od razu
        # dołącza do tego starcia i przejmuje jego aggro.
        if not self.combat_mob_key:
            shared = []
            for session in self.server.party_sessions(
                self.account_id, same_room=self.character.room_id
            ):
                if session is self or not session.combat_mob_key:
                    continue
                mob = self.server.world.mobs.get(session.combat_mob_key)
                if mob and mob.alive and mob.room_id == self.character.room_id:
                    shared.append(mob)
            if shared:
                shared.sort(key=lambda mob: mob.key)
                await self.server.apply_party_protection(self, shared[0])
        elif self.combat_mob_key:
            mob = self.server.world.mobs.get(self.combat_mob_key)
            if mob and mob.alive and mob.room_id == self.character.room_id:
                await self.server.apply_party_protection(self, mob)
        return True

