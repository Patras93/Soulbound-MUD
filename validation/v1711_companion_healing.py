# -*- coding: utf-8 -*-
"""v1.70.11: living companions heal; dead/hidden are never revived."""
import asyncio
import sqlite3
from types import SimpleNamespace
from player.session_mixins.era_sky_v1700 import SessionSkyV1700Mixin,ensure_schema

class TestSession(SessionSkyV1700Mixin):
    def __init__(self, conn, account=13, cls='Druid'):
        self.account_id=account;self.cls=cls
        self.character=SimpleNamespace(character_level=500,room_id='whisper_grove',name=f'Player{account}')
        self.server=SimpleNamespace(db=SimpleNamespace(conn=conn,_v1700_ready=True),party_sessions=lambda *a,**k: [self])
        self.current_hp=2000;self.current_mana=5000;self.closed=False
        self.combat_mob_key=None;self.messages=[]
    def max_hp(self):return 5000
    def active_class_names(self):return (self.cls,)
    def healing_power_v1125(self):return 600
    async def send(self, msg):self.messages.append(str(msg))

def put(conn,account,kind,hp,maxhp,active=1):
    conn.execute('INSERT OR REPLACE INTO summons_v1700(account_id,summon_type,level,active,hp,max_hp) VALUES(?,?,1,?,?,?)',
                 (account,kind,active,hp,maxhp));conn.commit()
def hp(conn,a,kind):
    return conn.execute('SELECT hp,active FROM summons_v1700 WHERE account_id=? AND summon_type=?',(a,kind)).fetchone()

async def run_async():
    n=0
    c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row;ensure_schema(c)
    druid=TestSession(c); put(c,13,'lifeoak',1000,5000)
    await druid.summons_v1700('lecz lifeoak')
    assert hp(c,13,'lifeoak')[0]>1000 and druid.current_mana==4940;n+=1
    old=hp(c,13,'lifeoak')[0];mana=druid.current_mana
    await druid.summons_v1700('lecz lifeoak')
    assert hp(c,13,'lifeoak')[0]>old and druid.current_mana==mana-60;n+=1
    put(c,13,'wilk',0,7000,0)
    mana=druid.current_mana
    await druid.summons_v1700('lecz wilk')
    assert hp(c,13,'wilk')[0]==0 and druid.current_mana==mana;n+=1
    put(c,13,'wilk',4000,7000,0)
    await druid.summons_v1700('lecz wilk')
    assert hp(c,13,'wilk')[0]==4000 and druid.current_mana==mana;n+=1
    put(c,13,'lifeoak',100,5000);put(c,13,'wilk',1000,7000)
    await druid.summons_v1700('lecz wszystko')
    assert hp(c,13,'lifeoak')[0]>100 and hp(c,13,'wilk')[0]>1000;n+=1
    mana=druid.current_mana;put(c,13,'wilk',100,7000);druid.current_mana=1
    druid._v1710_refresh_summon_health(c);before=hp(c,13,'wilk')[0]
    await druid.summons_v1700('lecz wilk')
    assert hp(c,13,'wilk')[0]==before and druid.current_mana==1;n+=1
    # Shared party gets own and ally summon access, never stranger, no self-revive.
    friend=TestSession(c,account=14,cls='Nekromanta');other=TestSession(c,account=15,cls='Druid')
    put(c,14,'wojownik',1000,6000);put(c,15,'lifeoak',100,5000)
    druid.server.party_sessions=lambda *a,**k:[druid,friend]
    friend.server.party_sessions=druid.server.party_sessions
    druid.current_mana=5000
    assert druid._v1711_find_companion('Szkielet Wojownika',include_party=True)[0] is friend;n+=1
    assert druid._v1711_find_companion('lifeoak',include_party=True)[0] is druid;n+=1
    assert druid._v1711_find_companion('konstrukt_zelaza',include_party=True) is None;n+=1
    assert len([x for x in druid._v1711_companions_for_healing(include_party=True) if x[0] is other])==0;n+=1
    before=hp(c,14,'wojownik')[0]
    candidate=druid._v1711_find_companion('wojownik',include_party=True)
    gained=druid._v1711_heal_companion(candidate[0],candidate[1],1234)
    assert gained==1234 and hp(c,14,'wojownik')[0]==before+1234;n+=1
    put(c,14,'wojownik',0,6000,0)
    assert druid._v1711_heal_companion(candidate[0],candidate[1],4000)==0 and hp(c,14,'wojownik')[0]==0;n+=1
    # If source is not marked combat-aware or cheat-support integration is missing, catch it.
    from pathlib import Path
    combat=(Path(__file__).resolve().parents[1]/'player/session_mixins/combat_skills.py').read_text(encoding='utf-8')
    assert "_v1711_find_companion(target_text,include_party=True)" in combat;n+=1
    assert "_v1711_companions_for_healing(include_party=True)" in combat;n+=1
    c.close();return n

def run_regression():return asyncio.run(run_async())
if __name__=='__main__':print('COMPANION HEALING v1.70.11:',run_regression(),'checks PASS')
