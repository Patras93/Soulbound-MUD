# -*- coding: utf-8 -*-
"""Class state, mastery, training and multiclass progression."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
from core.bootstrap_economy_professions import currency_reading_text
from core.classes_skills import CLASS_SKILLS
from core.progression_resources import class_mastery_xp_to_next, v0190_economy_sink
from player.character import CHARACTER_MAX_LEVEL, MULTICLASS_MAX_ACTIVE
from player.session_mixins.dungeon_progression import ITEMS, player_item_display_name_v0335
from storage.db_schema import CLASSES, legacy_currency_to_coins
from world.equipment_help import CLASS_MASTERY_MAX_LEVEL, NPCS
from world.runtime_progression import v0210_ascension_xp_to_next


class SessionClassProgressionMixin:

    def refresh_active_classes(self):
            if not self.character or not self.account_id:
                return []
            names = self.server.db.active_class_names(
                self.account_id, self.character.class_name
            )
            self.character._active_classes = list(names)
            return list(names)

    def active_class_names(self):
            self.refresh_active_classes()
            return self.character.active_class_names()

    def find_class_name(self, query):
            wanted = self.normalize_description_query(query)
            if not wanted:
                return None
            exact = []
            partial = []
            for class_name, class_type, weapon, base_power in CLASSES:
                normalized = self.normalize_description_query(class_name)
                if wanted == normalized:
                    exact.append(class_name)
                elif wanted in normalized:
                    partial.append(class_name)
            if exact:
                return exact[0]
            if len(partial) == 1:
                return partial[0]
            return None

    def skill_class_name(self, skill):
            skill_id = skill["id"] if isinstance(skill, dict) else str(skill)
            for class_name, skills in CLASS_SKILLS.items():
                if any(entry["id"] == skill_id for entry in skills):
                    return class_name
            return self.character.class_name

    def class_mastery_level(self, class_name):
            row = self.server.db.class_progress_row(self.account_id, class_name)
            return int(row["level"]) if row else 1

    def highest_active_class_mastery(self):
            active = self.active_class_names()
            if not active:
                return 1
            return max(self.class_mastery_level(class_name) for class_name in active)

    def equipment_character_level_requirement(self, item):
            if item.get("type") != "armor":
                return 1
            return max(1, min(CHARACTER_MAX_LEVEL, int(
                item.get("required_character_level", item.get("required_mastery", 1)) or 1
            )))

    def equipment_mastery_requirement_met(self, item):
            """EQ zwykle wymaga Levelu postaci; wybrane przedmioty mogą wymagać Biegłości konkretnej klasy."""
            if item.get("type") != "armor":
                return True
            required_class_mastery = int(item.get("required_class_mastery", 0) or 0)
            required_class = item.get("required_class")
            if required_class and required_class not in self.active_class_names():
                return False
            if required_class_mastery > 0 and required_class:
                return (required_class in self.active_class_names() and
                        self.class_mastery_level(required_class) >= required_class_mastery)
            return int(self.character.character_level) >= self.equipment_character_level_requirement(item)

    def equipment_mastery_requirement_text(self, item):
            """Czytelny opis progu EQ: Biegłość klasy dla wyjątków, Level postaci dla zwykłego EQ."""
            if item.get("type") != "armor":
                return ""
            required_class_mastery = int(item.get("required_class_mastery", 0) or 0)
            required_class = item.get("required_class")
            if required_class_mastery > 0 and required_class:
                current = self.class_mastery_level(required_class)
                return (
                    f"Wymaga Biegłości klasy {required_class} {required_class_mastery}. "
                    f"Masz Biegłość {current}."
                )
            required_level = self.equipment_character_level_requirement(item)
            return (
                f"Wymaga Levelu postaci {required_level}. "
                f"Masz Level postaci {int(self.character.character_level)}."
            )

    def enforce_equipment_character_level(self):
            """Unequip inaccessible gear: foreign class or unmet level/mastery.

            Inventory, upgrades, runes and socket data are NOT deleted.
            """
            removed = []
            for row in list(self.server.db.equipment(self.account_id)):
                item = ITEMS.get(row["item_id"])
                if not item or item.get("type") != "armor":
                    continue
                if not self.equipment_mastery_requirement_met(item):
                    self.server.db.unequip(self.account_id, row["slot"])
                    removed.append(item.get("name") or player_item_display_name_v0335(row["item_id"]))
            return removed

    def skill_required_mastery(self, skill):
            return max(1, int(skill.get("unlock", 1)))

    def skill_mastery_unlocked(self, skill):
            class_name = self.skill_class_name(skill)
            # v7.10.1: historical mastery does not unlock foreign-class skills.
            return (class_name in self.active_class_names()
                    and self.class_mastery_level(class_name) >= self.skill_required_mastery(skill))

    def skill_training_cost_silver(self, skill):
            """v0.19: koszt nauki korzysta z globalnej krzywej ekonomii."""
            unlock=max(1,min(CLASS_MASTERY_MAX_LEVEL,int(skill.get("unlock",1))))
            return v0190_economy_sink(unlock,"skill")

    def training_cost_text(self, silver_cost):
            return currency_reading_text(max(0, int(silver_cost)), 0, 0)

    def character_wallet_silver_value(self):
            return legacy_currency_to_coins(
                self.character.silver, self.character.gold, self.character.mithril
            )

    def pay_training_cost(self, silver_cost):
            silver_cost = max(0, int(silver_cost))
            total = self.character_wallet_silver_value()
            if total < silver_cost:
                return False
            self.character.silver = total - silver_cost
            self.character.gold = 0
            self.character.mithril = 0
            self.server.db.save_character(self.character)
            return True

    def teacher_here_for_active_class(self):
            active = set(self.active_class_names())
            for npc_id, npc in NPCS.items():
                if (
                    npc.get("room") == self.character.room_id
                    and npc.get("teacher_class") in active
                ):
                    return npc_id, npc
            return None, None

    async def show_multiclass(self):
        name = self.character.class_name
        row = self.server.db.class_progress_row(self.account_id, name)
        level = int(row["level"]) if row else 1
        await self.send(
            f"JEDNA KLASA NA POSTAĆ: {name}. Biegłość {level}/{CLASS_MASTERY_MAX_LEVEL}. "
            "Multiklasowość jest wyłączona."
        )
        await self.send(
            "Wcześniej zdobyte poziomy innych klas są zachowane w SQLite jako archiwum. "
            "Nie dają pasywów, umiejętności, EXP ani dodatkowego Multi Cap. "
            "Nie można dodawać, zmieniać ani usuwać klasy głównej."
        )

    async def handle_multiclass(self, raw):
        # Fail closed even if an old client sends add/remove aliases.
        await self.show_multiclass()

    async def grant_class_xp(
        self, total_xp, single_level_cap=False, *,
        content_level=None, content_scaled=False, overcap=False
    ):
            active = self.active_class_names()
            if not active:
                return
            original_total_xp = max(0, int(total_xp))
            if original_total_xp <= 0:
                return
            original_total_xp=self.scale_progression_xp_v11342(
                original_total_xp,
                content_level,
                content_scaled=content_scaled,
            )
            base_total_xp = self.apply_double_xp(original_total_xp)
            _guild_pct=self.guild_bonus_percent_v0926()
            total_xp=max(0,int(round(base_total_xp*(1.0+_guild_pct/100.0))))
            _mentor_pct = self.mentor_bonus_percent_v03050()
            if _mentor_pct:
                total_xp=max(0,int(round(total_xp*(1.0+_mentor_pct/100.0))))
                self.mentor_record_activity_v03051()

            # v7.10.1: class XP is granted only to the character's primary class.
            from systems.experience_bank_v2011 import banked_experience_v2011
            allocated = [banked_experience_v2011(
                self.server.db, self.account_id,
                total_xp, 'class',
                self.class_mastery_level(class_name),
                source_key=class_name, overcap=overcap)
                for class_name in active]
            overall_awarded = sum(allocated)
            self.session_summary_add("class_xp", overall_awarded)
            _guild_note=f" Bonus Gildii +{_guild_pct}%." if _guild_pct else ""
            _event_note=" Event x2 EXP." if base_total_xp>original_total_xp else ""
            await self.send(
                f"EXP klasy {self.character.class_name}: {overall_awarded}. "
                "Nagroda trafia tylko do klasy głównej (do Multi Cap)."
                + _event_note + _guild_note
            )

            for index, class_name in enumerate(active):
                share = allocated[index]
                result = self.server.db.add_class_mastery_xp(
                    self.account_id,
                    class_name,
                    share,
                    single_level_cap=single_level_cap,
                )
                if result["level_ups"]:
                    await self.send(
                        f"{class_name}: Biegłość rośnie do {result['level']}."
                    )
                ascension=None
                overflow=max(0,int(result.get("overflow_xp",0) or 0))
                if overflow>0 and result["level"]>=CLASS_MASTERY_MAX_LEVEL:
                    ascension=self.server.db.add_ascension_xp_v021(self.account_id,f"class:{class_name}",overflow)
                    if ascension["rank_ups"]:
                        await self.send(f"{class_name}: Wzniesienie rośnie do rangi {ascension['rank']}.")
                        for milestone in (1,10,25,50,100,250,500,1000):
                            if ascension["rank"]>=milestone>ascension["rank"]-ascension["rank_ups"]:
                                await self.unlock_title(f"v021:ascension:{class_name}:{milestone}",f"{class_name} — Wzniesienie {milestone}")
                if result["level"] >= CLASS_MASTERY_MAX_LEVEL:
                    if ascension:
                        nxt=(f" z {ascension['next_xp']}" if ascension['next_xp'] else " — maksimum")
                        await self.send(f"{class_name}: +{result['gain']} EXP klasy. Biegłość {CLASS_MASTERY_MAX_LEVEL}; Wzniesienie {ascension['rank']}, XP {ascension['xp']}{nxt}.")
                    else:
                        await self.send(f"{class_name}: +{result['gain']} EXP klasy. Biegłość {CLASS_MASTERY_MAX_LEVEL}, maksimum.")
                else:
                    await self.send(
                        f"{class_name}: +{result['gain']} EXP klasy. "
                        f"Biegłość {result['level']}, XP {result['xp']} z "
                        f"{result['next_xp']}."
                    )
