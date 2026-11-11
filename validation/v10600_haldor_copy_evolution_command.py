# -*- coding: utf-8 -*-
"""Isolated real SessionForgeGuildsMixin dispatch + SQLite physical-copy evolution.

Never starts the server or touches a production database.
"""
import os,sys,sqlite3,ast,asyncio,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.equipment_shadow_slots_v10600 import prepare_on_disposable_copy,equipped_copy
from systems.equipment_evolution_v10500 import required_materials
from systems.equipment_evolution_command_v10600 import _code

CAT={'test_haldor_armor':{'name':'Pancerz Próby','type':'armor','defense':160,
                            'affix_amount':80,'stats':{}}}


def _source_handler():
    source=(ROOT/'player/session_mixins/forge_guilds.py').read_text(encoding='utf8')
    tree=ast.parse(source)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SessionForgeGuildsMixin')
    method=next(n for n in cls.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='evolve_equipment_v10500')
    module=ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[]))
    ns={}
    exec(compile(module,str(ROOT/'player/session_mixins/forge_guilds.py'),'exec'),ns)
    return ns[method.name]


def run():
    previous=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
    c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
    checks=0
    def ok(cond,what):
        nonlocal checks
        if not cond:raise AssertionError(what)
        checks+=1
    try:
        c.executescript('''
            CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,
                PRIMARY KEY(account_id,item_id));
            CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,
                PRIMARY KEY(account_id,slot));
            CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER,
                PRIMARY KEY(account_id,record_key));
            CREATE TABLE profession_storage(account_id INTEGER,container TEXT,item_id TEXT,quantity INTEGER,
                PRIMARY KEY(account_id,container,item_id));
            INSERT INTO inventory VALUES(1,'test_haldor_armor',2),(2,'test_haldor_armor',1);
            INSERT INTO equipment VALUES(1,'body','test_haldor_armor'),
                (1,'secondary','test_haldor_armor');
        ''')
        class DB:
            conn=c
            _v106_shadow_item_catalog=CAT
            _v106_shadow_slots_disposable_copy=True
        db=DB()
        prepare_on_disposable_copy(c,CAT,confirm_disposable_copy=True)
        method=_source_handler()
        class Forge:
            account_id=1
            combat_mob_key=None
            at_forge=True
            def __init__(self):
                self.server=type('S',(),{'db':db})()
                self.messages=[]
                self._read_only_equipment_cache_v1262={'old':1}
            def at_haldor_forge_v0925(self):return self.at_forge
            async def send(self,text):self.messages.append(str(text))
        f=Forge()
        def say(arg):asyncio.run(method(f,arg))
        say('kopia lista')
        ok('strona 1/1' in f.messages[0],'NVDA paginated list header')
        ok(len(f.messages)==3,'two worn armors listed, no un-worn copies')
        ok('Pancerz Próby' in f.messages[1] and 'slot body' in f.messages[1],'first worn armor printed')
        rows=list(c.execute('SELECT slot,instance_id FROM v106_equipped_instances WHERE account_id=1 ORDER BY slot,instance_id'))
        code1=_code(rows[0]['instance_id']);code2=_code(rows[1]['instance_id'])
        ok(code1 in f.messages[1] and code2 in f.messages[2],'codes tied to concrete instances')
        ok(code1!=code2,'different copies never share an 8-digit fingerprint in fixture')
        ok('Etap 0/10' in f.messages[1],'initial stage visible')
        say('kopia lista 2')
        ok('strony od 1 do 1' in f.messages[-1],'invalid page rejected')
        say('kopia abc POTWIERDZAM')
        ok('Użycie:' in f.messages[-1],'invalid index rejected')
        say('kopia 1 '+code1+' potwierdzam')
        ok('Użycie:' in f.messages[-1],'explicit confirmation required')
        say('wyzeruj 1 POTWIERDZAM')
        ok('wstrzymana' in f.messages[-1],'dangerous legacy reset blocked')
        say('1')
        ok('wstrzymana' in f.messages[-1],'legacy template evolve blocked')
        say('kopia 1 deadbeef POTWIERDZAM')
        ok('Kod nie zgadza' in f.messages[-1],'wrong instance confirmation refused')
        ok(equipped_copy(c,1,'body',CAT)[2]==0,'wrong confirmation no mutation')
        f.at_forge=False;say('kopia 1 '+code1+' POTWIERDZAM')
        ok('Haldor' in f.messages[-1],'not at Haldor refused')
        f.at_forge=True;f.combat_mob_key='rat';say('kopia 1 '+code1+' POTWIERDZAM')
        ok('walki' in f.messages[-1],'combat refusal')
        f.combat_mob_key=None
        say('kopia 1 '+code1+' POTWIERDZAM')
        ok('Brak materiałów' in f.messages[-1],'materials preflight refused')
        ok(equipped_copy(c,1,'body',CAT)[2]==0,'missing materials no evolution')
        mat=required_materials(1)
        for iid,qty in mat.items():
            c.execute('INSERT INTO profession_storage VALUES(?,?,?,?)',(1,'craftbox',iid,qty*4))
        c.commit()
        say('kopia 1 '+code1+' POTWIERDZAM')
        ok('Ewolucja 1/10' in f.messages[-1],'successful evolution status')
        ok('Konstytucji +' in f.messages[-1] and 'obrona +' in f.messages[-1],'NVDA bonus status')
        ok(equipped_copy(c,1,'body',CAT)[2]==1,'specific physical stage updated')
        ok(equipped_copy(c,1,'secondary',CAT)[2]==0,'second identical copy unchanged')
        ok(f._read_only_equipment_cache_v1262 is None,'stat cache invalidated')
        ok(all(c.execute('SELECT quantity FROM profession_storage WHERE account_id=1 AND item_id=?',
                         (iid,)).fetchone()[0]==qty*3 for iid,qty in mat.items()),'exact material cost')
        say('kopia lista')
        ok('Etap 1/10' in f.messages[-2] and 'Etap 0/10' in f.messages[-1],
           'after upgrade list reads stages of two copies')
        # Crash the second evolution after material mutation; savepoint must revert.
        next_mat=required_materials(2)
        for iid,qty in next_mat.items():
            c.execute('INSERT OR REPLACE INTO profession_storage VALUES(?,?,?,?)',
                      (1,'craftbox',iid,qty*2))
        c.execute('CREATE TRIGGER stop_copy_upgrade BEFORE UPDATE ON v106_item_instances '
                  "WHEN NEW.evolution_stage=2 BEGIN SELECT RAISE(ABORT,'test-stop'); END")
        before=list(c.execute('SELECT item_id,quantity FROM profession_storage WHERE account_id=1 ORDER BY item_id'))
        try:say('kopia 1 '+code1+' POTWIERDZAM')
        except sqlite3.IntegrityError:ok(True,'SQLite injected error is observable')
        else:raise AssertionError('SQL trigger error hidden')
        ok('błąd SQLite' in f.messages[-1],'NVDA error after rollback')
        ok(equipped_copy(c,1,'body',CAT)[2]==1,'failed SQL reverted physical stage')
        after=list(c.execute('SELECT item_id,quantity FROM profession_storage WHERE account_id=1 ORDER BY item_id'))
        ok([(r[0],r[1]) for r in before]==[(r[0],r[1]) for r in after],
           'failed SQL reverted all materials')
        c.execute('DROP TRIGGER stop_copy_upgrade')
        # Corrupt legacy slot: no command should charge resources on drift.
        c.execute("UPDATE equipment SET item_id='mismatch' WHERE account_id=1 AND slot='body'")
        say('kopia 1 '+code1+' POTWIERDZAM')
        ok('niespójny rejestr' in f.messages[-1],'slot drift preflight fail closed')
        c.execute("UPDATE equipment SET item_id='test_haldor_armor' WHERE account_id=1 AND slot='body'")
        os.environ.pop('SOULBOUND_V106_STAGING')
        try:say('kopia lista')
        except PermissionError:ok(True,'staging environment required')
        else:raise AssertionError('missing staging flag allowed')
        os.environ['SOULBOUND_V106_STAGING']='1'
        db._v106_shadow_slots_disposable_copy=False
        try: _ = __import__('systems.equipment_evolution_command_v10600',fromlist=['_worn_armor'])._worn_armor(db,1)
        except PermissionError:ok(True,'disposable DB marker required')
        else:raise AssertionError('copy marker ignored')
        ok(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        return checks
    finally:
        c.close()
        if previous is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=previous

if __name__=='__main__':print('V106 HALDOR COPY EVOLUTION COMMAND:',run(),'PASS')
