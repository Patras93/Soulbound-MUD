# -*- coding: utf-8 -*-
"""Declarative command router introduced in Soulbound v0.39.0.

Simple commands are data here; only commands with custom branching remain in
command_loop.py. This keeps aliases and direct handler calls easy to audit.
"""

import asyncio

from core.command_catalog import COMMAND_CATALOG, COMMAND_LOOP_BREAK
from world.economy_quests import LOOT_FILTER_INPUTS

COMMAND_TEXT = object()
COMMAND_NAME = object()

COMMAND_REGISTRY = {
    'classguild': ('show_guild', (COMMAND_TEXT,), {}),
    'guildquest': ('guild_class_quest', (COMMAND_TEXT,), {}),
    'guildexam': ('guild_exam', (COMMAND_TEXT,), {}),
    'guildbounty': ('guild_bounty', (COMMAND_TEXT,), {}),
    'bounty': ('handle_bounty', (COMMAND_TEXT,), {}),
    'legendarycontracts': ('handle_legendary_contracts_v022', (COMMAND_TEXT,), {}),
    'worldprojects': ('show_world_projects_v022', (COMMAND_TEXT,), {}),
    'worldproject': ('handle_world_project_v022', (COMMAND_TEXT,), {}),
    'fishrecords': ('show_fish_records_v022', (COMMAND_TEXT,), {}),
    'chronicle': ('show_server_chronicle_v03811', (COMMAND_TEXT,), {}),
    'help': ('show_help', (COMMAND_TEXT,), {}),
    'wimpy': ('handle_wimpy', (COMMAND_TEXT,), {}),
    'eventxp': ('show_double_xp_event', (), {}),
    'encoding': ('set_encoding', (COMMAND_TEXT,), {}),
    'describe': ('describe_target', (COMMAND_TEXT,), {}),
    'changes': ('show_latest_changes', (), {}),
    'progress': ('show_progress', (COMMAND_TEXT,), {}),
    'historybuffer': ('show_history_buffer', (COMMAND_TEXT,), {}),
    'regionprogress': ('show_region_progress', (), {}),
    'exploration': ('show_exploration', (COMMAND_TEXT,), {}),
    'achievements': ('show_achievements', (), {}),
    'titles': ('show_titles', (), {}),
    'title': ('set_title', (COMMAND_TEXT,), {}),
    'collection': ('show_collection', (COMMAND_TEXT,), {}),
    'collection2': ('collection_codex_v03052', (COMMAND_TEXT,), {}),
    'completion': ('completion_v03052', (), {}),
    'deathrecap': ('recap2_v0320', (), {'death': True}),
    'combatrecap': ('recap2_v0320', (), {'death': False}),
    'loothistory': ('loot_history_v03052', (COMMAND_TEXT,), {}),
    'nvda': ('accessibility_v03052', (COMMAND_TEXT,), {}),
    'museum': ('show_museum_v0260', (COMMAND_TEXT,), {}),
    'prestige': ('show_prestige_v0260', (), {}),
    'bosscodex': ('show_boss_codex', (COMMAND_TEXT,), {}),
    'drophistory': ('loot_history_v03052', (COMMAND_TEXT,), {}),
    'lootfilter': ('set_loot_filter', (COMMAND_TEXT,), {}),
    'combatlog': ('set_combat_log', (COMMAND_TEXT,), {}),
    'look': ('look', (COMMAND_TEXT,), {}),
    'corpse': ('show_corpses', (COMMAND_TEXT,), {}),
    'lootcorpse': ('loot_corpse', (COMMAND_TEXT,), {}),
    'getcorpseitem': ('get_from_corpse', (COMMAND_TEXT,), {}),
    'cryptinfo': ('show_crypt_info', (), {}),
    'astralinfo': ('show_astral_info', (), {}),
    'astralportal': ('use_astral_portal', (COMMAND_TEXT,), {}),
    'portal': ('use_crypt_portal', (COMMAND_TEXT,), {}),
    'exits': ('show_exits', (COMMAND_TEXT,), {}),
    'map': ('show_map', (COMMAND_TEXT,), {}),
    'cartography': ('show_cartography_v024', (), {}),
    'worldevents': ('show_world_events', (), {}),
    'dynamicevents': ('show_dynamic_events_v029', (), {}),
    'nemesis': ('show_nemesis_v029', (), {}),
    'globalgenerator': ('show_global_generator_v025', (COMMAND_TEXT,), {}),
    'weather': ('show_weather_v015', (), {}),
    'biomemastery': ('show_biome_mastery_v015', (COMMAND_TEXT,), {}),
    'worldquest': ('handle_dynamic_world_quest_v015', (COMMAND_TEXT,), {}),
    'factions': ('show_factions_v016', (COMMAND_TEXT,), {}),
    'worldbosses': ('show_world_bosses_v016', (), {}),
    'legendaryrares': ('show_legendary_rares_v016', (), {}),
    'travelers': ('show_travelers_v016', (), {}),
    'artifacts': ('show_artifacts_v017', (), {}),
    'biomesets': ('show_biome_sets_v017', (COMMAND_TEXT,), {}),
    'factionstories': ('show_faction_stories_v017', (COMMAND_TEXT,), {}),
    'season': ('show_season_v018', (), {}),
    'expeditions': ('show_expeditions_v018', (), {}),
    'expedition': ('start_expedition_v018', (COMMAND_TEXT,), {}),
    'transport': ('transport_v03052', (COMMAND_TEXT,), {}),
    'greatruins': ('show_great_ruins_v018', (), {}),
    'legendaryevents': ('show_legendary_events_v018', (), {}),
    'endless': ('show_endless_v018', (), {}),
    'megadungeons': ('show_megadungeons_v020', (), {}),
    'gauntlets': ('show_gauntlets_v020', (), {}),
    'gauntlet': ('start_gauntlet_v020', (COMMAND_TEXT,), {}),
    'mythicbosses': ('show_mythic_bosses_v020', (), {}),
    'artifactupgrade': ('artifact_upgrade_v020', (COMMAND_TEXT,), {}),
    'endgamegoals': ('show_endgame_goals_v020', (), {}),
    'ascension': ('show_ascension_v021', (COMMAND_TEXT,), {}),
    'worldtier': ('handle_world_tier_v021', (COMMAND_TEXT,), {}),
    'mythicsets': ('show_mythic_sets_v021', (COMMAND_TEXT,), {}),
    'endlessgauntlet': ('handle_endless_gauntlet_v021', (COMMAND_TEXT,), {}),
    'mythicprogression': ('show_mythic_progression_v021', (), {}),
    'instancesecret': ('discover_instance_secret', (), {}),
    'bestiary': ('show_bestiary', (COMMAND_TEXT,), {}),
    'atlas': ('show_atlas', (COMMAND_TEXT,), {}),
    'classcodex': ('show_class_codex', (COMMAND_TEXT,), {}),
    'chest': ('open_treasure_chest', (COMMAND_TEXT,), {}),
    'where': ('show_where', (), {}),
    'expareas': ('show_exp_areas', (COMMAND_TEXT,), {}),
    'terraininfo': ('show_terrain_info', (COMMAND_TEXT,), {}),
    'dungeon_exit': ('dungeon_exit', (), {}),
    'dungeonexit': ('dungeon_exit', (), {}),
    'who': ('who', (), {}),
    'say': ('say', (COMMAND_TEXT,), {}),
    'gossip': ('channel_broadcast_v03050', ('gossip', COMMAND_TEXT), {}),
    'newbie': ('channel_broadcast_v03050', ('newbie', COMMAND_TEXT), {}),
    'trade': ('channel_broadcast_v03050', ('trade', COMMAND_TEXT), {}),
    'ignore': ('handle_ignore_v03051', (COMMAND_TEXT, False), {}),
    'unignore': ('handle_ignore_v03051', (COMMAND_TEXT, True), {}),
    'afk': ('handle_afk_v03051', (COMMAND_TEXT,), {}),
    'whois': ('whois_v03051', (COMMAND_TEXT,), {}),
    'mail': ('handle_mail_v03051', (COMMAND_TEXT,), {}),
    'board': ('handle_board_v03051', (COMMAND_TEXT,), {}),
    'lfg': ('handle_lfg_v03051', (COMMAND_TEXT,), {}),
    'newbieprotect': ('newbie_protection_v03051', (COMMAND_TEXT,), {}),
    'house': ('housing_v03052', (COMMAND_TEXT,), {}),
    'records': ('records_v03051', (COMMAND_TEXT,), {}),
    'inspect': ('inspect_v03051', (COMMAND_TEXT,), {}),
    'inspectprivacy': ('inspect_privacy_v03051', (COMMAND_TEXT,), {}),
    'tell': ('tell', (COMMAND_TEXT,), {}),
    'reply': ('reply_private_v0928', (COMMAND_TEXT,), {}),
    'party': ('handle_party', (COMMAND_TEXT,), {}),
    'partyinvite': ('party_invite', (COMMAND_TEXT,), {}),
    'partyaccept': ('party_accept', (), {}),
    'partydecline': ('party_decline', (), {}),
    'partyleave': ('leave_party', (), {'announce': True}),
    'partykick': ('party_kick', (COMMAND_TEXT,), {}),
    'partydisband': ('disband_party', (), {}),
    'partyleader': ('transfer_party_leader', (COMMAND_TEXT,), {}),
    'partyprotect': ('protect_party', (COMMAND_TEXT,), {}),
    'partychat': ('party_chat', (COMMAND_TEXT,), {}),
    'assist': ('assist_party_member', (COMMAND_TEXT,), {}),
    'partyrevive': ('revive_party_member_v0371', (COMMAND_TEXT,), {}),
    'selfrespawn': ('respawn_from_downed_v0371', (), {'auto': False}),
    'charisma': ('show_charisma', (), {}),
    'multiclass': ('handle_multiclass', (COMMAND_TEXT,), {}),
    'rest': ('handle_rest', (COMMAND_TEXT,), {}),
    'stats': ('show_stats', (COMMAND_TEXT,), {}),
    'hp': ('show_hp', (), {}),
    'score': ('show_score', (), {}),
    'level': ('show_character_level', (), {}),
    'xp': ('show_character_xp', (), {}),
    'mana': ('handle_mana_command', (COMMAND_TEXT,), {}),
    'declension': ('show_name_declension', (), {}),
    'skills': ('show_skills', (COMMAND_TEXT,), {}),
    'spells': ('show_spells', (COMMAND_TEXT,), {}),
    'skillnames': ('show_all_skill_names', (), {}),
    'skillqueue': ('handle_skill_queue', (COMMAND_TEXT,), {}),
    'learn': ('learn_class_skill', (COMMAND_TEXT,), {}),
    'soul': ('show_soul', (COMMAND_TEXT,), {}),
    'money': ('show_money', (), {}),
    'bank': ('handle_bank', (COMMAND_TEXT,), {}),
    'net': ('show_container', ('net',), {}),
    'bag': ('show_container', ('bag',), {}),
    'woodpile': ('show_container', ('woodpile',), {}),
    'herbbag': ('show_container', ('herbbag',), {}),
    'craftbox': ('show_craftbox_v0925', (COMMAND_TEXT,), {}),
    'salvage': ('salvage_equipment_v0925', (COMMAND_TEXT,), {}),
    'reforge': ('reforge_equipment_v0925', (COMMAND_TEXT,), {}),
    'equpgrade': ('upgrade_equipment_v03042', (COMMAND_TEXT,), {}),
    'runes': ('handle_runes_v03114', (COMMAND_TEXT,), {}),
    'socketrune': ('socket_rune_v0925', (COMMAND_TEXT,), {}),
    'playerguild': ('handle_guild_v0926', (COMMAND_TEXT,), {}),
    'masteryachievements': ('show_mastery_achievements_v0925', (), {}),
    'put': ('put_in_container', (COMMAND_TEXT,), {}),
    'take': ('take_from_container', (COMMAND_TEXT,), {}),
    'professions': ('show_professions', (COMMAND_TEXT,), {}),
    'ranks': ('show_profession_ranks', (), {}),
    'tools': ('show_tools', (COMMAND_TEXT,), {}),
    'toolinfo_fishing': ('show_single_tool', ('fishing',), {}),
    'toolinfo_mining': ('show_single_tool', ('mining',), {}),
    'toolinfo_woodcutting': ('show_single_tool', ('woodcutting',), {}),
    'toolinfo_crafting': ('show_single_tool', ('crafting',), {}),
    'toolinfo_cooking': ('show_single_tool', ('cooking',), {}),
    'toolinfo_herbalism': ('show_single_tool', ('herbalism',), {}),
    'toolinfo_alchemy': ('show_single_tool', ('alchemy',), {}),
    'toolinfo_jewelcrafting': ('show_single_tool', ('jewelcrafting',), {}),
    'tiers': ('show_tool_tiers', (), {}),
    'guide': ('start_guide_task', (COMMAND_TEXT,), {}),
    'route': ('show_route', (COMMAND_TEXT,), {}),
    'location': ('show_location', (), {}),
    'mineinfo': ('show_mine_info', (), {}),
    'sell': ('sell_command', (COMMAND_TEXT,), {}),
    'recipes': ('show_recipes', (COMMAND_TEXT,), {}),
    'smelt': ('smelt_item_v03114', (COMMAND_TEXT,), {}),
    'materialconversion': ('material_conversion_v03114', (), {}),
    'refine': ('refine_v03114', (COMMAND_TEXT,), {}),
    'socketcraft': ('socket_craft_v03114', (COMMAND_TEXT,), {}),
    'vmaxupgrade': ('vmax_upgrade_v03114', (COMMAND_TEXT,), {}),
    'techsets': ('show_tech_sets_v03114', (), {}),
    'techupgrade': ('tech_set_upgrade_v0320', (COMMAND_TEXT,), {}),
    'partyquest': ('party_quest_status_v0320', (), {}),
    'dungeonbonus': ('dungeon_party_bonus_status_v0320', (), {}),
    'blacksmithinginfo': ('show_blacksmithing_info', (), {}),
    'jewelcraftinginfo': ('show_jewelcrafting_info', (), {}),
    'cookinginfo': ('show_cooking_info', (), {}),
    'krawiectwo': ('v03053_show_profession', ('Krawiectwo',), {}),
    'garbarstwo': ('v03053_show_profession', ('Garbarstwo',), {}),
    'stolarstwo': ('v03053_show_profession', ('Stolarstwo',), {}),
    'zaklinanie': ('v03053_show_profession', ('Zaklinanie',), {}),
    'szyj': ('v03053_craft', ('Krawiectwo', COMMAND_TEXT), {}),
    'garbuj': ('v03053_craft', ('Garbarstwo', COMMAND_TEXT), {}),
    'stolarka': ('v03053_craft', ('Stolarstwo', COMMAND_TEXT), {}),
    'zaklinaj': ('v03053_enchant', (COMMAND_TEXT,), {}),
    'enchants': ('v03053_enchants', (), {}),
    'gems': ('show_gems', (), {}),
    'geodes': ('show_geodes', (), {}),
    'geodeopen': ('open_geode', (COMMAND_TEXT,), {}),
    'cutgem': ('cut_gem', (COMMAND_TEXT,), {}),
    'socketgem': ('socket_gem', (COMMAND_TEXT,), {}),
    'gemsockets': ('show_socketed_gems', (), {}),
    'techsalvage': ('tech_salvage_v03111', (COMMAND_TEXT,), {}),
    'techcraft': ('tech_craft_v03111', (COMMAND_TEXT,), {}),
    'vmaxstatus': ('vmax_status_v03111', (), {}),
    'inventory': ('inventory', (), {}),
    'equipment': ('equipment', (COMMAND_TEXT,), {}),
    'autoequip': ('auto_equip_best_v03040', (), {}),
    'classsets': ('show_class_sets', (COMMAND_TEXT,), {}),
    'equipringauto': ('equip_shortcut_dual_v03020', ('ring', COMMAND_TEXT), {}),
    'equipcharmauto': ('equip_shortcut_dual_v03020', ('charm', COMMAND_TEXT), {}),
    'equipearringauto': ('equip_shortcut_dual_v03020', ('earring', COMMAND_TEXT), {}),
    'unequip': ('unequip_item', (COMMAND_TEXT,), {}),
    'giveeq': ('give_player', (COMMAND_TEXT,), {}),
    'use': ('use_item', (COMMAND_TEXT,), {}),
    'shop': ('shop', (COMMAND_TEXT,), {}),
    'buy': ('buy', (COMMAND_TEXT,), {}),
    'talk': ('talk', (COMMAND_TEXT,), {}),
    'deliver': ('deliver_quest_item', (COMMAND_TEXT,), {}),
    'questaccept': ('accept_quest_command', (COMMAND_TEXT,), {}),
    'turnin': ('turn_in_quest_command', (COMMAND_TEXT,), {}),
    'waterinfo': ('show_water_info', (), {}),
    'fishjournal': ('show_fish_journal', (COMMAND_TEXT,), {}),
    'teachers': ('show_teachers', (), {}),
    'quests': ('quests', (COMMAND_TEXT,), {}),
    'consider': ('consider_mob', (COMMAND_TEXT,), {}),
    'attack': ('attack', (COMMAND_TEXT,), {}),
    'flee': ('flee', (), {}),
    'unlock': ('unlock_context', (COMMAND_TEXT,), {}),
    'admin': ('admin_command', (COMMAND_TEXT,), {}),
    'wipe': ('wipe_command', (COMMAND_TEXT,), {}),
}


# v0.49.0: the remaining custom branches formerly embedded in command_loop.py
# are ordinary registry entries too.  Their focused wrapper methods live in
# command_special_handlers.py; direct equipment shortcuts can call the final
# gameplay method without wrappers.
COMMAND_REGISTRY.update({
    'lifetime': ('command_lifetime_v0490', (COMMAND_TEXT,), {}),
    'leaderboards': ('command_leaderboards_v0490', (COMMAND_TEXT,), {}),
    'codex': ('command_codex_v0490', (COMMAND_TEXT,), {}),
    'channels': ('command_channels_v0490', (COMMAND_TEXT,), {}),
    'mentor': ('command_mentor_v0490', (COMMAND_TEXT,), {}),
    'emote': ('emote_v03051', (COMMAND_NAME, COMMAND_TEXT), {}),
    'smile': ('emote_v03051', (COMMAND_NAME, COMMAND_TEXT), {}),
    'wave': ('emote_v03051', (COMMAND_NAME, COMMAND_TEXT), {}),
    'cheer': ('emote_v03051', (COMMAND_NAME, COMMAND_TEXT), {}),
    'friends': ('handle_friends_v0928', (COMMAND_TEXT,), {}),
    'skill': ('command_skill_v0490', (COMMAND_TEXT,), {}),
    'craftmastery': ('show_crafting_mastery_v03054', (COMMAND_TEXT,), {}),
    'mistrzostwocraftu': ('show_crafting_mastery_v03054', (COMMAND_TEXT,), {}),
    'fish': ('command_fish_v0490', (COMMAND_TEXT,), {}),
    'mine': ('command_mine_v0490', (COMMAND_TEXT,), {}),
    'woodcut': ('command_woodcut_v0490', (COMMAND_TEXT,), {}),
    'herb': ('command_herb_v0490', (COMMAND_TEXT,), {}),
    'craft': ('command_craft_v0490', (COMMAND_TEXT,), {}),
    'jewelcraft': ('command_jewelcraft_v0490', (COMMAND_TEXT,), {}),
    'cook': ('command_cook_v0490', (COMMAND_TEXT,), {}),
    'alchemy': ('command_alchemy_v0490', (COMMAND_TEXT,), {}),
    'equiphead': ('equip_shortcut_slot_v03016', ('head', COMMAND_TEXT), {}),
    'equipbody': ('equip_shortcut_slot_v03016', ('body', COMMAND_TEXT), {}),
    'equiphands': ('equip_shortcut_slot_v03016', ('hands', COMMAND_TEXT), {}),
    'equiplegs': ('equip_shortcut_slot_v03016', ('legs', COMMAND_TEXT), {}),
    'equipfeet': ('equip_shortcut_slot_v03016', ('feet', COMMAND_TEXT), {}),
    'equipcharm': ('equip_shortcut_slot_v03016', ('charm1', COMMAND_TEXT), {}),
    'equipcharm2': ('equip_shortcut_slot_v03016', ('charm2', COMMAND_TEXT), {}),
    'equipring1': ('equip_shortcut_slot_v03016', ('ring1', COMMAND_TEXT), {}),
    'equipring2': ('equip_shortcut_slot_v03016', ('ring2', COMMAND_TEXT), {}),
    'equipnecklace': ('equip_shortcut_slot_v03016', ('necklace', COMMAND_TEXT), {}),
    'equipearring1': ('equip_shortcut_slot_v03016', ('earring1', COMMAND_TEXT), {}),
    'equipearring2': ('equip_shortcut_slot_v03016', ('earring2', COMMAND_TEXT), {}),
    'equipshoulders': ('equip_shortcut_slot_v03016', ('shoulders', COMMAND_TEXT), {}),
    'equipbelt': ('equip_shortcut_slot_v03016', ('belt', COMMAND_TEXT), {}),
    'equipcloak': ('equip_shortcut_slot_v03016', ('cloak', COMMAND_TEXT), {}),
    'equipbracers': ('equip_shortcut_slot_v03016', ('bracers', COMMAND_TEXT), {}),
    'equiprelic': ('equip_shortcut_slot_v03016', ('relic', COMMAND_TEXT), {}),
    'equip': ('command_equip_v0490', (COMMAND_TEXT,), {}),
    'save': ('command_save_v0490', (), {}),
    'quit': ('command_quit_v0490', (), {}),
})

# Command-state policy is metadata, not parser code.  The loop asks the
# catalog whether the resolved canonical command is safe in a given state.
DOWNED_SAFE_COMMANDS = {
    "help", "look", "party", "partychat", "say", "tell", "reply", "who",
    "where", "hp", "score", "records", "chronicle", "selfrespawn",
    "historybuffer", "lifetime", "deathrecap", "combatrecap",
}
REST_SAFE_COMMANDS = {
    "rest", "help", "encoding", "describe", "changes", "look", "level", "xp", "wimpy", "eventxp",
    "corpse", "cryptinfo", "astralinfo", "consider", "waterinfo", "fishjournal", "exits", "map",
    "worldevents", "atlas", "codex", "bestiary", "where", "who", "gossip", "newbie", "trade",
    "channels", "mentor", "expareas", "terraininfo", "classsets", "say", "stats", "hp", "score",
    "mana", "declension", "skills", "spells", "skillnames", "skillqueue", "soul", "money", "net",
    "bag", "woodpile", "herbbag", "professions", "ranks", "tools", "toolinfo_fishing",
    "toolinfo_mining", "toolinfo_woodcutting", "toolinfo_crafting", "toolinfo_cooking",
    "toolinfo_herbalism", "toolinfo_alchemy", "toolinfo_jewelcrafting", "jewelcraftinginfo", "gems",
    "gemsockets", "tiers", "location", "route", "guide", "recipes", "inventory", "equipment", "shop",
    "teachers", "quests", "charisma", "multiclass", "back", "dungeonexit", "progress", "exploration",
    "achievements", "titles", "title", "collection", "bosscodex", "bounty", "drophistory", "lootfilter",
    "regionprogress", "combatlog", "lifetime", "historybuffer", "craftbox", "craftmastery",
    "mistrzostwocraftu", "runes", "clan", "masteryachievements", "friends", "ignore", "unignore", "afk",
    "whois", "mail", "board", "lfg", "newbieprotect", "house", "records", "inspect", "inspectprivacy",
    "emote", "smile", "wave", "cheer", "collection2", "completion", "deathrecap", "combatrecap",
    "loothistory", "chronicle", "nvda", "krawiectwo", "garbarstwo", "stolarstwo", "zaklinanie", "szyj",
    "garbuj", "stolarka", "enchants",
}
GUIDE_SAFE_COMMANDS = {
    "guide", "route", "help", "encoding", "describe", "changes", "wimpy", "eventxp", "look", "level",
    "xp", "exits", "map", "atlas", "codex", "bestiary", "where", "who", "whois", "terraininfo",
    "location", "stats", "hp", "score", "money", "soul", "skills", "spells", "skillnames", "inventory",
    "equipment", "quests", "progress", "exploration", "achievements", "titles", "weather", "biomemastery",
    "worldquest", "artifacts", "biomesets", "factionstories", "season", "expeditions", "transport",
    "greatruins", "legendaryevents", "endless", "megadungeons", "gauntlets", "mythicbosses",
    "artifactupgrade", "endgamegoals", "collection", "museum", "prestige", "bosscodex", "leaderboards",
    "bounty", "chronicle", "legendarycontracts", "worldprojects", "worldproject", "fishrecords",
    "drophistory", "combatlog", "lifetime", "historybuffer", "fishjournal", "say", "gossip", "newbie",
    "trade", "channels", "mentor", "tell", "reply", "friends", "craftbox", "craftmastery",
    "mistrzostwocraftu", "runes", "clan", "masteryachievements", "partychat",
}

for _canonical, (_handler, _positional, _keywords) in COMMAND_REGISTRY.items():
    COMMAND_CATALOG.register_handler(
        _canonical, _handler, source="player/session_mixins/command_registry.py",
        help_topic=_canonical, kind="session",
    )
for _canonical in DOWNED_SAFE_COMMANDS | REST_SAFE_COMMANDS | GUIDE_SAFE_COMMANDS:
    COMMAND_CATALOG.set_policy(
        _canonical,
        downed_safe=_canonical in DOWNED_SAFE_COMMANDS,
        rest_safe=_canonical in REST_SAFE_COMMANDS,
        guide_safe=_canonical in GUIDE_SAFE_COMMANDS,
    )


def resolve_session_command(token, args=""):
    """Resolve one user command through the authoritative v0.49 catalog."""
    raw = str(token or "").strip().lower()
    if raw == "loot" and str(args or "").strip().lower() in LOOT_FILTER_INPUTS:
        return "lootfilter"
    return COMMAND_CATALOG.resolve(raw)


def command_state_safe(command, state):
    definition = COMMAND_CATALOG.definition(command)
    if definition is None:
        return False
    if state == "downed":
        return bool(definition.downed_safe)
    if state == "rest":
        return bool(definition.rest_safe)
    if state == "guide":
        return bool(definition.guide_safe)
    raise ValueError(f"Unknown command safety state: {state}")


class SessionCommandRegistryMixin:
    async def dispatch_registered_command(self, command, args):
        spec = COMMAND_REGISTRY.get(command)
        if spec is None:
            return False
        method_name, positional, keywords = spec
        method = getattr(self, method_name)

        def _resolve(value):
            if value is COMMAND_TEXT:
                return args
            if value is COMMAND_NAME:
                return command
            return value

        resolved_positional = tuple(_resolve(value) for value in positional)
        resolved_keywords = {key: _resolve(value) for key, value in keywords.items()}
        try:
            result = await method(*resolved_positional, **resolved_keywords)
            if result is COMMAND_LOOP_BREAK:
                return COMMAND_LOOP_BREAK
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            report = self.server.report_runtime_error(
                exc, command=command, handler=method_name
            )
            try:
                await self.send(
                    f"Wystąpił błąd komendy [{report['error_id']}]. "
                    "Sesja pozostaje aktywna; identyfikator błędu jest zapisany w logu serwera."
                )
            except Exception:
                raise
        return True
