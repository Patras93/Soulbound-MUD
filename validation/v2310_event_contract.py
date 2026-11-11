# -*- coding: utf-8 -*-
"""Independent, fast, fail-closed event harness smoke, without starting game server."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from validation.v2400_real_quest_events import run_event_coverage
from data.quests import QUESTS


def main():
    result = run_event_coverage(QUESTS)
    assert result['executed'] >= 35, 'Za malo rzeczywistych zdarzen'
    assert result['errors'] == [], 'Test zdarzen zglasza bledy'
    print('AUTONOMICZNE ZDARZENIA QUESTOW v2.31.0: '
          f'{result["executed"]}/{len(QUESTS)} statycznych zadan; '
          f'{result["checks"]} checks PASS', flush=True)

if __name__ == '__main__': main()
