# -*- coding: utf-8 -*-
"""Static Soulbound catalog. Data only; gameplay logic lives elsewhere."""
from data.catalog_parts.npcs_01 import build_catalog as _npcs_part_01
from data.catalog_parts.npcs_02 import build_catalog as _npcs_part_02

NPCS = {}
NPCS.update(_npcs_part_01())
NPCS.update(_npcs_part_02())

__all__ = ['NPCS']


# All current catalogue content uses the same current release gate.
def _magitek_teacher_enabled():
    from systems.runtime_activation import enabled
    return bool(enabled())


if _magitek_teacher_enabled():
    NPCS['teacher_magitek_v107'] = {
        'name': 'Inżynierka Iria', 'room': 'guild_arcane_chamber',
        'dialogue': 'Uczę Magiteków łączyć magię i technologię. Nie wymagam misji ani poziomu 95.',
        'teacher_class': 'Magitek', 'quest': None,
    }
