# v4.20.0: bound, AST-identical method implementations (MRO unchanged)
from core.legacy_method_binding_v4200 import bind_legacy_method_v4200 as _sb420_bind
import player.session_methods_v4200.skilllearning_part01 as _sb420_src_01
# SessionSkillLearningMixin.unlock -> player/session_methods_v4200/skilllearning_part01.py
# SessionSkillLearningMixin.handle_job_set -> player/session_methods_v4200/skilllearning_part01.py
# SessionSkillLearningMixin.natural_skill_from_input -> player/session_methods_v4200/skilllearning_part01.py
# SessionSkillLearningMixin.find_skill_from_input -> player/session_methods_v4200/skilllearning_part01.py
# SessionSkillLearningMixin.class_codex_class_name -> player/session_methods_v4200/skilllearning_part01.py
# SessionSkillLearningMixin.show_class_codex -> player/session_methods_v4200/skilllearning_part01.py
# SessionSkillLearningMixin.show_skill_catalog_names -> player/session_methods_v4200/skilllearning_part01.py
# SessionSkillLearningMixin.show_skills -> player/session_methods_v4200/skilllearning_part01.py
# SessionSkillLearningMixin.show_spells -> player/session_methods_v4200/skilllearning_part01.py
import player.session_methods_v4200.skilllearning_part02 as _sb420_src_02
# SessionSkillLearningMixin.protected_friendly_npc -> player/session_methods_v4200/skilllearning_part02.py
# SessionSkillLearningMixin.reject_player_attack -> player/session_methods_v4200/skilllearning_part02.py
# SessionSkillLearningMixin.skill_content_stage_v11342 -> player/session_methods_v4200/skilllearning_part02.py
# SessionSkillLearningMixin.grant_skill_use_xp -> player/session_methods_v4200/skilllearning_part02.py
# SessionSkillLearningMixin.skill_combat_target -> player/session_methods_v4200/skilllearning_part02.py
# SessionSkillLearningMixin.apply_boss_defense -> player/session_methods_v4200/skilllearning_part02.py
# SessionSkillLearningMixin.boss_phase_multiplier -> player/session_methods_v4200/skilllearning_part02.py
import player.session_methods_v4200.skilllearning_part03 as _sb420_src_03
# SessionSkillLearningMixin.boss_attack_profile -> player/session_methods_v4200/skilllearning_part03.py
# SessionSkillLearningMixin.mec_intercept_incoming_attack_v11196 -> player/session_methods_v4200/skilllearning_part03.py
import player.session_methods_v4200.skilllearning_part04 as _sb420_src_04
# SessionSkillLearningMixin.enemy_counterattack -> player/session_methods_v4200/skilllearning_part04.py
# SessionSkillLearningMixin.natural_learn_skill_from_input -> player/session_methods_v4200/skilllearning_part04.py
# SessionSkillLearningMixin.learn_class_skill -> player/session_methods_v4200/skilllearning_part04.py

# -*- coding: utf-8 -*-
"""Skill discovery, catalog, learning and target validation."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import math
import random
import time
from core.bootstrap_economy_professions import SOUL_MILESTONE_TIERS, SOUL_TRIAL_QUEST_IDS
from core.classes_skills import (
    CLASSES, CLASS_SKILLS, NATURAL_SKILL_INTENTS, ROOMS, effective_skill_mana_cost,
    MEC_PROTOCOL_SKILLS_V11155,
)
from core.progression_600 import (
    SKILL_MAX_LEVEL, SOUL_MAX_TIER, SOUL_TIER_THRESHOLDS,
    soul_tier_title_for_class, soul_weapon_trait_for_tier_v11193,
)
from core.progression_resources import (
    skill_cooldown_multiplier, skill_xp_to_next, v0190_mob_stage,
    v0190_scaled_gain, skill_power_multiplier,
)
from network.protocol_gameplay_utils import find_by_name, normalize_lookup_text
from systems.content_registry import MOB_TEMPLATES, NPCS, QUESTS
from systems.soul_ancients_v1330 import ancient_attack
from systems.soul_evolutions_v1332 import council_allies
from systems.equipment_crafting import GUILD_REPUTATION_MAX
from world.economy_quests import v0863_is_boss_template


class SessionSkillLearningMixin:
    async def unlock(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method unlock")

    def class_skills(self):
            skills = []
            for class_name in self.active_class_names():
                skills.extend(CLASS_SKILLS.get(class_name, []))
            return skills

    def selected_job_ability(self, slot_type):
            skill_id=self.server.db.job_ability_slot(self.account_id,slot_type)
            return self.skill_by_id(skill_id) if skill_id else None

    def job_ability_selected(self, slot_type, skill_id):
            return self.server.db.job_ability_slot(self.account_id,slot_type)==str(skill_id)

    async def handle_job_set(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method handle_job_set")

    def class_teacher(self, class_name=None):
            wanted = class_name or self.character.class_name
            for npc_id, npc in NPCS.items():
                if npc.get("teacher_class") == wanted:
                    return npc_id, npc
            return None, None

    def normalized_skill_text(self, value):
            return self.normalize_description_query(value)

    def skill_natural_tokens(self, skill):
            tokens = set()
            names = [skill["name"], skill["id"]] + skill.get("aliases", [])
            names += skill.get("natural_tags", [])

            for value in names:
                normalized = self.normalized_skill_text(value)
                if not normalized:
                    continue
                tokens.add(normalized)
                tokens.update(normalized.split())

            return tokens

    def natural_skill_from_input(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method natural_skill_from_input")

    def find_skill_from_input(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method find_skill_from_input")

    def class_codex_class_name(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method class_codex_class_name")

    def class_codex_training_cost(self, class_name, skill):
            base_cost = self.skill_training_cost_silver(skill)
            discount = self.character.guild_training_discount(class_name)
            final_cost = max(1, int(round(base_cost * (1.0 - discount))))
            return base_cost, final_cost, discount

    async def show_class_codex(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_class_codex")

    async def show_all_skill_names(self):
            await self.send("NAZWY SKILLI WSZYSTKICH KLAS")
            for class_name in [cls[0] for cls in CLASSES]:
                skills = CLASS_SKILLS.get(class_name, [])
                names = ", ".join(
                    f"{index}. {skill['name']}"
                    for index, skill in enumerate(skills, 1)
                )
                await self.send(f"{class_name}: {names}.")
            await self.send(
                "Nazw możesz używać w komendach skill <nazwa> oraz naucz <nazwa>."
            )

    async def show_skill_catalog_names(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_skill_catalog_names")

    async def show_skills(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_skills")

    async def show_spells(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_spells")

    def protected_friendly_npc(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method protected_friendly_npc")

    async def reject_friendly_npc_attack(self, query):
            npc = self.protected_friendly_npc(query)
            if not npc:
                return False

            await self.send(
                f"{npc['name']} jest pokojowym i chronionym NPC-em. "
                "Sprzedawców, nauczycieli, postaci zadaniowych i innych "
                "pomocnych NPC-ów nie można atakować ani zabijać."
            )
            return True

    def protected_player_target(self, query):
            raw = normalize_lookup_text(str(query or "").strip())
            if not raw:
                return None
            for session in list(self.server.sessions):
                if session.closed or not session.character:
                    continue
                if session.character.room_id != self.character.room_id:
                    continue
                if normalize_lookup_text(session.character.name) == raw:
                    return session
            return None

    async def reject_player_attack(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method reject_player_attack")

    def skill_progress_data(self, skill):
            if not self.server.db.knows_skill(self.account_id, skill["id"]):
                return {"level": 0, "xp": 0, "uses": 0}
            row = self.server.db.skill_progress(self.account_id, skill["id"])
            return {
                "level": int(row["level"]),
                "xp": int(row["xp"]),
                "uses": int(row["uses"]),
            }

    def effective_skill_cooldown(self, skill, skill_level):
            if not skill.get("mechanic_cooldown"):
                return 0
            return max(
                1,
                int(round(int(skill.get("cooldown", 0) or 0) * skill_cooldown_multiplier(skill_level)))
            )

    def skill_content_stage_v11342(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method skill_content_stage_v11342")

    async def grant_skill_use_xp(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method grant_skill_use_xp")

    def skill_scale_value(self, scale):
            # v0.34.6: respektuj autorskie źródło mocy konkretnego skilla.
            # Łowca/Łotrzyk oraz zręcznościowe techniki Mnicha/Meca/Inżyniera
            # muszą naprawdę liczyć Zręczność zamiast wpadać w fallback Siły.
            scale = str(scale or "strength").lower()
            if scale == "intelligence":
                return self.effective_intelligence()
            if scale == "dexterity":
                return self.effective_dexterity()
            return self.effective_strength()

    def engagement_block_message(self, mob):
            name = MOB_TEMPLATES[mob.template_id]["name"]
            if self.server.party_key_for_account(self.account_id) is None:
                return f"{name} walczy już z innym graczem."
            return f"{name} walczy już z graczem spoza twojej drużyny."

    async def skill_combat_target(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method skill_combat_target")

    async def apply_boss_defense(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method apply_boss_defense")

    async def boss_phase_multiplier(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method boss_phase_multiplier")

    async def boss_attack_profile(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method boss_attack_profile")

    async def mec_intercept_incoming_attack_v11196(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method mec_intercept_incoming_attack_v11196")

    async def enemy_counterattack(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method enemy_counterattack")

    def natural_learn_skill_from_input(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method natural_learn_skill_from_input")

    async def learn_class_skill(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method learn_class_skill")

# v4.20.0: exact historical implementations rebound onto original class.
SessionSkillLearningMixin.unlock = _sb420_bind(_sb420_src_01.unlock, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.handle_job_set = _sb420_bind(_sb420_src_01.handle_job_set, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.natural_skill_from_input = _sb420_bind(_sb420_src_01.natural_skill_from_input, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.find_skill_from_input = _sb420_bind(_sb420_src_01.find_skill_from_input, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.class_codex_class_name = _sb420_bind(_sb420_src_01.class_codex_class_name, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.show_class_codex = _sb420_bind(_sb420_src_01.show_class_codex, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.show_skill_catalog_names = _sb420_bind(_sb420_src_01.show_skill_catalog_names, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.show_skills = _sb420_bind(_sb420_src_01.show_skills, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.show_spells = _sb420_bind(_sb420_src_01.show_spells, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.protected_friendly_npc = _sb420_bind(_sb420_src_02.protected_friendly_npc, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.reject_player_attack = _sb420_bind(_sb420_src_02.reject_player_attack, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.skill_content_stage_v11342 = _sb420_bind(_sb420_src_02.skill_content_stage_v11342, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.grant_skill_use_xp = _sb420_bind(_sb420_src_02.grant_skill_use_xp, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.skill_combat_target = _sb420_bind(_sb420_src_02.skill_combat_target, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.apply_boss_defense = _sb420_bind(_sb420_src_02.apply_boss_defense, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.boss_phase_multiplier = _sb420_bind(_sb420_src_02.boss_phase_multiplier, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.boss_attack_profile = _sb420_bind(_sb420_src_03.boss_attack_profile, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.mec_intercept_incoming_attack_v11196 = _sb420_bind(_sb420_src_03.mec_intercept_incoming_attack_v11196, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.enemy_counterattack = _sb420_bind(_sb420_src_04.enemy_counterattack, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.natural_learn_skill_from_input = _sb420_bind(_sb420_src_04.natural_learn_skill_from_input, globals(), "SessionSkillLearningMixin")
SessionSkillLearningMixin.learn_class_skill = _sb420_bind(_sb420_src_04.learn_class_skill, globals(), "SessionSkillLearningMixin")

