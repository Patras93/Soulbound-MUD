# -*- coding: utf-8 -*-
"""Party sharing helper for courier package acceptance."""

from player.session_mixins.shops_teachers import currency_reading_text


async def share_courier_package_with_party_v10019(session, offer, city):
    """Copy the leader's accepted courier package to local eligible party members."""
    party_key = session.server.party_key_for_account(session.account_id)
    if party_key is None or int(party_key) != int(session.account_id):
        return

    recipients = [
        member
        for member in session.server.party_sessions(
            session.account_id, same_room=session.character.room_id
        )
        if member is not session
        and member.character
        and not member.closed
        and int(getattr(member, "current_hp", 0) or 0) > 0
    ]
    accepted_names = []
    skipped_names = []

    for member in sorted(
        recipients, key=lambda item: item.character.name.lower()
    ):
        member_state = member.server.db.postal_delivery_state_v0522(
            member.account_id
        )
        if member_state.get("active"):
            skipped_names.append(member.character.name)
            await member.send(
                f"Lider {session.character.name} odbiera dla drużyny paczkę "
                f"{offer['package_name']}, ale masz już aktywną paczkę."
            )
            continue

        member_offer = dict(offer)
        member.server.db.record_courier_city_visit_v0530(
            member.account_id, city
        )
        member.server.db.save_postal_delivery_state_v0522(
            member.account_id, active=member_offer
        )
        await member.courier_sync_achievements_v0540(announce=True)
        accepted_names.append(member.character.name)
        await member.send(
            f"Lider {session.character.name} odbiera dla drużyny: "
            f"{member_offer['package_name']}. "
            f"Cel: {member_offer['destination_city']}. "
            f"Nagroda: {currency_reading_text(member_offer['reward_coins'],0,0)}. "
            f"Możesz wpisać prowadz {member.postal_guide_query_v0522(member_offer)}."
        )

    if accepted_names:
        await session.send(
            "Paczkę otrzymała razem z tobą drużyna: "
            + ", ".join(accepted_names)
            + "."
        )
    if skipped_names:
        await session.send(
            "Nie wszyscy mogli otrzymać paczkę. Pominięto: "
            + ", ".join(skipped_names)
            + "."
        )


__all__ = ["share_courier_package_with_party_v10019"]
