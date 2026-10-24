# -*- coding: utf-8 -*-
"""Source queue rotation shared by realtime combat and detached Admin Live preview.

This function makes only a *choice*. Casting has side effects and remains in
realtime combat. No mutation of cursors, database, character, or world here.
"""
QUEUE_TYPES = ('physical', 'magic', 'feedback')


def choose_queued_skill(preferred, cursors, entries, resolve, usable):
    """Return (channel, selected_index, channel_length, skill) or None.

    Match v81 try_auto_skill_queue's wraparound order exactly. Supplying
    callbacks lets tests use static queues and the arena use a cloned actor.
    """
    if preferred not in QUEUE_TYPES:
        preferred = QUEUE_TYPES[0]
    start = QUEUE_TYPES.index(preferred)
    for channel in QUEUE_TYPES[start:] + QUEUE_TYPES[:start]:
        rows = entries(channel)
        if not rows:
            continue
        size = len(rows)
        offset = int(cursors.get(channel, 0) or 0) % size
        for attempt in range(size):
            index = (offset + attempt) % size
            skill = resolve(rows[index]['skill_id'])
            if usable(skill):
                return channel, index, size, skill
    return None
