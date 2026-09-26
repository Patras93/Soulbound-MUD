# -*- coding: utf-8 -*-
"""Collection views, boss codex, corpses, loot and leaderboards."""

class SessionCollectionLootRecordsMixin:

    def _collection_v2_count(self, item_ids, discovered_eq=None):
            if discovered_eq is None:
                discovered_eq = self.server.db.collection_entry_ids(self.account_id, "equipment")
            item_ids = set(item_ids)
            return len(item_ids.intersection(discovered_eq)), len(item_ids)

    async def show_collection_v2_classes(self):
            discovered = self.server.db.collection_entry_ids(self.account_id, "equipment")
            await self.send("KODEKS KOLEKCJI — EQ WEDŁUG KLASY")
            for class_name in sorted(COLLECTION_V2_CLASS_GROUPS, key=normalize_lookup_text):
                count, total = self._collection_v2_count(COLLECTION_V2_CLASS_GROUPS[class_name], discovered)
                pct = int(count * 100 / max(1, total))
                await self.send(f"{class_name}: {count} z {total}, {pct}%.")

    async def show_collection_v2_sets(self, page=1):
            discovered = self.server.db.collection_entry_ids(self.account_id, "equipment")
            rows = []
            for set_id, items in COLLECTION_V2_SET_GROUPS.items():
                count, total = self._collection_v2_count(items, discovered)
                pct = int(count * 100 / max(1, total))
                rows.append((normalize_lookup_text(COLLECTION_V2_SET_NAMES[set_id]), COLLECTION_V2_SET_NAMES[set_id], count, total, pct))
            rows.sort()
            page_size = 30
            pages = max(1, math.ceil(len(rows) / page_size))
            page = max(1, min(int(page), pages))
            await self.send(f"KODEKS KOLEKCJI — SETY. Strona {page} z {pages}; setów {len(rows)}.")
            start = (page - 1) * page_size
            for _key, name, count, total, pct in rows[start:start + page_size]:
                await self.send(f"{name}: {count} z {total}, {pct}%.")
            if page < pages:
                await self.send(f"Następna strona: kolekcja sety2 {page + 1}.")

    async def show_collection_v2_legends(self):
            discovered = self.server.db.collection_entry_ids(self.account_id, "equipment")
            all_items = set().union(*COLLECTION_V2_LEGENDARY_GROUPS.values()) if COLLECTION_V2_LEGENDARY_GROUPS else set()
            count, total = self._collection_v2_count(all_items, discovered)
            await self.send(f"KODEKS KOLEKCJI — LEGENDY: {count} z {total}, {int(count*100/max(1,total))}%.")
            for class_name in sorted(COLLECTION_V2_LEGENDARY_GROUPS, key=normalize_lookup_text):
                c, t = self._collection_v2_count(COLLECTION_V2_LEGENDARY_GROUPS[class_name], discovered)
                await self.send(f"{class_name}: {c} z {t}, {int(c*100/max(1,t))}%.")

    async def show_collection_v2_materials(self):
            discovered = self.server.db.collection_entry_ids(self.account_id, "equipment")
            await self.send("KODEKS KOLEKCJI — MATERIAŁOWE EQ")
            for tier in CORPSE_MATERIAL_TIERS:
                key = tier["key"]
                c, t = self._collection_v2_count(COLLECTION_V2_MATERIAL_GROUPS.get(key, ()), discovered)
                await self.send(f"{COLLECTION_V2_MATERIAL_LABELS[key]}: {c} z {t}, {int(c*100/max(1,t))}%.")

    async def show_collection_v2_regions(self):
            discovered = self.server.db.discovered_room_ids(self.account_id)
            await self.send("KODEKS KOLEKCJI — REGIONY")
            for zone in sorted(EXPLORATION_ZONE_ROOMS, key=normalize_lookup_text):
                rooms = EXPLORATION_ZONE_ROOMS[zone]
                count = sum(1 for room_id in rooms if room_id in discovered)
                total = len(rooms)
                await self.send(f"{zone}: {count} z {total}, {int(count*100/max(1,total))}%.")

    async def show_collection_v2_instances(self):
            await self.send("KODEKS KOLEKCJI — INSTANCJE")
            any_seen = False
            for kind, info in INSTANCE_MAP_DEFS.items():
                visited = self.server.db.instance_visited_floors(self.account_id, kind)
                if not visited:
                    continue
                any_seen = True
                highest = max(visited)
                start, end = instance_sector_bounds(kind, highest)
                count = sum(1 for floor in visited if start <= floor <= end)
                secrets = self.server.db.instance_secret_rows(self.account_id, kind)
                checkpoints = self.server.db.instance_checkpoint_floors(self.account_id, kind)
                await self.send(
                    f"{info['label']}: sektor {start}-{end} {count} z 100, {count}%; "
                    f"najwyższe piętro {highest}; sekrety {len(secrets)}; checkpointy {len(checkpoints)}."
                )
            if not any_seen:
                await self.send("Nie odkryto jeszcze żadnej instancji.")

    async def show_collection(self, args=""):
            await self.sync_collection_from_inventory()
            raw = str(args or "").strip()
            norm = normalize_lookup_text(raw)
            compact = norm.replace(" ", "")

            if compact in ("klasy", "classes", "class", "klasa"):
                await self.show_collection_v2_classes()
                return
            first_token = normalize_lookup_text(raw.split()[0]).replace(" ", "") if raw.split() else ""
            if first_token in ("sety2", "sety", "sets2", "setprogress", "setprogression"):
                page = int(raw.split()[-1]) if raw.split()[-1].isdigit() else 1
                await self.show_collection_v2_sets(page)
                return
            if compact in ("legendy", "legendarne", "legends", "legendary"):
                await self.show_collection_v2_legends()
                return
            if compact in ("materialyeq", "materialeq", "eqmaterialy", "eqmaterials"):
                await self.show_collection_v2_materials()
                return
            if compact in ("regiony", "regions"):
                await self.show_collection_v2_regions()
                return
            if compact in ("instancje", "instances", "dungeons"):
                await self.show_collection_v2_instances()
                return
            if compact in ("swiat", "świat", "world", "worldlife"):
                await self.show_collection_world_v015()
                return
            if not norm:
                discovered_total = 0
                catalog_total = 0
                await self.send("KODEKS KOLEKCJI")
                for category, catalog in COLLECTION_CATALOGS.items():
                    found = self.server.db.collection_entry_ids(self.account_id, category)
                    count = len(set(catalog).intersection(found))
                    total = len(catalog)
                    pct = int(count * 100 / max(1, total))
                    discovered_total += count
                    catalog_total += total
                    await self.send(
                        f"{COLLECTION_CATEGORY_LABELS[category]}: {count} z {total}, {pct}%."
                    )
                pct = int(discovered_total * 100 / max(1, catalog_total))
                await self.send(f"Cały Collection Codex: {pct}%.")
                await self.send(
                    "Collection Codex 2.0: kolekcja klasy, kolekcja sety2, kolekcja legendy, "
                    "kolekcja materialy eq, kolekcja regiony, kolekcja instancje, kolekcja swiat. "
                    "Klasyczne widoki nadal działają: ryby, minerały, zioła, klejnoty, bossowie, rare, "
                    "materiały, wyjątkowe, eq, named, sety i skrzynie."
                )
                return

            parts = raw.split()
            category_key = normalize_lookup_text(parts[0]).replace(" ", "")
            category = COLLECTION_CATEGORY_ALIASES.get(category_key)
            if not category:
                joined = norm.replace(" ", "")
                category = COLLECTION_CATEGORY_ALIASES.get(joined)
            if not category:
                await self.send(
                    "Kategorie: ryby, minerały, zioła, klejnoty, bossowie, rare, "
                    "materiały, wyjątkowe, eq; dodatkowo named, sety, skrzynie."
                )
                return

            page = 1
            if len(parts) >= 2 and parts[-1].isdigit():
                page = max(1, int(parts[-1]))
            page_size = 40
            catalog = COLLECTION_CATALOGS[category]
            found = self.server.db.collection_entry_ids(self.account_id, category)
            count = len(set(catalog).intersection(found))
            total = len(catalog)
            pages = max(1, math.ceil(total / page_size))
            page = min(page, pages)
            await self.send(
                f"{COLLECTION_CATEGORY_LABELS[category]}: {count} z {total}, "
                f"{int(count * 100 / max(1, total))}%. Strona {page} z {pages}."
            )
            rows = sorted(catalog.items(), key=lambda row: normalize_lookup_text(row[1]))
            start = (page - 1) * page_size
            end = min(total, start + page_size)
            for number, (entry_id, name) in enumerate(rows[start:end], start + 1):
                if entry_id in found:
                    await self.send(f"{number}. {name}. Odkryty.")
                else:
                    await self.send(
                        f"{number}. Nieodkryty wpis {COLLECTION_CATEGORY_LABELS[category]}."
                    )
            if page < pages:
                await self.send(
                    f"Następna strona: kolekcja {category} {page + 1}."
                )

    async def show_boss_codex(self, args=""):
            raw = str(args or "").strip()
            norm = normalize_lookup_text(raw)
            discovered = self.server.db.collection_entry_ids(self.account_id, "bosses")
            discovered = set(BOSS_COLLECTION_CATALOG).intersection(discovered)
            total = len(BOSS_COLLECTION_CATALOG)

            if not norm:
                await self.send(
                    f"BOSS CODEX: odkryto {len(discovered)} z {total} bossów."
                )
                await self.send(
                    "Wpisz bosskodex lista albo bosskodex <nazwa bossa>. "
                    "Codex pokazuje kille, pierwszy/ostatni kill, solo/grupa, rekord czasu, "
                    "najwyższą wersję piętra i odkryte unikalne dropy."
                )
                for kind, info in INSTANCE_MAP_DEFS.items():
                    highest = self.server.db.highest_boss_floor_cleared(self.account_id, kind)
                    if highest:
                        await self.send(f"{info['label']}: najwyższy zaliczony próg bossa {highest}.")
                return

            if norm.startswith("lista") or norm == "list":
                parts = raw.split()
                page = 1
                if parts and parts[-1].isdigit():
                    page = max(1, int(parts[-1]))
                rows = sorted(
                    ((boss_id, BOSS_COLLECTION_CATALOG[boss_id]) for boss_id in discovered),
                    key=lambda row: normalize_lookup_text(row[1]),
                )
                page_size = 30
                pages = max(1, math.ceil(len(rows) / page_size))
                page = min(page, pages)
                await self.send(
                    f"BOSS CODEX. Odkryto {len(discovered)} z {total}. Strona {page} z {pages}."
                )
                start = (page - 1) * page_size
                for number, (boss_id, name) in enumerate(rows[start:start + page_size], start + 1):
                    entry = self.server.db.bestiary_entry(self.account_id, boss_id)
                    kills = int(entry["kills"] or 0) if entry else 0
                    await self.send(f"{number}. {name}. Pokonany {kills} razy.")
                if page < pages:
                    await self.send(f"Następna strona: bosskodex lista {page + 1}.")
                return

            candidates = {boss_id: {"name": name} for boss_id, name in BOSS_COLLECTION_CATALOG.items()}
            found = find_by_name(candidates, raw)
            if not found:
                await self.send("Nie rozpoznaję takiego bossa.")
                return
            boss_id, data = found
            if boss_id not in discovered:
                await self.send("Ten boss nie został jeszcze odkryty w twoim Boss Codexie.")
                return

            entry = self.server.db.bestiary_entry(self.account_id, boss_id)
            if not entry:
                await self.send("Brak zapisanej historii tego bossa.")
                return
            extra = self.server.db.boss_codex_stats(self.account_id, boss_id)
            solo = int(extra["solo_kills"] or 0) if extra else 0
            group = int(extra["group_kills"] or 0) if extra else 0
            total_kills = max(0, int(entry["kills"] or 0))
            legacy_unknown = max(0, total_kills - solo - group)
            fastest = entry["fastest_kill_ms"]
            fastest_text = (
                f"{int(fastest) / 1000.0:.2f} sekundy" if fastest is not None else "brak rekordu czasu"
            )
            await self.send(
                f"BOSS CODEX: {data['name']}. Pokonania {total_kills}. "
                f"Solo {solo}. Grupa {group}."
                + (f" Starsze nierozdzielone {legacy_unknown}." if legacy_unknown else "")
            )
            await self.send(
                f"Pierwszy kill: {entry['first_killed_at']}. Ostatni kill: {entry['last_killed_at']}. "
                f"Najlepszy czas: {fastest_text}."
            )
            boss_template = MOB_TEMPLATES.get(boss_id, {})
            instance_kind, boss_floor = boss_floor_identity(boss_template)
            if instance_kind and boss_floor:
                highest_version = self.server.db.highest_boss_floor_cleared(self.account_id, instance_kind)
                await self.send(
                    f"Wersja piętrowa: {boss_floor}. Najwyższy pokonany próg bossa w instancji "
                    f"{INSTANCE_MAP_DEFS.get(instance_kind, {}).get('label', instance_kind)}: {highest_version}."
                )
            drops = self.server.db.boss_codex_drops(self.account_id, boss_id)
            if drops:
                names = [
                    ITEMS[row["item_id"]]["name"]
                    for row in drops
                    if row["item_id"] in ITEMS and boss_codex_drop_is_unique(row["item_id"])
                ]
                if names:
                    await self.send(
                        f"Odkryte unikalne dropy: {len(names)}. " + ", ".join(names) + "."
                    )
                else:
                    await self.send("Odkryte unikalne dropy: jeszcze brak zapisanych.")
            else:
                await self.send("Odkryte unikalne dropy: jeszcze brak zapisanych.")

    async def show_drop_history(self):
            rows = self.server.db.drop_history_rows(self.account_id, 20)
            if not rows:
                await self.send("Drop History jest puste.")
                return
            await self.send("DROP HISTORY. Ostatnie wartościowe dropy:")
            for number, row in enumerate(rows, 1):
                extra = []
                if row["source"]:
                    extra.append(f"źródło {row['source']}")
                if row["zone"]:
                    extra.append(f"strefa {row['zone']}")
                suffix = ". " + ", ".join(extra) if extra else ""
                await self.send(
                    f"{number}. {row['item_name']}. {row['rarity']}{suffix}."
                )

    async def set_loot_filter(self, args=""):
            raw = str(args or "").strip().lower()
            aliases = {
                "wszystko": "all", "all": "all",
                "rare+": "rare+", "rzadki+": "rare+", "rzadkie+": "rare+",
                "epic+": "epic+", "epicki+": "epic+", "epickie+": "epic+",
                "legendary": "legendary", "legendarny": "legendary",
                "off": "off", "wylacz": "off", "wyłącz": "off",
            }
            if raw in ("", "status"):
                await self.send(
                    f"Loot filter: {self.character.loot_filter}. "
                    "Tryby: loot all, loot rare+, loot epic+, loot legendary, loot off."
                )
                return
            mode = aliases.get(raw)
            if not mode:
                await self.send(
                    "Nieznany filtr. Użyj: loot all, loot rare+, loot epic+, loot legendary albo loot off."
                )
                return
            self.character.loot_filter = mode
            self.server.db.save_character(self.character)
            await self.send(f"Loot filter ustawiony: {mode}.")

    async def show_corpses(self, query=""):
            all_corpses = self.server.world.room_corpses(self.character.room_id)
            if not all_corpses:
                await self.send("Nie ma tutaj żadnych ciał.")
                return
            corpses = all_corpses
            if query.strip():
                corpse = self.server.world.find_corpse(self.character.room_id, query)
                if not corpse:
                    await self.send("Nie widzę takiego ciała.")
                    return
                corpses = [corpse]

            for corpse in corpses:
                number = all_corpses.index(corpse) + 1
                names = ", ".join(ITEMS[i]["name"] for i in corpse.items) if corpse.items else "brak ekwipunku"
                await self.send(
                    f"{number}. Ciało: {corpse.mob_name}. Selektor: {number}.cialo lub {number}.corpse. "
                    f"Ekwipunek na ciele: {names}."
                )
            await self.send(
                "Podgląd: l in 2.corpse albo l w 2.cialo. "
                "Całość: przeszukaj 2.cialo. Pojedynczy przedmiot: "
                "get <przedmiot> from 2.corpse albo wez <przedmiot> z 2.cialo."
            )

    def _corpse_party_recipients_v03510(self, corpse):
            """Local party members who receive a copy of corpse loot.

            The corpse itself remains a single shared world object. Removing an
            item from it happens once, then every online member of the looter's
            party who is standing in the corpse room receives one copy. Players
            outside that room are never included.
            """
            recipients = self.server.party_sessions(
                self.account_id, same_room=corpse.room_id
            )
            if not recipients:
                recipients = [self]
            recipients = [
                session for session in recipients
                if session.character and not session.closed
                and session.character.room_id == corpse.room_id
            ]
            if not recipients:
                recipients = [self]
            return sorted(
                recipients, key=lambda session: session.character.name.lower()
            )

    async def _record_corpse_loot(self, corpse, looted):
            recipients = self._corpse_party_recipients_v03510(corpse)
            boss_id = canonical_bestiary_template_id(corpse.mob_template_id)
            for recipient in recipients:
                for item_id in looted:
                    recipient.server.db.add_item(recipient.account_id, item_id, 1)
                    await recipient.record_item_collection(
                        item_id, source=corpse.mob_name, announce=True
                    )
                    if boss_id in BOSS_COLLECTION_CATALOG:
                        if recipient.server.db.add_boss_codex_drop(
                            recipient.account_id, boss_id, item_id
                        ):
                            await recipient.send(
                                f"Boss Codex: odkryty drop {ITEMS[item_id]['name']} z "
                                f"{BOSS_COLLECTION_CATALOG[boss_id]}."
                            )
            return recipients

    async def loot_corpse(self, query=""):
            corpses = self.server.world.room_corpses(self.character.room_id)
            if not corpses:
                await self.send("Nie ma tutaj żadnych ciał do przeszukania.")
                return
            corpse = self.server.world.find_corpse(self.character.room_id, query)
            if corpse is None:
                if not query.strip() and len(corpses) > 1:
                    await self.send(
                        "Jest tutaj kilka ciał. Wpisz ciało, a potem np. przeszukaj 2.cialo."
                    )
                else:
                    await self.send("Nie widzę takiego ciała.")
                return
            if not corpse.items:
                await self.send(
                    f"Przeszukujesz ciało: {corpse.mob_name}. Nie ma już na nim ekwipunku."
                )
                return
            looted = list(corpse.items)
            corpse.items.clear()
            recipients = await self._record_corpse_loot(corpse, looted)

            spoken_loot = [
                ITEMS[i]["name"] for i in looted
                if i in ITEMS and self.loot_message_allowed(i)
            ]
            if spoken_loot:
                await self.send(
                    f"Przeszukujesz ciało: {corpse.mob_name}. Zabierasz: "
                    + ", ".join(spoken_loot) + "."
                )
            else:
                await self.send(
                    f"Przeszukujesz ciało: {corpse.mob_name}. "
                    "Zdobyty loot ukrywa aktywny filtr."
                )

            if len(recipients) > 1:
                for recipient in recipients:
                    if recipient is self:
                        continue
                    visible = [
                        ITEMS[i]["name"] for i in looted
                        if i in ITEMS and recipient.loot_message_allowed(i)
                    ]
                    if visible:
                        await recipient.send(
                            f"Loot z ciała drużyny: {corpse.mob_name}. Otrzymujesz: "
                            + ", ".join(visible) + "."
                        )
                    else:
                        await recipient.send(
                            f"Loot z ciała drużyny: {corpse.mob_name}. "
                            "Otrzymane przedmioty ukrywa aktywny filtr."
                        )

            armor_slots = sorted({
                ITEMS[item_id].get("slot")
                for item_id in looted
                if ITEMS.get(item_id, {}).get("type") == "armor"
            })
            if armor_slots:
                commands = {
                    "head": "załóż hełm",
                    "body": "załóż zbroja",
                    "hands": "załóż rękawice",
                    "legs": "załóż nogi",
                    "feet": "załóż buty",
                    "charm": "załóż talizman",
                    "ring": "załóż pierścień",
                    "necklace": "załóż naszyjnik",
                    "earring": "załóż kolczyki",
                    "shoulders": "załóż naramienniki",
                    "belt": "załóż pas",
                    "cloak": "załóż peleryna",
                    "bracers": "załóż karwasze",
                    "relic": "załóż relikt",
                }
                quick = [commands[slot] for slot in armor_slots if slot in commands]
                await self.send(
                    "Zdobyty pancerz możesz założyć. Skróty: "
                    + ", ".join(quick) + "."
                )

    async def get_from_corpse(self, args=""):
            """Zabierz jeden przedmiot albo wszystko z wybranego ciała.

            Przykłady: get sword from 2.corpse; get all from 2.corpse;
            wez miecz z 2.cialo; weź wszystko z 3.ciało.
            """
            raw = str(args or "").strip()
            if not raw:
                await self.send(
                    "Użycie: get <przedmiot> from <ciało> albo wez <przedmiot> z <ciało>. "
                    "Przykład: get all from 2.corpse."
                )
                return

            parts = re.split(r"\s+(?:from|z|ze)\s+", raw, maxsplit=1, flags=re.IGNORECASE)
            if len(parts) != 2:
                await self.send(
                    "Podaj źródło. Przykład: get miecz from 2.corpse albo wez miecz z 2.cialo."
                )
                return
            item_query, corpse_query = parts[0].strip(), parts[1].strip()
            corpse = self.server.world.find_corpse(self.character.room_id, corpse_query)
            if corpse is None:
                await self.send("Nie widzę takiego ciała.")
                return
            if not corpse.items:
                await self.send(f"Ciało {corpse.mob_name} jest już puste.")
                return

            normalized_item = normalize_lookup_text(item_query)
            if normalized_item in ("all", "wszystko", "calosc", "całość"):
                await self.loot_corpse(corpse_query)
                return

            candidates = {
                item_id: ITEMS[item_id]
                for item_id in corpse.items
                if item_id in ITEMS
            }
            found = find_by_name(candidates, item_query)
            if not found:
                await self.send(
                    f"Na ciele {corpse.mob_name} nie ma takiego przedmiotu. "
                    f"Wpisz l in {self.server.world.room_corpses(self.character.room_id).index(corpse)+1}.corpse."
                )
                return
            item_id, item = found
            # Remove first: one corpse item can be distributed only once, even
            # when every local party member receives a personal copy.
            corpse.items.remove(item_id)
            recipients = await self._record_corpse_loot(corpse, [item_id])
            await self.send(
                f"Zabierasz {item['name']} z ciała: {corpse.mob_name}."
            )
            if len(recipients) > 1:
                for recipient in recipients:
                    if recipient is self:
                        continue
                    if recipient.loot_message_allowed(item_id):
                        await recipient.send(
                            f"Loot z ciała drużyny: otrzymujesz {item['name']} z "
                            f"{corpse.mob_name}."
                        )

    async def open_treasure_chest(self, args=""):
            normalized = self.normalize_description_query(str(args or "").strip())
            if normalized in ("geoda", "geode", "geode kamienna", "geoda kamienna", "geoda krysztalowa", "geoda kryształowa", "crystal geode", "stone geode", "geoda astralna", "astral geode"):
                await self.open_geode(args)
                return
            opened_at = self.server.db.treasure_chest_opened_at(
                self.account_id, self.character.room_id
            )
            cfg,remaining=self.server.world.treasure_chest_status(
                self.character.room_id, opened_at
            )
            if not cfg:
                await self.send("Nie ma tutaj skrzyni skarbów do otwarcia.")
                return
            if remaining > 0:
                await self.send(f"{cfg['name']} jest już otwarta i pusta. Odnowi się za około {remaining} sekund.")
                return
            result=self.server.world.open_treasure_chest(self.character.room_id)
            if not result:
                await self.send("Nie udało się otworzyć skrzyni.")
                return
            self.server.db.mark_treasure_chest_opened(
                self.account_id, self.character.room_id
            )
            self.character.silver += int(result["silver"])
            self.character.gold += int(result["gold"])
            for item_id in result["items"]:
                if item_id in ITEMS:
                    self.server.db.add_item(self.account_id,item_id,1)
                    await self.record_item_collection(
                        item_id, source=result["name"], announce=True
                    )
            is_new_chest = self.server.db.add_collection_entry(
                self.account_id, "chests", self.character.room_id
            )
            if is_new_chest:
                await self.send(
                    f"Nowy wpis Codexu: {result['name']}, Skrzynia."
                )
            await self.advance_achievement("chests_opened", 1)
            self.server.db.save_character(self.character)
            rarity_name=TREASURE_CHEST_RARITIES[result["rarity"]][0]
            await self.send(f"Otwierasz: {result['name']}. Rzadkość skrzyni: {rarity_name}.")
            await self.send(
                "Waluta: "
                + currency_reading_text(result["silver"], result["gold"], 0)
                + "."
            )
            spoken_items = [
                ITEMS[i]["name"] for i in result["items"]
                if i in ITEMS and self.loot_message_allowed(i)
            ]
            if spoken_items:
                await self.send("Przedmioty: " + ", ".join(spoken_items) + ".")
            elif result["items"]:
                await self.send("Przedmioty ze skrzyni ukrywa aktywny loot filter.")

    async def show_leaderboards(self, args=""):
            """v0.9.23: trwałe rankingi postaci oparte wyłącznie na zapisanym stanie."""
            raw = self.normalize_description_query(args or "")
            compact = raw.replace(" ", "")
            db = self.server.db

            def floor_rows(kind, limit=10):
                return db.conn.execute(
                    "SELECT c.name AS name, MAX(p.floor) AS score "
                    "FROM characters c JOIN instance_map_progress p ON p.account_id=c.account_id "
                    "WHERE p.instance_kind=? GROUP BY c.account_id,c.name "
                    "HAVING MAX(p.floor)>0 ORDER BY score DESC,c.name COLLATE NOCASE LIMIT ?",
                    (kind, int(limit)),
                ).fetchall()

            def boss_speed_rows(limit=10):
                return db.conn.execute(
                    "SELECT c.name AS name,b.mob_template_id AS boss_id,b.fastest_kill_ms AS ms "
                    "FROM bestiary_stats b JOIN boss_codex_stats bc "
                    "ON bc.account_id=b.account_id AND bc.boss_id=b.mob_template_id "
                    "JOIN characters c ON c.account_id=b.account_id "
                    "WHERE b.fastest_kill_ms IS NOT NULL "
                    "ORDER BY b.fastest_kill_ms ASC,c.name COLLATE NOCASE LIMIT ?",
                    (int(limit),),
                ).fetchall()

            legendary_cache = getattr(type(self).show_leaderboards, "_legendary_ids_v0717", None)
            if not isinstance(legendary_cache, tuple) or legendary_cache[0] != len(ITEMS):
                legendary_ids = frozenset(
                    item_id for item_id, item in ITEMS.items()
                    if item.get("type") in ("armor", "weapon") and (
                        str(item.get("rarity", "")).lower() == "legendary"
                        or item.get("legendary_set_loot")
                        or item.get("legendary_class_relic")
                    )
                )
                legendary_cache = (len(ITEMS), legendary_ids)
                type(self).show_leaderboards._legendary_ids_v0717 = legendary_cache
            legendary_ids = legendary_cache[1]

            def collection_rank(kind, limit=10):
                rows = []
                chars = db.conn.execute(
                    "SELECT account_id,name FROM characters ORDER BY name COLLATE NOCASE"
                ).fetchall()
                for char in chars:
                    discovered = db.collection_entry_ids(char["account_id"], "equipment")
                    if kind == "legends":
                        score = len(discovered.intersection(legendary_ids))
                    else:
                        score = sum(
                            1 for items in COLLECTION_V2_SET_GROUPS.values()
                            if items and set(items).issubset(discovered)
                        )
                    if score > 0:
                        rows.append((char["name"], score))
                rows.sort(key=lambda row: (-row[1], str(row[0]).lower()))
                return rows[:int(limit)]

            async def send_floor(title, kind, limit=10):
                rows = floor_rows(kind, limit)
                await self.send(title + ":")
                if not rows:
                    await self.send("Brak zapisanych wyników.")
                    return
                for pos, row in enumerate(rows, 1):
                    await self.send(f"{pos}. {row['name']} — piętro {int(row['score'])}.")

            async def send_boss(limit=10):
                rows = boss_speed_rows(limit)
                await self.send("Najszybsze pokonania bossów:")
                if not rows:
                    await self.send("Brak zapisanych rekordów.")
                    return
                for pos, row in enumerate(rows, 1):
                    boss_name = BOSS_COLLECTION_CATALOG.get(row["boss_id"], row["boss_id"])
                    await self.send(
                        f"{pos}. {row['name']} — {boss_name}, {int(row['ms'])/1000.0:.2f} s."
                    )

            async def send_collection(title, kind, limit=10):
                rows = collection_rank(kind, limit)
                await self.send(title + ":")
                if not rows:
                    await self.send("Brak zapisanych wyników.")
                    return
                label = "legend" if kind == "legends" else "pełnych setów"
                for pos, (name, score) in enumerate(rows, 1):
                    await self.send(f"{pos}. {name} — {score} {label}.")

            if compact in ("krypta", "crypt"):
                await send_floor("Ranking Krypty", "crypt")
                return
            if compact in ("wieza", "wieża", "astral", "tower", "wiezaastralna"):
                await send_floor("Ranking Wieży Astralnej", "astral")
                return
            if compact in ("boss", "bossowie", "bosses", "czas", "time"):
                await send_boss()
                return
            if compact in ("legendy", "legends", "legendary"):
                await send_collection("Ranking odkrytych legend", "legends")
                return
            if compact in ("sety", "sets", "set"):
                await send_collection("Ranking skompletowanych setów", "sets")
                return
            if compact:
                await self.send(
                    "Użycie: rankingi krypta, rankingi wieza, rankingi boss, "
                    "rankingi legendy albo rankingi sety."
                )
                return
            # Domyślnie krótki Top 5 każdej kategorii, wygodny dla NVDA.
            await send_floor("Ranking Krypty", "crypt", 5)
            await send_floor("Ranking Wieży Astralnej", "astral", 5)
            await send_boss(5)
            await send_collection("Ranking odkrytych legend", "legends", 5)
            await send_collection("Ranking skompletowanych setów", "sets", 5)
