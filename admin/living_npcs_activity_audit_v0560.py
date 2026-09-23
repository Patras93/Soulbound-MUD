# -*- coding: utf-8 -*-
"""Soulbound v0.56.0 - living NPCs and activity journal audit."""
from pathlib import Path
from data.catalogs import NPCS, QUESTS
from world.living_npcs import (
    V0560_HOURLY_COOLDOWN, V0560_TAVERN_NPC_IDS, V0560_TAVERN_QUEST_IDS,
    V0560_GENERATED_HOURLY_IDS, V0560_LIVING_NPCS_STATE,
)
from player.session_mixins.command_registry import COMMAND_REGISTRY

ROOT = Path(__file__).resolve().parents[1]

def _has_quest(npc):
    ids=[]
    for key in ('quest','quest_chain','specialist_quests','quests'):
        v=npc.get(key)
        if isinstance(v,str): ids.append(v)
        elif v: ids.extend(v)
    if any(qid in QUESTS for qid in ids): return True
    giver=str(npc.get('name') or '').strip().casefold()
    return bool(giver) and any(str(q.get('giver') or '').strip().casefold()==giver for q in QUESTS.values())

def living_npcs_activity_audit_v0560():
    errors=[]
    if len(V0560_TAVERN_NPC_IDS)!=8: errors.append(f'expected 8 new innkeepers, got {len(V0560_TAVERN_NPC_IDS)}')
    if len(V0560_TAVERN_QUEST_IDS)!=24: errors.append(f'expected 24 tavern hourlies, got {len(V0560_TAVERN_QUEST_IDS)}')
    for qid in tuple(V0560_TAVERN_QUEST_IDS)+tuple(V0560_GENERATED_HOURLY_IDS):
        q=QUESTS.get(qid)
        if not q: errors.append(f'missing hourly quest: {qid}'); continue
        if not q.get('repeatable') or int(q.get('repeat_cooldown',0)) != V0560_HOURLY_COOLDOWN:
            errors.append(f'{qid}: not hourly repeatable')
    uncovered=[nid for nid,npc in NPCS.items() if not _has_quest(npc)]
    if uncovered: errors.append('NPCs without quests: '+', '.join(uncovered[:30]))
    for cmd in ('activityjournal','whattodo'):
        if cmd not in COMMAND_REGISTRY: errors.append(f'missing command: {cmd}')
    schema=(ROOT/'storage/schema_migrate_social.py').read_text(encoding='utf-8')
    world=(ROOT/'storage/db_world.py').read_text(encoding='utf-8')
    for token in ('activity_journal_v0560','idx_activity_journal_v0560_account_time'):
        if token not in schema: errors.append(f'missing journal schema: {token}')
    for token in ('record_activity_v0560','activity_rows_v0560'):
        if token not in world: errors.append(f'missing journal persistence: {token}')
    for path, tokens in {
        'player/session_mixins/quest_commands.py':('record_activity_v0560','"quest"'),
        'player/session_mixins/combat_rewards.py':('record_activity_v0560','"boss"'),
        'player/session_mixins/courier_delivery.py':('record_activity_v0560','"dostawa"'),
        'storage/db_inventory.py':('record_activity_v0560','"drop"'),
        'storage/db_world.py':('"osiagniecie"','"awans"'),
    }.items():
        txt=(ROOT/path).read_text(encoding='utf-8')
        for token in tokens:
            if token not in txt: errors.append(f'{path}: missing {token}')
    return {
        'version':'0.56.0','tavern_count':len(V0560_TAVERN_NPC_IDS),
        'tavern_hourly_count':len(V0560_TAVERN_QUEST_IDS),
        'generated_hourly_count':len(V0560_GENERATED_HOURLY_IDS),
        'npc_count':len(NPCS),'npc_without_quest_count':len(uncovered),
        'error_count':len(errors),'errors':errors,
    }

LIVING_NPCS_ACTIVITY_AUDIT_V0560=living_npcs_activity_audit_v0560()
if LIVING_NPCS_ACTIVITY_AUDIT_V0560['error_count']:
    raise RuntimeError('Living NPCs & Activity Journal Audit v0.56.0 failed: '+ '; '.join(LIVING_NPCS_ACTIVITY_AUDIT_V0560['errors'][:100]))

__all__=['living_npcs_activity_audit_v0560','LIVING_NPCS_ACTIVITY_AUDIT_V0560']
