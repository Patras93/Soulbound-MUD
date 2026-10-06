# -*- coding: utf-8 -*-
"""Admin commands, wipe and unlock helpers."""

class SessionAdminToolsMixin:

    def is_admin(self):
            if self.master_account_id is None:
                return False
            username = self.server.db.account_name(self.master_account_id).casefold()
            return bool(username and username in ADMIN_ACCOUNT_NAMES)

    async def admin_command(self, args=""):
            if not self.is_admin():
                await self.send("Nieznana komenda. Wpisz help.")
                return
            raw = str(args or "").strip()
            norm = self.normalize_description_query(raw)
            if not norm or norm in ("help", "pomoc"):
                await self.send("ADMIN OWNER-ONLY")
                await self.send("admin status / administrator status — status uprawnień.")
                await self.send("admin heal / administrator ulecz — pełne HP i Mana.")
                await self.send("admin goto <room_id> / administrator teleport <room_id> — teleport testowy.")
                await self.send("admin give <item_id> [ilość] / administrator daj <item_id> [ilość].")
                await self.send("wipe moje postacie POTWIERDZAM / wipe my characters CONFIRM.")
                await self.send("wipe wszystkie postacie POTWIERDZAM / wipe all characters CONFIRM.")
                await self.send("Wipe usuwa postacie i ich progres, ale NIE usuwa kont/loginów/haseł.")
                return
            if norm in ("status",):
                await self.send(
                    f"Administrator: TAK. Konto: {self.server.db.account_name(self.master_account_id)}."
                )
                return
            if norm in ("heal", "ulecz", "wylecz"):
                self.current_hp = self.max_hp()
                self.current_mana = self.max_mana()
                await self.send(f"ADMIN: HP {self.current_hp}/{self.max_hp()}, Mana {self.current_mana}/{self.max_mana()}.")
                return
            parts = raw.split()
            first = self.normalize_description_query(parts[0]) if parts else ""
            if first in ("goto", "teleport", "idz", "idź"):
                target = " ".join(parts[1:]).strip()
                room_id = target if target in ROOMS else self.find_room(target)
                if not room_id or room_id not in ROOMS:
                    await self.send("ADMIN: nie znaleziono lokacji.")
                    return
                self.character.room_id = room_id
                self.server.db.save_character(self.character)
                await self.send(f"ADMIN: teleport do {ROOMS[room_id]['name']}.")
                await self.look()
                return
            if first in ("give", "daj"):
                if len(parts) < 2:
                    await self.send("Użycie: admin give <item_id> [ilość].")
                    return
                item_id = parts[1]
                try:
                    qty = max(1, min(9999, int(parts[2]) if len(parts) >= 3 else 1))
                except ValueError:
                    qty = 1
                if item_id not in ITEMS:
                    await self.send("ADMIN: nieznany item_id.")
                    return
                self.server.db.add_item(self.account_id, item_id, qty)
                await self.send(f"ADMIN: dodano {ITEMS[item_id]['name']} x{qty}.")
                return
            await self.send("Nieznana opcja admin. Wpisz admin help.")

    async def prepare_character_wipe(self):
            """Wyczyść stan sesyjny bez zapisywania usuwanej postaci."""
            if self.guide_task_active():
                await self.cancel_guide(announce=False)
            for task_name in ("rest_task", "auto_fishing_task", "auto_mining_task", "auto_woodcutting_task", "auto_herbalism_task", "combat_task"):
                task = getattr(self, task_name, None)
                if task and not task.done():
                    task.cancel()
                setattr(self, task_name, None)
            self.resting = False
            self.auto_fishing = self.auto_mining = self.auto_woodcutting = self.auto_herbalism = False
            if self.character:
                await self.leave_party(announce=False)
            self.combat_mob_key = None
            self.account_id = None
            self.character = None
            self.current_hp = 0
            self.current_mana = 0

    async def wipe_command(self, args=""):
            if not self.is_admin():
                await self.send("Nieznana komenda. Wpisz help.")
                return
            norm = self.normalize_description_query(args)
            own_tokens = ("moje postacie", "my characters")
            all_tokens = ("wszystkie postacie", "all characters")
            confirmed_pl = norm.endswith(" potwierdzam")
            confirmed_en = norm.endswith(" confirm")
            if not (confirmed_pl or confirmed_en):
                await self.send(
                    "WIPE wymaga potwierdzenia. Konta NIE zostaną usunięte. "
                    "Użyj: wipe moje postacie POTWIERDZAM albo wipe wszystkie postacie POTWIERDZAM."
                )
                return
            scope = norm.rsplit(" ", 1)[0]
            if scope not in own_tokens + all_tokens:
                await self.send("Nieprawidłowy zakres wipe.")
                return

            if scope in own_tokens:
                target_masters = {int(self.master_account_id)}
            else:
                target_masters = {
                    int(row["id"])
                    for row in self.server.db.conn.execute(
                        "SELECT id FROM accounts WHERE id NOT IN ("
                        "SELECT character_account_id FROM account_characters "
                        "WHERE character_account_id<>master_account_id)"
                    ).fetchall()
                }

            # Inne aktywne sesje z wipe zostają rozłączone bez zapisu usuwanej postaci.
            for session in list(self.server.sessions):
                if session is self or session.master_account_id not in target_masters:
                    continue
                try:
                    await session.send("ADMIN WIPE: postacie zostały wyczyszczone. Konto pozostaje. Połącz się ponownie.")
                    await session.prepare_character_wipe()
                    session.closed = True
                    session.writer.close()
                except Exception:  # AUDIT_INTENTIONAL_PASS: target session may already be disconnected during wipe
                    pass

            await self.prepare_character_wipe()
            if scope in own_tokens:
                removed = self.server.db.wipe_characters_for_master(self.master_account_id)
            else:
                removed, _masters = self.server.db.wipe_all_characters_preserve_accounts()
            # Wipe składu drużyn to tylko stan sesyjny.
            self.server.parties.clear()
            self.server.party_invites.clear()
            self.server.party_protectors.clear()
            self.server.party_goals.clear()
            self.server.party_ready_checks.clear()
            await self.send(f"WIPE POSTACI zakończony. Usunięto postaci: {removed}. Konta i hasła zachowane.")
            selected = await self.character_selection_flow()
            if selected is True:
                await self.enter_world()

    def boss_floor_chest_here(self):
            return _boss_floor_chest_spec(self.character.room_id) if self.character else None

    async def unlock_boss_floor_chest(self):
            spec = self.boss_floor_chest_here()
            if not spec:
                return False
            kind, floor, power = spec
            key_id = boss_floor_key_id(kind, floor)
            chest_name = boss_floor_chest_name(kind, floor)

            party_key = self.party_key()
            if party_key is not None and party_key != self.account_id:
                leader = self.server.session_by_account(party_key)
                leader_name = (
                    leader.character.name
                    if leader and getattr(leader, "character", None)
                    else "lider drużyny"
                )
                await self.send(
                    f"W drużynie tę skrzynię otwiera lider: {leader_name}. "
                    "Stań przy skrzyni razem z liderem, aby dostać nagrodę z jednego wspólnego otwarcia."
                )
                return True

            if self.server.db.item_qty(self.account_id, key_id) <= 0:
                await self.send(
                    f"{chest_name} jest zamknięta. "
                    f"Nie masz właściwego klucza. Klucz znajduje się w ciele bossa tego piętra."
                )
                return True
            if not self.server.db.remove_item(self.account_id, key_id, 1):
                await self.send("Nie udało się zużyć klucza.")
                return True

            recipients = [self]
            if party_key is not None:
                recipients = [
                    member
                    for member in self.server.party_sessions(
                        self.account_id, same_room=self.character.room_id
                    )
                    if getattr(member, "character", None) is not None
                    and member.account_id is not None
                ]
                if self not in recipients:
                    recipients.append(self)

            # Jedno fizyczne otwarcie skrzyni daje osobny loot roll każdemu
            # obecnemu członkowi drużyny. Jeżeli członek ma własny klucz z tego
            # samego bossa, zużywamy jedną sztukę, żeby nie zostawić podwójnego
            # odbioru tej samej party-run skrzyni.
            unique_recipients = {}
            for member in recipients:
                unique_recipients[int(member.account_id)] = member
            recipients = [
                unique_recipients[account_id]
                for account_id in sorted(unique_recipients)
            ]

            leader_name = self.character.name
            rewarded = []
            for member in recipients:
                consumed_member_key = False
                if member is not self and self.server.db.item_qty(member.account_id, key_id) > 0:
                    consumed_member_key = bool(
                        self.server.db.remove_item(member.account_id, key_id, 1)
                    )

                reward = boss_chest_reward_roll(kind, floor, power)
                member.character.gold += int(reward["gold"])
                for item_id in reward["items"]:
                    self.server.db.add_item(member.account_id, item_id, 1)
                    await member.record_item_collection(
                        item_id, source=chest_name, announce=True
                    )
                self.server.db.save_character(member.character)
                rewarded.append(member.character.name)

                if member is self:
                    await member.send(
                        f"Odkluczasz i otwierasz: {chest_name}. "
                        f"Klucz zostaje zużyty. Złoto: +{reward['gold']}."
                    )
                else:
                    key_text = (
                        " Twój odpowiadający Klucz Bossa również zostaje zużyty."
                        if consumed_member_key
                        else ""
                    )
                    await member.send(
                        f"{leader_name} odklucza i otwiera: {chest_name}. "
                        f"Otrzymujesz Złoto: +{reward['gold']}.{key_text}"
                    )
                if reward["items"]:
                    await member.send(
                        "Nagrody: "
                        + ", ".join(ITEMS[i]["name"] for i in reward["items"])
                        + "."
                    )

            if len(rewarded) > 1:
                await self.send(
                    f"Wspólne otwarcie drużyny: nagrody otrzymało {len(rewarded)} osób "
                    "stojących przy skrzyni: " + ", ".join(rewarded) + "."
                )
            return True

    async def unlock_context(self, args=""):
            q = self.normalize_description_query(args)
            if q in ("soul", "dusza", "bron duszy", "broń duszy"):
                await self.unlock()
                return
            if self.boss_floor_chest_here() is not None:
                await self.unlock_boss_floor_chest()
                return
            await self.unlock()
