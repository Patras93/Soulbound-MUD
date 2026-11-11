# -*- coding: utf-8 -*-
"""v1.26.0: deterministic geology, durable mine, AI, trading, professions, expeditions."""
import os
import sqlite3
import tempfile
from types import SimpleNamespace

from core.mine_world_v1260 import (geology_v1260,mine_route_v1260,
                                   mine_map_lines_v1260,discovery_mineral_reward_v1260)
from core.mine_tunnels import mine_tunnel_room_id,HORIZONTAL_MINE_DIRECTIONS
from systems.craft_chain_v1260 import craft_chain_bonus_v1260
from systems.grand_expedition_v1260 import expedition_region_v1260
from systems.team_learning_v1260 import enemy_team_pressure_v1260
from systems.market_quotes_v1260 import market_quotes_v1260
from systems.market_dynamics_v1250 import market_demand_v1250
from systems.mercenary_memory_v1250 import memory_choice_v1250, memory_learn_v1250
from storage.db_world import DatabaseWorldMixin
from storage.schema_progression import create_progression_schema


def audit_v1260():
    checks = 0
    def ck(ok,msg):
        nonlocal checks
        checks += 1
        if not ok:
            raise AssertionError('SOULBOUND v1.26.0: '+msg)

    # Stable generated geology, all discoverable locations, unbounded scaling.
    g=geology_v1260(25,5,-3)
    ck(g==geology_v1260(25,5,-3),'generation not deterministic')
    ck(geology_v1260(1,0,0)['kind']=='rock','central shaft not safe')
    ck(geology_v1260(999999,999999,999999)['richness']>geology_v1260(500,50,50)['richness'],'artificial richness cap')
    ck(g['bonus_quantity']>=0 and g['reward_gold']>0,'invalid geology rewards')
    for kind in ('rock','ore_vein','cave','lake','ruins','chamber','vault','rare_ore'):
        ck(any(geology_v1260(30,x,y)['kind']==kind for x in range(1,85) for y in range(1,11)),
           'unreachable geology '+kind)
    ck(discovery_mineral_reward_v1260({'kind':'rock','floor':200,'distance':10,'richness':4}) is None,
       'free treasure for plain rock')
    ck(discovery_mineral_reward_v1260({'kind':'vault','floor':205,'distance':5,'richness':4})[0]=='eternium_ore',
       'deep vault lacks high-tier ore')
    ck(discovery_mineral_reward_v1260({'kind':'ruins','floor':30,'distance':5,'richness':3})[0]=='gold_ore',
       'ruins ore tier')
    ck(discovery_mineral_reward_v1260({'kind':'rare_ore','floor':1,'distance':5,'richness':1})[1]>=1,
       'low-level reward must exist')

    cells=[(0,0),(0,1),(1,1),(1,2),(2,2),(2,1)]
    path=mine_route_v1260(cells,(2,2))
    ck(path is not None and len(path)==2,'mine path should use diagonals')
    ck(path==mine_route_v1260(cells,(2,2)),'route nondeterminism')
    ck(mine_route_v1260([(0,0),(4,4)],(4,4)) is None,'route through unexcavated stone')
    ck(mine_route_v1260(cells,(0,0))==(),'root route')
    map_lines=mine_map_lines_v1260(cells,25,(2,2))
    ck(len(map_lines)==len(cells)+1,'mine map cell count')
    ck('TU JESTEŚ' in '\n'.join(map_lines),'missing position marker')
    ck('X=2, Y=2' in '\n'.join(map_lines),'missing coordinates')
    ck(len(mine_map_lines_v1260(cells*100,25,(0,0),max_rooms=3))==5,
       'screen reader map verbosity cap')
    ck(len(HORIZONTAL_MINE_DIRECTIONS)==8,'lost diagonal mine corridors')
    ck(mine_tunnel_room_id(700,11,2,-6).startswith('mine_floor_700_dig_11_'),
       'deep room identity changed')

    # Real SQLite restarts and cross-character isolation.
    with tempfile.TemporaryDirectory() as directory:
        file=os.path.join(directory,'mine.sqlite3')
        def db_open():
            db=DatabaseWorldMixin()
            conn=sqlite3.connect(file);conn.row_factory=sqlite3.Row
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute('CREATE TABLE IF NOT EXISTS accounts(id INTEGER PRIMARY KEY)')
            conn.executemany('INSERT OR IGNORE INTO accounts(id) VALUES(?)',[(11,),(12,)])
            db.conn=conn
            create_progression_schema(db)
            conn.commit()
            return db
        db=db_open()
        ck(db.mine_discover_v1260(11,31,5,6,'Górniczka')=={'new':True,'global_first':True},
           'first world discovery')
        ck(db.mine_discover_v1260(11,31,5,6,'Górniczka')=={'new':False,'global_first':False},
           'duplicate local discovery')
        ck(db.mine_discover_v1260(12,31,5,6,'Drugi')=={'new':True,'global_first':False},
           'world first duplicate')
        ck(db.mine_claim_v1260(11,31,5,6),'first treasure claim')
        ck(not db.mine_claim_v1260(11,31,5,6),'double treasury payout')
        ck(not db.mine_claimed_v1260(12,31,5,6),'private reward leaked')
        db.mercenary_memory_save_v1260(11,'mag','smok',{'attempts':[2,5,8],'success':[2.,4.5,7.0]})
        ck(db.mercenary_memory_read_v1260(11,'mag','smok')['attempts'][2]==8,'merc first save')
        ck(db.mercenary_memory_read_v1260(12,'mag','smok') is None,'merc memory leaked')
        ck(db.grand_expedition_start_v1260(11),'expedition start')
        ck(not db.grand_expedition_start_v1260(11),'duplicate expedition start')
        ck(db.grand_expedition_visit_v1260(11,'mine') is None,'wrong-way stage skip')
        ck(db.grand_expedition_visit_v1260(11,'city')==1,'city stage')
        ck(db.grand_expedition_visit_v1260(11,'city') is None,'city duplicate stage')
        ck(db.grand_expedition_visit_v1260(11,'ocean')==2,'ocean stage')
        db.conn.close()
        db=db_open()
        ck(db.mine_claimed_v1260(11,31,5,6),'treasure lost on restart')
        ck(db.mine_discover_v1260(12,31,5,6,'Drugi')=={'new':False,'global_first':False},
           'discovery lost on restart')
        ck(db.mercenary_memory_read_v1260(11,'mag','smok')['attempts']==[2,5,8],
           'mercenary memory lost on restart')
        ck(db.grand_expedition_state_v1260(11)['stage']==2,'expedition lost on restart')
        ck(db.grand_expedition_visit_v1260(11,'dungeon')==3,'dungeon stage')
        ck(db.grand_expedition_visit_v1260(11,'mine')==4,'mine stage')
        ck(db.grand_expedition_claim_v1260(11)==1,'first expedition claim')
        ck(db.grand_expedition_claim_v1260(11) is None,'double expedition claim')
        ck(db.grand_expedition_start_v1260(11),'new expedition cycle')
        ck(db.grand_expedition_state_v1260(11)['cycle']==2,'cycle did not increment')
        db.conn.close()

    for room,region in (
        ('market','city'),('ocean_sector_4','ocean'),('crypt_floor_20','dungeon'),
        ('mine_floor_999_dig_11_p2_m4','mine'),('village','')):
        ck(expedition_region_v1260(room)==region,'wrong expedition region '+room)

    ck(craft_chain_bonus_v1260('good',3,[40,50,30,60],0)=='excellent','craft synergy not effective')
    ck(craft_chain_bonus_v1260('good',3,[2,4,0,0],0)=='good','craft synergy for novice')
    ck(craft_chain_bonus_v1260('legendary',4,[100]*4,0)=='legendary','legendary quality overflow')
    ck(craft_chain_bonus_v1260('excellent',4,[100]*4,1)=='excellent','craft always succeeds')
    ck(craft_chain_bonus_v1260('masterwork',4,[100]*4,0)=='legendary','craft can promote masterwork')

    mob=SimpleNamespace(player_hits=50,combat_turn=10)
    ck(enemy_team_pressure_v1260(mob,{'name':'Wilk'})>1,'monster never responds')
    ck(enemy_team_pressure_v1260(mob,{'name':'Wilk'})<=1.21,'monster counterattack excessive')
    ck(enemy_team_pressure_v1260(SimpleNamespace(player_hits=7,combat_turn=2),{})==1,
       'weak party punished')
    ck(enemy_team_pressure_v1260(mob,{'boss':True})==1,'hand-authored boss changed')
    ck(enemy_team_pressure_v1260(mob,{'uoss_superboss':True})==1,'superboss changed')

    quotes=market_quotes_v1260(now=26000)
    ck(len(quotes)==6,'missing resource category quotes')
    for name in ('Ryby','Rudy','Drewno','Zioła'):
        ck(any(name in line for line in quotes),'market quote absent '+name)
    ck(quotes==market_quotes_v1260(now=26000),'quotes randomize mid-slot')
    ck(any('Pozostało' in line for line in quotes),'no quote refresh time')
    ck(all(.92<=market_demand_v1250(cat,now=26000)<=1.22 for cat in
           ('fish','ore','wood','herb')),'market unbounded discount/premium')

    from config.command_aliases import COMMAND_ALIAS_DEFINITIONS
    import ast
    from pathlib import Path
    tree=ast.parse((Path(__file__).resolve().parents[1] / 'player/session_mixins/command_registry.py').read_text(encoding='utf-8'))
    cmd={node.value for entry in tree.body if isinstance(entry, ast.Assign)
         for node in ([*entry.value.keys] if isinstance(entry.value, ast.Dict)
                      and any(isinstance(t,ast.Name) and t.id=='COMMAND_REGISTRY' for t in entry.targets) else [])
         if isinstance(node,ast.Constant)}
    for alias,command in [('kopalnia','mineinfo'),('wielkawyprawa','grandex1260'),
                          ('notowania','marketquotes1260')]:
        ck(COMMAND_ALIAS_DEFINITIONS.get(alias)==command,'bad alias '+alias)
    for name in ('mineinfo','grandex1260','marketquotes1260'):
        ck(name in cmd,'command not registered '+name)
    return checks

if __name__=='__main__':
    print('SOULBOUND v1.26:',audit_v1260(),'checks PASS')
