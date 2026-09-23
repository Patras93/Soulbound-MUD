# -*- coding: utf-8 -*-
"""Museum, achievements, collection recording and bounty board."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import math
import random
from core.bootstrap_economy_professions import SILVER_PER_GOLD, TOOL_PROFESSION_MAP, currency_reading_text, profession_max_level
from core.classes_skills import ROOMS
from core.mines_threat import ITEMS
from core.progression_resources import (
    V019_QUEST_COIN,
    V019_SOUL_KILL_NORMAL,
    v0190_log_curve,
    v0190_mob_stage,
    v096_fishing_workload_scale,
)
from network.protocol_gameplay_utils import canonical_profession_resource_id, normalize_lookup_text, v0929_kill_drop_item
from systems.content_registry import MOB_TEMPLATES, QUESTS
from systems.crafting_quality import player_item_display_name_v0335
from systems.equipment_crafting import CUT_GEM_IDS, RAW_GEM_IDS
from systems.items_resources import RARE_FISH_VARIANT_IDS
from world.dynamic_content import (
    ACHIEVEMENT_TITLE_REWARDS,
    ACHIEVEMENT_TRACKS,
    ALL_EXPLORATION_ROOMS,
    BESTIARY_CATALOG,
    BESTIARY_SPAWN_ROOMS,
    BOSS_COLLECTION_CATALOG,
    BOUNTY_KINDS,
    BOUNTY_OFFER_COUNT,
    BOUNTY_RESOURCE_LABELS,
    BOUNTY_RESOURCE_NEEDS,
    COLLECTION_CATALOGS,
    EQUIPMENT_COLLECTION_CATALOG,
    FISH_COLLECTION_CATALOG,
    GEM_COLLECTION_CATALOG,
    HERB_COLLECTION_CATALOG,
    MATERIAL_COLLECTION_CATALOG,
    MINERAL_COLLECTION_CATALOG,
    MINI_BOSS_IDS,
    NAMED_LOOT_CATALOG,
    SET_COLLECTION_CATALOG,
    SET_ENTRY_BY_ITEM,
    UNIQUE_ITEM_COLLECTION_CATALOG,
    canonical_bestiary_template_id,
    loot_filter_allows,
    loot_rarity_rank,
)
from world.economy_quests import (
    COLLECTION_CATEGORY_LABELS,
    INSTANCE_MAP_DEFS,
    instance_secret_index,
    v0863_is_boss_template,
    v0914_combat_quest_stat_reward,
)
from world.world_state import (
    V0260_GLOBAL_MUSEUM_TITLES,
    V0260_INSTANCE_SECRET_CATALOG,
    V0260_LEGENDARY_ITEM_CATALOG,
    V0260_MUSEUM_ALIASES,
    V0260_MUSEUM_CATALOGS,
    V0260_MUSEUM_CATEGORY_TITLES,
    V0260_MUSEUM_LABELS,
    V0260_SET_PIECE_GROUPS,
    V0260_SURFACE_SECRET_CATALOG,
    V0260_TITLE_BONUSES,
    V0260_WOOD_CATALOG,
    v0260_museum_rank,
)


class SessionMuseumBountyMixin:

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
                # v0.38.7: warianty zagęszczające lochy są techniczne. Ich
                # nazwy mogą mieć formę „Grobowy Upiór — Kościany Rycerz” i
                # nigdy nie mogą być osobnym celem Tablicy Zleceń.
                if template.get("dense_dungeon_variant"):
                    continue
                if v0863_is_boss_template(template):
                    continue
                result.append((mob_id, template.get("name") or "Nieznany przeciwnik"))
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

    def normalize_bounty_kill_entry_v0387(self, entry):
            """Return one clean, canonical bounty entry without technical mob names."""
            row = dict(entry or {})
            if str(row.get("kind") or "") != "kill":
                return row, False
            old_target = str(row.get("target") or "")
            canonical = canonical_bestiary_template_id(old_target)
            if canonical not in MOB_TEMPLATES:
                return row, False
            needed = max(1, int(row.get("needed", 1) or 1))
            clean_name = str(MOB_TEMPLATES[canonical].get("name") or canonical)
            clean_label = f"Pokonaj {needed} razy: {clean_name}"
            changed = old_target != canonical or str(row.get("label") or "") != clean_label
            row["target"] = canonical
            row["label"] = clean_label
            return row, changed

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

            # v0.38.7: napraw również już zapisane oferty/aktywny kontrakt
            # z wcześniejszej wersji, bez zerowania postępu gracza.
            changed = False
            clean_offers = []
            for offer in state.get("offers") or []:
                clean, was_changed = self.normalize_bounty_kill_entry_v0387(offer)
                clean_offers.append(clean)
                changed = changed or was_changed
            clean_active, active_changed = self.normalize_bounty_kill_entry_v0387(state.get("active") or {})
            changed = changed or active_changed
            state["offers"] = clean_offers
            state["active"] = clean_active
            if changed:
                self.server.db.save_bounty_board_state(
                    self.account_id, offers=clean_offers, active=clean_active,
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
                "Komendy: bounty accept <1-3>, bounty aktywne, bounty odbierz, bounty porzuć; "
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

            if norm in ("porzuc", "porzuć", "abandon", "cancel"):
                if not active:
                    await self.send("Nie masz aktywnego kontraktu do porzucenia.")
                    return
                label = str(active.get("label", "Kontrakt"))
                progress = max(0, int(active.get("progress", 0)))
                needed = max(1, int(active.get("needed", 1)))
                self.server.db.save_bounty_board_state(
                    self.account_id,
                    offers=state.get("offers", []),
                    active={},
                    completed_count=state.get("completed_count", 0),
                )
                await self.send(
                    f"Porzucono kontrakt: {label}. Postęp {progress} z {needed} został anulowany. "
                    "Oferty na Tablicy Zleceń pozostały bez zmian."
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
                "bounty odbierz; bounty porzuć lub bounty porzuc; bounty odśwież."
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
                item_display_name_v03811 = player_item_display_name_v0335(item_id)
                self.server.db.add_drop_history(
                    self.account_id,
                    item_id,
                    item_display_name_v03811,
                    rarity,
                    source,
                    zone,
                )
                if rank >= 3:
                    try:
                        self.server.db.record_server_exceptional_drop_v03811(
                            self.account_id, self.character.name, item_id,
                            item_display_name_v03811, rarity, source, zone,
                        )
                    except Exception:
                        pass

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
