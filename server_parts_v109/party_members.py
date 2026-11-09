# -*- coding: utf-8 -*-
"""v109: wydzielone metody serwera — party_members; bez zmiany zachowania."""
class MudPartyMembersV109Mixin:
    def party_key_for_account(self, account_id):
        for leader_id, members in self.parties.items():
            if account_id in members:
                return leader_id
        return None

    def same_party(self, account_a, account_b):
        key_a = self.party_key_for_account(account_a)
        key_b = self.party_key_for_account(account_b)
        return key_a is not None and key_a == key_b

    def clear_party_protector_for_account(self, account_id):
        removed = False
        for leader_id, protector_id in list(self.party_protectors.items()):
            if protector_id == account_id:
                self.party_protectors.pop(leader_id, None)
                removed = True
        return removed

    def party_protector_session(self, account_id, same_room=None):
        key = self.party_key_for_account(account_id)
        if key is None:
            return None
        protector_id = self.party_protectors.get(key)
        if protector_id is None:
            return None
        if protector_id not in self.parties.get(key, set()):
            self.party_protectors.pop(key, None)
            return None
        protector = self.session_by_account(protector_id)
        if (
            not protector
            or not protector.character
            or protector.closed
            or protector.current_hp <= 0
            or not protector.character.has_active_class("Strażnik")
        ):
            self.party_protectors.pop(key, None)
            return None
        if (
            same_room is not None
            and protector.character.room_id != same_room
        ):
            return None
        return protector

    def party_sessions(self, account_id, same_room=None):
        key = self.party_key_for_account(account_id)
        if key is None:
            session = self.session_by_account(account_id)
            if (
                session
                and (
                    same_room is None
                    or session.character.room_id == same_room
                )
            ):
                return [session]
            return []

        result = []
        for member_id in self.parties.get(key, set()):
            session = self.session_by_account(member_id)
            if not session:
                continue
            if (
                same_room is not None
                and session.character.room_id != same_room
            ):
                continue
            result.append(session)
        return result

    def party_engaged_mobs(self, session, room_id=None):
        """Żywe moby będące wspólnymi celami lokalnej drużyny.

        Cel nie jest zapisywany osobno: wynika z realnego engaged_by któregoś
        członka tej samej drużyny w tym samym pokoju. Dzięki temu każdy mob
        zaatakowany przez członka party natychmiast staje się legalnym celem
        dla pozostałych członków party, bez zombie-targetów po wyjściu.
        """
        if not session or not session.character:
            return []
        rid = session.character.room_id if room_id is None else room_id
        members = self.party_sessions(session.account_id, same_room=rid)
        if not members:
            return []
        member_names = {
            m.character.name for m in members
            if m.character and not m.closed and m.current_hp > 0
        }
        if not member_names:
            return []
        result = []
        for mob in self.world.room_mobs(rid):
            if not mob.alive:
                continue
            self.sanitize_mob_engagement(mob)
            if mob.engaged_by in member_names:
                result.append(mob)
        return result

    def party_combat_targets(self, owner_session, mob):
        """All living local party members are targets of one mob action.

        A Guardian protector remains a special case: while protection is active,
        the protector takes the party-facing attack. Otherwise every living party
        member in the room is attacked once by that mob action.
        """
        if not owner_session or not mob or not mob.alive:
            return [owner_session] if owner_session else []
        protector = self.party_protector_session(
            owner_session.account_id, same_room=mob.room_id
        )
        if protector and protector.current_hp > 0:
            return [protector]
        candidates = [
            session for session in self.party_sessions(
                owner_session.account_id, same_room=mob.room_id
            )
            if session.character and not session.closed and session.current_hp > 0
        ]
        return sorted(candidates or [owner_session], key=lambda session: session.character.name.lower())

    def party_combat_target(self, owner_session, mob):
        # Compatibility for callers that still need one target.
        targets=self.party_combat_targets(owner_session,mob)
        return targets[0] if targets else owner_session
