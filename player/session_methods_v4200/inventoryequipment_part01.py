# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
def parse_player_currency_transfer(self, payload):
        """Zwraca (amount_silver, opis) lub None, gdy payload nie jest walutą."""
        words = str(payload or "").strip().split()
        if len(words) < 2:
            return None
        amount = None
        unit = None
        if words[0].isdigit():
            amount = int(words[0])
            unit = " ".join(words[1:])
        elif words[-1].isdigit():
            amount = int(words[-1])
            unit = " ".join(words[:-1])
        else:
            return None
        multiplier = currency_unit_multiplier(unit)
        if multiplier is None:
            return None
        if amount <= 0:
            return (0, "")
        total = amount * int(multiplier)
        if total > CURRENCY_SQLITE_SAFE_TOTAL:
            return (CURRENCY_SQLITE_SAFE_TOTAL + 1, "")
        return total, currency_reading_text(total, 0, 0, full_names=True)


async def give_player(self, raw):
        """Przekazuje walutę albo zwykły przedmiot graczowi stojącemu obok."""
        text = str(raw or "").strip()
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await self.send(
                "Użycie: daj <gracz> <przedmiot>; daj <gracz> <ilość> <przedmiot>; "
                "daj <gracz> <ilość> złota."
            )
            return

        target_name, payload = parts[0].strip(), parts[1].strip()
        target = self.server.find_character_session(target_name)
        if target is None or target.closed or not target.character:
            await self.send(f"Gracz {target_name} nie jest teraz online.")
            return
        if target is self or target.account_id == self.account_id:
            await self.send("Nie możesz przekazać przedmiotu ani waluty samemu sobie.")
            return
        if target.character.room_id != self.character.room_id:
            await self.send(
                f"{target.character.name} nie znajduje się w tej samej lokacji. "
                "Przekazywanie działa tylko między graczami stojącymi obok."
            )
            return

        currency = self.parse_player_currency_transfer(payload)
        if currency is not None:
            amount_silver, description = currency
            if amount_silver <= 0:
                await self.send("Kwota musi być większa od zera.")
                return
            if amount_silver > CURRENCY_SQLITE_SAFE_TOTAL:
                await self.send("Ta kwota jest zbyt duża.")
                return
            sender_total = int(self.server.db.shared_wallet_for_character(self.account_id)[0])
            if sender_total < amount_silver:
                await self.send(
                    "Nie masz wystarczającej ilości waluty. Masz: "
                    + currency_reading_text(sender_total, 0, 0, full_names=True)
                    + "."
                )
                return
            if not self.server.db.transfer_shared_currency(
                self.account_id, target.account_id, amount_silver
            ):
                await self.send("Nie udało się przekazać waluty. Nic nie zostało zmienione.")
                return
            self.server.db.apply_shared_wallet_to_character(self.character)
            self.server.db.apply_shared_wallet_to_character(target.character)
            await self.send(
                f"Przekazujesz graczowi {target.character.name}: {description}.",
                history_category="system",
            )
            await target.send(
                f"{self.character.name} przekazuje ci: {description}.",
                history_category="system",
            )
            return

        qty = 1
        item_query = payload
        item_parts = payload.split(maxsplit=1)
        if item_parts and item_parts[0].isdigit():
            qty = int(item_parts[0])
            item_query = item_parts[1].strip() if len(item_parts) > 1 else ""
        if qty <= 0 or not item_query:
            await self.send("Ilość przedmiotów musi być dodatnia i trzeba podać nazwę przedmiotu.")
            return

        found = self.resolve_transferable_inventory_item(item_query)
        if not found:
            owned = {
                item_id: ITEMS.get(item_id, {"name": item_id})
                for item_id, qty in self._owned_inventory_quantities_v0717().items()
                if qty > 0
            }
            owned_found = find_by_name(owned, item_query)
            if owned_found:
                item_id, item = owned_found
                if is_character_bound_item(item_id):
                    await self.send(
                        f"{item['name']} jest przypisany do postaci i nie może być przekazany."
                    )
                elif item.get("type") == "quest":
                    await self.send(
                        f"{item['name']} jest przedmiotem questowym i nie może być przekazany."
                    )
                elif self.free_transferable_quantity(item_id) <= 0:
                    await self.send(
                        f"{item['name']} jest założony. Najpierw zdejmij wolną sztukę z EQ."
                    )
                else:
                    await self.send("Tego przedmiotu nie można teraz przekazać.")
            else:
                await self.send(
                    "Nie rozpoznaję takiego przedmiotu w twoim inventory. "
                    "Podaj pełną nazwę; ilość wpisz przed nazwą, np. daj Arven 3 Mikstura Leczenia."
                )
            return

        item_id, item = found
        free_qty = self.free_transferable_quantity(item_id)
        if free_qty < qty:
            await self.send(
                f"Masz tylko {free_qty} wolnych sztuk: {item['name']}."
            )
            return

        if not self.server.db.transfer_inventory_item(
            self.account_id, target.account_id, item_id, qty
        ):
            await self.send("Nie udało się przekazać przedmiotu. Nic nie zostało zmienione.")
            return

        # Zachowaj istniejące dane reforgingu/run tylko wtedy, gdy ostatnia
        # sztuka konkretnego EQ opuszcza konto nadawcy.
        if (
            item.get("type") == "armor"
            and self.server.db.item_qty(self.account_id, item_id) <= 0
        ):
            self.server.db.transfer_equipment_crafting_v0925(
                self.account_id, target.account_id, item_id
            )

        quantity_text = f"{qty} x " if qty != 1 else ""
        await self.send(
            f"Przekazujesz graczowi {target.character.name}: {quantity_text}{item['name']}.",
            history_category="system",
        )
        await target.send(
            f"{self.character.name} przekazuje ci: {quantity_text}{item['name']}.",
            history_category="system",
        )


async def inventory(self):
        rows = self.server.db.inventory(self.account_id)
        # v0.33.16: inventory pokazuje tylko WOLNE sztuki.
        # Baza zachowuje łączną ilość przedmiotu, również gdy konkretna sztuka
        # jest aktualnie założona. Odejmujemy więc każdą sztukę obecną w EQ
        # wyłącznie na potrzeby prezentacji inventory. Dzięki temu dwa identyczne
        # pierścienie/talizmany/kolczyki są liczone poprawnie sztuka po sztuce.
        equipped_counts = {}
        for equipped in self.server.db.equipment(self.account_id):
            equipped_id = str(equipped["item_id"])
            equipped_counts[equipped_id] = equipped_counts.get(equipped_id, 0) + 1

        await self.send(
            "Waluta: "
            + currency_reading_text(
                self.character.silver, self.character.gold, self.character.mithril,
                full_names=True, include_zero=True,
            )
            + "."
        )
        await self.send(
            "Siatka na ryby, Sakwa górnicza, Stos drewna, Torba Zielarska "
            "i Szkatułka Rzemieślnicza są osobnymi magazynami; użyj siatka/net, "
            "sakwa/bag, drewno/stos, ziola/herbs oraz szkatułka/craftbox."
        )
        visible_rows = []
        for row in rows:
            item_id = str(row["item_id"])
            visible_quantity = max(
                0,
                int(row["quantity"]) - int(equipped_counts.get(item_id, 0)),
            )
            if visible_quantity > 0:
                visible_rows.append((row, visible_quantity))

        if not visible_rows:
            await self.send("Ekwipunek jest pusty.")
            return
        await self.send("Ekwipunek:")
        for row, visible_quantity in visible_rows:
            item = ITEMS.get(row["item_id"]) or ensure_crafting_quality_variant_v0332(row["item_id"]) or {"name": player_item_display_name_v0335(row["item_id"]), "desc": ""}
            bound_text = (
                " Przypisany do postaci; nie można oddać ani wyrzucić."
                if is_character_bound_item(row["item_id"])
                else ""
            )
            await self.send(
                f"{item['name']} x{visible_quantity}. "
                f"{self.item_runtime_description(str(row['item_id']), item)}{bound_text}"
            )


async def inspect_equipped_v1225(self, query):
        rows = self.server.db.equipment(self.account_id)
        if not rows:
            await self.send("Nie masz założonego dodatkowego wyposażenia.")
            return
        key = normalize_lookup_text(str(query or "").strip())
        matches = []
        for index, row in enumerate(rows, 1):
            item_id = str(row["item_id"])
            item = ITEMS.get(item_id) or ensure_crafting_quality_variant_v0332(item_id)
            slot = str(row["slot"])
            labels = {"head":"glowa", "body":"korpus", "hands":"dlonie",
                "legs":"nogi", "feet":"stopy", "shield":"tarcza", "ring":"pierscien",
                "necklace":"naszyjnik", "charm":"talizman", "cloak":"peleryna",
                "shoulders":"naramienniki", "belt":"pas", "bracers":"karwasze",
                "board":"board", "relic":"relikt"}
            name = str(item.get("name", item_id)) if item else item_id
            candidates = {str(index), normalize_lookup_text(slot),
                normalize_lookup_text(labels.get(slot, slot)), normalize_lookup_text(name),
                normalize_lookup_text(item_id)}
            if key in candidates or (len(key)>2 and key in normalize_lookup_text(name)):
                matches.append((index, row, item, name))
        if not matches:
            await self.send("Nie masz takiego przedmiotu na sobie. Wpisz eq, aby poznać sloty, lub eq info po wszystkie bonusy.")
            return
        if len(matches)>1:
            await self.send("Znaleziono kilka założonych przedmiotów: " + "; ".join(
                f"{n}. {row['slot']}: {name}" for n,row,item,name in matches) + ". Podaj numer z listy eq.")
            return
        n,row,item,name = matches[0]
        await self.send(f"EQ INFO: pozycja {n}, slot {row['slot']}. {name}.")
        if not item:
            await self.send("Brak danych katalogowych tego przedmiotu.")
            return
        await self.send(self.format_item_description(str(row['item_id']),item))
        level = self.server.db.equipment_upgrade_level_v03042(self.account_id,row['item_id'])
        if level:
            await self.send(f"Ulepszenie Kowalstwa: +{level}. Premia obrony z ulepszenia: +{v03042_upgrade_defense_bonus(item,level)}.")
        if item.get('slot') in ('ring','necklace'):
            await self.send(self.jewelry_socket_text(str(row['slot']),str(row['item_id']),item))
        await self.send("Przedmiot pozostaje założony. Nic nie zostało zmienione.")


async def equipment(self, mode=""):
        mode = self.normalize_description_query(mode)
        if mode.startswith('info ') or mode.startswith('szczegoly ') or mode.startswith('szczegóły '):
            await self.inspect_equipped_v1225(mode.split(' ',1)[1])
            return
        if mode in ("auto", "automatycznie", "najlepsze", "best"):
            await self.auto_equip_best_v03040()
            return
        detailed = mode in (
            "info", "pelne", "pełne", "szczegoly", "szczegóły", "details"
        )
        rows = self.server.db.equipment(self.account_id)

        await self.send("EQ INFO" if detailed else "EQ")
        c = self.character
        soul_line = (
            f"Broń Duszy: {c.soul_weapon}. "
            f"Soul Poziom {c.soul_level}/{SOUL_MAX_LEVEL}. "
            f"Soul Tier {c.soul_tier}/{SOUL_MAX_TIER} — {soul_tier_title_for_class(c.soul_tier, c.class_name)}. "
            f"Moc {c.soul_power()}."
        )
        if detailed:
            if c.soul_level < SOUL_MAX_LEVEL:
                soul_line += f" Soul XP {c.soul_xp} z {c.soul_xp_to_next()}."
            else:
                soul_line += " Soul XP maksimum."
            soul_line += f" Bonus klasowy: {c.soul_weapon_class_bonus_text()}."
        await self.send(soul_line)

        if not rows:
            await self.send("Nie masz założonego dodatkowego wyposażenia.")

        slot_names = {
            "head": "Głowa", "body": "Korpus", "hands": "Dłonie",
            "legs": "Nogi", "feet": "Stopy", "charm": "Talizman",
            "charm1": "Talizman 1", "charm2": "Talizman 2",
            "shield": "Tarcza",
            "ring": "Pierścień", "ring1": "Pierścień 1",
            "ring2": "Pierścień 2", "necklace": "Naszyjnik",
            "earring1": "Kolczyk 1", "earring2": "Kolczyk 2",
            "shoulders": "Naramienniki", "belt": "Pas", "cloak": "Peleryna",
            "bracers": "Karwasze", "bracelet": "Bransoletka", "relic": "Relikt", "accessory1": "Akcesorium 1", "accessory2": "Akcesorium 2", "board": "Board",
        }
        for row in rows:
            item = ITEMS.get(row["item_id"]) or ensure_crafting_quality_variant_v0332(row["item_id"])
            upgrade_level = self.server.db.equipment_upgrade_level_v03042(
                self.account_id, row["item_id"]
            ) if item else 0
            base_name = item["name"] if item else player_item_display_name_v0335(row["item_id"])
            name = v03042_upgraded_display_name(base_name, upgrade_level)
            defense = (
                int(item.get("defense", 0) or 0)
                + v03042_upgrade_defense_bonus(item, upgrade_level)
                if item else 0
            )
            slot_name = slot_names.get(row["slot"], row["slot"])
            if not detailed:
                socket_short = ""
                if item and item.get("slot") in ("ring", "necklace"):
                    capacity = jewelry_socket_capacity(item)
                    occupied = len(self.socketed_gem_rows_for_item(row["slot"], row["item_id"]))
                    socket_short = f" Gniazda {occupied}/{capacity}."
                await self.send(f"{slot_name}: {name}. Obrona +{defense}.{socket_short}")
                continue

            extra = ""
            if item and upgrade_level > 0:
                upgrade_stat = v03042_upgrade_primary_stat(
                    item,
                    str((self.server.db.equipment_reforge(self.account_id, row["item_id"]) or {}).get("affix") or item.get("affix") or ""),
                )
                upgrade_amount = v03042_upgrade_stat_bonus(upgrade_level)
                stat_label = CLASS_SET_STAT_NAMES.get(upgrade_stat, upgrade_stat)
                extra += (
                    f" Ulepszenie Kowalstwa +{upgrade_level}/{V03042_EQ_UPGRADE_MAX}: "
                    f"obrona po ulepszeniu +{defense}"
                    + (f", {stat_label} +{upgrade_amount}." if upgrade_amount > 0 else ".")
                )
            if item and item.get("rarity_name"):
                extra += f" Rzadkość: {item['rarity_name']}."
            if item and item.get("affix"):
                affix_name = CRYPT_AFFIXES.get(item["affix"], item["affix"])
                extra += f" Bonus: {affix_name} +{item.get('affix_amount', 0)}."
            if item and item.get("status_proof"):
                extra += " Odporności statusowe: " + ", ".join(map(str, item.get("status_proof") or ())) + "."
            if item and item.get("element_wards"):
                _wards = ", ".join(f"{name} {int(round(float(value)*100))}%" for name,value in (item.get("element_wards") or {}).items())
                if _wards:
                    extra += " Wardy: " + _wards + "."
            if item and float(item.get("mp_cost_multiplier",1.0) or 1.0) != 1.0:
                extra += f" Mnożnik kosztu MP x{float(item.get('mp_cost_multiplier')):g}."
            if item and item.get("reraise_once"):
                extra += " Re-raise: jednorazowy; przedmiot znika po aktywacji."
            if item and item.get("source_effects"):
                extra += " Efekty źródłowe: " + ", ".join(map(str,item.get("source_effects") or ())) + "."
            if item:
                _flat = []
                for _key, _label in (("attack","Attack"),("magic_attack","Magic Attack"),("magic_defense","Magic Defense"),("weapon_power","Weapon Power")):
                    _value = int(item.get(_key, 0) or 0)
                    if _value:
                        _flat.append(f"{_label} +{_value}")
                if _flat:
                    extra += " Power: " + ", ".join(_flat) + "."
            if item:
                _multi_eq = crossover_text_v3001(item)
                if _multi_eq:
                    extra += " " + _multi_eq
            if item and item.get("stats"):
                fixed_stats = ", ".join(
                    f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{amount}"
                    for stat, amount in item.get("stats", {}).items()
                    if int(amount or 0) != 0
                )
                if fixed_stats:
                    extra += f" Statystyki bazowe: {fixed_stats}."
            if item and item.get("soulbound_balance_stats"):
                balance_stats = ", ".join(
                    f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{amount}"
                    for stat, amount in item.get("soulbound_balance_stats", {}).items()
                    if int(amount or 0) != 0
                )
                if balance_stats:
                    extra += f" Bonus Soulbound: {balance_stats}."
            if item and item.get("cyborg_board_scaling") == "character_level":
                _level = int(self.character.character_level)
                _mb = moogle_board_stat_bonus_v0313(_level)
                extra += f" Skalowanie Moogle Board: Level postaci {_level}/{CHARACTER_MAX_LEVEL}, +{_mb} do Siły, Zręczności, Kondycji, Inteligencji i Siły Woli. Level 150 daje +20; od Levelu 151 każdy kolejny Level zwiększa bonus o +2."
            if item and item.get("slot") in ("ring", "necklace"):
                extra += " " + self.jewelry_socket_text(row["slot"], row["item_id"], item)
            await self.send(f"{slot_name}: {name}. Obrona +{defense}.{extra}")

        if not detailed:
            await self.send(
                f"Łączna obrona fizyczna: {self.defense()}. Wpisz eq info po bonusy i sety albo eq info 1 po opis założonego przedmiotu."
            )
            return

        bonuses = self.equipment_bonus_totals()
        await self.send(
            f"Łączna obrona fizyczna: {self.defense()}. Obrona magiczna: {self.magic_defense()}."
        )
        await self.send(
            "Łączne bonusy EQ i socketów: "
            f"Siła +{bonuses['strength']}, Zręczność +{bonuses['dexterity']}, "
            f"Kondycja +{bonuses['constitution']}, Inteligencja +{bonuses['intelligence']}, "
            f"Siła Woli +{bonuses['willpower']}, HP +{bonuses['hp']}, Mana +{bonuses['mana']}."
        )
        await self.send(
            f"Efektywne staty: Siła {self.effective_strength()}, Zręczność {self.effective_dexterity()}, "
            f"Kondycja {self.effective_constitution()}, Inteligencja {self.effective_intelligence()}, "
            f"Siła Woli {self.effective_willpower()}."
        )
        await self.send(self.crypt_set_bonus_text())
        await self.send(self.astral_set_bonus_text())
        for line in self.class_set_status_lines():
            await self.send(line)
        for line in self.regional_set_status_lines():
            await self.send(line)
        await self.send("Regionalne sety mają progi 2/4/6. Komenda sety pokazuje progi 2/4/6/8 wszystkich zestawów klasowych.")
        await self.send("Komenda gniazda pokazuje dokładnie osadzone klejnoty w biżuterii.")


async def show_class_sets(self, query=""):
        q = self.normalize_description_query(query)
        counts = self.class_set_counts()

        if q in ("", "aktywne", "active"):
            await self.send("SETY KLASOWE")
            any_set = False
            for class_name in self.active_class_names():
                count = int(counts.get(class_name, 0))
                if count <= 0:
                    continue
                any_set = True
                await self.send(
                    f"{class_name}: {count}/14 części. Bonusy kończą się na progu 8. "
                    f"{self.class_set_threshold_text(class_name)}."
                )
            if not any_set:
                await self.send("Nie masz założonej części aktywnego setu klasowego.")
            await self.send(
                "Wpisz sety info po wszystkie 14 zestawów albo sety <klasa>."
            )
            return

        if q in ("info", "wszystkie", "all", "pelne", "pełne"):
            await self.send("SETY KLASOWE 2/4/6/8 - WSZYSTKIE KLASY")
            for class_name in CLASS_EQUIPMENT_SETS:
                set_name = CLASS_EQUIPMENT_SETS[class_name]["set_name"]
                await self.send(
                    f"{class_name}, Zestaw {set_name}. "
                    f"{self.class_set_threshold_text(class_name)}."
                )
            return

        found = None
        for class_name in CLASS_EQUIPMENT_SETS:
            if q == self.normalize_description_query(class_name):
                found = class_name
                break
        if not found:
            await self.send(
                "Nie rozpoznaję klasy. Wpisz sety info po listę wszystkich 14 zestawów."
            )
            return

        set_name = CLASS_EQUIPMENT_SETS[found]["set_name"]
        count = int(counts.get(found, 0))
        await self.send(
            f"SET {found}: Zestaw {set_name}. Masz założone {count}/14 części; bonusy aktywują się na 2/4/6/8."
        )
        await self.send(self.class_set_threshold_text(found) + ".")
        await self.send(
            "Czternaście logicznych części to: głowa, korpus, dłonie, nogi, stopy, talizman, "
            "pierścień, naszyjnik, kolczyki, naramienniki, pas, peleryna, karwasze i relikt. "
            "Drugi taki sam talizman, pierścień ani kolczyk nie zwiększa licznika setu."
        )


def equipment_item_score(self, item):
        if not item:
            return (-1, -1, -1, "")
        rarity_order = {
            "common": 0,
            "crafted": 1,
            "rare": 2,
            "epic": 3,
            "legendary": 4,
            "mythic": 5,
            "unique": 6,
            "eternal": 7,
        }
        stat_power = int(item.get("affix_amount", 0) or 0) + sum(
            max(0, int(v or 0)) for v in (item.get("stats") or {}).values()
        ) + sum(
            max(0, int(v or 0)) for v in (item.get("soulbound_balance_stats") or {}).values()
        )
        return (
            int(item.get("defense", 0) or 0),
            rarity_order.get(item.get("rarity"), 0),
            stat_power,
            normalize_lookup_text(item.get("name", "")),
        )


def auto_equipment_stat_weight_v11196(self, stat):
        """Class-aware AUTO EQ weighting without changing item stats."""
        stat = str(stat or "")
        active = tuple(self.active_class_names())
        best = 0.20
        for class_name in active:
            primary, secondary = class_equipment_base_stat_pair(class_name)
            if stat == primary:
                best = max(best, 1.00)
            elif stat == secondary:
                best = max(best, 0.85)
            elif stat == "constitution":
                best = max(best, 0.55)
            elif stat == "dexterity":
                best = max(best, 0.45)
            elif stat == "willpower":
                best = max(best, 0.35)
            elif stat == "intelligence":
                best = max(best, 0.30)
            elif stat == "strength":
                best = max(best, 0.30)
            if class_name == "Mec":
                best = max(best, {
                    "strength": 0.75, "dexterity": 1.00, "constitution": 0.90,
                    "intelligence": 0.70, "willpower": 0.70,
                }.get(stat, 0.20))
            elif class_name == "Mnich" and stat == "willpower":
                best = max(best, 0.60)
        return best

