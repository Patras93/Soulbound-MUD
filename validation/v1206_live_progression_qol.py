# -*- coding: utf-8 -*-
"""v12.00.6: runtime OLC EXP and NVDA reply/look/combat completion tests."""
import asyncio
import copy
import sqlite3
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as Obj
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def run_regression():
    import server  # initialize canonical world catalog extensions before session mixins
    from systems.live_content_v1204 import LiveContentV1204
    from systems.live_progression_v1206 import (
        PROFESSION_XP_PERCENT, TOOL_XP_PERCENT, xp_with_live_bonus, install)
    from core.bootstrap_economy_professions import PROFESSION_RANK_NAMES, TOOL_PROFESSION_MAP
    from core.classes_skills import CLASS_SKILLS
    from player.session_mixins.social_base import SessionBaseSocialMixin
    from player.session_mixins.combat_rewards import deferred_kill_commits_v11125
    from player.session import Session

    count = 0
    original_skills = {name: list(rows) for name, rows in CLASS_SKILLS.items()}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            conn = sqlite3.connect(str(Path(tmp) / 'olc.db'))
            conn.row_factory = sqlite3.Row
            world = Obj(mobs={}, _last_refresh_at=0.0,
                        _register_runtime_spawn=lambda *_: None)
            server = Obj(world=world, sessions=[])
            service = LiveContentV1204(Obj(conn=conn))
            original_all = copy.deepcopy(service.active)
            try:
                for profession in PROFESSION_RANK_NAMES:
                    service.stage_edit('profesja', profession, 'xp_percent', '220')
                    count += 1
                for tool in TOOL_PROFESSION_MAP:
                    service.stage_edit('narzedzie', tool, 'xp_percent', '210')
                    count += 1
                skill = next(row for rows in CLASS_SKILLS.values() for row in rows
                             if 'mana' in row and isinstance(row['mana'], int))
                skill_id = skill['id']
                old_mana = skill['mana']
                new_mana = old_mana + 1
                service.stage_edit('skill', skill_id, 'mana', str(new_mana))
                count += 1
                service.validate(service.draft); count += 1
                # Only author-approved positive values, no XP creation from zero.
                assert xp_with_live_bonus(100,'Jubilerstwo') == 100; count += 1
                assert 'rewizję 1' in service.apply(server, 'admin'); count += 1
                for profession in PROFESSION_RANK_NAMES:
                    assert xp_with_live_bonus(100, profession) == 220
                    count += 1
                for tool in TOOL_PROFESSION_MAP:
                    assert xp_with_live_bonus(100, tool, tool=True) == 210
                    count += 1
                assert xp_with_live_bonus(0, 'Jubilerstwo') == 0; count += 1
                assert any(row['id'] == skill_id and row['mana'] == new_mana
                           for rows in CLASS_SKILLS.values() for row in rows); count += 1
                # Persistence through the same shared SQLite database.
                second = LiveContentV1204(Obj(conn=conn))
                assert second.active['profession_edits']['Jubilerstwo']['xp_percent'] == 220; count += 1
                assert second.active['tool_edits'][next(iter(TOOL_PROFESSION_MAP))]['xp_percent'] == 210; count += 1
                second._remove(world)
                service._remove(world)
                service._install(original_all, world)
                assert xp_with_live_bonus(100,'Jubilerstwo') == 100; count += 1
                assert any(row['id'] == skill_id and row['mana'] == old_mana
                           for rows in CLASS_SKILLS.values() for row in rows); count += 1
                # Skills cannot change in the middle of an engaged mob fight.
                service.draft = copy.deepcopy(service.active)
                service.stage_edit('skill', skill_id, 'mana', str(new_mana+1))
                fighter = Obj(room_id='temple_basement',home_room_id='temple_basement',
                              template_id='temple_rat',alive=True,engaged_by='Knight',aoe_engaged_by=None)
                world.mobs['fighter'] = fighter
                try:
                    service.apply(server,'admin')
                except ValueError as exc:
                    assert 'walk' in str(exc); count += 1
                else:
                    raise AssertionError('Skill changed while in battle')
                world.mobs.clear()
            finally:
                service._remove(world)
                conn.close()

        async def checks_async():
            checked = 0
            sends = []
            server = Obj(find_character_session=lambda name: None)
            own = Obj(last_private_sender_name=None, character=Obj(name='Sender'),
                      server=server, sent_messages=[])
            async def send(msg, **kw): sends.append(msg)
            async def tell(text): sends.append('TELL:' + text); return True
            own.send = send; own.tell = tell
            await SessionBaseSocialMixin.reply_private_v0928(own, 'ping')
            assert not any('REPLY:' in m for m in sends); checked += 1
            recipient = Obj(closed=False,character=Obj(name='Friend'))
            server.find_character_session = lambda name: recipient if name == 'Friend' else None
            own.last_private_sender_name = 'Friend'
            sends.clear()
            await SessionBaseSocialMixin.reply_private_v0928(own, 'Cześć!')
            assert sends == ['TELL:Friend Cześć!','REPLY: odpowiedź wysłana do Friend.']; checked += 1
            recipient.closed = True
            sends.clear()
            await SessionBaseSocialMixin.reply_private_v0928(own, 'Cześć!')
            assert not any('REPLY:' in m for m in sends); checked += 1

            # Actual bound `look_at_player` method, two real party membership states.
            msgs = []
            actor = Obj(party_key=lambda: 5, send=None)
            async def actor_send(msg): msgs.append(msg)
            actor.send = actor_send
            char = Obj(name='Archer', race='Elf', class_name='Łucznik', soul_level=1,
                       soul_tier=1, soul_weapon='Łuk', active_title=None,
                       active_class_names=lambda: ['Łucznik'])
            player = Obj(character=char, party_key=lambda:5, is_downed_v0371=lambda:True)
            await Session.look_at_player(actor, player)
            assert any('POWALONY' in msg for msg in msgs); checked += 1
            player.party_key=lambda:6
            msgs.clear()
            await Session.look_at_player(actor, player)
            assert not any('POWALONY' in msg for msg in msgs); checked += 1

            # Combat finish for solo, AoE and shared party. Use actual decorated
            # kill wrapper with the production callback/deferral infrastructure.
            from contextlib import nullcontext
            clear = Obj(conn=Obj(deferred_commits=lambda: nullcontext()))
            members=[]
            enemy1=Obj(room_id='crypt',alive=True,engaged_by='Hero',aoe_engaged_by='Hero',engaged_at=10.0,v1400_kill_in_progress=False)
            enemy2=Obj(room_id='crypt',alive=True,engaged_by='Hero',aoe_engaged_by='Hero',engaged_at=10.0,v1400_kill_in_progress=False)
            for name in ('Hero','Ally'):
                e=Obj(character=Obj(name=name,room_id='crypt'),closed=False,server=None,
                      account_id=name,msgs=[])
                async def push(msg, **kw): e.msgs.append((msg,kw))
                # default-argument closure needed to avoid binding last member
                async def push(msg,*,_member=e,**kw): _member.msgs.append((msg,kw))
                e.send=push
                members.append(e)
            party_server=Obj(db=clear,world=Obj(mobs={'e1':enemy1,'e2':enemy2}),
                             party_sessions=lambda _account,same_room=None: members)
            for member in members: member.server=party_server
            async def simulated_kill(_,mob): mob.alive=False
            wrapped=deferred_kill_commits_v11125(simulated_kill)
            await wrapped(members[0],enemy1)
            assert not members[0].msgs and not members[1].msgs; checked += 1
            await wrapped(members[0],enemy2)
            assert all(len(m.msgs)==1 for m in members); checked += 1
            assert all('KONIEC WALKI' in m.msgs[0][0] and m.msgs[0][1]['combat_detail']=='essential'
                       for m in members); checked += 1
            await wrapped(members[0],enemy2)
            assert all(len(m.msgs)==1 for m in members); checked += 1
            # No success message if the player fled and aggro was released.
            enemy3=Obj(room_id='crypt',alive=True,engaged_by=None,aoe_engaged_by=None,engaged_at=0.0,
                       v1400_kill_in_progress=False)
            party_server.world.mobs['e3']=enemy3
            await wrapped(members[0],enemy3)
            assert all(len(m.msgs)==1 for m in members); checked += 1
            enemy4=Obj(room_id='crypt',alive=True,engaged_by='Hero',aoe_engaged_by=None,
                       engaged_at=__import__('time').monotonic()+1.0,v1400_kill_in_progress=False)
            party_server.world.mobs['e4']=enemy4
            await wrapped(members[0],enemy4)
            assert all(len(m.msgs)==2 for m in members); checked += 1
            return checked
        count+=asyncio.run(checks_async())
        # Confirm look in the room enumerates downed *party*, not strangers.
        source=(Path(__file__).resolve().parents[1] / 'player/session_methods_v4200/perceptionmaps_part02.py').read_text('utf8')
        assert 'session.is_downed_v0371()' in source and 'session.party_key() == _my_party' in source
        count += 1
        assert len(PROFESSION_RANK_NAMES) == 22 and len(TOOL_PROFESSION_MAP) == 22
        count += 1
    finally:
        install({}, {})
        CLASS_SKILLS.clear()
        CLASS_SKILLS.update(original_skills)
    return count

if __name__=='__main__':
    print('V12.00.6 OLC EXP / REPLY / LOOK / KONIEC WALKI:',run_regression(),'checks PASS')
