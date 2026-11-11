# -*- coding: utf-8 -*-
"""v110: v15.40-v19 OLC w jednym bezpiecznym rozruchu z osmioma nowymi rasami.

Historyczne OLC14 wymaga uprzednio zbudowanego katalogu runtime. Test
startuje z prawdziwym bootstrapem na izolowanej bazie w TEMP, zamiast
uzalezniac testy od przypadkowej kolejnosci importow lub dotykac produkcji.
"""
from __future__ import annotations
import os
from pathlib import Path
import socket
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))


def main():
    with tempfile.TemporaryDirectory(prefix='sb110_olc_late_') as scratch:
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        for key in ('SOULBOUND_DB', 'SOULBOUND_HOST', 'SOULBOUND_PORT',
                    'PORT', 'RAILWAY_TCP_APPLICATION_PORT'):
            os.environ.pop(key, None)
        os.environ.update(
            SOULBOUND_DB=str(Path(scratch) / 'late_olc.sqlite'),
            SOULBOUND_HOST='127.0.0.1',
            SOULBOUND_PORT=str(port),
            SOULBOUND_V107_STAGING='1',
            SOULBOUND_V109_STAGING='1',
            SOULBOUND_V110_STAGING='1',
        )
        from systems.v11000_activation import authorized_mode
        assert authorized_mode(os.environ['SOULBOUND_DB']) == 'test'
        import server
        try:
            from core.classes_skills import CLASSES, RACES
            from core.archetypes.expansion import CLASS_SPECS, RACE_SPECS
            from player.session_mixins.io_auth_character import (
                RACES as CREATOR_RACES, CLASSES as CREATOR_CLASSES)
            assert len(CLASSES) == len(RACES) == 38
            assert CREATOR_RACES is RACES and CREATOR_CLASSES is CLASSES
            class_names = {row[0] for row in CLASSES}
            race_names = {row[0] for row in RACES}
            assert len(class_names) == len(race_names) == 38
            assert len(CLASS_SPECS) == len(RACE_SPECS) == 8
            assert all(spec[0] in class_names for spec in CLASS_SPECS)
            assert all(spec[0] in race_names for spec in RACE_SPECS)
            from validation.v1540_olc12_guardian_rewards import run as rewards
            from validation.v1600_olc13_mass_editor import run as mass_editor
            from validation.v1700_olc14_dependencies_crafting import run as dependencies
            from validation.v1900_olc_status_skills import run as statuses
            results = (rewards(), mass_editor(), dependencies(), statuses())
            assert results == (32, 40, 48, 64), results
            assert len(CLASSES) == len(RACES) == 38
            assert all(spec[0] in {row[0] for row in RACES} for spec in RACE_SPECS)
            print('V110 OLC LATE + RACES PASS: 184 historyczne kontrole OLC '
                  'oraz 8 ras/8 klas dostepnych w kreatorze; '
                  'SQLite wyłącznie TEMP, localhost', flush=True)
            return 0
        finally:
            server._BOOT_SOCKET.close()


if __name__ == '__main__':
    raise SystemExit(main())
