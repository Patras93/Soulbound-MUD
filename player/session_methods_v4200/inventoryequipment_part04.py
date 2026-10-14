# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def equip_item(self, query):
        if self.combat_mob_key:
            await self.send(
                "Nie możesz zmieniać ekwipunku podczas aktywnej walki. "
                "Najpierw użyj flee albo zakończ walkę."
            )
            return

        raw_query = str(query or "").strip()
        normalized = self.normalize_description_query(raw_query)
        if not normalized:
            await self.send(
                "Użycie: załóż <pełna nazwa EQ>. Pierścienie, talizmany, kolczyki i akcesoria wybierają wolny slot automatycznie; "
                "ręczny slot 1/2 nadal działa. Skróty: zp, zt i zkol. Całość automatycznie: załóż auto albo eq auto."
            )
            return
        if normalized in ("auto", "automatycznie", "najlepsze", "best"):
            await self.auto_equip_best_v03040()
            return

        # Slot-only commands never choose the best item automatically.
        requested_slot = EQUIPMENT_SLOT_ALIASES.get(normalized)
        if requested_slot:
            if requested_slot in ("ring", "charm", "earring", "accessory"):
                await self.equip_shortcut_dual_v03020(requested_slot)
                return

            candidates = self.owned_armor_for_slot(requested_slot)
            if not candidates:
                await self.send(
                    f"Nie masz żadnego pancerza w slocie {EQUIPMENT_SLOT_NAMES[requested_slot]}."
                )
                return

            current_id = self.server.db.equipped_item(self.account_id, requested_slot)
            choices = self.equipment_choices_text(candidates)
            if current_id:
                current = ITEMS.get(current_id, {"name": current_id})
                await self.send(
                    f"Slot {EQUIPMENT_SLOT_NAMES[requested_slot]} jest zajęty przez: {current['name']}. "
                    "Nic nie zostało zmienione. Podaj pełną nazwę przedmiotu, który chcesz założyć, "
                    "albo najpierw użyj zdejmij " + EQUIPMENT_SLOT_NAMES[requested_slot] + "."
                )
                if choices:
                    await self.send(f"Posiadane opcje dla tego slotu: {choices}.")
                return

            if len(candidates) != 1:
                await self.send(
                    f"Masz kilka przedmiotów dla slotu {EQUIPMENT_SLOT_NAMES[requested_slot]}. "
                    "Gra nie wybiera najlepszego automatycznie. Podaj pełną nazwę wybranego EQ."
                )
                if choices:
                    await self.send(f"Posiadane opcje: {choices}.")
                return
            _score, item_id, item = candidates[0]
            found = (item_id, item)
            explicit_slot = requested_slot
        else:
            explicit_slot, item_query = self.explicit_dual_slot_and_item_query(raw_query)
            if explicit_slot and not item_query:
                candidates = self.owned_armor_for_slot(explicit_slot)
                choices = self.equipment_choices_text(candidates)
                current_id = self.server.db.equipped_item(self.account_id, explicit_slot)
                if current_id:
                    current = ITEMS.get(current_id, {"name": current_id})
                    await self.send(
                        f"Slot {EQUIPMENT_SLOT_NAMES[explicit_slot]} jest zajęty przez: {current['name']}. "
                        "Nic nie zostało zmienione. Podaj pełną nazwę wybranego przedmiotu."
                    )
                elif len(candidates) == 1:
                    _score, item_id, item = candidates[0]
                    found = (item_id, item)
                else:
                    await self.send(
                        f"Wybierz konkretny przedmiot dla slotu {EQUIPMENT_SLOT_NAMES[explicit_slot]}. "
                        "Gra nie wybiera najlepszego automatycznie."
                    )
                    if choices:
                        await self.send(f"Posiadane opcje: {choices}.")
                    return
                if current_id:
                    if choices:
                        await self.send(f"Posiadane opcje: {choices}.")
                    return
            else:
                found = self.resolve_equipment_for_equip(item_query)

        if not found:
            await self.send(
                "Nie rozpoznaję posiadanego EQ. Podaj pełną nazwę przedmiotu. "
                "Pierścienie, talizmany i kolczyki nie wymagają podawania slotu 1/2."
            )
            return

        item_id, item = found
        if item.get("type") != "armor":
            await self.send("Tego przedmiotu nie można założyć.")
            return

        required_class = None if item.get("universal_all_classes") else item.get("required_class")
        if required_class and required_class not in self.active_class_names():
            await self.send(
                f"{item['name']} wymaga aktywnej klasy {required_class}."
            )
            return

        required_race = item.get("required_race")
        if required_race and str(self.character.race) != str(required_race):
            await self.send(
                f"{item['name']} może używać tylko rasa {required_race}."
            )
            return

        required_mastery = max(1, int(item.get("required_mastery", 1)))
        if not self.equipment_mastery_requirement_met(item):
            await self.send(
                f"{item['name']}: {self.equipment_mastery_requirement_text(item)}"
            )
            return

        if self.server.db.item_qty(self.account_id, item_id) <= 0:
            await self.send("Nie masz tego przedmiotu.")
            return

        logical_slot = item["slot"]
        if logical_slot == "accessory":
            actual_slot = explicit_slot if explicit_slot in ("accessory1", "accessory2") else self.automatic_dual_slot_v03020("accessory")
        elif logical_slot == "ring":
            actual_slot = explicit_slot if explicit_slot in ("ring1", "ring2") else self.automatic_dual_slot_v03020("ring")
        elif logical_slot == "charm":
            actual_slot = explicit_slot if explicit_slot in ("charm1", "charm2") else self.automatic_dual_slot_v03020("charm")
        elif logical_slot == "earring":
            actual_slot = explicit_slot if explicit_slot in ("earring1", "earring2") else self.automatic_dual_slot_v03020("earring")
        else:
            actual_slot = logical_slot
            if explicit_slot and explicit_slot != actual_slot:
                await self.send(
                    f"{item['name']} nie pasuje do slotu {EQUIPMENT_SLOT_NAMES.get(explicit_slot, explicit_slot)}."
                )
                return

        if logical_slot in ("ring", "charm", "earring", "accessory"):
            paired = {
                "ring": ("ring1", "ring2"),
                "charm": ("charm1", "charm2"),
                "earring": ("earring1", "earring2"),
                "accessory": ("accessory1", "accessory2"),
            }[logical_slot]
            already_equipped = sum(
                1 for row in self.equipped_item_rows()
                if row["slot"] in paired and row["item_id"] == item_id and row["slot"] != actual_slot
            )
            if self.server.db.item_qty(self.account_id, item_id) <= already_equipped:
                await self.send(
                    "Do drugiego slotu potrzebujesz drugiej sztuki tego samego przedmiotu."
                )
                return

        old_item_id = self.server.db.equipped_item(self.account_id, actual_slot)
        if old_item_id == item_id:
            await self.send(f"{item['name']} jest już założony w tym slocie.")
            return

        returned_gems = []
        if actual_slot in ("ring1", "ring2", "earring1", "earring2", "necklace") and old_item_id:
            returned_gems = await self.return_socketed_gems(actual_slot, old_item_id)

        # Replacing is explicit by chosen item; v0.30.20 may auto-pick the free/weaker ring or charm slot.
        self.server.db.equip(self.account_id, actual_slot, item_id)
        replaced_item = ITEMS.get(old_item_id) if old_item_id else None
        self.current_hp = min(self.current_hp, self.max_hp())
        self.current_mana = min(self.current_mana, self.max_mana())

        if replaced_item:
            await self.send(
                f"Na twoje polecenie zdejmujesz: {replaced_item['name']}. "
                f"Zakładasz wybrany przedmiot w tym samym slocie."
            )

        rarity = f" Rzadkość: {item['rarity_name']}." if item.get("rarity_name") else ""
        affix = ""
        if item.get("affix"):
            affix_name = CRYPT_AFFIXES.get(item["affix"], item["affix"])
            affix = f" Bonus: {affix_name} +{item.get('affix_amount', 0)}."
        fixed_stats = ""
        if item.get("stats"):
            fixed_text = ", ".join(
                f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{amount}"
                for stat, amount in item.get("stats", {}).items()
                if int(amount or 0) != 0
            )
            if fixed_text:
                fixed_stats = f" Statystyki bazowe: {fixed_text}."
        balance_stats = ""
        if item.get("soulbound_balance_stats"):
            balance_text = ", ".join(
                f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{amount}"
                for stat, amount in item.get("soulbound_balance_stats", {}).items()
                if int(amount or 0) != 0
            )
            if balance_text:
                balance_stats = f" Bonus Soulbound: {balance_text}."
        await self.send(
            f"Zakładasz: {item['name']}. "
            f"Slot: {EQUIPMENT_SLOT_NAMES.get(actual_slot, actual_slot)}. "
            f"Obrona przedmiotu +{item.get('defense', 0)}.{rarity}{affix}{fixed_stats}{balance_stats}"
            + (" " + crossover_text_v3001(item) if crossover_text_v3001(item) else "")
        )
        if returned_gems:
            await self.send(
                "Z poprzedniej biżuterii wyjęto i zwrócono do Szkatułki Rzemieślniczej: "
                + ", ".join(ITEMS[g]["name"] for g in returned_gems) + "."
            )
        await self.send(f"Obrona fizyczna wynosi teraz {self.defense()}.")
        await self.send(self.crypt_set_bonus_text())
        await self.send(self.astral_set_bonus_text())


async def unequip_item(self, query):
        if self.combat_mob_key:
            await self.send(
                "Nie możesz zmieniać ekwipunku podczas aktywnej walki. "
                "Najpierw użyj flee albo zakończ walkę."
            )
            return

        normalized = self.normalize_description_query(str(query or "").strip())

        # Wygodna komenda zbiorcza: `zdejmij wszystko` opróżnia wszystkie
        # zwykłe sloty EQ jednym poleceniem. Broń Duszy nie jest rekordem
        # equipment i pozostaje bez zmian.
        if normalized in ("wszystko", "all", "cale", "całe", "calosc", "całość"):
            rows = list(self.server.db.equipment(self.account_id))
            if not rows:
                await self.send("Nie masz założonego dodatkowego wyposażenia.")
                return

            removed_names = []
            returned_gems = []
            for row in rows:
                slot = str(row["slot"])
                item_id = str(row["item_id"])
                item = (
                    ITEMS.get(item_id)
                    or ensure_crafting_quality_variant_v0332(item_id)
                    or {"name": player_item_display_name_v0335(item_id)}
                )
                if slot in ("ring1", "ring2", "earring1", "earring2", "necklace"):
                    returned_gems.extend(
                        await self.return_socketed_gems(slot, item_id)
                    )
                self.server.db.unequip(self.account_id, slot)
                removed_names.append(item.get("name", player_item_display_name_v0335(item_id)))

            self.current_hp = min(self.current_hp, self.max_hp())
            self.current_mana = min(self.current_mana, self.max_mana())
            await self.send(
                f"Zdejmujesz całe EQ: {len(removed_names)} elementów. "
                "Wszystkie dodatkowe sloty EQ są teraz puste."
            )
            if returned_gems:
                await self.send(
                    "Wyjęte klejnoty wracają do Szkatułki Rzemieślniczej: "
                    + ", ".join(
                        (ITEMS.get(gem_id) or {}).get(
                            "name", player_item_display_name_v0335(gem_id)
                        )
                        for gem_id in returned_gems
                    )
                    + "."
                )
            return

        slot = EQUIPMENT_SLOT_ALIASES.get(normalized)
        if slot in ("ring", "charm", "earring"):
            noun = {"ring":"pierścień", "charm":"talizman", "earring":"kolczyk"}[slot]
            await self.send(f"Podaj konkretny slot: zdejmij {noun} 1 albo zdejmij {noun} 2.")
            return
        if slot not in EQUIPMENT_SLOT_NAMES:
            await self.send(
                "Użycie: zdejmij <slot> albo zdejmij wszystko, np. zdejmij hełm, "
                "zdejmij pierścień 1, zdejmij kolczyk 2, zdejmij talizman 2 albo zdejmij naszyjnik."
            )
            return

        item_id = self.server.db.equipped_item(self.account_id, slot)
        if not item_id:
            await self.send(f"Slot {EQUIPMENT_SLOT_NAMES[slot]} jest już pusty.")
            return
        item = ITEMS.get(item_id) or ensure_crafting_quality_variant_v0332(item_id) or {"name": player_item_display_name_v0335(item_id)}
        returned_gems = []
        if slot in ("ring1", "ring2", "earring1", "earring2", "necklace"):
            returned_gems = await self.return_socketed_gems(slot, item_id)
        self.server.db.unequip(self.account_id, slot)
        self.current_hp = min(self.current_hp, self.max_hp())
        self.current_mana = min(self.current_mana, self.max_mana())
        await self.send(
            f"Zdejmujesz: {item['name']}. Slot {EQUIPMENT_SLOT_NAMES[slot]} jest teraz pusty."
        )
        if returned_gems:
            await self.send(
                "Wyjęte klejnoty wracają do Szkatułki Rzemieślniczej: "
                + ", ".join(ITEMS[g]["name"] for g in returned_gems) + "."
            )


def consumable_resource_restore_v11196(self, flat_amount, maximum):
        """Late-game-safe HP/MP consumable restoration.

        Existing flat values remain the early-game minimum. At large HP/MP
        pools the same item also restores a share proportional to its authored
        flat strength: flat/3500 of the relevant maximum resource. There is no
        maximum-resource ceiling, so consumables do not become irrelevant as
        Constitution/INT/WILL continue growing.
        """
        flat=max(0,int(flat_amount or 0))
        maximum=max(0,int(maximum or 0))
        if flat<=0 or maximum<=0:
            return 0
        scaled=int(round(maximum*(flat/3500.0)))
        return max(flat,scaled)


def find_consumable_for_use(self, query):
        q = self.normalize_description_query(query)
        if not q:
            return None, []

        # v0.71.4: skrót `użyj mapy` musi widzieć jawnie importowaną mapę
        # questową Erena. W v0.71.3 użycie globals().get(...) zawsze zwracało
        # None w tym jawnym module i komenda błędnie próbowała zużyć zwykłą mapę.
        if q in {"mapa", "mapy", "mape", "mapę", "mapa skarbu", "mape skarbu", "mapę skarbu", "treasure map"}:
            if self.server.db.item_qty(self.account_id, V0243_EREN_SECRET_MAP_ITEM) > 0:
                return (V0243_EREN_SECRET_MAP_ITEM, ITEMS[V0243_EREN_SECRET_MAP_ITEM]), []
            return (V014_TREASURE_MAP_ITEM, ITEMS[V014_TREASURE_MAP_ITEM]), []

        # Celowe krótkie aliasy wymagane dla szybkiej obsługi NVDA.
        direct_aliases = {
            "mikstura": "healing_potion",
            "miksture": "healing_potion",
            "miksturę": "healing_potion",
            "potion": "healing_potion",
            "eliksir": "soul_elixir",
            "elixir": "soul_elixir",
            "eliksir duszy": "soul_elixir",
            "soul elixir": "soul_elixir",
            "mana": "mana_potion",
            "mikstura many": "mana_potion",
            "mana potion": "mana_potion",
        }
        item_id = direct_aliases.get(q)
        if item_id:
            return (item_id, ITEMS[item_id]), []

        # v0.71.7: consumable catalog is static after startup; normalize it
        # once instead of rebuilding/scanning the full ITEMS catalog per use.
        cache = getattr(type(self).find_consumable_for_use, "_v0717_cache", None)
        if not isinstance(cache, tuple) or not cache or cache[0] != len(ITEMS):
            rows = tuple(
                (
                    item_id,
                    item,
                    self.normalize_description_query(item_id),
                    self.normalize_description_query(item.get("name", "")),
                )
                for item_id, item in ITEMS.items()
                if item.get("type") == "consumable"
            )
            type(self).find_consumable_for_use._v0717_cache = (len(ITEMS), rows)
            cache = (len(ITEMS), rows)

        exact = []
        partial = []
        for item_id, item, normalized_id, normalized_name in cache[1]:
            if q == normalized_id or q == normalized_name:
                exact.append((item_id, item))
            elif q in normalized_id or q in normalized_name:
                partial.append((item_id, item))

        if exact:
            return exact[0], []
        if len(partial) == 1:
            return partial[0], []
        if len(partial) > 1:
            return None, partial
        return None, []


def restore_missing_eren_map_v0714(self):
        """Odtwarza mapę tylko dla aktywnego questa Erena bez zapisanego tropu.

        Chroni konta, które weszły w v0.71.4 z już aktywnym zadaniem. Nie daje
        drugiej mapy po prawidłowym użyciu pierwszej.
        """
        quest_id = "city_cartographer_secret_marks"
        row = self.server.db.quest(self.account_id, quest_id)
        if not row or row["status"] != "active":
            return False
        if self.server.db.item_qty(self.account_id, V0243_EREN_SECRET_MAP_ITEM) > 0:
            return False
        prefix = f"{quest_id}|"
        tracked = self.server.db.collection_entry_ids(
            self.account_id, "quest_treasure_targets_v0243"
        )
        if any(str(entry).startswith(prefix) for entry in tracked):
            return False
        self.server.db.add_item(self.account_id, V0243_EREN_SECRET_MAP_ITEM, 1)
        self.server.db.add_collection_entry(
            self.account_id, "quest_map_grants_v0243", quest_id
        )
        return True

