# -*- coding: utf-8 -*-
"""v109: destructive admin WIPE guarded, simulated session only."""
from __future__ import annotations
import asyncio
from types import SimpleNamespace
from player.session_mixins.admin_tools import SessionAdminToolsMixin

def run():
    checks=0
    class DB:
        def __init__(self):
            self.calls=0
            self.conn=SimpleNamespace(execute=lambda _: SimpleNamespace(fetchall=lambda: [{"id":1},{"id":2}]))
        def wipe_characters_for_master(self,aid):self.calls+=1;return 2
        def wipe_all_characters_preserve_accounts(self):self.calls+=1;return 3,2
    class S(SessionAdminToolsMixin):
        def __init__(self,owner=True):
            self.owner=owner;self.master_account_id=1;self.account_id=3
            self.server=SimpleNamespace(db=DB(),sessions=[self],parties={},party_invites={},
                party_protectors={},party_goals={},party_routes_v1193={},party_ready_checks={})
            self.messages=[];self.prepared=0;self.selection=0;self.world_entered=0
        def is_admin(self):return self.owner
        def normalize_description_query(self,a):return str(a or '').strip().casefold()
        async def send(self,a):self.messages.append(str(a))
        async def prepare_character_wipe(self):self.prepared+=1
        async def character_selection_flow(self):self.selection+=1;return True
        async def enter_world(self):self.world_entered+=1
    async def main():
        nonlocal checks
        admin=S();guest=S(False)
        await guest.wipe_command('moje postacie POTWIERDZAM')
        assert guest.server.db.calls==0 and guest.prepared==0 and 'Nieznana komenda' in guest.messages[-1];checks+=1
        for cmd in ('moje postacie','wszystkie postacie','moje postacie potwierdzam xxx','nieprawidlowe potwierdzam'):
            await admin.wipe_command(cmd)
            assert admin.server.db.calls==0 and admin.prepared==0,cmd
            checks+=1
        await admin.wipe_command('moje postacie POTWIERDZAM')
        assert admin.server.db.calls==1 and admin.prepared==1;checks+=1
        assert admin.selection==1 and admin.world_entered==1;checks+=1
        assert any('Konta i hasła zachowane' in m for m in admin.messages);checks+=1
        another=S();await another.wipe_command('wszystkie postacie POTWIERDZAM')
        assert another.server.db.calls==1 and another.prepared==1;checks+=1
        # This never opens/changes a real database; DB is a call-counter stub.
    asyncio.run(main())
    return checks
if __name__=='__main__':print('V109 ADMIN WIPE:',run(),'PASS; synthetic only')
