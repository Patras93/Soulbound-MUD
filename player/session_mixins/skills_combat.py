# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: skills_combat."""
from player.session_mixins.skill_learning import SessionSkillLearningMixin
from player.session_mixins.skill_queue_buffs import SessionSkillQueueBuffsMixin
from player.session_mixins.combat import SessionCombatMixin


from player.session_mixins.combat_rewards import party_drop_recipients_v0359

class SessionSkillsCombatMixin(
    SessionSkillLearningMixin,
    SessionSkillQueueBuffsMixin,
    SessionCombatMixin,
):
    """Compatibility aggregate; gameplay methods live in focused mixins."""
    pass
