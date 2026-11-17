# -*- coding: utf-8 -*-
"""Check immutable release progression and read-only published content; no old editor tests."""
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from systems.published_world_content import PublishedWorldContent
from systems import adaptive_switch_v102006 as adaptive
from core import live_level_caps_v5200 as limits

ROOT=Path(__file__).resolve().parents[1]

def main():
    checks=0
    assert all(limits.cap(axis) is None for axis in limits.PROGRESSION_KEYS)
    checks+=1
    assert limits.cap('ulepszenia_eq')==10
    checks+=1
    assert not any(k in vars(limits) for k in ('change','change_all','_atomic_write','reset_all','load'))
    checks+=1
    assert not any(k in vars(adaptive) for k in ('command','_store','reset_world'))
    checks+=1
    assert not any(p.name.startswith(('admin'+'_live','admin'+'_guardian','live'+'_olc')) for p in ROOT.rglob('*.py'))
    checks+=1
    assert not any(hasattr(PublishedWorldContent,k) for k in ('stage_new_item','stage_edit','apply','export','stage_file'))
    checks+=1
    db=sqlite3.connect(':memory:')
    db.row_factory=sqlite3.Row
    before=db.total_changes
    state=PublishedWorldContent(SimpleNamespace(conn=db))
    assert db.total_changes==before and state.revision==0
    checks+=1
    assert state.active and isinstance(state.active,dict)
    checks+=1
    assert not hasattr(state,'draft') and not hasattr(state,'history')
    checks+=1
    db.close()
    print(f'PUBLISHED READ-ONLY & PROGRESSION: {checks}/{checks} PASS',flush=True)
    return checks

if __name__=='__main__':main()
