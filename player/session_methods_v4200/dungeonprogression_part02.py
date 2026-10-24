# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def show_mine_info(self):
        """Czytelny status Kopalni Głębinowej dla NVDA."""
        progress = self.mine_progress()
        room_id = self.character.room_id
        floor = mine_floor_number(room_id)
        approach_names = {
            "cave_entrance": "Wejście do Kopalni Głębinowej — przed poziomem 1",
            "cave_tunnel": "Tunel Kryształowej Jaskini — droga do poziomu 1",
            "crystal_chamber": "Komnata Kryształowa — bezpośrednio przed poziomem 1",
        }

        await self.send("KOPALNIA GŁĘBINOWA")
        if floor is not None:
            pos = mine_tunnel_coords(room_id, self.account_id)
            if pos:
                await self.send(f'Położenie: poziom {floor}, chodnik X={pos[1]}, Y={pos[2]}.')
                available = self.server.db.mine_tunnel_directions_v1251(self.account_id, *pos)
                await self.send('Własne odkryte przejścia: ' + (
                    ', '.join(MINE_DIRECTION_LABELS[d] for d in available) if available else 'brak') + '.')
            else:
                await self.send(f"Położenie: poziom {floor}.")
            await self.send('Kopanie kierunkowe: kop north/south/east/west, '
                            'kop northeast/northwest/southeast/southwest, kop up/down. '
                            'Po polsku: kop północ, kop południe, kop prawo, kop lewo, kop góra, kop dół. '
                            'Automat: kop on north (lub wybrany kierunek), zatrzymanie: kop off. '
                            'Mapa: kopalnia mapa; pozycja: kopalnia gdzie; powrót: kopalnia droga; skarby: kopalnia skarb.')
        elif room_id in approach_names:
            await self.send(f"Położenie: {approach_names[room_id]}.")
        else:
            room_name = ROOMS.get(room_id, {}).get("name", "nieznana lokacja")
            await self.send(
                f"Położenie: {room_name}. Nie jesteś teraz w Kopalni Głębinowej. "
                "Użyj: prowadz kopalnia."
            )

        max_floor = int(progress["max_floor_unlocked"])
        await self.send(
            f"Najgłębiej odblokowany poziom: {max_floor}. "
            "Kopalnia nie ma górnego limitu pięter; moc zasobów skaluje się do progresji 600."
        )

        if floor is not None:
            if floor == max_floor:
                hits = int(progress["wall_hits"])
                required = int(progress["wall_required_hits"])
                missing = max(0, required - hits)
                await self.send(
                    f"Ściana do poziomu {floor + 1}: {hits}/{required} uderzeń. "
                    f"Brakuje {missing}."
                )
            elif floor < max_floor:
                await self.send(
                    f"Zejście do poziomu {floor + 1} jest już odblokowane."
                )
            else:
                await self.send(
                    "Uwaga: jesteś głębiej niż zapisany postęp odblokowania; "
                    "użyj ruchu w górę albo zaloguj się ponownie, jeśli to stary zapis."
                )

        auto_text = "włączone" if self.auto_mining else "wyłączone"
        await self.send(f"Auto-kopanie: {auto_text}.")

        try:
            profession_level = int(self.profession_level_for_tool("mining"))
        except Exception:
            profession_level = 1
        try:
            tool_level = int(self.server.db.tool(self.account_id, "mining")["level"])
        except Exception:
            tool_level = 1
        await self.send(
            f"Górnictwo: {profession_level}/{PROFESSION_MAX_LEVEL}. Kilof: {tool_level}/{TOOL_MAX_LEVEL}."
        )

        # W Kopalni Głębinowej ruda wymaga jednocześnie odpowiedniego Kilofa
        # i głębokości. Pokazujemy kilka najwyższych spełnionych progów zamiast
        # zalewać czytnik ekranu całą tabelą atlasu.
        if floor is not None:
            eligible = []
            for item_id in ORE_ATLAS_ALL:
                if item_id not in ITEMS:
                    continue
                need_tool = int(ORE_ATLAS_LEVELS.get(item_id, 1))
                need_floor = int(ORE_MINE_FLOOR_MINIMUMS.get(item_id, 1))
                if tool_level >= need_tool and floor >= need_floor:
                    eligible.append((max(need_tool, need_floor), need_tool, need_floor, item_id))
            eligible.sort(key=lambda row: (row[0], row[1], row[2], ITEMS[row[3]].get("name", row[3])))
            best = eligible[-5:]
            if best:
                await self.send(
                    "Najwyższe dostępne rudy przy tym Kilofie i piętrze: "
                    + ", ".join(player_item_display_name_v0335(item_id) for *_rest, item_id in best)
                    + "."
                )

            future = []
            for item_id in ORE_ATLAS_ALL:
                if item_id not in ITEMS:
                    continue
                need_tool = int(ORE_ATLAS_LEVELS.get(item_id, 1))
                need_floor = int(ORE_MINE_FLOOR_MINIMUMS.get(item_id, 1))
                if need_tool > tool_level or need_floor > floor:
                    distance = max(0, need_tool - tool_level) + max(0, need_floor - floor)
                    future.append((distance, max(need_tool, need_floor), item_id, need_tool, need_floor))
            if future:
                future.sort(key=lambda row: (row[0], row[1], ITEMS[row[2]].get("name", row[2])))
                _distance, _rank, item_id, need_tool, need_floor = future[0]
                await self.send(
                    f"Najbliższy kolejny próg rudy: {player_item_display_name_v0335(item_id)} — "
                    f"Kilof {need_tool}, poziom kopalni {need_floor}."
                )

        if self.auto_mining:
            if floor is None and room_id in approach_names:
                await self.send(
                    "Auto-kopanie samo przejdzie do poziomu 1 i będzie schodzić po przebiciu kolejnych ścian."
                )
            elif floor is not None:
                await self.send(
                    "Auto-kopanie po przebiciu ściany automatycznie schodzi na następny odblokowany poziom."
                )
        else:
            await self.send("Włącz auto-kopanie komendą: kop on.")


def profession_dungeon_access_error(self, target_room):
        dungeon, floor = profession_dungeon_floor(target_room)
        if not dungeon:
            return None
        if dungeon == "crystal_mine":
            # v0.25.1: to już zwykłe Kryształowe Groty, nie loch Górnictwa.
            return None

        tool_type, item_id, tool_name = PROF_DUNGEON_TOOL[dungeon]
        if self.server.db.item_qty(self.account_id, item_id) <= 0:
            return (
                f"Ten loch profesyjny wymaga narzędzia: {tool_name}."
            )

        profession = profession_for_tool_type(tool_type)
        prow = self.server.db.profession(self.account_id, profession)
        profession_level = int(prow["level"])
        required = profession_dungeon_required_tool_level(floor)
        if profession_level < required:
            return (
                f"Ten poziom lochu profesyjnego wymaga "
                f"{profession} poziom {required}. Masz poziom {profession_level}. "
                f"Poziom {tool_name} nie blokuje piętra; odblokowuje lepsze surowce."
            )
        return None


async def grant_stat_xp_v11342(
    self, amount, targets=None, *, content_level,
    content_scaled=False
):
        amount=max(0,int(amount or 0))
        if amount<=0:
            return 0
        amount=self.scale_progression_xp_v11342(
            amount,
            content_level,
            content_scaled=content_scaled,
        )
        amount=self.apply_double_xp(amount)
        from systems.experience_bank_v2011 import banked_experience_v2011
        # Per-stat bank: no shared pool that could duplicate XP for six stats.
        target_names = list(targets) if targets is not None else list(self.character.STAT_PROGRESS_FIELDS)
        awarded = []
        for stat_name in target_names:
            paid = banked_experience_v2011(
                self.server.db, self.account_id, amount, 'stat',
                self.character.character_level, source_key=stat_name)
            awarded.append(paid)
            for message in self.character.add_stat_progress(paid, targets=(stat_name,)):
                await self.send(message)
        return min(awarded) if awarded else 0


async def grant_combat_quest_stat_xp(
    self, raw_reward, repeatable=False, source_label="Quest walki", *,
    content_level=None, content_scaled=False
):
        """Przyznaje EXP do każdej z sześciu statystyk z systemu questowego."""
        # v39: accepts either old common int or individual stat-name -> int map.
        # Every reward uses the SAME native scaling, double XP and EXP bank.
        from collections.abc import Mapping
        if isinstance(raw_reward, Mapping):
            if set(raw_reward) != set(self.character.STAT_PROGRESS_FIELDS):
                raise ValueError('Nagrody statystyk: wymagane dokladnie szesc statystyk.')
            rewards = {name: max(0, int(raw_reward[name])) for name in raw_reward}
        else:
            one = max(0, int(raw_reward or 0))
            rewards = {name: one for name in self.character.STAT_PROGRESS_FIELDS}
        if not any(rewards.values()):
            return []
        applied = []
        for stat_name in self.character.STAT_PROGRESS_FIELDS:
            base = rewards[stat_name]
            if not base:
                applied.append(0)
                continue
            base = self.scale_progression_xp_v11342(
                base, content_level, content_scaled=content_scaled)
            granted = v0874_quest_stat_progress_base_grant(
                self.character, stat_name, base, repeatable
            )
            granted = self.apply_double_xp(granted)
            from systems.experience_bank_v2011 import banked_experience_v2011
            granted=banked_experience_v2011(
                self.server.db, self.account_id, granted, 'stat',
                self.character.character_level, source_key=stat_name)
            applied.append(granted)
            for msg in self.character.add_stat_progress(granted, targets=(stat_name,)):
                await self.send(msg)
        lo = min(applied) if applied else 0
        hi = max(applied) if applied else 0
        amount_text = str(lo) if lo == hi else f"{lo}-{hi}"
        if lo == hi:
            await self.send(f"{source_label}: {amount_text} EXP do kazdej statystyki.")
        else:
            labels = self.character.STAT_PROGRESS_FIELDS
            await self.send(f"{source_label}: " + ', '.join(
                f'{labels[name][0]} {amount}'
                for name, amount in zip(labels, applied)) + ' EXP.')
        return applied


async def grant_soul_xp(
    self, amount, single_level_cap=False, *,
    content_level=None, content_scaled=False, overcap=False
):
        old_level = self.character.soul_level
        amount=self.scale_progression_xp_v11342(
            amount,
            content_level,
            content_scaled=content_scaled,
        )
        amount = self.apply_double_xp(amount)
        _mentor_pct = self.mentor_bonus_percent_v03050()
        if _mentor_pct:
            amount = max(0, int(round(amount * (1.0 + _mentor_pct / 100.0))))
            self.mentor_record_activity_v03051()

        from systems.experience_bank_v2011 import banked_experience_v2011
        amount = banked_experience_v2011(
            self.server.db, self.account_id, amount, 'soul',
            self.character.soul_level, overcap=overcap)
        self.session_summary_add("soul_xp", amount)
        messages = self.character.add_soul_xp(
            amount, single_level_cap=single_level_cap
        )
        for message in messages:
            await self.send(message)

        await self.set_achievement_progress("soul_level", self.character.soul_level)

        if self.character.soul_level > old_level:
            self.current_hp = self.max_hp()
            await self.send(
                f"Awans Soul Level odnawia całe HP. "
                f"HP: {self.current_hp} z {self.max_hp()}."
            )
            hint_fn = getattr(self, "exp_area_soul_level_up_hint_v2910", None)
            hint = hint_fn(old_level, self.character.soul_level) if callable(hint_fn) else None
            if hint:
                await self.send(hint)

        return self.character.soul_level > old_level


async def use_catacomb_portal_v2010(self, raw):
        if getattr(self, "current_hp", 1) <= 0 or getattr(self, "is_downed_v0371", lambda: False)():
            await self.send("Martwa lub powalona postać nie może korzystać z portali. Najpierw się odrodź.")
            return
        from world.world_expansion_v import CATACOMB_LEVELS_V0900
        if self.combat_mob_key:
            await self.send('Nie można używać portalu Katakumb podczas walki.')
            return
        party_key = self.party_key()
        if self.portal_requires_local_leader_v12811():
            await self.send('W drużynie portal uruchamia lider stojący w tej samej sali.')
            return
        here = str(self.character.room_id)
        current_floor = self.catacomb_floor_v2010(here)
        if current_floor is not None:
            self.remember_catacomb_floor_v2010(here)
        known = self.catacomb_unlocked_floors_v2010()
        value = self.normalize_room_query(raw)
        if not value or value in ('lista','list','status'):
            await self.send('Portal Katakumb: odblokowane piętra: '
                + (', '.join(map(str,known)) if known else 'brak')
                + '. Użyj portal 1, portal 2 albo portal 3.')
            return
        if value in ('wyjdz','wyjdź','wyjscie','wyjście','exit','out'):
            target = 'temple_basement_deep_nest'
            floor = None
        elif value in ('1','2','3'):
            floor = int(value)
            target = CATACOMB_LEVELS_V0900[floor][0]
            if floor not in known:
                await self.send(f'Piętro {floor} Katakumb nie jest jeszcze odblokowane.')
                return
        else:
            await self.send('Użycie: portal 1, portal 2, portal 3 lub portal wyjdz.')
            return
        old = here
        candidates = (list(self.server.party_sessions(self.account_id,same_room=old))
                      if party_key == self.account_id else [self])
        if self not in candidates: candidates.append(self)
        moved=[]; skipped=[]
        for member in candidates:
            if not member or not getattr(member,'character',None): continue
            if getattr(member, 'current_hp', 1) <= 0 or getattr(member, 'is_downed_v0371', lambda: False)():
                skipped.append(f'{member.character.name}: postać martwa lub powalona'); continue
            if member.combat_mob_key:
                skipped.append(f'{member.character.name}: trwa walka'); continue
            if floor is not None and floor not in member.catacomb_unlocked_floors_v2010():
                skipped.append(f'{member.character.name}: piętro {floor} nieodblokowane'); continue
            member.previous_room_id = member.character.room_id
            member.previous_room_id = member.character.room_id
            member.character.room_id = target
            member.server.db.save_character(member.character)
            moved.append(member)
        for member in moved:
            await member.send(f'Portal Katakumb: {"wyjście" if floor is None else f"piętro {floor}"}.')
            await member.look()
        if skipped: await self.send('Nie przeniesiono: ' + '; '.join(skipped) + '.')


async def show_checkpoint_portal_status_v11331(
        self, *, kind, label, start_floor
):
        floors = self.checkpoint_portal_floors_v11331(kind)
        if not floors:
            await self.send(
                f"{label}: brak odblokowanych checkpointów. "
                f"Pierwszy portal jest na piętrze/poziomie {start_floor}."
            )
            return
        await self.send(
            f"{label}: najwyższy checkpoint {max(floors)}."
        )
        await self.send(
            "Odblokowane checkpointy: "
            + ", ".join(str(floor) for floor in floors)
            + "."
        )
        await self.send(
            "Checkpointy są co 10 pięter. Z dowolnego odblokowanego checkpointu możesz przejść portalem do innego odblokowanego checkpointu."
        )


async def party_checkpoint_portal_exit_v11331(
        self, *, kind, floor, target_room, label
):
        if getattr(self, "current_hp", 1) <= 0 or getattr(self, "is_downed_v0371", lambda: False)():
            await self.send("Martwa lub powalona postać nie może korzystać z portali.")
            return True
        """Exit a cleared 10-floor checkpoint with eligible local party."""
        party_key = self.party_key()
        if self.portal_requires_local_leader_v12811():
            leader = self.server.session_by_account(party_key)
            leader_name = (
                leader.character.name
                if leader and getattr(leader, "character", None)
                else "lider drużyny"
            )
            await self.send(
                f"W drużynie portal checkpointu uruchamia lider: {leader_name}."
            )
            return True

        old = self.character.room_id
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
            member.character.room_id = target_room
            member.server.db.save_character(member.character)
            moved.append(member)

        if moved:
            for member in moved:
                await member.send(
                    f"{label} checkpointu {floor} przenosi cię do wyjścia lochu."
                )
                await member.look()
            if len(moved) > 1:
                await self.send(
                    f"Portal checkpointu przenosi razem {len(moved)} graczy."
                )
        if skipped:
            await self.send(
                "Nie przeniesiono: " + "; ".join(skipped) + "."
            )
        return True


async def show_astral_portal_status(self, kind="astral"):
        if kind == "mythic_astral":
            await self.show_checkpoint_portal_status_v11331(
                kind="mythic_astral",
                label="Mityczny Astralny Portal",
                start_floor=10,
            )
            await self.send(
                "Przy Mitycznej Astralnej Bramie: astralportal <10/20/30/...>. "
                "Na checkpointcie: astralportal <odblokowane pietro> albo astralportal wyjdz."
            )
            return

        await self.show_checkpoint_portal_status_v11331(
            kind="astral",
            label="Astralny Portal",
            start_floor=ASTRAL_MIN_FLOOR,
        )
        await self.send(
            f"Przy Astralnej Bramie: astralportal "
            f"<{ASTRAL_MIN_FLOOR}/{ASTRAL_MIN_FLOOR + 10}/...>. "
            "Na checkpointcie: astralportal <odblokowane pietro> albo astralportal wyjdz."
        )

