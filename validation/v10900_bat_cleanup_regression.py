# -*- coding: utf-8 -*-
"""v109: osobny przebieg historycznych testow BAT na syntetycznych plikach.

Wspolne testy v108/v109 i 51 dawnych sum SHA256 sa w module v108;
nie importujemy juz wycofanego, wykonywalnego narzedzia porzadki_bat.py.
"""
from __future__ import annotations
from validation.v10800_bat_cleanup_regression import run as _run_legacy_fixture


def run():
    return _run_legacy_fixture(version='109')


if __name__ == '__main__':
    print('V109 PORZADKI BAT:', run(), 'PASS; test bez danych graczy', flush=True)
