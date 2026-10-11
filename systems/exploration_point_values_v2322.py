# -*- coding: utf-8 -*-
"""Exploration rewards by room difficulty, special features and authored overrides.

Do not confuse room discovery counts with EP. The scale is intentionally
moderate and independent of the player's level: exploring a difficult area
should be more rewarding even if a high-level party leads a lower-level one.
"""


def room_explorer_points_v2322(room):
    room = room or {}
    explicit = room.get("exploration_ep")
    if explicit is not None:
        try:
            return max(1, min(30, int(explicit)))
        except (TypeError, ValueError):
            explicit = None  # Malformed authored override: use level-based points.

    stage = 1
    for key in ("recommended_mastery", "recommended_level", "generator_level", "level"):
        try:
            number = int(room.get(key) or 0)
        except (TypeError, ValueError):
            number = 0
        if number > 0:
            stage = number
            break

    # Level 1-100: 2 EP; 101-200: 3; 201-300: 4; 301-400: 5;
    # 401-500: 6; ... capped at 8 EP before landmark bonuses.
    points = 2 + min(6, max(0, (stage - 1) // 100))
    if room.get("v0140_secret_room") or room.get("v1190_secret") or room.get("hidden_secret"):
        points += 2
    if room.get("v0140_mini_final") or room.get("v018_ruin_final") or room.get("exploration_boss_room"):
        points += 1
    return min(12, points)


def zone_explorer_points_v2322(room_ids, visited, awarded, rooms):
    """Per-account attainable EP: legacy rooms keep their original 1 EP.

    The historic room record is permanent. A room without a new ledger entry
    was discovered before this feature and must not be counted as if it had
    received the new larger award.
    """
    earned = possible = 0
    for room_id in room_ids:
        if room_id in visited:
            value = max(1, int(awarded.get(room_id, 1)))
            earned += value
        else:
            value = room_explorer_points_v2322(rooms.get(room_id, {}))
        possible += value
    return earned, possible
