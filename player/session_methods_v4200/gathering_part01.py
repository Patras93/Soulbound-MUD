# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def stop_auto_fishing(self, announce=True, immediate=True):
        self.auto_fishing = False
        task = self.auto_fishing_task
        if immediate:
            self.auto_fishing_task = None
            if task and task is not asyncio.current_task() and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:  # AUDIT_INTENTIONAL_PASS: normal auto-action task cancellation
                    pass
            if announce:
                await self.send("Auto-łowienie wyłączone.")
            return
        if task and not task.done():
            if announce:
                await self.send(
                    "Auto-łowienie wyłączone. "
                    "Trwający połów zostanie dokończony, ale następny już się nie rozpocznie."
                )
            return
        self.auto_fishing_task = None
        if announce:
            await self.send("Auto-łowienie wyłączone.")


async def auto_fishing_loop(self):
        try:
            while self.auto_fishing and not self.closed:
                if self.combat_mob_key:
                    await self.send(
                        "Auto-łowienie zatrzymane: rozpoczęła się walka."
                    )
                    break
                if self.server.db.item_qty(
                    self.account_id, "fishing_rod"
                ) <= 0:
                    await self.send(
                        "Auto-łowienie zatrzymane: nie masz Wędki."
                    )
                    break
                if self.character.room_id not in FISHING_ROOMS and not self.active_event_fishery_v3312():
                    await self.send(
                        "Auto-łowienie zatrzymane: nie stoisz przy łowisku."
                    )
                    break
                await self.fish(from_auto=True)
        except asyncio.CancelledError:  # AUDIT_INTENTIONAL_PASS: normal auto-action task cancellation
            pass
        except Exception as exc:
            try:
                await self.send(
                    f"Auto-łowienie zatrzymane przez błąd wewnętrzny: "
                    f"{type(exc).__name__}: {exc}."
                )
            except Exception:  # AUDIT_INTENTIONAL_PASS: secondary error reporting must not mask the original failure
                pass
            try:
                import traceback
                print("AUTO_FISHING_ERROR\n" + traceback.format_exc(), flush=True)
            except Exception:  # AUDIT_INTENTIONAL_PASS: secondary error reporting must not mask the original failure
                pass
        finally:
            self.auto_fishing = False
            if self.auto_fishing_task is asyncio.current_task():
                self.auto_fishing_task = None


async def set_auto_fishing(self, enabled):
        if enabled:
            if self.auto_fishing:
                await self.send("Auto-łowienie jest już włączone.")
                return
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz rozpocząć auto-łowienia podczas walki."
                )
                return
            if self.server.db.item_qty(
                self.account_id, "fishing_rod"
            ) <= 0:
                await self.send(
                    "Do auto-łowienia potrzebujesz Wędki."
                )
                return
            if self.character.room_id not in FISHING_ROOMS and not self.active_event_fishery_v3312():
                await self.send(
                    "Auto-łowienie możesz włączyć tylko przy łowisku. "
                    "Automat nie chodzi sam."
                )
                return
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)
            self.auto_fishing = True
            self.auto_fishing_task = asyncio.create_task(
                self.auto_fishing_loop()
            )
            await self.send(
                "Auto-łowienie włączone. Łowi tylko w aktualnym miejscu "
                "i nie chodzi samodzielnie. "
                "Wpisz low off albo fish off, aby je zatrzymać."
            )
            return
        if not self.auto_fishing and not self.auto_fishing_task:
            await self.send("Auto-łowienie jest już wyłączone.")
            return
        await self.stop_auto_fishing(
            announce=True, immediate=False
        )


async def stop_auto_mining(self, announce=True, immediate=True):
        self.auto_mining = False
        self.auto_mine_direction_v1251 = None
        task = self.auto_mining_task
        if immediate:
            self.auto_mining_task = None
            if task and task is not asyncio.current_task() and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:  # AUDIT_INTENTIONAL_PASS: normal auto-action task cancellation
                    pass
            if announce:
                await self.send("Auto-kopanie wyłączone.")
            return
        if task and not task.done():
            if announce:
                await self.send(
                    "Auto-kopanie wyłączone. "
                    "Trwające wydobycie zostanie dokończone, ale następne już się nie rozpocznie."
                )
            return
        self.auto_mining_task = None
        if announce:
            await self.send("Auto-kopanie wyłączone.")


async def auto_mining_loop(self):
        try:
            while self.auto_mining and not self.closed:
                if self.combat_mob_key:
                    await self.send(
                        "Auto-kopanie zatrzymane: rozpoczęła się walka."
                    )
                    break
                if self.server.db.item_qty(
                    self.account_id, "pickaxe"
                ) <= 0:
                    await self.send(
                        "Auto-kopanie zatrzymane: nie masz Kilofa."
                    )
                    break
                if not is_mining_room(self.character.room_id) and not self.active_profession_event_v3312("mining"):
                    await self.send(
                        "Auto-kopanie zatrzymane: nie stoisz w miejscu wydobycia."
                    )
                    break
                direction = getattr(self, 'auto_mine_direction_v1251', None)
                if direction == 'up':
                    from core.progression_resources import mine_floor_number
                    floor = mine_floor_number(self.character.room_id)
                    if floor is None or floor <= 1:
                        await self.send('Kopalnia: osiągnięto najwyższe piętro. Auto-kopanie zatrzymane.')
                        break
                    old = self.character.room_id
                    await self.move('up', preserve_auto_mining=True)
                    if self.character.room_id == old:
                        await self.send('Nie można przejść wyżej. Auto-kopanie zatrzymane.')
                        break
                    continue
                if direction is None or direction == 'down':
                    if await self.auto_mine_descend_if_unlocked():
                        continue
                if direction in HORIZONTAL_MINE_DIRECTIONS:
                    from core.mine_tunnels import mine_tunnel_coords
                    pos = mine_tunnel_coords(self.character.room_id, self.account_id)
                    if pos is None:
                        await self.send('Auto-kopanie boczne wymaga piętra Kopalni Głębinowej.')
                        break
                    if self.server.db.mine_tunnel_target_v1251(self.account_id, *pos, direction):
                        old = self.character.room_id
                        await self.move(direction, preserve_auto_mining=True)
                        if self.character.room_id == old:
                            await self.send('Przejście niedostępne. Auto-kopanie zatrzymane.')
                            break
                        continue
                await self.mine(from_auto=True, direction=direction)
        except asyncio.CancelledError:  # AUDIT_INTENTIONAL_PASS: normal auto-action task cancellation
            pass
        except Exception as exc:
            try:
                await self.send(
                    f"Auto-kopanie zatrzymane przez błąd wewnętrzny: "
                    f"{type(exc).__name__}: {exc}."
                )
            except Exception:  # AUDIT_INTENTIONAL_PASS: secondary error reporting must not mask the original failure
                pass
            try:
                import traceback
                print("AUTO_MINING_ERROR\n" + traceback.format_exc(), flush=True)
            except Exception:  # AUDIT_INTENTIONAL_PASS: secondary error reporting must not mask the original failure
                pass
        finally:
            self.auto_mining = False
            self.auto_mine_direction_v1251 = None
            if self.auto_mining_task is asyncio.current_task():
                self.auto_mining_task = None


async def set_auto_mining(self, enabled, direction=None):
        if enabled:
            from core.mine_tunnels import HORIZONTAL_MINE_DIRECTIONS
            if direction in HORIZONTAL_MINE_DIRECTIONS:
                from core.mine_tunnels import mine_tunnel_coords
                if mine_tunnel_coords(self.character.room_id, self.account_id) is None:
                    await self.send('Najpierw wejdź na poziom Kopalni Głębinowej.')
                    return
            if self.auto_mining:
                self.auto_mine_direction_v1251 = direction
                await self.send('Zmieniono kierunek auto-kopania na: ' + (direction or 'down') + '.')
                return
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz rozpocząć auto-kopania podczas walki."
                )
                return
            if self.server.db.item_qty(
                self.account_id, "pickaxe"
            ) <= 0:
                await self.send(
                    "Do auto-kopania potrzebujesz Kilofa."
                )
                return
            if not is_mining_room(self.character.room_id) and not self.active_profession_event_v3312("mining"):
                await self.send(
                    "Auto-kopanie możesz włączyć tylko w miejscu wydobycia. "
                    "Automat nie chodzi sam."
                )
                return
            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)
            self.auto_mine_direction_v1251 = direction
            self.auto_mining = True
            self.auto_mining_task = asyncio.create_task(
                self.auto_mining_loop()
            )
            if direction and direction != 'down':
                await self.send(
                    f'Auto-kopanie włączone: {direction}. '
                    'Automat będzie drążyć wybrany kierunek, a po przebiciu '
                    'przejścia przesunie się do następnego chodnika. '
                    'Wpisz kop off, aby zatrzymać.'
                )
            elif self.active_profession_event_v3312("mining") and not is_mining_room(self.character.room_id):
                await self.send(
                    'Auto-kopanie włączone na aktywnym złożu wydarzenia. '
                    'Pozostaje w bieżącym sektorze; po zakończeniu wydarzenia się zatrzyma. '
                    'Wpisz kop off, aby wyłączyć.'
                )
            else:
                await self.send(
                    'Auto-kopanie włączone: schodzenie w dół. '
                    'Z części wejściowej automat dociera do piętra 1; '
                    'po przebiciu ściany schodzi na następne piętro. '
                    'Wpisz kop off albo mine off, aby zatrzymać.'
                )
            return
        if not self.auto_mining and not self.auto_mining_task:
            await self.send("Auto-kopanie jest już wyłączone.")
            return
        await self.stop_auto_mining(
            announce=True, immediate=False
        )


async def stop_auto_woodcutting(self, announce=True, immediate=True):
        self.auto_woodcutting = False
        task = self.auto_woodcutting_task
        if immediate:
            self.auto_woodcutting_task = None
            if task and task is not asyncio.current_task() and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:  # AUDIT_INTENTIONAL_PASS: normal auto-action task cancellation
                    pass
            if announce:
                await self.send("Auto-Drwalstwo wyłączone.")
            return
        if task and not task.done():
            if announce:
                await self.send(
                    "Auto-Drwalstwo wyłączone. "
                    "Trwające cięcie zostanie dokończone, ale następne już się nie rozpocznie."
                )
            return
        self.auto_woodcutting_task = None
        if announce:
            await self.send("Auto-Drwalstwo wyłączone.")


async def auto_woodcutting_loop(self):
        try:
            while self.auto_woodcutting and not self.closed:
                if self.combat_mob_key:
                    await self.send(
                        "Auto-Drwalstwo zatrzymane: rozpoczęła się walka."
                    )
                    break
                if self.server.db.item_qty(
                    self.account_id, "saw"
                ) <= 0:
                    await self.send(
                        "Auto-Drwalstwo zatrzymane: nie masz Piły."
                    )
                    break
                if self.character.room_id not in WOODCUTTING_ROOMS and not self.active_profession_event_v3312("woodcutting"):
                    await self.send(
                        "Auto-Drwalstwo zatrzymane: nie stoisz przy drzewach."
                    )
                    break
                await self.woodcut(from_auto=True)
        except asyncio.CancelledError:  # AUDIT_INTENTIONAL_PASS: normal auto-action task cancellation
            pass
        except Exception as exc:
            try:
                await self.send(
                    f"Auto-Drwalstwo zatrzymane przez błąd wewnętrzny: "
                    f"{type(exc).__name__}: {exc}."
                )
            except Exception:  # AUDIT_INTENTIONAL_PASS: secondary error reporting must not mask the original failure
                pass
            try:
                import traceback
                print("AUTO_WOODCUTTING_ERROR\n" + traceback.format_exc(), flush=True)
            except Exception:  # AUDIT_INTENTIONAL_PASS: secondary error reporting must not mask the original failure
                pass
        finally:
            self.auto_woodcutting = False
            if self.auto_woodcutting_task is asyncio.current_task():
                self.auto_woodcutting_task = None


async def set_auto_woodcutting(self, enabled):
        if enabled:
            if self.auto_woodcutting:
                await self.send(
                    "Auto-Drwalstwo jest już włączone."
                )
                return
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz rozpocząć auto-Drwalstwa podczas walki."
                )
                return
            if self.server.db.item_qty(
                self.account_id, "saw"
            ) <= 0:
                await self.send(
                    "Do auto-Drwalstwa potrzebujesz Piły."
                )
                return
            if self.character.room_id not in WOODCUTTING_ROOMS and not self.active_profession_event_v3312("woodcutting"):
                await self.send(
                    "Auto-Drwalstwo możesz włączyć tylko przy drzewach. "
                    "Automat nie chodzi sam."
                )
                return
            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)
            self.auto_woodcutting = True
            self.auto_woodcutting_task = asyncio.create_task(
                self.auto_woodcutting_loop()
            )
            await self.send(
                "Auto-Drwalstwo włączone. Ścina tylko w aktualnym miejscu "
                "i nie chodzi samodzielnie. "
                "Wpisz tnij off albo woodcut off, aby je zatrzymać."
            )
            return
        if not self.auto_woodcutting and not self.auto_woodcutting_task:
            await self.send(
                "Auto-Drwalstwo jest już wyłączone."
            )
            return
        await self.stop_auto_woodcutting(
            announce=True, immediate=False
        )


async def stop_auto_herbalism(self, announce=True, immediate=True):
        self.auto_herbalism = False
        task = self.auto_herbalism_task

        if immediate:
            self.auto_herbalism_task = None
            if task and task is not asyncio.current_task() and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:  # AUDIT_INTENTIONAL_PASS: normal auto-action task cancellation
                    pass
            if announce:
                await self.send("Auto-Zielarstwo wyłączone.")
            return

        if task and not task.done():
            if announce:
                await self.send(
                    "Auto-Zielarstwo wyłączone. "
                    "Trwający zbiór zostanie dokończony, ale następny już się nie rozpocznie."
                )
            return

        self.auto_herbalism_task = None
        if announce:
            await self.send("Auto-Zielarstwo wyłączone.")


async def auto_herbalism_loop(self):
        try:
            while self.auto_herbalism and not self.closed:
                if self.combat_mob_key:
                    await self.send(
                        "Auto-Zielarstwo zatrzymane: rozpoczęła się walka."
                    )
                    break
                if self.server.db.item_qty(
                    self.account_id, "herbalist_sickle"
                ) <= 0:
                    await self.send(
                        "Auto-Zielarstwo zatrzymane: nie masz Sierpa Zielarskiego."
                    )
                    break
                if self.character.room_id not in HERBALISM_ROOMS and not self.active_profession_event_v3312("herbalism"):
                    await self.send(
                        "Auto-Zielarstwo zatrzymane: nie stoisz w miejscu z ziołami."
                    )
                    break

                await self.gather_herb(from_auto=True)

        except asyncio.CancelledError:  # AUDIT_INTENTIONAL_PASS: normal auto-action task cancellation
            pass
        except Exception as exc:
            try:
                await self.send(
                    f"Auto-Zielarstwo zatrzymane przez błąd wewnętrzny: "
                    f"{type(exc).__name__}: {exc}."
                )
            except Exception:  # AUDIT_INTENTIONAL_PASS: secondary error reporting must not mask the original failure
                pass
            try:
                import traceback
                print("AUTO_HERBALISM_ERROR\n" + traceback.format_exc(), flush=True)
            except Exception:  # AUDIT_INTENTIONAL_PASS: secondary error reporting must not mask the original failure
                pass
        finally:
            self.auto_herbalism = False
            if self.auto_herbalism_task is asyncio.current_task():
                self.auto_herbalism_task = None


async def set_auto_herbalism(self, enabled):
        if enabled:
            if self.auto_herbalism:
                await self.send(
                    "Auto-Zielarstwo jest już włączone."
                )
                return
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz rozpocząć auto-Zielarstwa podczas walki."
                )
                return
            if self.server.db.item_qty(
                self.account_id, "herbalist_sickle"
            ) <= 0:
                await self.send(
                    "Do auto-Zielarstwa potrzebujesz Sierpa Zielarskiego."
                )
                return

            if self.character.room_id not in HERBALISM_ROOMS and not self.active_profession_event_v3312("herbalism"):
                await self.send(
                    "Auto-Zielarstwo możesz włączyć tylko w miejscu z ziołami. "
                    "Automat nie chodzi sam."
                )
                return

            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)

            self.auto_herbalism = True
            self.auto_herbalism_task = asyncio.create_task(
                self.auto_herbalism_loop()
            )
            await self.send(
                "Auto-Zielarstwo włączone. Zbiera tylko w aktualnym miejscu "
                "i nie chodzi samodzielnie. "
                "Wpisz zbieraj off, aby je zatrzymać."
            )
            return

        if not self.auto_herbalism and not self.auto_herbalism_task:
            await self.send(
                "Auto-Zielarstwo jest już wyłączone."
            )
            return
        await self.stop_auto_herbalism(
            announce=True, immediate=False
        )

