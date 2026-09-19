import time
# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: io_auth_character."""

class SessionIOAuthCharacterMixin:
    def encode_session_text(self, value):
            value = str(value)
            try:
                return value.encode(
                    self.output_encoding,
                    errors="strict",
                )
            except UnicodeEncodeError:
                return value.encode(
                    self.output_encoding,
                    errors="replace",
                )

    async def negotiate_polish_charset(self):
            if self.closed:
                return
            try:
                self.writer.write(
                    telnet_charset_offer_bytes()
                )
                await self.writer.drain()
            except (ConnectionError, BrokenPipeError):
                self.closed = True

    async def show_encoding(self):
            label = (
                "UTF-8"
                if self.output_encoding == "utf-8"
                else "Windows-1250"
            )
            await self.send(
                f"Kodowanie sesji: {label}."
            )
            await self.send(
                "Zmiana: kodowanie utf8 albo kodowanie cp1250."
            )

    async def set_encoding(self, raw):
            value = normalize_lookup_text(raw)

            if not value:
                await self.show_encoding()
                return

            if value in {"utf8", "utf 8", "unicode"}:
                self.input_encoding = "utf-8"
                self.output_encoding = "utf-8"
                await self.send(
                    "Kodowanie przełączone na UTF-8. "
                    "Test: ą ć ę ł ń ó ś ź ż."
                )
                return

            if value in {
                "cp1250",
                "windows1250",
                "windows 1250",
                "win1250",
            }:
                self.input_encoding = "cp1250"
                self.output_encoding = "cp1250"
                await self.send(
                    "Kodowanie przełączone na Windows-1250. "
                    "Test: ą ć ę ł ń ó ś ź ż."
                )
                return

            await self.send(
                "Nieznane kodowanie. Użyj: "
                "kodowanie utf8 albo kodowanie cp1250."
            )

    def history_buffer_category(self, text, combat_detail=None):
            """Best-effort classification for gameplay history buffers."""
            if combat_detail:
                return "combat"
            raw = str(text or "").strip()
            if not raw:
                return None
            low = normalize_lookup_text(raw)
            # XP/progression messages. This intentionally captures level-up and
            # profession/skill progression lines as well as explicit XP gains.
            if (
                re.search(r"(?:^|\b)(?:xp|exp)(?:\b|$)", low)
                or re.search(r"(?:^|\s)[+]?\d+[\s\wąćęłńóśźż-]*(?:xp|exp)(?:\s|$|[.,:])", low)
                or "biegłość" in raw.lower() or "bieglosc" in low
                or "soul level" in low or "skill level" in low
                or "level postaci" in low and ("awans" in low or "exp" in low or "xp" in low)
            ):
                return "xp"
            if any(token in low for token in (
                "gotowe do oddania", "postep questa", "postęp questa",
                "quest ukończ", "quest ukoncz", "przyjmujesz zadanie",
                "zadanie ukończ", "zadanie ukoncz", "quest:"
            )):
                return "quest"
            if any(token in low for token in (
                "drop:", "loot:", "łup", "lup", "zdobywasz:",
                "znajdujesz:", "wypada:", "otrzymujesz przedmiot"
            )):
                return "loot"
            return None

    def record_history_buffer(self, text, category=None, combat_detail=None):
            if self.history_replaying:
                return
            raw = str(text or "").strip()
            if not raw:
                return
            category = category or self.history_buffer_category(raw, combat_detail=combat_detail)
            if category not in self.history_buffers:
                return
            self.history_sequence += 1
            stamp = time.strftime("%H:%M:%S")
            self.history_buffers[category].append((self.history_sequence, stamp, raw))

    def normalize_history_category(self, raw):
            value = self.normalize_description_query(str(raw or "").strip())
            aliases = {
                "xp":"xp", "exp":"xp", "doswiadczenie":"xp", "doświadczenie":"xp",
                "loot":"loot", "drop":"loot", "dropy":"loot", "lupy":"loot", "łupy":"loot",
                "quest":"quest", "questy":"quest", "zadania":"quest", "zadanie":"quest",
                "system":"system", "sys":"system", "systemowe":"system",
                "chat":"chat", "czat":"chat", "say":"chat",
                "party":"party", "druzyna":"party", "drużyna":"party", "pc":"party",
                "tell":"tell", "pm":"tell", "prywatne":"tell", "wiadomosci":"tell", "wiadomości":"tell",
                "combat":"combat", "walka":"combat", "fight":"combat",
                "all":"all", "wszystko":"all", "cale":"all", "całe":"all",
            }
            return aliases.get(value)

    async def show_history_buffer(self, args=""):
            raw = str(args or "").strip()
            norm = self.normalize_description_query(raw)
            if not norm:
                counts = ", ".join(
                    f"{name} {len(self.history_buffers[name])}"
                    for name in ("xp", "loot", "quest", "system", "chat", "party", "tell", "combat")
                )
                await self.send(
                    "BUFORY HISTORII: " + counts + ". Użycie: bufor xp, bufor loot, "
                    "bufor quest, bufor system, bufor chat, bufor party, bufor tell, bufor walka, bufor all.",
                    history_store=False,
                )
                await self.send(
                    "Możesz też użyć historia xp / historia loot / historia quest. "
                    "Domyślnie pokazuję 20 ostatnich wpisów; np. bufor xp 50.",
                    history_store=False,
                )
                return

            # Czyszczenie wybranej kategorii lub wszystkich buforów.
            parts = raw.split()
            first_norm = self.normalize_description_query(parts[0]) if parts else ""
            if first_norm in ("clear", "wyczysc", "wyczyść", "reset"):
                target = self.normalize_history_category(" ".join(parts[1:])) if len(parts) > 1 else "all"
                if not target:
                    await self.send("Użycie: bufor wyczysc <xp|loot|quest|system|chat|party|tell|walka|all>.", history_store=False)
                    return
                if target == "all":
                    for buf in self.history_buffers.values():
                        buf.clear()
                    await self.send("Wyczyszczono wszystkie sesyjne bufory historii.", history_store=False)
                else:
                    self.history_buffers[target].clear()
                    await self.send(f"Wyczyszczono bufor: {target}.", history_store=False)
                return

            category = self.normalize_history_category(parts[0])
            if not category:
                await self.send("Nieznany bufor. Użyj: bufor xp, loot, quest, system, chat, party, tell, walka albo all.", history_store=False)
                return
            limit = HISTORY_BUFFER_DEFAULT_SHOW
            if len(parts) > 1:
                try:
                    limit = max(1, min(HISTORY_BUFFER_LIMIT, int(parts[1])))
                except ValueError:
                    pass

            if category == "all":
                entries = []
                for key, buf in self.history_buffers.items():
                    entries.extend((seq, stamp, key, text) for seq, stamp, text in buf)
                entries.sort(key=lambda row: row[0])
                entries = entries[-limit:]
                title = "WSZYSTKIE BUFORY"
            else:
                entries = [
                    (seq, stamp, category, text)
                    for seq, stamp, text in list(self.history_buffers[category])[-limit:]
                ]
                title = f"BUFOR {category.upper()}"

            self.history_replaying = True
            try:
                await self.send(f"{title}: ostatnie {len(entries)} wpisów.", history_store=False)
                if not entries:
                    await self.send("Brak zapisanych wpisów w tej sesji.", history_store=False)
                    return
                for _seq, stamp, key, text in entries:
                    prefix = f"[{stamp}]" if category != "all" else f"[{stamp} {key}]"
                    await self.send(f"{prefix} {text}", history_store=False)
            finally:
                self.history_replaying = False

    async def send(self, text="", combat_detail=None, history_category=None, history_store=True):
            if self.closed:
                return
            if (
                combat_detail is None
                and self.auto_queue_casting
                and self.combat_mob_key
            ):
                combat_detail = "normal"
            if combat_detail and self.account_id is not None:
                mode = self.server.db.combat_log_mode(self.account_id)
                rank = {"concise": 0, "normal": 1, "full": 2}
                needed = {"essential": 0, "normal": 1, "full": 2}.get(
                    str(combat_detail).lower(), 1
                )
                if rank.get(mode, 1) < needed:
                    return
            if history_store:
                self.record_history_buffer(text, category=history_category, combat_detail=combat_detail)
            try:
                self.writer.write(
                    self.encode_session_text(
                        str(text) + "\r\n"
                    )
                )
                await self.writer.drain()
            except (ConnectionError, BrokenPipeError):
                self.closed = True

    async def send_combat(self, text, detail="essential"):
            try:
                if self.account_id:
                    self.server.db.add_combat_event_v0320(self.account_id, str(text), "combat")
            except Exception:
                pass
            await self.send(text, combat_detail=detail)

    async def set_combat_log(self, args=""):
            raw = self.normalize_description_query(str(args or "").strip())
            aliases = {
                "concise": "concise", "krotki": "concise", "krótki": "concise",
                "minimal": "concise", "cichy": "concise",
                "normal": "normal", "normalny": "normal",
                "full": "full", "pelny": "full", "pełny": "full",
            }
            if not raw:
                mode = self.server.db.combat_log_mode(self.account_id)
                await self.send(
                    f"Combat Log: {mode}. Dostępne: combat concise, combat normal, combat full."
                )
                return
            mode = aliases.get(raw)
            if not mode:
                await self.send(
                    "Użycie: combat concise, combat normal albo combat full."
                )
                return
            self.server.db.set_combat_log_mode(self.account_id, mode)
            labels = {
                "concise": "zwięzły — tylko ważne wydarzenia i ostrzeżenia",
                "normal": "normalny — trafienia i skille bez najbardziej technicznych detali",
                "full": "pełny — wszystkie szczegóły walki",
            }
            await self.send(f"Combat Log ustawiony: {labels[mode]}.")

    async def combat_hp_warning(self):
            if not self.character or self.current_hp <= 0:
                return
            max_hp = max(1, self.max_hp())
            ratio = self.current_hp / max_hp
            level = 0
            label = ""
            if ratio <= 0.10:
                level, label = 3, "KRYTYCZNE HP"
            elif ratio <= 0.25:
                level, label = 2, "NISKIE HP"
            elif ratio <= 0.50:
                level, label = 1, "HP poniżej połowy"
            if level < self.combat_hp_warn_level:
                # Po leczeniu ponownie uzbrój progi, żeby kolejne zejście HP
                # znów dało zwięzłe ostrzeżenie.
                self.combat_hp_warn_level = level
                return
            if level > self.combat_hp_warn_level:
                self.combat_hp_warn_level = level
                await self.send_combat(
                    f"{label}: {max(0, self.current_hp)} z {max_hp}.",
                    "essential",
                )

    async def prompt(self, text):
            if self.closed:
                return
            try:
                self.writer.write(
                    self.encode_session_text(text)
                )
                await self.writer.drain()
            except (ConnectionError, BrokenPipeError):
                self.closed = True

    async def read_line(self):
            try:
                while True:
                    data = await self.reader.readline()
                    if not data:
                        return None
                    text = clean_telnet(
                        data,
                        self.input_encoding,
                    )
                    text = (
                        text.replace("\r", "")
                        .replace("\n", "")
                        .strip()
                    )
                    if text:
                        return text
            except (
                ConnectionError,
                asyncio.IncompleteReadError,
            ):
                return None

    async def ask(self, text):
            await self.prompt(text)
            return await self.read_line()

    async def login_flow(self):
            await self.negotiate_polish_charset()
            await self.send(f"SOULBOUND ONLINE v{VERSION}")
            await self.send("ENCODING: UTF-8")
            await self.send(
                "Jeśli polskie znaki są błędne, wpisz: "
                "kodowanie cp1250"
            )
            while True:
                await self.send("MENU GŁÓWNE")
                await self.send("1. Zaloguj się")
                await self.send("2. Utwórz nowe konto")
                await self.send("3. Wyjdź")
                await self.send(
                    f"Jedno konto może mieć do {MAX_CHARACTERS_PER_ACCOUNT} postaci."
                )
                cmd = await self.ask("Wybierz opcję: ")
                if cmd is None:
                    return False
                normalized = normalize_lookup_text(cmd)
                if normalized in ("1", "login", "zaloguj", "zaloguj sie"):
                    if await self.do_login():
                        return True
                elif normalized in ("2", "new", "nowe", "konto", "utworz konto", "nowe konto"):
                    if await self.do_new_account():
                        return True
                elif normalized in ("3", "quit", "wyjdz", "wyjscie"):
                    return False
                else:
                    await self.send("Nieprawidłowa opcja. Wybierz 1, 2 albo 3.")

    async def do_login(self):
            username = await self.ask("Nazwa konta: ")
            if username is None:
                return False
            row = self.server.db.account_by_name(username)
            if not row or self.server.db.is_character_profile(row["id"]):
                await self.send("Nie ma takiego konta.")
                return False
            password = await self.ask("Hasło: ")
            if password is None:
                return False
            if not verify_password(password, row["password_salt"], row["password_hash"]):
                await self.send("Nieprawidłowe hasło.")
                return False
            old_session = self.server.session_by_master_account(row["id"], exclude=self)
            if old_session is not None:
                await self.send("To konto jest już zalogowane.")
                answer = await self.ask("Czy chcesz się przelogować? tak/nie: ")
                if answer is None:
                    return False
                if normalize_lookup_text(answer) not in ("tak", "yes", "y", "t"):
                    await self.send("Przelogowanie anulowane.")
                    return False

                resume_character_id = int(old_session.account_id) if old_session.character else None
                resume_character_name = old_session.character.name if old_session.character else None
                try:
                    await old_session.send(
                        "To konto zostało przejęte przez nowe logowanie. Ta sesja zostanie zamknięta."
                    )
                except Exception:
                    pass
                await old_session.close()
                self.server.sessions.discard(old_session)

                self.master_account_id = int(row["id"])
                if resume_character_id is not None:
                    selected = next(
                        (r for r in self.server.db.characters_for_master(self.master_account_id)
                         if int(r["character_account_id"]) == resume_character_id),
                        None,
                    )
                    if selected is not None:
                        self.account_id = int(selected["character_account_id"])
                        self.character = Character.from_row(selected)
                        self.refresh_guild_bonus_v0926()
                        self.server.db.apply_shared_wallet_to_character(self.character)
                        if self.character.room_id not in ROOMS:
                            self.server.world.ensure_runtime_room(self.character.room_id)
                        if self.character.room_id not in ROOMS:
                            self.character.room_id = "square"
                        await self.send(
                            f"Przelogowano. Wracasz na postać: {resume_character_name or self.character.name}."
                        )
                        return True
                await self.send("Przelogowano konto. Wybierz postać.")
                return await self.character_selection_flow()

            self.master_account_id = int(row["id"])
            return await self.character_selection_flow()

    async def send_character_list(self):
            rows = list(
                self.server.db.characters_for_master(self.master_account_id)
            )
            count = len(rows)
            await self.send(
                f"POSTACIE NA KONCIE: {count}/{MAX_CHARACTERS_PER_ACCOUNT}"
            )
            if not rows:
                await self.send("Brak utworzonych postaci.")
                return rows
            for row in rows:
                await self.send(
                    f"{row['slot']}. {row['name']}. "
                    f"Rasa: {row['race']}. Klasa: {row['class_name']}. "
                    f"Soul Level: {row['soul_level']}."
                )
            return rows

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
                self.refresh_guild_bonus_v0926()
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
                except Exception:
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
                    f"{row['slot']}. {row['name']} — Rasa {row['race']}, Klasa {row['class_name']}, "
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
                password = await self.ask("Hasło, minimum 6 znaków: ")
                if password is None:
                    return False
                if len(password) < 6:
                    await self.send("Hasło jest za krótkie.")
                    continue
                confirm = await self.ask("Powtórz hasło: ")
                if confirm is None:
                    return False
                if password != confirm:
                    await self.send("Hasła się różnią.")
                    continue
                break
            self.master_account_id = self.server.db.create_account(username, password)
            self.account_id = None
            await self.send("Konto utworzone.")
            await self.send(
                f"Na tym koncie możesz utworzyć maksymalnie {MAX_CHARACTERS_PER_ACCOUNT} postaci."
            )
            return await self.character_selection_flow()

    async def choose_number(self, items, prompt_text):
            while True:
                raw = await self.ask(prompt_text)
                if raw is None:
                    return None
                try:
                    n = int(raw)
                    if 1 <= n <= len(items):
                        return items[n - 1]
                except ValueError:
                    pass
                await self.send("Nieprawidłowy numer.")

    def valid_name_case_form(self, value):
            value = value.strip()
            if not (1 <= len(value) <= 40):
                return False
            return not any(ord(ch) < 32 for ch in value)

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
            await self.send("Wybierz rasę:")
            await self.send(
                "Znaczenie statystyk: Siła zwiększa atak fizyczny; "
                "Zręczność zwiększa szybkość i unik; Kondycja zwiększa HP; "
                "Inteligencja zwiększa Manę i moc czarów; "
                "Siła Woli zwiększa obronę magiczną; "
                "Charyzma zwiększa rabat sklepowy i limit drużyny."
            )
            for i, race in enumerate(RACES, 1):
                rname, desc, s, d, c, inte, w = race
                advice = race_class_recommendation_text(rname)
                await self.send(
                    f"{i}. {rname}. {desc} Siła {s}, Zręczność {d}, Kondycja {c}, "
                    f"Inteligencja {inte}, Siła Woli {w}, Charyzma 10. {advice}"
                )
            race = await self.choose_number(RACES, "Numer rasy: ")
            if race is None:
                return False
            selected_race_name = race[0]
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
                skills = CLASS_SKILLS.get(cname, [])
                skill_text = "; ".join(
                    f"{s['name']} do nauki od Biegłości klasy {s['unlock']}" for s in skills
                )
                await self.send(
                    f"{i}. {cname}. Typ {kind}. {desc} "
                    f"{growth} Broń Duszy: {weapon}. Umiejętności: {skill_text}."
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
                    self.master_account_id, name, race, cls, name_cases
                )
            except ValueError as exc:
                if str(exc) == "character_limit":
                    await self.send(
                        "Na jednym koncie można mieć maksymalnie 14 postaci."
                    )
                    return False
                raise
            self.account_id = int(character_account_id)
            self.character = Character.from_row(
                self.server.db.character_for_account(self.account_id)
            )
            self.refresh_guild_bonus_v0926()
            self.server.db.apply_shared_wallet_to_character(self.character)
            await self.send(
                f"Utworzono postać {self.character.name} w slocie {slot} z "
                f"{MAX_CHARACTERS_PER_ACCOUNT}."
            )
            await self.send(
                "Postać ma osobny Level 1-400. Sześć statystyk bazowych nadal rośnie automatycznie."
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
            "profession_xp": {},
            "tool_xp": {},
        }

    def session_summary_add(self, key, amount, subkey=None):
        state = getattr(self, "_session_summary", None)
        if not state:
            return
        amount = max(0, int(amount or 0))
        if amount <= 0:
            return
        if subkey is None:
            state[key] = int(state.get(key, 0) or 0) + amount
        else:
            bucket = state.setdefault(key, {})
            bucket[str(subkey)] = int(bucket.get(str(subkey), 0) or 0) + amount

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
            self.start_session_summary()

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
            await self.daily_login_v03051()
            if self.channel_enabled_v03051("gossip"):
                await self.show_channel_history_v03051("gossip", 20)
            await self.sync_extended_achievements()
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
            await self.send("Wpisz help, aby poznać komendy.")
            await self.look()
