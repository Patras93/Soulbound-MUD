# -*- coding: utf-8 -*-
"""Rotating NPC crafting orders introduced in Soulbound v0.60.0."""

import hashlib
import time

from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL, currency_reading_text
from core.progression_resources import v0190_quest_currency_reward
from network.protocol_gameplay_utils import normalize_lookup_text
from systems.content_registry import NPCS
from systems.equipment_crafting import ALCHEMY_RECIPES, COOK_RECIPES, CRAFT_RECIPES, JEWELCRAFT_RECIPES
from systems.professions import V03053_CRAFT_RECIPES
from core.mines_threat import ITEMS


CRAFTING_ORDER_REFRESH_SECONDS_V0600 = 3600

# Product-producing specialists only. Gathering professions keep their own quests.
CRAFTING_ORDER_NPCS_V0600 = {
    "specialist_crafting": {"profession": "Kowalstwo", "tool_type": "crafting", "source": "craft"},
    "specialist_cooking": {"profession": "Gotowanie", "tool_type": "cooking", "source": "cook"},
    "specialist_alchemy": {"profession": "Alchemia", "tool_type": "alchemy", "source": "alchemy"},
    "jeweler_mirella": {"profession": "Jubilerstwo", "tool_type": "jewelcrafting", "source": "jewel"},
    "tailor_lysa": {"profession": "Krawiectwo", "tool_type": "tailoring", "source": "extended"},
    "leatherworker_soren": {"profession": "Garbarstwo", "tool_type": "leatherworking", "source": "extended"},
    "carpenter_edric": {"profession": "Stolarstwo", "tool_type": "carpentry", "source": "extended"},
}


def _stable_index_v0600(seed: str, size: int) -> int:
    if size <= 0:
        return 0
    digest = hashlib.sha256(seed.encode("utf-8", errors="ignore")).digest()
    return int.from_bytes(digest[:8], "big") % size


class SessionCraftingOrdersV0600Mixin:
    def crafting_order_cycle_v0600(self):
        return int(time.time()) // CRAFTING_ORDER_REFRESH_SECONDS_V0600

    def crafting_order_npc_here_v0600(self):
        room_id = str(self.character.room_id)
        matches = []
        for npc_id, spec in CRAFTING_ORDER_NPCS_V0600.items():
            npc = NPCS.get(npc_id, {})
            if str(npc.get("room") or "") == room_id:
                matches.append((npc_id, npc, spec))
        return matches[0] if matches else None

    def crafting_order_recipe_rows_v0600(self, npc_id):
        spec = CRAFTING_ORDER_NPCS_V0600.get(npc_id)
        if not spec:
            return []
        profession = spec["profession"]
        prow = self.server.db.profession(self.account_id, profession)
        level = max(1, int(prow["level"] if prow else 1))
        source = spec["source"]
        if source == "cook":
            tables = (COOK_RECIPES,)
        elif source == "alchemy":
            tables = (ALCHEMY_RECIPES,)
        elif source == "jewel":
            tables = (JEWELCRAFT_RECIPES,)
        elif source == "extended":
            tables = (V03053_CRAFT_RECIPES,)
        else:
            tables = (CRAFT_RECIPES,)

        rows = []
        seen_outputs = set()
        room_id = str(NPCS.get(npc_id, {}).get("room") or "")
        for table in tables:
            for recipe_id, recipe in table.items():
                if not isinstance(recipe, dict):
                    continue
                if source == "extended" and str(recipe.get("profession") or "") != profession:
                    continue
                if source == "craft":
                    rprof = str(recipe.get("profession") or "")
                    rtool = str(recipe.get("tool_type") or "")
                    if rprof != "Kowalstwo" and rtool != "crafting":
                        continue
                    category = str(recipe.get("category") or "").lower()
                    if any(token in category for token in ("salvage", "tech", "refine")):
                        continue
                required = max(1, int(recipe.get("min_profession_level", recipe.get("min_tool_level", 1)) or 1))
                if required > level:
                    continue
                stations = tuple(map(str, recipe.get("stations") or ()))
                if stations and room_id and room_id not in stations:
                    continue
                output = str(recipe.get("output") or "")
                if not output or output not in ITEMS or output in seen_outputs:
                    continue
                item = ITEMS[output]
                if item.get("type") in ("quest", "tool"):
                    continue
                seen_outputs.add(output)
                rows.append((str(recipe_id), recipe, output, item, required))
        rows.sort(key=lambda row: (row[4], normalize_lookup_text(row[3].get("name", "")), row[0]))
        return rows

    def crafting_order_quantity_v0600(self, item, recipe, cycle, npc_id, offer_no):
        item_type = str(item.get("type") or "")
        if item_type == "armor":
            choices = (1, 2, 3)
        elif item_type in ("consumable", "food", "potion") or "heal" in item or "mana" in item:
            choices = (5, 10, 20)
        else:
            choices = (5, 10, 20)
        idx = _stable_index_v0600(f"qty:{self.account_id}:{cycle}:{npc_id}:{offer_no}:{item.get('name','')}", len(choices))
        return int(choices[idx])

    def crafting_order_reward_v0600(self, recipe, needed):
        level = max(1, int(recipe.get("min_profession_level", recipe.get("min_tool_level", 1)) or 1))
        pseudo = {"min_profession_level": level, "needed": int(needed), "repeatable": True}
        coins = max(50, int(v0190_quest_currency_reward(pseudo)))
        prof_xp = max(25, int(recipe.get("profession_xp", max(20, level * 3)) or 0) * max(1, int(needed)) // 2)
        tool_xp = max(15, int(recipe.get("tool_xp", max(15, level * 2)) or 0) * max(1, int(needed)) // 3)
        return coins, prof_xp, tool_xp

    def crafting_order_offers_v0600(self, npc_id):
        cycle = self.crafting_order_cycle_v0600()
        rows = self.crafting_order_recipe_rows_v0600(npc_id)
        if not rows:
            return []
        offers = []
        used = set()
        for offer_no in range(1, min(3, len(rows)) + 1):
            idx = _stable_index_v0600(f"order:{self.account_id}:{cycle}:{npc_id}:{offer_no}", len(rows))
            for shift in range(len(rows)):
                row = rows[(idx + shift) % len(rows)]
                if row[2] not in used:
                    break
            recipe_id, recipe, output, item, required = row
            used.add(output)
            needed = self.crafting_order_quantity_v0600(item, recipe, cycle, npc_id, offer_no)
            coins, prof_xp, tool_xp = self.crafting_order_reward_v0600(recipe, needed)
            spec = CRAFTING_ORDER_NPCS_V0600[npc_id]
            offers.append({
                "number": offer_no,
                "order_key": f"{cycle}:{npc_id}:{offer_no}:{recipe_id}:{needed}",
                "cycle": cycle,
                "npc_id": npc_id,
                "profession": spec["profession"],
                "tool_type": spec["tool_type"],
                "recipe_id": recipe_id,
                "item_id": output,
                "item_name": str(item.get("name") or output),
                "needed": needed,
                "required_level": required,
                "reward_coins": coins,
                "reward_profession_xp": prof_xp,
                "reward_tool_xp": tool_xp,
            })
        return offers

    async def announce_crafting_order_progress_v0600(self, item_id, amount=1):
        changed = self.server.db.increment_crafting_order_v0600(self.account_id, item_id, amount)
        if not changed:
            return
        progress, needed, item_name = changed
        if progress >= needed:
            await self.send(
                f"Zamówienie rzemieślnicze: {item_name}. Postęp {progress} z {needed}. "
                "GOTOWE DO ODDANIA u NPC, który zlecił zamówienie.",
                combat_detail="essential",
            )
        else:
            await self.send(
                f"Zamówienie rzemieślnicze: {item_name}. Postęp {progress} z {needed}.",
                combat_detail="essential",
            )

    async def handle_crafting_orders_v0600(self, args=""):
        raw = str(args or "").strip()
        words = raw.split()
        mode = normalize_lookup_text(words[0]) if words else "lista"
        active = self.server.db.crafting_order_v0600(self.account_id)

        if mode in ("status", "stan"):
            if not active or not str(active["item_id"] or ""):
                await self.send("Nie masz aktywnego zamówienia rzemieślniczego.")
                return
            npc_name = NPCS.get(str(active["npc_id"]), {}).get("name", str(active["npc_id"]))
            await self.send(
                f"AKTYWNE ZAMÓWIENIE: {active['item_name']}. Postęp {int(active['progress'])} z {int(active['needed'])}. "
                f"Profesja: {active['profession']}. Zleceniodawca: {npc_name}. "
                f"Nagroda: {currency_reading_text(int(active['reward_coins']),0,0)}, "
                f"{int(active['reward_profession_xp'])} XP profesji i {int(active['reward_tool_xp'])} XP narzędzia."
            )
            return

        if mode in ("porzuc", "porzuć", "abandon"):
            if not active or not str(active["item_id"] or ""):
                await self.send("Nie masz aktywnego zamówienia rzemieślniczego.")
                return
            self.server.db.abandon_crafting_order_v0600(self.account_id)
            await self.send("Porzucasz aktywne zamówienie rzemieślnicze. Wykonany postęp przepada.")
            return

        if mode in ("oddaj", "deliver", "turnin"):
            if not active or not str(active["item_id"] or ""):
                await self.send("Nie masz aktywnego zamówienia rzemieślniczego.")
                return
            here = self.crafting_order_npc_here_v0600()
            if not here or here[0] != str(active["npc_id"]):
                npc = NPCS.get(str(active["npc_id"]), {})
                room = str(npc.get("room") or "")
                await self.send(f"To zamówienie oddasz u {npc.get('name', active['npc_id'])}. Lokacja: {room}.")
                return
            needed = int(active["needed"])
            progress = int(active["progress"])
            if progress < needed:
                await self.send(f"Zamówienie nie jest gotowe. Postęp {progress} z {needed}; brakuje {needed-progress}.")
                return
            have = int(self.quest_crafted_item_have_v0333(str(active["item_id"])))
            if have < needed:
                await self.send(f"Masz tylko {have} z {needed} wymaganych sztuk. Produkty muszą być nadal przy tobie lub w magazynie profesji.")
                return
            if not self.consume_quest_crafted_items_v0333(str(active["item_id"]), needed):
                await self.send("Nie udało się pobrać produktów do zamówienia. Sprawdź ekwipunek i magazyn profesji.")
                return
            coins = int(active["reward_coins"])
            self.character.silver = min(CURRENCY_SQLITE_SAFE_TOTAL, int(self.character.silver) + coins)
            await self.grant_profession_reward_xp(
                str(active["profession"]), int(active["reward_profession_xp"]),
                str(active["tool_type"]), int(active["reward_tool_xp"]),
            )
            self.server.db.finish_crafting_order_v0600(self.account_id, int(active["cycle_slot"]))
            self.server.db.add_lifetime_stat(self.account_id, "crafting_orders_completed", 1)
            self.server.db.save_character(self.character)
            try:
                self.server.db.record_activity_v0560(
                    self.account_id, "quest", "Zamówienie rzemieślnicze",
                    f"{active['item_name']} x{needed}; {active['profession']}.",
                )
            except Exception:
                pass
            await self.send(
                f"ZAMÓWIENIE WYKONANE: {active['item_name']} x{needed}. "
                f"Nagroda {currency_reading_text(coins,0,0)}, {int(active['reward_profession_xp'])} XP profesji "
                f"i {int(active['reward_tool_xp'])} XP narzędzia. Zamówienia nie dają Soul XP."
            )
            return

        if mode in ("wez", "weź", "accept", "przyjmij"):
            if active and str(active["item_id"] or ""):
                await self.send("Masz już aktywne zamówienie. Wpisz zamowienia status albo zamowienia porzuc.")
                return
            here = self.crafting_order_npc_here_v0600()
            if not here:
                await self.send("W tej lokacji nie ma NPC obsługującego rotujące zamówienia rzemieślnicze.")
                return
            if len(words) < 2 or not words[1].isdigit():
                await self.send("Użycie: zamowienia wez <numer>, na przykład zamowienia wez 2.")
                return
            offers = self.crafting_order_offers_v0600(here[0])
            number = int(words[1])
            if number < 1 or number > len(offers):
                await self.send(f"Nie ma oferty {number}. Dostępny zakres: 1-{len(offers)}.")
                return
            offer = offers[number-1]
            state = self.server.db.crafting_order_v0600(self.account_id)
            if state and int(state["completed_cycle_slot"] or -1) == int(offer["cycle"]):
                await self.send("W tym cyklu godzinowym ukończyłeś już zamówienie. Nowe oferty pojawią się po odświeżeniu.")
                return
            self.server.db.start_crafting_order_v0600(self.account_id, offer)
            await self.send(
                f"Przyjmujesz zamówienie: {offer['item_name']} x{offer['needed']}. Start 0 z {offer['needed']}. "
                f"Nagroda: {currency_reading_text(offer['reward_coins'],0,0)}, {offer['reward_profession_xp']} XP profesji "
                f"i {offer['reward_tool_xp']} XP narzędzia. Liczą się wyłącznie sztuki wykonane po przyjęciu."
            )
            return

        # Default: list offers at the local specialist.
        here = self.crafting_order_npc_here_v0600()
        if not here:
            names = []
            for npc_id in CRAFTING_ORDER_NPCS_V0600:
                npc = NPCS.get(npc_id, {})
                if npc:
                    names.append(f"{npc.get('name', npc_id)} — {npc.get('room','?')}")
            await self.send("Rotujące zamówienia rzemieślnicze odbierzesz u specjalistów: " + "; ".join(names) + ".")
            return
        npc_id, npc, spec = here
        offers = self.crafting_order_offers_v0600(npc_id)
        await self.send(
            f"ZAMÓWIENIA RZEMIEŚLNICZE — {npc.get('name', npc_id)}. Profesja: {spec['profession']}. "
            "Oferty zmieniają się co 60 minut; na jeden cykl można ukończyć jedno zamówienie."
        )
        if active and str(active["item_id"] or ""):
            await self.send(
                f"Masz aktywne: {active['item_name']} x{int(active['needed'])}; postęp {int(active['progress'])}/{int(active['needed'])}."
            )
        for offer in offers:
            await self.send(
                f"{offer['number']}. {offer['item_name']} x{offer['needed']}. Wymaga {spec['profession']} {offer['required_level']}. "
                f"Nagroda {currency_reading_text(offer['reward_coins'],0,0)}, {offer['reward_profession_xp']} XP profesji, "
                f"{offer['reward_tool_xp']} XP narzędzia."
            )
        await self.send("Przyjęcie: zamowienia wez <numer>. Stan: zamowienia status. Oddanie: zamowienia oddaj.")
