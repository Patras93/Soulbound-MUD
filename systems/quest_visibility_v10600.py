# -*- coding: utf-8 -*-
"""v106: czyste filtrowanie ofert, bez zmian historii i stanu SQLite.

Ukończone jednorazowe zadania mają pozostać w `quest ukończone`,
ale nie w ofercie NPC ani w numerowanych stronach `quest list`.
"""


def is_quest_offer_visible_v10600(quest, record):
    """Nie chowaj aktywnych ani odnawialnych; chowaj ukończone jednorazowe."""
    if not record or quest.get("repeatable"):
        return True
    if record["status"] == "active":
        return True
    if record["status"] == "completed":
        return False
    # Stare testowe rekordy nie zawsze zawierają `completion_count`.
    count = record["completion_count"] if "completion_count" in record.keys() else 0
    return int(count or 0) == 0


def filter_quest_offers_v10600(quest_ids, quest_catalog, db, account_id):
    """Zachowuje kolejność, nie zapisuje niczego do bazy."""
    result = []
    for qid in quest_ids:
        quest = quest_catalog.get(qid)
        if quest is None:
            continue
        row = db.quest(account_id, qid)
        if is_quest_offer_visible_v10600(quest, row):
            result.append(qid)
    return result
