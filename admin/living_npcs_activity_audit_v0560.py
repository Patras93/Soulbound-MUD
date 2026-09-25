# -*- coding: utf-8 -*-
"""Soulbound v0.56.0 - living NPCs and activity journal audit."""
from collections import Counter
from pathlib import Path
from core.progression_resources import v0270_quest_character_reward
from data.catalogs import ITEMS, MOB_TEMPLATES, NPCS, QUESTS
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
    hourly_ids=tuple(V0560_TAVERN_QUEST_IDS)+tuple(V0560_GENERATED_HOURLY_IDS)
    for qid in hourly_ids:
        q=QUESTS.get(qid)
        if not q: errors.append(f'missing hourly quest: {qid}'); continue
        if not q.get('repeatable') or int(q.get('repeat_cooldown',0)) != V0560_HOURLY_COOLDOWN:
            errors.append(f'{qid}: not hourly repeatable')
        if v0270_quest_character_reward(q) <= 1:
            errors.append(f'{qid}: character XP still falls back to 1')

    # v0.71.2: generated hourlies must be varied and their travel targets must
    # not collapse onto one alphabetically-first NPC.
    generated=[QUESTS[qid] for qid in V0560_GENERATED_HOURLY_IDS if qid in QUESTS]
    kind_counts=Counter(str(q.get('kind') or '') for q in generated)
    if generated and len(kind_counts) < 4:
        errors.append(f'generated hourlies use only {len(kind_counts)} objective kinds: {dict(kind_counts)}')
    talk_count=int(kind_counts.get('talk_npc',0))
    if generated and talk_count > max(1, int(len(generated)*0.40)):
        errors.append(f'talk_npc dominates generated hourlies: {talk_count}/{len(generated)}')
    target_counts=Counter(str(q.get('target_npc') or '') for q in generated if q.get('target_npc'))
    top_target_count=max(target_counts.values(), default=0)
    if top_target_count > 4:
        errors.append(f'one NPC is targeted by {top_target_count} generated travel errands; expected <=4')
    for qid in V0560_GENERATED_HOURLY_IDS:
        q=QUESTS.get(qid,{})
        kind=str(q.get('kind') or '')
        if kind in ('talk_npc','deliver_npc') and str(q.get('target_npc') or '') not in NPCS:
            errors.append(f'{qid}: missing target NPC')
        if kind == 'deliver_npc':
            item_id=str(q.get('quest_item') or '')
            if item_id not in ITEMS or int((q.get('accept_items') or {}).get(item_id,0) or 0) < 1:
                errors.append(f'{qid}: invalid generated delivery item')
        if kind == 'kill' and str(q.get('target') or '') not in MOB_TEMPLATES:
            errors.append(f'{qid}: missing kill target')
        if kind == 'collect_category' and str(q.get('target') or '') not in {'fish','ore','wood','herb'}:
            errors.append(f'{qid}: invalid collection category {q.get("target")!r}')

    # Guard the whole repeatable catalog against the old generator-level 1-XP fallback.
    low_repeatable=[qid for qid,q in QUESTS.items() if q.get('repeatable') and v0270_quest_character_reward(q) <= 1]
    if low_repeatable:
        errors.append('repeatable quests with <=1 Character XP: '+', '.join(low_repeatable[:30]))
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
        'generated_kind_counts':dict(kind_counts),
        'generated_top_target_count':top_target_count,
        'repeatable_low_character_xp_count':len(low_repeatable),
        'npc_count':len(NPCS),'npc_without_quest_count':len(uncovered),
        'error_count':len(errors),'errors':errors,
    }

LIVING_NPCS_ACTIVITY_AUDIT_V0560=living_npcs_activity_audit_v0560()
if LIVING_NPCS_ACTIVITY_AUDIT_V0560['error_count']:
    raise RuntimeError('Living NPCs & Activity Journal Audit v0.56.0 failed: '+ '; '.join(LIVING_NPCS_ACTIVITY_AUDIT_V0560['errors'][:100]))

__all__=['living_npcs_activity_audit_v0560','LIVING_NPCS_ACTIVITY_AUDIT_V0560']
