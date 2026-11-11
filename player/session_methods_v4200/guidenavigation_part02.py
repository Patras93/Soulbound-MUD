# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def show_route(self, query):
        raw = str(query or "").strip()
        normalized = self.normalize_room_query(raw)
        if normalized in ("krok", "next", "nastepny", "następny", "dalej"):
            await self.show_route_next_step()
            return

        full = False
        for prefix in ("pelna ", "pełna ", "full ", "dokladna ", "dokładna "):
            if normalized.startswith(self.normalize_room_query(prefix)):
                # Odetnij pierwsze słowo z oryginalnego tekstu, aby zachować
                # polskie znaki w nazwie celu.
                raw = raw.split(maxsplit=1)[1] if " " in raw else ""
                normalized = self.normalize_room_query(raw)
                full = True
                break

        if not raw:
            if self.route_target_room:
                target = self.route_target_room
                target_is_npc = self.route_target_is_npc
                target_label = self.route_target_label or ROOMS[target]["name"]
            else:
                await self.send(
                    "Użycie: trasa <cel>, trasa pełna <cel> albo trasa krok."
                )
                return
        else:
            if normalized.startswith("to "):
                raw = raw[3:].strip()
            npc_match = self.find_guide_npc(raw)
            target_is_npc = npc_match is not None
            target_npc = npc_match[1] if npc_match else None
            if target_is_npc:
                matches = [target_npc["room"]]
                target_label = target_npc["name"]
            else:
                matches = self.find_room_matches(raw)
                matches = list(dict.fromkeys(
                    self.guide_exploration_safe_target(room_id)
                    for room_id in matches
                ))
                target_label = ""

            if not matches:
                await self.send(
                    "Nie rozpoznaję celu trasy. Użyj prowadz lista, aby sprawdzić dostępne cele."
                )
                return
            if len(matches) > 1:
                options = self.compact_guide_matches(matches)
                await self.send(f"Cel trasy jest niejednoznaczny: {raw}.")
                for option in options[:20]:
                    await self.send(option["label"] + ".")
                await self.send(
                    "Podaj dokładniejszą nazwę po komendzie trasa; niczego nie wybieram automatycznie."
                )
                return
            target = matches[0]
            if not target_label:
                target_label = ROOMS[target]["name"]
            self.route_target_room = target
            self.route_target_label = target_label
            self.route_target_is_npc = target_is_npc

        path = self.shortest_path(self.character.room_id, target)
        if path is None:
            await self.send("Nie udało się znaleźć drogi do tej lokacji.")
            return

        await self.send(
            f"TRASA: {ROOMS[self.character.room_id]['name']} -> {target_label}."
        )
        if not path:
            await self.send("Jesteś już w celu. Liczba przejść: 0.")
            return

        direction, next_room = path[0]
        await self.send(
            f"Liczba przejść: {len(path)}. Pierwszy krok: "
            f"{self.route_direction_name(direction)} do {ROOMS[next_room]['name']}."
        )
        await self.send(
            "Skrócona droga: " + self.compact_route_directions(path) + "."
        )
        zones = self.route_zone_sequence(self.character.room_id, path)
        if zones:
            await self.send("Strefy po drodze: " + " -> ".join(zones) + ".")
        estimate = self.estimated_guide_seconds(path)
        await self.send(f"Szacowany czas automatycznego prowadzenia: {estimate:.1f} sekundy.")
        await self.send("Prowadzenie dochodzi dokładnie do wskazanej lokalizacji; nie wymaga ręcznego ostatniego kroku.")
        if full:
            await self.send("PEŁNA TRASA:")
            for index, (step_direction, step_room) in enumerate(path, 1):
                await self.send(
                    f"Krok {index} z {len(path)}: {self.route_direction_name(step_direction)} -> {ROOMS[step_room]['name']}."
                )
        else:
            await self.send(
                "Pełny krok-po-kroku odczyt: trasa pełna <cel>. Następny krok później: trasa krok."
            )


def shortest_path(self, start_room, target_room):
        if start_room == target_room:
            return []

        queue = [(start_room, [])]
        visited = {start_room}

        while queue:
            room_id, path = queue.pop(0)
            room = ROOMS.get(room_id)
            if not room:
                continue
            for direction, next_room in room["exits"].items():
                if next_room in visited:
                    continue
                # v0.23.0: świat ma wyjścia do pięter tworzonych dopiero na
                # żądanie. Nie rozwijamy ich wszystkich podczas BFS (to mogłoby
                # generować kolejne piętra bez końca). Materializujemy tylko
                # brakujący pokój, jeżeli jest dokładnie szukanym celem; inne
                # lazy-exity bezpiecznie pomijamy.
                if next_room not in ROOMS and next_room == target_room:
                    self.server.world.ensure_runtime_room(next_room)
                if next_room not in ROOMS:
                    continue
                new_path = path + [(direction, next_room)]
                if next_room == target_room:
                    return new_path
                visited.add(next_room)
                queue.append((next_room, new_path))
        return None


def shortest_path_within_floor_v11340(
        self, start_room, target_room, floor_parser, floor_number
):
        """Route inside one dungeon floor without crossing its up/down edge."""
        if start_room == target_room:
            return []
        queue = [(start_room, [])]
        visited = {start_room}
        while queue:
            room_id, path = queue.pop(0)
            room = ROOMS.get(room_id)
            if not room:
                continue
            for direction, next_room in room.get("exits", {}).items():
                if next_room in visited:
                    continue
                if floor_parser(next_room) != floor_number:
                    continue
                if next_room not in ROOMS:
                    self.server.world.ensure_runtime_room(next_room)
                if next_room not in ROOMS:
                    continue
                new_path = path + [(direction, next_room)]
                if next_room == target_room:
                    return new_path
                visited.add(next_room)
                queue.append((next_room, new_path))
        return None


def guide_descending_floor_v1501(self, room_id):
        """Describe only the CURRENT descending dungeon floor.

        Deliberately do not create the next floor: the last movement is
        always manual, so all boss, access and checkpoint checks remain.
        """
        from systems.echo_dungeon_v1500 import echo_identity, echo_floor_id
        from world.magitek_infinite import magitek_floor_number, magitek_floor_id
        from core.progression_resources import mine_floor_number, mine_floor_id

        def echo_parser(rid):
            identity = echo_identity(rid)
            return identity[0] if identity else None

        families = (
            ("Labirynt Echa", echo_parser, echo_floor_id),
            ("Krypta", crypt_floor_number, crypt_floor_id),
            ("Mityczna Krypta", mythic_crypt_floor_number, mythic_crypt_floor_id),
            ("UOSS Deep Dungeon", uoss_deep_dungeon_floor_number_v11331,
             uoss_deep_dungeon_floor_id_v11331),
            ("Kompleks Magitek", magitek_floor_number, magitek_floor_id),
            ("Kopalnia Głębinowa", mine_floor_number, mine_floor_id),
        )
        for label, parser, builder in families:
            floor = parser(room_id)
            if floor is not None:
                return label, floor, parser, builder
        dungeon, floor = profession_dungeon_floor(room_id)
        if dungeon and floor is not None:
            labels = {
                "crystal_mine": "Kryształowe Groty",
                "sunken_grotto": "Zatopiona Grota",
                "ancient_forest": "Pradawny Las",
                "alchemy_garden": "Ogród Alchemika",
            }
            def parser(rid):
                name, level = profession_dungeon_floor(rid)
                return level if name == dungeon else None
            def builder(level):
                return profession_dungeon_room_id(dungeon, level)
            return labels.get(dungeon, dungeon), floor, parser, builder
        return None


def guide_exploration_safe_target(self, room_id):
        """Prowadzenie nigdy nie omija eksploracji pięter lochów."""
        room_id = str(room_id or "")
        if crypt_floor_number(room_id):
            return "crypt_entrance"
        if astral_floor_number(room_id) is not None:
            return "astral_gate"
        if mine_floor_number(room_id) is not None:
            return mine_floor_id(MINE_MIN_FLOOR)
        if mythic_crypt_floor_number(room_id):
            return "mythic_crypt_gate"
        if mythic_astral_floor_number(room_id):
            return "mythic_astral_gate"
        if giant_fortress_floor_number(room_id) is not None:
            return "giant_fortress_gate"
        # v102.00.13: do not route to Floor 0 (Serpentarius) or a generated
        # Deep Dungeon floor through automatic navigation. Always use the lift.
        if (room_id == "uoss_deep_dungeon_floor_0_v11331"
                or uoss_deep_dungeon_floor_number_v11331(room_id) is not None):
            return "uoss_deep_dungeon_entry_v11331"
        dungeon, floor = profession_dungeon_floor(room_id)
        if dungeon and floor:
            return profession_dungeon_room_id(dungeon, 1)
        return room_id


def guide_floor_request_label(self, query):
        q = self.normalize_room_query(query)
        checks = (
            (r"(?:krypta|crypt|pietro|pietro krypty|krypta pietro|crypt floor)\s*\d+", "Krypta"),
            (r"(?:wieza|wieza astralna|astral|astralna wieza|poziom wiezy|astral floor)\s*\d+", "Wieża Astralna"),
            (r"(?:kopalnia|mine|poziom kopalni|kopalnia poziom|mine floor)\s*\d+", "Kopalnia Głębinowa"),
            (r"(?:mityczna krypta|mythic crypt)\s*\d+", "Mityczna Krypta"),
            (r"(?:deep dungeon|uoss deep dungeon|deep)\s+(?:(?:floor|pietro)\s+)?\d+", "Deep Dungeon — Winda"),
            (r"(?:mityczna wieza astralna|mythic astral(?: tower)?)\s*\d+", "Mityczna Wieża Astralna"),
            (r"(?:twierdza|twierdza gigantow|giant fortress)\s*\d+", "Twierdza Gigantów"),
            (r"(?:kopalnia krysztalow|crystal mine)\s*\d+", "Kopalnia Głębinowa"),
            (r"(?:zatopiona grota|sunken grotto)\s*\d+", "Zatopiona Grota"),
            (r"(?:pradawny las|ancient forest)\s*\d+", "Pradawny Las"),
            (r"(?:ogrod alchemika|alchemy garden)\s*\d+", "Ogród Alchemika"),
        )
        for pattern, label in checks:
            if re.fullmatch(pattern, q):
                return label
        return None


def guide_floor_family_specs(self):
        return (
            {
                "prefix": "mine_floor_",
                "label": (
                    "Wejście do Kopalni Głębinowej"
                ),
                "minimum": MINE_MIN_FLOOR,
                "maximum": None,
                "target_room": mine_floor_id(MINE_MIN_FLOOR),
            },
            {
                "prefix": "crypt_floor_",
                "label": (
                    "Wejście do Krypty"
                ),
                "minimum": 1,
                "maximum": None,
                "target_room": "crypt_entrance",
            },
            {
                "prefix": "mythic_crypt_floor_",
                "label": (
                    "Wejście do Mitycznej Krypty"
                ),
                "minimum": MYTHIC_MIN_FLOOR,
                "maximum": None,
                "target_room": "mythic_crypt_gate",
            },
            {
                "prefix": "astral_floor_",
                "label": (
                    "Wejście do Wieży Astralnej"
                ),
                "minimum": ASTRAL_MIN_FLOOR,
                "maximum": None,
                "target_room": "astral_gate",
            },
            {
                "prefix": "mythic_astral_floor_",
                "label": (
                    "Wejście do Mitycznej Wieży Astralnej"
                ),
                "minimum": MYTHIC_MIN_FLOOR,
                "maximum": None,
                "target_room": "mythic_astral_gate",
            },
            {
                "prefix": "giant_fortress_",
                "label": (
                    "Wejście do Twierdzy Gigantów"
                ),
                "minimum": 1,
                "maximum": None,
                "target_room": "giant_fortress_gate",
            },
            {
                "prefix": "prof_sunken_grotto_",
                "label": (
                    "Wejście do Zatopionej Groty"
                ),
                "minimum": 1,
                "maximum": None,
                "target_room": profession_dungeon_room_id(
                    "sunken_grotto", 1
                ),
            },
            {
                "prefix": "prof_ancient_forest_",
                "label": (
                    "Wejście do Pradawnego Lasu"
                ),
                "minimum": 1,
                "maximum": None,
                "target_room": profession_dungeon_room_id(
                    "ancient_forest", 1
                ),
            },
            {
                "prefix": "prof_alchemy_garden_",
                "label": (
                    "Wejście do Ogrodu Alchemika"
                ),
                "minimum": 1,
                "maximum": None,
                "target_room": profession_dungeon_room_id(
                    "alchemy_garden", 1
                ),
            },
        )


def compact_guide_matches(self, matches):
        matches = list(dict.fromkeys(matches))
        matched = set()
        options = []

        for spec in self.guide_floor_family_specs():
            family_rooms = [
                room_id
                for room_id in matches
                if room_id.startswith(spec["prefix"])
            ]
            if not family_rooms:
                continue

            matched.update(family_rooms)
            options.append({
                "kind": "room",
                "label": spec["label"],
                "room_id": spec["target_room"],
            })

        for room_id in matches:
            if room_id in matched:
                continue
            options.append({
                "kind": "room",
                "label": (
                    f"{ROOMS[room_id]['name']}. "
                    f"Strefa: {ROOMS[room_id]['zone']}"
                ),
                "room_id": room_id,
            })

        return options


async def ask_guide_choice(self, matches, query):
        options = self.compact_guide_matches(matches)

        if not options:
            return False

        self.guide_choice_state = {
            "mode": "destination",
            "query": str(query or ""),
            "options": options,
        }

        await self.send(
            f"Znaleziono kilka pasujących celów dla: {query}."
        )
        await self.send(
            "Wybierz cyfrę:"
        )

        for number, option in enumerate(options, 1):
            await self.send(
                f"{number}. {option['label']}."
            )

        await self.send(
            "Wpisz tylko samą cyfrę wyboru."
        )
        return True


async def handle_guide_choice_number(self, raw):
        state = self.guide_choice_state
        if not state:
            return False

        value = str(raw or "").strip()

        if self.normalize_room_query(value) in (
            "anuluj", "cancel", "stop",
        ):
            self.guide_choice_state = None
            await self.send(
                "Anulowano wybór celu prowadzenia."
            )
            return True

        if not value.isdigit():
            return False

        number = int(value)

        if state["mode"] == "destination":
            options = state["options"]
            if not 1 <= number <= len(options):
                await self.send(
                    f"Nieprawidłowy numer. Wybierz od 1 do "
                    f"{len(options)} albo wpisz anuluj."
                )
                return True

            option = options[number - 1]
            self.guide_choice_state = None
            await self.start_guide_task(option["room_id"])
            return True

        self.guide_choice_state = None
        return False


def find_guide_npc(self, query):
        """Return one uniquely matched NPC for guide/walk, or None.

        NPC destinations are the only guide targets entered automatically.
        Normal rooms/locations stop one exit before the target.
        """
        q = self.normalize_room_query(query)
        if not q:
            return None

        exact = []
        partial = []
        for npc_id, npc in NPCS.items():
            room_id = npc.get("room")
            if room_id not in ROOMS:
                continue

            npc_id_q = self.normalize_room_query(npc_id)
            name_q = self.normalize_room_query(npc.get("name", ""))
            aliases = {npc_id_q, name_q}

            # A unique personal name such as Toren, Garran or Mirella is
            # convenient for a screen-reader user and still resolves to NPC.
            words = [word for word in name_q.split() if len(word) >= 3]
            aliases.update(words)

            if q in aliases:
                exact.append((npc_id, npc))
            elif any(q in alias for alias in aliases if alias):
                partial.append((npc_id, npc))

        if len(exact) == 1:
            return exact[0]
        if not exact and len(partial) == 1:
            return partial[0]
        return None

