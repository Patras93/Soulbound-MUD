from validation.v4200_virtual_source import read_actual_refactored_source_v4200 as _sb420_view
# -*- coding: utf-8 -*-
"""v3.00.4: static fast guard. Runtime behavior tested in full audit."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_regression_fast():
    checks = 0

    def check(ok, label):
        nonlocal checks
        if not ok:
            raise AssertionError('TEACHER LEARN FAST: ' + label)
        checks += 1

    files = {
        'learning': 'player/session_mixins/skill_learning.py',
        'classes': 'player/session_mixins/class_progression.py',
        'teachers': 'player/session_mixins/shops_teachers.py',
        'look': 'player/session_mixins/perception_maps.py',
        'help': 'world/equipment_help.py',
    }
    content = {key: _sb420_view(ROOT / value) for key, value in files.items()}
    for key, source in content.items():
        ast.parse(source)
        check(bool(source), key + ' exists')
    check('teacher_here_for_active_class()' in content['learning'], 'learn requires local active-class teacher')
    check('if not teacher:' in content['learning'], 'teacher absence guarded')
    check('if self.combat_mob_key:' in content['learning'], 'combat guard preserved')
    check('class_skills = list(CLASS_SKILLS.get(class_name, []))' in content['learning'], 'full indices without filtered renumbering')
    check('if not value:' in content['learning'] and 'await self.teacher_lesson(teacher)' in content['learning'], 'bare learn lists')
    check('if mastery < int(skill["unlock"]):' in content['learning'], 'mastery guarded')
    check('self.pay_training_cost(training_cost)' in content['learning'], 'fee remains')
    check('self.server.db.learn_skill(' in content['learning'], 'durable learned skill')
    check('npc.get("room") == self.character.room_id' in content['classes'], 'same room')
    check('npc.get("teacher_class") in active' in content['classes'], 'active class only')
    check('"Samo learn' in content['help'], 'help explains bare learn')
    check('Nauczyciel klasy {_local_teacher' in content['look'], 'local look describes learn')
    check('Nauka: samo learn' in content['teachers'], 'teacher NPC describes learn')
    return checks


if __name__ == '__main__':
    print(f'TEACHER LEARN v3.00.4 FAST: {run_regression_fast()} checks PASS')
