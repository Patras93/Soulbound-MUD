# -*- coding: utf-8 -*-
"""Shop, buying and teacher interactions."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import re
from core.bootstrap_economy_professions import currency_reading_text
from core.classes_skills import CLASS_DESCRIPTIONS, CLASS_SKILLS, ROOMS
from core.mines_threat import EQUIPMENT_SLOT_NAMES, ITEMS, TOOL_BUY_ALIASES, TOOL_SHOP_ROOMS, is_character_bound_item
from core.progression_600 import CHARACTER_MAX_LEVEL, SKILL_MAX_LEVEL
from core.progression_resources import skill_xp_to_next
from network.protocol_gameplay_utils import find_by_name, normalize_lookup_text
from systems.content_registry import NPCS
from systems.equipment_crafting import MINING_STORAGE_IDS, SHOPS, SHOP_SELLERS, class_equipment_unlocked_tier
from systems.items_resources import (
    CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER,
    CLASS_SHOP_CLASSES_BY_ROOM,
    FISH_STORAGE_IDS,
    HERB_STORAGE_IDS,
    WOOD_STORAGE_IDS,
)


class SessionShopsTeachersMixin:
    def current_shop_offers(self, class_filter=""):
            room_id = self.character.room_id
            class_names = CLASS_SHOP_CLASSES_BY_ROOM.get(room_id)
            if not class_names:
                return list(SHOPS.get(room_id, ()))

            selected = list(class_names)
            query = normalize_lookup_text(class_filter or "")
            if query:
                matched = [
                    class_name for class_name in class_names
                    if query in normalize_lookup_text(class_name)
                    or normalize_lookup_text(class_name) in query
                ]
                if matched:
                    selected = matched
                else:
                    return []

            offers = []
            for class_name in selected:
                # v0.30.35: klasowe EQ odblokowuje Poziom postaci, nie Biegłość klasy.
                character_level = max(1, min(CHARACTER_MAX_LEVEL, int(self.character.character_level)))
                unlocked_tier = class_equipment_unlocked_tier(character_level)
                offers.extend(
                    CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER
                    .get(class_name, {})
                    .get(unlocked_tier, ())
                )
            return offers

    def shop_offer_lock_text(self, item_id, item):
            """Krótki stan dostępności do czytania na numerowanej liście sklepu."""
            states = []
            if is_character_bound_item(item_id) and self.server.db.item_qty(self.account_id, item_id) > 0:
                states.append("już posiadasz")
            required_class = item.get("required_class")
            if required_class and required_class not in self.active_class_names():
                states.append(f"wymaga aktywnej klasy {required_class}")
            if item.get("type") == "armor" and not self.equipment_mastery_requirement_met(item):
                required_level = self.equipment_character_level_requirement(item)
                states.append(f"wymaga Levelu postaci {required_level}")
            return "; ".join(states)

    def equipped_items_for_shop_item(self, item):
            """Zwraca założone przedmioty zajmujące logicznie ten sam slot co oferta."""
            if item.get("type") != "armor":
                return []
            logical = item.get("slot")
            if logical == "ring":
                valid_slots = {"ring", "ring1", "ring2"}
            elif logical == "charm":
                valid_slots = {"charm", "charm1", "charm2"}
            elif logical == "earring":
                valid_slots = {"earring", "earring1", "earring2"}
            else:
                valid_slots = {logical}
            results = []
            for row in self.server.db.equipment(self.account_id):
                if row["slot"] not in valid_slots:
                    continue
                equipped = ITEMS.get(row["item_id"])
                if equipped:
                    results.append((row["slot"], row["item_id"], equipped))
            return results

    async def shop_info(self, query, class_filter=""):
            """Pełny podgląd pozycji sklepu przed zakupem, szczególnie wygodny dla NVDA."""
            room_id = self.character.room_id
            offers = self.current_shop_offers(class_filter)
            if not offers:
                await self.send("W tej lokacji nie ma sklepu.")
                return

            raw = str(query or "").strip()
            if not raw:
                await self.send("Użycie: shop info <numer>, na przykład shop info 1.")
                return

            found = None
            numeric = re.fullmatch(r"\d+", raw)
            if numeric:
                number = int(raw)
                if number < 1 or number > len(offers):
                    await self.send(
                        f"Nie ma pozycji {number} w tym sklepie. Zakres: 1-{len(offers)}."
                    )
                    return
                item_id = offers[number - 1]
                found = (number, item_id, ITEMS[item_id])
            else:
                possible = {item_id: ITEMS[item_id] for item_id in offers}
                by_name = find_by_name(possible, raw)
                if by_name:
                    item_id, item = by_name
                    found = (offers.index(item_id) + 1, item_id, item)

            if not found:
                await self.send(
                    "Nie rozpoznaję tej pozycji sklepu. Wpisz shop po numerowaną listę, "
                    "potem shop info <numer>."
                )
                return

            number, item_id, item = found
            base_price = self.shop_item_base_value_silver(item)
            cashback = self.shop_cashback_silver(item)
            final_price = max(0, base_price - cashback)
            await self.send(f"INFORMACJE O SKLEPIE {number}. {item['name']}.")
            await self.send(self.format_item_description(item_id, item))
            if cashback > 0:
                await self.send(
                    "Cena katalogowa: " + currency_reading_text(base_price, 0, 0)
                    + ". Zwrot z rabatu Charyzmy: " + currency_reading_text(cashback, 0, 0)
                    + ". Efektywny koszt: " + currency_reading_text(final_price, 0, 0) + "."
                )
            else:
                await self.send("Koszt zakupu: " + currency_reading_text(base_price, 0, 0) + ".")

            lock_text = self.shop_offer_lock_text(item_id, item)
            if lock_text:
                await self.send("Stan zakupu: " + lock_text + ".")
            else:
                await self.send("Stan zakupu: możesz kupić ten przedmiot.")

            if item.get("type") == "armor":
                equipped = self.equipped_items_for_shop_item(item)
                new_def = int(item.get("defense", 0) or 0)
                if not equipped:
                    await self.send("Porównanie EQ: w tym slocie nic nie masz założonego.")
                else:
                    await self.send("Porównanie z aktualnym EQ:")
                    for slot, equipped_id, current in equipped:
                        old_def = int(current.get("defense", 0) or 0)
                        diff = new_def - old_def
                        diff_text = f"+{diff}" if diff > 0 else str(diff)
                        slot_name = EQUIPMENT_SLOT_NAMES.get(slot, slot)
                        await self.send(
                            f"{slot_name}: {current['name']}. Obrona +{old_def}. "
                            f"Nowy przedmiot: +{new_def}. Różnica {diff_text}."
                        )
                        # Pełne statystyki obecnego przedmiotu są ważniejsze niż zgadywana ocena mocy.
                        await self.send("Obecne EQ: " + self.format_item_description(equipped_id, current))
            await self.send(f"Kupno: kup {number}. Powrót do listy: shop.")

    async def shop(self, args=""):
            room_id = self.character.room_id
            class_names = CLASS_SHOP_CLASSES_BY_ROOM.get(room_id, ())
            raw_args = (args or "").strip()

            # shop info 1 / sklep info 1 / list info 1
            info_match = re.match(r"^(?:info|informacje|opis|details|szczegoly|szczegóły)(?:\s+(.+))?$", raw_args, flags=re.IGNORECASE)
            if info_match:
                await self.shop_info(info_match.group(1) or "")
                return

            class_filter = raw_args
            offers = self.current_shop_offers(class_filter)
            if not offers:
                if class_filter and class_names:
                    await self.send(
                        "W tej sali nie ma sklepu wskazanej klasy. Dostępne: "
                        + ", ".join(class_names) + "."
                    )
                else:
                    await self.send("W tej lokacji nie ma sklepu.")
                return
            seller_id = SHOP_SELLERS.get(self.character.room_id)
            seller = NPCS.get(seller_id) if seller_id else None
            seller_text = f" Sprzedawca: {seller['name']}." if seller else ""
            class_heading = f" Klasa: {class_filter}." if class_filter and class_names else ""
            await self.send(
                f"Oferta sklepu.{class_heading} Rabat Charyzmy: "
                f"{self.character.shop_discount_percent()} procent.{seller_text}"
            )
            for number, item_id in enumerate(offers, 1):
                item = ITEMS[item_id]
                price_coins = self.shop_item_base_value_silver(item)
                cashback = self.shop_cashback_silver(item)
                effective = max(0, price_coins - cashback)
                price_text = currency_reading_text(effective, 0, 0)
                lock_text = self.shop_offer_lock_text(item_id, item)
                state = f" — {lock_text}" if lock_text else ""
                await self.send(f"{number}. {item['name']} — cena {price_text}{state}.")
            await self.send(
                "Podgląd przed zakupem: shop info <numer>, np. shop info 1. "
                "Kupno: kup <numer> lub kup <numer> <ilość>. "
                "Sprzedaż: sprzedaj <nazwa>."
            )

    async def buy(self, query):
            raw_query = (query or "").strip()
            normalized_query = normalize_lookup_text(raw_query)
            requested_tool = TOOL_BUY_ALIASES.get(normalized_query)

            offers = self.current_shop_offers()
            if not offers:
                if requested_tool:
                    target_room = TOOL_SHOP_ROOMS[requested_tool]
                    await self.send(
                        f"{ITEMS[requested_tool]['name']} kupisz w lokacji "
                        f"{ROOMS[target_room]['name']}. "
                        f"Możesz użyć walk {target_room.replace('_', ' ')}."
                    )
                    return
                await self.send("W tej lokacji nie ma sklepu.")
                return

            possible = {item_id: ITEMS[item_id] for item_id in offers}
            quantity = 1
            found = None

            # Zakup numerem z aktualnej, ponumerowanej listy sklepu.
            # Przykłady: kup 9, kup 9 3.
            numeric_match = re.fullmatch(r"\s*(\d+)(?:\s+(\d+))?\s*", raw_query)
            if numeric_match:
                offer_number = int(numeric_match.group(1))
                if numeric_match.group(2):
                    quantity = int(numeric_match.group(2))
                if quantity < 1:
                    await self.send("Liczba sztuk musi być większa od zera.")
                    return
                if offer_number < 1 or offer_number > len(offers):
                    await self.send(
                        f"Nie ma pozycji {offer_number} w tym sklepie. "
                        f"Wpisz shop albo list, aby usłyszeć ofertę od 1 do {len(offers)}."
                    )
                    return
                item_id = offers[offer_number - 1]
                found = (item_id, ITEMS[item_id])

            if not found and requested_tool and requested_tool in possible:
                found = (requested_tool, possible[requested_tool])
            if not found:
                found = find_by_name(possible, raw_query)

            if not found:
                if requested_tool:
                    target_room = TOOL_SHOP_ROOMS[requested_tool]
                    await self.send(
                        f"{ITEMS[requested_tool]['name']} nie jest sprzedawana tutaj. "
                        f"Kupisz ją w lokacji {ROOMS[target_room]['name']}."
                    )
                    return
                await self.send(
                    "Tego przedmiotu nie ma w ofercie. "
                    "Możesz też kupować numerem, na przykład kup 9."
                )
                return

            item_id, item = found

            if is_character_bound_item(item_id):
                if quantity != 1:
                    await self.send(
                        f"{item['name']} jest przypisany do postaci i można kupić tylko jedną sztukę."
                    )
                    return
                owned_quantity = self.server.db.item_qty(
                    self.account_id, item_id
                )
                if owned_quantity > 0:
                    await self.send(
                        f"{item['name']} jest już przypisany do tej postaci. "
                        "Każde narzędzie profesji można kupić tylko raz."
                    )
                    return

            required_class = item.get("required_class")
            if (
                required_class
                and required_class
                not in self.active_class_names()
            ):
                await self.send(
                    f"{item['name']} jest wyposażeniem klasy "
                    f"{required_class}. Aktywuj tę klasę, aby kupić "
                    "ten przedmiot."
                )
                return

            required_mastery = max(1, int(item.get("required_mastery", 1)))
            if not self.equipment_mastery_requirement_met(item):
                await self.send(
                    f"{item['name']}: {self.equipment_mastery_requirement_text(item)}"
                )
                return

            unit_price = self.shop_item_base_value_silver(item)
            total_price = unit_price * quantity
            current = self.character_wallet_silver_value()
            if current < total_price:
                await self.send(
                    "Masz za mało pieniędzy. Potrzeba "
                    + currency_reading_text(total_price, 0, 0)
                    + f" za {quantity} szt. Masz "
                    + currency_reading_text(current, 0, 0) + "."
                )
                return
            self.character.silver = current - total_price
            self.character.gold = 0
            self.character.mithril = 0
            cashback = self.shop_cashback_silver(item) * quantity
            if cashback > 0:
                self.character.silver += cashback
            if item_id in (FISH_STORAGE_IDS | MINING_STORAGE_IDS | WOOD_STORAGE_IDS | HERB_STORAGE_IDS):
                self.store_profession_resource(item_id, quantity)
            else:
                self.server.db.add_item(self.account_id, item_id, quantity)
            if item.get("type") == "tool":
                self.server.db.ensure_tool(self.account_id, item["tool_type"])
            self.server.db.save_character(self.character)
            if quantity == 1:
                await self.send(f"Kupujesz {item['name']} za " + currency_reading_text(total_price, 0, 0) + ".")
            else:
                await self.send(
                    f"Kupujesz {quantity} szt. {item['name']} za "
                    + currency_reading_text(total_price, 0, 0) + "."
                )
            if cashback > 0:
                await self.send(
                    "Rabat Charyzmy: sprzedawca zwraca ci "
                    + currency_reading_text(cashback, 0, 0) + "."
                )

    async def show_teachers(self):
            teachers = [
                (npc_id, npc) for npc_id, npc in NPCS.items()
                if npc.get("teacher_class")
            ]
            await self.send("Nauczyciele klasowi mają osobne sale w Gildii Dusz. Nauka jest płatna:")
            for number, (npc_id, npc) in enumerate(teachers, 1):
                own = (
                    " Aktywna klasa."
                    if npc["teacher_class"] in self.active_class_names()
                    else ""
                )
                room_name = ROOMS[npc["room"]]["name"]
                await self.send(
                    f"{number}. {npc['name']}. Klasa: {npc['teacher_class']}. "
                    f"Lokacja: {room_name}.{own}"
                )
            await self.send(
                "Użyj prowadz <nazwa lokacji>, aby dojść do odpowiedniej sali, "
                "potem talk <nauczyciel>. Każdy skill pokazuje cenę nauki."
            )

    async def teacher_lesson(self, npc):
            class_name = npc["teacher_class"]
            learned = self.server.db.learned_skill_ids(self.account_id)

            await self.send(
                f"Lekcja klasy {class_name}. {CLASS_DESCRIPTIONS.get(class_name, '')}"
            )

            for number, skill in enumerate(CLASS_SKILLS.get(class_name, []), 1):
                progress = ""
                if class_name not in self.active_class_names():
                    status = f"wymaga aktywnej klasy {class_name} i Biegłości {skill['unlock']}"
                elif skill["id"] in learned:
                    row = self.server.db.skill_progress(self.account_id, skill["id"])
                    status = "już nauczona"
                    if int(row["level"]) >= SKILL_MAX_LEVEL:
                        progress = f" Skill Poziom {SKILL_MAX_LEVEL}, maksymalny."
                    else:
                        progress = (
                            f" Skill Poziom {row['level']}, XP {row['xp']} z "
                            f"{skill_xp_to_next(int(row['level']))}."
                        )
                elif self.class_mastery_level(class_name) >= int(skill["unlock"]):
                    status = "możesz nauczyć się teraz"
                else:
                    status = f"zablokowana do Biegłości klasy {skill['unlock']}"

                mana = f" Mana {skill.get('mana', 0)}." if skill.get("mana", 0) else ""
                training_cost = self.skill_training_cost_silver(skill)
                training_discount = self.character.guild_training_discount(class_name)
                training_cost = max(1, int(round(training_cost * (1.0 - training_discount))))
                cost_text = (
                    ""
                    if skill["id"] in learned
                    else f" Cena nauki po rabacie Gildii: {self.training_cost_text(training_cost)}."
                )
                await self.send(
                    f"{number}. {skill['name']}. {status}.{progress} "
                    f"Cooldown bazowy {skill['cooldown']} sekund.{mana} "
                    f"{skill['desc']}{cost_text}"
                )

            if class_name in self.active_class_names():
                role = (
                    "głównej" if class_name == self.character.class_name
                    else "dodatkowej aktywnej"
                )
                await self.send(
                    f"To jest nauczyciel twojej {role} klasy {class_name}. "
                    f"Aktualna Biegłość klasy {class_name}: {self.class_mastery_level(class_name)}."
                )
                await self.send(
                    "Nauka: learn <numer>, naucz <pełna nazwa> albo "
                    "naturalnie, np. naucz leczenie, naucz tarcza, "
                    "naucz ciecie, naucz pocisk, naucz ogien. "
                    f"Każdy nauczony skill rozwija własny Skill Level 1-{SKILL_MAX_LEVEL}. "
                    "Nauka jest płatna; cena jest podana przy każdym skillu."
                )
            else:
                await self.send(
                    f"Klasa {class_name} nie jest teraz aktywna. "
                    "Dodaj ją przez multiclass add <klasa>, aby móc się uczyć."
                )
