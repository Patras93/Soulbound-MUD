# -*- coding: utf-8 -*-
"""OLC 14 — data-only prerequisites of several quests.

No level gates, no new EXP formulas and no change to stored quest progress.
Existing requires_quest is preserved and combined with requires_quests.
"""


def quest_requirements(quest):
    first = quest.get('requires_quest')
    rest = quest.get('requires_quests', [])
    if not isinstance(rest, list):
        raise ValueError('requires_quests musi być listą JSON.')
    return tuple(dict.fromkeys(([first] if first else []) + rest))


def validate_dependencies(quest_id, quest, all_ids):
    rest = quest.get('requires_quests', [])
    if (not isinstance(rest, list) or len(rest) > 8 or
            any(not isinstance(x, str) or not x for x in rest) or
            len(rest) != len(set(rest))):
        raise ValueError('requires_quests: 0–8 unikalnych ID questów.')
    for target in quest_requirements(quest):
        if target not in all_ids or target == quest_id:
            raise ValueError(f'{quest_id}: nieznany lub własny quest wymagany: {target}.')


def validate_dependency_graph(quests):
    """Cycle check O(V + E), supporting multiple prerequisites and old quests."""
    keys = set(quests)
    states = {}  # 1 visiting, 2 done
    for start in quests:
        if states.get(start) == 2:
            continue
        stack = [(start, False)]
        while stack:
            node, done = stack.pop()
            if done:
                states[node] = 2
                continue
            state = states.get(node, 0)
            if state == 2:
                continue
            if state == 1:
                raise ValueError(f'Łańcuch questów: cykl zależności przy {node}.')
            states[node] = 1
            stack.append((node, True))
            quest = quests[node]
            # Historical single-parent links may reference old retired quests.
            # Preserve legacy behaviour for those links, but always validate
            # NEW multi-parent references and cycles. Edited/new single-parent
            # links are validated by the OLC write path.
            extra = quest.get('requires_quests', [])
            if (not isinstance(extra, list) or len(extra) > 8 or
                    any(not isinstance(x, str) or not x for x in extra) or
                    len(extra) != len(set(extra))):
                raise ValueError(f'{node}: błędna lista wymaganych questów.')
            for next_id in reversed(quest_requirements(quest)):
                if next_id not in keys:
                    if next_id in extra:
                        raise ValueError(f'{node}: nieznany wymagany quest {next_id}.')
                    continue
                if next_id == node or states.get(next_id) == 1:
                    raise ValueError(f'Łańcuch questów: cykl zależności przy {next_id}.')
                if states.get(next_id) != 2:
                    stack.append((next_id, False))
    return len(states)


def describe_quest_dependencies(service, quest_id, definitions):
    """Read-only concise prerequisite diff for NVDA, not a mutation command."""
    if quest_id not in definitions and quest_id not in service.draft.get('quests', {}):
        raise ValueError('Nieznane ID questa. Użyj admin live katalog quest FRAZA.')
    def entry(payload):
        base = dict(definitions.get(quest_id, {}))
        # The live registry may currently include the active OLC override.
        # Do not mistake it for the authored default when previewing auto.
        if ('requires_quests' in service.active.get('quest_edits', {}).get(quest_id, {})
                and 'requires_quests' not in payload.get('quest_edits', {}).get(quest_id, {})):
            base.pop('requires_quests', None)
        base.update(payload.get('quests', {}).get(quest_id, {}))
        base.update(payload.get('quest_edits', {}).get(quest_id, {}))
        labels=[]
        for key in quest_requirements(base):
            named = (definitions.get(key) or payload.get('quests', {}).get(key) or {}).get('name',key)
            labels.append(f'{key} ({str(named)[:55]})')
        return ', '.join(labels) if labels else 'brak warunków fabularnych'
    current=entry(service.active)
    planned=entry(service.draft)
    suffix='; BEZ ZMIAN' if current==planned else '; oczekuje na zatwierdzenie'
    return (f'OLC ZALEŻNOŚCI {quest_id}. Obecnie: {current}. '
            f'Po zmianie: {planned}{suffix}. Niczego nie zapisano.')


def validate_multi_dialogue(value, known_quests):
    """Only completed quest IDs may unlock a text response. No scripts."""
    if not isinstance(value, dict) or set(value) != {'quests','text'}:
        raise ValueError('Dialog NPC: wymagany JSON {"quests":["id1","id2"],"text":"Tekst"}.')
    qids=value['quests']; message=value['text']
    if (not isinstance(qids, list) or not 1 <= len(qids) <= 8 or
            any(not isinstance(qid,str) or qid not in known_quests for qid in qids) or
            len(qids) != len(set(qids))):
        raise ValueError('Dialog NPC: lista od 1 do 8 różnych, istniejących questów.')
    if (not isinstance(message,str) or not message.strip() or len(message)>700 or
            any(ord(c)<32 for c in message)):
        raise ValueError('Dialog NPC: wymagany tekst do 700 znaków.')
    return True


def multi_dialogue_text(npc, completed):
    """Return multi-condition NPC line, or None to keep old NPC behavior."""
    rule=npc.get('olc_dialogue_after_quests')
    if (isinstance(rule,dict) and isinstance(rule.get('quests'),list) and
            rule['quests'] and all(completed(qid) for qid in rule['quests'])):
        return rule.get('text')
    return None
