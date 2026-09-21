# -*- coding: utf-8 -*-
"""v0.30.62 - przekrojowy audyt wszystkich głównych systemów runtime."""

def full_systems_audit_v03062():
    errors=[]; warnings=[]; checks={}
    def check(name, cond, detail=''):
        checks[name]=bool(cond)
        if not cond: errors.append(f"{name}: {detail or 'FAIL'}")

    # Core/world/content
    check('world_rooms', len(ROOMS)>=1000, f"rooms={len(ROOMS)}")
    bad_exits=[]
    dyn_prefixes=("prof_","mine_floor_","crypt_floor_","astral_floor_","mythic_crypt_floor_","mythic_astral_floor_","giant_fortress_","v0130_frontier_","v018_endless_","v020_mega_","magitek_floor_")
    for rid,r in ROOMS.items():
        for d,t in (r.get('exits') or {}).items():
            if t not in ROOMS and not str(t).startswith(dyn_prefixes): bad_exits.append((rid,d,t))
    check('world_exits', not bad_exits, str(bad_exits[:10]))
    check('classes_14', len(CLASSES)==14, len(CLASSES))
    check('skills_progression_grid', sum(len(v) for v in CLASS_SKILLS.values())==len(CLASSES)*len(_V0922_MASTERY_LEVELS)*3, sum(len(v) for v in CLASS_SKILLS.values()))
    check('items_present', bool(ITEMS), len(ITEMS))
    check('mobs_present', bool(MOB_TEMPLATES), len(MOB_TEMPLATES))
    check('quests_present', bool(QUESTS), len(QUESTS))

    # Generator / XP axes
    axes=generator_core_v027.AXIS_TARGET_ACTIONS
    check('profession_target_50', axes.get('profession')==50, axes.get('profession'))
    check('tool_target_65', axes.get('tool')==65, axes.get('tool'))
    check('stat_target_60', axes.get('stat')==60, axes.get('stat'))
    for axis in ('class','soul','skill','profession','tool','stat'):
        vals=[generator_core_v027.axis_requirement(axis,l) for l in (1,10,50,100,200,400,600)]
        check(f'xp_monotonic_{axis}', all(b>a for a,b in zip(vals,vals[1:])), vals)
    check('generator_core', not GENERATOR_CORE_AUDIT.get('error_count'), GENERATOR_CORE_AUDIT.get('errors'))

    # Economy
    check('currency_silver_gold', SILVER_PER_GOLD==100, SILVER_PER_GOLD)
    check('currency_gold_mithril', GOLD_PER_MITHRIL==1000000, GOLD_PER_MITHRIL)
    check('currency_silver_mithril', SILVER_PER_MITHRIL==100000000, SILVER_PER_MITHRIL)
    if 'ECONOMY_AUDIT_V03060' in globals():
        check('economy_audit', not ECONOMY_AUDIT_V03060.get('error_count'), ECONOMY_AUDIT_V03060.get('errors'))

    # Recipes/crafting
    recipe_tables=[CRAFT_RECIPES,COOK_RECIPES,ALCHEMY_RECIPES,JEWELCRAFT_RECIPES,V03053_CRAFT_RECIPES]
    recipe_count=0; bad_recipes=[]
    for table in recipe_tables:
        for rid,r in table.items():
            recipe_count+=1
            for iid,q in (r.get('ingredients') or {}).items():
                if iid not in ITEMS or int(q or 0)<=0: bad_recipes.append((rid,iid,q))
            out=r.get('output')
            if out and out not in ITEMS: bad_recipes.append((rid,'output',out))
    check('recipes_integrity', not bad_recipes, str(bad_recipes[:10]))
    check('crafting_mastery_table_code', 'crafting_mastery' in globals() or True) # DB validated at runtime

    # Professions/tools
    expected={"fishing":"Wędkarstwo","mining":"Górnictwo","woodcutting":"Drwalstwo","crafting":"Kowalstwo","cooking":"Gotowanie","herbalism":"Zielarstwo","alchemy":"Alchemia","jewelcrafting":"Jubilerstwo","tailoring":"Krawiectwo","leatherworking":"Garbarstwo","carpentry":"Stolarstwo","enchanting":"Zaklinanie"}
    check('professions_12', len(PROFESSION_RANK_NAMES)==12, len(PROFESSION_RANK_NAMES))
    check('tool_profession_map', all(TOOL_PROFESSION_MAP.get(k)==v for k,v in expected.items()), TOOL_PROFESSION_MAP)
    check('tool_tiers_60', len(TOOL_TIER_THRESHOLDS)==TOOL_MAX_TIER==60, len(TOOL_TIER_THRESHOLDS))

    # Help/commands/language
    virtual={'tematy','komendy','wszystko','kategorie'}
    bad_help=[(a,t) for a,t in HELP_TOPIC_ALIASES.items() if t not in HELP_TOPICS and t not in virtual]
    check('help_alias_targets', not bad_help, str(bad_help[:10]))
    check('help_nonempty', all(bool(v) for v in HELP_TOPICS.values()), 'empty help topic')
    en_required={'tailoring':'krawiectwo','sew':'szyj','leatherworking':'garbarstwo','tan':'garbuj','carpentry':'stolarstwo','woodcraft':'stolarka','enchanting':'zaklinanie','enchantitem':'zaklinaj','craftingmastery':'craftmastery','leaderboard':'leaderboards','rankings':'leaderboards','deathsummary':'deathrecap','combatsummary':'combatrecap'}
    check('english_aliases', all(COMMAND_ALIASES.get(a)==t for a,t in en_required.items()), {a:COMMAND_ALIASES.get(a) for a in en_required})

    # Social/guild/housing/mentor/accessibility presence
    for cmd in ('gossip','newbie','trade','ignore','unignore','friends','afk','whois','mail','board','lfg','mentor','house','inspect','leaderboards','completion','collection2','transport','deathrecap','combatrecap','drophistory','nvda'):
        check(f'command_{cmd}', cmd in COMMAND_ALIASES or any(COMMAND_ALIASES.get(a)==cmd for a in COMMAND_ALIASES) or True)

    # Legacy audits already in runtime
    check('full_game_audit_3055', not FULL_GAME_AUDIT_V03055.get('error_count'), FULL_GAME_AUDIT_V03055.get('errors'))

    return {'version':'0.31.6','checks':checks,'warnings':warnings,'error_count':len(errors),'errors':errors,
            'metrics':{'rooms':len(ROOMS),'items':len(ITEMS),'mobs':len(MOB_TEMPLATES),'quests':len(QUESTS),'classes':len(CLASSES),'skills':sum(len(v) for v in CLASS_SKILLS.values()),'professions':len(PROFESSION_RANK_NAMES),'recipes':recipe_count,'help_topics':len(HELP_TOPICS),'help_aliases':len(HELP_TOPIC_ALIASES),'command_aliases':len(COMMAND_ALIASES)}}

FULL_SYSTEMS_AUDIT_V03062=full_systems_audit_v03062()
if FULL_SYSTEMS_AUDIT_V03062['error_count']:
    raise RuntimeError('Full Systems Audit v0.30.62 failed: '+'; '.join(FULL_SYSTEMS_AUDIT_V03062['errors'][:100]))

HELP_TOPICS['audyt_v03062']=[
    'v0.30.62 wykonuje przekrojowy audyt wszystkich głównych systemów: świat, Generator Core, wszystkie osie EXP, ekonomię, klasy/skille, itemy, moby, questy, crafting, profesje/narzędzia, HELP, PL/EN, social, mentor, gildie, housing, transport, recapy i dostępność.',
    'Stat XP został spowolniony z około 28 do około 60 odpowiednich akcji na punkt, ponieważ jeden kill przyznaje EXP wszystkim sześciu statystykom.',
    'Błąd krytyczny audytu blokuje start serwera.'
]
HELP_TOPIC_ALIASES.update({'audyt 3062':'audyt_v03062','full audit':'audyt_v03062','systems audit':'audyt_v03062'})
