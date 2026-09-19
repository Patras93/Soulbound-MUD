# -*- coding: utf-8 -*-
"""Soulbound v0.30.54 - Crafting Quality, Critical Craft and category Mastery."""
import copy
import math
import random

CRAFT_QUALITY_V03054 = {
    "normal": {"name":"Zwykły", "mult":1.00, "rarity":"crafted"},
    "good": {"name":"Dobry", "mult":1.06, "rarity":"uncommon"},
    "excellent": {"name":"Doskonały", "mult":1.13, "rarity":"rare"},
    "masterwork": {"name":"Mistrzowski", "mult":1.22, "rarity":"epic"},
    "legendary": {"name":"Legendarny", "mult":1.35, "rarity":"legendary"},
}
CRAFT_QUALITY_ORDER_V03054=("normal","good","excellent","masterwork","legendary")
CRAFT_CRIT_AFFIXES_V03054=("strength","dexterity","constitution","intelligence","willpower","hp","mana")
CRAFT_CRIT_AFFIX_NAMES_V03054={
    "strength":"Siła","dexterity":"Zręczność","constitution":"Kondycja",
    "intelligence":"Inteligencja","willpower":"Siła Woli","hp":"HP","mana":"Mana",
}

def crafting_mastery_level_v03054(actions):
    # Niezależny progres 1-100. 2500 udanych craftów ~= poziom 100.
    return max(1,min(100,1+int(math.sqrt(max(0,int(actions))*4.0))))

def crafting_mastery_category_v03054(recipe, profession):
    raw=str(recipe.get("category") or recipe.get("tool_type") or profession or "ogolne")
    return normalize_lookup_text(raw).replace(" ","_") or "ogolne"

def crafting_quality_roll_v03054(profession_level, tool_level, mastery_level):
    skill=max(0.0,min(1.0,(max(1,int(profession_level))/400.0)*0.45 + (max(1,int(tool_level))/400.0)*0.20 + (max(1,int(mastery_level))/100.0)*0.35))
    weights=[60-35*skill,25+8*skill,10+12*skill,4+9*skill,1+6*skill]
    return random.choices(CRAFT_QUALITY_ORDER_V03054,weights=weights,k=1)[0]

def crafting_critical_chance_v03054(profession_level, mastery_level):
    # 2% start, do około 12% na pełnym progresie.
    return min(0.12,0.02 + max(1,int(profession_level))/400.0*0.035 + max(1,int(mastery_level))/100.0*0.065)

def crafting_critical_affix_amount_v03054(stat, quality_key, mastery_level):
    idx=CRAFT_QUALITY_ORDER_V03054.index(quality_key)
    if stat in ("hp","mana"):
        return 20 + idx*15 + max(0,int(mastery_level)//10)*3
    return 1 + idx + max(0,int(mastery_level)//35)

def crafting_quality_variant_id_v03054(base_id, quality_key, crit_affix=None):
    suffix=crit_affix or "none"
    return f"craftq_{quality_key}_{suffix}_{base_id}"

def _scale_int_v03054(value,mult,minimum_if_positive=True):
    v=int(value or 0)
    if v<=0: return v
    out=int(round(v*float(mult)))
    return max(v if minimum_if_positive else 0,out)

def register_crafting_quality_variant_v03054(base_id, quality_key, crit_affix=None, mastery_level=1):
    vid=crafting_quality_variant_id_v03054(base_id,quality_key,crit_affix)
    if vid in ITEMS: return vid
    base=ITEMS.get(base_id)
    if not base: return base_id
    data=copy.deepcopy(base)
    q=CRAFT_QUALITY_V03054[quality_key]
    mult=float(q["mult"])
    base_name=str(base.get("name",base_id))
    data["name"]=f"{q['name']} {base_name}" + (f" Krytyczny" if crit_affix else "")
    data["crafted_base_id_v03054"]=base_id
    data["craft_quality_v03054"]=quality_key
    data["craft_quality_name_v03054"]=q["name"]
    data["craft_critical_v03054"]=bool(crit_affix)
    data["rarity"]=q["rarity"]
    data["rarity_name"]=q["name"]
    for key in ("defense","damage","min_damage","max_damage","attack","power"):
        if key in data: data[key]=_scale_int_v03054(data.get(key),mult)
    if "affix_amount" in data:
        data["affix_amount"]=_scale_int_v03054(data.get("affix_amount"),mult)
    stats=dict(data.get("stats") or {})
    for key,val in list(stats.items()):
        if isinstance(val,(int,float)):
            stats[key]=_scale_int_v03054(val,mult)
    props=dict(data.get("properties") or {})
    for key,val in list(props.items()):
        if isinstance(val,(int,float)):
            props[key]=_scale_int_v03054(val,mult)
    if crit_affix:
        amount=crafting_critical_affix_amount_v03054(crit_affix,quality_key,mastery_level)
        stats[crit_affix]=int(stats.get(crit_affix,0) or 0)+amount
        data["craft_critical_affix_v03054"]=crit_affix
        data["craft_critical_affix_amount_v03054"]=amount
    if stats: data["stats"]=stats
    if props: data["properties"]=props
    old_desc=str(data.get("desc","")).strip()
    extra=f"Jakość craftu: {q['name']} ({int(round((mult-1)*100)):+d}% bazowej mocy)."
    if crit_affix:
        extra += f" Krytyczny craft: {CRAFT_CRIT_AFFIX_NAMES_V03054.get(crit_affix,crit_affix)} +{data['craft_critical_affix_amount_v03054']}."
    data["desc"]=(old_desc+" "+extra).strip()
    data["price"]=base.get("price")
    ITEMS[vid]=data
    return vid

def crafting_output_is_quality_equipment_v03054(output_id):
    item=ITEMS.get(output_id,{})
    return item.get("type") in ("armor","weapon","equipment") or bool(item.get("slot"))

def crafting_quality_output_v03054(output_id, quality_key, critical, mastery_level):
    if not crafting_output_is_quality_equipment_v03054(output_id):
        return output_id,None
    crit_affix=random.choice(CRAFT_CRIT_AFFIXES_V03054) if critical else None
    return register_crafting_quality_variant_v03054(output_id,quality_key,crit_affix,mastery_level),crit_affix
