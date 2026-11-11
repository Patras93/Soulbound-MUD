# -*- coding: utf-8 -*-
"""Real learning presentation: only unlocked and unknown skills, original indexes."""
import asyncio
import server  # Boots legacy globals before catalog imports.
from core.classes_skills import CLASS_SKILLS
from systems.content_registry import NPCS
from validation.v3004_teacher_learn import _Session

async def _audit():
    checks = 0
    def check(ok, message):
        nonlocal checks
        checks += 1
        if not ok:
            raise AssertionError('LEARN AVAILABLE v5.00.1: ' + message)

    for class_name, skills in CLASS_SKILLS.items():
        teacher = next((x for x in NPCS.values() if x.get('teacher_class') == class_name), None)
        check(teacher is not None, class_name + ' teacher exists')
        if teacher is None:
            continue
        subject = _Session(class_name, teacher['room'], [class_name], level=1)
        await subject.learn_class_skill('')
        displayed = [x for x in subject.messages if x[:1].isdigit() and '. ' in x]
        eligible = [(index, skill) for index, skill in enumerate(skills, 1) if int(skill['unlock']) <= 1]
        check(len(displayed) == len(eligible), class_name + ': first level only')
        for index, skill in eligible:
            check(any(x.startswith(f'{index}. {skill["name"]}.') for x in displayed), class_name + ': stable index '+str(index))
        for index, skill in enumerate(skills, 1):
            if skill['unlock'] > 1:
                check(not any(x.startswith(f'{index}. {skill["name"]}.') for x in displayed), class_name + ': locked hidden '+str(index))
        if eligible:
            index, first = eligible[0]
            subject.messages.clear()
            await subject.learn_class_skill(str(index))
            check(first['id'] in subject.server.db.known, class_name + ': indexed learn works')
            subject.messages.clear()
            await subject.learn_class_skill('')
            check(not any(x.startswith(f'{index}. {first["name"]}.') for x in subject.messages), class_name + ': known hidden')
            other = [(j, x) for j, x in eligible if j != index]
            for next_index, skill in other:
                check(any(x.startswith(f'{next_index}. {skill["name"]}.') for x in subject.messages), class_name + ': no renumber')
            subject.messages.clear()
            await subject.teacher_lesson(teacher)
            check(any(x.startswith(f'{index}. {first["name"]}.') for x in subject.messages), class_name + ': full talk still lists learned')
            check(any('już nauczona' in x for x in subject.messages), class_name + ': full talk retains status')
        subject.server.db.known.update(skill['id'] for _, skill in eligible)
        subject.messages.clear()
        await subject.learn_class_skill('')
        check(any('Nie masz teraz nowych umiejętności' in x for x in subject.messages), class_name + ': empty list explained')
        check(not any(x[:1].isdigit() and '. ' in x for x in subject.messages), class_name + ': empty truly empty')
    return checks

def audit_v5001_learn_available():
    return asyncio.run(_audit())

if __name__ == '__main__':
    import server
    print('LEARN AVAILABLE v5.00.1:', audit_v5001_learn_available(), 'checks PASS')
