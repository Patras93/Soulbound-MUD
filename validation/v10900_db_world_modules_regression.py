# -*- coding: utf-8 -*-
'''Ścisłe testy podziału db_world oraz odizolowanego SQLite; bez danych graczy.'''
from __future__ import annotations
import ast, hashlib, sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_AST_SHA256='12718d15405909fe015e9060689b2bfcd168db7d0bb1b0e98e3716d9e429970b'
GROUPS={'activity_achievements': ('activity_rows_v0560', 'achievement_metric', 'add_achievement_metric', 'set_achievement_metric_max', 'unlock_achievement', 'achievement_rows', 'unlock_title', 'title_rows'), 'bestiary_codex': ('bestiary_entry', 'bestiary_rows', 'boss_codex_stats', 'add_boss_codex_drop', 'boss_codex_drops'), 'bounties_quests': ('dynamic_world_quest_v015', 'clear_dynamic_world_quest_v015'), 'collections': ('add_collection_entry', 'collection_entry_ids', 'collection_entry_discovered_at', 'touch_collection_entry', 'remove_collection_entry'), 'dungeons_checkpoints': ('crypt_checkpoint', 'sync_legacy_crypt_checkpoint', 'crypt_portal', 'unlock_crypt_portal', 'astral_checkpoint', 'astral_portal', 'unlock_astral_portal', 'highest_boss_floor_cleared'), 'exploration': ('exploration_room_point_awards_v2322', 'discovered_room_ids', 'claim_exploration_reward'), 'fishing': ('fish_journal_entry', 'fish_journal_rows', 'fish_journal_ids', 'fish_global_record_v022', 'fish_global_top_v022', 'fish_rarest_global_v022', 'fish_rarest_personal_v022'), 'instances_chests': ('instance_visited_floors', 'instance_highest_floor', 'mark_instance_secret', 'instance_secret_rows', 'mark_instance_checkpoint', 'treasure_chest_opened_at', 'mark_treasure_chest_opened'), 'mercenaries_expeditions': ('mercenary_memory_save_v1260', 'grand_expedition_start_v1260', 'grand_expedition_state_v1260', 'grand_expedition_claim_v1260'), 'mines': ('mine_tunnel_exists_v1251', 'mine_tunnel_target_v1251', 'mine_tunnel_directions_v1251', 'mine_tunnel_cells_v1260', 'mine_claim_v1260', 'mine_claimed_v1260'), 'nemesis_ascension': ('nemesis_row_v029', 'defeat_nemesis_v029', 'ascension_row_v021', 'ascension_rows_v021', 'world_tier_v021', 'set_world_tier_v021', 'endless_gauntlet_best_v021', 'mark_endless_gauntlet_round_v021'), 'projects_contracts': ('world_project_state_v022', 'world_project_contribution_v022', 'mark_world_project_reward_claimed_v022', 'legendary_contract_state_v022', 'save_legendary_contract_state_v022'), 'reputations_lifetime': ('faction_reputation_v016', 'faction_reputations_v016', 'add_faction_reputation_v016', 'add_lifetime_stat', 'set_lifetime_stat_max', 'lifetime_stats', 'city_reputation_v0710')}
LEGACY_BOUND = {
 'unlock_crypt_checkpoint','unlock_astral_checkpoint','boss_floor_cleared',
 'mine_progress','add_mine_wall_hit','mine_tunnel_hit_v1251','mine_discover_v1260',
 'mercenary_memory_read_v1260','grand_expedition_visit_v1260','mine_startup_status',
 'mark_room_discovered_with_points_v2322','record_bestiary_kill','record_boss_codex_kill',
 'promote_nemesis_v029','add_ascension_xp_v021','mark_instance_floor_visited',
 'instance_checkpoint_floors','record_activity_v0560','bounty_board_state',
 'save_bounty_board_state','save_dynamic_world_quest_v015','record_fish_catch',
 'record_fishing_global_v022','add_world_project_contribution_v022',
 'postal_delivery_state_v0522','save_postal_delivery_state_v0522',
 'courier_guild_state_v0530','save_courier_guild_state_v0530','add_city_reputation_v0710',
}
RETAINED=LEGACY_BOUND|{'lifetime_stat','ensure_mine_progress','mark_room_discovered',
  'exploration_reward_claimed','mark_boss_floor_cleared','city_reputations_v0710',
  'record_courier_city_visit_v0530'}

def run():
 checks=0
 tree=ast.parse((ROOT/'storage/db_world.py').read_text('utf8'))
 cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='DatabaseWorldMixin')
 found={x.name:x for x in cls.body if isinstance(x,ast.FunctionDef)}
 assert set(found)==RETAINED,(set(found)^RETAINED);checks+=len(found)
 for group,names in GROUPS.items():
  t=ast.parse((ROOT/f'storage/db_world_parts_v109/{group}.py').read_text('utf8'))
  c=next(x for x in t.body if isinstance(x,ast.ClassDef))
  meth={x.name:x for x in c.body if isinstance(x,ast.FunctionDef)}
  assert set(meth)==set(names),(group,set(meth)^set(names))
  assert not set(meth)&set(found),group
  found.update(meth);checks+=len(meth)+1
 assert len(found)==111
 raw='\n'.join(n+'='+ast.dump(found[n],include_attributes=False) for n in sorted(found))
 assert hashlib.sha256(raw.encode()).hexdigest()==EXPECTED_AST_SHA256;checks+=111
 from storage.db_world import DatabaseWorldMixin
 from storage.database import Database
 assert issubclass(Database,DatabaseWorldMixin);checks+=1
 assert DatabaseWorldMixin.__module__=='storage.db_world';checks+=1
 assert len([x for x in DatabaseWorldMixin.__mro__ if x.__name__.endswith('V109Mixin')])==len(GROUPS);checks+=1
 for name in found:
  assert callable(getattr(DatabaseWorldMixin,name,None)),name
  checks+=1
 for name in LEGACY_BOUND:
  bound=DatabaseWorldMixin.__dict__.get(name)
  assert bound is not None and bound.__module__=='storage.db_world'
  assert bound.__globals__ is __import__('storage.db_world',fromlist=['']).__dict__
  checks+=1
 # Only an in-memory SQLite connection. Explicit schema, no user or live DB.
 conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
 conn.executescript('''
 CREATE TABLE exploration_rooms(account_id INTEGER,room_id TEXT,PRIMARY KEY(account_id,room_id));
 CREATE TABLE exploration_rewards(account_id INTEGER,zone TEXT,PRIMARY KEY(account_id,zone));
 CREATE TABLE exploration_room_points_v2322(account_id INTEGER,room_id TEXT,ep_points INTEGER,PRIMARY KEY(account_id,room_id));
 CREATE TABLE exploration_zero_ep_v1002(account_id INTEGER,room_id TEXT,PRIMARY KEY(account_id,room_id));
 CREATE TABLE collection_codex(account_id INTEGER,category TEXT,entry_id TEXT,discovered_at TEXT DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(account_id,category,entry_id));
 CREATE TABLE achievement_progress(account_id INTEGER,metric TEXT,value INTEGER,PRIMARY KEY(account_id,metric));
 CREATE TABLE faction_reputation_v016(account_id INTEGER,faction_id TEXT,reputation INTEGER,updated_at TEXT DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(account_id,faction_id));
 CREATE TABLE lifetime_statistics(account_id INTEGER,stat_key TEXT,value INTEGER,updated_at TEXT DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(account_id,stat_key));
 CREATE TABLE legendary_contracts_v022(account_id INTEGER PRIMARY KEY,offers_json TEXT,active_json TEXT,completed_count INTEGER,updated_at TEXT);
 CREATE TABLE fish_journal(account_id INTEGER,species_id TEXT,fish_count INTEGER,PRIMARY KEY(account_id,species_id));
 ''')
 class Trial(DatabaseWorldMixin):
  def __init__(self,connection):self.conn=connection
 db=Trial(conn)
 try:
  assert db.discovered_room_ids(1)==set();checks+=1
  assert db.mark_room_discovered(1,'test_room') is True;checks+=1
  assert db.mark_room_discovered(1,'test_room') is False;checks+=1
  assert db.discovered_room_ids(1)=={'test_room'} and db.discovered_room_ids(2)==set();checks+=1
  assert db.claim_exploration_reward(1,'zone') is True;checks+=1
  assert db.claim_exploration_reward(1,'zone') is False;checks+=1
  assert db.exploration_reward_claimed(1,'zone') and not db.exploration_reward_claimed(2,'zone');checks+=1
  assert db.add_collection_entry(1,'relic','relic_a') is True;checks+=1
  assert not db.add_collection_entry(1,'relic','relic_a');checks+=1
  assert db.collection_entry_ids(1,'relic')=={'relic_a'} and db.collection_entry_ids(2,'relic')==set();checks+=1
  assert db.collection_entry_discovered_at(1,'relic','relic_a');checks+=1
  assert db.touch_collection_entry(1,'relic','relic_a');checks+=1
  assert db.remove_collection_entry(1,'relic','relic_a');checks+=1
  assert not db.remove_collection_entry(1,'relic','relic_a');checks+=1
  assert db.add_achievement_metric(1,'beasts',4)==4;checks+=1
  assert db.set_achievement_metric_max(1,'beasts',3)==4;checks+=1
  assert db.set_achievement_metric_max(1,'beasts',12)==12;checks+=1
  assert db.achievement_metric(2,'beasts')==0;checks+=1
  assert db.add_faction_reputation_v016(1,'stone',2)==2;checks+=1
  assert db.add_faction_reputation_v016(1,'stone',-8)==2;checks+=1
  assert db.faction_reputations_v016(1)=={'stone':2} and not db.faction_reputations_v016(2);checks+=1
  assert db.add_lifetime_stat(1,'bosses',3)==3;checks+=1
  assert db.set_lifetime_stat_max(1,'bosses',2)==3;checks+=1
  assert db.set_lifetime_stat_max(1,'bosses',9)==9;checks+=1
  assert db.lifetime_stat(2,'bosses')==0 and db.lifetime_stats(1)=={'bosses':9};checks+=1
  assert db.save_legendary_contract_state_v022(1,offers=[{'id':9}],active={'id':9},completed_count=4) is None;checks+=1
  assert db.legendary_contract_state_v022(1)=={'offers':[{'id':9}],'active':{'id':9},'completed_count':4};checks+=1
  assert db.legendary_contract_state_v022(2)['active']=={};checks+=1
  conn.execute('BEGIN')
  conn.execute('INSERT INTO exploration_rooms(account_id,room_id) VALUES(?,?)',(9,'rollback_room'))
  conn.rollback()
  assert 'rollback_room' not in db.discovered_room_ids(9);checks+=1
  assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok';checks+=1
 finally:conn.close()
 print(f'V109 DB WORLD MODULAR: {checks} PASS; 111 AST=v108, 13 modules, legacy bound and SQLite in memory')
 return checks
if __name__=='__main__':run()
