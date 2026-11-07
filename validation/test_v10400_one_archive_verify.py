# -*- coding: utf-8 -*-
"""No-server regression for the consolidated v104 runner."""
import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from validation.v10400_one_archive_verify import (
    STAGES, EXTRA, candidate_status, execute_stage, private_environment,
)


class OneArchiveSafety(unittest.TestCase):
    def test_pipeline_has_all_required_lanes(self):
        names = ' '.join(x[0] for x in STAGES + EXTRA)
        for word in ('unittest', '50 modulow', '1096', '296', 'TCP', 'FAST', 'FULL'):
            self.assertIn(word, names)

    def test_never_inherits_production_env(self):
        with tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_') as d:
            with patch.dict(os.environ, {'PORT':'4000','SOULBOUND_HOST':'0.0.0.0',
                                          'SOULBOUND_DB':'C:/Soulbound-MUD/live.sqlite',
                                          'DATABASE_URL':'secret', 'SOULBOUND_ULTRA_SOURCE_DB':'C:/Soulbound-MUD/live.sqlite'}, clear=False):
                env=private_environment(Path(d))
            self.assertEqual(env['SOULBOUND_HOST'], '127.0.0.1')
            self.assertNotEqual(env['PORT'],'4000')
            self.assertNotIn('DATABASE_URL',env)
            self.assertNotIn('SOULBOUND_ULTRA_SOURCE_DB',env)
            self.assertTrue(env['SOULBOUND_DB'].startswith(d))

    def test_broken_stage_is_fail_not_pass(self):
        with tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_') as d:
            rc, output, _=execute_stage('negatywny', ('-c', 'import sys; sys.exit(7)'), 10, Path(d))
            self.assertEqual(rc,7)

    def test_timeout_terminates_stage(self):
        with tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_') as d:
            rc, output, seconds=execute_stage('limit', ('-c','import time; time.sleep(30)'), 1, Path(d))
            self.assertEqual(rc, 124)
            self.assertIn('TIMEOUT', output)
            self.assertLess(seconds, 10)

    def test_stage_success_can_be_recorded(self):
        with tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_') as d:
            rc, output, _=execute_stage('pozytywny', ('-c','print("TEST OK")'), 10, Path(d))
            self.assertEqual(rc,0)
            self.assertIn('TEST OK', output)

    def test_release_identity_matches_runtime_and_changelog(self):
        import re
        root = Path(__file__).resolve().parents[1]
        source = (root / 'core/bootstrap_economy_professions.py').read_text(encoding='utf-8')
        match = re.search(r'^\s*VERSION\s*=\s*[\"\'](\d+\.\d+\.\d+)[\"\']', source, re.M)
        self.assertIsNotNone(match)
        runtime_version = match.group(1)
        root_version = (root / 'VERSION').read_text(encoding='utf-8').strip()
        changelog = (root / 'CHANGELOG_PL.txt').read_text(encoding='utf-8')
        registry = (root / 'systems/content_registry.py').read_text(encoding='utf-8')
        labels = re.findall(r'^LATEST_CHANGES_TITLE\s*=\s*"Soulbound v([^\s]+)', registry, re.M)
        self.assertEqual(runtime_version, root_version)
        self.assertTrue(changelog.startswith('Aktualna paczka: v' + runtime_version + '\n'))
        self.assertTrue(labels and labels[-1] == runtime_version)

    def test_expected_release_label_matches_current_candidate(self):
        # Legacy runner checks the candidate identity; it never deploys it.
        from core.bootstrap_economy_professions import VERSION
        self.assertEqual(candidate_status(), VERSION)
        self.assertGreaterEqual(tuple(int(x) for x in candidate_status().split('.')), (104,0,0))

if __name__=='__main__': unittest.main()
