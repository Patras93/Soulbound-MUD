# -*- coding: utf-8 -*-
"""Two-hour class quest refresh and safe conversion of old hourly guild state."""
from __future__ import annotations
from unittest.mock import patch


def audit_class_quest_cadence_v1289():
    from player.session_mixins.class_guild_progress import (
        CLASS_GUILD_QUEST_CYCLE_SECONDS, SessionClassGuildProgressMixin,
    )
    from systems.content_registry import QUESTS
    from systems.equipment_crafting import GUILD_CLASS_QUEST_POOLS

    problems = []
    checked = 0

    def check(test, description):
        nonlocal checked
        checked += 1
        if not test:
            problems.append(description)

    check(CLASS_GUILD_QUEST_CYCLE_SECONDS == 7200, 'guild quests refresh interval is 7200 seconds')
    for key, quest in QUESTS.items():
        if key.startswith('hourly_class_'):
            check(int(quest.get('repeat_cooldown', 0)) == 7200,
                  f'{key} legacy instructor quest cooldown must be 7200')
    check(len(GUILD_CLASS_QUEST_POOLS) == 14, '14 class guild quest pools')

    class FakeCharacter:
        def __init__(self, raw):
            self.data = {'Wojownik': raw}
        def _guild_json(self, key):
            return self.data
        def _set_guild_json(self, key, value):
            self.data = value

    class FakeDb:
        saves = 0
        def save_character(self, character):
            self.saves += 1
        def class_progress_row(self, account_id, class_name):
            return {'level': 40}

    class FakeSession(SessionClassGuildProgressMixin):
        account_id = 1
        def __init__(self, raw):
            self.character = FakeCharacter(raw)
            self.server = type('Server', (), {'db': FakeDb()})()

    session = FakeSession({'slot': 3, 'active': 0,
                           'quests': {'0': {'progress': 7, 'completed': False}},
                           'mastery_level': 25, 'ever_completed': False})
    # Old 03:15 hourly slot maps into new 02:00-03:59 two-hour window.
    with patch('time.time', return_value=3 * 3600 + 15 * 60):
        state_info, state = session.class_guild_quest_state_v1120('Wojownik')
        check(state['slot'] == 1 and state['cycle_seconds'] == 7200,
              'legacy slot translated to current two-hour window')
        check(state['quests']['0']['progress'] == 7 and state['active'] == 0,
              'in-progress hourly class quest preserved at upgrade')
        check(session.class_guild_quest_refresh_seconds_v1120() == 45 * 60,
              'remaining cooldown computed to next two-hour boundary')
        check(session.class_guild_quest_hour_slot_v1120() == 1,
              'rotation occurs every second hour')
        check(session.server.db.saves == 1,
              'legacy migration written once and retained')
        session.class_guild_quest_state_v1120('Wojownik')
        check(session.server.db.saves == 1,
              'same two-hour window does not rewrite state')
    with patch('time.time', return_value=4 * 3600 + 60):
        _, state = session.class_guild_quest_state_v1120('Wojownik')
        check(state['slot'] == 2 and not state['quests'] and state['active'] is None,
              'new cycle rotates quests only at two-hour boundary')
        check(state['mastery_level'] == 40, 'new mastery snapshot applied to new cycle')
        check(session.class_guild_quest_refresh_seconds_v1120() == 7140,
              'fresh two-hour cycle has correct countdown')

    return {'checks': checked, 'error_count': len(problems), 'errors': problems}


if __name__ == '__main__':
    import server
    result = audit_class_quest_cadence_v1289()
    print(f"CLASS QUESTS v1.28.9: {result['checks']} checks, {result['error_count']} errors")
    if result['error_count']:
        for error in result['errors']:
            print(error)
        raise SystemExit(1)
