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
# v0.61.3: orders accepted before this hotfix may have had their products
# consumed by the broken turn-in path before the reward_tool_type crash.
CRAFTING_ORDER_BROKEN_TURNIN_CUTOFF_V0613 = 1790294400

# v0.71.3: all 12 professions have rotating orders. Product professions use
# real recipes, gathering professions request fresh category gathers, and
# Enchanting counts successful enchanting actions.
CRAFTING_ORDER_NPCS_V0600 = {
    "specialist_fishing": {"profession": "Wędkarstwo", "tool_type": "fishing", "source": "gather", "gather_category": "fish", "gather_label": "ryb"},
    "specialist_mining": {"profession": "Górnictwo", "tool_type": "mining", "source": "gather", "gather_category": "ore", "gather_label": "rud"},
    "specialist_woodcutting": {"profession": "Drwalstwo", "tool_type": "woodcutting", "source": "gather", "gather_category": "wood", "gather_label": "sztuk drewna"},
    "specialist_crafting": {"profession": "Kowalstwo", "tool_type": "crafting", "source": "craft"},
    "specialist_cooking": {"profession": "Gotowanie", "tool_type": "cooking", "source": "cook"},
    "specialist_herbalism": {"profession": "Zielarstwo", "tool_type": "herbalism", "source": "gather", "gather_category": "herb", "gather_label": "ziół"},
    "specialist_alchemy": {"profession": "Alchemia", "tool_type": "alchemy", "source": "alchemy"},
    "jeweler_mirella": {"profession": "Jubilerstwo", "tool_type": "jewelcrafting", "source": "jewel"},
    "tailor_lysa": {"profession": "Krawiectwo", "tool_type": "tailoring", "source": "extended"},
    "leatherworker_soren": {"profession": "Garbarstwo", "tool_type": "leatherworking", "source": "extended"},
    "carpenter_edric": {"profession": "Stolarstwo", "tool_type": "carpentry", "source": "extended"},
    "guild_quartermaster_arcane": {"profession": "Zaklinanie", "tool_type": "enchanting", "source": "action", "action_type": "enchanting"},
}


def _stable_index_v0600(seed: str, size: int) -> int:
    if size <= 0:
        return 0
    digest = hashlib.sha256(seed.encode("utf-8", errors="ignore")).digest()
    return int.from_bytes(digest[:8], "big") % size


class SessionCraftingOrdersV0600Mixin:
    def crafting_order_cycle_v0600(self):
        return int(time.time()) // CRAFTING_ORDER_REFRESH_SECONDS_V0600

    def crafting_order_synthetic_kind_v0713(self, item_id):
        item_id = str(item_id or "")
        if item_id.startswith("__gather__:"):
            parts = item_id.split(":")
            return ("gather", parts[1] if len(parts) > 1 else "")
        if item_id.startswith("__action__:"):
            parts = item_id.split(":")
            return ("action", parts[1] if len(parts) > 1 else "")
        return ("product", "")

    async def announce_gathering_order_progress_v0713(self, category, amount=1):
        active = self.server.db.crafting_order_v0600(self.account_id)
        if not active or not str(active["item_id"] or ""):
            return
        kind, target = self.crafting_order_synthetic_kind_v0713(active["item_id"])
        if kind != "gather" or target != str(category):
            return
        await self.announce_crafting_order_progress_v0600(str(active["item_id"]), amount)

    async def announce_profession_action_order_progress_v0713(self, tool_type, amount=1):
        active = self.server.db.crafting_order_v0600(self.account_id)
        if not active or not str(active["item_id"] or ""):
            return
        kind, target = self.crafting_order_synthetic_kind_v0713(active["item_id"])
        if kind != "action" or target != str(tool_type):
            return
        await self.announce_crafting_order_progress_v0600(str(active["item_id"]), amount)

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
        if source == "gather":
            category = str(spec.get("gather_category") or "")
            label = str(spec.get("gather_label") or "surowców")
            rows = []
            for tier, tier_label in enumerate(("mała", "średnia", "duża"), 1):
                output = f"__gather__:{category}:{tier}"
                recipe = {
                    "min_profession_level": 1,
                    "order_reward_level": level,
                    "order_kind": "gather",
                    "order_tier": tier,
                    "profession_xp": max(20, level * 3),
                    "tool_xp": max(15, level * 2),
                }
                item = {
                    "name": f"{tier_label.capitalize()} dostawa: {label}",
                    "type": "profession_order",
                    "order_kind": "gather",
                    "order_tier": tier,
                }
                rows.append((f"gather_{category}_{tier}", recipe, output, item, 1))
            return rows
        if source == "action":
            action_type = str(spec.get("action_type") or spec.get("tool_type") or "")
            rows = []
            for tier, tier_label in enumerate(("mała", "średnia", "duża"), 1):
                output = f"__action__:{action_type}:{tier}"
                recipe = {
                    "min_profession_level": 1,
                    "order_reward_level": level,
                    "order_kind": "action",
                    "order_tier": tier,
                    "profession_xp": max(20, level * 3),
                    "tool_xp": max(15, level * 2),
                }
                item = {
                    "name": f"{tier_label.capitalize()} seria zaklęć",
                    "type": "profession_order",
                    "order_kind": "action",
                    "order_tier": tier,
                }
                rows.append((f"action_{action_type}_{tier}", recipe, output, item, 1))
            return rows
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
                stations = tuple(map(str, recipe.get("stations") or ()))
                if source == "extended" and str(recipe.get("profession") or "") != profession:
                    continue
                if source == "craft":
                    rprof = str(recipe.get("profession") or "")
                    rtool = str(recipe.get("tool_type") or "")
                    category = str(recipe.get("category") or "").lower()
                    # Legacy Kowalstwo recipes predate explicit profession/tool_type fields.
                    # Their canonical ownership is the Haldor forge/crafting_workshop station.
                    blacksmith_recipe = (
                        rprof == "Kowalstwo"
                        or rtool == "crafting"
                        or "forge" in stations
                        or "crafting_workshop" in stations
                    )
                    if not blacksmith_recipe:
                        continue
                    if any(token in category for token in ("salvage", "tech", "refine")):
                        continue
                required = max(1, int(recipe.get("min_profession_level", recipe.get("min_tool_level", 1)) or 1))
                if required > level:
                    continue
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
        order_kind = str(item.get("order_kind") or recipe.get("order_kind") or "")
        reward_level = max(1, int(recipe.get("order_reward_level", 1) or 1))
        if order_kind == "gather":
            base = min(25, 5 + reward_level // 25)
            choices = (base, base * 2, base * 3)
            tier = max(1, min(3, int(item.get("order_tier", recipe.get("order_tier", offer_no)) or offer_no)))
            return int(choices[tier - 1])
        if order_kind == "action":
            base = 1 + min(2, reward_level // 200)
            choices = (base, base + 1, base + 2)
            tier = max(1, min(3, int(item.get("order_tier", recipe.get("order_tier", offer_no)) or offer_no)))
            return int(choices[tier - 1])
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
        level = max(1, int(recipe.get("order_reward_level", recipe.get("min_profession_level", recipe.get("min_tool_level", 1))) or 1))
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
            completion_key = self.server.db.crafting_order_completion_key_v0700(
                cycle, npc_id, output, needed
            )
            offers.append({
                "number": offer_no,
                "order_key": f"{cycle}:{npc_id}:{offer_no}:{recipe_id}:{needed}",
                "completion_key": completion_key,
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
                f"Zamówienie profesji: {item_name}. Postęp {progress} z {needed}. "
                "GOTOWE DO ODDANIA u NPC, który zlecił zamówienie.",
                combat_detail="essential",
            )
        else:
            await self.send(
                f"Zamówienie profesji: {item_name}. Postęp {progress} z {needed}.",
                combat_detail="essential",
            )

    async def handle_crafting_orders_v0600(self, args=""):
        raw = str(args or "").strip()
        words = raw.split()
        mode = normalize_lookup_text(words[0]) if words else "lista"
        active = self.server.db.crafting_order_v0600(self.account_id)

        if mode in ("status", "stan"):
            if not active or not str(active["item_id"] or ""):
                await self.send("Nie masz aktywnego zamówienia profesji.")
                return
            npc_name = NPCS.get(str(active["npc_id"]), {}).get("name", str(active["npc_id"]))
            await self.send(
                f"AKTYWNE ZAMÓWIENIE: {active['item_name']}. Postęp {int(active['progress'])} z {int(active['needed'])}. "
                f"Profesja: {active['profession']}. Zleceniodawca: {npc_name}. "
                f"Nagroda: {currency_reading_text(int(active['reward_coins']),0,0)}, "
                f"{int(active['reward_profession_xp'])} XP profesji i {int(active['reward_tool_xp'])} XP narzędzia."
            )
            return

        if mode in ("historia", "history", "statystyki", "stats"):
            rows = list(self.server.db.crafting_order_stats_v0614(self.account_id))
            legacy = next((r for r in rows if str(r["profession"]) == "__legacy__"), None)
            detailed = [r for r in rows if str(r["profession"]) != "__legacy__"]
            legacy_count = int(legacy["completed_count"] or 0) if legacy else 0
            completed = legacy_count + sum(int(r["completed_count"] or 0) for r in detailed)
            coins = sum(int(r["total_coins"] or 0) for r in detailed)
            prof_xp = sum(int(r["profession_xp"] or 0) for r in detailed)
            tool_xp = sum(int(r["tool_xp"] or 0) for r in detailed)
            best = max([int(r["best_reward_coins"] or 0) for r in detailed] or [0])
            await self.send(
                f"HISTORIA ZAMÓWIEŃ PROFESJI. Ukończone łącznie: {completed}. "
                f"Szczegółowo od v0.61.4: zarobek {currency_reading_text(coins,0,0)}, "
                f"XP profesji {prof_xp}, XP narzędzi {tool_xp}, rekord nagrody {currency_reading_text(best,0,0)}."
            )
            if legacy_count:
                await self.send(
                    f"Starsze zamówienia sprzed v0.61.4: {legacy_count}. Gra wcześniej nie zapisywała ich profesji, zarobku ani XP, więc nie dopisuję zmyślonych danych."
                )
            if not detailed:
                await self.send("Brak szczegółowych ukończeń od v0.61.4.")
                return
            for r in sorted(detailed, key=lambda row: normalize_lookup_text(str(row["profession"]))):
                await self.send(
                    f"{r['profession']}: {int(r['completed_count'])} zamówień; "
                    f"zarobek {currency_reading_text(int(r['total_coins']),0,0)}; "
                    f"XP profesji {int(r['profession_xp'])}; XP narzędzia {int(r['tool_xp'])}; "
                    f"najdroższe {currency_reading_text(int(r['best_reward_coins']),0,0)}."
                )
            return

        if mode in ("porzuc", "porzuć", "abandon"):
            if not active or not str(active["item_id"] or ""):
                await self.send("Nie masz aktywnego zamówienia profesji.")
                return
            self.server.db.abandon_crafting_order_v0600(self.account_id)
            await self.send("Porzucasz aktywne zamówienie profesji. Wykonany postęp przepada.")
            return

        if mode in ("oddaj", "deliver", "turnin"):
            if not active or not str(active["item_id"] or ""):
                await self.send("Nie masz aktywnego zamówienia profesji.")
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

            # Preflight every reward field BEFORE removing physical products.
            # v0.60.0-v0.61.2 used the non-existent SQLite key `tool_type` here,
            # which consumed the order products and then crashed with IndexError.
            tool_type = str(active["reward_tool_type"] or "")
            if not self.valid_tool_type(tool_type):
                await self.send(
                    f"Zamówienie ma nieprawidłowy typ narzędzia: {tool_type or 'brak'}. "
                    "Produkty nie zostały pobrane; zgłoś ten błąd administratorowi."
                )
                return

            item_id = str(active["item_id"])
            if self.server.db.crafting_order_offer_completed_v0700(
                self.account_id, int(active["cycle_slot"]), str(active["npc_id"]), item_id, needed
            ):
                await self.send(
                    "To konkretne zamówienie zostało już ukończone w tym cyklu. "
                    "Pozostałe oferty nadal możesz wykonać."
                )
                self.server.db.abandon_crafting_order_v0600(self.account_id)
                return
            order_kind, order_target = self.crafting_order_synthetic_kind_v0713(item_id)
            legacy_recovery = False
            if order_kind == "gather":
                category = self.quest_collect_category_info(order_target)
                if not category:
                    await self.send("Zamówienie ma nieprawidłową kategorię zbieracką. Zgłoś błąd administratorowi.")
                    return
                ids, container, label = category
                have = int(self.server.db.total_items_across_storage_and_inventory(
                    self.account_id, ids, container
                ))
                if have < needed:
                    await self.send(
                        f"Masz tylko {have} z {needed} wymaganych {label}. "
                        "Świeży postęp jest zaliczony, ale surowce muszą być nadal w magazynie profesji lub ekwipunku."
                    )
                    return
                if not self.server.db.consume_items_across_storage_and_inventory(
                    self.account_id, ids, needed, container
                ):
                    await self.send("Nie udało się pobrać surowców do zamówienia. Sprawdź magazyn profesji.")
                    return
            elif order_kind == "action":
                # Udana akcja Zaklinania już zużyła swoje materiały; nie pobieramy
                # drugiego produktu przy oddawaniu zamówienia.
                pass
            else:
                have = int(self.quest_crafted_item_have_v0333(item_id))
                legacy_recovery = (
                    have < needed
                    and progress >= needed
                    and int(active["accepted_at"] or 0) <= CRAFTING_ORDER_BROKEN_TURNIN_CUTOFF_V0613
                )
                if have < needed and not legacy_recovery:
                    await self.send(f"Masz tylko {have} z {needed} wymaganych sztuk. Produkty muszą być nadal przy tobie lub w magazynie profesji.")
                    return
                if not legacy_recovery:
                    if not self.consume_quest_crafted_items_v0333(item_id, needed):
                        await self.send("Nie udało się pobrać produktów do zamówienia. Sprawdź ekwipunek i magazyn profesji.")
                        return
                else:
                    await self.send(
                        "NAPRAWA ZAMÓWIENIA v0.61.3: wykryto aktywne, ukończone zamówienie przyjęte przed hotfixem. "
                        "Stara ścieżka mogła już pobrać produkty przed crashem, więc nie pobieram ich ponownie."
                    )

            coins = int(active["reward_coins"])
            self.character.silver = min(CURRENCY_SQLITE_SAFE_TOTAL, int(self.character.silver) + coins)
            await self.grant_profession_reward_xp(
                str(active["profession"]), int(active["reward_profession_xp"]),
                tool_type, int(active["reward_tool_xp"]),
            )
            completed_ok = self.server.db.finish_crafting_order_v0700(
                self.account_id, int(active["cycle_slot"]), str(active["npc_id"]),
                item_id, needed, str(active["profession"]), coins,
                int(active["reward_profession_xp"]), int(active["reward_tool_xp"]),
            )
            if not completed_ok:
                await self.send(
                    "To konkretne zamówienie zostało już zapisane jako ukończone w tym cyklu. "
                    "Pozostałe oferty nadal są dostępne."
                )
                return
            self.server.db.add_lifetime_stat(self.account_id, "crafting_orders_completed", 1)
            self.server.db.save_character(self.character)
            try:
                self.server.db.record_activity_v0560(
                    self.account_id, "quest", "Zamówienie profesji",
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
                await self.send("W tej lokacji nie ma NPC obsługującego rotujące zamówienia profesji.")
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
            if self.server.db.crafting_order_offer_completed_v0700(
                self.account_id, offer["cycle"], offer["npc_id"], offer["item_id"], offer["needed"]
            ):
                await self.send(
                    "To konkretne zamówienie zostało już ukończone w tym cyklu. "
                    "Wybierz jedną z pozostałych ofert."
                )
                return
            self.server.db.start_crafting_order_v0600(self.account_id, offer)
            kind, _target = self.crafting_order_synthetic_kind_v0713(offer["item_id"])
            if kind == "gather":
                progress_note = "Liczą się wyłącznie surowce zebrane po przyjęciu; przy oddaniu musisz nadal posiadać wymaganą ilość."
            elif kind == "action":
                progress_note = "Liczą się wyłącznie udane akcje Zaklinania wykonane po przyjęciu; przy oddaniu nie pobieram produktu drugi raz."
            else:
                progress_note = "Liczą się wyłącznie sztuki wykonane po przyjęciu."
            await self.send(
                f"Przyjmujesz zamówienie: {offer['item_name']} x{offer['needed']}. Start 0 z {offer['needed']}. "
                f"Nagroda: {currency_reading_text(offer['reward_coins'],0,0)}, {offer['reward_profession_xp']} XP profesji "
                f"i {offer['reward_tool_xp']} XP narzędzia. {progress_note}"
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
            await self.send("Rotujące zamówienia profesji odbierzesz u specjalistów: " + "; ".join(names) + ".")
            return
        npc_id, npc, spec = here
        offers = self.crafting_order_offers_v0600(npc_id)
        await self.send(
            f"ZAMÓWIENIA PROFESJI — {npc.get('name', npc_id)}. Profesja: {spec['profession']}. "
            "Oferty zmieniają się co 60 minut; specjalista pokazuje do 3 ofert, a każdą dostępną możesz ukończyć raz w danym cyklu. "
            "Po oddaniu jednej pozostałe nadal są dostępne."
        )
        if active and str(active["item_id"] or ""):
            await self.send(
                f"Masz aktywne: {active['item_name']} x{int(active['needed'])}; postęp {int(active['progress'])}/{int(active['needed'])}."
            )
        for offer in offers:
            done = self.server.db.crafting_order_offer_completed_v0700(
                self.account_id, offer["cycle"], offer["npc_id"], offer["item_id"], offer["needed"]
            )
            state_text = "UKOŃCZONE W TYM CYKLU. " if done else ""
            await self.send(
                f"{offer['number']}. {state_text}{offer['item_name']} x{offer['needed']}. Wymaga {spec['profession']} {offer['required_level']}. "
                f"Nagroda {currency_reading_text(offer['reward_coins'],0,0)}, {offer['reward_profession_xp']} XP profesji, "
                f"{offer['reward_tool_xp']} XP narzędzia."
            )
        if not offers:
            await self.send(
                f"Brak ofert dla aktualnego poziomu profesji {spec['profession']}. "
                "Jeżeli to Kowalstwo poziom 1+, zgłoś błąd administratorowi."
            )
        await self.send("Przyjęcie: zamowienia wez <numer>. Stan: zamowienia status. Historia: zamowienia historia. Oddanie: zamowienia oddaj.")
