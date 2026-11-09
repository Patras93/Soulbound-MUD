# -*- coding: utf-8 -*-
"""v110: autoratatywny katalog klas po wczytaniu przez native_runtime.

Wczesny import historycznych testow moze zostawic stare odniesienie
`core.classes_skills` w atrybucie pakietu core. Native runtime w tym samym
procesie poprawnie tworzy nowy modul w sys.modules. Nowe definicje musza
trafiac do KANONICZNEGO modulu, inaczej kreator nie widzi nowych ras.
"""
from __future__ import annotations
import sys
from types import ModuleType


def canonical_classes_skills():
    import core
    # Native runtime can create sys.modules['core.classes_skills'] without
    # publishing the attribute on its parent package. Never rely on an
    # earlier incidental import by a test or player command.
    canonical=sys.modules.get('core.classes_skills')
    if not isinstance(canonical,ModuleType):
        raise RuntimeError('v110: brak kanonicznego katalogu klas')
    required=('CLASSES','RACES','CLASS_SKILLS','CLASS_STARTING_STAT_BONUSES',
              'RACE_CLASS_RECOMMENDATIONS')
    if not all(hasattr(canonical, field) for field in required):
        raise RuntimeError('v110: niekompletny katalog klas')
    if getattr(core, 'classes_skills', None) is not canonical:
        # Package cache can hold the pre-bootstrap historical module. Replace
        # its pointer, not sys.modules or any player-owned data.
        core.classes_skills=canonical
    return canonical
