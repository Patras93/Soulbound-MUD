# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def cut_gem(self, query):
        q = self.normalize_description_query(query)
        if not q:
            await self.send(
                "Użycie: szlifuj <kamień>. "
                "Przykład: szlifuj rubin."
            )
            return False

        candidates = {}
        for recipe_id, recipe in JEWELCRAFT_RECIPES.items():
            if not recipe.get("gem_cut_recipe"):
                continue
            output = ITEMS[recipe["output"]]
            raw_id = next(iter(recipe["ingredients"]))
            raw = ITEMS[raw_id]
            candidates[recipe_id] = {
                "name": output["name"],
                "aliases": (
                    raw["name"],
                    output["name"],
                    recipe_id.replace("cut_", ""),
                ),
                "recipe": recipe,
            }

        found = find_by_name(candidates, query)
        if not found:
            await self.send(
                "Nie rozpoznaję kamienia do szlifowania. "
                "Wpisz kamienie."
            )
            return False

        _recipe_id, entry = found
        return await self.perform_recipe(
            entry["recipe"]["name"],
            JEWELCRAFT_RECIPES,
            "szlifowanie",
        )


async def socket_gem(self, query):
        if self.combat_mob_key:
            await self.send(
                "Nie możesz osadzać klejnotów podczas walki."
            )
            return False

        raw = str(query or "").strip()
        if not raw:
            await self.send(
                "Użycie: osadz <klejnot> <pierścień/kolczyk/naszyjnik>. "
                "Przykład: osadz rubin kolczyk 1."
            )
            return False

        normalized = self.normalize_description_query(raw)
        slot = None
        slot_tokens = (
            ("pierścień 1", "ring1"), ("pierscien 1", "ring1"),
            ("ring 1", "ring1"), ("ring1", "ring1"),
            ("pierścień 2", "ring2"), ("pierscien 2", "ring2"),
            ("ring 2", "ring2"), ("ring2", "ring2"),
            ("pierścień", "ring"), ("pierscien", "ring"),
            ("ring", "ring"),
            ("kolczyk 1", "earring1"), ("earring 1", "earring1"), ("earring1", "earring1"),
            ("kolczyk 2", "earring2"), ("earring 2", "earring2"), ("earring2", "earring2"),
            ("kolczyk", "earring"), ("kolczyki", "earring"), ("earring", "earring"),
            ("naszyjnik", "necklace"), ("necklace", "necklace"),
            ("głowa", "head"), ("glowa", "head"), ("head", "head"),
            ("ciało", "body"), ("cialo", "body"), ("body", "body"),
            ("tarcza", "shield"), ("tarczy", "shield"), ("shield", "shield"),
            ("ręce", "hands"), ("rece", "hands"), ("hands", "hands"),
            ("nogi", "legs"), ("legs", "legs"), ("stopy", "feet"), ("feet", "feet"),
            ("barki", "shoulders"), ("shoulders", "shoulders"), ("pas", "belt"), ("belt", "belt"),
            ("płaszcz", "cloak"), ("plaszcz", "cloak"), ("cloak", "cloak"),
            ("karwasze", "bracers"), ("bracers", "bracers"), ("relikt", "relic"), ("relic", "relic"),
            ("board", "board"),
        )
        gem_query = raw
        for token, resolved in slot_tokens:
            token_norm = self.normalize_description_query(token)
            if normalized.endswith(" " + token_norm):
                slot = resolved
                words = raw.split()
                token_words = len(token.split())
                gem_query = " ".join(words[:-token_words]).strip()
                break
            if normalized == token_norm:
                slot = resolved
                gem_query = ""
                break

        if not slot:
            await self.send(
                "Na końcu podaj slot EQ, np. ring1, necklace, body, head, bracers albo board."
            )
            return False

        if slot in ("ring", "earring"):
            pair = ("ring1", "ring2") if slot == "ring" else ("earring1", "earring2")
            slot = pair[0] if self.server.db.equipped_item(self.account_id, pair[0]) else pair[1]

        item_id = self.server.db.equipped_item(self.account_id, slot)
        item = ITEMS.get(item_id) if item_id else None
        if not item:
            await self.send(f"Nie masz założonego przedmiotu w slocie {EQUIPMENT_SLOT_NAMES.get(slot, slot)}.")
            return False
        capacity = self.equipment_total_socket_capacity_v03114(item_id, item, "gem")
        if capacity <= 0:
            await self.send(f"{item['name']} nie ma gniazd na klejnoty.")
            return False
        rows = self.socketed_gem_rows_for_item(
            slot,
            item_id,
        )
        if len(rows) >= capacity:
            await self.send(
                f"{item['name']} ma wszystkie gniazda zajęte: "
                f"{len(rows)} z {capacity}."
            )
            return False

        owned_gems = {
            gem_id: ITEMS[gem_id]
            for gem_id in CUT_GEM_IDS
            if self.available_recipe_item(gem_id) > 0
        }
        found = find_by_name(owned_gems, gem_query)
        if not found:
            await self.send(
                "Nie masz takiego oszlifowanego klejnotu."
            )
            return False

        gem_id, gem = found
        if not self.consume_recipe_item(gem_id, 1):
            await self.send("Nie masz tego klejnotu w Szkatułce Rzemieślniczej.")
            return False

        used = {
            int(row["socket_index"])
            for row in rows
        }
        socket_index = next(
            i for i in range(1, capacity + 1)
            if i not in used
        )
        self.server.db.add_socketed_gem(
            self.account_id,
            slot,
            item_id,
            socket_index,
            gem_id,
        )

        self.current_hp = min(
            self.current_hp,
            self.max_hp(),
        )
        self.current_mana = min(
            self.current_mana,
            self.max_mana(),
        )

        affix_name = CRYPT_AFFIXES.get(
            gem.get("affix"),
            gem.get("affix"),
        )
        await self.send(
            f"Osadzasz {gem['name']} w {item['name']}. "
            f"Gniazdo {socket_index} z {capacity}. "
            f"Bonus: {affix_name} "
            f"+{gem.get('affix_amount', 0)}."
        )
        return True


async def show_socketed_gems(self):
        await self.send("GNIAZDA EQ")
        found_any = False
        for row in self.equipped_item_rows():
            slot=row["slot"]; item_id=row["item_id"]; item=ITEMS.get(item_id)
            if not item:
                continue
            capacity=self.equipment_total_socket_capacity_v03114(item_id,item,"gem")
            rune_capacity=self.equipment_total_socket_capacity_v03114(item_id,item,"rune")
            if capacity<=0 and rune_capacity<=0:
                continue
            found_any=True
            gems=self.socketed_gem_rows_for_item(slot,item_id) if capacity>0 else []
            runes=list(self.server.db.equipment_runes_v0925(self.account_id,item_id)) if rune_capacity>0 else []
            await self.send(f"{EQUIPMENT_SLOT_NAMES.get(slot,slot)}: {item['name']}. Klejnoty {len(gems)}/{capacity}. Runy {len(runes)}/{rune_capacity}.")
        if not found_any:
            await self.send("Nie masz założonego EQ z gniazdami.")


def automatic_dual_slot_v03020(self, logical_slot):
        """Pick first free ring/charm/earring slot; when full, replace the weaker equipped piece."""
        pairs = {
            "ring": ("ring1", "ring2"),
            "charm": ("charm1", "charm2"),
            "earring": ("earring1", "earring2"),
            "accessory": ("accessory1", "accessory2"),
        }
        paired = pairs[logical_slot]
        for slot in paired:
            if not self.server.db.equipped_item(self.account_id, slot):
                return slot
        scored = []
        for order, slot in enumerate(paired):
            item_id = self.server.db.equipped_item(self.account_id, slot)
            item = ITEMS.get(item_id, {})
            scored.append((self.auto_equipment_score_v03040(item, item_id), order, slot))
        scored.sort(key=lambda row: (row[0], row[1]))
        return scored[0][2]


async def equip_shortcut_dual_v03020(self, logical_slot, query=""):
        pairs = {
            "ring": ("ring1", "ring2", "pierścienie", "zp"),
            "charm": ("charm1", "charm2", "talizmany", "zt"),
            "earring": ("earring1", "earring2", "kolczyki", "zkol"),
            "accessory": ("accessory1", "accessory2", "akcesoria", "zakc"),
        }
        s1, s2, noun, shortcut = pairs[logical_slot]
        candidates = self.owned_armor_for_slot(s1)
        if not candidates:
            await self.send(f"Nie masz żadnego EQ w kategorii {noun}.")
            return
        raw = str(query or "").strip()
        if not raw:
            n1 = ITEMS.get(self.server.db.equipped_item(self.account_id, s1), {}).get("name", "pusty")
            n2 = ITEMS.get(self.server.db.equipped_item(self.account_id, s2), {}).get("name", "pusty")
            await self.send(f"{noun.capitalize()}. Slot 1: {n1}. Slot 2: {n2}. Wybierz numer przedmiotu:")
            for idx, (_score, item_id, item) in enumerate(candidates, 1):
                await self.send(f"{idx}. {player_item_display_name_v0335(item_id)}. Poziom postaci {int(item.get('required_character_level', item.get('required_mastery',1)) or 1)}.")
            return
        if raw.isdigit():
            idx = int(raw)
            if not 1 <= idx <= len(candidates):
                await self.send(f"Nie ma pozycji {idx}. Zakres: 1-{len(candidates)}.")
                return
            _score, item_id, item = candidates[idx-1]
        else:
            pool = {item_id:item for _score,item_id,item in candidates}
            found = find_by_name(pool, raw)
            if not found:
                await self.send(f"Nie rozpoznaję przedmiotu. Wpisz {shortcut}, aby dostać listę.")
                return
            item_id, item = found
        await self.equip_item(player_item_display_name_v0335(item_id))


async def equip_shortcut_slot_v03016(self, slot, query=""):
        """NVDA-friendly numbered slot picker.

        Sam skrót pokazuje numerowaną listę. Skrót + numer zakłada wybraną
        pozycję. Skrót + nazwa nadal działa, ale wyłącznie w obrębie tego slotu.
        """
        slot = str(slot or "")
        candidates = self.owned_armor_for_slot(slot)
        if not candidates:
            await self.send(
                f"Nie masz żadnego EQ dla slotu {EQUIPMENT_SLOT_NAMES.get(slot, slot)}."
            )
            return
        raw = str(query or "").strip()
        if not raw:
            current_id = self.server.db.equipped_item(self.account_id, slot)
            current_name = ITEMS.get(current_id, {}).get("name") if current_id else None
            await self.send(
                f"EQ {EQUIPMENT_SLOT_NAMES.get(slot, slot)}. "
                f"Aktualnie: {current_name or 'pusty slot'}. Wybierz numer:"
            )
            for idx, (_score, item_id, item) in enumerate(candidates, 1):
                mastery = int(item.get("required_mastery", 1) or 1)
                marker = " [ZAŁOŻONE]" if item_id == current_id else ""
                await self.send(
                    f"{idx}. {player_item_display_name_v0335(item_id)}. "
                    f"Poziom postaci {int(item.get('required_character_level', mastery) or mastery)}. "
                    f"{CLASS_SET_STAT_NAMES.get(item.get('affix'), item.get('affix'))} "
                    f"+{int(item.get('affix_amount', 0) or 0)}; "
                    + ", ".join(
                        f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{int(amount or 0)}"
                        for stat, amount in (item.get("stats") or {}).items()
                    )
                    + marker
                )
            return

        found = None
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(candidates):
                _score, item_id, item = candidates[index - 1]
                found = (item_id, item)
            else:
                await self.send(f"Nie ma pozycji {index}. Zakres: 1-{len(candidates)}.")
                return
        else:
            pool = {item_id: item for _score, item_id, item in candidates}
            found = find_by_name(pool, raw)
            if not found:
                await self.send(
                    f"Nie rozpoznaję EQ dla slotu {EQUIPMENT_SLOT_NAMES.get(slot, slot)}. "
                    "Wpisz sam skrót, aby dostać numerowaną listę."
                )
                return

        item_id, item = found
        if slot in ("ring1", "ring2", "charm1", "charm2", "earring1", "earring2"):
            await self.equip_item(f"{slot} {player_item_display_name_v0335(item_id)}")
        else:
            await self.equip_item(player_item_display_name_v0335(item_id))

