# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
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

        # v1.50.1: `walk gora` / `walk góra` -- rozpoznaj bieżącą
        # wieżę, a potem użyj istniejącego, bezpiecznego prowadzenia
        # wewnątrz jej piętra. Nigdy nie wykonuj ostatniego `up`.
        # Dotyczy zwykłej i Mitycznej Wieży Astralnej oraz Twierdzy Gigantów.
        if normalized in ("gora", "w gore", "up"):
            if astral_floor_number(self.character.room_id) is not None:
                normalized = "wieza gora"
            elif mythic_astral_floor_number(self.character.room_id) is not None:
                normalized = "mityczna wieza gora"
            elif giant_fortress_floor_number(self.character.room_id) is not None:
                normalized = "twierdza gora"
            else:
                await self.send(
                    "walk gora / walk góra działa na piętrze Wieży Astralnej, "
                    "Mitycznej Wieży Astralnej lub Twierdzy Gigantów. "
                    "Najpierw wejdź do wieży. W lochach schodzących w dół "
                    "użyj walk dol / walk dool."
                )
                return

        # v0.23.0: część celów (Kopalnia Głębinowa i lochy profesyjne)
        # jest tworzona dopiero na żądanie. W v0.22 alias był odrzucany,
        # dopóki pokój nie istniał już w ROOMS, więc np. `prowadz kopalnia`
        # mogło odpowiadać, że nie rozpoznaje celu.
        shortcut = GUIDE_DESTINATION_ALIASES.get(normalized)
        if shortcut and shortcut not in ROOMS:
            self.server.world.ensure_runtime_room(shortcut)

        # v1.50.1: krótkie `walk dol` / `walk dool` wybiera zejście
        # z AKTUALNEGO piętra. Nie przechodzi na następne piętro.
        generic_down_requested = normalized in (
            "dol", "dool", "w dol", "down", "zejscie", "zejscie w dol",
        )
        direct_generic_down = False
        generic_down_floor = None
        generic_down_label = None
        generic_down_direction = None
        generic_down_parser = None
        generic_down_number = None
        if generic_down_requested:
            context = self.guide_descending_floor_v1501(self.character.room_id)
            if context is None:
                await self.send(
                    "walk dol działa na piętrze lochu, z którego można zejść niżej. "
                    "Najpierw wejdź do lochu. W wieżach użyj walk wieza gora."
                )
                return
            (generic_down_label, current_down_floor,
             generic_down_parser, down_floor_builder) = context
            generic_down_floor = current_down_floor + 1
            generic_down_number = current_down_floor
            self.server.world.ensure_runtime_room(down_floor_builder(current_down_floor))
            generic_target = None
            for room_id, room in ROOMS.items():
                if generic_down_parser(room_id) != current_down_floor:
                    continue
                for direction, next_room in room.get("exits", {}).items():
                    if generic_down_parser(next_room) == generic_down_floor:
                        generic_target = room_id
                        generic_down_direction = direction
                        break
                if generic_target:
                    break
            if generic_target is None:
                await self.send(
                    f"Na piętrze {current_down_floor} ({generic_down_label}) "
                    "nie znaleziono przejścia na następne piętro."
                )
                return
            target_is_treasure = False
            treasure_label = ""
            npc_match = None
            target_is_npc = False
            target_npc = None
            matches = [generic_target]
            direct_generic_down = True

        # v1.13.40: `walk krypta dół` działa zarówno w zwykłej, jak i
        # Mitycznej Krypcie. Komenda prowadzi wyłącznie do komnaty z wyjściem
        # `down`; ostatnie zejście gracz nadal wykonuje ręcznie, więc blokada
        # bossa/checkpointu pozostaje w zwykłym runtime ruchu.
        crypt_down_requested = normalized in (
            "krypta dol", "krypta w dol", "krypta down", "crypt down",
            "krypty dol", "krypta dool", "krytta dol", "krytta dool",
            "mityczna krypta dol", "mityczna krypta w dol",
            "mityczna krypta down", "mythic crypt down",
        )
        direct_crypt_down = False
        crypt_down_floor = None
        crypt_down_label = "Krypty"
        direct_floor_parser_v11340 = None
        direct_floor_number_v11340 = None
        if crypt_down_requested:
            current_crypt_floor = crypt_floor_number(self.character.room_id)
            crypt_floor_parser = crypt_floor_number
            crypt_floor_builder = crypt_floor_id
            if current_crypt_floor is None:
                current_crypt_floor = mythic_crypt_floor_number(
                    self.character.room_id
                )
                crypt_floor_parser = mythic_crypt_floor_number
                crypt_floor_builder = mythic_crypt_floor_id
                crypt_down_label = "Mitycznej Krypty"
            if current_crypt_floor is None:
                await self.send(
                    "walk krypta dół działa wewnątrz zwykłej albo Mitycznej Krypty. "
                    "Najpierw wejdź na jej piętro."
                )
                return
            crypt_down_floor = current_crypt_floor + 1
            canonical_floor = crypt_floor_builder(current_crypt_floor)
            self.server.world.ensure_runtime_room(canonical_floor)

            # Szukamy prawdziwej komnaty tej samej rodziny lochu, z której
            # wyjście `down` prowadzi na kolejne piętro.
            crypt_target = None
            for room_id, room in ROOMS.items():
                if crypt_floor_parser(room_id) != current_crypt_floor:
                    continue
                next_room = room.get("exits", {}).get("down")
                if crypt_floor_parser(next_room) == crypt_down_floor:
                    crypt_target = room_id
                    break
            if crypt_target is None:
                await self.send(
                    f"Nie udało się odnaleźć zejścia na tym piętrze {crypt_down_label}."
                )
                return

            target_is_treasure = False
            treasure_label = ""
            npc_match = None
            target_is_npc = False
            target_npc = None
            matches = [crypt_target]
            direct_crypt_down = True
            direct_floor_parser_v11340 = crypt_floor_parser
            direct_floor_number_v11340 = current_crypt_floor

        # v1.13.40: `walk wieża góra` działa w zwykłej i Mitycznej
        # Wieży Astralnej. Zatrzymuje się przed końcowym `up`.
        astral_up_requested = normalized in (
            "wieza gora", "wieza w gore", "wieza up",
            "wieza astralna gora", "wieza astralna w gore",
            "astral gora", "astral up", "tower up",
            "mityczna wieza gora", "mityczna wieza w gore",
            "mityczna wieza astralna gora", "mityczna wieza astralna w gore",
            "mythic astral up", "mythic astral tower up", "mythic tower up",
            # Celowo obsługujemy też częstą literówkę.
            "wierza gora", "wierza w gore", "wierza up",
            "mityczna wierza gora", "mityczna wierza w gore",
        )
        direct_astral_up = False
        astral_up_floor = None
        astral_up_label = "Wieży Astralnej"
        if astral_up_requested:
            current_astral_floor = astral_floor_number(self.character.room_id)
            astral_floor_parser = astral_floor_number
            astral_floor_builder = astral_floor_id
            if current_astral_floor is None:
                current_astral_floor = mythic_astral_floor_number(
                    self.character.room_id
                )
                astral_floor_parser = mythic_astral_floor_number
                astral_floor_builder = mythic_astral_floor_id
                astral_up_label = "Mitycznej Wieży Astralnej"
            if current_astral_floor is None:
                await self.send(
                    "walk wieża góra działa wewnątrz zwykłej albo Mitycznej "
                    "Wieży Astralnej. Najpierw wejdź na jej poziom."
                )
                return

            astral_up_floor = current_astral_floor + 1
            canonical_floor = astral_floor_builder(current_astral_floor)
            self.server.world.ensure_runtime_room(canonical_floor)

            astral_target = None
            for room_id, room in ROOMS.items():
                if astral_floor_parser(room_id) != current_astral_floor:
                    continue
                next_room = room.get("exits", {}).get("up")
                if astral_floor_parser(next_room) == astral_up_floor:
                    astral_target = room_id
                    break
            if astral_target is None:
                await self.send(
                    f"Nie udało się odnaleźć wejścia w górę na tym poziomie "
                    f"{astral_up_label}."
                )
                return

            target_is_treasure = False
            treasure_label = ""
            npc_match = None
            target_is_npc = False
            target_npc = None
            matches = [astral_target]
            direct_astral_up = True
            direct_floor_parser_v11340 = astral_floor_parser
            direct_floor_number_v11340 = current_astral_floor

        # Twierdza Gigantów: ten sam model, ale kierunek progresji to up.
        fortress_up_requested = normalized in (
            "twierdza gora", "twierdza w gore", "twierdza up",
            "twierdza gigantow gora", "twierdza gigantow w gore",
            "giant fortress up", "fortress up",
        )
        direct_fortress_up = False
        fortress_up_floor = None
        if fortress_up_requested:
            current_fortress_floor = giant_fortress_floor_number(
                self.character.room_id
            )
            if current_fortress_floor is None:
                await self.send(
                    "walk twierdza góra działa wewnątrz Twierdzy Gigantów. "
                    "Najpierw wejdź na jej piętro."
                )
                return
            fortress_up_floor = current_fortress_floor + 1
            self.server.world.ensure_runtime_room(
                giant_fortress_floor_id(current_fortress_floor)
            )
            fortress_target = None
            for room_id, room in ROOMS.items():
                if giant_fortress_floor_number(room_id) != current_fortress_floor:
                    continue
                next_room = room.get("exits", {}).get("up")
                if giant_fortress_floor_number(next_room) == fortress_up_floor:
                    fortress_target = room_id
                    break
            if fortress_target is None:
                await self.send(
                    "Nie udało się odnaleźć wejścia w górę na tym piętrze "
                    "Twierdzy Gigantów."
                )
                return
            target_is_treasure = False
            treasure_label = ""
            npc_match = None
            target_is_npc = False
            target_npc = None
            matches = [fortress_target]
            direct_fortress_up = True
            direct_floor_parser_v11340 = giant_fortress_floor_number
            direct_floor_number_v11340 = current_fortress_floor

        # UOSS Deep Dungeon: zejście jest down; na progach co 25 pięter
        # ostatni ręczny krok nadal respektuje blokadę Apandy.
        deep_down_requested = normalized in (
            "deep dol", "deep w dol", "deep down",
            "deep dungeon dol", "deep dungeon w dol", "deep dungeon down",
            "deep dool", "deep dungeon dool",
        )
        direct_deep_down = False
        deep_down_floor = None
        if deep_down_requested:
            current_deep_floor = uoss_deep_dungeon_floor_number_v11331(
                self.character.room_id
            )
            if current_deep_floor is None:
                await self.send(
                    "walk deep dół działa wewnątrz UOSS Deep Dungeon. "
                    "Najpierw wejdź na jego piętro."
                )
                return
            deep_down_floor = current_deep_floor + 1
            self.server.world.ensure_runtime_room(
                uoss_deep_dungeon_floor_id_v11331(current_deep_floor)
            )
            deep_target = None
            for room_id, room in ROOMS.items():
                if uoss_deep_dungeon_floor_number_v11331(room_id) != current_deep_floor:
                    continue
                next_room = room.get("exits", {}).get("down")
                if (
                    uoss_deep_dungeon_floor_number_v11331(next_room)
                    == deep_down_floor
                ):
                    deep_target = room_id
                    break
            if deep_target is None:
                await self.send(
                    "Nie udało się odnaleźć zejścia na tym piętrze Deep Dungeon."
                )
                return
            target_is_treasure = False
            treasure_label = ""
            npc_match = None
            target_is_npc = False
            target_npc = None
            matches = [deep_target]
            direct_deep_down = True
            direct_floor_parser_v11340 = uoss_deep_dungeon_floor_number_v11331
            direct_floor_number_v11340 = current_deep_floor

        # v0.24.0: aktywny trop Mapy Skarbu jest celem zależnym od postaci,
        # więc nie może być zwykłym globalnym aliasem pokoju.
        direct_floor_edge = (
            direct_crypt_down
            or direct_astral_up
            or direct_fortress_up
            or direct_deep_down
            or direct_generic_down
        )
        treasure_match = None if direct_floor_edge else re.fullmatch(
            r"(?:skarb|skarbu|treasure)(?:\s+(\d+))?", normalized
        )
        if not direct_floor_edge:
            target_is_treasure = treasure_match is not None
            treasure_label = ""
        if direct_floor_edge:
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
            if direct_generic_down:
                await self.send(
                    f"Już jesteś przed przejściem na piętro {generic_down_floor} "
                    f"({generic_down_label}). Wykonaj ostatni krok ręcznie: "
                    f"{self.route_direction_name(generic_down_direction)}."
                )
            elif direct_crypt_down:
                await self.send(
                    f"Już jesteś przed zejściem na piętro {crypt_down_floor} {crypt_down_label}. "
                    "Wykonaj zejście ręcznie."
                )
            elif direct_astral_up:
                await self.send(
                    f"Już jesteś przed wejściem na poziom {astral_up_floor} "
                    f"{astral_up_label}. Wykonaj wejście w górę ręcznie."
                )
            elif direct_fortress_up:
                await self.send(
                    f"Już jesteś przed wejściem na piętro {fortress_up_floor} "
                    "Twierdzy Gigantów. Wykonaj wejście w górę ręcznie."
                )
            elif direct_deep_down:
                await self.send(
                    f"Już jesteś przed zejściem na piętro {deep_down_floor} "
                    "Deep Dungeon. Wykonaj zejście ręcznie."
                )
            elif target_is_npc:
                await self.send(
                    f"NPC {target_npc['name']} jest już tutaj: "
                    f"{ROOMS[target]['name']}."
                )
            else:
                await self.send(f"Już jesteś tutaj: {ROOMS[target]['name']}.")
            return

        if direct_generic_down:
            full_path = self.shortest_path_within_floor_v11340(
                self.character.room_id, target,
                generic_down_parser, generic_down_number,
            )
        elif direct_floor_edge and direct_floor_parser_v11340 is not None:
            full_path = self.shortest_path_within_floor_v11340(
                self.character.room_id,
                target,
                direct_floor_parser_v11340,
                direct_floor_number_v11340,
            )
        else:
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
        self._mercenary_guide_announced_v12210 = False
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
        elif direct_generic_down:
            await self.send(
                f"Prowadzę przed przejście na piętro {generic_down_floor} "
                f"({generic_down_label}). Automatyczne przejścia: {len(path)}. "
                f"Ostatni krok wykonujesz ręcznie: "
                f"{self.route_direction_name(generic_down_direction)}."
            )
        elif direct_crypt_down:
            await self.send(
                f"Prowadzę przed zejście na piętro {crypt_down_floor} {crypt_down_label}. "
                f"Automatyczne przejścia: {len(path)}. "
                "Ostatnie zejście wykonujesz ręcznie."
            )
        elif direct_astral_up:
            await self.send(
                f"Prowadzę przed wejście na poziom {astral_up_floor} {astral_up_label}. "
                f"Automatyczne przejścia: {len(path)}. "
                "Ostatnie wejście w górę wykonujesz ręcznie."
            )
        elif direct_fortress_up:
            await self.send(
                f"Prowadzę przed wejście na piętro {fortress_up_floor} Twierdzy Gigantów. "
                f"Automatyczne przejścia: {len(path)}. "
                "Ostatnie wejście w górę wykonujesz ręcznie."
            )
        elif direct_deep_down:
            await self.send(
                f"Prowadzę przed zejście na piętro {deep_down_floor} Deep Dungeon. "
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
            elif direct_generic_down and self.character.room_id == target:
                await self.send(
                    f"Dotarłeś przed przejście na piętro {generic_down_floor} "
                    f"({generic_down_label}). Wykonaj ostatni krok ręcznie: "
                    f"{self.route_direction_name(generic_down_direction)}."
                )
                await self.look()
            elif direct_crypt_down and self.character.room_id == target:
                await self.send(
                    f"Dotarłeś przed zejście na piętro {crypt_down_floor} {crypt_down_label}. "
                    "Wykonaj zejście ręcznie."
                )
                await self.look()
            elif direct_astral_up and self.character.room_id == target:
                await self.send(
                    f"Dotarłeś przed wejście na poziom {astral_up_floor} "
                    f"{astral_up_label}. Wykonaj wejście w górę ręcznie."
                )
                await self.look()
            elif direct_fortress_up and self.character.room_id == target:
                await self.send(
                    f"Dotarłeś przed wejście na piętro {fortress_up_floor} "
                    "Twierdzy Gigantów. Wykonaj wejście w górę ręcznie."
                )
                await self.look()
            elif direct_deep_down and self.character.room_id == target:
                await self.send(
                    f"Dotarłeś przed zejście na piętro {deep_down_floor} "
                    "Deep Dungeon. Wykonaj zejście ręcznie."
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

