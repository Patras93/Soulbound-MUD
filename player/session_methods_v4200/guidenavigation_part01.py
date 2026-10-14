# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def show_current_city_walk_destinations(self):
        """Pokaż cele komendy walk dostępne w aktualnym mieście lub osadzie."""
        current_room_id = str(self.character.room_id)
        current_room = ROOMS.get(current_room_id, {})
        current_zone = current_room.get("zone", "")

        city_name = None
        for candidate_name, hub_room_id in GUIDE_CITY_HUBS_V0522.items():
            hub_room = ROOMS.get(hub_room_id)
            if hub_room and hub_room.get("zone") == current_zone:
                city_name = candidate_name
                break

        if not city_name:
            await self.send(
                "Nie jesteś teraz w mieście ani osadzie. "
                "Użyj walk list, aby zobaczyć pozostałe cele prowadzenia."
            )
            return

        destinations = [
            (room_id, room)
            for room_id, room in ROOMS.items()
            if room.get("zone") == current_zone and room_id != current_room_id
        ]
        destinations.sort(
            key=lambda row: self.normalize_room_query(row[1].get("name", row[0]))
        )

        await self.send(
            f"WALK — {city_name}. Aktualnie: "
            f"{current_room.get('name', current_room_id)}."
        )
        if not destinations:
            await self.send("W tym mieście nie ma innych dostępnych lokacji.")
            return

        await self.send("Możesz iść do:")
        for _room_id, room in destinations:
            room_name = room.get("name", _room_id)
            await self.send(f"{room_name}: walk {room_name}.")


def room_search_aliases(self, room_id, room):
        aliases = {
            self.normalize_room_query(room_id),
            self.normalize_room_query(room_id.replace("_", " ")),
            self.normalize_room_query(room["name"]),
        }

        zone = self.normalize_room_query(room.get("zone", ""))
        name = self.normalize_room_query(room["name"])
        if zone and name:
            aliases.add(f"{zone} {name}")

        floor = crypt_floor_number(room_id)
        if floor:
            aliases.update({
                f"krypta {floor}",
                f"crypt {floor}",
                f"pietro {floor}",
                f"pietro krypty {floor}",
                f"krypta pietro {floor}",
                f"crypt floor {floor}",
            })

        astral_floor = astral_floor_number(room_id)
        if astral_floor is not None:
            aliases.update({
                f"wieza {astral_floor}",
                f"wieza astralna {astral_floor}",
                f"astral {astral_floor}",
                f"astralna wieza {astral_floor}",
                f"poziom wiezy {astral_floor}",
                f"astral floor {astral_floor}",
            })

        # Krótkie, naturalne warianty popularnych nazw.
        words = name.split()
        if len(words) > 1:
            aliases.add(" ".join(words[1:]))

        return {alias for alias in aliases if alias}


def guide_zone_query_name(self, query):
        q = self.normalize_room_query(query)
        aliases = {
            "miasto": "miasto dusz",
            "gildia": "gildia dusz",
            "gory": "gory",
            "wioska": "wioska gorska",
            "wioska gorska": "wioska gorska",
            "laki": "laki zielarskie",
            "laka": "laki zielarskie",
            "podziemia": "podziemia",
            "trolle": "jaskinia trolli",
            "jaskinia trolli": "jaskinia trolli",
            "wieza astralna": "wieza astralna",
            "mityczna wieza astralna": "mityczna wieza astralna",
            "mityczna krypta": "mityczna krypta",
            "twierdza gigantow": "twierdza gigantow",
            "kopalnia glebinowa": "kopalnia glebinowa",
            "lasy": "loch profesyjny pradawny las",
            "pradawny las": "loch profesyjny pradawny las",
            "ogrod alchemika": "loch profesyjny ogrod alchemika",
            "zatopiona grota": "loch profesyjny zatopiona grota",
        }
        return aliases.get(q, q)


def rooms_in_exact_zone(self, query):
        zone_query = self.guide_zone_query_name(query)
        matches = [
            room_id
            for room_id, room in ROOMS.items()
            if self.normalize_room_query(
                room.get("zone", "")
            ) == zone_query
        ]
        return sorted(
            matches,
            key=lambda rid: self.normalize_room_query(
                ROOMS[rid]["name"]
            ),
        )


def find_room_matches(self, query):
        q = self.normalize_room_query(query)
        if not q:
            return []

        # Najpierw bezpieczne wejścia. Dzięki temu nazwa lochu nie
        # rozwija się do listy jego pięter.
        shortcut = GUIDE_DESTINATION_ALIASES.get(q)
        if shortcut and shortcut in ROOMS:
            return [shortcut]

        zone_matches = self.rooms_in_exact_zone(q)
        if zone_matches:
            return zone_matches

        # "wieza" jest celowo szerokim terenem:
        # zwykła i Mityczna Wieża Astralna.
        if q in ("wieza", "tower"):
            matches = []
            for zone_name in (
                "Wieża Astralna",
                "Mityczna Wieża Astralna",
            ):
                matches.extend(
                    self.rooms_in_exact_zone(zone_name)
                )
            if matches:
                return list(dict.fromkeys(matches))

        # "jaskinia" jako szeroki teren pokazuje zarówno
        # Kryształową Jaskinię, jak i Jaskinię Trolli.
        if q in ("jaskinia", "cave"):
            matches = []
            for room_id in (
                "cave_entrance",
                "troll_cave_entrance",
            ):
                if room_id in ROOMS:
                    matches.append(room_id)
            if matches:
                return matches

        # Zapytania o piętra są sprowadzane do wejścia.
        crypt_match = re.fullmatch(
            r"(?:krypta|crypt|pietro|pietro krypty|krypta pietro|crypt floor)\s*(\d+)",
            q,
        )
        if crypt_match:
            floor = int(crypt_match.group(1))
            if floor >= 1:
                return ["crypt_entrance"]
            return []

        astral_match = re.fullmatch(
            r"(?:wieza|wieza astralna|astral|astralna wieza|poziom wiezy|astral floor)\s*(\d+)",
            q,
        )
        if astral_match:
            floor = int(astral_match.group(1))
            if floor >= ASTRAL_MIN_FLOOR:
                return ["astral_gate"]
            return []

        mine_match = re.fullmatch(
            r"(?:kopalnia|mine|poziom kopalni|kopalnia poziom|mine floor)\s*(\d+)",
            q,
        )
        if mine_match:
            floor = int(mine_match.group(1))
            if floor >= MINE_MIN_FLOOR:
                return [mine_floor_id(MINE_MIN_FLOOR)]
            return []

        exact = []
        partial = []

        for room_id, room in ROOMS.items():
            aliases = self.room_search_aliases(room_id, room)
            if q in aliases:
                exact.append(room_id)
                continue
            if any(q in alias for alias in aliases):
                partial.append(room_id)

        if exact:
            return sorted(
                set(exact),
                key=lambda rid: ROOMS[rid]["name"].lower(),
            )

        return sorted(
            set(partial),
            key=lambda rid: ROOMS[rid]["name"].lower(),
        )


async def show_guide_destinations(self, category=""):
        q = self.normalize_room_query(category)
        category_aliases = {
            "": "",
            "miasto": "miasto", "city": "miasto", "town": "miasto",
            "miasta": "miasta", "cities": "miasta", "towns": "miasta", "osady": "miasta",
            "gildia": "gildia", "guild": "gildia", "teachers": "gildia", "nauczyciele": "gildia",
            "profesje": "profesje", "professions": "profesje", "crafting": "profesje",
            "eq": "eq", "ekwipunek": "eq", "sklepy eq": "eq", "equipment": "eq", "gear": "eq",
            "tereny": "tereny", "regions": "tereny", "regiony": "tereny", "zones": "tereny",
            "lochy": "lochy", "dungeons": "lochy", "dungeon": "lochy", "endgame": "lochy",
            "npc": "npc", "npcs": "npc", "postacie": "npc",
            "wszystko": "wszystko", "all": "wszystko", "pelna": "wszystko", "full": "wszystko",
        }
        selected = category_aliases.get(q)
        if selected is None:
            await self.send(
                "Nie znam takiej kategorii. Dostępne: miasto, miasta, gildia, profesje, eq, tereny, lochy, npc, wszystko."
            )
            return

        if not selected:
            await self.send("PROWADZENIE / WALK — KATEGORIE")
            await self.send("1. miasto — ważne miejsca Miasta Dusz.")
            await self.send("2. miasta — wszystkie miasta i osady świata.")
            await self.send("3. gildia — sale 14 nauczycieli klas.")
            await self.send("4. profesje — mistrzowie, warsztaty i sklepy narzędzi.")
            await self.send("5. eq — sklepy z klasowym wyposażeniem.")
            await self.send("6. tereny — regiony świata.")
            await self.send("7. lochy — Krypta, Wieże, Kopalnie, Twierdza i lochy profesyjne.")
            await self.send("8. npc — nazwani NPC i ich lokalizacje.")
            await self.send("9. wszystko — pełna lista lokacji pogrupowana strefami.")
            await self.send("Użyj np. prowadz lista gildia albo walk list dungeons.")
            return

        if selected == "miasto":
            await self.send("PROWADZENIE — MIASTO DUSZ")
            rooms = [(rid, room) for rid, room in ROOMS.items() if room.get("zone") == "Miasto Dusz"]
            for room_id, room in sorted(rooms, key=lambda x: self.normalize_room_query(x[1]["name"])):
                await self.send(f"{room['name']}: prowadz {room['name']}.")
            return

        if selected == "miasta":
            await self.send("PROWADZENIE — MIASTA I OSADY")
            for city_name, room_id in GUIDE_CITY_HUBS_V0522.items():
                if room_id not in ROOMS:
                    continue
                await self.send(
                    f"{city_name}: {ROOMS[room_id]['name']}. prowadz {city_name}."
                )
            await self.send("Punkty pocztowe działają w tych samych 9 miejscowościach. Wpisz poczta w punkcie pocztowym, aby zobaczyć paczki.")
            return

        if selected == "gildia":
            await self.send("PROWADZENIE — GILDIA I NAUCZYCIELE")
            teachers = [npc for npc in NPCS.values() if npc.get("teacher_class") and npc.get("room") in ROOMS]
            for npc in sorted(teachers, key=lambda x: self.normalize_room_query(x.get("teacher_class", ""))):
                room = ROOMS[npc["room"]]
                await self.send(f"{npc['teacher_class']}: {npc['name']}, {room['name']}. prowadz {npc['name']}.")
            return

        if selected == "profesje":
            await self.send("PROWADZENIE — PROFESJE 14/14")
            profession_npcs = (
                ("Wędkarstwo", "specialist_fishing"),
                ("Górnictwo", "specialist_mining"),
                ("Drwalstwo", "specialist_woodcutting"),
                ("Zielarstwo", "specialist_herbalism"),
                ("Kowalstwo", "specialist_crafting"),
                ("Gotowanie", "specialist_cooking"),
                ("Alchemia", "specialist_alchemy"),
                ("Jubilerstwo", "jeweler_mirella"),
                ("Krawiectwo", "tailor_lysa"),
                ("Garbarstwo", "leatherworker_soren"),
                ("Stolarstwo", "carpenter_edric"),
                ("Zaklinanie", "guild_quartermaster_arcane"),
                ("Archeologia", "specialist_archaeology"),
                ("Kartografia", "specialist_cartography"),
            )
            shown = 0
            for profession, npc_id in profession_npcs:
                npc = NPCS.get(npc_id, {})
                room_id = npc.get("room")
                name = npc.get("name")
                if not name or room_id not in ROOMS:
                    await self.send(f"{profession}: cel prowadzenia chwilowo niedostępny.")
                    continue
                shown += 1
                await self.send(
                    f"{profession}: {name}, {ROOMS[room_id]['name']}. walk {name}."
                )
            await self.send(f"Pokazano profesje: {shown} z 14.")
            return

        if selected == "eq":
            await self.send("PROWADZENIE — SKLEPY Z EQ KLASOWYM")
            for room_id, classes in sorted(CLASS_SHOP_CLASSES_BY_ROOM.items(), key=lambda row: self.normalize_room_query(ROOMS.get(row[0], {}).get("name", row[0]))):
                if room_id not in ROOMS:
                    continue
                seller_id = SHOP_SELLERS.get(room_id)
                seller = NPCS.get(seller_id, {}) if seller_id else {}
                seller_name = seller.get("name", ROOMS[room_id]["name"])
                class_text = ", ".join(classes)
                await self.send(
                    f"{class_text}: {seller_name}, {ROOMS[room_id]['name']}. "
                    f"walk {seller_name}."
                )
            await self.send("Możesz też wpisać np. walk eq wojownik, walk eq mag albo walk sklep eq druid.")
            return

        if selected == "tereny":
            await self.send("PROWADZENIE — TERENY")
            zones = sorted({room.get("zone", "") for room in ROOMS.values() if room.get("zone")}, key=self.normalize_room_query)
            for zone in zones:
                await self.send(f"{zone}: prowadz {zone}.")
            return

        if selected == "lochy":
            await self.send("PROWADZENIE — LOCHY I ENDGAME")
            entries = [
                "Krypta: prowadz krypta.",
                "Wieża Astralna: prowadz wieza astralna.",
                "Kopalnia Głębinowa: prowadz kopalnia glebinowa.",
                "Kryształowe Groty (bez Górnictwa): prowadz krysztalowe groty.",
                "Mityczna Krypta: prowadz mityczna krypta.",
                "Mityczna Wieża Astralna: prowadz mityczna wieza astralna.",
                "Twierdza Gigantów: prowadz twierdza gigantow.",
                "Zatopiona Grota: prowadz zatopiona grota.",
                "Pradawny Las: prowadz pradawny las.",
                "Ogród Alchemika: prowadz ogrod alchemika.",
                "Jaskinia Trolli: prowadz jaskinia trolli.",
            ]
            for line in entries:
                await self.send(line)
            await self.send("Prowadzenie zatrzymuje się przy progu. Wpisz nazwę lochu, np. krypty, wieza astralna albo jaskinia trolli, aby wejść bez kierunku. Wewnątrz eksplorujesz normalnie; wyjście wraca do progu.")
            return

        if selected == "npc":
            await self.send("PROWADZENIE — NPC")
            rows = []
            for npc in NPCS.values():
                room_id = npc.get("room")
                name = npc.get("name")
                if name and room_id in ROOMS:
                    rows.append((name, ROOMS[room_id]["name"]))
            for name, room_name in sorted(set(rows), key=lambda x:self.normalize_room_query(x[0])):
                await self.send(f"{name}: {room_name}. prowadz {name}.")
            return

        # Pełna lista pozostaje dostępna, ale nie zalewa NVDA domyślnie.
        await self.send("PROWADZENIE — PEŁNA LISTA")
        zones = {}
        for room_id, room in ROOMS.items():
            if room_id.startswith(("crypt_floor_", "astral_floor_", "mythic_crypt_floor_", "mythic_astral_floor_")):
                continue
            zones.setdefault(room["zone"], []).append(room["name"])
        for zone in sorted(zones, key=self.normalize_room_query):
            names = sorted(set(zones[zone]), key=self.normalize_room_query)
            await self.send(f"{zone}: " + "; ".join(names) + ".")
        await self.send("Krypta: piętra 1-∞, generowane na żądanie.")
        await self.send(f"Wieża Astralna: od poziomu {ASTRAL_MIN_FLOOR} bez górnego limitu.")
        await self.send(f"Kopalnia Głębinowa: od poziomu {MINE_MIN_FLOOR} bez górnego limitu.")
        await self.send("Mityczna Wieża Astralna, Twierdza Gigantów i cztery lochy profesyjne: bez górnego limitu.")
        await self.send("Jeśli cel pasuje do kilku miejsc, wybierasz tylko jeden numer z jednej listy.")


def compact_route_directions(self, path):
        if not path:
            return "jesteś już na miejscu"
        runs = []
        last = None
        count = 0
        for direction, _next_room in path:
            if direction == last:
                count += 1
                continue
            if last is not None:
                label = self.route_direction_name(last)
                runs.append(f"{label} x{count}" if count > 1 else label)
            last = direction
            count = 1
        if last is not None:
            label = self.route_direction_name(last)
            runs.append(f"{label} x{count}" if count > 1 else label)
        return ", ".join(runs)


async def cancel_guide(self, announce=True, reason="Prowadzenie zatrzymane."):
        task = self.guide_task
        was_active = bool(task and not task.done())
        self.guide_choice_state = None
        if was_active and task is not asyncio.current_task():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:  # AUDIT_INTENTIONAL_PASS: normal guide-task cancellation
                pass
        if self.guide_task is task:
            self.guide_task = None
        self.guiding = False
        self.guide_target_room = None
        self.guide_target_label = ""
        self.guide_target_is_npc = False
        self.guide_final_direction = None
        if announce:
            if was_active:
                await self.send(reason)
            else:
                await self.send("Prowadzenie nie jest aktywne.")
        return was_active


async def show_guide_status(self):
        if not self.guide_task_active() or not self.guide_target_room:
            await self.send("Prowadzenie nie jest aktywne.")
            return
        target = self.guide_target_room
        path = self.shortest_path(self.character.room_id, target)
        if path is None:
            await self.send(
                f"Prowadzenie aktywne do: {self.guide_target_label}, ale aktualnie nie da się wyliczyć pozostałej drogi."
            )
            return
        next_text = "brak, cel osiągnięty"
        if path:
            direction, next_room = path[0]
            next_text = (
                f"{self.route_direction_name(direction)} do {ROOMS[next_room]['name']}"
            )
        await self.send(
            f"Prowadzenie aktywne. Teraz: {ROOMS[self.character.room_id]['name']}. "
            f"Cel: {self.guide_target_label}. Pozostało przejść do celu: {len(path)}. "
            f"Następny krok: {next_text}."
        )
        if (not self.guide_target_is_npc) and self.guide_final_direction:
            await self.send(
                f"Dla zwykłej lokacji prowadzenie zatrzyma się przed celem; końcowy kierunek wykonasz ręcznie: {self.guide_final_direction}."
            )


def _guide_task_finished(self, task):
        if self.guide_task is task:
            self.guide_task = None
        try:
            task.result()
        except asyncio.CancelledError:  # AUDIT_INTENTIONAL_PASS: completed callback sees normal cancellation
            pass
        except Exception as exc:
            print(
                f"[GUIDE ERROR] {type(exc).__name__}: {exc}",
                file=sys.stderr,
                flush=True,
            )
            if not self.closed:
                try:
                    asyncio.get_running_loop().create_task(
                        self.send("Prowadzenie zostało zatrzymane przez błąd nawigacji.")
                    )
                except RuntimeError:  # AUDIT_INTENTIONAL_PASS: event loop may already be shutting down
                    pass


async def start_guide_task(self, args):
        normalized = self.normalize_room_query(args)
        if normalized in ("stop", "anuluj", "cancel", "przerwij", "zatrzymaj"):
            await self.cancel_guide(announce=True)
            return
        if normalized in ("status", "stan", "gdzie", "info"):
            await self.show_guide_status()
            return
        if self.guide_task_active():
            await self.send(
                "Prowadzenie już trwa. Użyj prowadz status albo prowadz stop."
            )
            return
        task = asyncio.create_task(self.guide_to(args))
        self.guide_task = task
        task.add_done_callback(self._guide_task_finished)
        # Oddaj sterowanie pętli wejścia, ale pozwól zadaniu wypisać pierwszy
        # komunikat jeszcze przed następnym promptem.
        await asyncio.sleep(0)


async def show_route_next_step(self):
        target = self.route_target_room
        if not target or target not in ROOMS:
            await self.send("Najpierw zaplanuj trasę: trasa <cel>.")
            return
        path = self.shortest_path(self.character.room_id, target)
        if path is None:
            await self.send("Nie udało się znaleźć drogi do zapamiętanego celu.")
            return
        if not path:
            await self.send(f"Jesteś już w celu trasy: {ROOMS[target]['name']}.")
            return
        direction, next_room = path[0]
        await self.send(
            f"Następny krok: {self.route_direction_name(direction)}. "
            f"Następna lokacja: {ROOMS[next_room]['name']}. "
            f"Do celu pozostaje {len(path)} przejść."
        )

