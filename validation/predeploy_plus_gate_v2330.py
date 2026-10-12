# -*- coding: utf-8 -*-
"""ULTRA 60 PLUS step 60: preserves legacy cloned-data check, then deep properties."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from validation.predeploy_ultimate60_v2329 import schema_and_data_preserved
from validation.predeploy_plus_v2330 import main as deep_checks

def main():
    schema_and_data_preserved()
    result=deep_checks()
    assert result>=5000
    print('PLUS CHECKS PASS',flush=True)
    print('ULTIMATE CASE 60/60 PLUS PASS',flush=True)

if __name__=='__main__':main()
