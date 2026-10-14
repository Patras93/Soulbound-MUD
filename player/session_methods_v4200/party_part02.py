# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def show_party(self):
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            await self.send(
                f"Twój limit jako przyszłego lidera: "
                f"{self.character.party_capacity()} osób."
            )
            return

        leader = self.server.session_by_account(key)
        leader_name = leader.character.name if leader else f"konto {key}"
        capacity = (
            leader.character.party_capacity()
            if leader else PARTY_BASE_CAPACITY
        )
        members = sorted(
            self.server.party_sessions(self.account_id),
            key=lambda s: s.character.name.lower(),
        )
        await self.send(
            f"DRUŻYNA. Lider: {leader_name}. "
            f"Członkowie: {len(members)} z {capacity}."
        )
        protector = self.server.party_protector_session(self.account_id)
        if protector:
            await self.send(
                f"Osłona drużyny: aktywna. Tank: {protector.character.name}."
            )
        else:
            await self.send("Osłona drużyny: wyłączona.")
        goal = str(self.server.party_goals.get(key) or "").strip()
        if goal:
            await self.send(f"Cel drużyny: {goal}.")
        else:
            await self.send("Cel drużyny: nie ustawiono.")
        if key in self.server.party_routes_v1193:
            await self.send("Trasa drużyny: druzyna trasa. Odczyt kroku: druzyna trasa krok.")
        if key in self.server.party_ready_checks:
            ready = self.server.party_ready_checks.get(key, set())
            await self.send(
                f"Gotowość: {len(ready)} z {len(members)}. "
                "Użyj: druzyna gotowi albo druzyna niegotowy."
            )
        await self.send(
            "Synergie klas w tej lokacji: "
            + party_synergy_summary_v11338(self)
            + "."
        )
        await self.send(
            "Synergy 2.0 — dostępne reakcje: "
            + party_synergy2_summary_v11339(self)
            + "."
        )
        for number, session in enumerate(members, 1):
            marker = " Lider." if session.account_id == key else ""
            downed = " Powalony — można wskrzesić." if session.is_downed_v0371() else ""
            await self.send(
                f"{number}. {session.character.name}. "
                f"Lokacja: {ROOMS[session.character.room_id]['name']}.{marker}{downed}"
            )


async def set_party_goal_v0610(self, value=""):
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            return False

        raw = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split()).strip()
        normalized = self.normalize_description_query(raw)
        if not raw:
            goal = str(self.server.party_goals.get(key) or "").strip()
            if goal:
                await self.send(f"Cel drużyny: {goal}.")
            else:
                await self.send(
                    "Cel drużyny: nie ustawiono. Lider używa: druzyna cel <tekst>."
                )
            return True

        if key != self.account_id:
            await self.send("Tylko lider może ustawić albo wyczyścić cel drużyny.")
            return False

        if normalized in ("off", "clear", "usun", "wyczysc", "brak", "none"):
            existed = bool(self.server.party_goals.pop(key, None))
            self.server.party_ready_checks.pop(key, None)
            if existed:
                await self.server.party_broadcast(
                    key,
                    f"{self.character.name} usuwa cel drużyny. Kontrola gotowości została wyzerowana.",
                )
            else:
                await self.send("Cel drużyny już nie jest ustawiony.")
            return True

        goal = raw[:160].strip()
        if not goal:
            await self.send("Użycie: druzyna cel <tekst> albo druzyna cel off.")
            return False
        self.server.party_goals[key] = goal
        self.server.party_ready_checks.pop(key, None)
        await self.server.party_broadcast(
            key,
            f"Nowy cel drużyny: {goal}. Kontrola gotowości została wyzerowana.",
        )
        return True


async def show_party_ready_v0610(self):
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            return False
        if key not in self.server.party_ready_checks:
            await self.send(
                "Kontrola gotowości nie jest aktywna. Lider uruchamia ją komendą: druzyna gotowi."
            )
            return True

        ready = self.server.party_ready_checks.get(key, set())
        members = sorted(
            self.server.party_sessions(self.account_id),
            key=lambda session: session.character.name.lower(),
        )
        await self.send(f"GOTOWOŚĆ DRUŻYNY: {len(ready)} z {len(members)}.")
        for number, session in enumerate(members, 1):
            status = "gotowy" if session.account_id in ready else "niegotowy"
            await self.send(f"{number}. {session.character.name}: {status}.")
        return True


async def handle_party_ready_v0610(self, value=""):
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            return False

        mode = self.normalize_description_query(str(value or "").strip())
        if mode in ("status", "lista", "list"):
            return await self.show_party_ready_v0610()

        if mode in ("reset", "restart", "odnow"):
            if key != self.account_id:
                await self.send("Tylko lider może zresetować kontrolę gotowości.")
                return False
            self.server.party_ready_checks[key] = {self.account_id}
            await self.server.party_broadcast(
                key,
                f"{self.character.name} rozpoczyna nową kontrolę gotowości. "
                "Każdy odpowiada: druzyna gotowi.",
            )
            return await self.show_party_ready_v0610()

        ready = self.server.party_ready_checks.get(key)
        if ready is None:
            if key != self.account_id:
                await self.send(
                    "Kontrola gotowości nie jest aktywna. Musi ją rozpocząć lider drużyny."
                )
                return False
            ready = {self.account_id}
            self.server.party_ready_checks[key] = ready
            await self.server.party_broadcast(
                key,
                f"{self.character.name} rozpoczyna kontrolę gotowości. "
                "Każdy odpowiada: druzyna gotowi.",
            )
        elif self.account_id not in ready:
            ready.add(self.account_id)
            await self.server.party_broadcast(
                key,
                f"{self.character.name}: GOTOWY.",
            )
        else:
            await self.send("Twoja gotowość jest już potwierdzona.")

        members = set(self.server.parties.get(key, set()))
        ready.intersection_update(members)
        if members and members.issubset(ready):
            await self.server.party_broadcast(
                key,
                "WSZYSCY GOTOWI. Cała drużyna potwierdziła gotowość.",
            )
        else:
            await self.send(f"Gotowi: {len(ready)} z {len(members)}.")
        return True


async def set_party_not_ready_v0610(self):
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            return False
        ready = self.server.party_ready_checks.get(key)
        if ready is None:
            await self.send("Kontrola gotowości nie jest aktywna.")
            return False
        if self.account_id not in ready:
            await self.send("Już masz status: niegotowy.")
            return True
        ready.discard(self.account_id)
        await self.server.party_broadcast(key, f"{self.character.name}: NIEGOTOWY.")
        return True


async def leave_party(self, announce=True):
        key = self.party_key()
        if key is None:
            if announce:
                await self.send("Nie należysz do drużyny.")
            return False

        protector_id = self.server.party_protectors.get(key)
        if protector_id == self.account_id:
            await self.stop_party_protection(announce=False)
            protector_id = None

        members = self.server.parties.get(key, set())
        members.discard(self.account_id)

        if self.account_id == key:
            # v0.36.0: lider nie przekazuje już przywództwa. Jego wyjście
            # zawsze rozwiązuje drużynę, niezależnie od tego, ilu członków zostało.
            for member_id in list(members):
                session = self.server.session_by_account(member_id)
                if session:
                    await session.send(
                        f"Lider {self.character.name} opuszcza drużynę. Drużyna została rozwiązana."
                    )
            self.server.parties.pop(key, None)
            self.server.party_protectors.pop(key, None)
            self.server.party_goals.pop(key, None)
            self.server.party_ready_checks.pop(key, None)
            self.server.party_routes_v1193.pop(key, None)
            for invited_id, leader_id in list(self.server.party_invites.items()):
                if leader_id == key:
                    self.server.party_invites.pop(invited_id, None)
            if announce:
                await self.send("Opuszczasz drużynę. Drużyna została rozwiązana.")
            return True
        else:
            self.server.parties[key] = members
            ready = self.server.party_ready_checks.get(key)
            if ready is not None:
                ready.discard(self.account_id)
            await self.server.party_broadcast(
                key,
                f"{self.character.name} opuszcza drużynę.",
                exclude=self,
            )

        for target_id, leader_id in list(self.server.party_invites.items()):
            if target_id == self.account_id or leader_id == self.account_id:
                self.server.party_invites.pop(target_id, None)

        if announce:
            await self.send("Opuszczasz drużynę.")
        return True


async def disband_party(self):
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            return
        if key != self.account_id:
            await self.send("Tylko lider może rozwiązać drużynę.")
            return

        members = list(self.server.parties.get(key, set()))
        for member_id in members:
            session = self.server.session_by_account(member_id)
            if session:
                await session.send(
                    "Drużyna została rozwiązana przez lidera."
                )
        self.server.parties.pop(key, None)
        self.server.party_protectors.pop(key, None)
        self.server.party_goals.pop(key, None)
        self.server.party_ready_checks.pop(key, None)
        self.server.party_routes_v1193.pop(key, None)
        for target_id, leader_id in list(self.server.party_invites.items()):
            if leader_id == key:
                self.server.party_invites.pop(target_id, None)


async def party_invite(self, name):
        name = self.clean_party_player_argument(name, relation="to")
        if not name:
            await self.send("Użycie: zaproś <gracz> [do drużyny].")
            return
        target = self.server.find_character_session(name.strip())
        if not target:
            await self.send("Ten gracz nie jest online.")
            return
        if target is self:
            await self.send("Nie możesz zaprosić samego siebie.")
            return
        if self.server.party_key_for_account(target.account_id) is not None:
            await self.send("Ten gracz już należy do drużyny.")
            return

        key = self.party_key()
        if key is None:
            key = self.account_id
            self.server.parties[key] = {self.account_id}
        elif key != self.account_id:
            await self.send("Tylko lider drużyny może zapraszać.")
            return

        capacity = self.character.party_capacity()
        if len(self.server.parties[key]) >= capacity:
            await self.send(
                f"Drużyna jest pełna. Limit lidera: {capacity} osób."
            )
            return

        self.server.party_invites[target.account_id] = key
        await target.send(
            f"{self.character.name} zaprasza cię do drużyny. "
            f"Wpisz dołącz / dolacz albo odrzuć / odrzuc."
        )
        await self.send(
            f"Zapraszasz {target.character.name} do drużyny."
        )


async def party_accept(self):
        leader_id = self.server.party_invites.get(self.account_id)
        if leader_id is None:
            await self.send("Nie masz aktywnego zaproszenia do drużyny.")
            return

        leader = self.server.session_by_account(leader_id)
        members = self.server.parties.get(leader_id)
        if not leader or members is None:
            self.server.party_invites.pop(self.account_id, None)
            await self.send("Ta drużyna nie jest już dostępna.")
            return
        if self.party_key() is not None:
            self.server.party_invites.pop(self.account_id, None)
            await self.send("Już należysz do drużyny.")
            return

        capacity = leader.character.party_capacity()
        if len(members) >= capacity:
            self.server.party_invites.pop(self.account_id, None)
            await self.send("Drużyna osiągnęła limit lidera.")
            return

        members.add(self.account_id)
        ready = self.server.party_ready_checks.get(leader_id)
        if ready is not None:
            ready.discard(self.account_id)
        self.server.party_invites.pop(self.account_id, None)
        await self.server.party_broadcast(
            leader_id,
            f"{self.character.name} dołącza do drużyny."
        )


async def party_kick(self, name):
        name = self.clean_party_player_argument(name, relation="from")
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            return
        if key != self.account_id:
            await self.send("Tylko lider może wyrzucać członków.")
            return

        target = self.server.find_character_session(name.strip())
        if not target or target.account_id not in self.server.parties[key]:
            await self.send("Nie ma takiego członka w twojej drużynie.")
            return
        if target is self:
            await self.send(
                "Lider używa druzyna opusc albo druzyna rozwiaz."
            )
            return

        if self.server.party_protectors.get(key) == target.account_id:
            await target.stop_party_protection(announce=False)

        self.server.parties[key].discard(target.account_id)
        ready = self.server.party_ready_checks.get(key)
        if ready is not None:
            ready.discard(target.account_id)
        await target.send(
            f"{self.character.name} usuwa cię z drużyny."
        )
        await self.server.party_broadcast(
            key,
            f"{target.character.name} zostaje usunięty z drużyny.",
            exclude=target,
        )


async def assist_party_member(self, name):
        name = str(name or "").strip()

        if not name:
            await self.send(
                "Użycie: wspieraj <gracz> albo assist <gracz>."
            )
            return False

        if self.party_key() is None:
            await self.send(
                "Nie należysz do drużyny."
            )
            return False

        target = self.server.find_character_session(name)
        if not target:
            await self.send(
                "Ten gracz nie jest online."
            )
            return False

        if target is self:
            await self.send(
                "Nie możesz wspierać samego siebie."
            )
            return False

        if not self.server.same_party(
            self.account_id,
            target.account_id,
        ):
            await self.send(
                f"{target.character.name} nie należy do twojej drużyny."
            )
            return False

        if (
            target.character.room_id
            != self.character.room_id
        ):
            await self.send(
                f"{target.character.name} nie jest w tej samej lokacji."
            )
            return False

        target_mob_key = target.combat_mob_key
        if not target_mob_key:
            await self.send(
                f"{target.character.name} z nikim teraz nie walczy."
            )
            return False

        mob = self.server.world.mobs.get(
            target_mob_key
        )
        if (
            not mob
            or not mob.alive
            or mob.room_id != self.character.room_id
        ):
            await self.send(
                "Cel walki tego gracza nie jest już dostępny."
            )
            return False

        if (
            self.combat_mob_key
            and self.combat_mob_key != mob.key
        ):
            current = self.server.world.mobs.get(
                self.combat_mob_key
            )
            current_name = (
                MOB_TEMPLATES[current.template_id]["name"]
                if current and current.alive
                else "inny przeciwnik"
            )
            await self.send(
                f"Już walczysz z: {current_name}. "
                "Najpierw zakończ tę walkę albo użyj flee."
            )
            return False

        if self.combat_mob_key == mob.key:
            await self.send(
                f"Już wspierasz {target.character.name} "
                f"przeciw {MOB_TEMPLATES[mob.template_id]['name']}."
            )
            return False

        if not self.server.engagement_allowed(
            self,
            mob,
        ):
            await self.send(
                "Nie możesz dołączyć do tej walki."
            )
            return False

        self.combat_mob_key = mob.key
        await self.server.apply_party_protection(self, mob)

        mob_name = MOB_TEMPLATES[
            mob.template_id
        ]["name"]

        await self.send(
            f"Wspierasz {target.character.name} "
            f"przeciw {mob_name}."
        )

        await self.server.broadcast_room(
            self.character.room_id,
            f"{self.character.name} wspiera "
            f"{target.character.name} przeciw {mob_name}.",
            exclude=self,
        )

        await self.attack("")
        return True

