# -*- coding: utf-8 -*-
"""8 nowych profesji: rzeczywiste materiały, wyrób, cooldown i progres questów.

Nowy moduł, bez modyfikowania transakcyjnej metody v107. Wszystkie efekty
jednego działania zamknięte w jednym odwracalnym bloku SQLite.
"""
from __future__ import annotations
import time
from core.archetypes.expansion import PROFESSION_SPECS
from player.session_mixins.profesje6 import _remove_all, _sum

COOLDOWN=12

def product_id(index):return 'v11000_prof_product_'+str(index+1)

def tool_item_id(index):return 'v11000_prof_tool_'+str(index+1)

# Product and tool descriptors belong exclusively to data.items_v110.professions.

def process(db,account_id,index,reward_callback,*,now=None):
    if type(index) is not int or not 0<=index<len(PROFESSION_SPECS):
        return None,'Nie ma takiej profesji v110.',None
    name,tool,tool_label,ingredient=PROFESSION_SPECS[index]
    now=int(time.time() if now is None else now)
    tool_item=tool_item_id(index)
    if db.item_qty(account_id,tool_item)<1:
        return None,'Brak narzędzia: '+tool_label+'. Kup na targu za 1200 srebra.',None
    if _sum(db,account_id,ingredient)<1:
        return None,'Brak surowca dla '+name+': '+ingredient,None
    with db.conn.deferred_commits():
        # Recheck inside the same SQLite unit: work cannot proceed after
        # a concurrent sale or transfer of the character-bound tool.
        if db.item_qty(account_id,tool_item)<1:
            return None,'Brak narzędzia: '+tool_label+'. Kup na targu za 1200 srebra.',None
        row=db.conn.execute('SELECT ready_at FROM v110_profession_cooldowns '
            'WHERE account_id=? AND tool_type=?',(account_id,tool)).fetchone()
        if row and int(row[0])>now:
            return None,'Praca '+name+' za '+str(int(row[0])-now)+' sekund.',None
        if not _remove_all(db,account_id,ingredient,1):
            raise RuntimeError('v110: brak surowca podczas transakcji; wycofano')
        item=product_id(index)
        db.add_item(account_id,item,1,commit=False)
        messages,_,_=reward_callback(name,200000,tool,120000,
                              content_level=102001,content_key='v110_'+tool)
        changed=db.increment_profession_action_quests_v0700(
            account_id,name,tool,1,action_code='v110_'+tool,tier=1)
        db.conn.execute('INSERT INTO v110_profession_cooldowns(account_id,tool_type,ready_at) '
            'VALUES (?,?,?) ON CONFLICT(account_id,tool_type) '
            'DO UPDATE SET ready_at=excluded.ready_at',(account_id,tool,now+COOLDOWN))
        db.conn.commit()
    return messages,changed,item
