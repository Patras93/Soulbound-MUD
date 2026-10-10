# -*- coding: utf-8 -*-
"""v1.70.10 checks: Oak level locks, construct recipes, training and HP refresh."""
import asyncio
import sqlite3
from types import SimpleNamespace
from data.items import ITEMS
from systems.necro_constructs_v1710 import NECRO_MINIONS, summon_key
from player.session_mixins.era_sky_v1700 import (SessionSkyV1700Mixin,
    SUMMONS,SUMMON_MANA,DRUID_OAK_MIN_LEVEL,ensure_schema)

class DB:
    _v1700_ready=True
    def __init__(self,conn):self.conn=conn;self.inv={}
    def item_qty(self, aid, item):return self.inv.get((aid,item),0)
    def storage_qty(self,aid,box,item):return 0
    def remove_storage_item(self,*args,**kwargs):return False
    def remove_item(self,aid,item,qty,commit=True):
        if self.item_qty(aid,item)<qty:return False
        self.inv[aid,item]-=qty
        if commit:self.conn.commit()
        return True

class Session(SessionSkyV1700Mixin):
    def __init__(self,conn,cls,level=1):
        self.account_id=77;self.server=SimpleNamespace(db=DB(conn))
        self.character=SimpleNamespace(room_id='whisper_grove',character_level=level)
        self.cls=cls;self.current_mana=10000;self.combat_mob_key=None;self.messages=[];self.base_hp=20000
    def active_class_names(self):return (self.cls,)
    async def send(self,msg):self.messages.append(str(msg))
    def max_hp(self):return self.base_hp
    def physical_power(self):return 8000
    def spell_power(self):return 6000

async def _run_async():
    n=0
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
    # Simulate migration of summons table created before XP and stance were introduced.
    conn.execute('CREATE TABLE summons_v1700 (account_id INTEGER, summon_type TEXT, level INTEGER DEFAULT 1, active INTEGER DEFAULT 1, soul_rank INTEGER DEFAULT 0, hp INTEGER DEFAULT 0, max_hp INTEGER DEFAULT 0, PRIMARY KEY(account_id,summon_type))')
    ensure_schema(conn)
    columns={r[1] for r in conn.execute('PRAGMA table_info(summons_v1700)')}
    assert {'xp','stance','hp','max_hp','soul_rank'}<=columns;n+=1
    assert len(NECRO_MINIONS)>=15;n+=1
    assert DRUID_OAK_MIN_LEVEL=={'lifeoak':150,'ancientoak':400};n+=1
    assert set(NECRO_MINIONS).issubset(SUMMONS);n+=1
    assert summon_key('metal construct')=='konstrukt_zelaza';n+=1
    for kind,spec in NECRO_MINIONS.items():
        assert SUMMON_MANA[kind]==spec[2] and SUMMONS[kind][1]=='Nekromanta';n+=1
        assert spec[1]>=1 and spec[2]>0 and spec[8]>=0;n+=1
        assert all(item in ITEMS or item in ('v1700_common_tooth','v1700_dragon_tooth') for item in spec[3]),(kind,spec[3]);n+=1
        assert spec[7] in ('atak','obrona','wsparcie');n+=1
    d=Session(conn,'Druid',149);d.server.db.inv[77,'v1702_pinecone']=20
    await d.summons_v1700('przywolaj lifeoak')
    assert '150' in d.messages[-1] and d.current_mana==10000 and d.server.db.item_qty(77,'v1702_pinecone')==20;n+=1
    await d.summons_v1700('przywolaj ancientoak')
    assert '400' in d.messages[-1] and d.current_mana==10000 and d.server.db.item_qty(77,'v1702_pinecone')==20;n+=1
    d.character.character_level=150
    await d.summons_v1700('przywolaj lifeoak')
    a=conn.execute("SELECT active,hp,max_hp FROM summons_v1700 WHERE account_id=77 AND summon_type='lifeoak'").fetchone()
    assert a['active']==1 and a['hp']>0 and d.current_mana==9920 and d.server.db.item_qty(77,'v1702_pinecone')==18;n+=1
    d.character.character_level=399
    await d.summons_v1700('przywolaj ancientoak')
    assert '400' in d.messages[-1] and d.current_mana==9920 and d.server.db.item_qty(77,'v1702_pinecone')==18;n+=1
    d.character.character_level=400
    await d.summons_v1700('przywolaj ancientoak')
    a=conn.execute("SELECT active,hp FROM summons_v1700 WHERE account_id=77 AND summon_type='ancientoak'").fetchone()
    assert a['active']==1 and a['hp']>0 and d.current_mana==9740 and d.server.db.item_qty(77,'v1702_pinecone')==13;n+=1
    # At a later login previous active state may not bypass level restrictions.
    d._v1703_dismiss_summons_on_login()
    d.character.character_level=100;initial_mp=d.current_mana;old_cones=d.server.db.item_qty(77,'v1702_pinecone')
    await d.summons_v1700('aktywuj lifeoak')
    assert '150' in d.messages[-1] and d.current_mana==initial_mp and d.server.db.item_qty(77,'v1702_pinecone')==old_cones;n+=1
    conn.close()
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row;ensure_schema(conn)
    nec=Session(conn,'Nekromanta',74)
    nec.server.db.inv[77,'iron_ingot']=20
    await nec.necro_v1700('przywolaj metal')
    assert nec.current_mana==10000 and '75' in nec.messages[-1] and nec.server.db.item_qty(77,'iron_ingot')==20;n+=1
    nec.character.character_level=75
    await nec.necro_v1700('przywolaj metal')
    row=conn.execute("SELECT level,xp,hp,max_hp,active FROM summons_v1700 WHERE summon_type='konstrukt_zelaza'").fetchone()
    assert row['active']==1 and row['hp']==row['max_hp'] and nec.current_mana==9855 and nec.server.db.item_qty(77,'iron_ingot')==8;n+=1
    max0=row['max_hp'];conn.execute("UPDATE summons_v1700 SET hp=? WHERE summon_type='konstrukt_zelaza'",(max0//3,));conn.commit()
    nec.base_hp*=2;nec._v1710_refresh_summon_health(conn)
    scaled=conn.execute("SELECT hp,max_hp FROM summons_v1700 WHERE summon_type='konstrukt_zelaza'").fetchone()
    assert scaled['max_hp']==max0*2 and abs(scaled['hp']/scaled['max_hp']-1/3)<.01;n+=1
    for _ in range(75):nec._v1710_earn_summon_xp(conn,'konstrukt_zelaza',1000)
    row=conn.execute("SELECT level,xp FROM summons_v1700 WHERE summon_type='konstrukt_zelaza'").fetchone()
    assert row['level']>1 and row['xp']>=0;n+=1
    # Legacy warrior progression cannot accidentally gain passive summon XP.
    conn.execute("INSERT INTO summons_v1700(account_id,summon_type,level,xp,active) VALUES(77,'wojownik',9,0,0)")
    nec._v1710_earn_summon_xp(conn,'wojownik',50000)
    assert conn.execute("SELECT level,xp FROM summons_v1700 WHERE summon_type='wojownik'").fetchone()['level']==9;n+=1
    nec._v1703_dismiss_summons_on_login()
    assert conn.execute("SELECT active,hp,level FROM summons_v1700 WHERE summon_type='konstrukt_zelaza'").fetchone()['hp']==0;n+=1
    mp=nec.current_mana
    await nec.necro_v1700('przywolaj metal')
    assert 'Brak materiałów' in nec.messages[-1] and nec.current_mana==mp;n+=1
    conn.close()
    return n

def run_regression():return asyncio.run(_run_async())
if __name__=='__main__':print('SUMMON MASTERY v1.70.10:',run_regression(),'checks PASS')
