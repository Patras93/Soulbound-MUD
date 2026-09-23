# -*- coding: utf-8 -*-
"""Charisma, money and bank operations."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import math
from core.bootstrap_economy_professions import (
    CHARISMA_MAX_DISCOUNT,
    GOLD_PER_MITHRIL,
    SILVER_PER_GOLD,
    SILVER_PER_MITHRIL,
    V019_SAFE_INT,
    currency_reading_text,
    generator_core_v027,
    legacy_currency_to_coins,
)
from core.mines_threat import ITEMS, is_character_bound_item
from core.progression_resources import BANK_ROOM, v0190_economy_sink
from network.protocol_gameplay_utils import find_by_name, normalize_lookup_text


class SessionBankingCharismaMixin:

    def shop_item_base_value_silver(self, item):
            price = int(item.get("price") or 0)
            currency = item.get("currency", "silver")
            if currency == "silver":
                base = price
            elif currency == "gold":
                base = price * SILVER_PER_GOLD
            elif currency == "mithril":
                base = price * GOLD_PER_MITHRIL * SILVER_PER_GOLD
            else:
                base = 0
            required=max(1,int(item.get("required_mastery",1) or 1))
            if required >= 10 and base > 0:
                base=max(base,v0190_economy_sink(required,"equipment"))
            return min(V019_SAFE_INT,max(0,int(base)))

    def shop_cashback_silver(self, item):
            base = self.shop_item_base_value_silver(item)
            return (base * self.character.shop_discount_percent()) // 100

    async def show_charisma(self):
            c = self.character
            await self.send(f"Charyzma: {c.charisma}.")
            await self.send(
                f"Rabat sklepowy: {c.shop_discount_percent()} procent "
                f"z maksymalnych {CHARISMA_MAX_DISCOUNT} procent."
            )
            if c.shop_discount_percent() < CHARISMA_MAX_DISCOUNT:
                await self.send(
                    f"Do następnego 1 procent rabatu: "
                    f"{c.charisma_to_next_discount()} Charyzmy."
                )
            else:
                await self.send("Rabat sklepowy osiągnął maksimum.")
            await self.send(
                f"Limit drużyny jako lider: {c.party_capacity()} osób."
            )
            await self.send(
                f"Do następnego miejsca w drużynie: "
                f"{c.charisma_to_next_party_slot()} Charyzmy."
            )
            await self.send(
                "Charyzma jest szóstą normalną statystyką i ma własny niezależny EXP oraz próg. "
                "Udana sprzedaż przyznaje dodatkowy EXP Charyzmy zależny od wartości transakcji."
            )

    def charisma_sale_xp(self, sale_value_silver, units=1):
            """v0.19: handel także korzysta z Global Progression Generatora."""
            value = max(1, int(sale_value_silver or 0))
            units = max(1, int(units or 1))
            level = max(1, int(self.character.charisma))
            normal_stat_gain = generator_core_v027.axis_gain("stat", level, 1.0)
            value_factor = max(0.50, min(4.0, 0.55 + math.log10(value + 10) * 0.28))
            bulk_factor = max(1.0, min(1.8, 1.0 + math.log2(units + 1) * 0.08))
            gain = int(round(max(2.0, normal_stat_gain * 0.12 * value_factor * bulk_factor)))
            return min(V019_SAFE_INT, max(2, gain))

    async def gain_charisma_from_sale(self, sale_value_silver, units=1):
            old_discount = self.character.shop_discount_percent()
            old_capacity = self.character.party_capacity()
            xp = self.apply_double_xp(self.charisma_sale_xp(sale_value_silver, units=units))
            for message in self.character.add_stat_progress(xp, targets=("charisma",)):
                await self.send(message)
            new_discount = self.character.shop_discount_percent()
            new_capacity = self.character.party_capacity()
            if new_discount > old_discount:
                await self.send(
                    f"Nowy rabat sklepowy: {new_discount} procent."
                )
            if new_capacity > old_capacity:
                await self.send(
                    f"Nowy limit drużyny jako lider: {new_capacity} osób."
                )

    def bank_here(self):
            return self.character.room_id == BANK_ROOM

    def bank_currency_name(self, currency):
            if currency == "mithril":
                return "mithril"
            if currency == "gold":
                return "złota"
            return "srebra"

    def normalize_bank_currency(self, raw):
            value = normalize_lookup_text(raw)
            if value in ("silver", "srebro", "srebra", "srebrnych", "s"):
                return "silver"
            if value in ("gold", "zloto", "złoto", "zlota", "złota", "g"):
                return "gold"
            if value in ("mithril", "mithrilu", "m"):
                return "mithril"
            if value in ("moneta", "monety", "monet", "coins", "coin"):
                return "silver"
            return None

    def bank_amount_to_silver(self, amount, currency):
            amount = max(0, int(amount))
            if currency == "gold":
                return amount * SILVER_PER_GOLD
            if currency == "mithril":
                return amount * SILVER_PER_MITHRIL
            return amount

    async def show_bank(self):
            if not self.bank_here():
                await self.send(
                    "Bank Dusz obsługuje Bankier Aldren na Rynku. "
                    "Wpisz prowadz bank."
                )
                return

            row = self.server.db.bank_balance(
                self.account_id
            )
            await self.send("BANK DUSZ")
            await self.send(
                "Saldo: "
                + currency_reading_text(
                    row["silver"], row["gold"], row["mithril"],
                    full_names=True, include_zero=True,
                )
                + "."
            )

            items = self.server.db.bank_items(
                self.account_id
            )
            if not items:
                await self.send(
                    "Skrytka przedmiotów: pusta."
                )
            else:
                await self.send("Skrytka przedmiotów:")
                for item_row in items:
                    item = ITEMS.get(
                        item_row["item_id"],
                        {"name": item_row["item_id"]},
                    )
                    await self.send(
                        f"{item['name']} x"
                        f"{item_row['quantity']}."
                    )

            await self.send(
                "Komendy: bank wplac <ile> [srebra|zlota|mithril], "
                "bank wyplac <ile> [srebra|zlota|mithril], "
                "bank wplac wszystko, bank wyplac wszystko, "
                "bank wloz <przedmiot> [ile], "
                "bank wyjmij <przedmiot> [ile]."
            )

    async def bank_deposit_currency(self, amount, currency):
            amount = int(amount)
            if amount <= 0:
                await self.send(
                    "Kwota wpłaty musi być większa od zera."
                )
                return False

            wallet = self.character_wallet_silver_value()
            if wallet < amount:
                await self.send(
                    "Nie masz takiej wartości. Masz "
                    + currency_reading_text(wallet, 0, 0) + "."
                )
                return False

            if not self.server.db.change_bank_currency(
                self.account_id, currency, amount
            ):
                await self.send("Nie udało się wykonać wpłaty.")
                return False

            self.character.silver = wallet - amount
            self.character.gold = 0
            self.character.mithril = 0
            self.server.db.save_character(self.character)
            await self.send(
                "Wpłacasz " + currency_reading_text(amount, 0, 0)
                + " do Banku Dusz."
            )
            return True

    async def bank_withdraw_currency(self, amount, currency):
            amount = int(amount)
            if amount <= 0:
                await self.send(
                    "Kwota wypłaty musi być większa od zera."
                )
                return False

            balance = self.server.db.bank_balance(
                self.account_id
            )
            available = legacy_currency_to_coins(
                balance["silver"], balance["gold"], balance["mithril"]
            )
            if available < amount:
                await self.send(
                    "Na koncie nie ma takiej wartości. Saldo: "
                    + currency_reading_text(available, 0, 0) + "."
                )
                return False

            if not self.server.db.change_bank_currency(
                self.account_id, currency, -amount
            ):
                await self.send("Nie udało się wykonać wypłaty.")
                return False

            self.character.silver = self.character_wallet_silver_value() + amount
            self.character.gold = 0
            self.character.mithril = 0
            self.server.db.save_character(self.character)
            await self.send(
                "Wypłacasz " + currency_reading_text(amount, 0, 0)
                + " z Banku Dusz."
            )
            return True

    def split_bank_item_quantity(self, raw):
            raw = str(raw or "").strip()
            if not raw:
                return "", 1

            parts = raw.split()
            quantity = 1

            if (
                len(parts) > 1
                and parts[-1].isdigit()
            ):
                quantity = max(1, int(parts[-1]))
                raw = " ".join(parts[:-1]).strip()

            return raw, quantity

    async def bank_deposit_item(self, raw):
            query, quantity = self.split_bank_item_quantity(
                raw
            )
            if not query:
                await self.send(
                    "Użycie: bank wloz <przedmiot> [ilość]."
                )
                return False

            owned = {
                item_id: item
                for item_id, item in ITEMS.items()
                if self.server.db.item_qty(
                    self.account_id, item_id
                ) > 0
            }
            found = find_by_name(owned, query)
            if not found:
                await self.send(
                    "Nie masz takiego przedmiotu w inventory."
                )
                return False

            item_id, item = found

            if is_character_bound_item(item_id):
                await self.send(
                    f"{item['name']} jest przypisany do tej postaci. "
                    "Nie można go oddać, wyrzucić ani schować w Banku Dusz."
                )
                return False

            current = self.server.db.item_qty(
                self.account_id, item_id
            )

            equipped_ids = {
                row["item_id"]
                for row in self.server.db.equipment(
                    self.account_id
                )
            }
            if item_id in equipped_ids:
                await self.send(
                    f"{item['name']} jest aktualnie założony. "
                    "Nie można schować założonego przedmiotu w banku."
                )
                return False

            if current < quantity:
                await self.send(
                    f"Masz tylko {current} sztuk "
                    f"{item['name']}."
                )
                return False

            if not self.server.db.remove_item(
                self.account_id, item_id, quantity
            ):
                return False
            self.server.db.add_bank_item(
                self.account_id, item_id, quantity
            )

            await self.send(
                f"Do skrytki trafia {item['name']} x{quantity}."
            )
            return True

    async def bank_withdraw_item(self, raw):
            query, quantity = self.split_bank_item_quantity(
                raw
            )
            if not query:
                await self.send(
                    "Użycie: bank wyjmij <przedmiot> [ilość]."
                )
                return False

            rows = self.server.db.bank_items(
                self.account_id
            )
            stored = {
                row["item_id"]: ITEMS.get(
                    row["item_id"],
                    {"name": row["item_id"]},
                )
                for row in rows
            }
            found = find_by_name(stored, query)
            if not found:
                await self.send(
                    "Nie ma takiego przedmiotu w skrytce."
                )
                return False

            item_id, item = found
            current = self.server.db.bank_item_qty(
                self.account_id, item_id
            )
            if current < quantity:
                await self.send(
                    f"W skrytce jest tylko {current} sztuk "
                    f"{item['name']}."
                )
                return False

            if not self.server.db.remove_bank_item(
                self.account_id, item_id, quantity
            ):
                return False
            self.server.db.add_item(
                self.account_id, item_id, quantity
            )

            await self.send(
                f"Wyjmujesz ze skrytki "
                f"{item['name']} x{quantity}."
            )
            return True

    async def handle_bank(self, raw):
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz korzystać z banku podczas walki."
                )
                return

            if not self.bank_here():
                await self.send(
                    "Bank Dusz znajduje się na Rynku u Bankiera Aldrena. "
                    "Wpisz prowadz bank."
                )
                return

            raw = str(raw or "").strip()
            normalized = normalize_lookup_text(raw)

            if not normalized or normalized in (
                "saldo",
                "stan",
                "list",
                "lista",
            ):
                await self.show_bank()
                return

            parts = raw.split(maxsplit=1)
            action = normalize_lookup_text(parts[0])
            rest = parts[1] if len(parts) > 1 else ""
            normalized_rest = normalize_lookup_text(rest)

            if action in ("wplac", "deposit"):
                if normalized_rest == "wszystko":
                    deposited_any = False
                    amount = self.character_wallet_silver_value()
                    if amount > 0:
                        self.character.silver = amount
                        self.character.gold = 0
                        self.character.mithril = 0
                        await self.bank_deposit_currency(amount, "silver")
                        deposited_any = True
                    if not deposited_any:
                        await self.send(
                            "Nie masz waluty do wpłacenia."
                        )
                    return

                tokens = rest.split()
                if len(tokens) not in (1, 2) or not tokens[0].isdigit():
                    await self.send("Użycie: bank wplac <ile> [srebra|zlota|mithril].")
                    return
                currency = self.normalize_bank_currency(tokens[1]) if len(tokens) == 2 else "silver"
                if not currency:
                    await self.send("Nieznany nominał. Użyj: srebra, zlota albo mithril.")
                    return
                amount = self.bank_amount_to_silver(int(tokens[0]), currency)
                await self.bank_deposit_currency(amount, "silver")
                return

            if action in ("wyplac", "withdraw"):
                if normalized_rest == "wszystko":
                    balance = self.server.db.bank_balance(
                        self.account_id
                    )
                    withdrew_any = False
                    amount = legacy_currency_to_coins(
                        balance["silver"], balance["gold"], balance["mithril"]
                    )
                    if amount > 0:
                        await self.bank_withdraw_currency(amount, "silver")
                        withdrew_any = True
                    if not withdrew_any:
                        await self.send(
                            "Konto bankowe nie ma waluty do wypłacenia."
                        )
                    return

                tokens = rest.split()
                if len(tokens) not in (1, 2) or not tokens[0].isdigit():
                    await self.send("Użycie: bank wyplac <ile> [srebra|zlota|mithril].")
                    return
                currency = self.normalize_bank_currency(tokens[1]) if len(tokens) == 2 else "silver"
                if not currency:
                    await self.send("Nieznany nominał. Użyj: srebra, zlota albo mithril.")
                    return
                amount = self.bank_amount_to_silver(int(tokens[0]), currency)
                await self.bank_withdraw_currency(amount, "silver")
                return

            if action in (
                "wloz",
                "schowaj",
                "put",
                "deposititem",
            ):
                await self.bank_deposit_item(rest)
                return

            if action in (
                "wyjmij",
                "wez",
                "take",
                "withdrawitem",
            ):
                await self.bank_withdraw_item(rest)
                return

            await self.send(
                "Użycie: bank; bank wplac 100 srebra; bank wplac 5 zlota; bank wplac 1 mithril; "
                "bank wyplac 100 srebra; bank wplac wszystko; "
                "bank wyplac wszystko; bank wloz <przedmiot> [ile]; "
                "bank wyjmij <przedmiot> [ile]."
            )

    async def show_money(self):
            self.server.db.save_character(self.character)
            c = self.character
            await self.send(
                "Masz "
                + currency_reading_text(
                    c.silver, c.gold, c.mithril,
                    full_names=True, include_zero=True,
                )
                + "."
            )
            await self.send(
                "To jedno wspólne saldo. 100 srebra = 1 złoto, a 1 000 000 złota = 1 mithril."
            )
