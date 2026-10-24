# -*- coding: utf-8 -*-
"""Focused v52 level-cap regression tests (fully isolated temporary JSON)."""
import asyncio
import json
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace
from core import live_level_caps_v5200 as caps
from systems.admin_live_level_caps_v5200 import _handle, dispatch_v52_caps


def run():
    count=0
    def check(test,label=''):
        nonlocal count
        assert test,label
        count+=1
    with tempfile.TemporaryDirectory(prefix='v52_caps_') as d:
        old_path=caps.CAP_FILE
        old_state=dict(caps._state)
        old_loaded=caps._loaded
        caps.CAP_FILE=Path(d)/'live'/'admin_level_caps.json'
        try:
            defaults=caps.load()
            check(len(defaults)==10)
            for k in caps.KEYS:
                check(defaults[k]==caps.DEFAULTS[k],k)
                check(caps.can_grow(k,caps.DEFAULTS[k]-1))
                check(not caps.can_grow(k,caps.DEFAULTS[k]))
                check(caps.normalize_key(k)==k)
            check(not caps.CAP_FILE.exists())
            check('Postac 800' in _handle(''))
            check('Bieglosc klas' in _handle(''))
            check('bez limitu' in _handle('pomoc') or 'bezlimitu' in _handle('pomoc'))
            check(_handle('ustaw postac 1200').startswith('LIMITY PLAN:'))
            check(not caps.CAP_FILE.exists())
            check(caps.cap('postac')==800)
            resp=_handle('ustaw postac 1200 POTWIERDZAM')
            check('800 -> 1200' in resp)
            check(caps.cap('postac')==1200)
            check(caps.can_grow('postac',1100))
            check(not caps.can_grow('postac',1200))
            check(caps.CAP_FILE.exists())
            check(json.loads(caps.CAP_FILE.read_text())['caps']['postac']==1200)
            # Simulate a fresh process: disk state must survive cached-state loss.
            saved=dict(caps._state)
            caps._state.update(caps.DEFAULTS)
            check(caps.load()==saved)
            check('Postac' in _handle('postac'))
            check('bez limitu' in _handle('ustaw postac bezlimitu POTWIERDZAM'))
            check(caps.cap('postac') is None)
            check(caps.can_grow('postac',10**12))
            check(json.loads(caps.CAP_FILE.read_text())['caps']['postac'] is None)
            # XP thresholds must allow growth above the old static 800 barrier.
            from core import progression_resources as progress
            from player.character import Character
            from storage.db_progression import DatabaseProgressionMixin
            check(progress.character_xp_to_next(801)>0)
            check(progress.character_xp_to_next(1200)>0)
            check(progress.class_mastery_xp_to_next(801)==0) # still default 800
            check('1200' in _handle('ustaw bieglosc 1200 POTWIERDZAM'))
            check(progress.class_mastery_xp_to_next(801)>0)
            check('1200' in _handle('ustaw dusza 1200 POTWIERDZAM'))
            check(progress.soul_xp_to_next(801)>0)
            check('1200' in _handle('ustaw bron 1200 POTWIERDZAM'))
            check(progress.soul_weapon_mastery_xp_to_next(801)>0)
            check('1200' in _handle('ustaw skille 1200 POTWIERDZAM'))
            check(progress.skill_xp_to_next(801)>0)
            check('1200' in _handle('ustaw profesje 1200 POTWIERDZAM'))
            check('1200' in _handle('ustaw narzedzia 1200 POTWIERDZAM'))
            check('1200' in _handle('ustaw gildia 1200 POTWIERDZAM'))
            check(caps.cap('gildia')==1200)
            check('bez limitu' in _handle('wszystkie bezlimitu POTWIERDZAM'))
            for k in caps.KEYS:check(caps.cap(k) is None)
            check('800' in _handle('reset wszystko POTWIERDZAM'))
            for k in caps.KEYS:check(caps.cap(k)==caps.DEFAULTS[k])
            # Guard against clamping a pre-existing character when admin lowers cap.
            _handle('ustaw postac 100 POTWIERDZAM')
            dummy=SimpleNamespace(character_level=950,character_xp=9_999)
            check(Character.add_character_xp(dummy,2500)==[])
            check(dummy.character_level==950)
            check(dummy.character_xp==9999)
            _handle('ustaw bron 100 POTWIERDZAM')
            dummy2=SimpleNamespace(soul_weapon_mastery_level=950,soul_weapon_mastery_xp=125)
            result=Character.add_soul_weapon_mastery_xp(dummy2,1000)
            check(result['level']==950)
            check(dummy2.soul_weapon_mastery_xp==125)
            # DB write paths must never lower levels already earned.
            db=DatabaseProgressionMixin()
            db.conn=sqlite3.connect(':memory:')
            db.conn.row_factory=sqlite3.Row
            db.conn.executescript('''
                CREATE TABLE class_progress(account_id INTEGER,class_name TEXT,level INTEGER,xp INTEGER,active_slot INTEGER,
                    PRIMARY KEY(account_id,class_name));
                CREATE TABLE skill_progress(account_id INTEGER,skill_id TEXT,level INTEGER,xp INTEGER,uses INTEGER,
                    PRIMARY KEY(account_id,skill_id));
            ''')
            db.conn.execute("INSERT INTO class_progress VALUES (1,'Wojownik',900,100,1)")
            db.conn.execute("INSERT INTO skill_progress VALUES (1,'warrior_slash',950,125,10)")
            _handle('ustaw bieglosc 100 POTWIERDZAM')
            _handle('ustaw skille 100 POTWIERDZAM')
            rr=db.add_class_mastery_xp(1,'Wojownik',500)
            check(rr['level']==900)
            check(db.class_progress_row(1,'Wojownik')['xp']==100)
            check(rr['overflow_xp']==500)
            ss=db.add_skill_xp(1,'warrior_slash',200)
            check(ss['level']==950)
            check(db.skill_progress(1,'warrior_slash')['xp']==125)
            # File tampering is rejected without changing running limits.
            snap=caps.current()
            caps.CAP_FILE.write_text('{"schema":1,"caps":{"postac":-4}}')
            try:caps.load()
            except ValueError:check(True)
            else:check(False,'corrupt file accepted')
            check(caps.current()==snap)
            # Recover with a valid file and verify restart/reload persistence.
            caps._atomic_write(caps.DEFAULTS)
            check(caps.load()==caps.DEFAULTS)
            check(not any(x in str(caps.CAP_FILE) for x in ('soulbound.db','sqlite')))
            # Handler rejects non-admin and never mutates file.
            class Client:
                def __init__(self,yes):self.yes=yes;self.messages=[]
                def is_admin(self):return self.yes
                async def send(self,msg):self.messages.append(msg)
            player=Client(False)
            asyncio.run(dispatch_v52_caps(player,'ustaw postac 900 POTWIERDZAM'))
            check('Nieznana komenda' in player.messages[0])
            check(caps.cap('postac')==800)
            admin=Client(True)
            asyncio.run(dispatch_v52_caps(admin,'ustaw postac 900 POTWIERDZAM'))
            check(caps.cap('postac')==900)
            check('LIMITY ZAPISANO' in admin.messages[0])
            # A conflicting external file edit must not be silently overwritten.
            changed={k:800 for k in caps.KEYS}; changed['postac']=777
            caps._atomic_write(changed)
            try:_handle('ustaw postac 950 POTWIERDZAM')
            except ValueError:check(True)
            else:check(False,'stale settings allowed')
            check(caps.cap('postac')==900)
            check(caps.read_file()['postac']==777)
            check(caps.load()['postac']==777)
            # Invalid/broken confirmation does not write.
            for bad in ('ustaw postac abc','ustaw postac -5','ustaw postac 10000001','ustaw gildia 0','ustaw nieznane 800'):
                before=caps.CAP_FILE.read_bytes()
                try:_handle(bad)
                except ValueError as exc:check(isinstance(exc, ValueError), "invalid cap rejected")
                check(caps.CAP_FILE.read_bytes()==before,bad)
            from core.character_resources import character_hp_base, character_mana_base
            from core.player_math import skill_level_power
            baseline_hp=character_hp_base(800,175)
            check(character_hp_base(801,175)==baseline_hp)
            _handle('ustaw postac 1200 POTWIERDZAM')
            check(character_hp_base(801,175)>baseline_hp)
            check(character_mana_base(801,175,175)>character_mana_base(800,175,175))
            check(skill_level_power(801)==skill_level_power(800))
            _handle('ustaw skille 1200 POTWIERDZAM')
            check(skill_level_power(801)>skill_level_power(800))
            # Compatibility-bound server.py methods read cap globals from the
            # main server namespace, not always the source file namespace.
            import sys, types
            previous_server=sys.modules.get('server')
            simulated_server=types.ModuleType('server')
            simulated_server.__file__='C:\\Soulbound-MUD\\server.py'
            simulated_server.CHARACTER_MAX_LEVEL=800
            sys.modules['server']=simulated_server
            try:
                caps._apply_to_runtime()
                check(simulated_server.CHARACTER_MAX_LEVEL==1200)
                _handle('ustaw postac 1600 POTWIERDZAM')
                check(simulated_server.CHARACTER_MAX_LEVEL==1600)
            finally:
                if previous_server is None:sys.modules.pop('server',None)
                else:sys.modules['server']=previous_server
            db.conn.close()
        finally:
            caps.CAP_FILE=old_path
            caps._state.update(old_state)
            caps._loaded=old_loaded
            caps._apply_to_runtime()
    print(f'v52 admin live level caps: {count} PASS')
    return count


if __name__=='__main__':run()
