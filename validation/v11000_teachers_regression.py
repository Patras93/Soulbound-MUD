# -*- coding: utf-8 -*-
"""v110: actual private server, eight independent teachers and native learn.

No production database or port can be used. This file exercises an unprimed
runtime (no preliminary import of core.classes_skills), complementing the
preloaded-catalogue smoke test in v11000_server_smoke.
"""
from __future__ import annotations
import asyncio
import os
from pathlib import Path
import socket
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
sys.path.insert(0,str(ROOT))


def main():
    with tempfile.TemporaryDirectory(prefix='sb110_teachers_') as scratch:
        with socket.socket() as candidate:
            candidate.bind(('127.0.0.1',0))
            port=candidate.getsockname()[1]
        for key in ('SOULBOUND_DB','SOULBOUND_HOST','SOULBOUND_PORT',
                    'PORT','RAILWAY_TCP_APPLICATION_PORT'):
            os.environ.pop(key,None)
        os.environ.update(SOULBOUND_DB=str(Path(scratch)/'teachers.sqlite'),
            SOULBOUND_HOST='127.0.0.1',SOULBOUND_PORT=str(port),
            SOULBOUND_V107_STAGING='1',SOULBOUND_V109_STAGING='1',
            SOULBOUND_V110_STAGING='1')
        # Critical: do NOT preload core.classes_skills before native bootstrap.
        import server
        from core.archetypes.expansion import CLASS_SPECS
        from core.classes_skills import CLASSES,RACES,CLASS_SKILLS
        from player.session_mixins.io_auth_character import CLASSES as CREATOR_CLASSES
        from validation.v3004_teacher_learn import _Session
        from validation.v5001_learn_available import audit_v5001_learn_available

        assert len(CLASSES)==len(RACES)==38
        assert CREATOR_CLASSES is CLASSES
        seen_rooms=set()
        count=0
        for row in CLASS_SPECS:
            name=row[0]
            matches=[(ident,npc) for ident,npc in server.NPCS.items()
                     if npc.get('teacher_class')==name]
            assert len(matches)==1, (name,matches)
            ident,teacher=matches[0]
            assert ident.startswith('v11000_realm_')
            assert teacher['room'] in server.ROOMS
            assert teacher['room'] not in seen_rooms
            seen_rooms.add(teacher['room'])
            s=_Session(name,teacher['room'],[name],level=1)
            found,found_teacher=s.teacher_here_for_active_class()
            assert found==ident and found_teacher is teacher
            asyncio.run(s.learn_class_skill(''))
            assert any('Lekcja klasy '+name in text for text in s.messages),name
            first=CLASS_SKILLS[name][0]
            assert first['unlock']==1
            asyncio.run(s.learn_class_skill('1'))
            assert first['id'] in s.server.db.known,name
            assert len(s.pay_calls)==1 and len(s.server.db.learn_calls)==1,name
            s.character.room_id='temple_spawn'
            asyncio.run(s.learn_class_skill('1'))
            assert len(s.server.db.learn_calls)==1,name
            count+=8
        count+=audit_v5001_learn_available()
        server._BOOT_SOCKET.close()
        print('V110 TEACHERS PASS: 8 classes, 8 unique NPC teachers, '
              f'8 real learn paths; {count} checks including v5001; '
              'cold boot on localhost, disposable SQLite only',flush=True)


if __name__=='__main__':main()
