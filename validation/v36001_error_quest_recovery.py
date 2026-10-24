# -*- coding: utf-8 -*-
"""Regressions for numeric error triage and safe quest fix, no real database."""
import asyncio
from core.bootstrap_economy_professions import ADMIN_ACCOUNT_NAMES
from validation.v3600_admin_guardian2 import Fake, DB


async def _suite():
    db=DB()
    db.conn.executescript('''CREATE TABLE admin_errors_v1224(
      id TEXT PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      exception TEXT NOT NULL, file TEXT NOT NULL, line INT NOT NULL,
      subsystem TEXT NOT NULL, handler TEXT NOT NULL,
      resolved_at TEXT NOT NULL DEFAULT '', resolved_by TEXT NOT NULL DEFAULT '');
      INSERT INTO admin_errors_v1224(id,exception,file,line,subsystem,handler) VALUES
       ('SB-AAAA0001','ValueError','player/session_mixins/quest_offers.py',10,'quest','quest'),
       ('SB-AAAA0002','TypeError','systems/network.py',11,'server','network');''')
    s=Fake(True,db)
    count=0
    await s.admin_command('blad lista 10')
    assert 'NUMER 1 / SB-AAAA0001' in ' '.join(s.messages);count+=1
    await s.admin_command('blad numer 1')
    assert 'SB-AAAA0001' in s.messages[-1];count+=1
    await s.admin_command('blad numer SB-AAAA0002')
    assert 'SB-AAAA0002' in s.messages[-1];count+=1
    await s.admin_command('blad diagnoza 1')
    assert 'Obszar QUEST' in s.messages[-1];count+=1
    await s.admin_command('blad diagnoza SB-AAAA0002')
    assert 'poza rozpoznana' in s.messages[-1];count+=1
    await s.admin_command('blad diagnoza SB-DEADBEEF')
    assert 'Brak tego numeru' in s.messages[-1];count+=1
    await s.admin_command('blad numer 0')
    assert 'Podaj numer' in s.messages[-1];count+=1
    await s.admin_command('blad numer ABC')
    assert 'Podaj numer' in s.messages[-1];count+=1
    await s.admin_command('blad questy Friend')
    assert 'brak ujemnych' in s.messages[-1];count+=1
    await s.admin_command('blad questy xxx')
    assert 'Brak postaci' in s.messages[-1];count+=1
    await s.admin_command('blad napraw 1 Friend temple_rats POTWIERDZAM')
    assert 'Brak jednoznacznie' in s.messages[-1];count+=1
    db.conn.execute("INSERT INTO quests VALUES(2,'temple_rats','active',-5,0,0)")
    await s.admin_command('blad questy Friend')
    assert 'temple_rats: postep -5' in s.messages[-1];count+=1
    before=db.quest(2,'temple_rats')['progress']
    await s.admin_command('blad napraw 2 Friend temple_rats POTWIERDZAM')
    assert 'nie jest blad z obszaru questow' in s.messages[-1] and db.quest(2,'temple_rats')['progress']==before;count+=1
    await s.admin_command('blad napraw 1 Friend temple_rats')
    assert 'POTWIERDZAM' in s.messages[-1] and db.quest(2,'temple_rats')['progress']==before;count+=1
    await s.admin_command('blad napraw SB-AAAA0001 Friend temple_rats POTWIERDZAM')
    assert 'numer korekty 1' in s.messages[-1] and db.quest(2,'temple_rats')['progress']==0;count+=1
    assert db.conn.execute("SELECT resolved_at FROM admin_errors_v1224 WHERE id='SB-AAAA0001'").fetchone()[0]=='';count+=1
    assert any(entry[1]=='g2_error_quest_repair' for entry in db.logged);count+=1
    await s.admin_command('blad napraw 1 Friend temple_rats POTWIERDZAM')
    assert 'Brak jednoznacznie' in s.messages[-1];count+=1
    await s.admin_command('historia cofnij 1 POTWIERDZAM')
    assert 'COFNIETO' in s.messages[-1] and db.quest(2,'temple_rats')['progress']==-5;count+=1
    # Online player cannot be modified. Only diagnostic reading is allowed.
    friend=Fake(False,db)
    s.server.sessions.append(friend)
    s.server.find_character_session=lambda name: next((x for x in s.server.sessions if x.character and x.character.name.casefold()==name.casefold()),None)
    await s.admin_command('blad napraw 1 Friend temple_rats POTWIERDZAM')
    assert 'offline' in s.messages[-1] and db.quest(2,'temple_rats')['progress']==-5;count+=1
    # Non-owner cannot use the old admin error operations.
    await friend.admin_command('blad lista')
    assert 'Nieznana komenda' in friend.messages[-1];count+=1
    db.conn.execute("UPDATE admin_errors_v1224 SET resolved_at='2026-10-22' WHERE id='SB-AAAA0001'")
    s.server.sessions.remove(friend)
    await s.admin_command('blad napraw 1 Friend temple_rats POTWIERDZAM')
    assert 'oznaczone jako naprawione' in s.messages[-1] and db.quest(2,'temple_rats')['progress']==-5;count+=1
    return count


def run():
    ADMIN_ACCOUNT_NAMES.add('owner')
    try:
        return asyncio.run(_suite())
    finally:
        ADMIN_ACCOUNT_NAMES.discard('owner')


if __name__ == '__main__':
    print('ADMIN BLAD + QUEST RECOVERY v36.00.1:',run(),'checks PASS')
