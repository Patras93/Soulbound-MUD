# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
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
            except ValueError:  # AUDIT_INTENTIONAL_PASS: invalid optional history limit keeps the default
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
            mode = self.combat_log_mode_cached_v1178()
            rank = {"concise": 0, "normal": 1, "full": 2}
            needed = {"essential": 0, "normal": 1, "full": 2}.get(
                str(combat_detail).lower(), 1
            )
            if rank.get(mode, 1) < needed:
                return
        if history_store:
            self.record_history_buffer(text, category=history_category, combat_detail=combat_detail)
        if history_store and self.account_id is not None and not getattr(self, "history_replaying", False):
            try:
                _value = str(text or "").strip()
                if _value and is_level_promotion_v2003(_value):
                    self.server.db.record_activity_v0560(self.account_id, "awans", _value, "")
            except Exception as exc:
                print(f"ACTIVITY_PROMOTION_LOG_ERROR: {type(exc).__name__}: {exc}", flush=True)
        try:
            self.writer.write(
                self.encode_session_text(
                    str(text) + "\r\n"
                )
            )
            await self.writer.drain()
        except (ConnectionError, BrokenPipeError):
            self.closed = True


async def set_combat_log(self, args=""):
        raw = self.normalize_description_query(str(args or "").strip())
        aliases = {
            "concise": "concise", "krotki": "concise", "krótki": "concise",
            "minimal": "concise", "cichy": "concise",
            "normal": "normal", "normalny": "normal",
            "full": "full", "pelny": "full", "pełny": "full",
        }
        # v1.18.0: never hide combat history from screen reader users.
        if raw in ("ostatnie", "historia", "last", "log") or raw.startswith(("ostatnie ", "historia ", "last ")):
            parts = raw.split()
            count = 10
            if len(parts) > 1 and parts[1].isdigit():
                count = max(1, min(100, int(parts[1])))
            await self.show_history_buffer(f"combat {count}")
            return
        if raw in ("pomoc", "help", "?"):
            await self.send("combat concise — ważne zdarzenia; combat normal — zwykłe trafienia; combat full — szczegóły; combat ostatnie [1-100] — historia sesji.")
            return
        if not raw:
            mode = self.combat_log_mode_cached_v1178()
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
        self._combat_log_mode_cache_v1178 = (self.account_id, mode, time.monotonic())
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


async def login_flow(self):
        await self.negotiate_polish_charset()
        await self.send(f"SOULBOUND ONLINE v{VERSION}")
        await self.send("ENCODING: UTF-8")
        await self.send(
            "Kodowanie domyślne: UTF-8. Jeśli polskie znaki są uszkodzone, wpisz: "
            "kodowanie utf8. Windows-1250 używaj tylko w starym kliencie: kodowanie cp1250."
        )
        while True:
            await self.send("MENU GŁÓWNE")
            await self.send("1. Zaloguj się")
            await self.send("2. Utwórz nowe konto")
            await self.send("3. Wyjdź")
            await self.send("4. Odzyskaj hasło (jednorazowy kod)")
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
            elif normalized in ("3", "quit", "exit", "wyjdz", "wyjscie"):
                await self.close_from_main_menu()
                return False
            elif normalized in ("4", "odzyskaj", "odzyskaj haslo", "odzyskaj hasło", "reset", "forgot"):
                await self.recover_password_from_login_v1222()
            else:
                await self.send("Nieprawidłowa opcja. Wybierz 1, 2, 3 albo 4.")


async def recover_password_from_login_v1222(self):
        await self.send("ODZYSKIWANIE HASŁA")
        await self.send("Użyj kodu zapisanego podczas zakładania konta albo komendy konto kod.")
        await self.send("Kod jednorazowy administratora również działa.")
        username = await self.ask("Login konta (0 anuluje): ")
        if username is None or username.strip() == "0":
            return
        code = await self.ask("Kod odzyskiwania: ")
        if code is None:
            return
        password = await self.ask("Nowe hasło (10-256 znaków): ")
        if password is None:
            return
        confirm = await self.ask("Powtórz nowe hasło: ")
        if confirm is None:
            return
        if len(password) < 10 or len(password) > 256 or password != confirm:
            await self.send("Hasła są różne albo mają nieprawidłową długość. Niczego nie zmieniono.")
            return
        changed = self.server.db.reset_password_with_code_v1222(username, code, password)
        if not changed:
            await self.send("Nie udało się zresetować hasła. Kod może być błędny, wygasły lub zużyty.")
            return
        row = self.server.db.master_account_by_name(username)
        if row is not None:
            # Invalidate any existing sessions for a changed password.
            for active in list(self.server.sessions):
                if active is self or getattr(active, "master_account_id", None) != int(row["id"]):
                    continue
                await active.send("Hasło konta zostało zmienione. Połącz się ponownie.")
                await active.close()
        await self.send("Hasło zostało zmienione. Zaloguj się nowym hasłem. Postacie i EQ zachowano.")


async def recover_password_by_email_v1223(self):
    # v5.00.1: retained for ABI only, impossible to reset through mail.
    await self.send("Odzyskanie hasła: menu 4, wyłącznie jednorazowy kod.")


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
            except Exception:  # AUDIT_INTENTIONAL_PASS: replaced session may already be disconnected
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
                f"Rasa: {row['race']}. Płeć: {row['gender']}. Klasa: {row['class_name']}. "
                f"Soul Level: {row['soul_level']}."
            )
        return rows

