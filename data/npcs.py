# -*- coding: utf-8 -*-
"""Static Soulbound catalog. Data only; gameplay logic lives elsewhere."""
from data.catalogs_v109.npcs_01 import build_catalog as _npcs_part_01
from data.catalogs_v109.npcs_02 import build_catalog as _npcs_part_02

NPCS = {}
NPCS.update(_npcs_part_01())
NPCS.update(_npcs_part_02())

__all__ = ['NPCS']


# v107 staging: separate Magitek trainer (class is available from level 1).
import os as _magitek_os_v107
if _magitek_os_v107.environ.get('SOULBOUND_V107_STAGING') == '1':
    NPCS['teacher_magitek_v107'] = {
        'name': 'Inżynierka Iria', 'room': 'guild_arcane_chamber',
        'dialogue': 'Uczę Magiteków łączyć magię i technologię. Nie wymagam misji ani poziomu 95.',
        'teacher_class': 'Magitek', 'quest': None,
    }
