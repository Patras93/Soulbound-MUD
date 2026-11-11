# -*- coding: utf-8 -*-
"""Run old actual EQ write-barrier test with current v110 readiness checks.

The old test ends by importing v107 readiness, which reads a retired external
installer file. Keep its real SQL assertions and replace only that unrelated
release-policy lookup with the current v110 readiness.
"""
from __future__ import annotations
import sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from validation import v10700_release_readiness as legacy
from validation.v10700_equipment_write_barrier_regression import run
from validation.v11000_release_readiness import unmet_requirements

def main():
    def contemporary_readiness():
        return tuple(unmet_requirements(ROOT))
    with patch.object(legacy,'unmet_requirements',contemporary_readiness):
        checked=run()
    assert checked >= 15
    print(f'V110 EQ BARRIER: {checked} real SQL protections PASS; '
          'current readiness, no retired installer',flush=True)

if __name__=='__main__':main()
