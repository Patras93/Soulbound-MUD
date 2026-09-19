
def v0190_log_curve(value, anchors):
    """v0.27 compatibility adapter for historical curve call sites.

    The old anchor Y values are deliberately ignored. X coordinates are used only
    as ordinal/range metadata so legacy systems can remain wired while Generator
    Core owns every active numeric result.
    """
    # Resolve a stable semantic identity without trusting the historical values.
    identity = "legacy-curve"
    for _name, _obj in globals().items():
        if _obj is anchors and isinstance(_name, str) and (_name.startswith("V019_") or _name.startswith("V020_") or _name.startswith("V021_") or _name.startswith("V022_")):
            identity = _name
            break
    try:
        xs = [max(1, int(round(float(x)))) for x, _y in anchors]
        maximum = max(xs) if xs else 400
    except Exception:
        maximum = 400
    raw = max(1, int(round(float(value))))
    # Real 1-400 axes keep their stage. Short ordinal systems (e.g. ranks 1-10)
    # are stretched through the same 1-400 Generator Core space.
    stage = generator_core_v027.clamp(raw, 1, 400) if maximum >= 300 else generator_core_v027.stage_from_index(raw, max(1, maximum))

    exact = {
        "V019_CLASS_REQ": lambda: generator_core_v027.axis_requirement("class", stage),
        "V019_SOUL_REQ": lambda: generator_core_v027.axis_requirement("soul", stage),
        "V019_SKILL_REQ": lambda: generator_core_v027.axis_requirement("skill", stage),
        "V019_PROF_REQ": lambda: generator_core_v027.axis_requirement("profession", stage),
        "V019_TOOL_REQ": lambda: generator_core_v027.axis_requirement("tool", stage),
        "V019_STAT_REQ": lambda: generator_core_v027.axis_requirement("stat", stage),
        "V019_SKILL_GAIN": lambda: generator_core_v027.axis_gain("skill", stage),
        "V019_PROF_GAIN": lambda: generator_core_v027.axis_gain("profession", stage),
        "V019_TOOL_GAIN": lambda: generator_core_v027.axis_gain("tool", stage),
        "V019_CLASS_KILL_NORMAL": lambda: generator_core_v027.axis_gain("class", stage, 1.0),
        "V019_CLASS_KILL_BOSS": lambda: generator_core_v027.axis_gain("class", stage, generator_core_v027.RANK_REWARD["boss"]),
        "V019_SOUL_KILL_NORMAL": lambda: generator_core_v027.axis_gain("soul", stage, 1.0),
        "V019_SOUL_KILL_BOSS": lambda: generator_core_v027.axis_gain("soul", stage, generator_core_v027.RANK_REWARD["boss"]),
        "V019_STAT_KILL_NORMAL": lambda: generator_core_v027.axis_gain("stat", stage, 1.0),
        "V019_STAT_KILL_BOSS": lambda: generator_core_v027.axis_gain("stat", stage, generator_core_v027.RANK_REWARD["boss"]),
        "V019_COIN_KILL_NORMAL": lambda: generator_core_v027.currency_for_stage(stage, "normal"),
        "V019_COIN_KILL_BOSS": lambda: generator_core_v027.currency_for_stage(stage, "boss"),
        "V019_HP_NORMAL": lambda: generator_core_v027.mob_hp(stage, "normal"),
        "V019_DAMAGE_NORMAL": lambda: generator_core_v027.mob_damage(stage, "normal"),
        "V019_QUEST_COIN": lambda: generator_core_v027.system_reward(stage, "quest"),
        "V019_ECONOMY_SINK": lambda: generator_core_v027.system_cost(stage, "economy"),
        "V019_RESOURCE_SALE": lambda: generator_core_v027.resource_sale_for_stage(stage),
    }
    if identity in exact:
        return min(V019_SAFE_INT, max(1, int(exact[identity]())))
    upper = identity.upper()
    if "HP" in upper:
        result = generator_core_v027.mob_hp(stage, "boss" if "BOSS" in upper else "normal")
    elif "DAMAGE" in upper or "DMG" in upper:
        result = generator_core_v027.mob_damage(stage, "boss" if "BOSS" in upper else "normal")
    elif "REQ" in upper or "COST" in upper:
        result = generator_core_v027.system_cost(stage, identity)
    elif "SALE" in upper:
        result = generator_core_v027.resource_sale_for_stage(stage)
    else:
        result = generator_core_v027.system_reward(stage, identity)
    return min(V019_SAFE_INT, max(1, int(result)))

V019_CLASS_REQ = ((1,1000),(10,80000),(20,500000),(30,1200000),(40,2500000),(50,5000000),(75,18000000),(100,60000000),(150,600000000),(200,6000000000),(250,60000000000),(300,600000000000),(350,6000000000000),(399,60000000000000))
V019_SOUL_REQ = ((1,500),(10,12000),(20,100000),(30,250000),(40,500000),(50,1000000),(75,6000000),(100,25000000),(150,250000000),(200,2500000000),(250,25000000000),(300,250000000000),(350,2500000000000),(399,25000000000000))
V019_SKILL_REQ = ((1,100),(10,1000),(20,5000),(30,12000),(40,25000),(50,50000),(75,180000),(100,600000),(150,6000000),(200,60000000),(250,500000000),(300,4000000000),(350,25000000000),(399,150000000000))
V019_PROF_REQ = ((1,200),(10,2000),(20,10000),(30,25000),(40,60000),(50,120000),(75,600000),(100,3000000),(150,30000000),(200,300000000),(250,3000000000),(300,30000000000),(350,300000000000),(399,3000000000000))
V019_TOOL_REQ = ((1,200),(10,1000),(20,5000),(30,12000),(40,30000),(50,80000),(75,400000),(100,2000000),(150,20000000),(200,200000000),(250,2000000000),(300,20000000000),(350,200000000000),(399,2000000000000))
V019_STAT_REQ = ((1,100),(10,100),(20,1000),(30,10000),(40,25000),(50,60000),(75,400000),(100,2000000),(150,40000000),(200,800000000),(300,80000000000),(400,8000000000000))
V019_SKILL_GAIN = ((1,30),(10,75),(20,150),(50,800),(100,10000),(200,1000000),(300,50000000),(399,1000000000))
V019_PROF_GAIN = ((1,40),(10,100),(20,250),(50,1500),(100,15000),(150,120000),(200,1000000),(250,8000000),(300,60000000),(350,400000000),(399,6000000000))
V019_TOOL_GAIN = ((1,30),(10,75),(20,180),(50,900),(100,10000),(200,700000),(300,40000000),(399,4000000000))

def v0190_requirement(kind, level):
    # v0.27.0: Generator Core jest jedynym źródłem krzywych progresji.
    return generator_core_v027.axis_requirement(kind, int(level))

def v0190_scaled_gain(raw, level, kind, typical_raw):
    # Stare wartości raw/typical_raw nie sterują już balansem. Sam fakt akcji
    # uruchamia wygenerowaną nagrodę właściwej osi progresji.
    if int(raw or 0) <= 0:
        return 0
    return generator_core_v027.axis_gain(kind, int(level), 1.0)

# Centralny generator walki i ekonomii v0.19.0.
# Nagrody nigdy nie są celowo obniżane poniżej starszych wartości.
# Balans długości gry wynika przede wszystkim z rosnących wymagań.
V019_CLASS_KILL_NORMAL = ((1,100),(5,300),(10,1500),(20,10000),(30,25000),(40,60000),(50,120000),(75,500000),(100,2000000),(150,20000000),(200,200000000),(250,2000000000),(300,20000000000),(350,200000000000),(400,2000000000000))
V019_CLASS_KILL_BOSS = ((1,1500),(10,75000),(20,250000),(30,450000),(40,750000),(50,1250000),(75,4500000),(100,15000000),(150,150000000),(200,1500000000),(250,15000000000),(300,150000000000),(350,1500000000000),(400,15000000000000))
V019_SOUL_KILL_NORMAL = ((1,40),(10,300),(20,2000),(30,4500),(50,20000),(75,90000),(100,400000),(150,4000000),(200,40000000),(250,400000000),(300,4000000000),(350,40000000000),(400,400000000000))
V019_SOUL_KILL_BOSS = ((1,300),(10,6000),(20,50000),(30,90000),(50,250000),(75,1500000),(100,6000000),(150,60000000),(200,600000000),(250,6000000000),(300,60000000000),(350,600000000000),(400,6000000000000))
V019_STAT_KILL_NORMAL = ((1,2),(10,10),(20,50),(30,250),(40,700),(50,3000),(75,20000),(100,100000),(150,2000000),(200,40000000),(250,400000000),(300,4000000000),(350,40000000000),(400,400000000000))
V019_STAT_KILL_BOSS = ((1,20),(10,100),(20,250),(30,1500),(40,5000),(50,15000),(75,100000),(100,500000),(150,10000000),(200,200000000),(250,2000000000),(300,20000000000),(350,200000000000),(400,2000000000000))
V019_COIN_KILL_NORMAL = ((1,10),(10,200),(20,2000),(30,7500),(40,20000),(50,50000),(75,250000),(100,1000000),(150,25000000),(200,500000000),(250,10000000000),(300,200000000000),(350,4000000000000),(400,80000000000000))
V019_COIN_KILL_BOSS = ((1,100),(10,5000),(20,50000),(30,150000),(40,400000),(50,1000000),(75,6000000),(100,30000000),(150,600000000),(200,15000000000),(250,300000000000),(300,6000000000000),(350,120000000000000),(400,2400000000000000))
V019_HP_NORMAL = ((1,80),(10,300),(20,900),(30,1800),(50,5000),(75,12000),(100,25000),(150,100000),(200,500000),(250,2500000),(300,10000000),(350,50000000),(400,200000000))
V019_DAMAGE_NORMAL = ((1,5),(10,15),(20,35),(30,60),(50,120),(75,260),(100,500),(150,1600),(200,5000),(250,16000),(300,50000),(350,160000),(400,500000))
V019_QUEST_COIN = ((1,100),(10,2000),(20,20000),(30,60000),(50,500000),(75,3000000),(100,20000000),(150,500000000),(200,10000000000),(250,200000000000),(300,4000000000000),(350,80000000000000),(400,1600000000000000))
V019_ECONOMY_SINK = ((1,200),(10,5000),(20,20000),(30,70000),(50,500000),(75,3000000),(100,25000000),(150,500000000),(200,10000000000),(250,200000000000),(300,4000000000000),(350,80000000000000),(400,1600000000000000))
V019_RESOURCE_SALE = ((1,5),(10,50),(20,200),(30,500),(50,2500),(75,12000),(100,50000),(150,1000000),(200,20000000),(250,400000000),(300,8000000000),(350,160000000000),(400,3200000000000))

def v0190_mob_stage(template):
    template = template or {}
    # Idempotencja: ten sam template może wystąpić w wielu spawnach. Po
    # pierwszej klasyfikacji etap nie może ponownie rosnąć od HP/damage już
    # zwiększonych przez generator.
    if template.get("v019_stage") is not None:
        return max(1, min(400, int(template.get("v019_stage") or 1)))
    if template.get("crypt_floor") is not None:
        return max(1, min(400, int(template.get("crypt_floor") or 1)))
    if template.get("astral_floor") is not None:
        return max(1, min(400, int(template.get("astral_floor") or 1)))
    if template.get("giant_fortress_floor") is not None:
        return max(1, min(400, int(template.get("giant_fortress_floor") or 1)))
    if template.get("mythic_crypt_floor") is not None:
        floor=max(1,int(template.get("mythic_crypt_floor") or 1))
        return max(130,min(400,120 + floor*2//5))
    if template.get("mythic_astral_floor") is not None:
        floor=max(1,int(template.get("mythic_astral_floor") or 1))
        return max(150,min(400,140 + floor*3//10))
    if template.get("v018_endless_band") is not None:
        band=max(1,int(template.get("v018_endless_band") or 1))
        return max(200,min(400,190 + band*5))
    if template.get("required_mastery") is not None:
        return max(1,min(400,int(template.get("required_mastery") or 1)))
    try:
        if "v0866_mob_progression_power" in globals():
            return max(1,min(400,int(round(v0866_mob_progression_power(template)))))
    except Exception:
        pass
    hp=max(1,float(template.get("max_hp",1) or 1))
    dmg=max(1,float(template.get("damage",1) or 1))
    estimate=max(1.0, ((hp/80.0)**0.45)*8.0 + ((dmg/5.0)**0.55)*4.0)
    return max(1,min(400,int(round(estimate))))

def v0190_mob_rank(template):
    template=template or {}
    if template.get("world_boss") or template.get("mythic_crypt_boss") or template.get("mythic_astral_boss") or template.get("v016_world_boss"):
        return "world_boss"
    if template.get("crypt_boss") or template.get("astral_boss") or template.get("giant_fortress_boss") or template.get("boss_mechanic") or template.get("v018_great_ruin_guardian"):
        return "boss"
    if template.get("mini_boss"):
        return "mini"
    if template.get("rare_mob") or template.get("rare_variant") or template.get("rare_troll") or template.get("v016_legendary_rare"):
        return "rare"
    if template.get("elite_affix"):
        return "elite"
    return "normal"

def v0190_generated_combat_reward(template, kind):
    template = template or {}
    stage = max(1, min(400, int(template.get("generator_level", template.get("v019_stage", 1)) or 1)))
    rank = str(template.get("generator_rank") or generator_core_v027.mob_rank(template))
    intensity = generator_core_v027.RANK_REWARD.get(rank, 1.0)
    if kind == "coins":
        return generator_core_v027.currency_for_stage(stage, rank)
    axis = {"class": "class", "soul": "soul", "stat": "stat", "character": "character"}[kind]
    return generator_core_v027.axis_gain(axis, stage, intensity)

def v0190_combat_reward(template, kind):
    # v0.27.0: brak max(stara, wygenerowana). Ręczne liczby nie wygrywają.
    return v0190_generated_combat_reward(template, kind)

def v0190_apply_combat_template(template):
    """Nadaj wygenerowane statystyki także mobom tworzonym w runtime."""
    if not isinstance(template, dict):
        return template
    stage = template.get("generator_level")
    if stage is None:
        stage = generator_core_v027.semantic_floor_level(template)
    if stage is None:
        for key in ("elite_base_template", "rare_base_template", "base_template", "template_id"):
            base = template.get(key)
            if base and base in globals().get("MOB_TEMPLATES", {}):
                stage = globals()["MOB_TEMPLATES"][base].get("generator_level")
                if stage is not None:
                    break
    if stage is None:
        stage = 1 + int(generator_core_v027.stable_unit(str(template.get("name", "mob"))) * 399)
    stage = max(1, min(400, int(stage)))
    rank = generator_core_v027.mob_rank(template)
    template["generator_level"] = stage
    template["v019_stage"] = stage
    template["max_hp"] = generator_core_v027.mob_hp(stage, rank)
    template["base_max_hp"] = template["max_hp"]
    template["damage"] = generator_core_v027.mob_damage(stage, rank)
    template["character_xp_reward"] = generator_core_v027.axis_gain("character", stage, generator_core_v027.RANK_REWARD.get(rank,1.0))
    template["class_xp_reward"] = generator_core_v027.axis_gain("class", stage, generator_core_v027.RANK_REWARD.get(rank,1.0))
    template["soul_reward"] = generator_core_v027.axis_gain("soul", stage, generator_core_v027.RANK_REWARD.get(rank,1.0))
    template["stat_reward"] = generator_core_v027.axis_gain("stat", stage, generator_core_v027.RANK_REWARD.get(rank,1.0))
    template["silver"] = generator_core_v027.currency_for_stage(stage, rank)
    template["gold"] = 0
    template["mithril"] = 0
    drops=template.get("drops")
    if isinstance(drops,dict) and drops:
        base_chance={"normal":.055,"elite":.09,"rare":.14,"mini":.22,"boss":.34,"world_boss":.48}.get(rank,.055)
        count=max(1,len(drops))
        for item_id in list(drops):
            chance=base_chance*generator_core_v027.stable_jitter(f"{template.get('name','mob')}:{item_id}",.22)/(count**.20)
            drops[item_id]=round(generator_core_v027.clamp(chance,.005,.85),5)
    return template

def v0190_quest_stage(quest):
    quest=quest or {}
    values=[1]
    for key in ("required_soul_level","min_tool_level","min_profession_level","required_mastery","level"):
        try:
            val=int(quest.get(key,0) or 0)
            if val>0: values.append(val)
        except Exception: pass
    target=quest.get("target")
    if target in globals().get("MOB_TEMPLATES",{}):
        values.append(v0190_mob_stage(MOB_TEMPLATES[target]))
    # Liczba wymaganych akcji podnosi wartość zadania, ale nie udaje levelu.
    needed=max(1,int(quest.get("needed",1) or 1))
    base=max(values)
    return max(1,min(400,int(round(base + min(30,math.sqrt(needed)*2)))))

def v0190_quest_currency_reward(quest):
    quest = quest or {}
    if quest.get("generator_level") is not None:
        return max(0, int(quest.get("reward_silver", 0) or 0))
    stage = v0190_quest_stage(quest)
    workload = max(1.0, min(8.0, math.sqrt(max(1, int(quest.get("needed",1) or 1)))))
    return int(round(generator_core_v027.currency_for_stage(stage) * max(2.0, workload) * (.72 if quest.get("repeatable") else 1.0)))

def v0190_quest_stat_reward(quest):
    quest = quest or {}
    if quest.get("generator_level") is not None:
        return max(0, int(quest.get("reward_stat_progress", 0) or 0))
    return generator_core_v027.axis_gain("stat", v0190_quest_stage(quest), 2.0)

def v0190_quest_soul_reward(quest):
    quest = quest or {}
    if quest.get("generator_level") is not None:
        return max(0, int(quest.get("reward_soul_xp", 0) or 0))
    return generator_core_v027.axis_gain("soul", v0190_quest_stage(quest), 2.0)

def v0270_quest_character_reward(quest):
    quest = quest or {}
    if quest.get("generator_level") is not None:
        return max(1, int(quest.get("character_xp_reward", 1) or 1))
    return generator_core_v027.axis_gain("character", v0190_quest_stage(quest), 2.0)

def v0190_economy_sink(stage, category="generic"):
    stage=max(1,min(400,int(stage)))
    mult={"skill":1.0,"equipment":0.60,"service":0.35,"generic":1.0}.get(category,1.0)
    return min(V019_SAFE_INT,max(1,int(round(generator_core_v027.item_price_for_stage(stage)*mult))))

def v0190_resource_stage(item_id, item=None):
    """Poziom ekonomiczny surowca 1-400 z Generator Core."""
    item = item or globals().get("ITEMS", {}).get(item_id, {}) or {}
    if item.get("generator_level") is not None:
        return max(1, min(400, int(item.get("generator_level") or 1)))
    base_id = str(item.get("base_resource_id") or item_id)
    base_item = globals().get("ITEMS", {}).get(base_id, item) or item
    # Ryby mają pełne tabele unlocków, gdy funkcja jest już zdefiniowana.
    try:
        if "fish_unlock_level" in globals() and (base_id in globals().get("FISH_RESOURCE_IDS", set()) or base_id.startswith("fish_400_")):
            return max(1, min(400, int(fish_unlock_level(base_id))))
    except Exception:
        pass
    for key in ("min_tool_level", "min_profession_level", "required_mastery", "level"):
        try:
            val = int(base_item.get(key, 0) or 0)
            if val > 0:
                return max(1, min(400, val))
        except Exception:
            pass
    text = f"{base_id} {base_item.get('desc','')}"
    matches = re.findall(r"(?:level|poziom|lvl)[ _:+-]*(\d{1,4})", text, flags=re.I)
    if not matches:
        matches = re.findall(r"(?:^|_)([1-4]\d{2})(?:_|$)", base_id)
    if matches:
        return max(1, min(400, max(int(x) for x in matches)))
    return 1

def v0190_resource_sale_coins(item_id, item=None):
    item = item or globals().get("ITEMS", {}).get(item_id, {}) or {}
    stage = v0190_resource_stage(item_id, item)
    mult = max(1.0, float(item.get("rare_value_multiplier", 1.0) or 1.0))
    return generator_core_v027.resource_sale_for_stage(stage, mult)

CHARACTER_MAX_LEVEL = 400
STAT_MAX_LEVEL = None  # v0.27.1: statystyki są bez twardego limitu
def character_xp_to_next(level):
    level=max(1,min(CHARACTER_MAX_LEVEL,int(level)))
    if level >= CHARACTER_MAX_LEVEL:
        return 0
    return generator_core_v027.axis_requirement("character", level)

CLASS_MASTERY_MAX_LEVEL = 400
CLASS_MASTERY_XP_BASE = 1000
CLASS_MASTERY_XP_STEP = 250
MULTICLASS_MAX_ACTIVE = 3

def class_mastery_xp_to_next(level):
    level = max(1, min(CLASS_MASTERY_MAX_LEVEL, int(level)))
    if level >= CLASS_MASTERY_MAX_LEVEL:
        return 0
    return v0190_requirement("class", level)

def class_type_for_name(class_name):
    for cname, ctype, weapon, base in CLASSES:
        if cname == class_name:
            return ctype
    return "physical"

SKILL_MAX_LEVEL = 400
SKILL_XP_BASE = 50
# v0.8.64: stara wartość 25 dawała około 50 tysięcy użyć na jeden
# skill 1-200. Mniejszy krok + większe XP za użycie utrzymują długą,
# ale osiągalną progresję.
SKILL_XP_STEP = 8

def skill_xp_to_next(level):
    level = max(1, min(SKILL_MAX_LEVEL, int(level)))
    if level >= SKILL_MAX_LEVEL:
        return 0
    return v0190_requirement("skill", level)

def skill_power_multiplier(level):
    return generator_core_v027.skill_level_power(level)

def skill_cooldown_multiplier(level):
    return generator_core_v027.skill_cooldown_factor(level)

# v0.35.0: osobna biegłość zwykłego ataku Broni Duszy.
# Nie rozwija skilli/spelli i nie jest Soul Levelem ani Biegłością klasy.
SOUL_WEAPON_MASTERY_MAX_LEVEL = 400

def soul_weapon_mastery_xp_to_next(level):
    level = max(1, min(SOUL_WEAPON_MASTERY_MAX_LEVEL, int(level)))
    if level >= SOUL_WEAPON_MASTERY_MAX_LEVEL:
        return 0
    # Ta sama długość pojedynczego poziomu co Skill Level: około 18 realnych trafień.
    return v0190_requirement("skill", level)

def soul_weapon_mastery_bonuses(level):
    level = max(1, min(SOUL_WEAPON_MASTERY_MAX_LEVEL, int(level)))
    progress = (level - 1) / float(SOUL_WEAPON_MASTERY_MAX_LEVEL - 1)
    # Premie są celowo umiarkowane i dotyczą wyłącznie podstawowego ataku.
    return {
        "damage_percent": round(8.0 * (progress ** 0.85), 4),
        "crit_chance": round(0.02 * (progress ** 0.90), 6),
        "crit_damage_percent": round(12.0 * (progress ** 0.90), 4),
        "boss_damage_percent": round(5.0 * (progress ** 1.05), 4),
        "echo_chance": round((0.01 + 0.04 * (((level - 200) / 200.0) ** 0.85)) if level >= 200 else 0.0, 6),
        "echo_damage_percent": 30.0 if level >= 200 else 0.0,
    }

BANK_ROOM = "market"

PROFESSION_COOLDOWN = 2.0

# v0.8.66 - realny czas czynności wynika z poziomu UMIEJĘTNOŚCI/PROFESJI.
# Narzędzie nie skraca czasu; jego level odblokowuje lepszy surowiec/jakość/bonus.
TOOL_ACTION_BASE_SECONDS = {
    # v0.9.6: Wędkarstwo zaczyna od 16 s i schodzi płynnie do 3 s przy 200.
    "fishing": 16,
    "mining": 30,
    "woodcutting": 24,
    "crafting": 20,
    "cooking": 12,
    "herbalism": 10,
    "alchemy": 18,
    "jewelcrafting": 20,
}

TOOL_ACTION_MIN_SECONDS = {
    "fishing": 3,
    "mining": 10,
    "woodcutting": 8,
    "crafting": 7,
    "cooking": 4,
    "herbalism": 3,
    "alchemy": 6,
    "jewelcrafting": 7,
}

REST_TICK_SECONDS = 5.0
REST_REGEN_PERCENT = 10

# v0.9.6: wartości referencyjne z v0.9.5 służą tylko do rebalansu
# XP/cen/zleceń po zmianie czasu 15->5 na 16->3.
V095_FISHING_BASE_SECONDS = 15
V095_FISHING_MIN_SECONDS = 5

PROFESSION_SPEED_CAP_LEVEL = 200

# v0.10.2: Tool XP dla narzędzi zbierackich jest wyrównany względem
# rzeczywistego czasu jednej akcji. Wcześniej Kilof i Piła dostawały prawie
# tyle samo XP co znacznie szybszy Sierp, więc wbijanie ich leveli trwało
# wielokrotnie dłużej. Mnożniki nie zmieniają Profession XP ani dropu.
GATHER_TOOL_LEVELING_MULTIPLIERS = {
    "fishing": 1.50,
    "mining": 3.00,
    "woodcutting": 2.40,
    "herbalism": 1.00,
}

def balanced_gather_tool_xp(tool_type, raw_xp):
    multiplier = GATHER_TOOL_LEVELING_MULTIPLIERS.get(str(tool_type), 1.0)
    return max(1, int(round(max(1, int(raw_xp)) * multiplier)))

def _profession_speed_progress(level):
    # Stary balans timerów 1-200 pozostaje 1:1. Po 200 profesja rozwija się
    # dalej, ale nie skraca akcji poniżej ustalonego minimum.
    effective = max(1, min(PROFESSION_SPEED_CAP_LEVEL, int(level)))
    return (effective - 1) / max(1, PROFESSION_SPEED_CAP_LEVEL - 1)

def _linear_profession_seconds(level, base_seconds, minimum_seconds):
    progress = _profession_speed_progress(level)
    seconds = round(base_seconds - (base_seconds - minimum_seconds) * progress)
    return max(int(minimum_seconds), int(seconds))

def v095_fishing_action_seconds(level):
    return _linear_profession_seconds(level, V095_FISHING_BASE_SECONDS, V095_FISHING_MIN_SECONDS)

def v096_fishing_action_seconds(level):
    return _linear_profession_seconds(
        level, TOOL_ACTION_BASE_SECONDS["fishing"], TOOL_ACTION_MIN_SECONDS["fishing"]
    )

def v096_fishing_reward_scale(level):
    """Skaluje nagrody per połów, aby XP/h nie eksplodował przy 3 s endgame.

    Używa ciągłej krzywej zamiast zaokrąglonych sekund, żeby współczynnik
    malał płynnie i nigdy nie skakał w górę przez zaokrąglenie timera.
    """
    level = max(1, min(PROFESSION_MAX_LEVEL, int(level)))
    progress = _profession_speed_progress(level)
    old_seconds = V095_FISHING_BASE_SECONDS - (V095_FISHING_BASE_SECONDS - V095_FISHING_MIN_SECONDS) * progress
    new_seconds = TOOL_ACTION_BASE_SECONDS["fishing"] - (TOOL_ACTION_BASE_SECONDS["fishing"] - TOOL_ACTION_MIN_SECONDS["fishing"]) * progress
    return max(0.55, min(1.10, new_seconds / old_seconds))

def v096_fishing_workload_scale(level):
    """Ile sztuk potrzeba dla podobnego czasu kontraktu jak w v0.9.5."""
    return max(1.0, min(1.75, 1.0 / v096_fishing_reward_scale(level)))

RIVER_FISHING_ROOMS = {"riverbank", "stone_bridge"}
LAKE_FISHING_ROOMS = {"lake_shore"}
SEA_FISHING_ROOMS = {"sea_pier"}
OCEAN_FISHING_ROOMS = {"ocean_platform"}
FRESHWATER_FISHING_ROOMS = RIVER_FISHING_ROOMS | LAKE_FISHING_ROOMS
MARINE_FISHING_ROOMS = SEA_FISHING_ROOMS | OCEAN_FISHING_ROOMS
FISHING_ROOMS = FRESHWATER_FISHING_ROOMS | MARINE_FISHING_ROOMS

# v0.9.5: opis ekologiczny łowiska jest oddzielony od technicznej puli
# river/lake/sea/ocean. Dzięki temu np. Czarny Kanał może mówić graczowi
# "Łowisko: Kanał", a nadal korzystać z rzecznej progresji ryb.
FISHING_WATER_TYPE_OVERRIDES = {
    "riverbank": "Rzeka",
    "stone_bridge": "Rzeka",
    "lake_shore": "Jezioro",
    "sea_pier": "Morze",
    "ocean_platform": "Ocean",
    "sewer_black_channel": "Kanał",
    "forest_stream": "Strumień",
    "blackwater_pool": "Bagienne rozlewisko",
    "troll_underground_river": "Podziemna rzeka",
    "ice_cave_frozen_lake": "Zamarznięte jezioro",
}

FISHING_HABITAT_LABELS = {
    "river": "rzeka",
    "lake": "jezioro",
    "sea": "morze",
    "ocean": "ocean",
}

# Preferowane pule ekologiczne dla wybranych istniejących wód świata.
# Filtr działa wyłącznie na gatunkach już odblokowanych przez Wędkę;
# gdy na bardzo niskim levelu przecięcie byłoby puste, zachowujemy pulę bazową.
FISHING_ECOLOGY_PREFERRED_IDS = {
    "forest_stream": {
        "small_fish", "dace", "river_perch", "chub", "stone_loach",
        "brown_trout", "grayling", "silver_trout", "golden_trout",
        "salmon", "river_taimen", "spirit_grayling",
    },
    "blackwater_pool": {
        "lake_roach", "crucian_carp", "bream", "tench", "lake_perch",
        "pike", "zander", "freshwater_eel", "golden_tench",
        "deepwater_pike", "moon_carp", "astral_pike",
    },
    "troll_underground_river": {
        "small_fish", "dace", "stone_loach", "burbot", "river_catfish",
        "moon_eel", "ancient_sturgeon", "runic_sturgeon", "chrono_eel",
    },
    "ice_cave_frozen_lake": {
        "lake_roach", "lake_smelt", "vendace", "whitefish", "lake_char",
        "lake_trout", "crystal_whitefish", "starfin_char", "mirror_sturgeon",
    },
}
MINE_MIN_FLOOR = 1
# v0.9.13: 200 oznacza wyłącznie ręcznie przygotowaną część kopalni.
# Kolejne poziomy są generowane na żądanie bez górnego limitu.
MINE_PREGENERATED_MAX_FLOOR = 200
MINE_MAX_FLOOR = MINE_PREGENERATED_MAX_FLOOR  # legacy compatibility only
MINE_WALL_SCALING_START_FLOOR = 10

def mine_wall_hit_range(floor):
    """Zwraca losowy przedział wytrzymałości ściany dla danego piętra."""
    floor = max(MINE_MIN_FLOOR, int(floor))
    effective_floor = min(400, floor)
    if effective_floor < MINE_WALL_SCALING_START_FLOOR:
        return 3, 8
    low = max(6, int(math.floor(effective_floor * 0.70)))
    high = max(low + 1, int(math.ceil(effective_floor * 1.30)))
    return low, high

def roll_mine_wall_hits_required(floor, current_hits=0):
    """Losuje próg raz na ścianę; istniejący postęp nigdy nie jest tracony."""
    low, high = mine_wall_hit_range(floor)
    minimum = max(low, int(current_hits) + 1)
    if minimum > high:
        return int(current_hits) + 1
    return random.randint(minimum, high)

def mine_floor_id(floor):
    return f"mine_floor_{int(floor)}"

def mine_floor_number(room_id):
    match = re.fullmatch(r"mine_floor_(\d+)(?:_r\d+)?", str(room_id or ""))
    if not match:
        return None
    floor = int(match.group(1))
    return floor if floor >= MINE_MIN_FLOOR else None

MINING_DEPTH_ROOMS = {
    mine_floor_id(floor)
    for floor in range(MINE_MIN_FLOOR, MINE_PREGENERATED_MAX_FLOOR + 1)
}
MINING_ROOMS = {
    "cave_entrance", "cave_tunnel", "crystal_chamber"
} | MINING_DEPTH_ROOMS


UNIFIED_DEEP_MINE_STATIC_ROOMS = {
    "cave_entrance", "cave_tunnel", "crystal_chamber"
}

def is_mining_room(room_id):
    """v0.25.1: mining is available only in the single Deep Mine complex."""
    room_id = str(room_id or "")
    return room_id in UNIFIED_DEEP_MINE_STATIC_ROOMS or mine_floor_number(room_id) is not None

AUTO_FISHING_ROUTE = (
    "riverbank", "lake_shore", "sea_pier", "ocean_platform",
)
AUTO_WOODCUTTING_ROUTE = (
    "lumberjack_camp", "whisper_grove", "meadow",
    "old_road", "deep_grove",
)
AUTO_HERBALISM_ROUTE = (
    "meadow", "mint_meadow", "flower_meadow", "lakeside_meadow",
    "riverbank", "lake_shore", "whisper_grove",
    "herbalist_hut", "old_road", "deep_grove",
)

WOODCUTTING_ROOMS = {"lumberjack_camp", "meadow", "whisper_grove", "deep_grove", "old_road"}
MEADOW_HERBALISM_ROOMS = {
    "meadow", "mint_meadow", "flower_meadow", "lakeside_meadow"
}
HERBALISM_ROOMS = {
    "herbalist_hut", "meadow", "mint_meadow", "flower_meadow",
    "lakeside_meadow", "whisper_grove", "deep_grove",
    "riverbank", "lake_shore", "old_road"
}

ENDGAME_FISH_UNLOCKS = {
    "river": (
        (100, "soulfin_trout"),
        (140, "runic_sturgeon"),
        (180, "chrono_eel"),
        (200, "eternal_salmon"),
    ),
    "lake": (
        (100, "crystal_carp"),
        (140, "moon_pike"),
        (180, "starfin_char"),
        (200, "mirror_leviathan"),
    ),
    "sea": (
        (100, "storm_cod"),
        (140, "abyss_halibut"),
        (180, "void_turbot"),
        (200, "crown_monkfish"),
    ),
    "ocean": (
        (100, "celestial_tuna"),
        (120, "dragon_mahi"),
        (120, "reef_shark"),
        (140, "abyss_tuna"),
        (140, "mako_shark"),
        (160, "storm_marlin"),
        (160, "hammerhead_shark"),
        (180, "moon_leviathan"),
        (180, "tiger_shark"),
        (190, "ghost_marlin"),
        (200, "great_white_shark"),
        (200, "eternal_coelacanth"),
    ),
}

BASE_FISH_MIN_TOOL_LEVELS = {
    # Zwykły Tuńczyk jest dużym oceanicznym połowem
    # i nie powinien pojawiać się na niskich levelach Wędki.
    "tuna": 80,
}

MORE_FISH_UNLOCKS = {
    "river": (
        (1, "river_bleak"),
        (5, "stone_loach"),
        (15, "river_bream"),
        (30, "brown_trout"),
        (50, "river_taimen"),
        (75, "emerald_barbel"),
        (110, "spirit_grayling"),
        (150, "bloodfin_salmon"),
        (175, "star_river_eel"),
        (200, "eternal_river_dragon"),
    ),
    "lake": (
        (1, "lake_gudgeon"),
        (8, "lake_smelt"),
        (20, "blue_bream"),
        (35, "golden_tench"),
        (55, "deepwater_pike"),
        (80, "crystal_whitefish"),
        (110, "moon_carp"),
        (150, "astral_pike"),
        (175, "mirror_sturgeon"),
        (200, "eternal_lake_serpent"),
    ),
    "sea": (
        (1, "sand_eel"),
        (10, "garfish"),
        (20, "sea_bream"),
        (35, "bluefish"),
        (55, "conger_eel"),
        (80, "red_snapper"),
        (110, "storm_herring"),
        (150, "abyss_conger"),
        (175, "void_sole"),
        (200, "eternal_sea_drake"),
    ),
    "ocean": (
        (1, "flying_fish"),
        (15, "bonito"),
        (30, "yellowfin_tuna"),
        (50, "king_mackerel"),
        (70, "marlin_black"),
        (90, "opah"),
        (120, "celestial_swordfish"),
        (150, "astral_sunfish"),
        (180, "void_marlin"),
        (200, "world_leviathan"),
    ),
}

ENDGAME_ORE_UNLOCKS = (
    (100, "cobalt_ore"),
    (120, "runestone_ore"),
    (140, "dragonsteel_ore"),
    (160, "astral_ore"),
    (180, "void_ore"),
    (200, "eternium_ore"),
)

ENDGAME_WOOD_UNLOCKS = (
    (100, "runewood_log"),
    (120, "dragonwood_log"),
    (140, "astralwood_log"),
    (160, "voidwood_log"),
    (180, "starheart_log"),
    (200, "eternal_worldwood_log"),
)

ENDGAME_HERB_UNLOCKS = (
    (100, "sunfire_bloom"),
    (120, "dragon_sage"),
    (140, "astral_orchid"),
    (160, "void_lotus"),
    (180, "phoenix_crown"),
    (200, "eternal_blossom"),
)

# v0.9.12: dalsza progresja narzędzi 201-400 ma własne zasoby.
PROGRESSION_400_LEVELS = tuple(range(220, 401, 20))
ENDGAME_ORE_UNLOCKS += tuple((level, f"ore_400_{level}") for level in PROGRESSION_400_LEVELS)
ENDGAME_WOOD_UNLOCKS += tuple((level, f"wood_400_{level}") for level in PROGRESSION_400_LEVELS)
ENDGAME_HERB_UNLOCKS += tuple((level, f"herb_400_{level}") for level in PROGRESSION_400_LEVELS)
for _habitat in tuple(ENDGAME_FISH_UNLOCKS):
    ENDGAME_FISH_UNLOCKS[_habitat] = tuple(ENDGAME_FISH_UNLOCKS[_habitat]) + tuple(
        (level, f"fish_400_{_habitat}_{level}") for level in PROGRESSION_400_LEVELS
    )

def unlocked_resource_pool(
    base_items,
    unlocks,
    tool_level,
):
    result = []
    tool_level = int(tool_level)

    for item_id in base_items:
        minimum = int(
            BASE_FISH_MIN_TOOL_LEVELS.get(item_id, 1)
        )
        if tool_level >= minimum and item_id not in result:
            result.append(item_id)

    for required_level, item_id in unlocks:
        if (
            tool_level >= int(required_level)
            and item_id not in result
        ):
            result.append(item_id)

    return tuple(result)


def add_more_fish_to_pool(pool, habitat, tool_level):
    result = list(pool)
    for required_level, item_id in MORE_FISH_UNLOCKS.get(habitat, ()):
        if int(tool_level) >= int(required_level) and item_id not in result:
            result.append(item_id)
    for required_level, item_id, _name in WORLD_FISH_UNLOCKS.get(habitat, ()):
        if int(tool_level) >= int(required_level) and item_id not in result:
            result.append(item_id)
    return tuple(result)

WORLD_FISH_UNLOCKS = {
    "river": (
        (1, 'world_arapaima', 'Arapaima'),
        (5, 'world_red_bellied_piranha', 'Pirania czerwonobrzucha'),
        (10, 'world_black_piranha', 'Pirania czarna'),
        (15, 'world_pacu', 'Pacu'),
        (20, 'world_tambaqui', 'Tambaqui'),
        (25, 'world_golden_dorado', 'Dorado złociste'),
        (30, 'world_peacock_bass', 'Bass pawiooki'),
        (35, 'world_nile_perch', 'Okoń nilowy'),
        (40, 'world_goliath_tigerfish', 'Tygrysica goliat'),
        (45, 'world_mahseer', 'Mahseer'),
        (50, 'world_rohu', 'Rohu'),
        (55, 'world_catla', 'Katla'),
        (60, 'world_giant_snakehead', 'Wężogłów olbrzymi'),
        (65, 'world_giant_gourami', 'Gurami olbrzymi'),
        (70, 'world_clown_knifefish', 'Nożowiec chitala'),
        (75, 'world_electric_eel', 'Węgorz elektryczny'),
        (80, 'world_alligator_gar', 'Niszczuka krokodyla'),
        (85, 'world_american_paddlefish', 'Wiosłonos amerykański'),
        (90, 'world_bowfin', 'Amia'),
        (95, 'world_muskellunge', 'Muskellunge'),
        (100, 'world_brook_trout', 'Pstrąg źródlany'),
        (105, 'world_rainbow_trout', 'Pstrąg tęczowy'),
        (110, 'world_chinook_salmon', 'Łosoś królewski'),
        (115, 'world_sockeye_salmon', 'Łosoś nerka'),
        (120, 'world_coho_salmon', 'Łosoś kiżucz'),
        (125, 'world_chum_salmon', 'Łosoś keta'),
        (130, 'world_pink_salmon', 'Łosoś różowy'),
        (135, 'world_cutthroat_trout', 'Pstrąg łososiowy'),
        (140, 'world_freshwater_drum', 'Kulbak słodkowodny'),
        (145, 'world_blue_catfish', 'Sum błękitny'),
        (150, 'world_channel_catfish', 'Sum kanałowy'),
        (155, 'world_flathead_catfish', 'Sum płaskogłowy'),
        (160, 'world_grass_carp', 'Amur biały'),
        (165, 'world_bighead_carp', 'Tołpyga pstra'),
        (170, 'world_silver_carp', 'Tołpyga biała'),
        (175, 'world_black_carp', 'Amur czarny'),
        (180, 'world_wels_catfish', 'Sum europejski'),
        (185, 'world_freshwater_stingray', 'Płaszczka słodkowodna'),
        (195, 'world_giant_barb', 'Brzana olbrzymia'),
        (200, 'world_mekong_giant_catfish', 'Sum mekongski'),
    ),
    "lake": (
        (1, 'world_largemouth_bass', 'Bass wielkogębowy'),
        (5, 'world_smallmouth_bass', 'Bass małogębowy'),
        (10, 'world_black_crappie', 'Pomoxis czarny'),
        (15, 'world_white_crappie', 'Pomoxis biały'),
        (20, 'world_bluegill', 'Bass słoneczny'),
        (25, 'world_pumpkinseed', 'Bass dyniowy'),
        (30, 'world_yellow_perch', 'Okoń żółty'),
        (35, 'world_walleye', 'Sandacz amerykański'),
        (40, 'world_sauger', 'Sandacz kanadyjski'),
        (45, 'world_kokanee_salmon', 'Kokanee'),
        (50, 'world_cisco', 'Sielawa amerykańska'),
        (55, 'world_lake_sturgeon', 'Jesiotr jeziorowy'),
        (60, 'world_brown_bullhead', 'Sumik brunatny'),
        (65, 'world_black_bullhead', 'Sumik czarny'),
        (70, 'world_yellow_bullhead', 'Sumik żółty'),
        (75, 'world_nile_tilapia', 'Tilapia nilowa'),
        (80, 'world_mozambique_tilapia', 'Tilapia mozambicka'),
        (85, 'world_blue_tilapia', 'Tilapia niebieska'),
        (90, 'world_oscar_cichlid', 'Pielęgnica pawiooka'),
        (95, 'world_discus', 'Paletka'),
        (100, 'world_freshwater_angelfish', 'Skalar'),
        (105, 'world_silver_arowana', 'Arowana srebrna'),
        (110, 'world_asian_arowana', 'Arowana azjatycka'),
        (115, 'world_giant_barbel_siam', 'Brzana syjamska'),
        (120, 'world_giant_freshwater_whipray', 'Płaszczka rzeczna olbrzymia'),
        (125, 'world_pangas_catfish', 'Panga'),
        (130, 'world_redtail_catfish', 'Sum czerwonoogonowy'),
        (135, 'world_ripsaw_catfish', 'Sum kolczasty'),
        (140, 'world_payara', 'Payara'),
        (145, 'world_wolf_fish', 'Trahira'),
        (150, 'world_arctic_grayling', 'Lipień arktyczny'),
        (155, 'world_lake_chub', 'Jelec jeziorowy'),
        (160, 'world_round_whitefish', 'Sieja okrągła'),
        (165, 'world_inconnu', 'Nelma'),
        (170, 'world_huchen', 'Głowacica'),
        (175, 'world_ide_world', 'Jaź syberyjski'),
        (180, 'world_golden_mahseer', 'Mahseer złoty'),
        (185, 'world_marble_trout', 'Pstrąg marmurkowy'),
        (195, 'world_taimen', 'Tajmień syberyjski'),
        (200, 'world_chinese_perch', 'Okoń chiński'),
    ),
    "sea": (
        (1, 'world_atlantic_tarpon', 'Tarpon atlantycki'),
        (5, 'world_bonefish', 'Albula'),
        (10, 'world_permit_fish', 'Permit'),
        (15, 'world_common_snook', 'Snook'),
        (20, 'world_red_drum', 'Kulbin czerwony'),
        (25, 'world_black_drum', 'Kulbin czarny'),
        (30, 'world_striped_bass', 'Moron prążkowany'),
        (35, 'world_atlantic_croaker', 'Kulbin atlantycki'),
        (40, 'world_sheepshead', 'Sargus owczy'),
        (45, 'world_pompano', 'Pompan'),
        (50, 'world_greater_amberjack', 'Seriola olbrzymia'),
        (55, 'world_yellowtail_snapper', 'Lucjan żółtoogonowy'),
        (60, 'world_mangrove_snapper', 'Lucjan namorzynowy'),
        (65, 'world_lane_snapper', 'Lucjan pręgowany'),
        (70, 'world_red_grouper', 'Strzępiel czerwony'),
        (75, 'world_goliath_grouper', 'Strzępiel goliat'),
        (80, 'world_nassau_grouper', 'Strzępiel nassauski'),
        (85, 'world_european_conger', 'Konger europejski'),
        (90, 'world_mediterranean_moray', 'Murena śródziemnomorska'),
        (95, 'world_giant_moray', 'Murena olbrzymia'),
        (100, 'world_red_lionfish', 'Skrzydlica ognista'),
        (105, 'world_stonefish', 'Szkaradnica'),
        (110, 'world_scorpionfish', 'Skorpena'),
        (115, 'world_queen_triggerfish', 'Rogatnica królewska'),
        (120, 'world_clown_triggerfish', 'Rogatnica klaun'),
        (125, 'world_bumphead_parrotfish', 'Papugoryba garbogłowa'),
        (130, 'world_napoleon_wrasse', 'Wargacz garbogłowy'),
        (135, 'world_corkwing_wrasse', 'Wargacz korkowy'),
        (140, 'world_atlantic_bonito', 'Bonito atlantyckie'),
        (145, 'world_spanish_mackerel', 'Makrela hiszpańska'),
        (150, 'world_atlantic_mackerel', 'Makrela atlantycka'),
        (155, 'world_horse_mackerel', 'Ostrobok'),
        (160, 'world_capelin', 'Gromadnik'),
        (165, 'world_atlantic_saury', 'Sajra atlantycka'),
        (170, 'world_john_dory', 'Piotrosz'),
        (175, 'world_tub_gurnard', 'Kurek czerwony'),
        (180, 'world_wolffish', 'Zębacz pasiasty'),
        (185, 'world_lumpsucker', 'Tasza'),
        (195, 'world_atlantic_anglerfish', 'Żabnica atlantycka'),
        (200, 'world_atlantic_halibut_world', 'Halibut atlantycki'),
    ),
    "ocean": (
        (1, 'world_blue_marlin', 'Marlin błękitny'),
        (5, 'world_white_marlin', 'Marlin biały'),
        (10, 'world_striped_marlin', 'Marlin pasiasty'),
        (15, 'world_longbill_spearfish', 'Włócznik długodzioby'),
        (20, 'world_shortbill_spearfish', 'Włócznik krótkodzioby'),
        (25, 'world_atlantic_bluefin_tuna_world', 'Tuńczyk błękitnopłetwy atlantycki'),
        (30, 'world_southern_bluefin_tuna', 'Tuńczyk błękitnopłetwy południowy'),
        (35, 'world_skipjack_tuna', 'Bonito pasiaste'),
        (40, 'world_blackfin_tuna', 'Tuńczyk czarnopłetwy'),
        (45, 'world_longtail_tuna', 'Tuńczyk długogonowy'),
        (50, 'world_escolar', 'Eskolar'),
        (55, 'world_oilfish', 'Kostropak'),
        (60, 'world_oarfish', 'Wstęgor królewski'),
        (65, 'world_lancetfish', 'Lancetnik długonosy'),
        (70, 'world_pomfret', 'Pomfret'),
        (75, 'world_remora', 'Podnawka'),
        (80, 'world_pilot_fish', 'Pilot'),
        (85, 'world_blue_shark', 'Żarłacz błękitny'),
        (90, 'world_oceanic_whitetip_shark', 'Żarłacz białopłetwy oceaniczny'),
        (95, 'world_common_thresher', 'Kosogon pospolity'),
        (100, 'world_bigeye_thresher', 'Kosogon wielkooki'),
        (105, 'world_porbeagle', 'Żarłacz śledziowy'),
        (110, 'world_greenland_shark', 'Rekin polarny'),
        (115, 'world_salmon_shark', 'Rekin łososiowy'),
        (120, 'world_goblin_shark', 'Rekin chochlik'),
        (125, 'world_megamouth_shark', 'Rekin wielkogębowy'),
        (130, 'world_cookiecutter_shark', 'Rekin foremkowy'),
        (135, 'world_bluntnose_sixgill', 'Sześcioszpar szary'),
        (140, 'world_frilled_shark', 'Chlamida'),
        (145, 'world_whale_shark', 'Rekin wielorybi'),
        (150, 'world_manta_ray', 'Manta oceaniczna'),
        (155, 'world_spotted_eagle_ray', 'Orleń cętkowany'),
        (160, 'world_devil_ray', 'Diabeł morski'),
        (165, 'world_sunfish_sharptail', 'Samogłów ostroogonowy'),
        (170, 'world_slender_sunfish', 'Samogłów smukły'),
        (175, 'world_antarctic_toothfish', 'Antarktyczny kłykacz'),
        (180, 'world_patagonian_toothfish', 'Kłykacz patagoński'),
        (185, 'world_orange_roughy', 'Gardłosz atlantycki'),
        (195, 'world_grenadier', 'Buławik'),
        (200, 'world_coelacanth_world', 'Latimeria'),
    ),
}

WORLD_HERB_UNLOCKS = {
    "meadow": (
        (1, 'world_rosemary', 'Rozmaryn'),
        (10, 'world_thyme', 'Tymianek'),
        (20, 'world_basil', 'Bazylia'),
        (30, 'world_oregano', 'Oregano'),
        (40, 'world_parsley', 'Pietruszka'),
        (50, 'world_dill', 'Koper'),
        (60, 'world_coriander', 'Kolendra'),
        (70, 'world_fennel', 'Koper włoski'),
        (80, 'world_tarragon', 'Estragon'),
        (90, 'world_marjoram', 'Majeranek'),
        (100, 'world_savory', 'Cząber'),
        (110, 'world_chives', 'Szczypiorek'),
        (120, 'world_garlic', 'Czosnek'),
        (130, 'world_ginger', 'Imbir'),
        (140, 'world_turmeric', 'Kurkuma'),
        (150, 'world_galangal', 'Galangal'),
        (160, 'world_cardamom', 'Kardamon'),
        (170, 'world_clove', 'Goździk'),
        (190, 'world_vanilla', 'Wanilia'),
        (200, 'world_saffron', 'Szafran'),
    ),
    "water": (
        (1, 'world_lemongrass', 'Trawa cytrynowa'),
        (10, 'world_aloe_vera', 'Aloes'),
        (20, 'world_calendula', 'Nagietek'),
        (30, 'world_echinacea', 'Jeżówka'),
        (40, 'world_st_johns_wort', 'Dziurawiec'),
        (50, 'world_ribwort_plantain', 'Babka lancetowata'),
        (60, 'world_dandelion', 'Mniszek lekarski'),
        (70, 'world_burdock', 'Łopian'),
        (80, 'world_horsetail', 'Skrzyp polny'),
        (90, 'world_elderflower', 'Kwiat bzu czarnego'),
        (100, 'world_hawthorn', 'Głóg'),
        (110, 'world_rosehip', 'Dzika róża'),
        (120, 'world_hibiscus', 'Hibiskus'),
        (130, 'world_jasmine', 'Jaśmin'),
        (140, 'world_arnica', 'Arnika'),
        (150, 'world_comfrey', 'Żywokost'),
        (160, 'world_mugwort', 'Bylica pospolita'),
        (170, 'world_wormwood', 'Piołun'),
        (190, 'world_skullcap', 'Tarczyca bajkalska'),
        (200, 'world_passionflower', 'Męczennica'),
    ),
    "forest": (
        (1, 'world_hops', 'Chmiel'),
        (10, 'world_licorice_root', 'Lukrecja'),
        (20, 'world_marshmallow_root', 'Prawoślaz'),
        (30, 'world_fenugreek', 'Kozieradka'),
        (40, 'world_cumin', 'Kmin rzymski'),
        (50, 'world_anise', 'Anyż'),
        (60, 'world_star_anise', 'Anyż gwiazdkowy'),
        (70, 'world_black_cumin', 'Czarnuszka'),
        (80, 'world_sesame', 'Sezam'),
        (90, 'world_flax', 'Len'),
        (100, 'world_chia', 'Chia'),
        (110, 'world_amaranth', 'Amarantus'),
        (120, 'world_quinoa', 'Komosa ryżowa'),
        (130, 'world_maca', 'Maca'),
        (140, 'world_guarana', 'Guarana'),
        (150, 'world_yerba_mate', 'Yerba mate'),
        (160, 'world_tea_leaf', 'Liść herbaty'),
        (170, 'world_coffee_berry', 'Owoc kawowca'),
        (190, 'world_cocoa_pod', 'Owoc kakaowca'),
        (200, 'world_kola_nut', 'Orzech kola'),
    ),
    "deep": (
        (1, 'world_holy_basil', 'Tulsi'),
        (10, 'world_ashwagandha', 'Ashwagandha'),
        (20, 'world_moringa', 'Moringa'),
        (30, 'world_neem', 'Neem'),
        (40, 'world_gotu_kola', 'Gotu kola'),
        (50, 'world_bacopa', 'Bakopa'),
        (60, 'world_shatavari', 'Shatavari'),
        (70, 'world_rhodiola', 'Różeniec górski'),
        (80, 'world_eleuthero', 'Eleuterokok'),
        (90, 'world_astragalus', 'Traganek'),
        (100, 'world_milk_thistle', 'Ostropest plamisty'),
        (110, 'world_artichoke_leaf', 'Liść karczocha'),
        (120, 'world_gentian', 'Goryczka'),
        (130, 'world_angelica', 'Arcydzięgiel'),
        (140, 'world_juniper_berry', 'Jagoda jałowca'),
        (150, 'world_bay_leaf', 'Liść laurowy'),
        (160, 'world_olive_leaf', 'Liść oliwny'),
        (170, 'world_eucalyptus_leaf', 'Liść eukaliptusa'),
        (190, 'world_myrrh', 'Mirra'),
        (200, 'world_frankincense', 'Olibanum'),
    ),
}

WORLD_WOOD_UNLOCKS = {
    "beginner": (
        (1, 'world_norway_spruce', 'Pień świerku pospolitego'),
        (7, 'world_silver_fir', 'Pień jodły pospolitej'),
        (13, 'world_european_larch', 'Pień modrzewia europejskiego'),
        (19, 'world_douglas_fir', 'Pień daglezji'),
        (25, 'world_western_hemlock', 'Pień choiny zachodniej'),
        (31, 'world_mediterranean_cypress', 'Pień cyprysa'),
        (37, 'world_juniper_wood', 'Pień jałowca'),
        (43, 'world_black_locust', 'Pień robinii akacjowej'),
        (49, 'world_acacia_wood', 'Pień akacji'),
        (55, 'world_american_sycamore', 'Pień platana amerykańskiego'),
        (61, 'world_elm_wood', 'Pień wiązu'),
        (67, 'world_hornbeam_wood', 'Pień grabu'),
        (73, 'world_basswood', 'Pień lipy amerykańskiej'),
        (79, 'world_aspen_wood', 'Pień osiki'),
        (85, 'world_cottonwood', 'Pień topoli bawełnianej'),
    ),
    "forest": (
        (20, 'world_cherry_wood', 'Pień wiśni'),
        (26, 'world_apple_wood', 'Pień jabłoni'),
        (32, 'world_pear_wood', 'Pień gruszy'),
        (38, 'world_plum_wood', 'Pień śliwy'),
        (44, 'world_olive_wood', 'Pień oliwki'),
        (50, 'world_eucalyptus_wood', 'Pień eukaliptusa'),
        (56, 'world_rubberwood', 'Pień kauczukowca'),
        (62, 'world_cork_oak', 'Pień dębu korkowego'),
        (68, 'world_white_oak', 'Pień dębu białego'),
        (74, 'world_red_oak', 'Pień dębu czerwonego'),
        (80, 'world_sugar_maple', 'Pień klonu cukrowego'),
        (86, 'world_red_maple', 'Pień klonu czerwonego'),
        (92, 'world_hickory', 'Pień hikory'),
        (98, 'world_pecan_wood', 'Pień pekana'),
        (104, 'world_rosewood', 'Pień palisandru'),
    ),
    "deep": (
        (60, 'world_padauk', 'Pień padouku'),
        (67, 'world_wenge', 'Pień wenge'),
        (74, 'world_iroko', 'Pień iroko'),
        (81, 'world_sapele', 'Pień sapeli'),
        (88, 'world_merbau', 'Pień merbau'),
        (95, 'world_bubinga', 'Pień bubingi'),
        (102, 'world_zebrawood', 'Pień zebrano'),
        (109, 'world_jatoba', 'Pień jatoby'),
        (116, 'world_purpleheart', 'Pień amarantowca'),
        (123, 'world_greenheart', 'Pień greenheart'),
        (130, 'world_lignum_vitae', 'Pień gwajakowca'),
        (137, 'world_sandalwood', 'Pień sandałowca'),
        (144, 'world_agarwood', 'Drewno agarowe'),
        (151, 'world_koa', 'Pień koa'),
        (158, 'world_paulownia', 'Pień paulowni'),
        (165, 'world_balsa', 'Pień balsy'),
        (172, 'world_baobab', 'Pień baobabu'),
        (179, 'world_kauri', 'Pień kauri'),
        (186, 'world_jarrah', 'Pień jarrah'),
        (193, 'world_tasmanian_blackwood', 'Pień akacji czarnej tasmańskiej'),
    ),
}

WORLD_ORE_UNLOCKS = (
    (5, 5, 'world_cassiterite', 'Ruda cyny - kasyteryt'),
    (10, 10, 'world_galena', 'Ruda ołowiu - galena'),
    (15, 15, 'world_sphalerite', 'Ruda cynku - sfaleryt'),
    (20, 20, 'world_pentlandite', 'Ruda niklu - pentlandyt'),
    (25, 25, 'world_chromite', 'Ruda chromu - chromit'),
    (30, 30, 'world_pyrolusite', 'Ruda manganu - piroluzyt'),
    (35, 35, 'world_bauxite', 'Boksyt'),
    (40, 40, 'world_ilmenite', 'Ruda tytanu - ilmenit'),
    (45, 45, 'world_rutile', 'Ruda tytanu - rutyl'),
    (50, 50, 'world_wolframite', 'Ruda wolframu - wolframit'),
    (55, 55, 'world_scheelite', 'Ruda wolframu - scheelit'),
    (60, 60, 'world_molybdenite', 'Ruda molibdenu - molibdenit'),
    (65, 65, 'world_cinnabar', 'Ruda rtęci - cynober'),
    (70, 70, 'world_stibnite', 'Ruda antymonu - antymonit'),
    (75, 75, 'world_arsenopyrite', 'Arsenopiryt'),
    (80, 80, 'world_cobaltite', 'Kobaltyn'),
    (85, 85, 'world_spodumene', 'Ruda litu - spodumen'),
    (90, 90, 'world_lepidolite', 'Ruda litu - lepidolit'),
    (95, 95, 'world_coltan', 'Kolumbit-tantalit'),
    (100, 100, 'world_pyrochlore', 'Ruda niobu - pirochlor'),
    (105, 105, 'world_monazite', 'Monacyt'),
    (110, 110, 'world_bastnasite', 'Bastnazyt'),
    (115, 115, 'world_uraninite', 'Uraninit'),
    (120, 120, 'world_thorite', 'Toryt'),
    (125, 125, 'world_platinum_ore', 'Ruda platyny'),
    (130, 130, 'world_palladium_ore', 'Ruda palladu'),
    (135, 135, 'world_rhodium_ore', 'Ruda rodu'),
    (140, 140, 'world_iridium_ore', 'Ruda irydu'),
    (145, 145, 'world_osmium_ore', 'Ruda osmu'),
    (150, 150, 'world_vanadinite', 'Ruda wanadu - wanadynit'),
    (155, 155, 'world_magnesite', 'Magnezyt'),
    (160, 160, 'world_celestite', 'Celestyn'),
    (165, 165, 'world_barite', 'Baryt'),
    (170, 170, 'world_apatite', 'Apatyt fosforanowy'),
    (175, 175, 'world_native_sulfur', 'Siarka rodzima'),
    (180, 180, 'world_halite', 'Halit'),
    (185, 185, 'world_sylvite', 'Sylwin'),
    (190, 190, 'world_kimberlite', 'Kimberlit diamentonośny'),
    (195, 195, 'world_graphite', 'Grafit'),
    (200, 200, 'world_magnetite_world', 'Magnetyt'),
)


def _world_resource_sell_fields(level):
    level = max(1, min(200, int(level)))
    if level < 100:
        return {"sell_silver": max(5, 5 + level * 2)}
    return {"sell_gold": max(1, (level - 80) // 8)}

def _register_world_resource_items():
    for habitat, rows in WORLD_FISH_UNLOCKS.items():
        for level, item_id, name in rows:
            item = {
                "name": name,
                "type": "resource",
                "price": None,
                "desc": (
                    f"Ryba świata. Łowisko: {habitat}. "
                    f"Wędka level {level}+."
                ),
            }
            item.update(_world_resource_sell_fields(level))
            ITEMS[item_id] = item

    for group, rows in WORLD_HERB_UNLOCKS.items():
        for level, item_id, name in rows:
            item = {
                "name": name,
                "type": "resource",
                "price": None,
                "desc": (
                    f"Roślina świata. Grupa występowania: {group}. "
                    f"Sierp level {level}+."
                ),
            }
            item.update(_world_resource_sell_fields(level))
            ITEMS[item_id] = item

    for group, rows in WORLD_WOOD_UNLOCKS.items():
        for level, item_id, name in rows:
            item = {
                "name": name,
                "type": "resource",
                "price": None,
                "desc": (
                    f"Drewno świata. Grupa występowania: {group}. "
                    f"Piła level {level}+."
                ),
            }
            item.update(_world_resource_sell_fields(level))
            ITEMS[item_id] = item

    for level, floor, item_id, name in WORLD_ORE_UNLOCKS:
        item = {
            "name": name,
            "type": "resource",
            "price": None,
            "desc": (
                f"Ruda lub minerał świata. Kilof level {level}+, "
                f"Kopalnia Głębinowa poziom {floor}+."
            ),
        }
        item.update(_world_resource_sell_fields(level))
        ITEMS[item_id] = item

def unlocked_world_ids(rows, tool_level):
    return tuple(
        item_id
        for required, item_id, _name in rows
        if int(tool_level) >= int(required)
    )

def unlocked_world_ore_ids(tool_level, floor):
    return tuple(
        item_id
        for required_level, required_floor, item_id, _name
        in WORLD_ORE_UNLOCKS
        if int(tool_level) >= int(required_level)
        and int(floor) >= int(required_floor)
    )

FISH_RESOURCE_IDS = {
    # Rzeka
    "small_fish", "river_carp", "river_perch", "dace", "chub", "common_nase",
    "barbel", "ide", "asp", "grayling", "burbot", "pike", "zander",
    "silver_trout", "golden_trout", "salmon", "river_catfish",
    "ancient_sturgeon", "moon_eel",
    # Jezioro
    "lake_roach", "rudd", "crucian_carp", "bream", "tench", "lake_perch",
    "vendace", "whitefish", "lake_char", "lake_trout", "pike", "zander",
    "giant_pike", "freshwater_eel",
    # Morze
    "sprat", "sardine", "anchovy", "herring", "mackerel", "whiting",
    "cod", "hake", "sea_bass", "red_mullet", "haddock", "pollock",
    "flounder", "sole", "halibut", "turbot", "monkfish",
    # Ocean
    "tuna", "albacore", "bigeye_tuna", "mahi_mahi", "wahoo",
    "barracuda", "cobia", "amberjack", "sailfish", "swordfish",
    "bluefin_tuna", "ocean_sunfish", "reef_shark", "mako_shark",
    "tiger_shark", "hammerhead_shark", "great_white_shark", "ghost_marlin",
    # Endgame 100-200
    "soulfin_trout", "runic_sturgeon", "chrono_eel", "eternal_salmon",
    "crystal_carp", "moon_pike", "starfin_char", "mirror_leviathan",
    "storm_cod", "abyss_halibut", "void_turbot", "crown_monkfish",
    "celestial_tuna", "dragon_mahi", "abyss_tuna", "storm_marlin",
    "moon_leviathan", "eternal_coelacanth",
    # v0.6.98
    "river_bleak", "stone_loach", "river_bream", "brown_trout",
    "river_taimen", "emerald_barbel", "spirit_grayling",
    "bloodfin_salmon", "star_river_eel", "eternal_river_dragon",
    "lake_gudgeon", "lake_smelt", "blue_bream", "golden_tench",
    "deepwater_pike", "crystal_whitefish", "moon_carp",
    "astral_pike", "mirror_sturgeon", "eternal_lake_serpent",
    "sand_eel", "garfish", "sea_bream", "bluefish", "conger_eel",
    "red_snapper", "storm_herring", "abyss_conger", "void_sole",
    "eternal_sea_drake",
    "flying_fish", "bonito", "yellowfin_tuna", "king_mackerel",
    "marlin_black", "opah", "celestial_swordfish", "astral_sunfish",
    "void_marlin", "world_leviathan",
}

# v0.34.4: Górnictwo ma zawsze dawać normalny urobek, a aktualnie odblokowane
# rudy/minerały nie mogą ginąć w ogromnej kumulatywnej puli. Starsze zasoby
# nadal pozostają możliwe, lecz świeże progi mają wyższą wagę.
def mining_ore_weights(resource_ids, effective_level, context="mining"):
    effective_level = max(1, min(400, int(effective_level)))
    result = []
    for item_id in resource_ids:
        unlock = max(1, min(400, int(ORE_ATLAS_LEVELS.get(item_id, 1) or 1)))
        age = max(0, effective_level - unlock)
        # Około 10-20% dla świeżego zasobu przy zwykłych progach 1-200;
        # stare rudy nigdy nie spadają do zera.
        freshness = 0.20 + 8.0 / ((1.0 + age / 20.0) ** 1.50)
        affinity = 0.92 + 0.16 * generator_core_v027.stable_unit(
            f"{context}:{item_id}:mining-affinity"
        )
        result.append(max(0.05, freshness * affinity))
    return result


def mining_mithril_currency_chance(tool_level, profession_level, floor):
    """Szansa na bezpośrednie znalezienie 1 mithrilu jako WALUTY.

    Mithril nie jest rudą i nie zastępuje normalnego urobku. Odblokowuje się
    od Kilofa/Górnictwa 80 i poziomu kopalni 80. Szansa rośnie od 0.5% do 2%.
    """
    tool_level = max(1, min(400, int(tool_level)))
    profession_level = max(1, min(400, int(profession_level)))
    floor = max(1, min(400, int(floor or 1)))
    effective = min(tool_level, profession_level, floor)
    if effective < 80:
        return 0.0
    progress = (effective - 80) / 320.0
    return round(0.005 + 0.015 * progress, 6)

ORE_RESOURCE_IDS = {
    "stone_chunk", "copper_ore", "iron_ore",
    "silver_ore", "gold_ore",
    "cobalt_ore", "runestone_ore", "dragonsteel_ore",
    "astral_ore", "void_ore", "eternium_ore",
}
WOOD_RESOURCE_IDS = {
    "fallen_branch", "birch_log", "alder_log", "pine_log", "poplar_log",
    "willow_log", "linden_log", "oak_log", "beech_log", "maple_log",
    "ash_log", "chestnut_log", "walnut_log", "cedar_log", "yew_log",
    "mahogany_log", "teak_log", "redwood_log", "ironwood_log", "ebony_log",
    "silverwood_log", "spiritwood_log", "ancient_heartwood", "worldtree_wood",
    "runewood_log", "dragonwood_log", "astralwood_log",
    "voidwood_log", "starheart_log", "eternal_worldwood_log",
}

HERB_RESOURCE_IDS = {
    "nettle", "chamomile", "mint", "sage", "lavender", "yarrow",
    "lemon_balm", "valerian", "ginseng", "nightshade", "mandrake",
    "moonflower", "soulroot", "phoenix_leaf", "star_moss", "astral_lotus",
    "sunfire_bloom", "dragon_sage", "astral_orchid",
    "void_lotus", "phoenix_crown", "eternal_blossom",
}
HERB_MEADOW_ATLAS = {"nettle", "chamomile", "mint", "yarrow", "lemon_balm", "lavender"}
HERB_FOREST_ATLAS = {"sage", "valerian", "ginseng", "nightshade", "mandrake", "moonflower", "soulroot"}
HERB_WATER_ATLAS = {"mint", "lemon_balm", "star_moss", "moonflower"}
HERB_DEEP_ATLAS = {
    "mandrake", "moonflower", "soulroot", "phoenix_leaf",
    "star_moss", "astral_lotus",
    "sunfire_bloom", "dragon_sage", "astral_orchid",
    "void_lotus", "phoenix_crown", "eternal_blossom",
}

RIVER_FISH_ATLAS = {
    "small_fish", "dace", "river_perch", "chub", "common_nase",
    "river_carp", "barbel", "ide", "asp", "grayling", "burbot",
    "silver_trout", "golden_trout", "pike", "zander", "salmon",
    "river_catfish", "ancient_sturgeon", "moon_eel",
    "soulfin_trout", "runic_sturgeon", "chrono_eel", "eternal_salmon",
    "river_bleak", "stone_loach", "river_bream", "brown_trout",
    "river_taimen", "emerald_barbel", "spirit_grayling",
    "bloodfin_salmon", "star_river_eel", "eternal_river_dragon",
}
LAKE_FISH_ATLAS = {
    "lake_roach", "rudd", "crucian_carp", "bream", "tench",
    "lake_perch", "vendace", "whitefish", "lake_char", "lake_trout",
    "pike", "zander", "giant_pike", "freshwater_eel",
    "crystal_carp", "moon_pike", "starfin_char", "mirror_leviathan",
    "lake_gudgeon", "lake_smelt", "blue_bream", "golden_tench",
    "deepwater_pike", "crystal_whitefish", "moon_carp",
    "astral_pike", "mirror_sturgeon", "eternal_lake_serpent",
}
SEA_FISH_ATLAS = {
    "sprat", "sardine", "anchovy", "herring", "mackerel", "whiting",
    "cod", "hake", "sea_bass", "red_mullet", "haddock", "pollock",
    "flounder", "sole", "halibut", "turbot", "monkfish",
    "storm_cod", "abyss_halibut", "void_turbot", "crown_monkfish",
    "sand_eel", "garfish", "sea_bream", "bluefish", "conger_eel",
    "red_snapper", "storm_herring", "abyss_conger",
    "void_sole", "eternal_sea_drake",
}
OCEAN_FISH_ATLAS = {
    "mackerel", "mahi_mahi", "albacore", "wahoo", "barracuda", "tuna",
    "sailfish", "bigeye_tuna", "cobia", "amberjack", "swordfish",
    "bluefin_tuna", "ocean_sunfish", "reef_shark", "mako_shark",
    "tiger_shark", "hammerhead_shark", "great_white_shark", "ghost_marlin",
    "celestial_tuna", "dragon_mahi", "abyss_tuna",
    "storm_marlin", "moon_leviathan", "eternal_coelacanth",
    "flying_fish", "bonito", "yellowfin_tuna", "king_mackerel",
    "marlin_black", "opah", "celestial_swordfish",
    "astral_sunfish", "void_marlin", "world_leviathan",
}

WOOD_BEGINNER_ATLAS = {
    "fallen_branch", "birch_log", "alder_log", "pine_log", "poplar_log",
    "willow_log", "linden_log", "oak_log", "beech_log", "maple_log",
}
WOOD_FOREST_ATLAS = {
    "linden_log", "oak_log", "beech_log", "maple_log", "ash_log",
    "chestnut_log", "walnut_log", "cedar_log", "yew_log",
    "mahogany_log", "teak_log", "redwood_log", "ironwood_log",
}
WOOD_DEEP_ATLAS = {
    "ash_log", "chestnut_log", "walnut_log", "cedar_log", "yew_log",
    "mahogany_log", "teak_log", "redwood_log", "ironwood_log",
    "ebony_log", "silverwood_log", "spiritwood_log",
    "ancient_heartwood", "worldtree_wood",
    "runewood_log", "dragonwood_log", "astralwood_log",
    "voidwood_log", "starheart_log", "eternal_worldwood_log",
}

# v0.9.12: zasoby 220-400 są pełnoprawnymi zasobami atlasów/kolekcji.
_POST400_ORE_IDS = {item_id for _level, item_id in ENDGAME_ORE_UNLOCKS if _level > 200}
_POST400_WOOD_IDS = {item_id for _level, item_id in ENDGAME_WOOD_UNLOCKS if _level > 200}
_POST400_HERB_IDS = {item_id for _level, item_id in ENDGAME_HERB_UNLOCKS if _level > 200}
_POST400_FISH_BY_HABITAT = {
    habitat: {item_id for _level, item_id in rows if _level > 200}
    for habitat, rows in ENDGAME_FISH_UNLOCKS.items()
}
ORE_RESOURCE_IDS.update(_POST400_ORE_IDS)
WOOD_RESOURCE_IDS.update(_POST400_WOOD_IDS)
HERB_RESOURCE_IDS.update(_POST400_HERB_IDS)
FISH_RESOURCE_IDS.update(*(ids for ids in _POST400_FISH_BY_HABITAT.values()))
RIVER_FISH_ATLAS.update(_POST400_FISH_BY_HABITAT.get("river", set()))
LAKE_FISH_ATLAS.update(_POST400_FISH_BY_HABITAT.get("lake", set()))
SEA_FISH_ATLAS.update(_POST400_FISH_BY_HABITAT.get("sea", set()))
OCEAN_FISH_ATLAS.update(_POST400_FISH_BY_HABITAT.get("ocean", set()))
WOOD_DEEP_ATLAS.update(_POST400_WOOD_IDS)
HERB_DEEP_ATLAS.update(_POST400_HERB_IDS)

WORLD_FISH_IDS = {
    item_id
    for rows in WORLD_FISH_UNLOCKS.values()
    for _level, item_id, _name in rows
}
WORLD_HERB_IDS = {
    item_id
    for rows in WORLD_HERB_UNLOCKS.values()
    for _level, item_id, _name in rows
}
WORLD_WOOD_IDS = {
    item_id
    for rows in WORLD_WOOD_UNLOCKS.values()
    for _level, item_id, _name in rows
}
WORLD_ORE_IDS = {
    item_id
    for _level, _floor, item_id, _name in WORLD_ORE_UNLOCKS
}

FISH_RESOURCE_IDS.update(WORLD_FISH_IDS)
HERB_RESOURCE_IDS.update(WORLD_HERB_IDS)
WOOD_RESOURCE_IDS.update(WORLD_WOOD_IDS)
ORE_RESOURCE_IDS.update(WORLD_ORE_IDS)

RIVER_FISH_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_FISH_UNLOCKS["river"]
)
LAKE_FISH_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_FISH_UNLOCKS["lake"]
)
SEA_FISH_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_FISH_UNLOCKS["sea"]
)
OCEAN_FISH_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_FISH_UNLOCKS["ocean"]
)

HERB_MEADOW_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_HERB_UNLOCKS["meadow"]
)
HERB_WATER_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_HERB_UNLOCKS["water"]
)
HERB_FOREST_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_HERB_UNLOCKS["forest"]
)
HERB_DEEP_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_HERB_UNLOCKS["deep"]
)

WOOD_BEGINNER_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_WOOD_UNLOCKS["beginner"]
)
WOOD_FOREST_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_WOOD_UNLOCKS["forest"]
)
WOOD_DEEP_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_WOOD_UNLOCKS["deep"]
)

# Pełne atlasy zasobów.
# Te zbiory są bezpośrednio oparte na aktywnych RESOURCE_IDS,
# dzięki czemu każda istniejąca ryba, ruda, sztuka drewna i zioło
# zawsze trafia do pełnego widoku atlasu.
FISH_ATLAS_ALL = set(FISH_RESOURCE_IDS)
ORE_ATLAS_ALL = set(ORE_RESOURCE_IDS)
WOOD_ATLAS_ALL = set(WOOD_RESOURCE_IDS)
HERB_ATLAS_ALL = set(HERB_RESOURCE_IDS)
