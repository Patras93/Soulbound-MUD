# -*- coding: utf-8 -*-
"""v109: sprzedaż — profession_exp; identyczne metody względem v108."""
from .dependencies import *

class SalesProfessionExpV109Mixin:

    def grant_profession_sale_xp(
        self, container, units, *, content_level
    ):
            definition = self.profession_sale_definition(container)
            units = max(0, int(units or 0))
            if not definition or units <= 0:
                return []

            profession, _tool_type = definition
            prow = self.server.db.profession(self.account_id, profession)
            level = int(prow["level"])
            # Bazowa nagroda nadal zależy od liczby sprzedanych sztuk,
            # ale v1.13.42 różnicuje ją również jakością realnego materiału.
            xp_scale = (
                v096_fishing_reward_scale(level)
                if container == "net" else 1.0
            )
            content_mult,_tool_mult=(
                self.profession_content_xp_multiplier_v11342(
                    content_level,_tool_type
                )
            )
            actual_xp=max(
                1,
                int(round(
                    units
                    * PROFESSION_XP_GAIN_MULTIPLIER
                    * xp_scale
                    * content_mult
                )),
            )
            actual_xp = self.apply_double_xp(actual_xp)
            # v2.32.19: selling a large stored batch is ONE award, subject
            # to the same account-wide Multi Cap, not cap x sold quantity.
            from systems.experience_bank_v2011 import banked_experience_v2011
            actual_xp = banked_experience_v2011(
                self.server.db, self.account_id, actual_xp,
                'profession', level, source_key=profession)
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
                messages.append(f"AWANS PROFESJI: {profession} osiąga poziom {level}.")

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
    def profession_sale_content_level_v11342(self, rows, container=None):
            weighted=0
            total=0
            for item_id,quantity in rows:
                quantity=max(0,int(quantity or 0))
                if quantity<=0:
                    continue
                item_container=self.recipe_container_for_item(item_id)
                if container is not None and item_container!=container:
                    continue
                if item_container not in ("net","bag","woodpile","herbbag"):
                    continue
                stage=self.profession_content_level_v11342(
                    item_id=item_id,item=ITEMS.get(item_id,{})
                )
                weighted += int(stage) * quantity
                total += quantity
            if total<=0:
                return 1
            return max(1,min(800,int(round(weighted/float(total)))))
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
    async def announce_profession_sale_xp(
        self, container, units, *, content_level
    ):
            for message in self.grant_profession_sale_xp(
                container,units,content_level=content_level
            ):
                await self.send(message)
    async def announce_profession_sale_xp_for_rows(self, rows):
            for container,units in self.profession_sale_units_for_rows(rows).items():
                if units>0:
                    content_level=self.profession_sale_content_level_v11342(
                        rows,container
                    )
                    await self.announce_profession_sale_xp(
                        container,units,content_level=content_level
                    )
    async def gain_charisma_from_bulk_sale(self, rewards):
            units = max(0, int(rewards.get("units", 0) or 0))
            if units <= 0:
                return
            sale_value = legacy_currency_to_coins(
                rewards.get("silver", 0), rewards.get("gold", 0), rewards.get("mithril", 0)
            )
            await self.gain_charisma_from_sale(sale_value, units=units)
