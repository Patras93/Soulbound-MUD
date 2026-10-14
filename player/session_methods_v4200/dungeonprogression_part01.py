# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
def portal_requires_local_leader_v12811(self):
        """Allow solo travel even when an old party has an offline leader.

        The party leader is mandatory only for a multi-player portal action
        with another real connected party member standing in this room.
        """
        key = self.party_key()
        if key is None or key == self.account_id:
            return False
        here = self.character.room_id
        return any(
            member and member is not self and not getattr(member, "closed", False)
            and getattr(member, "character", None)
            and member.character.room_id == here
            for member in self.server.party_sessions(self.account_id, same_room=here)
        )


async def register_uoss_deep_dungeon_visit_v11331(self, room_id=None):
        floor = uoss_deep_dungeon_floor_number_v11331(
            room_id if room_id is not None else self.character.room_id
        )
        if floor is None:
            return False

        was_new = self.server.db.add_collection_entry(
            self.account_id,
            UOSS_DEEP_DUNGEON_VISITS_V11331,
            str(floor),
        )
        if was_new:
            await self.send(
                f"Deep Dungeon: odkrywasz piętro {floor}. "
                f"Najgłębszy zapisany poziom: {self.uoss_deep_dungeon_max_floor_v11331()}."
            )

        if floor >= UOSS_DEEP_DUNGEON_SERPENTARIUS_UNLOCK_FLOOR_V11331:
            unlocked = self.server.db.add_collection_entry(
                self.account_id,
                "deep_dungeon_discovery",
                "floor_100",
            )
            if unlocked:
                await self.send(
                    "Deep Dungeon: dotarcie do piętra 100 odblokowuje Floor 0 "
                    "i Super Bossa Serpentarius. Winda: deepelevator 0."
                )
        return True


async def show_uoss_deep_dungeon_status_v11331(self, args=""):
        highest = self.uoss_deep_dungeon_max_floor_v11331()
        unlock_floor = UOSS_DEEP_DUNGEON_SERPENTARIUS_UNLOCK_FLOOR_V11331
        unlocks = self.server.db.collection_entry_ids(
            self.account_id, "deep_dungeon_discovery"
        )
        serpentarius_unlocked = "floor_100" in unlocks

        await self.send("UOSS DEEP DUNGEON — BEZ LIMITU")
        await self.send(
            f"Najgłębsze odwiedzone piętro: {highest if highest else 'brak'}."
        )
        if highest:
            next_apanda = ((highest // 25) + 1) * 25
            await self.send(
                f"Apanda występuje co 25 pięter. Następny próg: {next_apanda}."
            )
        else:
            await self.send("Apanda występuje co 25 pięter: 25, 50, 75, 100 i dalej.")

        if serpentarius_unlocked:
            error = superboss_member_entry_error_v11331(
                self, "serpentarius"
            )
            if error:
                await self.send(
                    "Serpentarius: odblokowany przez piętro 100, "
                    f"ale wejście jest teraz niedostępne. {error}"
                )
            else:
                await self.send(
                    "Serpentarius: odblokowany. Użyj deepelevator 0 "
                    "albo superboss serpentarius."
                )
        else:
            await self.send(
                f"Serpentarius: zablokowany. Musisz osobiście dotrzeć "
                f"co najmniej do piętra {unlock_floor}."
            )
        await self.send(
            "Wejście: Sala Super Bossów, kierunek down. "
            "Winda: deepelevator <odwiedzone piętro>; Floor 0: deepelevator 0."
        )


async def use_uoss_deep_dungeon_elevator_v11331(self, raw=""):
        if self.combat_mob_key:
            await self.send("Nie możesz użyć windy Deep Dungeon podczas walki.")
            return

        current = str(self.character.room_id)
        current_floor = uoss_deep_dungeon_floor_number_v11331(current)
        if (
            current != UOSS_DEEP_DUNGEON_ENTRY_V11331
            and current != UOSS_DEEP_DUNGEON_FLOOR0_V11331
            and current_floor is None
        ):
            await self.send(
                "Winda Deep Dungeon działa tylko wewnątrz Deep Dungeon."
            )
            return

        value = self.normalize_room_query(raw)
        if not value or value in ("status", "lista", "list"):
            await self.show_uoss_deep_dungeon_status_v11331()
            return

        match = re.search(r"(\d+)", value)
        if not match:
            await self.send(
                "Użycie: deepelevator <odwiedzone piętro> albo deepelevator 0."
            )
            return
        floor = int(match.group(1))

        party_key = self.party_key()
        if self.portal_requires_local_leader_v12811():
            leader = self.server.session_by_account(party_key)
            leader_name = (
                leader.character.name
                if leader and getattr(leader, "character", None)
                else "lider drużyny"
            )
            await self.send(
                f"Tylko lider uruchamia windę dla drużyny. Lider: {leader_name}."
            )
            return

        candidates = (
            list(
                self.server.party_sessions(
                    self.account_id,
                    same_room=self.character.room_id,
                )
            )
            if party_key == self.account_id
            else [self]
        )
        if self not in candidates:
            candidates.append(self)

        target = (
            UOSS_DEEP_DUNGEON_FLOOR0_V11331
            if floor == 0
            else uoss_deep_dungeon_floor_id_v11331(floor)
        )
        if floor > 0:
            self.server.world.ensure_runtime_room(target)

        moved = []
        skipped = []
        for member in candidates:
            if not member or not getattr(member, "character", None):
                continue
            if member.combat_mob_key:
                skipped.append(f"{member.character.name}: trwa walka")
                continue

            member_highest = member.uoss_deep_dungeon_max_floor_v11331()
            if floor == 0:
                error = superboss_member_entry_error_v11331(
                    member, "serpentarius"
                )
                if error:
                    skipped.append(
                        f"{member.character.name}: {error}"
                    )
                    continue
            elif floor < 1 or floor > member_highest:
                skipped.append(
                    f"{member.character.name}: najwyższe odwiedzone piętro "
                    f"{member_highest if member_highest else 'brak'}"
                )
                continue

            member.previous_room_id = member.character.room_id
            member.previous_room_id = member.character.room_id
            member.character.room_id = target
            member.server.db.save_character(member.character)
            moved.append(member)

        if moved:
            destination = "Floor 0" if floor == 0 else f"piętro {floor}"
            for member in moved:
                await member.send(
                    f"Lider {self.character.name} uruchamia windę Deep Dungeon. "
                    f"Cel: {destination}."
                )
                await member.look()
            if len(moved) > 1:
                await self.send(
                    f"Winda przenosi razem {len(moved)} graczy."
                )
        if skipped:
            await self.send(
                "Nie przeniesiono: " + "; ".join(skipped) + "."
            )


async def auto_mine_descend_if_unlocked(self):
        if not self.auto_mining or self.closed:
            return False
        if self.combat_mob_key:
            return False

        current_room = self.character.room_id

        # v0.24.4: auto-kopanie potrafi wejść do Kopalni Głębinowej z całej
        # ręcznej części jaskini zamiast bez końca kopać przy wejściu.
        approach_steps = {
            "cave_entrance": ("down", "cave_tunnel"),
            "cave_tunnel": ("east", "crystal_chamber"),
            "crystal_chamber": ("down", mine_floor_id(MINE_MIN_FLOOR)),
        }
        if current_room in approach_steps:
            direction, target = approach_steps[current_room]
            if target.startswith("mine_floor_"):
                self.server.world.ensure_infinite_dungeon_floor(target)
            if ROOMS.get(current_room, {}).get("exits", {}).get(direction) != target:
                _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (current_room,), "exits", {})[direction] = target
            old = current_room
            self.previous_room_id = old
            await self.server.broadcast_room(old, f"{self.character.name} odchodzi.", exclude=self)
            self.character.room_id = target
            self.server.db.save_character(self.character)
            await self.discover_room(target, announce=False)
            await self.server.broadcast_room(target, f"{self.character.name} przychodzi.", exclude=self)
            await self.send(f"Auto-kopanie schodzi głębiej: {ROOMS[target]['name']}.")
            return True

        floor = mine_floor_number(current_room)
        if floor is None:
            return False

        expected_target = mine_floor_id(floor + 1)
        self.server.world.ensure_infinite_dungeon_floor(expected_target)
        # Napraw stare runtime-roomy/zapisy, którym brakowało wyjścia down.
        _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (current_room,), "exits", {})["down"] = expected_target
        target = ROOMS[current_room]["exits"].get("down")

        if target != expected_target:
            return False

        progress = self.mine_progress()
        if progress["max_floor_unlocked"] < floor + 1:
            return False

        if self.mine_descent_blocked_for_player(
            current_room,
            "down",
        ):
            return False

        old = current_room
        self.previous_room_id = old
        await self.server.broadcast_room(
            old,
            f"{self.character.name} odchodzi.",
            exclude=self,
        )

        self.character.room_id = target
        self.server.db.save_character(
            self.character
        )
        await self.discover_room(target, announce=False)

        await self.server.broadcast_room(
            target,
            f"{self.character.name} przychodzi.",
            exclude=self,
        )

        await self.send(
            f"Ściana w dół jest przebita. "
            f"Auto-kopanie schodzi na poziom {floor + 1}."
        )
        return True


async def auto_walk_to_target(self, target, label, flag_attr):
        path = self.shortest_path(
            self.character.room_id, target
        )
        if path is None:
            await self.send(
                f"{label}: nie udało się znaleźć drogi."
            )
            return False

        for direction, next_room in path:
            if self.closed or not getattr(self, flag_attr, False):
                return False
            if self.combat_mob_key:
                await self.send(
                    f"{label} zatrzymane: rozpoczęła się walka."
                )
                return False
            if self.mythic_entry_error(next_room):
                return False
            if self.profession_dungeon_access_error(next_room):
                return False
            if self.astral_entry_blocked(next_room):
                return False
            if self.mythic_crypt_descent_blocked_for_player(
                self.character.room_id, direction
            ):
                return False
            if self.mythic_astral_ascent_blocked_for_player(
                self.character.room_id, direction
            ):
                return False
            if self.giant_fortress_ascent_blocked_for_player(
                self.character.room_id, direction
            ):
                return False
            if self.crypt_descent_blocked_for_player(
                self.character.room_id, direction
            ):
                return False
            if self.astral_ascent_blocked_for_player(
                self.character.room_id, direction
            ):
                return False
            if self.mine_descent_blocked_for_player(
                self.character.room_id, direction
            ):
                await self.send(
                    f"{label}: ściana kopalni blokuje zejście."
                )
                return False

            old = self.character.room_id
            await self.server.broadcast_room(
                old,
                f"{self.character.name} odchodzi.",
                exclude=self,
            )
            self.character.room_id = next_room
            self.server.db.save_character(self.character)
            await self.discover_room(next_room, announce=False)
            await self.server.broadcast_room(
                next_room,
                f"{self.character.name} przychodzi.",
                exclude=self,
            )
            await self.send(
                f"{label}: {direction} -> "
                f"{ROOMS[next_room]['name']}."
            )
            await asyncio.sleep(0.12)

        return self.character.room_id == target


async def command_mineinfo_v1260(self, args):
    from core.mine_world_v1260 import geology_v1260, mine_map_lines_v1260, mine_route_v1260
    from core.mine_tunnels import mine_tunnel_coords, MINE_DIRECTION_LABELS
    mode = str(args or '').strip().casefold()
    if mode not in ('mapa','map','gdzie','where','droga','route','skarb','skarbiec','vault','wyprawa'):
        if not mode:
            await self.show_mine_info()
        else:
            await self.send('Komendy: kopalnia, kopalnia mapa, kopalnia gdzie, kopalnia droga, kopalnia skarb.')
        return
    pos = mine_tunnel_coords(self.character.room_id, self.account_id)
    if pos is None:
        await self.send('Te komendy działają wewnątrz Kopalni Głębinowej. Dojście: prowadz kopalnia.')
        return
    floor,x,y=pos
    cells=self.server.db.mine_tunnel_cells_v1260(self.account_id,floor)
    geo=geology_v1260(floor,x,y)
    if mode in ('gdzie','where'):
        await self.send(f'KOPALNIA: piętro {floor}, X={x}, Y={y}. Odkrycie: {geo["name"]}. '
                        f'Około {max(abs(x),abs(y))} kroków od centralnego szybu w linii prostej.')
    elif mode in ('mapa','map'):
        for line in mine_map_lines_v1260(cells,floor,(x,y)):
            await self.send(line)
    elif mode in ('droga','route'):
        route=mine_route_v1260(cells,(x,y))
        if route is None:
            await self.send('Brak odkrytego połączenia z centralnym szybem na tym piętrze.')
        elif not route:
            await self.send('Jesteś przy centralnym szybie. W górę: up; w dół: down.')
        else:
            await self.send(f'DROGA DO SZYBU: {len(route)} kroków. ' +
                            ', '.join(MINE_DIRECTION_LABELS[d] for d in route) + '. ' +
                            'Możesz przejść je kolejno komendą walk lub kierunkami.')
    elif mode in ('skarb','skarbiec','vault'):
        if geo['kind'] not in ('vault','chamber','ruins','rare_ore','lost_city','ancient_kingdom','giant_cavern'):
            await self.send('Tutaj nie ma skarbca ani reliktów do odebrania.')
            return
        if self.server.db.mine_claimed_v1260(self.account_id,floor,x,y):
            await self.send('To odkrycie zostało już przez ciebie odebrane.')
            return
        if geo['has_guardian'] and any(m.alive for m in self.server.world.room_mobs(self.character.room_id)
               if __import__('systems.content_registry',fromlist=['MOB_TEMPLATES']).MOB_TEMPLATES.get(m.template_id,{}).get('mine_guard_v1260')):
            await self.send('Skarbca pilnuje Strażnik Głębin. Pokonaj go, zanim odbierzesz łupy.')
            return
        # All loot is stored using the native profession casket and wallet.
        # The durable claim prevents duplication after deployment/relogin.
        if not self.server.db.mine_claim_v1260(self.account_id,floor,x,y):
            await self.send('Skarb został już odebrany.')
            return
        from core.mine_world_v1260 import discovery_mineral_reward_v1260
        from core.mines_threat import ITEMS
        mineral=discovery_mineral_reward_v1260(geo)
        material_text=''
        if mineral:
            item_id, amount=mineral
            if item_id in ITEMS:
                self.server.db.add_item(self.account_id,item_id,amount)
                material_text=f' Rzadki zasób: {amount} x {ITEMS[item_id]["name"]}.'
        self.character.gold += geo['reward_gold']
        self.server.db.save_character(self.character)
        await self.send(f'ODKRYCIE O KURDE: {geo["name"]}! Zdobywasz {geo["reward_gold"]} złota.'
                        + material_text + ' Skarb jest jednorazowy i zapisany na stałe.')
    else:
        await self.send('Wielkie wyprawy: zobacz wyprawy oraz legendarne wyprawy; '
                        'twoje postępy kopalniane są zapisane na stałe.')

