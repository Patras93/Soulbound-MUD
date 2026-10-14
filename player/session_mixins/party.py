# v4.20.0: bound, AST-identical method implementations (MRO unchanged)
from core.legacy_method_binding_v4200 import bind_legacy_method_v4200 as _sb420_bind
import player.session_methods_v4200.party_part01 as _sb420_src_01
# SessionPartyMixin.clean_party_player_argument -> player/session_methods_v4200/party_part01.py
# SessionPartyMixin.auto_priest_heal_option -> player/session_methods_v4200/party_part01.py
# SessionPartyMixin.perform_auto_priest_heal -> player/session_methods_v4200/party_part01.py
# SessionPartyMixin.begin_downed_v0371 -> player/session_methods_v4200/party_part01.py
# SessionPartyMixin.respawn_from_downed_v0371 -> player/session_methods_v4200/party_part01.py
# SessionPartyMixin.revive_party_member_v0371 -> player/session_methods_v4200/party_part01.py
# SessionPartyMixin.respawn_downed_player_v11343 -> player/session_methods_v4200/party_part01.py
# SessionPartyMixin.create_party -> player/session_methods_v4200/party_part01.py
# SessionPartyMixin.transfer_party_leader -> player/session_methods_v4200/party_part01.py
# SessionPartyMixin.stop_party_protection -> player/session_methods_v4200/party_part01.py
# SessionPartyMixin.protect_party -> player/session_methods_v4200/party_part01.py
import player.session_methods_v4200.party_part02 as _sb420_src_02
# SessionPartyMixin.show_party -> player/session_methods_v4200/party_part02.py
# SessionPartyMixin.set_party_goal_v0610 -> player/session_methods_v4200/party_part02.py
# SessionPartyMixin.show_party_ready_v0610 -> player/session_methods_v4200/party_part02.py
# SessionPartyMixin.handle_party_ready_v0610 -> player/session_methods_v4200/party_part02.py
# SessionPartyMixin.set_party_not_ready_v0610 -> player/session_methods_v4200/party_part02.py
# SessionPartyMixin.leave_party -> player/session_methods_v4200/party_part02.py
# SessionPartyMixin.disband_party -> player/session_methods_v4200/party_part02.py
# SessionPartyMixin.party_invite -> player/session_methods_v4200/party_part02.py
# SessionPartyMixin.party_accept -> player/session_methods_v4200/party_part02.py
# SessionPartyMixin.party_kick -> player/session_methods_v4200/party_part02.py
# SessionPartyMixin.assist_party_member -> player/session_methods_v4200/party_part02.py
import player.session_methods_v4200.party_part03 as _sb420_src_03
# SessionPartyMixin.handle_party -> player/session_methods_v4200/party_part03.py

# -*- coding: utf-8 -*-
"""Party creation, protection, revive and assist."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
import asyncio
import time
from core.progression_resources import skill_power_multiplier
from player.character import PARTY_BASE_CAPACITY
from player.session_mixins.io_auth_character import CLASS_SKILLS
from player.session_mixins.movement import MOB_TEMPLATES, ROOMS
from systems.party_synergies import (
    party_synergy_healing_multiplier_v11338,
    party_synergy_summary_v11338,
    party_synergy2_summary_v11339,
)


class SessionPartyMixin:

    def party_key(self):
            return self.server.party_key_for_account(self.account_id)

    def clean_party_player_argument(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method clean_party_player_argument")

    def auto_priest_heal_option(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method auto_priest_heal_option")

    async def perform_auto_priest_heal(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method perform_auto_priest_heal")

    def is_downed_v0371(self):
            return bool(
                self.character
                and self.current_hp <= 0
                and float(getattr(self, "party_downed_until_v0371", 0.0) or 0.0) > time.time()
                and getattr(self, "party_downed_room_v0371", None) == self.character.room_id
            )

    def party_revive_candidates_v0371(self):
            if not self.character or self.party_key() is None:
                return []
            room_id = self.character.room_id
            return [
                member for member in self.server.party_sessions(self.account_id, same_room=room_id)
                if member is not self and member.character and not member.closed and member.current_hp > 0
            ]

    def clear_downed_v0371(self, cancel_task=True):
            task = getattr(self, "party_downed_task_v0371", None)
            current = asyncio.current_task()
            if cancel_task and task and task is not current and not task.done():
                task.cancel()
            self.party_downed_task_v0371 = None
            self.party_downed_until_v0371 = 0.0
            self.party_downed_killer_v0371 = ""
            self.party_downed_room_v0371 = None

    async def _party_downed_timeout_v0371(self, deadline, room_id):
            try:
                await asyncio.sleep(max(0.0, float(deadline) - time.time()))
            except asyncio.CancelledError:
                return
            if (
                self.closed or not self.character or self.current_hp > 0
                or getattr(self, "party_downed_room_v0371", None) != room_id
                or float(getattr(self, "party_downed_until_v0371", 0.0) or 0.0) != float(deadline)
            ):
                return
            await self.respawn_from_downed_v0371(auto=True)

    async def begin_downed_v0371(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method begin_downed_v0371")

    async def respawn_from_downed_v0371(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method respawn_from_downed_v0371")

    async def revive_party_member_v0371(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method revive_party_member_v0371")

    async def respawn_downed_player_v11343(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method respawn_downed_player_v11343")

    async def create_party(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method create_party")

    async def transfer_party_leader(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method transfer_party_leader")

    async def stop_party_protection(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method stop_party_protection")

    async def protect_party(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method protect_party")

    async def show_party(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_party")

    async def set_party_goal_v0610(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method set_party_goal_v0610")

    async def show_party_ready_v0610(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_party_ready_v0610")

    async def handle_party_ready_v0610(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method handle_party_ready_v0610")

    async def set_party_not_ready_v0610(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method set_party_not_ready_v0610")

    async def leave_party(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method leave_party")

    async def disband_party(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method disband_party")

    async def party_invite(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method party_invite")

    async def party_accept(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method party_accept")

    async def party_decline(self):
            leader_id = self.server.party_invites.pop(self.account_id, None)
            if leader_id is None:
                await self.send("Nie masz aktywnego zaproszenia.")
                return
            leader = self.server.session_by_account(leader_id)
            if leader:
                await leader.send(
                    f"{self.character.name} odrzuca zaproszenie do drużyny."
                )
            await self.send("Odrzucasz zaproszenie do drużyny.")

    async def party_kick(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method party_kick")

    async def party_chat(self, message):
            if not message.strip():
                await self.send("Użycie: pc <tekst>.")
                return
            if self.party_key() is None:
                await self.send("Nie należysz do drużyny.")
                return
            await self.server.party_broadcast(
                self.account_id,
                f"[Drużyna] {self.character.name}: {message.strip()}",
                history_category="party",
            )

    async def assist_party_member(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method assist_party_member")

    async def handle_party(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method handle_party")

# v4.20.0: exact historical implementations rebound onto original class.
SessionPartyMixin.clean_party_player_argument = _sb420_bind(_sb420_src_01.clean_party_player_argument, globals(), "SessionPartyMixin")
SessionPartyMixin.auto_priest_heal_option = _sb420_bind(_sb420_src_01.auto_priest_heal_option, globals(), "SessionPartyMixin")
SessionPartyMixin.perform_auto_priest_heal = _sb420_bind(_sb420_src_01.perform_auto_priest_heal, globals(), "SessionPartyMixin")
SessionPartyMixin.begin_downed_v0371 = _sb420_bind(_sb420_src_01.begin_downed_v0371, globals(), "SessionPartyMixin")
SessionPartyMixin.respawn_from_downed_v0371 = _sb420_bind(_sb420_src_01.respawn_from_downed_v0371, globals(), "SessionPartyMixin")
SessionPartyMixin.revive_party_member_v0371 = _sb420_bind(_sb420_src_01.revive_party_member_v0371, globals(), "SessionPartyMixin")
SessionPartyMixin.respawn_downed_player_v11343 = _sb420_bind(_sb420_src_01.respawn_downed_player_v11343, globals(), "SessionPartyMixin")
SessionPartyMixin.create_party = _sb420_bind(_sb420_src_01.create_party, globals(), "SessionPartyMixin")
SessionPartyMixin.transfer_party_leader = _sb420_bind(_sb420_src_01.transfer_party_leader, globals(), "SessionPartyMixin")
SessionPartyMixin.stop_party_protection = _sb420_bind(_sb420_src_01.stop_party_protection, globals(), "SessionPartyMixin")
SessionPartyMixin.protect_party = _sb420_bind(_sb420_src_01.protect_party, globals(), "SessionPartyMixin")
SessionPartyMixin.show_party = _sb420_bind(_sb420_src_02.show_party, globals(), "SessionPartyMixin")
SessionPartyMixin.set_party_goal_v0610 = _sb420_bind(_sb420_src_02.set_party_goal_v0610, globals(), "SessionPartyMixin")
SessionPartyMixin.show_party_ready_v0610 = _sb420_bind(_sb420_src_02.show_party_ready_v0610, globals(), "SessionPartyMixin")
SessionPartyMixin.handle_party_ready_v0610 = _sb420_bind(_sb420_src_02.handle_party_ready_v0610, globals(), "SessionPartyMixin")
SessionPartyMixin.set_party_not_ready_v0610 = _sb420_bind(_sb420_src_02.set_party_not_ready_v0610, globals(), "SessionPartyMixin")
SessionPartyMixin.leave_party = _sb420_bind(_sb420_src_02.leave_party, globals(), "SessionPartyMixin")
SessionPartyMixin.disband_party = _sb420_bind(_sb420_src_02.disband_party, globals(), "SessionPartyMixin")
SessionPartyMixin.party_invite = _sb420_bind(_sb420_src_02.party_invite, globals(), "SessionPartyMixin")
SessionPartyMixin.party_accept = _sb420_bind(_sb420_src_02.party_accept, globals(), "SessionPartyMixin")
SessionPartyMixin.party_kick = _sb420_bind(_sb420_src_02.party_kick, globals(), "SessionPartyMixin")
SessionPartyMixin.assist_party_member = _sb420_bind(_sb420_src_02.assist_party_member, globals(), "SessionPartyMixin")
SessionPartyMixin.handle_party = _sb420_bind(_sb420_src_03.handle_party, globals(), "SessionPartyMixin")

