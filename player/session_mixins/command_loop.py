# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: command_loop."""

class SessionCommandLoopMixin:
    async def command_loop(self):
            while not self.closed:
                # v0.30.27: cichy prompt dla NVDA. Nie wypisujemy znaku ">"
                # po każdej komendzie; klient po prostu czeka na następną linię.
                raw = await self.read_line()
                if raw is None:
                    break
                if raw.startswith("'"):
                    await self.say(raw[1:])
                    continue
                if raw.strip() == "/":
                    await self.teleport_to_temple_command()
                    continue

                if self.guide_choice_state:
                    normalized_raw = self.normalize_room_query(raw)
                    if (
                        raw.strip().isdigit()
                        or normalized_raw in (
                            "anuluj", "cancel", "stop",
                        )
                    ):
                        handled = await self.handle_guide_choice_number(
                            raw
                        )
                        if handled:
                            continue
                    else:
                        self.guide_choice_state = None

                parts = raw.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                # v0.30.26: twardy alias parsera. `ex` zawsze trafia do tego
                # samego handlera co `exits`, niezależnie od późniejszych tabel aliasów.
                if command == "ex":
                    command = "exits"
                if command == "loot" and args.strip().lower() in LOOT_FILTER_INPUTS:
                    command = "lootfilter"
                else:
                    command = COMMAND_ALIASES.get(command, command)
                direction = DIRECTION_ALIASES.get(command)

                rest_safe_commands = {
                    "rest", "help", "encoding", "describe", "changes", "look", "level", "xp", "wimpy", "eventxp",
                    "corpse", "cryptinfo", "astralinfo", "consider",
                    "waterinfo", "fishjournal", "exits", "map", "worldevents", "atlas", "codex", "bestiary",
                    "where", "who", "gossip", "newbie", "trade", "channels", "mentor", "expareas", "terraininfo", "classsets", "say", "stats", "hp", "score", "mana", "declension", "skills", "spells",
                    "skillnames", "skillqueue", "soul", "money", "net", "bag",
                    "woodpile", "herbbag", "professions", "ranks",
                    "tools", "toolinfo_fishing", "toolinfo_mining",
                    "toolinfo_woodcutting", "toolinfo_crafting",
                    "toolinfo_cooking", "toolinfo_herbalism",
                    "toolinfo_alchemy", "toolinfo_jewelcrafting",
                    "jewelcraftinginfo", "gems", "gemsockets",
                    "tiers", "location", "route", "guide",
                    "recipes", "inventory", "equipment", "shop",
                    "teachers", "quests", "charisma", "multiclass",
                    "back", "dungeonexit", "progress", "exploration",
                    "achievements", "titles", "title", "collection", "bosscodex", "bounty",
                    "drophistory", "lootfilter", "regionprogress", "combatlog", "lifetime", "historybuffer", "craftbox", "craftmastery", "mistrzostwocraftu", "runes", "clan", "masteryachievements", "friends", "friend", "ignore", "unignore", "afk", "whois", "mail", "board", "lfg", "newbieprotect", "house", "records", "inspect", "inspectprivacy", "emote", "smile", "wave", "cheer", "collection2", "completion", "deathrecap", "combatrecap", "loothistory", "nvda", "krawiectwo", "garbarstwo", "stolarstwo", "zaklinanie", "szyj", "garbuj", "stolarka", "enchants",
                }

                if (
                    self.resting
                    and not direction
                    and command not in rest_safe_commands
                ):
                    await self.stop_rest(
                        announce=True,
                        reason="wykonujesz inną akcję",
                    )

                guide_safe_commands = {
                    "guide", "route", "help", "encoding", "describe", "changes", "wimpy", "eventxp",
                    "look", "level", "xp", "exits", "map", "atlas", "codex", "bestiary", "where", "who",
                    "terraininfo", "location", "stats", "hp", "score", "money",
                    "soul", "skills", "spells", "skillnames", "inventory", "equipment",
                    "quests", "progress", "exploration", "achievements", "titles", "weather", "biomemastery", "worldquest", "artifacts", "biomesets", "factionstories", "season", "expeditions", "transport", "greatruins", "legendaryevents", "endless", "megadungeons", "gauntlets", "mythicbosses", "artifactupgrade", "endgamegoals",
                    "collection", "museum", "prestige", "bosscodex", "leaderboards", "bounty", "legendarycontracts", "worldprojects", "worldproject", "fishrecords", "drophistory", "combatlog", "lifetime", "historybuffer", "fishjournal", "say", "gossip", "newbie", "trade", "channels", "mentor", "tell", "reply", "friends", "craftbox", "craftmastery", "mistrzostwocraftu", "runes", "clan", "masteryachievements",
                    "partychat",
                }
                if self.guide_task_active() and (
                    direction or command not in guide_safe_commands
                ):
                    await self.cancel_guide(
                        announce=True,
                        reason="Prowadzenie przerwane: wykonujesz ręczny ruch albo inną aktywność.",
                    )

                if direction:
                    await self.move(direction)
                elif command == "classguild":
                    await self.show_guild(args)
                elif command == "guildquest":
                    await self.guild_class_quest(args)
                elif command == "guildexam":
                    await self.guild_exam(args)
                elif command == "guildbounty":
                    await self.guild_bounty(args)
                elif command == "bounty":
                    await self.handle_bounty(args)
                elif command == "legendarycontracts":
                    await self.handle_legendary_contracts_v022(args)
                elif command == "worldprojects":
                    await self.show_world_projects_v022(args)
                elif command == "worldproject":
                    await self.handle_world_project_v022(args)
                elif command == "fishrecords":
                    await self.show_fish_records_v022(args)
                elif command == "help":
                    await self.show_help(args)
                elif command == "wimpy":
                    await self.handle_wimpy(args)
                elif command == "eventxp":
                    await self.show_double_xp_event()
                elif command == "encoding":
                    await self.set_encoding(args)
                elif command == "describe":
                    await self.describe_target(args)
                elif command == "changes":
                    await self.show_latest_changes()
                elif command == "progress":
                    await self.show_progress(args)
                elif command == "lifetime":
                    history_prefix = str(args or "").strip().split(maxsplit=1)[0] if str(args or "").strip() else ""
                    if self.normalize_history_category(history_prefix) or self.normalize_description_query(history_prefix) in ("clear", "wyczysc", "wyczyść", "reset"):
                        await self.show_history_buffer(args)
                    else:
                        await self.show_lifetime_statistics()
                elif command == "historybuffer":
                    await self.show_history_buffer(args)
                elif command == "regionprogress":
                    await self.show_region_progress()
                elif command == "exploration":
                    await self.show_exploration(args)
                elif command == "achievements":
                    await self.show_achievements()
                elif command == "titles":
                    await self.show_titles()
                elif command == "title":
                    await self.set_title(args)
                elif command == "collection":
                    await self.show_collection(args)
                elif command == "collection2":
                    await self.collection_codex_v03052(args)
                elif command == "completion":
                    await self.completion_v03052()
                elif command == "deathrecap":
                    await self.recap2_v0320(death=True)
                elif command == "combatrecap":
                    await self.recap2_v0320(death=False)
                elif command == "loothistory":
                    await self.loot_history_v03052(args)
                elif command == "nvda":
                    await self.accessibility_v03052(args)
                elif command == "museum":
                    await self.show_museum_v0260(args)
                elif command == "prestige":
                    await self.show_prestige_v0260()
                elif command == "bosscodex":
                    await self.show_boss_codex(args)
                elif command == "leaderboards":
                    if normalize_lookup_text(args or "") in ("profesje","profession","professions","bossowie","bosses","kolekcje","collection","rekordy","records","gildie","guilds","mentor","mentorzy"):
                        await self.leaderboards_v03052(args)
                    else:
                        await self.show_leaderboards(args)
                elif command == "drophistory":
                    await self.loot_history_v03052(args)
                elif command == "lootfilter":
                    await self.set_loot_filter(args)
                elif command == "combatlog":
                    await self.set_combat_log(args)
                elif command == "look":
                    await self.look(args)
                elif command == "corpse":
                    await self.show_corpses(args)
                elif command == "lootcorpse":
                    await self.loot_corpse(args)
                elif command == "getcorpseitem":
                    await self.get_from_corpse(args)
                elif command == "cryptinfo":
                    await self.show_crypt_info()
                elif command == "astralinfo":
                    await self.show_astral_info()
                elif command == "astralportal":
                    await self.use_astral_portal(args)
                elif command == "portal":
                    await self.use_crypt_portal(args)
                elif command == "exits":
                    await self.show_exits(args)
                elif command == "map":
                    await self.show_map(args)
                elif command == "cartography":
                    await self.show_cartography_v024()
                elif command == "worldevents":
                    await self.show_world_events()
                elif command == "dynamicevents":
                    await self.show_dynamic_events_v029()
                elif command == "nemesis":
                    await self.show_nemesis_v029()
                elif command == "globalgenerator":
                    await self.show_global_generator_v025(args)
                elif command == "weather":
                    await self.show_weather_v015()
                elif command == "biomemastery":
                    await self.show_biome_mastery_v015(args)
                elif command == "worldquest":
                    await self.handle_dynamic_world_quest_v015(args)
                elif command == "factions":
                    await self.show_factions_v016(args)
                elif command == "worldbosses":
                    await self.show_world_bosses_v016()
                elif command == "legendaryrares":
                    await self.show_legendary_rares_v016()
                elif command == "travelers":
                    await self.show_travelers_v016()
                elif command == "artifacts":
                    await self.show_artifacts_v017()
                elif command == "biomesets":
                    await self.show_biome_sets_v017(args)
                elif command == "factionstories":
                    await self.show_faction_stories_v017(args)
                elif command == "season":
                    await self.show_season_v018()
                elif command == "expeditions":
                    await self.show_expeditions_v018()
                elif command == "expedition":
                    await self.start_expedition_v018(args)
                elif command == "transport":
                    await self.transport_v03052(args)
                elif command == "greatruins":
                    await self.show_great_ruins_v018()
                elif command == "legendaryevents":
                    await self.show_legendary_events_v018()
                elif command == "endless":
                    await self.show_endless_v018()
                elif command == "megadungeons":
                    await self.show_megadungeons_v020()
                elif command == "gauntlets":
                    await self.show_gauntlets_v020()
                elif command == "gauntlet":
                    await self.start_gauntlet_v020(args)
                elif command == "mythicbosses":
                    await self.show_mythic_bosses_v020()
                elif command == "artifactupgrade":
                    await self.artifact_upgrade_v020(args)
                elif command == "endgamegoals":
                    await self.show_endgame_goals_v020()
                elif command == "ascension":
                    await self.show_ascension_v021(args)
                elif command == "worldtier":
                    await self.handle_world_tier_v021(args)
                elif command == "mythicsets":
                    await self.show_mythic_sets_v021(args)
                elif command == "endlessgauntlet":
                    await self.handle_endless_gauntlet_v021(args)
                elif command == "mythicprogression":
                    await self.show_mythic_progression_v021()
                elif command == "instancesecret":
                    await self.discover_instance_secret()
                elif command == "bestiary":
                    await self.show_bestiary(args)
                elif command == "atlas":
                    await self.show_atlas(args)
                elif command == "codex":
                    _codex_args = (args or "").strip()
                    _codex_norm = self.normalize_description_query(_codex_args)
                    if _codex_norm in ("klasy", "klasa", "class", "classes"):
                        await self.show_class_codex("info")
                    elif _codex_norm.startswith("klasy ") or _codex_norm.startswith("klasa "):
                        await self.show_class_codex(_codex_args.split(maxsplit=1)[1])
                    elif _codex_norm.startswith("class ") or _codex_norm.startswith("classes "):
                        await self.show_class_codex(_codex_args.split(maxsplit=1)[1])
                    else:
                        await self.show_world_codex(args)
                elif command == "classcodex":
                    await self.show_class_codex(args)
                elif command == "chest":
                    await self.open_treasure_chest(args)
                elif command == "where":
                    await self.show_where()
                elif command == "expareas":
                    await self.show_exp_areas(args)
                elif command == "terraininfo":
                    await self.show_terrain_info(args)
                elif command == "dungeon_exit":
                    await self.dungeon_exit()
                elif command == "dungeonexit":
                    await self.dungeon_exit()
                elif command == "who":
                    await self.who()
                elif command == "say":
                    await self.say(args)
                elif command == "gossip":
                    await self.channel_broadcast_v03050("gossip", args)
                elif command == "newbie":
                    await self.channel_broadcast_v03050("newbie", args)
                elif command == "trade":
                    await self.channel_broadcast_v03050("trade", args)
                elif command == "channels":
                    _cp=str(args or '').strip().split(maxsplit=1)
                    if _cp and normalize_lookup_text(_cp[0]) in ("history","historia"):
                        await self.show_channel_history_v03051(_cp[1] if len(_cp)>1 else "gossip")
                    else:
                        await self.show_channels_v03050()
                elif command == "mentor":
                    _mn=normalize_lookup_text(str(args or '').strip())
                    if _mn in ("zadania","tasks"): await self.mentor_tasks_v03051(False)
                    elif _mn in ("odbierz","claim"): await self.mentor_tasks_v03051(True)
                    else: await self.mentor_v03052(args)
                elif command == "ignore":
                    await self.handle_ignore_v03051(args,False)
                elif command == "unignore":
                    await self.handle_ignore_v03051(args,True)
                elif command == "afk":
                    await self.handle_afk_v03051(args)
                elif command == "whois":
                    await self.whois_v03051(args)
                elif command == "mail":
                    await self.handle_mail_v03051(args)
                elif command == "board":
                    await self.handle_board_v03051(args)
                elif command == "lfg":
                    await self.handle_lfg_v03051(args)
                elif command == "newbieprotect":
                    await self.newbie_protection_v03051(args)
                elif command == "house":
                    await self.housing_v03052(args)
                elif command == "records":
                    await self.records_v03051(args)
                elif command == "inspect":
                    await self.inspect_v03051(args)
                elif command == "inspectprivacy":
                    await self.inspect_privacy_v03051(args)
                elif command in ("emote","smile","wave","cheer"):
                    await self.emote_v03051(command,args)
                elif command == "tell":
                    await self.tell(args)
                elif command == "reply":
                    await self.reply_private_v0928(args)
                elif command in ("friends","friend"):
                    await self.handle_friends_v0928(args)
                elif command == "party":
                    await self.handle_party(args)
                elif command == "partyinvite":
                    await self.party_invite(args)
                elif command == "partyaccept":
                    await self.party_accept()
                elif command == "partydecline":
                    await self.party_decline()
                elif command == "partyleave":
                    await self.leave_party(announce=True)
                elif command == "partykick":
                    await self.party_kick(args)
                elif command == "partydisband":
                    await self.disband_party()
                elif command == "partyleader":
                    await self.transfer_party_leader(args)
                elif command == "partyprotect":
                    await self.protect_party(args)
                elif command == "partychat":
                    await self.party_chat(args)
                elif command == "assist":
                    await self.assist_party_member(args)
                elif command == "charisma":
                    await self.show_charisma()
                elif command == "multiclass":
                    await self.handle_multiclass(args)
                elif command == "rest":
                    await self.handle_rest(args)
                elif command == "stats":
                    await self.show_stats(args)
                elif command == "hp":
                    await self.show_hp()
                elif command == "score":
                    await self.show_score()
                elif command == "level":
                    await self.show_character_level()
                elif command == "xp":
                    await self.show_character_xp()
                elif command == "mana":
                    await self.handle_mana_command(args)
                elif command == "declension":
                    await self.show_name_declension()
                elif command == "skills":
                    await self.show_skills(args)
                elif command == "spells":
                    await self.show_spells(args)
                elif command == "skillnames":
                    await self.show_all_skill_names()
                elif command == "skill":
                    skill_args = str(args or "").strip()
                    skill_args_norm = normalize_lookup_text(skill_args)
                    if skill_args_norm in ("info", "help", "opis"):
                        await self.show_skill_help("")
                    elif any(
                        skill_args_norm.startswith(prefix)
                        for prefix in ("info ", "help ", "opis ")
                    ):
                        query = skill_args.split(maxsplit=1)[1] if " " in skill_args else ""
                        if not await self.show_skill_help(query):
                            await self.send("Nie znam takiej umiejętności ani spella. Wpisz skillnames.")
                    else:
                        await self.use_class_skill(args)
                elif command == "skillqueue":
                    await self.handle_skill_queue(args)
                elif command == "learn":
                    await self.learn_class_skill(args)
                elif command == "soul":
                    await self.show_soul(args)
                elif command == "money":
                    await self.show_money()
                elif command == "bank":
                    await self.handle_bank(args)
                elif command == "net":
                    await self.show_container("net")
                elif command == "bag":
                    await self.show_container("bag")
                elif command == "woodpile":
                    await self.show_container("woodpile")
                elif command == "herbbag":
                    await self.show_container("herbbag")
                elif command == "craftbox":
                    await self.show_craftbox_v0925(args)
                elif command in ("craftmastery", "mistrzostwocraftu"):
                    await self.show_crafting_mastery_v03054(args)
                elif command == "salvage":
                    await self.salvage_equipment_v0925(args)
                elif command == "reforge":
                    await self.reforge_equipment_v0925(args)
                elif command == "equpgrade":
                    await self.upgrade_equipment_v03042(args)
                elif command == "runes":
                    await self.handle_runes_v03114(args)
                elif command == "socketrune":
                    await self.socket_rune_v0925(args)
                elif command == "playerguild":
                    await self.handle_guild_v0926(args)
                elif command == "masteryachievements":
                    await self.show_mastery_achievements_v0925()
                elif command == "put":
                    await self.put_in_container(args)
                elif command == "take":
                    await self.take_from_container(args)
                elif command == "professions":
                    await self.show_professions(args)
                elif command == "ranks":
                    await self.show_profession_ranks()
                elif command == "tools":
                    await self.show_tools(args)
                elif command == "toolinfo_fishing":
                    await self.show_single_tool("fishing")
                elif command == "toolinfo_mining":
                    await self.show_single_tool("mining")
                elif command == "toolinfo_woodcutting":
                    await self.show_single_tool("woodcutting")
                elif command == "toolinfo_crafting":
                    await self.show_single_tool("crafting")
                elif command == "toolinfo_cooking":
                    await self.show_single_tool("cooking")
                elif command == "toolinfo_herbalism":
                    await self.show_single_tool("herbalism")
                elif command == "toolinfo_alchemy":
                    await self.show_single_tool("alchemy")
                elif command == "toolinfo_jewelcrafting":
                    await self.show_single_tool("jewelcrafting")
                elif command == "tiers":
                    await self.show_tool_tiers()
                elif command == "fish":
                    mode = args.strip().lower()
                    if mode in ("on", "start", "1"):
                        await self.set_auto_fishing(True)
                    elif mode in ("off", "stop", "0"):
                        await self.set_auto_fishing(False)
                    elif mode:
                        await self.send(
                            "Użycie: fish, fish on, fish off, low on albo low off."
                        )
                    else:
                        await self.fish()
                elif command == "guide":
                    await self.start_guide_task(args)
                elif command == "route":
                    await self.show_route(args)
                elif command == "location":
                    await self.show_location()
                elif command == "mineinfo":
                    await self.show_mine_info()
                elif command == "mine":
                    mode = args.strip().lower()
                    if mode in ("on", "start", "1"):
                        await self.set_auto_mining(True)
                    elif mode in ("off", "stop", "0"):
                        await self.set_auto_mining(False)
                    elif mode:
                        await self.send(
                            "Użycie: mine, mine on, mine off, kop on albo kop off."
                        )
                    else:
                        await self.mine()
                elif command == "woodcut":
                    mode = args.strip().lower()
                    if mode in ("on", "start", "1"):
                        await self.set_auto_woodcutting(True)
                    elif mode in ("off", "stop", "0"):
                        await self.set_auto_woodcutting(False)
                    elif mode:
                        await self.send("Użycie: tnij, tnij on, tnij off, woodcut on albo woodcut off.")
                    else:
                        await self.woodcut()
                elif command == "herb":
                    mode = args.strip().lower()
                    if mode in ("on", "start", "1"):
                        await self.set_auto_herbalism(True)
                    elif mode in ("off", "stop", "0"):
                        await self.set_auto_herbalism(False)
                    elif mode:
                        await self.send("Użycie: zbieraj, zbieraj on albo zbieraj off.")
                    else:
                        await self.gather_herb()
                elif command == "sell":
                    await self.sell_command(args)
                elif command == "recipes":
                    await self.show_recipes(args)
                elif command == "craft":
                    if not args.strip():
                        await self.send("Użycie: craft <receptura>. Wpisz receptury.")
                    else:
                        await self.craft_item_v03114(args)
                elif command == "smelt":
                    await self.smelt_item_v03114(args)
                elif command == "materialconversion":
                    await self.material_conversion_v03114()
                elif command == "refine":
                    await self.refine_v03114(args)
                elif command == "socketcraft":
                    await self.socket_craft_v03114(args)
                elif command == "vmaxupgrade":
                    await self.vmax_upgrade_v03114(args)
                elif command == "techsets":
                    await self.show_tech_sets_v03114()
                elif command == "techupgrade":
                    await self.tech_set_upgrade_v0320(args)
                elif command == "partyquest":
                    await self.party_quest_status_v0320()
                elif command == "dungeonbonus":
                    await self.dungeon_party_bonus_status_v0320()
                elif command == "blacksmithinginfo":
                    await self.show_blacksmithing_info()
                elif command == "jewelcraftinginfo":
                    await self.show_jewelcrafting_info()
                elif command == "jewelcraft":
                    if not args.strip():
                        await self.send(
                            "Użycie: jub <receptura>. "
                            "Wpisz receptury jubilerstwo."
                        )
                    else:
                        await self.jewelcraft_item(args)
                elif command == "cookinginfo":
                    await self.show_cooking_info()
                elif command == "cook":
                    cook_mode = args.strip().lower()
                    if cook_mode in ("lista", "list", "receptury", "przepisy"):
                        await self.show_recipes("cook")
                    elif not cook_mode:
                        await self.send(
                            "Użycie: gotuj <potrawa>. "
                            "Wpisz gotuj lista albo receptury cook."
                        )
                    else:
                        await self.cook_item(args)
                elif command == "alchemy":
                    if not args.strip():
                        await self.send("Użycie: alchemia <mikstura>. Wpisz receptury alchemia.")
                    else:
                        await self.alchemy_item(args)
                elif command == "krawiectwo":
                    await self.v03053_show_profession("Krawiectwo")
                elif command == "garbarstwo":
                    await self.v03053_show_profession("Garbarstwo")
                elif command == "stolarstwo":
                    await self.v03053_show_profession("Stolarstwo")
                elif command == "zaklinanie":
                    await self.v03053_show_profession("Zaklinanie")
                elif command == "szyj":
                    await self.v03053_craft("Krawiectwo", args)
                elif command == "garbuj":
                    await self.v03053_craft("Garbarstwo", args)
                elif command == "stolarka":
                    await self.v03053_craft("Stolarstwo", args)
                elif command == "zaklinaj":
                    await self.v03053_enchant(args)
                elif command == "enchants":
                    await self.v03053_enchants()
                elif command == "gems":
                    await self.show_gems()
                elif command == "geodes":
                    await self.show_geodes()
                elif command == "geodeopen":
                    await self.open_geode(args)
                elif command == "cutgem":
                    await self.cut_gem(args)
                elif command == "socketgem":
                    await self.socket_gem(args)
                elif command == "gemsockets":
                    await self.show_socketed_gems()
                elif command == "techsalvage":
                    await self.tech_salvage_v03111(args)
                elif command == "techcraft":
                    await self.tech_craft_v03111(args)
                elif command == "vmaxstatus":
                    await self.vmax_status_v03111()
                elif command == "inventory":
                    await self.inventory()
                elif command == "equipment":
                    await self.equipment(args)
                elif command == "autoequip":
                    await self.auto_equip_best_v03040()
                elif command == "classsets":
                    await self.show_class_sets(args)
                elif command in ("equiphead", "equipbody", "equiphands", "equiplegs", "equipfeet", "equipcharm", "equipcharm2", "equipring1", "equipring2", "equipnecklace", "equipearring1", "equipearring2", "equipshoulders", "equipbelt", "equipcloak", "equipbracers", "equiprelic"):
                    shortcut_slots = {
                        "equiphead": "head", "equipbody": "body", "equiphands": "hands",
                        "equiplegs": "legs", "equipfeet": "feet", "equipcharm": "charm1", "equipcharm2": "charm2",
                        "equipring1": "ring1", "equipring2": "ring2", "equipnecklace": "necklace",
                        "equipearring1": "earring1", "equipearring2": "earring2",
                        "equipshoulders": "shoulders", "equipbelt": "belt", "equipcloak": "cloak",
                        "equipbracers": "bracers", "equiprelic": "relic",
                    }
                    await self.equip_shortcut_slot_v03016(shortcut_slots[command], args)
                elif command == "equipringauto":
                    await self.equip_shortcut_dual_v03020("ring", args)
                elif command == "equipcharmauto":
                    await self.equip_shortcut_dual_v03020("charm", args)
                elif command == "equipearringauto":
                    await self.equip_shortcut_dual_v03020("earring", args)
                elif command == "equip":
                    equip_target = self.normalize_description_query(str(args or "").strip())
                    if equip_target in ("druzyna", "druzyne", "party"):
                        await self.create_party()
                    else:
                        await self.equip_item(args)
                elif command == "unequip":
                    await self.unequip_item(args)
                elif command == "giveeq":
                    await self.give_player(args)
                elif command == "use":
                    await self.use_item(args)
                elif command == "shop":
                    await self.shop(args)
                elif command == "buy":
                    await self.buy(args)
                elif command == "talk":
                    await self.talk(args)
                elif command == "deliver":
                    await self.deliver_quest_item(args)
                elif command == "questaccept":
                    await self.accept_quest_command(args)
                elif command == "turnin":
                    await self.turn_in_quest_command(args)
                elif command == "waterinfo":
                    await self.show_water_info()
                elif command == "fishjournal":
                    await self.show_fish_journal(args)
                elif command == "teachers":
                    await self.show_teachers()
                elif command == "quests":
                    await self.quests(args)
                elif command == "consider":
                    await self.consider_mob(args)
                elif command == "attack":
                    await self.attack(args)
                elif command == "flee":
                    await self.flee()
                elif command == "unlock":
                    await self.unlock_context(args)
                elif command == "admin":
                    await self.admin_command(args)
                elif command == "wipe":
                    await self.wipe_command(args)
                elif command == "save":
                    self.server.db.save_character(self.character)
                    await self.send("Postać zapisana.")
                elif command == "quit":
                    # v0.8.52: quit kończy tylko grę bieżącą postacią.
                    # Połączenie i konto pozostają aktywne; wracamy do MENU POSTACI.
                    await self.send("Zapisuję postać i wracam do wyboru postaci.")
                    await self.leave_current_character_for_selection()

                    selected = await self.character_selection_flow()
                    if selected is True:
                        await self.enter_world()
                        continue

                    # Opcja 4 w MENU POSTACI wylogowuje konto. Zachowujemy wtedy
                    # normalny ekran logowania bez rozłączania klienta.
                    if not self.closed and self.master_account_id is None:
                        if await self.login_flow():
                            await self.enter_world()
                            continue

                    # Brak danych oznacza zwykle rozłączenie klienta.
                    self.closed = True
                    break
                else:
                    await self.send("Nieznana komenda. Wpisz help.")

    async def leave_current_character_for_selection(self):
            """Zapisz i wyprowadź aktywną postać ze świata bez zamykania połączenia."""
            if not self.character:
                self.account_id = None
                return

            # Zatrzymaj wszystkie aktywności przypisane do bieżącej postaci.
            if self.guide_task_active():
                await self.cancel_guide(announce=False)
            if self.resting or self.rest_task:
                await self.stop_rest(announce=False)
            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)

            await self.leave_party(announce=False)
            old_room = self.character.room_id
            old_name = self.character.name

            await self.stop_realtime_combat()
            self.server.release_all_engagements_for_session(self)
            self.combat_mob_key = None

            await self.show_session_summary()
            self.server.db.save_character(self.character)
            await self.server.broadcast_room(
                old_room, f"{old_name} opuszcza grę.", exclude=self
            )

            # Wyczyść tylko stan sesyjny postaci. Konto główne zostaje zalogowane.
            self.account_id = None
            self.character = None
            self.current_hp = 0
            self.current_mana = 0
            self.combat_hp_warn_level = 0
            self.skill_cooldowns = {}
            self.skill_guard = 0
            self.skill_evade = False
            self.skill_evade_lockout_until = 0.0
            self.active_skill_buffs = {}
            self._party_auto_heal_busy = False
            self.skill_queue_cursors = {"physical": 0, "magic": 0}
            self.skill_queue_next_type = "physical"
            self.auto_queue_casting = False
            self.guide_choice_state = None
            self.quest_list_context = None
            self.previous_room_id = None
            self.last_private_sender_account_id = None
            self.last_private_sender_name = None
            self._session_summary = None

    async def close(self):
            if self.closed:
                return
            if self.resting or self.rest_task:
                await self.stop_rest(announce=False)
            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)
            if self.character:
                await self.leave_party(announce=False)
            await self.stop_realtime_combat()
            self.closed = True
            if self.character:
                self.server.release_all_engagements_for_session(self)
            if self.character:
                self.server.db.save_character(self.character)
                await self.server.broadcast_room(
                    self.character.room_id, f"{self.character.name} opuszcza grę.", exclude=self
                )
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass
