# -*- coding: utf-8 -*-
"""Manual fishing, mining, woodcutting and herbalism actions."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import asyncio
import random
import time
from core.bootstrap_economy_professions import tool_tier, tool_tier_bonus_chance, tool_tier_name, v0250_gather_hotspot
from core.classes_skills import ROOMS
from core.mines_threat import ITEMS
from core.progression_600 import PROFESSION_MAX_LEVEL
from core.progression_resources import (
    FISHING_ROOMS,
    HERBALISM_ROOMS,
    PROFESSION_COOLDOWN,
    WOODCUTTING_ROOMS,
    balanced_gather_tool_xp,
    is_mining_room,
    mine_floor_number,
    mining_mithril_currency_chance,
    v096_fishing_reward_scale,
)
from network.protocol_gameplay_utils import roll_profession_gather_quantity
from systems.dungeons_regions import profession_dungeon_floor
from systems.equipment_crafting import GEM_QUALITY_INFO, roll_mining_geode
from systems.items_resources import (
    RARE_FISH_VARIANT_IDS,
    base_fish_species_id,
    fish_rarity_label,
    fish_species_rarity,
    format_fish_length,
    format_fish_weight,
    roll_fish_measurement,
    roll_fish_variant,
    roll_herb_variant,
    roll_mining_vein,
    roll_wood_variant,
)
from world.generation_systems import v0140_gather_event_bonus, v0150_environment_bonus

from events.contracts import ResourceGatheredEvent

class SessionGatheringActionsMixin:

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
            global_record_before_v03811 = self.server.db.fish_global_record_v022(species_id)
            global_record_v022 = self.server.db.record_fishing_global_v022(
                species_id, item_id, self.character.name, best_length, best_weight, self.account_id
            )
            try:
                self.server.db.record_server_fish_record_v03811(
                    self.account_id, self.character.name, species_id, item_id,
                    best_length, best_weight, global_record_v022,
                    had_global_record=(global_record_before_v03811 is not None),
                )
            except Exception:
                pass
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

            await self.announce_gathering_order_progress_v0713("fish", resource_quest_quantity)
            await self.server.events.publish(ResourceGatheredEvent(
                session=self, action="fishing", item_id=item_id, quantity=resource_quest_quantity,
                category="fish", bounty_kind="fish", dynamic_kind="fish", legendary_kind="fish",
                faction="waters", faction_reason="fishing", lifetime_stat="fish_caught",
                secondary_category=f"fish_{habitat}", distinct_category="fish",
                distinct_item_id=species_id,
                rare_achievement="rare_fish_caught" if item_id in RARE_FISH_VARIANT_IDS else None,
                rare_lifetime_stat="rare_fish_caught" if item_id in RARE_FISH_VARIANT_IDS else None,
            ))

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
            if ITEMS.get(base_item_id, {}).get("deep_ocean") or ROOMS.get(self.character.room_id, {}).get("deep_ocean_fishing"):
                try:
                    self.server.db.conn.execute(
                        "UPDATE ocean_ship_v1000 SET deep_catches=deep_catches+1 WHERE account_id=?",
                        (self.account_id,),
                    )
                    map_name = self.maybe_grant_ocean_treasure_map_v1000() if hasattr(self, "maybe_grant_ocean_treasure_map_v1000") else None
                    self.server.db.conn.commit()
                    if map_name:
                        await self.send(f"MAPA SKARBU: podczas połowu znajdujesz {map_name}. Wpisz skarby.")
                except Exception:
                    pass
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
                floor_for_currency = min(PROFESSION_MAX_LEVEL, max(1, int(dungeon_floor_for_currency) * 10))
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
                floor_for_geode = min(PROFESSION_MAX_LEVEL, int(dungeon_floor) * 10)
            geode_id = roll_mining_geode(
                tool_level, profession_level, floor_for_geode or 1
            )
            if geode_id:
                self.store_profession_resource(geode_id, 1)
                await self.send(
                    f"GEODA: znajdujesz {ITEMS[geode_id]['name']} x1. "
                    "Trafia do Sakwy Górnika. Otwórz: open geode / otwórz geodę."
                )

            await self.announce_gathering_order_progress_v0713("ore", mined_resource_quantity)
            await self.server.events.publish(ResourceGatheredEvent(
                session=self, action="mining", item_id=item_id, quantity=mined_resource_quantity,
                category="ore", bounty_kind="mine", dynamic_kind="mine", legendary_kind="gather",
                faction="miners", faction_reason="mining", lifetime_stat="ore_mined",
            ))

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
            await self.announce_gathering_order_progress_v0713("wood", resource_quest_quantity)
            await self.server.events.publish(ResourceGatheredEvent(
                session=self, action="woodcutting", item_id=item_id, quantity=resource_quest_quantity,
                category="wood", bounty_kind="wood", dynamic_kind="wood", legendary_kind="gather",
                faction="green_path", faction_reason="woodcutting", lifetime_stat="wood_gathered",
            ))

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
            await self.announce_gathering_order_progress_v0713("herb", resource_quest_quantity)
            await self.server.events.publish(ResourceGatheredEvent(
                session=self, action="herbalism", item_id=item_id, quantity=resource_quest_quantity,
                category="herb", bounty_kind="herb", dynamic_kind="herb", legendary_kind="gather",
                faction="green_path", faction_reason="herbalism", lifetime_stat="herbs_gathered",
            ))

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
