# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: skills_combat."""
from player.session_mixins.skill_learning import SessionSkillLearningMixin
from player.session_mixins.skill_queue_buffs import SessionSkillQueueBuffsMixin
from player.session_mixins.combat import SessionCombatMixin
from core.classes_skills import CLASS_SKILLS, MEC_PROTOCOL_SKILLS_V11155
from core.progression_resources import v0190_scaled_gain
from core.bootstrap_economy_professions import V019_SAFE_INT
from core.progression_600 import SKILL_MAX_LEVEL
from systems.experience_bank_v2011 import banked_experience_v2011
import random


from player.session_mixins.combat_rewards import party_drop_recipients_v0359

class SessionSkillsCombatMixin(
    SessionSkillLearningMixin,
    SessionSkillQueueBuffsMixin,
    SessionCombatMixin,
):
    """Compatibility aggregate and current skill-use XP tuning."""

    async def grant_skill_use_xp(self, skill):
        """Real skill use only. Keep the historical method and AST untouched.

        Gain is based on the already established independent reward curve, not
        on next-level requirements. The progressive multiplier corrects the
        extremely low skill gains at levels 1-800 without changing thresholds,
        cooldowns, bonuses, EXP Bank rules or account-wide Multi Cap.
        """
        current = self.skill_progress_data(skill)
        skill_level = max(1, int(current.get('level', 1)))
        content_stage = self.skill_content_stage_v11342(skill)
        raw = 25 + random.randint(0, 10)
        base = v0190_scaled_gain(raw, skill_level, 'skill', 30)
        base = max(1, int(round(
            base * self.progression_content_multiplier_v11342(content_stage)
        )))
        # v113.00.32: approx. 125-450 active casts per skill level, before
        # real Multi Cap, event bonuses and local difficulty. No requirement-
        # linked feedback: changing skill_xp_to_next never increases rewards.
        boosted = min(V019_SAFE_INT, base * (48 + skill_level // 2))
        # At the real maximum there is no payable skill XP, so never emit a
        # phantom HALF_CAP/FULL_CAP event for a skill already at its limit.
        gain = 0 if skill_level >= SKILL_MAX_LEVEL else self.apply_double_xp(boosted)
        if gain:
            gain = banked_experience_v2011(
                self.server.db, self.account_id, gain, 'skill', skill_level,
                source_key=skill['id'],
            )
        result = self.server.db.add_skill_xp(self.account_id, skill['id'], gain)
        if result['level_ups']:
            await self.send(
                f"{skill['name']} awansuje na Skill Level {result['level']}.",
                combat_detail='essential' if self.combat_mob_key else None,
            )
        if result['level'] >= SKILL_MAX_LEVEL:
            await self.send(
                f"{skill['name']}: Skill Level {SKILL_MAX_LEVEL}. Maksymalny poziom.",
                combat_detail='full' if self.combat_mob_key else None,
            )
        else:
            await self.send(
                f"{skill['name']}: Skill XP +{gain}. "
                f"Level {result['level']}, XP {result['xp']} z {result['next_xp']}.",
                combat_detail='full' if self.combat_mob_key else None,
            )
        # Existing class-passive rule: 25% of the *paid* active skill XP.
        # No extra casts/uses, no foreign-class or unrelated Mec protocols.
        if str(skill.get('kind', '')) != 'passive':
            skill_class = self.skill_class_name(skill)
            passive_gain = max(1, gain // 4)
            for passive in CLASS_SKILLS.get(skill_class, ()): 
                if passive.get('kind') != 'passive' or passive.get('id') == skill.get('id'):
                    continue
                if not self.server.db.knows_skill(self.account_id, passive['id']):
                    continue
                protocol_specials = MEC_PROTOCOL_SKILLS_V11155.get(passive['id'])
                if protocol_specials is not None and str(skill.get('mec_special', '')) not in set(protocol_specials):
                    continue
                passive_level = max(1, int(self.skill_progress_data(passive).get('level', 1)))
                passive_paid = banked_experience_v2011(
                    self.server.db, self.account_id, passive_gain,
                    'skill', passive_level, source_key=passive['id'],
                )
                self.server.db.add_skill_xp(self.account_id, passive['id'], passive_paid)
        return result
