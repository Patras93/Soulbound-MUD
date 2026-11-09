# -*- coding: utf-8 -*-
"""v109: muzeum, osiągnięcia i zlecenia — kill_progress. Historyczne metody bez zmian."""
from .dependencies import *

class MuseumKillProgressV109Mixin:
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
            # v11.00.9: all event-driven quests use the same accessible
            # progress announcer. Never hide exploration/secret/world-event
            # milestones in concise combat-log mode.
            for quest_id, progress, needed in changed:
                if hasattr(self, 'announce_active_quest_progress'):
                    await self.announce_active_quest_progress(quest_id)
                else:
                    # Standalone historical exploration regression harnesses
                    # don't compose the entire SessionQuestsMixin. Preserve
                    # the same named stage label, not a technical quest ID.
                    q = QUESTS[quest_id]
                    if q.get('v800_class_saga'):
                        await self.send(
                            f'Droga Legendy {q["required_class"]}, etap {q["v800_stage"]}/120: '
                            f'Postęp {progress} z {needed}.'
                        )
                    else:
                        await self.send(f"Postęp questa: {q['name']}. {progress} z {needed}.")
            return changed
