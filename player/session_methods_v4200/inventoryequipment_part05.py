# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def use_item(self, query):
        raw_query = str(query or "").strip()
        lowered = raw_query.lower()

        # Wygodna składnia dla umiejętności:
        # użyj umiejętność <nazwa> [cel]
        # use skill <name> [target]
        skill_prefixes = (
            "skill ",
            "umiejętność ",
            "umiejetnosc ",
            "zdolność ",
            "zdolnosc ",
            "czar ",
            "spell ",
        )
        for prefix in skill_prefixes:
            if lowered.startswith(prefix):
                skill_query = raw_query[len(prefix):].strip()
                if not skill_query:
                    await self.send(
                        "Użycie: użyj umiejętność <nazwa> [cel] "
                        "albo use skill <name> [target]."
                    )
                    return
                await self.use_class_skill(skill_query)
                return

        normalized_use = self.normalize_description_query(raw_query)
        map_aliases_v0714 = {"mapa", "mapy", "mape", "mapę", "mapa skarbu", "mape skarbu", "mapę skarbu", "treasure map"}
        restored_eren_map = False
        if normalized_use in map_aliases_v0714:
            restored_eren_map = self.restore_missing_eren_map_v0714()
            if restored_eren_map:
                await self.send("Odtworzono brakującą questową Mapę Erena dla aktywnego zadania Znak poza mapą.")

        found, ambiguous = self.find_consumable_for_use(raw_query)

        if ambiguous:
            names = ", ".join(item["name"] for _, item in ambiguous)
            await self.send(
                f"Nazwa pasuje do kilku przedmiotów: {names}. "
                "Podaj dokładniejszą nazwę."
            )
            return

        if not found:
            skill, _target = self.find_skill_from_input(raw_query)
            if skill:
                await self.use_class_skill(raw_query)
                return

            await self.send(
                "Nie rozpoznaję przedmiotu ani umiejętności. "
                "Przykłady: użyj mikstura; użyj umiejętność <nazwa> [cel]; "
                "use skill <name> [target]."
            )
            return

        item_id, item = found

        if item.get("treasure_map"):
            if self.combat_mob_key:
                await self.send("Nie możesz odczytywać mapy skarbu podczas walki.")
                return
            await self.use_v0140_treasure_map(item_id)
            return

        if self.server.db.item_qty(self.account_id, item_id) <= 0:
            await self.send(f"Nie masz przedmiotu: {item['name']}.")
            return

        if item.get("type") != "consumable":
            await self.send("Tego przedmiotu nie używa się w ten sposób.")
            return

        if "heal" in item or "mana" in item:
            max_hp = self.max_hp()
            max_mana = self.max_mana()

            missing_hp = max(0, max_hp - self.current_hp)
            missing_mana = max(0, max_mana - self.current_mana)

            can_restore_hp = (
                item.get("heal", 0) > 0
                and missing_hp > 0
            )
            can_restore_mana = (
                item.get("mana", 0) > 0
                and max_mana > 0
                and missing_mana > 0
            )

            if not can_restore_hp and not can_restore_mana:
                if max_mana > 0:
                    await self.send("Masz pełne HP i Manę.")
                else:
                    await self.send("Masz pełne życie.")
                return

            self.server.db.remove_item(
                self.account_id, item_id, 1
            )

            healed = 0
            restored_mana = 0

            if can_restore_hp:
                healed = min(
                    self.consumable_resource_restore_v11196(
                        item.get("heal", 0), max_hp
                    ),
                    missing_hp,
                )
                self.current_hp += healed

            if can_restore_mana:
                restored_mana = min(
                    self.consumable_resource_restore_v11196(
                        item.get("mana", 0), max_mana
                    ),
                    missing_mana,
                )
                self.current_mana += restored_mana

            parts = []
            if healed:
                parts.append(f"{healed} HP")
            if restored_mana:
                parts.append(f"{restored_mana} Many")

            await self.send(
                f"Używasz {item['name']}. Odzyskujesz "
                + " i ".join(parts) + "."
            )
            await self.send(
                f"HP {self.current_hp} z {max_hp}."
            )
            if max_mana > 0:
                await self.send(
                    f"Mana {self.current_mana} z {max_mana}."
                )

            if self.combat_mob_key:
                await self.ensure_realtime_combat()
            return

        if "soul_xp" in item:
            self.server.db.remove_item(
                self.account_id, item_id, 1
            )
            await self.send(
                f"Używasz {item['name']}."
            )
            soul_item_stage=max(
                1,
                min(
                    600,
                    int(
                        item.get("generator_level")
                        or item.get("required_character_level")
                        or item.get("required_mastery")
                        or item.get("min_profession_level")
                        or item.get("level")
                        or 1
                    ),
                ),
            )
            await self.grant_soul_xp(
                item["soul_xp"],
                content_level=soul_item_stage,
                content_scaled=False,
            )
            self.server.db.save_character(self.character)

            if self.combat_mob_key:
                await self.ensure_realtime_combat()
            return

        await self.send(
            "Ten przedmiot nie ma efektu do użycia."
        )

