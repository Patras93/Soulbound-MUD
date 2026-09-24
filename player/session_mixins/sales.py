# -*- coding: utf-8 -*-
"""Item/resource sale rules, bulk selling and sale XP."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import re
from core.bootstrap_economy_professions import (
    PROFESSION_XP_GAIN_MULTIPLIER,
    currency_reading_text,
    legacy_currency_to_coins,
    profession_max_level,
    profession_max_rank,
    profession_rank,
    profession_rank_name,
)
from core.mines_threat import EQUIPMENT_SLOT_ALIASES, ITEMS, is_character_bound_item
from core.progression_resources import v0190_resource_sale_coins, v096_fishing_reward_scale
from network.protocol_gameplay_utils import find_by_name, normalize_lookup_text
from systems.content_registry import NPCS
from systems.crafting_expansion import CRAFT_MATERIAL_STORAGE_IDS
from systems.equipment_crafting import MINING_STORAGE_IDS, SHOPS, SHOP_SELLERS
from systems.items_resources import (
    BLACKSMITH_SLOT_DEFS,
    BLACKSMITH_TIERS,
    FISH_STORAGE_IDS,
    HERB_STORAGE_IDS,
    WOOD_STORAGE_IDS,
    v096_fish_price_scale,
)
from world.economy_quests import V0863_MATERIAL_SALE_BASE_SILVER


class SessionSalesMixin:

    def generic_item_sale_allowed_here(self):
            # Zwykłe przedmioty można odsprzedawać w każdej lokacji z normalnym sklepem.
            return self.character.room_id in SHOPS

    def generic_item_sale_buyer_name(self):
            seller_id = SHOP_SELLERS.get(self.character.room_id)
            seller = NPCS.get(seller_id) if seller_id else None
            return seller.get("name") if seller else "lokalny handlarz"

    def market_buyer_rejects_item(self, item_id, item):
            # v0.9.15: Rynek ma osobny skup łupów/EQ, ale nigdy nie przejmuje
            # sprzedaży profesji. Każdy surowiec typu resource zostaje dla
            # właściwego fachowca albo systemu craftingu.
            if self.character.room_id != "market":
                return False
            if not item:
                return True
            if item.get("type") in {"resource", "craft_material"}:
                return True
            if item_id in CRAFT_MATERIAL_STORAGE_IDS:
                return True
            if item_id in (
                FISH_STORAGE_IDS | MINING_STORAGE_IDS | WOOD_STORAGE_IDS | HERB_STORAGE_IDS
            ):
                return True
            return False

    def blacksmith_crafted_sale_cap_v0341(self, item_id, item):
            """Cap NPC resale of crafted blacksmith gear by the value of consumed ore.

            Smithing should create equipment and profession progress, not multiply currency.
            Normal crafts are worth at most 90% of the source ore opportunity value; only
            high-quality/critical crafts can earn a modest premium.
            """
            material_key = str(item.get("blacksmith_material") or "").strip()
            if not material_key:
                return None

            tier = next((row for row in BLACKSMITH_TIERS if str(row.get("key")) == material_key), None)
            if not tier:
                return None
            ore = ITEMS.get(str(tier.get("ore")), {})
            ore_value = legacy_currency_to_coins(
                ore.get("sell_silver", 0), ore.get("sell_gold", 0), ore.get("sell_mithril", 0)
            )
            if ore_value <= 0:
                return None

            slot = str(item.get("slot") or "")
            slot_row = BLACKSMITH_SLOT_DEFS.get(slot)
            if not slot_row:
                return None
            ingot_cost = max(1, int(slot_row[2] or 1))
            material_value = ore_value * ingot_cost

            quality = str(item.get("craft_quality_v03054") or "normal").lower()
            quality_factor = {
                "normal": 0.90,
                "good": 0.95,
                "excellent": 1.00,
                "masterwork": 1.08,
                "legendary": 1.18,
            }.get(quality, 0.90)
            if item.get("craft_critical_v03054"):
                quality_factor += 0.05
            return max(1, int(material_value * quality_factor))

    def generic_item_sale_value(self, item_id, item):
            smith_cap = self.blacksmith_crafted_sale_cap_v0341(item_id, item)
            # Jawna cena sprzedaży ma pierwszeństwo.
            explicit = {
                "silver": int(item.get("sell_silver", 0) or 0),
                "gold": int(item.get("sell_gold", 0) or 0),
                "mithril": int(item.get("sell_mithril", 0) or 0),
            }
            if any(explicit.values()):
                if item.get("blacksmith_material"):
                    total = legacy_currency_to_coins(
                        explicit["silver"], explicit["gold"], explicit["mithril"]
                    )
                    if smith_cap is not None:
                        total = min(total, smith_cap)
                    return {"silver": total, "gold": 0, "mithril": 0}
                if item_id in FISH_STORAGE_IDS:
                    total = legacy_currency_to_coins(
                        explicit["silver"], explicit["gold"], explicit["mithril"]
                    )
                    total = max(1, int(round(total * v096_fish_price_scale(item_id))))
                    return {"silver": total, "gold": 0, "mithril": 0}
                return explicit

            # Przedmiot kupny: sklep odkupuje za 50% ceny bazowej.
            price = item.get("price")
            currency = item.get("currency", "silver")
            if isinstance(price, (int, float)) and price > 0 and currency in explicit:
                value = max(1, int(price) // 2)
                result = {"silver": 0, "gold": 0, "mithril": 0}
                result[currency] = value
                if smith_cap is not None:
                    total = legacy_currency_to_coins(result["silver"], result["gold"], result["mithril"])
                    total = min(total, smith_cap)
                    return {"silver": total, "gold": 0, "mithril": 0}
                return result

            # v0.9.15: zwykły loot z mobów (np. kły i trofea) można
            # sprzedać w każdym normalnym sklepie. Jawne sell_* nadal ma pierwszeństwo.
            if item.get("type") == "loot":
                rarity_bonus = {
                    "common": 0, "rare": 20, "epic": 60,
                    "legendary": 150, "mythic": 350, "unique": 600,
                }.get(str(item.get("rarity") or "common"), 0)
                loot_value = max(1, int(item.get("loot_sell_silver", 25) or 25))
                return {"silver": loot_value + rarity_bonus, "gold": 0, "mithril": 0}

            # v0.8.61: zdobyty/craftowany ekwipunek bez ceny sklepowej ma
            # wartość zgodną z materiałem, statystykami i właściwościami.
            if item.get("type") == "armor":
                defense = max(0, int(item.get("defense", 0) or 0))
                affix = max(0, abs(int(item.get("affix_amount", 0) or 0)))
                sockets = max(0, int(item.get("sockets", 0) or 0))
                mastery = max(0, int(item.get("required_mastery", 0) or 0))
                craft_level = max(
                    int(item.get("jewelcraft_level", 0) or 0),
                    int(item.get("blacksmith_tier", 0) or 0) * 10,
                )
                material_key = str(item.get("corpse_material") or item.get("blacksmith_material") or "")
                material_base = V0863_MATERIAL_SALE_BASE_SILVER.get(
                    material_key, 0
                )
                stat_power = sum(max(0, int(v or 0)) for v in (item.get("stats") or {}).values())
                property_power = sum(max(0.0, float(v or 0)) for v in (item.get("properties") or {}).values())
                silver = max(
                    25,
                    material_base
                    + defense * 40
                    + affix * 30
                    + sockets * 150
                    + mastery * 20
                    + craft_level * 25
                    + stat_power * 120
                    + int(property_power * 250),
                )
                if smith_cap is not None:
                    silver = min(silver, smith_cap)
                return {"silver": silver, "gold": 0, "mithril": 0}

            return {"silver": 0, "gold": 0, "mithril": 0}

    def generic_item_is_sellable(self, item_id, item):
            if not item or item.get("type") in {"quest", "tool", "resource", "craft_material"}:
                return False
            if item_id in CRAFT_MATERIAL_STORAGE_IDS:
                return False
            if is_character_bound_item(item_id):
                return False
            values = self.generic_item_sale_value(item_id, item)
            return any(values.values())

    def resource_sale_allowed_here(self, item_id):
            # v0.8.67: surowce profesji skupują tylko właściwi fachowcy.
            room_id = self.character.room_id
            if item_id in FISH_STORAGE_IDS:
                return room_id == "fish_market"
            if item_id in MINING_STORAGE_IDS:
                return room_id == "mountain_market"
            if item_id in WOOD_STORAGE_IDS:
                return room_id == "lumberjack_camp"
            if item_id in HERB_STORAGE_IDS:
                return room_id == "herbalist_hut"
            return False

    def resource_sale_location_text(self, container):
            return {
                "net": "Targ Rybny — Rybak Borys i rybacy",
                "bag": "Górski Targ Minerałów — Handlarka Minerałów Dagna",
                "woodpile": "Obóz Drwala — Drwal Bran",
                "herbbag": "Chata Zielarki — Zielarka Liora",
            }.get(container, "właściwy punkt skupu profesji")

    def resource_sale_buyer_text(self, container):
            return {
                "net": "Rybakom na Targu Rybnym",
                "bag": "Handlarce Minerałów Dagnie",
                "woodpile": "Drwalowi Branowi",
                "herbbag": "Zielarce Liorze",
            }.get(container, "właściwemu skupującemu")

    def profession_sale_definition(self, container):
            # v0.8.68: sprzedaż u właściwego fachowca rozwija specjalizację/profesję,
            # ale nie narzędzie. EXP jest liczony za faktycznie sprzedane sztuki.
            return {
                "net": ("Wędkarstwo", "fishing"),
                "bag": ("Górnictwo", "mining"),
                "woodpile": ("Drwalstwo", "woodcutting"),
                "herbbag": ("Zielarstwo", "herbalism"),
            }.get(container)

    def grant_profession_sale_xp(self, container, units):
            definition = self.profession_sale_definition(container)
            units = max(0, int(units or 0))
            if not definition or units <= 0:
                return []

            profession, _tool_type = definition
            prow = self.server.db.profession(self.account_id, profession)
            level = int(prow["level"])
            # 1 bazowy XP za sztukę; Wędkarstwo v0.9.6 kompensuje szybszy endgame.
            xp_scale = v096_fishing_reward_scale(level) if container == "net" else 1.0
            actual_xp = max(1, int(round(units * PROFESSION_XP_GAIN_MULTIPLIER * xp_scale)))
            actual_xp = self.apply_double_xp(actual_xp)
            xp = int(prow["xp"]) + actual_xp
            actions = int(prow["actions"])
            cap = profession_max_level(profession)
            old_rank = profession_rank(level, profession)
            messages = [
                f"{profession}: sprzedaż +{actual_xp} XP specjalizacji "
                f"za {units} sztuk."
            ]

            while level < cap:
                needed = self.profession_xp_to_next(level, profession)
                if xp < needed:
                    break
                xp -= needed
                level += 1
                messages.append(f"AWANS PROFESJI: {profession} osiąga poziom {level}.")

            if level >= cap:
                level = cap
                xp = 0

            self.server.db.save_profession(
                self.account_id, profession, level, xp, actions
            )

            new_rank = profession_rank(level, profession)
            if new_rank > old_rank:
                messages.append(
                    f"{profession}: awansujesz na Rangę {new_rank} "
                    f"z {profession_max_rank(profession)}: "
                    f"{profession_rank_name(profession, level)}."
                )
            return messages

    def profession_sale_units_for_rows(self, rows):
            totals = {"net": 0, "bag": 0, "woodpile": 0, "herbbag": 0}
            for item_id, quantity in rows:
                quantity = max(0, int(quantity or 0))
                if quantity <= 0:
                    continue
                if item_id in FISH_STORAGE_IDS:
                    totals["net"] += quantity
                elif item_id in MINING_STORAGE_IDS:
                    totals["bag"] += quantity
                elif item_id in WOOD_STORAGE_IDS:
                    totals["woodpile"] += quantity
                elif item_id in HERB_STORAGE_IDS:
                    totals["herbbag"] += quantity
            return totals

    async def announce_profession_sale_xp(self, container, units):
            for message in self.grant_profession_sale_xp(container, units):
                await self.send(message)

    async def announce_profession_sale_xp_for_rows(self, rows):
            for container, units in self.profession_sale_units_for_rows(rows).items():
                if units > 0:
                    await self.announce_profession_sale_xp(container, units)

    def bulk_sell_rewards_for_rows(self, rows):
            total_silver = 0
            total_gold = 0
            total_mithril = 0
            total_units = 0
            total_types = 0

            for item_id, quantity in rows:
                item = ITEMS.get(item_id, {})
                quantity = max(0, int(quantity))
                if quantity <= 0:
                    continue

                values = self.generic_item_sale_value(item_id, item)
                silver = int(values["silver"])
                gold = int(values["gold"])
                mithril = int(values["mithril"])
                if not (silver or gold or mithril):
                    continue

                total_units += quantity
                total_types += 1
                total_silver += silver * quantity
                total_gold += gold * quantity
                total_mithril += mithril * quantity

            return {
                "units": total_units,
                "types": total_types,
                "silver": total_silver,
                "gold": total_gold,
                "mithril": total_mithril,
            }

    def sale_reward_text(self, rewards):
            return currency_reading_text(
                rewards["silver"], rewards["gold"], rewards["mithril"]
            )

    async def gain_charisma_from_bulk_sale(self, rewards):
            units = max(0, int(rewards.get("units", 0) or 0))
            if units <= 0:
                return
            sale_value = legacy_currency_to_coins(
                rewards.get("silver", 0), rewards.get("gold", 0), rewards.get("mithril", 0)
            )
            await self.gain_charisma_from_sale(sale_value, units=units)

    def normalize_bulk_sell_target(self, query):
            q = normalize_lookup_text(query)
            direct = {
                "wszystko siatka": "net",
                "wszystko ryby": "net",
                "wszystkie ryby": "net",
                "cala siatka": "net",
                "cale ryby": "net",

                "wszystko sakwa": "bag",
                "wszystko rudy": "bag",
                "wszystkie rudy": "bag",
                "cala sakwa": "bag",

                "wszystko stos": "woodpile",
                "wszystko drewno": "woodpile",
                "cale drewno": "woodpile",
                "caly stos": "woodpile",

                "wszystko torba": "herbbag",
                "wszystko ziola": "herbbag",
                "wszystkie ziola": "herbbag",
                "cala torba": "herbbag",

                "wszystko przedmioty": "inventory",
                "wszystkie przedmioty": "inventory",
                "wszystko": "inventory",
                "all": "inventory",
                "all items": "inventory",
                "everything": "inventory",

                "ryby siatka": "net",
                "ryba siatka": "net",
                "fish net": "net",
                "net": "net",
                "siatka": "net",
                "ryby": "net",

                "rudy sakwa": "bag",
                "ruda sakwa": "bag",
                "ore bag": "bag",
                "ores bag": "bag",
                "bag": "bag",
                "sakwa": "bag",
                "rudy": "bag",

                "drewno stos": "woodpile",
                "wood pile": "woodpile",
                "woodpile": "woodpile",
                "stos": "woodpile",
                "drewno": "woodpile",

                "ziola torba": "herbbag",
                "ziola herbs": "herbbag",
                "herbs bag": "herbbag",
                "herbbag": "herbbag",
                "ziola": "herbbag",
                "herbs": "herbbag",
                "torba zielarska": "herbbag",

                "przedmioty": "inventory",
                "items": "inventory",
                "inventory": "inventory",
                "ekwipunek": "inventory",
            }
            return direct.get(q)

    async def bulk_sell_container(self, container):
            definition = self.profession_storage_definition(container)
            if not definition:
                await self.send("Nieznany magazyn profesji.")
                return False

            rows_db = self.server.db.storage_rows(
                self.account_id, container
            )
            if not rows_db:
                await self.send(
                    f"{self.container_label(container)} jest pusty."
                )
                return False

            sell_rows = []
            for row in rows_db:
                item_id = row["item_id"]
                qty = int(row["quantity"])
                item = ITEMS.get(item_id, {})
                if (
                    item_id in definition["ids"]
                    and qty > 0
                    and self.resource_sale_allowed_here(item_id)
                    and (
                        item.get("sell_silver", 0)
                        or item.get("sell_gold", 0)
                        or item.get("sell_mithril", 0)
                    )
                ):
                    sell_rows.append((item_id, qty))

            if not sell_rows:
                await self.send(
                    f"Nie możesz sprzedać zawartości "
                    f"{self.container_label(container)} tutaj. "
                    f"Sprzedaż: "
                    f"{self.resource_sale_location_text(container)}."
                )
                return False

            rewards = self.bulk_sell_rewards_for_rows(sell_rows)

            for item_id, qty in sell_rows:
                if not self.server.db.remove_storage_item(
                    self.account_id, container, item_id, qty
                ):
                    raise RuntimeError(
                        f"Nie udało się sprzedać {item_id} x{qty}."
                    )

            self.character.silver += rewards["silver"]
            self.character.gold += rewards["gold"]
            self.character.mithril += rewards["mithril"]

            await self.gain_charisma_from_bulk_sale(rewards)
            await self.announce_profession_sale_xp(container, rewards["units"])
            self.server.db.save_character(self.character)

            await self.send(
                f"Sprzedajesz {self.resource_sale_buyer_text(container)} cały magazyn: "
                f"{self.container_label(container)}. "
                f"Sztuk: {rewards['units']}. "
                f"Rodzajów: {rewards['types']}."
            )
            await self.send(
                f"Zarobek: {self.sale_reward_text(rewards)}."
            )
            return True

    async def bulk_sell_inventory_items(self):
            rows = self.server.db.inventory(self.account_id)
            equipped_counts = {}
            for equipped in self.server.db.equipment(self.account_id):
                item_id = equipped["item_id"]
                equipped_counts[item_id] = equipped_counts.get(item_id, 0) + 1

            sell_rows = []
            skipped = 0

            for row in rows:
                item_id = row["item_id"]
                qty = int(row["quantity"])
                item = ITEMS.get(item_id, {})
                equipped_count = min(qty, int(equipped_counts.get(item_id, 0)))
                sellable_qty = max(0, qty - equipped_count)

                if sellable_qty <= 0:
                    skipped += qty
                    continue

                if equipped_count:
                    skipped += equipped_count

                # v0.30.20: sell all jest celowo BEZPIECZNE. Hurtowo sprzedaje
                # wyłącznie niezałożone EQ. Mikstury, consumables, loot, materiały,
                # quest itemy, narzędzia i wszystkie inne typy pozostają nietknięte.
                if item.get("type") != "armor":
                    skipped += qty
                    continue
                if is_character_bound_item(item_id):
                    skipped += qty
                    continue
                if not self.generic_item_sale_allowed_here():
                    skipped += qty
                    continue
                if not self.generic_item_is_sellable(item_id, item):
                    skipped += qty
                    continue
                sell_rows.append((item_id, sellable_qty))

            if not sell_rows:
                await self.send(
                    "Nie masz tutaj niezałożonego EQ do sprzedaży. "
                    "Sell all nigdy nie sprzedaje mikstur, materiałów, lootu, narzędzi ani quest itemów."
                )
                return False

            rewards = self.bulk_sell_rewards_for_rows(sell_rows)

            for item_id, qty in sell_rows:
                if not self.server.db.remove_item(
                    self.account_id, item_id, qty
                ):
                    raise RuntimeError(
                        f"Nie udało się sprzedać {item_id} x{qty}."
                    )

            self.character.silver += rewards["silver"]
            self.character.gold += rewards["gold"]
            self.character.mithril += rewards["mithril"]

            await self.gain_charisma_from_bulk_sale(rewards)
            await self.announce_profession_sale_xp_for_rows(sell_rows)
            self.server.db.save_character(self.character)

            await self.send(
                f"Sprzedajesz sprzedawcy {self.generic_item_sale_buyer_name()} "
                f"niezałożone EQ z inventory. "
                f"Sztuk: {rewards['units']}. "
                f"Rodzajów: {rewards['types']}."
            )
            await self.send(
                f"Zarobek: {self.sale_reward_text(rewards)}."
            )
            if skipped:
                await self.send(
                    f"Pominięto {skipped} sztuk: sell all chroni wszystko poza niezałożonym EQ "
                    f"oraz nigdy nie sprzedaje aktualnie założonych części."
                )
            return True

    def logical_sell_equipment_slot(self, slot):
            slot = str(slot or "").strip().lower()
            if slot in ("ring1", "ring2"):
                return "ring"
            if slot in ("charm1", "charm2"):
                return "charm"
            return slot

    def sell_slot_from_query(self, query):
            q = normalize_lookup_text(query)
            if not q:
                return None
            for alias, slot in EQUIPMENT_SLOT_ALIASES.items():
                if normalize_lookup_text(alias) == q:
                    return self.logical_sell_equipment_slot(slot)
            return None

    def owned_single_sale_candidates(self, query):
            """v0.23: rozwiązuje sprzedaż WYŁĄCZNIE wśród faktycznie posiadanych,
            wolnych i sprzedawalnych przedmiotów. Dzięki temu `sprzedaj helm` nie
            przeszukuje 26 tysięcy globalnych definicji EQ i nie wybiera losowo.
            """
            q = normalize_lookup_text(query)
            if not q:
                return []
            requested_slot = self.sell_slot_from_query(query)
            rows = []
            for row in self.server.db.inventory(self.account_id):
                item_id = row["item_id"]
                item = ITEMS.get(item_id)
                if not item or not self.generic_item_is_sellable(item_id, item):
                    continue
                free_qty = max(
                    0, int(row["quantity"]) - self.equipped_quantity_of_item(item_id)
                )
                if free_qty <= 0:
                    continue
                if requested_slot:
                    if item.get("type") != "armor":
                        continue
                    if self.logical_sell_equipment_slot(item.get("slot")) != requested_slot:
                        continue
                    rows.append((item_id, item, free_qty))
                    continue
                item_name = normalize_lookup_text(item.get("name", ""))
                item_key = normalize_lookup_text(item_id)
                if q == item_name or q == item_key or q in item_name or q in item_key:
                    rows.append((item_id, item, free_qty))
            return rows

    async def ask_single_sale_choice(self, query, candidates):
            self.sell_choice_state = {
                "room_id": self.character.room_id,
                "query": str(query or "").strip(),
                "item_ids": [item_id for item_id, _item, _qty in candidates],
            }
            await self.send(
                f"Pasuje kilka twoich wolnych przedmiotów: {len(candidates)}. "
                "Wybierz numer komendą sprzedaj <numer>."
            )
            for number, (item_id, item, free_qty) in enumerate(candidates, 1):
                values = self.generic_item_sale_value(item_id, item)
                await self.send(
                    f"{number}. {item['name']}. Wolne sztuki: {free_qty}. "
                    f"Cena jednej: {currency_reading_text(values['silver'], values['gold'], values['mithril'])}."
                )

    async def sell_command(self, query):
            raw_query = str(query or "").strip()
            # Numer po liście niejednoznacznych przedmiotów oznacza wybór z tej
            # listy, a nie nazwę globalnego itemu. Lista działa tylko w tym samym sklepie.
            if raw_query.isdigit() and self.sell_choice_state:
                state = self.sell_choice_state
                if state.get("room_id") != self.character.room_id:
                    self.sell_choice_state = None
                    await self.send("Poprzednia lista sprzedaży wygasła. Wskaż przedmiot ponownie.")
                    return
                index = int(raw_query) - 1
                item_ids = list(state.get("item_ids") or ())
                if index < 0 or index >= len(item_ids):
                    await self.send(
                        f"Nie ma pozycji {raw_query}. Wybierz numer od 1 do {len(item_ids)}."
                    )
                    return
                item_id = item_ids[index]
                self.sell_choice_state = None
                await self.sell_resource(item_id)
                return

            if not raw_query.isdigit():
                self.sell_choice_state = None

            target = self.normalize_bulk_sell_target(query)

            if target == "inventory":
                await self.bulk_sell_inventory_items()
                return

            if target in {"net", "bag", "woodpile", "herbbag"}:
                await self.bulk_sell_container(target)
                return

            await self.sell_resource(query)

    def parse_numbered_inventory_query(self, query):
            raw = str(query or "").strip()
            match = re.match(r"^\s*(\d+)\s*[\.\)]\s*(.+?)\s*$", raw)
            if not match:
                return None, raw
            return max(1, int(match.group(1))), match.group(2).strip()

    async def sell_resource(self, query):
            copy_number, item_query = self.parse_numbered_inventory_query(query)

            # v0.23: dla zwykłej sprzedaży najpierw patrzymy na RZECZY GRACZA,
            # nie na cały katalog ITEMS. Obsługuje to m.in. `sprzedaj helm` i
            # fragment nazwy. Przy wielu trafieniach zawsze jest jawny wybór.
            found = None
            if copy_number is None:
                owned_candidates = self.owned_single_sale_candidates(item_query)
                if len(owned_candidates) == 1:
                    item_id, item, _free_qty = owned_candidates[0]
                    found = (item_id, item)
                elif len(owned_candidates) > 1:
                    await self.ask_single_sale_choice(item_query, owned_candidates)
                    return

            if not found:
                found = find_by_name(ITEMS, item_query)
            if not found:
                await self.send(
                    "Nie rozpoznaję takiego przedmiotu albo pasuje kilka pozycji. "
                    "Dla EQ możesz użyć typu, np. sprzedaj helm."
                )
                return
            item_id, item = found

            if self.market_buyer_rejects_item(item_id, item):
                await self.send(
                    "Handlarz Skupu Radan nie skupuje materiałów rzemieślniczych ani zasobów profesyjnych. "
                    "Ryby, rudy i minerały, drewno oraz zioła sprzedawaj u właściwych fachowców."
                )
                return

            # v0.8.51: zwykłe przedmioty (np. talizmany, pierścienie, pancerze)
            # można sprzedać w dowolnym normalnym sklepie.
            if item.get("type") != "resource" and item_id not in MINING_STORAGE_IDS:
                if not self.generic_item_is_sellable(item_id, item):
                    await self.send("Tego przedmiotu nie można sprzedać.")
                    return
                if not self.generic_item_sale_allowed_here():
                    await self.send(
                        "Zwykłe przedmioty sprzedasz w lokacji z normalnym sklepem. "
                        "Przejdź do sklepu i użyj: sprzedaj <nazwa przedmiotu>."
                    )
                    return
                owned_qty = self.server.db.item_qty(self.account_id, item_id)
                if owned_qty <= 0:
                    await self.send("Nie masz tego przedmiotu.")
                    return
                equipped_count = sum(
                    1 for row in self.server.db.equipment(self.account_id)
                    if row["item_id"] == item_id
                )
                if copy_number is not None:
                    if copy_number > owned_qty:
                        await self.send(
                            f"Masz tylko {owned_qty} sztuk: {item['name']}."
                        )
                        return
                    if copy_number <= equipped_count:
                        await self.send(
                            f"Egzemplarz {copy_number}: {item['name']} jest założony. "
                            f"Sprzedaj egzemplarz od {equipped_count + 1} wzwyż albo zdejmij talizman/EQ."
                        )
                        return
                elif owned_qty <= equipped_count:
                    await self.send(
                        f"Wszystkie posiadane sztuki {item['name']} są założone. "
                        "Najpierw zdejmij jedną albo wskaż wolny egzemplarz numerem."
                    )
                    return
                values = self.generic_item_sale_value(item_id, item)
                if not self.server.db.remove_item(self.account_id, item_id, 1):
                    await self.send("Nie udało się sprzedać przedmiotu.")
                    return
                self.character.silver += values["silver"]
                self.character.gold += values["gold"]
                self.character.mithril += values["mithril"]
                await self.gain_charisma_from_sale(legacy_currency_to_coins(values["silver"], values["gold"], values["mithril"]))
                self.server.db.save_character(self.character)
                copy_text = f" egzemplarz {copy_number}" if copy_number is not None else ""
                await self.send(
                    f"Sprzedajesz sprzedawcy {self.generic_item_sale_buyer_name()}{copy_text}: "
                    f"{item['name']} za "
                    f"{currency_reading_text(values['silver'], values['gold'], values['mithril'])}."
                )
                return

            fish_items = FISH_STORAGE_IDS
            ore_items = MINING_STORAGE_IDS
            wood_items = WOOD_STORAGE_IDS
            herb_items = HERB_STORAGE_IDS

            if item_id in fish_items:
                source_container = "net"
            elif item_id in ore_items:
                source_container = "bag"
            elif item_id in wood_items:
                source_container = "woodpile"
            elif item_id in herb_items:
                source_container = "herbbag"
            else:
                source_container = None

            storage_quantity = (
                self.server.db.storage_qty(self.account_id, source_container, item_id)
                if source_container else 0
            )
            inventory_quantity = self.server.db.item_qty(self.account_id, item_id)
            if storage_quantity <= 0 and inventory_quantity <= 0:
                await self.send("Nie masz tego przedmiotu.")
                return

            if item_id in fish_items and self.character.room_id != "fish_market":
                await self.send("Ryby skupują tylko rybacy na Targu Rybnym.")
                return
            if item_id in ore_items and self.character.room_id != "mountain_market":
                await self.send("Rudy, minerały i surowe klejnoty skupuje tylko Handlarka Minerałów Dagna na Górskim Targu Minerałów.")
                return
            if item_id in wood_items and self.character.room_id != "lumberjack_camp":
                await self.send("Drewno skupuje tylko Drwal Bran w Obozie Drwala.")
                return
            if item_id in herb_items and self.character.room_id != "herbalist_hut":
                await self.send("Zioła skupuje tylko Zielarka Liora w Chacie Zielarki.")
                return

            removed = False
            if source_container and self.server.db.storage_qty(
                self.account_id, source_container, item_id
            ) > 0:
                removed = self.server.db.remove_storage_item(
                    self.account_id, source_container, item_id, 1
                )
            elif self.server.db.item_qty(self.account_id, item_id) > 0:
                removed = self.server.db.remove_item(
                    self.account_id, item_id, 1
                )

            if not removed:
                await self.send("Nie masz tego surowca.")
                return

            # v0.19: sprzedaż zasobów skaluje się razem z globalną ekonomią.
            reward_coins = v0190_resource_sale_coins(item_id, item)
            self.character.silver += reward_coins
            await self.gain_charisma_from_sale(reward_coins)
            await self.announce_profession_sale_xp(source_container, 1)
            self.server.db.save_character(self.character)

            buyer = self.resource_sale_buyer_text(source_container)
            await self.send(
                f"Sprzedajesz {buyer}: {item['name']} za "
                + currency_reading_text(reward_coins, 0, 0) + "."
            )

    def recipe_container_for_item(self, item_id):
            if item_id in FISH_STORAGE_IDS:
                return "net"
            if item_id in MINING_STORAGE_IDS:
                return "bag"
            if item_id in WOOD_STORAGE_IDS:
                return "woodpile"
            if item_id in HERB_STORAGE_IDS:
                return "herbbag"
            if item_id in CRAFT_MATERIAL_STORAGE_IDS:
                return "craftbox"
            return None
