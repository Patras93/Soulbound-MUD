# -*- coding: utf-8 -*-
"""Regressions for ephemeral summons, local Fame, queue and all-axes rewards."""
import asyncio
import sqlite3
import time
from types import SimpleNamespace
from player.session_mixins.era_sky_v1700 import SessionSkyV1700Mixin,ensure_schema
from systems.fame_v1702 import (fame_catalog, fame_region, fame_report,
                                record_fame_kill,pay_due_fame)
from data.rooms import ROOMS
from data.mobs import MOB_TEMPLATES

async def _run():
    conn=sqlite3.connect(':memory:')
    conn.row_factory=sqlite3.Row
    ensure_schema(conn)
    logs=[]
    class DB:
        _v1700_ready=True
        def __init__(self):self.conn=conn;self.inv={};self.saved=0
        def item_qty(self,aid,item):return self.inv.get((aid,item),0)
        def storage_qty(self,*args):return 0
        def remove_storage_item(self,*args,**kw):return False
        def remove_item(self,aid,item,qty,commit=True):
            if self.item_qty(aid,item)<qty:return False
            self.inv[(aid,item)]-=qty;return True
        def add_item(self,aid,item,qty,commit=True):self.inv[(aid,item)]=self.item_qty(aid,item)+qty
        def save_character(self,ch):self.saved+=1
    db=DB()
    class Session(SessionSkyV1700Mixin):
        def __init__(self,aid,cls):
            self.account_id=aid
            self.server=SimpleNamespace(db=db)
            self.character=SimpleNamespace(level=(150 if cls=='Druid' else 90),character_level=(150 if cls=='Druid' else 90),STAT_PROGRESS_FIELDS=['strength','dexterity'],room_id='square')
            self.cls=cls;self.combat_mob_key=None;self.current_mana=900;self.closed=False
            self.soul=0;self.class_xp=0;self.stat_xp=0;self.char_xp=0
        def max_hp(self):return 1000
        async def send(self,txt):logs.append(str(txt))
        def active_class_names(self):return (self.cls,)
        async def _v1701_need_mana(self,amount):
            if self.current_mana<amount:return False
            return True
        async def grant_combat_soul_xp_v11350(self,xp,**kw):self.soul+=xp
        async def grant_class_xp(self,xp,**kw):self.class_xp+=xp
        async def grant_stat_xp_v11342(self,xp,**kw):self.stat_xp+=xp
        def add_character_xp_with_event(self,xp,**kw):self.char_xp+=xp;return []
    checks=0
    summons=[(21,'wojownik',6,2,350,550),(22,'lifeoak',9,0,500,900),(23,'zywiolak_ogien_mniejszy',4,0,250,650)]
    for aid,kind,lv,rank,hp,maximum in summons:
        conn.execute('INSERT INTO summons_v1700(account_id,summon_type,level,active,soul_rank,hp,max_hp) '
                     'VALUES(?,?,?,1,?,?,?)',(aid,kind,lv,rank,hp,maximum))
    conn.commit()
    for aid,cls in [(21,'Nekromanta'),(22,'Druid'),(23,'Mag')]:
        player=Session(aid,cls)
        assert player._v1703_dismiss_summons_on_login()==1
        row=conn.execute('SELECT * FROM summons_v1700 WHERE account_id=?',(aid,)).fetchone()
        assert row['active']==0 and row['hp']==0 and row['level']==summons[aid-21][2] and row['soul_rank']==summons[aid-21][3]
        checks+=2
        kind=summons[aid-21][1];start=player.current_mana
        await player.summons_v1700(f'przywolaj {kind}')
        if aid==23:assert player.current_mana<start
        else:assert player.current_mana==start
        checks+=1
        if aid==21:db.add_item(aid,'v1700_dragon_tooth',1)
        if aid==22:db.add_item(aid,'v1702_pinecone',2)
        if aid!=23:
            await player.summons_v1700(f'przywolaj {kind}')
        row=conn.execute('SELECT * FROM summons_v1700 WHERE account_id=?',(aid,)).fetchone()
        assert row['active']==1 and row['hp']==row['max_hp'] and row['level']==player.character.character_level  # owner level
        checks+=1
    cat=fame_catalog();assert cat
    from systems.content_registry import MOB_SPAWNS
    zone,targets=next((z,b) for z,b in cat.items() if len(b)>=2)
    rid,tid=next((rid,mid) for rid,mid in MOB_SPAWNS if mid in targets and fame_region(rid)==zone)
    mob=SimpleNamespace(room_id=rid,template_id=tid)
    p=Session(80,'Druid'); p.character.room_id=rid
    assert len(record_fame_kill(conn,[p],mob,MOB_TEMPLATES[tid]))==1
    assert not record_fame_kill(conn,[p],mob,MOB_TEMPLATES[tid])
    assert 'zaliczone (premia EXP oczekuje)' in ' '.join(fame_report(conn,80,'log',room_id=rid))
    checks+=3
    assert fame_report(conn,80,'',room_id=rid)!=['You have no fame in this area.']
    assert (await pay_due_fame(p))==0
    conn.execute('UPDATE fame_pending_v1703 SET due_at=? WHERE account_id=80',(time.time()-1,));conn.commit()
    assert (await pay_due_fame(p))==1
    assert p.soul>0 and p.class_xp>0 and p.stat_xp>0 and p.char_xp>0
    assert (await pay_due_fame(p))==0
    remaining = [x for x in targets if x != tid]
    if len(targets) == 2:
        final_name = MOB_TEMPLATES.get(remaining[0], {}).get('name') or remaining[0]
        expected = f'You have most fame in this area. Missing fame: {final_name}.'
    else:
        expected = 'You have some fame in this area.'
    assert fame_report(conn,80,'',room_id=rid)==[expected]
    checks+=5
    assert fame_report(conn,80,'log wszystko',room_id='temple')
    assert fame_report(conn,80,'none',room_id='temple')
    checks+=2
    return checks

def run_regression():return asyncio.run(_run())
