# -*- coding: utf-8 -*-
"""v12.00.1 real EXP curves, quality, all 22 professions/tools, board safety."""
from __future__ import annotations
from types import SimpleNamespace


def run_regression():
    from systems.profession_exp_pacing_v1201 import improved_work_xp
    from systems.profession_projects_v1200 import PROJECTS
    from core.progression_resources import v0190_requirement
    from config.balance import profession_xp_requirement_v1401, tool_xp_requirement_v1402
    from systems.new_professions import PROFESSIONS as NEW_PROFESSIONS
    import server  # initialize historical world globals before importing world state
    from player.session_mixins import museum_bounty as module
    from player.session_mixins.museum_bounty import SessionMuseumBountyMixin
    checks=0
    assert len(PROJECTS)==22
    checks+=1
    for profession,project in PROJECTS.items():
        tool=project.tool
        for level in (1,25,50,100,200,400,600,799):
            pro_req=profession_xp_requirement_v1401(v0190_requirement('profession',level),profession,level)
            tool_req=tool_xp_requirement_v1402(v0190_requirement('tool',level),tool,level)
            for raw,required,kind in ((100,pro_req,False),(15,tool_req,True)):
                easy=improved_work_xp(raw,required,level,1,tool=kind)
                normal=improved_work_xp(raw,required,level,level,tool=kind)
                hard=improved_work_xp(raw,required,level,min(800,level+40),tool=kind)
                untagged=improved_work_xp(raw,required,level,None,tool=kind)
                assert easy>=raw and normal>=easy and hard>=normal, (profession,level,kind,raw,required,easy,normal,hard)
                assert untagged >= raw
                assert untagged == raw*(4 if kind else 2)
                assert improved_work_xp(0,required,level,level,tool=kind)==0
                checks+=5
                if level>=100:
                    # Higher-level real work progresses in thousands, not
                    # tens/hundreds of thousands of identical actions.
                    assert normal*2500 >= required, (profession,level,kind,normal,required)
                    checks+=1
                if level>=200:
                    # Trivial material must not gain level-appropriate awards.
                    assert easy < normal
                    checks+=1
    # Strict level filter, preserving familiar names and boss exclusions.
    old={name:getattr(module,name) for name in
         ('BESTIARY_CATALOG','MOB_TEMPLATES','BESTIARY_SPAWN_ROOMS',
          'BOSS_COLLECTION_CATALOG','v0863_is_boss_template')}
    try:
        module.BESTIARY_CATALOG={'rat','bandit','elite','dragon','fake_boss'}
        module.MOB_TEMPLATES={
            'rat':{'name':'Szczur','generator_level':1},
            'bandit':{'name':'Bandyta','generator_level':39},
            'elite':{'name':'Zbyt silny','generator_level':500},
            'dragon':{'name':'Smok','generator_level':200},
            'fake_boss':{'name':'Boss','generator_level':41,'mini_boss':True},
        }
        module.BESTIARY_SPAWN_ROOMS={name:['room'] for name in module.BESTIARY_CATALOG}
        module.BOSS_COLLECTION_CATALOG=set()
        module.v0863_is_boss_template=lambda row:bool(row.get('mini_boss'))
        person=SessionMuseumBountyMixin.__new__(SessionMuseumBountyMixin)
        person.character=SimpleNamespace(character_level=40)
        assert person.bounty_kill_candidates()==[('bandit','Bandyta')]
        checks+=1
        person.character.character_level=1
        assert person.bounty_kill_candidates()==[('rat','Szczur')]
        checks+=1
        person.character.character_level=350
        found=person.bounty_kill_candidates()
        assert found and all(k in ('dragon',) for k,_ in found)
        checks+=1
    finally:
        for name,value in old.items():setattr(module,name,value)
    # Saved active board with progress is never rewritten at a level change.
    class FakeDB:
        def __init__(self,active=None):
            self.state={'offers':[{'board_band':1,'kind':'kill','target':'rat','needed':8}],
                        'active':active or {},'completed_count':3}
            self.written=[]
        def bounty_board_state(self,account_id):
            return dict(self.state)
        def save_bounty_board_state(self,account_id,**kwargs):
            self.written.append(kwargs)
    person=SessionMuseumBountyMixin.__new__(SessionMuseumBountyMixin)
    person.account_id=42
    person.character=SimpleNamespace(character_level=51)
    db=FakeDB({'kind':'mine','progress':4,'needed':10})
    person.server=SimpleNamespace(db=db)
    person.generate_bounty_offers=lambda:[{'board_band':5,'kind':'mine','needed':8}]
    state=person.ensure_bounty_board()
    assert state['active']['progress']==4 and not db.written
    checks+=1
    db.state['active']={}
    state=person.ensure_bounty_board()
    assert state['offers'][0]['board_band']==5
    assert db.written[0]['active']=={}
    checks+=2
    return checks


if __name__=='__main__':
    print('v12.00.1 EXP 22 PROF / 22 TOOLS / BOARD:',run_regression(),'checks PASS')
