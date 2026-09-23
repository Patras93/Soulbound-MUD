# -*- coding: utf-8 -*-
"""Movement and dungeon exit routing."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import asyncio
import sys
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
from systems.content_registry import MOB_TEMPLATES
from systems.dungeons_regions import (
    ASTRAL_MIN_SOUL_LEVEL,
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
            entry_label_v03812 = (
                str(getattr(self, "_dungeon_entry_label_v03812", "") or "").strip()
                if not guided else ""
            )

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
                    if entry_label_v03812:
                        await member.send(
                            f"Podążasz za liderem {self.character.name} do: {entry_label_v03812}."
                        )
                        member._dungeon_entry_label_v03812 = entry_label_v03812
                    else:
                        await member.send(
                            f"Podążasz za liderem {self.character.name}: {label}."
                        )
                    try:
                        await member.move(direction)
                    finally:
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
                city_name_v0530 = COURIER_CITY_ROOM_TO_NAME_V0530.get(str(target))
                if city_name_v0530 and self.account_id is not None:
                    self.server.db.record_courier_city_visit_v0530(self.account_id, city_name_v0530)
                await self.server.broadcast_room(
                    target, f"{self.character.name} przychodzi.", exclude=self
                )
                if entry_label_v03812:
                    await self.send(f"WEJŚCIE: {target_name}.")
                else:
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
                    f"Docelowy poziom około {target_danger}/{CHARACTER_MAX_LEVEL}, "
                    f"twoja siła około {player_power}/{CHARACTER_MAX_LEVEL}. "
                    f"Ocena: {v0866_threat_label(target_danger, player_power)}."
                )

            await self.walk_room_transition(
                direction, target, guided=False, show_room=True
            )
