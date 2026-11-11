# -*- coding: utf-8 -*-
"""Modularny serwer v109: kod metod bez zmian + izolowane testy sesji/aggro.

Nie uruchamia sieci, nie uruchamia serwera i nie otwiera bazy graczy.
"""
from __future__ import annotations
import ast
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace
from server_parts_v109 import MudSessionsV109Mixin, MudPartyMembersV109Mixin, MudEngagementV109Mixin

ROOT=Path(__file__).resolve().parents[1]
GROUPS={
 'sessions':('account_online','session_by_master_account','find_character_session','session_by_account'),
 'party_members':('party_key_for_account','same_party','clear_party_protector_for_account','party_protector_session','party_sessions','party_engaged_mobs','party_combat_targets','party_combat_target'),
 'engagement':('sanitize_mob_engagement','release_all_engagements_for_session','engagement_allowed','reassign_mob_engagement','session_engaged_mobs'),
}
V108_AST_SHA256='c37fac6a459eba177ef9bc58a2453ee1d5d829e8d811116bf3193c44a19d26d3'


def _check_sources():
    methods=[]
    for filename,names in GROUPS.items():
        file=ROOT/'server_parts_v109'/f'{filename}.py'
        tree=ast.parse(file.read_text(encoding='utf-8-sig'))
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
        got={n.name:n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        assert set(got)==set(names),filename
        methods.extend(got.values())
    h=hashlib.sha256('\n'.join(ast.dump(n,include_attributes=False)
                               for n in sorted(methods,key=lambda m:m.name)).encode()).hexdigest()
    assert h==V108_AST_SHA256,('Metody zmienione względem zatwierdzonej v108',h)
    source=(ROOT/'server/mud_server.py').read_text(encoding='utf-8-sig')
    tree=ast.parse(source)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='MudServer')
    own={n.name for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    assert not own.intersection({n for names in GROUPS.values() for n in names})
    for must_stay in ('__init__','run','handle_client','party_nearby_broadcast','broadcast_room','broadcast_all'):
        assert must_stay in own
    spec=spec_from_file_location('sb_v109_modular_server_audit',ROOT/'server/mud_server.py')
    module=module_from_spec(spec)
    spec.loader.exec_module(module)
    assert {group.__name__ for group in module.MudServer.__mro__}.issuperset({
        MudSessionsV109Mixin.__name__,MudPartyMembersV109Mixin.__name__,MudEngagementV109Mixin.__name__})
    return len(methods)+6+1+1


def _session(aid,name,room='start',hp=100,*,master=None,guardian=False):
    char=SimpleNamespace(name=name,room_id=room,has_active_class=lambda value:guardian and value=='Strażnik')
    return SimpleNamespace(account_id=aid,master_account_id=master or aid,character=char,
                           closed=False,current_hp=hp,combat_mob_key=None)


def _mob(key,name,room='start'):
    return SimpleNamespace(key=key,engaged_by=name,aoe_engaged_by=None,room_id=room,
        alive=True,engaged_at=10.0,combat_turn=3,player_hits=3)


class Subject(MudSessionsV109Mixin,MudPartyMembersV109Mixin,MudEngagementV109Mixin):
    def __init__(self):
        self.a=_session(1,'Ala')
        self.b=_session(2,'Borys',guardian=True)
        self.c=_session(3,'Cezary',room='other')
        self.d=_session(4,'Daria')
        self.sessions=[self.a,self.b,self.c,self.d]
        self.parties={1:{1,2,3}}
        self.party_protectors={1:2}
        self.mobs=[]
        self.world=SimpleNamespace(mobs={},room_mobs=lambda rid:[m for m in self.mobs if m.room_id==rid])
        self.resets=[]
    def reset_adaptive_mob_encounter_v11330(self,mob):self.resets.append(mob.key)


def _test_behaviour():
    checks=0
    s=Subject()
    assert s.account_online(1) and s.session_by_master_account(2) is s.b;checks+=2
    assert s.find_character_session('bOrYs') is s.b and s.session_by_account(4) is s.d;checks+=2
    assert s.party_key_for_account(3)==1 and s.party_key_for_account(4) is None;checks+=2
    assert s.same_party(1,2) and not s.same_party(1,4);checks+=2
    assert set(x.account_id for x in s.party_sessions(1,'start'))=={1,2};checks+=1
    assert [x.account_id for x in s.party_sessions(4)]==[4];checks+=1
    mob=_mob('rat','Ala')
    assert s.party_protector_session(1) is s.b;checks+=1
    assert s.party_combat_targets(s.a,mob)==[s.b];checks+=1
    s.party_protectors={}
    assert [x.account_id for x in s.party_combat_targets(s.a,mob)]==[1,2];checks+=1
    assert s.party_combat_target(s.a,mob) is s.a;checks+=1
    s.mobs=[mob];s.world.mobs={'rat':mob}
    s.a.combat_mob_key='rat'
    assert s.sanitize_mob_engagement(mob) is s.a;checks+=1
    assert s.engagement_allowed(s.b,mob) and not s.engagement_allowed(s.d,mob);checks+=2
    assert s.party_engaged_mobs(s.b)==[mob];checks+=1
    assert s.session_engaged_mobs(s.a)==[mob];checks+=1
    s.b.combat_mob_key='rat'
    assert s.release_all_engagements_for_session(s.a)==1 and mob.engaged_by=='Borys';checks+=2
    s.b.combat_mob_key=None
    s.a.combat_mob_key=None
    s.a.closed=True
    assert s.sanitize_mob_engagement(mob) is None and mob.engaged_by is None
    assert s.resets==['rat'];checks+=2
    assert s.clear_party_protector_for_account(2) is False;checks+=1
    s.party_protectors={1:2}
    assert s.clear_party_protector_for_account(2) and s.party_protectors=={};checks+=1
    s.c.closed=True
    assert s.session_by_account(3) is s.c
    assert s.session_by_master_account(3) is None
    checks+=2
    return checks


def run():
    source=_check_sources()
    behaviour=_test_behaviour()
    return source+behaviour


if __name__=='__main__':
    print('V109 MODULY SERWERA:',run(),'checks PASS; bez bazy produkcyjnej')
