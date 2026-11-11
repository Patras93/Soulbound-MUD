# -*- coding: utf-8 -*-
"""Oryginalne metody wydzielone w v109 bez zmiany algorytmow."""
# -*- coding: utf-8 -*-
"""HELP, changelog and skill help."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
import os
from difflib import get_close_matches
from core.classes_skills import effective_skill_mana_cost
from core.progression_600 import SKILL_MAX_LEVEL
from core.progression_resources import skill_xp_to_next
from player.session_mixins.exploration_progress import ALL_EXPLORATION_ROOMS, ROOMS, normalize_lookup_text
from player.session_mixins.io_auth_character import CLASS_SKILLS
from player.session_mixins.museum_bounty import BESTIARY_CATALOG
from storage.db_schema import FISH_RESOURCE_IDS
from systems.content_registry import LATEST_CHANGES, LATEST_CHANGES_TITLE
from data.current_help import get_help_catalogs as _current_help_catalogs
HELP_TOPICS = _current_help_catalogs()[0]
HELP_TOPIC_ALIASES = _current_help_catalogs()[1]
from world.world_state import _FINAL_SKILL_HELP_EXACT_INDEX, _FINAL_SKILL_HELP_SEARCH_ROWS



class HelpSkillsV109Mixin:
    def all_skill_help_entries(self):
            entries = []
            for class_name, skills in CLASS_SKILLS.items():
                for skill in skills:
                    entries.append((class_name, skill))
            return entries

    def skill_help_query_text(self, query):
            normalized = normalize_lookup_text(query)
            prefixes = (
                "skill ", "spell ", "czar ", "umiejetnosc ", "zdolnosc ",
                "info ", "opis ", "help ", "pomoc ",
            )
            changed = True
            while normalized and changed:
                changed = False
                for prefix in prefixes:
                    if normalized.startswith(prefix):
                        normalized = normalized[len(prefix):].strip()
                        changed = True
                        break
            return normalized

    def find_global_skill_help_matches(self, query):
            wanted = self.skill_help_query_text(query)
            if not wanted:
                return []

            # Najczęstszy przypadek (pełna nazwa, ID lub alias) jest O(1).
            exact = _FINAL_SKILL_HELP_EXACT_INDEX.get(wanted, ())
            if exact:
                unique = {}
                for class_name, skill in exact:
                    unique[skill["id"]] = (class_name, skill)
                return list(unique.values())

            # Fragmenty nazw są celowo dopuszczone, ale nigdy nie zgadujemy przy
            # wielu trafieniach. Skan wykonuje się tylko dla niepełnego zapytania.
            unique = {}
            for class_name, skill, normalized_names in _FINAL_SKILL_HELP_SEARCH_ROWS:
                if any(wanted in value for value in normalized_names):
                    unique[skill["id"]] = (class_name, skill)
            return list(unique.values())

    def skill_help_kind_label(self, kind):
            return {
                "damage": "obrażenia pojedynczego celu",
                "aoe_damage": "obrażenia obszarowe",
                "execute": "finisher / egzekucja",
                "drain": "obrażenia i wysysanie życia",
                "boost": "buff / wzmocnienie",
                "guard": "obrona / guard",
                "evade": "unik",
                "heal": "leczenie",
                "group_heal": "leczenie drużynowe",
                "regen": "regeneracja okresowa",
                "passive": "pasywna / automatyczna",
                "utility": "narzędzie użytkowe / trwałe ulepszenie",
            }.get(kind, str(kind or "nieznany"))

    def skill_help_scale_label(self, scale):
            return {
                "strength": "Siła",
                "dexterity": "Zręczność",
                "intelligence": "Inteligencja",
                "willpower": "Siła Woli",
                "attack": "Atak",
                "hp_difference": "różnica maksymalnego i bieżącego HP",
                "target_current_hp_percent": "procent bieżącego HP celu",
            }.get(scale, str(scale or "brak bezpośredniego skalowania statystyką"))

    def skill_help_effect_details(self, skill):
            parts = []
            kind = skill.get("kind")
            status = skill.get('olc_status')
            if isinstance(status, dict) and status.get('kind') in ('poison','burn','freeze','shock'):
                labels = {'poison':'trucizna', 'burn':'podpalenie',
                          'freeze':'zamrożenie', 'shock':'porażenie'}
                parts.append(f"Efekt po trafieniu: {labels[status['kind']]}, szansa bazowa {round(float(status['chance'])*100)} procent; bossowie mają dodatkowe odporności")
            if skill.get("scale"):
                parts.append("Skalowanie: " + self.skill_help_scale_label(skill.get("scale")))
            if "mult" in skill:
                parts.append(f"Mnożnik mocy: x{float(skill['mult']):.2f}")
            if kind == "execute" and "execute_mult" in skill:
                parts.append(f"Mnożnik egzekucji: x{float(skill['execute_mult']):.2f}")
            if kind == "boost" and "boost" in skill:
                pct = int(round((float(skill.get("boost", 1.0)) - 1.0) * 100))
                duration = skill.get("duration")
                if duration:
                    parts.append(f"Bazowe wzmocnienie: +{pct} procent przez {int(duration)} sekund")
                else:
                    parts.append(f"Bazowe wzmocnienie: +{pct} procent; czas działania wynika z mechaniki tej umiejętności")
            if kind == "guard" and "guard" in skill:
                parts.append(f"Bazowa redukcja następnego trafienia: {int(skill['guard'])}")
            if kind in ("heal", "group_heal") and "heal_pct" in skill:
                parts.append(f"Bazowe leczenie: {int(round(float(skill['heal_pct']) * 100))} procent maksymalnego HP")
            if kind == "drain" and "drain_pct" in skill:
                parts.append(f"Wysysanie życia: {int(round(float(skill['drain_pct']) * 100))} procent zadanych obrażeń")
            if skill.get("self_damage"):
                parts.append(f"Koszt własnego HP: {int(skill['self_damage'])}")
            if skill.get("self_damage_pct"):
                parts.append(f"Koszt własnego HP: {int(round(float(skill['self_damage_pct']) * 100))} procent")

            target_labels = {
                "self": "siebie",
                "one_ally": "jeden sojusznik",
                "one_enemy": "jeden przeciwnik",
                "one_target": "jeden cel",
                "all_allies": "wszyscy sojusznicy w lokacji",
                "party": "drużyna w lokacji",
            }
            source_target = skill.get("source_target_mode")
            if source_target:
                raw_targets = source_target if isinstance(source_target, (list, tuple)) else [source_target]
                parts.append(
                    "Cel źródłowy: " + ", ".join(
                        target_labels.get(str(value), str(value).replace("_", " "))
                        for value in raw_targets
                    )
                )

            stat_labels = {
                "attack": "Atak",
                "agi": "Zręczność/AGI",
                "agility": "Zręczność/AGI",
                "dexterity": "Zręczność",
                "int": "Inteligencja",
                "intelligence": "Inteligencja",
                "will": "Siła Woli",
                "willpower": "Siła Woli",
                "vitality": "Kondycja",
                "vit": "Kondycja",
                "critical_hit_chance": "szansa na trafienie krytyczne",
                "hp": "HP",
            }
            influences = skill.get("source_stat_influence")
            if influences:
                raw_stats = influences if isinstance(influences, (list, tuple)) else [influences]
                parts.append(
                    "Wpływ statystyk źródłowych: " + ", ".join(
                        stat_labels.get(str(value), str(value).replace("_", " "))
                        for value in raw_stats
                    )
                )

            properties = skill.get("source_properties")
            if properties:
                prop_labels = {
                    "cleanseable": "Cleanseable",
                    "dispelable": "Dispelable",
                    "dispellable": "Dispellable",
                    "extendable": "Extendable",
                    "reflectable": "Reflectable",
                    "silenceable": "Silenceable",
                    "multicastable": "Multicastable",
                }
                parts.append(
                    "Właściwości źródłowe: " + ", ".join(
                        prop_labels.get(str(value), str(value).replace("_", " "))
                        for value in properties
                    )
                )

            level_effect = skill.get("level_effect")
            if level_effect:
                level_effect_labels = {
                    "increases_duration": "Skill Level zwiększa czas działania",
                    "increases_healing_power": "Skill Level zwiększa moc leczenia",
                    "increases_accuracy_and_duration": "Skill Level zwiększa celność i czas działania",
                }
                parts.append(
                    level_effect_labels.get(
                        str(level_effect),
                        "Efekt Skill Level: " + str(level_effect).replace("_", " "),
                    )
                )
            return parts

    async def show_skill_help(self, query):
            wanted = self.skill_help_query_text(query)
            if not wanted:
                await self.send(
                    "Użycie: help skill <nazwa>, help <nazwa skilla> albo skill info <nazwa>. "
                    "Wpisz skillnames, aby usłyszeć wszystkie nazwy."
                )
                return True

            matches = self.find_global_skill_help_matches(wanted)
            if not matches:
                return False
            if len(matches) > 1:
                await self.send(
                    "Nazwa jest niejednoznaczna. Pasujące umiejętności: "
                    + "; ".join(
                        f"{skill['name']} ({class_name}, ID: {skill['id']})"
                        for class_name, skill in matches[:20]
                    )
                    + ". Użyj help skill <ID>, aby wybrać dokładnie właściwą umiejętność."
                )
                return True

            class_name, skill = matches[0]
            kind = skill.get("kind")
            queue_type = self.skill_queue_type(skill)
            mastery_needed = self.skill_required_mastery(skill)
            mastery_current = self.class_mastery_level(class_name)
            learned = self.server.db.knows_skill(self.account_id, skill["id"])
            active = class_name in self.active_class_names()
            mana = effective_skill_mana_cost(skill, class_name)
            base_cd = int(skill.get("cooldown", 0) or 0)

            await self.send(f"HELP SKILL: {skill['name']}.")
            await self.send(
                f"Klasa: {class_name}. Typ: {self.skill_help_kind_label(kind)}. "
                f"Wymagana Biegłość klasy: {mastery_needed}. "
                f"Kolejka: {self.skill_queue_type_label(queue_type)}."
            )
            cooldown_text = (
                f"Mechaniczny cooldown bazowy: {base_cd} sekund. "
                if skill.get("mechanic_cooldown")
                else "Cooldown zwykłego ponownego użycia: brak. "
            )
            await self.send(
                (f"Mana: {mana}. " if mana else "Mana: nie jest używana przez tę umiejętność. ")
                + cooldown_text
                + f"Opis: {skill.get('desc', 'Brak opisu.')}"
            )
            effect_parts = self.skill_help_effect_details(skill)
            if effect_parts:
                await self.send("Mechanika: " + ". ".join(effect_parts) + ".")

            teacher_id, teacher = self.class_teacher(class_name)
            if teacher:
                room_name = ROOMS.get(teacher.get("room"), {}).get("name", "nieznana lokacja")
                base_cost, final_cost, discount = self.class_codex_training_cost(class_name, skill)
                cost_text = self.training_cost_text(final_cost)
                await self.send(
                    f"Nauczyciel: {teacher['name']}, {room_name}. "
                    f"Aktualny koszt nauki: {cost_text}."
                )

            if learned:
                progress = self.skill_progress_data(skill)
                level = max(1, int(progress.get("level", 1)))
                effective_cd = self.effective_skill_cooldown(skill, level)
                if level >= SKILL_MAX_LEVEL:
                    progress_text = f"Skill Poziom {level}, maksymalny"
                else:
                    progress_text = (
                        f"Skill Poziom {level}, XP {progress.get('xp', 0)} z "
                        f"{skill_xp_to_next(level)}, użycia {progress.get('uses', 0)}"
                    )
                learned_cd_text = (
                    f" Mechaniczny cooldown przy tym Skill Level: {effective_cd} sekund."
                    if skill.get("mechanic_cooldown")
                    else " Bez cooldownu zwykłego ponownego użycia."
                )
                await self.send(
                    f"Status: nauczona. {progress_text}." + learned_cd_text
                )
            elif not active:
                await self.send(
                    f"Status: klasa {class_name} nie jest aktywna. Twoja Biegłość tej klasy: {mastery_current}."
                )
            elif mastery_current < mastery_needed:
                await self.send(
                    f"Status: jeszcze zablokowana. Biegłość {class_name}: {mastery_current} z wymaganych {mastery_needed}."
                )
            else:
                await self.send(
                    f"Status: odblokowana do nauki. Biegłość {class_name}: {mastery_current}."
                )

            if kind == "passive":
                await self.send(
                    f"Komendy: help skill {skill['name']}. Umiejętność działa automatycznie po nauczeniu i nie zajmuje slotu kolejki."
                )
            else:
                await self.send(
                    f"Komendy: skill {skill['name']} [cel]; kolejka dodaj {skill['name']}."
                )
            return True

