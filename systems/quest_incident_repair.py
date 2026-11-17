"""Targeted quest incident safety, independent of removed simulation panels."""
from data.quests import QUESTS
def find_online(session, nick):
    if not nick or len(nick) > 80:
        return None
    candidate = session.server.find_character_session(nick)
    return candidate if candidate and not candidate.closed and candidate.character and candidate.character.name.casefold() == nick.casefold() else None

def _quest_row(s, nick, qid):
    row=s.server.db.conn.execute('SELECT account_id,name FROM characters WHERE name=? COLLATE NOCASE',(nick,)).fetchone()
    if not row: raise ValueError('Nieznany nick. Podaj dokladna nazwe postaci.')
    quest=QUESTS.get(qid)
    if not quest: raise ValueError('Nieznany ID questa.')
    saved=s.server.db.quest(int(row['account_id']),qid)
    return row,quest,saved

def _quest_data(s, nick, qid):
    row, quest, saved=_quest_row(s,nick,qid)
    if not saved: return f"QUEST {row['name']} {qid}: nieprzyjety. Brak automatycznej zmiany."
    state='BLEDNY UJEMNY POSTEP: MOZLIWA NAPRAWA DO ZERO TYLKO OFFLINE.' if saved['status']=='active' and int(saved['progress'])<0 else 'Brak jednoznacznej, automatycznej naprawy.'
    return (f"QUEST {row['name']} {qid}: status {saved['status']}, postep {saved['progress']}, "
       f"cel {quest.get('needed','?')}, zakonczono {saved['completion_count']} razy; " + state)

def _quest_repair(s, nick, qid):
    row, quest, saved=_quest_row(s,nick,qid)
    if not saved or saved['status']!='active' or int(saved['progress'])>=0:
        raise ValueError('Brak jednoznacznie blednego ujemnego postepu. Nic nie zmieniono.')
    if find_online(s,nick): raise ValueError('Gracz musi byc offline podczas korekty postepu.')
    conn=s.server.db.conn
    conn.execute('''CREATE TABLE IF NOT EXISTS admin_guardian_quest_repairs_v3600(
      id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER NOT NULL,
      quest_id TEXT NOT NULL, before_progress INTEGER NOT NULL,
      fixed_progress INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      reverted INTEGER NOT NULL DEFAULT 0)''')
    conn.commit()
    old=int(saved['progress'])
    cursor=conn.execute("UPDATE quests SET progress=0 WHERE account_id=? AND quest_id=? AND status='active' AND progress=?",
       (row['account_id'],qid,old))
    if cursor.rowcount!=1:
        conn.rollback(); raise ValueError('Stan questa ulegl zmianie. Sprobuj ponownie diagnostyke.')
    cur=conn.execute('INSERT INTO admin_guardian_quest_repairs_v3600(account_id,quest_id,before_progress,fixed_progress) VALUES (?,?,?,0)',(row['account_id'],qid,old))
    conn.commit()
    return f"QUESTNAPRAW: numer korekty {cur.lastrowid}; {row['name']} {qid} postep {old}->0. Pozostale pola i nagrody bez zmian."
