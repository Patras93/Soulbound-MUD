# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def use_astral_portal(self, raw):
        if getattr(self, "current_hp", 1) <= 0 or getattr(self, "is_downed_v0371", lambda: False)():
            await self.send("Martwa lub powalona postać nie może korzystać z portali. Najpierw się odrodź.")
            return
        party_key = self.party_key()
        if self.portal_requires_local_leader_v12811():
            leader = self.server.session_by_account(party_key)
            leader_name = (
                leader.character.name
                if leader and getattr(leader, "character", None)
                else "lider drużyny"
            )
            await self.send(
                f"W drużynie Astralny Portal uruchamia lider: {leader_name}."
            )
            return
        if self.combat_mob_key:
            await self.send(
                "Nie możesz użyć Astralnego Portalu podczas walki."
            )
            return

        room_id = str(self.character.room_id)
        normal_floor = astral_floor_number(room_id)
        mythic_floor = mythic_astral_floor_number(room_id)
        mythic_context = (
            room_id == "mythic_astral_gate"
            or mythic_floor is not None
        )
        kind = "mythic_astral" if mythic_context else "astral"
        current_floor = mythic_floor if mythic_context else normal_floor
        gate = "mythic_astral_gate" if mythic_context else "astral_gate"
        floor_id = (
            mythic_astral_floor_id
            if mythic_context else astral_floor_id
        )
        is_checkpoint = (
            is_mythic_astral_boss_floor
            if mythic_context else is_astral_boss_floor
        )
        label = (
            "Mityczny Astralny Portal"
            if mythic_context else "Astralny Portal"
        )
        start_floor = 10 if mythic_context else ASTRAL_MIN_FLOOR

        value = self.normalize_room_query(raw)
        if (
            current_floor is not None
            and is_checkpoint(current_floor)
            and self.checkpoint_portal_unlocked_v11331(
                kind, current_floor
            )
            and (
                not value
                or value in (
                    "wyjdz", "wyjdź", "exit", "out",
                    "wyjscie", "wyjście",
                )
            )
        ):
            await self.party_checkpoint_portal_exit_v11331(
                kind=kind,
                floor=current_floor,
                target_room=gate,
                label=label,
            )
            return

        if not value or value in ("status", "lista", "list"):
            await self.show_astral_portal_status(kind=kind)
            return

        match = re.search(r"(\d+)", value)
        if not match:
            await self.send(
                f"Użycie: astralportal {start_floor}, "
                f"astralportal {start_floor + 10}, ... bez górnego limitu."
            )
            return

        floor = int(match.group(1))
        if not is_checkpoint(floor):
            await self.send(
                f"Checkpointy tej Wieży są co 10 poziomów od "
                f"{start_floor} bez górnego limitu."
            )
            return
        if not self.checkpoint_portal_unlocked_v11331(kind, floor):
            floors = self.checkpoint_portal_floors_v11331(kind)
            await self.send(
                f"Checkpoint poziomu {floor} jest zablokowany. "
                f"Najwyższy odblokowany: "
                f"{max(floors) if floors else 'brak'}."
            )
            return
        if not self.checkpoint_portal_origin_v2010(
            room_id=room_id, gate_rooms=(gate,), kind=kind,
            current_floor=current_floor, is_checkpoint=is_checkpoint,
        ):
            await self.send(
                f"{label}: przejście na odblokowane piętro działa przy Bramie "
                "lub na odblokowanym checkpointcie co 10 pięter."
            )
            return

        target = floor_id(floor)
        self.server.world.ensure_infinite_dungeon_floor(target)
        old = room_id
        candidates = (
            list(
                self.server.party_sessions(
                    self.account_id, same_room=old
                )
            )
            if party_key == self.account_id
            else [self]
        )
        if self not in candidates:
            candidates.append(self)

        moved = []
        skipped = []
        for member in candidates:
            if not member or not getattr(member, "character", None):
                continue
            if getattr(member, 'current_hp', 1) <= 0 or getattr(member, 'is_downed_v0371', lambda: False)():
                skipped.append(f"{member.character.name}: postać martwa lub powalona")
                continue
            if member.combat_mob_key:
                skipped.append(f"{member.character.name}: trwa walka")
                continue
            if not member.checkpoint_portal_unlocked_v11331(
                kind, floor
            ):
                skipped.append(
                    f"{member.character.name}: checkpoint {floor} "
                    "nie jest odblokowany"
                )
                continue
            member.previous_room_id = member.character.room_id
            member.character.room_id = target
            member.server.db.save_character(member.character)
            moved.append(member)

        if moved:
            for member in moved:
                await member.send(
                    f"Lider {self.character.name} uruchamia {label}. "
                    f"Cel: checkpoint {floor}."
                )
                await member.look()
            if len(moved) > 1:
                await self.send(
                    f"{label} przenosi razem {len(moved)} graczy."
                )
        if skipped:
            await self.send(
                "Nie przeniesiono: " + "; ".join(skipped) + "."
            )


async def show_portal_status(self, kind="crypt"):
        if kind == "mythic_crypt":
            await self.show_checkpoint_portal_status_v11331(
                kind="mythic_crypt",
                label="Mityczny Portal Krypty",
                start_floor=10,
            )
            await self.send(
                "Przy Bramie Mitycznej Krypty: portal <10/20/30/...>. "
                "Na checkpointcie: portal <odblokowane pietro> albo portal wyjdz."
            )
            return

        await self.show_checkpoint_portal_status_v11331(
            kind="crypt",
            label="Portal Krypty",
            start_floor=10,
        )
        await self.send(
            "Przy wejściu Krypty: portal <10/20/30/...>. "
            "Na checkpointcie: portal <odblokowane pietro> albo portal wyjdz."
        )


async def use_crypt_portal(self, raw):
        if getattr(self, "current_hp", 1) <= 0 or getattr(self, "is_downed_v0371", lambda: False)():
            await self.send("Martwa lub powalona postać nie może korzystać z portali. Najpierw się odrodź.")
            return
        party_key = self.party_key()
        if self.portal_requires_local_leader_v12811():
            leader = self.server.session_by_account(party_key)
            leader_name = (
                leader.character.name
                if leader and getattr(leader, "character", None)
                else "lider drużyny"
            )
            await self.send(
                f"W drużynie Portal Krypty uruchamia lider: {leader_name}."
            )
            return
        if self.combat_mob_key:
            await self.send(
                "Nie możesz użyć Portalu Krypty podczas walki."
            )
            return

        room_id = str(self.character.room_id)
        if (self.catacomb_floor_v2010(room_id) is not None
                or room_id == 'temple_basement_deep_nest'):
            await self.use_catacomb_portal_v2010(raw)
            return
        normal_floor = crypt_floor_number(room_id)
        mythic_floor = mythic_crypt_floor_number(room_id)
        mythic_context = (
            room_id == "mythic_crypt_gate"
            or mythic_floor is not None
        )
        kind = "mythic_crypt" if mythic_context else "crypt"
        current_floor = mythic_floor if mythic_context else normal_floor
        gate = "mythic_crypt_gate" if mythic_context else "crypt_hall"
        floor_id = (
            mythic_crypt_floor_id
            if mythic_context else crypt_floor_id
        )
        is_checkpoint = (
            is_mythic_crypt_boss_floor
            if mythic_context else is_crypt_boss_floor
        )
        label = (
            "Mityczny Portal Krypty"
            if mythic_context else "Portal Krypty"
        )

        value = self.normalize_room_query(raw)
        if (
            current_floor is not None
            and is_checkpoint(current_floor)
            and self.checkpoint_portal_unlocked_v11331(
                kind, current_floor
            )
            and (
                not value
                or value in (
                    "wyjdz", "wyjdź", "exit", "out",
                    "wyjscie", "wyjście",
                )
            )
        ):
            await self.party_checkpoint_portal_exit_v11331(
                kind=kind,
                floor=current_floor,
                target_room=gate,
                label=label,
            )
            return

        if not value or value in ("status", "lista", "list"):
            await self.show_portal_status(kind=kind)
            return

        match = re.search(r"(\d+)", value)
        if not match:
            await self.send(
                "Użycie: portal 10, portal 20, portal 30, ... "
                "bez górnego limitu."
            )
            return
        floor = int(match.group(1))
        if not is_checkpoint(floor):
            await self.send(
                "Portale są co 10 pięter: 10, 20, 30, ... "
                "bez górnego limitu."
            )
            return
        if not self.checkpoint_portal_unlocked_v11331(kind, floor):
            floors = self.checkpoint_portal_floors_v11331(kind)
            await self.send(
                f"Portal piętra {floor} jest zablokowany. "
                f"Najwyższy odblokowany: "
                f"{max(floors) if floors else 'brak'}."
            )
            return

        allowed_gates = (
            ("mythic_crypt_gate",)
            if mythic_context
            else ("crypt_hall", "crypt_entrance")
        )
        if not self.checkpoint_portal_origin_v2010(
            room_id=room_id, gate_rooms=allowed_gates, kind=kind,
            current_floor=current_floor, is_checkpoint=is_checkpoint,
        ):
            await self.send(
                f"{label}: przejście na odblokowane piętro działa przy wejściu "
                "lub na odblokowanym checkpointcie co 10 pięter."
            )
            return

        if self.resting or self.rest_task:
            await self.stop_rest(announce=False)
        if self.auto_fishing or self.auto_fishing_task:
            await self.stop_auto_fishing(announce=False)
        if self.auto_mining or self.auto_mining_task:
            await self.stop_auto_mining(announce=False)
        if self.auto_woodcutting or self.auto_woodcutting_task:
            await self.stop_auto_woodcutting(announce=False)
        if self.auto_herbalism or self.auto_herbalism_task:
            await self.stop_auto_herbalism(announce=False)

        target = floor_id(floor)
        self.server.world.ensure_infinite_dungeon_floor(target)
        old = room_id
        candidates = (
            list(
                self.server.party_sessions(
                    self.account_id, same_room=old
                )
            )
            if party_key == self.account_id
            else [self]
        )
        if self not in candidates:
            candidates.append(self)

        moved = []
        skipped = []
        for member in candidates:
            if not member or not getattr(member, "character", None):
                continue
            if getattr(member, 'current_hp', 1) <= 0 or getattr(member, 'is_downed_v0371', lambda: False)():
                skipped.append(f"{member.character.name}: postać martwa lub powalona")
                continue
            if member.combat_mob_key:
                skipped.append(f"{member.character.name}: trwa walka")
                continue
            if not member.checkpoint_portal_unlocked_v11331(
                kind, floor
            ):
                skipped.append(
                    f"{member.character.name}: checkpoint {floor} "
                    "nie jest odblokowany"
                )
                continue
            if member.resting or member.rest_task:
                await member.stop_rest(announce=False)
            if member.auto_fishing or member.auto_fishing_task:
                await member.stop_auto_fishing(announce=False)
            if member.auto_mining or member.auto_mining_task:
                await member.stop_auto_mining(announce=False)
            if member.auto_woodcutting or member.auto_woodcutting_task:
                await member.stop_auto_woodcutting(announce=False)
            if member.auto_herbalism or member.auto_herbalism_task:
                await member.stop_auto_herbalism(announce=False)

            member.previous_room_id = member.character.room_id
            member.character.room_id = target
            member.server.db.save_character(member.character)
            moved.append(member)

        if moved:
            for member in moved:
                await member.send(
                    f"Lider {self.character.name} uruchamia {label}. "
                    f"Cel: checkpoint {floor}."
                )
                await member.look()
            if len(moved) > 1:
                await self.send(
                    f"{label} przenosi razem {len(moved)} graczy."
                )
        if skipped:
            await self.send(
                "Nie przeniesiono: " + "; ".join(skipped) + "."
            )

