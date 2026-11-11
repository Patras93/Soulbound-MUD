# -*- coding: utf-8 -*-
"""Test bez jakichkolwiek zapisów do SQLite lub uruchamiania serwera."""
from datetime import date, datetime, timezone
import os
import subprocess
import sys
from pathlib import Path
from systems.holiday.schedule import active_schedule, seasonal_message

def test():
    for year in (2026,2027,2028,2030):
        for month in range(1,13):
            s=active_schedule(date(year,month,15))
            assert s['month']==month and s['zone'] and s['boss']
            assert s['month_ends_at'].date()>s['day']
            assert s['daily_key']==f'{year}-{month:02d}-15'
            for event in s['active']:
                assert event['starts_at']<=datetime(year,month,15,tzinfo=event['starts_at'].tzinfo)<event['ends_at']
    assert {x['name'] for x in active_schedule(date(2027,3,28))['active']} >= {'Wielkanoc'}
    assert {x['name'] for x in active_schedule(date(2027,3,29))['active']} >= {'Wielkanoc'}
    assert 'Wielkanoc' not in {x['name'] for x in active_schedule(date(2027,3,30))['active']}
    assert 'Tłusty Czwartek' in {x['name'] for x in active_schedule(date(2027,2,4))['active']}
    assert 'Halloween' in {x['name'] for x in active_schedule(date(2027,11,1))['active']}
    assert 'Halloween' not in {x['name'] for x in active_schedule(date(2027,11,3))['active']}
    assert 'Boże Narodzenie' in {x['name'] for x in active_schedule(date(2027,12,27))['active']}
    assert 'Boże Narodzenie' not in {x['name'] for x in active_schedule(date(2027,12,28))['active']}
    assert 'Sylwester' in {x['name'] for x in active_schedule(date(2027,12,31))['active']}
    assert 'Sylwester' not in {x['name'] for x in active_schedule(date(2028,1,1))['active']}
    dec=active_schedule(date(2026,12,31)); jan=active_schedule(date(2027,1,1))
    assert dec['weekly_key']==jan['weekly_key'] # ISO rok, nie kalendarzowy
    assert dec['daily_key'] != jan['daily_key']
    assert active_schedule(datetime(2027,1,1,0,30,tzinfo=timezone.utc))['day']==date(2027,1,1)
    try:active_schedule(datetime(2027,1,1))
    except ValueError as exc: assert str(exc) == 'naive datetime not allowed'
    else:raise AssertionError('naive datetime accepted')
    assert seasonal_message(date(2027,12,25)).startswith('WYDARZENIA SWIATECZNE:')
    # Real Windows regression: no OS TZPATH and no pip-installed tzdata.
    # Using -S removes site-packages; the calendar must use bundled TZif.
    root=Path(__file__).resolve().parents[1]
    env=os.environ.copy()
    env['PYTHONTZPATH']=''
    env['PYTHONPATH']=str(root)
    isolated=(
        'from datetime import date,datetime,timedelta; '
        'from zoneinfo import TZPATH; '
        'assert not TZPATH; '
        'from systems.holiday.calendar import WARSAW; '
        'from systems.holiday.schedule import active_schedule; '
        'assert WARSAW.utcoffset(datetime(2027,1,15,12,tzinfo=WARSAW))==timedelta(hours=1); '
        'assert WARSAW.utcoffset(datetime(2027,7,15,12,tzinfo=WARSAW))==timedelta(hours=2); '
        'assert active_schedule(date(2027,12,25))["active"]; '
        'assert active_schedule(date(2027,7,15))["month_ends_at"].utcoffset()==timedelta(hours=2)'
    )
    result=subprocess.run([sys.executable,'-S','-c',isolated],cwd=root,env=env,
                          capture_output=True,text=True,timeout=20)
    assert result.returncode==0, ('Windows timezone without tzdata failed: '+result.stderr[-1200:])
    print('V111 HOLIDAY SCHEDULE PASS: dates, cross-year, Easter, timezone without tzdata, daily/weekly keys')

if __name__=='__main__':test()
