# -*- coding: utf-8 -*-
"""v7.10.1: real single-class mode checks using isolated in-memory SQLite.
Never mutates actual server data or existing characters.
"""
import asyncio
from types import SimpleNamespace
import server as _runtime_ready_v71101
from config.balance import MULTICLASS_MAX_ACTIVE
from core.classes_skills import CLASS_SKILLS, CLASSES
from storage.db_progression import DatabaseProgressionMixin
from validation.v23215_multi_cap import TestDB
from systems.multi_cap_v23215 import multi_cap_experience_v23215, multi_cap_level_value_v23217
from player.character import Character
from player.session_mixins.class_progression import SessionClassProgressionMixin


def run_regression():
    checks = 0
    def check(value, label):
        nonlocal checks
        assert value, 'v7.10.1 single class: '+label
        checks += 1

    check(MULTICLASS_MAX_ACTIVE == 1, 'global limit one')
    check(len(CLASSES) == 22, 'twenty-two classes available at creation')
    db = TestDB()
    own = 'Wojownik'
    other = 'Mag'
    db.ensure_primary_class(1, own)
    baseline = multi_cap_experience_v23215(db.conn, 1)
    check(baseline == 5500, 'one class primary baseline')
    db.ensure_class_progress(1, other)
    db.conn.execute('UPDATE class_progress SET level=400,xp=789,active_slot=2 WHERE account_id=1 AND class_name=?', (other,))
    db.conn.commit()
    check(multi_cap_experience_v23215(db.conn, 1) == baseline, 'old inactive class no cap')
    classes = db.active_class_names(1, own)
    check(classes == [own], 'only one active after login')
    archived = db.class_progress_row(1, other)
    check(archived['active_slot'] is None and archived['level']==400 and archived['xp']==789,
          'old mastery preserved, no active slot')
    for name in (other, 'Druid', 'Kapłan'):
        ok, message = db.activate_secondary_class(1, own, name)
        check(not ok and 'wyłączone' in message, 'cannot add '+name)
        check(db.active_class_names(1, own) == [own], 'no new class persisted '+name)
    ok,_ = db.deactivate_secondary_class(1, own, own)
    check(not ok, 'cannot remove primary')
    fake = SimpleNamespace(class_name=own, _active_classes=[own,other,'Druid'])
    check(Character.active_class_names(fake) == [own], 'character defense independent of old cache')
    check(other not in Character.active_class_names(fake), 'no secondary passives')
    own_sk = CLASS_SKILLS[own][0]['id']
    other_sk = CLASS_SKILLS[other][0]['id']
    db.conn.execute('INSERT INTO learned_skills VALUES(1,?)',(other_sk,))
    db.conn.execute('INSERT INTO skill_progress VALUES(1,?,?)',(other_sk,100))
    db.conn.commit()
    check(multi_cap_experience_v23215(db.conn,1)==baseline,'secondary learned skill excluded from cap')
    db.conn.execute('INSERT INTO learned_skills VALUES(1,?)',(own_sk,))
    db.conn.execute('INSERT INTO skill_progress VALUES(1,?,?)',(own_sk,3))
    db.conn.commit()
    check(multi_cap_experience_v23215(db.conn,1)==baseline+1500,'primary learned skill counted')
    db.conn.execute("INSERT INTO ascension_progress_v021 VALUES(1,'class:Mag',100)")
    db.conn.commit()
    check(multi_cap_experience_v23215(db.conn,1)==baseline+1500, 'inactive ascension excluded')
    db.conn.execute("INSERT INTO ascension_progress_v021 VALUES(1,'class:Wojownik',2)")
    db.conn.commit()
    check(multi_cap_experience_v23215(db.conn,1)==baseline+2500,'primary ascension counted')
    db.conn.execute('UPDATE class_progress SET level=8 WHERE account_id=1 AND class_name=?',(own,))
    db.conn.commit()
    check(multi_cap_experience_v23215(db.conn,1)==baseline+2500+7*500,'primary mastery counted')
    db.ensure_primary_class(1, own)
    check(db.class_progress_row(1, other)['level']==400,'repeated login keeps archive')
    check(db.active_class_names(1,own)==[own], 'idempotent single class')

    class FakeSession(SessionClassProgressionMixin):
        character = SimpleNamespace(class_name=own, soul_weapon='Broń Duszy', _active_classes=[own,other])
        account_id = 1
        combat_mob_key = None
        server = SimpleNamespace(db=db)
        messages = []
        async def send(self, message): self.messages.append(message)
    ses=FakeSession()
    ses.character.active_class_names = lambda: [own]
    for command in ('', 'status', 'add Mag', 'remove Wojownik', 'włącz Druid', 'usuń Mag'):
        ses.messages.clear()
        asyncio.run(ses.handle_multiclass(command))
        check(any('JEDNA KLASA' in v for v in ses.messages),'command rejects '+command)
        check(db.active_class_names(1,own)==[own], 'command no DB change '+command)
    # Equipment earned by archived class must be refused without deleting its row.
    ses.character.character_level=800
    ses.equipment_character_level_requirement=lambda item:1
    ses.class_mastery_level=lambda name:400 if name==other else 8
    check(not ses.skill_mastery_unlocked(CLASS_SKILLS[other][0]),
          'archived class mastery cannot unlock magic skill')
    check(ses.skill_mastery_unlocked(CLASS_SKILLS[own][0]),
          'primary class mastery grants own skills')
    check(not ses.equipment_mastery_requirement_met({'type':'armor','required_class':other,'required_class_mastery':100}),
          'archived class armor disallowed')
    check(ses.equipment_mastery_requirement_met({'type':'armor','required_class':own,'required_class_mastery':5}),
          'main-class armor allowed')
    check(db.class_progress_row(1, other)['level']==400, 'all archived progress untouched')
    # Previously equipped secondary-class gear cannot confer residual bonuses.
    # The login gate removes only the equipped slot, never player inventory.
    from core.mines_threat import ITEMS
    warrior_id = next(k for k,it in ITEMS.items() if it.get('class_shop_item') and it.get('required_class')==own)
    mage_id = next(k for k,it in ITEMS.items() if it.get('class_shop_item') and it.get('required_class')==other)
    slots=[{'slot':'head','item_id':warrior_id}, {'slot':'body','item_id':mage_id}]
    removed=[]
    class EquipDB:
        def equipment(self, account_id): return list(slots)
        def unequip(self, account_id, slot): removed.append(slot)
        def active_class_names(self, account_id, primary_class): return [primary_class]
    ses.server = SimpleNamespace(db=EquipDB())
    ses.equipment_character_level_requirement = lambda item: 1
    discarded = ses.enforce_equipment_character_level()
    check(removed==['body'] and len(discarded)==1, 'foreign class EQ unequipped at login')
    check(all(k in slots[1] for k in ('item_id','slot')),
          'historical equipped item record exists, not deleted from ITEMS or inventory')
    ses.server = SimpleNamespace(db=db)
    db.conn.close()
    return checks

if __name__=='__main__':
    print('ONE CLASS v7.10.1:',run_regression(),'PASS')
