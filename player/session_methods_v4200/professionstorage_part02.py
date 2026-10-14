# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
def store_profession_resource(self, item_id, quantity=1):
        quantity = max(1, int(quantity))
        if item_id in FISH_STORAGE_IDS:
            self.server.db.add_storage_item(
                self.account_id, "net", item_id, quantity
            )
            return "net"
        if item_id in MINING_STORAGE_IDS:
            self.server.db.add_storage_item(
                self.account_id, "bag", item_id, quantity
            )
            return "bag"
        if item_id in WOOD_STORAGE_IDS:
            self.server.db.add_storage_item(
                self.account_id, "woodpile", item_id, quantity
            )
            return "woodpile"
        if item_id in HERB_STORAGE_IDS:
            self.server.db.add_storage_item(
                self.account_id, "herbbag", item_id, quantity
            )
            return "herbbag"
        raise ValueError(
            f"Przedmiot {item_id} nie jest surowcem obsługiwanej profesji."
        )


def category_ids(self, query, container=None):
        q = query.strip().lower()
        if q in ("fish", "ryba", "ryby"):
            return set(FISH_STORAGE_IDS)
        if q in ("ore", "ruda", "rudy"):
            return set(ORE_STORAGE_IDS)
        if q in ("wood", "drewno", "pnie", "pień", "pien"):
            return set(WOOD_STORAGE_IDS)
        if q in ("herb", "herbs", "ziolo", "zioło", "ziola", "zioła"):
            return set(HERB_STORAGE_IDS)
        if container == "net":
            allowed = FISH_STORAGE_IDS
        elif container == "bag":
            allowed = MINING_STORAGE_IDS
        elif container == "woodpile":
            allowed = WOOD_STORAGE_IDS
        elif container == "herbbag":
            allowed = HERB_STORAGE_IDS
        elif container == "craftbox":
            allowed = CRAFT_MATERIAL_STORAGE_IDS
        else:
            allowed = (
                FISH_STORAGE_IDS | ORE_RESOURCE_IDS | WOOD_RESOURCE_IDS | HERB_RESOURCE_IDS
                | set(CRAFT_MATERIAL_STORAGE_IDS)
            )

        found = find_by_name(
            {item_id: ITEMS[item_id] for item_id in allowed},
            query
        )
        return {found[0]} if found else set()


def profession_storage_definition(self, container):
        definitions = {
            "net": {
                "ids": FISH_STORAGE_IDS,
                "count_label": "ryb",
                "type_label": "gatunków",
                "value_label": "całej siatki",
            },
            "bag": {
                "ids": MINING_STORAGE_IDS,
                "count_label": "urobku",
                "type_label": "rodzajów",
                "value_label": "całej Sakwy Górnika",
            },
            "woodpile": {
                "ids": WOOD_STORAGE_IDS,
                "count_label": "sztuk drewna",
                "type_label": "rodzajów",
                "value_label": "całego stosu drewna",
            },
            "herbbag": {
                "ids": HERB_STORAGE_IDS,
                "count_label": "ziół",
                "type_label": "rodzajów",
                "value_label": "całej torby zielarskiej",
                "show_value": True,
            },
            "craftbox": {
                "ids": CRAFT_MATERIAL_STORAGE_IDS,
                "count_label": "materiałów rzemieślniczych",
                "type_label": "rodzajów",
                "value_label": "Szkatułki Rzemieślniczej",
                "show_value": False,
            },
        }
        return definitions.get(container)


def profession_storage_summary(self, container, rows=None):
        definition = self.profession_storage_definition(container)
        if not definition:
            return {
                "count": 0,
                "types": 0,
                "silver": 0,
                "gold": 0,
                "mithril": 0,
            }

        if rows is None:
            rows = self.server.db.storage_rows(
                self.account_id, container
            )

        total_count = 0
        total_silver = 0
        total_gold = 0
        total_mithril = 0
        type_count = 0

        allowed_ids = definition["ids"]

        for row in rows:
            item_id = row["item_id"]
            if item_id not in allowed_ids:
                continue

            quantity = max(0, int(row["quantity"]))
            if quantity <= 0:
                continue

            type_count += 1
            total_count += quantity

            item = ITEMS.get(item_id, {})
            # v0.19: wartość torby korzysta z tego samego generatora co realna sprzedaż.
            total_silver += profession_resource_market_value_v1148(
                item_id, item, category="ore" if container == "bag" else None
            ) * quantity

        return {
            "count": total_count,
            "types": type_count,
            "silver": total_silver,
            "gold": total_gold,
            "mithril": total_mithril,
        }


async def show_craftbox_v0925(self, args=""):
        rows = list(self.server.db.storage_rows(self.account_id, "craftbox"))
        norm = normalize_lookup_text(args)
        if not norm or norm in ("info", "lista", "list", "kategorie", "categories"):
            counts = {key:0 for key in V0925_CRAFTBOX_CATEGORIES}
            types = {key:set() for key in V0925_CRAFTBOX_CATEGORIES}
            for row in rows:
                cat=v0925_craftbox_category(str(row["item_id"]))
                counts[cat]=counts.get(cat,0)+int(row["quantity"])
                types.setdefault(cat,set()).add(str(row["item_id"]))
            await self.send("SZKATUŁKA RZEMIEŚLNICZA — KATEGORIE")
            for key,label in V0925_CRAFTBOX_CATEGORIES.items():
                await self.send(f"{label}: {counts.get(key,0)} sztuk, {len(types.get(key,set()))} rodzajów.")
            await self.send("Użyj: szkatułka kowalstwo / jubilerstwo / alchemia / runy / salvage / inne.")
            return
        cat=V0925_CRAFTBOX_ALIASES.get(norm)
        if cat is None:
            await self.send("Nie znam takiej kategorii Szkatułki. Dostępne: kowalstwo, jubilerstwo, alchemia, runy, salvage, inne.")
            return
        filtered=[row for row in rows if v0925_craftbox_category(str(row["item_id"]))==cat]
        await self.send(f"SZKATUŁKA — {V0925_CRAFTBOX_CATEGORIES[cat]}:")
        if not filtered:
            await self.send("Pusto.")
            return
        total=0
        for row in filtered:
            item=ITEMS.get(str(row["item_id"]), {"name":player_item_display_name_v0335(str(row["item_id"]))})
            qty=int(row["quantity"]); total+=qty
            await self.send(f"{item['name']} x{qty}.")
        await self.send(f"Łącznie w tej kategorii: {total} sztuk, {len(filtered)} rodzajów.")


async def show_container(self, container):
        label = self.container_label(container)
        rows = self.server.db.storage_rows(
            self.account_id, container
        )
        await self.send(label + ":")

        definition = self.profession_storage_definition(container)

        if not rows:
            await self.send("Pusto.")
            if definition:
                await self.send(
                    f"Łącznie {definition['count_label']}: 0. "
                    f"{definition['type_label'].capitalize()}: 0."
                )
                if definition.get("show_value", True):
                    await self.send(
                        "Szacowany zarobek ze sprzedaży "
                        f"{definition['value_label']}: {currency_price_text(0)}."
                    )
            return

        for row in rows:
            item = ITEMS.get(
                row["item_id"],
                {"name": row["item_id"]},
            )
            await self.send(
                f"{item['name']} x{row['quantity']}."
            )

        if definition:
            summary = self.profession_storage_summary(
                container, rows
            )
            await self.send(
                f"Łącznie {definition['count_label']}: "
                f"{summary['count']}. "
                f"{definition['type_label'].capitalize()}: "
                f"{summary['types']}."
            )
            if definition.get("show_value", True):
                await self.send(
                    "Szacowany zarobek ze sprzedaży "
                    f"{definition['value_label']}: "
                    f"{self.profession_storage_value_text(summary)}."
                )
            else:
                await self.send(
                    "Materiały i oszlifowane klejnoty w Szkatułce są chronione przed sell/sell all "
                    "i są pobierane automatycznie przez receptury."
                )


async def put_in_container(self, args):
        # Przykłady:
        # wloz ryba siatka
        # put fish net
        # wloz ruda sakwa
        parts = args.split()
        if len(parts) < 2:
            await self.send(
                "Użycie: wloz ryba siatka / put fish net / "
                "wloz ruda sakwa / put ore bag."
            )
            return

        container = self.normalize_container(parts[-1])
        if not container:
            await self.send("Podaj na końcu: siatka/net, sakwa/bag, stos/woodpile albo ziola/herbbag.")
            return
        if container == "craftbox":
            await self.send(
                "Szkatułka Rzemieślnicza działa automatycznie. Materiały rzemieślnicze i oszlifowane klejnoty jubilerskie "
                "trafiają do niej przy zdobyciu, a receptury pobierają je bez wyjmowania."
            )
            return

        query = " ".join(parts[:-1])
        ids = self.category_ids(query, container)
        if not ids:
            await self.send("Nie rozpoznaję takiego surowca.")
            return

        expected = {
            "net": FISH_RESOURCE_IDS,
            "bag": ORE_RESOURCE_IDS,
            "woodpile": WOOD_RESOURCE_IDS,
            "herbbag": HERB_RESOURCE_IDS,
        }[container]
        ids &= expected
        if not ids:
            await self.send(
                "Do Siatki wkłada się ryby, do Sakwy rudy, na Stos drewno, a do Torby Zielarskiej zioła."
            )
            return

        moved = []
        for item_id in sorted(ids):
            qty = self.server.db.item_qty(self.account_id, item_id)
            if qty <= 0:
                continue
            self.server.db.remove_item(self.account_id, item_id, qty, commit=False)
            self.server.db.add_storage_item(
                self.account_id, container, item_id, qty, commit=False
            )
            moved.append((item_id, qty))
        if moved:
            self.server.db.conn.commit()

        if not moved:
            await self.send("Nie masz takich surowców w zwykłym ekwipunku.")
            return

        for item_id, qty in moved:
            await self.send(
                f"Wkładasz {ITEMS[item_id]['name']} x{qty} do "
                f"{self.container_label(container)}."
            )


async def take_from_container(self, args):
        parts = args.split()
        if len(parts) < 2:
            await self.send(
                "Użycie: wyjmij przedmiot siatka/sakwa/stos albo take item net/bag/woodpile."
            )
            return

        container = self.normalize_container(parts[-1])
        if not container:
            await self.send("Podaj na końcu: siatka/net, sakwa/bag, stos/woodpile albo ziola/herbbag.")
            return
        if container == "craftbox":
            await self.send(
                "Materiałów nie trzeba wyjmować ze Szkatułki Rzemieślniczej. "
                "Receptury pobierają je z niej automatycznie."
            )
            return

        query = " ".join(parts[:-1])
        ids = self.category_ids(query, container)
        if not ids:
            await self.send("Nie rozpoznaję takiego surowca.")
            return

        moved = []
        for item_id in sorted(ids):
            qty = self.server.db.storage_qty(
                self.account_id, container, item_id
            )
            if qty <= 0:
                continue
            self.server.db.remove_storage_item(
                self.account_id, container, item_id, qty, commit=False
            )
            self.server.db.add_item(self.account_id, item_id, qty, commit=False)
            moved.append((item_id, qty))
        if moved:
            self.server.db.conn.commit()

        if not moved:
            await self.send("Nie ma tego surowca w tym pojemniku.")
            return

        for item_id, qty in moved:
            await self.send(
                f"Wyjmujesz {ITEMS[item_id]['name']} x{qty} z "
                f"{self.container_label(container)}."
            )


async def grant_tool_reward_xp(
    self, tool_type, tool_xp, *, content_level=None
):
        if not self.valid_tool_type(tool_type):
            raise ValueError(
                f"Nieznany typ narzędzia: {tool_type}"
            )

        row = self.server.db.tool(
            self.account_id, tool_type
        )
        level = int(row["level"])
        raw_tool_xp=max(0,int(tool_xp or 0))
        stage=max(
            1,
            min(PROFESSION_MAX_LEVEL,int(content_level or level or 1)),
        )
        _base_prof,_base_tool=self.profession_content_xp_floor_v11342(
            0,0,stage,tool_type
        )
        authored_tool_mult=self.profession_authored_xp_multiplier_v11343(
            max(raw_tool_xp,_base_tool),_base_tool
        )
        tool_xp = v0190_scaled_gain(raw_tool_xp, level, "tool", 12)
        if content_level is not None:
            _prof_mult,_tool_mult=self.profession_content_xp_multiplier_v11342(
                stage,tool_type
            )
            tool_xp=max(
                0,
                int(round(tool_xp*_tool_mult*authored_tool_mult)),
            )
        else:
            tool_xp=max(0,int(round(tool_xp*authored_tool_mult)))
        tool_xp = self.apply_double_xp(tool_xp)
        self.session_summary_add("tool_xp", tool_xp, tool_type)
        xp = int(row["xp"]) + tool_xp
        uses = int(row["uses"])

        tool_name = {
            "fishing": "Wędka",
            "mining": "Kilof",
            "woodcutting": "Piła",
            "crafting": "Młot Rzemieślniczy",
            "cooking": "Nóż Kucharski",
            "herbalism": "Sierp Zielarski",
            "alchemy": "Moździerz Alchemiczny",
            "jewelcrafting": "Szczypce Jubilerskie",
            "tailoring": "Zestaw Krawiecki",
            "leatherworking": "Nóż Garbarski",
            "carpentry": "Narzędzia Ciesielskie",
            "enchanting": "Fokus Runiczny",
            "archaeology": "Pędzel Archeologa",
            "cartography_profession": "Kompas Mierniczy",
        }[tool_type]

        await self.send(
            f"{tool_name}: nagroda +{tool_xp} XP."
        )

        cap = tool_max_level(tool_type)
        while level < cap:
            needed = self.tool_xp_to_next(
                level, tool_type
            )
            if xp < needed:
                break
            xp -= needed
            level += 1
            await self.send(
                f"{tool_name} osiąga poziom {level}."
            )

        if level >= cap:
            level = cap
            xp = 0

        self.server.db.save_tool(
            self.account_id,
            tool_type,
            level,
            xp,
            uses,
        )
        if level>=cap:
            await self.send(f"{tool_name}: poziom {level}, XP maksimum.")
        else:
            await self.send(
                f"{tool_name}: poziom {level}, XP {xp} z "
                f"{self.tool_xp_to_next(level,tool_type)}."
            )

