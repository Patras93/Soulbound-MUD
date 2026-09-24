# -*- coding: utf-8 -*-
"""Soulbound v0.49.0 Session assembly from focused mixins."""

from player.session_mixins.core_progression import SessionCoreProgressionMixin
from player.session_mixins.io_auth_character import SessionIOAuthCharacterMixin
from player.session_mixins.equipment_stats import SessionEquipmentStatsMixin
from player.session_mixins.perception_maps import SessionPerceptionMapsMixin
from player.session_mixins.progress_titles import SessionProgressTitlesV0580Mixin
from player.session_mixins.progress_gaps import SessionProgressGapsV0590Mixin
from player.session_mixins.crafting_orders import SessionCraftingOrdersV0600Mixin
from player.session_mixins.equipment_compare import SessionEquipmentCompareV0600Mixin
from player.session_mixins.item_sources import SessionItemSourcesV0610Mixin
from player.session_mixins.world_progression import SessionWorldProgressionMixin
from player.session_mixins.help_codex_profile import SessionHelpCodexProfileMixin
from player.session_mixins.mail_attachments import SessionMailAttachmentsV0614Mixin
from player.session_mixins.social_expansion import SessionSocialExpansionMixin
from player.session_mixins.courier_delivery import SessionCourierDeliveryMixin
from player.session_mixins.movement_party_social import SessionMovementPartySocialMixin
from player.session_mixins.professions_storage_guide import SessionProfessionsStorageGuideMixin
from player.session_mixins.admin_gathering_sales import SessionAdminGatheringSalesMixin
from player.session_mixins.crafting_inventory_equipment import SessionCraftingInventoryEquipmentMixin
from player.session_mixins.quests import SessionQuestsMixin
from player.session_mixins.skills_combat import SessionSkillsCombatMixin
from player.session_mixins.crafting_expansion import SessionCraftingExpansionV03114Mixin
from player.session_mixins.forge_guilds import SessionForgeGuildsMixin
from player.session_mixins.progression_accessibility import SessionProgressionAccessibilityV03052Mixin
from player.session_mixins.professions import SessionProfessionsV03053Mixin
from player.session_mixins.tech_crafting import SessionTechCraftingV03111Mixin
from player.session_mixins.milestone import SessionMilestoneV0320Mixin
from player.session_mixins.command_special_handlers import SessionCommandSpecialHandlersMixin
from player.session_mixins.activity_guidance import SessionActivityGuidanceV0560Mixin
from player.session_mixins.command_registry import SessionCommandRegistryMixin
from player.session_mixins.command_loop import SessionCommandLoopMixin


class Session(
    SessionCoreProgressionMixin,
    SessionIOAuthCharacterMixin,
    SessionEquipmentStatsMixin,
    SessionPerceptionMapsMixin,
    SessionProgressTitlesV0580Mixin,
    SessionProgressGapsV0590Mixin,
    SessionCraftingOrdersV0600Mixin,
    SessionEquipmentCompareV0600Mixin,
    SessionItemSourcesV0610Mixin,
    SessionWorldProgressionMixin,
    SessionHelpCodexProfileMixin,
    SessionMailAttachmentsV0614Mixin,
    SessionSocialExpansionMixin,
    SessionCourierDeliveryMixin,
    SessionMovementPartySocialMixin,
    SessionProfessionsStorageGuideMixin,
    SessionAdminGatheringSalesMixin,
    SessionCraftingInventoryEquipmentMixin,
    SessionQuestsMixin,
    SessionSkillsCombatMixin,
    SessionCraftingExpansionV03114Mixin,
    SessionForgeGuildsMixin,
    SessionProgressionAccessibilityV03052Mixin,
    SessionProfessionsV03053Mixin,
    SessionTechCraftingV03111Mixin,
    SessionMilestoneV0320Mixin,
    SessionCommandSpecialHandlersMixin,
    SessionActivityGuidanceV0560Mixin,
    SessionCommandRegistryMixin,
    SessionCommandLoopMixin
):
    """Player session composed from focused subsystem mixins."""
    pass
