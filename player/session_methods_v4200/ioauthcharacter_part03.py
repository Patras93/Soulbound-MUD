# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def character_creator(self):
        await self.send("KREATOR POSTACI")
        while True:
            name = await self.ask("Nazwa postaci, 3-20 znaków: ")
            if name is None:
                return False
            name = name.strip()
            if not safe_name(name) or self.server.db.character_name_exists(name):
                await self.send("Nieprawidłowa lub zajęta nazwa.")
                continue
            break

        genders = ("kobieta", "mężczyzna")
        await self.send("Wybierz płeć postaci: 1. kobieta. 2. mężczyzna.")
        gender = await self.choose_number(genders, "Numer płci: ")
        if gender is None:
            return False
        await self.send(f"Wybrana płeć: {gender}.")

        await self.send("Wybierz rasę:")
        await self.send(
            "Driada jest rasą wyłącznie kobiecą. "
            "Znaczenie statystyk: Siła zwiększa atak fizyczny; "
            "Zręczność zwiększa szybkość i unik; Kondycja zwiększa HP; "
            "Inteligencja zwiększa Manę i moc czarów; "
            "Siła Woli zwiększa obronę magiczną; "
            "Charyzma zwiększa rabat sklepowy i limit drużyny."
        )
        for i, race in enumerate(RACES, 1):
            rname, desc, s, d, c, inte, w = race
            advice = race_class_recommendation_text(rname)
            restriction = " Tylko kobieta." if rname == "Driada" else ""
            await self.send(
                f"{i}. {rname}.{restriction} {desc} Siła {s}, Zręczność {d}, Kondycja {c}, "
                f"Inteligencja {inte}, Siła Woli {w}, Charyzma 10. {advice}"
            )
        while True:
            race = await self.choose_number(RACES, "Numer rasy: ")
            if race is None:
                return False
            selected_race_name = race[0]
            if selected_race_name == "Driada" and gender != "kobieta":
                await self.send(
                    "Driadą może być wyłącznie kobieta. Wybierz inną rasę albo wróć do kreatora i wybierz płeć kobieta."
                )
                continue
            break
        await self.send(
            f"Wybrana rasa: {selected_race_name}. {race_class_recommendation_text(selected_race_name)} "
            "To tylko rekomendacja. Możesz wybrać dowolną z 14 klas."
        )
        await self.send("Wybierz klasę:")
        for i, cls in enumerate(CLASSES, 1):
            cname, ctype, weapon, _ = cls
            kind = "fizyczna" if ctype == "physical" else "magiczna"
            desc = CLASS_DESCRIPTIONS.get(cname, "")
            growth = (
                "Rozwój: wszystkie statystyki automatycznie: Siła, Zręczność, "
                "Kondycja, Inteligencja, Siła Woli i Charyzma. Każda klasa ma HP i Manę; "
                "Inteligencja zwiększa Manę także klasom fizycznym."
            )
            await self.send(
                f"{i}. {cname}. Typ {kind}. {desc} "
                f"{growth} Broń Duszy: {weapon}."
            )
        cls = await self.choose_number(CLASSES, "Numer klasy: ")
        if cls is None:
            return False

        preview_stats = class_starting_stats_for(race, cls)
        preview_hp, preview_mana = starting_hp_mana_for(race, cls)
        await self.send(
            f"Start {race[0]} / {cls[0]}. "
            f"Siła {preview_stats['strength']}, Zręczność {preview_stats['dexterity']}, "
            f"Kondycja {preview_stats['constitution']}, Inteligencja {preview_stats['intelligence']}, "
            f"Siła Woli {preview_stats['willpower']}, Charyzma {preview_stats['charisma']}. "
            f"Startowe HP {preview_hp}. Startowa Mana {preview_mana}."
        )

        name_cases = await self.ask_name_declension(name)
        if name_cases is None:
            return False

        try:
            character_account_id, slot = self.server.db.create_character_for_master(
                self.master_account_id, name, race, cls, name_cases, gender=gender
            )
        except ValueError as exc:
            if str(exc) == "character_limit":
                await self.send(
                    "Na jednym koncie można mieć maksymalnie 14 postaci."
                )
                return False
            if str(exc) == "dryad_female_only":
                await self.send(
                    "Nie można utworzyć tej postaci: Driadą może być wyłącznie kobieta."
                )
                return False
            raise
        self.account_id = int(character_account_id)
        self.character = Character.from_row(
            self.server.db.character_for_account(self.account_id)
        )
        _guild_after_create = self.server.db.ensure_character_guild_from_master_v0345(
            self.master_account_id, self.account_id
        )
        self.refresh_guild_bonus_v0926()
        self.server.db.apply_shared_wallet_to_character(self.character)
        await self.send(
            f"Utworzono postać {self.character.name}. Płeć: {self.character.gender}. W slocie {slot} z "
            f"{MAX_CHARACTERS_PER_ACCOUNT}."
        )
        if _guild_after_create.get("status") in ("joined", "already") and slot > 1:
            _grow = self.server.db.clan_membership(self.account_id)
            if _grow:
                await self.send(
                    f"Gildia konta: {_grow['name']}. Nowa postać została automatycznie przypisana jako Członek."
                )
        elif _guild_after_create.get("status") == "conflict":
            await self.send(
                "UWAGA: starsze postacie tego konta należą do różnych Gildii. "
                "Nowa postać nie została przypisana automatycznie."
            )
        await self.send(
            "Postać ma osobny Level 1-800. Sześć statystyk bazowych nadal rośnie automatycznie."
        )
        if slot == 1:
            await self.send(
                "Pierwsza postać zakłada wspólny portfel konta: 2 złota, 30 srebra. "
                "Otrzymujesz też 2 Mikstury leczenia."
            )
        else:
            await self.send(
                "Waluta jest wspólna dla wszystkich postaci na tym koncie. "
                "Ta postać korzysta z istniejącego salda: "
                + currency_reading_text(
                    self.character.silver, self.character.gold, self.character.mithril,
                    full_names=True, include_zero=True,
                )
                + ". Otrzymujesz 2 Mikstury leczenia."
            )
        return True


def start_session_summary(self):
    if not self.character or self.account_id is None:
        self._session_summary = None
        return
    stats = self.server.db.lifetime_stats(self.account_id)
    row = self.server.db.conn.execute(
        "SELECT COALESCE(MAX(id),0) AS max_id FROM drop_history WHERE account_id=?",
        (self.account_id,),
    ).fetchone()
    self._session_summary = {
        "started_at": time.time(),
        "kills_start": int(stats.get("kills_total", 0)),
        "crafted_start": int(stats.get("crafted_items", 0)),
        "profession_actions_start": int(stats.get("profession_actions", 0)),
        "drop_start_id": int(row["max_id"] or 0) if row else 0,
        "character_xp": 0,
        "class_xp": 0,
        "soul_xp": 0,
        "soul_weapon_mastery_xp": 0,
        "profession_xp": {},
        "tool_xp": {},
    }


async def show_session_summary(self):
    state = getattr(self, "_session_summary", None)
    if not state or self.account_id is None:
        return
    stats = self.server.db.lifetime_stats(self.account_id)
    kills = max(0, int(stats.get("kills_total", 0)) - int(state.get("kills_start", 0)))
    crafted = max(0, int(stats.get("crafted_items", 0)) - int(state.get("crafted_start", 0)))
    prof_actions = max(0, int(stats.get("profession_actions", 0)) - int(state.get("profession_actions_start", 0)))
    rows = self.server.db.conn.execute(
        "SELECT item_name,COUNT(*) AS qty FROM drop_history WHERE account_id=? AND id>? GROUP BY item_name ORDER BY qty DESC,item_name LIMIT 8",
        (self.account_id, int(state.get("drop_start_id", 0))),
    ).fetchall()
    drop_total_row = self.server.db.conn.execute(
        "SELECT COUNT(*) AS qty FROM drop_history WHERE account_id=? AND id>?",
        (self.account_id, int(state.get("drop_start_id", 0))),
    ).fetchone()
    drop_total = int(drop_total_row["qty"] or 0) if drop_total_row else 0
    duration = max(0, int(time.time() - float(state.get("started_at", time.time()))))
    await self.send(
        f"PODSUMOWANIE SESJI. Czas: {self.format_duration_short(duration)}. "
        f"Zabici przeciwnicy: {kills}. Wytworzone przedmioty: {crafted}. "
        f"Akcje profesji: {prof_actions}. Dropy: {drop_total}.",
        history_store=False,
    )
    xp_parts = []
    if int(state.get("character_xp", 0)):
        xp_parts.append(f"Postać {int(state['character_xp'])} XP")
    if int(state.get("class_xp", 0)):
        xp_parts.append(f"Klasy {int(state['class_xp'])} XP")
    if int(state.get("soul_xp", 0)):
        xp_parts.append(f"Soul {int(state['soul_xp'])} XP")
    if int(state.get("soul_weapon_mastery_xp", 0)):
        xp_parts.append(f"Soul Weapon Mastery {int(state['soul_weapon_mastery_xp'])} XP")
    if xp_parts:
        await self.send("Zdobyte XP: " + "; ".join(xp_parts) + ".", history_store=False)
    prof_xp = state.get("profession_xp", {}) or {}
    if prof_xp:
        text = ", ".join(f"{name} +{amount} XP" for name, amount in sorted(prof_xp.items()))
        await self.send("Profesje: " + text + ".", history_store=False)
    tool_xp = state.get("tool_xp", {}) or {}
    if tool_xp:
        _tool_names = {
            "fishing":"Wędka", "mining":"Kilof", "woodcutting":"Piła",
            "crafting":"Młot Rzemieślniczy", "cooking":"Nóż Kucharski",
            "herbalism":"Sierp Zielarski", "alchemy":"Moździerz Alchemiczny",
            "jewelcrafting":"Szczypce Jubilerskie",
        }
        text = ", ".join(f"{_tool_names.get(name, name)} +{amount} XP" for name, amount in sorted(tool_xp.items()))
        await self.send("Narzędzia: " + text + ".", history_store=False)
    if rows:
        await self.send(
            "Najczęstsze dropy: " + ", ".join(f"{row['item_name']} x{int(row['qty'])}" for row in rows) + ".",
            history_store=False,
        )


async def enter_world(self):
        self.refresh_active_classes()
        # v1.70.3: summons disappear between sessions; experience and
        # soulstone upgrades stay in SQLite. Never recast for free.
        _dismissed_summons = self._v1703_dismiss_summons_on_login()
        self.start_session_summary()
        # v0.36.3: trwały status profilu działa także po wylogowaniu.
        self.server.db.mark_player_login_v0363(self.account_id)

        moved_gems = self.migrate_raw_mining_gems_to_bag_v0867()
        moved_craft_materials = self.migrate_craft_materials_to_casket_v0915()
        level_unequipped = self.enforce_equipment_character_level()

        # Najpierw zachowaj zgodność starego mechanizmu portali Krypty
        # na podstawie lokacji zapisanej przy poprzednim wylogowaniu.
        self.server.db.sync_legacy_crypt_checkpoint(
            self.account_id, self.character.room_id
        )

        # Każde wejście do świata zaczyna się w Świątyni Odrodzenia.
        # Nie ma znaczenia, gdzie postać wylogowała się poprzednio.
        self.character.room_id = "temple"
        self.server.db.save_character(self.character)

        self.current_hp = self.max_hp()
        self.current_mana = self.max_mana()
        self.ensure_standing_regen_v1124()

        await self.server.broadcast_room(
            self.character.room_id,
            f"{self.character.name} pojawia się w Świątyni Odrodzenia.",
            exclude=self,
        )
        await self.send(
            f"Witaj, {self.character.name_case('voc')}. "
            f"Soulbound v{VERSION} World Core."
        )
        await self.send(
            "Rozpoczynasz sesję w Świątyni Odrodzenia."
        )
        if _dismissed_summons:
            await self.send(
                f"Twoje przywołania ({_dismissed_summons}) rozproszyły się przy logowaniu. "
                "Poziomy i ulepszenia zostały zachowane. Przywołaj je ponownie za manę i materiały."
            )
        await self.daily_login_v03051()
        # v1.11.17: nie odtwarzaj historii kanałów społecznościowych przy logowaniu.
        # Gossip/newbie/trade nadal działają na żywo; historię gracz otwiera ręcznie.
        await self.sync_extended_achievements()
        await self.sync_titles_v0580(announce=True)
        if moved_gems:
            await self.send(
                f"Sakwa Górnika: przeniesiono {moved_gems} surowych klejnotów "
                "ze starego inventory do sakwy."
            )
        if moved_craft_materials:
            await self.send(
                f"Szkatułka Rzemieślnicza: przeniesiono {moved_craft_materials} "
                "materiałów ze starego inventory do szkatułki."
            )
        if level_unequipped:
            await self.send(
                "EQ zdjęte z powodu zbyt niskiego Levelu postaci: "
                + ", ".join(level_unequipped) + ". Przedmioty pozostają w inventory."
            )
        if self.double_xp_state()["active"]:
            await self.show_double_xp_event()
        # Pending Fame earned just before logout is never lost.
        from systems.fame_v1702 import fame_pay_later
        import asyncio
        asyncio.create_task(fame_pay_later(self))
        await self.send("Wpisz help, aby poznać komendy.")
        await self.look()

