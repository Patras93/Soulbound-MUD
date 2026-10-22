# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
def visible_companion_for_look_v1801(self, query):
    from systems.visible_companions_v1801 import nearby_companions_v1801
    wanted = self.normalize_description_query(query)
    if not wanted:
        return None
    matches = []
    for entry in nearby_companions_v1801(self.server, self.character.room_id):
        owner, kind, name, *_ = entry
        labels = (kind, name, f'{name} {owner.character.name}')
        normalized = tuple(self.normalize_description_query(label) for label in labels)
        if wanted in normalized:
            return entry
        if any(wanted in label for label in normalized):
            matches.append(entry)
    return matches[0] if len(matches) == 1 else None


def visible_player_for_look(self, query):
        wanted = self.normalize_description_query(query)
        if not wanted:
            return None

        exact = []
        partial = []
        for session in self.server.sessions:
            if (
                not session.character
                or session.character.room_id != self.character.room_id
            ):
                continue
            normalized = self.normalize_description_query(
                session.character.name
            )
            if wanted == normalized:
                exact.append(session)
            elif wanted in normalized:
                partial.append(session)

        if exact:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None


def visible_mob_for_look(self, query):
        wanted = self.normalize_description_query(query)
        if not wanted:
            return None

        exact = []
        partial = []
        for mob in self.server.world.room_mobs(
            self.character.room_id
        ):
            template = MOB_TEMPLATES[mob.template_id]
            name = self.normalize_description_query(
                template["name"]
            )
            template_id = self.normalize_description_query(
                mob.template_id
            )
            entry = (mob, template)
            if wanted in {name, template_id}:
                exact.append(entry)
            elif wanted in name or wanted in template_id:
                partial.append(entry)

        if exact:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None


def visible_item_for_look(self, query):
        wanted = self.normalize_description_query(query)
        if not wanted:
            return None

        candidates = {}

        for row in self.server.db.inventory(self.account_id):
            item_id = row["item_id"]
            item = ITEMS.get(item_id)
            if not item:
                continue
            entry = candidates.setdefault(
                item_id,
                {
                    "item": item,
                    "quantity": 0,
                    "equipped": [],
                    "shop": False,
                },
            )
            entry["quantity"] += int(row["quantity"])

        for row in self.server.db.equipment(self.account_id):
            item_id = row["item_id"]
            item = ITEMS.get(item_id)
            if not item:
                continue
            entry = candidates.setdefault(
                item_id,
                {
                    "item": item,
                    "quantity": 0,
                    "equipped": [],
                    "shop": False,
                },
            )
            entry["equipped"].append(row["slot"])

        for item_id in self.current_shop_offers():
            item = ITEMS.get(item_id)
            if not item:
                continue
            entry = candidates.setdefault(
                item_id,
                {
                    "item": item,
                    "quantity": 0,
                    "equipped": [],
                    "shop": False,
                },
            )
            entry["shop"] = True

        exact = []
        partial = []
        for item_id, entry in candidates.items():
            item = entry["item"]
            normalized_id = self.normalize_description_query(item_id)
            normalized_name = self.normalize_description_query(
                player_item_display_name_v0335(item_id)
            )
            result = (item_id, entry)

            if wanted in {normalized_id, normalized_name}:
                exact.append(result)
            elif (
                wanted in normalized_id
                or wanted in normalized_name
            ):
                partial.append(result)

        if exact:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None


async def look_at_player(self, session):
        character = session.character
        classes = character.active_class_names()
        _same_party = self.party_key() is not None and self.party_key() == session.party_key()
        _downed = _same_party and session.is_downed_v0371()
        await self.send(f"{character.name}. Gracz."
                        + (" POWALONY — można wskrzesić." if _downed else ""))
        await self.send(
            f"Rasa: {character.race}. "
            f"Klasa: {', '.join(classes)}. "
            f"Soul Level {character.soul_level}. "
            f"Soul Tier {character.soul_tier} — {soul_tier_title_for_class(character.soul_tier, character.class_name)}."
        )
        await self.send(
            f"Broń Duszy: {character.soul_weapon}."
        )
        if character.active_title:
            await self.send(f"Tytuł: {character.active_title}.")


async def look_at_npc(self, npc_id, npc):
        await self.send(f"{npc['name']}. NPC.")
        desc = NPC_DESCRIPTIONS.get(
            npc_id,
            npc.get("dialogue", ""),
        )
        if desc:
            await self.send(desc)

        quest_ids = []
        if npc.get("quest"):
            quest_ids.append(npc["quest"])
        quest_ids.extend(npc.get("quest_chain") or ())
        quest_ids.extend(npc.get("specialist_quests") or ())
        quest_ids = list(dict.fromkeys(quest_ids))

        if quest_ids:
            names = [
                QUESTS[qid]["name"]
                for qid in quest_ids
                if qid in QUESTS
            ]
            if names:
                await self.send(
                    "Powiązane zadania: "
                    + ", ".join(names)
                    + "."
                )


async def look_at_mob(self, mob, template):
        dtype = (
            "magiczne"
            if template.get("damage_type") == "magic"
            else "fizyczne"
        )
        await self.send(
            f"{template['name']}. Przeciwnik."
        )
        await self.send(
            f"HP: {mob.hp} z {template['max_hp']}. "
            f"Bazowe obrażenia: {template.get('damage', 0)}. "
            f"Typ obrażeń: {dtype}."
        )

        if template.get("rare_troll"):
            await self.send("Rzadki wariant trolla.")
        if template.get("rare_mob"):
            await self.send("Rzadki przeciwnik: zwiększone HP, obrażenia i nagrody.")

        if template.get("elite_affix_text"):
            await self.send(
                "Elitarny affix: "
                + template["elite_affix_text"]
            )

        if template.get("boss_mechanic_text"):
            await self.send(
                "Mechanika: "
                + template["boss_mechanic_text"]
            )


async def look_at_item(self, item_id, entry):
        item = entry["item"]
        await self.send(
            self.format_item_description(item_id, item)
        )

        if item_id == "moogle_board":
            _level = max(1, int(self.character.character_level or 1))
            if _level <= 150:
                _bonus = min(20, 2 + 2 * (_level // 10))
            else:
                _bonus = 20 + 2 * (_level - 150)
            await self.send(
                f"Aktualne statystyki Moogle Board przy Levelu {_level}: "
                f"Siła +{_bonus}, Zręczność +{_bonus}, Kondycja +{_bonus}, "
                f"Inteligencja +{_bonus}, Siła Woli +{_bonus}."
            )

        context = []
        quantity = int(entry.get("quantity", 0))
        if quantity > 0:
            context.append(f"Masz {quantity} szt.")

        for slot in entry.get("equipped", ()):
            context.append(
                "Założony: "
                + EQUIPMENT_SLOT_NAMES.get(slot, slot)
            )

        if entry.get("shop"):
            context.append(
                "Dostępny w sklepie tej lokacji"
            )

        if context:
            await self.send(". ".join(context) + ".")

