# -*- coding: utf-8 -*-
"""Isolation, threshold selection and atomic-draft regression for EXP PROGI."""
import copy
from pathlib import Path
import sqlite3
from types import SimpleNamespace
from unittest.mock import patch
from data.quests import QUESTS
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_quest_xp_threshold_v1 import (
    preview, stage, plan, _available, _eligible, MAX_QUEST_OVERRIDES,
)


def run():
    checks = 0
    dispatcher = (Path(__file__).resolve().parents[1] / 'player/session_mixins/admin_tools.py').read_text(encoding='utf-8')
    assert dispatcher.count("if cmd == 'expprogi':") == 1; checks += 1
    assert 'read_only_preview = True  # Keep pre-existing DRAFT on errors.' in dispatcher; checks += 1
    conn = sqlite3.connect(':memory:'); conn.row_factory = sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    service = LiveContentV1204(SimpleNamespace(conn=conn))
    original_catalog = copy.deepcopy(QUESTS)
    try:
        before = copy.deepcopy(service.draft)
        summary = preview(service, 'xp_statystyk', '1000')
        assert 'EXPPROGI' in summary and 'Podgląd bez zapisu' in summary; checks += 1
        assert service.draft == before; checks += 1
        match, _ = _eligible(service, 'olc_reward_stat_xp', 1000)
        assert match and all(0 < xp < 1000 for _, xp in match); checks += 1
        row_id = match[0][0]
        c = stage(service, 'xp_statystyk', '1000', '25000')
        assert 'Przygotowano' in c; checks += 1
        assert service.draft['quest_edits'][row_id]['olc_reward_stat_xp'] == 25000; checks += 1
        assert original_catalog == QUESTS; checks += 1
        assert service.active == before; checks += 1
        c2 = stage(service, 'xp_statystyk', '1000', '25000')
        assert 'Brak zmian' in c2; checks += 1
        # All previously staged values at or above the threshold remain untouched.
        all_old = copy.deepcopy(service.draft)
        stage(service, 'xp_postaci', '1000', '17000')
        for qid, d in all_old['quest_edits'].items():
            assert service.draft['quest_edits'][qid].get('olc_reward_stat_xp') == d.get('olc_reward_stat_xp')
        checks += 1
        assert _available(QUESTS['fisher_30_fish'], 'fisher_30_fish', 'olc_reward_class_xp') is False; checks += 1
        assert _available(QUESTS['fisher_30_fish'], 'fisher_30_fish', 'olc_reward_soul_xp') is False; checks += 1
        # All-field command cannot create combat mastery in professional gathering quests.
        rows, _ = plan(service, 'wszystkie', '1000')
        assert all(field != 'olc_reward_class_xp' for qid, field, _ in rows if qid == 'fisher_30_fish'); checks += 1
        assert all(field != 'olc_reward_soul_xp' for qid, field, _ in rows if qid == 'fisher_30_fish'); checks += 1
        state = copy.deepcopy(service.draft)
        for field, limit, new in [('xp_statystyk','NaN','1000'),
                                  ('reward_xp','1000','-5'),
                                  ('niedozwolone','1000','5000'),
                                  ('xp_statystyk','1000','999'),
                                  ('xp_statystyk','0','5000'),
                                  ('xp_statystyk','1000','2.5')]:
            try: stage(service, field, limit, new)
            except ValueError: checks += 1
            else: raise AssertionError('invalid parameter accepted')
            assert state == service.draft
        checks += 1
        # Full rollback if validating the composite DRAFT fails.
        with patch.object(service, 'validate', side_effect=ValueError('test failure')):
            try: stage(service, 'xp_duszy', '1000000', '2000000')
            except ValueError: checks += 1
            else: raise AssertionError('failed validation committed draft')
        assert state == service.draft; checks += 1
        # No updates to quest goal, currency or restart flag.
        for qid in service.draft['quest_edits']:
            assert not set(service.draft['quest_edits'][qid]) & {'needed','target','reward_gold','reward_silver','repeat_cooldown'}
        checks += 1
        assert QUESTS == original_catalog; checks += 1
        # Dry-run retains stage without SQLite publication.
        assert conn.execute('SELECT COUNT(*) FROM live_content_v1204').fetchone()[0] == 0; checks += 1
        return checks
    finally:
        service._remove(None)
        conn.close()

if __name__ == '__main__':
    print('ADMIN LIVE EXPPROGI:',run(),'checks PASS')
