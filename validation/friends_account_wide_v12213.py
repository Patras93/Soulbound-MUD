# -*- coding: utf-8 -*-
"""v1.22.13: regression tests for account-wide friendship and safe migration."""
import asyncio
import ast
from pathlib import Path
import sqlite3
from types import SimpleNamespace
from storage.db_accounts import DatabaseAccountsMixin
from storage.db_shared import normalize_lookup_text

# Keep the regression test lightweight; runtime modules load via the game bootstrap.
_friends_tree=ast.parse((Path(__file__).resolve().parents[1]/"player/session_mixins/friends.py").read_text("utf-8"))
_friends_node=next(node for node in _friends_tree.body if isinstance(node,ast.ClassDef) and node.name=="SessionFriendsMixin")
_ns={"normalize_lookup_text":normalize_lookup_text}
exec(compile(ast.fix_missing_locations(ast.Module(body=[_friends_node],type_ignores=[])), "player/session_mixins/friends.py", "exec"),_ns)
SessionFriendsMixin=_ns["SessionFriendsMixin"]


def validate_friends_account_wide_v12213():
    checks = 0
    def check(value, name):
        nonlocal checks
        if not value:
            raise AssertionError('FRIENDS ACCOUNT WIDE v1.22.13: ' + name)
        checks += 1

    class Storage(DatabaseAccountsMixin):
        def __init__(self):
            self.conn = sqlite3.connect(':memory:')
            self.conn.row_factory = sqlite3.Row
            self.conn.executescript('''
                CREATE TABLE accounts(id INTEGER PRIMARY KEY,username TEXT);
                CREATE TABLE account_characters(master_account_id INTEGER,character_account_id INTEGER,slot INTEGER);
                CREATE TABLE characters(account_id INTEGER PRIMARY KEY,name TEXT);
                CREATE TABLE migration_flags(flag TEXT PRIMARY KEY);
                CREATE TABLE player_friends_v0928(account_id INTEGER,friend_account_id INTEGER,created_at TEXT DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(account_id,friend_account_id));
                CREATE TABLE player_friend_requests_v0928(sender_account_id INTEGER,target_account_id INTEGER,created_at TEXT DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(sender_account_id,target_account_id));
            ''')
        def characters_for_master(self, master):
            return self.conn.execute('SELECT c.name FROM account_characters ac JOIN characters c ON c.account_id=ac.character_account_id WHERE ac.master_account_id=? ORDER BY ac.slot',(master,)).fetchall()

    db = Storage()
    for ident,name,master,slot in ((1,'Adam',1,1),(2,'Beata',2,1),(3,'AdamDrugi',1,2),
                                   (4,'BeataDruga',2,2),(5,'Celina',5,1),(6,'CelinaDruga',5,2)):
        db.conn.execute('INSERT INTO accounts(id,username) VALUES(?,?)',(ident,'user'+str(ident)))
        db.conn.execute('INSERT INTO characters(account_id,name) VALUES(?,?)',(ident,name))
        db.conn.execute('INSERT INTO account_characters(master_account_id,character_account_id,slot) VALUES(?,?,?)',(master,ident,slot))
    # Legacy accepted friendship between secondary characters.
    db.conn.execute('INSERT INTO player_friends_v0928(account_id,friend_account_id) VALUES(3,4)')
    db.conn.execute('INSERT INTO player_friends_v0928(account_id,friend_account_id) VALUES(4,3)')
    # Legacy pending invitation from a secondary character.
    db.conn.execute('INSERT INTO player_friend_requests_v0928(sender_account_id,target_account_id) VALUES(6,3)')
    db.conn.commit()
    db.migrate_friend_accounts_v12213()
    check(db.are_friends_v0928(1,2),'old friends persisted')
    check(db.are_friends_v0928(3,4),'old friend aliases resolved')
    check(db.are_friends_v0928(1,4),'mixed primary and secondary resolved')
    check(db.are_friends_v0928(4,3),'symmetry')
    check(not db.are_friends_v0928(1,5),'pending not accidentally accepted')
    check(db.conn.execute('SELECT 1 FROM player_friend_requests_v0928 WHERE sender_account_id=5 AND target_account_id=1').fetchone() is not None, 'pending request migrated')
    check(db.conn.execute('SELECT COUNT(*) FROM player_friends_v0928').fetchone()[0]==2,'deduplicated accepted edges')
    check(db.conn.execute('SELECT COUNT(*) FROM player_friend_requests_v0928').fetchone()[0]==1,'deduplicated pending edges')
    db.migrate_friend_accounts_v12213()
    check(db.conn.execute('SELECT COUNT(*) FROM player_friends_v0928').fetchone()[0]==2,'migration idempotent')

    class Client(SessionFriendsMixin):
        def __init__(self, ident, char_id, name, server):
            self.account_id=char_id
            self.master_account_id=ident
            self.character=SimpleNamespace(name=name)
            self.server=server
            self.messages=[]
            self.closed=False
            self.invited=[]
        async def send(self,message):
            self.messages.append(message)
        async def party_invite(self,name):
            self.invited.append(name)
        async def handle_guild_v0926(self,command):
            self.invited.append(command)

    server=SimpleNamespace(db=db)
    online={}
    server.session_by_master_account=lambda master:online.get(master)
    adam=Client(1,3,'AdamDrugi',server)
    beata=Client(2,4,'BeataDruga',server)
    celina=Client(5,6,'CelinaDruga',server)
    online.update({1:adam,2:beata,5:celina})

    async def run():
        await adam.handle_friends_v0928('')
        listing='\n'.join(adam.messages)
        check('Postacie znajomego: Adam' not in listing,'no own characters on friend list')
        check('Beata (offline)' in listing,'first friend character displayed')
        check('BeataDruga (online)' in listing,'active secondary friend displayed')
        db.conn.execute('INSERT INTO accounts(id,username) VALUES(7,"user7")')
        db.conn.execute('INSERT INTO characters(account_id,name) VALUES(7,"BeataTrzecia")')
        db.conn.execute('INSERT INTO account_characters(master_account_id,character_account_id,slot) VALUES(2,7,3)')
        db.conn.commit()
        adam.messages.clear()
        await adam.handle_friends_v0928('')
        check('BeataTrzecia (offline)' in '\n'.join(adam.messages),'newly created character auto appears')
        check(db.are_friends_v0928(3,7),'new character recognized as friend immediately')
        adam.messages.clear()
        await adam.handle_friends_v0928('zaproszenia')
        check(any('Celina' in v for v in adam.messages),'pending alt invitation visible')
        await adam.handle_friends_v0928('akceptuj CelinaDruga')
        check(db.are_friends_v0928(1,5),'alt request accepted for master')
        check(db.are_friends_v0928(6,3),'both alt accounts friends after acceptance')
        await adam.handle_friends_v0928('dodaj BeataTrzecia')
        check(any('już' in v for v in adam.messages),'cannot duplicate friendship through another alt')
        await adam.handle_friends_v0928('party Beata')
        check(beata.character.name in adam.invited,'party invite follows actual online character')
        await adam.handle_friends_v0928('usun BeataTrzecia')
        check(not db.are_friends_v0928(1,2),'friend removed for whole account')
        check(not db.are_friends_v0928(3,4),'friend removed for all other character slots')
        await adam.handle_friends_v0928('dodaj Adam')
        check(any('własnej' in v for v in adam.messages),'cannot friend own alt')
        db.conn.execute('DELETE FROM player_friends_v0928 WHERE (account_id=1 AND friend_account_id=5) OR (account_id=5 AND friend_account_id=1)')
        db.conn.commit()
        adam.messages.clear()
        await adam.handle_friends_v0928('dodaj Celina')
        check(not db.are_friends_v0928(1,5),'friend invitation is not acceptance')
        check(db.conn.execute('SELECT 1 FROM player_friend_requests_v0928 WHERE sender_account_id=1 AND target_account_id=5').fetchone() is not None,'pending invitation uses master account')
        await celina.handle_friends_v0928('akceptuj AdamDrugi')
        check(db.are_friends_v0928(5,1),'accept by alternate character works')
        await celina.handle_friends_v0928('usun Adam')
        check(not db.are_friends_v0928(1,5),'removal works from another account')

    asyncio.run(run())
    return checks


if __name__ == '__main__':
    print(f'FRIENDS ACCOUNT WIDE v1.22.13: {validate_friends_account_wide_v12213()} checks PASS')
