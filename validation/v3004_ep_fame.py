# -*- coding: utf-8 -*-
"""Integration: four award types for each EP, saved and never repeated."""
from validation.v2322_auto_exploration import run_regression as run_ep_integrity
from validation.v3004_ep_fame_fast import run_regression_fast
from systems.milestone_cap_rewards_v2103 import fame_cap_awards_v2103
from types import SimpleNamespace


def run_regression():
    checks = run_regression_fast()
    checks += run_ep_integrity()

    class Classless:
        character = SimpleNamespace(character_level=19, soul_level=17)
        def active_class_names(self):
            return ()
        def class_mastery_level(self, name):
            raise AssertionError('A classless session has no class XP')

    caps = fame_cap_awards_v2103(Classless())
    assert caps['character'] > 0
    assert caps['soul'] > 0
    assert caps['stat'] > 0
    assert caps['class_total'] == 0
    checks += 4
    return checks


if __name__ == '__main__':
    print(f'EP JAK FAME v3.00.4: {run_regression()} checks PASS')
