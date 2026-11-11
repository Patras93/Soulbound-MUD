# -*- coding: utf-8 -*-
"""Soulbound v0.58.1 - late NPC hourly reconciliation regression audit."""
from data.catalogs import NPCS, QUESTS
from world.living_npcs_finalize import LIVING_NPCS_FINALIZE_STATE


def _v0581_has_quest(npc):
    ids=[]
    for key in ("quest","quest_chain","specialist_quests","quests"):
        value=npc.get(key)
        if isinstance(value,str): ids.append(value)
        elif value: ids.extend(value)
    if any(qid in QUESTS for qid in ids):
        return True
    giver=str(npc.get("name") or "").strip().casefold()
    return bool(giver) and any(str(q.get("giver") or "").strip().casefold()==giver for q in QUESTS.values())


def living_npcs_late_finalize_audit_v0581():
    errors=[]
    shop_ids=sorted(nid for nid,npc in NPCS.items() if str(nid).startswith("class_eq_shop_") or npc.get("class_eq_shop"))
    uncovered=sorted(nid for nid,npc in NPCS.items() if not _v0581_has_quest(npc))
    uncovered_shops=[nid for nid in shop_ids if not _v0581_has_quest(NPCS[nid])]
    state=dict(LIVING_NPCS_FINALIZE_STATE.get("state", {}) or {})
    if uncovered:
        errors.append("NPCs without quests after late finalize: "+", ".join(uncovered[:30]))
    if uncovered_shops:
        errors.append("Class EQ shop NPCs without quests: "+", ".join(uncovered_shops))
    if int(state.get("npc_without_quest_count", -1)) != 0:
        errors.append(f"late finalizer state reports npc_without_quest_count={state.get('npc_without_quest_count')}")
    return {
        "version":"0.58.1",
        "class_eq_shop_npc_count":len(shop_ids),
        "late_generated_count":len(tuple(LIVING_NPCS_FINALIZE_STATE.get("new_npc_ids", ()) or ())),
        "npc_without_quest_count":len(uncovered),
        "error_count":len(errors),
        "errors":errors,
    }

LIVING_NPCS_LATE_FINALIZE_AUDIT_V0581=living_npcs_late_finalize_audit_v0581()
if LIVING_NPCS_LATE_FINALIZE_AUDIT_V0581["error_count"]:
    raise RuntimeError("Living NPCs Late Finalize Audit v0.58.1 failed: "+"; ".join(LIVING_NPCS_LATE_FINALIZE_AUDIT_V0581["errors"][:100]))

__all__=["living_npcs_late_finalize_audit_v0581","LIVING_NPCS_LATE_FINALIZE_AUDIT_V0581"]
