# -*- coding: utf-8 -*-
"""Required v105 read-only migration of real Windows source DB on TEMP copy."""
from __future__ import annotations
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from validation.v10500_safe_db_migration_audit import rehearse

def main():
    source=os.environ.get('SOULBOUND_ULTRA_SOURCE_DB','').strip()
    if not source or not Path(source).is_file():
        raise RuntimeError('Brak prawdziwej bazy SQLite do audytu migracji v105')
    result=rehearse(source)
    assert result['player_records_unchanged'] and result['repeated_startup']=='PASS'
    print('V105 REAL-SOURCE SQLITE MIGRATION ON TEMP CLONE PASS: '+repr(result),flush=True)
if __name__=='__main__':main()
