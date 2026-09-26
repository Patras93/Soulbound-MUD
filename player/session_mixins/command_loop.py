# -*- coding: utf-8 -*-
"""Soulbound v0.49.0 Session command loop.

The loop now parses transport/state only. Command identity, aliases, handlers and
state-safety metadata live in the central command registry.
"""
from __future__ import annotations

import time

from core.command_catalog import COMMAND_LOOP_BREAK
from core.mines_threat import DIRECTION_ALIASES
from player.session_mixins.command_registry import command_state_safe, resolve_session_command


class SessionCommandLoopMixin:
    async def command_loop(self):
        while not self.closed:
            # Cichy prompt dla NVDA: klient po prostu czeka na kolejną linię.
            raw = await self.read_line()
            if raw is None:
                break
            if raw.startswith("'"):
                await self.say(raw[1:])
                continue
            if raw.strip() == "/":
                await self.teleport_to_temple_command()
                continue

            if self.guide_choice_state:
                normalized_raw = self.normalize_room_query(raw)
                if raw.strip().isdigit() or normalized_raw in ("anuluj", "cancel", "stop"):
                    handled = await self.handle_guide_choice_number(raw)
                    if handled:
                        continue
                else:
                    self.guide_choice_state = None

            # Naturalne nazwy wejść do instancji są pre-parserem świata, nie
            # aliasami komend; mogą zawierać więcej niż jeden wyraz.
            if await self.try_dungeon_entry_command_v03812(raw):
                continue

            parts = raw.split(maxsplit=1)
            token = parts[0].lower() if parts else ""
            args = parts[1] if len(parts) > 1 else ""
            command = resolve_session_command(token, args)
            direction = DIRECTION_ALIASES.get(command)
            self._last_command_for_diagnostics = command

            if self.is_downed_v0371():
                if direction or not command_state_safe(command, "downed"):
                    remaining = max(0, int(round(self.party_downed_until_v0371 - time.time())))
                    await self.send(
                        f"Jesteś powalony. Pozostało około {remaining} s na wskrzeszenie. "
                        "Czekaj na członka drużyny albo wpisz odrodz."
                    )
                    continue

            if self.resting and not direction and not command_state_safe(command, "rest"):
                await self.stop_rest(announce=True, reason="wykonujesz inną akcję")

            if self.guide_task_active() and (
                direction or not command_state_safe(command, "guide")
            ):
                await self.cancel_guide(
                    announce=True,
                    reason="Prowadzenie przerwane: wykonujesz ręczny ruch albo inną aktywność.",
                )

            if direction:
                await self.move(direction)
                continue

            _perf_started_v0718 = time.perf_counter()
            dispatched = await self.dispatch_registered_command(command, args)
            _perf_elapsed_v0718 = time.perf_counter() - _perf_started_v0718
            if _perf_elapsed_v0718 >= 0.25:
                print(
                    f"[PERF SLOW COMMAND] {command or token}: {_perf_elapsed_v0718:.3f}s",
                    flush=True,
                )
            if dispatched is COMMAND_LOOP_BREAK:
                break
            if dispatched:
                continue

            await self.send("Nieznana komenda. Wpisz help.")

    async def leave_current_character_for_selection(self):
            """Zapisz i wyprowadź aktywną postać ze świata bez zamykania połączenia."""
            if not self.character:
                self.account_id = None
                return

            # Zatrzymaj wszystkie aktywności przypisane do bieżącej postaci.
            self.clear_downed_v0371(cancel_task=True)
            if self.guide_task_active():
                await self.cancel_guide(announce=False)
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

            await self.leave_party(announce=False)
            old_room = self.character.room_id
            old_name = self.character.name

            await self.stop_realtime_combat()
            self.server.release_all_engagements_for_session(self)
            self.combat_mob_key = None

            await self.show_session_summary()
            self.server.db.save_character(self.character)
            self.server.db.mark_player_logout_v0363(self.account_id)
            await self.server.broadcast_room(
                old_room, f"{old_name} opuszcza grę.", exclude=self
            )

            # Wyczyść tylko stan sesyjny postaci. Konto główne zostaje zalogowane.
            self.account_id = None
            self.character = None
            self.current_hp = 0
            self.current_mana = 0
            self.combat_hp_warn_level = 0
            self.skill_cooldowns = {}
            self.skill_guard = 0
            self.skill_evade = False
            self.skill_evade_lockout_until = 0.0
            self.active_skill_buffs = {}
            self._party_auto_heal_busy = False
            self.skill_queue_cursors = {"physical": 0, "magic": 0}
            self.skill_queue_next_type = "physical"
            self.auto_queue_casting = False
            self.guide_choice_state = None
            self.quest_list_context = None
            self.previous_room_id = None
            self.last_private_sender_account_id = None
            self.last_private_sender_name = None
            self._session_summary = None

    async def close(self):
            if self.closed:
                return
            self.clear_downed_v0371(cancel_task=True)
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
            if self.character:
                await self.leave_party(announce=False)
            await self.stop_realtime_combat()
            self.closed = True
            if self.character:
                self.server.release_all_engagements_for_session(self)
            if self.character:
                self.server.db.save_character(self.character)
                self.server.db.mark_player_logout_v0363(self.account_id)
                await self.server.broadcast_room(
                    self.character.room_id, f"{self.character.name} opuszcza grę.", exclude=self
                )
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass
