# -*- coding: utf-8 -*-
"""Soulbound v0.30.47 Session mixin: world_progression."""

class SessionWorldProgressionMixin:
    def v0260_title_bonus_rule(self):
            if not self.character:
                return None
            return V0260_TITLE_BONUSES.get(str(self.character.active_title or ""))

    def v0260_profession_xp_bonus_percent(self, profession, tool_type):
            rule = self.v0260_title_bonus_rule()
            if not rule:
                return 0
            wanted = str(rule.get("tool", ""))
            if wanted == "all" or wanted == str(tool_type):
                return max(0, int(rule.get("percent", 0) or 0))
            return 0

    def v0260_title_bonus_text(self, title_name=None):
            name = str(title_name if title_name is not None else (self.character.active_title if self.character else "") or "")
            rule = V0260_TITLE_BONUSES.get(name)
            return str(rule.get("text", "")) if rule else ""

    def v0260_completed_set_ids(self):
            discovered_eq = self.server.db.collection_entry_ids(self.account_id, "equipment")
            completed = set()
            for set_id, piece_groups in V0260_SET_PIECE_GROUPS.items():
                if piece_groups and all(set(ids).intersection(discovered_eq) for ids in piece_groups.values()):
                    completed.add(set_id)
            return completed

    def v0260_museum_found_ids(self, category):
            category = str(category or "")
            if category == "sets":
                return self.v0260_completed_set_ids()
            db_category = {
                "fish": "fish", "minerals": "minerals", "herbs": "herbs",
                "wood": "wood_v026", "bosses": "bosses",
                "legendary": "legendary_v026", "secrets": "museum_secrets_v026",
            }.get(category)
            if not db_category:
                return set()
            return self.server.db.collection_entry_ids(self.account_id, db_category)

    def v0260_museum_snapshot(self):
            rows = []
            total_found = 0
            total_entries = 0
            for category, catalog in V0260_MUSEUM_CATALOGS.items():
                found = self.v0260_museum_found_ids(category)
                count = len(set(catalog).intersection(found))
                total = len(catalog)
                pct = int(count * 100 / max(1, total))
                rows.append((category, count, total, pct))
                total_found += count
                total_entries += total
            # Każdy z ośmiu działów waży równo. Dzięki temu tysiące wariantów
            # legendarnego EQ nie dominują procentu całej kolekcji.
            overall = round(
                sum((count * 100.0 / max(1, total)) for _cat, count, total, _pct in rows)
                / max(1, len(rows)),
                1,
            )
            prestige = int(round(overall * 10))
            return rows, total_found, total_entries, overall, prestige

    async def v0260_sync_museum(self):
            # Importuje stare osiągnięcia do nowego Muzeum bez odbierania graczowi historii.
            await self.sync_collection_from_inventory()
            old_materials = self.server.db.collection_entry_ids(self.account_id, "materials")
            for item_id in V0260_WOOD_CATALOG:
                if item_id in old_materials:
                    self.server.db.add_collection_entry(self.account_id, "wood_v026", item_id)

            historic_items = set()
            for old_cat in ("equipment", "unique", "named"):
                historic_items.update(self.server.db.collection_entry_ids(self.account_id, old_cat))
            for item_id in V0260_LEGENDARY_ITEM_CATALOG:
                if item_id in historic_items:
                    self.server.db.add_collection_entry(self.account_id, "legendary_v026", item_id)

            for room_id in self.server.db.collection_entry_ids(self.account_id, "surface_secrets_v0140"):
                if room_id in V0260_SURFACE_SECRET_CATALOG:
                    self.server.db.add_collection_entry(self.account_id, "museum_secrets_v026", room_id)
            for kind in INSTANCE_MAP_DEFS:
                for row in self.server.db.instance_secret_rows(self.account_id, kind):
                    idx = instance_secret_index(kind, int(row["floor"]))
                    if idx is not None:
                        key = f"instance:{kind}:{idx}"
                        if key in V0260_INSTANCE_SECRET_CATALOG:
                            self.server.db.add_collection_entry(self.account_id, "museum_secrets_v026", key)

    async def v0260_check_museum_rewards(self, announce=True):
            rows, _found, _total, overall, _prestige = self.v0260_museum_snapshot()
            for category, count, total, pct in rows:
                if total <= 0 or count < total:
                    continue
                title_name = V0260_MUSEUM_CATEGORY_TITLES[category]
                aid = f"museum:{category}:complete"
                if self.server.db.unlock_achievement(self.account_id, aid, f"Muzeum: {V0260_MUSEUM_LABELS[category]}", "Platinum"):
                    if announce:
                        await self.send(f"Muzeum ukończone: {V0260_MUSEUM_LABELS[category]}, 100%.")
                await self.unlock_title(f"museum:{category}", title_name, announce=announce)
            for threshold, title_name in V0260_GLOBAL_MUSEUM_TITLES:
                if overall >= threshold:
                    await self.unlock_title(f"museum:overall:{threshold}", title_name, announce=announce)
            return overall

    async def show_museum_v0260(self, args=""):
            await self.v0260_sync_museum()
            await self.v0260_check_museum_rewards(announce=True)
            raw = str(args or "").strip()
            norm = normalize_lookup_text(raw)
            parts = raw.split()
            if not norm or norm in ("status", "all", "wszystko"):
                rows, found, total, overall, prestige = self.v0260_museum_snapshot()
                await self.send(f"MUZEUM SOULBOUND — ukończenie kolekcji całej gry: {found} z {total}, {overall}%.")
                await self.send(f"Prestiż Muzealny: {prestige} z 1000. Ranga: {v0260_museum_rank(overall)}.")
                for category, count, cat_total, pct in rows:
                    await self.send(f"{V0260_MUSEUM_LABELS[category]}: {count} z {cat_total}, {pct}%.")
                await self.send("Szczegóły: muzeum ryby, rudy, ziola, drewno, bossowie, sety, legendarne albo sekrety.")
                return

            key = normalize_lookup_text(parts[0]).replace(" ", "") if parts else norm.replace(" ", "")
            category = V0260_MUSEUM_ALIASES.get(key)
            if not category:
                await self.send("Działy Muzeum: ryby, rudy, ziola, drewno, bossowie, sety, legendarne, sekrety.")
                return
            page = 1
            if len(parts) > 1 and parts[-1].isdigit():
                page = max(1, int(parts[-1]))
            catalog = V0260_MUSEUM_CATALOGS[category]
            found_ids = self.v0260_museum_found_ids(category)
            rows = sorted(catalog.items(), key=lambda row: normalize_lookup_text(row[1]))
            page_size = 40
            pages = max(1, math.ceil(len(rows) / page_size))
            page = min(page, pages)
            found_count = len(set(catalog).intersection(found_ids))
            pct = int(found_count * 100 / max(1, len(catalog)))
            await self.send(f"MUZEUM — {V0260_MUSEUM_LABELS[category]}: {found_count} z {len(catalog)}, {pct}%. Strona {page} z {pages}.")
            start = (page - 1) * page_size
            for number, (entry_id, name) in enumerate(rows[start:start + page_size], start + 1):
                if entry_id in found_ids:
                    await self.send(f"{number}. {name}. Odkryty.")
                else:
                    await self.send(f"{number}. Nieodkryty wpis.")
            if page < pages:
                await self.send(f"Następna strona: muzeum {parts[0]} {page + 1}.")

    async def show_prestige_v0260(self):
            await self.v0260_sync_museum()
            await self.v0260_check_museum_rewards(announce=True)
            _rows, found, total, overall, prestige = self.v0260_museum_snapshot()
            await self.send(f"PRESTIŻ MUZEALNY: {prestige} z 1000. Ranga: {v0260_museum_rank(overall)}.")
            await self.send(f"Muzeum: {found} z {total} wpisów, {overall}% ukończenia.")
            active = self.character.active_title or "brak"
            await self.send(f"Aktywny tytuł: {active}.")
            bonus = self.v0260_title_bonus_text()
            if bonus:
                await self.send(f"Aktywny bonus tytułu: {bonus}.")
            else:
                await self.send("Aktywny tytuł nie daje bonusu mechanicznego.")

    def loot_message_allowed(self, item_id):
            return loot_filter_allows(self.character.loot_filter, item_id)

    async def unlock_title(self, title_id, title_name, announce=True):
            is_new = self.server.db.unlock_title(
                self.account_id, title_id, title_name
            )
            if is_new and announce:
                await self.send(f"Nowy tytuł: {title_name}.")
            return is_new

    async def check_achievement_tiers(self, metric, value):
            definition = ACHIEVEMENT_TRACKS.get(metric)
            if not definition:
                return
            value = max(0, int(value))
            for threshold, tier in definition["tiers"]:
                if value < int(threshold):
                    continue
                achievement_id = f"{metric}:{tier.lower()}"
                if self.server.db.unlock_achievement(
                    self.account_id,
                    achievement_id,
                    definition["name"],
                    tier,
                ):
                    await self.send(
                        f"Osiągnięcie: {definition['name']}, {tier}."
                    )
                    reward_title = ACHIEVEMENT_TITLE_REWARDS.get((metric, tier))
                    if reward_title:
                        await self.unlock_title(
                            f"achievement:{achievement_id}", reward_title
                        )

    async def advance_achievement(self, metric, amount=1):
            if metric not in ACHIEVEMENT_TRACKS:
                return
            value = self.server.db.add_achievement_metric(
                self.account_id, metric, amount
            )
            await self.check_achievement_tiers(metric, value)

    async def set_achievement_progress(self, metric, value):
            if metric not in ACHIEVEMENT_TRACKS:
                return
            value = self.server.db.set_achievement_metric_max(
                self.account_id, metric, value
            )
            await self.check_achievement_tiers(metric, value)

    def current_rare_fish_stock(self):
            return sum(
                int(row["quantity"])
                for row in self.server.db.storage_rows(self.account_id, "net")
                if str(row["item_id"]) in RARE_FISH_VARIANT_IDS
            )

    def current_gem_stock(self):
            total = sum(
                int(row["quantity"])
                for row in self.server.db.storage_rows(self.account_id, "bag")
                if str(row["item_id"]) in RAW_GEM_IDS
            )
            total += sum(
                int(row["quantity"])
                for row in self.server.db.inventory(self.account_id)
                if str(row["item_id"]) in RAW_GEM_IDS or str(row["item_id"]) in CUT_GEM_IDS
            )
            return total

    async def sync_extended_achievements(self):
            # Rekonstruowalne metryki są synchronizowane z rzeczywistym trwałym stanem.
            await self.set_achievement_progress(
                "exploration_rooms",
                len(self.server.db.discovered_room_ids(self.account_id).intersection(ALL_EXPLORATION_ROOMS)),
            )
            masters = 0
            transcendents = 0
            for profession in dict.fromkeys(TOOL_PROFESSION_MAP.values()):
                row = self.server.db.profession(self.account_id, profession)
                level = int(row["level"])
                # Historyczny milestone v0.9.3 pozostaje przy 200 mimo rozszerzenia capu do 400.
                if level >= 200:
                    masters += 1
                if level >= profession_max_level(profession):
                    transcendents += 1
            await self.set_achievement_progress("profession_masters", masters)
            await self.set_achievement_progress("profession_transcendents", transcendents)
            bestiary_ids = {str(row["mob_template_id"]) for row in self.server.db.bestiary_rows(self.account_id)}
            await self.set_achievement_progress(
                "bestiary_unique", len(bestiary_ids.intersection(BESTIARY_CATALOG))
            )
            await self.set_achievement_progress(
                "multiclass_classes", len(self.active_class_names())
            )
            await self.set_achievement_progress("soul_level", self.character.soul_level)
            await self.set_achievement_progress("rare_fish_caught", self.current_rare_fish_stock())
            await self.set_achievement_progress("gems_found", self.current_gem_stock())
            bounty_state = self.server.db.bounty_board_state(self.account_id)
            await self.set_achievement_progress(
                "bounties_completed", bounty_state.get("completed_count", 0)
            )
            await self.sync_mastery_achievements_v0925()

    def bounty_kill_candidates(self):
            result = []
            for mob_id in sorted(BESTIARY_CATALOG):
                template = MOB_TEMPLATES.get(mob_id, {})
                if not BESTIARY_SPAWN_ROOMS.get(mob_id):
                    continue
                if mob_id in BOSS_COLLECTION_CATALOG or template.get("mini_boss"):
                    continue
                if template.get("rare_mob") or template.get("rare_base_template") or template.get("elite_base_template"):
                    continue
                if v0863_is_boss_template(template):
                    continue
                result.append((mob_id, template.get("name", mob_id)))
            return result

    def generate_bounty_offers(self):
            offers = []
            kinds = list(BOUNTY_KINDS)
            random.shuffle(kinds)
            # Trzy różne typy na planszy zwiększają szansę, że gracz może wykonać
            # kontrakt bez zmiany aktualnej aktywności/profesji.
            for kind in kinds[:BOUNTY_OFFER_COUNT]:
                if kind == "kill":
                    candidates = self.bounty_kill_candidates()
                    if not candidates:
                        continue
                    target, name = random.choice(candidates)
                    needed = random.choice((8, 10, 12, 15))
                    base_needed = needed
                    label = f"Pokonaj {needed} razy: {name}"
                elif kind in ("mine", "fish", "wood", "herb"):
                    target = kind
                    base_needed = random.choice(BOUNTY_RESOURCE_NEEDS[kind])
                    needed = base_needed
                    if kind == "fish":
                        fish_level = self.profession_level_for_tool("fishing")
                        needed = max(
                            base_needed,
                            int(math.ceil(base_needed * v096_fishing_workload_scale(fish_level))),
                        )
                    label = f"{BOUNTY_RESOURCE_LABELS[kind]}: {needed} sztuk"
                else:
                    target = "any"
                    base_needed = random.choice(BOUNTY_RESOURCE_NEEDS.get(kind, (1, 2, 3)))
                    needed = base_needed
                    unit = {
                        "explore": "nowych sektorów", "event": "wydarzeń", "secret": "sekretów", "mini": "mini-lochów",
                    }.get(kind, "celów")
                    label = f"{BOUNTY_RESOURCE_LABELS.get(kind, kind)}: {needed} {unit}"
                reward_needed = base_needed
                if kind == "kill" and target in MOB_TEMPLATES:
                    reward_stage=v0190_mob_stage(MOB_TEMPLATES[target])
                elif kind in ("mine","fish","wood","herb"):
                    reward_stage=max(1,self.profession_level_for_tool({"mine":"mining","fish":"fishing","wood":"woodcutting","herb":"herbalism"}[kind]))
                else:
                    _char = getattr(self, "character", None)
                    _soul = int(getattr(_char, "soul_level", 1) or 1) if _char is not None else 1
                    try:
                        _mastery = int(self.highest_active_class_mastery())
                    except Exception:
                        _mastery = 1
                    reward_stage=max(1, _soul, _mastery)
                soul_xp=max(1,int(round(v0190_log_curve(reward_stage,V019_SOUL_KILL_NORMAL)*max(2.0,math.sqrt(reward_needed)))))
                reward_coins=max(1,int(round(v0190_log_curve(reward_stage,V019_QUEST_COIN)*0.75)))
                gold=max(1,reward_coins//SILVER_PER_GOLD)
                offers.append({
                    "kind": kind,
                    "target": target,
                    "label": label,
                    "needed": int(needed),
                    "reward_soul_xp": int(soul_xp),
                    "reward_gold": int(gold),
                })
            while len(offers) < BOUNTY_OFFER_COUNT:
                kind = random.choice(("mine", "fish", "wood", "herb"))
                target = kind
                base_needed = random.choice(BOUNTY_RESOURCE_NEEDS[kind])
                needed = base_needed
                if kind == "fish":
                    fish_level = self.profession_level_for_tool("fishing")
                    needed = max(
                        base_needed,
                        int(math.ceil(base_needed * v096_fishing_workload_scale(fish_level))),
                    )
                reward_stage=max(1,self.profession_level_for_tool({"mine":"mining","fish":"fishing","wood":"woodcutting","herb":"herbalism"}[kind]))
                soul_xp=max(1,int(round(v0190_log_curve(reward_stage,V019_SOUL_KILL_NORMAL)*max(2.0,math.sqrt(base_needed)))))
                reward_coins=max(1,int(round(v0190_log_curve(reward_stage,V019_QUEST_COIN)*0.75)))
                gold=max(1,reward_coins//SILVER_PER_GOLD)
                offers.append({
                    "kind": kind,
                    "target": target,
                    "label": f"{BOUNTY_RESOURCE_LABELS[kind]}: {needed} sztuk",
                    "needed": int(needed),
                    "reward_soul_xp": int(soul_xp),
                    "reward_gold": int(gold),
                })
            return offers[:BOUNTY_OFFER_COUNT]

    def ensure_bounty_board(self):
            state = self.server.db.bounty_board_state(self.account_id)
            if not state.get("offers"):
                state["offers"] = self.generate_bounty_offers()
                self.server.db.save_bounty_board_state(
                    self.account_id,
                    offers=state["offers"],
                    active=state.get("active", {}),
                    completed_count=state.get("completed_count", 0),
                )
            return state

    async def show_bounty_board(self):
            state = self.ensure_bounty_board()
            active = state.get("active") or {}
            await self.send(
                f"TABLICA ZLECEŃ. Ukończone kontrakty: {int(state.get('completed_count', 0))}."
            )
            if active:
                progress = max(0, int(active.get("progress", 0)))
                needed = max(1, int(active.get("needed", 1)))
                status = "cel wykonany" if progress >= needed else "w toku"
                await self.send(
                    f"Aktywny kontrakt: {active.get('label', 'Kontrakt')}. "
                    f"Postęp {progress} z {needed}, {status}. "
                    f"Nagroda: {int(active.get('reward_soul_xp', 0))} Soul XP i "
                    f"{currency_reading_text(0, int(active.get('reward_gold', 0)), 0)}."
                )
            else:
                await self.send("Aktywny kontrakt: brak.")
            await self.send("DOSTĘPNE KONTRAKTY:")
            for index, offer in enumerate(state.get("offers") or [], 1):
                await self.send(
                    f"{index}. {offer.get('label', 'Kontrakt')}. "
                    f"Start 0 z {int(offer.get('needed', 1))}. "
                    f"Nagroda: {int(offer.get('reward_soul_xp', 0))} Soul XP i "
                    f"{currency_reading_text(0, int(offer.get('reward_gold', 0)), 0)}."
                )
            await self.send(
                "Komendy: bounty accept <1-3>, bounty aktywne, bounty odbierz; "
                "bounty odśwież losuje nową tablicę tylko bez aktywnego kontraktu."
            )

    async def handle_bounty(self, args=""):
            raw = str(args or "").strip()
            norm = normalize_lookup_text(raw)
            if not norm or norm in ("lista", "list", "status", "info"):
                await self.show_bounty_board()
                return
            state = self.ensure_bounty_board()
            active = state.get("active") or {}

            if norm in ("aktywne", "aktywny", "active", "progress", "postep", "postęp"):
                if not active:
                    await self.send("Nie masz aktywnego kontraktu. Wpisz bounty.")
                    return
                progress = max(0, int(active.get("progress", 0)))
                needed = max(1, int(active.get("needed", 1)))
                await self.send(
                    f"Kontrakt: {active.get('label', 'Kontrakt')}. Postęp {progress} z {needed}."
                )
                return

            if norm in ("odbierz", "claim"):
                if not active:
                    await self.send("Nie masz aktywnego kontraktu do odebrania.")
                    return
                progress = max(0, int(active.get("progress", 0)))
                needed = max(1, int(active.get("needed", 1)))
                if progress < needed:
                    await self.send(
                        f"Kontrakt nie jest ukończony. Postęp {progress} z {needed}."
                    )
                    return
                soul_xp = max(0, int(active.get("reward_soul_xp", 0)))
                gold = max(0, int(active.get("reward_gold", 0)))
                label = str(active.get("label", "Kontrakt"))
                if str(active.get("kind")) == "kill":
                    combat_quest = {
                        "kind": "kill", "target": active.get("target"),
                        "needed": needed, "repeatable": True,
                    }
                    contract_stat_xp = v0914_combat_quest_stat_reward(combat_quest)
                    await self.grant_combat_quest_stat_xp(
                        contract_stat_xp, repeatable=True, source_label="Kontrakt bojowy"
                    )
                if soul_xp:
                    await self.grant_soul_xp(soul_xp)
                self.character.gold += gold
                self.server.db.save_character(self.character)
                completed = int(state.get("completed_count", 0)) + 1
                self.server.db.add_lifetime_stat(self.account_id, "bounties_completed", 1)
                offers = self.generate_bounty_offers()
                self.server.db.save_bounty_board_state(
                    self.account_id, offers=offers, active={}, completed_count=completed
                )
                await self.set_achievement_progress("bounties_completed", completed)
                await self.send(
                    f"Kontrakt odebrany: {label}. Nagroda: {soul_xp} Soul XP i " + currency_reading_text(0, gold, 0) + ". "
                    f"Ukończone kontrakty: {completed}. Tablica wylosowała nowe oferty."
                )
                return

            if norm in ("odswiez", "odśwież", "refresh", "new", "nowe"):
                if active:
                    await self.send(
                        "Nie można odświeżyć Tablicy Zleceń przy aktywnym kontrakcie."
                    )
                    return
                offers = self.generate_bounty_offers()
                self.server.db.save_bounty_board_state(
                    self.account_id, offers=offers, active={},
                    completed_count=state.get("completed_count", 0),
                )
                await self.send("Tablica Zleceń została ponownie wylosowana.")
                await self.show_bounty_board()
                return

            accept_text = norm
            for prefix in ("accept ", "przyjmij ", "wez ", "weź "):
                if accept_text.startswith(prefix):
                    accept_text = accept_text[len(prefix):].strip()
                    break
            if accept_text.isdigit():
                if active:
                    progress = int(active.get("progress", 0))
                    needed = int(active.get("needed", 1))
                    await self.send(
                        f"Masz już aktywny kontrakt. Postęp {progress} z {needed}."
                    )
                    return
                index = int(accept_text) - 1
                offers = list(state.get("offers") or [])
                if not (0 <= index < len(offers)):
                    await self.send("Nie ma takiego numeru kontraktu. Wpisz bounty.")
                    return
                active = dict(offers[index])
                active["progress"] = 0
                active["completed"] = False
                self.server.db.save_bounty_board_state(
                    self.account_id, offers=offers, active=active,
                    completed_count=state.get("completed_count", 0),
                )
                await self.send(
                    f"Przyjęto kontrakt: {active['label']}. Postęp 0 z {int(active['needed'])}. "
                    f"Nagroda: {int(active['reward_soul_xp'])} Soul XP i " + currency_reading_text(0, int(active['reward_gold']), 0) + "."
                )
                return

            await self.send(
                "Użycie: bounty; bounty accept <1-3>; bounty aktywne; "
                "bounty odbierz; bounty odśwież."
            )

    async def advance_bounty(self, kind, target=None, amount=1):
            state = self.server.db.bounty_board_state(self.account_id)
            active = state.get("active") or {}
            if not active:
                return False
            kind = str(kind or "")
            if str(active.get("kind")) != kind:
                return False
            if kind == "kill":
                wanted = canonical_bestiary_template_id(active.get("target"))
                actual = canonical_bestiary_template_id(target)
                if wanted != actual:
                    return False
            old = max(0, int(active.get("progress", 0)))
            needed = max(1, int(active.get("needed", 1)))
            if old >= needed:
                return False
            new = min(needed, old + max(0, int(amount)))
            if new <= old:
                return False
            active["progress"] = new
            active["completed"] = new >= needed
            self.server.db.save_bounty_board_state(
                self.account_id,
                offers=state.get("offers", []),
                active=active,
                completed_count=state.get("completed_count", 0),
            )
            if new >= needed:
                await self.send(
                    f"Kontrakt: {active.get('label', 'Kontrakt')}. Postęp {new} z {needed}. "
                    "Cel wykonany. Użyj bounty odbierz."
                )
            else:
                await self.send(
                    f"Kontrakt: {active.get('label', 'Kontrakt')}. Postęp {new} z {needed}."
                )
            return True

    async def check_all_minibosses_achievement(self):
            if not MINI_BOSS_IDS:
                return
            discovered = self.server.db.collection_entry_ids(
                self.account_id, "bosses"
            )
            if not MINI_BOSS_IDS.issubset(discovered):
                return
            achievement_id = "all_minibosses"
            if self.server.db.unlock_achievement(
                self.account_id,
                achievement_id,
                "Wszystkie Mini-Bossy",
                "Platinum",
            ):
                await self.send("Osiągnięcie: Wszystkie Mini-Bossy, Platinum.")
                await self.unlock_title(
                    "achievement:all_minibosses", "Pogromca Mini-Bossów"
                )

    async def announce_item_collect_quest_progress(self, item_id, amount=1):
            """v0.8.66: postęp collect rośnie tylko od nowego zdobycza po przyjęciu."""
            changed = self.server.db.increment_item_collect_quest(
                self.account_id, item_id, amount
            )
            for quest_id, progress, needed in changed:
                quest = QUESTS[quest_id]
                label = str(
                    quest.get("progress_label")
                    or ITEMS.get(item_id, {}).get("name", "przedmiotów")
                )
                if progress >= needed:
                    await self.send(
                        f"Postęp questa: {quest['name']}. "
                        f"{progress} z {needed} {label}. "
                        f"Cel wykonany. Wróć do NPC: {quest.get('giver', 'NPC')}."
                    )
                else:
                    await self.send(
                        f"Postęp questa: {quest['name']}. "
                        f"{progress} z {needed} {label}."
                    )

    async def grant_hourly_quest_kill_drop_v0929(self, mob_template_id, template):
            # v0.30.38: specjalne questy kill->item zwiększają licznik bezpośrednio
            # w miejscu przyznania przedmiotu. Nie polegamy już na pośrednim
            # record_item_collection(), dzięki czemu NVDA zawsze dostaje X/Y.
            for quest_id in (
                "haldor_broken_blades_v0929",
                "haldor_armor_recycling_v0929",
                "orin_toxic_glands_v0929",
            ):
                row = self.server.db.quest(self.account_id, quest_id)
                quest = QUESTS.get(quest_id)
                if not row or row["status"] != "active" or not quest:
                    continue
                if int(row["progress"]) >= int(quest.get("needed", 1)):
                    continue
                item_id = v0929_kill_drop_item(quest_id, mob_template_id, template)
                if not item_id:
                    continue

                self.server.db.add_item(self.account_id, item_id, 1)
                changed = self.server.db.increment_item_collect_quest(
                    self.account_id, item_id, 1
                )
                await self.send(
                    f"Przedmiot questowy: {ITEMS[item_id]['name']} x1 z {template.get('name', mob_template_id)}."
                )
                for changed_quest_id, progress, needed in changed:
                    if changed_quest_id != quest_id:
                        continue
                    label = str(
                        quest.get("progress_label")
                        or ITEMS.get(item_id, {}).get("name", "przedmiotów")
                    )
                    if progress >= needed:
                        await self.send(
                            f"Postęp questa: {quest['name']}. "
                            f"{progress} z {needed} {label}. "
                            f"Cel wykonany. Wróć do NPC: {quest.get('giver', 'NPC')}."
                        )
                    else:
                        await self.send(
                            f"Postęp questa: {quest['name']}. "
                            f"{progress} z {needed} {label}."
                        )

                # Kolekcja/Museum nadal dostaje przedmiot, ale nie może drugi raz
                # podbić tego samego questa.
                await self.record_item_collection(
                    item_id, source=template.get("name", mob_template_id),
                    announce=True, record_history=False, amount=1,
                    quest_progress=False,
                )

    async def record_item_collection(
            self, item_id, source="", announce=True, record_history=True, amount=1,
            quest_progress=True,
        ):
            item = ITEMS.get(item_id)
            if not item:
                return
            zone = ROOMS.get(self.character.room_id, {}).get("zone", "")
            rank = loot_rarity_rank(item_id)
            if record_history and rank >= 1:
                rarity = str(item.get("rarity_name") or item.get("rarity") or "Rare")
                self.server.db.add_drop_history(
                    self.account_id,
                    item_id,
                    item.get("name", item_id),
                    rarity,
                    source,
                    zone,
                )

            base_resource_id = canonical_profession_resource_id(item_id)
            collection_candidates = []
            if base_resource_id in FISH_COLLECTION_CATALOG:
                collection_candidates.append(("fish", base_resource_id))
            if base_resource_id in MINERAL_COLLECTION_CATALOG:
                collection_candidates.append(("minerals", base_resource_id))
            if base_resource_id in HERB_COLLECTION_CATALOG:
                collection_candidates.append(("herbs", base_resource_id))
            if base_resource_id in MATERIAL_COLLECTION_CATALOG:
                collection_candidates.append(("materials", base_resource_id))
            if item_id in GEM_COLLECTION_CATALOG:
                collection_candidates.append(("gems", item_id))
            if item_id in UNIQUE_ITEM_COLLECTION_CATALOG:
                collection_candidates.append(("unique", item_id))
            if item_id in EQUIPMENT_COLLECTION_CATALOG:
                collection_candidates.append(("equipment", item_id))
            if base_resource_id in V0260_WOOD_CATALOG:
                collection_candidates.append(("wood_v026", base_resource_id))
            if item_id in V0260_LEGENDARY_ITEM_CATALOG:
                collection_candidates.append(("legendary_v026", item_id))

            museum_changed = False
            for category, entry_id in collection_candidates:
                is_new = self.server.db.add_collection_entry(
                    self.account_id, category, entry_id
                )
                if is_new and category in ("wood_v026", "legendary_v026"):
                    museum_changed = True
                if is_new and announce:
                    if category == "wood_v026":
                        await self.send(f"Nowy wpis Muzeum: Drewno — {V0260_WOOD_CATALOG[entry_id]}.")
                    elif category == "legendary_v026":
                        await self.send(f"Nowy wpis Muzeum: Legendarne przedmioty — {V0260_LEGENDARY_ITEM_CATALOG[entry_id]}.")
                    else:
                        await self.send(
                            f"Nowa kolekcja: {COLLECTION_CATEGORY_LABELS[category]} — "
                            f"{COLLECTION_CATALOGS[category][entry_id]}."
                        )

            if item_id in NAMED_LOOT_CATALOG:
                is_new = self.server.db.add_collection_entry(
                    self.account_id, "named", item_id
                )
                if is_new and announce:
                    await self.send(
                        f"Nowy wpis Codexu: {NAMED_LOOT_CATALOG[item_id]}, Named Loot."
                    )

            set_entry = SET_ENTRY_BY_ITEM.get(item_id)
            if set_entry:
                is_new = self.server.db.add_collection_entry(
                    self.account_id, "sets", set_entry
                )
                if is_new and announce:
                    await self.send(
                        f"Nowy wpis Codexu: {SET_COLLECTION_CATALOG[set_entry]['name']}, Set."
                    )
                museum_changed = museum_changed or bool(is_new)

            if museum_changed and announce:
                await self.v0260_check_museum_rewards(announce=True)

            # v0.8.40: quest item progress is spoken immediately after loot.
            # This deliberately ignores the loot speech filter: quest progress is
            # gameplay-critical information for screen-reader users.
            if announce and quest_progress:
                await self.announce_item_collect_quest_progress(
                    item_id, max(1, int(amount))
                )

    async def sync_collection_from_inventory(self):
            owned = {row["item_id"] for row in self.server.db.inventory(self.account_id)}
            owned.update(row["item_id"] for row in self.server.db.equipment(self.account_id))
            for container in ("net", "bag", "woodpile", "herbbag", "craftbox"):
                owned.update(
                    row["item_id"] for row in self.server.db.storage_rows(self.account_id, container)
                )
            for item_id in owned:
                await self.record_item_collection(
                    item_id, source="posiadany przedmiot",
                    announce=False, record_history=False
                )
            for fish_id in self.server.db.fish_journal_ids(self.account_id):
                if fish_id in FISH_COLLECTION_CATALOG:
                    self.server.db.add_collection_entry(self.account_id, "fish", fish_id)

    async def record_mob_progress(self, mob):
            template = MOB_TEMPLATES[mob.template_id]
            self.server.db.add_lifetime_stat(self.account_id, "kills_total", 1)
            self.server.db.add_lifetime_stat(self.account_id, "combat_victories", 1)
            base_id = (
                template.get("rare_base_template")
                or template.get("elite_base_template")
                or mob.template_id
            )
            base_name = MOB_TEMPLATES.get(base_id, template).get("name", "")

            if "goblin" in str(base_id).lower() or "goblin" in base_name.lower():
                await self.advance_achievement("goblin_kills", 1)

            if template.get("rare_mob"):
                is_new = self.server.db.add_collection_entry(
                    self.account_id, "rare", mob.template_id
                )
                if is_new:
                    await self.send(
                        f"Nowy wpis Codexu: {template['name']}, Rare Mob."
                    )
                await self.advance_achievement("rare_kills", 1)
                self.server.db.add_lifetime_stat(self.account_id, "rare_kills", 1)

            is_boss = any(
                template.get(flag)
                for flag in (
                    "world_boss", "mini_boss", "crypt_boss", "astral_boss",
                    "mythic_crypt_boss", "mythic_astral_boss", "giant_fortress_boss",
                )
            )
            if is_boss:
                BOSS_COLLECTION_CATALOG.setdefault(mob.template_id, template.get("name", mob.template_id))
                is_new = self.server.db.add_collection_entry(
                    self.account_id, "bosses", mob.template_id
                )
                if is_new:
                    await self.send(
                        f"Nowy wpis Codexu: {template['name']}, Boss."
                    )
                    await self.v0260_check_museum_rewards(announce=True)
                await self.advance_achievement("boss_kills", 1)
                self.server.db.add_lifetime_stat(self.account_id, "boss_kills", 1)
                if template.get("mini_boss"):
                    await self.check_all_minibosses_achievement()

    async def advance_v0140_quest_progress(self, kind, target="any", amount=1):
            amount = max(1, int(amount))
            changed = []
            for row in self.server.db.quest_rows(self.account_id):
                if row["status"] != "active":
                    continue
                quest = QUESTS.get(row["quest_id"])
                if not quest or quest.get("kind") != kind:
                    continue
                wanted = str(quest.get("target", "any"))
                if wanted not in ("any", str(target)):
                    continue
                needed = max(1, int(quest.get("needed", 1)))
                old = max(0, int(row["progress"]))
                new = min(needed, old + amount)
                if new == old:
                    continue
                self.server.db.set_quest_progress(self.account_id, row["quest_id"], new)
                changed.append((row["quest_id"], new, needed))
            for quest_id, progress, needed in changed:
                await self.send(f"Postęp questa: {QUESTS[quest_id]['name']}. {progress} z {needed}.")
                if progress >= needed:
                    await self.send("Cel wykonany. Wróć do właściwego NPC.")
            return changed

    async def register_v0140_world_event_visit(self, room_id):
            event = v0140_event_for_room(room_id)
            if not event:
                return False
            is_new = self.server.db.add_collection_entry(
                self.account_id, "world_events_v0140", event["token"]
            )
            if is_new:
                await self.advance_v0140_quest_progress("world_event", event["type"], 1)
                await self.advance_bounty("event", event["type"], 1)
                await self.advance_dynamic_world_quest_v015("event", event["type"], 1)
                self.server.db.add_collection_entry(self.account_id, "event_types_v015", event["type"])
                await self.add_faction_reputation_v016("cartographers", 1, reason="world_event")
            return is_new

    async def show_weather_v015(self):
            identity = v0130_frontier_room_identity(self.character.room_id)
            phase = v0150_time_state()
            if not identity:
                await self.send(f"Pora świata: {phase['label']}. W stałym rdzeniu pogoda jest spokojna i nie wpływa na dostępność zawartości.")
                return
            weather = v0150_weather_state(self.character.room_id)
            await self.send(f"Pora świata: {phase['label']}. Pogoda: {weather['label']}.")
            for tool, label in (("fishing","Wędkarstwo"),("herbalism","Zielarstwo"),("mining","Górnictwo"),("woodcutting","Drwalstwo")):
                bonus = v0150_environment_bonus(self.character.room_id, tool)
                if bonus["xp_mult"] > 1.0:
                    await self.send(f"{label}: +{int(round((bonus['xp_mult']-1.0)*100))}% XP z warunków świata.")
            await self.send("Pogoda nie blokuje questów, ruchu, walki ani profesji. Brak pułapek pogodowych.")

    def biome_mastery_state_v015(self, kind):
            if kind not in V013_FRONTIER_SPECS:
                return (0, V013_FRONTIER_ROOMS_PER_BIOME, 0)
            discovered = self.server.db.discovered_room_ids(self.account_id)
            ids = set(v0130_frontier_room_ids(kind))
            count = len(ids.intersection(discovered))
            total = len(ids)
            pct = int(count * 100 / max(1,total))
            return count, total, pct

    async def check_biome_mastery_v015(self, kind):
            if kind not in V013_FRONTIER_SPECS:
                return
            count,total,pct = self.biome_mastery_state_v015(kind)
            for threshold in V015_BIOME_MASTERY_THRESHOLDS:
                if pct < threshold:
                    continue
                entry = f"{kind}:{threshold}"
                if self.server.db.add_collection_entry(self.account_id, "biome_mastery_v015", entry):
                    title = v0150_biome_mastery_title(kind, threshold)
                    await self.send(f"Biome Mastery: {V013_FRONTIER_SPECS[kind]['zone']} {threshold}%. {count} z {total} sektorów.")
                    await self.unlock_title(f"biome:{entry}", title)

    async def show_biome_mastery_v015(self, args=""):
            query = normalize_lookup_text(args)
            selected = None
            if query:
                for kind,spec in V013_FRONTIER_SPECS.items():
                    if query in (normalize_lookup_text(kind), normalize_lookup_text(spec['zone'])):
                        selected = kind; break
            kinds = (selected,) if selected else tuple(V013_FRONTIER_SPECS)
            await self.send("BIOME MASTERY")
            for kind in kinds:
                await self.check_biome_mastery_v015(kind)
                count,total,pct = self.biome_mastery_state_v015(kind)
                await self.send(f"{V013_FRONTIER_SPECS[kind]['zone']}: {count} z {total}, {pct}%.")

    async def show_collection_world_v015(self):
            await self.send("COLLECTION CODEX — ŚWIAT v0.15")
            for kind in V013_FRONTIER_SPECS:
                await self.check_biome_mastery_v015(kind)
            mastery = self.server.db.collection_entry_ids(self.account_id, "biome_mastery_v015")
            weather = self.server.db.collection_entry_ids(self.account_id, "weather_v015")
            secrets = self.server.db.collection_entry_ids(self.account_id, "surface_secrets_v0140")
            discovered_rooms = self.server.db.discovered_room_ids(self.account_id)
            minis = {rid for rid in discovered_rooms if ROOMS.get(rid, {}).get("v0140_mini_final")}
            event_tokens = self.server.db.collection_entry_ids(self.account_id, "world_events_v0140")
            events = {token.split(":", 2)[1] for token in event_tokens if token.count(":") >= 2}
            total_weather = sum(len(set(pool)) for pool in V015_WEATHER_POOLS.values())
            await self.send(f"Biome Mastery: {len(mastery)} z {len(V013_FRONTIER_SPECS)*len(V015_BIOME_MASTERY_THRESHOLDS)} progów.")
            await self.send(f"Poznane wzorce pogody: {len(weather)} z {total_weather} kombinacji biom-pogoda.")
            await self.send(f"Sekrety świata: {len(secrets)} z {len(v0140_surface_secret_room_ids())}.")
            await self.send(f"Finały mini-lochów odkryte: {len(minis)}.")
            await self.send(f"Typy eventów odwiedzone: {len(events)} z {len(V014_WORLD_EVENT_DEFS)}.")

    async def handle_dynamic_world_quest_v015(self, args=""):
            raw = normalize_lookup_text(args)
            row = self.server.db.dynamic_world_quest_v015(self.account_id)
            active = dict(row) if row else None
            offer = v0150_dynamic_world_offer(self.account_id)
            if raw in ("", "oferta", "offer"):
                if active:
                    await self.send(f"Aktywne zadanie świata: {active['label']}. Postęp {active['progress']} z {active['needed']}.")
                await self.send(f"Aktualna oferta: {offer['label']}. Cel {offer['needed']}. Nagroda: {offer['reward_soul_xp']} Soul XP i " + currency_reading_text(0, int(offer['reward_gold']), 0) + ".")
                await self.send("Komendy: worldquest accept, worldquest aktywne, worldquest odbierz, worldquest porzuc.")
                return
            if raw in ("accept","przyjmij","przyjmij zadanie"):
                if active:
                    await self.send("Masz już aktywne dynamiczne zadanie świata.")
                    return
                self.server.db.save_dynamic_world_quest_v015(self.account_id, offer)
                await self.send(f"Przyjęto: {offer['label']}. Postęp 0 z {offer['needed']}.")
                return
            if raw in ("aktywne","active","status"):
                if not active:
                    await self.send("Nie masz aktywnego dynamicznego zadania świata.")
                    return
                await self.send(f"{active['label']}. Postęp {active['progress']} z {active['needed']}." + (" Cel wykonany; użyj worldquest odbierz." if active['completed'] else ""))
                return
            if raw in ("porzuc","porzuć","abandon"):
                if not active:
                    await self.send("Nie masz aktywnego zadania.")
                    return
                self.server.db.clear_dynamic_world_quest_v015(self.account_id)
                await self.send("Porzucono dynamiczne zadanie świata.")
                return
            if raw in ("odbierz","claim","nagroda"):
                if not active or not active['completed']:
                    await self.send("Dynamiczne zadanie świata nie jest jeszcze ukończone.")
                    return
                await self.grant_soul_xp(int(active['reward_soul_xp']))
                self.character.gold += int(active['reward_gold'])
                self.server.db.save_character(self.character)
                self.server.db.add_lifetime_stat(self.account_id, "dynamic_world_quests_completed", 1)
                label = active['label']
                self.server.db.clear_dynamic_world_quest_v015(self.account_id)
                await self.send(f"Ukończono dynamiczne zadanie: {label}. Nagroda odebrana.")
                return
            await self.send("Użycie: worldquest; worldquest accept; worldquest aktywne; worldquest odbierz; worldquest porzuc.")

    async def advance_dynamic_world_quest_v015(self, kind, target=None, amount=1):
            row = self.server.db.dynamic_world_quest_v015(self.account_id)
            if not row:
                return False
            active = dict(row)
            if active.get("completed"):
                return False
            qtype = str(active.get("quest_type") or "")
            if qtype != str(kind or ""):
                return False
            wanted = str(active.get("target") or "any")
            if wanted not in ("any", str(target)):
                return False
            old = max(0,int(active.get("progress",0)))
            needed = max(1,int(active.get("needed",1)))
            new = min(needed, old + max(0,int(amount)))
            if new <= old:
                return False
            active["progress"] = new
            active["completed"] = new >= needed
            self.server.db.save_dynamic_world_quest_v015(self.account_id, active)
            await self.send(f"Dynamiczne zadanie: {active['label']}. Postęp {new} z {needed}." + (" Cel wykonany." if new >= needed else ""))
            return True

    async def add_faction_reputation_v016(self, faction_id, amount=1, reason=""):
            if faction_id not in V016_FACTIONS:
                return 0
            old = self.server.db.faction_reputation_v016(self.account_id, faction_id)
            new = self.server.db.add_faction_reputation_v016(self.account_id, faction_id, amount)
            old_rank = v0160_faction_rank(old)
            new_rank = v0160_faction_rank(new)
            if new_rank != old_rank:
                await self.send(f"Reputacja: {V016_FACTIONS[faction_id]['name']} — {new_rank}, {new} pkt.")
            for threshold in V016_FACTION_THRESHOLDS:
                if not (old < threshold <= new):
                    continue
                reward_key = f"{faction_id}:{threshold}"
                if not self.server.db.add_collection_entry(self.account_id, "faction_rewards_v016", reward_key):
                    continue
                if threshold == 25:
                    await self.unlock_title(f"faction:{reward_key}", f"Przyjaciel: {V016_FACTIONS[faction_id]['name']}")
                elif threshold == 75:
                    self.server.db.add_item(self.account_id, V014_TREASURE_MAP_ITEM, 1)
                    await self.send(f"Nagroda frakcji: {ITEMS[V014_TREASURE_MAP_ITEM]['name']} x1.")
                elif threshold == 150:
                    badge = f"v016_badge_{faction_id}"
                    self.server.db.add_item(self.account_id, badge, 1)
                    await self.record_item_collection(badge, source=V016_FACTIONS[faction_id]["name"], announce=True)
                elif threshold == 300:
                    self.server.db.add_item(self.account_id, "soul_elixir", 3)
                    await self.unlock_title(f"faction:{reward_key}", f"Mistrz: {V016_FACTIONS[faction_id]['name']}")
                    await self.send("Nagroda frakcji: Eliksir Duszy x3.")
            return new

    async def show_factions_v016(self, args=""):
            query = normalize_lookup_text(args)
            await self.send("FRAKCJE ŚWIATA")
            matched = False
            for faction_id, data in V016_FACTIONS.items():
                if query and query not in (normalize_lookup_text(faction_id), normalize_lookup_text(data["name"])) and query not in normalize_lookup_text(data["name"]):
                    continue
                matched = True
                rep = self.server.db.faction_reputation_v016(self.account_id, faction_id)
                await self.send(f"{data['name']}: {rep} pkt, ranga {v0160_faction_rank(rep)}. {data['desc']}")
            if query and not matched:
                await self.send("Nie rozpoznaję takiej frakcji.")

    async def show_world_bosses_v016(self):
            now = time.time()
            bosses = v0160_active_world_bosses(now)
            remaining = max(0, int(bosses[0]["expires_at"]-now)) if bosses else 0
            await self.send(f"WORLD BOSSY — rotacja za około {remaining} sekund.")
            for i, e in enumerate(bosses,1):
                template = MOB_TEMPLATES[e["template_id"]]
                await self.send(f"{i}. {template['name']}. {V013_FRONTIER_SPECS[e['kind']]['zone']}, sektor {e['x']+1}-{e['y']+1}.")
            await self.send("Wszystkie world bossy są pasywne. Walkę rozpoczyna wyłącznie gracz.")

    async def show_legendary_rares_v016(self):
            now = time.time()
            entries = v0160_active_legendary_rares(now)
            remaining = max(0, int(entries[0]["expires_at"]-now)) if entries else 0
            await self.send(f"LEGENDARY RARE — rotacja za około {remaining} sekund.")
            for i,e in enumerate(entries,1):
                template=MOB_TEMPLATES[e["template_id"]]
                await self.send(f"{i}. {template['name']}. Ostatni trop: {V013_FRONTIER_SPECS[e['kind']]['zone']}, sektor {e['x']+1}-{e['y']+1}. Może wędrować po zmaterializowanej części biomu.")
            await self.send("Legendary rare są pasywne i nie atakują pierwsze.")

    async def show_travelers_v016(self):
            await self.send("WĘDRUJĄCY NPC")
            for npc_id,data in V016_TRAVELERS.items():
                rid=v0160_traveler_room(npc_id)
                room=ROOMS.get(rid,{})
                await self.send(f"{data['name']}: {room.get('name', rid)}, strefa {room.get('zone','nieznana')}.")

    async def show_season_v018(self):
            season=v0180_season_state()
            remaining=max(0,int(season["expires_at"]-time.time()))
            await self.send(f"SEZON: {season['label']}. {season['desc']} Zmiana za około {remaining//60} minut.")
            await self.send("Sezon nie blokuje zawartości. Daje tylko małe premie ekologiczne do wybranych profesji.")

    async def show_expeditions_v018(self):
            await self.send("EKSPEDYCJE OCEANICZNE")
            discovered=self.server.db.discovered_room_ids(self.account_id)
            for key,data in V018_EXPEDITIONS.items():
                root=v0180_archipelago_room_id(key,0,0)
                state="odkryta" if root in discovered else "nieodkryta"
                await self.send(f"{key}: {data['name']}. Zalecana Biegłość {data['mastery']}. {state}. 16 sektorów.")
            await self.send("Wypłynięcie: ekspedycja <nazwa>. Start tylko z Portu Dusz lub Przystani Bractwa Wód.")

    async def start_expedition_v018(self, args=""):
            query=normalize_lookup_text(args)
            if self.combat_mob_key:
                await self.send("Nie możesz rozpocząć ekspedycji podczas walki."); return
            if self.character.room_id not in {"harbor","v016_waters_square"}:
                await self.send("Ekspedycje wypływają z Portu Dusz albo Nabrzeża Bractwa Wód."); return
            chosen=None
            for key,data in V018_EXPEDITIONS.items():
                if query in (normalize_lookup_text(key),normalize_lookup_text(data["name"])) or (query and query in normalize_lookup_text(data["name"])):
                    chosen=key; break
            if not chosen:
                await self.show_expeditions_v018(); return
            target=v0180_archipelago_room_id(chosen,0,0)
            self.server.world.ensure_runtime_room(target)
            old=self.character.room_id; self.previous_room_id=old; self.character.room_id=target
            self.server.db.save_character(self.character)
            await self.send(f"Wypływasz na ekspedycję: {V018_EXPEDITIONS[chosen]['name']}.")
            await self.look()

    async def handle_transport_v018(self, args=""):
            query=normalize_lookup_text(args)
            discovered=self.server.db.discovered_room_ids(self.account_id)
            if not query:
                await self.send("TRANSPORT — dostępne odkryte cele:")
                for key,rid in V018_TRANSPORT_HUBS.items():
                    if rid in discovered or rid in ("market","harbor","temple"):
                        await self.send(f"{key}: {ROOMS.get(rid,{}).get('name',rid)}")
                await self.send("Użycie: transport <cel>. Musisz stać w jednym z hubów transportowych.")
                return
            if self.combat_mob_key:
                await self.send("Nie możesz korzystać z transportu podczas walki."); return
            if self.character.room_id not in V018_TRANSPORT_ORIGINS:
                await self.send("Transport działa tylko z odkrytych hubów: miasta, osad frakcji i Bramy Rubieży Końca."); return
            chosen=None
            for key,rid in V018_TRANSPORT_HUBS.items():
                name=ROOMS.get(rid,{}).get("name",rid)
                if query in (normalize_lookup_text(key),normalize_lookup_text(name)) or (query and query in normalize_lookup_text(name)):
                    chosen=(key,rid); break
            if not chosen:
                await self.send("Nie rozpoznaję celu transportu. Wpisz transport bez argumentu."); return
            key,target=chosen
            if target not in discovered and target not in ("market","harbor","temple"):
                await self.send("Najpierw musisz odkryć ten hub normalną eksploracją."); return
            self.server.world.ensure_runtime_room(target)
            old=self.character.room_id; self.previous_room_id=old; self.character.room_id=target
            self.server.db.save_character(self.character)
            await self.send(f"Transport: docierasz do {ROOMS[target]['name']}.")
            await self.look()

    async def show_great_ruins_v018(self):
            ruins=v0180_all_great_ruins()
            discovered=self.server.db.discovered_room_ids(self.account_id)
            found=0
            for kind,x,y,size in ruins:
                if v0130_frontier_room_id(kind,x,y) in discovered:
                    found+=1
            await self.send(f"WIELKIE RUINY: {len(ruins)} możliwych kompleksów w świecie; odnalezione wejścia {found}.")
            await self.send("Każdy kompleks ma 20-40 pokoi, pętle i finałowego pasywnego strażnika. Brak pułapek.")

    async def show_legendary_events_v018(self):
            await self.send("LEGENDARNE WYDARZENIA ŚWIATA")
            for i,e in enumerate(v0180_active_legendary_events(),1):
                zone=V013_FRONTIER_SPECS[e["kind"]]["zone"]
                await self.send(f"{i}. {e['title']}. {zone}, sektor {e['x']+1}-{e['y']+1}. {e['desc']}")

    async def show_endless_v018(self):
            depth=v0180_endless_identity(self.character.room_id)
            if depth:
                await self.send(f"RUBIEŻ KOŃCA: sektor {depth}, pasmo trudności {v0180_endless_band(depth)}/{V018_ENDLESS_POWER_CAP_BAND}.")
            else:
                await self.send("RUBIEŻ KOŃCA: wejście znajduje się przy proceduralnej Bramie Korony. Prowadzenie: prowadź rubież końca.")
            await self.send("Mapa nie ma sztywnego końca, ale skalowanie walki ma twardy cap. PASSIVE WORLD i brak pułapek obowiązują wszędzie.")

    def v0210_total_ascension_rank(self):
            return sum(int(r["rank"] or 0) for r in self.server.db.ascension_rows_v021(self.account_id) if str(r["track"]).startswith("class:"))

    def v0210_any_class_at_400(self):
            row=self.server.db.conn.execute("SELECT MAX(level) AS mx FROM class_progress WHERE account_id=?",(self.account_id,)).fetchone()
            return int(row["mx"] or 0)>=400 if row else False

    async def show_ascension_v021(self,args=""):
            q=normalize_lookup_text(args); rows={str(r["track"]):r for r in self.server.db.ascension_rows_v021(self.account_id)}
            await self.send("WZNIESIENIE KLAS — po Biegłości 400, bez resetu")
            shown=0
            for cname,_,_,_ in CLASSES:
                if q and q not in normalize_lookup_text(cname): continue
                prow=self.server.db.class_progress_row(self.account_id,cname)
                level=int(prow["level"] if prow else 1)
                row=rows.get(f"class:{cname}"); rank=int(row["rank"] or 0) if row else 0; xp=int(row["xp"] or 0) if row else 0
                if level<400 and not q: continue
                nxt=v0210_ascension_xp_to_next(rank)
                await self.send(f"{cname}: Biegłość {level}/400; Wzniesienie {rank}/{V021_ASCENSION_MAX_RANK}; " + (f"XP {xp} z {nxt}." if nxt else "maksymalna Ranga Wzniesienia.")); shown+=1
            if not shown: await self.send("Żadna klasa nie osiągnęła jeszcze Biegłości 400.")
            await self.send(f"Łączna Ranga Wzniesienia: {self.v0210_total_ascension_rank()}.")

    async def handle_world_tier_v021(self,args=""):
            current=self.v0210_world_tier(); raw=str(args or "").strip()
            if not raw:
                m=v0210_world_tier_multipliers(current); total=self.v0210_total_ascension_rank()
                await self.send(f"WORLD TIER {current}/{V021_WORLD_TIER_MAX}. Efektywne HP przeciwników x{m['effective_hp']:.2f}, obrażenia x{m['enemy_damage']:.2f}, nagrody x{m['reward']:.2f}. Łączne Wzniesienie: {total}.")
                await self.send("Ustawienie: worldtier <1-10>. PASSIVE WORLD nadal obowiązuje."); return
            if self.combat_mob_key:
                await self.send("World Tier można zmienić tylko poza walką."); return
            if not raw.isdigit():
                await self.send("Użycie: worldtier <1-10>."); return
            tier=int(raw)
            if not 1<=tier<=V021_WORLD_TIER_MAX:
                await self.send("World Tier musi być od 1 do 10."); return
            if tier>=2 and not self.v0210_any_class_at_400():
                await self.send("World Tier 2+ wymaga co najmniej jednej klasy z Biegłością 400."); return
            need=V021_WORLD_TIER_ASCENSION_REQUIREMENT[tier]; total=self.v0210_total_ascension_rank()
            if total<need:
                await self.send(f"World Tier {tier} wymaga łącznej Rangi Wzniesienia {need}. Masz {total}."); return
            self.server.db.set_world_tier_v021(self.account_id,tier); m=v0210_world_tier_multipliers(tier)
            await self.send(f"Ustawiono World Tier {tier}. Efektywne HP x{m['effective_hp']:.2f}, obrażenia przeciwników x{m['enemy_damage']:.2f}, nagrody x{m['reward']:.2f}.")

    async def show_mythic_sets_v021(self,args=""):
            q=normalize_lookup_text(args); counts=self.v0210_mythic_set_counts(); shown=0
            await self.send("MITYCZNE ZESTAWY 8-CZĘŚCIOWE")
            for key,name in V021_MYTHIC_SET_NAMES.items():
                if q and q not in normalize_lookup_text(key) and q not in normalize_lookup_text(name): continue
                count=int(counts.get(key,0)); await self.send(f"{name}: {count}/13. Progi: 2 HP/Mana +6%; 4 obrażenia +6%; 6 obrona +8%; 8 dodatkowo +5% do wszystkich trzech."); shown+=1
            if not shown: await self.send("Nie rozpoznaję takiego mitycznego zestawu.")

    def v0210_live_endless_gauntlet_boss(self,room_id):
            self.server.world.refresh()
            return next((m for m in self.server.world.mobs.values() if m.alive and m.room_id==room_id and MOB_TEMPLATES.get(m.template_id,{}).get("v021_endless_gauntlet")),None)

    def v0210_endless_gauntlet_blocked(self,room_id,direction):
            return v0210_endless_gauntlet_identity(room_id) is not None and direction=="north" and self.v0210_live_endless_gauntlet_boss(room_id) is not None

    async def handle_endless_gauntlet_v021(self,args=""):
            best=self.server.db.endless_gauntlet_best_v021(self.account_id); raw=normalize_lookup_text(args)
            if raw in ("status","info"):
                await self.send(f"ENDLESS GAUNTLET: najlepsza ukończona runda {best}. Co 5 rund rośnie pasmo trudności; maksymalne pasmo 100."); return
            if self.character.room_id!=V020_GAUNTLET_LOBBY:
                await self.send("Endless Gauntlet rozpoczyna się w Sali Boss Gauntletów przy Straży Rubieży."); return
            start=max(1,best+1) if raw in ("dalej","continue","kontynuuj") else 1
            target=v0210_endless_gauntlet_room_id(start); self.server.world.ensure_runtime_room(target)
            self.previous_room_id=self.character.room_id; self.character.room_id=target; self.server.db.save_character(self.character)
            await self.send(f"Wchodzisz do Endless Gauntletu, runda {start}. Boss nie atakuje pierwszy."); await self.look()

    async def show_mythic_progression_v021(self):
            total=self.v0210_total_ascension_rank(); wt=self.v0210_world_tier(); best=self.server.db.endless_gauntlet_best_v021(self.account_id)
            t10=sum(1 for fid in V017_ARTIFACTS if v0200_artifact_owned_tier(self.server.db,self.account_id,fid)[0]>=10)
            full=sum(1 for key,count in self.v0210_mythic_set_counts().items() if count>=8)
            await self.send("MITYCZNA PROGRESJA v0.21")
            await self.send(f"Łączna Ranga Wzniesienia: {total}. World Tier: {wt}/10. Endless Gauntlet: najlepsza runda {best}. Artefakty Tier 10: {t10}/5. Sety mityczne z końcowym bonusem 8/13: {full}/5.")

    def v022_project_key(self, raw):
            q=normalize_lookup_text(raw)
            aliases={"port":"port","port dusz":"port","bridge":"bridge","most":"bridge","most polnocny":"bridge","tower":"tower","wieza":"tower","wieza kartografow":"tower","settlement":"settlement","osada":"settlement","osada konca swiata":"settlement"}
            if q in aliases: return aliases[q]
            for key,spec in V022_WORLD_PROJECTS.items():
                if q==key or q in normalize_lookup_text(spec["name"]): return key
            return None

    async def show_world_projects_v022(self, args=""):
            q=str(args or "").strip(); key=self.v022_project_key(q) if q else None
            if q and not key:
                await self.send("Nie rozpoznaję projektu. Dostępne: port, bridge, tower, settlement."); return
            keys=[key] if key else list(V022_WORLD_PROJECTS)
            await self.send("WORLD PROJECTS — wspólne, trwałe projekty całego serwera")
            for pkey in keys:
                spec=V022_WORLD_PROJECTS[pkey]; state=self.server.db.world_project_state_v022(pkey); contrib=self.server.db.world_project_contribution_v022(pkey,self.account_id)
                await self.send(f"{pkey}: {spec['name']}. {'UKOŃCZONY' if state['completed'] else 'w budowie'}. Twój wkład: {contrib['points']} pkt; wymagane do nagrody {spec['min_points']} pkt.")
                for cat,need in spec["requirements"].items():
                    have=min(int(need),int(state["progress"].get(cat,0) or 0)); label=V022_PROJECT_CATEGORY_LABELS[cat]
                    if cat=="coins": await self.send(f"  {label}: {currency_reading_text(have,0,0)} z {currency_reading_text(need,0,0)}.")
                    else: await self.send(f"  {label}: {have} z {need}.")
            await self.send("Użycie: projekt oddaj <projekt> <drewno|rudy|ryby|ziola> <ilość>; projekt wplac <projekt> <kwota> <nominał>; projekt odbierz <projekt>.")

    async def handle_world_project_v022(self,args=""):
            parts=str(args or "").strip().split()
            if not parts: await self.show_world_projects_v022(); return
            action=normalize_lookup_text(parts[0])
            if action not in ("oddaj","contribute","wplac","wpłać","deposit","odbierz","claim"):
                await self.show_world_projects_v022(" ".join(parts)); return
            if len(parts)<2:
                await self.send("Podaj projekt: port, bridge, tower albo settlement."); return
            key=self.v022_project_key(parts[1])
            if not key: await self.send("Nie rozpoznaję projektu."); return
            spec=V022_WORLD_PROJECTS[key]; state=self.server.db.world_project_state_v022(key)
            if action in ("odbierz","claim"):
                if not state["completed"]: await self.send("Ten projekt nie jest jeszcze ukończony."); return
                c=self.server.db.world_project_contribution_v022(key,self.account_id)
                if c["reward_claimed"]: await self.send("Nagroda za ten projekt została już odebrana."); return
                if c["points"]<int(spec["min_points"]): await self.send(f"Do nagrody potrzeba osobistego wkładu {spec['min_points']} pkt. Masz {c['points']}."); return
                if not self.server.db.mark_world_project_reward_claimed_v022(key,self.account_id): await self.send("Nagroda jest już odebrana."); return
                reward=v022_project_reward(key); [await self.send(_m) for _m in self.add_character_xp_with_event(reward["character_xp"])]; await self.grant_class_xp(reward["class_xp"]); await self.grant_soul_xp(reward["soul_xp"]); self.character.silver=min(CURRENCY_SQLITE_SAFE_TOTAL,self.character.silver+reward["coins"]); self.server.db.save_character(self.character)
                self.server.db.unlock_title(self.account_id,f"v022_project_{key}",spec["title"]); self.server.db.add_lifetime_stat(self.account_id,"world_projects_claimed",1)
                await self.send(f"Odbierasz nagrodę projektu {spec['name']}: {reward['class_xp']} Class XP, {reward['soul_xp']} Soul XP, {currency_reading_text(reward['coins'],0,0)} i tytuł {spec['title']}."); return
            if state["completed"]: await self.send("Projekt jest już ukończony."); return
            if action in ("wplac","wpłać","deposit"):
                if len(parts)<4 or not parts[2].isdigit(): await self.send("Użycie: projekt wplac <projekt> <kwota> <srebro|zloto|mithril>."); return
                amount=int(parts[2]); mult=currency_unit_multiplier(parts[3]);
                if amount<=0 or mult is None: await self.send("Nieprawidłowa kwota lub nominał."); return
                coins=amount*mult; remaining=max(0,int(spec["requirements"].get("coins",0))-int(state["progress"].get("coins",0) or 0)); coins=min(coins,remaining)
                wallet=legacy_currency_to_coins(self.character.silver,self.character.gold,self.character.mithril)
                if coins<=0: await self.send("Projekt nie potrzebuje już waluty."); return
                if wallet<coins: await self.send("Nie masz wystarczającej ilości waluty."); return
                wallet-=coins; self.character.silver=wallet; self.character.gold=0; self.character.mithril=0; self.server.db.save_character(self.character)
                pts=max(1,coins//1_000_000); result=self.server.db.add_world_project_contribution_v022(key,self.account_id,"coins",coins,pts)
                await self.send(f"Wpłacasz {currency_reading_text(result['accepted'],0,0)} na {spec['name']}. Twój wkład +{pts} pkt.")
            else:
                if len(parts)<4 or not parts[3].isdigit(): await self.send("Użycie: projekt oddaj <projekt> <drewno|rudy|ryby|ziola> <ilość>."); return
                cmap={"drewno":"wood","wood":"wood","rudy":"ore","ruda":"ore","ore":"ore","ryby":"fish","fish":"fish","ziola":"herbs","zioła":"herbs","herbs":"herbs"}; cat=cmap.get(normalize_lookup_text(parts[2])); amount=int(parts[3])
                if cat not in spec["requirements"]: await self.send("Ten projekt nie potrzebuje tego rodzaju zasobu."); return
                if amount<=0: await self.send("Ilość musi być dodatnia."); return
                container,get_ids=V022_PROJECT_RESOURCE_SOURCES[cat]; ids=tuple(get_ids()); remaining=max(0,int(spec["requirements"][cat])-int(state["progress"].get(cat,0) or 0)); amount=min(amount,remaining)
                have=self.server.db.total_items_across_storage_and_inventory(self.account_id,ids,container=container); take=min(amount,have)
                if take<=0: await self.send("Nie masz odpowiednich zasobów albo ten etap jest już wypełniony."); return
                if not self.server.db.consume_items_across_storage_and_inventory(self.account_id,ids,take,container=container): await self.send("Nie udało się przekazać zasobów."); return
                result=self.server.db.add_world_project_contribution_v022(key,self.account_id,cat,take,take); await self.send(f"Przekazujesz {take} sztuk: {V022_PROJECT_CATEGORY_LABELS[cat]}. Twój wkład +{take} pkt.")
            if result.get("newly_completed"):
                for ss in list(self.server.sessions):
                    if getattr(ss,"character",None): await ss.send(f"WORLD PROJECT UKOŃCZONY: {spec['name']}! Współtwórcy z wymaganym wkładem mogą użyć projekt odbierz {key}.")

    def generate_legendary_contracts_v022(self):
            stage=max(V027_LEGENDARY_MIN_MASTERY,self.highest_active_class_mastery()); kinds=list(V022_LEGENDARY_KINDS); random.shuffle(kinds); return [v022_legendary_contract_offer(k,stage) for k in kinds[:3]]

    def ensure_legendary_contracts_v022(self):
            state=self.server.db.legendary_contract_state_v022(self.account_id)
            if not state["offers"]:
                state["offers"]=self.generate_legendary_contracts_v022(); self.server.db.save_legendary_contract_state_v022(self.account_id,offers=state["offers"],active=state["active"],completed_count=state["completed_count"])
            return state

    async def show_legendary_contracts_v022(self):
            if self.highest_active_class_mastery()<V027_LEGENDARY_MIN_MASTERY: await self.send(f"Legendarne kontrakty odblokowują się przy wygenerowanej Biegłości {V027_LEGENDARY_MIN_MASTERY} dowolnej aktywnej klasy."); return
            state=self.ensure_legendary_contracts_v022(); await self.send(f"LEGENDARNE KONTRAKTY. Ukończone: {state['completed_count']}.")
            active=state["active"]
            if active: await self.send(f"Aktywny: {active['label']}. Postęp {int(active.get('progress',0))} z {active['needed']}. Nagrody: {active['reward_class_xp']} Class XP, {active['reward_soul_xp']} Soul XP, {currency_reading_text(active['reward_coins'],0,0)}.")
            else: await self.send("Aktywny: brak.")
            for i,o in enumerate(state["offers"],1): await self.send(f"{i}. {o['label']}. Start 0 z {o['needed']}. Nagrody: {o['reward_class_xp']} Class XP, {o['reward_soul_xp']} Soul XP, {currency_reading_text(o['reward_coins'],0,0)}.")

    async def handle_legendary_contracts_v022(self,args=""):
            if self.highest_active_class_mastery()<V027_LEGENDARY_MIN_MASTERY: await self.show_legendary_contracts_v022(); return
            raw=normalize_lookup_text(args); state=self.ensure_legendary_contracts_v022(); active=state["active"]
            if not raw or raw in ("lista","list","status","info"): await self.show_legendary_contracts_v022(); return
            if raw in ("aktywne","aktywny","active","postep","postęp"):
                if not active: await self.send("Brak aktywnego legendarnego kontraktu."); return
                await self.send(f"{active['label']}: {int(active.get('progress',0))} z {active['needed']}."); return
            if raw in ("odbierz","claim"):
                if not active or int(active.get('progress',0))<int(active.get('needed',1)): await self.send("Legendarny kontrakt nie jest gotowy do odebrania."); return
                [await self.send(_m) for _m in self.add_character_xp_with_event(int(active.get('reward_character_xp',0)))]; await self.grant_class_xp(int(active['reward_class_xp'])); await self.grant_soul_xp(int(active['reward_soul_xp'])); self.character.silver=min(CURRENCY_SQLITE_SAFE_TOTAL,self.character.silver+int(active['reward_coins'])); self.server.db.save_character(self.character)
                completed=state["completed_count"]+1; self.server.db.add_lifetime_stat(self.account_id,"legendary_contracts_completed",1); offers=self.generate_legendary_contracts_v022(); self.server.db.save_legendary_contract_state_v022(self.account_id,offers=offers,active={},completed_count=completed)
                await self.send(f"LEGENDARNY KONTRAKT UKOŃCZONY. Nagroda: {active['reward_class_xp']} Class XP, {active['reward_soul_xp']} Soul XP i {currency_reading_text(active['reward_coins'],0,0)}."); return
            if raw in ("odswiez","odśwież","refresh"):
                if active: await self.send("Nie można odświeżyć ofert przy aktywnym legendarnym kontrakcie."); return
                offers=self.generate_legendary_contracts_v022(); self.server.db.save_legendary_contract_state_v022(self.account_id,offers=offers,active={},completed_count=state["completed_count"]); await self.show_legendary_contracts_v022(); return
            txt=raw
            for pref in ("accept ","przyjmij ","wez ","weź "):
                if txt.startswith(pref): txt=txt[len(pref):].strip(); break
            if txt.isdigit():
                if active: await self.send("Masz już aktywny legendarny kontrakt."); return
                idx=int(txt)-1
                if not 0<=idx<len(state["offers"]): await self.send("Nie ma takiego numeru oferty."); return
                active=dict(state["offers"][idx]); active["progress"]=0; self.server.db.save_legendary_contract_state_v022(self.account_id,offers=state["offers"],active=active,completed_count=state["completed_count"]); await self.send(f"Przyjęto: {active['label']}. Postęp 0 z {active['needed']}."); return
            await self.send("Użycie: legendarycontracts accept <1-3>; aktywne; odbierz; odswiez.")

    async def advance_legendary_contract_v022(self,kind,amount=1):
            state=self.server.db.legendary_contract_state_v022(self.account_id); active=state["active"]
            if not active or str(active.get("kind"))!=str(kind): return False
            old=int(active.get("progress",0)); need=int(active.get("needed",1)); new=min(need,old+max(0,int(amount)))
            if new<=old: return False
            active["progress"]=new; self.server.db.save_legendary_contract_state_v022(self.account_id,offers=state["offers"],active=active,completed_count=state["completed_count"])
            await self.send(f"Legendarny kontrakt: {active['label']}. Postęp {new} z {need}." + (" Cel wykonany — użyj legendarycontracts odbierz." if new>=need else "")); return True

    async def show_fish_records_v022(self,args=""):
            q=str(args or "").strip()
            if q:
                candidates={fid:{"name":ITEMS.get(fid,{}).get("name",fid)} for fid in FISH_RESOURCE_IDS if fid in ITEMS}; found=find_by_name(candidates,q)
                if not found: await self.send("Nie znam takiego gatunku ryby."); return
                fid,fish=found; personal=self.server.db.fish_journal_entry(self.account_id,fid); glob=self.server.db.fish_global_record_v022(fid)
                await self.send(f"REKORD GATUNKU: {fish['name']} — rzadkość {fish_rarity_label(fid)}.")
                if personal: await self.send(f"Twój rekord: {format_fish_length(personal['best_length_mm'])}, {format_fish_weight(personal['best_weight_g'])}.")
                else: await self.send("Twój rekord: brak połowu tego gatunku.")
                if glob: await self.send(f"Rekord serwera długości: {format_fish_length(glob['best_length_mm'])} — {glob['length_holder']}. Rekord masy: {format_fish_weight(glob['best_weight_g'])} — {glob['weight_holder']}.")
                else: await self.send("Rekord serwera: brak.")
                return
            rows=self.server.db.fish_journal_rows(self.account_id); await self.send("FISHING RECORDS 2.0")
            if rows:
                longest=max(rows,key=lambda r:int(r['best_length_mm'] or 0)); heaviest=max(rows,key=lambda r:int(r['best_weight_g'] or 0)); rarest=max(rows,key=lambda r:(v022_fish_rarity_score(str(r['fish_id'])),int(r['best_weight_g'] or 0)))
                await self.send(f"Twój najdłuższy okaz: {ITEMS.get(longest['fish_id'],{}).get('name',longest['fish_id'])}, {format_fish_length(longest['best_length_mm'])}.")
                await self.send(f"Twój najcięższy okaz: {ITEMS.get(heaviest['fish_id'],{}).get('name',heaviest['fish_id'])}, {format_fish_weight(heaviest['best_weight_g'])}.")
                await self.send(f"Twój najrzadszy odkryty gatunek: {ITEMS.get(rarest['fish_id'],{}).get('name',rarest['fish_id'])}, {fish_rarity_label(rarest['fish_id'])}.")
            else: await self.send("Nie masz jeszcze zapisanych połowów.")
            personal_rare=self.server.db.fish_rarest_personal_v022(self.account_id)
            if personal_rare: await self.send(f"Twój najrzadszy okaz: {ITEMS.get(personal_rare['item_id'],ITEMS.get(personal_rare['fish_id'],{})).get('name',personal_rare['fish_id'])}; {personal_rare['rarity_label']}; {format_fish_weight(personal_rare['weight_g'])}.")
            rare=self.server.db.fish_rarest_global_v022()
            if rare: await self.send(f"Najrzadszy okaz serwera: {ITEMS.get(rare['item_id'],ITEMS.get(rare['fish_id'],{})).get('name',rare['fish_id'])}; {rare['rarity_label']}; {format_fish_weight(rare['weight_g'])}; złowił {rare['holder_name']}.")
            top=self.server.db.fish_global_top_v022(5)
            if top:
                await self.send("Najcięższe rekordy gatunków na serwerze:")
                for i,row in enumerate(top,1): await self.send(f"{i}. {ITEMS.get(row['fish_id'],{}).get('name',row['fish_id'])}: {format_fish_weight(row['best_weight_g'])} — {row['weight_holder']}.")
            await self.send("Szczegóły gatunku: rekordyryb <nazwa ryby>.")

    def v0200_live_blocking_boss(self, room_id, *, mega=False, gauntlet=False):
            self.server.world.refresh()
            for mob in self.server.world.mobs.values():
                if not mob.alive or mob.room_id != room_id: continue
                t=MOB_TEMPLATES.get(mob.template_id,{})
                if mega and t.get("v020_megadungeon_boss"): return mob
                if gauntlet and t.get("v020_gauntlet"): return mob
            return None

    def v0200_megadungeon_blocked(self, room_id, direction):
            ident=v0200_mega_identity(room_id)
            if not ident: return False
            key,index=ident
            if direction != "north" or not v0200_mega_is_boss_index(key,index): return False
            target=ROOMS.get(room_id,{}).get("exits",{}).get(direction); target_ident=v0200_mega_identity(target)
            if not target_ident or target_ident[1] <= index: return False
            dungeon_kind=f"v020_mega_{key}"
            if self.server.db.boss_floor_cleared(self.account_id,dungeon_kind,index): return False
            return self.v0200_live_blocking_boss(room_id,mega=True) is not None

    def v0200_gauntlet_blocked(self, room_id, direction):
            room=ROOMS.get(room_id,{})
            if not room.get("v020_gauntlet") or direction != "north": return False
            return self.v0200_live_blocking_boss(room_id,gauntlet=True) is not None

    async def show_megadungeons_v020(self):
            await self.send("MEGALOCHY ENDGAME")
            discovered=self.server.db.discovered_room_ids(self.account_id)
            for key,spec in V020_MEGADUNGEONS.items():
                gate=v0200_mega_gate_id(key); state="odkryty" if gate in discovered else "nieodkryty"
                clears=self.server.db.highest_boss_floor_cleared(self.account_id,f"v020_mega_{key}")
                await self.send(f"{key}: {spec['name']}. {spec['size']} pokoi; start Biegłość około {spec['stage']}; {state}; najwyższy zaliczony próg {clears}.")
            await self.send("Boss co 25 pokoi blokuje tylko dalszą sekcję przy pierwszym zaliczeniu. Brak pułapek.")

    async def show_gauntlets_v020(self):
            await self.send("BOSS GAUNTLETY")
            clears=self.server.db.collection_entry_ids(self.account_id,"gauntlet_clears_v020")
            for key,data in V020_GAUNTLETS.items():
                await self.send(f"{key}: {data['name']}. 5 rund, etapy {data['stages'][0]}-{data['stages'][-1]}. Finał zaliczony: {'tak' if key in clears else 'nie'}.")
            await self.send("Wejdź do Sali Boss Gauntletów przy Straży Rubieży i użyj: gauntlet <nazwa>.")

    async def start_gauntlet_v020(self,args=""):
            if self.character.room_id != V020_GAUNTLET_LOBBY:
                await self.send("Boss gauntlet rozpoczyna się wyłącznie w Sali Boss Gauntletów przy Straży Rubieży."); return
            q=normalize_lookup_text(args); chosen=None
            for key,data in V020_GAUNTLETS.items():
                if q in (normalize_lookup_text(key),normalize_lookup_text(data['name'])) or (q and q in normalize_lookup_text(data['name'])): chosen=key; break
            if not chosen: await self.show_gauntlets_v020(); return
            target=f"v020_gauntlet_{chosen}_1"; self.previous_room_id=self.character.room_id; self.character.room_id=target; self.server.db.save_character(self.character)
            await self.send(f"Rozpoczynasz: {V020_GAUNTLETS[chosen]['name']}. Boss nie zaatakuje pierwszy."); await self.look()

    async def show_mythic_bosses_v020(self):
            now=time.time(); entries=v0200_active_mythic_world_bosses(now); remaining=max(0,int(entries[0]['expires_at']-now)) if entries else 0
            await self.send(f"MITYCZNE WORLD BOSSY — rotacja za około {remaining//60} minut.")
            for i,e in enumerate(entries,1):
                await self.send(f"{i}. {MOB_TEMPLATES[e['template_id']]['name']}. {V013_FRONTIER_SPECS[e['kind']]['zone']}, sektor {e['x']+1}-{e['y']+1}.")
            await self.send("Wszystkie są pasywne. Dają mityczne materiały endgame.")

    async def artifact_upgrade_v020(self,args=""):
            query=normalize_lookup_text(args)
            candidates=[]
            for fid,data in V017_ARTIFACTS.items():
                tier,item_id=v0200_artifact_owned_tier(self.server.db,self.account_id,fid)
                if tier:
                    candidates.append((fid,data,tier,item_id))
            if not query:
                await self.send("ROZWÓJ ARTEFAKTÓW")
                if not candidates: await self.send("Nie posiadasz jeszcze artefaktu frakcyjnego."); return
                for fid,data,tier,item_id in candidates:
                    await self.send(f"{data['name']}: poziom {tier}/{V020_ARTIFACT_MAX_TIER}. " + ("Maksymalny." if tier>=V020_ARTIFACT_MAX_TIER else "Użyj ulepszartefakt <nazwa>."))
                return
            chosen=None
            for row in candidates:
                fid,data,tier,item_id=row
                if query in normalize_lookup_text(data['name']) or query in normalize_lookup_text(fid): chosen=row; break
            if not chosen:
                await self.send("Nie znajduję posiadanego artefaktu o tej nazwie."); return
            fid,data,tier,item_id=chosen
            if tier>=V020_ARTIFACT_MAX_TIER: await self.send(f"Ten artefakt ma już maksymalny poziom {V020_ARTIFACT_MAX_TIER}."); return
            if any(row["item_id"] == item_id for row in self.equipped_item_rows()):
                await self.send("Najpierw zdejmij artefakt. Ulepszanie nie zmienia założonego przedmiotu w locie."); return
            next_tier=tier+1; req=V020_ARTIFACT_UPGRADE_COSTS[next_tier]; missing=[]
            for iid,qty in req.items():
                if iid=="coins": continue
                have=self.server.db.item_qty(self.account_id,iid)
                if have<qty: missing.append(f"{ITEMS[iid]['name']} {have}/{qty}")
            coins=int(req.get("coins",0)); wallet=self.character_wallet_silver_value()
            if wallet<coins: missing.append(f"waluta {currency_reading_text(wallet,0,0)} / {currency_reading_text(coins,0,0)}")
            if missing:
                await self.send("Brakuje: "+"; ".join(missing)+"."); return
            # Nie ma RNG/faila: dopiero po pełnej walidacji pobieramy koszt i zamieniamy przedmiot.
            for iid,qty in req.items():
                if iid!="coins": self.server.db.remove_item(self.account_id,iid,qty)
            self.character.silver=wallet-coins; self.character.gold=0; self.character.mithril=0
            self.server.db.remove_item(self.account_id,item_id,1)
            new_item=V020_ARTIFACT_VARIANTS[fid][next_tier-1]; self.server.db.add_item(self.account_id,new_item,1); self.server.db.save_character(self.character)
            await self.record_item_collection(new_item,source="Rozwój artefaktu",announce=True)
            await self.send(f"Artefakt rozwinięty bez ryzyka: {ITEMS[new_item]['name']}. Koszt waluty: {currency_reading_text(coins,0,0)}.")

    async def show_endgame_goals_v020(self):
            mega=len(self.server.db.collection_entry_ids(self.account_id,"mega_boss_kills_v020"))
            gaunt=int(self.server.db.collection_entry_ids(self.account_id,"gauntlet_final_kills_v020") and len(self.server.db.collection_entry_ids(self.account_id,"gauntlet_final_kills_v020")) or 0)
            mythic=len(self.server.db.collection_entry_ids(self.account_id,"mythic_world_kills_v020"))
            t5=sum(1 for fid in V017_ARTIFACTS if v0200_artifact_owned_tier(self.server.db,self.account_id,fid)[0]>=5)
            vals={"mega_bosses":mega,"gauntlet_finals":gaunt,"mythic_world":mythic,"artifact_t5":t5}
            await self.send("DŁUGOTERMINOWE CELE ENDGAME")
            for key,need,label in V020_ENDGAME_GOALS: await self.send(f"{label}: {min(vals[key],need)} z {need}.")

    async def show_artifacts_v017(self):
            await self.send("ARTEFAKTY FRAKCYJNE")
            discovered = self.server.db.collection_entry_ids(self.account_id, "unique")
            for faction_id, data in V017_ARTIFACTS.items():
                item_id = data["item_id"]
                owned = self.server.db.item_qty(self.account_id, item_id) > 0 or item_id in discovered
                equipped = any(row["item_id"] == item_id for row in self.equipped_item_rows())
                state = "założony" if equipped else ("odkryty" if owned else "nieodkryty")
                await self.send(f"{data['name']} — {V016_FACTIONS[faction_id]['name']}. {state}. {data['effect']}")

    async def show_biome_sets_v017(self, args=""):
            query = normalize_lookup_text(args)
            counts = self.regional_set_counts()
            await self.send("ZESTAWY BIOMOWE")
            shown = 0
            for kind, name in V017_BIOME_SET_NAMES.items():
                if query and query not in normalize_lookup_text(kind) and query not in normalize_lookup_text(name) and query not in normalize_lookup_text(V013_FRONTIER_SPECS[kind]["zone"]):
                    continue
                sid = f"v017_{kind}"
                count = int(counts.get(sid, 0))
                cfg = REGIONAL_SET_BONUSES[sid]
                await self.send(
                    f"{name}: {count}/6 założonych. Biom: {V013_FRONTIER_SPECS[kind]['zone']}. "
                    f"2/6 HP/Mana +{int(round((cfg['hp']-1)*100))}%, "
                    f"4/6 obrażenia +{int(round((cfg['damage']-1)*100))}%, "
                    f"6/6 obrona +{int(round((cfg['defense']-1)*100))}%."
                )
                shown += 1
            if not shown:
                await self.send("Nie rozpoznaję takiego zestawu biomowego.")

    async def show_faction_stories_v017(self, args=""):
            query = normalize_lookup_text(args)
            rows = {row["quest_id"]: row for row in self.server.db.quest_rows(self.account_id)}
            await self.send("HISTORIE FRAKCJI")
            shown = 0
            for faction_id, chain in V017_FACTION_STORY_QUESTS.items():
                faction_name = V016_FACTIONS[faction_id]["name"]
                title = V017_FACTION_STORIES[faction_id]["title"]
                if query and query not in normalize_lookup_text(faction_id) and query not in normalize_lookup_text(faction_name) and query not in normalize_lookup_text(title):
                    continue
                completed = sum(1 for qid in chain if rows.get(qid, {}).get("status") == "completed")
                active = [qid for qid in chain if rows.get(qid, {}).get("status") == "active"]
                state = f"ukończone {completed}/6"
                if active:
                    qid = active[0]
                    row = rows[qid]
                    state += f", aktywny: {QUESTS[qid]['name']} {row['progress']}/{QUESTS[qid]['needed']}"
                elif completed == 6:
                    state += ", historia zakończona"
                await self.send(f"{faction_name} — {title}: {state}.")
                shown += 1
            if not shown:
                await self.send("Nie rozpoznaję takiej historii frakcji.")

    async def show_dynamic_events_v029(self):
            now = time.time()
            events = v0290_active_world_events(now)
            remaining = max(0, int(events[0]["expires_at"] - now)) if events else 0
            await self.send(f"DYNAMICZNE EVENTY v0.29 — rotacja za około {remaining} sekund.")
            if not events:
                await self.send("Brak aktywnych eventów.")
                return
            for number, event in enumerate(events, 1):
                room = ROOMS.get(event["room_id"], {})
                await self.send(
                    f"{number}. {event['title']}. {room.get('name', event['room_id'])}. "
                    f"Etap {event['stage']}. Ranga {event['rank']}. Liczba przeciwników {event['count']}."
                )
            await self.send("Wszystkie wygenerowane eventy są pasywne do chwili ataku.")

    async def show_nemesis_v029(self):
            row = self.server.db.nemesis_row_v029(self.account_id)
            if not row:
                await self.send("Nie masz jeszcze Nemesis. Przeciwnik może nim zostać, jeśli pokona cię w walce.")
                return
            if not int(row["active"] or 0):
                await self.send(
                    f"Ostatni Nemesis został pokonany. Łącznie pokonane Nemesis: {int(row['defeats'] or 0)}. "
                    "Nowy może powstać przy kolejnej porażce z przeciwnikiem."
                )
                return
            room_id = str(row["room_id"])
            self.server.world.ensure_runtime_room(room_id)
            room_name = ROOMS.get(room_id, {}).get("name", room_id)
            await self.send(
                f"NEMESIS: {row['nemesis_name']}. Ranga {int(row['rank'])}. Etap {int(row['level'])}. "
                f"Pokonał cię {int(row['kills_player'])} razy. Lokalizacja: {room_name}."
            )
            if str(self.character.room_id) == room_id:
                self.server.world.ensure_v029_nemesis(row)
                await self.send("Nemesis jest tutaj.")
                return
            path = self.shortest_path(self.character.room_id, room_id)
            if path:
                first = path[0] if path else None
                if first:
                    direction, next_room = first
                    await self.send(
                        f"Trasa ma {len(path)} kroków. Pierwszy kierunek: {self.route_direction_name(direction)} "
                        f"do {ROOMS.get(next_room, {}).get('name', next_room)}."
                    )
            else:
                await self.send("Cel istnieje, ale jego dynamiczna trasa nie jest jeszcze zmaterializowana. Wejdź ponownie do regionu i użyj nemesis.")

    async def show_world_events(self):
            await self.show_double_xp_event()
            now = time.time()
            events = v0140_active_world_events(now)
            remaining = max(0, int(events[0]["expires_at"] - now)) if events else 0
            await self.send(f"WYDARZENIA ŚWIATA — następna rotacja za około {remaining} sekund.")
            for number, event in enumerate(events, 1):
                zone = V013_FRONTIER_SPECS[event["kind"]]["zone"]
                await self.send(
                    f"{number}. {event['title']}. {zone}, sektor {event['x']+1}-{event['y']+1}. {event['desc']}"
                )
            await self.send("Wszystkie eventy są opcjonalne. Żaden mob nie zaczyna walki sam.")
            await self.show_dynamic_events_v029()

    def v0140_treasure_map_target(self):
            discovered = self.server.db.collection_entry_ids(self.account_id, "surface_secrets_v0140")
            known = self.server.db.collection_entry_ids(self.account_id, "treasure_targets_v0140")
            identity = v0130_frontier_room_identity(self.character.room_id) if self.character else None
            preferred_kind = identity[0] if identity else None
            candidates = [rid for rid in v0140_surface_secret_room_ids(preferred_kind) if rid not in discovered and rid not in known]
            if not candidates:
                candidates = [rid for rid in v0140_surface_secret_room_ids() if rid not in discovered and rid not in known]
            if not candidates:
                return None
            seed = _v0140_hash_int("map-target", self.account_id, len(known), self.character.name if self.character else "")
            return candidates[seed % len(candidates)]

    async def use_v0140_treasure_map(self, item_id):
            target = self.v0140_treasure_map_target()
            if not target:
                await self.send("Mapa nie znajduje już żadnego nieodkrytego sekretu proceduralnych rubieży.")
                return False
            if not self.server.db.remove_item(self.account_id, item_id, 1):
                await self.send("Nie masz tej mapy skarbu.")
                return False
            self.server.db.add_collection_entry(self.account_id, "treasure_targets_v0140", target)
            item = ITEMS.get(item_id, {})
            quest_id = item.get("quest_treasure_map_for")
            if quest_id:
                row = self.server.db.quest(self.account_id, quest_id)
                if row and row["status"] == "active":
                    self.server.db.add_collection_entry(
                        self.account_id, "quest_treasure_targets_v0243", f"{quest_id}|{target}"
                    )
            # v0.24.3: samo użycie mapy przygotowuje bezpieczny korytarz nawigacyjny.
            # Dzięki temu `prowadz skarb` nie wskazuje celu, do którego graf tras jeszcze nie istnieje.
            route_ready = self.materialize_frontier_route_v024(target)
            info = v0140_surface_secret_info(target)
            zone = V013_FRONTIER_SPECS[info["kind"]]["zone"]
            await self.send(
                f"Odczytujesz {item.get('name', 'Mapę Skarbu Rubieży')}. Trop zapisany: {zone}, sektor {info['x']+1}-{info['y']+1}. "
                + ("Trasa została przygotowana. Wpisz prowadz skarb. " if route_ready else "Wpisz mapa skarbu i spróbuj ponownie przygotować trasę. ")
                + "Po dotarciu użyj sekret / secret."
            )
            return True

    async def show_v0140_treasure_targets(self):
            targets = sorted(self.server.db.collection_entry_ids(self.account_id, "treasure_targets_v0140"))
            discovered = self.server.db.collection_entry_ids(self.account_id, "surface_secrets_v0140")
            active = [rid for rid in targets if rid not in discovered and v0140_surface_secret_info(rid)]
            await self.send(f"MAPY SKARBÓW: aktywne tropy {len(active)}, rozwiązane {len(targets)-len(active)}.")
            if not active:
                await self.send("Brak aktywnego tropu. Mapy Skarbu Rubieży wypadają m.in. z rare i skrzyń mini-lochów.")
                return
            for number, rid in enumerate(active, 1):
                info = v0140_surface_secret_info(rid)
                zone = V013_FRONTIER_SPECS[info["kind"]]["zone"]
                await self.send(f"{number}. {zone}, sektor {info['x']+1}-{info['y']+1}. Użyj sekret w tym sektorze.")

    def materialize_frontier_route_v024(self, room_id):
            """Materializuje tylko bezpieczny korytarz od bramy biomu do celu.

            Proceduralne sektory normalnie powstają dopiero przy wejściu. Nawigacja
            do aktywnego tropu mapy potrzebuje jednak skończonego grafu trasy.
            Tworzymy więc tylko prostą trasę 0,0 -> x,0 -> x,y, a nie cały biom.
            """
            identity = v0130_frontier_room_identity(room_id)
            if identity is None:
                return self.server.world.ensure_runtime_room(room_id)
            kind, target_x, target_y = identity
            coords = [(0, 0)]
            coords.extend((x, 0) for x in range(1, target_x + 1))
            coords.extend((target_x, y) for y in range(1, target_y + 1))
            for x, y in coords:
                if not self.server.world.ensure_runtime_room(
                    v0130_frontier_room_id(kind, x, y)
                ):
                    return False
            return room_id in ROOMS

    def active_treasure_targets_v024(self):
            targets = sorted(
                self.server.db.collection_entry_ids(
                    self.account_id, "treasure_targets_v0140"
                )
            )
            discovered = self.server.db.collection_entry_ids(
                self.account_id, "surface_secrets_v0140"
            )
            return [
                rid for rid in targets
                if rid not in discovered and v0140_surface_secret_info(rid)
            ]

    async def show_cartography_v024(self):
            discovered_rooms = self.server.db.discovered_room_ids(self.account_id)
            frontier_rooms = tuple(
                rid
                for kind in V013_FRONTIER_SPECS
                for rid in v0130_frontier_room_ids(kind)
            )
            frontier_known = sum(1 for rid in frontier_rooms if rid in discovered_rooms)
            secrets = self.server.db.collection_entry_ids(
                self.account_id, "surface_secrets_v0140"
            )
            mini = self.server.db.collection_entry_ids(
                self.account_id, "mini_dungeons_v015"
            )
            events = self.server.db.collection_entry_ids(
                self.account_id, "world_events_v0140"
            )
            all_targets = self.server.db.collection_entry_ids(
                self.account_id, "treasure_targets_v0140"
            )
            active = self.active_treasure_targets_v024()
            solved = max(0, len(all_targets) - len(active))
            await self.send("KARTOGRAFIA")
            await self.send(
                f"Rubieże: odkryto {frontier_known} z {len(frontier_rooms)} sektorów. "
                f"Sekrety: {len(secrets)}. Mini-lochy ukończone: {len(mini)}. "
                f"Wydarzenia odwiedzone: {len(events)}."
            )
            await self.send(
                f"Mapy skarbów: aktywne tropy {len(active)}, rozwiązane {solved}."
            )
            if active:
                for number, rid in enumerate(active, 1):
                    info = v0140_surface_secret_info(rid)
                    zone = V013_FRONTIER_SPECS[info["kind"]]["zone"]
                    await self.send(
                        f"Trop {number}: {zone}, sektor {info['x']+1}-{info['y']+1}. "
                        f"Prowadzenie: prowadz skarb {number}."
                    )
            else:
                await self.send(
                    "Brak aktywnego tropu. Użyj Mapy Skarbu Rubieży, aby zapisać nowy cel."
                )

            eren_chain = tuple(NPCS.get("cartographer_eren", {}).get("quest_chain") or ())
            if eren_chain:
                completed = 0
                active_names = []
                for qid in eren_chain:
                    row = self.server.db.quest(self.account_id, qid)
                    if row and (row["status"] == "completed" or int(row["completion_count"] or 0) > 0):
                        completed += 1
                    if row and row["status"] == "active":
                        active_names.append(QUESTS[qid]["name"])
                await self.send(
                    f"Łańcuch Erena: ukończone {completed}/{len(eren_chain)}."
                )
                if active_names:
                    await self.send("Aktywne u Erena: " + "; ".join(active_names) + ".")
            await self.send(
                "Komendy: mapa skarbu, prowadz skarb [numer], quest list Eren, help kartografia."
            )

    async def discover_room(self, room_id, announce=True):
            if room_id not in ROOMS:
                return False

            # v0.9.21: instancje mają niezależną, nieskończoną mapę sektorów po 100 pięter.
            instance_kind, instance_floor = instance_room_identity(room_id)
            if instance_kind and instance_floor is not None:
                instance_new = self.server.db.mark_instance_floor_visited(
                    self.account_id, instance_kind, instance_floor
                )
                info = INSTANCE_MAP_DEFS.get(instance_kind, {})
                if info.get("passive_checkpoints") and instance_floor % 10 == 0:
                    self.server.db.mark_instance_checkpoint(
                        self.account_id, instance_kind, instance_floor
                    )
                if instance_new and instance_secret_index(instance_kind, instance_floor) is not None:
                    if announce:
                        await self.send(
                            "Mapa instancji: wyczuwasz tutaj ukryty ślad. "
                            "Użyj sekret / secret, aby go zbadać."
                        )

            is_new = self.server.db.mark_room_discovered(
                self.account_id, room_id
            )
            if not is_new:
                return False

            self.server.db.add_lifetime_stat(self.account_id, "rooms_discovered", 1)
            room_meta = ROOMS[room_id]
            if room_meta.get("v018_archipelago"):
                self.server.db.add_collection_entry(self.account_id, "archipelago_sectors_v018", room_id)
            if room_meta.get("v018_ruin_final"):
                self.server.db.add_collection_entry(self.account_id, "great_ruins_v018", room_meta.get("v018_ruin_parent", room_id))
            if room_meta.get("v018_endless"):
                self.server.db.add_lifetime_stat(self.account_id, "endless_sectors_discovered", 1)
            if room_meta.get("procedural_surface"):
                biome_kind_v015 = room_meta.get("procedural_biome", "any")
                await self.advance_v0140_quest_progress(
                    "explore_frontier", biome_kind_v015, 1
                )
                await self.advance_bounty("explore", biome_kind_v015, 1)
                await self.advance_legendary_contract_v022("explore", 1)
                await self.advance_dynamic_world_quest_v015("explore", biome_kind_v015, 1)
                await self.check_biome_mastery_v015(biome_kind_v015)
                await self.add_faction_reputation_v016("cartographers", 1, reason="exploration")
            if room_meta.get("v0140_mini_final"):
                mini_kind_v015 = room_meta.get("v0140_mini_kind", "any")
                await self.advance_v0140_quest_progress(
                    "mini_dungeon", mini_kind_v015, 1
                )
                await self.advance_bounty("mini", mini_kind_v015, 1)
                await self.advance_dynamic_world_quest_v015("mini", mini_kind_v015, 1)
                self.server.db.add_collection_entry(self.account_id, "mini_dungeons_v015", str(room_id))
            zone = room_meta["zone"]
            zone_rooms = EXPLORATION_ZONE_ROOMS.get(zone, ())
            discovered = self.server.db.discovered_room_ids(self.account_id)
            current = sum(1 for rid in zone_rooms if rid in discovered)
            total = max(1, len(zone_rooms))
            old_count = max(0, current - 1)
            old_pct = int(old_count * 100 / total)
            pct = int(current * 100 / total)

            if announce and len(zone_rooms) >= EXPLORATION_ZONE_MIN_ROOMS:
                milestones = (25, 50, 75, 100)
                crossed = [m for m in milestones if old_pct < m <= pct]
                if crossed:
                    await self.send(
                        f"Eksploracja: {zone} {pct}% odkryta."
                    )

            await self.set_achievement_progress(
                "exploration_rooms",
                len(discovered.intersection(ALL_EXPLORATION_ROOMS)),
            )

            if (
                zone in TRACKED_EXPLORATION_ZONES
                and current >= total
                and self.server.db.claim_exploration_reward(self.account_id, zone)
            ):
                await self.complete_zone_exploration(zone, total)
            return True

    async def discover_current_room(self, announce=True):
            return await self.discover_room(
                self.character.room_id, announce=announce
            )

    async def complete_zone_exploration(self, zone, room_count):
            title_name = _zone_title(zone)
            reward_item = EXPLORATION_REWARD_ITEMS[zone]
            soul_xp = max(250, min(5000, room_count * 50))
            silver = max(500, room_count * 100)
            gold = max(1, room_count // 10)

            await self.send(f"Eksploracja ukończona: {zone}, 100 procent.")
            await self.grant_soul_xp(soul_xp)
            self.character.silver += silver
            self.character.gold += gold
            self.server.db.add_item(self.account_id, reward_item, 1)
            self.server.db.save_character(self.character)
            await self.send(
                "Nagroda eksploracyjna: "
                + currency_reading_text(silver, gold, 0) + "."
            )
            await self.send(
                f"Unikalny przedmiot: {ITEMS[reward_item]['name']}."
            )
            await self.unlock_title(
                f"zone:{_collection_slug(zone)}", title_name
            )
            achievement_id = f"exploration100:{_collection_slug(zone)}"
            if self.server.db.unlock_achievement(
                self.account_id,
                achievement_id,
                f"100% eksploracji: {zone}",
                "Gold",
            ):
                await self.send(
                    f"Osiągnięcie: 100% eksploracji: {zone}, Gold."
                )

    def exploration_percent(self, zone):
            room_ids = EXPLORATION_ZONE_ROOMS.get(zone, ())
            if not room_ids:
                return 0, 0, 0
            discovered = self.server.db.discovered_room_ids(self.account_id)
            count = sum(1 for rid in room_ids if rid in discovered)
            return count, len(room_ids), int(count * 100 / len(room_ids))

    async def show_exploration(self, args=""):
            raw = str(args or "").strip()
            norm = normalize_lookup_text(raw)
            discovered = self.server.db.discovered_room_ids(self.account_id)
            world_count = sum(1 for rid in ALL_EXPLORATION_ROOMS if rid in discovered)
            world_pct = int(world_count * 100 / max(1, len(ALL_EXPLORATION_ROOMS)))

            if norm in ("all", "wszystko", "lista", "list"):
                await self.send(
                    f"EKSPLORACJA ŚWIATA: {world_count} z {len(ALL_EXPLORATION_ROOMS)}, {world_pct}%."
                )
                for zone in sorted(TRACKED_EXPLORATION_ZONES, key=normalize_lookup_text):
                    count, total, pct = self.exploration_percent(zone)
                    await self.send(f"{zone}: {count} z {total}, {pct}%.")
                return

            zone = ROOMS[self.character.room_id]["zone"]
            if raw and norm not in ("region", "strefa", "world", "swiat"):
                candidates = {
                    z: {"name": z} for z in EXPLORATION_ZONE_ROOMS
                }
                found = find_by_name(candidates, raw)
                if not found:
                    await self.send("Nie rozpoznaję takiej strefy eksploracji.")
                    return
                zone = found[0]
            count, total, pct = self.exploration_percent(zone)
            await self.send(f"{zone}: {pct}% odkryta. {count} z {total} lokacji.")
            await self.send(
                f"Cały świat: {world_pct}% odkryty. {world_count} z {len(ALL_EXPLORATION_ROOMS)} lokacji."
            )

    async def show_region_progress(self, zone=None):
            zone = zone or ROOMS[self.character.room_id]["zone"]
            count, total, pct = self.exploration_percent(zone)
            await self.send(f"{zone}: eksploracja {pct}%, {count} z {total} lokacji.")
            region = REGION_COLLECTION_ENTRIES.get(zone, {})
            for category in ("bosses", "rare", "chests", "named"):
                total_ids = set(region.get(category, set()))
                if not total_ids:
                    continue
                found_ids = self.server.db.collection_entry_ids(
                    self.account_id, category
                )
                found_count = len(total_ids.intersection(found_ids))
                label = COLLECTION_CATEGORY_LABELS[category]
                await self.send(
                    f"{label}: {found_count} z {len(total_ids)}."
                )

    async def show_progress(self, args=""):
            norm = normalize_lookup_text(args)
            if norm in ("region", "strefa", "region progress", "regionprogress"):
                await self.show_region_progress()
                return
            await self.show_exploration("")
            achievement_count = len(self.server.db.achievement_rows(self.account_id))
            await self.sync_collection_from_inventory()
            discovered_total = sum(
                len(self.server.db.collection_entry_ids(self.account_id, category))
                for category in COLLECTION_CATALOGS
            )
            catalog_total = sum(len(catalog) for catalog in COLLECTION_CATALOGS.values())
            collection_pct = int(discovered_total * 100 / max(1, catalog_total))
            await self.send(
                f"Collection Codex: {discovered_total} z {catalog_total}, {collection_pct}%."
            )
            await self.v0260_sync_museum()
            _mrows, mfound, mtotal, mpct, mprestige = self.v0260_museum_snapshot()
            await self.send(f"Muzeum: {mfound} z {mtotal}, {mpct}%. Prestiż {mprestige}/1000.")
            await self.send(f"Odblokowane achievementy: {achievement_count}.")
            if self.character.active_title:
                await self.send(f"Aktywny tytuł: {self.character.active_title}.")

    async def show_achievements(self):
            await self.sync_extended_achievements()
            rows = self.server.db.achievement_rows(self.account_id)
            await self.send(f"ACHIEVEMENTY. Odblokowane: {len(rows)}.")
            for metric, definition in ACHIEVEMENT_TRACKS.items():
                value = self.server.db.achievement_metric(self.account_id, metric)
                next_row = next(
                    ((threshold, tier) for threshold, tier in definition["tiers"] if value < threshold),
                    None,
                )
                if next_row:
                    await self.send(
                        f"{definition['name']}: {value}. Następny próg {next_row[1]}: {next_row[0]}."
                    )
                else:
                    await self.send(
                        f"{definition['name']}: {value}. Najwyższy próg ukończony."
                    )
            if rows:
                await self.send("ODBLOKOWANE:")
                for row in rows[-30:]:
                    await self.send(f"{row['name']}, {row['tier']}.")

    async def show_titles(self):
            await self.v0260_sync_museum()
            await self.v0260_check_museum_rewards(announce=False)
            rows = list(self.server.db.title_rows(self.account_id))
            await self.send(f"TYTUŁY. Odblokowane: {len(rows)}.")
            await self.send(
                f"Aktywny: {self.character.active_title or 'brak'}."
            )
            for number, row in enumerate(rows, 1):
                marker = " Aktywny." if row["title_name"] == self.character.active_title else ""
                bonus = self.v0260_title_bonus_text(row["title_name"])
                bonus_text = f" Bonus: {bonus}." if bonus else ""
                await self.send(f"{number}. {row['title_name']}.{marker}{bonus_text}")

    async def set_title(self, args=""):
            raw = str(args or "").strip()
            if not raw:
                await self.show_titles()
                return
            if normalize_lookup_text(raw) in ("off", "wylacz", "brak", "none"):
                self.character.active_title = ""
                self.server.db.save_character(self.character)
                await self.send("Aktywny tytuł wyłączony.")
                return
            rows = list(self.server.db.title_rows(self.account_id))
            chosen = None
            if raw.isdigit():
                index = int(raw) - 1
                if 0 <= index < len(rows):
                    chosen = rows[index]
            if chosen is None:
                q = normalize_lookup_text(raw)
                exact = [row for row in rows if normalize_lookup_text(row["title_name"]) == q]
                partial = [row for row in rows if q and q in normalize_lookup_text(row["title_name"])]
                if exact:
                    chosen = exact[0]
                elif len(partial) == 1:
                    chosen = partial[0]
            if chosen is None:
                await self.send("Nie rozpoznaję odblokowanego tytułu. Wpisz tytuly.")
                return
            self.character.active_title = str(chosen["title_name"])
            self.server.db.save_character(self.character)
            await self.send(f"Aktywny tytuł: {self.character.active_title}.")
            bonus = self.v0260_title_bonus_text()
            if bonus:
                await self.send(f"Bonus aktywnego tytułu: {bonus}.")

    def _collection_v2_count(self, item_ids, discovered_eq=None):
            if discovered_eq is None:
                discovered_eq = self.server.db.collection_entry_ids(self.account_id, "equipment")
            item_ids = set(item_ids)
            return len(item_ids.intersection(discovered_eq)), len(item_ids)

    async def show_collection_v2_classes(self):
            discovered = self.server.db.collection_entry_ids(self.account_id, "equipment")
            await self.send("COLLECTION CODEX 2.0 — EQ WEDŁUG KLASY")
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
            await self.send(f"COLLECTION CODEX 2.0 — SETY. Strona {page} z {pages}; setów {len(rows)}.")
            start = (page - 1) * page_size
            for _key, name, count, total, pct in rows[start:start + page_size]:
                await self.send(f"{name}: {count} z {total}, {pct}%.")
            if page < pages:
                await self.send(f"Następna strona: kolekcja sety2 {page + 1}.")

    async def show_collection_v2_legends(self):
            discovered = self.server.db.collection_entry_ids(self.account_id, "equipment")
            all_items = set().union(*COLLECTION_V2_LEGENDARY_GROUPS.values()) if COLLECTION_V2_LEGENDARY_GROUPS else set()
            count, total = self._collection_v2_count(all_items, discovered)
            await self.send(f"COLLECTION CODEX 2.0 — LEGENDY: {count} z {total}, {int(count*100/max(1,total))}%.")
            for class_name in sorted(COLLECTION_V2_LEGENDARY_GROUPS, key=normalize_lookup_text):
                c, t = self._collection_v2_count(COLLECTION_V2_LEGENDARY_GROUPS[class_name], discovered)
                await self.send(f"{class_name}: {c} z {t}, {int(c*100/max(1,t))}%.")

    async def show_collection_v2_materials(self):
            discovered = self.server.db.collection_entry_ids(self.account_id, "equipment")
            await self.send("COLLECTION CODEX 2.0 — MATERIAŁOWE EQ")
            for tier in CORPSE_MATERIAL_TIERS:
                key = tier["key"]
                c, t = self._collection_v2_count(COLLECTION_V2_MATERIAL_GROUPS.get(key, ()), discovered)
                await self.send(f"{COLLECTION_V2_MATERIAL_LABELS[key]}: {c} z {t}, {int(c*100/max(1,t))}%.")

    async def show_collection_v2_regions(self):
            discovered = self.server.db.discovered_room_ids(self.account_id)
            await self.send("COLLECTION CODEX 2.0 — REGIONY")
            for zone in sorted(EXPLORATION_ZONE_ROOMS, key=normalize_lookup_text):
                rooms = EXPLORATION_ZONE_ROOMS[zone]
                count = sum(1 for room_id in rooms if room_id in discovered)
                total = len(rooms)
                await self.send(f"{zone}: {count} z {total}, {int(count*100/max(1,total))}%.")

    async def show_collection_v2_instances(self):
            await self.send("COLLECTION CODEX 2.0 — INSTANCJE")
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
                await self.send("COLLECTION CODEX")
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

    async def _record_corpse_loot(self, corpse, looted):
            for item_id in looted:
                self.server.db.add_item(self.account_id, item_id, 1)
                await self.record_item_collection(
                    item_id, source=corpse.mob_name, announce=True
                )
                boss_id = canonical_bestiary_template_id(corpse.mob_template_id)
                if boss_id in BOSS_COLLECTION_CATALOG:
                    if self.server.db.add_boss_codex_drop(self.account_id, boss_id, item_id):
                        await self.send(
                            f"Boss Codex: odkryty drop {ITEMS[item_id]['name']} z "
                            f"{BOSS_COLLECTION_CATALOG[boss_id]}."
                        )

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
            await self._record_corpse_loot(corpse, looted)

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
            corpse.items.remove(item_id)
            await self._record_corpse_loot(corpse, [item_id])
            await self.send(
                f"Zabierasz {item['name']} z ciała: {corpse.mob_name}."
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

            legendary_ids = {
                item_id for item_id, item in ITEMS.items()
                if item.get("type") in ("armor", "weapon") and (
                    str(item.get("rarity", "")).lower() == "legendary"
                    or item.get("legendary_set_loot")
                    or item.get("legendary_class_relic")
                )
            }

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
