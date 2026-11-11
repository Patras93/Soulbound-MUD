# -*- coding: utf-8 -*-
import sqlite3
from datetime import date
from systems.holiday.challenges import record_kill,progress

def test():
    conn=sqlite3.connect(':memory:')
    d=date(2027,10,31)
    assert progress(conn,7,d)['daily']==0
    assert not record_kill(conn,7,'v11100_holiday_11_boss','x',day=d)['credited']
    assert not record_kill(conn,7,'old_mob','x',day=d)['credited']
    assert record_kill(conn,7,'v11100_holiday_10_mob_1','fight1',day=d)['credited']
    assert not record_kill(conn,7,'v11100_holiday_10_mob_1','fight1',day=d)['credited']
    assert progress(conn,7,d)['daily']==1
    for n in range(2,10):
        record_kill(conn,7,'v11100_holiday_10_mob_1',f'fight{n}',day=d)
    assert progress(conn,7,d)['daily']==5
    assert progress(conn,8,d)['daily']==0
    assert record_kill(conn,7,'v11100_holiday_10_boss','boss1',day=d)['credited']
    assert progress(conn,7,d)['weekly']==1
    assert progress(conn,7,date(2027,11,1))['daily']==0
    assert progress(conn,7,date(2027,11,1))['weekly']==0 # nowy tydzień ISO
    assert progress(conn,7,date(2027,11,8))['weekly']==0
    assert record_kill(conn,7,'v11100_holiday_11_mob_1','fight11',day=date(2027,11,1))['credited']
    assert progress(conn,7,date(2027,11,1))['daily']==1
    # Wycofanie transakcji nadrzędnej odtwarza liczniki i unikalne walki.
    conn.execute('SAVEPOINT outer')
    record_kill(conn,9,'v11100_holiday_10_boss','rollback',day=d)
    assert progress(conn,9,d)['weekly']==1
    conn.execute('ROLLBACK TO SAVEPOINT outer');conn.execute('RELEASE SAVEPOINT outer')
    assert progress(conn,9,d)['weekly']==0
    try: record_kill(conn,7,'v11100_holiday_10_boss','',day=d)
    except ValueError as exc: assert str(exc) == 'Invalid verified fight identity'
    else:raise AssertionError('empty fight accepted')
    print('V111 HOLIDAY CHALLENGES PASS: exactly-once, inactive zones, daily/weekly, isolation, rollback')

if __name__=='__main__':test()
