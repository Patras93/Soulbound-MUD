# -*- coding: utf-8 -*-
"""Movement and dungeon exit routing."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import asyncio
import sys
import re
from collections import deque
from core.classes_skills import ROOMS
from core.mines_threat import (
    DIRECTION_WALK_LABELS,
    GUIDE_STEP_DELAY,
    WALK_STEP_DELAY,
    v0866_room_threat_profile,
    v0866_threat_label,
)
from core.progression_600 import CHARACTER_MAX_LEVEL
from config.postal import COURIER_CITY_ROOM_TO_NAME_V0530
from core.progression_resources import mine_floor_number
from core.mine_tunnels import HORIZONTAL_MINE_DIRECTIONS, mine_tunnel_coords, mine_tunnel_identity, mine_tunnel_room_id
from systems.content_registry import MOB_TEMPLATES
from systems.mercenary_taverns import MERCENARIES, mercenary_follow_notice_v12210
from world.uoss_superboss_world import (
    UOSS_DEEP_DUNGEON_ENTRY_V11331,
    UOSS_DEEP_DUNGEON_FLOOR0_V11331,
    uoss_deep_dungeon_floor_number_v11331,
)
from systems.dungeons_regions import (
    astral_floor_number,
    crypt_floor_number,
    giant_fortress_floor_number,
    mythic_astral_floor_number,
    mythic_crypt_floor_number,
    profession_dungeon_floor,
)


class SessionMovementMixin:

    def dungeon_exit_destination(self, room_id=None):
            """Zwraca bezpieczny punkt wyjścia z rozpoznanego lochu."""
            room_id = str(room_id or self.character.room_id)

            # UOSS Deep Dungeon jest nieskończony; Floor 0 jest progiem Serpentariusa.
            if (
                uoss_deep_dungeon_floor_number_v11331(room_id) is not None
                or room_id == UOSS_DEEP_DUNGEON_FLOOR0_V11331
            ):
                return UOSS_DEEP_DUNGEON_ENTRY_V11331, "UOSS Deep Dungeon"

            # W obcych prywatnych chodnikach nie wykonuj automatycznej teleportacji.
            _tunnel_owner = mine_tunnel_identity(room_id)
            if _tunnel_owner is not None and _tunnel_owner[1] != self.account_id:
                return None
            # Kopalnia Głębinowa, również osobiste wykopane chodniki.
            if (mine_floor_number(room_id) is not None or
                    mine_tunnel_coords(room_id, self.account_id) is not None):
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
            # v108: do not teleport a player while their movement coroutine is
            # still walking, or while downed / dead. Teammates were already
            # screened below, but the leader / solo player was not.
            if (getattr(self, 'moving', False) or getattr(self, 'guiding', False)):
                await self.send(
                    "Wyjście awaryjne jest niedostępne podczas ruchu lub prowadzenia. "
                    "Zatrzymaj przemieszczanie i spróbuj ponownie."
                )
                return False
            if (getattr(self, 'current_hp', 1) <= 0 or
                    self.is_downed_v0371()):
                await self.send(
                    "Nie możesz skorzystać z wyjścia awaryjnego jako postać powalona. "
                    "Najpierw wróć do życia."
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
            mine_followers = []
            if dungeon_name == "Kopalnia Głębinowa" and self.party_key() == self.account_id:
                mine_followers = [member for member in
                    self.server.party_sessions(self.account_id, same_room=self.character.room_id)
                    if member is not self and getattr(member, "character", None)]
            if dungeon_name == "Kopalnia Głębinowa" and (self.auto_mining or self.auto_mining_task):
                await self.stop_auto_mining(announce=False)
                await self.send("Auto-kopanie wyłączone przed wyjściem z kopalni.")
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
            for member in mine_followers:
                # Each player is validated separately; never forcibly move a
                # player in combat, during a guide, or from another room.
                if (member.character.room_id != old or member.combat_mob_key or
                        member.moving or member.guiding or
                        getattr(member, 'current_hp', 0) <= 0 or member.is_downed_v0371()):
                    continue
                if member.auto_mining or member.auto_mining_task:
                    await member.stop_auto_mining(announce=False)
                member.previous_room_id = old
                member.character.room_id = target
                member.server.db.save_character(member.character)
                await member.send("Drużyna opuszcza Kopalnię Głębinową. Auto-kopanie wyłączone.")
                await member.look()
            return True

    async def change_dungeon_floor_v2009(self, raw=""):
            """Find the stairs from any room and walk through ordinary move().

            No teleport, no skipping guards/checkpoints, no skipping floors.
            Party followers run the same normal per-player entry validation.
            """
            direction_text = str(raw or '').strip().lower()
            direction_text = direction_text.replace('ó', 'o').replace('ł', 'l').replace('ę', 'e')
            direction_text = direction_text.replace('w gore', 'gora').replace('w dol', 'dol')
            if direction_text in ('gora', 'up', 'wyzej', 'w gore'):
                direction = 'up'
            elif direction_text in ('dol', 'dool', 'down', 'nizej', 'zejdz'):
                direction = 'down'
            else:
                await self.send('Użycie: pietro gora albo pietro dol. Przejście tylko o jedno piętro przez prawdziwe schody.')
                return
            if self.combat_mob_key or self.moving or self.guiding:
                await self.send('Najpierw zakończ walkę lub trwające prowadzenie.')
                return
            start = str(self.character.room_id)
            from systems.dungeons_regions import (
                crypt_floor_number, astral_floor_number, mythic_crypt_floor_number,
                mythic_astral_floor_number, giant_fortress_floor_number,
            )
            from world.uoss_superboss_world import uoss_deep_dungeon_floor_number_v11331
            from world.magitek_infinite import magitek_floor_number
            from systems.echo_dungeon_v1500 import echo_identity
            from core.progression_resources import mine_floor_number

            def _catacombs(room):
                found = re.match(r'^(?:v0900_)?catacomb_f([1-3])_', str(room))
                return int(found.group(1)) if found else None

            def _echo(room):
                ident = echo_identity(room)
                return int(ident[0]) if ident else None

            family = None
            for label, parser in (
                ('Katakumby', _catacombs), ('Krypta', crypt_floor_number),
                ('Mityczna Krypta', mythic_crypt_floor_number),
                ('Wieża Astralna', astral_floor_number),
                ('Mityczna Wieża Astralna', mythic_astral_floor_number),
                ('Twierdza Gigantów', giant_fortress_floor_number),
                ('UOSS Deep Dungeon', uoss_deep_dungeon_floor_number_v11331),
                ('Labirynt Echa', _echo), ('Kompleks Magitek', magitek_floor_number),
                ('Kopalnia Głębinowa', mine_floor_number),
            ):
                level = parser(start)
                if level is not None:
                    family = (label, parser, level)
                    break
            if family is None:
                await self.send('Nie jesteś na rozpoznanym piętrze. Użyj normalnych kierunków.')
                return
            label, parser, level = family
            # Route only INSIDE the same floor; the final crossing is a
            # separate move() that enforces all usual dungeon locks.
            queue = deque([(start, [])])
            visited = {start}
            route = None
            while queue:
                room_id, steps = queue.popleft()
                room = ROOMS.get(room_id) or {}
                for step, dest in room.get('exits', {}).items():
                    if step != direction:
                        continue
                    destination_floor = parser(dest)
                    if ((destination_floor is not None and abs(destination_floor - level) == 1)
                            or (destination_floor is None and not (level > 1 or direction == 'down'))):
                        route = steps + [(step, dest)]
                        break
                if route is not None:
                    break
                for step, dest in room.get('exits', {}).items():
                    if dest not in visited and parser(dest) == level:
                        visited.add(dest)
                        queue.append((dest, steps + [(step, dest)]))
            if route is None:
                await self.send(f'{label}, piętro {level}: brak schodów w wybranym kierunku.')
                return
            await self.send(f'{label}, piętro {level}: idziesz do schodów. Ruch normalny, blokady bossów obowiązują.')
            for step, expected in route:
                previous = str(self.character.room_id)
                await self.move(step)
                if str(self.character.room_id) != str(expected):
                    await self.send('Przejście zatrzymane przez blokadę, walkę lub brak dostępu.')
                    return
            await self.send(f'{label}: jesteś w {ROOMS.get(self.character.room_id, {}).get("name", self.character.room_id)}.')

    def movement_delay(self, direction, guided=False):
            # Jeden krok = 0,10 s: reczny, prowadzenie i ruch po schodach.
            # Czas SQLite/wiadomosci moze osobno zwiekszyc realny czas.
            return GUIDE_STEP_DELAY if guided else WALK_STEP_DELAY

    async def teleport_to_party_leader(self, raw=""):
            """Voluntary reunion, limited to ordinary crypt floors already unlocked.

            Never summons arbitrary accounts, skips a personal boss gate,
            travels to private side rooms, or moves anyone during combat.
            """
            requested = " ".join(str(raw or "").casefold().split())
            if requested not in ("", "to leader", "leader", "do lidera", "lider", "lidera"):
                await self.send("Użycie: teleport to leader lub tp lider.")
                return False
            if self.closed or not self.character or self.account_id is None:
                return False
            key = self.party_key()
            if key is None or key == self.account_id:
                await self.send("Tylko członek drużyny może teleportować się do lidera.")
                return False
            leader = self.server.session_by_account(key)
            if (not leader or leader.closed or not leader.character
                    or leader.party_key() != key):
                await self.send("Lider drużyny jest niedostępny.")
                return False
            if (self.combat_mob_key or self.moving or self.guiding
                    or getattr(self, 'current_hp', 0) <= 0 or self.is_downed_v0371()):
                await self.send("Teleport niedostępny podczas walki, ruchu lub po powaleniu.")
                return False
            if (leader.combat_mob_key or leader.moving or leader.guiding
                    or getattr(leader, 'current_hp', 0) <= 0 or leader.is_downed_v0371()):
                await self.send("Lider jest zajęty walką lub ruchem. Teleportuj się po jego zatrzymaniu.")
                return False
            old = str(self.character.room_id)
            target = str(leader.character.room_id)
            if old == target:
                await self.send("Jesteś już przy liderze.")
                return True
            # This is a recovery mechanism for fast crypt guidance, not a
            # general remote travel system. Only standard public floors.
            def crypt_location(room, *, allow_side_room=False):
                suffix = r'(?:_r\d+)?' if allow_side_room else ''
                match = re.fullmatch(r'(crypt|mythic_crypt)_floor_([1-9]\d*)' + suffix, room)
                if not match:
                    return None
                family, number = match.group(1), int(match.group(2))
                parsed = (crypt_floor_number(room) if family == 'crypt'
                          else mythic_crypt_floor_number(room))
                return (family, number) if parsed == number else None
            source = crypt_location(old, allow_side_room=True)
            destination = crypt_location(target)
            if source is None or destination is None or source[0] != destination[0]:
                await self.send("Teleport do lidera działa tylko pomiędzy zwykłymi piętrami tej samej Krypty. Bez sekretnych komnat.")
                return False
            family, start_floor = source
            target_floor = destination[1]
            # Crossing down from each tenth floor normally requires a boss
            # clear from THIS player's account; being in the party is not a
            # substitute for it. Never teleport through an uncleared gate.
            if target_floor > start_floor:
                for boss_floor in range(((start_floor + 9) // 10) * 10, target_floor, 10):
                    if not self.server.db.boss_floor_cleared(self.account_id, family, boss_floor):
                        await self.send(
                            f"Teleport zablokowany: najpierw zalicz bramę bossa na piętrze {boss_floor}."
                        )
                        return False
            # Recheck membership/leader destination immediately before save;
            # no await between this guard and the actual room assignment.
            if (self.party_key() != key or leader.closed or leader.character.room_id != target
                    or self.combat_mob_key or self.moving or self.guiding):
                await self.send("Drużyna lub położenie lidera zmieniły się. Spróbuj ponownie.")
                return False
            self.previous_room_id = old
            self.character.room_id = target
            try:
                self.server.db.save_character(self.character)
            except Exception:
                self.character.room_id = old
                self.previous_room_id = None
                raise
            await self.server.broadcast_room(old, f"{self.character.name} teleportuje się do lidera.", exclude=self)
            await self.server.broadcast_room(target, f"{self.character.name} dołącza do drużyny teleportem.", exclude=self)
            await self.send(f"Teleport do lidera {leader.character.name}: {ROOMS.get(target, {}).get('name', target)}.")
            await leader.send(f"{self.character.name} wrócił do drużyny teleportem.")
            await self.look()
            return True

    async def party_movement_barrier_v1130020(self, target):
            """Do not let rapid dungeon navigation strand an online teammate.

            A busy follower is stopped BEFORE the leader takes a step.  If a
            follower became blocked DURING the previous step, keep the stop
            latched until the party actually regroups.  No teleport, gate
            bypass or forced combat cancellation is performed.
            """
            if self.account_id is None or self.party_key() != self.account_id:
                return True
            room_id = self.character.room_id
            members = [member for member in self.server.party_sessions(self.account_id)
                       if member is not self and member.character and not member.closed]
            here = [member for member in members if member.character.room_id == room_id]
            busy = []
            for member in here:
                reasons = []
                if getattr(member, 'combat_mob_key', None):
                    reasons.append('walka')
                if getattr(member, 'moving', False):
                    reasons.append('ruch')
                if getattr(member, 'guiding', False):
                    reasons.append('prowadzenie')
                if getattr(member, 'current_hp', 1) <= 0:
                    reasons.append('powalony')
                if reasons:
                    busy.append(f"{member.character.name} ({'/'.join(reasons)})")
            if busy:
                await self.send('Drużyna czeka: ' + ', '.join(sorted(busy))
                                + '. Zakończcie walkę lub ruch przed kolejnym krokiem.')
                return False

            # Detect a separated crypt team even after a manual command or a
            # reconnection.  Members outside the crypt are not automatically
            # teleported into a dungeon or used to block independent visits.
            old_crypt = crypt_floor_number(room_id) is not None
            old_mythic = mythic_crypt_floor_number(room_id) is not None
            was_split = bool(getattr(self, '_party_follow_blocked_v1130012', False))
            separated = []
            for member in members:
                member_room = member.character.room_id
                if member_room == room_id:
                    continue
                same_crypt = old_crypt and crypt_floor_number(member_room) is not None
                same_mythic = old_mythic and mythic_crypt_floor_number(member_room) is not None
                if was_split or same_crypt or same_mythic:
                    label = ROOMS.get(member_room, {}).get('name', str(member_room))
                    separated.append(f'{member.character.name} ({label})')
            if separated:
                self._party_follow_blocked_v1130012 = True
                # Recovery MUST be possible. Allow only a step that goes
                # directly toward a lost member; a generic stop on all moves
                # would trap the leader forever in the next crypt room.
                closer = False
                for member in members:
                    member_room = member.character.room_id
                    if member_room == room_id:
                        continue
                    if target == member_room:
                        closer = True
                        break
                    shortest = getattr(self, 'shortest_path', None)
                    if callable(shortest):
                        path = shortest(room_id, member_room)
                        if path and path[0][1] == target:
                            closer = True
                            break
                if closer:
                    await self.send('Drużyna rozdzielona. Wracasz po członka drużyny.')
                    return True
                await self.send('Drużyna rozdzielona: ' + ', '.join(sorted(separated))
                                + '. Dalsze zejście wstrzymane. Zawróć do członka drużyny.')
                return False
            self._party_follow_blocked_v1130012 = False
            return True

    async def walk_room_transition(self, direction, target, guided=False, show_room=False):
            """Wykonuje pojedynczy krok z krótkim czasem marszu zamiast teleportu.

            v0.30.11 party-follow: gdy porusza się lider drużyny, członkowie, którzy
            stoją z nim w tej samej lokacji, próbują wykonać ten sam krok. Każdy
            follower przechodzi przez zwykłe `move()`, więc walka i indywidualne
            blokady wejścia nadal są respektowane; nie ma teleportowania przez bramy.
            """
            if self.closed or not self.character:
                return False
            # A leader must finish the previous party step before another
            # direction is accepted.  Otherwise a queued command can observe
            # followers still walking and silently leave them behind.
            if getattr(self, "moving", False):
                await self.send("Ruch drużyny jeszcze trwa. Poczekaj na zakończenie kroku.")
                return False
            if not await self.party_movement_barrier_v1130020(target):
                return False
            old = self.character.room_id
            if old == target:
                return True
            self.server.world.ensure_runtime_room(target)
            label = DIRECTION_WALK_LABELS.get(direction, str(direction))
            target_name = ROOMS.get(target, {}).get("name", str(target))
            sailing_v1000 = bool(
                ROOMS.get(old, {}).get("requires_ship")
                or ROOMS.get(target, {}).get("requires_ship")
            ) and not ROOMS.get(target, {}).get("underwater")
            entry_label_v03812 = (
                str(getattr(self, "_dungeon_entry_label_v03812", "") or "").strip()
                if not guided else ""
            )

            # Zbierz followerów PRZED ruchem lidera. Tylko lider uruchamia follow,
            # więc ruch członka nie wywoła rekurencyjnego łańcucha.
            party_followers = []
            # Remember every member who started with the leader, including
            # busy members. They cannot be forced through a restricted exit,
            # but a failed follow must never stay silent.
            party_start_members = []
            party_key = self.party_key() if self.account_id is not None else None
            if party_key == self.account_id:
                for member in self.server.party_sessions(self.account_id, same_room=old):
                    if member is self or not member.character or member.closed:
                        continue
                    party_start_members.append(member)
                    if member.moving or member.guiding:
                        continue
                    party_followers.append(member)

            async def follow_leader(member):
                try:
                    if entry_label_v03812:
                        await member.send(
                            f"Podążasz za liderem {self.character.name} do: {entry_label_v03812}."
                        )
                        member._dungeon_entry_label_v03812 = entry_label_v03812
                    else:
                        await member.send(
                            f"Podążasz za liderem {self.character.name}: {label}."
                        )
                    party_ship_passage = sailing_v1000 and hasattr(self, "ocean_ship_level_v1000")
                    if party_ship_passage:
                        member._party_ship_passage_v10014 = {
                            "leader": self.account_id,
                            "navigation": self.ocean_ship_level_v1000("navigation"),
                            "hull": self.ocean_ship_level_v1000("hull"),
                        }
                        await member.send(
                            f"Płyniesz wewnątrz statku lidera {self.character.name}."
                        )
                    member._party_follow_batch_save_v11123 = True
                    try:
                        # Secret door is not a normal world exit. A follower may
                        # use it only after discovering this very same floor.
                        if direction == "secret" and ROOMS.get(target, {}).get("v1190_secret_role") == "chamber":
                            from world.world_secrets_v1190 import secret_room_identity_v1190
                            _, secret_kind, secret_floor = secret_room_identity_v1190(target)
                            known = any(int(row["floor"]) == secret_floor for row in
                                        member.server.db.instance_secret_rows(member.account_id, secret_kind))
                            if not known:
                                await member.send("Lider znalazł ukrytą komnatę. Najpierw odkryj sekret na tym piętrze komendą sekret.")
                            elif member.combat_mob_key:
                                await member.send("Jesteś w walce. Nie możesz wejść za liderem do sekretu.")
                            else:
                                await member.walk_room_transition("secret", target, guided=False, show_room=True)
                        else:
                            await member.move(direction)
                    finally:
                        member._party_follow_batch_save_v11123 = False
                        if party_ship_passage:
                            member._party_ship_passage_v10014 = None
                        if entry_label_v03812:
                            member._dungeon_entry_label_v03812 = ""
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
                if entry_label_v03812:
                    await self.send(f"Wchodzisz do: {entry_label_v03812}.")
                    await self.server.broadcast_room(
                        old, f"{self.character.name} wchodzi do {entry_label_v03812}.", exclude=self
                    )
                else:
                    await self.send(f"{'Płyniesz' if sailing_v1000 else 'Idziesz'} {label}. Cel: {target_name}.")
                    # v113.00.28: followers still see their own movement, but
                    # should not broadcast five duplicate exits per leader step.
                    # The leader broadcasts normally. The existing batch marker
                    # is set only around validated follower transitions.
                    if not getattr(self, "_party_follow_batch_save_v11123", False):
                        await self.server.broadcast_room(
                            old, f"{self.character.name} {'odpływa' if sailing_v1000 else 'rusza'} {label}.", exclude=self
                        )
                await asyncio.sleep(self.movement_delay(direction, guided=guided))
                if self.closed:
                    return False

                self.previous_room_id = old
                self.character.room_id = target
                self.server.db.save_character(
                    self.character,
                    commit=not bool(getattr(self, "_party_follow_batch_save_v11123", False)),
                )
                await self.register_uoss_deep_dungeon_visit_v11331(target)
                # v2.32.2: prowadzenie moze pominac look() dla NVDA.
                # Samo dotarcie do nowej lokacji przyznaje wtedy EP + EXP
                # automatycznie, dokladnie raz przez mark_room_discovered().
                if not show_room:
                    # Starsze symulatory ruchu sa uproszczonymi atrapami sesji.
                    # Prawdziwa Session dziedziczy discover_current_room().
                    if hasattr(self, "discover_current_room"):
                        await self.discover_current_room(announce=True)
                if callable(getattr(self, 'remember_catacomb_floor_v2010', None)):
                    self.remember_catacomb_floor_v2010(target)
                if callable(getattr(self, "grand_expedition_visit_v1260", None)):
                    await self.grand_expedition_visit_v1260(target)
                if hasattr(self, "ocean_contract_step_v1001"):
                    contract_event = self.ocean_contract_step_v1001(old, target)
                    if contract_event == "started":
                        await self.send("Kontrakt morski: rozpoczęto zaliczanie rejsu.")
                    elif contract_event == "lost":
                        await self.send("Kontrakt morski: opuszczono szlak, postęp rejsu wyzerowany. Wróć do portu nadania.")
                    elif contract_event == "complete":
                        await self.send("Kontrakt morski: dopłynięcie potwierdzone. Wpisz handel morski oddaj.")
                city_name_v0530 = COURIER_CITY_ROOM_TO_NAME_V0530.get(str(target))
                if city_name_v0530 and self.account_id is not None:
                    self.server.db.record_courier_city_visit_v0530(self.account_id, city_name_v0530)
                if not getattr(self, "_party_follow_batch_save_v11123", False):
                    await self.server.broadcast_room(
                        target, f"{self.character.name} {'przypływa' if sailing_v1000 else 'przychodzi'}.", exclude=self
                    )
                if entry_label_v03812:
                    await self.send(f"WEJŚCIE: {target_name}.")
                else:
                    await self.send(f"{'Dopływasz' if sailing_v1000 else 'Docierasz'} do: {target_name}.")
                # Manual moves already show the follower line in `look`.
                # A guided route shows it only once, not on every step (NVDA).
                if not show_room:
                    if not guided or not getattr(self, "_mercenary_guide_announced_v12210", False):
                        names = [
                            MERCENARIES[row["role"]]["name"]
                            for row in self.server.db.mercenary_contracts(self.account_id)
                            if row["role"] in MERCENARIES
                        ] if self.account_id is not None else []
                        notice = mercenary_follow_notice_v12210(names)
                        if notice:
                            await self.send(notice)
                        if guided:
                            self._mercenary_guide_announced_v12210 = True
                if show_room:
                    await self.look()
            finally:
                try:
                    # Keep moving=True for the ENTIRE party step, including
                    # follower tasks and their SQLite commit.  Clearing it
                    # before gather() let the leader accept a second step
                    # while members were still in the previous room.
                    if follow_tasks:
                        await asyncio.gather(*follow_tasks, return_exceptions=True)
                        # v1.11.23: one commit for all followers' positions.
                        self.server.db.conn.commit()
                    lagging_members = [
                        member for member in party_start_members
                        if member.character and not member.closed
                        and member.character.room_id != target
                    ]
                    if lagging_members:
                        self._party_follow_blocked_v1130012 = True
                        lagging = sorted({
                            member.character.name for member in lagging_members
                        }, key=str.casefold)
                        if not self.closed:
                            await self.send(
                                "Drużyna: zostali w tyle: " + ", ".join(lagging)
                                + ". Sprawdź walkę, prowadzenie lub blokadę przejścia."
                            )
                        for member in lagging_members:
                            if not member.closed:
                                await member.send(
                                    "Nie nadążasz za liderem. Sprawdź blokadę przejścia lub zakończ ruch."
                                )
                finally:
                    self.moving = False
            # The historically protected guide_to() already stops on False.
            # Signal that a guided multi-step route must stop after this
            # completed step if any follower stayed behind; never pretend
            # the whole party arrived, and never teleport past a blocked exit.
            if guided and bool(getattr(self, "_party_follow_blocked_v1130012", False)):
                if not self.closed:
                    await self.send("Prowadzenie wstrzymane: członek drużyny został w tyle.")
                return False
            return True

    async def move(self, direction, preserve_auto_mining=False):
            if getattr(self, "moving", False):
                # v113.00.28: real player commands can arrive before the
                # previous 0.1s party step has committed. Briefly await the
                # step instead of discarding their next direction. No busy
                # polling, unbounded command queue or change to movement speed.
                # Test fixtures without runtime state retain the original guard.
                if (hasattr(self, "resting") and self.account_id is not None
                        and self.party_key() == self.account_id
                        and not getattr(self, "guiding", False)
                        and not getattr(self, "_party_follow_batch_save_v11123", False)):
                    for _ in range(30):
                        if not self.moving or self.closed:
                            break
                        await asyncio.sleep(0.01)
                if getattr(self, "moving", False) or self.closed:
                    await self.send("Trwa poprzedni krok. Poczekaj na zakończenie ruchu drużyny.")
                    return
            if self.resting or self.rest_task:
                await self.stop_rest(
                    announce=True, reason="ruszasz się"
                )
            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
                await self.send("Auto-łowienie wyłączone z powodu ruchu.")
            if (self.auto_mining or self.auto_mining_task) and not preserve_auto_mining:
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
            # Directional, player-owned tunnels take precedence over old procedural
            # side-rooms; never leak one miner's passages to another account.
            identity = mine_tunnel_identity(self.character.room_id)
            if identity is not None and identity[1] != self.account_id:
                await self.send("To nie jest twój chodnik kopalniany.")
                return
            tunnel_coords = mine_tunnel_coords(self.character.room_id, self.account_id)
            personal_target = None
            if tunnel_coords and direction in HORIZONTAL_MINE_DIRECTIONS:
                floor, x, y = tunnel_coords
                personal_target = self.server.db.mine_tunnel_target_v1251(
                    self.account_id, floor, x, y, direction)
            target = personal_target or ROOMS[self.character.room_id]["exits"].get(direction)
            if not target:
                await self.send("Nie możesz iść w tym kierunku.")
                return
            self.server.world.ensure_runtime_room(target)
            if (ROOMS.get(self.character.room_id, {}).get("v1190_secret_role") == "chamber"
                    and direction == "east"
                    and any(bool(MOB_TEMPLATES.get(m.template_id, {}).get("v1190_secret_guard"))
                            for m in self.server.world.room_mobs(self.character.room_id))):
                await self.send("Przejścia do Archiwum Szeptów pilnuje strażnik. Najpierw go pokonaj.")
                return

            if self.uoss_deep_dungeon_descent_blocked_v11331(
                self.character.room_id, direction
            ):
                floor = uoss_deep_dungeon_floor_number_v11331(
                    self.character.room_id
                )
                await self.send(
                    f"Nie możesz zejść niżej z piętra {floor}. "
                    "Apanda tego progu nie została jeszcze zaliczona przez ciebie."
                )
                return

            serpentarius_error = (
                self.uoss_serpentarius_room_entry_error_v11331(target)
            )
            if serpentarius_error:
                await self.send(serpentarius_error)
                return

            target_room = ROOMS.get(target, {})
            if target_room.get("requires_ship"):
                party_ship = getattr(self, "_party_ship_passage_v10014", None) or {}
                using_party_ship = bool(party_ship)
                if not using_party_ship and (
                    not hasattr(self, "ocean_ship_owned_v1000")
                    or not self.ocean_ship_owned_v1000()
                ):
                    await self.send("Na ten morski szlak potrzebujesz własnego statku albo musisz płynąć z liderem drużyny stojącym obok.")
                    return
                req_nav = int(target_room.get("ocean_navigation_required", 1) or 1)
                req_hull = int(target_room.get("ocean_hull_required", 1) or 1)
                nav_level = (
                    int(party_ship.get("navigation", 0))
                    if using_party_ship
                    else self.ocean_ship_level_v1000("navigation")
                )
                hull_level = (
                    int(party_ship.get("hull", 0))
                    if using_party_ship
                    else self.ocean_ship_level_v1000("hull")
                )
                if nav_level < req_nav or hull_level < req_hull:
                    await self.send(f"Ten sektor wymaga Nawigacji {req_nav} i Kadłuba {req_hull}.")
                    return
            elif target_room.get("underwater") and hasattr(self, "ocean_ship_level_v1000"):
                req_hull = int(target_room.get("ocean_hull_required", 1) or 1)
                if not self.ocean_ship_owned_v1000() or self.ocean_ship_level_v1000("hull") < req_hull:
                    await self.send(f"Zejście do tych podwodnych ruin wymaga statku z Kadłubem {req_hull}+.")
                    return
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
                    f"Docelowy poziom około {target_danger}/{CHARACTER_MAX_LEVEL}, "
                    f"twoja siła około {player_power}/{CHARACTER_MAX_LEVEL}. "
                    f"Ocena: {v0866_threat_label(target_danger, player_power)}."
                )

            await self.walk_room_transition(
                direction, target, guided=False, show_room=True
            )
