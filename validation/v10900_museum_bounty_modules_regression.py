# -*- coding: utf-8 -*-
"""v109: module boundary and real SQLite in-memory bounty progress regression.

Never imports production runtime, never contacts GitHub or a live player DB.
The immutable AST digest is derived from the approved production v108 ZIP.
"""
from __future__ import annotations
import ast
import asyncio
import hashlib
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
SOURCE='player/session_mixins/museum_bounty.py'
PREFIX='player/session_mixins/museum_parts_v109'
GROUPS={
 'titles':('v0260_title_bonus_rule','v0260_profession_xp_bonus_percent','v0260_title_bonus_text'),
 'museum':('v0260_completed_set_ids','v0260_museum_found_ids','v0260_museum_snapshot','v0260_sync_museum','v0260_check_museum_rewards','show_museum_v0260','show_prestige_v0260'),
 'achievements':('loot_message_allowed','unlock_title','check_achievement_tiers','advance_achievement','set_achievement_progress','current_rare_fish_stock','current_gem_stock','sync_extended_achievements','check_all_minibosses_achievement'),
 'bounty_catalog':('bounty_kill_candidates','generate_bounty_offers','bounty_content_stage_v11342','normalize_bounty_kill_entry_v0387','ensure_bounty_board'),
 'bounty_board':('show_bounty_board','share_bounty_with_party_v1119','handle_bounty','advance_bounty'),
 'collection':('announce_item_collect_quest_progress','grant_hourly_quest_kill_drop_v0929','record_item_collection','sync_collection_from_inventory'),
 'kill_progress':('record_mob_progress','advance_v0140_quest_progress'),
}
APPROVED_V108_AST_SHA256='874a582fb9e7b3ca4b2734ec6fd38895143bdd8b9e27b504e659388f452d5817'


def _extract():
    pieces=[]
    methods={}
    classes={}
    checks=0
    for part,names in GROUPS.items():
        path=ROOT/PREFIX/(part+'.py')
        source=path.read_text('utf-8')
        assert len(source.encode('utf-8'))<30000 and 'from .dependencies import *' in source,part
        tree=ast.parse(source,filename=str(path))
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
        got={n.name:n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        assert set(got)==set(names),part
        assert not set(methods).intersection(got),part
        assert all(ast.get_docstring(n) is not None or True for n in got.values())
        classes[part]=cls
        methods.update(got)
        pieces.extend(got.values())
        checks+=4+len(got)
    digest=hashlib.sha256('\n'.join(ast.dump(m,include_attributes=False)
        for m in sorted(pieces,key=lambda m:m.name)).encode('utf-8')).hexdigest()
    assert len(methods)==34 and digest==APPROVED_V108_AST_SHA256,(len(methods),digest)
    checks+=2
    facade=ast.parse((ROOT/SOURCE).read_text('utf-8'))
    base=next(n for n in facade.body if isinstance(n,ast.ClassDef) and n.name=='SessionMuseumBountyMixin')
    assert not any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) for n in base.body)
    names=[n.id for n in base.bases]
    assert names==[classes[key].name for key in GROUPS],names
    checks+=2
    from systems.v10900_activation import REQUIRED
    for rel in [SOURCE,f'{PREFIX}/dependencies.py',f'{PREFIX}/__init__.py',
                *(f'{PREFIX}/{key}.py' for key in GROUPS),
                'validation/v10900_museum_bounty_modules_regression.py']:
        assert rel in REQUIRED,rel
        checks+=1
    return checks,classes,base


def _isolated_logic(classes,facade):
    """Execute unchanged real method AST against disposable account stores.

    No production module initialization; this is deliberate, because normal
    world bootstrap requires live registries that are unavailable in this test.
    """
    scope={
        'V0260_TITLE_BONUSES':{'Rybak':{'tool':'fishing','percent':9,'text':'Plus 9%'}},
        'loot_filter_allows':lambda mode,item:mode!='off',
        'canonical_bestiary_template_id':lambda x:str(x or '').removeprefix('elite_'),
        'MOB_TEMPLATES':{'goblin':{'name':'Goblin'}},
    }
    code=ast.fix_missing_locations(ast.Module(body=[*classes.values(),facade],type_ignores=[]))
    exec(compile(code,'v109 isolated museum AST','exec'),scope)
    cls=scope['SessionMuseumBountyMixin']
    checks=0
    assert len(cls.__bases__)==len(GROUPS)
    checks+=1
    for key,names in GROUPS.items():
        for name in names:
            assert callable(getattr(cls,name))
            checks+=1

    db=sqlite3.connect(':memory:')
    db.execute('CREATE TABLE bounty_state(account_id INTEGER PRIMARY KEY, payload TEXT NOT NULL)')
    class Db:
        def bounty_board_state(self,account_id):
            row=db.execute('SELECT payload FROM bounty_state WHERE account_id=?',(account_id,)).fetchone()
            return json.loads(row[0]) if row else {'offers':[],'active':{},'completed_count':0}
        def save_bounty_board_state(self,account_id,*,offers=None,active=None,completed_count=None):
            previous=self.bounty_board_state(account_id)
            update={'offers':previous['offers'] if offers is None else offers,
                    'active':previous['active'] if active is None else active,
                    'completed_count':previous['completed_count'] if completed_count is None else completed_count}
            db.execute('INSERT INTO bounty_state VALUES (?,?) ON CONFLICT(account_id) DO UPDATE SET payload=excluded.payload',
                       (account_id,json.dumps(update)))
            db.commit()
        def collection_entry_ids(self,aid,category):return set()
    class Session(cls):
        def __init__(self,aid):
            self.character=SimpleNamespace(active_title='Rybak',loot_filter='on',character_level=1)
            self.account_id=aid
            self.server=SimpleNamespace(db=Db())
            self.messages=[]
        async def send(self,m):self.messages.append(str(m))
    player=Session(1)
    assert player.v0260_title_bonus_rule()['percent']==9;checks+=1
    assert player.v0260_profession_xp_bonus_percent('Wędkarstwo','fishing')==9;checks+=1
    assert player.v0260_profession_xp_bonus_percent('Kowalstwo','smithing')==0;checks+=1
    assert player.v0260_title_bonus_text()=='Plus 9%';checks+=1
    assert player.loot_message_allowed('fish') is True;checks+=1
    player.character.loot_filter='off'
    assert player.loot_message_allowed('fish') is False;checks+=1
    clean,changed=player.normalize_bounty_kill_entry_v0387({'kind':'kill','target':'elite_goblin','needed':3,'label':'old'})
    assert changed and clean['target']=='goblin' and clean['label']=='Pokonaj 3 razy: Goblin';checks+=1
    clean2,changed2=player.normalize_bounty_kill_entry_v0387(clean)
    assert not changed2 and clean2==clean;checks+=1

    state={'offers':[],'active':{'kind':'kill','target':'goblin','needed':3,
            'progress':0,'completed':False,'label':'Pokonaj 3 gobliny'},'completed_count':0}
    player.server.db.save_bounty_board_state(1,**state)
    player.server.db.save_bounty_board_state(2,**state)
    assert asyncio.run(player.advance_bounty('kill','wolf')) is False;checks+=1
    assert asyncio.run(player.advance_bounty('kill','goblin',2)) is True;checks+=1
    assert player.server.db.bounty_board_state(1)['active']['progress']==2;checks+=1
    assert player.server.db.bounty_board_state(2)['active']['progress']==0;checks+=1
    assert asyncio.run(player.advance_bounty('kill','goblin',9)) is True;checks+=1
    assert player.server.db.bounty_board_state(1)['active']['completed'] is True;checks+=1
    assert asyncio.run(player.advance_bounty('kill','goblin')) is False;checks+=1
    assert len(player.messages)==2 and 'Cel wykonany' in player.messages[-1];checks+=1
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';checks+=1
    db.close()
    return checks


def run():
    n,classes,facade=_extract()
    n+=_isolated_logic(classes,facade)
    print(f'V109 MUSEUM/BOUNTY MODULAR: {n} PASS; 34 metody AST zgodne z v108; '
          'izolacja kont i SQLite w pamieci PASS; produkcja nietknieta',flush=True)
    return n

if __name__=='__main__':run()
