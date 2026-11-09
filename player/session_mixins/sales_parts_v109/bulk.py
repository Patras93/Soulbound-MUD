# -*- coding: utf-8 -*-
"""v109: sprzedaż — bulk; identyczne metody względem v108."""
from .dependencies import *

class SalesBulkV109Mixin:

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
            sale_content_level=self.profession_sale_content_level_v11342(
                sell_rows,container
            )
            await self.announce_profession_sale_xp(
                container,
                rewards["units"],
                content_level=sale_content_level,
            )
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
                if self.item_is_protected_v1280(item_id):
                    skipped += qty
                    continue
                if is_character_bound_item(item_id):
                    skipped += qty
                    continue
                from systems.equipment_evolution_v10500 import is_evolved
                if is_evolved(self.server.db.conn, self.account_id, item_id):
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

            rewards = self.bulk_sell_rewards_for_rows(
                sell_rows, shop_purchase_basis=True
            )

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
