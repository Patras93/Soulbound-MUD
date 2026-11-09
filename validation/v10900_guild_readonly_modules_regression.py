# -*- coding: utf-8 -*-
"""v109: read-only guild method modularity, no production database access."""
from __future__ import annotations
import ast
import hashlib
import sqlite3
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_AST_SHA256="e542826aae7b4702f867dc2472d5ff46a8b91f9a4ac28745b93d7b7f3f2bdd09"
MOVED={
 'membership':('guild_row_v0926','clan_row_v0925','clan_session_by_account_v0925'),
 'bonuses':('refresh_guild_bonus_v0926','guild_bonus_percent_v0926'),
 'permissions':('guild_role_v0926','guild_has_permission_v0926','guild_rank_name_v0926','guild_rank_priority_v0926'),
 'money':('parse_guild_money_v0926',),
}

def run_regression():
    checks=0
    original=ast.parse((ROOT/'player/session_mixins/forge_guilds.py').read_text('utf8'))
    facade=next(n for n in original.body if isinstance(n,ast.ClassDef) and n.name=='SessionForgeGuildsMixin')
    methods={m.name:m for m in facade.body if isinstance(m,(ast.FunctionDef,ast.AsyncFunctionDef))}
    for module,names in MOVED.items():
        path=ROOT/f'player/session_mixins/guild_readonly_parts_v109/{module}.py'
        tree=ast.parse(path.read_text('utf8'))
        one=next(n for n in tree.body if isinstance(n,ast.ClassDef))
        found={m.name:m for m in one.body if isinstance(m,(ast.FunctionDef,ast.AsyncFunctionDef))}
        assert set(found)==set(names),(module,sorted(found),names)
        assert not set(found)&set(methods),(module,'duplicate')
        methods.update(found)
        checks+=len(names)
    assert len(methods)==36
    fingerprint=hashlib.sha256(('\n'.join(n+'='+ast.dump(methods[n],include_attributes=False) for n in sorted(methods))).encode()).hexdigest()
    assert fingerprint==EXPECTED_AST_SHA256,fingerprint
    checks+=36
    from player.session_mixins.forge_guilds import SessionForgeGuildsMixin
    assert SessionForgeGuildsMixin.__module__=='player.session_mixins.forge_guilds'
    assert all(callable(getattr(SessionForgeGuildsMixin,n,None)) for n in methods)
    checks+=len(methods)
    # In-memory session + SQLite; never opens game saves, no write access to prod.
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
    conn.executescript("""CREATE TABLE player_clans (id INTEGER PRIMARY KEY, level INTEGER);
       INSERT INTO player_clans(id,level) VALUES (2,12);
    """)
    class DB:
        def __init__(self): self.conn=conn
        def clan_membership(self,aid):
            return {'clan_id':2,'rank':('member' if aid==10 else 'leader')} if aid in (10,11) else None
        def guild_role_v0926(self,cid,rank):
            return {'name':'Członek','priority':3,'withdraw_items':0,'invite_members':1} if cid==2 and rank=='member' else None
    class Dummy(SessionForgeGuildsMixin):
        def __init__(self,aid):
            self.account_id=aid
            self.server=SimpleNamespace(db=DB(),sessions=[])
            self.character=SimpleNamespace(_guild_bonus_percent=0)
        def normalize_bank_currency(self,currency):
            return {'gold':'gold','silver':'silver'}.get(currency)
        def bank_amount_to_silver(self,amount,currency):return amount*(100 if currency=='gold' else 1)
    m=Dummy(10);leader=Dummy(11);outsider=Dummy(12)
    assert m.guild_row_v0926()=={'clan_id':2,'rank':'member'};checks+=1
    assert m.clan_row_v0925()==m.guild_row_v0926();checks+=1
    assert m.guild_rank_name_v0926()=='Członek';checks+=1
    assert m.guild_rank_priority_v0926()==3;checks+=1
    assert m.guild_has_permission_v0926('invite_members') is True;checks+=1
    assert m.guild_has_permission_v0926('withdraw_items') is False;checks+=1
    assert leader.guild_has_permission_v0926('withdraw_items') is True;checks+=1
    assert outsider.guild_has_permission_v0926('invite_members') is False;checks+=1
    assert m.parse_guild_money_v0926('2 gold')==200;checks+=1
    assert m.parse_guild_money_v0926('0 gold') is None;checks+=1
    assert m.parse_guild_money_v0926('2 unknown') is None;checks+=1
    assert m.clan_session_by_account_v0925(99) is None;checks+=1
    friend=SimpleNamespace(account_id=99,closed=False)
    m.server.sessions=[friend]
    assert m.clan_session_by_account_v0925(99) is friend;checks+=1
    assert conn.execute('SELECT count(*) FROM player_clans').fetchone()[0]==1;checks+=1
    conn.close()
    print(f'GUILD READONLY MODULES v109: {checks} PASS; AST v108 identical; isolated SQLite')
    return checks

if __name__=='__main__':run_regression()
