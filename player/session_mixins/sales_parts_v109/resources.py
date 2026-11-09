# -*- coding: utf-8 -*-
"""v109: sprzedaż — resources; identyczne metody względem v108."""
from .dependencies import *

class SalesResourcesV109Mixin:

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
            if self.item_is_protected_v1280(item_id):
                await self.send("Ten przedmiot jest chroniony. Użyj: odchron <nazwa EQ>.")
                return

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
                normal = legacy_currency_to_coins(
                    values["silver"], values["gold"], values["mithril"]
                )
                payout = self.server.db.shop_resale_total_v1175(
                    self.account_id, item_id, 1, normal
                )
                from systems.live_olc28_expansion import sale_coins
                payout=sale_coins(payout)
                from systems.live_olc29_creation import trade_price
                payout=trade_price(self.character.room_id,payout,'sell')
                values = {"silver": payout, "gold": 0, "mithril": 0}
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
                    f"{currency_price_text(values['silver'], values['gold'], values['mithril'])}."
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

            # v1.13.8: pojedyncza i hurtowa sprzedaż korzystają z tej samej
            # wartości, łącznie z jackpotem rzadkiego wariantu i premią gatunku ryby.
            values = self.generic_item_sale_value(item_id, item)
            reward_coins = legacy_currency_to_coins(
                values["silver"], values["gold"], values["mithril"]
            )
            from systems.live_olc28_expansion import sale_coins
            reward_coins=sale_coins(reward_coins)
            from systems.live_olc29_creation import trade_price
            reward_coins=trade_price(self.character.room_id,reward_coins,'sell')
            self.character.silver += reward_coins
            await self.gain_charisma_from_sale(reward_coins)
            sale_content_level=self.profession_content_level_v11342(
                item_id=item_id,item=item
            )
            await self.announce_profession_sale_xp(
                source_container,1,content_level=sale_content_level
            )
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
