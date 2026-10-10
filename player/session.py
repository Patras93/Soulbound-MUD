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
from player.session_mixins.friends import SessionFriendsMixin
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
from player.session_mixins.ocean import SessionOceanV1000Mixin
from player.session_mixins.exploration_professions import SessionExplorationProfessionsV1100Mixin
from player.session_mixins.command_special_handlers import SessionCommandSpecialHandlersMixin
from player.session_mixins.activity_guidance import SessionActivityGuidanceV0560Mixin
from player.session_mixins.mercenary_taverns import SessionMercenaryTavernsMixin
from player.session_mixins.world_crises_v1220 import SessionWorldCrisesV1220Mixin
from player.session_mixins.quality_of_life_v1180 import SessionQualityOfLifeV1180Mixin
from player.session_mixins.upgrade_v1193 import SessionUpgradeV1193Mixin
from player.session_mixins.great_world import SessionGreatWorldV1200Mixin
from player.session_mixins.six_eras_v1310 import SessionSixErasV1310Mixin
from player.session_mixins.soul_ancients_v1330 import SessionSoulAncientsV1330Mixin
from player.session_mixins.imperial_economy_v1320 import SessionImperialEconomyV1320Mixin
from player.session_mixins.imperial_economy_v1321 import SessionImperialEconomyV1321Mixin
from player.session_mixins.living_empires_v1340 import SessionLivingEmpiresV1340Mixin
from player.session_mixins.ocean4_v1350 import SessionOcean4V1350Mixin
from player.session_mixins.economy4_v1360 import SessionEconomy4V1360Mixin
from player.session_mixins.legendary_achievements_v1370 import SessionLegendaryAchievementsV1370Mixin
from player.session_mixins.forgotten_v1500 import SessionForgottenV1500Mixin
from player.session_mixins.era_legends_v1600 import SessionEraLegendsV1600Mixin
from player.session_mixins.era_sky_v1700 import SessionSkyV1700Mixin
from player.session_mixins.command_registry import SessionCommandRegistryMixin
from player.session_mixins.command_loop import SessionCommandLoopMixin
from player.session_mixins.item_protection_v1280 import SessionItemProtectionV1280Mixin
from player.session_mixins.password_recovery_v1222 import SessionPasswordRecoveryV1222Mixin


class Session(
    SessionForgottenV1500Mixin,
    SessionSkyV1700Mixin,
    SessionEraLegendsV1600Mixin,
    SessionLegendaryAchievementsV1370Mixin,
    SessionEconomy4V1360Mixin,
    SessionOcean4V1350Mixin,
    SessionLivingEmpiresV1340Mixin,
    SessionImperialEconomyV1321Mixin,
    SessionItemProtectionV1280Mixin,
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
    SessionFriendsMixin,
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
    SessionOceanV1000Mixin,
    SessionExplorationProfessionsV1100Mixin,
    SessionCommandSpecialHandlersMixin,
    SessionActivityGuidanceV0560Mixin,
    SessionMercenaryTavernsMixin,
    SessionWorldCrisesV1220Mixin,
    SessionQualityOfLifeV1180Mixin,
    SessionUpgradeV1193Mixin,
    SessionGreatWorldV1200Mixin,
    SessionSoulAncientsV1330Mixin,
    SessionSixErasV1310Mixin,
    SessionImperialEconomyV1320Mixin,
    SessionCommandRegistryMixin,
    SessionPasswordRecoveryV1222Mixin,
    SessionCommandLoopMixin
):
    """Player session composed from focused subsystem mixins."""
    pass
