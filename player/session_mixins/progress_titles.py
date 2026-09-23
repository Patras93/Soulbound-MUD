# -*- coding: utf-8 -*-
"""Soulbound v0.58.0 - Titles 2.0 and unified progress summary."""
from __future__ import annotations

from config.postal import COURIER_RANKS_V0530, courier_rank_for_reputation_v0530
from core.progression_600 import (
    CHARACTER_MAX_LEVEL,
    CLASS_MASTERY_MAX_LEVEL,
    PROFESSION_MAX_LEVEL,
    SOUL_MAX_LEVEL,
    SOUL_MAX_TIER,
    SOUL_WEAPON_MASTERY_MAX_LEVEL,
)
from core.progression_resources import character_xp_to_next, class_mastery_xp_to_next
from network.protocol_gameplay_utils import normalize_lookup_text
from systems.equipment_crafting import GUILD_REPUTATION_MAX
from world.dynamic_content import ALL_EXPLORATION_ROOMS, COLLECTION_CATALOGS
from world.generation_systems import V016_FACTIONS, v0160_faction_rank


PROFESSIONS_V0580 = (
    "Wędkarstwo", "Górnictwo", "Drwalstwo", "Zielarstwo",
    "Gotowanie", "Alchemia", "Kowalstwo", "Jubilerstwo",
    "Krawiectwo", "Garbarstwo", "Stolarstwo", "Zaklinanie",
)

EXPLORATION_TITLES_V0580 = (
    (10, "Wędrowiec Świata"),
    (25, "Kartograf Rubieży"),
    (50, "Wielki Odkrywca"),
    (75, "Mistrz Horyzontów"),
    (100, "Odkrywca Całego Świata"),
)

BOSS_TITLES_V0580 = (
    (10, "Łowca Bossów"),
    (50, "Pogromca Bossów"),
    (100, "Kat Tytanów"),
    (250, "Postrach Bossów"),
    (500, "Legenda Łowców Bossów"),
    (1000, "Nemezis Bossów"),
)

PROFESSION_TITLE_THRESHOLDS_V0580 = (
    (200, "Mistrz"),
    (400, "Arcymistrz"),
    (600, "Legenda"),
)

PLAYER_GUILD_TITLES_V0580 = (
    (1, "Towarzysz Gildii"),
    (10, "Weteran Gildii"),
    (100, "Filar Gildii"),
    (300, "Arcymistrz Gildii"),
    (600, "Legenda Gildii"),
)

CLASS_GUILD_TITLES_V0580 = (
    (250, "Zaufany Gildii"),
    (700, "Elita Gildii"),
    (1000, "Legenda Gildii"),
)


class SessionProgressTitlesV0580Mixin:
    def _profession_levels_v0580(self):
        rows = self.server.db.conn.execute(
            "SELECT profession,level,xp FROM professions WHERE account_id=?",
            (self.account_id,),
        ).fetchall()
        known = {str(row["profession"]): (max(1, int(row["level"] or 1)), max(0, int(row["xp"] or 0))) for row in rows}
        return {name: known.get(name, (1, 0)) for name in PROFESSIONS_V0580}

    def _world_exploration_v0580(self):
        discovered = self.server.db.discovered_room_ids(self.account_id)
        found = len(discovered.intersection(ALL_EXPLORATION_ROOMS))
        total = max(1, len(ALL_EXPLORATION_ROOMS))
        pct = int(found * 100 / total)
        return found, total, pct

    async def sync_titles_v0580(self, announce=True):
        """Synchronize Titles 2.0 from durable state, including old saves."""
        unlocked = []

        async def grant(title_id, title_name):
            if await self.unlock_title(title_id, title_name, announce=announce):
                unlocked.append(title_name)

        # Exploration titles.
        _found, _total, world_pct = self._world_exploration_v0580()
        for threshold, title in EXPLORATION_TITLES_V0580:
            if world_pct >= threshold:
                await grant(f"titles2:exploration:{threshold}", title)

        # Boss titles use the long-lived kill counter, so old characters catch up.
        boss_kills = max(0, int(self.server.db.lifetime_stat(self.account_id, "boss_kills") or 0))
        for threshold, title in BOSS_TITLES_V0580:
            if boss_kills >= threshold:
                await grant(f"titles2:bosses:{threshold}", title)

        # Profession titles: per profession plus cross-profession milestones.
        profession_levels = self._profession_levels_v0580()
        for profession, (level, _xp) in profession_levels.items():
            for threshold, prefix in PROFESSION_TITLE_THRESHOLDS_V0580:
                if level >= threshold:
                    await grant(
                        f"titles2:profession:{profession}:{threshold}",
                        f"{prefix} — {profession}",
                    )
        masters_200 = sum(1 for level, _xp in profession_levels.values() if level >= 200)
        masters_600 = sum(1 for level, _xp in profession_levels.values() if level >= PROFESSION_MAX_LEVEL)
        if masters_200 >= 4:
            await grant("titles2:profession:versatile", "Wszechstronny Rzemieślnik")
        if masters_200 >= len(PROFESSIONS_V0580):
            await grant("titles2:profession:all200", "Mistrz Wszystkich Rzemiosł")
        if masters_600 >= len(PROFESSIONS_V0580):
            await grant("titles2:profession:all600", "Arcylegenda Profesji")

        # Courier Guild ranks already existed; this makes them retroactive too.
        courier = self.server.db.courier_guild_state_v0530(self.account_id)
        courier_rep = max(1, int(courier.get("reputation", 1) or 1))
        for threshold, title, _bonus in COURIER_RANKS_V0530:
            if courier_rep >= int(threshold):
                await grant(f"courier_guild_v0530:{threshold}", title)

        # Class-guild reputation titles for every class the character has developed.
        class_rows = self.server.db.conn.execute(
            "SELECT class_name FROM class_progress WHERE account_id=? ORDER BY class_name COLLATE NOCASE",
            (self.account_id,),
        ).fetchall()
        class_names = {str(row["class_name"]) for row in class_rows}
        class_names.update(self.active_class_names())
        for class_name in sorted(class_names):
            rep = max(0, min(GUILD_REPUTATION_MAX, int(self.character.guild_reputation(class_name))))
            for threshold, prefix in CLASS_GUILD_TITLES_V0580:
                if rep >= threshold:
                    await grant(
                        f"titles2:classguild:{class_name}:{threshold}",
                        f"{prefix}: {class_name}",
                    )

        # Player-guild titles are based on the persistent guild level and role.
        membership = self.server.db.clan_membership(self.account_id)
        if membership:
            guild_level = max(1, int(membership["level"] or 1))
            for threshold, title in PLAYER_GUILD_TITLES_V0580:
                if guild_level >= threshold:
                    await grant(f"titles2:playerguild:{threshold}", title)
            if str(membership["rank"] or "").casefold() == "leader" or int(membership["owner_account_id"] or 0) == int(self.account_id):
                await grant("titles2:playerguild:leader", "Lider Gildii")

        # Cross-faction prestige titles complement the existing faction-specific titles.
        faction_reps = self.server.db.faction_reputations_v016(self.account_id)
        if V016_FACTIONS and all(int(faction_reps.get(fid, 0)) >= 150 for fid in V016_FACTIONS):
            await grant("titles2:factions:all150", "Ambasador Pięciu Frakcji")
        if V016_FACTIONS and all(int(faction_reps.get(fid, 0)) >= 300 for fid in V016_FACTIONS):
            await grant("titles2:factions:all300", "Legenda Pięciu Frakcji")

        return unlocked

    async def show_unified_progress_v0580(self):
        # Keep all retroactive achievements/titles current before rendering the summary.
        await self.sync_extended_achievements()
        await self.sync_titles_v0580(announce=True)

        c = self.character
        await self.send("POSTĘP — PODSUMOWANIE")

        # Character Level.
        if int(c.character_level) >= CHARACTER_MAX_LEVEL:
            await self.send(f"Level postaci: {c.character_level}/{CHARACTER_MAX_LEVEL}, maksimum.")
        else:
            need = character_xp_to_next(int(c.character_level))
            missing = max(0, int(need) - int(c.character_xp))
            await self.send(
                f"Level postaci: {c.character_level}/{CHARACTER_MAX_LEVEL}. EXP {c.character_xp} z {need}; brakuje {missing}."
            )

        # Class mastery.
        mastery_parts = []
        for class_name in self.active_class_names():
            row = self.server.db.class_progress_row(self.account_id, class_name)
            level = int(row["level"] or 1)
            xp = int(row["xp"] or 0)
            if level >= CLASS_MASTERY_MAX_LEVEL:
                mastery_parts.append(f"{class_name} {level}/{CLASS_MASTERY_MAX_LEVEL} max")
            else:
                need = class_mastery_xp_to_next(level)
                mastery_parts.append(f"{class_name} {level}/{CLASS_MASTERY_MAX_LEVEL}, XP {xp}/{need}")
        await self.send("Biegłość: " + ("; ".join(mastery_parts) if mastery_parts else "brak aktywnej klasy") + ".")

        # Soul and Soul Weapon Mastery.
        if int(c.soul_level) >= SOUL_MAX_LEVEL:
            soul_xp = "maksimum"
        elif c.soul_progress_is_tier_locked():
            soul_xp = "Soul XP zablokowany do odblokowania następnego Tieru"
        else:
            soul_xp = f"Soul XP {c.soul_xp}/{c.soul_xp_to_next()}"
        await self.send(
            f"Dusza: Soul Level {c.soul_level}/{SOUL_MAX_LEVEL}; Tier {c.soul_tier}/{SOUL_MAX_TIER}; {soul_xp}."
        )
        if int(c.soul_weapon_mastery_level) >= SOUL_WEAPON_MASTERY_MAX_LEVEL:
            swm = "maksimum"
        else:
            swm = f"XP {c.soul_weapon_mastery_xp}/{c.soul_weapon_mastery_xp_to_next()}"
        await self.send(
            f"Soul Weapon Mastery: {c.soul_weapon_mastery_level}/{SOUL_WEAPON_MASTERY_MAX_LEVEL}; {swm}."
        )

        # Professions in three compact NVDA-friendly lines.
        profession_levels = self._profession_levels_v0580()
        profession_parts = [f"{name} {level}/{PROFESSION_MAX_LEVEL}" for name, (level, _xp) in profession_levels.items()]
        for start in range(0, len(profession_parts), 4):
            label = "Profesje" if start == 0 else "Profesje ciąg dalszy"
            await self.send(f"{label}: " + "; ".join(profession_parts[start:start + 4]) + ".")

        # Reputations: Courier, factions, class guilds and player guild.
        courier = self.server.db.courier_guild_state_v0530(self.account_id)
        courier_rep = max(1, int(courier.get("reputation", 1) or 1))
        courier_rank = courier_rank_for_reputation_v0530(courier_rep)["name"]
        await self.send(f"Reputacja Kurierów: {courier_rep}/400, ranga {courier_rank}.")

        faction_reps = self.server.db.faction_reputations_v016(self.account_id)
        faction_parts = []
        for fid, data in V016_FACTIONS.items():
            rep = int(faction_reps.get(fid, 0) or 0)
            faction_parts.append(f"{data['name']} {rep}, {v0160_faction_rank(rep)}")
        await self.send("Frakcje: " + ("; ".join(faction_parts) if faction_parts else "brak") + ".")

        guild_rep_parts = []
        for class_name in self.active_class_names():
            rep = max(0, int(c.guild_reputation(class_name)))
            guild_rep_parts.append(f"{class_name} {rep}/{GUILD_REPUTATION_MAX}, {c.guild_rep_rank(class_name)[1]}")
        await self.send("Reputacja gildii klasowych: " + ("; ".join(guild_rep_parts) if guild_rep_parts else "brak") + ".")

        membership = self.server.db.clan_membership(self.account_id)
        if membership:
            await self.send(
                f"Gildia gracza: {membership['name']}; poziom {int(membership['level'])}; ranga {membership['rank']}."
            )
        else:
            await self.send("Gildia gracza: brak.")

        # Achievements/titles and exploration.
        achievement_count = len(self.server.db.achievement_rows(self.account_id))
        title_count = len(self.server.db.title_rows(self.account_id))
        await self.send(
            f"Osiągnięcia: {achievement_count}. Tytuły: {title_count}. Aktywny tytuł: {c.active_title or 'brak'}."
        )
        found, total, pct = self._world_exploration_v0580()
        await self.send(f"Eksploracja świata: {found} z {total} lokacji, {pct}%.")

        # Preserve the old collection/museum snapshot in the unified command.
        await self.sync_collection_from_inventory()
        discovered_total = sum(
            len(self.server.db.collection_entry_ids(self.account_id, category))
            for category in COLLECTION_CATALOGS
        )
        catalog_total = sum(len(catalog) for catalog in COLLECTION_CATALOGS.values())
        collection_pct = int(discovered_total * 100 / max(1, catalog_total))
        await self.v0260_sync_museum()
        _mrows, mfound, mtotal, mpct, mprestige = self.v0260_museum_snapshot()
        await self.send(
            f"Kolekcje: {discovered_total}/{catalog_total}, {collection_pct}%. Muzeum: {mfound}/{mtotal}, {mpct}%, prestiż {mprestige}/1000."
        )


__all__ = [
    "SessionProgressTitlesV0580Mixin",
    "PROFESSIONS_V0580",
    "EXPLORATION_TITLES_V0580",
    "BOSS_TITLES_V0580",
]
