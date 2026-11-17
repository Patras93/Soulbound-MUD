# -*- coding: utf-8 -*-
"""Editor input bounds matching owner-configured live caps. No player writes."""
from core import live_level_caps_v5200 as caps

def level_bound(axis):
    if axis not in ('bieglosc','profesje','narzedzia','gildia','eq'):
        raise ValueError('Nieznany limit poziomu OLC.')
    return min(caps.TECHNICAL_CEILING, caps.effective_number(caps.cap(axis)))
