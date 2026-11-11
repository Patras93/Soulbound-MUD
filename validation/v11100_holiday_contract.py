# -*- coding: utf-8 -*-
"""Standalone v111 calendar and XP-zone contract, no player data or production runtime."""
from __future__ import annotations
from datetime import date, datetime, timezone, timedelta
from systems.holiday.calendar import MONTHS, easter, movable, occasions, today, local_day, WARSAW, _load_warsaw_timezone
from world.holiday_expareas import install
from world.v11000_realms import prefix
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfoNotFoundError
from world.v11000_realm_index import REGIONS


def check():
    assert len(MONTHS)==12
    # Windows with no installed tzdata must still calculate Warsaw dates and DST.
    path=Path(__file__).resolve().parents[1]/'data/tzdb/Europe_Warsaw.tzif'
    assert path.read_bytes().startswith(b'TZif'), 'missing bundled IANA timezone data'
    class NoInstalledTzdata:
        def __init__(self, key):
            raise ZoneInfoNotFoundError(key)
        @staticmethod
        def from_file(stream, key):
            from zoneinfo import ZoneInfo
            return ZoneInfo.from_file(stream, key=key)
    with patch('systems.holiday.calendar.ZoneInfo', NoInstalledTzdata):
        fallback=_load_warsaw_timezone()
    assert fallback.utcoffset(datetime(2027,1,15,12,tzinfo=fallback))==timedelta(hours=1)
    assert fallback.utcoffset(datetime(2027,7,15,12,tzinfo=fallback))==timedelta(hours=2)
    assert WARSAW.utcoffset(datetime(2027,1,15,12,tzinfo=WARSAW))==timedelta(hours=1)
    assert WARSAW.utcoffset(datetime(2027,7,15,12,tzinfo=WARSAW))==timedelta(hours=2)
    assert easter(2026)==date(2026,4,5)
    assert easter(2027)==date(2027,3,28)
    assert easter(2028)==date(2028,4,16)
    assert date(2027,2,4) in [day for day,_ in movable(2027)]
    assert 'Halloween' in occasions(date(2027,10,31))
    assert 'Boże Narodzenie' in occasions(date(2027,12,25))
    assert local_day(datetime(2026,12,31,23,30,tzinfo=timezone.utc))==date(2027,1,1)
    assert today(date(2027,3,28))['occasions']==('Wielkanoc',)
    parent=prefix(REGIONS[-1][0])+'_14'
    room={parent:{'exits':{}}};mobs={};spawns=[];npcs={};quests={};items={}
    recipes={};zones={};cats={};guides={};power={}
    r=install(room,mobs,spawns,npcs,quests,items,recipes,zones,cats,guides,power)
    for name,amount in [('regions',12),('rooms',96),('mobs',60),('quests',36),
                        ('npcs',12),('items',12),('spawns',108)]:
        assert r[name]==amount,(name,r[name])
    assert len({name for name,_,_ in MONTHS})==12
    assert len({row['name'] for row in items.values()})==12
    assert len(quests)==36
    assert len({mob for _,mob in spawns})==60
    assert all(q['target'] in mobs and q['giver'] in {n['name'] for n in npcs.values()} for q in quests.values())
    assert all(all(id in room for id in data['exits'].values()) for key,data in room.items())
    assert len(zones)==12 and len(guides)==12 and len(power)==12
    assert all('auto_aggro' in mob and not mob['auto_aggro'] for mob in mobs.values())
    assert all('soul_shard' in mob['drops'] for mob in mobs.values())
    assert len([m for m in mobs.values() if m.get('boss')])==12
    print('V111 HOLIDAY CONTRACT PASS: calendar 2026-2028, 12 zones, 96 rooms, 60 mobs, 36 quests, 12 souvenirs, 108 spawns')

if __name__=='__main__':check()
