# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: admin_gathering_sales."""

class SessionAdminGatheringSalesMixin:
    def is_admin(self):
            if self.master_account_id is None:
                return False
            username = self.server.db.account_name(self.master_account_id).casefold()
            return bool(username and username in ADMIN_ACCOUNT_NAMES)

    async def admin_command(self, args=""):
            if not self.is_admin():
                await self.send("Nieznana komenda. Wpisz help.")
                return
            raw = str(args or "").strip()
            norm = self.normalize_description_query(raw)
            if not norm or norm in ("help", "pomoc"):
                await self.send("ADMIN OWNER-ONLY")
                await self.send("admin status / administrator status — status uprawnień.")
                await self.send("admin heal / administrator ulecz — pełne HP i Mana.")
                await self.send("admin goto <room_id> / administrator teleport <room_id> — teleport testowy.")
                await self.send("admin give <item_id> [ilość] / administrator daj <item_id> [ilość].")
                await self.send("wipe moje postacie POTWIERDZAM / wipe my characters CONFIRM.")
                await self.send("wipe wszystkie postacie POTWIERDZAM / wipe all characters CONFIRM.")
                await self.send("Wipe usuwa postacie i ich progres, ale NIE usuwa kont/loginów/haseł.")
                return
            if norm in ("status",):
                await self.send(
                    f"Administrator: TAK. Konto: {self.server.db.account_name(self.master_account_id)}."
                )
                return
            if norm in ("heal", "ulecz", "wylecz"):
                self.current_hp = self.max_hp()
                self.current_mana = self.max_mana()
                await self.send(f"ADMIN: HP {self.current_hp}/{self.max_hp()}, Mana {self.current_mana}/{self.max_mana()}.")
                return
            parts = raw.split()
            first = self.normalize_description_query(parts[0]) if parts else ""
            if first in ("goto", "teleport", "idz", "idź"):
                target = " ".join(parts[1:]).strip()
                room_id = target if target in ROOMS else self.find_room(target)
                if not room_id or room_id not in ROOMS:
                    await self.send("ADMIN: nie znaleziono lokacji.")
                    return
                self.character.room_id = room_id
                self.server.db.save_character(self.character)
                await self.send(f"ADMIN: teleport do {ROOMS[room_id]['name']}.")
                await self.look()
                return
            if first in ("give", "daj"):
                if len(parts) < 2:
                    await self.send("Użycie: admin give <item_id> [ilość].")
                    return
                item_id = parts[1]
                try:
                    qty = max(1, min(9999, int(parts[2]) if len(parts) >= 3 else 1))
                except ValueError:
                    qty = 1
                if item_id not in ITEMS:
                    await self.send("ADMIN: nieznany item_id.")
                    return
                self.server.db.add_item(self.account_id, item_id, qty)
                await self.send(f"ADMIN: dodano {ITEMS[item_id]['name']} x{qty}.")
                return
            await self.send("Nieznana opcja admin. Wpisz admin help.")

    async def prepare_character_wipe(self):
            """Wyczyść stan sesyjny bez zapisywania usuwanej postaci."""
            if self.guide_task_active():
                await self.cancel_guide(announce=False)
            for task_name in ("rest_task", "auto_fishing_task", "auto_mining_task", "auto_woodcutting_task", "auto_herbalism_task", "combat_task"):
                task = getattr(self, task_name, None)
                if task and not task.done():
                    task.cancel()
                setattr(self, task_name, None)
            self.resting = False
            self.auto_fishing = self.auto_mining = self.auto_woodcutting = self.auto_herbalism = False
            if self.character:
                await self.leave_party(announce=False)
            self.combat_mob_key = None
            self.account_id = None
            self.character = None
            self.current_hp = 0
            self.current_mana = 0

    async def wipe_command(self, args=""):
            if not self.is_admin():
                await self.send("Nieznana komenda. Wpisz help.")
                return
            norm = self.normalize_description_query(args)
            own_tokens = ("moje postacie", "my characters")
            all_tokens = ("wszystkie postacie", "all characters")
            confirmed_pl = norm.endswith(" potwierdzam")
            confirmed_en = norm.endswith(" confirm")
            if not (confirmed_pl or confirmed_en):
                await self.send(
                    "WIPE wymaga potwierdzenia. Konta NIE zostaną usunięte. "
                    "Użyj: wipe moje postacie POTWIERDZAM albo wipe wszystkie postacie POTWIERDZAM."
                )
                return
            scope = norm.rsplit(" ", 1)[0]
            if scope not in own_tokens + all_tokens:
                await self.send("Nieprawidłowy zakres wipe.")
                return

            if scope in own_tokens:
                target_masters = {int(self.master_account_id)}
            else:
                target_masters = {
                    int(row["id"])
                    for row in self.server.db.conn.execute(
                        "SELECT id FROM accounts WHERE id NOT IN ("
                        "SELECT character_account_id FROM account_characters "
                        "WHERE character_account_id<>master_account_id)"
                    ).fetchall()
                }

            # Inne aktywne sesje z wipe zostają rozłączone bez zapisu usuwanej postaci.
            for session in list(self.server.sessions):
                if session is self or session.master_account_id not in target_masters:
                    continue
                try:
                    await session.send("ADMIN WIPE: postacie zostały wyczyszczone. Konto pozostaje. Połącz się ponownie.")
                    await session.prepare_character_wipe()
                    session.closed = True
                    session.writer.close()
                except Exception:
                    pass

            await self.prepare_character_wipe()
            if scope in own_tokens:
                removed = self.server.db.wipe_characters_for_master(self.master_account_id)
            else:
                removed, _masters = self.server.db.wipe_all_characters_preserve_accounts()
            # Wipe składu drużyn to tylko stan sesyjny.
            self.server.parties.clear()
            self.server.party_invites.clear()
            self.server.party_protectors.clear()
            await self.send(f"WIPE POSTACI zakończony. Usunięto postaci: {removed}. Konta i hasła zachowane.")
            selected = await self.character_selection_flow()
            if selected is True:
                await self.enter_world()

    def boss_floor_chest_here(self):
            return _boss_floor_chest_spec(self.character.room_id) if self.character else None

    async def unlock_boss_floor_chest(self):
            spec = self.boss_floor_chest_here()
            if not spec:
                return False
            kind, floor, power = spec
            key_id = boss_floor_key_id(kind, floor)
            if self.server.db.item_qty(self.account_id, key_id) <= 0:
                await self.send(
                    f"{boss_floor_chest_name(kind, floor)} jest zamknięta. "
                    f"Nie masz właściwego klucza. Klucz znajduje się w ciele bossa tego piętra."
                )
                return True
            if not self.server.db.remove_item(self.account_id, key_id, 1):
                await self.send("Nie udało się zużyć klucza.")
                return True
            reward = boss_chest_reward_roll(kind, floor, power)
            self.character.gold += int(reward["gold"])
            for item_id in reward["items"]:
                self.server.db.add_item(self.account_id, item_id, 1)
                await self.record_item_collection(item_id, source=boss_floor_chest_name(kind, floor), announce=True)
            self.server.db.save_character(self.character)
            await self.send(
                f"Odkluczasz i otwierasz: {boss_floor_chest_name(kind, floor)}. "
                f"Klucz zostaje zużyty. Złoto: +{reward['gold']}."
            )
            if reward["items"]:
                await self.send("Nagrody: " + ", ".join(ITEMS[i]["name"] for i in reward["items"]) + ".")
            return True

    async def unlock_context(self, args=""):
            q = self.normalize_description_query(args)
            if q in ("soul", "dusza", "bron duszy", "broń duszy"):
                await self.unlock()
                return
            if self.boss_floor_chest_here() is not None:
                await self.unlock_boss_floor_chest()
                return
            await self.unlock()

    def profession_ready(self):
            now = time.time()
            remaining = PROFESSION_COOLDOWN - (now - self.last_profession_action)
            if remaining > 0:
                return False, remaining
            self.last_profession_action = now
            return True, 0.0

    def current_infinite_gather_feature(self, tool_type=None):
            """Bonus aktualnego proceduralnego sektora zbieractwa.

            Dane są zapisane w definicji pokoju, więc zwykły świat i ręcznie
            przygotowane poziomy zachowują dokładnie dotychczasowe nagrody.
            """
            room = ROOMS.get(self.character.room_id, {}) if self.character else {}
            feature = room.get("infinite_gather_feature") or {}
            event_feature = v0140_gather_event_bonus(self.character.room_id, tool_type=tool_type) if self.character else {"label":"", "quantity_bonus":0, "xp_mult":1.0}
            env_feature = v0150_environment_bonus(self.character.room_id, tool_type=tool_type) if self.character else {"label":"", "quantity_bonus":0, "xp_mult":1.0}
            global_feature = v0250_gather_hotspot(self.character.room_id, tool_type=tool_type) if self.character else {"label":"", "quantity_bonus":0, "xp_mult":1.0}
            labels = [
                str(feature.get("label", "") or ""),
                str(event_feature.get("label", "") or ""),
                str(env_feature.get("label", "") or ""),
                str(global_feature.get("label", "") or ""),
            ]
            return {
                "label": " + ".join(label for label in labels if label),
                "quantity_bonus": (
                    max(0, int(feature.get("quantity_bonus", 0) or 0))
                    + max(0, int(event_feature.get("quantity_bonus", 0) or 0))
                    + max(0, int(env_feature.get("quantity_bonus", 0) or 0))
                    + max(0, int(global_feature.get("quantity_bonus", 0) or 0))
                ),
                "xp_mult": (
                    max(1.0, float(feature.get("xp_mult", 1.0) or 1.0))
                    * max(1.0, float(event_feature.get("xp_mult", 1.0) or 1.0))
                    * max(1.0, float(env_feature.get("xp_mult", 1.0) or 1.0))
                    * max(1.0, float(global_feature.get("xp_mult", 1.0) or 1.0))
                ),
            }

    async def announce_infinite_gather_feature(self, feature):
            if not feature.get("label"):
                self.last_gather_feature_signature = None
                return
            qty = int(feature.get("quantity_bonus", 0) or 0)
            xp_mult = float(feature.get("xp_mult", 1.0) or 1.0)
            # v0.30.7: pogoda/pora i inne stałe warunki sektora nie są
            # powtarzane przy każdym połowie, wydobyciu, cięciu lub zbiorze.
            # Gdy warunki faktycznie się zmienią, nowy komunikat padnie raz.
            signature = (str(feature.get("label", "")), qty, round(xp_mult, 6))
            if signature == self.last_gather_feature_signature:
                return
            self.last_gather_feature_signature = signature
            parts = []
            if qty:
                parts.append(f"+{qty} do bazowego zbioru")
            if xp_mult > 1.0:
                parts.append(f"+{int(round((xp_mult - 1.0) * 100))} procent XP profesji i narzędzia")
            await self.send(
                f"SPECJALNY SEKTOR — {feature['label']}: " + ", ".join(parts) + "."
            )

    async def fish(self, from_auto=False):
            if self.combat_mob_key:
                await self.send("Nie możesz łowić podczas walki.")
                return
            if self.character.room_id not in FISHING_ROOMS:
                await self.send("Tutaj nie ma odpowiedniego łowiska.")
                return
            if self.server.db.item_qty(self.account_id, "fishing_rod") <= 0:
                await self.send("Do Wędkarstwa potrzebujesz Wędki. Kup ją u Rybaka Tomasa na Targu Rybnym.")
                return
            ready, remaining = self.profession_ready()
            if not ready:
                if not from_auto:
                    await self.send("Musisz chwilę odczekać przed kolejnym zarzuceniem wędki.")
                return

            tool = self.server.db.tool(self.account_id, "fishing")
            tool_level = int(tool["level"])
            profession_level = self.profession_level_for_tool("fishing")
            action_seconds = self.profession_action_seconds(
                "fishing", profession_level
            )
            await self.send(
                f"Zarzucasz Wędkę. Czas połowu: "
                f"{action_seconds} sekund."
            )
            await asyncio.sleep(action_seconds)

            habitat = self.fishing_habitat()
            base_item_id = self.fishing_loot(
                tool_level, habitat=habitat
            )
            item_id = roll_fish_variant(
                base_item_id, tool_level
            )
            base_quantity = roll_profession_gather_quantity(tool_level, profession_level, "fishing")
            gather_feature = self.current_infinite_gather_feature("fishing")
            base_quantity += gather_feature["quantity_bonus"]
            self.store_profession_resource(item_id, base_quantity)
            item = ITEMS[item_id]
            resource_quest_quantity = base_quantity
            if item_id != base_item_id:
                await self.send(
                    f"RZADKI WARIANT RYBY: "
                    f"{item.get('rare_resource_label', 'rzadki')}."
                )
            await self.send(
                f"Łowisz: {item['name']} x{base_quantity}. "
                "Połów trafia do Siatki na ryby."
            )
            await self.announce_infinite_gather_feature(gather_feature)

            current_tier = tool_tier(tool_level)
            bonus_chance = min(
                0.50,
                tool_tier_bonus_chance(tool_level)
                + self.character.racial_profession_bonus_chance()
            )
            if bonus_chance > 0 and random.random() < bonus_chance:
                self.store_profession_resource(item_id, 1)
                resource_quest_quantity += 1
                await self.send(
                    f"Bonus Tieru {current_tier} Wędki: wyciągasz dodatkowo {item['name']} x1."
                )

            species_id = base_fish_species_id(item_id)
            measurements = [
                roll_fish_measurement(item_id)
                for _ in range(max(1, resource_quest_quantity))
            ]
            best_length = max(length for length, _weight in measurements)
            best_weight = max(weight for _length, weight in measurements)
            journal_result = self.server.db.record_fish_catch(
                self.account_id, species_id, resource_quest_quantity,
                best_length, best_weight, self.character.room_id,
            )
            global_record_v022 = self.server.db.record_fishing_global_v022(
                species_id, item_id, self.character.name, best_length, best_weight, self.account_id
            )
            await self.record_item_collection(
                species_id, source=self.fishing_water_type() or "łowisko",
                announce=True, record_history=False, amount=resource_quest_quantity
            )
            await self.send(
                f"Okaz: {format_fish_length(best_length)}, {format_fish_weight(best_weight)}. "
                f"Rzadkość gatunku: {fish_rarity_label(species_id)}."
            )
            if journal_result["new_species"]:
                await self.send(
                    f"NOWY GATUNEK W DZIENNIKU RYB: {ITEMS[species_id]['name']}."
                )
                self.server.db.add_lifetime_stat(
                    self.account_id, "fish_species_discovered", 1
                )
            elif journal_result["new_length_record"] or journal_result["new_weight_record"]:
                parts = []
                if journal_result["new_length_record"]:
                    parts.append(
                        f"długość {format_fish_length(journal_result['best_length_mm'])}"
                    )
                if journal_result["new_weight_record"]:
                    parts.append(
                        f"masa {format_fish_weight(journal_result['best_weight_g'])}"
                    )
                await self.send(
                    f"NOWY REKORD {ITEMS[species_id]['name']}: "
                    + ", ".join(parts) + "."
                )
                self.server.db.add_lifetime_stat(
                    self.account_id, "fish_record_updates", 1
                )
            if fish_species_rarity(species_id) == "legendary":
                self.server.db.add_lifetime_stat(
                    self.account_id, "legendary_fish_caught", resource_quest_quantity
                )
            if global_record_v022.get("new_global_length") or global_record_v022.get("new_global_weight") or global_record_v022.get("new_global_rarest"):
                parts=[]
                if global_record_v022.get("new_global_length"): parts.append("rekord długości serwera")
                if global_record_v022.get("new_global_weight"): parts.append("rekord masy serwera")
                if global_record_v022.get("new_global_rarest"): parts.append("najrzadszy okaz serwera")
                await self.send("REKORDY WĘDKARSKIE — " + ", ".join(parts) + ".")

            await self.announce_resource_quest_progress(
                item_id, resource_quest_quantity
            )
            await self.announce_collect_category_quest_progress("fish", resource_quest_quantity)
            await self.announce_distinct_category_quest_progress("fish", species_id)
            await self.announce_collect_category_quest_progress(
                f"fish_{habitat}", resource_quest_quantity
            )
            await self.advance_bounty("fish", item_id, resource_quest_quantity)
            await self.advance_legendary_contract_v022("fish", resource_quest_quantity)
            await self.advance_dynamic_world_quest_v015("fish", item_id, resource_quest_quantity)
            await self.add_faction_reputation_v016("waters", 1, reason="fishing")
            self.server.db.add_lifetime_stat(self.account_id, "fish_caught", resource_quest_quantity)
            self.server.db.add_lifetime_stat(self.account_id, "profession_actions", 1)
            if item_id in RARE_FISH_VARIANT_IDS:
                await self.advance_achievement("rare_fish_caught", resource_quest_quantity)
                self.server.db.add_lifetime_stat(self.account_id, "rare_fish_caught", resource_quest_quantity)

            fish_xp_scale = v096_fishing_reward_scale(profession_level)
            floor_xp_mult = gather_feature["xp_mult"]
            profession_xp = max(1, int(round((10 + random.randint(0, 5)) * fish_xp_scale * floor_xp_mult)))
            tool_xp = balanced_gather_tool_xp(
                "fishing",
                max(1, int(round((8 + random.randint(0, 4)) * fish_xp_scale * floor_xp_mult))),
            )
            messages, profession_level, new_tool_level = self.grant_profession_progress(
                "Wędkarstwo", profession_xp, "fishing", tool_xp,
            )
            for msg in messages:
                await self.send(msg)
            await self.sync_extended_achievements()
            if new_tool_level != tool_level:
                await self.send(
                    f"Wędka ma teraz poziom {new_tool_level}, Tier "
                    f"{tool_tier(new_tool_level)}: "
                    f"{tool_tier_name('fishing', new_tool_level)}."
                )

    async def mine(self, from_auto=False):
            if self.combat_mob_key:
                await self.send("Nie możesz wydobywać podczas walki.")
                return
            if not is_mining_room(self.character.room_id):
                await self.send("Tutaj nie ma odpowiedniego złoża.")
                return
            if self.server.db.item_qty(self.account_id, "pickaxe") <= 0:
                await self.send("Do Górnictwa potrzebujesz Kilofa. Kup go u Górnika Torena przy Wejściu do Kopalni Głębinowej.")
                return
            ready, remaining = self.profession_ready()
            if not ready:
                if not from_auto:
                    await self.send("Musisz chwilę odczekać przed kolejnym uderzeniem kilofa.")
                return

            tool = self.server.db.tool(self.account_id, "mining")
            tool_level = int(tool["level"])
            profession_level = self.profession_level_for_tool("mining")
            action_seconds = self.profession_action_seconds(
                "mining", profession_level
            )
            await self.send(
                f"Rozpoczynasz wydobycie Kilofem. "
                f"Czas wydobycia: {action_seconds} sekund."
            )
            await asyncio.sleep(action_seconds)

            gather_feature = self.current_infinite_gather_feature("mining")
            item_id = self.mining_loot(
                tool_level, self.character.room_id
            )

            if not item_id or item_id not in ITEMS:
                await self.send("Nie udało się odnaleźć prawidłowego urobku dla tego poziomu kopalni.")
                return

            vein = roll_mining_vein(tool_level)
            vein_quantity = int(vein["quantity"]) + gather_feature["quantity_bonus"]
            self.store_profession_resource(item_id, vein_quantity)
            mined_resource_quantity = vein_quantity
            item = ITEMS[item_id]
            await self.record_item_collection(
                item_id, source="Górnictwo", announce=True, record_history=False, amount=vein_quantity
            )
            await self.send(
                f"ŻYŁA: {vein['name']}. "
                f"Wydobywasz: {item['name']} x{vein_quantity}. "
                "Urobek trafia do Sakwy górniczej."
            )
            await self.announce_infinite_gather_feature(gather_feature)

            current_tier = tool_tier(tool_level)
            bonus_chance = min(
                0.50,
                tool_tier_bonus_chance(tool_level)
                + self.character.racial_profession_bonus_chance()
            )
            if bonus_chance > 0 and random.random() < bonus_chance:
                self.store_profession_resource(item_id, 1)
                mined_resource_quantity += 1
                await self.send(
                    f"Bonus Tieru {current_tier} Kilofa: wydobywasz dodatkowo {item['name']} x1."
                )

            # v0.34.4: Mithril jest walutą, nie rudą. Jest niezależnym bonusem
            # i nigdy nie zastępuje normalnego urobku.
            floor_for_currency = mine_floor_number(self.character.room_id)
            dungeon_for_currency, dungeon_floor_for_currency = profession_dungeon_floor(self.character.room_id)
            if dungeon_for_currency == "crystal_mine":
                floor_for_currency = min(400, max(1, int(dungeon_floor_for_currency) * 10))
            mithril_chance = mining_mithril_currency_chance(
                tool_level, profession_level, floor_for_currency or 1
            )
            if mithril_chance > 0 and random.random() < mithril_chance:
                self.character.mithril += 1
                self.server.db.save_character(self.character)
                self.server.db.add_lifetime_stat(self.account_id, "mithril_mined", 1)
                await self.send(
                    "MITHRIL: odkrywasz czysty mithril walutowy x1. "
                    "Trafia bezpośrednio do wspólnego portfela konta."
                )

            gem_id = self.mining_gem_drop(
                tool_level, profession_level, self.character.room_id,
            )
            if gem_id:
                self.store_profession_resource(gem_id, 1)
                quality = ITEMS[gem_id].get("gem_quality", "raw")
                quality_text = GEM_QUALITY_INFO.get(quality, GEM_QUALITY_INFO["raw"])["label"]
                await self.send(
                    f"KLEJNOT {quality_text.upper()}: znajdujesz {ITEMS[gem_id]['name']} x1. "
                    "Kamień trafia do Sakwy Górnika."
                )
                await self.record_item_collection(
                    gem_id, source="Górnictwo: klejnot", announce=True, record_history=False
                )
                await self.advance_achievement("gems_found", 1)
                self.server.db.add_lifetime_stat(self.account_id, "gems_found", 1)

            floor_for_geode = mine_floor_number(self.character.room_id)
            dungeon_name, dungeon_floor = profession_dungeon_floor(self.character.room_id)
            if dungeon_name == "crystal_mine":
                floor_for_geode = min(400, int(dungeon_floor) * 10)
            geode_id = roll_mining_geode(
                tool_level, profession_level, floor_for_geode or 1
            )
            if geode_id:
                self.store_profession_resource(geode_id, 1)
                await self.send(
                    f"GEODA: znajdujesz {ITEMS[geode_id]['name']} x1. "
                    "Trafia do Sakwy Górnika. Otwórz: open geode / otwórz geodę."
                )

            await self.announce_resource_quest_progress(
                item_id, mined_resource_quantity
            )
            await self.announce_collect_category_quest_progress("ore", mined_resource_quantity)
            await self.advance_bounty("mine", item_id, mined_resource_quantity)
            await self.advance_legendary_contract_v022("gather", mined_resource_quantity)
            await self.advance_dynamic_world_quest_v015("mine", item_id, mined_resource_quantity)
            await self.add_faction_reputation_v016("miners", 1, reason="mining")
            self.server.db.add_lifetime_stat(self.account_id, "ore_mined", mined_resource_quantity)

            self.server.db.add_lifetime_stat(self.account_id, "profession_actions", 1)
            floor_xp_mult = gather_feature["xp_mult"]
            messages, profession_level, new_tool_level = self.grant_profession_progress(
                "Górnictwo",
                max(1, int(round((10 + random.randint(0, 5)) * floor_xp_mult))),
                "mining",
                balanced_gather_tool_xp(
                    "mining",
                    max(1, int(round((8 + random.randint(0, 4)) * floor_xp_mult))),
                ),
            )
            for msg in messages:
                await self.send(msg)
            await self.sync_extended_achievements()
            if new_tool_level != tool_level:
                await self.send(
                    f"Kilof ma teraz poziom {new_tool_level}, Tier "
                    f"{tool_tier(new_tool_level)}: "
                    f"{tool_tier_name('mining', new_tool_level)}."
                )
            if new_tool_level >= 80 and tool_level < 80:
                await self.send(
                    "Twój Kilof osiągnął poziom 80. Od poziomu kopalni 80 możesz znaleźć mithril bezpośrednio jako walutę."
                )

            floor = mine_floor_number(self.character.room_id)
            if floor is not None:
                wall = self.server.db.add_mine_wall_hit(
                    self.account_id, floor
                )
                if wall["unlocked_floor"] is not None:
                    unlocked = wall["unlocked_floor"]
                    await self.send(
                        f"Przebijasz ścianę w dół! "
                        f"Odblokowano Kopalnię - poziom {unlocked}."
                    )
                    if from_auto and self.auto_mining:
                        descended = await self.auto_mine_descend_if_unlocked()
                        if not descended:
                            await self.send(
                                "Ściana jest przebita, ale auto-kopanie "
                                "nie może bezpiecznie zejść w dół."
                            )
                elif floor == wall["max_floor_unlocked"]:
                    required_hits = wall["wall_required_hits"]
                    await self.send(
                        f"Ściana w dół: {wall['wall_hits']} z "
                        f"{required_hits} uderzeń."
                    )

    async def woodcut(self, from_auto=False):
            if self.combat_mob_key:
                await self.send("Nie możesz ścinać drzew podczas walki.")
                return
            if self.character.room_id not in WOODCUTTING_ROOMS:
                await self.send("Tutaj nie ma odpowiednich drzew do Drwalstwa.")
                return
            if self.server.db.item_qty(self.account_id, "saw") <= 0:
                await self.send("Do Drwalstwa potrzebujesz Piły. Kup ją u Mistrza Drwalstwa Orena w Leśniczówce.")
                return
            ready, remaining = self.profession_ready()
            if not ready:
                if not from_auto:
                    await self.send("Musisz chwilę odczekać przed kolejnym cięciem.")
                return

            tool = self.server.db.tool(self.account_id, "woodcutting")
            tool_level = int(tool["level"])
            profession_level = self.profession_level_for_tool("woodcutting")
            action_seconds = self.profession_action_seconds(
                "woodcutting", profession_level
            )
            await self.send(
                f"Rozpoczynasz cięcie Piłą. "
                f"Czas cięcia: {action_seconds} sekund."
            )
            await asyncio.sleep(action_seconds)

            base_item_id = self.woodcutting_loot(
                tool_level, self.character.room_id
            )
            item_id = roll_wood_variant(
                base_item_id, tool_level
            )
            base_quantity = roll_profession_gather_quantity(tool_level, profession_level, "woodcutting")
            gather_feature = self.current_infinite_gather_feature("woodcutting")
            base_quantity += gather_feature["quantity_bonus"]
            self.store_profession_resource(item_id, base_quantity)
            resource_quest_quantity = base_quantity
            item = ITEMS[item_id]
            if item_id != base_item_id:
                await self.send(
                    f"RZADKI WARIANT DRZEWA: "
                    f"{item.get('rare_resource_label', 'rzadki')}."
                )
            await self.send(
                f"Pozyskujesz: {item['name']} x{base_quantity}. "
                "Drewno trafia na Stos drewna."
            )
            await self.announce_infinite_gather_feature(gather_feature)

            current_tier = tool_tier(tool_level)
            bonus_chance = min(
                0.50,
                tool_tier_bonus_chance(tool_level)
                + self.character.racial_profession_bonus_chance()
            )
            if bonus_chance > 0 and random.random() < bonus_chance:
                self.store_profession_resource(item_id, 1)
                resource_quest_quantity += 1
                await self.send(
                    f"Bonus Tieru {current_tier} Piły: pozyskujesz dodatkowo {item['name']} x1."
                )

            await self.record_item_collection(
                item_id, source="Drwalstwo", announce=True, record_history=False, amount=resource_quest_quantity
            )
            await self.announce_resource_quest_progress(item_id, resource_quest_quantity)
            await self.announce_collect_category_quest_progress("wood", resource_quest_quantity)
            await self.advance_bounty("wood", item_id, resource_quest_quantity)
            await self.advance_legendary_contract_v022("gather", resource_quest_quantity)
            await self.advance_dynamic_world_quest_v015("wood", item_id, resource_quest_quantity)
            await self.add_faction_reputation_v016("green_path", 1, reason="woodcutting")
            self.server.db.add_lifetime_stat(self.account_id, "wood_gathered", resource_quest_quantity)
            self.server.db.add_lifetime_stat(self.account_id, "profession_actions", 1)

            floor_xp_mult = gather_feature["xp_mult"]
            messages, profession_level, new_tool_level = self.grant_profession_progress(
                "Drwalstwo",
                max(1, int(round((10 + random.randint(0, 5)) * floor_xp_mult))),
                "woodcutting",
                balanced_gather_tool_xp(
                    "woodcutting",
                    max(1, int(round((8 + random.randint(0, 4)) * floor_xp_mult))),
                ),
            )
            for msg in messages:
                await self.send(msg)
            await self.sync_extended_achievements()
            if new_tool_level != tool_level:
                await self.send(
                    f"Piła ma teraz poziom {new_tool_level}, Tier "
                    f"{tool_tier(new_tool_level)}: "
                    f"{tool_tier_name('woodcutting', new_tool_level)}."
                )

    async def gather_herb(self, from_auto=False):
            if self.combat_mob_key:
                await self.send("Nie możesz zbierać ziół podczas walki.")
                return
            if self.character.room_id not in HERBALISM_ROOMS:
                await self.send("Tutaj nie ma odpowiednich ziół.")
                return
            if self.server.db.item_qty(self.account_id, "herbalist_sickle") <= 0:
                await self.send("Do Zielarstwa potrzebujesz Sierpa Zielarskiego. Kup go u Mistrzyni Zielarstwa Seny w Ogrodzie Zielarskim.")
                return
            ready, remaining = self.profession_ready()
            if not ready:
                if not from_auto:
                    await self.send("Musisz chwilę odczekać przed kolejnym zbiorem.")
                return

            tool = self.server.db.tool(self.account_id, "herbalism")
            old_level = int(tool["level"])
            profession_level = self.profession_level_for_tool("herbalism")
            action_seconds = self.profession_action_seconds(
                "herbalism", profession_level
            )
            await self.send(
                f"Rozpoczynasz zbiór Sierpem Zielarskim. "
                f"Czas zbioru: {action_seconds} sekund."
            )
            await asyncio.sleep(action_seconds)

            base_item_id = self.herbalism_loot(
                old_level, self.character.room_id
            )
            item_id = roll_herb_variant(
                base_item_id, old_level
            )
            base_quantity = roll_profession_gather_quantity(old_level, profession_level, "herbalism")
            gather_feature = self.current_infinite_gather_feature("herbalism")
            base_quantity += gather_feature["quantity_bonus"]
            self.store_profession_resource(item_id, base_quantity)
            resource_quest_quantity = base_quantity
            if item_id != base_item_id:
                await self.send(
                    f"RZADKI WARIANT ROŚLINY: "
                    f"{ITEMS[item_id].get('rare_resource_label', 'rzadki')}."
                )
            await self.send(
                f"Zbierasz: {ITEMS[item_id]['name']} x{base_quantity}. "
                "Roślina trafia do Torby Zielarskiej."
            )
            await self.announce_infinite_gather_feature(gather_feature)

            bonus_chance = min(
                0.50,
                tool_tier_bonus_chance(old_level) + self.character.racial_profession_bonus_chance()
            )
            if bonus_chance > 0 and random.random() < bonus_chance:
                self.store_profession_resource(item_id, 1)
                resource_quest_quantity += 1
                await self.send(
                    f"Bonus Tieru {tool_tier(old_level)} Sierpa Zielarskiego: "
                    f"zbierasz dodatkowo {ITEMS[item_id]['name']} x1."
                )

            await self.record_item_collection(
                item_id, source="Zielarstwo", announce=True, record_history=False, amount=resource_quest_quantity
            )
            await self.announce_resource_quest_progress(
                item_id, resource_quest_quantity
            )
            await self.announce_collect_category_quest_progress("herb", resource_quest_quantity)
            await self.advance_bounty("herb", item_id, resource_quest_quantity)
            await self.advance_legendary_contract_v022("gather", resource_quest_quantity)
            await self.advance_dynamic_world_quest_v015("herb", item_id, resource_quest_quantity)
            await self.add_faction_reputation_v016("green_path", 1, reason="herbalism")
            self.server.db.add_lifetime_stat(self.account_id, "herbs_gathered", resource_quest_quantity)
            self.server.db.add_lifetime_stat(self.account_id, "profession_actions", 1)

            floor_xp_mult = gather_feature["xp_mult"]
            messages, profession_level, new_tool_level = self.grant_profession_progress(
                "Zielarstwo",
                max(1, int(round((10 + random.randint(0, 5)) * floor_xp_mult))),
                "herbalism",
                balanced_gather_tool_xp(
                    "herbalism",
                    max(1, int(round((8 + random.randint(0, 4)) * floor_xp_mult))),
                ),
            )
            for msg in messages:
                await self.send(msg)
            await self.sync_extended_achievements()
            if new_tool_level != old_level:
                await self.send(
                    f"Sierp Zielarski ma teraz poziom {new_tool_level}, Tier "
                    f"{tool_tier(new_tool_level)}: {tool_tier_name('herbalism', new_tool_level)}."
                )

    def generic_item_sale_allowed_here(self):
            # Zwykłe przedmioty można odsprzedawać w każdej lokacji z normalnym sklepem.
            return self.character.room_id in SHOPS

    def generic_item_sale_buyer_name(self):
            seller_id = SHOP_SELLERS.get(self.character.room_id)
            seller = NPCS.get(seller_id) if seller_id else None
            return seller.get("name") if seller else "lokalny handlarz"

    def market_buyer_rejects_item(self, item_id, item):
            # v0.9.15: Rynek ma osobny skup łupów/EQ, ale nigdy nie przejmuje
            # sprzedaży profesji. Każdy surowiec typu resource zostaje dla
            # właściwego fachowca albo systemu craftingu.
            if self.character.room_id != "market":
                return False
            if not item:
                return True
            if item.get("type") in {"resource", "craft_material"}:
                return True
            if item_id in CRAFT_MATERIAL_STORAGE_IDS:
                return True
            if item_id in (
                FISH_STORAGE_IDS | MINING_STORAGE_IDS | WOOD_STORAGE_IDS | HERB_STORAGE_IDS
            ):
                return True
            return False

    def blacksmith_crafted_sale_cap_v0341(self, item_id, item):
            """Cap NPC resale of crafted blacksmith gear by the value of consumed ore.

            Smithing should create equipment and profession progress, not multiply currency.
            Normal crafts are worth at most 90% of the source ore opportunity value; only
            high-quality/critical crafts can earn a modest premium.
            """
            material_key = str(item.get("blacksmith_material") or "").strip()
            if not material_key:
                return None

            tier = next((row for row in BLACKSMITH_TIERS if str(row.get("key")) == material_key), None)
            if not tier:
                return None
            ore = ITEMS.get(str(tier.get("ore")), {})
            ore_value = legacy_currency_to_coins(
                ore.get("sell_silver", 0), ore.get("sell_gold", 0), ore.get("sell_mithril", 0)
            )
            if ore_value <= 0:
                return None

            slot = str(item.get("slot") or "")
            slot_row = BLACKSMITH_SLOT_DEFS.get(slot)
            if not slot_row:
                return None
            ingot_cost = max(1, int(slot_row[2] or 1))
            material_value = ore_value * ingot_cost

            quality = str(item.get("craft_quality_v03054") or "normal").lower()
            quality_factor = {
                "normal": 0.90,
                "good": 0.95,
                "excellent": 1.00,
                "masterwork": 1.08,
                "legendary": 1.18,
            }.get(quality, 0.90)
            if item.get("craft_critical_v03054"):
                quality_factor += 0.05
            return max(1, int(material_value * quality_factor))

    def generic_item_sale_value(self, item_id, item):
            smith_cap = self.blacksmith_crafted_sale_cap_v0341(item_id, item)
            # Jawna cena sprzedaży ma pierwszeństwo.
            explicit = {
                "silver": int(item.get("sell_silver", 0) or 0),
                "gold": int(item.get("sell_gold", 0) or 0),
                "mithril": int(item.get("sell_mithril", 0) or 0),
            }
            if any(explicit.values()):
                if item.get("blacksmith_material"):
                    total = legacy_currency_to_coins(
                        explicit["silver"], explicit["gold"], explicit["mithril"]
                    )
                    if smith_cap is not None:
                        total = min(total, smith_cap)
                    return {"silver": total, "gold": 0, "mithril": 0}
                if item_id in FISH_STORAGE_IDS:
                    total = legacy_currency_to_coins(
                        explicit["silver"], explicit["gold"], explicit["mithril"]
                    )
                    total = max(1, int(round(total * v096_fish_price_scale(item_id))))
                    return {"silver": total, "gold": 0, "mithril": 0}
                return explicit

            # Przedmiot kupny: sklep odkupuje za 50% ceny bazowej.
            price = item.get("price")
            currency = item.get("currency", "silver")
            if isinstance(price, (int, float)) and price > 0 and currency in explicit:
                value = max(1, int(price) // 2)
                result = {"silver": 0, "gold": 0, "mithril": 0}
                result[currency] = value
                if smith_cap is not None:
                    total = legacy_currency_to_coins(result["silver"], result["gold"], result["mithril"])
                    total = min(total, smith_cap)
                    return {"silver": total, "gold": 0, "mithril": 0}
                return result

            # v0.9.15: zwykły loot z mobów (np. kły i trofea) można
            # sprzedać w każdym normalnym sklepie. Jawne sell_* nadal ma pierwszeństwo.
            if item.get("type") == "loot":
                rarity_bonus = {
                    "common": 0, "rare": 20, "epic": 60,
                    "legendary": 150, "mythic": 350, "unique": 600,
                }.get(str(item.get("rarity") or "common"), 0)
                loot_value = max(1, int(item.get("loot_sell_silver", 25) or 25))
                return {"silver": loot_value + rarity_bonus, "gold": 0, "mithril": 0}

            # v0.8.61: zdobyty/craftowany ekwipunek bez ceny sklepowej ma
            # wartość zgodną z materiałem, statystykami i właściwościami.
            if item.get("type") == "armor":
                defense = max(0, int(item.get("defense", 0) or 0))
                affix = max(0, abs(int(item.get("affix_amount", 0) or 0)))
                sockets = max(0, int(item.get("sockets", 0) or 0))
                mastery = max(0, int(item.get("required_mastery", 0) or 0))
                craft_level = max(
                    int(item.get("jewelcraft_level", 0) or 0),
                    int(item.get("blacksmith_tier", 0) or 0) * 10,
                )
                material_key = str(item.get("corpse_material") or item.get("blacksmith_material") or "")
                material_base = V0863_MATERIAL_SALE_BASE_SILVER.get(
                    material_key, 0
                )
                stat_power = sum(max(0, int(v or 0)) for v in (item.get("stats") or {}).values())
                property_power = sum(max(0.0, float(v or 0)) for v in (item.get("properties") or {}).values())
                silver = max(
                    25,
                    material_base
                    + defense * 40
                    + affix * 30
                    + sockets * 150
                    + mastery * 20
                    + craft_level * 25
                    + stat_power * 120
                    + int(property_power * 250),
                )
                if smith_cap is not None:
                    silver = min(silver, smith_cap)
                return {"silver": silver, "gold": 0, "mithril": 0}

            return {"silver": 0, "gold": 0, "mithril": 0}

    def generic_item_is_sellable(self, item_id, item):
            if not item or item.get("type") in {"quest", "tool", "resource", "craft_material"}:
                return False
            if item_id in CRAFT_MATERIAL_STORAGE_IDS:
                return False
            if is_character_bound_item(item_id):
                return False
            values = self.generic_item_sale_value(item_id, item)
            return any(values.values())

    def resource_sale_allowed_here(self, item_id):
            # v0.8.67: surowce profesji skupują tylko właściwi fachowcy.
            room_id = self.character.room_id
            if item_id in FISH_STORAGE_IDS:
                return room_id == "fish_market"
            if item_id in MINING_STORAGE_IDS:
                return room_id == "mountain_market"
            if item_id in WOOD_STORAGE_IDS:
                return room_id == "lumberjack_camp"
            if item_id in HERB_STORAGE_IDS:
                return room_id == "herbalist_hut"
            return False

    def resource_sale_location_text(self, container):
            return {
                "net": "Targ Rybny — Rybak Borys i rybacy",
                "bag": "Górski Targ Minerałów — Handlarka Minerałów Dagna",
                "woodpile": "Obóz Drwala — Drwal Bran",
                "herbbag": "Chata Zielarki — Zielarka Liora",
            }.get(container, "właściwy punkt skupu profesji")

    def resource_sale_buyer_text(self, container):
            return {
                "net": "Rybakom na Targu Rybnym",
                "bag": "Handlarce Minerałów Dagnie",
                "woodpile": "Drwalowi Branowi",
                "herbbag": "Zielarce Liorze",
            }.get(container, "właściwemu skupującemu")

    def profession_sale_definition(self, container):
            # v0.8.68: sprzedaż u właściwego fachowca rozwija specjalizację/profesję,
            # ale nie narzędzie. EXP jest liczony za faktycznie sprzedane sztuki.
            return {
                "net": ("Wędkarstwo", "fishing"),
                "bag": ("Górnictwo", "mining"),
                "woodpile": ("Drwalstwo", "woodcutting"),
                "herbbag": ("Zielarstwo", "herbalism"),
            }.get(container)

    def grant_profession_sale_xp(self, container, units):
            definition = self.profession_sale_definition(container)
            units = max(0, int(units or 0))
            if not definition or units <= 0:
                return []

            profession, _tool_type = definition
            prow = self.server.db.profession(self.account_id, profession)
            level = int(prow["level"])
            # 1 bazowy XP za sztukę; Wędkarstwo v0.9.6 kompensuje szybszy endgame.
            xp_scale = v096_fishing_reward_scale(level) if container == "net" else 1.0
            actual_xp = max(1, int(round(units * PROFESSION_XP_GAIN_MULTIPLIER * xp_scale)))
            actual_xp = self.apply_double_xp(actual_xp)
            xp = int(prow["xp"]) + actual_xp
            actions = int(prow["actions"])
            cap = profession_max_level(profession)
            old_rank = profession_rank(level, profession)
            messages = [
                f"{profession}: sprzedaż +{actual_xp} XP specjalizacji "
                f"za {units} sztuk."
            ]

            while level < cap:
                needed = self.profession_xp_to_next(level, profession)
                if xp < needed:
                    break
                xp -= needed
                level += 1
                messages.append(f"{profession} osiąga poziom {level}.")

            if level >= cap:
                level = cap
                xp = 0

            self.server.db.save_profession(
                self.account_id, profession, level, xp, actions
            )

            new_rank = profession_rank(level, profession)
            if new_rank > old_rank:
                messages.append(
                    f"{profession}: awansujesz na Rangę {new_rank} "
                    f"z {profession_max_rank(profession)}: "
                    f"{profession_rank_name(profession, level)}."
                )
            return messages

    def profession_sale_units_for_rows(self, rows):
            totals = {"net": 0, "bag": 0, "woodpile": 0, "herbbag": 0}
            for item_id, quantity in rows:
                quantity = max(0, int(quantity or 0))
                if quantity <= 0:
                    continue
                if item_id in FISH_STORAGE_IDS:
                    totals["net"] += quantity
                elif item_id in MINING_STORAGE_IDS:
                    totals["bag"] += quantity
                elif item_id in WOOD_STORAGE_IDS:
                    totals["woodpile"] += quantity
                elif item_id in HERB_STORAGE_IDS:
                    totals["herbbag"] += quantity
            return totals

    async def announce_profession_sale_xp(self, container, units):
            for message in self.grant_profession_sale_xp(container, units):
                await self.send(message)

    async def announce_profession_sale_xp_for_rows(self, rows):
            for container, units in self.profession_sale_units_for_rows(rows).items():
                if units > 0:
                    await self.announce_profession_sale_xp(container, units)

    def bulk_sell_rewards_for_rows(self, rows):
            total_silver = 0
            total_gold = 0
            total_mithril = 0
            total_units = 0
            total_types = 0

            for item_id, quantity in rows:
                item = ITEMS.get(item_id, {})
                quantity = max(0, int(quantity))
                if quantity <= 0:
                    continue

                values = self.generic_item_sale_value(item_id, item)
                silver = int(values["silver"])
                gold = int(values["gold"])
                mithril = int(values["mithril"])
                if not (silver or gold or mithril):
                    continue

                total_units += quantity
                total_types += 1
                total_silver += silver * quantity
                total_gold += gold * quantity
                total_mithril += mithril * quantity

            return {
                "units": total_units,
                "types": total_types,
                "silver": total_silver,
                "gold": total_gold,
                "mithril": total_mithril,
            }

    def sale_reward_text(self, rewards):
            return currency_reading_text(
                rewards["silver"], rewards["gold"], rewards["mithril"]
            )

    async def gain_charisma_from_bulk_sale(self, rewards):
            units = max(0, int(rewards.get("units", 0) or 0))
            if units <= 0:
                return
            sale_value = legacy_currency_to_coins(
                rewards.get("silver", 0), rewards.get("gold", 0), rewards.get("mithril", 0)
            )
            await self.gain_charisma_from_sale(sale_value, units=units)

    def normalize_bulk_sell_target(self, query):
            q = normalize_lookup_text(query)
            direct = {
                "wszystko siatka": "net",
                "wszystko ryby": "net",
                "wszystkie ryby": "net",
                "cala siatka": "net",
                "cale ryby": "net",

                "wszystko sakwa": "bag",
                "wszystko rudy": "bag",
                "wszystkie rudy": "bag",
                "cala sakwa": "bag",

                "wszystko stos": "woodpile",
                "wszystko drewno": "woodpile",
                "cale drewno": "woodpile",
                "caly stos": "woodpile",

                "wszystko torba": "herbbag",
                "wszystko ziola": "herbbag",
                "wszystkie ziola": "herbbag",
                "cala torba": "herbbag",

                "wszystko przedmioty": "inventory",
                "wszystkie przedmioty": "inventory",
                "wszystko": "inventory",
                "all": "inventory",
                "all items": "inventory",
                "everything": "inventory",

                "ryby siatka": "net",
                "ryba siatka": "net",
                "fish net": "net",
                "net": "net",
                "siatka": "net",
                "ryby": "net",

                "rudy sakwa": "bag",
                "ruda sakwa": "bag",
                "ore bag": "bag",
                "ores bag": "bag",
                "bag": "bag",
                "sakwa": "bag",
                "rudy": "bag",

                "drewno stos": "woodpile",
                "wood pile": "woodpile",
                "woodpile": "woodpile",
                "stos": "woodpile",
                "drewno": "woodpile",

                "ziola torba": "herbbag",
                "ziola herbs": "herbbag",
                "herbs bag": "herbbag",
                "herbbag": "herbbag",
                "ziola": "herbbag",
                "herbs": "herbbag",
                "torba zielarska": "herbbag",

                "przedmioty": "inventory",
                "items": "inventory",
                "inventory": "inventory",
                "ekwipunek": "inventory",
            }
            return direct.get(q)

    async def bulk_sell_container(self, container):
            definition = self.profession_storage_definition(container)
            if not definition:
                await self.send("Nieznany magazyn profesji.")
                return False

            rows_db = self.server.db.storage_rows(
                self.account_id, container
            )
            if not rows_db:
                await self.send(
                    f"{self.container_label(container)} jest pusty."
                )
                return False

            sell_rows = []
            for row in rows_db:
                item_id = row["item_id"]
                qty = int(row["quantity"])
                item = ITEMS.get(item_id, {})
                if (
                    item_id in definition["ids"]
                    and qty > 0
                    and self.resource_sale_allowed_here(item_id)
                    and (
                        item.get("sell_silver", 0)
                        or item.get("sell_gold", 0)
                        or item.get("sell_mithril", 0)
                    )
                ):
                    sell_rows.append((item_id, qty))

            if not sell_rows:
                await self.send(
                    f"Nie możesz sprzedać zawartości "
                    f"{self.container_label(container)} tutaj. "
                    f"Sprzedaż: "
                    f"{self.resource_sale_location_text(container)}."
                )
                return False

            rewards = self.bulk_sell_rewards_for_rows(sell_rows)

            for item_id, qty in sell_rows:
                if not self.server.db.remove_storage_item(
                    self.account_id, container, item_id, qty
                ):
                    raise RuntimeError(
                        f"Nie udało się sprzedać {item_id} x{qty}."
                    )

            self.character.silver += rewards["silver"]
            self.character.gold += rewards["gold"]
            self.character.mithril += rewards["mithril"]

            await self.gain_charisma_from_bulk_sale(rewards)
            await self.announce_profession_sale_xp(container, rewards["units"])
            self.server.db.save_character(self.character)

            await self.send(
                f"Sprzedajesz {self.resource_sale_buyer_text(container)} cały magazyn: "
                f"{self.container_label(container)}. "
                f"Sztuk: {rewards['units']}. "
                f"Rodzajów: {rewards['types']}."
            )
            await self.send(
                f"Zarobek: {self.sale_reward_text(rewards)}."
            )
            return True

    async def bulk_sell_inventory_items(self):
            rows = self.server.db.inventory(self.account_id)
            equipped_counts = {}
            for equipped in self.server.db.equipment(self.account_id):
                item_id = equipped["item_id"]
                equipped_counts[item_id] = equipped_counts.get(item_id, 0) + 1

            sell_rows = []
            skipped = 0

            for row in rows:
                item_id = row["item_id"]
                qty = int(row["quantity"])
                item = ITEMS.get(item_id, {})
                equipped_count = min(qty, int(equipped_counts.get(item_id, 0)))
                sellable_qty = max(0, qty - equipped_count)

                if sellable_qty <= 0:
                    skipped += qty
                    continue

                if equipped_count:
                    skipped += equipped_count

                # v0.30.20: sell all jest celowo BEZPIECZNE. Hurtowo sprzedaje
                # wyłącznie niezałożone EQ. Mikstury, consumables, loot, materiały,
                # quest itemy, narzędzia i wszystkie inne typy pozostają nietknięte.
                if item.get("type") != "armor":
                    skipped += qty
                    continue
                if is_character_bound_item(item_id):
                    skipped += qty
                    continue
                if not self.generic_item_sale_allowed_here():
                    skipped += qty
                    continue
                if not self.generic_item_is_sellable(item_id, item):
                    skipped += qty
                    continue
                sell_rows.append((item_id, sellable_qty))

            if not sell_rows:
                await self.send(
                    "Nie masz tutaj niezałożonego EQ do sprzedaży. "
                    "Sell all nigdy nie sprzedaje mikstur, materiałów, lootu, narzędzi ani quest itemów."
                )
                return False

            rewards = self.bulk_sell_rewards_for_rows(sell_rows)

            for item_id, qty in sell_rows:
                if not self.server.db.remove_item(
                    self.account_id, item_id, qty
                ):
                    raise RuntimeError(
                        f"Nie udało się sprzedać {item_id} x{qty}."
                    )

            self.character.silver += rewards["silver"]
            self.character.gold += rewards["gold"]
            self.character.mithril += rewards["mithril"]

            await self.gain_charisma_from_bulk_sale(rewards)
            await self.announce_profession_sale_xp_for_rows(sell_rows)
            self.server.db.save_character(self.character)

            await self.send(
                f"Sprzedajesz sprzedawcy {self.generic_item_sale_buyer_name()} "
                f"niezałożone EQ z inventory. "
                f"Sztuk: {rewards['units']}. "
                f"Rodzajów: {rewards['types']}."
            )
            await self.send(
                f"Zarobek: {self.sale_reward_text(rewards)}."
            )
            if skipped:
                await self.send(
                    f"Pominięto {skipped} sztuk: sell all chroni wszystko poza niezałożonym EQ "
                    f"oraz nigdy nie sprzedaje aktualnie założonych części."
                )
            return True

    def logical_sell_equipment_slot(self, slot):
            slot = str(slot or "").strip().lower()
            if slot in ("ring1", "ring2"):
                return "ring"
            if slot in ("charm1", "charm2"):
                return "charm"
            return slot

    def sell_slot_from_query(self, query):
            q = normalize_lookup_text(query)
            if not q:
                return None
            for alias, slot in EQUIPMENT_SLOT_ALIASES.items():
                if normalize_lookup_text(alias) == q:
                    return self.logical_sell_equipment_slot(slot)
            return None

    def owned_single_sale_candidates(self, query):
            """v0.23: rozwiązuje sprzedaż WYŁĄCZNIE wśród faktycznie posiadanych,
            wolnych i sprzedawalnych przedmiotów. Dzięki temu `sprzedaj helm` nie
            przeszukuje 26 tysięcy globalnych definicji EQ i nie wybiera losowo.
            """
            q = normalize_lookup_text(query)
            if not q:
                return []
            requested_slot = self.sell_slot_from_query(query)
            rows = []
            for row in self.server.db.inventory(self.account_id):
                item_id = row["item_id"]
                item = ITEMS.get(item_id)
                if not item or not self.generic_item_is_sellable(item_id, item):
                    continue
                free_qty = max(
                    0, int(row["quantity"]) - self.equipped_quantity_of_item(item_id)
                )
                if free_qty <= 0:
                    continue
                if requested_slot:
                    if item.get("type") != "armor":
                        continue
                    if self.logical_sell_equipment_slot(item.get("slot")) != requested_slot:
                        continue
                    rows.append((item_id, item, free_qty))
                    continue
                item_name = normalize_lookup_text(item.get("name", ""))
                item_key = normalize_lookup_text(item_id)
                if q == item_name or q == item_key or q in item_name or q in item_key:
                    rows.append((item_id, item, free_qty))
            return rows

    async def ask_single_sale_choice(self, query, candidates):
            self.sell_choice_state = {
                "room_id": self.character.room_id,
                "query": str(query or "").strip(),
                "item_ids": [item_id for item_id, _item, _qty in candidates],
            }
            await self.send(
                f"Pasuje kilka twoich wolnych przedmiotów: {len(candidates)}. "
                "Wybierz numer komendą sprzedaj <numer>."
            )
            for number, (item_id, item, free_qty) in enumerate(candidates, 1):
                values = self.generic_item_sale_value(item_id, item)
                await self.send(
                    f"{number}. {item['name']}. Wolne sztuki: {free_qty}. "
                    f"Cena jednej: {currency_reading_text(values['silver'], values['gold'], values['mithril'])}."
                )

    async def sell_command(self, query):
            raw_query = str(query or "").strip()
            # Numer po liście niejednoznacznych przedmiotów oznacza wybór z tej
            # listy, a nie nazwę globalnego itemu. Lista działa tylko w tym samym sklepie.
            if raw_query.isdigit() and self.sell_choice_state:
                state = self.sell_choice_state
                if state.get("room_id") != self.character.room_id:
                    self.sell_choice_state = None
                    await self.send("Poprzednia lista sprzedaży wygasła. Wskaż przedmiot ponownie.")
                    return
                index = int(raw_query) - 1
                item_ids = list(state.get("item_ids") or ())
                if index < 0 or index >= len(item_ids):
                    await self.send(
                        f"Nie ma pozycji {raw_query}. Wybierz numer od 1 do {len(item_ids)}."
                    )
                    return
                item_id = item_ids[index]
                self.sell_choice_state = None
                await self.sell_resource(item_id)
                return

            if not raw_query.isdigit():
                self.sell_choice_state = None

            target = self.normalize_bulk_sell_target(query)

            if target == "inventory":
                await self.bulk_sell_inventory_items()
                return

            if target in {"net", "bag", "woodpile", "herbbag"}:
                await self.bulk_sell_container(target)
                return

            await self.sell_resource(query)

    def parse_numbered_inventory_query(self, query):
            raw = str(query or "").strip()
            match = re.match(r"^\s*(\d+)\s*[\.\)]\s*(.+?)\s*$", raw)
            if not match:
                return None, raw
            return max(1, int(match.group(1))), match.group(2).strip()

    async def sell_resource(self, query):
            copy_number, item_query = self.parse_numbered_inventory_query(query)

            # v0.23: dla zwykłej sprzedaży najpierw patrzymy na RZECZY GRACZA,
            # nie na cały katalog ITEMS. Obsługuje to m.in. `sprzedaj helm` i
            # fragment nazwy. Przy wielu trafieniach zawsze jest jawny wybór.
            found = None
            if copy_number is None:
                owned_candidates = self.owned_single_sale_candidates(item_query)
                if len(owned_candidates) == 1:
                    item_id, item, _free_qty = owned_candidates[0]
                    found = (item_id, item)
                elif len(owned_candidates) > 1:
                    await self.ask_single_sale_choice(item_query, owned_candidates)
                    return

            if not found:
                found = find_by_name(ITEMS, item_query)
            if not found:
                await self.send(
                    "Nie rozpoznaję takiego przedmiotu albo pasuje kilka pozycji. "
                    "Dla EQ możesz użyć typu, np. sprzedaj helm."
                )
                return
            item_id, item = found

            if self.market_buyer_rejects_item(item_id, item):
                await self.send(
                    "Handlarz Skupu Radan nie skupuje materiałów rzemieślniczych ani zasobów profesyjnych. "
                    "Ryby, rudy i minerały, drewno oraz zioła sprzedawaj u właściwych fachowców."
                )
                return

            # v0.8.51: zwykłe przedmioty (np. talizmany, pierścienie, pancerze)
            # można sprzedać w dowolnym normalnym sklepie.
            if item.get("type") != "resource" and item_id not in MINING_STORAGE_IDS:
                if not self.generic_item_is_sellable(item_id, item):
                    await self.send("Tego przedmiotu nie można sprzedać.")
                    return
                if not self.generic_item_sale_allowed_here():
                    await self.send(
                        "Zwykłe przedmioty sprzedasz w lokacji z normalnym sklepem. "
                        "Przejdź do sklepu i użyj: sprzedaj <nazwa przedmiotu>."
                    )
                    return
                owned_qty = self.server.db.item_qty(self.account_id, item_id)
                if owned_qty <= 0:
                    await self.send("Nie masz tego przedmiotu.")
                    return
                equipped_count = sum(
                    1 for row in self.server.db.equipment(self.account_id)
                    if row["item_id"] == item_id
                )
                if copy_number is not None:
                    if copy_number > owned_qty:
                        await self.send(
                            f"Masz tylko {owned_qty} sztuk: {item['name']}."
                        )
                        return
                    if copy_number <= equipped_count:
                        await self.send(
                            f"Egzemplarz {copy_number}: {item['name']} jest założony. "
                            f"Sprzedaj egzemplarz od {equipped_count + 1} wzwyż albo zdejmij talizman/EQ."
                        )
                        return
                elif owned_qty <= equipped_count:
                    await self.send(
                        f"Wszystkie posiadane sztuki {item['name']} są założone. "
                        "Najpierw zdejmij jedną albo wskaż wolny egzemplarz numerem."
                    )
                    return
                values = self.generic_item_sale_value(item_id, item)
                if not self.server.db.remove_item(self.account_id, item_id, 1):
                    await self.send("Nie udało się sprzedać przedmiotu.")
                    return
                self.character.silver += values["silver"]
                self.character.gold += values["gold"]
                self.character.mithril += values["mithril"]
                await self.gain_charisma_from_sale(legacy_currency_to_coins(values["silver"], values["gold"], values["mithril"]))
                self.server.db.save_character(self.character)
                copy_text = f" egzemplarz {copy_number}" if copy_number is not None else ""
                await self.send(
                    f"Sprzedajesz sprzedawcy {self.generic_item_sale_buyer_name()}{copy_text}: "
                    f"{item['name']} za "
                    f"{currency_reading_text(values['silver'], values['gold'], values['mithril'])}."
                )
                return

            fish_items = FISH_STORAGE_IDS
            ore_items = MINING_STORAGE_IDS
            wood_items = WOOD_STORAGE_IDS
            herb_items = HERB_STORAGE_IDS

            if item_id in fish_items:
                source_container = "net"
            elif item_id in ore_items:
                source_container = "bag"
            elif item_id in wood_items:
                source_container = "woodpile"
            elif item_id in herb_items:
                source_container = "herbbag"
            else:
                source_container = None

            storage_quantity = (
                self.server.db.storage_qty(self.account_id, source_container, item_id)
                if source_container else 0
            )
            inventory_quantity = self.server.db.item_qty(self.account_id, item_id)
            if storage_quantity <= 0 and inventory_quantity <= 0:
                await self.send("Nie masz tego przedmiotu.")
                return

            if item_id in fish_items and self.character.room_id != "fish_market":
                await self.send("Ryby skupują tylko rybacy na Targu Rybnym.")
                return
            if item_id in ore_items and self.character.room_id != "mountain_market":
                await self.send("Rudy, minerały i surowe klejnoty skupuje tylko Handlarka Minerałów Dagna na Górskim Targu Minerałów.")
                return
            if item_id in wood_items and self.character.room_id != "lumberjack_camp":
                await self.send("Drewno skupuje tylko Drwal Bran w Obozie Drwala.")
                return
            if item_id in herb_items and self.character.room_id != "herbalist_hut":
                await self.send("Zioła skupuje tylko Zielarka Liora w Chacie Zielarki.")
                return

            removed = False
            if source_container and self.server.db.storage_qty(
                self.account_id, source_container, item_id
            ) > 0:
                removed = self.server.db.remove_storage_item(
                    self.account_id, source_container, item_id, 1
                )
            elif self.server.db.item_qty(self.account_id, item_id) > 0:
                removed = self.server.db.remove_item(
                    self.account_id, item_id, 1
                )

            if not removed:
                await self.send("Nie masz tego surowca.")
                return

            # v0.19: sprzedaż zasobów skaluje się razem z globalną ekonomią.
            reward_coins = v0190_resource_sale_coins(item_id, item)
            self.character.silver += reward_coins
            await self.gain_charisma_from_sale(reward_coins)
            await self.announce_profession_sale_xp(source_container, 1)
            self.server.db.save_character(self.character)

            buyer = self.resource_sale_buyer_text(source_container)
            await self.send(
                f"Sprzedajesz {buyer}: {item['name']} za "
                + currency_reading_text(reward_coins, 0, 0) + "."
            )

    def recipe_container_for_item(self, item_id):
            if item_id in FISH_STORAGE_IDS:
                return "net"
            if item_id in MINING_STORAGE_IDS:
                return "bag"
            if item_id in WOOD_STORAGE_IDS:
                return "woodpile"
            if item_id in HERB_STORAGE_IDS:
                return "herbbag"
            if item_id in CRAFT_MATERIAL_STORAGE_IDS:
                return "craftbox"
            return None
