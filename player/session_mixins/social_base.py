# -*- coding: utf-8 -*-
"""Legacy/base social methods used by the newer social layer."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
from player.session_mixins.exp_terrain import ROOMS
from player.session_mixins.exploration_progress import normalize_lookup_text


class SessionBaseSocialMixin:

    async def who(self):
            online = [
                session
                for session in self.server.sessions
                if session.character
            ]
            online.sort(
                key=lambda session: session.character.name.lower()
            )

            await self.send(
                f"Gracze online: {len(online)}."
            )

            if not online:
                return

            for session in online:
                character = session.character
                room = ROOMS.get(
                    character.room_id,
                    {
                        "name": character.room_id,
                        "zone": "Nieznana strefa",
                    },
                )

                classes = character.active_class_names()
                class_text = (
                    ", ".join(classes)
                    if classes
                    else character.class_name
                )

                title_text = (
                    f" Tytuł: {character.active_title}."
                    if character.active_title else ""
                )
                await self.send(
                    f"{character.name}. "
                    f"Klasa: {class_text}. "
                    f"Soul Level {character.soul_level}. "
                    f"Lokalizacja: {room['name']}. "
                    f"Strefa: {room['zone']}."
                    f"{title_text}"
                )

    async def say(self, text):
            message = str(text or "").strip()

            if not message:
                await self.send("Użycie: say tekst")
                return

            if len(message) > 500:
                message = message[:500]
                await self.send(
                    "Wiadomość skrócono do 500 znaków."
                )

            await self.send(
                f"Mówisz: {message}", history_category="chat"
            )
            await self.server.broadcast_room(
                self.character.room_id,
                f"{self.character.name} mówi: {message}",
                exclude=self, history_category="chat",
            )

    async def tell(self, args):
            parts = str(args or "").split(maxsplit=1)
            if len(parts) != 2:
                await self.send("Użycie: tell <gracz> <tekst>.")
                return
            target_name, message = parts[0].strip(), parts[1].strip()
            if not message:
                await self.send("Wiadomość nie może być pusta.")
                return
            if len(message) > 500:
                message = message[:500]
                await self.send("Wiadomość prywatną skrócono do 500 znaków.")
            target = self.server.find_character_session(target_name)
            if not target or target.closed or not target.character:
                await self.send("Ten gracz nie jest online.")
                return
            if target is self:
                await self.send("Nie musisz wysyłać prywatnej wiadomości do siebie.")
                return
            target.last_private_sender_account_id = self.account_id
            target.last_private_sender_name = self.character.name
            await target.send(
                f"[TELL] {self.character.name}: {message}", history_category="tell"
            )
            await self.send(
                f"[TELL do {target.character.name}] {message}", history_category="tell"
            )

    async def reply_private_v0928(self, message):
            message = str(message or "").strip()
            if not message:
                await self.send("Użycie: reply <tekst> albo odpisz <tekst>.")
                return
            if not self.last_private_sender_name:
                await self.send("Nie masz jeszcze nadawcy prywatnej wiadomości, któremu można odpisać.")
                return
            target = self.server.find_character_session(self.last_private_sender_name)
            if not target or target.closed or not target.character:
                await self.send(f"{self.last_private_sender_name} nie jest teraz online.")
                return
            await self.tell(f"{target.character.name} {message}")

    async def channel_broadcast_v03050(self, channel, message):
            message = str(message or "").strip()
            if not message:
                await self.send(f"Użycie: {channel} <tekst>.")
                return
            if len(message) > 500:
                message = message[:500]
                await self.send("Wiadomość skrócono do 500 znaków.")
            labels = {"gossip":"GOSSIP", "newbie":"NEWBIE", "trade":"TRADE"}
            label = labels.get(channel, channel.upper())
            text = f"[{label}] {self.character.name}: {message}"
            for session in list(self.server.sessions):
                if session.closed or not session.character:
                    continue
                await session.send(text, history_category="chat")

    async def show_channels_v03050(self):
            await self.send("KANAŁY: gossip <tekst> — rozmowy ogólne; newbie <tekst> — pytania i pomoc dla nowych graczy; trade <tekst> — handel. Lokalnie: say. Prywatnie: tell. Drużyna: pc. Gildia: gildia czat <tekst>.")

    def mentor_progress_v03050(self, account_id=None):
            aid = int(account_id if account_id is not None else self.account_id)
            row = self.server.db.conn.execute(
                "SELECT COALESCE(MAX(level),1) AS mx FROM class_progress WHERE account_id=?", (aid,)
            ).fetchone()
            mastery = int(row["mx"] or 1) if row else 1
            crow = self.server.db.conn.execute(
                "SELECT soul_level FROM characters WHERE account_id=?", (aid,)
            ).fetchone()
            soul = int(crow["soul_level"] or 1) if crow else 1
            return mastery, soul

    def mentor_link_v03050(self):
            return self.server.db.conn.execute(
                "SELECT mentor_account_id,student_account_id FROM mentor_links_v03050 WHERE mentor_account_id=? OR student_account_id=?",
                (self.account_id, self.account_id),
            ).fetchone()

    def mentor_bonus_percent_v03050(self):
            row = self.mentor_link_v03050()
            if not row:
                return 0
            other_id = int(row["student_account_id"] if int(row["mentor_account_id"]) == int(self.account_id) else row["mentor_account_id"])
            other = self.server.session_by_account(other_id)
            if not other or other.closed or not other.character or not self.character:
                return 0
            if other.character.room_id != self.character.room_id:
                return 0
            if not self.server.same_party(self.account_id, other_id):
                return 0
            return 5

    async def handle_mentor_v03050(self, args=""):
            raw = str(args or "").strip()
            conn = self.server.db.conn
            if not raw or normalize_lookup_text(raw) in ("status","info"):
                row = self.mentor_link_v03050()
                if not row:
                    await self.send("Mentor: brak aktywnej relacji. Mentor wymaga Biegłości co najmniej 50 i Soul Level 50; uczeń może mieć najwyżej Biegłość 20 i Soul Level 20.")
                    return
                mid, sid = int(row["mentor_account_id"]), int(row["student_account_id"])
                mname = self.server.db.character_name_by_account_v0928(mid) or str(mid)
                sname = self.server.db.character_name_by_account_v0928(sid) or str(sid)
                bonus = self.mentor_bonus_percent_v03050()
                await self.send(f"Mentor: {mname}. Uczeń: {sname}. Bonus wspólnej gry: +5% XP, teraz {'aktywny' if bonus else 'nieaktywny'}.")
                return
            parts = raw.split(maxsplit=1)
            action = normalize_lookup_text(parts[0])
            rest = parts[1].strip() if len(parts)>1 else ""
            if action in ("zapros","zaproś","invite"):
                if not rest:
                    await self.send("Użycie: mentor zapros <gracz>.")
                    return
                mastery, soul = self.mentor_progress_v03050()
                if mastery < 50 or soul < 50:
                    await self.send(f"Aby zostać mentorem potrzebujesz Biegłości 50 i Soul Level 50. Masz Biegłość {mastery}, Soul Level {soul}.")
                    return
                target = self.server.find_character_session(rest)
                if not target or target.closed or not target.character:
                    await self.send("Ten gracz nie jest online.")
                    return
                tm, ts = self.mentor_progress_v03050(target.account_id)
                if tm > 20 or ts > 20:
                    await self.send(f"Ta postać nie jest już początkująca. Limit ucznia: Biegłość 20 i Soul Level 20. Ma Biegłość {tm}, Soul Level {ts}.")
                    return
                if self.mentor_link_v03050() or target.mentor_link_v03050():
                    await self.send("Ty albo ten gracz macie już aktywną relację mentor-uczeń.")
                    return
                conn.execute("INSERT OR REPLACE INTO mentor_requests_v03050(mentor_account_id,student_account_id,created_at) VALUES(?,?,CURRENT_TIMESTAMP)",(self.account_id,target.account_id)); conn.commit()
                await self.send(f"Zapraszasz {target.character.name} do relacji mentor-uczeń.")
                await target.send(f"{self.character.name} chce zostać twoim mentorem. Użyj: mentor akceptuj {self.character.name}.")
                return
            if action in ("akceptuj","accept"):
                if not rest:
                    await self.send("Użycie: mentor akceptuj <gracz>.")
                    return
                target = self.server.find_character_session(rest)
                if not target or target.closed or not target.character:
                    await self.send("Mentor musi być online podczas akceptacji.")
                    return
                req = conn.execute("SELECT 1 FROM mentor_requests_v03050 WHERE mentor_account_id=? AND student_account_id=?",(target.account_id,self.account_id)).fetchone()
                if not req:
                    await self.send("Nie masz zaproszenia od tej osoby.")
                    return
                tm, ts = self.mentor_progress_v03050()
                mm, ms = target.mentor_progress_v03050()
                if tm > 20 or ts > 20 or mm < 50 or ms < 50:
                    await self.send("Nie spełniacie już warunków relacji mentor-uczeń.")
                    return
                if self.mentor_link_v03050() or target.mentor_link_v03050():
                    await self.send("Ty albo mentor macie już aktywną relację.")
                    return
                conn.execute("DELETE FROM mentor_requests_v03050 WHERE mentor_account_id=? AND student_account_id=?",(target.account_id,self.account_id))
                conn.execute("INSERT INTO mentor_links_v03050(mentor_account_id,student_account_id) VALUES(?,?)",(target.account_id,self.account_id)); conn.commit()
                await self.send(f"{target.character.name} zostaje twoim mentorem. Wspólna gra w tej samej drużynie i lokacji daje wam +5% XP.")
                await target.send(f"Zostajesz mentorem gracza {self.character.name}. Wspólna gra w tej samej drużynie i lokacji daje wam +5% XP.")
                return
            if action in ("zakoncz","zakończ","end","usun","usuń"):
                row = self.mentor_link_v03050()
                if not row:
                    await self.send("Nie masz aktywnej relacji mentor-uczeń.")
                    return
                other_id = int(row["student_account_id"] if int(row["mentor_account_id"]) == int(self.account_id) else row["mentor_account_id"])
                other = self.server.session_by_account(other_id)
                conn.execute("DELETE FROM mentor_links_v03050 WHERE mentor_account_id=? AND student_account_id=?",(int(row["mentor_account_id"]),int(row["student_account_id"]))); conn.commit()
                await self.send("Kończysz relację mentor-uczeń.")
                if other and not other.closed:
                    await other.send(f"{self.character.name} kończy relację mentor-uczeń.")
                return
            await self.send("Użycie: mentor, mentor zapros <gracz>, mentor akceptuj <gracz>, mentor zakoncz.")

    def friend_account_id_v0928(self, name):
            return self.server.db.character_account_id_by_name_v0928(name)

    async def show_friends_v0928(self):
            conn = self.server.db.conn
            rows = conn.execute(
                "SELECT f.friend_account_id,c.name FROM player_friends_v0928 f "
                "JOIN characters c ON c.account_id=f.friend_account_id "
                "WHERE f.account_id=? ORDER BY c.name COLLATE NOCASE",
                (self.account_id,),
            ).fetchall()
            await self.send("ZNAJOMI:")
            if not rows:
                await self.send("Lista znajomych jest pusta.")
            for row in rows:
                session = self.server.session_by_account(int(row["friend_account_id"]))
                status = "online" if session and not session.closed and session.character else "offline"
                if status == "online" and session.character:
                    rid = session.character.room_id
                    extra = f" — {ROOMS.get(rid, {}).get('name', rid)}"
                else:
                    extra = ""
                await self.send(f"{row['name']}: {status}{extra}.")
            incoming = conn.execute(
                "SELECT c.name FROM player_friend_requests_v0928 r "
                "JOIN characters c ON c.account_id=r.sender_account_id "
                "WHERE r.target_account_id=? ORDER BY r.created_at,c.name COLLATE NOCASE",
                (self.account_id,),
            ).fetchall()
            if incoming:
                await self.send("OCZEKUJĄCE PROŚBY:")
                for row in incoming:
                    await self.send(f"{row['name']}. Użyj: znajomi akceptuj {row['name']} albo znajomi odrzuc {row['name']}.")

    async def handle_friends_v0928(self, args=""):
            raw = str(args or "").strip()
            if not raw:
                await self.show_friends_v0928()
                return
            parts = raw.split(maxsplit=1)
            action = normalize_lookup_text(parts[0])
            rest = parts[1].strip() if len(parts) > 1 else ""
            conn = self.server.db.conn
            if action in ("dodaj", "add", "zaproś", "zapros"):
                if not rest:
                    await self.send("Użycie: znajomi dodaj <gracz>.")
                    return
                target_id = self.friend_account_id_v0928(rest)
                if target_id is None:
                    await self.send("Nie ma takiej postaci.")
                    return
                if int(target_id) == int(self.account_id):
                    await self.send("Nie możesz dodać samego siebie do znajomych.")
                    return
                if self.server.db.are_friends_v0928(self.account_id, target_id):
                    await self.send("Ta osoba jest już na twojej liście znajomych.")
                    return
                if conn.execute(
                    "SELECT 1 FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?",
                    (target_id, self.account_id),
                ).fetchone():
                    # Dwie krzyżujące się prośby oznaczają zgodę obu stron.
                    conn.execute("DELETE FROM player_friend_requests_v0928 WHERE (sender_account_id=? AND target_account_id=?) OR (sender_account_id=? AND target_account_id=?)", (target_id,self.account_id,self.account_id,target_id))
                    conn.execute("INSERT OR IGNORE INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)", (self.account_id,target_id))
                    conn.execute("INSERT OR IGNORE INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)", (target_id,self.account_id))
                    conn.commit()
                    name = self.server.db.character_name_by_account_v0928(target_id) or rest
                    await self.send(f"{name} zostaje twoim znajomym.")
                    target = self.server.session_by_account(target_id)
                    if target and not target.closed:
                        await target.send(f"{self.character.name} zostaje twoim znajomym.")
                    return
                conn.execute(
                    "INSERT OR REPLACE INTO player_friend_requests_v0928(sender_account_id,target_account_id,created_at) VALUES(?,?,CURRENT_TIMESTAMP)",
                    (self.account_id,target_id),
                )
                conn.commit()
                name = self.server.db.character_name_by_account_v0928(target_id) or rest
                await self.send(f"Wysyłasz prośbę o dodanie do znajomych: {name}.")
                target = self.server.session_by_account(target_id)
                if target and not target.closed:
                    await target.send(f"{self.character.name} chce dodać cię do znajomych. Użyj: znajomi akceptuj {self.character.name} albo znajomi odrzuc {self.character.name}.")
                return
            if action in ("akceptuj", "accept", "zaakceptuj"):
                sender_id = self.friend_account_id_v0928(rest) if rest else None
                if sender_id is None:
                    await self.send("Użycie: znajomi akceptuj <gracz>.")
                    return
                req = conn.execute(
                    "SELECT 1 FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?",
                    (sender_id,self.account_id),
                ).fetchone()
                if not req:
                    await self.send("Nie masz prośby od tej osoby.")
                    return
                conn.execute("DELETE FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?", (sender_id,self.account_id))
                conn.execute("DELETE FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?", (self.account_id,sender_id))
                conn.execute("INSERT OR IGNORE INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)", (self.account_id,sender_id))
                conn.execute("INSERT OR IGNORE INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)", (sender_id,self.account_id))
                conn.commit()
                name = self.server.db.character_name_by_account_v0928(sender_id) or rest
                await self.send(f"Dodajesz {name} do znajomych.")
                target = self.server.session_by_account(sender_id)
                if target and not target.closed:
                    await target.send(f"{self.character.name} zaakceptował twoją prośbę o znajomość.")
                return
            if action in ("odrzuc", "odrzuć", "decline"):
                sender_id = self.friend_account_id_v0928(rest) if rest else None
                if sender_id is None:
                    await self.send("Użycie: znajomi odrzuc <gracz>.")
                    return
                cur = conn.execute("DELETE FROM player_friend_requests_v0928 WHERE sender_account_id=? AND target_account_id=?", (sender_id,self.account_id))
                conn.commit()
                await self.send("Odrzucono prośbę." if cur.rowcount else "Nie masz prośby od tej osoby.")
                return
            if action in ("usun", "usuń", "remove", "delete"):
                target_id = self.friend_account_id_v0928(rest) if rest else None
                if target_id is None:
                    await self.send("Użycie: znajomi usun <gracz>.")
                    return
                was = self.server.db.are_friends_v0928(self.account_id,target_id)
                conn.execute("DELETE FROM player_friends_v0928 WHERE (account_id=? AND friend_account_id=?) OR (account_id=? AND friend_account_id=?)", (self.account_id,target_id,target_id,self.account_id))
                conn.execute("DELETE FROM player_friend_requests_v0928 WHERE (sender_account_id=? AND target_account_id=?) OR (sender_account_id=? AND target_account_id=?)", (self.account_id,target_id,target_id,self.account_id))
                conn.commit()
                await self.send("Usunięto znajomego." if was else "Ta osoba nie była na twojej liście znajomych.")
                return
            if action in ("party", "druzyna", "drużyna"):
                target_id = self.friend_account_id_v0928(rest) if rest else None
                if target_id is None or not self.server.db.are_friends_v0928(self.account_id,target_id):
                    await self.send("Najpierw dodaj tę osobę do znajomych.")
                    return
                name = self.server.db.character_name_by_account_v0928(target_id)
                target = self.server.session_by_account(target_id)
                if not target or target.closed:
                    await self.send(f"{name or rest} nie jest teraz online.")
                    return
                await self.party_invite(target.character.name)
                return
            if action in ("gildia", "guild"):
                target_id = self.friend_account_id_v0928(rest) if rest else None
                if target_id is None or not self.server.db.are_friends_v0928(self.account_id,target_id):
                    await self.send("Najpierw dodaj tę osobę do znajomych.")
                    return
                name = self.server.db.character_name_by_account_v0928(target_id)
                target = self.server.session_by_account(target_id)
                if not target or target.closed:
                    await self.send(f"{name or rest} nie jest teraz online.")
                    return
                await self.handle_guild_v0926(f"zaproś {target.character.name}")
                return
            await self.send("Użycie: znajomi; znajomi dodaj/akceptuj/odrzuc/usun <gracz>; znajomi party <gracz>; znajomi gildia <gracz>.")
