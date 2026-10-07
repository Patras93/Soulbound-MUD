# -*- coding: utf-8 -*-
from data.mobs import MOB_TEMPLATES
import world.global_difficulty_overdrive as _difficulty

def _repair_exact_source_flags_v11346():
    repaired=[]
    for template_id,template in MOB_TEMPLATES.items():
        if not isinstance(template,dict):
            continue
        source_xp=max(0,int(template.get("source_xp",0) or 0))
        if bool(template.get("source_xp_exact")) and source_xp<=0:
            template["source_xp_exact"]=False
            template["combat_xp_zero_repair_v11346"]=True
            repaired.append(str(template_id))
    return tuple(sorted(repaired))

COMBAT_XP_ZERO_REPAIRED_TEMPLATES_V11346=_repair_exact_source_flags_v11346()

if not getattr(_difficulty.v0190_combat_reward,"_combat_xp_zero_repair_v11346",False):
    _combat_reward_before_v11346=_difficulty.v0190_combat_reward
    def _combat_reward_repaired_v11346(template,kind):
        value=max(0,int(_combat_reward_before_v11346(template,kind)))
        if str(kind) in {"character","class","soul","stat"}:
            return max(3,value)
        return value
    _combat_reward_repaired_v11346._combat_xp_zero_repair_v11346=True
    _difficulty.v0190_combat_reward=_combat_reward_repaired_v11346

def combat_xp_zero_audit_v11346():
    errors=[]
    for template_id,template in MOB_TEMPLATES.items():
        if not isinstance(template,dict):
            continue
        source_xp=max(0,int(template.get("source_xp",0) or 0))
        if bool(template.get("source_xp_exact")) and source_xp<=0:
            errors.append(f"{template_id}: invalid exact source XP")
    if not getattr(_difficulty.v0190_combat_reward,"_combat_xp_zero_repair_v11346",False):
        errors.append("combat reward wrapper inactive")
    return {"version":"1.13.46","repaired":COMBAT_XP_ZERO_REPAIRED_TEMPLATES_V11346,"error_count":len(errors),"errors":errors}

COMBAT_XP_ZERO_AUDIT_V11346=combat_xp_zero_audit_v11346()
