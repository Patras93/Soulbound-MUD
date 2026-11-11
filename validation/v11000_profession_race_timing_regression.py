# -*- coding: utf-8 -*-
"""Dodatkowe bramki: 8 klas, ras i profesji bez regresji czasow v107/v109."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from core.archetypes.expansion import CLASS_SPECS,RACE_SPECS,PROFESSION_SPECS
from core.archetypes.chaos import PROFESSION_SPECS as V107_PROFESSIONS
from core.archetypes.expansion_parts.profession_timing_v110 import register_timing,V110_TIMINGS
from core.profession_timing import TOOL_ACTION_BASE_SECONDS,TOOL_ACTION_MIN_SECONDS,profession_action_seconds


def main():
    assert len(CLASS_SPECS)==len(RACE_SPECS)==len(PROFESSION_SPECS)==8
    assert len({c[0] for c in CLASS_SPECS})==8
    assert len({r[0] for r in RACE_SPECS})==8
    assert len({p[1] for p in PROFESSION_SPECS})==8
    assert all(sum(r[3])==50 and len(r[3])==5 for r in RACE_SPECS)
    # Do not mutate real dictionaries used by the running server.
    base=dict(TOOL_ACTION_BASE_SECONDS)
    minimum=dict(TOOL_ACTION_MIN_SECONDS)
    original_base=dict(base)
    original_minimum=dict(minimum)
    register_timing(PROFESSION_SPECS,base,minimum)
    assert all(base[k]==v and minimum[k]==original_minimum[k]
               for k,v in original_base.items())
    assert len(base)==len(original_base)+16, (len(base),len(original_base))
    for _,tool,*_ in V107_PROFESSIONS:
        assert base[tool]==20 and minimum[tool]==5,tool
    for tool,(b,m) in V110_TIMINGS.items():
        assert base[tool]==b and minimum[tool]==m,tool
    frozen=(dict(base),dict(minimum))
    try:register_timing(PROFESSION_SPECS,base,minimum)
    except ValueError as exc:
        assert str(exc).startswith('v110:'), str(exc)
    else:raise AssertionError('Duplicate timing registration did not fail closed')
    assert (base,minimum)==frozen,'Duplicate registration changed catalogues'
    bad_specs=list(PROFESSION_SPECS)
    bad_specs[0]=(*bad_specs[0][:1],'fishing',*bad_specs[0][2:])
    try:register_timing(tuple(bad_specs),base,minimum)
    except ValueError as exc:
        assert str(exc).startswith('v110:'), str(exc)
    else:raise AssertionError('Timing collision not detected')
    assert (base,minimum)==frozen,'Collision changed catalogues'
    assert (TOOL_ACTION_BASE_SECONDS,TOOL_ACTION_MIN_SECONDS)==(original_base,original_minimum)
    print('V110 TIMERS & ARCHETYPES PASS: 8 klas, 8 ras, 8 narzedzi; '
          'historical tool times intact, duplicate/collision atomic',flush=True)

if __name__=='__main__':main()
