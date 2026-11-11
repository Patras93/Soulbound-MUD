# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
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
        tool_level = max(1, min(TOOL_MAX_LEVEL, int(tool_level)))
        floor = mine_floor_number(room_id)
        dungeon, dungeon_floor = profession_dungeon_floor(room_id)
        if dungeon == "crystal_mine":
            floor = min(TOOL_MAX_LEVEL, max(1, int(dungeon_floor) * 10))
        tool_access_level = tool_tier_access_level(tool_level)
        effective_level = tool_access_level if floor is None else min(tool_access_level, max(1, int(floor)))
        # v0.34.4: progi wydobycia są autorską semantyką gry i muszą
        # pochodzić z ORE_ATLAS_LEVELS / ORE_MINE_FLOOR_MINIMUMS.
        # Generator Core może balansować liczby i wagi, ale nie może
        # przesuwać odblokowań zasobów przez generator_level przedmiotu.
        pool = []
        for ore_id in ORE_RESOURCE_IDS:
            if ore_id not in ITEMS:
                continue
            need_tool = int(ORE_ATLAS_LEVELS.get(ore_id, 1) or 1)
            if tool_access_level < need_tool:
                continue
            if floor is not None:
                need_floor = int(ORE_MINE_FLOOR_MINIMUMS.get(ore_id, need_tool) or need_tool)
                if int(floor) < need_floor:
                    continue
            pool.append(ore_id)
        if not pool:
            return None
        pool = tuple(sorted(pool, key=lambda iid: (int(ORE_ATLAS_LEVELS.get(iid, 1) or 1), iid)))
        weights = mining_ore_weights(
            pool, effective_level, f"mining:{room_id}"
        )
        return random.choices(pool, weights=weights, k=1)[0]


def mining_gem_drop(self, tool_level, profession_level, room_id=None):
        tool_level = max(1, min(TOOL_MAX_LEVEL, int(tool_level)))
        profession_level = max(1, min(PROFESSION_MAX_LEVEL, int(profession_level)))
        room_id = room_id or self.character.room_id
        floor = mine_floor_number(room_id)
        dungeon, dungeon_floor = profession_dungeon_floor(room_id)
        if dungeon == "crystal_mine":
            floor = min(TOOL_MAX_LEVEL, max(1, int(dungeon_floor) * 10))
        # v0.30.26: rodzaj surowego klejnotu zależy od Tieru Kilofa.
        # Górnictwo nadal wpływa na jakość/szansę, ale nie odblokowuje
        # nowych rodzajów klejnotów pomiędzy progami Tieru narzędzia.
        effective = tool_tier_access_level(tool_level)
        if floor is not None:
            effective = min(effective, max(1, int(floor)))
        base_gems = getattr(type(self).mining_gem_drop, "_base_gems_v0717", None)
        if base_gems is None:
            base_gems = tuple(
                iid for iid, item in ITEMS.items()
                if item.get("type") == "gem_raw" and not item.get("gem_quality")
            )
            type(self).mining_gem_drop._base_gems_v0717 = base_gems
        pool = balance_math.resource_pool(
            base_gems, ITEMS, effective, f"gems:{room_id}"
        )
        gem_skill = min(tool_level, profession_level)
        chance = min(0.18, 0.035 + 0.11 * (gem_skill / float(PROFESSION_MAX_LEVEL)))
        chance *= 0.85 + 0.30 * balance_math.stable_unit(f"gems:{room_id}")
        if not pool or random.random() >= chance:
            return None
        weights = balance_math.resource_weights(pool, ITEMS, effective, f"gems:{room_id}")
        base_id = random.choices(pool, weights=weights, k=1)[0]
        quality = roll_mined_gem_quality(tool_level, profession_level)
        if quality and quality != "normal":
            candidate = f"{base_id}_{quality}"
            if candidate in ITEMS:
                return candidate
        return base_id


def woodcutting_loot(self, tool_level, room_id=None):
        room_id = room_id or self.character.room_id
        tool_level = max(1, min(TOOL_MAX_LEVEL, int(tool_level)))
        dungeon, dungeon_floor = profession_dungeon_floor(room_id)
        effective = tool_tier_access_level(tool_level)
        if dungeon == "ancient_forest":
            effective = min(effective, max(1, int(dungeon_floor) * 10))
        pool = balance_math.resource_pool(
            tuple(WOOD_RESOURCE_IDS), ITEMS, effective, f"wood:{room_id}"
        )
        if not pool:
            return None
        weights = balance_math.resource_weights(pool, ITEMS, effective, f"wood:{room_id}")
        return random.choices(pool, weights=weights, k=1)[0]


def herbalism_loot(self, tool_level, room_id=None):
        room_id = room_id or self.character.room_id
        tool_level = max(1, min(TOOL_MAX_LEVEL, int(tool_level)))
        dungeon, dungeon_floor = profession_dungeon_floor(room_id)
        effective = tool_tier_access_level(tool_level)
        if dungeon == "alchemy_garden":
            effective = min(effective, max(1, int(dungeon_floor) * 10))
        pool = balance_math.resource_pool(
            tuple(HERB_RESOURCE_IDS), ITEMS, effective, f"herb:{room_id}"
        )
        if not pool:
            return None
        weights = balance_math.resource_weights(pool, ITEMS, effective, f"herb:{room_id}")
        return random.choices(pool, weights=weights, k=1)[0]

