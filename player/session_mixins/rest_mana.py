# -*- coding: utf-8 -*-
"""Rest and mana regeneration."""

class SessionRestManaMixin:

    def rest_status_text(self):
            if not self.character:
                return "Brak postaci."
            max_hp = self.max_hp()
            max_mana = self.max_mana()
            if max_mana > 0:
                return (
                    f"HP {self.current_hp} z {max_hp}. "
                    f"Mana {self.current_mana} z {max_mana}. "
                    f"Odpoczynek: {'aktywny' if self.resting else 'wyłączony'}."
                )
            return (
                f"HP {self.current_hp} z {max_hp}. "
                f"Odpoczynek: {'aktywny' if self.resting else 'wyłączony'}."
            )

    def rest_needs_regeneration(self):
            if not self.character:
                return False

            if self.current_hp < self.max_hp():
                return True

            max_mana = self.max_mana()
            return (
                max_mana > 0
                and self.current_mana < max_mana
            )

    async def rest_tick(self):
            if not self.character:
                return False

            max_hp = self.max_hp()
            max_mana = self.max_mana()

            hp_before = self.current_hp
            mana_before = self.current_mana

            hp_gain = max(
                1,
                (max_hp * REST_REGEN_PERCENT + 99) // 100,
            )
            self.current_hp = min(
                max_hp,
                self.current_hp + hp_gain,
            )

            if max_mana > 0:
                mana_gain = max(
                    1,
                    (max_mana * REST_REGEN_PERCENT + 99) // 100,
                )
                self.current_mana = min(
                    max_mana,
                    self.current_mana + mana_gain,
                )
            else:
                self.current_mana = 0

            if (
                self.current_hp != hp_before
                or self.current_mana != mana_before
            ):
                if max_mana > 0:
                    await self.send(
                        f"Regeneracja: HP {self.current_hp} z {max_hp}. "
                        f"Mana {self.current_mana} z {max_mana}."
                    )
                else:
                    await self.send(
                        f"Regeneracja: HP {self.current_hp} z {max_hp}."
                    )

            return self.rest_needs_regeneration()

    async def rest_loop(self):
            try:
                while self.resting and not self.closed:
                    await asyncio.sleep(REST_TICK_SECONDS)

                    if (
                        not self.resting
                        or self.closed
                        or self.combat_mob_key
                    ):
                        break

                    needs_more = await self.rest_tick()
                    if not needs_more:
                        self.resting = False
                        await self.send(
                            "Odpoczynek zakończony. "
                            "HP i Mana są pełne."
                        )
                        break
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                try:
                    await self.send(
                        f"Odpoczynek został zatrzymany przez błąd wewnętrzny: "
                        f"{type(exc).__name__}: {exc}."
                    )
                except Exception:
                    pass
                try:
                    import traceback
                    print("REST_LOOP_ERROR\n" + traceback.format_exc(), flush=True)
                except Exception:
                    pass
            finally:
                self.resting = False
                if self.rest_task is asyncio.current_task():
                    self.rest_task = None

    async def stop_rest(self, announce=True, reason=None):
            was_resting = self.resting or (
                self.rest_task is not None
                and not self.rest_task.done()
            )

            self.resting = False
            task = self.rest_task
            self.rest_task = None

            if (
                task
                and task is not asyncio.current_task()
                and not task.done()
            ):
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            if announce and was_resting:
                if reason:
                    await self.send(
                        f"Odpoczynek przerwany: {reason}."
                    )
                else:
                    await self.send(
                        "Odpoczynek przerwany."
                    )

            return was_resting

    async def start_rest(self):
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz odpoczywać podczas walki. "
                    "Najpierw pokonaj przeciwnika albo użyj flee."
                )
                return

            if self.resting:
                await self.send(self.rest_status_text())
                return

            if not self.rest_needs_regeneration():
                await self.send(
                    "Nie musisz odpoczywać. "
                    "HP i Mana są już pełne."
                )
                return

            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)

            self.resting = True
            self.rest_task = asyncio.create_task(
                self.rest_loop()
            )

            await self.send(
                "Rozpoczynasz odpoczynek. "
                "Co 5 sekund regenerujesz HP i Manę."
            )
            await self.send(self.rest_status_text())

    async def start_mana_regen(self):
            # v0.6.84: nie ma już osobnego trybu tylko Many.
            # Każdy regen prowadzi do pełnego odpoczynku HP + Mana.
            await self.start_rest()

    async def handle_mana_command(self, raw):
            action = normalize_lookup_text(raw)

            if action in ("", "status", "stan"):
                await self.send(
                    f"Mana: {self.current_mana} z {self.max_mana()}."
                )
                if self.resting:
                    await self.send(
                        "Odpoczynek: włączony. "
                        "Regenerujesz HP i Manę."
                    )
                return

            if action in (
                "regen",
                "regeneruj",
                "on",
                "start",
            ):
                await self.start_rest()
                return

            if action in (
                "off",
                "stop",
                "koniec",
                "przerwij",
            ):
                if not await self.stop_rest(announce=True):
                    await self.send(
                        "Odpoczynek nie jest włączony."
                    )
                return

            await self.send(
                "Użycie: mana, mana regen, mana stop. "
                "Mana regen uruchamia pełny odpoczynek HP i Many."
            )

    async def handle_rest(self, raw):
            action = normalize_lookup_text(raw)

            if action in ("status", "stan"):
                await self.send(self.rest_status_text())
                return

            # regen mana i odpoczywaj mana również regenerują wszystko.
            if action in (
                "mana",
                "mana on",
                "mana start",
                "mana regen",
            ):
                await self.start_rest()
                return

            if action in (
                "mana off",
                "mana stop",
                "off",
                "stop",
                "koniec",
                "przerwij",
            ):
                if not await self.stop_rest(announce=True):
                    await self.send("Nie odpoczywasz.")
                return

            if action in ("", "on", "start"):
                await self.start_rest()
                return

            await self.send(
                "Użycie: odpoczywaj, regen, regen mana, "
                "odpoczywaj status, odpoczywaj stop."
            )
