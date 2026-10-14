# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
def auto_equipment_property_weight_v11196(self, prop):
        prop = str(prop or "")
        active = tuple(self.active_class_names())
        physical = any(class_equipment_base_stat_pair(name)[0] in {"strength", "dexterity"} for name in active)
        magic = any(class_equipment_base_stat_pair(name)[0] == "intelligence" for name in active)
        if prop == "physical_damage_pct":
            return 1.0 if physical else 0.20
        if prop == "magic_damage_pct":
            return 1.0 if magic or "Mec" in active else 0.20
        if prop == "max_mana_pct":
            return 1.0 if magic or "Mec" in active else 0.35
        if prop in {"max_hp_pct", "physical_defense_pct", "magic_defense_pct", "dodge_pct", "all_damage_pct", "lifesteal_percent", "mana_restore_percent"}:
            return 1.0
        return 0.50


def auto_equipment_score_v03040(self, item, item_id=None):
        """Porównanie indywidualnej mocy EQ dla opcjonalnego trybu auto.

        Nie zmienia balansu przedmiotów. Uwzględnia obronę, bazowe staty,
        właściwości procentowe, affix, rarity oraz pojemność gniazd biżuterii.
        """
        if not item or item.get("type") != "armor":
            return (-1, -1, -1, -1, -1, "")
        rarity_order = {
            "common": 0, "crafted": 1, "uncommon": 1, "rare": 2,
            "epic": 3, "legendary": 4, "mythic": 5, "unique": 6,
            "eternal": 7,
        }
        upgrade_level = (
            self.server.db.equipment_upgrade_level_v03042(self.account_id, item_id)
            if item_id else 0
        )
        defense = max(0, int(item.get("defense", 0) or 0)) + v03042_upgrade_defense_bonus(item, upgrade_level)
        stats = sum(
            max(0, int(v or 0)) * self.auto_equipment_stat_weight_v11196(stat)
            for stat, v in (item.get("stats") or {}).items()
        )
        stats += sum(
            max(0, int(v or 0)) * self.auto_equipment_stat_weight_v11196(stat)
            for stat, v in (item.get("soulbound_balance_stats") or {}).items()
        )
        _cross_stats, _cross_power = crossover_bonus_v3001(item)
        stats += sum(
            max(0, int(v)) * self.auto_equipment_stat_weight_v11196(stat)
            for stat, v in _cross_stats.items()
        )
        affix_stat = str(item.get("affix") or "")
        affix = max(0, int(item.get("affix_amount", 0) or 0)) * self.auto_equipment_stat_weight_v11196(affix_stat)
        upgrade_stat = v03042_upgrade_primary_stat(item, affix_stat)
        stats += v03042_upgrade_stat_bonus(upgrade_level) * self.auto_equipment_stat_weight_v11196(upgrade_stat)
        props = sum(
            max(0.0, float(v or 0.0)) * self.auto_equipment_property_weight_v11196(prop)
            for prop, v in (item.get("properties") or {}).items()
        )
        active = tuple(self.active_class_names())
        physical = any(class_equipment_base_stat_pair(name)[0] in {"strength", "dexterity"} for name in active)
        magic = any(class_equipment_base_stat_pair(name)[0] == "intelligence" for name in active)
        flat_power = 0.0
        flat_power += max(0, int(item.get("attack", 0) or 0)) * (1.0 if physical else 0.30)
        flat_power += max(0, int(item.get("weapon_power", 0) or 0)) * (1.0 if physical else 0.30)
        flat_power += max(0, int(item.get("magic_attack", 0) or 0)) * (1.0 if magic or "Mec" in active else 0.30)
        flat_power += _cross_power.get("attack",0) * (1.0 if physical else 0.30)
        flat_power += _cross_power.get("magic_attack",0) * (1.0 if magic or "Mec" in active else 0.30)
        flat_power += max(0, int(item.get("magic_defense", 0) or 0)) * 0.65
        # Source-backed special defenses must participate in AUTO EQ too.
        # Ward values are fractions (0.65 = 65%), while status proofs are
        # binary immunities. This affects comparison only; it does not invent
        # new combat effects for source items whose values are unknown.
        ward_score = int(round(sum(max(0.0, min(1.0, float(v or 0.0))) for v in (item.get("element_wards") or {}).values()) * 100.0))
        proof_score = 25 * len(tuple(item.get("status_proof") or ()))
        special_score = ward_score + proof_score + (25 if item.get("reraise_once") else 0)
        rarity = rarity_order.get(str(item.get("rarity") or "").lower(), 0)
        sockets = 0
        if item.get("slot") in ("ring", "earring", "necklace"):
            try:
                sockets = max(0, int(jewelry_socket_capacity(item)))
            except Exception:
                sockets = 0
        total = defense * 12 + stats * 8 + props * 10 + affix * 8 + flat_power * 8 + rarity * 5 + sockets * 3 + special_score
        return (
            total, defense, stats + affix + flat_power, props, rarity,
            normalize_lookup_text(item.get("name", "")),
        )


async def auto_equip_best_v03040(self):
        """Jednym poleceniem zakłada indywidualnie najmocniejsze dostępne EQ.

        Działa wyłącznie na posiadanych i aktualnie dozwolonych przedmiotach.
        Podwójne sloty respektują faktyczną liczbę posiadanych kopii.
        """
        if self.combat_mob_key:
            await self.send(
                "Nie możesz automatycznie zmieniać EQ podczas aktywnej walki. "
                "Najpierw zakończ walkę albo użyj flee."
            )
            return

        active_classes = set(self.active_class_names())
        owned = {}
        for item_id, qty in self._owned_inventory_quantities_v0717().items():
            item = ITEMS.get(item_id)
            if not item or item.get("type") != "armor":
                continue
            required_level = max(0, int(item.get("required_level", 0) or 0))
            if required_level and int(self.character.character_level) < required_level:
                continue
            required_class = None if item.get("universal_all_classes") else item.get("required_class")
            if required_class and required_class not in active_classes:
                continue
            required_race = item.get("required_race")
            if required_race and str(self.character.race) != str(required_race):
                continue
            if not self.equipment_mastery_requirement_met(item):
                continue
            owned[item_id] = (item, qty)

        if not owned:
            await self.send("AUTO EQ: nie masz żadnego dostępnego EQ do założenia.")
            return

        changes = []
        returned_gems = []
        equipped_rows_v0717 = self.server.db.equipment(self.account_id)
        equipped_by_slot_v0717 = {
            str(row["slot"]): str(row["item_id"]) for row in equipped_rows_v0717
        }
        single_slots = (
            "head", "body", "hands", "legs", "feet", "shield", "necklace",
            "shoulders", "belt", "cloak", "bracers", "bracelet", "relic", "board",
        )

        for slot in single_slots:
            candidates = [
                (self.auto_equipment_score_v03040(item, item_id), item_id, item)
                for item_id, (item, qty) in owned.items()
                if qty > 0 and item.get("slot") == slot
            ]
            if not candidates:
                continue
            candidates.sort(key=lambda row: row[0], reverse=True)
            _score, best_id, best_item = candidates[0]
            old_id = equipped_by_slot_v0717.get(slot)
            old_item = ITEMS.get(old_id) if old_id else None
            if old_id == best_id:
                continue
            if old_item and self.auto_equipment_score_v03040(old_item, old_id) >= self.auto_equipment_score_v03040(best_item, best_id):
                continue
            if slot == "necklace" and old_id:
                returned_gems.extend(await self.return_socketed_gems(slot, old_id))
            self.server.db.equip(self.account_id, slot, best_id, commit=False)
            equipped_by_slot_v0717[slot] = best_id
            changes.append((slot, old_item.get("name", old_id) if old_item else "pusty", best_item.get("name", best_id)))

        duals = {
            "ring": ("ring1", "ring2"),
            "charm": ("charm1", "charm2"),
            "earring": ("earring1", "earring2"),
            "accessory": ("accessory1", "accessory2"),
        }
        for logical_slot, pair in duals.items():
            # v0.33.11: dual-slot auto-equip must compare the two currently
            # equipped pieces as well as owned inventory candidates. Older
            # saves may have equipped jewelry whose inventory quantity is 0,
            # and those pieces must still participate in the ranking.
            candidate_counts = {}
            candidate_items = {}
            for item_id, (item, qty) in owned.items():
                item_slot = str(item.get("slot") or "")
                if item_slot not in (logical_slot, pair[0], pair[1]):
                    continue
                candidate_counts[item_id] = max(candidate_counts.get(item_id, 0), max(0, int(qty)))
                candidate_items[item_id] = item

            current_by_slot = {}
            equipped_counts = {}
            for slot in pair:
                cur = equipped_by_slot_v0717.get(slot)
                if not cur:
                    continue
                current_by_slot[slot] = cur
                cur_item = ITEMS.get(cur)
                if not cur_item:
                    continue
                cur_slot = str(cur_item.get("slot") or "")
                if cur_slot not in (logical_slot, pair[0], pair[1]):
                    continue
                candidate_items[cur] = cur_item
                equipped_counts[cur] = equipped_counts.get(cur, 0) + 1

            for item_id, count in equipped_counts.items():
                candidate_counts[item_id] = max(candidate_counts.get(item_id, 0), count)

            expanded = []
            for item_id, count in candidate_counts.items():
                item = candidate_items.get(item_id)
                if not item:
                    continue
                for _ in range(min(2, max(0, int(count)))):
                    expanded.append((self.auto_equipment_score_v03040(item, item_id), item_id, item))
            if not expanded:
                continue
            expanded.sort(key=lambda row: row[0], reverse=True)
            selected = expanded[:2]

            # Build the desired top-two multiset.
            wanted_counts = {}
            selected_score = {}
            for score, item_id, item in selected:
                wanted_counts[item_id] = wanted_counts.get(item_id, 0) + 1
                selected_score[item_id] = score

            desired = {}
            # Preserve an existing ring only when that exact copy belongs to
            # the final top-two set. This prevents needless slot shuffling.
            remaining = dict(wanted_counts)
            for slot in pair:
                cur = current_by_slot.get(slot)
                if cur and remaining.get(cur, 0) > 0:
                    desired[slot] = cur
                    remaining[cur] -= 1

            rest = []
            for score, item_id, item in selected:
                if remaining.get(item_id, 0) > 0:
                    rest.append((score, item_id, item))
                    remaining[item_id] -= 1

            # Fill empty/non-top slots with the strongest remaining pieces.
            for slot in pair:
                if slot not in desired and rest:
                    _score, item_id, _item = rest.pop(0)
                    desired[slot] = item_id

            for slot in pair:
                target_id = desired.get(slot)
                if not target_id:
                    continue
                old_id = equipped_by_slot_v0717.get(slot)
                if old_id == target_id:
                    continue
                target_item = ITEMS[target_id]
                old_item = ITEMS.get(old_id) if old_id else None
                if logical_slot in ("ring", "earring") and old_id:
                    returned_gems.extend(await self.return_socketed_gems(slot, old_id))
                self.server.db.equip(self.account_id, slot, target_id, commit=False)
                equipped_by_slot_v0717[slot] = target_id
                changes.append((slot, old_item.get("name", old_id) if old_item else "pusty", target_item.get("name", target_id)))

        if changes:
            self.server.db.conn.commit()

        self.current_hp = min(self.current_hp, self.max_hp())
        self.current_mana = min(self.current_mana, self.max_mana())

        if not changes:
            await self.send("AUTO EQ: masz już najmocniejsze dostępne indywidualne części według statystyk EQ.")
            return

        await self.send(f"AUTO EQ: zmieniono {len(changes)} slotów.")
        for slot, old_name, new_name in changes:
            await self.send(
                f"{EQUIPMENT_SLOT_NAMES.get(slot, slot)}: {old_name} -> {new_name}."
            )
        if returned_gems:
            await self.send(
                f"Z wymienionej biżuterii zwrócono {len(returned_gems)} klejnotów do Szkatułki Rzemieślniczej."
            )
        await self.send(
            "Auto EQ porównuje moc części pod aktywne klasy: właściwe statystyki ofensywne, Kondycję/Siłę Woli, "
            "Attack, Magic Attack, Weapon Power, obronę, właściwości, affix, rarity i gniazda. "
            "Nie zmienia przedmiotów niedostępnych przez Poziom postaci lub klasę."
        )


def owned_armor_for_slot(self, slot):
        candidates = []
        if slot in ("accessory1", "accessory2"):
            logical_slot = "accessory"
        elif slot in ("ring1", "ring2"):
            logical_slot = "ring"
        elif slot in ("charm1", "charm2"):
            logical_slot = "charm"
        elif slot in ("earring1", "earring2"):
            logical_slot = "earring"
        else:
            logical_slot = slot
        for item_id, quantity in self._owned_inventory_quantities_v0717().items():
            item = ITEMS.get(item_id)
            if not item or item.get("type") != "armor":
                continue
            if item.get("slot") != logical_slot:
                continue
            # Lista wyboru pokazuje wszystkie posiadane części tego slotu,
            # również te jeszcze zablokowane Biegłością/klasą.
            score = self.equipment_item_score(item)
            candidates.append((score, item_id, item))

        candidates.sort(key=lambda entry: entry[0], reverse=True)
        return candidates


def explicit_dual_slot_and_item_query(self, query):
        """Return (slot, remaining item query) for numbered ring/charm/earring/accessory syntax.

        Accepted examples:
        - załóż pierścień 1 <nazwa>
        - załóż <nazwa> pierścień 1
        - equip ring2 <name>
        - equip <name> charm1
        """
        raw = str(query or "").strip()
        normalized = self.normalize_description_query(raw)
        aliases = (
            ("pierścień 1", "ring1"), ("pierscien 1", "ring1"),
            ("ring 1", "ring1"), ("ring1", "ring1"),
            ("pierścień 2", "ring2"), ("pierscien 2", "ring2"),
            ("ring 2", "ring2"), ("ring2", "ring2"),
            ("talizman 1", "charm1"), ("charm 1", "charm1"), ("charm1", "charm1"),
            ("talizman 2", "charm2"), ("charm 2", "charm2"), ("charm2", "charm2"),
            ("kolczyk 1", "earring1"), ("earring 1", "earring1"), ("earring1", "earring1"),
            ("kolczyk 2", "earring2"), ("earring 2", "earring2"), ("earring2", "earring2"),
            ("akcesorium 1", "accessory1"), ("accessory 1", "accessory1"), ("accessory1", "accessory1"),
            ("akcesorium 2", "accessory2"), ("accessory 2", "accessory2"), ("accessory2", "accessory2"),
        )
        for alias, slot in aliases:
            alias_norm = self.normalize_description_query(alias)
            prefix = alias_norm + " "
            suffix = " " + alias_norm
            if normalized.startswith(prefix):
                # Slice by words rather than normalized character count so Polish diacritics are safe.
                alias_words = len(alias.split())
                rest = " ".join(raw.split()[alias_words:]).strip()
                return slot, rest
            if normalized.endswith(suffix):
                alias_words = len(alias.split())
                rest = " ".join(raw.split()[:-alias_words]).strip()
                return slot, rest
        return None, raw


def equipped_jewelry(self, slot):
        if slot in ("ring", "earring"):
            pair = ("ring1", "ring2") if slot == "ring" else ("earring1", "earring2")
            slot = pair[0] if self.server.db.equipped_item(self.account_id, pair[0]) else pair[1]
        valid = ("ring1", "ring2", "earring1", "earring2", "necklace")
        if slot not in valid:
            return None, None
        item_id = self.server.db.equipped_item(self.account_id, slot)
        item = ITEMS.get(item_id) if item_id else None
        if slot in ("ring1", "ring2"):
            logical = "ring"
        elif slot in ("earring1", "earring2"):
            logical = "earring"
        else:
            logical = slot
        if not item or item.get("slot") != logical:
            return None, None
        return item_id, item


def jewelry_socket_text(self, slot, item_id, item):
        capacity = jewelry_socket_capacity(item)
        if capacity <= 0:
            return "Brak gniazd."

        rows = self.socketed_gem_rows_for_item(
            slot,
            item_id,
        )
        if not rows:
            return f"Gniazda: 0 z {capacity} zajętych."

        names = [
            ITEMS.get(row["gem_id"], {"name": row["gem_id"]})["name"]
            for row in rows
        ]
        return (
            f"Gniazda: {len(rows)} z {capacity} zajętych. "
            f"Klejnoty: {', '.join(names)}."
        )


async def return_socketed_gems(self, slot, item_id=None):
        rows = list(
            self.server.db.socketed_gems(
                self.account_id,
                slot,
                item_id,
            )
            if item_id
            else self.server.db.socketed_gems(
                self.account_id,
                slot,
            )
        )
        if not rows:
            return []

        self.server.db.clear_socketed_gems(
            self.account_id,
            slot,
        )
        returned = []
        for row in rows:
            gem_id = row["gem_id"]
            if gem_id in ITEMS:
                self.server.db.add_item(
                    self.account_id,
                    gem_id,
                    1,
                )
                returned.append(gem_id)
        return returned


async def show_geodes(self):
        await self.send("GEODY")
        rows = {row["item_id"]: int(row["quantity"]) for row in self.server.db.storage_rows(self.account_id, "bag")}
        total = 0
        for geode_id, cfg in GEODE_DEFINITIONS.items():
            qty = rows.get(geode_id, 0)
            total += qty
            await self.send(
                f"{cfg['name']}: {qty}. Kilof {cfg['min_tool']}+, głębokość {cfg['min_floor']}+."
            )
        if total:
            await self.send("Otwieranie: open geode / otwórz geodę. Możesz też podać nazwę, np. otwórz geodę kryształową.")
        else:
            await self.send("Nie masz obecnie geod w Sakwie Górnika.")


def _find_owned_geode(self, query=""):
        rows = {row["item_id"]: int(row["quantity"]) for row in self.server.db.storage_rows(self.account_id, "bag")}
        owned = {gid: ITEMS[gid] for gid in GEODE_IDS if rows.get(gid, 0) > 0}
        if not owned:
            return None
        q = self.normalize_description_query(str(query or "").strip())
        for token in ("geoda", "geode", "geodę", "geodee"):
            q = q.replace(token, " ").strip()
        if q:
            found = find_by_name(owned, q)
            if found:
                return found[0]
        # Bez nazwy otwieramy najlepszą posiadaną geodę.
        priority = ("astral_geode", "crystal_geode", "stone_geode")
        return next((gid for gid in priority if gid in owned), None)


async def open_geode(self, query=""):
        geode_id = self._find_owned_geode(query)
        if not geode_id:
            await self.send("Nie masz takiej geody w Sakwie Górnika. Wpisz geody / geodes.")
            return False
        if not self.server.db.remove_storage_item(self.account_id, "bag", geode_id, 1):
            await self.send("Nie udało się pobrać geody z Sakwy Górnika.")
            return False
        cfg = GEODE_DEFINITIONS[geode_id]
        eligible = [d for d in GEM_DEFINITIONS if int(d["level"]) <= int(cfg["max_gem_level"])]
        weights = list(range(len(eligible), 0, -1))
        low_qty, high_qty = cfg["gem_qty"]
        quantity = random.randint(int(low_qty), int(high_qty))
        rewards = []
        rolled_qualities = []
        for _ in range(quantity):
            definition = random.choices(eligible, weights=weights, k=1)[0]
            quality = random.choices(GEM_QUALITY_ORDER, weights=cfg["quality_weights"], k=1)[0]
            rolled_qualities.append(quality)
            gem_id = gem_quality_item_id("raw", definition["key"], quality)
            self.store_profession_resource(gem_id, 1)
            await self.record_item_collection(
                gem_id, source=cfg["name"], announce=True, record_history=False
            )
            rewards.append(ITEMS[gem_id]["name"])
        gold_low, gold_high = cfg["gold"]
        gold = random.randint(int(gold_low), int(gold_high))
        if gold > 0:
            self.character.gold += gold
        shard = False
        if geode_id == "astral_geode" and random.random() < 0.08:
            self.server.db.add_item(self.account_id, "soul_shard", 1)
            shard = True
        self.server.db.save_character(self.character)
        await self.send(f"Otwierasz {cfg['name']}. Klejnoty: " + ", ".join(rewards) + ".")
        if "perfect" in rolled_qualities:
            await self.send(
                "JACKPOT GEODY: trafiasz Perfekcyjny klejnot — najwyższą jakość tego systemu."
            )
        elif "excellent" in rolled_qualities:
            await self.send(
                "ŚWIETNY WYNIK GEODY: trafiasz Doskonały klejnot."
            )
        if gold > 0:
            await self.send("W geodzie znajdujesz także " + currency_reading_text(0, gold, 0) + ".")
        if shard:
            await self.send("Rzadkie znalezisko: Odłamek Duszy x1.")
        return True


async def show_gems(self):
        await self.send("KAMIENIE SZLACHETNE")
        await self.send(
            "Surowe kamienie wypadają dodatkowo podczas Górnictwa i trafiają do Sakwy Górnika. "
            "Po oszlifowaniu stają się materiałem jubilerskim i automatycznie trafiają do Szkatułki Rzemieślniczej."
        )
        await self.send(
            "Jakości: Surowy, Czysty, Doskonały, Perfekcyjny. Lepszy Kilof i wyższe Górnictwo "
            "zwiększają szansę jakości; Perfekcyjny pozostaje rzadkim jackpotem. Geody dają dodatkową "
            "szansę na klejnoty: geody / geodes."
        )
        for definition in GEM_DEFINITIONS:
            await self.send(
                f"{definition['raw_name']} -> "
                f"{definition['cut_name']}. "
                f"Wymaga Górnictwa {definition['mining_level']} "
                f"i głębokości {definition['min_floor']}. "
                f"Szlifowanie: Jubilerstwo {definition['level']}. "
                f"Bonus: "
                f"{GEM_AFFIX_NAMES.get(definition['affix'], definition['affix'])} "
                f"+{definition['amount']}."
            )

