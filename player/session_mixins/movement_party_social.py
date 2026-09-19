# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: movement_party_social."""

class SessionMovementPartySocialMixin:
    def dungeon_exit_destination(self, room_id=None):
            """Zwraca bezpieczny punkt wyjścia z rozpoznanego lochu."""
            room_id = str(room_id or self.character.room_id)

            # Kopalnia Głębinowa 1-200.
            if mine_floor_number(room_id) is not None:
                return "crystal_chamber", "Kopalnia Głębinowa"

            # Zwykła Krypta 1-200.
            if crypt_floor_number(room_id) is not None:
                return "crypt_hall", "Krypta"

            # Zwykła Wieża Astralna 100-200.
            if astral_floor_number(room_id) is not None:
                return "astral_gate", "Wieża Astralna"

            # Mityczne wersje.
            if mythic_crypt_floor_number(room_id) is not None:
                return "mythic_crypt_gate", "Mityczna Krypta"
            if mythic_astral_floor_number(room_id) is not None:
                return "mythic_astral_gate", "Mityczna Wieża Astralna"

            # Twierdza Gigantów.
            if giant_fortress_floor_number(room_id) is not None:
                return "giant_fortress_gate", "Twierdza Gigantów"

            # Lochy profesyjne.
            dungeon, _floor = profession_dungeon_floor(room_id)
            profession_exits = {
                "crystal_mine": ("crystal_chamber", "Kryształowe Groty"),
                "sunken_grotto": ("sea_pier", "Zatopiona Grota"),
                "ancient_forest": ("deep_grove", "Pradawny Las"),
                "alchemy_garden": ("herbalist_hut", "Ogród Alchemika"),
            }
            if dungeon in profession_exits:
                return profession_exits[dungeon]

            # Rozbudowana Jaskinia Trolli.
            room = ROOMS.get(room_id, {})
            if room.get("zone") == "Jaskinia Trolli" and room_id != "troll_cave_entrance":
                return "troll_cave_entrance", "Jaskinia Trolli"

            # Opcjonalne odnogi endgame z v0.7.40+.
            challenge_exits = {
                "wild_ancient_path": ("beast_den", "Pradawny Szlak Bestii"),
                "wild_primal_hollow": ("beast_den", "Pradawna Kotlina Dziczy"),
                "mountain_tempest_path": ("storm_summit", "Ścieżka Wiecznej Burzy"),
                "mountain_tempest_sanctum": ("storm_summit", "Sanktuarium Wiecznej Burzy"),
                "troll_abyss": ("troll_altar", "Otchłań Trolli"),
                "troll_abyss_throne": ("troll_altar", "Tron Pierwszego Wodza"),
                "swamp_rotten_depths": ("bog_heart", "Gnijące Głębie Bagna"),
                "swamp_primordial_pool": ("bog_heart", "Pradawne Rozlewisko"),
                "desert_sun_tomb": ("sun_temple", "Grobowiec Słońca"),
                "desert_solar_sanctum": ("sun_temple", "Sanktuarium Wiecznego Słońca"),
            }
            return challenge_exits.get(room_id)

    async def dungeon_exit(self):
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz użyć wyjścia awaryjnego podczas walki. "
                    "Najpierw użyj flee albo pokonaj przeciwnika."
                )
                return False

            result = self.dungeon_exit_destination()
            if not result:
                await self.send(
                    "Nie jesteś w rozpoznanym lochu ani zamkniętej odnodze. "
                    "Użyj wyjścia kierunkowego, prowadz albo guide."
                )
                return False

            target, dungeon_name = result
            old = self.character.room_id
            if old == target:
                await self.send(f"Jesteś już przy wyjściu: {ROOMS[target]['name']}.")
                return True

            self.previous_room_id = old
            await self.server.broadcast_room(
                old, f"{self.character.name} wycofuje się z lochu.", exclude=self
            )
            self.character.room_id = target
            self.server.db.save_character(self.character)
            await self.server.broadcast_room(
                target, f"{self.character.name} wraca z lochu.", exclude=self
            )
            await self.send(
                f"WYJŚCIE AWARYJNE: opuszczasz {dungeon_name}. "
                f"Wracasz do: {ROOMS[target]['name']}."
            )
            await self.look()
            return True

    def movement_delay(self, direction, guided=False):
            base = GUIDE_STEP_DELAY if guided else WALK_STEP_DELAY
            if direction in ("up", "down"):
                base *= 1.15
            return max(0.05, float(base))

    async def walk_room_transition(self, direction, target, guided=False, show_room=False):
            """Wykonuje pojedynczy krok z krótkim czasem marszu zamiast teleportu.

            v0.30.11 party-follow: gdy porusza się lider drużyny, członkowie, którzy
            stoją z nim w tej samej lokacji, próbują wykonać ten sam krok. Każdy
            follower przechodzi przez zwykłe `move()`, więc walka i indywidualne
            blokady wejścia nadal są respektowane; nie ma teleportowania przez bramy.
            """
            if self.closed or not self.character:
                return False
            old = self.character.room_id
            if old == target:
                return True
            self.server.world.ensure_runtime_room(target)
            label = DIRECTION_WALK_LABELS.get(direction, str(direction))
            target_name = ROOMS.get(target, {}).get("name", str(target))

            # Zbierz followerów PRZED ruchem lidera. Tylko lider uruchamia follow,
            # więc ruch członka nie wywoła rekurencyjnego łańcucha.
            party_followers = []
            party_key = self.party_key() if self.account_id is not None else None
            if party_key == self.account_id:
                for member in self.server.party_sessions(self.account_id, same_room=old):
                    if member is self or not member.character or member.closed:
                        continue
                    if member.moving or member.guiding:
                        continue
                    party_followers.append(member)

            async def follow_leader(member):
                try:
                    await member.send(
                        f"Podążasz za liderem {self.character.name}: {label}."
                    )
                    await member.move(direction)
                except Exception as exc:
                    print(
                        f"[PARTY FOLLOW ERROR] {getattr(member.character, 'name', member.account_id)}: {exc}",
                        file=sys.stderr, flush=True,
                    )

            follow_tasks = [
                asyncio.create_task(follow_leader(member))
                for member in party_followers
            ]

            self.moving = True
            try:
                await self.send(f"Idziesz {label}. Cel: {target_name}.")
                await self.server.broadcast_room(
                    old, f"{self.character.name} rusza {label}.", exclude=self
                )
                await asyncio.sleep(self.movement_delay(direction, guided=guided))
                if self.closed:
                    return False

                self.previous_room_id = old
                self.character.room_id = target
                self.server.db.save_character(self.character)
                await self.server.broadcast_room(
                    target, f"{self.character.name} przychodzi.", exclude=self
                )
                await self.send(f"Docierasz do: {target_name}.")
                if show_room:
                    await self.look()
                return True
            finally:
                self.moving = False
                if follow_tasks:
                    await asyncio.gather(*follow_tasks, return_exceptions=True)

    async def move(self, direction):
            if self.resting or self.rest_task:
                await self.stop_rest(
                    announce=True, reason="ruszasz się"
                )
            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
                await self.send("Auto-łowienie wyłączone z powodu ruchu.")
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
                await self.send("Auto-kopanie wyłączone z powodu ruchu.")
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
                await self.send("Auto-Drwalstwo wyłączone z powodu ruchu.")
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)
                await self.send("Auto-Zielarstwo wyłączone z powodu ruchu.")
            if self.combat_mob_key:
                await self.send("Jesteś w walce. Najpierw użyj flee albo pokonaj przeciwnika.")
                return
            target = ROOMS[self.character.room_id]["exits"].get(direction)
            if not target:
                await self.send("Nie możesz iść w tym kierunku.")
                return
            self.server.world.ensure_runtime_room(target)
            _newbie_block = self.newbie_entry_block_v03051(target)
            if _newbie_block:
                await self.send(_newbie_block)
                return
            mythic_error = self.mythic_entry_error(target)
            if mythic_error:
                await self.send(mythic_error)
                return

            profession_error = self.profession_dungeon_access_error(
                target
            )
            if profession_error:
                await self.send(profession_error)
                return

            # v0.30.12: trudność zwykłych terenów jest odnoszona do Levelu postaci,
            # nie do Biegłości klasy. Próg pozostaje rekomendacją, nie twardą blokadą.
            target_level = int(ROOMS.get(target, {}).get("recommended_mastery", 0) or 0)
            character_level = max(1, int(getattr(self.character, "character_level", 1) or 1))
            if target_level and character_level < target_level:
                await self.send(
                    f"Ostrzeżenie: to bardzo trudny teren. Zalecany Level postaci {target_level}; "
                    f"masz Level {character_level}. Wchodzisz na własne ryzyko."
                )

            if self.astral_entry_blocked(target):
                await self.send(
                    f"Wieża Astralna wymaga Soul Level "
                    f"{ASTRAL_MIN_SOUL_LEVEL}. "
                    f"Masz Soul Level {self.character.soul_level}."
                )
                return
            if self.mine_descent_blocked_for_player(
                self.character.room_id, direction
            ):
                progress = self.mine_progress()
                floor = mine_floor_number(
                    self.character.room_id
                )
                required_hits = progress["wall_required_hits"]
                await self.send(
                    f"Nie możesz zejść niżej. Ściana kopalni nie jest "
                    f"przebita. Postęp: {progress['wall_hits']} z "
                    f"{required_hits}. Użyj kop albo kop on."
                )
                return
            if self.mythic_crypt_descent_blocked_for_player(
                self.character.room_id, direction
            ):
                boss = self.server.world.live_mythic_crypt_boss(
                    self.character.room_id
                )
                boss_name = (
                    MOB_TEMPLATES[boss.template_id]["name"]
                    if boss else "mityczny boss Krypty"
                )
                await self.send(
                    f"Nie możesz zejść niżej. Drogę blokuje "
                    f"{boss_name}."
                )
                return

            if self.mythic_astral_ascent_blocked_for_player(
                self.character.room_id, direction
            ):
                boss = self.server.world.live_mythic_astral_boss(
                    self.character.room_id
                )
                boss_name = (
                    MOB_TEMPLATES[boss.template_id]["name"]
                    if boss else "mityczny boss Wieży Astralnej"
                )
                await self.send(
                    f"Nie możesz wejść wyżej. Drogę blokuje "
                    f"{boss_name}."
                )
                return

            if self.giant_fortress_ascent_blocked_for_player(
                self.character.room_id, direction
            ):
                boss = self.server.world.live_giant_fortress_boss(
                    self.character.room_id
                )
                boss_name = (
                    MOB_TEMPLATES[boss.template_id]["name"]
                    if boss
                    else "boss Twierdzy Gigantów"
                )
                await self.send(
                    f"Nie możesz wejść wyżej. Drogę blokuje "
                    f"{boss_name}. Najpierw pokonaj bossa."
                )
                return

            if self.crypt_descent_blocked_for_player(
                self.character.room_id, direction
            ):
                boss = self.server.world.live_crypt_boss(
                    self.character.room_id
                )
                boss_name = (
                    MOB_TEMPLATES[boss.template_id]["name"]
                    if boss else "boss Krypty"
                )
                await self.send(
                    f"Nie możesz zejść niżej. Drogę blokuje {boss_name}. "
                    "Najpierw pokonaj bossa."
                )
                return
            if self.v0200_megadungeon_blocked(self.character.room_id, direction):
                boss=self.v0200_live_blocking_boss(self.character.room_id,mega=True)
                await self.send(f"Dalszą sekcję megalochu blokuje {MOB_TEMPLATES[boss.template_id]['name'] if boss else 'boss progu'}. Pokonaj go pierwszy raz, aby odblokować przejście na stałe.")
                return
            if self.v0200_gauntlet_blocked(self.character.room_id, direction):
                boss=self.v0200_live_blocking_boss(self.character.room_id,gauntlet=True)
                await self.send(f"Następną rundę blokuje {MOB_TEMPLATES[boss.template_id]['name'] if boss else 'boss próby'}. Najpierw go pokonaj.")
                return
            if self.v0210_endless_gauntlet_blocked(self.character.room_id,direction):
                await self.send("Następną rundę Endless Gauntletu blokuje aktywny boss. Pokonaj go, aby iść dalej.")
                return

            if self.astral_ascent_blocked_for_player(
                self.character.room_id, direction
            ):
                boss = self.server.world.live_astral_boss(
                    self.character.room_id
                )
                boss_name = (
                    MOB_TEMPLATES[boss.template_id]["name"]
                    if boss else "boss Wieży Astralnej"
                )
                await self.send(
                    f"Nie możesz wejść wyżej. Drogę blokuje {boss_name}. "
                    "Najpierw pokonaj bossa."
                )
                return
            # v0.8.66: dostępne ostrzeżenie przed ostrym skokiem trudności.
            # Nie blokuje wejścia; jedynie informuje gracza przed wykonaniem kroku.
            current_profile = v0866_room_threat_profile(
                self.character.room_id, fallback=1
            )
            target_profile = v0866_room_threat_profile(target, fallback=1)
            current_danger = max(
                int(current_profile.get("target") or 1),
                int(current_profile.get("boss_max") or 0),
            )
            target_danger = max(
                int(target_profile.get("target") or 1),
                int(target_profile.get("boss_max") or 0),
            )
            player_power = self.character_progression_power()
            if (
                target_danger - current_danger >= 25
                and target_danger - player_power >= 20
            ):
                await self.send(
                    f"UWAGA: przed tobą gwałtowny wzrost zagrożenia. "
                    f"Docelowy poziom około {target_danger}/400, "
                    f"twoja siła około {player_power}/400. "
                    f"Ocena: {v0866_threat_label(target_danger, player_power)}."
                )

            await self.walk_room_transition(
                direction, target, guided=False, show_room=True
            )

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
                if self.skill_cooldowns.get(skill["id"], 0) > now:
                    continue
                mastery_group = skill.get("mastery_choice_group")
                if mastery_group and self.skill_cooldowns.get(f"group::{mastery_group}", 0) > now:
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
                if self.skill_cooldowns.get(skill["id"], 0) > now:
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
                self.skill_cooldowns[skill["id"]] = now + effective_cooldown
                mastery_group = skill.get("mastery_choice_group")
                if mastery_group:
                    self.skill_cooldowns[f"group::{mastery_group}"] = now + effective_cooldown

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

    async def create_party(self):
            key = self.party_key()
            if key is not None:
                await self.send("Już należysz do drużyny.")
                await self.show_party()
                return False
            self.server.parties[self.account_id] = {self.account_id}
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
            self.server.parties.pop(key, None)
            self.server.parties[target.account_id] = set(members)
            if protector_id in members:
                self.server.party_protectors[target.account_id] = protector_id

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
            for number, session in enumerate(members, 1):
                marker = " Lider." if session.account_id == key else ""
                await self.send(
                    f"{number}. {session.character.name}. "
                    f"Lokacja: {ROOMS[session.character.room_id]['name']}.{marker}"
                )

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
                if members:
                    candidates = [
                        self.server.session_by_account(member_id)
                        for member_id in members
                    ]
                    candidates = [s for s in candidates if s]
                    if candidates:
                        new_leader = sorted(
                            candidates,
                            key=lambda s: s.character.name.lower(),
                        )[0]
                        self.server.parties[new_leader.account_id] = set(members)
                        self.server.parties.pop(key, None)
                        if protector_id in members:
                            self.server.party_protectors.pop(key, None)
                            self.server.party_protectors[new_leader.account_id] = protector_id
                        else:
                            self.server.party_protectors.pop(key, None)
                        for invited_id, leader_id in list(self.server.party_invites.items()):
                            if leader_id == key:
                                self.server.party_invites[invited_id] = new_leader.account_id
                        await self.server.party_broadcast(
                            new_leader.account_id,
                            f"{new_leader.character.name} zostaje nowym liderem drużyny."
                        )
                    else:
                        self.server.parties.pop(key, None)
                        self.server.party_protectors.pop(key, None)
                else:
                    self.server.parties.pop(key, None)
                    self.server.party_protectors.pop(key, None)
            else:
                self.server.parties[key] = members
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
                    "zaslon [off], wspieraj <gracz>, limit. Czat: pc <tekst>."
                )

    def character_progression_power(self):
            """Generated combat progression estimate 1-400, including Character Level."""
            return self.combat_xp_power_v023()

    def exp_area_target_power(self, area, room_id=None):
            static_target = int(
                EXP_AREA_TARGET_POWER.get(
                    area.get("id"),
                    max(1, int(area.get("soul_min", 1))),
                )
            )
            room_id = room_id or ""

            # v0.8.66: jeśli konkretny pokój ma spawny, realne moby mają
            # pierwszeństwo przed szeroką etykietą biomu. Naprawia to m.in.
            # Pradawny Szlak Bestii / Otchłań Trolli / Grobowiec Słońca.
            if room_id:
                profile = v0866_room_threat_profile(room_id, fallback=static_target)
                if profile["normal_count"] or profile["variant_count"] or profile["boss_count"]:
                    return max(1, min(400, int(profile["target"])))

            # v0.8.66: dla listy expowisk bez konkretnego pokoju bierzemy
            # realny próg wejściowy z lokacji wskazanych przez guide. Dzięki temu
            # szeroka strefa z endgame odnogą (np. Dzicz) nie udaje w całości
            # poziomu 200, ale też Kanały/Cmentarz nie są zaniżane starą etykietą.
            guide = str(area.get("guide", "") or "").strip()
            if guide:
                matches = self.find_room_matches(guide)
                direct_targets = []
                zones = set()
                for target_room in matches:
                    room = ROOMS.get(target_room, {})
                    if room.get("zone"):
                        zones.add(room.get("zone"))
                    profile = v0866_room_threat_profile(
                        target_room, fallback=static_target
                    )
                    if profile["normal_count"] or profile["variant_count"]:
                        direct_targets.append(int(profile["target"]))
                if direct_targets:
                    return max(1, min(400, min(direct_targets)))
                zone_entries = []
                for zone in zones:
                    profile = v0866_zone_threat_profile(zone)
                    if profile.get("min") is not None:
                        zone_entries.append(int(profile["min"]))
                if zone_entries:
                    return max(1, min(400, min(zone_entries)))

            return max(1, min(400, static_target))

    def exp_area_dynamic_threat(self, area, room_id=None):
            power = self.character_progression_power()
            target = self.exp_area_target_power(area, room_id=room_id)
            label = v0866_threat_label(target, power)
            return label, target, power

    def exp_area_character_level_band_v03012(self, area):
            """Zwraca zakres Levelu postaci właściwy dla terenu.

            Stare pola soul_min/mastery_min są traktowane tylko jako dane zgodności.
            Dla nazwanych regionów endgame zachowujemy jawne zakresy 300-400
            zapisane w ich kategorii difficulty.
            """
            difficulty = str(area.get("difficulty") or "")
            match = re.search(r"(\d{1,3})\s*[-–]\s*(\d{1,3})", difficulty)
            if match:
                minimum = max(1, min(CHARACTER_MAX_LEVEL, int(match.group(1))))
                maximum = max(minimum, min(CHARACTER_MAX_LEVEL, int(match.group(2))))
                return minimum, maximum
            minimum = max(1, int(area.get("soul_min", 1) or 1))
            maximum = max(minimum, int(area.get("soul_max", minimum) or minimum))
            return min(CHARACTER_MAX_LEVEL, minimum), min(CHARACTER_MAX_LEVEL, maximum)

    def exp_area_recommended(self, area):
            # v0.30.12: wszystkie tereny są dobierane po Levelu postaci.
            level = max(1, int(getattr(self.character, "character_level", 1) or 1))
            minimum, maximum = self.exp_area_character_level_band_v03012(area)
            return minimum <= level <= maximum

    def exp_area_for_room(self, room_id=None):
            room_id = room_id or (self.character.room_id if self.character else "")
            if room_id == "training_ground":
                area_id = "trening"
            else:
                zone = ROOMS.get(room_id, {}).get("zone")
                area_id = EXP_ZONE_AREA_ID.get(zone)
            if not area_id:
                return None
            return next((a for a in EXP_AREAS if a.get("id") == area_id), None)

    def combat_xp_power_v023(self):
            """Generator-based combat power 1-400 across all progression axes."""
            active = self.active_class_names()
            masteries = [self.class_mastery_level(name) for name in active] or [1]
            highest_mastery = max(masteries)
            average_mastery = sum(masteries) / len(masteries)
            combat_stats = (
                self.effective_strength(), self.effective_dexterity(),
                self.effective_constitution(), self.effective_intelligence(),
                self.effective_willpower(),
            )
            average_stats = min(400.0, sum(combat_stats) / len(combat_stats))
            gear_levels = []
            for row in self.server.db.equipment(self.account_id):
                item = ITEMS.get(row["item_id"], {})
                gear_levels.append(int(item.get("generator_level", 1) or 1))
            gear_power = min(400.0, (sum(gear_levels) / len(gear_levels)) if gear_levels else 1.0)
            character_level = max(1, min(400, int(getattr(self.character, "character_level", 1) or 1)))
            # Generated axes share the budget; no historical 1-200 branch remains.
            score = (
                character_level * 0.22
                + highest_mastery * 0.28
                + average_mastery * 0.08
                + min(400.0, int(self.character.soul_level)) * 0.16
                + average_stats * 0.10
                + gear_power * 0.16
            )
            return max(1, min(400, int(round(score))))

    def dynamic_kill_xp_profile(self, template, room_id=None):
            """Płynnie skaluje CAŁY EXP z zabicia do relacji siły 1-400.

            Mob silniejszy od postaci daje premię za ryzyko. Ten sam przeciwnik
            daje coraz mniej, kiedy postać rozwija Biegłość, Soul Level, staty i
            EQ. Spadek jest stopniowy, a nie progowy, więc nie ma nagłego urwania
            nagrody po przekroczeniu jednego sztucznego progu.
            """
            power = self.combat_xp_power_v023()
            target = v0190_mob_stage(template)
            delta = float(target) - float(power)

            if delta >= 0.0:
                # +40 siły moba ~= x1.25, +80 ~= x1.50, +160 ~= x2.00.
                multiplier = 1.0 + delta / 160.0
            else:
                # Farma przeciwnika słabszego o 30 ~= x0.90, 60 ~= x0.80,
                # 120 ~= x0.60. Minimalnie zostaje 35% bazowego EXP.
                multiplier = 1.0 + delta / 300.0
            multiplier = max(
                DYNAMIC_KILL_XP_MIN_MULTIPLIER,
                min(DYNAMIC_KILL_XP_MAX_MULTIPLIER, multiplier),
            )

            if delta <= -120:
                label = "trywialny"
            elif delta <= -60:
                label = "łatwy"
            elif delta <= -20:
                label = "korzystny"
            elif delta <= 20:
                label = "odpowiedni"
            elif delta <= 60:
                label = "trudny"
            elif delta <= 120:
                label = "śmiertelny"
            else:
                label = "ekstremalny"

            area = self.exp_area_for_room(room_id)
            return {
                "label": label,
                "multiplier": float(multiplier),
                "area": area.get("name") if area else None,
                "target": int(target),
                "power": int(power),
                "delta": int(round(delta)),
            }

    def find_exp_area(self, query):
            wanted = self.normalize_description_query(query)
            if not wanted:
                return None

            exact = []
            partial = []

            for area in EXP_AREAS:
                names = (
                    area["id"],
                    area["name"],
                    *area.get("aliases", ()),
                )
                normalized = {
                    self.normalize_description_query(name)
                    for name in names
                }

                if wanted in normalized:
                    exact.append(area)
                elif any(
                    wanted in name
                    for name in normalized
                ):
                    partial.append(area)

            if exact:
                return exact[0]
            if len(partial) == 1:
                return partial[0]
            return None

    def exp_area_soul_text(self, area):
            minimum, maximum = self.exp_area_character_level_band_v03012(area)
            if minimum == maximum:
                return f"Level postaci {minimum}"
            return f"Level postaci {minimum}-{maximum}"

    def exp_area_category_text(self, area, room_id=None):
            base = EXP_AREA_BASE_CATEGORY.get(area.get("id"), "Umiarkowany")
            dynamic, target, power = self.exp_area_dynamic_threat(area, room_id=room_id)
            return (
                f"Kategoria bazowa: {base}. "
                f"Dla twojej obecnej postaci: {dynamic}. "
                f"Siła postaci {power}/400, próg terenu około {target}/400"
            )

    def resolve_terrain_zone(self, query):
            raw = str(query or "").strip()
            q = self.normalize_description_query(raw)
            if q.startswith("info "):
                raw = raw.split(maxsplit=1)[1]
                q = self.normalize_description_query(raw)
            elif q == "info":
                return None, []

            if not q:
                return None, []

            # Najpierw dokładna nazwa strefy.
            exact_zones = []
            for room in ROOMS.values():
                zone = room.get("zone", "")
                if q == self.normalize_description_query(zone):
                    exact_zones.append(zone)
            exact_zones = sorted(set(exact_zones))
            if len(exact_zones) == 1:
                return exact_zones[0], exact_zones

            matches = self.find_room_matches(raw)
            zones = sorted({
                ROOMS[room_id].get("zone", "Nieznany teren")
                for room_id in matches
                if room_id in ROOMS
            })
            if len(zones) == 1:
                return zones[0], zones

            area = self.find_exp_area(raw)
            if area:
                guide_matches = self.find_room_matches(area["guide"])
                area_zones = sorted({
                    ROOMS[room_id].get("zone", "Nieznany teren")
                    for room_id in guide_matches
                    if room_id in ROOMS
                })
                if len(area_zones) == 1:
                    return area_zones[0], area_zones
                if area_zones:
                    return None, area_zones

            return None, zones

    def terrain_exp_areas(self, zone):
            result = []
            for area in EXP_AREAS:
                matches = self.find_room_matches(area["guide"])
                zones = {
                    ROOMS[room_id].get("zone")
                    for room_id in matches
                    if room_id in ROOMS
                }
                if zone in zones:
                    result.append(area)
            return result

    def terrain_professions(self, room_ids):
            room_ids = set(room_ids)
            result = []
            checks = (
                ("Wędkarstwo", FISHING_ROOMS),
                ("Drwalstwo", WOODCUTTING_ROOMS),
                ("Zielarstwo", HERBALISM_ROOMS),
            )
            for name, rooms in checks:
                if room_ids & set(rooms):
                    result.append(name)
            if any(is_mining_room(room_id) for room_id in room_ids):
                result.append("Górnictwo")
            if "alchemy_lab" in room_ids:
                result.append("Alchemia")
            if "crafting_workshop" in room_ids or "forge" in room_ids:
                result.append("Kowalstwo i Rzemiosło")
            if "blue_flame_kitchen" in room_ids or "inn" in room_ids:
                result.append("Gotowanie")
            if "jeweler_workshop" in room_ids:
                result.append("Jubilerstwo")
            return result

    async def show_terrain_info(self, query=""):
            raw = str(query or "").strip()
            if not raw or self.normalize_description_query(raw) == "info":
                zones = sorted(
                    {room.get("zone", "") for room in ROOMS.values() if room.get("zone")},
                    key=self.normalize_description_query,
                )
                await self.send("TEREN INFO")
                await self.send(
                    "Użycie: teren info <nazwa>. Przykład: teren info bagna."
                )
                await self.send(
                    f"Dostępnych stref: {len(zones)}. "
                    "Pełną listę lokacji nadal pokazuje mapa, a expowiska pokazują zakresy expienia."
                )
                return

            zone, candidates = self.resolve_terrain_zone(raw)
            if not zone:
                if candidates:
                    await self.send(
                        "Nazwa pasuje do kilku terenów: " + ", ".join(candidates) + ". "
                        "Podaj dokładniejszą nazwę."
                    )
                else:
                    await self.send(
                        "Nie rozpoznaję terenu. Przykład: teren info bagna, teren info góry."
                    )
                return

            room_ids = [
                room_id for room_id, room in ROOMS.items()
                if room.get("zone") == zone
            ]
            room_set = set(room_ids)
            npcs = sorted(
                {
                    npc.get("name", npc_id)
                    for npc_id, npc in NPCS.items()
                    if npc.get("room") in room_set
                },
                key=self.normalize_description_query,
            )
            giver_names = set(npcs)
            quests = sorted(
                {
                    quest.get("name", quest_id)
                    for quest_id, quest in QUESTS.items()
                    if quest.get("giver") in giver_names
                },
                key=self.normalize_description_query,
            )
            spawned_mobs = {
                mob_id
                for spawn_room, mob_id in MOB_SPAWNS
                if spawn_room in room_set
            }
            boss_ids = self.codex_boss_ids()
            bosses = sorted(
                {
                    MOB_TEMPLATES[mob_id]["name"]
                    for mob_id in spawned_mobs
                    if mob_id in boss_ids and mob_id in MOB_TEMPLATES
                },
                key=self.normalize_description_query,
            )
            enemy_names = sorted(
                {
                    MOB_TEMPLATES[mob_id]["name"]
                    for mob_id in spawned_mobs
                    if mob_id in MOB_TEMPLATES
                },
                key=self.normalize_description_query,
            )
            professions = self.terrain_professions(room_ids)
            areas = self.terrain_exp_areas(zone)

            await self.send(f"TEREN INFO: {zone}")
            await self.send(f"Lokacje w strefie: {len(room_ids)}.")
            balance_profile = v0866_zone_threat_profile(zone)
            if balance_profile.get("median") is not None:
                await self.send(
                    f"Realna siła zwykłych części terenu: od {balance_profile['min']} "
                    f"do {balance_profile['max']} na skali 1-400. "
                    f"Mediana {balance_profile['median']}, górne 20 procent około {balance_profile['p80']}."
                )
            if balance_profile.get("boss_max") is not None:
                await self.send(
                    f"Bossowie tej strefy: orientacyjna siła od {balance_profile['boss_min']} "
                    f"do {balance_profile['boss_max']} na skali 1-400."
                )
            if areas:
                soul_min = min(int(area["soul_min"]) for area in areas)
                soul_max = max(int(area["soul_max"]) for area in areas)
                difficulty = ", ".join(dict.fromkeys(area["difficulty"] for area in areas))
                # v0.8.54: bazowa kategoria + dynamiczna ocena względem bieżącej postaci.
                dynamic_labels = [self.exp_area_category_text(area) for area in areas]
                await self.send(
                    f"Orientacyjny Soul: {soul_min}-{soul_max}. Dawna trudność: {difficulty}."
                )
                for text in dict.fromkeys(dynamic_labels):
                    await self.send(text + ".")
                descriptions = list(dict.fromkeys(area["description"] for area in areas))
                await self.send("Opis: " + " ".join(descriptions))
            else:
                await self.send(
                    "Orientacyjny Soul: brak osobnego zakresu w expowiska; teren może pełnić funkcję huba lub strefy specjalnej."
                )

            await self.send(
                "NPC: " + (", ".join(npcs) if npcs else "brak stałych NPC") + "."
            )
            await self.send(
                "Questy: " + (", ".join(quests) if quests else "brak questów przypisanych do NPC tej strefy") + "."
            )
            await self.send(
                "Bossowie: " + (", ".join(bosses) if bosses else "brak wykrytych bossów") + "."
            )
            await self.send(
                f"Przeciwnicy: {len(enemy_names)} typów" +
                ((": " + ", ".join(enemy_names) + ".") if enemy_names and len(enemy_names) <= 12 else ".")
            )
            await self.send(
                "Profesje i aktywności: " +
                (", ".join(professions) if professions else "brak osobnej aktywności profesyjnej") + "."
            )
            await self.send(f"Dojście: prowadz {zone}.")
            await self.send(
                "Dodatkowo: expowiska <nazwa> pokazuje szczegóły expienia, a mapa pokazuje lokacje."
            )

    async def show_exp_area_details(self, area):
            recommended = (
                " Polecane dla ciebie."
                if self.exp_area_recommended(area)
                else ""
            )

            await self.send(
                f"{area['name']}. "
                f"{self.exp_area_soul_text(area)}. "
                f"{self.exp_area_category_text(area)}."
                f"{recommended}"
            )
            await self.send(
                f"Opis: {area['description']}"
            )
            await self.send(
                f"Przeciwnicy: {area['enemies']}."
            )
            await self.send(
                f"Uwagi: {area['note']}"
            )
            await self.send(
                f"Prowadzenie: prowadz {area['guide']}."
            )

    async def show_exp_areas(self, query=""):
            query = str(query or "").strip()
            normalized = (
                self.normalize_description_query(query)
                if query
                else ""
            )

            if normalized in {
                "polecane", "recommended", "dla mnie",
            }:
                areas = [
                    area
                    for area in EXP_AREAS
                    if self.exp_area_recommended(area)
                ]
                await self.send(
                    f"POLECANE EXPOWISKA. "
                    f"Soul Level: {self.character.soul_level}. "
                    f"Orientacyjna siła postaci: {self.character_progression_power()}/400."
                )
                if not areas:
                    await self.send(
                        "Brak terenu dokładnie w twoim "
                        "orientacyjnym zakresie. "
                        "Wpisz expowiska, aby zobaczyć wszystko."
                    )
                    return
                for area in areas:
                    await self.send(
                        f"{area['name']}. "
                        f"{self.exp_area_category_text(area)}. "
                        f"{area['description']}"
                    )
                return

            if query:
                area = self.find_exp_area(query)
                if not area:
                    await self.send(
                        "Nie rozpoznaję expowiska. "
                        "Wpisz expowiska, aby usłyszeć pełną listę."
                    )
                    return
                await self.show_exp_area_details(area)
                return

            await self.send(
                f"EXPOWISKA. Soul Level: {self.character.soul_level}. "
                f"Orientacyjna siła postaci: {self.character_progression_power()}/400."
            )
            await self.send(
                "Tereny mają kategorię bazową: Początkujący, Umiarkowany, Trudny, "
                "Śmiertelny lub Endgame. Ocena 'dla ciebie' zmienia się automatycznie "
                "wraz z Biegłością klas, Soul Levelem, statystykami i wyposażeniem."
            )

            for number, area in enumerate(
                EXP_AREAS,
                1,
            ):
                marker = (
                    " Polecane dla ciebie."
                    if self.exp_area_recommended(area)
                    else ""
                )
                await self.send(
                    f"{number}. {area['name']}. "
                    f"{self.exp_area_category_text(area)}. "
                    f"{area['description']}"
                    f"{marker}"
                )

            await self.send(
                "Szczegóły: expowiska nazwa. "
                "Tylko polecane: expowiska polecane."
            )

    async def who(self):
            online = [
                session
                for session in self.server.sessions
                if session.character
            ]
            online.sort(
                key=lambda session: session.character.name.lower()
            )

            await self.send(
                f"Gracze online: {len(online)}."
            )

            if not online:
                return

            for session in online:
                character = session.character
                room = ROOMS.get(
                    character.room_id,
                    {
                        "name": character.room_id,
                        "zone": "Nieznana strefa",
                    },
                )

                classes = character.active_class_names()
                class_text = (
                    ", ".join(classes)
                    if classes
                    else character.class_name
                )

                title_text = (
                    f" Tytuł: {character.active_title}."
                    if character.active_title else ""
                )
                await self.send(
                    f"{character.name}. "
                    f"Klasa: {class_text}. "
                    f"Soul Level {character.soul_level}. "
                    f"Lokalizacja: {room['name']}. "
                    f"Strefa: {room['zone']}."
                    f"{title_text}"
                )

    async def say(self, text):
            message = str(text or "").strip()

            if not message:
                await self.send("Użycie: say tekst")
                return

            if len(message) > 500:
                message = message[:500]
                await self.send(
                    "Wiadomość skrócono do 500 znaków."
                )

            await self.send(
                f"Mówisz: {message}", history_category="chat"
            )
            await self.server.broadcast_room(
                self.character.room_id,
                f"{self.character.name} mówi: {message}",
                exclude=self, history_category="chat",
            )

    async def tell(self, args):
            parts = str(args or "").split(maxsplit=1)
            if len(parts) != 2:
                await self.send("Użycie: tell <gracz> <tekst>.")
                return
            target_name, message = parts[0].strip(), parts[1].strip()
            if not message:
                await self.send("Wiadomość nie może być pusta.")
                return
            if len(message) > 500:
                message = message[:500]
                await self.send("Wiadomość prywatną skrócono do 500 znaków.")
            target = self.server.find_character_session(target_name)
            if not target or target.closed or not target.character:
                await self.send("Ten gracz nie jest online.")
                return
            if target is self:
                await self.send("Nie musisz wysyłać prywatnej wiadomości do siebie.")
                return
            target.last_private_sender_account_id = self.account_id
            target.last_private_sender_name = self.character.name
            await target.send(
                f"[TELL] {self.character.name}: {message}", history_category="tell"
            )
            await self.send(
                f"[TELL do {target.character.name}] {message}", history_category="tell"
            )

    async def reply_private_v0928(self, message):
            message = str(message or "").strip()
            if not message:
                await self.send("Użycie: reply <tekst> albo odpisz <tekst>.")
                return
            if not self.last_private_sender_name:
                await self.send("Nie masz jeszcze nadawcy prywatnej wiadomości, któremu można odpisać.")
                return
            target = self.server.find_character_session(self.last_private_sender_name)
            if not target or target.closed or not target.character:
                await self.send(f"{self.last_private_sender_name} nie jest teraz online.")
                return
            await self.tell(f"{target.character.name} {message}")

    async def channel_broadcast_v03050(self, channel, message):
            message = str(message or "").strip()
            if not message:
                await self.send(f"Użycie: {channel} <tekst>.")
                return
            if len(message) > 500:
                message = message[:500]
                await self.send("Wiadomość skrócono do 500 znaków.")
            labels = {"gossip":"GOSSIP", "newbie":"NEWBIE", "trade":"TRADE"}
            label = labels.get(channel, channel.upper())
            text = f"[{label}] {self.character.name}: {message}"
            for session in list(self.server.sessions):
                if session.closed or not session.character:
                    continue
                await session.send(text, history_category="chat")

    async def show_channels_v03050(self):
            await self.send("KANAŁY: gossip <tekst> — rozmowy ogólne; newbie <tekst> — pytania i pomoc dla nowych graczy; trade <tekst> — handel. Lokalnie: say. Prywatnie: tell. Drużyna: pc. Gildia: gildia czat <tekst>.")

    def mentor_progress_v03050(self, account_id=None):
            aid = int(account_id if account_id is not None else self.account_id)
            row = self.server.db.conn.execute(
                "SELECT COALESCE(MAX(level),1) AS mx FROM class_progress WHERE account_id=?", (aid,)
            ).fetchone()
            mastery = int(row["mx"] or 1) if row else 1
            crow = self.server.db.conn.execute(
                "SELECT soul_level FROM characters WHERE account_id=?", (aid,)
            ).fetchone()
            soul = int(crow["soul_level"] or 1) if crow else 1
            return mastery, soul

    def mentor_link_v03050(self):
            return self.server.db.conn.execute(
                "SELECT mentor_account_id,student_account_id FROM mentor_links_v03050 WHERE mentor_account_id=? OR student_account_id=?",
                (self.account_id, self.account_id),
            ).fetchone()

    def mentor_bonus_percent_v03050(self):
            row = self.mentor_link_v03050()
            if not row:
                return 0
            other_id = int(row["student_account_id"] if int(row["mentor_account_id"]) == int(self.account_id) else row["mentor_account_id"])
            other = self.server.session_by_account(other_id)
            if not other or other.closed or not other.character or not self.character:
                return 0
            if other.character.room_id != self.character.room_id:
                return 0
            if not self.server.same_party(self.account_id, other_id):
                return 0
            return 5

    async def handle_mentor_v03050(self, args=""):
            raw = str(args or "").strip()
            conn = self.server.db.conn
            if not raw or normalize_lookup_text(raw) in ("status","info"):
                row = self.mentor_link_v03050()
                if not row:
                    await self.send("Mentor: brak aktywnej relacji. Mentor wymaga Biegłości co najmniej 50 i Soul Level 50; uczeń może mieć najwyżej Biegłość 20 i Soul Level 20.")
                    return
                mid, sid = int(row["mentor_account_id"]), int(row["student_account_id"])
                mname = self.server.db.character_name_by_account_v0928(mid) or str(mid)
                sname = self.server.db.character_name_by_account_v0928(sid) or str(sid)
                bonus = self.mentor_bonus_percent_v03050()
                await self.send(f"Mentor: {mname}. Uczeń: {sname}. Bonus wspólnej gry: +5% XP, teraz {'aktywny' if bonus else 'nieaktywny'}.")
                return
            parts = raw.split(maxsplit=1)
            action = normalize_lookup_text(parts[0])
            rest = parts[1].strip() if len(parts)>1 else ""
            if action in ("zapros","zaproś","invite"):
                if not rest:
                    await self.send("Użycie: mentor zapros <gracz>.")
                    return
                mastery, soul = self.mentor_progress_v03050()
                if mastery < 50 or soul < 50:
                    await self.send(f"Aby zostać mentorem potrzebujesz Biegłości 50 i Soul Level 50. Masz Biegłość {mastery}, Soul Level {soul}.")
                    return
                target = self.server.find_character_session(rest)
                if not target or target.closed or not target.character:
                    await self.send("Ten gracz nie jest online.")
                    return
                tm, ts = self.mentor_progress_v03050(target.account_id)
                if tm > 20 or ts > 20:
                    await self.send(f"Ta postać nie jest już początkująca. Limit ucznia: Biegłość 20 i Soul Level 20. Ma Biegłość {tm}, Soul Level {ts}.")
                    return
                if self.mentor_link_v03050() or target.mentor_link_v03050():
                    await self.send("Ty albo ten gracz macie już aktywną relację mentor-uczeń.")
                    return
                conn.execute("INSERT OR REPLACE INTO mentor_requests_v03050(mentor_account_id,student_account_id,created_at) VALUES(?,?,CURRENT_TIMESTAMP)",(self.account_id,target.account_id)); conn.commit()
                await self.send(f"Zapraszasz {target.character.name} do relacji mentor-uczeń.")
                await target.send(f"{self.character.name} chce zostać twoim mentorem. Użyj: mentor akceptuj {self.character.name}.")
                return
            if action in ("akceptuj","accept"):
                if not rest:
                    await self.send("Użycie: mentor akceptuj <gracz>.")
                    return
                target = self.server.find_character_session(rest)
                if not target or target.closed or not target.character:
                    await self.send("Mentor musi być online podczas akceptacji.")
                    return
                req = conn.execute("SELECT 1 FROM mentor_requests_v03050 WHERE mentor_account_id=? AND student_account_id=?",(target.account_id,self.account_id)).fetchone()
                if not req:
                    await self.send("Nie masz zaproszenia od tej osoby.")
                    return
                tm, ts = self.mentor_progress_v03050()
                mm, ms = target.mentor_progress_v03050()
                if tm > 20 or ts > 20 or mm < 50 or ms < 50:
                    await self.send("Nie spełniacie już warunków relacji mentor-uczeń.")
                    return
                if self.mentor_link_v03050() or target.mentor_link_v03050():
                    await self.send("Ty albo mentor macie już aktywną relację.")
                    return
                conn.execute("DELETE FROM mentor_requests_v03050 WHERE mentor_account_id=? AND student_account_id=?",(target.account_id,self.account_id))
                conn.execute("INSERT INTO mentor_links_v03050(mentor_account_id,student_account_id) VALUES(?,?)",(target.account_id,self.account_id)); conn.commit()
                await self.send(f"{target.character.name} zostaje twoim mentorem. Wspólna gra w tej samej drużynie i lokacji daje wam +5% XP.")
                await target.send(f"Zostajesz mentorem gracza {self.character.name}. Wspólna gra w tej samej drużynie i lokacji daje wam +5% XP.")
                return
            if action in ("zakoncz","zakończ","end","usun","usuń"):
                row = self.mentor_link_v03050()
                if not row:
                    await self.send("Nie masz aktywnej relacji mentor-uczeń.")
                    return
                other_id = int(row["student_account_id"] if int(row["mentor_account_id"]) == int(self.account_id) else row["mentor_account_id"])
                other = self.server.session_by_account(other_id)
                conn.execute("DELETE FROM mentor_links_v03050 WHERE mentor_account_id=? AND student_account_id=?",(int(row["mentor_account_id"]),int(row["student_account_id"]))); conn.commit()
                await self.send("Kończysz relację mentor-uczeń.")
                if other and not other.closed:
                    await other.send(f"{self.character.name} kończy relację mentor-uczeń.")
                return
            await self.send("Użycie: mentor, mentor zapros <gracz>, mentor akceptuj <gracz>, mentor zakoncz.")

    def friend_account_id_v0928(self, name):
            return self.server.db.character_account_id_by_name_v0928(name)

    async def show_friends_v0928(self):
            conn = self.server.db.conn
            rows = conn.execute(
                "SELECT f.friend_account_id,c.name FROM player_friends_v0928 f "
                "JOIN characters c ON c.account_id=f.friend_account_id "
                "WHERE f.account_id=? ORDER BY c.name COLLATE NOCASE",
                (self.account_id,),
            ).fetchall()
            await self.send("ZNAJOMI:")
            if not rows:
                await self.send("Lista znajomych jest pusta.")
            for row in rows:
                session = self.server.session_by_account(int(row["friend_account_id"]))
                status = "online" if session and not session.closed and session.character else "offline"
                if status == "online" and session.character:
                    rid = session.character.room_id
                    extra = f" — {ROOMS.get(rid, {}).get('name', rid)}"
                else:
                    extra = ""
                await self.send(f"{row['name']}: {status}{extra}.")
            incoming = conn.execute(
                "SELECT c.name FROM player_friend_requests_v0928 r "
                "JOIN characters c ON c.account_id=r.sender_account_id "
                "WHERE r.target_account_id=? ORDER BY r.created_at,c.name COLLATE NOCASE",
                (self.account_id,),
            ).fetchall()
            if incoming:
                await self.send("OCZEKUJĄCE PROŚBY:")
                for row in incoming:
                    await self.send(f"{row['name']}. Użyj: znajomi akceptuj {row['name']} albo znajomi odrzuc {row['name']}.")

    async def handle_friends_v0928(self, args=""):
            raw = str(args or "").strip()
            if not raw:
                await self.show_friends_v0928()
                return
            parts = raw.split(maxsplit=1)
            action = normalize_lookup_text(parts[0])
            rest = parts[1].strip() if len(parts) > 1 else ""
            conn = self.server.db.conn
            if action in ("dodaj", "add", "zaproś", "zapros"):
                if not rest:
                    await self.send("Użycie: znajomi dodaj <gracz>.")
                    return
                target_id = self.friend_account_id_v0928(rest)
                if target_id is None:
                    await self.send("Nie ma takiej postaci.")
                    return
                if int(target_id) == int(self.account_id):
                    await self.send("Nie możesz dodać samego siebie do znajomych.")
                    return
                if self.server.db.are_friends_v0928(self.account_id, target_id):
                    await self.send("Ta osoba jest już na twojej liście znajomych.")
                    return
                if conn.execute(
                    "SELECT 1 FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?",
                    (target_id, self.account_id),
                ).fetchone():
                    # Dwie krzyżujące się prośby oznaczają zgodę obu stron.
                    conn.execute("DELETE FROM player_friend_requests_v0928 WHERE (sender_account_id=? AND target_account_id=?) OR (sender_account_id=? AND target_account_id=?)", (target_id,self.account_id,self.account_id,target_id))
                    conn.execute("INSERT OR IGNORE INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)", (self.account_id,target_id))
                    conn.execute("INSERT OR IGNORE INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)", (target_id,self.account_id))
                    conn.commit()
                    name = self.server.db.character_name_by_account_v0928(target_id) or rest
                    await self.send(f"{name} zostaje twoim znajomym.")
                    target = self.server.session_by_account(target_id)
                    if target and not target.closed:
                        await target.send(f"{self.character.name} zostaje twoim znajomym.")
                    return
                conn.execute(
                    "INSERT OR REPLACE INTO player_friend_requests_v0928(sender_account_id,target_account_id,created_at) VALUES(?,?,CURRENT_TIMESTAMP)",
                    (self.account_id,target_id),
                )
                conn.commit()
                name = self.server.db.character_name_by_account_v0928(target_id) or rest
                await self.send(f"Wysyłasz prośbę o dodanie do znajomych: {name}.")
                target = self.server.session_by_account(target_id)
                if target and not target.closed:
                    await target.send(f"{self.character.name} chce dodać cię do znajomych. Użyj: znajomi akceptuj {self.character.name} albo znajomi odrzuc {self.character.name}.")
                return
            if action in ("akceptuj", "accept", "zaakceptuj"):
                sender_id = self.friend_account_id_v0928(rest) if rest else None
                if sender_id is None:
                    await self.send("Użycie: znajomi akceptuj <gracz>.")
                    return
                req = conn.execute(
                    "SELECT 1 FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?",
                    (sender_id,self.account_id),
                ).fetchone()
                if not req:
                    await self.send("Nie masz prośby od tej osoby.")
                    return
                conn.execute("DELETE FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?", (sender_id,self.account_id))
                conn.execute("DELETE FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?", (self.account_id,sender_id))
                conn.execute("INSERT OR IGNORE INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)", (self.account_id,sender_id))
                conn.execute("INSERT OR IGNORE INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)", (sender_id,self.account_id))
                conn.commit()
                name = self.server.db.character_name_by_account_v0928(sender_id) or rest
                await self.send(f"Dodajesz {name} do znajomych.")
                target = self.server.session_by_account(sender_id)
                if target and not target.closed:
                    await target.send(f"{self.character.name} zaakceptował twoją prośbę o znajomość.")
                return
            if action in ("odrzuc", "odrzuć", "decline"):
                sender_id = self.friend_account_id_v0928(rest) if rest else None
                if sender_id is None:
                    await self.send("Użycie: znajomi odrzuc <gracz>.")
                    return
                cur = conn.execute("DELETE FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?", (sender_id,self.account_id))
                conn.commit()
                await self.send("Odrzucono prośbę." if cur.rowcount else "Nie masz prośby od tej osoby.")
                return
            if action in ("usun", "usuń", "remove", "delete"):
                target_id = self.friend_account_id_v0928(rest) if rest else None
                if target_id is None:
                    await self.send("Użycie: znajomi usun <gracz>.")
                    return
                was = self.server.db.are_friends_v0928(self.account_id,target_id)
                conn.execute("DELETE FROM player_friends_v0928 WHERE (account_id=? AND friend_account_id=?) OR (account_id=? AND friend_account_id=?)", (self.account_id,target_id,target_id,self.account_id))
                conn.execute("DELETE FROM player_friend_requests_v0928 WHERE (sender_account_id=? AND target_account_id=?) OR (sender_account_id=? AND target_account_id=?)", (self.account_id,target_id,target_id,self.account_id))
                conn.commit()
                await self.send("Usunięto znajomego." if was else "Ta osoba nie była na twojej liście znajomych.")
                return
            if action in ("party", "druzyna", "drużyna"):
                target_id = self.friend_account_id_v0928(rest) if rest else None
                if target_id is None or not self.server.db.are_friends_v0928(self.account_id,target_id):
                    await self.send("Najpierw dodaj tę osobę do znajomych.")
                    return
                name = self.server.db.character_name_by_account_v0928(target_id)
                target = self.server.session_by_account(target_id)
                if not target or target.closed:
                    await self.send(f"{name or rest} nie jest teraz online.")
                    return
                await self.party_invite(target.character.name)
                return
            if action in ("gildia", "guild"):
                target_id = self.friend_account_id_v0928(rest) if rest else None
                if target_id is None or not self.server.db.are_friends_v0928(self.account_id,target_id):
                    await self.send("Najpierw dodaj tę osobę do znajomych.")
                    return
                name = self.server.db.character_name_by_account_v0928(target_id)
                target = self.server.session_by_account(target_id)
                if not target or target.closed:
                    await self.send(f"{name or rest} nie jest teraz online.")
                    return
                await self.handle_guild_v0926(f"zaproś {target.character.name}")
                return
            await self.send("Użycie: znajomi; znajomi dodaj/akceptuj/odrzuc/usun <gracz>; znajomi party <gracz>; znajomi gildia <gracz>.")

    def shop_item_base_value_silver(self, item):
            price = int(item.get("price") or 0)
            currency = item.get("currency", "silver")
            if currency == "silver":
                base = price
            elif currency == "gold":
                base = price * SILVER_PER_GOLD
            elif currency == "mithril":
                base = price * GOLD_PER_MITHRIL * SILVER_PER_GOLD
            else:
                base = 0
            required=max(1,int(item.get("required_mastery",1) or 1))
            if required >= 10 and base > 0:
                base=max(base,v0190_economy_sink(required,"equipment"))
            return min(V019_SAFE_INT,max(0,int(base)))

    def shop_cashback_silver(self, item):
            base = self.shop_item_base_value_silver(item)
            return (base * self.character.shop_discount_percent()) // 100

    async def show_charisma(self):
            c = self.character
            await self.send(f"Charyzma: {c.charisma}.")
            await self.send(
                f"Rabat sklepowy: {c.shop_discount_percent()} procent "
                f"z maksymalnych {CHARISMA_MAX_DISCOUNT} procent."
            )
            if c.shop_discount_percent() < CHARISMA_MAX_DISCOUNT:
                await self.send(
                    f"Do następnego 1 procent rabatu: "
                    f"{c.charisma_to_next_discount()} Charyzmy."
                )
            else:
                await self.send("Rabat sklepowy osiągnął maksimum.")
            await self.send(
                f"Limit drużyny jako lider: {c.party_capacity()} osób."
            )
            await self.send(
                f"Do następnego miejsca w drużynie: "
                f"{c.charisma_to_next_party_slot()} Charyzmy."
            )
            await self.send(
                "Charyzma jest szóstą normalną statystyką i ma własny niezależny EXP oraz próg. "
                "Udana sprzedaż przyznaje dodatkowy EXP Charyzmy zależny od wartości transakcji."
            )

    def charisma_sale_xp(self, sale_value_silver, units=1):
            """v0.19: handel także korzysta z Global Progression Generatora."""
            value = max(1, int(sale_value_silver or 0))
            units = max(1, int(units or 1))
            level = max(1, int(self.character.charisma))
            normal_stat_gain = generator_core_v027.axis_gain("stat", level, 1.0)
            value_factor = max(0.50, min(4.0, 0.55 + math.log10(value + 10) * 0.28))
            bulk_factor = max(1.0, min(1.8, 1.0 + math.log2(units + 1) * 0.08))
            gain = int(round(max(2.0, normal_stat_gain * 0.12 * value_factor * bulk_factor)))
            return min(V019_SAFE_INT, max(2, gain))

    async def gain_charisma_from_sale(self, sale_value_silver, units=1):
            old_discount = self.character.shop_discount_percent()
            old_capacity = self.character.party_capacity()
            xp = self.apply_double_xp(self.charisma_sale_xp(sale_value_silver, units=units))
            for message in self.character.add_stat_progress(xp, targets=("charisma",)):
                await self.send(message)
            new_discount = self.character.shop_discount_percent()
            new_capacity = self.character.party_capacity()
            if new_discount > old_discount:
                await self.send(
                    f"Nowy rabat sklepowy: {new_discount} procent."
                )
            if new_capacity > old_capacity:
                await self.send(
                    f"Nowy limit drużyny jako lider: {new_capacity} osób."
                )

    def bank_here(self):
            return self.character.room_id == BANK_ROOM

    def bank_currency_name(self, currency):
            if currency == "mithril":
                return "mithril"
            if currency == "gold":
                return "złota"
            return "srebra"

    def normalize_bank_currency(self, raw):
            value = normalize_lookup_text(raw)
            if value in ("silver", "srebro", "srebra", "srebrnych", "s"):
                return "silver"
            if value in ("gold", "zloto", "złoto", "zlota", "złota", "g"):
                return "gold"
            if value in ("mithril", "mithrilu", "m"):
                return "mithril"
            if value in ("moneta", "monety", "monet", "coins", "coin"):
                return "silver"
            return None

    def bank_amount_to_silver(self, amount, currency):
            amount = max(0, int(amount))
            if currency == "gold":
                return amount * SILVER_PER_GOLD
            if currency == "mithril":
                return amount * SILVER_PER_MITHRIL
            return amount

    async def show_bank(self):
            if not self.bank_here():
                await self.send(
                    "Bank Dusz obsługuje Bankier Aldren na Rynku. "
                    "Wpisz prowadz bank."
                )
                return

            row = self.server.db.bank_balance(
                self.account_id
            )
            await self.send("BANK DUSZ")
            await self.send(
                "Saldo: "
                + currency_reading_text(
                    row["silver"], row["gold"], row["mithril"],
                    full_names=True, include_zero=True,
                )
                + "."
            )

            items = self.server.db.bank_items(
                self.account_id
            )
            if not items:
                await self.send(
                    "Skrytka przedmiotów: pusta."
                )
            else:
                await self.send("Skrytka przedmiotów:")
                for item_row in items:
                    item = ITEMS.get(
                        item_row["item_id"],
                        {"name": item_row["item_id"]},
                    )
                    await self.send(
                        f"{item['name']} x"
                        f"{item_row['quantity']}."
                    )

            await self.send(
                "Komendy: bank wplac <ile> [srebra|zlota|mithril], "
                "bank wyplac <ile> [srebra|zlota|mithril], "
                "bank wplac wszystko, bank wyplac wszystko, "
                "bank wloz <przedmiot> [ile], "
                "bank wyjmij <przedmiot> [ile]."
            )

    async def bank_deposit_currency(self, amount, currency):
            amount = int(amount)
            if amount <= 0:
                await self.send(
                    "Kwota wpłaty musi być większa od zera."
                )
                return False

            wallet = self.character_wallet_silver_value()
            if wallet < amount:
                await self.send(
                    "Nie masz takiej wartości. Masz "
                    + currency_reading_text(wallet, 0, 0) + "."
                )
                return False

            if not self.server.db.change_bank_currency(
                self.account_id, currency, amount
            ):
                await self.send("Nie udało się wykonać wpłaty.")
                return False

            self.character.silver = wallet - amount
            self.character.gold = 0
            self.character.mithril = 0
            self.server.db.save_character(self.character)
            await self.send(
                "Wpłacasz " + currency_reading_text(amount, 0, 0)
                + " do Banku Dusz."
            )
            return True

    async def bank_withdraw_currency(self, amount, currency):
            amount = int(amount)
            if amount <= 0:
                await self.send(
                    "Kwota wypłaty musi być większa od zera."
                )
                return False

            balance = self.server.db.bank_balance(
                self.account_id
            )
            available = legacy_currency_to_coins(
                balance["silver"], balance["gold"], balance["mithril"]
            )
            if available < amount:
                await self.send(
                    "Na koncie nie ma takiej wartości. Saldo: "
                    + currency_reading_text(available, 0, 0) + "."
                )
                return False

            if not self.server.db.change_bank_currency(
                self.account_id, currency, -amount
            ):
                await self.send("Nie udało się wykonać wypłaty.")
                return False

            self.character.silver = self.character_wallet_silver_value() + amount
            self.character.gold = 0
            self.character.mithril = 0
            self.server.db.save_character(self.character)
            await self.send(
                "Wypłacasz " + currency_reading_text(amount, 0, 0)
                + " z Banku Dusz."
            )
            return True

    def split_bank_item_quantity(self, raw):
            raw = str(raw or "").strip()
            if not raw:
                return "", 1

            parts = raw.split()
            quantity = 1

            if (
                len(parts) > 1
                and parts[-1].isdigit()
            ):
                quantity = max(1, int(parts[-1]))
                raw = " ".join(parts[:-1]).strip()

            return raw, quantity

    async def bank_deposit_item(self, raw):
            query, quantity = self.split_bank_item_quantity(
                raw
            )
            if not query:
                await self.send(
                    "Użycie: bank wloz <przedmiot> [ilość]."
                )
                return False

            owned = {
                item_id: item
                for item_id, item in ITEMS.items()
                if self.server.db.item_qty(
                    self.account_id, item_id
                ) > 0
            }
            found = find_by_name(owned, query)
            if not found:
                await self.send(
                    "Nie masz takiego przedmiotu w inventory."
                )
                return False

            item_id, item = found

            if is_character_bound_item(item_id):
                await self.send(
                    f"{item['name']} jest przypisany do tej postaci. "
                    "Nie można go oddać, wyrzucić ani schować w Banku Dusz."
                )
                return False

            current = self.server.db.item_qty(
                self.account_id, item_id
            )

            equipped_ids = {
                row["item_id"]
                for row in self.server.db.equipment(
                    self.account_id
                )
            }
            if item_id in equipped_ids:
                await self.send(
                    f"{item['name']} jest aktualnie założony. "
                    "Nie można schować założonego przedmiotu w banku."
                )
                return False

            if current < quantity:
                await self.send(
                    f"Masz tylko {current} sztuk "
                    f"{item['name']}."
                )
                return False

            if not self.server.db.remove_item(
                self.account_id, item_id, quantity
            ):
                return False
            self.server.db.add_bank_item(
                self.account_id, item_id, quantity
            )

            await self.send(
                f"Do skrytki trafia {item['name']} x{quantity}."
            )
            return True

    async def bank_withdraw_item(self, raw):
            query, quantity = self.split_bank_item_quantity(
                raw
            )
            if not query:
                await self.send(
                    "Użycie: bank wyjmij <przedmiot> [ilość]."
                )
                return False

            rows = self.server.db.bank_items(
                self.account_id
            )
            stored = {
                row["item_id"]: ITEMS.get(
                    row["item_id"],
                    {"name": row["item_id"]},
                )
                for row in rows
            }
            found = find_by_name(stored, query)
            if not found:
                await self.send(
                    "Nie ma takiego przedmiotu w skrytce."
                )
                return False

            item_id, item = found
            current = self.server.db.bank_item_qty(
                self.account_id, item_id
            )
            if current < quantity:
                await self.send(
                    f"W skrytce jest tylko {current} sztuk "
                    f"{item['name']}."
                )
                return False

            if not self.server.db.remove_bank_item(
                self.account_id, item_id, quantity
            ):
                return False
            self.server.db.add_item(
                self.account_id, item_id, quantity
            )

            await self.send(
                f"Wyjmujesz ze skrytki "
                f"{item['name']} x{quantity}."
            )
            return True

    async def handle_bank(self, raw):
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz korzystać z banku podczas walki."
                )
                return

            if not self.bank_here():
                await self.send(
                    "Bank Dusz znajduje się na Rynku u Bankiera Aldrena. "
                    "Wpisz prowadz bank."
                )
                return

            raw = str(raw or "").strip()
            normalized = normalize_lookup_text(raw)

            if not normalized or normalized in (
                "saldo",
                "stan",
                "list",
                "lista",
            ):
                await self.show_bank()
                return

            parts = raw.split(maxsplit=1)
            action = normalize_lookup_text(parts[0])
            rest = parts[1] if len(parts) > 1 else ""
            normalized_rest = normalize_lookup_text(rest)

            if action in ("wplac", "deposit"):
                if normalized_rest == "wszystko":
                    deposited_any = False
                    amount = self.character_wallet_silver_value()
                    if amount > 0:
                        self.character.silver = amount
                        self.character.gold = 0
                        self.character.mithril = 0
                        await self.bank_deposit_currency(amount, "silver")
                        deposited_any = True
                    if not deposited_any:
                        await self.send(
                            "Nie masz waluty do wpłacenia."
                        )
                    return

                tokens = rest.split()
                if len(tokens) not in (1, 2) or not tokens[0].isdigit():
                    await self.send("Użycie: bank wplac <ile> [srebra|zlota|mithril].")
                    return
                currency = self.normalize_bank_currency(tokens[1]) if len(tokens) == 2 else "silver"
                if not currency:
                    await self.send("Nieznany nominał. Użyj: srebra, zlota albo mithril.")
                    return
                amount = self.bank_amount_to_silver(int(tokens[0]), currency)
                await self.bank_deposit_currency(amount, "silver")
                return

            if action in ("wyplac", "withdraw"):
                if normalized_rest == "wszystko":
                    balance = self.server.db.bank_balance(
                        self.account_id
                    )
                    withdrew_any = False
                    amount = legacy_currency_to_coins(
                        balance["silver"], balance["gold"], balance["mithril"]
                    )
                    if amount > 0:
                        await self.bank_withdraw_currency(amount, "silver")
                        withdrew_any = True
                    if not withdrew_any:
                        await self.send(
                            "Konto bankowe nie ma waluty do wypłacenia."
                        )
                    return

                tokens = rest.split()
                if len(tokens) not in (1, 2) or not tokens[0].isdigit():
                    await self.send("Użycie: bank wyplac <ile> [srebra|zlota|mithril].")
                    return
                currency = self.normalize_bank_currency(tokens[1]) if len(tokens) == 2 else "silver"
                if not currency:
                    await self.send("Nieznany nominał. Użyj: srebra, zlota albo mithril.")
                    return
                amount = self.bank_amount_to_silver(int(tokens[0]), currency)
                await self.bank_withdraw_currency(amount, "silver")
                return

            if action in (
                "wloz",
                "schowaj",
                "put",
                "deposititem",
            ):
                await self.bank_deposit_item(rest)
                return

            if action in (
                "wyjmij",
                "wez",
                "take",
                "withdrawitem",
            ):
                await self.bank_withdraw_item(rest)
                return

            await self.send(
                "Użycie: bank; bank wplac 100 srebra; bank wplac 5 zlota; bank wplac 1 mithril; "
                "bank wyplac 100 srebra; bank wplac wszystko; "
                "bank wyplac wszystko; bank wloz <przedmiot> [ile]; "
                "bank wyjmij <przedmiot> [ile]."
            )

    async def show_money(self):
            self.server.db.save_character(self.character)
            c = self.character
            await self.send(
                "Masz "
                + currency_reading_text(
                    c.silver, c.gold, c.mithril,
                    full_names=True, include_zero=True,
                )
                + "."
            )
            await self.send(
                "To jedno wspólne saldo. 100 srebra = 1 złoto, a 1000 złota = 1 mithril."
            )
