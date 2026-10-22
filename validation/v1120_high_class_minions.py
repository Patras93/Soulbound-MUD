# -*- coding: utf-8 -*-
"""v11.00.20: real level gates, class identity, SQLite and resource safety for minions."""
import asyncio
import sqlite3
from types import SimpleNamespace

from core.classes_skills import CLASSES
from systems.class_minions_v1119 import CLASS_MINIONS_V1119, CLASS_MINIONS_BY_CLASS_V1119
from player.session_mixins.era_sky_v1700 import (
    SessionSkyV1700Mixin, SUMMONS, SUMMON_MANA, ensure_schema, ascii_fold,
)
from systems.necro_constructs_v1710 import NECRO_MINIONS
from systems.druid_call_v1708 import ANIMALS
from systems.mage_elementals_v1702 import ELEMENTALS


def _validate_catalog():
    checks = 0
    def ck(v, name):
        nonlocal checks
        checks += 1
        if not v:
            raise AssertionError('MINIONY v11.00.20: ' + name)
    classes = {r[0] for r in CLASSES}
    assert len(classes) == 22
    ck(len(CLASS_MINIONS_V1119) == 95, '95 unikalnych przywołań 19 klas')
    ck(len(CLASS_MINIONS_BY_CLASS_V1119) == 19, '19 klas klasowych')
    ck(set(CLASS_MINIONS_BY_CLASS_V1119) == classes - {'Druid','Mag','Nekromanta'}, '22/22 klas')
    ck(len(SUMMONS) == len(set(SUMMONS)), 'bez nadpisania globalnych summonów')
    ck(all(k in SUMMONS for k in (*NECRO_MINIONS, *ANIMALS, *ELEMENTALS)), 'stare systemy zachowane')
    ck(not set(CLASS_MINIONS_V1119).intersection(set(NECRO_MINIONS) | set(ANIMALS) | set(ELEMENTALS)), 'brak konfliktu ze starymi kodami')
    for cls,rows in CLASS_MINIONS_BY_CLASS_V1119.items():
        ck(len(rows) == 5, cls + ' 5 stopni')
        ck([r[3] for r in rows] == [1,90,200,400,600], cls + ' progi')
        ck(len({r[0] for r in rows}) == 5 and len({r[1] for r in rows}) == 5, cls+' nazwy')
        ck(all(r[2] == cls and r[5] == rows[0][5] for r in rows), cls+' typ mocy')
        ck(all(r[6] > 0 and r[7] > 0 for r in rows), cls+' skalowanie')
        ck(all(rows[i][6] < rows[i+1][6] and rows[i][7] < rows[i+1][7] for i in range(4)), cls+' moc rośnie')
        for row in rows:
            key,name,owner,level,mana,channel,dmg,hp = row
            ck(key == ascii_fold(key) and ' ' not in key, 'kody ASCII '+key)
            ck(SUMMONS[key] == (name,owner,{},channel,dmg), 'rejestr '+key)
            ck(SUMMON_MANA[key] == mana, 'mana '+key)
            ck((mana == 0) == (channel == 'physical'), 'kanał '+key)
    ck(len({r[0] for r in CLASS_MINIONS_V1119.values()}) == 95, 'unikalne ID')
    return checks

async def _validate_runtime():
    checks=0
    conn=sqlite3.connect(':memory:')
    conn.row_factory=sqlite3.Row
    ensure_schema(conn)
    class DB:
        _v1700_ready=True
        def __init__(self):self.conn=conn
        def item_qty(self,*a):return 0
        def storage_qty(self,*a):return 0
    db=DB()
    class Hero(SessionSkyV1700Mixin):
        def __init__(self,account,klass,level=1,mana=3000,active=None):
            self.account_id=account
            self.cls=klass
            self.character=SimpleNamespace(character_level=level,room_id='temple',name=klass)
            self.current_mana=mana
            self.current_hp=5000
            self.combat_mob_key=None
            self.server=SimpleNamespace(db=db)
            self.messages=[]
            self.override=active
        def max_hp(self):return 5000
        def physical_power(self):return 1200
        def spell_power(self):return 1200
        def active_class_names(self):return self.override if self.override is not None else (self.cls,)
        async def send(self,msg):self.messages.append(str(msg))
    for index,(klass, rows) in enumerate(CLASS_MINIONS_BY_CLASS_V1119.items(),1):
        hero=Hero(index,klass,199)
        await hero.summons_v1700('klasy '+ascii_fold(klass))
        assert sum(m.startswith(klass+':') and 'chowaniec przywolaj ' in m for m in hero.messages)==5,klass+' per-class screen reader list'
        hero.messages.clear()
        await hero.summons_v1700('klasy dostepne')
        assert sum(m.startswith(klass+':') and 'chowaniec przywolaj ' in m for m in hero.messages)==2,klass+' only unlocked'
        checks+=2
        hero.messages.clear()
        for row in rows[2:]:
            key,name,owner,level,cost,channel,dmg,hp=row
            # One level below the requirement: must not write SQLite or take MP.
            hero.character.character_level=level-1
            mana=hero.current_mana
            await hero.summons_v1700('przywolaj '+key)
            assert hero.current_mana == mana, key+' premature mana'
            assert conn.execute('SELECT COUNT(*) FROM summons_v1700 WHERE account_id=? AND summon_type=?',(index,key)).fetchone()[0] == 0, key+' premature row'
            assert 'wymaga poziomu postaci '+str(level) in hero.messages[-1], key+' message'
            checks+=3
            # On unlock: full HP stored, right owner level and exact mana cost.
            hero.character.character_level=level
            await hero.summons_v1700('przywolaj '+key)
            dbrow=conn.execute('SELECT level,active,xp,hp,max_hp FROM summons_v1700 WHERE account_id=? AND summon_type=?',(index,key)).fetchone()
            assert dbrow and dbrow['active']==1 and dbrow['level']==level and dbrow['xp']==0 and dbrow['hp']==dbrow['max_hp']>0, key+' persistence'
            assert hero.current_mana == mana-cost, key+' mana'
            checks+=2
            # Store two other summons, never exceed 3.
        assert conn.execute('SELECT COUNT(*) FROM summons_v1700 WHERE account_id=? AND active=1',(index,)).fetchone()[0]==3, klass+' limit'
        hero.character.character_level=600
        mana=hero.current_mana
        await hero.summons_v1700('przywolaj '+rows[0][0])
        assert '3 aktywne' in hero.messages[-1] and hero.current_mana==mana,klass+' 3 limit'
        checks+=2
        # Re-login hides the summons without deleting their ID or HP.
        assert hero._v1703_dismiss_summons_on_login() == 3
        assert conn.execute('SELECT COUNT(*) FROM summons_v1700 WHERE account_id=?',(index,)).fetchone()[0]==3,klass+' persisted'
        mana=hero.current_mana
        await hero.summons_v1700('aktywuj '+rows[4][0])
        assert conn.execute('SELECT active FROM summons_v1700 WHERE account_id=? AND summon_type=?',(index,rows[4][0])).fetchone()[0]==1
        assert hero.current_mana==mana-SUMMON_MANA[rows[4][0]],klass+' reactivation mana'
        checks+=3
        # A non-owner class, even at high level, cannot summon this pet.
        outsider=Hero(100+index,'Wojownik' if klass!='Wojownik' else 'Berserker',800,active=('Wojownik',) if klass!='Wojownik' else ('Berserker',))
        mana=outsider.current_mana
        await outsider.summons_v1700('przywolaj '+rows[4][0])
        assert 'Tylko aktywny' in outsider.messages[-1]
        assert outsider.current_mana == mana
        assert conn.execute('SELECT COUNT(*) FROM summons_v1700 WHERE account_id=?',(100+index,)).fetchone()[0]==0
        checks+=3
        # At full 800 owner level, old minions remain and levels follow the owner.
        hero.character.character_level=800
        conn.execute('UPDATE summons_v1700 SET active=0 WHERE account_id=?',(index,))
        conn.commit()
        await hero.summons_v1700('aktywuj '+rows[2][0])
        updated=conn.execute('SELECT level,xp,active,max_hp FROM summons_v1700 WHERE account_id=? AND summon_type=?',(index,rows[2][0])).fetchone()
        assert updated['level']==800 and updated['xp']==0 and updated['active']==1 and updated['max_hp']>0
        checks+=1
    conn.close()
    return checks

def run_regression():
    return _validate_catalog() + asyncio.run(_validate_runtime())

if __name__=='__main__':
    print(f'LEGENDARNE MINIONY KLAS 200/400/600 v11.00.20: {run_regression()} checks PASS')
