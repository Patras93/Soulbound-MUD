# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def show_profession_ranks(self):
        for profession in (
            "Wędkarstwo", "Górnictwo", "Drwalstwo",
            "Zielarstwo", "Gotowanie", "Alchemia",
            "Kowalstwo", "Jubilerstwo",
        ):
            await self.send(f"RANGI: {profession.upper()}")
            thresholds = profession_rank_thresholds(profession)
            max_rank = profession_max_rank(profession)
            max_level = profession_max_level(profession)

            for rank, minimum in enumerate(thresholds, 1):
                if rank < max_rank:
                    maximum = thresholds[rank] - 1
                    level_text = f"level {minimum}-{maximum}"
                else:
                    level_text = f"level {minimum}-{max_level}"

                await self.send(
                    f"Ranga {rank}: "
                    f"{PROFESSION_RANK_NAMES[profession][rank - 1]}. "
                    f"{level_text}."
                )


async def show_professions(self, mode=""):
        mode = self.normalize_description_query(mode)
        detailed = mode in (
            "info", "pelne", "pełne", "szczegoly", "szczegóły", "details"
        )
        gathering_professions = ("Wędkarstwo", "Górnictwo", "Drwalstwo", "Zielarstwo")
        crafting_professions = (
            "Gotowanie", "Alchemia", "Kowalstwo", "Jubilerstwo",
            "Krawiectwo", "Garbarstwo", "Stolarstwo", "Zaklinanie",
        )
        exploration_professions = ("Archeologia", "Kartografia")
        if mode in ("zbieractwo", "zbierackie", "gathering"):
            groups = (("ZBIERACTWO", gathering_professions),)
        elif mode in ("rzemiosla", "rzemiosła", "rzemioslo", "rzemiosło", "crafting"):
            groups = (("RZEMIOSŁA", crafting_professions),)
        elif mode in ("eksploracyjne", "eksploracja", "exploration"):
            groups = (("EKSPLORACJA", exploration_professions),)
        else:
            groups = (
                ("ZBIERACTWO", gathering_professions),
                ("RZEMIOSŁA", crafting_professions),
                ("EKSPLORACJA", exploration_professions),
            )
        await self.send("PROFESJE INFO" if detailed else "PROFESJE")
        for group_name, professions in groups:
            await self.send(group_name)
            for name in professions:
                row = self.server.db.profession(self.account_id, name)
                level = int(row["level"])
                max_level = profession_max_level(name)
                rank = profession_rank(level, name)
                max_rank = profession_max_rank(name)
                rank_name = profession_rank_name(name, level)
                if not detailed:
                    await self.send(
                        f"{name}: poziom {level}/{max_level}, ranga {rank}/{max_rank}: {rank_name}."
                    )
                    continue
                thresholds = profession_rank_thresholds(name)
                if rank < max_rank:
                    next_rank = f"Następna ranga od levelu {thresholds[rank]}."
                else:
                    next_rank = "Ranga maksymalna."
                xp_text = (
                    "maksimum" if level >= max_level else
                    f"{row['xp']} z {self.profession_xp_to_next(level, name)}"
                )
                await self.send(
                    f"{name}: poziom {level}/{max_level}. Ranga {rank}/{max_rank}: {rank_name}. "
                    f"XP {xp_text}. Akcje {row['actions']}. {next_rank}"
                )
        if detailed:
            await self.send(
                "Maksimum wszystkich czternastu profesji: poziom 600."
            )
            await self.send(
                "Poziom profesji skraca czas pracy i blokuje receptury/zlecenia. "
                "Poziom narzędzia odblokowuje lepsze surowce oraz zwiększa rare/quality i bonus urobku. "
                "Wpisz narzedzia info po Tiery i bonusy."
            )
        else:
            await self.send("Wpisz profesje info po XP, akcje, progi rang i zasady. Możesz też użyć profesje zbieractwo, profesje rzemiosla albo profesje eksploracja.")


async def show_tool_tiers(self):
        for tool_type, title in (
            ("fishing", "WĘDKI"),
            ("mining", "KILOFA"),
            ("woodcutting", "PIŁY"),
            ("crafting", "MŁOTA RZEMIEŚLNICZEGO"),
            ("cooking", "NOŻA KUCHARSKIEGO"),
            ("herbalism", "SIERPA ZIELARSKIEGO"),
            ("alchemy", "MOŹDZIERZA ALCHEMICZNEGO"),
            ("jewelcrafting", "SZCZYPIEC JUBILERSKICH"),
            ("tailoring", "ZESTAWU KRAWIECKIEGO"),
            ("leatherworking", "NOŻA GARBARSKIEGO"),
            ("carpentry", "NARZĘDZI CIESIELSKICH"),
            ("enchanting", "FOKUSU RUNICZNEGO"),
            ("archaeology", "PĘDZLA ARCHEOLOGA"),
            ("cartography_profession", "KOMPASU MIERNICZEGO"),
        ):
            await self.send(f"NAZWY TIERÓW {title}")
            for tier, minimum in enumerate(TOOL_TIER_THRESHOLDS, 1):
                if tier < TOOL_MAX_TIER:
                    maximum = TOOL_TIER_THRESHOLDS[tier] - 1
                    level_text = f"level {minimum}-{maximum}"
                else:
                    level_text = f"level {minimum}"
                bonus = int(TOOL_TIER_BONUS_CHANCES[tier - 1] * 100)
                await self.send(
                    f"Tier {tier}: {TOOL_TIER_NAMES[tool_type][tier - 1]}. "
                    f"{level_text}. Bonus {bonus} procent."
                )


def tool_info_definition(self, tool_type):
        definitions = {
            "fishing": ("fishing_rod", "Wędka"),
            "mining": ("pickaxe", "Kilof"),
            "woodcutting": ("saw", "Piła"),
            "crafting": ("crafting_hammer", "Młot Rzemieślniczy"),
            "cooking": ("chef_knife", "Nóż Kucharski"),
            "herbalism": ("herbalist_sickle", "Sierp Zielarski"),
            "alchemy": ("alchemy_mortar", "Moździerz Alchemiczny"),
            "jewelcrafting": ("jeweler_pliers", "Szczypce Jubilerskie"),
            "tailoring": ("tailor_kit", "Zestaw Krawiecki"),
            "leatherworking": ("tanning_knife", "Nóż Garbarski"),
            "carpentry": ("carpenter_tools", "Narzędzia Ciesielskie"),
            "enchanting": ("runic_focus", "Fokus Runiczny"),
            "archaeology": ("archaeology_brush", "Pędzel Archeologa"),
            "cartography_profession": ("surveyor_compass", "Kompas Mierniczy"),
        }
        return definitions.get(tool_type)


def tool_bonus_label(self, tool_type):
        if tool_type == "cooking":
            return "Szansa na dodatkową potrawę"
        if tool_type == "crafting":
            return "Szansa na dodatkowy produkt receptury"
        if tool_type == "alchemy":
            return "Szansa na dodatkową miksturę"
        if tool_type == "herbalism":
            return "Szansa na dodatkowe zioło"
        if tool_type == "jewelcrafting":
            return "Szansa na dodatkową biżuterię"
        if tool_type == "archaeology":
            return "Szansa na dodatkowe znalezisko"
        if tool_type == "cartography_profession":
            return "Szansa na Fragment Mapy Rubieży"
        return "Bonus dodatkowego urobku"


def tool_action_label(self, tool_type):
        return {
            "fishing": "Czas zarzucenia i połowu",
            "mining": "Czas wydobycia",
            "woodcutting": "Czas cięcia",
            "crafting": "Czas wytwarzania",
            "cooking": "Czas gotowania",
            "herbalism": "Czas zbioru",
            "alchemy": "Czas warzenia",
            "jewelcrafting": "Czas wykonania biżuterii",
            "tailoring": "Czas szycia",
            "leatherworking": "Czas garbowania",
            "carpentry": "Czas pracy stolarskiej",
            "enchanting": "Czas zaklinania",
            "archaeology": "Czas wykopalisk",
            "cartography_profession": "Czas pomiaru",
        }.get(tool_type, "Czas akcji")


async def show_single_tool(self, tool_type):
        definition = self.tool_info_definition(tool_type)
        if not definition:
            await self.send("Nieznane narzędzie.")
            return

        item_id, name = definition
        owned = self.server.db.item_qty(self.account_id, item_id) > 0
        if not owned:
            await self.send(f"{name}: nie posiadasz tego narzędzia.")
            if tool_type == "fishing":
                await self.send(
                    "Wędkę kupisz tylko u Mistrza Wędkarstwa Nerisa "
                    "w Szkole Wędkarstwa."
                )
            elif tool_type == "mining":
                await self.send(
                    "Kilof kupisz tylko u Górnika Torena przy "
                    "Wejściu do Kryształowej Jaskini."
                )
            elif tool_type == "woodcutting":
                await self.send(
                    "Piłę kupisz tylko u Mistrza Drwalstwa Orena "
                    "w Leśniczówce."
                )
            elif tool_type == "crafting":
                await self.send(
                    "Młot Rzemieślniczy kupisz tylko u Mistrza "
                    "Rzemiosła Haldora w Warsztacie Rzemieślniczym."
                )
            elif tool_type == "cooking":
                await self.send(
                    "Nóż Kucharski kupisz tylko u Kucharza Marcela "
                    "w Kuchni Błękitnego Płomienia."
                )
            elif tool_type == "herbalism":
                await self.send(
                    "Sierp Zielarski kupisz tylko u Mistrzyni "
                    "Zielarstwa Seny w Ogrodzie Zielarskim."
                )
            elif tool_type == "alchemy":
                await self.send(
                    "Moździerz Alchemiczny kupisz tylko u Mistrza "
                    "Alchemii Orina w Laboratorium Alchemicznym."
                )
            elif tool_type == "jewelcrafting":
                await self.send(
                    "Szczypce Jubilerskie kupisz tylko u Jubilerki Mirelli "
                    "w Pracowni Jubilerskiej."
                )
            elif tool_type == "archaeology":
                await self.send(
                    "Pędzel Archeologa kupisz tylko u Archeolożki Miry "
                    "w Bibliotece. Kupuje się go tylko raz na postać."
                )
            elif tool_type == "cartography_profession":
                await self.send(
                    "Kompas Mierniczy kupisz tylko u Mistrzyni Kartografii Aleny "
                    "w Archiwum Rubieży. Kupuje się go tylko raz na postać."
                )
            return

        row = self.server.db.tool(self.account_id, tool_type)
        level = int(row["level"])
        xp = int(row["xp"])
        uses = int(row["uses"])
        tier = tool_tier(level)
        max_level = tool_max_level(tool_type)
        tier_name = tool_tier_name(tool_type, level)
        bonus_percent = int(tool_tier_bonus_chance(level) * 100)
        bonus_label = self.tool_bonus_label(tool_type)

        await self.send(f"NARZĘDZIE: {name}.")
        await self.send(
            f"Aktualna nazwa narzędzia: {tier_name}."
        )
        await self.send(
            f"Poziom: {level} z {max_level}. "
            f"Użycia: {uses}."
        )
        profession = profession_for_tool_type(tool_type)
        profession_level = self.profession_level_for_tool(tool_type)
        await self.send(
            f"{self.tool_action_label(tool_type)}: "
            f"{self.profession_action_seconds(tool_type, profession_level)} sekund. "
            f"Tempo daje {profession} poziom {profession_level}; poziom narzędzia nie skraca czasu."
        )

        if level >= max_level:
            await self.send("XP: maksimum. Do następnego levelu: maksimum.")
        else:
            needed = self.tool_xp_to_next(level, tool_type)
            remaining = self.tool_xp_remaining_to_level(level, xp, tool_type)
            await self.send(
                f"XP obecnego levelu: {xp} z {needed}. "
                f"Do następnego levelu brakuje {remaining} XP."
            )

        await self.send(
            f"Obecny Tier: {tier} z {TOOL_MAX_TIER}. "
            f"Nazwa: {tier_name}. "
            f"{bonus_label}: {bonus_percent} procent."
        )

        if tier >= TOOL_MAX_TIER:
            await self.send("Tier maksymalny. Nie ma następnego Tieru.")
        else:
            target_level = TOOL_TIER_THRESHOLDS[tier]
            next_tier = tier + 1
            next_name = TOOL_TIER_NAMES[tool_type][next_tier - 1]
            levels_remaining, xp_remaining = (
                self.tool_xp_remaining_to_next_tier(
                    level, xp, tool_type
                )
            )
            await self.send(
                f"Następny Tier: {next_tier}, {next_name}, "
                f"od levelu {target_level}. "
                f"Brakuje {levels_remaining} leveli i łącznie "
                f"{xp_remaining} XP narzędzia."
            )

        await self.send(f"TIERY NARZĘDZIA: {name}.")
        for tier_number, minimum in enumerate(TOOL_TIER_THRESHOLDS, 1):
            if tier_number < TOOL_MAX_TIER:
                maximum = TOOL_TIER_THRESHOLDS[tier_number] - 1
                level_text = f"level {minimum}-{maximum}"
            else:
                if tool_type == "crafting":
                    level_text = (
                        f"level {minimum}-{TOOL_MAX_LEVEL}"
                    )
                else:
                    level_text = f"level {minimum}-{TOOL_MAX_LEVEL}"

            tier_bonus = int(
                TOOL_TIER_BONUS_CHANCES[tier_number - 1] * 100
            )
            marker = " Obecny." if tier_number == tier else ""
            await self.send(
                f"Tier {tier_number}: "
                f"{TOOL_TIER_NAMES[tool_type][tier_number - 1]}. "
                f"{level_text}. Bonus {tier_bonus} procent.{marker}"
            )


async def show_tools(self, mode=""):
        mode = self.normalize_description_query(mode)
        detailed = mode in (
            "info", "pelne", "pełne", "szczegoly", "szczegóły", "details"
        )
        tools = [
            ("fishing", "fishing_rod", "Wędka", "Neris", "Szkoła Wędkarstwa"),
            ("mining", "pickaxe", "Kilof", "Toren", "Wejście do Kryształowej Jaskini"),
            ("woodcutting", "saw", "Piła", "Oren", "Leśniczówka"),
            ("crafting", "crafting_hammer", "Młot Rzemieślniczy", "Haldor", "Warsztat Rzemieślniczy"),
            ("cooking", "chef_knife", "Nóż Kucharski", "Marcel", "Kuchnia Błękitnego Płomienia"),
            ("herbalism", "herbalist_sickle", "Sierp Zielarski", "Sena", "Ogród Zielarski"),
            ("alchemy", "alchemy_mortar", "Moździerz Alchemiczny", "Orin", "Laboratorium Alchemiczne"),
            ("jewelcrafting", "jeweler_pliers", "Szczypce Jubilerskie", "Mirella", "Pracownia Jubilerska"),
            ("tailoring", "tailor_kit", "Zestaw Krawiecki", "Lysa", "Pracownia Krawiecka"),
            ("leatherworking", "tanning_knife", "Nóż Garbarski", "Soren", "Warsztat Kaletnika"),
            ("carpentry", "carpenter_tools", "Narzędzia Ciesielskie", "Edric", "Warsztat Ciesielski"),
            ("enchanting", "runic_focus", "Fokus Runiczny", "Kwatermistrz Arkanów", "Komnata Arkanów"),
            ("archaeology", "archaeology_brush", "Pędzel Archeologa", "Archeolożka Elara", "Biblioteka"),
            ("cartography_profession", "surveyor_compass", "Kompas Mierniczy", "Mistrzyni Kartografii Alena", "Archiwum Rubieży"),
        ]
        await self.send("NARZĘDZIA INFO" if detailed else "NARZĘDZIA")
        for tool_type, item_id, name, seller, location in tools:
            owned = self.server.db.item_qty(self.account_id, item_id) > 0
            if not owned:
                if detailed:
                    await self.send(f"{name}: brak. Sprzedawca: {seller}, {location}.")
                else:
                    await self.send(f"{name}: brak.")
                continue
            row = self.server.db.tool(self.account_id, tool_type)
            level = int(row["level"])
            max_level = tool_max_level(tool_type)
            tier = tool_tier(level)
            tier_name = tool_tier_name(tool_type, level)
            if not detailed:
                await self.send(
                    f"{name}: poziom {level}/{max_level}, Tier {tier}/{TOOL_MAX_TIER}: {tier_name}."
                )
                continue
            bonus_percent = int(tool_tier_bonus_chance(level) * 100)
            xp_text = (
                "maksimum" if level >= max_level else
                f"{row['xp']} z {self.tool_xp_to_next(level, tool_type)}"
            )
            if tier < TOOL_MAX_TIER:
                next_text = f"Następny Tier od levelu {TOOL_TIER_THRESHOLDS[tier]}."
            else:
                next_text = "Tier maksymalny."
            await self.send(
                f"{name}: {tier_name}. Poziom {level}/{max_level}. Tier {tier}/{TOOL_MAX_TIER}. "
                f"XP {xp_text}. Użycia {row['uses']}. "
                f"{self.tool_action_label(tool_type)}: {self.profession_action_seconds(tool_type, self.profession_level_for_tool(tool_type))} sekund "
                f"(tempo z {profession_for_tool_type(tool_type)}). "
                f"{self.tool_bonus_label(tool_type)}: {bonus_percent} procent. {next_text} "
                f"Sprzedawca: {seller}, {location}."
            )
        if detailed:
            await self.send(
                "Każde narzędzie sprzedaje wyłącznie NPC własnej profesji. Narzędzia nie mają durability."
            )
        else:
            await self.send("Wpisz narzedzia info po XP, bonusy, czas akcji i sprzedawców.")


def fishing_water_type(self, room_id=None):
        room_id = room_id or self.character.room_id
        if room_id not in FISHING_ROOMS:
            if self.character and room_id == self.character.room_id and self.active_event_fishery_v3312():
                return {"river":"Rzeka", "lake":"Jezioro", "sea":"Morze", "ocean":"Ocean"}.get(self.fishing_habitat(room_id))
            return None
        if room_id in FISHING_WATER_TYPE_OVERRIDES:
            return FISHING_WATER_TYPE_OVERRIDES[room_id]
        dungeon, _floor = profession_dungeon_floor(room_id)
        if dungeon == "sunken_grotto":
            return "Zatopiona grota"
        if room_id in RIVER_FISHING_ROOMS:
            return "Rzeka"
        if room_id in LAKE_FISHING_ROOMS:
            return "Jezioro"
        if room_id in SEA_FISHING_ROOMS:
            return "Morze"
        if room_id in OCEAN_FISHING_ROOMS:
            if ROOMS.get(room_id, {}).get("deep_ocean_fishing"):
                return "Głęboki ocean"
            return "Ocean"
        return "Łowisko"


def fishing_ecology_pool(self, tool_level, habitat=None, room_id=None):
        room_id = room_id or self.character.room_id
        habitat = habitat or self.fishing_habitat(room_id)
        tool_level = max(1, min(TOOL_MAX_LEVEL, int(tool_level)))
        if not habitat:
            return ()
        dungeon, dungeon_floor = profession_dungeon_floor(room_id)
        effective_level = tool_level
        if dungeon == "sunken_grotto":
            effective_level = min(tool_level, max(1, int(dungeon_floor) * 10))
        # v0.30.39: ekologia łowiska nie wycina już odblokowanych gatunków.
        # v1.00.0: gatunki głębinowe są częścią Wędkarstwa 1-600, ale
        # występują wyłącznie w sektorach Ocean 2.0 oznaczonych deep_ocean_fishing.
        pool = tuple(self.fishing_available_pool(effective_level, habitat))
        is_deep = bool(ROOMS.get(room_id, {}).get("deep_ocean_fishing"))
        # Deep-ocean unlocks use their authored min_tool_level directly.
        # Generator Core may normalize economy/generator_level later, but that
        # must never move Fishing unlock thresholds away from 300-600.
        base_pool = [item_id for item_id in pool if not ITEMS.get(item_id, {}).get("deep_ocean")]
        if is_deep:
            deep_ids = sorted(
                item_id for item_id, item in ITEMS.items()
                if item.get("deep_ocean")
                and effective_level >= int(item.get("min_tool_level", 1) or 1)
            )
            for item_id in deep_ids:
                if item_id not in base_pool:
                    base_pool.append(item_id)
        return tuple(base_pool)


def fishing_loot(self, tool_level, habitat="river"):
        room_id = self.character.room_id
        pool = self.fishing_ecology_pool(tool_level, habitat=habitat, room_id=room_id)
        if not pool:
            return None
        weights = balance_math.resource_weights(
            pool, ITEMS, tool_level, f"fishing:{habitat}:{room_id}"
        )
        preferred = FISHING_ECOLOGY_PREFERRED_IDS.get(room_id) or set()
        if preferred:
            # Typowe gatunki danego stanowiska są częstsze, ale żaden wcześniej
            # odblokowany gatunek tego habitatu nie dostaje wagi 0.
            weights = [
                float(weight) * (2.75 if item_id in preferred else 1.0)
                for item_id, weight in zip(pool, weights)
            ]
        return random.choices(pool, weights=weights, k=1)[0]


async def show_water_info(self):
        habitat = self.fishing_habitat()
        water_type = self.fishing_water_type()
        if not habitat or not water_type:
            await self.send(
                "Tutaj nie ma łowiska. Komenda woda działa tylko w miejscu, "
                "w którym można łowić."
            )
            return

        tool = self.server.db.tool(self.account_id, "fishing")
        tool_level = int(tool["level"])
        pool = tuple(self.fishing_ecology_pool(tool_level, habitat=habitat, room_id=self.character.room_id))
        room = ROOMS.get(self.character.room_id, {})
        await self.send(
            f"ŁOWISKO: {water_type}. Lokacja: {room.get('name') or 'Nieznana lokacja'}."
        )
        await self.send(
            f"Ekosystem ryb: {FISHING_HABITAT_LABELS.get(habitat, habitat)}. "
            f"Wędka poziom {tool_level}, Tier {tool_tier(tool_level)}. "
            f"Dostępnych teraz gatunków: {len(pool)}."
        )

        known = self.server.db.fish_journal_ids(self.account_id)
        pool_species = {base_fish_species_id(item_id) for item_id in pool}
        known_here = sorted(
            pool_species & known,
            key=lambda item_id: normalize_lookup_text(ITEMS[item_id]["name"]),
        )
        unknown_count = max(0, len(pool_species) - len(known_here))
        await self.send(
            f"Dziennik ryb w tym łowisku: odkryte {len(known_here)}, "
            f"nieodkryte {unknown_count}."
        )
        if known_here:
            await self.send(
                "Znane gatunki tutaj: "
                + ", ".join(ITEMS[item_id]["name"] for item_id in known_here)
                + "."
            )

        habitat_ids = {
            "river": tuple(RIVER_FISH_ATLAS), "lake": tuple(LAKE_FISH_ATLAS),
            "sea": tuple(SEA_FISH_ATLAS), "ocean": tuple(OCEAN_FISH_ATLAS),
        }.get(habitat, ())
        locked = sorted(
            (int(ITEMS[iid].get("generator_level", 1) or 1), iid)
            for iid in habitat_ids if iid in ITEMS
            if int(ITEMS[iid].get("generator_level", 1) or 1) > tool_tier_access_level(tool_level)
        )
        if locked:
            next_level, next_item = locked[0]
            await self.send(
                f"Kolejny gatunek wymaga wyższego Tieru Wędki; "
                f"najbliższy próg zasobu to poziom {next_level}: {ITEMS[next_item]['name']}."
            )
        else:
            await self.send("Masz odblokowane wszystkie ryby tego ekosystemu.")

        await self.send(
            "Ryby nie mają twardego limitu sztuk. Łowisko nie wyczerpuje się od łowienia."
        )

