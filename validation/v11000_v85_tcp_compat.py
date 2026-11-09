# -*- coding: utf-8 -*-
"""v85 historical TCP safety covered by the stronger mandatory v110 TCP gate.

The original v85 fixture copies the full game under an untrusted TEMP name,
which v110 intentionally refuses as a valid test installation. Check the
actual v110 TCP harness contracts here; Windows 60/60 must separately run
v11000_tcp_six_players.py, or v110 release approval is impossible.
"""
from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from validation.v11000_tcp_six_players import (
    run_contract,run_sqlite_cleanup_regression,run_party_stream_regression,
)
from validation.v11000_tcp_six_party_journey import run_contract as six_quest

def main():
    windows=(ROOT/'testuj_soulbound_windows.py').read_text(encoding='utf-8-sig')
    ast.parse(windows)
    assert 'validation/v11000_tcp_six_players.py' in windows
    assert '(len(v110_extra)==4 and all(ret==0' in windows
    assert 'validation/v2102_tcp_six_players.py' in windows  # Old gate retained
    assert run_contract()>=12
    assert run_party_stream_regression()==5
    assert run_sqlite_cleanup_regression()==7
    assert six_quest()==3
    print('V110 V85 TCP COMPAT: old TCP gate retained, '
          'six-player TCP mandatory, contract / roster / SQLite cleanup PASS',flush=True)

if __name__=='__main__':main()
