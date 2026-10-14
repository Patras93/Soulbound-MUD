# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def choose_existing_character(self):
        rows = await self.send_character_list()
        if not rows:
            await self.send("Najpierw wybierz opcję 2 i stwórz postać.")
            return None

        await self.send(
            "Wpisz numer slotu albo nazwę postaci. "
            "Wpisz 0, aby wrócić do menu postaci."
        )
        while True:
            raw = await self.ask("Postać: ")
            if raw is None:
                return False
            choice = raw.strip()
            normalized = normalize_lookup_text(choice)
            if normalized in ("0", "back", "wroc", "powrot"):
                return None

            selected = None
            try:
                slot = int(choice)
            except ValueError:
                slot = None

            if slot is not None:
                selected = next(
                    (r for r in rows if int(r["slot"]) == slot), None
                )
            else:
                selected = next(
                    (r for r in rows if normalize_lookup_text(r["name"]) == normalized),
                    None,
                )

            if not selected:
                await self.send("Nie ma takiej postaci ani slotu.")
                continue

            self.account_id = int(selected["character_account_id"])
            self.character = Character.from_row(selected)
            # v0.34.5: starszy alt bez Gildii dziedziczy jedyną Gildię
            # pozostałych postaci tego samego konta przy wyborze postaci.
            _guild_sync = self.server.db.ensure_character_guild_from_master_v0345(
                self.master_account_id, self.account_id
            )
            self.refresh_guild_bonus_v0926()
            if _guild_sync.get("status") == "joined":
                await self.send(
                    f"Ta postać została automatycznie przypisana do Gildii {_guild_sync['name']} z tego konta."
                )
            elif _guild_sync.get("status") == "conflict":
                await self.send(
                    "UWAGA: postacie tego konta należą do różnych Gildii. "
                    "Automatyczne przypisanie tej postaci zostało pominięte."
                )
            self.server.db.apply_shared_wallet_to_character(self.character)
            if self.character.room_id not in ROOMS:
                self.server.world.ensure_runtime_room(self.character.room_id)
            if self.character.room_id not in ROOMS:
                self.character.room_id = "square"
            await self.send(
                f"Wybrano postać: {self.character.name}. "
                f"Slot {selected['slot']} z {MAX_CHARACTERS_PER_ACCOUNT}."
            )
            return True


async def delete_character_flow(self):
        rows = await self.send_character_list()
        if not rows:
            await self.send("Nie masz postaci do usunięcia.")
            return True

        await self.send(
            "Wpisz numer slotu albo nazwę postaci do usunięcia. "
            "Wpisz 0, aby anulować."
        )
        raw = await self.ask("Usuń postać: " )
        if raw is None:
            return False
        choice = raw.strip()
        normalized = normalize_lookup_text(choice)
        if normalized in ("0", "back", "wroc", "powrot", "anuluj", "cancel"):
            await self.send("Usuwanie anulowane.")
            return True

        selected = None
        try:
            slot = int(choice)
        except ValueError:
            slot = None
        if slot is not None:
            selected = next((r for r in rows if int(r["slot"]) == slot), None)
        else:
            selected = next(
                (r for r in rows if normalize_lookup_text(r["name"]) == normalized),
                None,
            )
        if not selected:
            await self.send("Nie ma takiej postaci ani slotu.")
            return True

        name = str(selected["name"])
        slot = int(selected["slot"])
        await self.send(
            f"UWAGA. Wybrano do trwałego usunięcia: {name}, slot {slot}."
        )
        await self.send(
            "Login, hasło i wspólny portfel konta pozostaną. "
            "Zniknie ta postać oraz jej własny progres, EQ, questy, profesje, "
            "eksploracja i Bestiariusz."
        )
        await self.send(f"Aby potwierdzić wpisz: USUN {name}")
        confirm = await self.ask("Potwierdzenie: " )
        if confirm is None:
            return False
        confirmation = normalize_lookup_text(confirm)
        accepted = {
            normalize_lookup_text(f"usun {name}"),
            normalize_lookup_text(f"usun postac {name}"),
            normalize_lookup_text(f"delete {name}"),
            normalize_lookup_text(f"delete character {name}"),
        }
        if confirmation not in accepted:
            await self.send("Nie potwierdzono. Postać nie została usunięta.")
            return True

        deleted = self.server.db.delete_character_for_master(
            self.master_account_id, int(selected["character_account_id"])
        )
        if not deleted:
            await self.send("Nie udało się znaleźć tej postaci. Niczego nie usunięto.")
            return True
        await self.send(
            f"Usunięto postać {deleted['name']} ze slotu {deleted['slot']}."
        )
        return True


async def send_admin_account_list_v0301(self):
        """Owner-only lista kont dostępna jeszcze przed wyborem postaci."""
        if not self.is_admin():
            return []
        rows = list(self.server.db.master_accounts())
        await self.send(f"KONTA: {len(rows)}.")
        if not rows:
            await self.send("Brak kont.")
            return rows
        for index, row in enumerate(rows, 1):
            await self.send(
                f"{index}. {row['username']} — postacie {int(row['character_count'] or 0)}/{MAX_CHARACTERS_PER_ACCOUNT}."
            )
        return rows


async def select_admin_master_account_v0301(self, prompt="Konto: "):
        """Wybór konta numerem z listy albo nazwą; nigdy profilem technicznym."""
        if not self.is_admin():
            return None
        rows = await self.send_admin_account_list_v0301()
        if not rows:
            return None
        await self.send("Wpisz numer konta albo dokładną nazwę. 0 — anuluj.")
        raw = await self.ask(prompt)
        if raw is None:
            return None
        choice = str(raw).strip()
        norm = normalize_lookup_text(choice)
        if norm in ("0", "anuluj", "cancel", "back", "wroc", "powrot"):
            return None
        try:
            number = int(choice)
        except ValueError:
            number = None
        if number is not None and 1 <= number <= len(rows):
            return rows[number - 1]
        return next(
            (row for row in rows if normalize_lookup_text(row["username"]) == norm),
            None,
        )


async def disconnect_master_sessions_v0301(self, master_account_id, reason, *, keep_self=True):
        """Rozłącz sesje celu przed usuwaniem danych, aby autosave nie odtworzył skasowanej postaci."""
        master_account_id = int(master_account_id)
        disconnected = 0
        for session in list(self.server.sessions):
            if keep_self and session is self:
                continue
            if session.master_account_id != master_account_id:
                continue
            try:
                await session.send(reason)
                await session.prepare_character_wipe()
                session.closed = True
                if session.writer:
                    session.writer.close()
                disconnected += 1
            except Exception:  # AUDIT_INTENTIONAL_PASS: admin wipe continues even if a target session vanished
                pass
        return disconnected


async def admin_show_account_characters_v0301(self):
        target = await self.select_admin_master_account_v0301()
        if not target:
            await self.send("Anulowano.")
            return
        master_id = int(target["id"])
        rows = list(self.server.db.characters_for_master(master_id))
        await self.send(
            f"KONTO {target['username']}: {len(rows)}/{MAX_CHARACTERS_PER_ACCOUNT} postaci."
        )
        if not rows:
            await self.send("Brak postaci na tym koncie.")
            return
        for row in rows:
            await self.send(
                f"{row['slot']}. {row['name']} — Rasa {row['race']}, płeć {row['gender']}, Klasa {row['class_name']}, "
                f"Level {int(row['character_level'] or 1)}, Soul {int(row['soul_level'] or 1)}."
            )


async def admin_wipe_master_v0301(self, target, *, own=False):
        master_id = int(target["id"])
        username = str(target["username"])
        count = self.server.db.character_count_for_master(master_id)
        if own:
            phrase = "WIPE MOJE POSTACIE POTWIERDZAM"
        else:
            phrase = f"WIPE {username} POTWIERDZAM"
        await self.send(
            f"UWAGA. Konto {username}: usunięte zostaną wszystkie postacie ({count}) i ich progres. "
            "Login i hasło pozostaną."
        )
        await self.send(f"Aby potwierdzić wpisz dokładnie: {phrase}")
        confirm = await self.ask("Potwierdzenie: ")
        if confirm is None or normalize_lookup_text(confirm) != normalize_lookup_text(phrase):
            await self.send("Nie potwierdzono. Niczego nie usunięto.")
            return
        await self.disconnect_master_sessions_v0301(
            master_id,
            "ADMIN WIPE: postacie Twojego konta zostały usunięte. Konto i hasło pozostają.",
            keep_self=(master_id == int(self.master_account_id)),
        )
        removed = self.server.db.wipe_characters_for_master(master_id)
        self.server.parties.clear()
        self.server.party_invites.clear()
        self.server.party_protectors.clear()
        self.server.party_goals.clear()
        self.server.party_routes_v1193.clear()
        self.server.party_ready_checks.clear()
        await self.send(f"ADMIN: konto {username} — usunięto postaci: {removed}. Konto zachowane.")


async def admin_delete_character_v0301(self):
        target = await self.select_admin_master_account_v0301()
        if not target:
            await self.send("Anulowano.")
            return
        master_id = int(target["id"])
        username = str(target["username"])
        rows = list(self.server.db.characters_for_master(master_id))
        if not rows:
            await self.send(f"Konto {username} nie ma postaci.")
            return
        for row in rows:
            await self.send(f"{row['slot']}. {row['name']} — Level {int(row['character_level'] or 1)}.")
        raw = await self.ask("Slot albo nazwa postaci do usunięcia, 0 — anuluj: ")
        if raw is None:
            return
        choice = str(raw).strip()
        norm = normalize_lookup_text(choice)
        if norm in ("0", "anuluj", "cancel", "back", "wroc", "powrot"):
            await self.send("Anulowano.")
            return
        try:
            slot = int(choice)
        except ValueError:
            slot = None
        if slot is not None:
            selected = next((row for row in rows if int(row["slot"]) == slot), None)
        else:
            selected = next((row for row in rows if normalize_lookup_text(row["name"]) == norm), None)
        if not selected:
            await self.send("Nie ma takiej postaci ani slotu.")
            return
        name = str(selected["name"])
        phrase = f"USUN {username} {name}"
        await self.send(
            f"UWAGA. Trwałe usunięcie postaci {name} z konta {username}. Konto i wspólny portfel pozostaną."
        )
        await self.send(f"Aby potwierdzić wpisz dokładnie: {phrase}")
        confirm = await self.ask("Potwierdzenie: ")
        if confirm is None or normalize_lookup_text(confirm) != normalize_lookup_text(phrase):
            await self.send("Nie potwierdzono. Niczego nie usunięto.")
            return
        await self.disconnect_master_sessions_v0301(
            master_id,
            "ADMIN: jedna z postaci tego konta została usunięta. Połącz się ponownie.",
            keep_self=(master_id == int(self.master_account_id)),
        )
        deleted = self.server.db.delete_character_for_master(
            master_id, int(selected["character_account_id"])
        )
        if not deleted:
            await self.send("Nie udało się usunąć postaci.")
            return
        await self.send(f"ADMIN: usunięto {deleted['name']} ze slotu {deleted['slot']} konta {username}.")


async def admin_wipe_all_v0301(self):
        phrase = "WIPE WSZYSTKIE POSTACIE POTWIERDZAM"
        accounts = list(self.server.db.master_accounts())
        char_count = sum(int(row["character_count"] or 0) for row in accounts)
        await self.send(
            f"OSTRZEŻENIE. Serwerowy wipe usunie {char_count} postaci z {len(accounts)} kont. "
            "Konta, loginy i hasła pozostaną."
        )
        await self.send(f"Aby potwierdzić wpisz dokładnie: {phrase}")
        confirm = await self.ask("Potwierdzenie: ")
        if confirm is None or normalize_lookup_text(confirm) != normalize_lookup_text(phrase):
            await self.send("Nie potwierdzono. Niczego nie usunięto.")
            return
        for target in accounts:
            master_id = int(target["id"])
            await self.disconnect_master_sessions_v0301(
                master_id,
                "ADMIN WIPE: wszystkie postacie serwera zostały wyczyszczone. Konto pozostaje.",
                keep_self=(master_id == int(self.master_account_id)),
            )
        removed, _masters = self.server.db.wipe_all_characters_preserve_accounts()
        self.server.parties.clear()
        self.server.party_invites.clear()
        self.server.party_protectors.clear()
        self.server.party_goals.clear()
        self.server.party_routes_v1193.clear()
        self.server.party_ready_checks.clear()
        await self.send(f"ADMIN: serwerowy wipe zakończony. Usunięto postaci: {removed}. Konta zachowane.")


async def admin_character_menu_v0301(self):
        """Ukryte menu właściciela dostępne nawet przy 0/14 postaci."""
        if not self.is_admin():
            await self.send("Nieprawidłowa opcja.")
            return
        while True:
            await self.send("ADMINISTRATOR — MENU POSTACI")
            await self.send("1. Lista kont")
            await self.send("2. Postacie wybranego konta")
            await self.send("3. Wipe moich postaci")
            await self.send("4. Wipe postaci wybranego konta")
            await self.send("5. Usuń jedną postać wybranego konta")
            await self.send("6. Wipe wszystkich postaci serwera")
            await self.send("0. Powrót")
            raw = await self.ask("Administrator: ")
            if raw is None:
                return
            choice = normalize_lookup_text(raw)
            if choice in ("0", "back", "wroc", "powrot"):
                return
            if choice in ("1", "konta", "accounts", "lista kont"):
                await self.send_admin_account_list_v0301()
                continue
            if choice in ("2", "postacie", "characters", "konto"):
                await self.admin_show_account_characters_v0301()
                continue
            if choice in ("3", "moje", "wipe moje", "wipe own"):
                target = self.server.db.master_account_by_name(
                    self.server.db.account_name(self.master_account_id)
                )
                if target:
                    await self.admin_wipe_master_v0301(target, own=True)
                continue
            if choice in ("4", "wipe konto", "wipe account"):
                target = await self.select_admin_master_account_v0301()
                if not target:
                    await self.send("Anulowano.")
                    continue
                await self.admin_wipe_master_v0301(target)
                continue
            if choice in ("5", "usun postac", "usuń postać", "delete character"):
                await self.admin_delete_character_v0301()
                continue
            if choice in ("6", "wipe wszystkie", "wipe all"):
                await self.admin_wipe_all_v0301()
                continue
            await self.send("Nieprawidłowa opcja administratora. Wybierz 0-6.")


async def character_selection_flow(self):
        while True:
            rows = list(
                self.server.db.characters_for_master(self.master_account_id)
            )
            count = len(rows)

            await self.send("MENU POSTACI")
            await self.send("1. Wybierz postać")
            await self.send("2. Stwórz nową postać")
            await self.send("3. Pokaż listę postaci")
            await self.send("4. Usuń postać")
            await self.send("5. Wyloguj")
            if self.is_admin():
                await self.send("6. Administrator")
            await self.send(
                f"Postacie na koncie: {count}/{MAX_CHARACTERS_PER_ACCOUNT}."
            )

            raw = await self.ask("Wybierz opcję: ")
            if raw is None:
                return False
            choice = normalize_lookup_text(raw)

            if choice in ("1", "wybierz", "wybierz postac", "postac", "play"):
                selected = await self.choose_existing_character()
                if selected is True:
                    return True
                if selected is False:
                    return False
                continue

            if choice in ("2", "new", "nowa", "nowa postac", "stworz", "stworz postac", "create"):
                if count >= MAX_CHARACTERS_PER_ACCOUNT:
                    await self.send(
                        f"Osiągnięto limit {MAX_CHARACTERS_PER_ACCOUNT} postaci na koncie."
                    )
                    continue
                return await self.character_creator()

            if choice in ("3", "lista", "list", "postacie", "pokaz postacie"):
                await self.send_character_list()
                continue

            if choice in (
                "4", "delete", "delete character", "usun", "usun postac",
                "usuń", "usuń postać", "kasuj", "skasuj postac", "skasuj postać"
            ):
                keep_session = await self.delete_character_flow()
                if not keep_session:
                    return False
                continue

            if choice in ("5", "logout", "wyloguj", "wylogowanie", "back", "wroc"):
                self.master_account_id = None
                self.account_id = None
                self.character = None
                await self.send("Wylogowano z konta.")
                return False

            if self.is_admin() and choice in ("6", "admin", "administrator"):
                await self.admin_character_menu_v0301()
                continue

            if self.is_admin():
                await self.send("Nieprawidłowa opcja. Wybierz 1, 2, 3, 4, 5 albo 6.")
            else:
                await self.send("Nieprawidłowa opcja. Wybierz 1, 2, 3, 4 albo 5.")


async def do_new_account(self):
        await self.send("Tworzenie nowego konta.")
        while True:
            username = await self.ask("Nazwa konta, 3-20 znaków: ")
            if username is None:
                return False
            username = username.strip()
            if not safe_name(username):
                await self.send("Dozwolone są litery, cyfry, _ i -. Długość 3-20.")
                continue
            if self.server.db.account_by_name(username):
                await self.send("Taka nazwa konta już istnieje.")
                continue
            break
        while True:
            password = await self.ask("Hasło, minimum 10 znaków: ")
            if password is None:
                return False
            if len(password) < 10:
                await self.send("Hasło jest za krótkie.")
                continue
            confirm = await self.ask("Powtórz hasło: ")
            if confirm is None:
                return False
            if password != confirm:
                await self.send("Hasła się różnią.")
                continue
            break
        # v1.22.4: accounts do not require SMTP. The administrator can
        # issue one-time reset codes and players can keep a backup code.
        # Existing verified e-mails remain valid for optional recovery.
        try:
            self.master_account_id = self.server.db.create_account(username, password)
        except sqlite3.IntegrityError:
            await self.send("Ta nazwa konta jest już zajęta.")
            return False
        self.account_id = None
        await self.send("Konto utworzone. E-mail nie jest wymagany. Po zalogowaniu możesz zapisać zapasowy kod przez: odzyskaj haslo kod.")
        await self.send(
            f"Na tym koncie możesz utworzyć maksymalnie {MAX_CHARACTERS_PER_ACCOUNT} postaci."
        )
        return await self.character_selection_flow()


async def ask_name_declension(self, base_name):
        await self.send("ODMIANA IMIENIA POSTACI")
        await self.send(
            "Mianownik jest nazwą wybraną na początku kreatora. "
            "Teraz podaj pozostałe sześć form."
        )
        result = {"nom": base_name}
        await self.send(f"Mianownik. Kto? Co?: {base_name}.")

        prompts = (
            ("gen", "Dopełniacz. Kogo? Czego?"),
            ("dat", "Celownik. Komu? Czemu?"),
            ("acc", "Biernik. Kogo? Co?"),
            ("ins", "Narzędnik. Z kim? Z czym?"),
            ("loc", "Miejscownik. O kim? O czym?"),
            ("voc", "Wołacz. O!"),
        )
        for key, label in prompts:
            while True:
                raw = await self.ask(f"{label}: ")
                if raw is None:
                    return None
                value = raw.strip()
                if self.valid_name_case_form(value):
                    result[key] = value
                    break
                await self.send("Nieprawidłowa forma. Użyj od 1 do 40 znaków.")

        await self.send("Zapisana odmiana imienia:")
        await self.send(f"Mianownik: {result['nom']}.")
        await self.send(f"Dopełniacz: {result['gen']}.")
        await self.send(f"Celownik: {result['dat']}.")
        await self.send(f"Biernik: {result['acc']}.")
        await self.send(f"Narzędnik: {result['ins']}.")
        await self.send(f"Miejscownik: {result['loc']}.")
        await self.send(f"Wołacz: {result['voc']}.")
        return result

