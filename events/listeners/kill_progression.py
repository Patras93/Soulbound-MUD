# -*- coding: utf-8 -*-
"""Kill-derived quest, bounty, contract, faction and collection progression."""
from events.contracts import PlayerMobKillProgressionEvent, PlayerMobKillQuestEvent


async def credit_primary_kill_quest(event: PlayerMobKillQuestEvent):
    await event.session.record_mob_progress(event.mob)


async def credit_extended_kill_progression(event: PlayerMobKillProgressionEvent):
    session = event.session
    await session.advance_bounty("kill", event.bestiary_id, 1)
    await session.advance_legendary_contract_v022("kill", 1)
    if event.is_boss:
        await session.advance_legendary_contract_v022("boss", 1)
    if event.is_world_boss:
        await session.advance_legendary_contract_v022("worldboss", 1)
    await session.advance_dynamic_world_quest_v015("kill", event.bestiary_id, 1)

    if event.is_legendary_rare:
        await session.advance_v0140_quest_progress("legendary_rare", event.biome, 1)
        await session.add_faction_reputation_v016("frontier_watch", 15, reason="legendary_rare")
        session.server.db.add_collection_entry(
            session.account_id, "legendary_rares_v016", event.bestiary_id
        )
    if event.is_v016_world_boss:
        await session.advance_v0140_quest_progress("world_boss", event.biome, 1)
        await session.add_faction_reputation_v016("frontier_watch", 40, reason="world_boss")
        session.server.db.add_collection_entry(
            session.account_id, "world_bosses_v016", event.bestiary_id
        )
    if event.is_great_ruin_guardian:
        session.server.db.add_collection_entry(
            session.account_id, "great_ruin_guardians_v018", event.bestiary_id
        )
        await session.add_faction_reputation_v016("cartographers", 20, reason="great_ruin")
    if event.is_legendary_event_boss:
        session.server.db.add_collection_entry(
            session.account_id, "legendary_event_bosses_v018", event.bestiary_id
        )
        await session.add_faction_reputation_v016("frontier_watch", 50, reason="legendary_event")
