# -*- coding: utf-8 -*-
"""Party creation, protection, revive and assist."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
import asyncio
import time
from core.progression_resources import skill_power_multiplier
from player.character import PARTY_BASE_CAPACITY
from player.session_mixins.io_auth_character import CLASS_SKILLS
from player.session_mixins.movement import MOB_TEMPLATES, ROOMS


class SessionPartyMixin:

    def party_key(self):
            return self.server.party_key_for_account(self.account_id)

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
                        * self.character.class_healing_multiplier(),
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
                        * self.character.class_healing_multiplier(),
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

    def is_downed_v0371(self):
            return bool(
                self.character
                and self.current_hp <= 0
                and float(getattr(self, "party_downed_until_v0371", 0.0) or 0.0) > time.time()
                and getattr(self, "party_downed_room_v0371", None) == self.character.room_id
            )

    def party_revive_candidates_v0371(self):
            if not self.character or self.party_key() is None:
                return []
            room_id = self.character.room_id
            return [
                member for member in self.server.party_sessions(self.account_id, same_room=room_id)
                if member is not self and member.character and not member.closed and member.current_hp > 0
            ]

    def clear_downed_v0371(self, cancel_task=True):
            task = getattr(self, "party_downed_task_v0371", None)
            current = asyncio.current_task()
            if cancel_task and task and task is not current and not task.done():
                task.cancel()
            self.party_downed_task_v0371 = None
            self.party_downed_until_v0371 = 0.0
            self.party_downed_killer_v0371 = ""
            self.party_downed_room_v0371 = None

    async def _party_downed_timeout_v0371(self, deadline, room_id):
            try:
                await asyncio.sleep(max(0.0, float(deadline) - time.time()))
            except asyncio.CancelledError:
                return
            if (
                self.closed or not self.character or self.current_hp > 0
                or getattr(self, "party_downed_room_v0371", None) != room_id
                or float(getattr(self, "party_downed_until_v0371", 0.0) or 0.0) != float(deadline)
            ):
                return
            await self.respawn_from_downed_v0371(auto=True)

    async def begin_downed_v0371(self, killer, seconds=60):
            if not self.character:
                return False
            self.clear_downed_v0371(cancel_task=True)
            self.current_hp = 0
            self.current_mana = 0
            self.combat_mob_key = None
            self.skill_guard = 0
            self.skill_evade = False
            self.skill_evade_lockout_until = 0.0
            deadline = time.time() + max(1, int(seconds or 60))
            self.party_downed_until_v0371 = deadline
            self.party_downed_killer_v0371 = str(killer or "")
            self.party_downed_room_v0371 = self.character.room_id
            self.party_downed_task_v0371 = asyncio.create_task(
                self._party_downed_timeout_v0371(deadline, self.character.room_id)
            )
            await self.send(
                "Jesteś POWALONY. Członek twojej drużyny stojący w tej samej lokacji "
                "może użyć: wskrzes <twoja nazwa>. Masz 60 sekund. "
                "Możesz też wpisać odrodz, aby natychmiast wrócić do Świątyni Odrodzenia."
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
            if not self.character or self.current_hp <= 0:
                await self.send("Powalona postać nie może wskrzeszać innych.")
                return False
            if self.party_key() is None:
                await self.send("Wskrzeszanie działa tylko między członkami tej samej drużyny.")
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
            if not self.server.same_party(self.account_id, target.account_id):
                await self.send("Ta postać nie należy do twojej drużyny.")
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
            ready = self.server.party_ready_checks.pop(key, None)
            self.server.parties.pop(key, None)
            self.server.parties[target.account_id] = set(members)
            if protector_id in members:
                self.server.party_protectors[target.account_id] = protector_id
            if goal:
                self.server.party_goals[target.account_id] = goal
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
            if key in self.server.party_ready_checks:
                ready = self.server.party_ready_checks.get(key, set())
                await self.send(
                    f"Gotowość: {len(ready)} z {len(members)}. "
                    "Użyj: druzyna gotowi albo druzyna niegotowy."
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

    async def party_decline(self):
            leader_id = self.server.party_invites.pop(self.account_id, None)
            if leader_id is None:
                await self.send("Nie masz aktywnego zaproszenia.")
                return
            leader = self.server.session_by_account(leader_id)
            if leader:
                await leader.send(
                    f"{self.character.name} odrzuca zaproszenie do drużyny."
                )
            await self.send("Odrzucasz zaproszenie do drużyny.")

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

    async def party_chat(self, message):
            if not message.strip():
                await self.send("Użycie: pc <tekst>.")
                return
            if self.party_key() is None:
                await self.send("Nie należysz do drużyny.")
                return
            await self.server.party_broadcast(
                self.account_id,
                f"[Drużyna] {self.character.name}: {message.strip()}",
                history_category="party",
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

    async def handle_party(self, args):
            parts = args.strip().split(maxsplit=1)
            if not parts:
                await self.show_party()
                return

            action = self.normalize_description_query(parts[0])
            value = parts[1] if len(parts) > 1 else ""

            if action in ("status", "lista", "list", "sklad"):
                await self.show_party()
            elif action in ("zaloz", "utworz", "stworz", "create"):
                await self.create_party()
            elif action in ("zapros", "invite"):
                if not value:
                    await self.send("Użycie: druzyna zapros <gracz>.")
                else:
                    await self.party_invite(value)
            elif action in ("dolacz", "accept"):
                await self.party_accept()
            elif action in ("odrzuc", "decline"):
                await self.party_decline()
            elif action in ("opusc", "leave"):
                await self.leave_party(announce=True)
            elif action in ("wyrzuc", "kick"):
                if not value:
                    await self.send("Użycie: druzyna wyrzuc <gracz>.")
                else:
                    await self.party_kick(value)
            elif action in ("rozwiaz", "disband"):
                await self.disband_party()
            elif action in ("lider", "leader", "przekaz"):
                await self.transfer_party_leader(value)
            elif action in ("zaslon", "oslon", "protect"):
                await self.protect_party(value)
            elif action in ("wspieraj", "assist", "pomagaj"):
                if not value:
                    await self.send(
                        "Użycie: druzyna wspieraj <gracz>."
                    )
                else:
                    await self.assist_party_member(value)
            elif action in ("wskrzes", "wskrześ", "revive"):
                await self.revive_party_member_v0371(value)
            elif action in ("cel", "goal", "objective"):
                await self.set_party_goal_v0610(value)
            elif action in ("gotowi", "ready", "readycheck"):
                await self.handle_party_ready_v0610(value)
            elif action in ("niegotowy", "notready", "unready"):
                await self.set_party_not_ready_v0610()
            elif action in ("limit", "capacity"):
                key = self.party_key()
                leader = self.server.session_by_account(key) if key else self
                leader = leader or self
                await self.send(
                    f"Limit drużyny: {leader.character.party_capacity()} osób. "
                    f"Startowo 8; +1 miejsce co 25 Charyzmy lidera."
                )
            else:
                await self.send(
                    "Drużyna: zaloz, status, zapros <gracz>, dolacz, odrzuc, "
                    "opusc, wyrzuc <gracz>, rozwiaz, lider <gracz>, "
                    "cel <tekst>/off, gotowi [status/reset], niegotowy, "
                    "zaslon [off], wspieraj <gracz>, wskrzes <gracz>, limit. Czat: pc <tekst>."
                )
