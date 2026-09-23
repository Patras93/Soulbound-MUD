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
            if required_class_mastery > 0 and required_class:
                return self.class_mastery_level(required_class) >= required_class_mastery
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
            """Unequip legacy gear that is above the current Character Level."""
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
            return self.class_mastery_level(class_name) >= self.skill_required_mastery(skill)

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
            active = self.active_class_names()
            await self.send(
                f"MULTICLASS: {len(active)} z {MULTICLASS_MAX_ACTIVE} aktywnych klas."
            )
            await self.send(
                f"Klasa główna: {self.character.class_name}. "
                f"Broń Duszy pozostaje: {self.character.soul_weapon}."
            )
            rows = self.server.db.active_class_rows(
                self.account_id, self.character.class_name
            )
            for row in rows:
                level = int(row["level"])
                xp = int(row["xp"])
                slot = int(row["active_slot"])
                role = "główna" if slot == 1 else f"dodatkowa, slot {slot}"
                if level >= CLASS_MASTERY_MAX_LEVEL:
                    _arow=self.server.db.ascension_row_v021(self.account_id,f"class:{row['class_name']}")
                    _rank=int(_arow["rank"] or 0); _axp=int(_arow["xp"] or 0); _need=v0210_ascension_xp_to_next(_rank)
                    progress = f"Biegłość {CLASS_MASTERY_MAX_LEVEL}, maksimum; Wzniesienie {_rank}" + (f", XP {_axp} z {_need}." if _need else ", maksimum Wzniesienia.")
                else:
                    needed = class_mastery_xp_to_next(level)
                    progress = (
                        f"Biegłość {level}, XP {xp} z {needed}, "
                        f"brakuje {max(0, needed - xp)} XP."
                    )
                await self.send(
                    f"{row['class_name']}: {role}. {progress} "
                    f"Pasyw: {self.character.class_passive_text_for(row['class_name'])}."
                )

            await self.send(
                "Dodanie klas jest opcjonalne. Użyj: multiclass add <klasa>. "
                "Usunięcie: multiclass remove <klasa>."
            )
            await self.send(
                "Maksymalnie 3 klasy łącznie. Class XP z każdego zabitego moba "
                "jest dzielony równo między wszystkie aktywne klasy."
            )
            await self.send(
                "Klasa główna i jej Broń Duszy nie zmieniają się. "
                "Dodatkowe klasy dają swoje pasywy i dostęp do skilli ich nauczycieli."
            )

    async def handle_multiclass(self, raw):
            if self.combat_mob_key:
                await self.send("Nie możesz zmieniać multiclass podczas walki.")
                return

            parts = raw.strip().split(maxsplit=1)
            if not parts:
                await self.show_multiclass()
                return

            action = self.normalize_description_query(parts[0])
            query = parts[1] if len(parts) > 1 else ""

            if action in ("status", "show", "lista", "list"):
                await self.show_multiclass()
                return

            if action in ("add", "dodaj", "wlacz", "włącz"):
                class_name = self.find_class_name(query)
                if not class_name:
                    await self.send(
                        "Nie rozpoznaję klasy. Dostępne: "
                        + ", ".join(cls[0] for cls in CLASSES) + "."
                    )
                    return
                if class_name == self.character.class_name:
                    await self.send("To już jest twoja klasa główna.")
                    return

                old_max_mana = self.max_mana()
                ok, result = self.server.db.activate_secondary_class(
                    self.account_id, self.character.class_name, class_name
                )
                if not ok:
                    await self.send(str(result))
                    return

                self.refresh_active_classes()
                new_max_mana = self.max_mana()
                if new_max_mana > old_max_mana:
                    self.current_mana = new_max_mana
                else:
                    self.current_mana = min(self.current_mana, new_max_mana)

                await self.send(
                    f"Aktywowano dodatkową klasę: {class_name}. "
                    f"Masz teraz {len(self.active_class_names())} aktywne klasy."
                )
                await self.send(
                    "Jej pasyw działa od razu. Skilli nauczysz się u nauczyciela "
                    f"klasy {class_name}."
                )
                await self.set_achievement_progress(
                    "multiclass_classes", len(self.active_class_names())
                )
                return

            if action in ("remove", "usun", "usuń", "wylacz", "wyłącz"):
                class_name = self.find_class_name(query)
                if not class_name:
                    await self.send("Nie rozpoznaję klasy do wyłączenia.")
                    return

                old_max_mana = self.max_mana()
                ok, result = self.server.db.deactivate_secondary_class(
                    self.account_id, self.character.class_name, class_name
                )
                if not ok:
                    await self.send(str(result))
                    return

                self.refresh_active_classes()
                new_max_mana = self.max_mana()
                self.current_mana = min(self.current_mana, new_max_mana)

                await self.send(
                    f"Wyłączono dodatkową klasę: {class_name}. "
                    "Jej Biegłość i nauczenie skille pozostają zapisane, "
                    "ale nie można ich używać, dopóki klasa znów nie będzie aktywna."
                )
                return

            await self.send(
                "Użycie: multiclass, multiclass add <klasa>, "
                "multiclass remove <klasa>."
            )

    async def grant_class_xp(self, total_xp):
            active = self.active_class_names()
            if not active:
                return
            original_total_xp = max(0, int(total_xp))
            if original_total_xp <= 0:
                return
            base_total_xp = self.apply_double_xp(original_total_xp)
            _guild_pct=self.guild_bonus_percent_v0926()
            total_xp=max(0,int(round(base_total_xp*(1.0+_guild_pct/100.0))))
            _mentor_pct = self.mentor_bonus_percent_v03050()
            if _mentor_pct:
                total_xp=max(0,int(round(total_xp*(1.0+_mentor_pct/100.0))))
                self.mentor_record_activity_v03051()

            self.session_summary_add("class_xp", total_xp)
            base_share, remainder = divmod(total_xp, len(active))
            _guild_note=f" Bonus Gildii +{_guild_pct}%: +{total_xp-base_total_xp}." if total_xp>base_total_xp else ""
            _event_note=" Event x2 EXP." if base_total_xp>original_total_xp else ""
            await self.send(
                f"EXP klas: {total_xp}. Aktywne klasy: {len(active)}. "
                "Pula jest dzielona między aktywne klasy." + _event_note + _guild_note
            )

            for index, class_name in enumerate(active):
                share = base_share + (1 if index < remainder else 0)
                result = self.server.db.add_class_mastery_xp(
                    self.account_id, class_name, share
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
                        await self.send(f"{class_name}: +{share} EXP klasy. Biegłość 600; Wzniesienie {ascension['rank']}, XP {ascension['xp']}{nxt}.")
                    else:
                        await self.send(f"{class_name}: +{share} EXP klasy. Biegłość {CLASS_MASTERY_MAX_LEVEL}, maksimum.")
                else:
                    await self.send(
                        f"{class_name}: +{share} EXP klasy. "
                        f"Biegłość {result['level']}, XP {result['xp']} z "
                        f"{result['next_xp']}."
                    )
