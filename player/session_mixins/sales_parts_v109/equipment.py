# -*- coding: utf-8 -*-
"""v109: sprzedaż — equipment; identyczne metody względem v108."""
from .dependencies import *

class SalesEquipmentV109Mixin:

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
                if self.item_is_protected_v1280(item_id):
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
                    f"Cena jednej: {currency_price_text(values['silver'], values['gold'], values['mithril'])}."
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
