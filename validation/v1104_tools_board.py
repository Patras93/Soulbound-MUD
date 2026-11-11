# -*- coding: utf-8 -*-
"""v11.00.4: 22 tools stocked correctly; real SQLite durable purchases.

Exercises the normal `kup` shop handler in mentor rooms and the historical
14-tool once-per-character protection without touching production SQLite.
"""
import asyncio
import os
import tempfile
from types import SimpleNamespace
import server
from config.character_tools import CHARACTER_BOUND_TOOL_IDS
from core.classes_skills import CLASSES, RACES
from core.bootstrap_economy_professions import VERSION
from core.mines_threat import TOOL_SHOP_ROOMS, ITEMS
from player.session_mixins.shops_teachers import SessionShopsTeachersMixin
from systems.new_professions import PROFESSIONS
from systems.equipment_crafting import SHOPS, SHOP_SELLERS
from storage.database import Database
from validation.v600_professions import _Practice

class _Buyer(SessionShopsTeachersMixin, _Practice):
    pass


def run_regression():
    checks = 0
    def ck(value, label):
        nonlocal checks
        checks += 1
        if not value: raise AssertionError('TOOLS/BOARD v11.00.4: ' + label)

    ck(tuple(map(int, VERSION.split('.'))) >= (11, 0, 4) and server.VERSION == VERSION, 'release identity')
    ck(len(PROFESSIONS)==8, 'new profession count')
    ck(len(CHARACTER_BOUND_TOOL_IDS)==22, 'old + new tool protection')
    for prof, (tool_type, item_id, name) in PROFESSIONS.items():
        room, tool = server.V1104_MERCHANT_BOARD['shop_tools'][prof]
        ck(room == 'v601_mentor_'+tool_type and tool == item_id, prof+' room')
        ck(item_id in SHOPS.get(room, ()), prof+' offered in mentor shop')
        ck(TOOL_SHOP_ROOMS.get(item_id) == room, prof+' helpful purchase destination')
        ck(ITEMS[item_id]['name']==name and ITEMS[item_id]['tool_type']==tool_type, prof+' identity')
        ck(SHOP_SELLERS.get(room) in server.NPCS, prof+' vendor')
        ck(server.NPCS[SHOP_SELLERS[room]]['room']==room, prof+' vendor standing there')
        ck(server.NPCS[SHOP_SELLERS[room]]['shopkeeper'], prof+' shopkeeper flag')
        ck(item_id in CHARACTER_BOUND_TOOL_IDS, prof+' character-bound')
        ck(ITEMS[item_id]['price']==1200, prof+' price')
        ck(SessionShopsTeachersMixin.shop_offer_unit_cashback_silver(
            SimpleNamespace(shop_item_base_value_silver=lambda item:1200),
            ITEMS[item_id]) == 0, prof+' no phantom charisma discount')
    ck('Tablica Zleceń Gildii Dusz' in server.ROOMS['guild_hall']['desc'], 'physical board in guild')
    ck('tablica_zlecen' in server.HELP_TOPICS, 'board help')
    ck('guild_hall' == server.V1104_MERCHANT_BOARD['board_room'], 'board room ID')
    old_tools=CHARACTER_BOUND_TOOL_IDS - {row[1] for row in PROFESSIONS.values()}
    ck(len(old_tools)==14, '14 historical tools')
    for item_id in sorted(old_tools):
        ck(item_id in ITEMS and ITEMS[item_id]['type']=='tool', item_id+' exists')
        ck(any(item_id in stock for stock in SHOPS.values()), item_id+' obtainable in shop')
        ck(any(item_id in SHOPS.get(room,()) for room in (TOOL_SHOP_ROOMS.get(item_id,''),)), item_id+' advertised location')
    checks += asyncio.run(_sqlite_tests(ck))
    return checks


async def _sqlite_tests(ck):
    with tempfile.TemporaryDirectory(prefix='sb1104_') as tmp:
        path=os.path.join(tmp,'tools.db')
        db=Database(path)
        master=db.create_account('Tools1104','LongSecurePassword2026!')
        cases={c:'Testowy' for c in ('nom','gen','dat','acc','ins','loc','voc')}
        a,_=db.create_character_for_master(master,'Kupujacy',RACES[0],CLASSES[0],cases)
        b,_=db.create_character_for_master(master,'DrugiKupujacy',RACES[0],CLASSES[0],cases)
        db.set_shared_wallet_for_master(master,100000,0,0)
        buyer=_Buyer(db,a); buyer.character.silver=100000
        for prof,(tool_type,item_id,name) in PROFESSIONS.items():
            buyer.character.room_id='v601_mentor_'+tool_type
            buyer.output=[]
            await buyer.buy(name)
            ck(db.item_qty(a,item_id)==1, prof+' buy by name')
            ck('Kupiono' in ' '.join(buyer.output), prof+' message')
            before=db.shared_wallet_for_master(master)
            buyer.output=[]
            await buyer.buy('1')
            ck('już kupione' in ' '.join(buyer.output).lower() or 'już kupione' in ' '.join(buyer.output).lower() or 'nie można kupić drugiego' in ' '.join(buyer.output).lower(), prof+' no duplicate by number')
            ck(db.shared_wallet_for_master(master)==before, prof+' no duplicate charge')
            ck(db.conn.execute('SELECT COUNT(*) FROM prof6_tools_owned WHERE account_id=? AND item_id=?',(a,item_id)).fetchone()[0] == 1, prof+' ledger')
        # Historical tools must lock into the same durable ledger even if the
        # character received them in earlier versions, where no ledger existed.
        for item_id in sorted(CHARACTER_BOUND_TOOL_IDS - {spec[1] for spec in PROFESSIONS.values()}):
            room=next(r for r,stock in SHOPS.items() if item_id in stock)
            # Guild arcane vendor's class shop requires a real character level;
            # use an isolated plain shop list when checking its bound item.
            buyer.character.room_id=room
            db.add_item(a,item_id,1)
            buyer.output=[]
            await buyer.buy(ITEMS[item_id]['name'])
            ck(db.item_qty(a,item_id)==1, item_id+' cannot double while owned')
            ck(db.conn.execute('SELECT 1 FROM prof6_tools_owned WHERE account_id=? AND item_id=?',(a,item_id)).fetchone() is not None, item_id+' legacy import into ledger')
        db.conn.close()
        db=Database(path)
        buyer=_Buyer(db,a)
        buyer.character.silver=db.shared_wallet_for_master(master)[0]
        for prof,(tool_type,item_id,name) in PROFESSIONS.items():
            buyer.character.room_id='v601_mentor_'+tool_type
            before=db.shared_wallet_for_master(master)
            buyer.output=[]
            await buyer.buy(name)
            ck(db.item_qty(a,item_id)==1, prof+' single after restart')
            ck(db.shared_wallet_for_master(master)==before, prof+' no double debit after restart')
        # Even if a previous copy vanishes, historical purchase must not
        # become a fresh purchase opportunity after restarting SQLite.
        legacy_tool = 'fishing_rod'
        db.conn.execute('UPDATE inventory SET quantity=0 WHERE account_id=? AND item_id=?', (a,legacy_tool))
        db.conn.commit()
        buyer.character.room_id = next(room for room,goods in SHOPS.items() if legacy_tool in goods)
        before = db.shared_wallet_for_master(master)
        buyer.output=[]
        await buyer.buy(ITEMS[legacy_tool]['name'])
        ck(db.item_qty(a,legacy_tool)==0, 'old tool historical purchase is immutable')
        ck(db.shared_wallet_for_master(master)==before, 'old tool never charges again')
        ck('już kupione' in ' '.join(buyer.output).lower() or 'już kupione' in ' '.join(buyer.output).lower(), 'old tool rejection message')
        second=_Buyer(db,b)
        second.character.silver=db.shared_wallet_for_master(master)[0]
        second.character.room_id='v601_mentor_trading'
        await second.buy('Waga Kupiecka')
        ck(db.item_qty(b,'merchant_scale')==1 and db.item_qty(a,'merchant_scale')==1, 'distinct characters allowed')
        db.conn.close()
    return 0

if __name__=='__main__':
    print('NARZEDZIA 22 I TABLICA GILDII v11.00.4:',run_regression(),'checks PASS')
