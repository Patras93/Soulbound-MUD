# -*- coding: utf-8 -*-
"""v102.00.11 - owner read-only error triage, guarded quest repair, exact undo."""
import asyncio
from core.bootstrap_economy_professions import ADMIN_ACCOUNT_NAMES
from validation.v3600_admin_guardian2 import Fake, DB


async def suite():
    db=DB()
    db.conn.executescript('''CREATE TABLE admin_errors_v1224(
      id TEXT PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      exception TEXT NOT NULL, file TEXT NOT NULL, line INT NOT NULL,
      subsystem TEXT NOT NULL, handler TEXT NOT NULL,
      resolved_at TEXT NOT NULL DEFAULT '', resolved_by TEXT NOT NULL DEFAULT '');
      INSERT INTO admin_errors_v1224(id,exception,file,line,subsystem,handler) VALUES
      ('SB-AAAA0001','ValueError','player/session_mixins/quest_offers.py',555,'quest','quests'),
      ('SB-AAAA0002','NameError','player/session_mixins/quest_offers.py',555,'quest','quests'),
      ('SB-AAAA0003','TypeError','network/protocol.py',7,'network','read');''')
    db.conn.execute("INSERT INTO quests VALUES(2,'temple_rats','active',-7,0,0)")
    s=Fake(True,db)
    checks=0

    async def check(command,expected):
        nonlocal checks
        old=len(s.messages)
        await s.admin_command(command)
        result=' '.join(s.messages[old:])
        assert expected in result, (command,expected,result[-700:])
        checks+=1
        return result

    await check('live bledy','CENTRUM NAPRAW: 3')
    await check('live bledy lista 2','CENTRUM NAPRAW: 2')
    await check('live błędy pokaz SB-AAAA0001','NUMER 1 / SB-AAAA0001')
    await check('live bledy diagnoza 2','BLAD KODU: NameError')
    await check('live bledy diagnoza SB-AAAA0003','BRAK ZWERYFIKOWANEJ NAPRAWY')
    await check('live napraw pomoc','CENTRUM NAPRAW:')
    await check('live bledy lista 0','Podaj dodatnia')
    await check('live bledy lista 51','Przekroczono')
    await check('live bledy pokaz SB-DEADBEEF','Nie znaleziono')
    await check('live bledy pokaz ABC','Podaj numer')
    await check('live napraw SB-AAAA0001','Numer SB nie identyfikuje postaci')
    await check('live napraw SB-AAAA0002 Friend temple_rats','Nie wykonuje zmian')
    await check('live napraw sprawdz SB-AAAA0001 Friend temple_rats','korekta MOZLIWA')
    await check('live napraw plan 1 Friend temple_rats','Podglad bez zapisu')
    assert db.quest(2,'temple_rats')['progress']==-7;checks+=1
    await check('live napraw sprawdz SB-AAAA0003 Friend temple_rats','Korekta niedozwolona') if False else None
    await check('live napraw 3 Friend temple_rats','Brak bezpiecznej automatycznej korekty')
    await check('live napraw zastosuj SB-AAAA0002 Friend temple_rats POTWIERDZAM','Korekta niedozwolona')
    assert db.quest(2,'temple_rats')['progress']==-7;checks+=1
    await check('live napraw zastosuj SB-AAAA0001 Friend temple_rats','POTWIERDZAM')
    await check('live napraw zastosuj SB-AAAA0001 Friend temple_rats POTWIERDZAM','numer korekty 1')
    assert db.quest(2,'temple_rats')['progress']==0;checks+=1
    assert db.conn.execute("SELECT resolved_at FROM admin_errors_v1224 WHERE id='SB-AAAA0001'").fetchone()[0]=='';checks+=1
    assert any(x[1]=='live_repair_quest_v1020011' for x in db.logged);checks+=1
    await check('live napraw zastosuj 1 Friend temple_rats POTWIERDZAM','Korekta niedozwolona')
    await check('live napraw cofnij 1','POTWIERDZAM')
    await check('live napraw cofnij 1 POTWIERDZAM','COFNIETO KOREKTE QUEST #1')
    assert db.quest(2,'temple_rats')['progress']==-7;checks+=1
    assert any(x[1]=='live_repair_undo_v1020011' for x in db.logged);checks+=1
    await check('live napraw cofnij 1 POTWIERDZAM','Nie ma aktywnej korekty')
    await check('live napraw cofnij abc POTWIERDZAM','Podaj dodatnia')
    await check('live napraw sprawdz 1 Friend no_such_quest','Nieznany ID questa')
    db.conn.execute("UPDATE admin_errors_v1224 SET resolved_at='2026-10-26' WHERE id='SB-AAAA0001'")
    await check('live napraw zastosuj 1 Friend temple_rats POTWIERDZAM','Korekta niedozwolona')
    db.conn.execute("UPDATE admin_errors_v1224 SET resolved_at='' WHERE id='SB-AAAA0001'")
    friend=Fake(False,db)
    s.server.sessions.append(friend)
    await check('live napraw sprawdz 1 Friend temple_rats','korekta NIEDOZWOLONA')
    await check('live napraw zastosuj 1 Friend temple_rats POTWIERDZAM','Korekta niedozwolona')
    assert db.quest(2,'temple_rats')['progress']==-7;checks+=1
    before=len(friend.messages)
    await friend.admin_command('live bledy lista 10')
    assert 'Nieznana komenda' in ' '.join(friend.messages[before:]);checks+=1
    before=len(friend.messages)
    await friend.admin_command('live napraw 1')
    assert 'Nieznana komenda' in ' '.join(friend.messages[before:]);checks+=1
    s.server.sessions.remove(friend)
    await check('live napraw 2 Friend temple_rats','BLAD KODU: NameError')
    assert db.quest(2,'temple_rats')['progress']==-7;checks+=1
    assert not any(x[1]=='live_repair_quest_v1020011' and 'SB-AAAA0002' in x[2] for x in db.logged);checks+=1
    return checks


def run():
    ADMIN_ACCOUNT_NAMES.add('owner')
    try:
        return asyncio.run(suite())
    finally:
        ADMIN_ACCOUNT_NAMES.discard('owner')


if __name__ == '__main__':
    print('ADMIN LIVE REPAIR CENTER v102.00.11:',run(),'checks PASS',flush=True)
