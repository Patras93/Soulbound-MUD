# -*- coding: utf-8 -*-
"""Soulbound v1.10.0 - Archeologia i Kartografia jako profesje 1-600."""

import asyncio
import random

from core.bootstrap_economy_professions import (
    currency_reading_text,
    profession_for_tool_type,
    profession_max_level,
    tool_tier,
    tool_tier_access_level,
    tool_tier_bonus_chance,
    tool_tier_name,
)
from core.classes_skills import ROOMS
from core.mines_threat import ITEMS
from data import catalog_mutations as _catalog_mut
from core.progression_600 import TOOL_MAX_LEVEL, TOOL_MAX_TIER
from core.progression_resources import v1138_resource_sale_base_coins
from network.protocol_gameplay_utils import normalize_lookup_text
from systems.content_registry import QUESTS


V1100_ARCHAEOLOGY_FINDS = (
    (1, "v1100_relic_001", "Odłamek Starej Ceramiki"),
    (30, "v1100_relic_030", "Brązowa Pieczęć Zapomnianego Domu"),
    (60, "v1100_relic_060", "Kościana Tabliczka Runiczna"),
    (90, "v1100_relic_090", "Srebrny Medalion Dawnego Kultu"),
    (120, "v1100_relic_120", "Fragment Posągu Pierwszego Strażnika"),
    (150, "v1100_relic_150", "Kryształowa Tablica Przysięgi"),
    (180, "v1100_relic_180", "Maska Kapłana Zaginionej Świątyni"),
    (210, "v1100_relic_210", "Złamany Klucz Królewskiej Krypty"),
    (240, "v1100_relic_240", "Astrolabium Starego Imperium"),
    (270, "v1100_relic_270", "Runiczny Dysk Kronikarzy"),
    (300, "v1100_relic_300", "Korona Bezimiennego Władcy"),
    (330, "v1100_relic_330", "Serce Mechanizmu Pradawnego Magiteku"),
    (360, "v1100_relic_360", "Zwój Gwiezdnych Katakumb"),
    (390, "v1100_relic_390", "Obsydianowy Totem Otchłani"),
    (420, "v1100_relic_420", "Pieczęć Przekroczenia"),
    (450, "v1100_relic_450", "Mapa Gwiezdnego Tronu"),
    (480, "v1100_relic_480", "Kryształ Wiecznego Echa"),
    (510, "v1100_relic_510", "Relikwiarz Serca Otchłani"),
    (540, "v1100_relic_540", "Fragment Korony Gwiazd"),
    (570, "v1100_relic_570", "Tablica Apogeum"),
    (600, "v1100_relic_600", "Artefakt Absolutu Duszy"),
)

for _level, _item_id, _name in V1100_ARCHAEOLOGY_FINDS:
    _catalog_mut.catalog_setdefault_path(
        "ITEMS",
        ITEMS,
        (),
        _item_id,
        {
            "name": _name,
            "type": "archaeology_find",
            "price": None,
            "sell_silver": int(round(
                v1138_resource_sale_base_coins(_level)
                * (5.0 if _level < 300 else (15.0 if _level < 500 else 30.0))
            )),
            "rarity": "rare" if _level < 300 else ("legendary" if _level < 500 else "mythic"),
            "rarity_name": "Znalezisko Archeologiczne",
            "archaeology_level": int(_level),
            "desc": f"Znalezisko Archeologii z progu {int(_level)}. Wpisuje się do kolekcji Archeologii.",
        },
    )


_ARCHAEOLOGY_KEYWORDS = (
    "ruin", "ruiny", "krypt", "cmentar", "grob", "grób", "katakumb",
    "swiatyn", "świątyn", "archiw", "staro", "magitek", "palac", "pałac",
    "katedr", "zatop", "grobowiec", "nekropol", "pradawn",
)


class SessionExplorationProfessionsV1100Mixin:
    def v1100_archaeology_site(self):
        if not self.character:
            return False
        room_id = str(self.character.room_id)
        room = ROOMS.get(room_id, {})
        haystack = normalize_lookup_text(
            " ".join(
                (
                    room_id,
                    str(room.get("name", "")),
                    str(room.get("zone", "")),
                    str(room.get("desc", "")),
                )
            )
        )
        if any(keyword in haystack for keyword in _ARCHAEOLOGY_KEYWORDS):
            return True
        return bool(
            room.get("crypt")
            or room.get("dungeon")
            or room.get("ancient")
            or room.get("ruin")
            or room.get("v018_great_ruin")
        )

    async def v1100_profession_quest_progress(self, profession, tool_type):
        changed = self.server.db.increment_profession_action_quests_v0700(
            self.account_id, profession, tool_type, 1
        )
        for quest_id, progress, needed in changed:
            quest = QUESTS.get(quest_id, {})
            await self.send(
                f"Postęp zadania: {quest.get('name', quest_id)} — {progress} z {needed}."
            )
        if hasattr(self, "announce_profession_action_order_progress_v0713"):
            await self.announce_profession_action_order_progress_v0713(tool_type, 1)

    async def excavate_v1100(self, _args=""):
        if self.server.db.item_qty(self.account_id, "archaeology_brush") <= 0:
            await self.send(
                "Nie masz Pędzla Archeologa. Kupisz go u Archeolożki Elary w Bibliotece; "
                "narzędzie kupuje się tylko raz na postać."
            )
            return
        if not self.v1100_archaeology_site():
            await self.send(
                "Tu nie ma stanowiska archeologicznego. Szukaj ruin, krypt, cmentarzy, "
                "świątyń, archiwów, Magiteku i innych pradawnych miejsc."
            )
            return
        ready, remaining = self.profession_ready()
        if not ready:
            await self.send(f"Musisz chwilę odczekać przed kolejnym wykopaliskiem: {remaining:.1f} s.")
            return

        tool = self.server.db.tool(self.account_id, "archaeology")
        tool_level = max(1, int(tool["level"]))
        profession_level = self.profession_level_for_tool("archaeology")
        action_seconds = self.profession_action_seconds("archaeology", profession_level)
        await self.send(
            f"Rozpoczynasz wykopaliska Pędzlem Archeologa. Czas pracy: {action_seconds} sekund."
        )
        await asyncio.sleep(action_seconds)

        access = tool_tier_access_level(tool_level)
        eligible = [row for row in V1100_ARCHAEOLOGY_FINDS if row[0] <= access]
        found_ids = self.server.db.collection_entry_ids(self.account_id, "archaeology_v1100")
        unseen = [row for row in eligible if row[1] not in found_ids]
        if unseen and random.random() < 0.70:
            find = random.choice(unseen)
        else:
            find = random.choice(eligible)

        _required, item_id, name = find
        quantity = 1
        if random.random() < tool_tier_bonus_chance(tool_level):
            quantity += 1
        self.server.db.add_item(self.account_id, item_id, quantity)
        is_new = self.server.db.add_collection_entry(self.account_id, "archaeology_v1100", item_id)

        base_xp = max(30, 50 + access * 2)
        discovery_mult = 2.00 if is_new else 1.00
        messages, *_ = self.grant_profession_progress(
            "Archeologia",
            max(1, int(round(base_xp * discovery_mult))),
            "archaeology",
            max(20, int(round((35 + access) * (1.50 if is_new else 1.00)))),
            content_level=_required,
        )
        self.server.db.add_lifetime_stat(self.account_id, "profession_actions", 1)
        prefix = "NOWE ZNALEZISKO" if is_new else "Znalezisko"
        await self.send(f"{prefix}: {name} x{quantity}.")
        if is_new:
            await self.send(
                "NOWE ODKRYCIE ARCHEOLOGICZNE: podwójny Profession XP i zwiększony Tool XP. "
                "Znalezisko ma także wysoką wartość kolekcjonerską przy sprzedaży."
            )
        await self.announce_profession_action_order_progress_v0713("archaeology", 1)
        for message in messages:
            await self.send(message)

    async def survey_v1100(self, _args=""):
        if self.server.db.item_qty(self.account_id, "surveyor_compass") <= 0:
            await self.send(
                "Nie masz Kompasu Mierniczego. Kupisz go u Mistrzyni Kartografii Aleny "
                "w Archiwum Rubieży; narzędzie kupuje się tylko raz na postać."
            )
            return
        ready, remaining = self.profession_ready()
        if not ready:
            await self.send(f"Musisz chwilę odczekać przed kolejnym pomiarem: {remaining:.1f} s.")
            return

        room_id = str(self.character.room_id)
        room = ROOMS.get(room_id, {})
        tool = self.server.db.tool(self.account_id, "cartography_profession")
        tool_level = max(1, int(tool["level"]))
        profession_level = self.profession_level_for_tool("cartography_profession")
        action_seconds = self.profession_action_seconds("cartography_profession", profession_level)
        await self.send(
            f"Rozstawiasz przyrządy i wykonujesz pomiar Kartograficzny. Czas pracy: {action_seconds} sekund."
        )
        await asyncio.sleep(action_seconds)

        is_new = self.server.db.add_collection_entry(
            self.account_id, "cartography_v1100", room_id
        )
        stage = max(
            1,
            min(
                600,
                int(
                    room.get("recommended_mastery")
                    or room.get("recommended_level")
                    or room.get("level")
                    or 1
                ),
            ),
        )
        access = tool_tier_access_level(tool_level)
        effective = max(1, min(600, max(stage, access // 2)))
        profession_xp = max(25, 40 + effective * (2 if is_new else 1))
        tool_xp = max(20, 30 + effective)

        discovery_reward_silver = 0
        if is_new:
            discovery_reward_silver = max(
                100,
                int(round(v1138_resource_sale_base_coins(effective) * 10.0)),
            )
            self.character.silver += discovery_reward_silver
            self.server.db.save_character(self.character)

        fragment = random.random() < tool_tier_bonus_chance(tool_level)
        if fragment:
            self.server.db.add_item(self.account_id, "v1100_map_fragment", 1)

        messages, *_ = self.grant_profession_progress(
            "Kartografia",
            profession_xp,
            "cartography_profession",
            tool_xp,
            content_level=effective,
        )
        self.server.db.add_lifetime_stat(self.account_id, "profession_actions", 1)
        name = room.get("name", room_id)
        if is_new:
            await self.send(
                f"NOWY POMIAR: {name}. Lokacja została wpisana do Atlasu Kartografa. "
                f"Premia odkrywcy: {currency_reading_text(discovery_reward_silver, 0, 0)}."
            )
        else:
            await self.send(f"Ponawiasz pomiar lokacji: {name}.")
        if fragment:
            await self.send("Bonus narzędzia: Fragment Mapy Rubieży x1.")
        await self.announce_profession_action_order_progress_v0713("cartography_profession", 1)
        for message in messages:
            await self.send(message)

    async def show_archaeology_v1100(self, args=""):
        mode = normalize_lookup_text(args)
        profession = self.server.db.profession(self.account_id, "Archeologia")
        tool = self.server.db.tool(self.account_id, "archaeology")
        found = self.server.db.collection_entry_ids(self.account_id, "archaeology_v1100")
        if mode in ("kolekcja", "collection", "znaleziska", "finds"):
            await self.send(f"KOLEKCJA ARCHEOLOGII: {len(found)} z {len(V1100_ARCHAEOLOGY_FINDS)}.")
            for level, item_id, name in V1100_ARCHAEOLOGY_FINDS:
                if item_id in found:
                    await self.send(f"Poziom {level}: {name}.")
                else:
                    await self.send(f"Poziom {level}: nieodkryte.")
            return
        await self.send(
            f"ARCHEOLOGIA: poziom {profession['level']}/{profession_max_level('Archeologia')}. "
            f"XP: {self.profession_xp_status_text_v11343('Archeologia')}. "
            f"Znaleziska {len(found)}/{len(V1100_ARCHAEOLOGY_FINDS)}."
        )
        await self.show_single_tool("archaeology")
        await self.send("Komendy: wykop; archeologia kolekcja. Narzędzie kupujesz tylko raz na postać.")

    async def show_cartography_profession_v1100(self, args=""):
        mode = normalize_lookup_text(args)
        if mode in ("swiat", "świat", "world", "stara", "old"):
            await self.show_cartography_v024()
            return
        profession = self.server.db.profession(self.account_id, "Kartografia")
        tool = self.server.db.tool(self.account_id, "cartography_profession")
        surveyed = self.server.db.collection_entry_ids(self.account_id, "cartography_v1100")
        total = max(1, len(ROOMS))
        current = str(self.character.room_id)
        status = "zmapowana" if current in surveyed else "niezmapowana"
        await self.send(
            f"KARTOGRAFIA: poziom {profession['level']}/{profession_max_level('Kartografia')}. "
            f"XP: {self.profession_xp_status_text_v11343('Kartografia')}. "
            f"Unikalne zmapowane lokacje: {len(surveyed)} z obecnych {total}."
        )
        await self.show_single_tool("cartography_profession")
        await self.send(
            f"Aktualna lokacja jest {status}. Komenda: mapuj. "
            "Kartografia świat pokazuje starszy system map świata. Narzędzie kupujesz tylko raz na postać."
        )
