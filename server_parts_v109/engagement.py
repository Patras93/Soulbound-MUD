# -*- coding: utf-8 -*-
"""v109: wydzielone metody serwera — engagement; bez zmiany zachowania."""
class MudEngagementV109Mixin:
    def sanitize_mob_engagement(self, mob):
        """Usuń zombie-aggro, jeśli deklarowany właściciel już realnie nie walczy."""
        if not mob or not mob.alive or not mob.engaged_by:
            return None

        owner = self.find_character_session(mob.engaged_by)
        aoe_owner = getattr(mob, "aoe_engaged_by", None)
        if (
            owner
            and owner.character
            and owner.current_hp > 0
            and owner.character.room_id == mob.room_id
            and (
                owner.combat_mob_key == mob.key
                or aoe_owner == mob.engaged_by
            )
        ):
            return owner

        # Jeśli stary właściciel zniknął, ale ktoś naprawdę nadal walczy z tym
        # mobem w tym samym pokoju, przekaż aggro aktywnemu uczestnikowi.
        candidates = [
            s for s in self.sessions
            if (
                not s.closed
                and s.character
                and s.current_hp > 0
                and s.character.room_id == mob.room_id
                and s.combat_mob_key == mob.key
            )
        ]
        if candidates:
            replacement = sorted(
                candidates, key=lambda s: s.character.name.lower()
            )[0]
            mob.engaged_by = replacement.character.name
            mob.aoe_engaged_by = None
            return replacement

        # Nikt realnie nie walczy: stan aggro był osierocony.
        mob.engaged_by = None
        mob.aoe_engaged_by = None
        mob.engaged_at = 0.0
        mob.combat_turn = 0
        mob.player_hits = 0
        self.reset_adaptive_mob_encounter_v11330(mob)
        return None

    def release_all_engagements_for_session(self, leaving_session):
        """Zwolnij wszystkie moby trzymane przez postać, nie tylko combat_mob_key."""
        if not leaving_session or not leaving_session.character:
            return 0
        released = 0
        name = leaving_session.character.name
        for mob in self.world.mobs.values():
            if not mob.alive or mob.engaged_by != name:
                continue
            self.reassign_mob_engagement(mob, leaving_session)
            if mob.engaged_by == name:
                mob.engaged_by = None
                mob.aoe_engaged_by = None
                mob.engaged_at = 0.0
                mob.combat_turn = 0
                mob.player_hits = 0
                self.reset_adaptive_mob_encounter_v11330(mob)
            released += 1
        return released

    def engagement_allowed(self, session, mob):
        if not mob or not mob.alive:
            return False
        self.sanitize_mob_engagement(mob)
        if not mob.engaged_by or mob.engaged_by == session.character.name:
            return True
        owner = self.find_character_session(mob.engaged_by)
        return bool(
            owner
            and self.same_party(session.account_id, owner.account_id)
        )

    def reassign_mob_engagement(self, mob, leaving_session):
        if not mob or not mob.alive:
            return
        if mob.engaged_by != leaving_session.character.name:
            return
        candidates = [
            session
            for session in self.party_sessions(
                leaving_session.account_id, same_room=mob.room_id
            )
            if (
                session is not leaving_session
                and session.combat_mob_key == mob.key
            )
        ]
        mob.engaged_by = (
            candidates[0].character.name if candidates else None
        )
        # Przekazanie zwykłego aggro kończy specjalne wielo-aggro AoE.
        mob.aoe_engaged_by = None

    def session_engaged_mobs(self, session, room_id=None):
        """Żywe moby, których aggro należy dokładnie do tej sesji.

        Obejmuje zarówno zwykły główny cel, jak i dodatkowe moby trafione AoE.
        """
        if not session or not session.character:
            return []
        rid = session.character.room_id if room_id is None else room_id
        owner_name = session.character.name
        result = []
        for mob in self.world.room_mobs(rid):
            if not mob.alive:
                continue
            self.sanitize_mob_engagement(mob)
            if mob.engaged_by == owner_name:
                result.append(mob)
        return result
