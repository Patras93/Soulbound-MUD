# -*- coding: utf-8 -*-
"""v105 actual server World() boss spawn and respawn level regression."""
import os
from pathlib import Path
import subprocess
import sys
import unittest


class V105BossRuntimeStageTests(unittest.TestCase):
    def test_all_bosses_keep_authored_stage_on_spawn_and_respawn(self):
        root=Path(__file__).resolve().parents[1]
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
        result=subprocess.run([sys.executable,'-m','validation.v10500_boss_runtime_audit'],
                              cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                              text=True,timeout=120)
        self.assertEqual(result.returncode,0, result.stdout+'\n'+result.stderr)
        self.assertIn("'checks': 365",result.stdout)
        self.assertIn("'bosses': 40",result.stdout)

if __name__=='__main__':unittest.main()
