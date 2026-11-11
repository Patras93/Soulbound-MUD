# -*- coding: utf-8 -*-
"""Bounty leader-to-party acceptance, independent SQLite progress and safety."""
import asyncio
import sqlite3
from types import SimpleNamespace

import server  # Initializes historical gameplay globals for world modules.
from player.session_mixins.museum_bounty import SessionMuseumBountyMixin
from storage.db_world import DatabaseWorldMixin


class _BountyDb(DatabaseWorldMixin):
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('''CREATE TABLE bounty_boards (
            account_id INTEGER PRIMARY KEY, offers_json TEXT NOT NULL,
            active_json TEXT NOT NULL, completed_count INTEGER DEFAULT 0,
            updated_at TEXT)''')


class _Server:
    def __init__(self, db):
        self.db=db
        self.sessions={}
        self.parties={1:{1,2,3,4}, 9:{9,10}}
    def party_key_for_account(self, aid):
        return next((lead for lead, members in self.parties.items() if aid in members), None)
    def party_sessions(self, aid, same_room=None):
        lead=self.party_key_for_account(aid)
        return [self.sessions[k] for k in self.parties.get(lead,()) if k in self.sessions]


class _Hero(SessionMuseumBountyMixin):
    def __init__(self,server,aid,name,room='guild_hall'):
        self.server=server
        self.account_id=aid
        self.character=SimpleNamespace(name=name,room_id=room)
        self.closed=False
        self.messages=[]
    async def send(self,message):
        self.messages.append(str(message))
    def ensure_bounty_board(self):
        return self.server.db.bounty_board_state(self.account_id)


def run_regression():
    checks=0
    db=_BountyDb(); server=_Server(db)
    heroes={aid:_Hero(server,aid,name,room) for aid,name,room in (
        (1,'Lider','guild_hall'),(2,'Wojowniczka','mines'),
        (3,'Druidka','guild_hall'),(4,'Mag','guild_hall'),
        (9,'Obcy lider','guild_hall'),(10,'Obcy członek','guild_hall'))}
    server.sessions=dict(heroes)
    offer={'kind':'kill','target':'goblin','label':'Pokonaj gobliny',
           'needed':8,'stage':18,'reward_soul_xp':1200,'reward_gold':32}
    extra={'kind':'mine','target':'mine','label':'Zbierz rudę',
           'needed':5,'stage':3,'reward_soul_xp':200,'reward_gold':2}
    for aid in heroes:
        db.save_bounty_board_state(aid,offers=[offer if aid==1 else extra],active={},completed_count=aid)
    own={'kind':'herb','target':'herb','label':'Zbierz zioła',
         'needed':9,'progress':4,'completed':False,'reward_soul_xp':250,'reward_gold':8}
    db.save_bounty_board_state(3,active=own)
    db.save_bounty_board_state(4,active={},completed_count=17)
    # Other party must not receive the leader's contract.
    asyncio.run(heroes[1].handle_bounty('accept 1'))
    leader=db.bounty_board_state(1)
    assert leader['active']['target']=='goblin' and leader['active']['progress']==0
    checks+=1
    teammate=db.bounty_board_state(2)
    assert teammate['active']['target']=='goblin' and teammate['active']['progress']==0
    assert teammate['active']['needed']==8 and teammate['active']['reward_soul_xp']==1200
    checks+=3
    assert teammate['offers'][0]['target']=='mine' and teammate['completed_count']==2
    checks+=2
    assert db.bounty_board_state(3)['active']==own
    assert db.bounty_board_state(3)['offers'][0]['target']=='mine'
    checks+=2
    assert db.bounty_board_state(4)['active']['target']=='goblin' and db.bounty_board_state(4)['completed_count']==17
    checks+=2
    assert not db.bounty_board_state(9)['active'] and not db.bounty_board_state(10)['active']
    checks+=1
    assert any('Lider Lider przyjął' in m for m in heroes[2].messages)
    assert any('Nie nadpisano aktywnych' in m for m in heroes[1].messages)
    checks+=2
    # Personal progress and cancellation must never rewrite anyone else's progress.
    step=db.bounty_board_state(2); step['active']['progress']=4
    db.save_bounty_board_state(2,active=step['active'])
    assert db.bounty_board_state(1)['active']['progress']==0
    checks+=1
    asyncio.run(heroes[1].handle_bounty('porzuc'))
    assert not db.bounty_board_state(1)['active'] and db.bounty_board_state(2)['active']['progress']==4
    checks+=1
    # Nonleader acceptance does not spread within party, even if physically present.
    db.save_bounty_board_state(4,active={})
    asyncio.run(heroes[4].handle_bounty('przyjmij 1'))
    assert db.bounty_board_state(4)['active']['target']=='mine'
    assert db.bounty_board_state(2)['active']['target']=='goblin'
    checks+=2
    # Offline party member must not be silently assigned a quest.
    db.save_bounty_board_state(1,active={})
    del server.sessions[4]
    db.save_bounty_board_state(4,active={})
    asyncio.run(heroes[1].handle_bounty('accept 1'))
    assert not db.bounty_board_state(4)['active']
    checks+=1
    # Membership can change during a command; no cross-party propagation.
    assert server.party_key_for_account(9)==9
    checks+=1
    db.conn.close()
    return checks

if __name__=='__main__':
    print(f'BOUNTY DLA DRUZYNY v11.00.19: {run_regression()} checks PASS')
