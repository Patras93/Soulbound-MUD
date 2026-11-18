# -*- coding: utf-8 -*-
"""Soulbound v0.49.0 Session assembly from focused mixins."""

from player.session_mixins.achievement_xp_v11331 import SessionAchievementXpV11331Mixin
from player.session_mixins.living_empire_v7000 import SessionLivingEmpireV7000Mixin
from player.session_mixins.profesje6 import SessionProfesje6Mixin
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
from player.session_mixins.master_professions_v2200 import SessionMasterProfessionsV2200Mixin
from player.session_mixins.eras_v2000 import SessionErasV2000Mixin
from player.session_mixins.economy4_v1360 import SessionEconomy4V1360Mixin
from player.session_mixins.legendary_achievements_v1370 import SessionLegendaryAchievementsV1370Mixin
from player.session_mixins.forgotten_v1500 import SessionForgottenV1500Mixin
from player.session_mixins.titans_v2100 import SessionTitansV2100Mixin
from player.session_mixins.era_legends_v1600 import SessionEraLegendsV1600Mixin
from player.session_mixins.era_sky_v1700 import SessionSkyV1700Mixin
from player.session_mixins.command_registry import SessionCommandRegistryMixin
from player.session_mixins.command_loop import SessionCommandLoopMixin
from player.session_mixins.item_protection_v1280 import SessionItemProtectionV1280Mixin
from player.session_mixins.password_recovery_v1222 import SessionPasswordRecoveryV1222Mixin


class Session(
    SessionAchievementXpV11331Mixin,
    SessionLivingEmpireV7000Mixin,
    SessionProfesje6Mixin,
    SessionTitansV2100Mixin,
    SessionForgottenV1500Mixin,
    SessionSkyV1700Mixin,
    SessionEraLegendsV1600Mixin,
    SessionLegendaryAchievementsV1370Mixin,
    SessionEconomy4V1360Mixin,
    SessionOcean4V1350Mixin,
    SessionMasterProfessionsV2200Mixin,
    SessionErasV2000Mixin,
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

    async def show_profession_atlas_v1602(self, query=""):
        """Complete live profession atlas; original historical 14 remain unchanged."""
        from core.bootstrap_economy_professions import TOOL_PROFESSION_MAP
        from core.progression_600 import PROFESSION_MAX_LEVEL, TOOL_MAX_LEVEL
        from systems.new_professions import PROFESSIONS, BASE_ACTIONS
        from player.session_mixins.atlas_codex import SessionAtlasCodexMixin
        from systems.profession_quest_expansion import PROFESSION_QUEST_SPECS_V0700
        from data.quests import QUESTS
        all_names = sorted(set(TOOL_PROFESSION_MAP.values()), key=str.casefold)
        lookup = self.normalize_description_query(query or "")
        if lookup in ("", "lista", "wszystkie", "all"):
            await self.send(f"ATLAS PROFESJI: liczba zawodów {len(all_names)}. Profesje i narzędzia: poziomy 1-{PROFESSION_MAX_LEVEL}.")
            for start in range(0, len(all_names), 8):
                await self.send("Profesje: " + "; ".join(all_names[start:start+8]) + ".")
            await self.send("Szczegóły: atlas profesje <nazwa>. Pozostałe działy: atlas odkrycia, ryby, rudy, drewno, geody, zioła.")
            return
        for name, (tool_type, tool_id, tool_name) in PROFESSIONS.items():
            if lookup in (self.normalize_description_query(name),
                          self.normalize_description_query(name).replace(' ', '_')):
                await self.send(f"ATLAS PROFESJI: {name}. Poziom 1-{PROFESSION_MAX_LEVEL}. Narzędzie: {tool_name}, do {TOOL_MAX_LEVEL}.")
                await self.send(f"Komendy: profesja status {name}; profesja czynnosci {name}; profesja kup {name}.")
                actions = [a for a in BASE_ACTIONS if a.prof == name]
                for a in actions:
                    await self.send(f"pracuj {name} {a.code} [próg] — {a.title}, teren: {a.region}, od poziomu {a.min_level}.")
                await self.send(f"Zlecenia: profesja zamowienie {name}; profesja oddaj {name}. Progi: 1, 25, 75, 150, 300, 500, 700.")
                await self.send(f"Powiązane zadania w katalogu: {sum(1 for q in QUESTS.values() if q.get('required_profession') == name or q.get('reward_profession') == name)}.")
                return
        from systems.profession_quest_expansion import PROFESSION_QUEST_SPECS_V0700
        historical = {self.normalize_description_query(spec[0])
                      for spec in PROFESSION_QUEST_SPECS_V0700}
        for tool_type, name in TOOL_PROFESSION_MAP.items():
            if lookup == self.normalize_description_query(name) and lookup not in historical:
                await self.send(f"ATLAS PROFESJI: {name}. Profesja 1-{PROFESSION_MAX_LEVEL}; narzędzie 1-{TOOL_MAX_LEVEL}.")
                await self.send(f"Typ narzędzia: {tool_type}. Postęp: profesje info / narzedzia info.")
                await self.send(f"Zadania powiązane: {sum(1 for q in QUESTS.values() if q.get('required_profession') == name or q.get('reward_profession') == name)}. Szczegóły: quest i help {name}.")
                return
        await SessionAtlasCodexMixin.show_profession_atlas_v1602(self, query)

    async def show_atlas(self, query=""):
        """Accurate dynamic profession index, with legacy resource atlas."""
        from core.bootstrap_economy_professions import TOOL_PROFESSION_MAP
        from player.session_mixins.atlas_codex import SessionAtlasCodexMixin
        q = self.normalize_description_query(query or "")
        if not q:
            await self.send(f"ATLAS. Odkrycia świata, profesje ({len(set(TOOL_PROFESSION_MAP.values()))}), ryby, drewno, rudy, geody i zioła.")
            await self.send("atlas profesje — aktualny katalog zawodów; atlas profesje <nazwa> — opis; atlas odkrycia — postępy świata.")
            await self.send("atlas ryby / rzeka / jezioro / morze / ocean; atlas drewno / rudy / geody / zioła; atlas <nazwa surowca>.")
            return
        from systems.profession_quest_expansion import PROFESSION_QUEST_SPECS_V0700
        historical = {name for name, *_ in PROFESSION_QUEST_SPECS_V0700}
        for name in TOOL_PROFESSION_MAP.values():
            if name not in historical and q == self.normalize_description_query(name):
                await self.show_profession_atlas_v1602(name)
                return
        await SessionAtlasCodexMixin.show_atlas(self, query)

    def max_hp(self):
        """Single-call snapshot removes duplicate EQ/SQLite lookups.

        Do not hold the cache across await, combat actions or separate calls:
        upgrading/removing equipment must take effect on the very next call.
        """
        key = '_read_only_equipment_cache_v1262'
        if key in self.__dict__:
            return super().max_hp()
        self.__dict__[key] = {}
        try:
            return super().max_hp()
        finally:
            self.__dict__.pop(key, None)

    def max_mana(self):
        """Use a fresh read-only equipment snapshot for this calculation only."""
        key = '_read_only_equipment_cache_v1262'
        if key in self.__dict__:
            return super().max_mana()
        self.__dict__[key] = {}
        try:
            return super().max_mana()
        finally:
            self.__dict__.pop(key, None)

    async def move(self, direction, preserve_auto_mining=False):
        """Measure manual and guide steps without changing travel permission."""
        from core.perf_diagnostics_v11320 import begin, finish
        scope, token = begin('move')
        try:
            return await super().move(direction, preserve_auto_mining=preserve_auto_mining)
        finally:
            finish(scope, token, minimum=0.25)

    async def look(self, query=""):
        """Add ground-drop information after the immutable native room view.

        This additive wrapper preserves the audited historical
        SessionPerceptionMapsMixin.look AST and all its early returns.
        """
        if self.character is None:
            await self.send('Najpierw wybierz postać w menu.')
            return
        await SessionPerceptionMapsMixin.look(self, query)
        if not str(query or "").strip() and self.character:
            if self.server.world.room_ground_loot(self.character.room_id):
                await self.show_ground_loot()

# v12.00.8: game-mechanics-preserving sound events layered above audited methods.
from systems.v115.optional_sound import install_sound_hooks_v1208 as _sound_install_v1208
_sound_install_v1208(Session)
