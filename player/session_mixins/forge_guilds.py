# -*- coding: utf-8 -*-
"""Soulbound v0.30.47 Session mixin: forge_guilds."""

class SessionForgeGuildsMixin:
    def at_haldor_forge_v0925(self):
            room_id=str(self.character.room_id or "")
            if room_id in ("forge", "crafting_workshop"):
                return True
            match=re.fullmatch(r"player_guild_estate_(\d+)_forge",room_id)
            if not match:
                return False
            row=self.guild_row_v0926()
            if not row or int(row["clan_id"])!=int(match.group(1)):
                return False
            hall=self.server.db.guild_hall_v0927(int(row["clan_id"]))
            return int(hall["forge_level"] or 0)>=1

    def resolve_owned_equipment_v0925(self, query, free_only=False):
            pool={}
            for item_id,item in ITEMS.items():
                if item.get("type") != "armor":
                    continue
                qty=self.server.db.item_qty(self.account_id,item_id)
                if qty <= 0: continue
                if free_only and self.free_equipment_quantity(item_id) <= 0: continue
                pool[item_id]=item
            return find_by_name(pool, query)

    async def salvage_equipment_v0925(self, args=""):
            """v0.30.41: rozkładanie każdego niezałożonego armor EQ.

            Obsługuje materiałowe, klasowe, bossowe, setowe, crafted, Kryptę,
            Astral i pozostałe linie armor. Broń Duszy nie jest itemem inventory.
            """
            if not self.at_haldor_forge_v0925():
                await self.send("EQ rozkłada Haldor w Kuźni/Warsztacie Rzemieślniczym.")
                return

            raw = str(args or "").strip()
            norm = normalize_lookup_text(raw)
            free_rows = []
            for item_id, item in ITEMS.items():
                if item.get("type") != "armor":
                    continue
                free_qty = int(self.free_equipment_quantity(item_id) or 0)
                if free_qty <= 0:
                    continue
                free_rows.append((item_id, item, free_qty))
            free_rows.sort(key=lambda row: normalize_lookup_text(row[1].get("name", row[0])))

            if not raw or norm in ("lista", "list", "info"):
                if not free_rows:
                    await self.send("Nie masz niezałożonego EQ do rozłożenia.")
                    return
                await self.send(f"ROZKŁADANIE EQ. Dostępne pozycje: {len(free_rows)}. Wybierz numer albo pełną nazwę.")
                for index, (item_id, item, free_qty) in enumerate(free_rows, 1):
                    material = v03041_salvage_material_key(item)
                    salvage_id = V0925_SALVAGE_MATERIALS[material][0]
                    level = max(1, min(400, int(item.get("required_character_level", item.get("required_mastery", 1)) or 1)))
                    await self.send(
                        f"{index}. {item.get('name', item_id)}. Wolne {free_qty}. "
                        f"Level {level}. Odzysk: {ITEMS[salvage_id]['name']}."
                    )
                return

            found = None
            if raw.isdigit():
                index = int(raw)
                if 1 <= index <= len(free_rows):
                    item_id, item, _free_qty = free_rows[index - 1]
                    found = (item_id, item)
            else:
                found = self.resolve_owned_equipment_v0925(raw, free_only=True)

            if not found:
                await self.send(
                    "Nie rozpoznaję wolnego EQ. Wpisz rozloz, aby dostać numerowaną listę. "
                    "Założonej sztuki nie można rozłożyć."
                )
                return

            item_id, item = found
            if self.free_equipment_quantity(item_id) <= 0:
                await self.send("Ta sztuka jest aktualnie założona. Najpierw ją zdejmij albo rozłóż inną wolną kopię.")
                return

            material = v03041_salvage_material_key(item)
            salvage_id = V0925_SALVAGE_MATERIALS[material][0]
            level = max(1, min(400, int(
                item.get("required_character_level", item.get("required_mastery", 1)) or 1
            )))
            rarity = str(item.get("rarity", "common") or "common").lower()
            rarity_bonus = {
                "uncommon": 0, "rare": 1, "epic": 1, "legendary": 2,
                "mythic": 3, "unique": 3, "eternal": 4, "crafted": 0,
            }.get(rarity, 0)
            qty = max(1, 1 + level // 100 + rarity_bonus)

            # Modyfikacje są przypięte do item_id. Zwracamy je dopiero wtedy,
            # gdy rozkładana jest ostatnia posiadana kopia tego konkretnego ID.
            total_before = int(self.server.db.item_qty(self.account_id, item_id) or 0)
            last_copy = total_before <= 1
            rune_rows = list(self.server.db.equipment_runes_v0925(self.account_id, item_id)) if last_copy else []
            reforged = self.server.db.equipment_reforge(self.account_id, item_id) if last_copy else None

            if not self.server.db.remove_item(self.account_id, item_id, 1):
                await self.send("Nie udało się rozłożyć przedmiotu.")
                return

            self.server.db.add_storage_item(self.account_id, "craftbox", salvage_id, qty)
            essence = 1 if level >= 100 else 0
            dust = 1 if level >= 200 else 0
            if rarity in ("legendary", "mythic", "unique", "eternal"):
                essence += 1
            if level >= 300:
                dust += 1
            if reforged:
                essence += 1
            if essence:
                self.server.db.add_storage_item(self.account_id, "craftbox", "reforge_essence", essence)
            if dust:
                self.server.db.add_storage_item(self.account_id, "craftbox", "rune_dust", dust)

            returned_runes = []
            if last_copy:
                for row in rune_rows:
                    rune_id = str(row["rune_id"])
                    if rune_id in ITEMS:
                        self.server.db.add_storage_item(self.account_id, "craftbox", rune_id, 1)
                        returned_runes.append(rune_id)
                self.server.db.clear_equipment_crafting_v0925(self.account_id, item_id)

            clan = self.server.db.clan_membership(self.account_id)
            if clan:
                self.server.db.clan_metric_add(int(clan["clan_id"]), "salvage", 1)
                self.server.db.clan_log(
                    int(clan["clan_id"]), self.account_id,
                    f"{self.character.name} rozłożył EQ: {item.get('name', item_id)}."
                )

            extras = []
            if essence:
                extras.append(f"Esencja Przekucia x{essence}")
            if dust:
                extras.append(f"Pył Runiczny x{dust}")
            if returned_runes:
                extras.append(
                    "zwrócone runy: " + ", ".join(ITEMS[r]["name"] for r in returned_runes)
                )
            extra_text = (", " + ", ".join(extras)) if extras else ""
            await self.send(
                f"Haldor rozkłada: {item['name']}. Otrzymujesz "
                f"{ITEMS[salvage_id]['name']} x{qty}{extra_text}. "
                "Wszystko trafia do odpowiednich kategorii Szkatułki."
            )

    def owned_equipment_upgrade_rows_v03042(self):
            rows = []
            for item_id, item in ITEMS.items():
                if item.get("type") != "armor":
                    continue
                qty = int(self.server.db.item_qty(self.account_id, item_id) or 0)
                if qty <= 0:
                    continue
                upgrade = self.server.db.equipment_upgrade_level_v03042(self.account_id, item_id)
                rows.append((item_id, item, qty, upgrade))
            rows.sort(key=lambda row: (row[3] >= V03042_EQ_UPGRADE_MAX, -v03042_equipment_level(row[1]), normalize_lookup_text(row[1].get("name", row[0]))))
            return rows

    async def upgrade_equipment_v03042(self, args=""):
            if not self.at_haldor_forge_v0925():
                await self.send("EQ ulepsza Haldor w Kuźni/Warsztacie Rzemieślniczym.")
                return
            if self.combat_mob_key:
                await self.send("Nie możesz ulepszać EQ podczas aktywnej walki.")
                return
            if self.server.db.item_qty(self.account_id, "crafting_hammer") <= 0:
                await self.send("Do ulepszania EQ potrzebujesz Młota Rzemieślniczego.")
                return

            raw = str(args or "").strip()
            norm = normalize_lookup_text(raw)
            rows = self.owned_equipment_upgrade_rows_v03042()
            if not raw or norm in ("lista", "list", "info"):
                await self.send("ULEPSZANIE EQ U HALDORA. Wybierz numer albo wpisz: ulepsz <pełna nazwa EQ>.")
                if not rows:
                    await self.send("Nie masz żadnego EQ do ulepszenia.")
                    return
                for idx, (item_id, item, qty, current) in enumerate(rows, 1):
                    if current >= V03042_EQ_UPGRADE_MAX:
                        await self.send(f"{idx}. {item['name']}. +{current}/{V03042_EQ_UPGRADE_MAX}. MAKSIMUM. x{qty}.")
                        continue
                    target = current + 1
                    req = v03042_upgrade_required_smithing(item, target)
                    material = v03041_salvage_material_key(item)
                    salvage_id = V0925_SALVAGE_MATERIALS[material][0]
                    cost = v03042_upgrade_material_cost(item, target)
                    await self.send(
                        f"{idx}. {item['name']}. +{current} -> +{target}. "
                        f"Wymaga Kowalstwo {req} i Młot Tier {required_tool_tier_for_level(req)}. "
                        f"Koszt: {ITEMS[salvage_id]['name']} x{cost}. x{qty}."
                    )
                return

            if raw.isdigit():
                idx = int(raw)
                if not 1 <= idx <= len(rows):
                    await self.send(f"Nie ma pozycji {idx}. Zakres: 1-{len(rows)}.")
                    return
                item_id, item, _qty, current = rows[idx - 1]
            else:
                found = self.resolve_owned_equipment_v0925(raw, free_only=False)
                if not found:
                    await self.send("Nie rozpoznaję posiadanego EQ. Wpisz ulepsz lista.")
                    return
                item_id, item = found
                current = self.server.db.equipment_upgrade_level_v03042(self.account_id, item_id)

            if current >= V03042_EQ_UPGRADE_MAX:
                await self.send(f"{item['name']} ma już maksymalne ulepszenie +{V03042_EQ_UPGRADE_MAX}.")
                return
            target = current + 1
            required_smithing = v03042_upgrade_required_smithing(item, target)
            profession_row = self.server.db.profession(self.account_id, "Kowalstwo")
            smithing_level = int(profession_row["level"])
            if smithing_level < required_smithing:
                await self.send(
                    f"Ulepszenie {item['name']} do +{target} wymaga Kowalstwo level {required_smithing}. "
                    f"Masz {smithing_level}."
                )
                return
            tool_row = self.server.db.tool(self.account_id, "crafting")
            hammer_level = int(tool_row["level"])
            hammer_tier = tool_tier(hammer_level)
            required_tier = required_tool_tier_for_level(required_smithing)
            if hammer_tier < required_tier:
                await self.send(
                    f"Ulepszenie do +{target} wymaga Młota Rzemieślniczego Tier {required_tier}+, "
                    f"a masz Tier {hammer_tier}."
                )
                return

            material = v03041_salvage_material_key(item)
            salvage_id = V0925_SALVAGE_MATERIALS[material][0]
            cost = v03042_upgrade_material_cost(item, target)
            have = self.server.db.storage_qty(self.account_id, "craftbox", salvage_id)
            if have < cost:
                await self.send(
                    f"Brakuje materiału. Potrzeba {ITEMS[salvage_id]['name']} x{cost}; masz {have}. "
                    "Niepotrzebne EQ możesz rozłożyć u Haldora komendą rozloz."
                )
                return

            action_seconds = generator_core_v027.profession_action_seconds("crafting", smithing_level)
            await self.send(
                f"Haldor rozpoczyna ulepszanie: {item['name']} +{current} -> +{target}. "
                f"Czas pracy: {action_seconds} sekund. Nie ma ryzyka zniszczenia ani cofnięcia ulepszenia."
            )
            await asyncio.sleep(action_seconds)
            if not self.server.db.remove_storage_item(self.account_id, "craftbox", salvage_id, cost):
                await self.send("Nie udało się pobrać materiałów. Ulepszenie przerwane.")
                return

            self.server.db.set_equipment_upgrade_level_v03042(self.account_id, item_id, target)
            stat_name = v03042_upgrade_primary_stat(
                item,
                str((self.server.db.equipment_reforge(self.account_id, item_id) or {}).get("affix") or item.get("affix") or ""),
            )
            stat_bonus = v03042_upgrade_stat_bonus(target)
            defense_bonus = v03042_upgrade_defense_bonus(item, target)
            stat_label = CLASS_SET_STAT_NAMES.get(stat_name, stat_name)
            await self.send(
                f"Ulepszenie zakończone: {item['name']} ma teraz +{target}/{V03042_EQ_UPGRADE_MAX}. "
                f"Bonus z ulepszenia: obrona +{defense_bonus}"
                + (f", {stat_label} +{stat_bonus}." if stat_bonus > 0 else ".")
            )

            xp_stage = max(required_smithing, v03042_equipment_level(item))
            profession_xp = max(12, 12 + xp_stage // 8 + target * 3)
            tool_xp = max(10, 10 + xp_stage // 10 + target * 2)
            messages, _prof_after, _tool_after = self.grant_profession_progress(
                "Kowalstwo", profession_xp, "crafting", tool_xp
            )
            for message in messages:
                await self.send(message)
            self.current_hp = min(self.current_hp, self.max_hp())
            self.current_mana = min(self.current_mana, self.max_mana())

    async def reforge_equipment_v0925(self, args=""):
            if not self.at_haldor_forge_v0925():
                await self.send("Przekuwanie wykonuje Haldor w Kuźni/Warsztacie Rzemieślniczym.")
                return
            found=self.resolve_owned_equipment_v0925(args, free_only=False)
            if not found:
                await self.send("Podaj pełną nazwę posiadanego EQ do przekucia.")
                return
            item_id,item=found
            mastery=max(1,int(item.get("required_mastery",1) or 1))
            cost=max(1,1+mastery//100)
            have=self.server.db.storage_qty(self.account_id,"craftbox","reforge_essence")
            if have < cost:
                await self.send(f"Potrzeba {cost} Esencji Przekucia w Szkatułce. Masz {have}.")
                return
            base_affix=str(item.get("affix") or "constitution")
            old=self.server.db.equipment_reforge(self.account_id,item_id)
            current=str(old["affix"]) if old else base_affix
            choices=[a for a in V0925_REFORGE_AFFIXES if a != current]
            seed=(self.account_id * 131 + sum(ord(c) for c in item_id) + (int(old["rerolls"]) if old else 0))
            new_affix=choices[seed % len(choices)]
            amount=max(1,int(item.get("affix_amount",0) or 0))
            if new_affix in ("hp","mana") and amount < 10: amount *= 10
            if current in ("hp","mana") and new_affix not in ("hp","mana"): amount=max(1,amount//10)
            if not self.server.db.remove_storage_item(self.account_id,"craftbox","reforge_essence",cost):
                await self.send("Nie udało się pobrać materiałów.")
                return
            self.server.db.save_equipment_reforge(self.account_id,item_id,new_affix,amount)
            clan=self.server.db.clan_membership(self.account_id)
            if clan:
                self.server.db.clan_metric_add(int(clan["clan_id"]),"reforge",1)
                self.server.db.clan_log(int(clan["clan_id"]),self.account_id,f"{self.character.name} przekuł EQ: {item.get('name',item_id)}.")
            await self.send(f"Przekucie zakończone: {item['name']}. Nowy bonus: {V0925_AFFIX_PL.get(new_affix,new_affix)} +{amount}. Wymóg Biegłości pozostaje {mastery}.")

    async def handle_runes_v0925(self, args=""):
            raw=str(args or "").strip(); norm=normalize_lookup_text(raw)
            if not raw or norm in ("lista","list","info"):
                await self.send("RUNY. Endgame EQ: Biegłość 200-299 ma 1 gniazdo, 300-399 ma 2, 400 ma 3. Tworzenie u Haldora: runy stworz <moc/ochrona/zycie/mana/unik/hart>. Osadzanie: runa <typ> <pełna nazwa EQ>. Wyjmowanie: runy wyjmij <nr> <pełna nazwa EQ>.")
                for key,(rid,name,effects) in V0925_RUNES.items():
                    await self.send(f"{key}: {name}. Koszt 5 Pyłu Runicznego. Efekt {effects}.")
                return
            parts=raw.split(maxsplit=2)
            action=normalize_lookup_text(parts[0])
            if action in ("stworz","stwórz","craft","wykuj"):
                if len(parts)<2:
                    await self.send("Użycie: runy stworz <typ>."); return
                if not self.at_haldor_forge_v0925():
                    await self.send("Runy wykuwa Haldor w Kuźni/Warsztacie Rzemieślniczym."); return
                key=normalize_lookup_text(parts[1]).replace("życie","zycie")
                aliases={"power":"moc","guard":"ochrona","life":"zycie","focus":"mana","agility":"unik","fortitude":"hart"}
                key=aliases.get(key,key)
                if key not in V0925_RUNES:
                    await self.send("Nieznany typ runy."); return
                if self.server.db.storage_qty(self.account_id,"craftbox","rune_dust") < 5:
                    await self.send("Potrzeba 5 Pyłu Runicznego w kategorii Runy Szkatułki."); return
                self.server.db.remove_storage_item(self.account_id,"craftbox","rune_dust",5)
                rid=V0925_RUNES[key][0]
                self.server.db.add_storage_item(self.account_id,"craftbox",rid,1)
                await self.send(f"Haldor wykuwa: {ITEMS[rid]['name']}. Runa trafia do Szkatułka -> Runy.")
                return
            if action in ("wyjmij","remove"):
                if len(parts)<3 or not parts[1].isdigit():
                    await self.send("Użycie: runy wyjmij <numer gniazda> <pełna nazwa EQ>."); return
                idx=int(parts[1]); found=self.resolve_owned_equipment_v0925(parts[2],False)
                if not found: await self.send("Nie rozpoznaję posiadanego EQ."); return
                rid=self.server.db.remove_equipment_rune_v0925(self.account_id,found[0],idx)
                if not rid: await self.send("To gniazdo jest puste."); return
                self.server.db.add_storage_item(self.account_id,"craftbox",rid,1)
                await self.send(f"Wyjmujesz {ITEMS.get(rid,{}).get('name',rid)} z gniazda {idx}. Runa wraca do Szkatułki.")
                return
            await self.send("Użyj: runy, runy stworz <typ> albo runy wyjmij <nr> <EQ>.")

    async def socket_rune_v0925(self, args=""):
            parts=str(args or "").strip().split(maxsplit=1)
            if len(parts)<2:
                await self.send("Użycie: runa <moc/ochrona/zycie/mana/unik/hart> <pełna nazwa EQ>."); return
            key=normalize_lookup_text(parts[0]).replace("życie","zycie")
            aliases={"power":"moc","guard":"ochrona","life":"zycie","focus":"mana","agility":"unik","fortitude":"hart"}
            key=aliases.get(key,key)
            if key not in V0925_RUNES:
                await self.send("Nieznany typ runy."); return
            found=self.resolve_owned_equipment_v0925(parts[1],False)
            if not found:
                await self.send("Nie rozpoznaję posiadanego EQ."); return
            item_id,item=found; sockets=v0925_equipment_socket_count(item)
            if sockets <= 0:
                await self.send("Gniazda runiczne ma endgame EQ wymagające co najmniej Biegłości 200."); return
            existing=list(self.server.db.equipment_runes_v0925(self.account_id,item_id))
            if len(existing) >= sockets:
                await self.send(f"Wszystkie {sockets} gniazda tego EQ są zajęte. Najpierw wyjmij runę."); return
            rid=V0925_RUNES[key][0]
            if self.server.db.storage_qty(self.account_id,"craftbox",rid) <= 0:
                await self.send(f"Nie masz w Szkatułce: {ITEMS[rid]['name']}. Najpierw wykuj runę."); return
            used={int(r["socket_index"]) for r in existing}; idx=next(i for i in range(1,sockets+1) if i not in used)
            self.server.db.remove_storage_item(self.account_id,"craftbox",rid,1)
            self.server.db.add_equipment_rune_v0925(self.account_id,item_id,idx,rid)
            await self.send(f"Osadzasz {ITEMS[rid]['name']} w gnieździe {idx}/{sockets}: {item['name']}. Wymóg Biegłości nie zmienia się.")

    async def show_mastery_achievements_v0925(self):
            await self.sync_mastery_achievements_v0925()
            await self.send("OSIĄGNIĘCIA KLASOWE I PROFESYJNE 1-400")
            for cname,*_ in CLASSES:
                lvl=self.class_mastery_level(cname)
                done=sum(1 for t in V0925_MASTERY_MILESTONES if lvl>=t)
                await self.send(f"Klasa {cname}: Biegłość {lvl}/400, kamienie milowe {done}/{len(V0925_MASTERY_MILESTONES)}.")
            for prof in dict.fromkeys(TOOL_PROFESSION_MAP.values()):
                lvl=int(self.server.db.profession(self.account_id,prof)["level"])
                done=sum(1 for t in V0925_MASTERY_MILESTONES if lvl>=t)
                await self.send(f"Profesja {prof}: {lvl}/400, kamienie milowe {done}/{len(V0925_MASTERY_MILESTONES)}.")
            await self.send("Dodatkowe osiągnięcia łączą mastery z bossami, craftingiem, kolekcją i eksploracją i pojawiają się w zwykłej komendzie osiągnięcia.")

    async def sync_mastery_achievements_v0925(self):
            boss_kills=self.server.db.achievement_metric(self.account_id,"boss_kills")
            explored=self.server.db.achievement_metric(self.account_id,"exploration_rooms")
            eq_collection=len(self.server.db.collection_entry_ids(self.account_id,"equipment"))
            _active_mastery_classes=set(self.active_class_names())
            _active_mastery_classes.update(str(r["class_name"]) for r in self.server.db.conn.execute("SELECT class_name FROM class_progress WHERE account_id=?",(self.account_id,)).fetchall())
            for cname,*_ in CLASSES:
                if cname not in _active_mastery_classes:
                    continue
                level=self.class_mastery_level(cname); slug=_collection_slug(cname)
                for threshold in V0925_MASTERY_MILESTONES:
                    if level>=threshold:
                        self.server.db.unlock_achievement(self.account_id,f"class_{slug}_{threshold}",f"{cname}: Biegłość {threshold}","Class Mastery")
                if level>=200 and boss_kills>=25:
                    self.server.db.unlock_achievement(self.account_id,f"class_{slug}_boss",f"{cname}: Pogromca Bossów","Class Challenge")
                if level>=300 and explored>=300:
                    self.server.db.unlock_achievement(self.account_id,f"class_{slug}_explore",f"{cname}: Wędrowiec Endgame","Class Challenge")
                if level>=400 and eq_collection>=500:
                    self.server.db.unlock_achievement(self.account_id,f"class_{slug}_collector",f"{cname}: Kolekcjoner Mistrzowski","Class Challenge")
            for prof in dict.fromkeys(TOOL_PROFESSION_MAP.values()):
                row=self.server.db.profession(self.account_id,prof); level=int(row["level"]); actions=int(row["actions"]); slug=_collection_slug(prof)
                for threshold in V0925_MASTERY_MILESTONES:
                    if level>=threshold:
                        self.server.db.unlock_achievement(self.account_id,f"prof_{slug}_{threshold}",f"{prof}: poziom {threshold}","Profession Mastery")
                if level>=200 and actions>=1000:
                    self.server.db.unlock_achievement(self.account_id,f"prof_{slug}_1000",f"{prof}: Tysiąc Prac","Profession Challenge")
                if level>=400 and actions>=5000:
                    self.server.db.unlock_achievement(self.account_id,f"prof_{slug}_5000",f"{prof}: Arcydzieło 400","Profession Challenge")

    def guild_row_v0926(self):
            return self.server.db.clan_membership(self.account_id)

    def clan_row_v0925(self):
            return self.guild_row_v0926()

    def clan_session_by_account_v0925(self, account_id):
            for sess in list(self.server.sessions):
                if getattr(sess,"account_id",None)==account_id and not sess.closed:
                    return sess
            return None

    def refresh_guild_bonus_v0926(self):
            pct=self.server.db.guild_bonus_percent_v0926(self.account_id) if getattr(self,"account_id",None) else 0
            if getattr(self,"character",None):
                self.character._guild_bonus_percent=int(pct)
            return int(pct)

    def guild_bonus_percent_v0926(self):
            return self.refresh_guild_bonus_v0926()

    def guild_role_v0926(self, membership=None):
            row=membership or self.guild_row_v0926()
            if not row:
                return None
            return self.server.db.guild_role_v0926(int(row["clan_id"]),str(row["rank"]))

    def guild_has_permission_v0926(self, permission, membership=None):
            row=membership or self.guild_row_v0926()
            if not row:
                return False
            if str(row["rank"])=="leader":
                return True
            role=self.guild_role_v0926(row)
            return bool(role and int(role[permission] or 0))

    def guild_rank_name_v0926(self, membership=None):
            row=membership or self.guild_row_v0926()
            if not row:
                return "Brak"
            role=self.guild_role_v0926(row)
            return str(role["name"]) if role else str(row["rank"])

    def guild_rank_priority_v0926(self, membership=None):
            row=membership or self.guild_row_v0926()
            if not row:
                return 0
            role=self.guild_role_v0926(row)
            return int(role["priority"]) if role else 0

    def parse_guild_money_v0926(self, raw):
            parts=str(raw or "").strip().split()
            if not parts or not parts[0].isdigit():
                return None
            amount=int(parts[0])
            if amount<=0:
                return None
            currency=self.normalize_bank_currency(parts[1]) if len(parts)>1 else "silver"
            if not currency:
                return None
            return self.bank_amount_to_silver(amount,currency)

    def guild_role_key_v0926(self, name):
            key=_collection_slug(str(name or ""))
            key=re.sub(r"[^a-z0-9_]+","_",key).strip("_")
            return key[:40] or "ranga"

    async def sync_clan_achievements_v0925(self, clan_id):
            conn=self.server.db.conn
            members=int(conn.execute("SELECT COUNT(*) c FROM player_clan_members WHERE clan_id=?",(clan_id,)).fetchone()["c"])
            bank=int(conn.execute("SELECT COALESCE(SUM(quantity),0) c FROM player_clan_bank WHERE clan_id=?",(clan_id,)).fetchone()["c"])
            grow=conn.execute("SELECT level,treasury FROM player_clans WHERE id=?",(clan_id,)).fetchone()
            level=int(grow["level"] or 1) if grow else 1; treasury=int(grow["treasury"] or 0) if grow else 0
            metrics={str(r["metric"]):int(r["value"]) for r in conn.execute("SELECT metric,value FROM player_clan_metrics WHERE clan_id=?",(clan_id,)).fetchall()}
            hall=self.server.db.guild_hall_v0927(clan_id)
            member_ids=[int(r["account_id"]) for r in conn.execute("SELECT account_id FROM player_clan_members WHERE clan_id=?",(clan_id,)).fetchall()]
            max_crypt=0; full_set=False
            if member_ids:
                q=",".join("?" for _ in member_ids)
                rr=conn.execute(f"SELECT COALESCE(MAX(floor),0) m FROM instance_map_progress WHERE account_id IN ({q}) AND instance_kind IN ('crypt','mythic_crypt')",member_ids).fetchone()
                max_crypt=int(rr["m"] or 0)
                for aid in member_ids:
                    owned=self.server.db.collection_entry_ids(aid,"equipment")
                    for cname,tiers in LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER.items():
                        if any(set(items).issubset(owned) for items in tiers.values()):
                            full_set=True; break
                    if full_set: break
            defs=(
                ("members3","Zgrana Trójka",members>=3),("members5","Piątka Bohaterów",members>=5),
                ("bank25","Pierwszy Skarbiec Przedmiotów",bank>=25),("bank100","Wspólny Magazyn",bank>=100),
                ("salvage25","Kuźnia Gildii",metrics.get("salvage",0)>=25),("reforge25","Mistrzowie Przekucia",metrics.get("reforge",0)>=25),
                ("treasury1m","Milion w Skarbcu",treasury>=1_000_000),("guild10","Gildia Poziomu 10",level>=10),
                ("guild50","Gildia Poziomu 50",level>=50),("guild100","Gildia Poziomu 100",level>=100),
                ("deposit_1m_gold","Milion Złota Wpłacony",metrics.get("money_deposited",0)>=1_000_000*SILVER_PER_GOLD),
                ("boss100","Stu Bossów Gildii",metrics.get("boss_kills",0)>=100),
                ("crypt1000","Tysiąc Pięter",max_crypt>=1000),
                ("full_class_set","Pełny Legendarny Set",full_set),
                ("hall10","Wielka Siedziba",int(hall["hall_level"])>=10),
                ("guild_boss25","Łowcy Bossów Gildyjnych",metrics.get("guild_boss_kills",0)>=25),
            )
            for aid,name,ok in defs:
                if ok:
                    conn.execute("INSERT OR IGNORE INTO player_clan_achievements(clan_id,achievement_id,name) VALUES(?,?,?)",(clan_id,aid,name))
            conn.commit()

    async def handle_guild_rank_v0926(self, rest, row):
            conn=self.server.db.conn; cid=int(row["clan_id"]); leader=str(row["rank"])=="leader"
            parts=str(rest or "").strip().split(maxsplit=1)
            if not parts:
                rows=conn.execute("SELECT role_key,name,priority,withdraw_money,withdraw_items,invite,kick FROM player_clan_roles WHERE clan_id=? ORDER BY priority DESC,name",(cid,)).fetchall()
                await self.send("RANGI GILDII:")
                await self.send("Lider: priorytet 1000, wszystkie uprawnienia.")
                for rr in rows:
                    perms=[V0926_GUILD_PERMISSION_LABELS[k] for k in V0926_GUILD_PERMISSION_LABELS if int(rr[k] or 0)]
                    await self.send(f"{rr['name']}: priorytet {rr['priority']}; uprawnienia: {', '.join(perms) if perms else 'brak specjalnych'}.")
                return
            sub=normalize_lookup_text(parts[0]); tail=parts[1].strip() if len(parts)>1 else ""
            if sub in ("utworz","utwórz","create"):
                if not leader: await self.send("Tylko lider może tworzyć rangi."); return
                name=tail.strip()
                if not name: await self.send("Użycie: gildia ranga utworz <nazwa>."); return
                if normalize_lookup_text(name) in ("lider","leader","czlonek","członek","member","oficer","officer"):
                    await self.send("Ta nazwa jest zarezerwowana."); return
                key=self.guild_role_key_v0926(name); base=key; n=2
                while conn.execute("SELECT 1 FROM player_clan_roles WHERE clan_id=? AND role_key=?",(cid,key)).fetchone():
                    key=f"{base}_{n}"; n+=1
                try:
                    conn.execute("INSERT INTO player_clan_roles(clan_id,role_key,name,priority) VALUES(?,?,?,20)",(cid,key,name[:40])); conn.commit()
                except Exception:
                    await self.send("Nie udało się utworzyć rangi; nazwa może już istnieć."); return
                self.server.db.clan_log(cid,self.account_id,f"{self.character.name} tworzy rangę {name}.")
                await self.send(f"Utworzono rangę: {name}. Domyślnie nie ma specjalnych uprawnień."); return
            if sub in ("usun","usuń","delete"):
                if not leader: await self.send("Tylko lider może usuwać rangi."); return
                rr=self.server.db.guild_role_by_name_v0926(cid,tail)
                if not rr or rr["role_key"] in ("member","officer"): await self.send("Nie znaleziono własnej rangi do usunięcia."); return
                conn.execute("UPDATE player_clan_members SET rank='member' WHERE clan_id=? AND rank=?",(cid,rr["role_key"]))
                conn.execute("DELETE FROM player_clan_roles WHERE clan_id=? AND role_key=?",(cid,rr["role_key"])); conn.commit()
                self.server.db.clan_log(cid,self.account_id,f"{self.character.name} usuwa rangę {rr['name']}; jej członkowie wracają do rangi Członek.")
                await self.send(f"Usunięto rangę {rr['name']}. Przypisani gracze mają teraz rangę Członek."); return
            if sub in ("ustaw","permission","uprawnienie"):
                if not leader: await self.send("Tylko lider może zmieniać uprawnienia rang."); return
                p=tail.rsplit(maxsplit=2)
                if len(p)<3: await self.send("Użycie: gildia ranga ustaw <ranga> <uprawnienie> <tak/nie>."); return
                role_name,perm_raw,val_raw=p[0],p[1],p[2]
                rr=self.server.db.guild_role_by_name_v0926(cid,role_name)
                if not rr: await self.send("Nie ma takiej rangi."); return
                if rr["role_key"] in ("member","officer"): await self.send("Domyślnych rang Członek/Oficer nie edytujemy; utwórz własną rangę."); return
                perm=V0926_GUILD_PERMISSION_ALIASES.get(normalize_lookup_text(perm_raw))
                if not perm: await self.send("Uprawnienia: wyplata, przedmioty, zapraszanie, wyrzucanie."); return
                val=normalize_lookup_text(val_raw) in ("tak","yes","on","1","true")
                conn.execute(f"UPDATE player_clan_roles SET {perm}=? WHERE clan_id=? AND role_key=?",(1 if val else 0,cid,rr["role_key"])); conn.commit()
                self.server.db.clan_log(cid,self.account_id,f"{self.character.name} ustawia rangę {rr['name']}: {V0926_GUILD_PERMISSION_LABELS[perm]} = {v0926_bool_word(val)}.")
                await self.send(f"Ranga {rr['name']}: {V0926_GUILD_PERMISSION_LABELS[perm]} = {v0926_bool_word(val)}."); return
            if sub in ("priorytet","priority"):
                if not leader: await self.send("Tylko lider może ustawiać priorytet rang."); return
                p=tail.rsplit(maxsplit=1)
                if len(p)!=2 or not p[1].isdigit(): await self.send("Użycie: gildia ranga priorytet <ranga> <1-900>."); return
                rr=self.server.db.guild_role_by_name_v0926(cid,p[0]); pr=max(1,min(900,int(p[1])))
                if not rr or rr["role_key"] in ("member","officer"): await self.send("Wybierz własną rangę."); return
                conn.execute("UPDATE player_clan_roles SET priority=? WHERE clan_id=? AND role_key=?",(pr,cid,rr["role_key"])); conn.commit()
                await self.send(f"Ranga {rr['name']} ma teraz priorytet {pr}."); return
            if sub in ("nadaj","assign"):
                if not leader: await self.send("Tylko lider może nadawać rangi."); return
                p=tail.split(maxsplit=1)
                if len(p)!=2: await self.send("Użycie: gildia ranga nadaj <gracz> <ranga>."); return
                target=self.server.find_character_session(p[0]); rr=self.server.db.guild_role_by_name_v0926(cid,p[1])
                if not target or not target.character: await self.send("Gracz musi być online."); return
                tr=target.guild_row_v0926()
                if not tr or int(tr["clan_id"])!=cid: await self.send("Ten gracz nie należy do twojej Gildii."); return
                if str(tr["rank"])=="leader": await self.send("Lider zachowuje rangę Lider."); return
                if not rr: await self.send("Nie ma takiej rangi."); return
                conn.execute("UPDATE player_clan_members SET rank=? WHERE clan_id=? AND account_id=?",(rr["role_key"],cid,target.account_id)); conn.commit()
                self.server.db.clan_log(cid,self.account_id,f"{self.character.name} nadaje {target.character.name} rangę {rr['name']}.")
                await self.send(f"{target.character.name} otrzymuje rangę {rr['name']}."); await target.send(f"W Gildii {row['name']} otrzymujesz rangę {rr['name']}."); return
            await self.send("Rangi: gildia rangi; gildia ranga utworz/usun/ustaw/priorytet/nadaj.")

    def ensure_guild_estate_rooms_v0927(self, clan_id, guild_name):
            cid=int(clan_id); base=f"player_guild_estate_{cid}"
            hall=self.server.db.guild_hall_v0927(cid); hall_level=int(hall["hall_level"])
            ROOMS[base]={"zone":f"Siedziba Gildii {guild_name}","name":f"Siedziba Gildii {guild_name}, poziom {hall_level}","desc":f"Prywatna Siedziba Gildii {guild_name}. Poziom Siedziby {hall_level}/10. Rozbudowa budynków jest osobna i tańsza od rozbudowy głównej Siedziby.","exits":{"south":"square"},"guild_hall_level":hall_level}
            generator_core_v027.runtime_room_level(base,ROOMS[base],ROOMS)
            mapping=(("forge_level","east","forge","Kuźnia Gildii"),("treasury_level","west","treasury","Skarbiec Gildii"),("library_level","up","library","Biblioteka Gildii"),("training_level","down","training","Sala Treningowa Gildii"))
            for field,direction,key,label in mapping:
                lvl=int(hall[field] or 0)
                if lvl<=0: continue
                rid=f"{base}_{key}"
                ROOMS[base]["exits"][direction]=rid
                back={"east":"west","west":"east","up":"down","down":"up"}[direction]
                ROOMS[rid]={"zone":f"Siedziba Gildii {guild_name}","name":f"{label}, poziom {lvl}","desc":f"{label} rozwinięta do poziomu {lvl}/10. Pomieszczenie należy wyłącznie do Gildii {guild_name}.","exits":{back:base},"guild_hall_level":lvl}
                generator_core_v027.runtime_room_level(rid,ROOMS[rid],ROOMS)
                npc_specs={
                    "forge": ("Mistrz Kuźni Gildii", "Obsługuje Salvage, Reforge i runy bez konieczności wracania do miejskiej Kuźni."),
                    "treasury": ("Kwatermistrz Gildii", "Pilnuje wspólnego banku przedmiotów i skarbca pieniędzy."),
                    "library": ("Archiwistka Gildii", "Prowadzi kroniki osiągnięć, kontraktów i odkryć członków."),
                    "training": ("Mistrz Oręża Gildii", "Prowadzi Salę Treningową i przygotowuje walki z bossami gildyjnymi."),
                }
                npc_name,npc_dialogue=npc_specs[key]
                NPCS[f"player_guild_{key}_{cid}"]={"name":npc_name,"room":rid,"dialogue":npc_dialogue}
            if hall_level>=2:
                NPCS[f"player_guild_contracts_{cid}"]={"name":"Opiekun Tablicy Kontraktów","room":base,"dialogue":"Prowadzi wspólne kontrakty Gildii. Użyj: gildia kontrakty."}
            if hall_level>=4:
                NPCS[f"player_guild_trophies_{cid}"]={"name":"Kustosz Trofeów","room":base,"dialogue":"Prowadzi Salę Trofeów Gildii. Użyj: gildia trofea."}
            if hall_level>=7:
                NPCS[f"player_guild_bossmaster_{cid}"]={"name":"Herold Wielkich Łowów","room":base,"dialogue":"Otwiera dostęp do specjalnych bossów Gildii. Użyj: gildia boss."}
            return base

    async def enter_guild_estate_v0927(self, row):
            cid=int(row["clan_id"]); base=self.ensure_guild_estate_rooms_v0927(cid,row["name"])
            old=self.character.room_id; self.character.room_id=base; self.server.db.save_character(self.character)
            if old in ROOMS: await self.server.broadcast_room(old,f"{self.character.name} udaje się do Siedziby Gildii.",exclude=self)
            await self.look()

    async def show_guild_hall_v0927(self, row):
            cid=int(row["clan_id"]); hall=self.server.db.guild_hall_v0927(cid); treasury=int(self.server.db.conn.execute("SELECT treasury FROM player_clans WHERE id=?",(cid,)).fetchone()["treasury"] or 0)
            level=int(hall["hall_level"]); await self.send(f"SIEDZIBA GILDII: poziom {level}/10. Skarbiec: {currency_reading_text(treasury,0,0)}.")
            if level<10: await self.send(f"Rozbudowa Siedziby {level}->{level+1}: {currency_reading_text(v0927_guild_hall_upgrade_cost(level),0,0)}.")
            for key,(label,_alias,_field) in V0927_GUILD_BUILDINGS.items():
                field=f"{key}_level" if key!='treasury' else 'treasury_level'
                lvl=int(hall[field]); text=f"{label}: {lvl}/10"
                if lvl<10: text+=f", następny poziom {currency_reading_text(v0927_guild_building_upgrade_cost(lvl),0,0)}"
                await self.send(text+".")
            unlocks=["prywatna Siedziba"]
            if level>=2: unlocks.append("Tablica Kontraktów")
            if level>=4: unlocks.append("Sala Trofeów")
            if level>=7: unlocks.append("Herold Wielkich Łowów i bossowie gildyjni")
            if level>=10: unlocks.append("Wielka Sala Mistrzów")
            await self.send("Odblokowane przez poziom Siedziby: "+", ".join(unlocks)+".")
            await self.send("Komendy: gildia siedziba wejdz; gildia siedziba rozbuduj; gildia budynek rozbuduj <kowal/skarbiec/biblioteka/trening>.")

    async def handle_guild_hall_v0927(self, raw, row):
            cid=int(row["clan_id"]); rank=str(row["rank"]); norm=normalize_lookup_text(raw)
            if not raw or norm in ("status","info"): await self.show_guild_hall_v0927(row); return
            if norm in ("wejdz","wejdź","enter"): await self.enter_guild_estate_v0927(row); return
            if norm.startswith("rozbuduj"):
                if rank!="leader": await self.send("Tylko lider może rozbudowywać Siedzibę Gildii."); return
                hall=self.server.db.guild_hall_v0927(cid); level=int(hall["hall_level"]); cost=v0927_guild_hall_upgrade_cost(level)
                if not cost: await self.send("Siedziba ma już poziom 10."); return
                confirm=any(x in norm for x in ("potwierdz","confirm","tak"))
                treasury=int(self.server.db.conn.execute("SELECT treasury FROM player_clans WHERE id=?",(cid,)).fetchone()["treasury"] or 0)
                if not confirm: await self.send(f"Rozbudowa Siedziby {level}->{level+1} kosztuje {currency_reading_text(cost,0,0)}. Wpisz: gildia siedziba rozbuduj potwierdz."); return
                if treasury<cost: await self.send(f"Brakuje {currency_reading_text(cost-treasury,0,0)}."); return
                self.server.db.conn.execute("UPDATE player_clans SET treasury=treasury-? WHERE id=?",(cost,cid)); self.server.db.conn.execute("UPDATE player_guild_halls_v0927 SET hall_level=hall_level+1,updated_at=CURRENT_TIMESTAMP WHERE clan_id=?",(cid,)); self.server.db.conn.commit(); self.server.db.clan_log(cid,self.account_id,f"{self.character.name} rozbudowuje Siedzibę Gildii do poziomu {level+1}; koszt {currency_reading_text(cost,0,0)}."); self.ensure_guild_estate_rooms_v0927(cid,row["name"]); await self.send(f"Siedziba Gildii osiąga poziom {level+1}."); return
            await self.send("Użyj: gildia siedziba; gildia siedziba wejdz; gildia siedziba rozbuduj [potwierdz].")

    async def handle_guild_building_v0927(self, raw, row):
            cid=int(row["clan_id"]); rank=str(row["rank"]); parts=str(raw or '').split(maxsplit=1)
            if len(parts)<2 or normalize_lookup_text(parts[0]) not in ("rozbuduj","upgrade"):
                await self.send("Użycie: gildia budynek rozbuduj <kowal/skarbiec/biblioteka/trening>."); return
            query=normalize_lookup_text(parts[1]); chosen=None
            for key,(label,alias,_field) in V0927_GUILD_BUILDINGS.items():
                if query in (key,normalize_lookup_text(label),normalize_lookup_text(alias)): chosen=key; break
            if not chosen: await self.send("Nieznany budynek."); return
            if rank!="leader": await self.send("Tylko lider może finansować rozbudowę budynków Siedziby."); return
            hall=self.server.db.guild_hall_v0927(cid); field=f"{chosen}_level" if chosen!='treasury' else 'treasury_level'; lvl=int(hall[field]); hall_level=int(hall['hall_level'])
            if lvl>=10: await self.send("Ten budynek ma już poziom 10."); return
            if lvl>=hall_level: await self.send(f"Najpierw rozbuduj Siedzibę powyżej poziomu {hall_level}; budynek nie może przewyższać Siedziby."); return
            cost=v0927_guild_building_upgrade_cost(lvl); treasury=int(self.server.db.conn.execute("SELECT treasury FROM player_clans WHERE id=?",(cid,)).fetchone()["treasury"] or 0)
            if treasury<cost: await self.send(f"Potrzeba {currency_reading_text(cost,0,0)}; brakuje {currency_reading_text(cost-treasury,0,0)}."); return
            self.server.db.conn.execute("UPDATE player_clans SET treasury=treasury-? WHERE id=?",(cost,cid)); self.server.db.conn.execute(f"UPDATE player_guild_halls_v0927 SET {field}={field}+1,updated_at=CURRENT_TIMESTAMP WHERE clan_id=?",(cid,)); self.server.db.conn.commit(); label=V0927_GUILD_BUILDINGS[chosen][0]; self.server.db.clan_log(cid,self.account_id,f"{self.character.name} rozbudowuje {label} do poziomu {lvl+1}; koszt {currency_reading_text(cost,0,0)}."); self.ensure_guild_estate_rooms_v0927(cid,row['name']); await self.send(f"{label} osiąga poziom {lvl+1}/10.")

    async def handle_guild_contracts_v0927(self, raw, row):
            cid=int(row["clan_id"]); norm=normalize_lookup_text(raw); now=int(time.time())
            hall=self.server.db.guild_hall_v0927(cid)
            if int(hall["hall_level"])<2:
                await self.send("Tablica Kontraktów odblokowuje się na poziomie 2 Siedziby Gildii."); return
            if not raw or norm in ("lista","list","status"):
                await self.send("KONTRAKTY GILDII:")
                for contract_id,d in V0927_GUILD_CONTRACTS.items():
                    rr=self.server.db.guild_contract_row_v0927(cid,contract_id); status=v0927_guild_contract_ready_text(rr['ready_at'])
                    await self.send(f"{d['name']}: {int(rr['progress'])}/{d['need']}; nagroda {currency_reading_text(d['reward'],0,0)} do skarbca; {status}.")
                await self.send("Materiałowy kontrakt: gildia kontrakt oddaj <ilość> — oddaje Pył Runiczny ze Szkatułki."); return
            parts=str(raw).split(maxsplit=1); action=normalize_lookup_text(parts[0]); rest=parts[1].strip() if len(parts)>1 else ''
            if action in ("oddaj","donate"):
                if not rest.isdigit() or int(rest)<=0: await self.send("Użycie: gildia kontrakt oddaj <ilość>."); return
                d=V0927_GUILD_CONTRACTS['rune20']; rr=self.server.db.guild_contract_row_v0927(cid,'rune20')
                if int(rr['ready_at'] or 0)>now: await self.send(f"Ten kontrakt {v0927_guild_contract_ready_text(rr['ready_at'])}."); return
                need=max(0,int(d['need'])-int(rr['progress'])); amount=min(int(rest),need,self.server.db.storage_qty(self.account_id,'craftbox',d['item_id']))
                if amount<=0: await self.send("Nie masz potrzebnego Pyłu Runicznego albo kontrakt jest już gotowy."); return
                self.server.db.remove_storage_item(self.account_id,'craftbox',d['item_id'],amount); changed=self.server.db.guild_contract_add_v0927(cid,'material',amount); await self.send(f"Oddajesz {amount} Pyłu Runicznego na kontrakt Gildii.")
                await self.finish_ready_guild_contracts_v0927(cid,changed); return
            await self.send("Użyj: gildia kontrakty albo gildia kontrakt oddaj <ilość>.")

    async def finish_ready_guild_contracts_v0927(self, cid, changed=None):
            for contract_id,d in V0927_GUILD_CONTRACTS.items():
                rr=self.server.db.guild_contract_row_v0927(cid,contract_id)
                if int(rr['progress'])>=int(d['need']) and int(rr['ready_at'] or 0)<=int(time.time()):
                    if self.server.db.guild_contract_complete_v0927(cid,contract_id):
                        self.server.db.clan_metric_add(cid,'contracts_completed',1); self.server.db.clan_log(cid,self.account_id,f"Kontrakt {d['name']} ukończony. Do skarbca trafia {currency_reading_text(d['reward'],0,0)}.")
                        for sess in list(self.server.sessions):
                            sr=sess.guild_row_v0926() if getattr(sess,'account_id',None) and not sess.closed else None
                            if sr and int(sr['clan_id'])==cid: await sess.send(f"Gildia kończy kontrakt {d['name']}. Do skarbca trafia {currency_reading_text(d['reward'],0,0)}.")

    def ensure_guild_boss_v0927(self, row):
            cid=int(row['clan_id']); hall=self.server.db.guild_hall_v0927(cid); hl=int(hall['hall_level']); base=self.ensure_guild_estate_rooms_v0927(cid,row['name']); arena=f"{base}_training" if int(hall['training_level'] or 0)>0 else base
            name=v0927_guild_boss_name(hl); tid=f"guild_boss_v0927_{cid}_{hl}"
            if tid not in MOB_TEMPLATES:
                MOB_TEMPLATES[tid]={"name":name,"damage_type":"physical","drops":{},"guild_boss":True,"guild_id":cid,"guild_hall_level":hl,"mini_boss":True,"elite_eligible":False}
                v0190_apply_combat_template(MOB_TEMPLATES[tid])
            mob=self.server.world._register_runtime_spawn(arena,tid); return mob,arena,name

    async def handle_guild_boss_v0927(self, raw, row):
            cid=int(row['clan_id']); norm=normalize_lookup_text(raw); conn=self.server.db.conn
            hall=self.server.db.guild_hall_v0927(cid)
            if int(hall['hall_level'])<7:
                await self.send("Bossowie gildyjni odblokowują się na poziomie 7 Siedziby Gildii."); return
            if int(hall['training_level'])<1:
                await self.send("Najpierw zbuduj Salę Treningową poziom 1."); return
            rec=conn.execute("SELECT * FROM player_guild_boss_records_v0927 WHERE clan_id=?",(cid,)).fetchone(); kills=int(rec['kills'] or 0) if rec else 0; best=int(rec['fastest_kill_ms']) if rec and rec['fastest_kill_ms'] is not None else None
            if not raw or norm in ("info","status"):
                await self.send(f"BOSS GILDYJNY. Pokonania: {kills}. Najlepszy czas: {best/1000:.2f} s." if best is not None else f"BOSS GILDYJNY. Pokonania: {kills}. Brak rekordu czasu.")
                await self.send("Lider: gildia boss przyzwij. Ranking: gildia boss ranking. Trofea: gildia trofea."); return
            if norm in ("ranking","leaderboard"):
                rows=conn.execute("SELECT c.name,r.kills,r.fastest_kill_ms FROM player_guild_boss_records_v0927 r JOIN player_clans c ON c.id=r.clan_id ORDER BY r.kills DESC,CASE WHEN r.fastest_kill_ms IS NULL THEN 1 ELSE 0 END,r.fastest_kill_ms ASC LIMIT 20").fetchall(); await self.send("RANKING BOSSÓW GILDYJNYCH:")
                for i,r in enumerate(rows,1): await self.send(f"{i}. {r['name']}: {r['kills']} pokonań, rekord {('-' if r['fastest_kill_ms'] is None else f"{int(r['fastest_kill_ms'])/1000:.2f} s")}.")
                if not rows: await self.send("Brak wyników.")
                return
            if norm in ("przyzwij","summon"):
                if str(row['rank'])!='leader': await self.send("Tylko lider może przyzwać bossa Gildii."); return
                mob,arena,name=self.ensure_guild_boss_v0927(row); now=int(time.time())
                if rec and now-int(rec['last_summoned_at'] or 0)<3600: await self.send(f"Boss Gildii może być przyzwany ponownie za {max(1,(3600-(now-int(rec['last_summoned_at']))+59)//60)} min."); return
                mob.alive=True; mob.hp=MOB_TEMPLATES[mob.template_id]['max_hp']; mob.respawn_at=0; mob.engaged_by=None; mob.engaged_at=0.0
                conn.execute("INSERT INTO player_guild_boss_records_v0927(clan_id,last_boss_name,last_summoned_at) VALUES(?,?,?) ON CONFLICT(clan_id) DO UPDATE SET last_boss_name=excluded.last_boss_name,last_summoned_at=excluded.last_summoned_at",(cid,name,now)); conn.commit(); self.server.db.clan_log(cid,self.account_id,f"{self.character.name} przyzywa bossa Gildii: {name}.")
                await self.send(f"Przyzwano: {name}. Czeka w {'Sali Treningowej' if arena.endswith('_training') else 'głównej Siedzibie'}. Wpisz: gildia siedziba wejdz."); return
            await self.send("Użyj: gildia boss; gildia boss przyzwij; gildia boss ranking.")

    async def show_guild_trophies_v0927(self, row):
            cid=int(row['clan_id']); hall=self.server.db.guild_hall_v0927(cid)
            if int(hall['hall_level'])<4:
                await self.send("Sala Trofeów odblokowuje się na poziomie 4 Siedziby Gildii."); return
            rows=self.server.db.conn.execute("SELECT name,count FROM player_guild_trophies_v0927 WHERE clan_id=? ORDER BY count DESC,name",(cid,)).fetchall(); await self.send("SALA TROFEÓW GILDII:")
            for r in rows: await self.send(f"{r['name']}: {r['count']}.")
            if not rows: await self.send("Brak trofeów bossów gildyjnych.")

    async def handle_guild_v0926(self, args=""):
            raw=str(args or "").strip(); norm=normalize_lookup_text(raw); conn=self.server.db.conn
            row=self.guild_row_v0926()
            if not raw or norm in ("status","info"):
                if not row:
                    await self.send("Nie należysz do Gildii. Użyj: gildia utworz <nazwa> albo gildia dolacz po zaproszeniu."); return
                cid=int(row["clan_id"]); await self.sync_clan_achievements_v0925(cid)
                members=int(conn.execute("SELECT COUNT(*) c FROM player_clan_members WHERE clan_id=?",(cid,)).fetchone()["c"])
                item_bank=int(conn.execute("SELECT COALESCE(SUM(quantity),0) c FROM player_clan_bank WHERE clan_id=?",(cid,)).fetchone()["c"])
                grow=conn.execute("SELECT level,treasury FROM player_clans WHERE id=?",(cid,)).fetchone(); level=int(grow["level"]); treasury=int(grow["treasury"])
                ach=int(conn.execute("SELECT COUNT(*) c FROM player_clan_achievements WHERE clan_id=?",(cid,)).fetchone()["c"])
                bonus=v0926_guild_bonus_percent(level); next_cost=v0926_guild_upgrade_cost(level)
                await self.send(f"GILDIA {row['name']}. Ranga: {self.guild_rank_name_v0926(row)}. Poziom {level} z {V0926_GUILD_MAX_LEVEL}. Bonus rozwoju +{bonus}%. Członkowie: {members}. Skarbiec: {currency_reading_text(treasury,0,0)}. Bank przedmiotów: {item_bank}. Osiągnięcia: {ach}.")
                if level<V0926_GUILD_MAX_LEVEL: await self.send(f"Następna rozbudowa kosztuje {currency_reading_text(next_cost,0,0)}.")
                hall=self.server.db.guild_hall_v0927(cid)
                await self.send(f"Siedziba: {int(hall['hall_level'])}/10. Kontrakty, bossowie i budynki są dostępne przez komendy Gildii.")
                await self.send("Komendy: gildia członkowie, zaproś, dołącz, chat, wpłać, wypłać, skarbiec, bank, rangi, ranga, rozbuduj, siedziba, budynek, kontrakty, kontrakt, boss, trofea, log, osiągnięcia.")
                return
            parts=raw.split(maxsplit=1); action=normalize_lookup_text(parts[0]); rest=parts[1].strip() if len(parts)>1 else ""
            if action in ("utworz","utwórz","create"):
                if row: await self.send("Już należysz do Gildii."); return
                name=rest.strip()
                if len(name)<3: await self.send("Nazwa Gildii musi mieć co najmniej 3 znaki."); return
                try:
                    cur=conn.execute("INSERT INTO player_clans(name,owner_account_id,level,treasury) VALUES(?,?,1,0)",(name,self.account_id)); cid=int(cur.lastrowid)
                    conn.execute("INSERT INTO player_clan_members(clan_id,account_id,rank) VALUES(?,?,'leader')",(cid,self.account_id)); conn.commit()
                    self.server.db.ensure_guild_default_roles_v0926(cid)
                    self.server.db.guild_hall_v0927(cid)
                    for _contract_id in V0927_GUILD_CONTRACTS:
                        self.server.db.guild_contract_row_v0927(cid,_contract_id)
                except Exception:
                    await self.send("Nie udało się utworzyć Gildii. Nazwa może być zajęta."); return
                self.server.db.clan_log(cid,self.account_id,f"{self.character.name} zakłada Gildię {name}."); self.refresh_guild_bonus_v0926()
                await self.send(f"Utworzono Gildię {name}. Poziom 1 daje +1% do Biegłości, Soul XP, EXP statystyk i profesji."); return
            if action in ("dolacz","dołącz","join"):
                if row: await self.send("Już należysz do Gildii."); return
                inv=conn.execute("SELECT i.clan_id,c.name FROM player_clan_invites i JOIN player_clans c ON c.id=i.clan_id WHERE i.target_account_id=? ORDER BY i.created_at DESC LIMIT 1",(self.account_id,)).fetchone()
                if not inv: await self.send("Nie masz zaproszenia do Gildii."); return
                conn.execute("INSERT INTO player_clan_members(clan_id,account_id,rank) VALUES(?,?,'member')",(inv["clan_id"],self.account_id)); conn.execute("DELETE FROM player_clan_invites WHERE target_account_id=?",(self.account_id,)); conn.commit()
                self.server.db.ensure_guild_default_roles_v0926(int(inv["clan_id"])); self.server.db.clan_log(int(inv["clan_id"]),self.account_id,f"{self.character.name} dołącza do Gildii."); self.refresh_guild_bonus_v0926()
                await self.send(f"Dołączasz do Gildii {inv['name']}."); return
            if not row: await self.send("Nie należysz do Gildii."); return
            cid=int(row["clan_id"]); rank=str(row["rank"]); self.server.db.ensure_guild_default_roles_v0926(cid)
            if action in ("siedziba","hall","estate"):
                await self.handle_guild_hall_v0927(rest,row); return
            if action in ("budynek","building"):
                await self.handle_guild_building_v0927(rest,row); return
            if action in ("kontrakty","contracts"):
                await self.handle_guild_contracts_v0927("",row); return
            if action in ("kontrakt","contract"):
                await self.handle_guild_contracts_v0927(rest,row); return
            if action in ("boss","bossgildii"):
                await self.handle_guild_boss_v0927(rest,row); return
            if action in ("trofea","trophies"):
                await self.show_guild_trophies_v0927(row); return
            if action in ("czlonkowie","członkowie","members"):
                await self.send(f"CZŁONKOWIE GILDII {row['name']}:")
                rows=conn.execute("SELECT m.account_id,m.rank,a.username FROM player_clan_members m JOIN accounts a ON a.id=m.account_id WHERE m.clan_id=?",(cid,)).fetchall()
                rendered=[]
                for mr in rows:
                    role=self.server.db.guild_role_v0926(cid,mr["rank"]); rendered.append((-(int(role["priority"]) if role else 0),str(mr["username"]),str(role["name"] if role else mr["rank"])))
                for _neg,name,rname in sorted(rendered): await self.send(f"{name}: {rname}.")
                return
            if action in ("rangi","roles"):
                await self.handle_guild_rank_v0926("",row); return
            if action in ("ranga","role"):
                await self.handle_guild_rank_v0926(rest,row); return
            if action in ("invite","zapros","zaproś"):
                if not self.guild_has_permission_v0926("invite",row): await self.send("Twoja ranga nie ma prawa zapraszania."); return
                target=self.server.find_character_session(rest)
                if not target or target.closed or not target.character: await self.send("Ten gracz nie jest online."); return
                if target.character.room_id!=self.character.room_id: await self.send("Zapraszany gracz musi stać w tej samej lokacji."); return
                if target.guild_row_v0926(): await self.send("Ten gracz już należy do Gildii."); return
                conn.execute("INSERT OR REPLACE INTO player_clan_invites(clan_id,target_account_id,inviter_account_id) VALUES(?,?,?)",(cid,target.account_id,self.account_id)); conn.commit()
                await self.send(f"Zapraszasz {target.character.name} do Gildii {row['name']}."); await target.send(f"{self.character.name} zaprasza cię do Gildii {row['name']}. Wpisz: gildia dolacz."); return
            if action in ("opusc","opuść","leave"):
                if rank=="leader": await self.send("Lider nie może opuścić Gildii. Najpierw przekaż przywództwo: gildia lider <gracz>."); return
                conn.execute("DELETE FROM player_clan_members WHERE clan_id=? AND account_id=?",(cid,self.account_id)); conn.commit(); self.server.db.clan_log(cid,self.account_id,f"{self.character.name} opuszcza Gildię."); self.refresh_guild_bonus_v0926(); await self.send("Opuszczasz Gildię."); return
            if action in ("leader","lider"):
                if rank!="leader": await self.send("Tylko lider może przekazać przywództwo."); return
                target=self.server.find_character_session(rest); tr=target.guild_row_v0926() if target else None
                if not target or not tr or int(tr["clan_id"])!=cid: await self.send("Ten gracz nie jest członkiem twojej Gildii i online."); return
                conn.execute("UPDATE player_clan_members SET rank='officer' WHERE clan_id=? AND account_id=?",(cid,self.account_id)); conn.execute("UPDATE player_clan_members SET rank='leader' WHERE clan_id=? AND account_id=?",(cid,target.account_id)); conn.execute("UPDATE player_clans SET owner_account_id=? WHERE id=?",(target.account_id,cid)); conn.commit()
                self.server.db.clan_log(cid,self.account_id,f"{self.character.name} przekazuje przywództwo {target.character.name}.")
                await self.send(f"{target.character.name} zostaje liderem Gildii."); await target.send("Zostajesz liderem Gildii."); return
            if action in ("kick","wyrzuc","wyrzuć"):
                if not self.guild_has_permission_v0926("kick",row): await self.send("Twoja ranga nie ma prawa wyrzucania."); return
                target=self.server.find_character_session(rest); tr=target.guild_row_v0926() if target else None
                if not target or not tr or int(tr["clan_id"])!=cid: await self.send("Nie znaleziono członka Gildii online."); return
                if str(tr["rank"])=="leader": await self.send("Nie można wyrzucić lidera."); return
                if self.guild_rank_priority_v0926(row)<=target.guild_rank_priority_v0926(tr): await self.send("Możesz wyrzucać tylko graczy o niższym priorytecie rangi."); return
                conn.execute("DELETE FROM player_clan_members WHERE clan_id=? AND account_id=?",(cid,target.account_id)); conn.commit(); target.refresh_guild_bonus_v0926(); self.server.db.clan_log(cid,self.account_id,f"{self.character.name} usuwa {target.character.name} z Gildii.")
                await self.send(f"Usuwasz {target.character.name} z Gildii."); await target.send(f"Zostałeś usunięty z Gildii {row['name']}."); return
            if action in ("log","dziennik"):
                rows=conn.execute("SELECT message,created_at FROM player_clan_log WHERE clan_id=? ORDER BY id DESC LIMIT 40",(cid,)).fetchall(); await self.send("LOG GILDII:")
                for lr in reversed(rows): await self.send(f"{lr['created_at']}: {lr['message']}")
                if not rows: await self.send("Brak wpisów.")
                return
            if action in ("osiagniecia","osiągnięcia","achievements"):
                await self.sync_clan_achievements_v0925(cid); rows=conn.execute("SELECT name,unlocked_at FROM player_clan_achievements WHERE clan_id=? ORDER BY unlocked_at",(cid,)).fetchall(); await self.send("WSPÓLNE OSIĄGNIĘCIA GILDII:")
                for ar in rows: await self.send(f"{ar['name']}, {ar['unlocked_at']}.")
                if not rows: await self.send("Jeszcze brak.")
                return
            if action in ("chat","czat"):
                if not rest: await self.send("Użycie: gildia chat <tekst>."); return
                for sess in list(self.server.sessions):
                    if getattr(sess,"account_id",None) and not sess.closed:
                        sr=sess.guild_row_v0926()
                        if sr and int(sr["clan_id"])==cid: await sess.send(f"[GILDIA] {self.character.name}: {rest}")
                return
            if action in ("skarbiec","treasury"):
                grow=conn.execute("SELECT level,treasury FROM player_clans WHERE id=?",(cid,)).fetchone(); level=int(grow["level"]); treasury=int(grow["treasury"])
                await self.send(f"SKARBIEC GILDII: {currency_reading_text(treasury,0,0)}. Poziom Gildii {level}; bonus +{v0926_guild_bonus_percent(level)}%.")
                if level<V0926_GUILD_MAX_LEVEL: await self.send(f"Koszt następnej rozbudowy: {currency_reading_text(v0926_guild_upgrade_cost(level),0,0)}.")
                return
            if action in ("wplac","wpłać","deposit"):
                amount=self.parse_guild_money_v0926(rest)
                if amount is None: await self.send("Użycie: gildia wplac <kwota> [monet|zlota|mithril]."); return
                wallet=self.character_wallet_silver_value()
                if wallet<amount: await self.send(f"Nie masz tyle. Portfel: {currency_reading_text(wallet,0,0)}."); return
                self.character.silver=wallet-amount; self.character.gold=0; self.character.mithril=0; self.server.db.save_character(self.character)
                conn.execute("UPDATE player_clans SET treasury=treasury+? WHERE id=?",(amount,cid)); conn.commit(); self.server.db.clan_metric_add(cid,"money_deposited",amount); self.server.db.clan_log(cid,self.account_id,f"{self.character.name} wpłaca do skarbca {currency_reading_text(amount,0,0)}.")
                await self.send(f"Wpłacasz do skarbca Gildii {currency_reading_text(amount,0,0)}."); return
            if action in ("wyplac","wypłać","withdraw"):
                if not self.guild_has_permission_v0926("withdraw_money",row): await self.send("Twoja ranga nie ma uprawnienia do wypłat ze skarbca."); return
                amount=self.parse_guild_money_v0926(rest)
                if amount is None: await self.send("Użycie: gildia wyplac <kwota> [monet|zlota|mithril]."); return
                grow=conn.execute("SELECT treasury FROM player_clans WHERE id=?",(cid,)).fetchone(); treasury=int(grow["treasury"] or 0)
                if treasury<amount: await self.send(f"W skarbcu jest tylko {currency_reading_text(treasury,0,0)}."); return
                conn.execute("UPDATE player_clans SET treasury=treasury-? WHERE id=?",(amount,cid)); conn.commit()
                self.character.silver=self.character_wallet_silver_value()+amount; self.character.gold=0; self.character.mithril=0; self.server.db.save_character(self.character)
                self.server.db.clan_log(cid,self.account_id,f"{self.character.name} ({self.guild_rank_name_v0926(row)}) wypłaca na własny portfel {currency_reading_text(amount,0,0)}.")
                await self.send(f"Wypłacasz ze skarbca Gildii {currency_reading_text(amount,0,0)}. Operacja została zapisana w logu."); return
            if action in ("rozbuduj","upgrade"):
                if rank!="leader": await self.send("Tylko lider może wydawać skarbiec na rozbudowę Gildii."); return
                grow=conn.execute("SELECT level,treasury FROM player_clans WHERE id=?",(cid,)).fetchone(); level=int(grow["level"]); treasury=int(grow["treasury"])
                if level>=V0926_GUILD_MAX_LEVEL: await self.send("Gildia ma już maksymalny poziom 100."); return
                cost=v0926_guild_upgrade_cost(level); confirm=normalize_lookup_text(rest) in ("potwierdz","potwierdź","confirm","tak")
                if not confirm:
                    await self.send(f"Rozbudowa Gildii z poziomu {level} na {level+1} kosztuje {currency_reading_text(cost,0,0)}. Skarbiec: {currency_reading_text(treasury,0,0)}. Aby wydać środki wpisz: gildia rozbuduj potwierdz."); return
                if treasury<cost: await self.send(f"Brakuje {currency_reading_text(cost-treasury,0,0)} w skarbcu Gildii."); return
                conn.execute("UPDATE player_clans SET treasury=treasury-?,level=level+1 WHERE id=?",(cost,cid)); conn.commit(); new_level=level+1; new_bonus=v0926_guild_bonus_percent(new_level)
                self.server.db.clan_log(cid,self.account_id,f"{self.character.name} rozbudowuje Gildię do poziomu {new_level}; koszt {currency_reading_text(cost,0,0)}.")
                for sess in list(self.server.sessions):
                    if getattr(sess,"account_id",None) and not sess.closed:
                        sr=sess.guild_row_v0926()
                        if sr and int(sr["clan_id"])==cid:
                            sess.refresh_guild_bonus_v0926(); await sess.send(f"Gildia osiąga poziom {new_level}. Bonus rozwoju wynosi teraz +{new_bonus}%.")
                return
            if action=="bank":
                bparts=rest.split(maxsplit=1); sub=normalize_lookup_text(bparts[0]) if bparts else ""; query=bparts[1].strip() if len(bparts)>1 else ""
                if not sub:
                    rows=conn.execute("SELECT item_id,quantity FROM player_clan_bank WHERE clan_id=? AND quantity>0 ORDER BY item_id",(cid,)).fetchall(); await self.send("BANK PRZEDMIOTÓW GILDII:")
                    for br in rows: await self.send(f"{ITEMS.get(br['item_id'],{}).get('name',br['item_id'])} x{br['quantity']}.")
                    if not rows: await self.send("Pusto.")
                    return
                if sub in ("wplac","wpłać","deposit"):
                    found=self.resolve_owned_equipment_v0925(query,True)
                    if not found:
                        pool={iid:item for iid,item in ITEMS.items() if self.server.db.item_qty(self.account_id,iid)>0 and item.get('type') not in ('quest','tool','resource','craft_material') and not is_character_bound_item(iid)}; found=find_by_name(pool,query)
                    if not found: await self.send("Nie rozpoznaję wolnego przedmiotu, który można wpłacić."); return
                    iid,item=found
                    if item.get('type')=='armor' and self.free_equipment_quantity(iid)<=0: await self.send("Założonego EQ nie można wpłacić."); return
                    if item.get('type')=='armor' and (self.server.db.equipment_reforge(self.account_id,iid) or self.server.db.equipment_runes_v0925(self.account_id,iid)):
                        await self.send("Przekute lub runiczne EQ przekaż bezpośrednio graczowi; bank Gildii przyjmuje tylko niemodyfikowane EQ."); return
                    if not self.server.db.remove_item(self.account_id,iid,1): await self.send("Nie udało się wpłacić."); return
                    conn.execute("INSERT INTO player_clan_bank(clan_id,item_id,quantity) VALUES(?,?,1) ON CONFLICT(clan_id,item_id) DO UPDATE SET quantity=quantity+1",(cid,iid)); conn.commit(); self.server.db.clan_metric_add(cid,"bank_deposits",1); self.server.db.clan_log(cid,self.account_id,f"{self.character.name} wpłaca do banku przedmiotów: {item['name']}."); await self.send(f"Wpłacasz do banku Gildii: {item['name']}."); return
                if sub in ("wyplac","wypłać","withdraw"):
                    if not self.guild_has_permission_v0926("withdraw_items",row): await self.send("Twoja ranga nie ma prawa wypłaty przedmiotów."); return
                    rows=conn.execute("SELECT item_id,quantity FROM player_clan_bank WHERE clan_id=? AND quantity>0",(cid,)).fetchall(); pool={str(r['item_id']):ITEMS.get(str(r['item_id']),{'name':str(r['item_id'])}) for r in rows}; found=find_by_name(pool,query)
                    if not found: await self.send("Nie ma takiego przedmiotu w banku."); return
                    iid,item=found
                    conn.execute("UPDATE player_clan_bank SET quantity=quantity-1 WHERE clan_id=? AND item_id=?",(cid,iid)); conn.execute("DELETE FROM player_clan_bank WHERE clan_id=? AND item_id=? AND quantity<=0",(cid,iid)); conn.commit(); self.server.db.add_item(self.account_id,iid,1); self.server.db.clan_log(cid,self.account_id,f"{self.character.name} ({self.guild_rank_name_v0926(row)}) wypłaca z banku: {item['name']}."); await self.send(f"Wypłacasz z banku Gildii: {item['name']}."); return
                await self.send("Użycie: gildia bank; gildia bank wplac <przedmiot>; gildia bank wyplac <przedmiot>."); return
            await self.send("Nieznana komenda Gildii. Wpisz: gildia.")

    async def handle_clan_v0925(self, args=""):
            await self.handle_guild_v0926(args)
