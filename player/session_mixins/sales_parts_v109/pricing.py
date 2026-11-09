# -*- coding: utf-8 -*-
"""v109: sprzedaż — pricing; identyczne metody względem v108."""
from .dependencies import *

class SalesPricingV109Mixin:

    def profession_resource_sale_value_v1138(self, item_id, item):
            # v1.14.8: jeden kanoniczny kurs wszystkich czterech profesji.
            # fish_trophy_value_multiplier_v1138(item_id) i mnożnik rzadkiego
            # okazu stosuje już sama funkcja rynku. NIE mnożyć drugi raz.
            category = "ore" if item_id in MINING_STORAGE_IDS else None
            return profession_resource_market_value_v1148(
                item_id, item, category=category
            )
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

            # v1.14.8: zasoby wszystkich magazynów profesji sprzedawane tą
            # samą wyceną niezależnie od starych sell_gold/sell_silver.
            # Ta ścieżka obsługuje także sprzedaż masową i warianty rare.
            profession_storage_ids = (
                FISH_STORAGE_IDS | MINING_STORAGE_IDS | WOOD_STORAGE_IDS | HERB_STORAGE_IDS
            )
            if item_id in profession_storage_ids:
                value = self.profession_resource_sale_value_v1138(item_id, item)
                return {"silver": value, "gold": 0, "mithril": 0}

            # v1.13.30: Rezonans Głębi is a new physical item instance, not the
            # historical shop/sell contract of its base item. Always value it
            # from real mechanical power plus uncapped depth rank, before old
            # explicit sell_* / price shortcuts can flatten the reward.
            if item.get("infinite_depth_variant"):
                defense = max(0, int(item.get("defense", 0) or 0))
                attack = max(0, int(item.get("attack", 0) or 0))
                magic_attack = max(0, int(item.get("magic_attack", 0) or 0))
                flat_power = attack + magic_attack
                affix = max(0, abs(int(item.get("affix_amount", 0) or 0)))
                sockets = max(0, int(item.get("sockets", 0) or 0))
                stat_power = sum(
                    max(0, int(v or 0))
                    for v in (item.get("stats") or {}).values()
                )
                property_power = sum(
                    max(0.0, float(v or 0))
                    for v in (item.get("properties") or {}).values()
                )
                material_key = str(
                    item.get("corpse_material")
                    or item.get("blacksmith_material")
                    or ""
                )
                material_base = V0863_MATERIAL_SALE_BASE_SILVER.get(
                    material_key, 0
                )
                mechanical_silver = max(
                    25,
                    material_base + defense * 40 + flat_power * 140
                    + affix * 30 + sockets * 150
                    + 600 * 20 + stat_power * 120
                    + int(property_power * 250),
                )
                depth_rank = max(
                    1, int(item.get("infinite_depth_rank", 1) or 1)
                )
                rarity = str(
                    item.get("rarity") or "common"
                ).strip().lower()
                resale_fraction = V11314_ARMOR_RESALE_QUEST_FRACTION.get(
                    rarity, 0.035
                )
                depth_factor = 1.0 + 0.030 * (depth_rank ** 0.82)
                depth_floor = max(
                    1,
                    int(round(
                        economy_stage_anchor_v11314(600)
                        * resale_fraction
                        * depth_factor
                    )),
                )
                return {
                    "silver": max(mechanical_silver, depth_floor),
                    "gold": 0,
                    "mithril": 0,
                }

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

                profession_storage_ids = (
                    FISH_STORAGE_IDS
                    | MINING_STORAGE_IDS
                    | WOOD_STORAGE_IDS
                    | HERB_STORAGE_IDS
                )
                if item_id in profession_storage_ids:
                    authored_total = legacy_currency_to_coins(
                        explicit["silver"], explicit["gold"], explicit["mithril"]
                    )
                    if item_id in FISH_STORAGE_IDS:
                        authored_total = max(
                            1,
                            int(round(
                                authored_total
                                * v096_fish_price_scale(item_id)
                                * fish_trophy_value_multiplier_v1138(item_id)
                            )),
                        )
                    total = max(
                        authored_total,
                        self.profession_resource_sale_value_v1138(item_id, item),
                    )
                    return {"silver": total, "gold": 0, "mithril": 0}

                # v1.13.25: old explicit sell_* values are no longer allowed to
                # make otherwise useful loot/EQ worthless. Exact/manual sale
                # contracts can opt out through the helper.
                if item.get("type") in {"loot", "armor"}:
                    total = legacy_explicit_sale_value_v11325(item_id, item)
                    if smith_cap is not None:
                        total = min(total, smith_cap)
                    return {"silver": total, "gold": 0, "mithril": 0}
                return explicit

            if item.get("type") in {"resource", "craft_material"}:
                total = self.profession_resource_sale_value_v1138(item_id, item)
                return {"silver": total, "gold": 0, "mithril": 0}

            # Przedmiot kupny: sklep odkupuje za 50% ceny bazowej.
            # v1.13.25: legacy armor cannot get stuck at half of an ancient,
            # pre-rebalance shop price; current progression floor still applies.
            price = item.get("price")
            currency = item.get("currency", "silver")
            if isinstance(price, (int, float)) and price > 0 and currency in explicit:
                value = max(1, int(price) // 2)
                result = {"silver": 0, "gold": 0, "mithril": 0}
                result[currency] = value
                total = legacy_currency_to_coins(
                    result["silver"], result["gold"], result["mithril"]
                )
                if item.get("type") == "armor":
                    total = max(
                        total,
                        legacy_explicit_sale_value_v11325(item_id, item),
                    )
                if smith_cap is not None:
                    total = min(total, smith_cap)
                if item.get("type") == "armor" or smith_cap is not None:
                    return {"silver": total, "gold": 0, "mithril": 0}
                return result

            # v0.9.15: zwykły loot z mobów (np. kły i trofea) można
            # sprzedać w każdym normalnym sklepie. Jawne sell_* nadal ma pierwszeństwo.
            if item.get("type") == "loot":
                stage = v0190_resource_stage(item_id, item)
                rarity_mult = {
                    "common": 0.50,
                    "uncommon": 0.75,
                    "rare": 1.25,
                    "epic": 2.25,
                    "legendary": 4.00,
                    "mythic": 7.00,
                    "unique": 10.00,
                }.get(str(item.get("rarity") or "common"), 0.50)
                progression_value = max(
                    1,
                    int(round(v1138_resource_sale_base_coins(stage) * rarity_mult)),
                )
                authored_value = max(1, int(item.get("loot_sell_silver", 25) or 25))
                return {
                    "silver": max(authored_value, progression_value),
                    "gold": 0,
                    "mithril": 0,
                }

            # v1.13.14: dobry drop zachowuje wartość także przy sprzedaży.
            if item.get("type") == "armor":
                defense = max(0, int(item.get("defense", 0) or 0))
                attack = max(0, int(item.get("attack", 0) or 0))
                magic_attack = max(0, int(item.get("magic_attack", 0) or 0))
                flat_power = attack + magic_attack
                affix = max(0, abs(int(item.get("affix_amount", 0) or 0)))
                sockets = max(0, int(item.get("sockets", 0) or 0))
                mastery = max(0, int(item.get("required_mastery", 0) or 0))
                craft_level = max(
                    int(item.get("jewelcraft_level", 0) or 0),
                    int(item.get("blacksmith_tier", 0) or 0) * 10,
                )
                material_key = str(item.get("corpse_material") or item.get("blacksmith_material") or "")
                material_base = V0863_MATERIAL_SALE_BASE_SILVER.get(material_key, 0)
                stat_power = sum(max(0, int(v or 0)) for v in (item.get("stats") or {}).values())
                property_power = sum(max(0.0, float(v or 0)) for v in (item.get("properties") or {}).values())
                mechanical_silver = max(
                    25,
                    material_base + defense * 40 + flat_power * 140
                    + affix * 30 + sockets * 150 + mastery * 20
                    + craft_level * 25 + stat_power * 120
                    + int(property_power * 250),
                )
                stage = v0190_resource_stage(item_id, item)
                rarity = str(item.get("rarity") or "common").strip().lower()
                resale_fraction = V11314_ARMOR_RESALE_QUEST_FRACTION.get(rarity, 0.035)
                progression_floor = max(
                    1, int(round(economy_stage_anchor_v11314(stage) * resale_fraction))
                )
                silver = max(mechanical_silver, progression_floor)
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
            from systems.equipment_evolution_v10500 import is_evolved
            if is_evolved(self.server.db.conn, self.account_id, item_id):
                return False
            values = self.generic_item_sale_value(item_id, item)
            return any(values.values())
    def bulk_sell_rewards_for_rows(self, rows, *, shop_purchase_basis=False):
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
                if shop_purchase_basis:
                    normal = legacy_currency_to_coins(silver, gold, mithril)
                    total_silver += self.server.db.shop_resale_total_v1175(
                        self.account_id, item_id, quantity, normal
                    )
                else:
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
