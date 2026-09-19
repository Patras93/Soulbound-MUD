# -*- coding: utf-8 -*-
"""Soulbound v0.30.47 Session mixin: core_progression."""

class SessionCoreProgressionMixin:
    def __init__(self, server, reader, writer):
            self.server = server
            self.reader = reader
            self.writer = writer
            self.input_encoding = DEFAULT_TEXT_ENCODING
            self.output_encoding = DEFAULT_TEXT_ENCODING
            self.master_account_id = None
            # account_id pozostaje identyfikatorem aktywnej postaci, aby wszystkie
            # istniejące systemy zapisu nadal działały bez mieszania slotów.
            self.account_id = None
            self.character = None
            self.closed = False
            self.current_hp = 0
            self.current_mana = 0
            self.combat_mob_key = None
            # v0.8.34: walka działa w czasie rzeczywistym. Jedno zadanie asyncio
            # prowadzi niezależne timery akcji gracza i przeciwnika.
            self.combat_task = None
            self.combat_player_interval = 1.35
            self.combat_enemy_interval = 1.85
            # v0.8.36: w trybie concise ostrzegamy tylko przy przekraczaniu
            # ważnych progów HP, zamiast czytać każde zwykłe trafienie.
            self.combat_hp_warn_level = 0
            self.last_profession_action = 0.0
            # v0.30.7: warunki zbierania (w tym pogoda/pora) są ogłaszane
            # tylko przy zmianie. Auto-zbieranie nie spamuje NVDA tym samym
            # komunikatem po każdym cyklu profesji.
            self.last_gather_feature_signature = None
            self.auto_fishing = False
            self.auto_fishing_task = None
            self.auto_mining = False
            self.auto_mining_task = None
            self.auto_woodcutting = False
            self.auto_woodcutting_task = None
            self.auto_herbalism = False
            self.auto_herbalism_task = None
            self.guiding = False
            self.guide_choice_state = None
            # v0.23.0: numerowany wybór przy niejednoznacznej sprzedaży pojedynczego EQ/przedmiotu.
            self.sell_choice_state = None
            # v0.8.57: prowadzenie jest osobnym zadaniem asyncio. Dzięki temu
            # gracz może odpytać status, zaplanować trasę lub przerwać marsz
            # bez czekania na zakończenie całej automatycznej podróży.
            self.guide_task = None
            self.guide_target_room = None
            self.guide_target_label = ""
            self.guide_target_is_npc = False
            self.guide_final_direction = None
            self.route_target_room = None
            self.route_target_label = ""
            self.route_target_is_npc = False
            # v0.8.56: normalny ruch ma zauważalny etap chodzenia.
            self.moving = False
            # v0.8.32: ostatnia numerowana lista questów: aktywne, ukończone lub NPC.
            # Dzięki temu quest info <numer> działa po każdej z tych list.
            self.quest_list_context = None
            self.skill_cooldowns = {}
            self.skill_guard = 0
            self.skill_evade = False
            # v0.8.64: wszystkie gwarantowane uniki dzielą krótki lockout po
            # zużyciu, żeby Łotrzyk/Łowca nie rotowali kilku evade w nietykalność.
            self.skill_evade_lockout_until = 0.0
            # v0.8.45: każdy skill typu boost jest czasowym, uniwersalnym buffem.
            # Aktywne buffy wzmacniają wszystkie skille i spelle o mierzalnej sile
            # (obrażenia, leczenie i guard), także przy multiclassie.
            self.active_skill_buffs = {}
            self._party_auto_heal_busy = False
            # v0.8.26: automatyczna rotacja dwóch kolejek skilli.
            # Konfiguracja kolejki jest trwała w SQLite, a kursory rotacji są sesyjne.
            self.skill_queue_cursors = {"physical": 0, "magic": 0}
            self.skill_queue_next_type = "physical"
            self.auto_queue_casting = False
            self.resting = False
            self.rest_task = None
            # Ostatnia zwykła lokacja do komendy cofnij/back.
            self.previous_room_id = None
            # v0.9.28: ostatni nadawca prywatnej wiadomości dla reply/odpisz.
            self.last_private_sender_account_id = None
            self.last_private_sender_name = None
            # v0.30.11: sesyjne bufory historii przyjazne NVDA.
            self.history_sequence = 0
            self.history_buffers = {
                key: deque(maxlen=HISTORY_BUFFER_LIMIT)
                for key in ("xp", "loot", "quest", "system", "chat", "party", "tell", "combat")
            }
            self.history_replaying = False

    def double_xp_state(self, now=None):
            return double_xp_event_state(now)

    def apply_double_xp(self, amount, now=None):
            amount = max(0, int(amount or 0))
            state = self.double_xp_state(now)
            return min(V019_SAFE_INT, amount * int(state["multiplier"]))

    def add_character_xp_with_event(self, amount):
            return self.character.add_character_xp(self.apply_double_xp(amount))

    async def show_double_xp_event(self):
            state = self.double_xp_state()
            if state["active"]:
                await self.send(
                    "EVENT x2 EXP AKTYWNY. Pozostało "
                    + self.format_duration_short(state["remaining_seconds"])
                    + ". Wszystkie główne rodzaje EXP są podwajane."
                )
            else:
                await self.send(
                    "EVENT x2 EXP: następny start za "
                    + self.format_duration_short(state["next_start_seconds"])
                    + ". Event trwa 15 minut i uruchamia się na początku każdej godziny."
                )

    async def handle_wimpy(self, raw=""):
            value = self.normalize_description_query(str(raw or "").strip())
            current = self.server.db.wimpy_percent(self.account_id)
            if not value or value in ("status", "show", "pokaz", "pokaż"):
                if current <= 0:
                    await self.send("WIMPY jest wyłączone. Użycie: wimpy set 50.")
                else:
                    await self.send(
                        f"WIMPY: {current} procent. Automatyczna ucieczka uruchamia się, "
                        f"gdy HP spadnie do {current} procent lub niżej."
                    )
                return
            for prefix in ("set ", "ustaw "):
                if value.startswith(prefix):
                    value = value[len(prefix):].strip()
                    break
            if value in ("off", "wylacz", "wyłącz", "disable", "0"):
                self.server.db.set_wimpy_percent(self.account_id, 0)
                await self.send("WIMPY wyłączone.")
                return
            try:
                percent = int(value)
            except (TypeError, ValueError):
                await self.send("Użycie: wimpy set <1-99>, wimpy off albo wimpy status.")
                return
            if percent < 1 or percent > 99:
                await self.send("WIMPY musi mieć wartość od 1 do 99 procent. 0 lub off wyłącza system.")
                return
            self.server.db.set_wimpy_percent(self.account_id, percent)
            await self.send(
                f"WIMPY ustawione na {percent} procent. Automatycznie uciekniesz, "
                f"gdy HP spadnie do {percent} procent lub niżej."
            )

    async def maybe_auto_wimpy(self):
            if not self.combat_mob_key or self.current_hp <= 0:
                return False
            percent = self.server.db.wimpy_percent(self.account_id)
            if percent <= 0:
                return False
            hp_percent = (max(0, self.current_hp) * 100.0) / max(1, self.max_hp())
            if hp_percent > percent:
                return False
            await self.send(
                f"WIMPY: HP spadło do {int(round(hp_percent))} procent. Automatyczna ucieczka."
            )
            await self.flee()
            return True

    async def teleport_to_temple_command(self):
            if not self.character:
                return
            if self.guide_task_active():
                await self.cancel_guide(announce=False)
            if self.resting or self.rest_task:
                await self.stop_rest(announce=False)
            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)
            if self.combat_mob_key:
                await self.flee()
            old_room = self.character.room_id
            if old_room == "temple":
                await self.send("Już jesteś w Świątyni Odrodzenia.")
                return
            self.previous_room_id = old_room
            self.character.room_id = "temple"
            self.server.db.save_character(self.character)
            await self.server.broadcast_room(
                old_room, f"{self.character.name} znika w świetle Świątyni.", exclude=self
            )
            await self.server.broadcast_room(
                "temple", f"{self.character.name} pojawia się w Świątyni Odrodzenia.", exclude=self
            )
            await self.send("Teleportujesz się do Świątyni Odrodzenia.")
            await self.look()

    def mine_progress(self):
            return self.server.db.mine_progress(self.account_id)

    def mine_descent_blocked_for_player(self, room_id, direction="down"):
            if direction != "down":
                return False
            floor = mine_floor_number(room_id)
            if floor is None:
                return False
            return (
                floor + 1
                > self.mine_progress()["max_floor_unlocked"]
            )

    async def auto_mine_descend_if_unlocked(self):
            if not self.auto_mining or self.closed:
                return False
            if self.combat_mob_key:
                return False

            current_room = self.character.room_id

            # v0.24.4: auto-kopanie potrafi wejść do Kopalni Głębinowej z całej
            # ręcznej części jaskini zamiast bez końca kopać przy wejściu.
            approach_steps = {
                "cave_entrance": ("down", "cave_tunnel"),
                "cave_tunnel": ("east", "crystal_chamber"),
                "crystal_chamber": ("down", mine_floor_id(MINE_MIN_FLOOR)),
            }
            if current_room in approach_steps:
                direction, target = approach_steps[current_room]
                if target.startswith("mine_floor_"):
                    self.server.world.ensure_infinite_dungeon_floor(target)
                if ROOMS.get(current_room, {}).get("exits", {}).get(direction) != target:
                    ROOMS[current_room].setdefault("exits", {})[direction] = target
                old = current_room
                self.previous_room_id = old
                await self.server.broadcast_room(old, f"{self.character.name} odchodzi.", exclude=self)
                self.character.room_id = target
                self.server.db.save_character(self.character)
                await self.discover_room(target, announce=False)
                await self.server.broadcast_room(target, f"{self.character.name} przychodzi.", exclude=self)
                await self.send(f"Auto-kopanie schodzi głębiej: {ROOMS[target]['name']}.")
                return True

            floor = mine_floor_number(current_room)
            if floor is None:
                return False

            expected_target = mine_floor_id(floor + 1)
            self.server.world.ensure_infinite_dungeon_floor(expected_target)
            # Napraw stare runtime-roomy/zapisy, którym brakowało wyjścia down.
            ROOMS[current_room].setdefault("exits", {})["down"] = expected_target
            target = ROOMS[current_room]["exits"].get("down")

            if target != expected_target:
                return False

            progress = self.mine_progress()
            if progress["max_floor_unlocked"] < floor + 1:
                return False

            if self.mine_descent_blocked_for_player(
                current_room,
                "down",
            ):
                return False

            old = current_room
            self.previous_room_id = old
            await self.server.broadcast_room(
                old,
                f"{self.character.name} odchodzi.",
                exclude=self,
            )

            self.character.room_id = target
            self.server.db.save_character(
                self.character
            )
            await self.discover_room(target, announce=False)

            await self.server.broadcast_room(
                target,
                f"{self.character.name} przychodzi.",
                exclude=self,
            )

            await self.send(
                f"Ściana w dół jest przebita. "
                f"Auto-kopanie schodzi na poziom {floor + 1}."
            )
            return True

    def nearest_auto_target(self, route):
            best = None
            best_len = None
            for room_id in route:
                path = self.shortest_path(
                    self.character.room_id, room_id
                )
                if path is None:
                    continue
                if best is None or len(path) < best_len:
                    best = room_id
                    best_len = len(path)
            return best

    def next_auto_target(self, route):
            current = self.character.room_id
            dungeon, _floor = profession_dungeon_floor(current)
            if dungeon in {
                "sunken_grotto", "ancient_forest", "alchemy_garden"
            }:
                return current
            if current not in route:
                return self.nearest_auto_target(route)
            index = route.index(current)
            return route[(index + 1) % len(route)]

    async def auto_walk_to_target(self, target, label, flag_attr):
            path = self.shortest_path(
                self.character.room_id, target
            )
            if path is None:
                await self.send(
                    f"{label}: nie udało się znaleźć drogi."
                )
                return False

            for direction, next_room in path:
                if self.closed or not getattr(self, flag_attr, False):
                    return False
                if self.combat_mob_key:
                    await self.send(
                        f"{label} zatrzymane: rozpoczęła się walka."
                    )
                    return False
                if self.mythic_entry_error(next_room):
                    return False
                if self.profession_dungeon_access_error(next_room):
                    return False
                if self.astral_entry_blocked(next_room):
                    return False
                if self.mythic_crypt_descent_blocked_for_player(
                    self.character.room_id, direction
                ):
                    return False
                if self.mythic_astral_ascent_blocked_for_player(
                    self.character.room_id, direction
                ):
                    return False
                if self.giant_fortress_ascent_blocked_for_player(
                    self.character.room_id, direction
                ):
                    return False
                if self.crypt_descent_blocked_for_player(
                    self.character.room_id, direction
                ):
                    return False
                if self.astral_ascent_blocked_for_player(
                    self.character.room_id, direction
                ):
                    return False
                if self.mine_descent_blocked_for_player(
                    self.character.room_id, direction
                ):
                    await self.send(
                        f"{label}: ściana kopalni blokuje zejście."
                    )
                    return False

                old = self.character.room_id
                await self.server.broadcast_room(
                    old,
                    f"{self.character.name} odchodzi.",
                    exclude=self,
                )
                self.character.room_id = next_room
                self.server.db.save_character(self.character)
                await self.discover_room(next_room, announce=False)
                await self.server.broadcast_room(
                    next_room,
                    f"{self.character.name} przychodzi.",
                    exclude=self,
                )
                await self.send(
                    f"{label}: {direction} -> "
                    f"{ROOMS[next_room]['name']}."
                )
                await asyncio.sleep(0.12)

            return self.character.room_id == target

    async def show_mine_info(self):
            """Czytelny status Kopalni Głębinowej dla NVDA."""
            progress = self.mine_progress()
            room_id = self.character.room_id
            floor = mine_floor_number(room_id)
            approach_names = {
                "cave_entrance": "Wejście do Kopalni Głębinowej — przed poziomem 1",
                "cave_tunnel": "Tunel Kryształowej Jaskini — droga do poziomu 1",
                "crystal_chamber": "Komnata Kryształowa — bezpośrednio przed poziomem 1",
            }

            await self.send("KOPALNIA GŁĘBINOWA")
            if floor is not None:
                await self.send(f"Położenie: poziom {floor}.")
            elif room_id in approach_names:
                await self.send(f"Położenie: {approach_names[room_id]}.")
            else:
                room_name = ROOMS.get(room_id, {}).get("name", "nieznana lokacja")
                await self.send(
                    f"Położenie: {room_name}. Nie jesteś teraz w Kopalni Głębinowej. "
                    "Użyj: prowadz kopalnia."
                )

            max_floor = int(progress["max_floor_unlocked"])
            await self.send(
                f"Najgłębiej odblokowany poziom: {max_floor}. "
                "Kopalnia nie ma górnego limitu pięter; moc zasobów skaluje się do progresji 400."
            )

            if floor is not None:
                if floor == max_floor:
                    hits = int(progress["wall_hits"])
                    required = int(progress["wall_required_hits"])
                    missing = max(0, required - hits)
                    await self.send(
                        f"Ściana do poziomu {floor + 1}: {hits}/{required} uderzeń. "
                        f"Brakuje {missing}."
                    )
                elif floor < max_floor:
                    await self.send(
                        f"Zejście do poziomu {floor + 1} jest już odblokowane."
                    )
                else:
                    await self.send(
                        "Uwaga: jesteś głębiej niż zapisany postęp odblokowania; "
                        "użyj ruchu w górę albo zaloguj się ponownie, jeśli to stary zapis."
                    )

            auto_text = "włączone" if self.auto_mining else "wyłączone"
            await self.send(f"Auto-kopanie: {auto_text}.")

            try:
                profession_level = int(self.profession_level_for_tool("mining"))
            except Exception:
                profession_level = 1
            try:
                tool_level = int(self.server.db.tool(self.account_id, "mining")["level"])
            except Exception:
                tool_level = 1
            await self.send(
                f"Górnictwo: {profession_level}/400. Kilof: {tool_level}/400."
            )

            # W Kopalni Głębinowej ruda wymaga jednocześnie odpowiedniego Kilofa
            # i głębokości. Pokazujemy kilka najwyższych spełnionych progów zamiast
            # zalewać czytnik ekranu całą tabelą atlasu.
            if floor is not None:
                eligible = []
                for item_id in ORE_ATLAS_ALL:
                    if item_id not in ITEMS:
                        continue
                    need_tool = int(ORE_ATLAS_LEVELS.get(item_id, 1))
                    need_floor = int(ORE_MINE_FLOOR_MINIMUMS.get(item_id, 1))
                    if tool_level >= need_tool and floor >= need_floor:
                        eligible.append((max(need_tool, need_floor), need_tool, need_floor, item_id))
                eligible.sort(key=lambda row: (row[0], row[1], row[2], ITEMS[row[3]].get("name", row[3])))
                best = eligible[-5:]
                if best:
                    await self.send(
                        "Najwyższe dostępne rudy przy tym Kilofie i piętrze: "
                        + ", ".join(ITEMS[item_id].get("name", item_id) for *_rest, item_id in best)
                        + "."
                    )

                future = []
                for item_id in ORE_ATLAS_ALL:
                    if item_id not in ITEMS:
                        continue
                    need_tool = int(ORE_ATLAS_LEVELS.get(item_id, 1))
                    need_floor = int(ORE_MINE_FLOOR_MINIMUMS.get(item_id, 1))
                    if need_tool > tool_level or need_floor > floor:
                        distance = max(0, need_tool - tool_level) + max(0, need_floor - floor)
                        future.append((distance, max(need_tool, need_floor), item_id, need_tool, need_floor))
                if future:
                    future.sort(key=lambda row: (row[0], row[1], ITEMS[row[2]].get("name", row[2])))
                    _distance, _rank, item_id, need_tool, need_floor = future[0]
                    await self.send(
                        f"Najbliższy kolejny próg rudy: {ITEMS[item_id].get('name', item_id)} — "
                        f"Kilof {need_tool}, poziom kopalni {need_floor}."
                    )

            if self.auto_mining:
                if floor is None and room_id in approach_names:
                    await self.send(
                        "Auto-kopanie samo przejdzie do poziomu 1 i będzie schodzić po przebiciu kolejnych ścian."
                    )
                elif floor is not None:
                    await self.send(
                        "Auto-kopanie po przebiciu ściany automatycznie schodzi na następny odblokowany poziom."
                    )
            else:
                await self.send("Włącz auto-kopanie komendą: kop on.")

    def mythic_entry_error(self, target_room):
            # v0.9.12: Mityczna Krypta jest zawsze dostępna; trudność, nie level,
            # jest barierą wejścia. Mityczna Wieża Astralna zachowuje własną zasadę.
            if target_room == "mythic_astral_gate":
                if self.character.soul_level < MYTHIC_ASTRAL_MIN_SOUL_LEVEL:
                    return (
                        "Mityczna Wieża Astralna jest zablokowana. "
                        f"Wymaga Soul Level {MYTHIC_ASTRAL_MIN_SOUL_LEVEL}. "
                        f"Masz Soul Level {self.character.soul_level}."
                    )

            return None

    def profession_dungeon_access_error(self, target_room):
            dungeon, floor = profession_dungeon_floor(target_room)
            if not dungeon:
                return None
            if dungeon == "crystal_mine":
                # v0.25.1: to już zwykłe Kryształowe Groty, nie loch Górnictwa.
                return None

            tool_type, item_id, tool_name = PROF_DUNGEON_TOOL[dungeon]
            if self.server.db.item_qty(self.account_id, item_id) <= 0:
                return (
                    f"Ten loch profesyjny wymaga narzędzia: {tool_name}."
                )

            profession = profession_for_tool_type(tool_type)
            prow = self.server.db.profession(self.account_id, profession)
            profession_level = int(prow["level"])
            required = profession_dungeon_required_tool_level(floor)
            if profession_level < required:
                return (
                    f"Ten poziom lochu profesyjnego wymaga "
                    f"{profession} level {required}. Masz level {profession_level}. "
                    f"Level {tool_name} nie blokuje piętra; odblokowuje lepsze surowce."
                )
            return None

    def giant_fortress_ascent_blocked_for_player(
            self, room_id, direction="up"
        ):
            floor = giant_fortress_floor_number(room_id)
            if floor is not None and self.server.db.boss_floor_cleared(self.account_id, "giant", floor):
                return False
            return self.server.world.giant_fortress_ascent_blocked(room_id, direction)

    def mythic_crypt_descent_blocked_for_player(
            self, room_id, direction="down"
        ):
            floor = mythic_crypt_floor_number(room_id)
            if floor is not None and self.server.db.boss_floor_cleared(self.account_id, "mythic_crypt", floor):
                return False
            return self.server.world.mythic_crypt_descent_blocked(room_id, direction)

    def mythic_astral_ascent_blocked_for_player(
            self, room_id, direction="up"
        ):
            floor = mythic_astral_floor_number(room_id)
            if floor is not None and self.server.db.boss_floor_cleared(self.account_id, "mythic_astral", floor):
                return False
            return self.server.world.mythic_astral_ascent_blocked(room_id, direction)

    def crypt_portal(self):
            return self.server.db.crypt_portal(self.account_id)

    def crypt_portal_floors(self):
            highest = max(0, int(self.crypt_portal()))
            return list(range(10, highest + 1, 10))

    def crypt_descent_blocked_for_player(self, room_id, direction="down"):
            floor = crypt_floor_number(room_id)
            if floor is not None and self.server.db.boss_floor_cleared(self.account_id, "crypt", floor):
                return False
            return self.server.world.crypt_descent_blocked(room_id, direction)

    def astral_portal(self):
            return self.server.db.astral_portal(self.account_id)

    def astral_portal_floors(self):
            highest = max(0, int(self.astral_portal()))
            if highest < ASTRAL_MIN_FLOOR:
                return []
            return list(range(ASTRAL_MIN_FLOOR, highest + 1, 10))

    def astral_ascent_blocked_for_player(self, room_id, direction="up"):
            floor = astral_floor_number(room_id)
            if floor is not None and self.server.db.boss_floor_cleared(self.account_id, "astral", floor):
                return False
            return self.server.world.astral_ascent_blocked(room_id, direction)

    def astral_entry_blocked(self, target_room):
            return (
                target_room == astral_floor_id(ASTRAL_MIN_FLOOR)
                and self.character.soul_level < ASTRAL_MIN_SOUL_LEVEL
            )

    async def grant_combat_quest_stat_xp(self, raw_reward, repeatable=False, source_label="Quest walki"):
            """Przyznaje EXP do każdej z sześciu statystyk z systemu questowego."""
            raw_reward = max(0, int(raw_reward or 0))
            if raw_reward <= 0:
                return []
            applied = []
            for stat_name in self.character.STAT_PROGRESS_FIELDS:
                granted = v0874_quest_stat_progress_base_grant(
                    self.character, stat_name, raw_reward, repeatable
                )
                granted = self.apply_double_xp(granted)
                applied.append(granted)
                for msg in self.character.add_stat_progress(granted, targets=(stat_name,)):
                    await self.send(msg)
            lo = min(applied) if applied else 0
            hi = max(applied) if applied else 0
            amount_text = str(lo) if lo == hi else f"{lo}-{hi}"
            await self.send(
                f"{source_label}: {amount_text} EXP osobno do Siły, Zręczności, "
                "Kondycji, Inteligencji, Siły Woli i Charyzmy."
            )
            return applied

    async def grant_soul_xp(self, amount):
            old_level = self.character.soul_level
            amount = self.apply_double_xp(amount)

            messages = self.character.add_soul_xp(amount)
            for message in messages:
                await self.send(message)

            await self.set_achievement_progress("soul_level", self.character.soul_level)

            if self.character.soul_level > old_level:
                self.current_hp = self.max_hp()
                await self.send(
                    f"Awans Soul Level odnawia całe HP. "
                    f"HP: {self.current_hp} z {self.max_hp()}."
                )

            return self.character.soul_level > old_level

    async def show_astral_portal_status(self):
            if self.character.soul_level < ASTRAL_MIN_SOUL_LEVEL:
                await self.send(
                    f"Wieża Astralna wymaga Soul Level {ASTRAL_MIN_SOUL_LEVEL}. "
                    f"Masz Soul Level {self.character.soul_level}."
                )
                return

            highest = self.astral_portal()
            unlocked = self.astral_portal_floors()
            if not highest:
                await self.send(
                    "Astralny Portal nie ma jeszcze odblokowanych checkpointów. "
                    "Pokonaj Strażnika Gwiezdnej Bramy na poziomie 100."
                )
                return

            await self.send(
                f"Najwyższy checkpoint Wieży Astralnej: poziom {highest}."
            )
            await self.send(
                "Odblokowane Astralne Portale: "
                + ", ".join(str(floor) for floor in unlocked)
                + "."
            )
            await self.send(
                "Użycie: astralportal <100/110/120/... bez górnego limitu>. "
                "Portal uruchamia się przy Astralnej Bramie."
            )

    async def use_astral_portal(self, raw):
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz użyć Astralnego Portalu podczas walki."
                )
                return

            if self.character.soul_level < ASTRAL_MIN_SOUL_LEVEL:
                await self.send(
                    f"Wieża Astralna wymaga Soul Level {ASTRAL_MIN_SOUL_LEVEL}. "
                    f"Masz {self.character.soul_level}."
                )
                return

            value = self.normalize_room_query(raw)
            if not value or value in ("status", "lista", "list"):
                await self.show_astral_portal_status()
                return

            match = re.search(r"(\d+)", value)
            if not match:
                await self.send(
                    "Użycie: astralportal 100, 110, 120, ... bez górnego limitu."
                )
                return

            floor = int(match.group(1))
            if not is_astral_boss_floor(floor):
                await self.send(
                    f"Checkpointy Wieży są co 10 poziomów od {ASTRAL_MIN_FLOOR} bez górnego limitu."
                )
                return

            highest = self.astral_portal()
            if floor > highest:
                await self.send(
                    f"Checkpoint poziomu {floor} jest zablokowany. "
                    f"Najwyższy odblokowany: {highest if highest else 'brak'}."
                )
                return

            if self.character.room_id != "astral_gate":
                await self.send(
                    "Astralny Portal działa tylko przy Astralnej Bramie. "
                    "Wpisz prowadz wieza astralna."
                )
                return

            target = astral_floor_id(floor)
            self.server.world.ensure_infinite_dungeon_floor(target)
            old = self.character.room_id
            await self.server.broadcast_room(
                old,
                f"{self.character.name} wchodzi w Astralny Portal.",
                exclude=self,
            )
            self.character.room_id = target
            self.server.db.save_character(self.character)
            await self.server.broadcast_room(
                target,
                f"{self.character.name} wychodzi z Astralnego Portalu.",
                exclude=self,
            )
            await self.send(
                f"Astralny Portal przenosi cię na poziom {floor}."
            )
            await self.look()

    async def show_portal_status(self):
            highest = self.crypt_portal()
            unlocked = self.crypt_portal_floors()
            if not unlocked:
                await self.send(
                    "Portale Krypty: brak. "
                    "Pokonaj bossa piętra 10, aby odblokować pierwszy portal."
                )
                return

            await self.send(
                f"Najwyższy odblokowany Portal Krypty: piętro {highest}."
            )
            await self.send(
                "Odblokowane Portale Krypty: "
                + ", ".join(str(floor) for floor in unlocked)
                + "."
            )
            await self.send(
                "Użycie: portal <10/20/30/...>. "
                "Portal można uruchomić w Sali Krypty albo w Przedsionku Krypty."
            )

    async def use_crypt_portal(self, raw):
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz użyć Portalu Krypty podczas walki."
                )
                return

            value = self.normalize_room_query(raw)
            if not value or value in ("status", "lista", "list"):
                await self.show_portal_status()
                return

            match = re.search(r"(\d+)", value)
            if not match:
                await self.send(
                    "Użycie: portal 10, portal 20, portal 30, ... bez górnego limitu."
                )
                return

            floor = int(match.group(1))
            if not is_crypt_boss_floor(floor):
                await self.send(
                    "Portale są co 10 pięter: 10, 20, 30, ... bez górnego limitu."
                )
                return

            highest = self.crypt_portal()
            if floor > highest:
                await self.send(
                    f"Portal piętra {floor} jest jeszcze zablokowany. "
                    f"Najwyższy odblokowany portal: "
                    f"{highest if highest else 'brak'}."
                )
                return

            if self.character.room_id not in ("crypt_hall", "crypt_entrance"):
                await self.send(
                    "Portal Krypty można uruchomić tylko w Sali Krypty "
                    "albo w Przedsionku Krypty. Użyj prowadz Sala Krypty."
                )
                return

            if self.resting or self.rest_task:
                await self.stop_rest(announce=False)
            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)

            target = crypt_floor_id(floor)
            self.server.world.ensure_infinite_dungeon_floor(target)
            old = self.character.room_id

            await self.server.broadcast_room(
                old,
                f"{self.character.name} wchodzi w Portal Krypty.",
                exclude=self,
            )
            self.character.room_id = target
            self.server.db.save_character(self.character)
            await self.server.broadcast_room(
                target,
                f"{self.character.name} wychodzi z Portalu Krypty.",
                exclude=self,
            )
            await self.send(
                f"Portal Krypty przenosi cię na piętro {floor}."
            )
            await self.look()

    def rest_status_text(self):
            if not self.character:
                return "Brak postaci."
            max_hp = self.max_hp()
            max_mana = self.max_mana()
            if max_mana > 0:
                return (
                    f"HP {self.current_hp} z {max_hp}. "
                    f"Mana {self.current_mana} z {max_mana}. "
                    f"Odpoczynek: {'aktywny' if self.resting else 'wyłączony'}."
                )
            return (
                f"HP {self.current_hp} z {max_hp}. "
                f"Odpoczynek: {'aktywny' if self.resting else 'wyłączony'}."
            )

    def rest_needs_regeneration(self):
            if not self.character:
                return False

            if self.current_hp < self.max_hp():
                return True

            max_mana = self.max_mana()
            return (
                max_mana > 0
                and self.current_mana < max_mana
            )

    async def rest_tick(self):
            if not self.character:
                return False

            max_hp = self.max_hp()
            max_mana = self.max_mana()

            hp_before = self.current_hp
            mana_before = self.current_mana

            hp_gain = max(
                1,
                (max_hp * REST_REGEN_PERCENT + 99) // 100,
            )
            self.current_hp = min(
                max_hp,
                self.current_hp + hp_gain,
            )

            if max_mana > 0:
                mana_gain = max(
                    1,
                    (max_mana * REST_REGEN_PERCENT + 99) // 100,
                )
                self.current_mana = min(
                    max_mana,
                    self.current_mana + mana_gain,
                )
            else:
                self.current_mana = 0

            if (
                self.current_hp != hp_before
                or self.current_mana != mana_before
            ):
                if max_mana > 0:
                    await self.send(
                        f"Regeneracja: HP {self.current_hp} z {max_hp}. "
                        f"Mana {self.current_mana} z {max_mana}."
                    )
                else:
                    await self.send(
                        f"Regeneracja: HP {self.current_hp} z {max_hp}."
                    )

            return self.rest_needs_regeneration()

    async def rest_loop(self):
            try:
                while self.resting and not self.closed:
                    await asyncio.sleep(REST_TICK_SECONDS)

                    if (
                        not self.resting
                        or self.closed
                        or self.combat_mob_key
                    ):
                        break

                    needs_more = await self.rest_tick()
                    if not needs_more:
                        self.resting = False
                        await self.send(
                            "Odpoczynek zakończony. "
                            "HP i Mana są pełne."
                        )
                        break
            except asyncio.CancelledError:
                pass
            finally:
                self.resting = False
                if self.rest_task is asyncio.current_task():
                    self.rest_task = None

    async def stop_rest(self, announce=True, reason=None):
            was_resting = self.resting or (
                self.rest_task is not None
                and not self.rest_task.done()
            )

            self.resting = False
            task = self.rest_task
            self.rest_task = None

            if (
                task
                and task is not asyncio.current_task()
                and not task.done()
            ):
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            if announce and was_resting:
                if reason:
                    await self.send(
                        f"Odpoczynek przerwany: {reason}."
                    )
                else:
                    await self.send(
                        "Odpoczynek przerwany."
                    )

            return was_resting

    async def start_rest(self):
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz odpoczywać podczas walki. "
                    "Najpierw pokonaj przeciwnika albo użyj flee."
                )
                return

            if self.resting:
                await self.send(self.rest_status_text())
                return

            if not self.rest_needs_regeneration():
                await self.send(
                    "Nie musisz odpoczywać. "
                    "HP i Mana są już pełne."
                )
                return

            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)

            self.resting = True
            self.rest_task = asyncio.create_task(
                self.rest_loop()
            )

            await self.send(
                "Rozpoczynasz odpoczynek. "
                "Co 5 sekund regenerujesz HP i Manę."
            )
            await self.send(self.rest_status_text())

    async def start_mana_regen(self):
            # v0.6.84: nie ma już osobnego trybu tylko Many.
            # Każdy regen prowadzi do pełnego odpoczynku HP + Mana.
            await self.start_rest()

    async def handle_mana_command(self, raw):
            action = normalize_lookup_text(raw)

            if action in ("", "status", "stan"):
                await self.send(
                    f"Mana: {self.current_mana} z {self.max_mana()}."
                )
                if self.resting:
                    await self.send(
                        "Odpoczynek: włączony. "
                        "Regenerujesz HP i Manę."
                    )
                return

            if action in (
                "regen",
                "regeneruj",
                "on",
                "start",
            ):
                await self.start_rest()
                return

            if action in (
                "off",
                "stop",
                "koniec",
                "przerwij",
            ):
                if not await self.stop_rest(announce=True):
                    await self.send(
                        "Odpoczynek nie jest włączony."
                    )
                return

            await self.send(
                "Użycie: mana, mana regen, mana stop. "
                "Mana regen uruchamia pełny odpoczynek HP i Many."
            )

    async def handle_rest(self, raw):
            action = normalize_lookup_text(raw)

            if action in ("status", "stan"):
                await self.send(self.rest_status_text())
                return

            # regen mana i odpoczywaj mana również regenerują wszystko.
            if action in (
                "mana",
                "mana on",
                "mana start",
                "mana regen",
            ):
                await self.start_rest()
                return

            if action in (
                "mana off",
                "mana stop",
                "off",
                "stop",
                "koniec",
                "przerwij",
            ):
                if not await self.stop_rest(announce=True):
                    await self.send("Nie odpoczywasz.")
                return

            if action in ("", "on", "start"):
                await self.start_rest()
                return

            await self.send(
                "Użycie: odpoczywaj, regen, regen mana, "
                "odpoczywaj status, odpoczywaj stop."
            )

    def refresh_active_classes(self):
            if not self.character or not self.account_id:
                return []
            names = self.server.db.active_class_names(
                self.account_id, self.character.class_name
            )
            self.character._active_classes = list(names)
            return list(names)

    def active_class_names(self):
            self.refresh_active_classes()
            return self.character.active_class_names()

    def find_class_name(self, query):
            wanted = self.normalize_description_query(query)
            if not wanted:
                return None
            exact = []
            partial = []
            for class_name, class_type, weapon, base_power in CLASSES:
                normalized = self.normalize_description_query(class_name)
                if wanted == normalized:
                    exact.append(class_name)
                elif wanted in normalized:
                    partial.append(class_name)
            if exact:
                return exact[0]
            if len(partial) == 1:
                return partial[0]
            return None

    def skill_class_name(self, skill):
            skill_id = skill["id"] if isinstance(skill, dict) else str(skill)
            for class_name, skills in CLASS_SKILLS.items():
                if any(entry["id"] == skill_id for entry in skills):
                    return class_name
            return self.character.class_name

    def class_mastery_level(self, class_name):
            row = self.server.db.class_progress_row(self.account_id, class_name)
            return int(row["level"]) if row else 1

    def highest_active_class_mastery(self):
            active = self.active_class_names()
            if not active:
                return 1
            return max(self.class_mastery_level(class_name) for class_name in active)

    def equipment_character_level_requirement(self, item):
            if item.get("type") != "armor":
                return 1
            return max(1, min(CHARACTER_MAX_LEVEL, int(
                item.get("required_character_level", item.get("required_mastery", 1)) or 1
            )))

    def equipment_mastery_requirement_met(self, item):
            """Compatibility name: v0.30.35 EQ gates are Character Level gates."""
            if item.get("type") != "armor":
                return True
            return int(self.character.character_level) >= self.equipment_character_level_requirement(item)

    def equipment_mastery_requirement_text(self, item):
            """Compatibility name kept for old callers; text now reports Character Level."""
            if item.get("type") != "armor":
                return ""
            required_level = self.equipment_character_level_requirement(item)
            return (
                f"Wymaga Levelu postaci {required_level}. "
                f"Masz Level postaci {int(self.character.character_level)}."
            )

    def enforce_equipment_character_level(self):
            """Unequip legacy gear that is above the current Character Level."""
            removed = []
            for row in list(self.server.db.equipment(self.account_id)):
                item = ITEMS.get(row["item_id"])
                if not item or item.get("type") != "armor":
                    continue
                if not self.equipment_mastery_requirement_met(item):
                    self.server.db.unequip(self.account_id, row["slot"])
                    removed.append(item.get("name", row["item_id"]))
            return removed

    def skill_required_mastery(self, skill):
            return max(1, int(skill.get("unlock", 1)))

    def skill_mastery_unlocked(self, skill):
            class_name = self.skill_class_name(skill)
            return self.class_mastery_level(class_name) >= self.skill_required_mastery(skill)

    def skill_training_cost_silver(self, skill):
            """v0.19: koszt nauki korzysta z globalnej krzywej ekonomii."""
            unlock=max(1,min(CLASS_MASTERY_MAX_LEVEL,int(skill.get("unlock",1))))
            return v0190_economy_sink(unlock,"skill")

    def training_cost_text(self, silver_cost):
            return currency_reading_text(max(0, int(silver_cost)), 0, 0)

    def character_wallet_silver_value(self):
            return legacy_currency_to_coins(
                self.character.silver, self.character.gold, self.character.mithril
            )

    def pay_training_cost(self, silver_cost):
            silver_cost = max(0, int(silver_cost))
            total = self.character_wallet_silver_value()
            if total < silver_cost:
                return False
            self.character.silver = total - silver_cost
            self.character.gold = 0
            self.character.mithril = 0
            self.server.db.save_character(self.character)
            return True

    def teacher_here_for_active_class(self):
            active = set(self.active_class_names())
            for npc_id, npc in NPCS.items():
                if (
                    npc.get("room") == self.character.room_id
                    and npc.get("teacher_class") in active
                ):
                    return npc_id, npc
            return None, None

    async def show_multiclass(self):
            active = self.active_class_names()
            await self.send(
                f"MULTICLASS: {len(active)} z {MULTICLASS_MAX_ACTIVE} aktywnych klas."
            )
            await self.send(
                f"Klasa główna: {self.character.class_name}. "
                f"Broń Duszy pozostaje: {self.character.soul_weapon}."
            )
            rows = self.server.db.active_class_rows(
                self.account_id, self.character.class_name
            )
            for row in rows:
                level = int(row["level"])
                xp = int(row["xp"])
                slot = int(row["active_slot"])
                role = "główna" if slot == 1 else f"dodatkowa, slot {slot}"
                if level >= CLASS_MASTERY_MAX_LEVEL:
                    _arow=self.server.db.ascension_row_v021(self.account_id,f"class:{row['class_name']}")
                    _rank=int(_arow["rank"] or 0); _axp=int(_arow["xp"] or 0); _need=v0210_ascension_xp_to_next(_rank)
                    progress = f"Biegłość {CLASS_MASTERY_MAX_LEVEL}, maksimum; Wzniesienie {_rank}" + (f", XP {_axp} z {_need}." if _need else ", maksimum Wzniesienia.")
                else:
                    needed = class_mastery_xp_to_next(level)
                    progress = (
                        f"Biegłość {level}, XP {xp} z {needed}, "
                        f"brakuje {max(0, needed - xp)} XP."
                    )
                await self.send(
                    f"{row['class_name']}: {role}. {progress} "
                    f"Pasyw: {self.character.class_passive_text_for(row['class_name'])}."
                )

            await self.send(
                "Dodanie klas jest opcjonalne. Użyj: multiclass add <klasa>. "
                "Usunięcie: multiclass remove <klasa>."
            )
            await self.send(
                "Maksymalnie 3 klasy łącznie. Class XP z każdego zabitego moba "
                "jest dzielony równo między wszystkie aktywne klasy."
            )
            await self.send(
                "Klasa główna i jej Broń Duszy nie zmieniają się. "
                "Dodatkowe klasy dają swoje pasywy i dostęp do skilli ich nauczycieli."
            )

    async def handle_multiclass(self, raw):
            if self.combat_mob_key:
                await self.send("Nie możesz zmieniać multiclass podczas walki.")
                return

            parts = raw.strip().split(maxsplit=1)
            if not parts:
                await self.show_multiclass()
                return

            action = self.normalize_description_query(parts[0])
            query = parts[1] if len(parts) > 1 else ""

            if action in ("status", "show", "lista", "list"):
                await self.show_multiclass()
                return

            if action in ("add", "dodaj", "wlacz", "włącz"):
                class_name = self.find_class_name(query)
                if not class_name:
                    await self.send(
                        "Nie rozpoznaję klasy. Dostępne: "
                        + ", ".join(cls[0] for cls in CLASSES) + "."
                    )
                    return
                if class_name == self.character.class_name:
                    await self.send("To już jest twoja klasa główna.")
                    return

                old_max_mana = self.max_mana()
                ok, result = self.server.db.activate_secondary_class(
                    self.account_id, self.character.class_name, class_name
                )
                if not ok:
                    await self.send(str(result))
                    return

                self.refresh_active_classes()
                new_max_mana = self.max_mana()
                if new_max_mana > old_max_mana:
                    self.current_mana = new_max_mana
                else:
                    self.current_mana = min(self.current_mana, new_max_mana)

                await self.send(
                    f"Aktywowano dodatkową klasę: {class_name}. "
                    f"Masz teraz {len(self.active_class_names())} aktywne klasy."
                )
                await self.send(
                    "Jej pasyw działa od razu. Skilli nauczysz się u nauczyciela "
                    f"klasy {class_name}."
                )
                await self.set_achievement_progress(
                    "multiclass_classes", len(self.active_class_names())
                )
                return

            if action in ("remove", "usun", "usuń", "wylacz", "wyłącz"):
                class_name = self.find_class_name(query)
                if not class_name:
                    await self.send("Nie rozpoznaję klasy do wyłączenia.")
                    return

                old_max_mana = self.max_mana()
                ok, result = self.server.db.deactivate_secondary_class(
                    self.account_id, self.character.class_name, class_name
                )
                if not ok:
                    await self.send(str(result))
                    return

                self.refresh_active_classes()
                new_max_mana = self.max_mana()
                self.current_mana = min(self.current_mana, new_max_mana)

                await self.send(
                    f"Wyłączono dodatkową klasę: {class_name}. "
                    "Jej Biegłość i nauczenie skille pozostają zapisane, "
                    "ale nie można ich używać, dopóki klasa znów nie będzie aktywna."
                )
                return

            await self.send(
                "Użycie: multiclass, multiclass add <klasa>, "
                "multiclass remove <klasa>."
            )

    async def grant_class_xp(self, total_xp):
            active = self.active_class_names()
            if not active:
                return
            original_total_xp = max(0, int(total_xp))
            if original_total_xp <= 0:
                return
            base_total_xp = self.apply_double_xp(original_total_xp)
            _guild_pct=self.guild_bonus_percent_v0926()
            total_xp=max(0,int(round(base_total_xp*(1.0+_guild_pct/100.0))))

            base_share, remainder = divmod(total_xp, len(active))
            _guild_note=f" Bonus Gildii +{_guild_pct}%: +{total_xp-base_total_xp}." if total_xp>base_total_xp else ""
            _event_note=" Event x2 EXP." if base_total_xp>original_total_xp else ""
            await self.send(
                f"EXP klas: {total_xp}. Aktywne klasy: {len(active)}. "
                "Pula jest dzielona między aktywne klasy." + _event_note + _guild_note
            )

            for index, class_name in enumerate(active):
                share = base_share + (1 if index < remainder else 0)
                result = self.server.db.add_class_mastery_xp(
                    self.account_id, class_name, share
                )
                if result["level_ups"]:
                    await self.send(
                        f"{class_name}: Biegłość rośnie do {result['level']}."
                    )
                ascension=None
                overflow=max(0,int(result.get("overflow_xp",0) or 0))
                if overflow>0 and result["level"]>=CLASS_MASTERY_MAX_LEVEL:
                    ascension=self.server.db.add_ascension_xp_v021(self.account_id,f"class:{class_name}",overflow)
                    if ascension["rank_ups"]:
                        await self.send(f"{class_name}: Wzniesienie rośnie do rangi {ascension['rank']}.")
                        for milestone in (1,10,25,50,100,250,500,1000):
                            if ascension["rank"]>=milestone>ascension["rank"]-ascension["rank_ups"]:
                                await self.unlock_title(f"v021:ascension:{class_name}:{milestone}",f"{class_name} — Wzniesienie {milestone}")
                if result["level"] >= CLASS_MASTERY_MAX_LEVEL:
                    if ascension:
                        nxt=(f" z {ascension['next_xp']}" if ascension['next_xp'] else " — maksimum")
                        await self.send(f"{class_name}: +{share} EXP klasy. Biegłość 400; Wzniesienie {ascension['rank']}, XP {ascension['xp']}{nxt}.")
                    else:
                        await self.send(f"{class_name}: +{share} EXP klasy. Biegłość {CLASS_MASTERY_MAX_LEVEL}, maksimum.")
                else:
                    await self.send(
                        f"{class_name}: +{share} EXP klasy. "
                        f"Biegłość {result['level']}, XP {result['xp']} z "
                        f"{result['next_xp']}."
                    )
