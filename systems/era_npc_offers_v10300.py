# -*- coding: utf-8 -*-
"""Krótkie, niezależne oferty NPC Ery Bez Granic (NVDA).

Fabuła, rajdy i zadania aktywnej klasy nie blokują się nawzajem.
Nie zmienia list, statusów ani postępu starszych NPC.
"""
from __future__ import annotations


def visible_era_quests(quest_ids, quests, get_row, active_classes):
    """Zwróć aktualne etapy niezależnych serii i oddzielne profesje.

    `get_row` jest jedynym odczytem z SQLite; zapisów nie wykonujemy.
    """
    classes = set(active_classes)
    groups = {'story': [], 'class': [], 'raid': []}
    professions = []
    for qid in dict.fromkeys(quest_ids):
        quest = quests.get(qid)
        if quest is None:
            continue
        required = quest.get('required_class')
        if required and required not in classes:
            continue
        if '_story_' in qid:
            groups['story'].append(qid)
        elif '_class_' in qid:
            groups['class'].append(qid)
        elif '_raid_quest_' in qid:
            groups['raid'].append(qid)
        else:
            professions.append(qid)

    def completed(qid):
        row = get_row(qid)
        return bool(row and (row['status'] == 'completed'
                   or int(row['completion_count'] or 0) > 0))

    result = []
    # Offer at most one quest per linear series; active has priority.
    for category in ('story', 'class', 'raid'):
        for qid in groups[category]:
            row = get_row(qid)
            if row and row['status'] == 'active':
                result.append(qid)
                break
            if completed(qid) and not quests[qid].get('repeatable'):
                continue
            prerequisite = quests[qid].get('requires_quest')
            if prerequisite and not completed(prerequisite):
                break
            result.append(qid)
            break
    # 14 independent professions remain directly selectable; do not force
    # an unrelated profession before a player can see their own contract.
    for qid in professions:
        row = get_row(qid)
        if not row or row['status'] != 'completed' or quests[qid].get('repeatable'):
            result.append(qid)
    return result
