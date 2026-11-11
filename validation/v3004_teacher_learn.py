# -*- coding: utf-8 -*-
"""v3.00.4: local LEARN at active-class teachers. In-memory only."""
import asyncio
from types import SimpleNamespace

from core.classes_skills import CLASS_SKILLS
from network.protocol_gameplay_utils import normalize_lookup_text
from player.session_mixins.skill_learning import SessionSkillLearningMixin
from player.session_mixins.class_progression import SessionClassProgressionMixin
from player.session_mixins.shops_teachers import SessionShopsTeachersMixin
from systems.content_registry import NPCS
from world.equipment_help import HELP_TOPICS


class _DB:
    def __init__(self):
        self.known = set()
        self.learn_calls = []

    def learned_skill_ids(self, _account):
        return set(self.known)

    def knows_skill(self, _account, skill_id):
        return skill_id in self.known

    def learn_skill(self, _account, skill_id):
        self.known.add(skill_id)
        self.learn_calls.append(skill_id)

    def skill_progress(self, _account, _skill_id):
        return {'level': 1, 'xp': 0}


class _Session(SessionSkillLearningMixin, SessionClassProgressionMixin, SessionShopsTeachersMixin):
    def __init__(self, class_name, room, active, level=1):
        self.character = SimpleNamespace(
            class_name=class_name, room_id=room,
            guild_training_discount=lambda _class_name: 0,
        )
        self.server = SimpleNamespace(db=_DB())
        self.account_id = 99
        self.combat_mob_key = None
        self._active = list(active)
        self._level = int(level)
        self.messages = []
        self.pay_calls = []

    # Existing v3.00.4 teacher contract tests focus on matching course indexes;
    # automatic queue integration is validated separately in v3.00.5.
    def auto_register_learned_skill_v3005(self, skill):
        return "passive"

    def active_class_names(self):
        return list(self._active)

    def class_mastery_level(self, _class_name):
        return self._level

    def normalize_description_query(self, raw):
        return normalize_lookup_text(raw)

    def pay_training_cost(self, amount):
        self.pay_calls.append(amount)
        return True

    async def send(self, message):
        self.messages.append(str(message))


async def _regression():
    checks = 0

    def check(expr, message):
        nonlocal checks
        if not expr:
            raise AssertionError('LEARN v3.00.4: ' + message)
        checks += 1

    teacher_id, teacher = next(
        (key, npc) for key, npc in NPCS.items()
        if npc.get('teacher_class') == 'Wojownik'
    )
    teacher_class = teacher['teacher_class']
    skills = list(CLASS_SKILLS[teacher_class])
    check(len(skills) >= 10, 'real teacher skills exist')
    check(teacher.get('room'), 'real teacher room exists')

    s = _Session(teacher_class, teacher['room'], [teacher_class], level=1)
    check(s.teacher_here_for_active_class()[0] == teacher_id, 'local teacher recognized')
    await s.learn_class_skill('')
    check(any('Lekcja klasy Wojownik' in msg for msg in s.messages), 'bare learn shows teacher list')
    check(any(msg.startswith('1. ' + skills[0]['name'] + '.') for msg in s.messages), 'same first index as talk')
    check(any(msg.startswith('2. ' + skills[1]['name'] + '.') for msg in s.messages), 'second teacher skill index')
    check(not s.pay_calls and not s.server.db.learn_calls, 'bare learn never charges or learns')

    s.messages.clear()
    await s.learn_class_skill('1')
    check(s.server.db.learn_calls == [skills[0]['id']], 'learn 1 works in teacher room')
    check(bool(s.pay_calls), 'learning has a fee')
    check(any('Nauczono.' in msg for msg in s.messages), 'learning success message')

    s.messages.clear()
    await s.learn_class_skill('1')
    check(len(s.server.db.learn_calls) == 1, 'already known skill never duplicated')
    check('Już znasz' in ''.join(s.messages), 'known skill message')

    s.messages.clear()
    await s.learn_class_skill(skills[0]['name'])
    check(len(s.server.db.learn_calls) == 1, 'learn by full name obeys known check')

    locked_index = next((i for i, skill in enumerate(skills, 1)
                         if int(skill['unlock']) > 1), None)
    check(locked_index is not None, 'locked skill exists')
    s.messages.clear()
    await s.learn_class_skill(str(locked_index))
    check(any('wymaga Biegłości klasy' in msg for msg in s.messages), 'locked index shows actual requirement')
    check(len(s.server.db.learn_calls) == 1, 'locked skill not learned')

    s.character.room_id = 'temple_spawn'
    s.messages.clear()
    before = len(s.server.db.learn_calls)
    await s.learn_class_skill('')
    await s.learn_class_skill('1')
    check(len(s.server.db.learn_calls) == before, 'learn unavailable outside teacher')
    check(len(s.messages) == 2 and all('Musisz być przy nauczycielu' in msg for msg in s.messages), 'outside messages clear')

    s.character.room_id = teacher['room']
    s._active = ['Mag']
    s.messages.clear()
    await s.learn_class_skill('')
    check('Musisz być przy nauczycielu' in s.messages[0], 'teacher of inactive class blocked')
    check(not s.teacher_here_for_active_class()[1], 'inactive teacher not treated as own')

    s._active = [teacher_class]
    s.combat_mob_key = 'monster'
    s.messages.clear()
    await s.learn_class_skill('')
    check('podczas walki' in s.messages[0], 'learn blocked during combat')

    s.combat_mob_key = None
    s._level = max(int(skill['unlock']) for skill in skills)
    s.messages.clear()
    await s.learn_class_skill(str(locked_index))
    check(skills[locked_index - 1]['id'] in s.server.db.known, 'same index succeeds after mastery')

    check('learn' in HELP_TOPICS, 'help learn topic exists')
    check(any('poza sala nauczyciela' in msg for msg in HELP_TOPICS['learn']), 'help describes teacher restriction')
    check(any('Numery learn' in msg for msg in HELP_TOPICS['nauczyciele']), 'help explains matching numbering')

    return checks


def run_regression():
    return asyncio.run(_regression())


if __name__ == '__main__':
    print(f'TEACHER LEARN v3.00.4: {run_regression()} checks PASS')
