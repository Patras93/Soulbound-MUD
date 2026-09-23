# -*- coding: utf-8 -*-
"""Shared progression listener for fishing, mining, woodcutting and herbalism."""
from events.contracts import ResourceGatheredEvent


async def credit_resource_progression(event: ResourceGatheredEvent):
    session = event.session
    qty = max(0, int(event.quantity))
    if qty <= 0:
        return

    await session.announce_resource_quest_progress(event.item_id, qty)
    await session.announce_collect_category_quest_progress(event.category, qty)
    if event.distinct_category and event.distinct_item_id:
        await session.announce_distinct_category_quest_progress(
            event.distinct_category, event.distinct_item_id
        )
    if event.secondary_category:
        await session.announce_collect_category_quest_progress(event.secondary_category, qty)

    await session.advance_bounty(event.bounty_kind, event.item_id, qty)
    await session.advance_legendary_contract_v022(event.legendary_kind, qty)
    await session.advance_dynamic_world_quest_v015(event.dynamic_kind, event.item_id, qty)
    await session.add_faction_reputation_v016(
        event.faction, 1, reason=event.faction_reason
    )
    session.server.db.add_lifetime_stat(session.account_id, event.lifetime_stat, qty)
    session.server.db.add_lifetime_stat(session.account_id, "profession_actions", 1)

    if event.rare_achievement:
        await session.advance_achievement(event.rare_achievement, qty)
    if event.rare_lifetime_stat:
        session.server.db.add_lifetime_stat(session.account_id, event.rare_lifetime_stat, qty)
