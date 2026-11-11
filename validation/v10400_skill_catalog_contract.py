# -*- coding: utf-8 -*-
"""Kontrola rozszerzenia katalogu v104 bez osłabiania historycznego audytu.

Dla każdej klasy muszą istnieć dokładnie trzy nowe ID. Stary katalog 5461
umiejętności jest sprawdzany osobno przez niezmienione sumy mechanik v11.
"""

LEGACY_SKILLS = 5461
NEW_SKILLS = 66
TOTAL_SKILLS = LEGACY_SKILLS + NEW_SKILLS


def old_and_new_skills(skills_by_class):
    if len(skills_by_class) != 22:
        raise AssertionError('v104: wymagane wszystkie 22 klasy.')
    old, new = {}, {}
    for index, (klass, rows) in enumerate(skills_by_class.items(), 1):
        prefix = f'v10400_skill_{index:02d}_'
        legacy = [item for item in rows if not str(item['id']).startswith('v10400_skill_')]
        added = [item for item in rows if str(item['id']).startswith('v10400_skill_')]
        expected = {f'{prefix}{i}' for i in (1, 2, 3)}
        actual = {str(item['id']) for item in added}
        if len(added) != 3 or actual != expected:
            raise AssertionError(f'v104: brak trzech prawidłowych nowych umiejętności: {klass}.')
        old[klass] = legacy
        new[klass] = added
    if sum(map(len, old.values())) != LEGACY_SKILLS:
        raise AssertionError('v104: naruszony historyczny katalog 5461 skilli.')
    if sum(map(len, new.values())) != NEW_SKILLS:
        raise AssertionError('v104: nieprawidłowa liczba nowych skilli.')
    ids = [str(s['id']) for rows in skills_by_class.values() for s in rows]
    if len(ids) != TOTAL_SKILLS or len(set(ids)) != len(ids):
        raise AssertionError('v104: zdublowany ID lub niekompletny katalog.')
    return old, new
