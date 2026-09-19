# -*- coding: utf-8 -*-
"""Soulbound v0.30.47 Session mixin: professions_storage_guide."""

class SessionProfessionsStorageGuideMixin:
    def profession_xp_to_next(self, level, profession=None):
            max_level = (
                profession_max_level(profession)
                if profession is not None
                else PROFESSION_MAX_LEVEL
            )
            if level >= max_level:
                return 0
            return v0190_requirement("profession", level)

    def tool_xp_to_next(self, level, tool_type=None):
            max_level = tool_max_level(tool_type)
            if level >= max_level:
                return 0

            return v0190_requirement("tool", level)

    def valid_tool_type(self, tool_type):
            return tool_type in (
                "fishing",
                "mining",
                "woodcutting",
                "crafting",
                "cooking",
                "herbalism",
                "alchemy",
                "jewelcrafting",
            )

    def tool_progress_state(self):
            result = {}
            for tool_type in (
                "fishing",
                "mining",
                "woodcutting",
                "crafting",
                "cooking",
                "herbalism",
                "alchemy",
                "jewelcrafting",
            ):
                row = self.server.db.tool(self.account_id, tool_type)
                result[tool_type] = (
                    int(row["level"]),
                    int(row["xp"]),
                    int(row["uses"]),
                )
            return result

    def grant_profession_progress(self, profession, prof_xp, tool_type, tool_xp):
            if not self.valid_tool_type(tool_type):
                raise ValueError(f"Nieznany typ narzędzia: {tool_type}")

            _guild_pct=self.guild_bonus_percent_v0926()
            prow = self.server.db.profession(
                self.account_id, profession
            )
            profession_cap = profession_max_level(profession)
            plevel = int(prow["level"])
            trow_preview = self.server.db.tool(self.account_id, tool_type)
            tlevel_preview = int(trow_preview["level"])
            legacy_prof_xp = max(0, int(prof_xp)) * PROFESSION_XP_GAIN_MULTIPLIER
            actual_prof_xp = v0190_scaled_gain(legacy_prof_xp, plevel, "profession", 40)
            tool_xp = v0190_scaled_gain(tool_xp, tlevel_preview, "tool", 12)
            actual_prof_xp=max(0,int(round(actual_prof_xp*(1.0+_guild_pct/100.0))))
            tool_xp=max(0,int(round(tool_xp*(1.0+_guild_pct/100.0))))
            _title_pct = self.v0260_profession_xp_bonus_percent(profession, tool_type)
            if _title_pct:
                actual_prof_xp=max(0,int(round(actual_prof_xp*(1.0+_title_pct/100.0))))
                tool_xp=max(0,int(round(tool_xp*(1.0+_title_pct/100.0))))
            actual_prof_xp = self.apply_double_xp(actual_prof_xp)
            tool_xp = self.apply_double_xp(tool_xp)
            old_profession_rank = profession_rank(
                plevel, profession
            )
            pxp = int(prow["xp"]) + actual_prof_xp
            actions = int(prow["actions"]) + 1
            messages = [f"{profession}: +{actual_prof_xp} XP."]

            while plevel < profession_cap:
                needed = self.profession_xp_to_next(
                    plevel, profession
                )
                if pxp < needed:
                    break
                pxp -= needed
                plevel += 1
                messages.append(f"{profession} osiąga poziom {plevel}.")
            if plevel >= profession_cap:
                plevel = profession_cap
                pxp = 0
            self.server.db.save_profession(
                self.account_id, profession, plevel, pxp, actions
            )

            new_profession_rank = profession_rank(
                plevel, profession
            )
            max_profession_rank = profession_max_rank(
                profession
            )
            if new_profession_rank > old_profession_rank:
                messages.append(
                    f"{profession}: awansujesz na Rangę {new_profession_rank} "
                    f"z {max_profession_rank}: "
                    f"{profession_rank_name(profession, plevel)}."
                )

            trow = self.server.db.tool(self.account_id, tool_type)
            tlevel = int(trow["level"])
            old_tool_tier = tool_tier(tlevel)
            txp = int(trow["xp"]) + tool_xp
            uses = int(trow["uses"]) + 1
            tool_name = {
                "fishing": "Wędka",
                "mining": "Kilof",
                "woodcutting": "Piła",
                "crafting": "Młot Rzemieślniczy",
                "cooking": "Nóż Kucharski",
                "herbalism": "Sierp Zielarski",
                "alchemy": "Moździerz Alchemiczny",
                "jewelcrafting": "Szczypce Jubilerskie",
            }.get(tool_type, tool_type)
            messages.append(f"{tool_name}: +{tool_xp} XP narzędzia.")

            tool_level_cap = tool_max_level(tool_type)
            while tlevel < tool_level_cap:
                needed = self.tool_xp_to_next(tlevel, tool_type)
                if txp < needed:
                    break
                txp -= needed
                tlevel += 1
                messages.append(f"{tool_name} osiąga level {tlevel}.")
            if tlevel >= tool_level_cap:
                tlevel = tool_level_cap
                txp = 0
            self.server.db.save_tool(
                self.account_id, tool_type, tlevel, txp, uses
            )

            new_tool_tier = tool_tier(tlevel)
            if new_tool_tier > old_tool_tier:
                messages.append(
                    f"{tool_name} awansuje na Tier {new_tool_tier} z {TOOL_MAX_TIER}: "
                    f"{tool_tier_name(tool_type, tlevel)}. "
                    f"Szansa na dodatkowy urobek: "
                    f"{int(tool_tier_bonus_chance(tlevel) * 100)} procent."
                )

            _char_stage=max(1,min(400,max(plevel,tlevel)))
            _char_gain=generator_core_v027.axis_gain("character",_char_stage,0.35)
            messages.extend(self.add_character_xp_with_event(_char_gain))
            self.server.db.save_character(self.character)
            return messages, plevel, tlevel

    def grant_tool_progress(self, tool_type, tool_xp):
            if not self.valid_tool_type(tool_type):
                raise ValueError(f"Nieznany typ narzędzia: {tool_type}")
            row = self.server.db.tool(self.account_id, tool_type)
            level = int(row["level"])
            old_tier = tool_tier(level)
            tool_xp = v0190_scaled_gain(tool_xp, level, "tool", 12)
            tool_xp = self.apply_double_xp(tool_xp)
            xp = int(row["xp"]) + max(0, int(tool_xp))
            uses = int(row["uses"]) + 1

            tool_name = {
                "fishing": "Wędka",
                "mining": "Kilof",
                "woodcutting": "Piła",
                "crafting": "Młot Rzemieślniczy",
                "cooking": "Nóż Kucharski",
                "herbalism": "Sierp Zielarski",
                "alchemy": "Moździerz Alchemiczny",
                "jewelcrafting": "Szczypce Jubilerskie",
            }.get(tool_type, tool_type)

            messages = [f"{tool_name}: +{tool_xp} XP narzędzia."]

            tool_level_cap = tool_max_level(tool_type)
            while level < tool_level_cap:
                needed = self.tool_xp_to_next(level, tool_type)
                if xp < needed:
                    break
                xp -= needed
                level += 1
                messages.append(f"{tool_name} osiąga level {level}.")

            if level >= tool_level_cap:
                level = tool_level_cap
                xp = 0

            self.server.db.save_tool(
                self.account_id, tool_type, level, xp, uses
            )

            new_tier = tool_tier(level)
            if new_tier > old_tier:
                if tool_type == "cooking":
                    bonus_name = "dodatkową potrawę"
                elif tool_type == "crafting":
                    bonus_name = "dodatkowy produkt receptury"
                else:
                    bonus_name = "dodatkowy urobek"
                messages.append(
                    f"{tool_name} awansuje na Tier {new_tier} z {TOOL_MAX_TIER}: "
                    f"{tool_tier_name(tool_type, level)}. "
                    f"Szansa na {bonus_name}: "
                    f"{int(tool_tier_bonus_chance(level) * 100)} procent."
                )

            _char_gain=generator_core_v027.axis_gain("character",max(1,min(400,level)),0.25)
            messages.extend(self.add_character_xp_with_event(_char_gain))
            self.server.db.save_character(self.character)
            return messages, level

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

    def migrate_raw_mining_gems_to_bag_v0867(self):
            moved = 0
            for item_id in RAW_GEM_IDS:
                qty = self.server.db.item_qty(self.account_id, item_id)
                if qty <= 0:
                    continue
                if self.server.db.remove_item(self.account_id, item_id, qty):
                    self.server.db.add_storage_item(
                        self.account_id, "bag", item_id, qty
                    )
                    moved += qty
            return moved

    def migrate_craft_materials_to_casket_v0915(self):
            moved = 0
            for item_id in CRAFT_MATERIAL_STORAGE_IDS:
                qty = self.server.db.item_qty(self.account_id, item_id)
                if qty <= 0:
                    continue
                if self.server.db.remove_item(self.account_id, item_id, qty):
                    self.server.db.add_storage_item(
                        self.account_id, "craftbox", item_id, qty
                    )
                    moved += qty
            return moved

    def container_label(self, container):
            return {
                "net": "Siatka na ryby",
                "bag": "Sakwa górnicza",
                "woodpile": "Stos drewna",
                "herbbag": "Torba Zielarska",
                "craftbox": "Szkatułka Rzemieślnicza",
            }.get(container, container)

    def normalize_container(self, token):
            t = token.strip().lower()
            if t in ("net", "siatka", "siatkę", "siatke"):
                return "net"
            if t in ("bag", "sakwa", "sakwe", "sakwę", "worek"):
                return "bag"
            if t in ("woodpile", "stos", "drewno", "sterta"):
                return "woodpile"
            if t in ("herbbag", "ziola", "zioła", "herbs", "torba"):
                return "herbbag"
            if t in ("craftbox", "szkatulka", "szkatułka", "materialy", "materiały"):
                return "craftbox"
            return None

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
                total_silver += v0190_resource_sale_coins(item_id, item) * quantity

            return {
                "count": total_count,
                "types": type_count,
                "silver": total_silver,
                "gold": total_gold,
                "mithril": total_mithril,
            }

    def fish_net_summary(self, rows=None):
            generic = self.profession_storage_summary(
                "net", rows
            )
            return {
                "fish": generic["count"],
                "species": generic["types"],
                "silver": generic["silver"],
                "gold": generic["gold"],
                "mithril": generic["mithril"],
            }

    def profession_storage_value_text(self, summary):
            return currency_reading_text(
                summary["silver"], summary["gold"], summary["mithril"]
            )

    def fish_net_value_text(self, summary):
            return self.profession_storage_value_text(summary)

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
                item=ITEMS.get(str(row["item_id"]), {"name":str(row["item_id"])})
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
                            f"{definition['value_label']}: 0 srebra."
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
                self.server.db.remove_item(self.account_id, item_id, qty)
                self.server.db.add_storage_item(
                    self.account_id, container, item_id, qty
                )
                moved.append((item_id, qty))

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
                    self.account_id, container, item_id, qty
                )
                self.server.db.add_item(self.account_id, item_id, qty)
                moved.append((item_id, qty))

            if not moved:
                await self.send("Nie ma tego surowca w tym pojemniku.")
                return

            for item_id, qty in moved:
                await self.send(
                    f"Wyjmujesz {ITEMS[item_id]['name']} x{qty} z "
                    f"{self.container_label(container)}."
                )

    async def grant_tool_reward_xp(self, tool_type, tool_xp):
            if not self.valid_tool_type(tool_type):
                raise ValueError(
                    f"Nieznany typ narzędzia: {tool_type}"
                )

            row = self.server.db.tool(
                self.account_id, tool_type
            )
            level = int(row["level"])
            tool_xp = v0190_scaled_gain(tool_xp, level, "tool", 12)
            tool_xp = self.apply_double_xp(tool_xp)
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
                    f"{tool_name} osiąga level {level}."
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

    async def grant_profession_reward_xp(self, profession, profession_xp, tool_type, tool_xp):
            if not self.valid_tool_type(tool_type):
                raise ValueError(f"Nieznany typ narzędzia: {tool_type}")

            _guild_pct=self.guild_bonus_percent_v0926()
            prow = self.server.db.profession(
                self.account_id, profession
            )
            profession_cap = profession_max_level(profession)
            plevel = int(prow["level"])
            trow_preview = self.server.db.tool(self.account_id, tool_type)
            tlevel_preview = int(trow_preview["level"])
            legacy_profession_xp = max(0, int(profession_xp)) * PROFESSION_XP_GAIN_MULTIPLIER
            actual_profession_xp = v0190_scaled_gain(legacy_profession_xp, plevel, "profession", 40)
            tool_xp = v0190_scaled_gain(tool_xp, tlevel_preview, "tool", 12)
            actual_profession_xp=max(0,int(round(actual_profession_xp*(1.0+_guild_pct/100.0))))
            tool_xp=max(0,int(round(tool_xp*(1.0+_guild_pct/100.0))))
            _title_pct = self.v0260_profession_xp_bonus_percent(profession, tool_type)
            if _title_pct:
                actual_profession_xp=max(0,int(round(actual_profession_xp*(1.0+_title_pct/100.0))))
                tool_xp=max(0,int(round(tool_xp*(1.0+_title_pct/100.0))))
            actual_profession_xp = self.apply_double_xp(actual_profession_xp)
            tool_xp = self.apply_double_xp(tool_xp)
            pxp = int(prow["xp"]) + actual_profession_xp
            actions = int(prow["actions"])

            await self.send(
                f"{profession}: nagroda +{actual_profession_xp} XP."
            )

            while plevel < profession_cap:
                needed = self.profession_xp_to_next(
                    plevel, profession
                )
                if pxp < needed:
                    break
                pxp -= needed
                plevel += 1
                await self.send(f"{profession} osiąga poziom {plevel}.")

            if plevel >= profession_cap:
                plevel = profession_cap
                pxp = 0

            self.server.db.save_profession(
                self.account_id, profession, plevel, pxp, actions
            )

            trow = self.server.db.tool(self.account_id, tool_type)
            tlevel = int(trow["level"])
            txp = int(trow["xp"]) + tool_xp
            uses = int(trow["uses"])
            tool_name = {
                "fishing": "Wędka",
                "mining": "Kilof",
                "woodcutting": "Piła",
                "crafting": "Młot Rzemieślniczy",
                "cooking": "Nóż Kucharski",
                "herbalism": "Sierp Zielarski",
                "alchemy": "Moździerz Alchemiczny",
                "jewelcrafting": "Szczypce Jubilerskie",
            }[tool_type]

            await self.send(f"{tool_name}: nagroda +{tool_xp} XP.")

            tool_level_cap = tool_max_level(tool_type)
            while tlevel < tool_level_cap:
                needed = self.tool_xp_to_next(tlevel, tool_type)
                if txp < needed:
                    break
                txp -= needed
                tlevel += 1
                await self.send(f"{tool_name} osiąga level {tlevel}.")

            if tlevel >= tool_level_cap:
                tlevel = tool_level_cap
                txp = 0

            self.server.db.save_tool(
                self.account_id, tool_type, tlevel, txp, uses
            )

    async def show_location(self):
            room = ROOMS[self.character.room_id]
            await self.send(
                f"Lokalizacja: {room['name']}. Strefa: {room['zone']}."
            )
            await self.show_exits()

    def normalize_room_query(self, value):
            text = str(value or "").strip().lower()
            text = text.replace("ł", "l").replace("Ł", "l")
            text = unicodedata.normalize("NFKD", text)
            text = "".join(
                ch for ch in text
                if not unicodedata.combining(ch)
            )
            text = text.replace("_", " ").replace("-", " ")
            text = re.sub(r"[^a-z0-9 ]+", " ", text)
            return " ".join(text.split())

    def room_search_aliases(self, room_id, room):
            aliases = {
                self.normalize_room_query(room_id),
                self.normalize_room_query(room_id.replace("_", " ")),
                self.normalize_room_query(room["name"]),
            }

            zone = self.normalize_room_query(room.get("zone", ""))
            name = self.normalize_room_query(room["name"])
            if zone and name:
                aliases.add(f"{zone} {name}")

            floor = crypt_floor_number(room_id)
            if floor:
                aliases.update({
                    f"krypta {floor}",
                    f"crypt {floor}",
                    f"pietro {floor}",
                    f"pietro krypty {floor}",
                    f"krypta pietro {floor}",
                    f"crypt floor {floor}",
                })

            astral_floor = astral_floor_number(room_id)
            if astral_floor is not None:
                aliases.update({
                    f"wieza {astral_floor}",
                    f"wieza astralna {astral_floor}",
                    f"astral {astral_floor}",
                    f"astralna wieza {astral_floor}",
                    f"poziom wiezy {astral_floor}",
                    f"astral floor {astral_floor}",
                })

            # Krótkie, naturalne warianty popularnych nazw.
            words = name.split()
            if len(words) > 1:
                aliases.add(" ".join(words[1:]))

            return {alias for alias in aliases if alias}

    def guide_zone_query_name(self, query):
            q = self.normalize_room_query(query)
            aliases = {
                "miasto": "miasto dusz",
                "gildia": "gildia dusz",
                "gory": "gory",
                "wioska": "wioska gorska",
                "wioska gorska": "wioska gorska",
                "laki": "laki zielarskie",
                "laka": "laki zielarskie",
                "podziemia": "podziemia",
                "trolle": "jaskinia trolli",
                "jaskinia trolli": "jaskinia trolli",
                "wieza astralna": "wieza astralna",
                "mityczna wieza astralna": "mityczna wieza astralna",
                "mityczna krypta": "mityczna krypta",
                "twierdza gigantow": "twierdza gigantow",
                "kopalnia glebinowa": "kopalnia glebinowa",
                "lasy": "loch profesyjny pradawny las",
                "pradawny las": "loch profesyjny pradawny las",
                "ogrod alchemika": "loch profesyjny ogrod alchemika",
                "zatopiona grota": "loch profesyjny zatopiona grota",
            }
            return aliases.get(q, q)

    def rooms_in_exact_zone(self, query):
            zone_query = self.guide_zone_query_name(query)
            matches = [
                room_id
                for room_id, room in ROOMS.items()
                if self.normalize_room_query(
                    room.get("zone", "")
                ) == zone_query
            ]
            return sorted(
                matches,
                key=lambda rid: self.normalize_room_query(
                    ROOMS[rid]["name"]
                ),
            )

    def find_room_matches(self, query):
            q = self.normalize_room_query(query)
            if not q:
                return []

            # Najpierw bezpieczne wejścia. Dzięki temu nazwa lochu nie
            # rozwija się do listy jego pięter.
            shortcut = GUIDE_DESTINATION_ALIASES.get(q)
            if shortcut and shortcut in ROOMS:
                return [shortcut]

            zone_matches = self.rooms_in_exact_zone(q)
            if zone_matches:
                return zone_matches

            # "wieza" jest celowo szerokim terenem:
            # zwykła i Mityczna Wieża Astralna.
            if q in ("wieza", "tower"):
                matches = []
                for zone_name in (
                    "Wieża Astralna",
                    "Mityczna Wieża Astralna",
                ):
                    matches.extend(
                        self.rooms_in_exact_zone(zone_name)
                    )
                if matches:
                    return list(dict.fromkeys(matches))

            # "jaskinia" jako szeroki teren pokazuje zarówno
            # Kryształową Jaskinię, jak i Jaskinię Trolli.
            if q in ("jaskinia", "cave"):
                matches = []
                for room_id in (
                    "cave_entrance",
                    "troll_cave_entrance",
                ):
                    if room_id in ROOMS:
                        matches.append(room_id)
                if matches:
                    return matches

            # Zapytania o piętra są sprowadzane do wejścia.
            crypt_match = re.fullmatch(
                r"(?:krypta|crypt|pietro|pietro krypty|krypta pietro|crypt floor)\s*(\d+)",
                q,
            )
            if crypt_match:
                floor = int(crypt_match.group(1))
                if floor >= 1:
                    return ["crypt_entrance"]
                return []

            astral_match = re.fullmatch(
                r"(?:wieza|wieza astralna|astral|astralna wieza|poziom wiezy|astral floor)\s*(\d+)",
                q,
            )
            if astral_match:
                floor = int(astral_match.group(1))
                if floor >= ASTRAL_MIN_FLOOR:
                    return ["astral_gate"]
                return []

            mine_match = re.fullmatch(
                r"(?:kopalnia|mine|poziom kopalni|kopalnia poziom|mine floor)\s*(\d+)",
                q,
            )
            if mine_match:
                floor = int(mine_match.group(1))
                if floor >= MINE_MIN_FLOOR:
                    return [mine_floor_id(MINE_MIN_FLOOR)]
                return []

            exact = []
            partial = []

            for room_id, room in ROOMS.items():
                aliases = self.room_search_aliases(room_id, room)
                if q in aliases:
                    exact.append(room_id)
                    continue
                if any(q in alias for alias in aliases):
                    partial.append(room_id)

            if exact:
                return sorted(
                    set(exact),
                    key=lambda rid: ROOMS[rid]["name"].lower(),
                )

            return sorted(
                set(partial),
                key=lambda rid: ROOMS[rid]["name"].lower(),
            )

    def find_room(self, query):
            matches = self.find_room_matches(query)
            return matches[0] if len(matches) == 1 else None

    async def show_guide_destinations(self, category=""):
            q = self.normalize_room_query(category)
            category_aliases = {
                "": "",
                "miasto": "miasto", "city": "miasto", "town": "miasto",
                "gildia": "gildia", "guild": "gildia", "teachers": "gildia", "nauczyciele": "gildia",
                "profesje": "profesje", "professions": "profesje", "crafting": "profesje",
                "eq": "eq", "ekwipunek": "eq", "sklepy eq": "eq", "equipment": "eq", "gear": "eq",
                "tereny": "tereny", "regions": "tereny", "regiony": "tereny", "zones": "tereny",
                "lochy": "lochy", "dungeons": "lochy", "dungeon": "lochy", "endgame": "lochy",
                "npc": "npc", "npcs": "npc", "postacie": "npc",
                "wszystko": "wszystko", "all": "wszystko", "pelna": "wszystko", "full": "wszystko",
            }
            selected = category_aliases.get(q)
            if selected is None:
                await self.send(
                    "Nie znam takiej kategorii. Dostępne: miasto, gildia, profesje, eq, tereny, lochy, npc, wszystko."
                )
                return

            if not selected:
                await self.send("PROWADZENIE / WALK — KATEGORIE")
                await self.send("1. miasto — ważne miejsca Miasta Dusz.")
                await self.send("2. gildia — sale 12 nauczycieli klas.")
                await self.send("3. profesje — mistrzowie, warsztaty i sklepy narzędzi.")
                await self.send("4. eq — sklepy z klasowym wyposażeniem.")
                await self.send("5. tereny — regiony świata.")
                await self.send("6. lochy — Krypta, Wieże, Kopalnie, Twierdza i lochy profesyjne.")
                await self.send("7. npc — nazwani NPC i ich lokalizacje.")
                await self.send("8. wszystko — pełna lista lokacji pogrupowana strefami.")
                await self.send("Użyj np. prowadz lista gildia albo walk list dungeons.")
                return

            if selected == "miasto":
                await self.send("PROWADZENIE — MIASTO DUSZ")
                rooms = [(rid, room) for rid, room in ROOMS.items() if room.get("zone") == "Miasto Dusz"]
                for room_id, room in sorted(rooms, key=lambda x: self.normalize_room_query(x[1]["name"])):
                    await self.send(f"{room['name']}: prowadz {room['name']}.")
                return

            if selected == "gildia":
                await self.send("PROWADZENIE — GILDIA I NAUCZYCIELE")
                teachers = [npc for npc in NPCS.values() if npc.get("teacher_class") and npc.get("room") in ROOMS]
                for npc in sorted(teachers, key=lambda x: self.normalize_room_query(x.get("teacher_class", ""))):
                    room = ROOMS[npc["room"]]
                    await self.send(f"{npc['teacher_class']}: {npc['name']}, {room['name']}. prowadz {npc['name']}.")
                return

            if selected == "profesje":
                await self.send("PROWADZENIE — PROFESJE")
                await self.send("Wędkarstwo: Szkoła Wędkarstwa i Mistrz Wędkarstwa Neris — walk Mistrz Wędkarstwa Neris; sklep/narzędzie u Rybaka Borysa — walk Rybak Borys.")
                await self.send("Górnictwo: Gildia Górników i Mistrz Górnictwa Kordan — walk Mistrz Górnictwa Kordan; Kilof i wejście do Kopalni u Górnika Torena — walk Górnik Toren.")
                await self.send("Drwalstwo: Leśniczówka i Mistrz Drwalstwa Oren — walk Mistrz Drwalstwa Oren; Obóz Drwala i Bran — walk Drwal Bran.")
                await self.send("Zielarstwo: Ogród Zielarski i Mistrzyni Zielarstwa Sena — walk Mistrzyni Zielarstwa Sena; Chata Zielarki i Liora — walk Zielarka Liora.")
                await self.send("Kowalstwo/Rzemiosło: Warsztat Rzemieślniczy i Haldor — walk Mistrz Rzemiosła Haldor; Kuźnia Dusz i Kowal Doran — walk Kowal Doran.")
                await self.send("Gotowanie: Kuchnia Błękitnego Płomienia i Kucharz Marcel — walk Kucharz Marcel.")
                await self.send("Alchemia: Laboratorium Alchemiczne i Mistrz Alchemii Orin — walk Mistrz Alchemii Orin; mikstury także w Aptece — walk apteka.")
                await self.send("Jubilerstwo: Pracownia Jubilerska i Jubilerka Mirella — walk Jubilerka Mirella.")
                await self.send("Możesz też wpisać np. walk profesje wedkarstwo, walk profesje gornictwo albo walk profesje alchemia.")
                return

            if selected == "eq":
                await self.send("PROWADZENIE — SKLEPY Z EQ KLASOWYM")
                for room_id, classes in sorted(CLASS_SHOP_CLASSES_BY_ROOM.items(), key=lambda row: self.normalize_room_query(ROOMS.get(row[0], {}).get("name", row[0]))):
                    if room_id not in ROOMS:
                        continue
                    seller_id = SHOP_SELLERS.get(room_id)
                    seller = NPCS.get(seller_id, {}) if seller_id else {}
                    seller_name = seller.get("name", ROOMS[room_id]["name"])
                    class_text = ", ".join(classes)
                    await self.send(
                        f"{class_text}: {seller_name}, {ROOMS[room_id]['name']}. "
                        f"walk {seller_name}."
                    )
                await self.send("Możesz też wpisać np. walk eq wojownik, walk eq mag albo walk sklep eq druid.")
                return

            if selected == "tereny":
                await self.send("PROWADZENIE — TERENY")
                zones = sorted({room.get("zone", "") for room in ROOMS.values() if room.get("zone")}, key=self.normalize_room_query)
                for zone in zones:
                    await self.send(f"{zone}: prowadz {zone}.")
                return

            if selected == "lochy":
                await self.send("PROWADZENIE — LOCHY I ENDGAME")
                entries = [
                    "Krypta: prowadz krypta.",
                    "Wieża Astralna: prowadz wieza astralna.",
                    "Kopalnia Głębinowa: prowadz kopalnia glebinowa.",
                    "Kryształowe Groty (bez Górnictwa): prowadz krysztalowe groty.",
                    "Mityczna Krypta: prowadz mityczna krypta.",
                    "Mityczna Wieża Astralna: prowadz mityczna wieza astralna.",
                    "Twierdza Gigantów: prowadz twierdza gigantow.",
                    "Zatopiona Grota: prowadz zatopiona grota.",
                    "Pradawny Las: prowadz pradawny las.",
                    "Ogród Alchemika: prowadz ogrod alchemika.",
                    "Jaskinia Trolli: prowadz jaskinia trolli.",
                ]
                for line in entries:
                    await self.send(line)
                await self.send("Prowadzenie zatrzymuje się przed wejściem. Piętra i wnętrze eksplorujesz samodzielnie.")
                return

            if selected == "npc":
                await self.send("PROWADZENIE — NPC")
                rows = []
                for npc in NPCS.values():
                    room_id = npc.get("room")
                    name = npc.get("name")
                    if name and room_id in ROOMS:
                        rows.append((name, ROOMS[room_id]["name"]))
                for name, room_name in sorted(set(rows), key=lambda x:self.normalize_room_query(x[0])):
                    await self.send(f"{name}: {room_name}. prowadz {name}.")
                return

            # Pełna lista pozostaje dostępna, ale nie zalewa NVDA domyślnie.
            await self.send("PROWADZENIE — PEŁNA LISTA")
            zones = {}
            for room_id, room in ROOMS.items():
                if room_id.startswith(("crypt_floor_", "astral_floor_", "mythic_crypt_floor_", "mythic_astral_floor_")):
                    continue
                zones.setdefault(room["zone"], []).append(room["name"])
            for zone in sorted(zones, key=self.normalize_room_query):
                names = sorted(set(zones[zone]), key=self.normalize_room_query)
                await self.send(f"{zone}: " + "; ".join(names) + ".")
            await self.send("Krypta: piętra 1-∞, generowane na żądanie.")
            await self.send(f"Wieża Astralna: od poziomu {ASTRAL_MIN_FLOOR} bez górnego limitu.")
            await self.send(f"Kopalnia Głębinowa: od poziomu {MINE_MIN_FLOOR} bez górnego limitu.")
            await self.send("Mityczna Wieża Astralna, Twierdza Gigantów i cztery lochy profesyjne: bez górnego limitu.")
            await self.send("Jeśli cel pasuje do kilku miejsc, wybierasz tylko jeden numer z jednej listy.")

    def guide_task_active(self):
            return bool(self.guide_task and not self.guide_task.done())

    def route_direction_name(self, direction):
            labels = {
                "north": "północ",
                "south": "południe",
                "east": "wschód",
                "west": "zachód",
                "up": "góra",
                "down": "dół",
            }
            return labels.get(direction, str(direction))

    def compact_route_directions(self, path):
            if not path:
                return "jesteś już na miejscu"
            runs = []
            last = None
            count = 0
            for direction, _next_room in path:
                if direction == last:
                    count += 1
                    continue
                if last is not None:
                    label = self.route_direction_name(last)
                    runs.append(f"{label} x{count}" if count > 1 else label)
                last = direction
                count = 1
            if last is not None:
                label = self.route_direction_name(last)
                runs.append(f"{label} x{count}" if count > 1 else label)
            return ", ".join(runs)

    def route_zone_sequence(self, start_room, path):
            room_ids = [start_room] + [next_room for _direction, next_room in path]
            zones = []
            for room_id in room_ids:
                zone = ROOMS.get(room_id, {}).get("zone", "")
                if zone and (not zones or zones[-1] != zone):
                    zones.append(zone)
            return zones

    def estimated_guide_seconds(self, path):
            return sum(self.movement_delay(direction, guided=True) for direction, _ in path)

    async def cancel_guide(self, announce=True, reason="Prowadzenie zatrzymane."):
            task = self.guide_task
            was_active = bool(task and not task.done())
            self.guide_choice_state = None
            if was_active and task is not asyncio.current_task():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            if self.guide_task is task:
                self.guide_task = None
            self.guiding = False
            self.guide_target_room = None
            self.guide_target_label = ""
            self.guide_target_is_npc = False
            self.guide_final_direction = None
            if announce:
                if was_active:
                    await self.send(reason)
                else:
                    await self.send("Prowadzenie nie jest aktywne.")
            return was_active

    async def show_guide_status(self):
            if not self.guide_task_active() or not self.guide_target_room:
                await self.send("Prowadzenie nie jest aktywne.")
                return
            target = self.guide_target_room
            path = self.shortest_path(self.character.room_id, target)
            if path is None:
                await self.send(
                    f"Prowadzenie aktywne do: {self.guide_target_label}, ale aktualnie nie da się wyliczyć pozostałej drogi."
                )
                return
            next_text = "brak, cel osiągnięty"
            if path:
                direction, next_room = path[0]
                next_text = (
                    f"{self.route_direction_name(direction)} do {ROOMS[next_room]['name']}"
                )
            await self.send(
                f"Prowadzenie aktywne. Teraz: {ROOMS[self.character.room_id]['name']}. "
                f"Cel: {self.guide_target_label}. Pozostało przejść do celu: {len(path)}. "
                f"Następny krok: {next_text}."
            )
            if (not self.guide_target_is_npc) and self.guide_final_direction:
                await self.send(
                    f"Dla zwykłej lokacji prowadzenie zatrzyma się przed celem; końcowy kierunek wykonasz ręcznie: {self.guide_final_direction}."
                )

    def _guide_task_finished(self, task):
            if self.guide_task is task:
                self.guide_task = None
            try:
                task.result()
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                print(
                    f"[GUIDE ERROR] {type(exc).__name__}: {exc}",
                    file=sys.stderr,
                    flush=True,
                )
                if not self.closed:
                    try:
                        asyncio.get_running_loop().create_task(
                            self.send("Prowadzenie zostało zatrzymane przez błąd nawigacji.")
                        )
                    except RuntimeError:
                        pass

    async def start_guide_task(self, args):
            normalized = self.normalize_room_query(args)
            if normalized in ("stop", "anuluj", "cancel", "przerwij", "zatrzymaj"):
                await self.cancel_guide(announce=True)
                return
            if normalized in ("status", "stan", "gdzie", "info"):
                await self.show_guide_status()
                return
            if self.guide_task_active():
                await self.send(
                    "Prowadzenie już trwa. Użyj prowadz status albo prowadz stop."
                )
                return
            task = asyncio.create_task(self.guide_to(args))
            self.guide_task = task
            task.add_done_callback(self._guide_task_finished)
            # Oddaj sterowanie pętli wejścia, ale pozwól zadaniu wypisać pierwszy
            # komunikat jeszcze przed następnym promptem.
            await asyncio.sleep(0)

    async def show_route_next_step(self):
            target = self.route_target_room
            if not target or target not in ROOMS:
                await self.send("Najpierw zaplanuj trasę: trasa <cel>.")
                return
            path = self.shortest_path(self.character.room_id, target)
            if path is None:
                await self.send("Nie udało się znaleźć drogi do zapamiętanego celu.")
                return
            if not path:
                await self.send(f"Jesteś już w celu trasy: {ROOMS[target]['name']}.")
                return
            direction, next_room = path[0]
            await self.send(
                f"Następny krok: {self.route_direction_name(direction)}. "
                f"Następna lokacja: {ROOMS[next_room]['name']}. "
                f"Do celu pozostaje {len(path)} przejść."
            )

    async def show_route(self, query):
            raw = str(query or "").strip()
            normalized = self.normalize_room_query(raw)
            if normalized in ("krok", "next", "nastepny", "następny", "dalej"):
                await self.show_route_next_step()
                return

            full = False
            for prefix in ("pelna ", "pełna ", "full ", "dokladna ", "dokładna "):
                if normalized.startswith(self.normalize_room_query(prefix)):
                    # Odetnij pierwsze słowo z oryginalnego tekstu, aby zachować
                    # polskie znaki w nazwie celu.
                    raw = raw.split(maxsplit=1)[1] if " " in raw else ""
                    normalized = self.normalize_room_query(raw)
                    full = True
                    break

            if not raw:
                if self.route_target_room:
                    target = self.route_target_room
                    target_is_npc = self.route_target_is_npc
                    target_label = self.route_target_label or ROOMS[target]["name"]
                else:
                    await self.send(
                        "Użycie: trasa <cel>, trasa pełna <cel> albo trasa krok."
                    )
                    return
            else:
                if normalized.startswith("to "):
                    raw = raw[3:].strip()
                npc_match = self.find_guide_npc(raw)
                target_is_npc = npc_match is not None
                target_npc = npc_match[1] if npc_match else None
                if target_is_npc:
                    matches = [target_npc["room"]]
                    target_label = target_npc["name"]
                else:
                    matches = self.find_room_matches(raw)
                    matches = list(dict.fromkeys(
                        self.guide_exploration_safe_target(room_id)
                        for room_id in matches
                    ))
                    target_label = ""

                if not matches:
                    await self.send(
                        "Nie rozpoznaję celu trasy. Użyj prowadz lista, aby sprawdzić dostępne cele."
                    )
                    return
                if len(matches) > 1:
                    options = self.compact_guide_matches(matches)
                    await self.send(f"Cel trasy jest niejednoznaczny: {raw}.")
                    for option in options[:20]:
                        await self.send(option["label"] + ".")
                    await self.send(
                        "Podaj dokładniejszą nazwę po komendzie trasa; niczego nie wybieram automatycznie."
                    )
                    return
                target = matches[0]
                if not target_label:
                    target_label = ROOMS[target]["name"]
                self.route_target_room = target
                self.route_target_label = target_label
                self.route_target_is_npc = target_is_npc

            path = self.shortest_path(self.character.room_id, target)
            if path is None:
                await self.send("Nie udało się znaleźć drogi do tej lokacji.")
                return

            await self.send(
                f"TRASA: {ROOMS[self.character.room_id]['name']} -> {target_label}."
            )
            if not path:
                await self.send("Jesteś już w celu. Liczba przejść: 0.")
                return

            direction, next_room = path[0]
            await self.send(
                f"Liczba przejść: {len(path)}. Pierwszy krok: "
                f"{self.route_direction_name(direction)} do {ROOMS[next_room]['name']}."
            )
            await self.send(
                "Skrócona droga: " + self.compact_route_directions(path) + "."
            )
            zones = self.route_zone_sequence(self.character.room_id, path)
            if zones:
                await self.send("Strefy po drodze: " + " -> ".join(zones) + ".")
            estimate = self.estimated_guide_seconds(path)
            await self.send(f"Szacowany czas automatycznego prowadzenia: {estimate:.1f} sekundy.")
            await self.send("Prowadzenie dochodzi dokładnie do wskazanej lokalizacji; nie wymaga ręcznego ostatniego kroku.")
            if full:
                await self.send("PEŁNA TRASA:")
                for index, (step_direction, step_room) in enumerate(path, 1):
                    await self.send(
                        f"Krok {index} z {len(path)}: {self.route_direction_name(step_direction)} -> {ROOMS[step_room]['name']}."
                    )
            else:
                await self.send(
                    "Pełny krok-po-kroku odczyt: trasa pełna <cel>. Następny krok później: trasa krok."
                )

    def shortest_path(self, start_room, target_room):
            if start_room == target_room:
                return []

            queue = [(start_room, [])]
            visited = {start_room}

            while queue:
                room_id, path = queue.pop(0)
                room = ROOMS.get(room_id)
                if not room:
                    continue
                for direction, next_room in room["exits"].items():
                    if next_room in visited:
                        continue
                    # v0.23.0: świat ma wyjścia do pięter tworzonych dopiero na
                    # żądanie. Nie rozwijamy ich wszystkich podczas BFS (to mogłoby
                    # generować kolejne piętra bez końca). Materializujemy tylko
                    # brakujący pokój, jeżeli jest dokładnie szukanym celem; inne
                    # lazy-exity bezpiecznie pomijamy.
                    if next_room not in ROOMS and next_room == target_room:
                        self.server.world.ensure_runtime_room(next_room)
                    if next_room not in ROOMS:
                        continue
                    new_path = path + [(direction, next_room)]
                    if next_room == target_room:
                        return new_path
                    visited.add(next_room)
                    queue.append((next_room, new_path))
            return None

    async def stop_auto_fishing(self, announce=True, immediate=True):
            self.auto_fishing = False
            task = self.auto_fishing_task

            if immediate:
                self.auto_fishing_task = None
                if task and task is not asyncio.current_task() and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                if announce:
                    await self.send("Auto-łowienie wyłączone.")
                return

            if task and not task.done():
                if announce:
                    await self.send(
                        "Auto-łowienie wyłączone. "
                        "Trwający połów zostanie dokończony, ale następny już się nie rozpocznie."
                    )
                return

            self.auto_fishing_task = None
            if announce:
                await self.send("Auto-łowienie wyłączone.")

    async def auto_fishing_loop(self):
            try:
                while self.auto_fishing and not self.closed:
                    if self.combat_mob_key:
                        await self.send(
                            "Auto-łowienie zatrzymane: rozpoczęła się walka."
                        )
                        break
                    if self.server.db.item_qty(
                        self.account_id, "fishing_rod"
                    ) <= 0:
                        await self.send(
                            "Auto-łowienie zatrzymane: nie masz Wędki."
                        )
                        break
                    if self.character.room_id not in FISHING_ROOMS:
                        await self.send(
                            "Auto-łowienie zatrzymane: nie stoisz przy łowisku."
                        )
                        break

                    await self.fish(from_auto=True)

            except asyncio.CancelledError:
                pass
            finally:
                self.auto_fishing = False
                if self.auto_fishing_task is asyncio.current_task():
                    self.auto_fishing_task = None

    async def set_auto_fishing(self, enabled):
            if enabled:
                if self.auto_fishing:
                    await self.send("Auto-łowienie jest już włączone.")
                    return
                if self.combat_mob_key:
                    await self.send(
                        "Nie możesz rozpocząć auto-łowienia podczas walki."
                    )
                    return
                if self.server.db.item_qty(
                    self.account_id, "fishing_rod"
                ) <= 0:
                    await self.send(
                        "Do auto-łowienia potrzebujesz Wędki."
                    )
                    return

                if self.character.room_id not in FISHING_ROOMS:
                    await self.send(
                        "Auto-łowienie możesz włączyć tylko przy łowisku. "
                        "Automat nie chodzi sam."
                    )
                    return

                if self.auto_mining or self.auto_mining_task:
                    await self.stop_auto_mining(announce=False)
                if self.auto_woodcutting or self.auto_woodcutting_task:
                    await self.stop_auto_woodcutting(announce=False)
                if self.auto_herbalism or self.auto_herbalism_task:
                    await self.stop_auto_herbalism(announce=False)

                self.auto_fishing = True
                self.auto_fishing_task = asyncio.create_task(
                    self.auto_fishing_loop()
                )
                await self.send(
                    "Auto-łowienie włączone. Łowi tylko w aktualnym miejscu "
                    "i nie chodzi samodzielnie. "
                    "Wpisz low off albo fish off, aby je zatrzymać."
                )
                return

            if not self.auto_fishing and not self.auto_fishing_task:
                await self.send("Auto-łowienie jest już wyłączone.")
                return
            await self.stop_auto_fishing(
                announce=True, immediate=False
            )

    def guide_exploration_safe_target(self, room_id):
            """Prowadzenie nigdy nie omija eksploracji pięter lochów."""
            room_id = str(room_id or "")
            if crypt_floor_number(room_id):
                return "crypt_entrance"
            if astral_floor_number(room_id) is not None:
                return "astral_gate"
            if mine_floor_number(room_id) is not None:
                return mine_floor_id(MINE_MIN_FLOOR)
            if mythic_crypt_floor_number(room_id):
                return "mythic_crypt_gate"
            if mythic_astral_floor_number(room_id):
                return "mythic_astral_gate"
            if giant_fortress_floor_number(room_id) is not None:
                return "giant_fortress_gate"
            dungeon, floor = profession_dungeon_floor(room_id)
            if dungeon and floor:
                return profession_dungeon_room_id(dungeon, 1)
            return room_id

    def guide_floor_request_label(self, query):
            q = self.normalize_room_query(query)
            checks = (
                (r"(?:krypta|crypt|pietro|pietro krypty|krypta pietro|crypt floor)\s*\d+", "Krypta"),
                (r"(?:wieza|wieza astralna|astral|astralna wieza|poziom wiezy|astral floor)\s*\d+", "Wieża Astralna"),
                (r"(?:kopalnia|mine|poziom kopalni|kopalnia poziom|mine floor)\s*\d+", "Kopalnia Głębinowa"),
                (r"(?:mityczna krypta|mythic crypt)\s*\d+", "Mityczna Krypta"),
                (r"(?:mityczna wieza astralna|mythic astral(?: tower)?)\s*\d+", "Mityczna Wieża Astralna"),
                (r"(?:twierdza|twierdza gigantow|giant fortress)\s*\d+", "Twierdza Gigantów"),
                (r"(?:kopalnia krysztalow|crystal mine)\s*\d+", "Kopalnia Głębinowa"),
                (r"(?:zatopiona grota|sunken grotto)\s*\d+", "Zatopiona Grota"),
                (r"(?:pradawny las|ancient forest)\s*\d+", "Pradawny Las"),
                (r"(?:ogrod alchemika|alchemy garden)\s*\d+", "Ogród Alchemika"),
            )
            for pattern, label in checks:
                if re.fullmatch(pattern, q):
                    return label
            return None

    def guide_floor_family_specs(self):
            return (
                {
                    "prefix": "mine_floor_",
                    "label": (
                        "Wejście do Kopalni Głębinowej"
                    ),
                    "minimum": MINE_MIN_FLOOR,
                    "maximum": None,
                    "target_room": mine_floor_id(MINE_MIN_FLOOR),
                },
                {
                    "prefix": "crypt_floor_",
                    "label": (
                        "Wejście do Krypty"
                    ),
                    "minimum": 1,
                    "maximum": None,
                    "target_room": "crypt_entrance",
                },
                {
                    "prefix": "mythic_crypt_floor_",
                    "label": (
                        "Wejście do Mitycznej Krypty"
                    ),
                    "minimum": MYTHIC_MIN_FLOOR,
                    "maximum": None,
                    "target_room": "mythic_crypt_gate",
                },
                {
                    "prefix": "astral_floor_",
                    "label": (
                        "Wejście do Wieży Astralnej"
                    ),
                    "minimum": ASTRAL_MIN_FLOOR,
                    "maximum": None,
                    "target_room": "astral_gate",
                },
                {
                    "prefix": "mythic_astral_floor_",
                    "label": (
                        "Wejście do Mitycznej Wieży Astralnej"
                    ),
                    "minimum": MYTHIC_MIN_FLOOR,
                    "maximum": None,
                    "target_room": "mythic_astral_gate",
                },
                {
                    "prefix": "giant_fortress_",
                    "label": (
                        "Wejście do Twierdzy Gigantów"
                    ),
                    "minimum": 1,
                    "maximum": None,
                    "target_room": "giant_fortress_gate",
                },
                {
                    "prefix": "prof_sunken_grotto_",
                    "label": (
                        "Wejście do Zatopionej Groty"
                    ),
                    "minimum": 1,
                    "maximum": None,
                    "target_room": profession_dungeon_room_id(
                        "sunken_grotto", 1
                    ),
                },
                {
                    "prefix": "prof_ancient_forest_",
                    "label": (
                        "Wejście do Pradawnego Lasu"
                    ),
                    "minimum": 1,
                    "maximum": None,
                    "target_room": profession_dungeon_room_id(
                        "ancient_forest", 1
                    ),
                },
                {
                    "prefix": "prof_alchemy_garden_",
                    "label": (
                        "Wejście do Ogrodu Alchemika"
                    ),
                    "minimum": 1,
                    "maximum": None,
                    "target_room": profession_dungeon_room_id(
                        "alchemy_garden", 1
                    ),
                },
            )

    def compact_guide_matches(self, matches):
            matches = list(dict.fromkeys(matches))
            matched = set()
            options = []

            for spec in self.guide_floor_family_specs():
                family_rooms = [
                    room_id
                    for room_id in matches
                    if room_id.startswith(spec["prefix"])
                ]
                if not family_rooms:
                    continue

                matched.update(family_rooms)
                options.append({
                    "kind": "room",
                    "label": spec["label"],
                    "room_id": spec["target_room"],
                })

            for room_id in matches:
                if room_id in matched:
                    continue
                options.append({
                    "kind": "room",
                    "label": (
                        f"{ROOMS[room_id]['name']}. "
                        f"Strefa: {ROOMS[room_id]['zone']}"
                    ),
                    "room_id": room_id,
                })

            return options

    async def ask_guide_choice(self, matches, query):
            options = self.compact_guide_matches(matches)

            if not options:
                return False

            self.guide_choice_state = {
                "mode": "destination",
                "query": str(query or ""),
                "options": options,
            }

            await self.send(
                f"Znaleziono kilka pasujących celów dla: {query}."
            )
            await self.send(
                "Wybierz cyfrę:"
            )

            for number, option in enumerate(options, 1):
                await self.send(
                    f"{number}. {option['label']}."
                )

            await self.send(
                "Wpisz tylko samą cyfrę wyboru."
            )
            return True

    async def handle_guide_choice_number(self, raw):
            state = self.guide_choice_state
            if not state:
                return False

            value = str(raw or "").strip()

            if self.normalize_room_query(value) in (
                "anuluj", "cancel", "stop",
            ):
                self.guide_choice_state = None
                await self.send(
                    "Anulowano wybór celu prowadzenia."
                )
                return True

            if not value.isdigit():
                return False

            number = int(value)

            if state["mode"] == "destination":
                options = state["options"]
                if not 1 <= number <= len(options):
                    await self.send(
                        f"Nieprawidłowy numer. Wybierz od 1 do "
                        f"{len(options)} albo wpisz anuluj."
                    )
                    return True

                option = options[number - 1]
                self.guide_choice_state = None
                await self.start_guide_task(option["room_id"])
                return True

            self.guide_choice_state = None
            return False

    def find_guide_npc(self, query):
            """Return one uniquely matched NPC for guide/walk, or None.

            NPC destinations are the only guide targets entered automatically.
            Normal rooms/locations stop one exit before the target.
            """
            q = self.normalize_room_query(query)
            if not q:
                return None

            exact = []
            partial = []
            for npc_id, npc in NPCS.items():
                room_id = npc.get("room")
                if room_id not in ROOMS:
                    continue

                npc_id_q = self.normalize_room_query(npc_id)
                name_q = self.normalize_room_query(npc.get("name", ""))
                aliases = {npc_id_q, name_q}

                # A unique personal name such as Toren, Garran or Mirella is
                # convenient for a screen-reader user and still resolves to NPC.
                words = [word for word in name_q.split() if len(word) >= 3]
                aliases.update(words)

                if q in aliases:
                    exact.append((npc_id, npc))
                elif any(q in alias for alias in aliases if alias):
                    partial.append((npc_id, npc))

            if len(exact) == 1:
                return exact[0]
            if not exact and len(partial) == 1:
                return partial[0]
            return None

    async def guide_to(self, query):
            self.guide_choice_state = None
            q = query.strip()
            if q.lower().startswith("to "):
                q = q[3:].strip()

            normalized = self.normalize_room_query(q)
            if normalized in ("profesje", "professions"):
                await self.show_guide_destinations("profesje")
                return
            if normalized in ("eq", "ekwipunek", "sklepy eq", "equipment", "gear"):
                await self.show_guide_destinations("eq")
                return
            list_prefixes = ("lista", "list", "cele", "destinations", "lokacje", "locations")
            for prefix in list_prefixes:
                if normalized == prefix or normalized.startswith(prefix + " "):
                    category = normalized[len(prefix):].strip()
                    await self.show_guide_destinations(category)
                    return

            if normalized in ("pomoc", "help", "navigation", "nawigacja"):
                await self.show_guide_destinations()
                return

            if not q:
                await self.send(
                    "Użycie: prowadz <cel> albo walk <cel>. "
                    "Lista kategorii: prowadz lista albo walk list."
                )
                return

            if self.combat_mob_key:
                await self.send("Nie możesz użyć prowadzenia podczas walki.")
                return

            # v0.23.0: część celów (Kopalnia Głębinowa i lochy profesyjne)
            # jest tworzona dopiero na żądanie. W v0.22 alias był odrzucany,
            # dopóki pokój nie istniał już w ROOMS, więc np. `prowadz kopalnia`
            # mogło odpowiadać, że nie rozpoznaje celu.
            shortcut = GUIDE_DESTINATION_ALIASES.get(normalized)
            if shortcut and shortcut not in ROOMS:
                self.server.world.ensure_runtime_room(shortcut)

            # v0.30.10 HOTFIX: wewnątrz zwykłej Krypty `walk krypta dół`
            # prowadzi wyłącznie do komnaty z zejściem bieżącego piętra. Nie wykonuje
            # ostatniego kroku `down`; gracz sam decyduje, kiedy zejść niżej.
            crypt_down_requested = normalized in (
                "krypta dol", "krypta w dol", "krypta down", "crypt down",
                "krypty dol", "krypta dool", "krytta dol", "krytta dool",
            )
            direct_crypt_down = False
            crypt_down_floor = None
            if crypt_down_requested:
                current_crypt_floor = crypt_floor_number(self.character.room_id)
                if current_crypt_floor is None:
                    await self.send(
                        "walk krypta dół działa wewnątrz zwykłej Krypty. "
                        "Najpierw wejdź na jej piętro."
                    )
                    return
                crypt_down_floor = current_crypt_floor + 1
                canonical_floor = crypt_floor_id(current_crypt_floor)
                self.server.world.ensure_runtime_room(canonical_floor)

                # Szukamy prawdziwej komnaty, z której wyjście `down` prowadzi na
                # następne piętro. Dzięki temu działa to także na rozgałęzionych
                # i dynamicznie generowanych piętrach.
                crypt_target = None
                for room_id, room in ROOMS.items():
                    if crypt_floor_number(room_id) != current_crypt_floor:
                        continue
                    next_room = room.get("exits", {}).get("down")
                    if crypt_floor_number(next_room) == crypt_down_floor:
                        crypt_target = room_id
                        break
                if crypt_target is None:
                    await self.send(
                        "Nie udało się odnaleźć zejścia na tym piętrze Krypty."
                    )
                    return

                target_is_treasure = False
                treasure_label = ""
                npc_match = None
                target_is_npc = False
                target_npc = None
                matches = [crypt_target]
                direct_crypt_down = True

            # v0.24.0: aktywny trop Mapy Skarbu jest celem zależnym od postaci,
            # więc nie może być zwykłym globalnym aliasem pokoju.
            treasure_match = None if direct_crypt_down else re.fullmatch(
                r"(?:skarb|skarbu|treasure)(?:\s+(\d+))?", normalized
            )
            if not direct_crypt_down:
                target_is_treasure = treasure_match is not None
                treasure_label = ""
            if direct_crypt_down:
                pass
            elif target_is_treasure:
                active_treasures = self.active_treasure_targets_v024()
                if not active_treasures:
                    await self.send(
                        "Nie masz aktywnego tropu Mapy Skarbu. Użyj mapy, a potem wpisz mapa skarbu."
                    )
                    return
                requested = treasure_match.group(1)
                if requested is None and len(active_treasures) > 1:
                    await self.send(
                        f"Masz {len(active_treasures)} aktywne tropy. Wpisz kartografia albo mapa skarbu, "
                        "a następnie prowadz skarb <numer>."
                    )
                    return
                index = int(requested or 1) - 1
                if index < 0 or index >= len(active_treasures):
                    await self.send(
                        f"Nie ma tropu numer {index + 1}. Aktywne tropy: {len(active_treasures)}."
                    )
                    return
                treasure_target = active_treasures[index]
                self.materialize_frontier_route_v024(treasure_target)
                if treasure_target not in ROOMS:
                    await self.send("Nie udało się przygotować sektora wskazanego przez mapę.")
                    return
                info = v0140_surface_secret_info(treasure_target)
                zone = V013_FRONTIER_SPECS[info["kind"]]["zone"]
                treasure_label = f"Trop skarbu: {zone}, sektor {info['x']+1}-{info['y']+1}"
                npc_match = None
                target_is_npc = False
                target_npc = None
                matches = [treasure_target]
            else:
                npc_match = self.find_guide_npc(q)
                target_is_npc = npc_match is not None
                target_npc = npc_match[1] if npc_match else None

                if target_is_npc:
                    matches = [target_npc["room"]]
                else:
                    floor_label = self.guide_floor_request_label(q)
                    matches = self.find_room_matches(q)
                    matches = list(dict.fromkeys(
                        self.guide_exploration_safe_target(room_id)
                        for room_id in matches
                    ))
                    # Bezpieczny cel po redukcji piętra także może być lazy-roomem.
                    for room_id in matches:
                        if room_id not in ROOMS:
                            self.server.world.ensure_runtime_room(room_id)
                    if floor_label and matches and floor_label != "Kopalnia Głębinowa":
                        await self.send(
                            f"Prowadzenie nie prowadzi na piętra. "
                            f"Eksploracja wnętrza pozostaje ręczna. "
                            f"Prowadzę tylko przed wejście: {floor_label}."
                        )
                    elif floor_label == "Kopalnia Głębinowa" and matches:
                        await self.send(
                            "Kopalnia: prowadzenie doprowadzi bezpośrednio na poziom 1. "
                            "Głębsze poziomy pozostają do eksploracji ręcznej."
                        )

            if not matches:
                await self.send(
                    "Nie rozpoznaję tego celu. "
                    "Wpisz prowadz lista albo walk list, aby wybrać kategorię."
                )
                return

            if len(matches) > 1:
                await self.ask_guide_choice(
                    matches,
                    q,
                )
                return

            target = matches[0]
            direct_mine_target = (
                (not target_is_npc)
                and target == mine_floor_id(MINE_MIN_FLOOR)
                and mine_floor_number(target) == MINE_MIN_FLOOR
            )
            # v0.30.6: prowadzenie zawsze dochodzi dokładnie do rozpoznanej lokalizacji.
            # Nadal respektuje wszystkie blokady wejścia i nie omija eksploracyjnych
            # ograniczeń dla pięter, bo te cele są wcześniej redukowane do bezpiecznych wejść.
            reach_exact_target = True

            if target == self.character.room_id:
                if direct_crypt_down:
                    await self.send(
                        f"Już jesteś przed zejściem na piętro {crypt_down_floor} Krypty. "
                        "Wykonaj zejście ręcznie."
                    )
                elif target_is_npc:
                    await self.send(
                        f"NPC {target_npc['name']} jest już tutaj: "
                        f"{ROOMS[target]['name']}."
                    )
                else:
                    await self.send(f"Już jesteś tutaj: {ROOMS[target]['name']}.")
                return

            full_path = self.shortest_path(self.character.room_id, target)
            if full_path is None:
                await self.send("Nie udało się znaleźć drogi do tej lokacji.")
                return

            self.guide_target_room = target
            self.guide_target_label = (
                target_npc["name"] if target_is_npc
                else (treasure_label if target_is_treasure else ROOMS[target]["name"])
            )
            self.guide_target_is_npc = target_is_npc

            # v0.30.6: pełna auto-nawigacja do celu. Nie zostawiamy ostatniego
            # ręcznego kroku; przejścia są wykonywane normalnie jedno po drugim,
            # więc walka, wymagania wejścia i inne blokady nadal mogą zatrzymać trasę.
            path = full_path
            stop_room = target
            final_direction = None
            self.guide_final_direction = None

            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
                await self.send("Auto-łowienie wyłączone z powodu rozpoczęcia podróży.")
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
                await self.send("Auto-kopanie wyłączone z powodu rozpoczęcia podróży.")
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
                await self.send("Auto-Drwalstwo wyłączone z powodu rozpoczęcia podróży.")
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)
                await self.send("Auto-Zielarstwo wyłączone z powodu rozpoczęcia podróży.")

            self.guiding = True
            if target_is_npc:
                await self.send(
                    f"Prowadzę do NPC: {target_npc['name']}. "
                    f"Lokalizacja: {ROOMS[target]['name']}. "
                    f"Liczba przejść: {len(path)}."
                )
            elif target_is_treasure:
                await self.send(
                    f"Prowadzę bezpośrednio do aktywnego tropu skarbu: {treasure_label}. "
                    f"Automatyczne przejścia: {len(path)}. Po dotarciu użyj sekret."
                )
            elif direct_crypt_down:
                await self.send(
                    f"Prowadzę przed zejście na piętro {crypt_down_floor} Krypty. "
                    f"Automatyczne przejścia: {len(path)}. "
                    "Ostatnie zejście wykonujesz ręcznie."
                )
            elif direct_mine_target:
                await self.send(
                    f"Prowadzę bezpośrednio do: {ROOMS[target]['name']}. "
                    f"Automatyczne przejścia: {len(path)}. "
                    "Nie musisz wykonywać ostatniego kroku ręcznie."
                )
            else:
                await self.send(
                    f"Prowadzę bezpośrednio do: {ROOMS[target]['name']}. "
                    f"Automatyczne przejścia: {len(path)}. "
                    "Nie musisz wykonywać żadnego kroku ręcznie."
                )

            try:
                for direction, next_room in path:
                    if self.closed:
                        break
                    if self.combat_mob_key:
                        await self.send("Prowadzenie przerwane przez walkę.")
                        break

                    old = self.character.room_id
                    mythic_error = self.mythic_entry_error(next_room)
                    if mythic_error:
                        await self.send(
                            "Prowadzenie zatrzymane. " + mythic_error
                        )
                        break

                    profession_error = (
                        self.profession_dungeon_access_error(next_room)
                    )
                    if profession_error:
                        await self.send(
                            "Prowadzenie zatrzymane. "
                            + profession_error
                        )
                        break

                    if self.astral_entry_blocked(next_room):
                        await self.send(
                            f"Prowadzenie zatrzymane. Wieża Astralna wymaga "
                            f"Soul Level {ASTRAL_MIN_SOUL_LEVEL}."
                        )
                        break
                    if self.mine_descent_blocked_for_player(old, direction):
                        progress = self.mine_progress()
                        floor = mine_floor_number(old)
                        required_hits = progress["wall_required_hits"]
                        await self.send(
                            f"Prowadzenie zatrzymane. Ściana kopalni "
                            f"blokuje zejście. Postęp "
                            f"{progress['wall_hits']} z "
                            f"{required_hits}."
                        )
                        break
                    if self.mythic_crypt_descent_blocked_for_player(
                        old, direction
                    ):
                        await self.send(
                            "Prowadzenie zatrzymane. "
                            "Mityczny boss Krypty blokuje zejście."
                        )
                        break
                    if self.mythic_astral_ascent_blocked_for_player(
                        old, direction
                    ):
                        await self.send(
                            "Prowadzenie zatrzymane. "
                            "Mityczny boss Wieży blokuje drogę w górę."
                        )
                        break
                    if self.giant_fortress_ascent_blocked_for_player(
                        old, direction
                    ):
                        boss = (
                            self.server.world.live_giant_fortress_boss(
                                old
                            )
                        )
                        boss_name = (
                            MOB_TEMPLATES[
                                boss.template_id
                            ]["name"]
                            if boss
                            else "boss Twierdzy Gigantów"
                        )
                        await self.send(
                            f"Prowadzenie zatrzymane. Drogę wyżej "
                            f"blokuje {boss_name}."
                        )
                        break
                    if self.crypt_descent_blocked_for_player(old, direction):
                        boss = self.server.world.live_crypt_boss(old)
                        boss_name = (
                            MOB_TEMPLATES[boss.template_id]["name"]
                            if boss else "boss Krypty"
                        )
                        await self.send(
                            f"Prowadzenie zatrzymane. Zejście niżej blokuje "
                            f"{boss_name}. Pokonaj bossa."
                        )
                        break
                    if self.astral_ascent_blocked_for_player(old, direction):
                        boss = self.server.world.live_astral_boss(old)
                        boss_name = (
                            MOB_TEMPLATES[boss.template_id]["name"]
                            if boss else "boss Wieży Astralnej"
                        )
                        await self.send(
                            f"Prowadzenie zatrzymane. Drogę w górę blokuje "
                            f"{boss_name}. Pokonaj bossa."
                        )
                        break
                    moved = await self.walk_room_transition(
                        direction, next_room, guided=True, show_room=False
                    )
                    if not moved:
                        break

                if target_is_npc and self.character.room_id == target:
                    await self.send(
                        f"Dotarłeś do NPC: {target_npc['name']}. "
                        f"Lokalizacja: {ROOMS[target]['name']}."
                    )
                    await self.look()
                elif direct_crypt_down and self.character.room_id == target:
                    await self.send(
                        f"Dotarłeś przed zejście na piętro {crypt_down_floor} Krypty. "
                        "Wykonaj zejście ręcznie."
                    )
                    await self.look()
                elif direct_mine_target and self.character.room_id == target:
                    await self.send(
                        f"Dotarłeś bezpośrednio do: {ROOMS[target]['name']}."
                    )
                    await self.look()
                elif target_is_treasure and self.character.room_id == target:
                    await self.send(
                        f"Dotarłeś bezpośrednio do tropu skarbu: {treasure_label}. "
                        "Użyj sekret, aby zbadać wskazane miejsce."
                    )
                    await self.look()
                elif (not target_is_npc) and (not direct_mine_target) and (not target_is_treasure) and self.character.room_id == target:
                    await self.send(
                        f"Dotarłeś bezpośrednio do: {ROOMS[target]['name']}."
                    )
                    await self.look()
            finally:
                self.guiding = False
                self.guide_target_room = None
                self.guide_target_label = ""
                self.guide_target_is_npc = False
                self.guide_final_direction = None

    async def stop_auto_mining(self, announce=True, immediate=True):
            self.auto_mining = False
            task = self.auto_mining_task

            if immediate:
                self.auto_mining_task = None
                if task and task is not asyncio.current_task() and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                if announce:
                    await self.send("Auto-kopanie wyłączone.")
                return

            if task and not task.done():
                if announce:
                    await self.send(
                        "Auto-kopanie wyłączone. "
                        "Trwające wydobycie zostanie dokończone, ale następne już się nie rozpocznie."
                    )
                return

            self.auto_mining_task = None
            if announce:
                await self.send("Auto-kopanie wyłączone.")

    async def auto_mining_loop(self):
            try:
                while self.auto_mining and not self.closed:
                    if self.combat_mob_key:
                        await self.send(
                            "Auto-kopanie zatrzymane: rozpoczęła się walka."
                        )
                        break
                    if self.server.db.item_qty(
                        self.account_id, "pickaxe"
                    ) <= 0:
                        await self.send(
                            "Auto-kopanie zatrzymane: nie masz Kilofa."
                        )
                        break
                    if not is_mining_room(self.character.room_id):
                        await self.send(
                            "Auto-kopanie zatrzymane: nie stoisz w miejscu wydobycia."
                        )
                        break

                    if await self.auto_mine_descend_if_unlocked():
                        continue

                    await self.mine(from_auto=True)

            except asyncio.CancelledError:
                pass
            finally:
                self.auto_mining = False
                if self.auto_mining_task is asyncio.current_task():
                    self.auto_mining_task = None

    async def set_auto_mining(self, enabled):
            if enabled:
                if self.auto_mining:
                    await self.send("Auto-kopanie jest już włączone.")
                    return
                if self.combat_mob_key:
                    await self.send(
                        "Nie możesz rozpocząć auto-kopania podczas walki."
                    )
                    return
                if self.server.db.item_qty(
                    self.account_id, "pickaxe"
                ) <= 0:
                    await self.send(
                        "Do auto-kopania potrzebujesz Kilofa."
                    )
                    return

                if not is_mining_room(self.character.room_id):
                    await self.send(
                        "Auto-kopanie możesz włączyć tylko w miejscu wydobycia. "
                        "Automat nie chodzi sam."
                    )
                    return

                if self.auto_fishing or self.auto_fishing_task:
                    await self.stop_auto_fishing(announce=False)
                if self.auto_woodcutting or self.auto_woodcutting_task:
                    await self.stop_auto_woodcutting(announce=False)
                if self.auto_herbalism or self.auto_herbalism_task:
                    await self.stop_auto_herbalism(announce=False)

                self.auto_mining = True
                self.auto_mining_task = asyncio.create_task(
                    self.auto_mining_loop()
                )
                await self.send(
                    "Auto-kopanie włączone. Jeśli jesteś w części wejściowej Kopalni Głębinowej, "
                    "automat sam zejdzie przez Wejście, Tunel i Komnatę na poziom 1 Kopalni Głębinowej. "
                    "Potem po przebiciu każdej ściany sam schodzi na następny odblokowany poziom. "
                    "Wpisz kop off albo mine off, aby je zatrzymać."
                )
                return

            if not self.auto_mining and not self.auto_mining_task:
                await self.send("Auto-kopanie jest już wyłączone.")
                return
            await self.stop_auto_mining(
                announce=True, immediate=False
            )

    async def stop_auto_woodcutting(self, announce=True, immediate=True):
            self.auto_woodcutting = False
            task = self.auto_woodcutting_task

            if immediate:
                self.auto_woodcutting_task = None
                if task and task is not asyncio.current_task() and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                if announce:
                    await self.send("Auto-Drwalstwo wyłączone.")
                return

            if task and not task.done():
                if announce:
                    await self.send(
                        "Auto-Drwalstwo wyłączone. "
                        "Trwające cięcie zostanie dokończone, ale następne już się nie rozpocznie."
                    )
                return

            self.auto_woodcutting_task = None
            if announce:
                await self.send("Auto-Drwalstwo wyłączone.")

    async def auto_woodcutting_loop(self):
            try:
                while self.auto_woodcutting and not self.closed:
                    if self.combat_mob_key:
                        await self.send(
                            "Auto-Drwalstwo zatrzymane: rozpoczęła się walka."
                        )
                        break
                    if self.server.db.item_qty(
                        self.account_id, "saw"
                    ) <= 0:
                        await self.send(
                            "Auto-Drwalstwo zatrzymane: nie masz Piły."
                        )
                        break
                    if self.character.room_id not in WOODCUTTING_ROOMS:
                        await self.send(
                            "Auto-Drwalstwo zatrzymane: nie stoisz przy drzewach."
                        )
                        break

                    await self.woodcut(from_auto=True)

            except asyncio.CancelledError:
                pass
            finally:
                self.auto_woodcutting = False
                if self.auto_woodcutting_task is asyncio.current_task():
                    self.auto_woodcutting_task = None

    async def set_auto_woodcutting(self, enabled):
            if enabled:
                if self.auto_woodcutting:
                    await self.send(
                        "Auto-Drwalstwo jest już włączone."
                    )
                    return
                if self.combat_mob_key:
                    await self.send(
                        "Nie możesz rozpocząć auto-Drwalstwa podczas walki."
                    )
                    return
                if self.server.db.item_qty(
                    self.account_id, "saw"
                ) <= 0:
                    await self.send(
                        "Do auto-Drwalstwa potrzebujesz Piły."
                    )
                    return

                if self.character.room_id not in WOODCUTTING_ROOMS:
                    await self.send(
                        "Auto-Drwalstwo możesz włączyć tylko przy drzewach. "
                        "Automat nie chodzi sam."
                    )
                    return

                if self.auto_fishing or self.auto_fishing_task:
                    await self.stop_auto_fishing(announce=False)
                if self.auto_mining or self.auto_mining_task:
                    await self.stop_auto_mining(announce=False)
                if self.auto_herbalism or self.auto_herbalism_task:
                    await self.stop_auto_herbalism(announce=False)

                self.auto_woodcutting = True
                self.auto_woodcutting_task = asyncio.create_task(
                    self.auto_woodcutting_loop()
                )
                await self.send(
                    "Auto-Drwalstwo włączone. Ścina tylko w aktualnym miejscu "
                    "i nie chodzi samodzielnie. "
                    "Wpisz tnij off albo woodcut off, aby je zatrzymać."
                )
                return

            if not self.auto_woodcutting and not self.auto_woodcutting_task:
                await self.send(
                    "Auto-Drwalstwo jest już wyłączone."
                )
                return
            await self.stop_auto_woodcutting(
                announce=True, immediate=False
            )

    async def stop_auto_herbalism(self, announce=True, immediate=True):
            self.auto_herbalism = False
            task = self.auto_herbalism_task

            if immediate:
                self.auto_herbalism_task = None
                if task and task is not asyncio.current_task() and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                if announce:
                    await self.send("Auto-Zielarstwo wyłączone.")
                return

            if task and not task.done():
                if announce:
                    await self.send(
                        "Auto-Zielarstwo wyłączone. "
                        "Trwający zbiór zostanie dokończony, ale następny już się nie rozpocznie."
                    )
                return

            self.auto_herbalism_task = None
            if announce:
                await self.send("Auto-Zielarstwo wyłączone.")

    async def auto_herbalism_loop(self):
            try:
                while self.auto_herbalism and not self.closed:
                    if self.combat_mob_key:
                        await self.send(
                            "Auto-Zielarstwo zatrzymane: rozpoczęła się walka."
                        )
                        break
                    if self.server.db.item_qty(
                        self.account_id, "herbalist_sickle"
                    ) <= 0:
                        await self.send(
                            "Auto-Zielarstwo zatrzymane: nie masz Sierpa Zielarskiego."
                        )
                        break
                    if self.character.room_id not in HERBALISM_ROOMS:
                        await self.send(
                            "Auto-Zielarstwo zatrzymane: nie stoisz w miejscu z ziołami."
                        )
                        break

                    await self.gather_herb(from_auto=True)

            except asyncio.CancelledError:
                pass
            finally:
                self.auto_herbalism = False
                if self.auto_herbalism_task is asyncio.current_task():
                    self.auto_herbalism_task = None

    async def set_auto_herbalism(self, enabled):
            if enabled:
                if self.auto_herbalism:
                    await self.send(
                        "Auto-Zielarstwo jest już włączone."
                    )
                    return
                if self.combat_mob_key:
                    await self.send(
                        "Nie możesz rozpocząć auto-Zielarstwa podczas walki."
                    )
                    return
                if self.server.db.item_qty(
                    self.account_id, "herbalist_sickle"
                ) <= 0:
                    await self.send(
                        "Do auto-Zielarstwa potrzebujesz Sierpa Zielarskiego."
                    )
                    return

                if self.character.room_id not in HERBALISM_ROOMS:
                    await self.send(
                        "Auto-Zielarstwo możesz włączyć tylko w miejscu z ziołami. "
                        "Automat nie chodzi sam."
                    )
                    return

                if self.auto_fishing or self.auto_fishing_task:
                    await self.stop_auto_fishing(announce=False)
                if self.auto_mining or self.auto_mining_task:
                    await self.stop_auto_mining(announce=False)
                if self.auto_woodcutting or self.auto_woodcutting_task:
                    await self.stop_auto_woodcutting(announce=False)

                self.auto_herbalism = True
                self.auto_herbalism_task = asyncio.create_task(
                    self.auto_herbalism_loop()
                )
                await self.send(
                    "Auto-Zielarstwo włączone. Zbiera tylko w aktualnym miejscu "
                    "i nie chodzi samodzielnie. "
                    "Wpisz zbieraj off, aby je zatrzymać."
                )
                return

            if not self.auto_herbalism and not self.auto_herbalism_task:
                await self.send(
                    "Auto-Zielarstwo jest już wyłączone."
                )
                return
            await self.stop_auto_herbalism(
                announce=True, immediate=False
            )

    async def show_profession_ranks(self):
            for profession in (
                "Wędkarstwo", "Górnictwo", "Drwalstwo",
                "Zielarstwo", "Gotowanie", "Alchemia",
                "Kowalstwo", "Jubilerstwo",
            ):
                await self.send(f"RANGI: {profession.upper()}")
                thresholds = profession_rank_thresholds(profession)
                max_rank = profession_max_rank(profession)
                max_level = profession_max_level(profession)

                for rank, minimum in enumerate(thresholds, 1):
                    if rank < max_rank:
                        maximum = thresholds[rank] - 1
                        level_text = f"level {minimum}-{maximum}"
                    else:
                        level_text = f"level {minimum}-{max_level}"

                    await self.send(
                        f"Ranga {rank}: "
                        f"{PROFESSION_RANK_NAMES[profession][rank - 1]}. "
                        f"{level_text}."
                    )

    async def show_professions(self, mode=""):
            mode = self.normalize_description_query(mode)
            detailed = mode in (
                "info", "pelne", "pełne", "szczegoly", "szczegóły", "details"
            )
            professions = (
                "Wędkarstwo", "Górnictwo", "Drwalstwo", "Zielarstwo",
                "Gotowanie", "Alchemia", "Kowalstwo", "Jubilerstwo",
            )
            await self.send("PROFESJE INFO" if detailed else "PROFESJE")
            for name in professions:
                row = self.server.db.profession(self.account_id, name)
                level = int(row["level"])
                max_level = profession_max_level(name)
                rank = profession_rank(level, name)
                max_rank = profession_max_rank(name)
                rank_name = profession_rank_name(name, level)
                if not detailed:
                    await self.send(
                        f"{name}: level {level}/{max_level}, ranga {rank}/{max_rank}: {rank_name}."
                    )
                    continue
                thresholds = profession_rank_thresholds(name)
                if rank < max_rank:
                    next_rank = f"Następna ranga od levelu {thresholds[rank]}."
                else:
                    next_rank = "Ranga maksymalna."
                xp_text = (
                    "maksimum" if level >= max_level else
                    f"{row['xp']} z {self.profession_xp_to_next(level, name)}"
                )
                await self.send(
                    f"{name}: level {level}/{max_level}. Ranga {rank}/{max_rank}: {rank_name}. "
                    f"XP {xp_text}. Akcje {row['actions']}. {next_rank}"
                )
            if detailed:
                await self.send(
                    "Maksimum wszystkich ośmiu profesji: level 400."
                )
                await self.send(
                    "Poziom profesji skraca czas pracy i blokuje receptury/zlecenia. "
                    "Poziom narzędzia odblokowuje lepsze surowce oraz zwiększa rare/quality i bonus urobku. "
                    "Wpisz narzedzia info po Tiery i bonusy."
                )
            else:
                await self.send("Wpisz profesje info po XP, akcje, progi rang i zasady.")

    async def show_tool_tiers(self):
            for tool_type, title in (
                ("fishing", "WĘDKI"),
                ("mining", "KILOFA"),
                ("woodcutting", "PIŁY"),
                ("crafting", "MŁOTA RZEMIEŚLNICZEGO"),
                ("cooking", "NOŻA KUCHARSKIEGO"),
                ("herbalism", "SIERPA ZIELARSKIEGO"),
                ("alchemy", "MOŹDZIERZA ALCHEMICZNEGO"),
                ("jewelcrafting", "SZCZYPIEC JUBILERSKICH"),
            ):
                await self.send(f"NAZWY TIERÓW {title}")
                for tier, minimum in enumerate(TOOL_TIER_THRESHOLDS, 1):
                    if tier < TOOL_MAX_TIER:
                        maximum = TOOL_TIER_THRESHOLDS[tier] - 1
                        level_text = f"level {minimum}-{maximum}"
                    else:
                        level_text = f"level {minimum}"
                    bonus = int(TOOL_TIER_BONUS_CHANCES[tier - 1] * 100)
                    await self.send(
                        f"Tier {tier}: {TOOL_TIER_NAMES[tool_type][tier - 1]}. "
                        f"{level_text}. Bonus {bonus} procent."
                    )

    def tool_info_definition(self, tool_type):
            definitions = {
                "fishing": ("fishing_rod", "Wędka"),
                "mining": ("pickaxe", "Kilof"),
                "woodcutting": ("saw", "Piła"),
                "crafting": ("crafting_hammer", "Młot Rzemieślniczy"),
                "cooking": ("chef_knife", "Nóż Kucharski"),
                "herbalism": ("herbalist_sickle", "Sierp Zielarski"),
                "alchemy": ("alchemy_mortar", "Moździerz Alchemiczny"),
                "jewelcrafting": ("jeweler_pliers", "Szczypce Jubilerskie"),
            }
            return definitions.get(tool_type)

    def tool_bonus_label(self, tool_type):
            if tool_type == "cooking":
                return "Szansa na dodatkową potrawę"
            if tool_type == "crafting":
                return "Szansa na dodatkowy produkt receptury"
            if tool_type == "alchemy":
                return "Szansa na dodatkową miksturę"
            if tool_type == "herbalism":
                return "Szansa na dodatkowe zioło"
            if tool_type == "jewelcrafting":
                return "Szansa na dodatkową biżuterię"
            return "Bonus dodatkowego urobku"

    def profession_level_for_tool(self, tool_type):
            profession = profession_for_tool_type(tool_type)
            if not profession:
                return 1
            row = self.server.db.profession(self.account_id, profession)
            return max(1, min(profession_max_level(profession), int(row["level"])))

    def profession_action_seconds(self, tool_type, profession_level):
            return generator_core_v027.profession_action_seconds(tool_type, profession_level)

    def tool_action_seconds(self, tool_type, profession_level):
            """Alias zgodności: od v0.8.66 argument oznacza level PROFESJI, nie narzędzia."""
            return self.profession_action_seconds(tool_type, profession_level)

    def recipe_action_seconds(self, tool_type, profession_level, recipe):
            """Generator Core owns both profession tempo and recipe-stage complexity."""
            base = generator_core_v027.profession_action_seconds(tool_type, profession_level)
            required = max(1, min(400, int(recipe.get("generator_level", 1) or 1)))
            progress_gap = max(0, required - int(profession_level))
            generated_penalty = int(round(3.0 * progress_gap / 400.0))
            return max(1, int(base + generated_penalty))

    def tool_action_label(self, tool_type):
            return {
                "fishing": "Czas zarzucenia i połowu",
                "mining": "Czas wydobycia",
                "woodcutting": "Czas cięcia",
                "crafting": "Czas wytwarzania",
                "cooking": "Czas gotowania",
                "herbalism": "Czas zbioru",
                "alchemy": "Czas warzenia",
                "jewelcrafting": "Czas wykonania biżuterii",
            }.get(tool_type, "Czas akcji")

    def tool_xp_remaining_to_level(self, level, xp, tool_type=None):
            max_level = tool_max_level(tool_type)
            if level >= max_level:
                return 0
            return max(
                0,
                self.tool_xp_to_next(level, tool_type) - int(xp),
            )

    def tool_xp_remaining_to_next_tier(self, level, xp, tool_type=None):
            tier = tool_tier(level)
            if tier >= TOOL_MAX_TIER:
                return 0, 0

            target_level = TOOL_TIER_THRESHOLDS[tier]
            levels_remaining = max(0, target_level - level)

            total_xp = self.tool_xp_remaining_to_level(level, xp, tool_type)
            for current_level in range(level + 1, target_level):
                total_xp += self.tool_xp_to_next(current_level, tool_type)

            return levels_remaining, total_xp

    async def show_single_tool(self, tool_type):
            definition = self.tool_info_definition(tool_type)
            if not definition:
                await self.send("Nieznane narzędzie.")
                return

            item_id, name = definition
            owned = self.server.db.item_qty(self.account_id, item_id) > 0
            if not owned:
                await self.send(f"{name}: nie posiadasz tego narzędzia.")
                if tool_type == "fishing":
                    await self.send(
                        "Wędkę kupisz tylko u Mistrza Wędkarstwa Nerisa "
                        "w Szkole Wędkarstwa."
                    )
                elif tool_type == "mining":
                    await self.send(
                        "Kilof kupisz tylko u Górnika Torena przy "
                        "Wejściu do Kryształowej Jaskini."
                    )
                elif tool_type == "woodcutting":
                    await self.send(
                        "Piłę kupisz tylko u Mistrza Drwalstwa Orena "
                        "w Leśniczówce."
                    )
                elif tool_type == "crafting":
                    await self.send(
                        "Młot Rzemieślniczy kupisz tylko u Mistrza "
                        "Rzemiosła Haldora w Warsztacie Rzemieślniczym."
                    )
                elif tool_type == "cooking":
                    await self.send(
                        "Nóż Kucharski kupisz tylko u Kucharza Marcela "
                        "w Kuchni Błękitnego Płomienia."
                    )
                elif tool_type == "herbalism":
                    await self.send(
                        "Sierp Zielarski kupisz tylko u Mistrzyni "
                        "Zielarstwa Seny w Ogrodzie Zielarskim."
                    )
                elif tool_type == "alchemy":
                    await self.send(
                        "Moździerz Alchemiczny kupisz tylko u Mistrza "
                        "Alchemii Orina w Laboratorium Alchemicznym."
                    )
                elif tool_type == "jewelcrafting":
                    await self.send(
                        "Szczypce Jubilerskie kupisz tylko u Jubilerki Mirelli "
                        "w Pracowni Jubilerskiej."
                    )
                return

            row = self.server.db.tool(self.account_id, tool_type)
            level = int(row["level"])
            xp = int(row["xp"])
            uses = int(row["uses"])
            tier = tool_tier(level)
            max_level = tool_max_level(tool_type)
            tier_name = tool_tier_name(tool_type, level)
            bonus_percent = int(tool_tier_bonus_chance(level) * 100)
            bonus_label = self.tool_bonus_label(tool_type)

            await self.send(f"NARZĘDZIE: {name}.")
            await self.send(
                f"Aktualna nazwa narzędzia: {tier_name}."
            )
            await self.send(
                f"Level: {level} z {max_level}. "
                f"Użycia: {uses}."
            )
            profession = profession_for_tool_type(tool_type)
            profession_level = self.profession_level_for_tool(tool_type)
            await self.send(
                f"{self.tool_action_label(tool_type)}: "
                f"{self.profession_action_seconds(tool_type, profession_level)} sekund. "
                f"Tempo daje {profession} level {profession_level}; level narzędzia nie skraca czasu."
            )

            if level >= max_level:
                await self.send("XP: maksimum. Do następnego levelu: maksimum.")
            else:
                needed = self.tool_xp_to_next(level, tool_type)
                remaining = self.tool_xp_remaining_to_level(level, xp, tool_type)
                await self.send(
                    f"XP obecnego levelu: {xp} z {needed}. "
                    f"Do następnego levelu brakuje {remaining} XP."
                )

            await self.send(
                f"Obecny Tier: {tier} z {TOOL_MAX_TIER}. "
                f"Nazwa: {tier_name}. "
                f"{bonus_label}: {bonus_percent} procent."
            )

            if tier >= TOOL_MAX_TIER:
                await self.send("Tier maksymalny. Nie ma następnego Tieru.")
            else:
                target_level = TOOL_TIER_THRESHOLDS[tier]
                next_tier = tier + 1
                next_name = TOOL_TIER_NAMES[tool_type][next_tier - 1]
                levels_remaining, xp_remaining = (
                    self.tool_xp_remaining_to_next_tier(
                        level, xp, tool_type
                    )
                )
                await self.send(
                    f"Następny Tier: {next_tier}, {next_name}, "
                    f"od levelu {target_level}. "
                    f"Brakuje {levels_remaining} leveli i łącznie "
                    f"{xp_remaining} XP narzędzia."
                )

            await self.send(f"TIERY NARZĘDZIA: {name}.")
            for tier_number, minimum in enumerate(TOOL_TIER_THRESHOLDS, 1):
                if tier_number < TOOL_MAX_TIER:
                    maximum = TOOL_TIER_THRESHOLDS[tier_number] - 1
                    level_text = f"level {minimum}-{maximum}"
                else:
                    if tool_type == "crafting":
                        level_text = (
                            f"level {minimum}-{TOOL_MAX_LEVEL}"
                        )
                    else:
                        level_text = f"level {minimum}-{TOOL_MAX_LEVEL}"

                tier_bonus = int(
                    TOOL_TIER_BONUS_CHANCES[tier_number - 1] * 100
                )
                marker = " Obecny." if tier_number == tier else ""
                await self.send(
                    f"Tier {tier_number}: "
                    f"{TOOL_TIER_NAMES[tool_type][tier_number - 1]}. "
                    f"{level_text}. Bonus {tier_bonus} procent.{marker}"
                )

    async def show_tools(self, mode=""):
            mode = self.normalize_description_query(mode)
            detailed = mode in (
                "info", "pelne", "pełne", "szczegoly", "szczegóły", "details"
            )
            tools = [
                ("fishing", "fishing_rod", "Wędka", "Neris", "Szkoła Wędkarstwa"),
                ("mining", "pickaxe", "Kilof", "Toren", "Wejście do Kryształowej Jaskini"),
                ("woodcutting", "saw", "Piła", "Oren", "Leśniczówka"),
                ("crafting", "crafting_hammer", "Młot Rzemieślniczy", "Haldor", "Warsztat Rzemieślniczy"),
                ("cooking", "chef_knife", "Nóż Kucharski", "Marcel", "Kuchnia Błękitnego Płomienia"),
                ("herbalism", "herbalist_sickle", "Sierp Zielarski", "Sena", "Ogród Zielarski"),
                ("alchemy", "alchemy_mortar", "Moździerz Alchemiczny", "Orin", "Laboratorium Alchemiczne"),
                ("jewelcrafting", "jeweler_pliers", "Szczypce Jubilerskie", "Mirella", "Pracownia Jubilerska"),
            ]
            await self.send("NARZĘDZIA INFO" if detailed else "NARZĘDZIA")
            for tool_type, item_id, name, seller, location in tools:
                owned = self.server.db.item_qty(self.account_id, item_id) > 0
                if not owned:
                    if detailed:
                        await self.send(f"{name}: brak. Sprzedawca: {seller}, {location}.")
                    else:
                        await self.send(f"{name}: brak.")
                    continue
                row = self.server.db.tool(self.account_id, tool_type)
                level = int(row["level"])
                max_level = tool_max_level(tool_type)
                tier = tool_tier(level)
                tier_name = tool_tier_name(tool_type, level)
                if not detailed:
                    await self.send(
                        f"{name}: level {level}/{max_level}, Tier {tier}/{TOOL_MAX_TIER}: {tier_name}."
                    )
                    continue
                bonus_percent = int(tool_tier_bonus_chance(level) * 100)
                xp_text = (
                    "maksimum" if level >= max_level else
                    f"{row['xp']} z {self.tool_xp_to_next(level, tool_type)}"
                )
                if tier < TOOL_MAX_TIER:
                    next_text = f"Następny Tier od levelu {TOOL_TIER_THRESHOLDS[tier]}."
                else:
                    next_text = "Tier maksymalny."
                await self.send(
                    f"{name}: {tier_name}. Level {level}/{max_level}. Tier {tier}/{TOOL_MAX_TIER}. "
                    f"XP {xp_text}. Użycia {row['uses']}. "
                    f"{self.tool_action_label(tool_type)}: {self.profession_action_seconds(tool_type, self.profession_level_for_tool(tool_type))} sekund "
                    f"(tempo z {profession_for_tool_type(tool_type)}). "
                    f"{self.tool_bonus_label(tool_type)}: {bonus_percent} procent. {next_text} "
                    f"Sprzedawca: {seller}, {location}."
                )
            if detailed:
                await self.send(
                    "Każde narzędzie sprzedaje wyłącznie NPC własnej profesji. Narzędzia nie mają durability."
                )
            else:
                await self.send("Wpisz narzedzia info po XP, bonusy, czas akcji i sprzedawców.")

    def fishing_water_type(self, room_id=None):
            room_id = room_id or self.character.room_id
            if room_id not in FISHING_ROOMS:
                return None
            if room_id in FISHING_WATER_TYPE_OVERRIDES:
                return FISHING_WATER_TYPE_OVERRIDES[room_id]
            dungeon, _floor = profession_dungeon_floor(room_id)
            if dungeon == "sunken_grotto":
                return "Zatopiona grota"
            if room_id in RIVER_FISHING_ROOMS:
                return "Rzeka"
            if room_id in LAKE_FISHING_ROOMS:
                return "Jezioro"
            if room_id in SEA_FISHING_ROOMS:
                return "Morze"
            if room_id in OCEAN_FISHING_ROOMS:
                return "Ocean"
            return "Łowisko"

    def fishing_habitat(self, room_id=None):
            room_id = room_id or self.character.room_id
            if room_id in RIVER_FISHING_ROOMS: return "river"
            if room_id in LAKE_FISHING_ROOMS: return "lake"
            if room_id in SEA_FISHING_ROOMS: return "sea"
            if room_id in OCEAN_FISHING_ROOMS: return "ocean"
            return None

    def fishing_available_pool(self, tool_level, habitat=None):
            habitat = habitat or self.fishing_habitat()
            tool_level = max(1, min(400, int(tool_level)))
            access_level = tool_tier_access_level(tool_level)
            habitat_ids = {
                "river": tuple(RIVER_FISH_ATLAS),
                "lake": tuple(LAKE_FISH_ATLAS),
                "sea": tuple(SEA_FISH_ATLAS),
                "ocean": tuple(OCEAN_FISH_ATLAS),
            }.get(habitat, ())
            return generator_core_v027.resource_pool(
                habitat_ids, ITEMS, access_level, f"fishing:{habitat or 'unknown'}"
            )

    def fishing_ecology_pool(self, tool_level, habitat=None, room_id=None):
            room_id = room_id or self.character.room_id
            habitat = habitat or self.fishing_habitat(room_id)
            tool_level = max(1, min(400, int(tool_level)))
            if not habitat:
                return ()
            dungeon, dungeon_floor = profession_dungeon_floor(room_id)
            effective_level = tool_level
            if dungeon == "sunken_grotto":
                effective_level = min(tool_level, max(1, int(dungeon_floor) * 10))
            # v0.30.39: ekologia łowiska nie wycina już odblokowanych gatunków.
            # Pula zawsze pozostaje kumulacyjna; preferencje wpływają tylko na wagę.
            return tuple(self.fishing_available_pool(effective_level, habitat))

    def fishing_loot(self, tool_level, habitat="river"):
            room_id = self.character.room_id
            pool = self.fishing_ecology_pool(tool_level, habitat=habitat, room_id=room_id)
            if not pool:
                return None
            weights = generator_core_v027.resource_weights(
                pool, ITEMS, tool_level, f"fishing:{habitat}:{room_id}"
            )
            preferred = FISHING_ECOLOGY_PREFERRED_IDS.get(room_id) or set()
            if preferred:
                # Typowe gatunki danego stanowiska są częstsze, ale żaden wcześniej
                # odblokowany gatunek tego habitatu nie dostaje wagi 0.
                weights = [
                    float(weight) * (2.75 if item_id in preferred else 1.0)
                    for item_id, weight in zip(pool, weights)
                ]
            return random.choices(pool, weights=weights, k=1)[0]

    async def show_water_info(self):
            habitat = self.fishing_habitat()
            water_type = self.fishing_water_type()
            if not habitat or not water_type:
                await self.send(
                    "Tutaj nie ma łowiska. Komenda woda działa tylko w miejscu, "
                    "w którym można łowić."
                )
                return

            tool = self.server.db.tool(self.account_id, "fishing")
            tool_level = int(tool["level"])
            pool = tuple(self.fishing_ecology_pool(tool_level, habitat=habitat, room_id=self.character.room_id))
            room = ROOMS.get(self.character.room_id, {})
            await self.send(
                f"ŁOWISKO: {water_type}. Lokacja: {room.get('name', self.character.room_id)}."
            )
            await self.send(
                f"Ekosystem ryb: {FISHING_HABITAT_LABELS.get(habitat, habitat)}. "
                f"Wędka level {tool_level}, Tier {tool_tier(tool_level)}. "
                f"Dostępnych teraz gatunków: {len(pool)}."
            )

            known = self.server.db.fish_journal_ids(self.account_id)
            pool_species = {base_fish_species_id(item_id) for item_id in pool}
            known_here = sorted(
                pool_species & known,
                key=lambda item_id: normalize_lookup_text(ITEMS[item_id]["name"]),
            )
            unknown_count = max(0, len(pool_species) - len(known_here))
            await self.send(
                f"Dziennik ryb w tym łowisku: odkryte {len(known_here)}, "
                f"nieodkryte {unknown_count}."
            )
            if known_here:
                await self.send(
                    "Znane gatunki tutaj: "
                    + ", ".join(ITEMS[item_id]["name"] for item_id in known_here)
                    + "."
                )

            habitat_ids = {
                "river": tuple(RIVER_FISH_ATLAS), "lake": tuple(LAKE_FISH_ATLAS),
                "sea": tuple(SEA_FISH_ATLAS), "ocean": tuple(OCEAN_FISH_ATLAS),
            }.get(habitat, ())
            locked = sorted(
                (int(ITEMS[iid].get("generator_level", 1) or 1), iid)
                for iid in habitat_ids if iid in ITEMS
                if int(ITEMS[iid].get("generator_level", 1) or 1) > tool_tier_access_level(tool_level)
            )
            if locked:
                next_level, next_item = locked[0]
                await self.send(
                    f"Kolejny gatunek wymaga wyższego Tieru Wędki; "
                    f"najbliższy próg zasobu to level {next_level}: {ITEMS[next_item]['name']}."
                )
            else:
                await self.send("Masz odblokowane wszystkie ryby tego ekosystemu.")

            await self.send(
                "Ryby nie mają twardego limitu sztuk. Łowisko nie wyczerpuje się od łowienia."
            )

    async def show_fish_journal(self, args=""):
            rows = self.server.db.fish_journal_rows(self.account_id)
            query = self.normalize_description_query(args)
            if not query:
                discovered = len(rows)
                legendary = sum(
                    1 for row in rows
                    if fish_species_rarity(str(row["fish_id"])) == "legendary"
                )
                total_caught = sum(max(0, int(row["caught_count"] or 0)) for row in rows)
                await self.send(
                    f"DZIENNIK RYB: odkryte gatunki {discovered} z {len(FISH_RESOURCE_IDS)}. "
                    f"Zarejestrowane połowy {total_caught}. Legendarne gatunki {legendary}."
                )
                await self.send(
                    "Wpisz dziennikryb lista, aby przeczytać odkryte gatunki, "
                    "albo dziennikryb <nazwa ryby>, aby sprawdzić rekordy."
                )
                return

            if query in ("lista", "list", "all", "wszystkie"):
                if not rows:
                    await self.send("Dziennik ryb jest pusty. Złów pierwszy gatunek.")
                    return
                ordered = sorted(
                    rows,
                    key=lambda row: normalize_lookup_text(
                        ITEMS.get(str(row["fish_id"]), {}).get("name", str(row["fish_id"]))
                    ),
                )
                await self.send(f"ODKRYTE GATUNKI RYB: {len(ordered)}.")
                for row in ordered:
                    fish_id = str(row["fish_id"])
                    name = ITEMS.get(fish_id, {}).get("name", fish_id)
                    rarity = fish_rarity_label(fish_id)
                    count = max(0, int(row["caught_count"] or 0))
                    best_l = max(0, int(row["best_length_mm"] or 0))
                    best_w = max(0, int(row["best_weight_g"] or 0))
                    if best_l > 0 and best_w > 0:
                        record = (
                            f" Rekord: {format_fish_length(best_l)}, "
                            f"{format_fish_weight(best_w)}."
                        )
                    else:
                        record = " Rekord rozmiaru od v0.9.5 jeszcze nie zapisany."
                    await self.send(
                        f"{name}. Rzadkość: {rarity}. Złowiono {count}.{record}"
                    )
                return

            candidates = {
                fish_id: {"name": ITEMS.get(fish_id, {}).get("name", fish_id)}
                for fish_id in FISH_RESOURCE_IDS
                if fish_id in ITEMS
            }
            found = find_by_name(candidates, args)
            if not found:
                await self.send("Nie znam takiego gatunku ryby.")
                return
            fish_id, fish = found
            row = self.server.db.fish_journal_entry(self.account_id, fish_id)
            if not row:
                await self.send(
                    f"{fish['name']}: gatunek jeszcze nieodkryty w Dzienniku ryb."
                )
                return
            habitats = fish_species_habitats(fish_id)
            habitat_text = ", ".join(habitats) if habitats else "specjalne łowisko"
            best_l = max(0, int(row["best_length_mm"] or 0))
            best_w = max(0, int(row["best_weight_g"] or 0))
            await self.send(
                f"{fish['name']}. Rzadkość: {fish_rarity_label(fish_id)}. "
                f"Złowiono {int(row['caught_count'] or 0)}. Wody: {habitat_text}."
            )
            if best_l > 0 or best_w > 0:
                await self.send(
                    f"Rekord długości: {format_fish_length(best_l)}. "
                    f"Rekord masy: {format_fish_weight(best_w)}."
                )
            else:
                await self.send(
                    "Gatunek pochodzi ze starszego zapisu; rekord długości i masy "
                    "zacznie się od pierwszego połowu w v0.9.5."
                )

    def mining_loot(self, tool_level, room_id=None):
            room_id = room_id or self.character.room_id
            tool_level = max(1, min(400, int(tool_level)))
            floor = mine_floor_number(room_id)
            dungeon, dungeon_floor = profession_dungeon_floor(room_id)
            if dungeon == "crystal_mine":
                floor = min(400, max(1, int(dungeon_floor) * 10))
            tool_access_level = tool_tier_access_level(tool_level)
            effective_level = tool_access_level if floor is None else min(tool_access_level, max(1, int(floor)))
            if random.random() < generator_core_v027.jackpot_chance(effective_level, f"mining:{room_id}"):
                return "__mithril_currency__"
            pool = generator_core_v027.resource_pool(
                tuple(ORE_RESOURCE_IDS), ITEMS, effective_level, f"mining:{room_id}"
            )
            if not pool:
                return None
            weights = generator_core_v027.resource_weights(
                pool, ITEMS, effective_level, f"mining:{room_id}"
            )
            return random.choices(pool, weights=weights, k=1)[0]

    def mining_gem_drop(self, tool_level, profession_level, room_id=None):
            tool_level = max(1, min(400, int(tool_level)))
            profession_level = max(1, min(400, int(profession_level)))
            room_id = room_id or self.character.room_id
            floor = mine_floor_number(room_id)
            dungeon, dungeon_floor = profession_dungeon_floor(room_id)
            if dungeon == "crystal_mine":
                floor = min(400, max(1, int(dungeon_floor) * 10))
            # v0.30.26: rodzaj surowego klejnotu zależy od Tieru Kilofa.
            # Górnictwo nadal wpływa na jakość/szansę, ale nie odblokowuje
            # nowych rodzajów klejnotów pomiędzy progami Tieru narzędzia.
            effective = tool_tier_access_level(tool_level)
            if floor is not None:
                effective = min(effective, max(1, int(floor)))
            base_gems = tuple(
                iid for iid, item in ITEMS.items()
                if item.get("type") == "gem_raw" and not item.get("gem_quality")
            )
            pool = generator_core_v027.resource_pool(
                base_gems, ITEMS, effective, f"gems:{room_id}"
            )
            gem_skill = min(tool_level, profession_level)
            chance = min(0.18, 0.035 + 0.11 * (gem_skill / 400.0))
            chance *= 0.85 + 0.30 * generator_core_v027.stable_unit(f"gems:{room_id}")
            if not pool or random.random() >= chance:
                return None
            weights = generator_core_v027.resource_weights(pool, ITEMS, effective, f"gems:{room_id}")
            base_id = random.choices(pool, weights=weights, k=1)[0]
            quality = roll_mined_gem_quality(tool_level, profession_level)
            if quality and quality != "normal":
                candidate = f"{base_id}_{quality}"
                if candidate in ITEMS:
                    return candidate
            return base_id

    def woodcutting_loot(self, tool_level, room_id=None):
            room_id = room_id or self.character.room_id
            tool_level = max(1, min(400, int(tool_level)))
            dungeon, dungeon_floor = profession_dungeon_floor(room_id)
            effective = tool_tier_access_level(tool_level)
            if dungeon == "ancient_forest":
                effective = min(effective, max(1, int(dungeon_floor) * 10))
            pool = generator_core_v027.resource_pool(
                tuple(WOOD_RESOURCE_IDS), ITEMS, effective, f"wood:{room_id}"
            )
            if not pool:
                return None
            weights = generator_core_v027.resource_weights(pool, ITEMS, effective, f"wood:{room_id}")
            return random.choices(pool, weights=weights, k=1)[0]

    def herbalism_loot(self, tool_level, room_id=None):
            room_id = room_id or self.character.room_id
            tool_level = max(1, min(400, int(tool_level)))
            dungeon, dungeon_floor = profession_dungeon_floor(room_id)
            effective = tool_tier_access_level(tool_level)
            if dungeon == "alchemy_garden":
                effective = min(effective, max(1, int(dungeon_floor) * 10))
            pool = generator_core_v027.resource_pool(
                tuple(HERB_RESOURCE_IDS), ITEMS, effective, f"herb:{room_id}"
            )
            if not pool:
                return None
            weights = generator_core_v027.resource_weights(pool, ITEMS, effective, f"herb:{room_id}")
            return random.choices(pool, weights=weights, k=1)[0]
