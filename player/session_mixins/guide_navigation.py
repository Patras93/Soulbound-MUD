# -*- coding: utf-8 -*-
"""Guide, routing and path-finding."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import asyncio
import re
import sys
import unicodedata
from core.classes_skills import ROOMS
from config.postal import GUIDE_CITY_HUBS_V0522
from core.mines_threat import GUIDE_DESTINATION_ALIASES
from core.progression_resources import MINE_MIN_FLOOR, mine_floor_id, mine_floor_number
from systems.content_registry import MOB_TEMPLATES, NPCS
from systems.dungeons_regions import (
    ASTRAL_MIN_FLOOR,
    ASTRAL_MIN_SOUL_LEVEL,
    MYTHIC_MIN_FLOOR,
    astral_floor_number,
    crypt_floor_id,
    crypt_floor_number,
    giant_fortress_floor_number,
    mythic_astral_floor_number,
    mythic_crypt_floor_number,
    profession_dungeon_floor,
    profession_dungeon_room_id,
)
from systems.equipment_crafting import SHOP_SELLERS
from systems.items_resources import CLASS_SHOP_CLASSES_BY_ROOM
from world.generation_systems import V013_FRONTIER_SPECS, v0140_surface_secret_info


class SessionGuideNavigationMixin:

    async def show_location(self):
            room = ROOMS[self.character.room_id]
            await self.send(
                f"Lokalizacja: {room['name']}. Strefa: {room['zone']}."
            )
            await self.show_exits()

    def normalize_room_query(self, value):
            text = str(value or "").strip().lower()
            text = text.replace("ł", "l").replace("Ł", "l")
            text = unicodedata.normalize("NFKD", text)
            text = "".join(
                ch for ch in text
                if not unicodedata.combining(ch)
            )
            text = text.replace("_", " ").replace("-", " ")
            text = re.sub(r"[^a-z0-9 ]+", " ", text)
            return " ".join(text.split())

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

    def find_room(self, query):
            matches = self.find_room_matches(query)
            return matches[0] if len(matches) == 1 else None

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
                await self.send("3. gildia — sale 12 nauczycieli klas.")
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
                await self.send("PROWADZENIE — PROFESJE")
                await self.send("Wędkarstwo: Szkoła Wędkarstwa i Mistrz Wędkarstwa Neris — walk Mistrz Wędkarstwa Neris; sklep/narzędzie u Rybaka Borysa — walk Rybak Borys.")
                await self.send("Górnictwo: Gildia Górników i Mistrz Górnictwa Kordan — walk Mistrz Górnictwa Kordan; Kilof i wejście do Kopalni u Górnika Torena — walk Górnik Toren.")
                await self.send("Drwalstwo: Leśniczówka i Mistrz Drwalstwa Oren — walk Mistrz Drwalstwa Oren; Obóz Drwala i Bran — walk Drwal Bran.")
                await self.send("Zielarstwo: Ogród Zielarski i Mistrzyni Zielarstwa Sena — walk Mistrzyni Zielarstwa Sena; Chata Zielarki i Liora — walk Zielarka Liora.")
                await self.send("Kowalstwo/Rzemiosło: Warsztat Rzemieślniczy i Haldor — walk Mistrz Rzemiosła Haldor; Kuźnia Dusz i Kowal Doran — walk Kowal Doran.")
                await self.send("Gotowanie: Kuchnia Błękitnego Płomienia i Kucharz Marcel — walk Kucharz Marcel.")
                await self.send("Alchemia: Laboratorium Alchemiczne i Mistrz Alchemii Orin — walk Mistrz Alchemii Orin; mikstury także w Aptece — walk apteka.")
                await self.send("Jubilerstwo: Pracownia Jubilerska i Jubilerka Mirella — walk Jubilerka Mirella.")
                await self.send("Możesz też wpisać np. walk profesje wedkarstwo, walk profesje gornictwo albo walk profesje alchemia.")
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

    def guide_task_active(self):
            return bool(self.guide_task and not self.guide_task.done())

    def route_direction_name(self, direction):
            labels = {
                "north": "północ",
                "south": "południe",
                "east": "wschód",
                "west": "zachód",
                "up": "góra",
                "down": "dół",
            }
            return labels.get(direction, str(direction))

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

    def route_zone_sequence(self, start_room, path):
            room_ids = [start_room] + [next_room for _direction, next_room in path]
            zones = []
            for room_id in room_ids:
                zone = ROOMS.get(room_id, {}).get("zone", "")
                if zone and (not zones or zones[-1] != zone):
                    zones.append(zone)
            return zones

    def estimated_guide_seconds(self, path):
            return sum(self.movement_delay(direction, guided=True) for direction, _ in path)

    async def cancel_guide(self, announce=True, reason="Prowadzenie zatrzymane."):
            task = self.guide_task
            was_active = bool(task and not task.done())
            self.guide_choice_state = None
            if was_active and task is not asyncio.current_task():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
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
            except asyncio.CancelledError:
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
                    except RuntimeError:
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

    async def guide_to(self, query):
            self.guide_choice_state = None
            q = query.strip()
            if q.lower().startswith("to "):
                q = q[3:].strip()

            normalized = self.normalize_room_query(q)
            if normalized in ("profesje", "professions"):
                await self.show_guide_destinations("profesje")
                return
            if normalized in ("eq", "ekwipunek", "sklepy eq", "equipment", "gear"):
                await self.show_guide_destinations("eq")
                return
            list_prefixes = ("lista", "list", "cele", "destinations", "lokacje", "locations")
            for prefix in list_prefixes:
                if normalized == prefix or normalized.startswith(prefix + " "):
                    category = normalized[len(prefix):].strip()
                    await self.show_guide_destinations(category)
                    return

            if normalized in ("pomoc", "help", "navigation", "nawigacja"):
                await self.show_guide_destinations()
                return

            if not q:
                await self.send(
                    "Użycie: prowadz <cel> albo walk <cel>. "
                    "Lista kategorii: prowadz lista albo walk list."
                )
                return

            if self.combat_mob_key:
                await self.send("Nie możesz użyć prowadzenia podczas walki.")
                return

            # v0.23.0: część celów (Kopalnia Głębinowa i lochy profesyjne)
            # jest tworzona dopiero na żądanie. W v0.22 alias był odrzucany,
            # dopóki pokój nie istniał już w ROOMS, więc np. `prowadz kopalnia`
            # mogło odpowiadać, że nie rozpoznaje celu.
            shortcut = GUIDE_DESTINATION_ALIASES.get(normalized)
            if shortcut and shortcut not in ROOMS:
                self.server.world.ensure_runtime_room(shortcut)

            # v0.30.10 HOTFIX: wewnątrz zwykłej Krypty `walk krypta dół`
            # prowadzi wyłącznie do komnaty z zejściem bieżącego piętra. Nie wykonuje
            # ostatniego kroku `down`; gracz sam decyduje, kiedy zejść niżej.
            crypt_down_requested = normalized in (
                "krypta dol", "krypta w dol", "krypta down", "crypt down",
                "krypty dol", "krypta dool", "krytta dol", "krytta dool",
            )
            direct_crypt_down = False
            crypt_down_floor = None
            if crypt_down_requested:
                current_crypt_floor = crypt_floor_number(self.character.room_id)
                if current_crypt_floor is None:
                    await self.send(
                        "walk krypta dół działa wewnątrz zwykłej Krypty. "
                        "Najpierw wejdź na jej piętro."
                    )
                    return
                crypt_down_floor = current_crypt_floor + 1
                canonical_floor = crypt_floor_id(current_crypt_floor)
                self.server.world.ensure_runtime_room(canonical_floor)

                # Szukamy prawdziwej komnaty, z której wyjście `down` prowadzi na
                # następne piętro. Dzięki temu działa to także na rozgałęzionych
                # i dynamicznie generowanych piętrach.
                crypt_target = None
                for room_id, room in ROOMS.items():
                    if crypt_floor_number(room_id) != current_crypt_floor:
                        continue
                    next_room = room.get("exits", {}).get("down")
                    if crypt_floor_number(next_room) == crypt_down_floor:
                        crypt_target = room_id
                        break
                if crypt_target is None:
                    await self.send(
                        "Nie udało się odnaleźć zejścia na tym piętrze Krypty."
                    )
                    return

                target_is_treasure = False
                treasure_label = ""
                npc_match = None
                target_is_npc = False
                target_npc = None
                matches = [crypt_target]
                direct_crypt_down = True

            # v0.24.0: aktywny trop Mapy Skarbu jest celem zależnym od postaci,
            # więc nie może być zwykłym globalnym aliasem pokoju.
            treasure_match = None if direct_crypt_down else re.fullmatch(
                r"(?:skarb|skarbu|treasure)(?:\s+(\d+))?", normalized
            )
            if not direct_crypt_down:
                target_is_treasure = treasure_match is not None
                treasure_label = ""
            if direct_crypt_down:
                pass
            elif target_is_treasure:
                active_treasures = self.active_treasure_targets_v024()
                if not active_treasures:
                    await self.send(
                        "Nie masz aktywnego tropu Mapy Skarbu. Użyj mapy, a potem wpisz mapa skarbu."
                    )
                    return
                requested = treasure_match.group(1)
                if requested is None and len(active_treasures) > 1:
                    await self.send(
                        f"Masz {len(active_treasures)} aktywne tropy. Wpisz kartografia albo mapa skarbu, "
                        "a następnie prowadz skarb <numer>."
                    )
                    return
                index = int(requested or 1) - 1
                if index < 0 or index >= len(active_treasures):
                    await self.send(
                        f"Nie ma tropu numer {index + 1}. Aktywne tropy: {len(active_treasures)}."
                    )
                    return
                treasure_target = active_treasures[index]
                self.materialize_frontier_route_v024(treasure_target)
                if treasure_target not in ROOMS:
                    await self.send("Nie udało się przygotować sektora wskazanego przez mapę.")
                    return
                info = v0140_surface_secret_info(treasure_target)
                zone = V013_FRONTIER_SPECS[info["kind"]]["zone"]
                treasure_label = f"Trop skarbu: {zone}, sektor {info['x']+1}-{info['y']+1}"
                npc_match = None
                target_is_npc = False
                target_npc = None
                matches = [treasure_target]
            else:
                npc_match = self.find_guide_npc(q)
                target_is_npc = npc_match is not None
                target_npc = npc_match[1] if npc_match else None

                if target_is_npc:
                    matches = [target_npc["room"]]
                else:
                    floor_label = self.guide_floor_request_label(q)
                    matches = self.find_room_matches(q)
                    matches = list(dict.fromkeys(
                        self.guide_exploration_safe_target(room_id)
                        for room_id in matches
                    ))
                    # Bezpieczny cel po redukcji piętra także może być lazy-roomem.
                    for room_id in matches:
                        if room_id not in ROOMS:
                            self.server.world.ensure_runtime_room(room_id)
                    if floor_label and matches and floor_label != "Kopalnia Głębinowa":
                        await self.send(
                            f"Prowadzenie nie prowadzi na piętra. "
                            f"Eksploracja wnętrza pozostaje ręczna. "
                            f"Prowadzę tylko przed wejście: {floor_label}."
                        )
                    elif floor_label == "Kopalnia Głębinowa" and matches:
                        await self.send(
                            "Kopalnia: prowadzenie doprowadzi bezpośrednio na poziom 1. "
                            "Głębsze poziomy pozostają do eksploracji ręcznej."
                        )

            if not matches:
                await self.send(
                    "Nie rozpoznaję tego celu. "
                    "Wpisz prowadz lista albo walk list, aby wybrać kategorię."
                )
                return

            if len(matches) > 1:
                await self.ask_guide_choice(
                    matches,
                    q,
                )
                return

            target = matches[0]
            direct_mine_target = (
                (not target_is_npc)
                and target == mine_floor_id(MINE_MIN_FLOOR)
                and mine_floor_number(target) == MINE_MIN_FLOOR
            )
            # v0.30.6: prowadzenie zawsze dochodzi dokładnie do rozpoznanej lokalizacji.
            # Nadal respektuje wszystkie blokady wejścia i nie omija eksploracyjnych
            # ograniczeń dla pięter, bo te cele są wcześniej redukowane do bezpiecznych wejść.
            reach_exact_target = True

            if target == self.character.room_id:
                if direct_crypt_down:
                    await self.send(
                        f"Już jesteś przed zejściem na piętro {crypt_down_floor} Krypty. "
                        "Wykonaj zejście ręcznie."
                    )
                elif target_is_npc:
                    await self.send(
                        f"NPC {target_npc['name']} jest już tutaj: "
                        f"{ROOMS[target]['name']}."
                    )
                else:
                    await self.send(f"Już jesteś tutaj: {ROOMS[target]['name']}.")
                return

            full_path = self.shortest_path(self.character.room_id, target)
            if full_path is None:
                await self.send("Nie udało się znaleźć drogi do tej lokacji.")
                return

            self.guide_target_room = target
            self.guide_target_label = (
                target_npc["name"] if target_is_npc
                else (treasure_label if target_is_treasure else ROOMS[target]["name"])
            )
            self.guide_target_is_npc = target_is_npc

            # v0.30.6: pełna auto-nawigacja do celu. Nie zostawiamy ostatniego
            # ręcznego kroku; przejścia są wykonywane normalnie jedno po drugim,
            # więc walka, wymagania wejścia i inne blokady nadal mogą zatrzymać trasę.
            path = full_path
            stop_room = target
            final_direction = None
            self.guide_final_direction = None

            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
                await self.send("Auto-łowienie wyłączone z powodu rozpoczęcia podróży.")
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
                await self.send("Auto-kopanie wyłączone z powodu rozpoczęcia podróży.")
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
                await self.send("Auto-Drwalstwo wyłączone z powodu rozpoczęcia podróży.")
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)
                await self.send("Auto-Zielarstwo wyłączone z powodu rozpoczęcia podróży.")

            self.guiding = True
            if target_is_npc:
                await self.send(
                    f"Prowadzę do NPC: {target_npc['name']}. "
                    f"Lokalizacja: {ROOMS[target]['name']}. "
                    f"Liczba przejść: {len(path)}."
                )
            elif target_is_treasure:
                await self.send(
                    f"Prowadzę bezpośrednio do aktywnego tropu skarbu: {treasure_label}. "
                    f"Automatyczne przejścia: {len(path)}. Po dotarciu użyj sekret."
                )
            elif direct_crypt_down:
                await self.send(
                    f"Prowadzę przed zejście na piętro {crypt_down_floor} Krypty. "
                    f"Automatyczne przejścia: {len(path)}. "
                    "Ostatnie zejście wykonujesz ręcznie."
                )
            elif direct_mine_target:
                await self.send(
                    f"Prowadzę bezpośrednio do: {ROOMS[target]['name']}. "
                    f"Automatyczne przejścia: {len(path)}. "
                    "Nie musisz wykonywać ostatniego kroku ręcznie."
                )
            else:
                await self.send(
                    f"Prowadzę bezpośrednio do: {ROOMS[target]['name']}. "
                    f"Automatyczne przejścia: {len(path)}. "
                    "Nie musisz wykonywać żadnego kroku ręcznie."
                )

            try:
                for direction, next_room in path:
                    if self.closed:
                        break
                    if self.combat_mob_key:
                        await self.send("Prowadzenie przerwane przez walkę.")
                        break

                    old = self.character.room_id
                    mythic_error = self.mythic_entry_error(next_room)
                    if mythic_error:
                        await self.send(
                            "Prowadzenie zatrzymane. " + mythic_error
                        )
                        break

                    profession_error = (
                        self.profession_dungeon_access_error(next_room)
                    )
                    if profession_error:
                        await self.send(
                            "Prowadzenie zatrzymane. "
                            + profession_error
                        )
                        break

                    if self.astral_entry_blocked(next_room):
                        await self.send(
                            f"Prowadzenie zatrzymane. Wieża Astralna wymaga "
                            f"Soul Poziom {ASTRAL_MIN_SOUL_LEVEL}."
                        )
                        break
                    if self.mine_descent_blocked_for_player(old, direction):
                        progress = self.mine_progress()
                        floor = mine_floor_number(old)
                        required_hits = progress["wall_required_hits"]
                        await self.send(
                            f"Prowadzenie zatrzymane. Ściana kopalni "
                            f"blokuje zejście. Postęp "
                            f"{progress['wall_hits']} z "
                            f"{required_hits}."
                        )
                        break
                    if self.mythic_crypt_descent_blocked_for_player(
                        old, direction
                    ):
                        await self.send(
                            "Prowadzenie zatrzymane. "
                            "Mityczny boss Krypty blokuje zejście."
                        )
                        break
                    if self.mythic_astral_ascent_blocked_for_player(
                        old, direction
                    ):
                        await self.send(
                            "Prowadzenie zatrzymane. "
                            "Mityczny boss Wieży blokuje drogę w górę."
                        )
                        break
                    if self.giant_fortress_ascent_blocked_for_player(
                        old, direction
                    ):
                        boss = (
                            self.server.world.live_giant_fortress_boss(
                                old
                            )
                        )
                        boss_name = (
                            MOB_TEMPLATES[
                                boss.template_id
                            ]["name"]
                            if boss
                            else "boss Twierdzy Gigantów"
                        )
                        await self.send(
                            f"Prowadzenie zatrzymane. Drogę wyżej "
                            f"blokuje {boss_name}."
                        )
                        break
                    if self.crypt_descent_blocked_for_player(old, direction):
                        boss = self.server.world.live_crypt_boss(old)
                        boss_name = (
                            MOB_TEMPLATES[boss.template_id]["name"]
                            if boss else "boss Krypty"
                        )
                        await self.send(
                            f"Prowadzenie zatrzymane. Zejście niżej blokuje "
                            f"{boss_name}. Pokonaj bossa."
                        )
                        break
                    if self.astral_ascent_blocked_for_player(old, direction):
                        boss = self.server.world.live_astral_boss(old)
                        boss_name = (
                            MOB_TEMPLATES[boss.template_id]["name"]
                            if boss else "boss Wieży Astralnej"
                        )
                        await self.send(
                            f"Prowadzenie zatrzymane. Drogę w górę blokuje "
                            f"{boss_name}. Pokonaj bossa."
                        )
                        break
                    moved = await self.walk_room_transition(
                        direction, next_room, guided=True, show_room=False
                    )
                    if not moved:
                        break

                if target_is_npc and self.character.room_id == target:
                    await self.send(
                        f"Dotarłeś do NPC: {target_npc['name']}. "
                        f"Lokalizacja: {ROOMS[target]['name']}."
                    )
                    await self.look()
                elif direct_crypt_down and self.character.room_id == target:
                    await self.send(
                        f"Dotarłeś przed zejście na piętro {crypt_down_floor} Krypty. "
                        "Wykonaj zejście ręcznie."
                    )
                    await self.look()
                elif direct_mine_target and self.character.room_id == target:
                    await self.send(
                        f"Dotarłeś bezpośrednio do: {ROOMS[target]['name']}."
                    )
                    await self.look()
                elif target_is_treasure and self.character.room_id == target:
                    await self.send(
                        f"Dotarłeś bezpośrednio do tropu skarbu: {treasure_label}. "
                        "Użyj sekret, aby zbadać wskazane miejsce."
                    )
                    await self.look()
                elif (not target_is_npc) and (not direct_mine_target) and (not target_is_treasure) and self.character.room_id == target:
                    await self.send(
                        f"Dotarłeś bezpośrednio do: {ROOMS[target]['name']}."
                    )
                    await self.look()
            finally:
                self.guiding = False
                self.guide_target_room = None
                self.guide_target_label = ""
                self.guide_target_is_npc = False
                self.guide_final_direction = None
