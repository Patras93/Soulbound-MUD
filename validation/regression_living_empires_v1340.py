import sys,sqlite3

from systems import living_empires_v1340 as live
from systems import imperial_economy_v1320 as eco
conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
conn.execute('CREATE TABLE player_clans(id INTEGER PRIMARY KEY, treasury INTEGER NOT NULL)')
conn.execute('INSERT INTO player_clans VALUES(1,10000000)')
live.init(conn)
conn.execute("INSERT INTO empire_forts_v1320(fort,clan_id,walls,conquered_at) VALUES('bazalt',1,2,100000)")
conn.execute("INSERT INTO empire_armies_v1320(clan_id,troop,quantity) VALUES(1,'wojownik',150)")
conn.commit()
checks=0
def check(v,msg):
 global checks
 assert v,msg; checks+=1
check(live.detail(conn,'bazalt',now=100001)['owner']==1,'owner')
check(live.garrison_strength(conn,'bazalt')==0,'empty')
res=live.move_garrison(conn,1,'bazalt','wojownik',50)
check(res==150000,'garrison power')
check(conn.execute('SELECT quantity FROM empire_armies_v1320').fetchone()[0]==100,'moving conserved soldiers')
try:live.move_garrison(conn,1,'bazalt','wojownik',1_000)
except ValueError: checks += 1
else: raise AssertionError('overspend garrison')
check(conn.execute('SELECT quantity FROM empire_garrisons_v1340').fetchone()[0]==50,'rollback')
check(live.refresh(conn,'bazalt',now=100000+live.RAID+1)['raid'] is not None,'NPC raid 12h')
check(live.detail(conn,'bazalt',now=100000+live.RAID+2)['raids']==1,'one raid per schedule')
check(live.detail(conn,'bazalt',now=100000+live.RAID+2)['reserve']>0,'income')
coins=live.collect(conn,1,'bazalt',now=100000+live.RAID+3)
check(coins>0,'earned')
check(live.collect(conn,1,'bazalt',now=100000+live.RAID+3)==0,'no duplicated payment')
# ownership limited to own guild; NO second player guild setup
first=live.enemy_camp(conn,1,'bazalt','natarcie',now=100000+live.RAID+10)
check(first['won'],'PVE fight wins')
check(first['reward']>0,'reward')
check(conn.execute('SELECT victories FROM empire_pve_raids_v1340').fetchone()[0]==1,'victory persisted')
try:live.enemy_camp(conn,1,'bazalt','natarcie',now=100000+live.RAID+11)
except ValueError as ex:check('odpoczywają' in str(ex),'cooldown')
else:raise AssertionError('cooldown bypass')
# different fort cannot be raided without ownership
try:live.enemy_camp(conn,1,'orkowie')
except ValueError:checks+=1
else:raise AssertionError('unowned attacked')
# disconnect/no players online doesn't cause fort loss
check(live.owner_of(conn,'bazalt')['clan_id']==1,'fort retained')
# upgrade non-empty treasury, no coin generation
level,paid=live.upgrade(conn,1,'bazalt','farmy');check(level==1 and paid>0,'upgrade')
# transfer invalidates old garrison and territory
conn.execute("UPDATE empire_forts_v1320 SET clan_id=2 WHERE fort='bazalt'")
check(not conn.execute("SELECT 1 FROM empire_garrisons_v1340 WHERE fort='bazalt'").fetchone(),'garrison invalidation')
check(not conn.execute("SELECT 1 FROM empire_territories_v1340 WHERE fort='bazalt'").fetchone(),'income invalidation')
print('LIVING EMPIRES PvE PASS',checks)
