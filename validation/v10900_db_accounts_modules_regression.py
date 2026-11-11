# -*- coding: utf-8 -*-
"""v109: historyczna zgodność metod kont i rzeczywista izolowana SQLite.

Nie otwiera baz użytkowników, nie uruchamia sieci ani serwera produkcji.
"""
from __future__ import annotations
import ast
import hashlib
import inspect
import sqlite3
from pathlib import Path
from storage.db_accounts import DatabaseAccountsMixin
from storage.database import Database
from storage.schema_core import create_core_schema

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_AST_SHA256='bfa62ebefe27476fcc7c79502802a4583d960380a4b8561e052a07b916291c56'
GROUPS={
    'password_recovery': ('issue_password_recovery_v1222','reset_password_with_code_v1222'),
    'legacy_email': ('verified_account_email_v1223','email_taken_v1223','create_account_verified_email_v1223','attach_verified_email_v1223','issue_email_reset_v1223','revoke_email_reset_v1223','reset_password_by_email_v1223'),
    'master_accounts': ('account_name','master_accounts','master_account_by_name'),
    'account_identity': ('account_by_name','is_character_profile','master_account_for_character'),
    'character_deletion': ('_delete_character_mercenary_data_v3002','wipe_characters_for_master','delete_character_for_master','wipe_all_characters_preserve_accounts'),
    'character_roster': ('character_for_account','characters_for_master','character_count_for_master'),
    'character_slots': ('_next_character_slot','_create_hidden_character_account'),
    'presence': ('mark_player_login_v0363','mark_player_logout_v0363','player_presence_v0363'),
    'character_names': ('character_name_exists','character_account_id_by_name_v0928','character_name_by_account_v0928'),
    'friends': ('friend_master_v12213','friend_character_names_v12213','migrate_friend_accounts_v12213','are_friends_v0928'),
    'wallet_read': ('shared_wallet_for_character',),
}
RETAINED={'shared_wallet_for_master','set_shared_wallet_for_master','set_shared_wallet_for_character','apply_shared_wallet_to_character','enable_big_number_copy_rehearsal_v104','create_account','create_character_for_master','create_character','save_character'}

def run():
    checks=0
    p=ROOT/'storage/db_accounts.py'
    tree=ast.parse(p.read_text('utf8'))
    cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='DatabaseAccountsMixin')
    methods={n.name:n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    assert set(methods)==RETAINED, ('API fasady',set(methods)^RETAINED)
    checks+=len(methods)
    for group,expected in GROUPS.items():
        tree=ast.parse((ROOT/f'storage/db_accounts_parts_v109/{group}.py').read_text('utf8'))
        c=next(x for x in tree.body if isinstance(x,ast.ClassDef))
        got={n.name:n for n in c.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        assert set(got)==set(expected),(group,set(got)^set(expected))
        assert not set(got)&set(methods),group
        methods.update(got)
        checks+=len(got)+1
    assert len(methods)==44
    combined='\n'.join(n+'='+ast.dump(methods[n],include_attributes=False) for n in sorted(methods))
    assert hashlib.sha256(combined.encode()).hexdigest()==EXPECTED_AST_SHA256,'historia AST v108'
    checks+=44
    assert DatabaseAccountsMixin.__module__=='storage.db_accounts';checks+=1
    assert issubclass(Database,DatabaseAccountsMixin);checks+=1
    for name in methods:
        assert callable(getattr(DatabaseAccountsMixin,name,None)),name
        checks+=1
    assert all(name in DatabaseAccountsMixin.__dict__ for name in RETAINED);checks+=1
    assert inspect.getsource(DatabaseAccountsMixin.create_character).lstrip().startswith('def create_character(');checks+=1
    assert inspect.getsource(DatabaseAccountsMixin.save_character).lstrip().startswith('def save_character(');checks+=1
    assert len([c for c in DatabaseAccountsMixin.__mro__ if c.__name__.endswith('V109Mixin')])==len(GROUPS);checks+=1
    assert len([c for c in DatabaseAccountsMixin.__mro__ if c.__name__=='DatabaseAccountsMixin'])==1;checks+=1
    # Fresh real in-memory DB; no real account or game file opened.
    class Trial(DatabaseAccountsMixin):pass
    db=Trial();db.conn=sqlite3.connect(':memory:');db.conn.row_factory=sqlite3.Row
    try:
        db.conn.execute('PRAGMA foreign_keys=ON')
        create_core_schema(db)
        a=db.create_account('TestUserA','SecurePasswordAAA_2026')
        b=db.create_account('TestUserB','SecurePasswordBBB_2026')
        assert a!=b;checks+=1
        assert int(db.account_by_name('testusera')['id'])==a;checks+=1
        assert int(db.master_account_by_name('TestUserB')['id'])==b;checks+=1
        assert db.master_account_for_character(a)==a;checks+=1
        assert not db.is_character_profile(a);checks+=1
        assert db.issue_email_reset_v1223('TestUserA') is None;checks+=1
        try: db.attach_verified_email_v1223(a,'fake@example.invalid')
        except ValueError:checks+=1
        else: raise AssertionError('old unsafe email path enabled')
        token=db.issue_password_recovery_v1222(a,'backup',now=1000)
        assert token and len(token)==32;checks+=1
        assert db.issue_password_recovery_v1222(a,'backup',now=1001) is None;checks+=1
        assert not db.reset_password_with_code_v1222('TestUserA',token,'short',now=1001);checks+=1
        assert not db.reset_password_with_code_v1222('TestUserB',token,'NewLongPasswordBBB_2026',now=1001);checks+=1
        assert db.reset_password_with_code_v1222('TestUserA',token,'NewLongPasswordAAA_2026',now=1001);checks+=1
        assert not db.reset_password_with_code_v1222('TestUserA',token,'AnotherLongPassword2026',now=1001);checks+=1
        assert db.conn.execute('SELECT COUNT(*) FROM password_recovery_v1222 WHERE account_id=?',(a,)).fetchone()[0]==0;checks+=1
        # No cross-account mutation from recovery flow.
        from storage.db_shared import hash_password
        import hmac
        def verify_password(password,salt_hex,hash_hex):
            return hmac.compare_digest(hash_password(password,bytes.fromhex(salt_hex))[1],hash_hex)
        row_a=db.account_by_name('TestUserA')
        row_b=db.account_by_name('TestUserB')
        assert verify_password('NewLongPasswordAAA_2026',row_a['password_salt'],row_a['password_hash']);checks+=1
        assert verify_password('SecurePasswordBBB_2026',row_b['password_salt'],row_b['password_hash']);checks+=1
        assert db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok';checks+=1
    finally:db.conn.close()
    print(f'V109 DB ACCOUNTS MODULAR: {checks} PASS; 44 AST=v108, 11 modules, SQLite in memory')
    return checks

if __name__=='__main__':run()
