# -*- coding: utf-8 -*-
"""Manual v105 duplicated evolved EQ allocation, explicitly on disposable SQLite copies.

Old records identify an item template, not which duplicate was upgraded.
There is no inference here: an operator must inspect the clone and explicitly
select one of the previously indistinguishable copies and, if worn, its slot.
No automatic production migration, no server-boot integration.
"""
from __future__ import annotations
import os
from uuid import uuid5,NAMESPACE_URL
from systems.equipment_instances_v10600 import _schema,_manual_row,_manual_verified
from systems.equipment_inventory_flow_v10600 import _legacy_modifiers
from systems.equipment_shadow_slots_v10600 import _schema as _slot_schema


def _refuse_external_copies(conn,account,item):
    """Never guess which copy evolved if the same template also exists off-bag."""
    tables={str(row[0]) for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if 'bank_items' in tables and conn.execute(
            'SELECT 1 FROM bank_items WHERE account_id=? AND item_id=? AND quantity>0',
            (account,item)).fetchone():
        raise RuntimeError('v106 EQ: identyczna sztuka także w banku; ręczna decyzja wstrzymana')
    if 'profession_storage' in tables and conn.execute(
            'SELECT 1 FROM profession_storage WHERE account_id=? AND item_id=? AND quantity>0',
            (account,item)).fetchone():
        raise RuntimeError('v106 EQ: identyczna sztuka także w magazynie; ręczna decyzja wstrzymana')
    if 'player_mail_v03051' in tables and conn.execute('''
            SELECT 1 FROM player_mail_v03051
            WHERE attachment_kind='item' AND attachment_item_id=?
              AND attachment_claimed=0
              AND (sender_account_id=? OR recipient_account_id=?) LIMIT 1''',
            (item,account,account)).fetchone():
        raise RuntimeError('v106 EQ: identyczna sztuka w nieodebranej poczcie')
    if 'v106_stored_instances' in tables and conn.execute('''
            SELECT 1 FROM v106_stored_instances st
            JOIN v106_item_instances i ON i.instance_id=st.instance_id
            WHERE i.account_id=? AND i.item_id=? LIMIT 1''',
            (account,item)).fetchone():
        raise RuntimeError('v106 EQ: istnieje fizyczna kopia poza ekwipunkiem')


def reconcile_on_disposable_copy(conn,catalog,*,account_id,item_id,
        expected_quantity,expected_legacy_stage,chosen_ordinal,
        reviewer_reference,selected_worn_slot=None,confirm_disposable_copy=False):
    """Atomically acknowledge one legacy evolved physical unit; never guess.

    The reviewer must supply observed count/stage as anti-stale preconditions.
    `chosen_ordinal` is a human judgment, not an automatically known identity.
    Equipment slots require an explicit human selection of the evolved slot.
    No per-template reforge/runes/upgrades are migrated by this procedure.
    """
    if confirm_disposable_copy is not True or os.environ.get('SOULBOUND_V106_STAGING')!='1':
        raise PermissionError('v106 EQ: ręczne uzgodnienie tylko na kopii z aktywnym staging')
    if (type(account_id) is not int or account_id<1 or
            type(expected_quantity) is not int or not 2<=expected_quantity<=20000 or
            type(expected_legacy_stage) is not int or not 1<=expected_legacy_stage<=10 or
            type(chosen_ordinal) is not int or not 1<=chosen_ordinal<=expected_quantity):
        raise ValueError('v106 EQ: nieprawidłowe ID, ilość, etap lub numer kopii')
    if (not isinstance(item_id,str) or not item_id or
            not isinstance(catalog,dict) or not isinstance(catalog.get(item_id),dict) or
            catalog[item_id].get('type') not in ('armor','weapon')):
        raise ValueError('v106 EQ: nieznany typ fizycznego wyposażenia')
    if (not isinstance(reviewer_reference,str) or
            not 8<=len(reviewer_reference.strip())<=160 or
            any(c in reviewer_reference for c in '\r\n\0')):
        raise ValueError('v106 EQ: wymagany identyfikator ręcznej decyzji (8–160 znaków)')
    from systems.equipment_evolution_v10500 import KEY_PREFIX
    outer=conn.in_transaction
    conn.execute('SAVEPOINT sb106_manual_reconcile')
    try:
        _schema(conn)
        _slot_schema(conn)
        conn.execute('''CREATE TABLE IF NOT EXISTS v106_manual_evolution_allocations(
            account_id INTEGER NOT NULL,item_id TEXT NOT NULL,
            chosen_ordinal INTEGER NOT NULL,expected_quantity INTEGER NOT NULL,
            legacy_stage INTEGER NOT NULL,review_reference TEXT NOT NULL,
            selected_worn_slot TEXT,
            PRIMARY KEY(account_id,item_id)
        )''')
        countrow=conn.execute('SELECT quantity FROM inventory '
            'WHERE account_id=? AND item_id=?',(account_id,item_id)).fetchone()
        stagerow=conn.execute('SELECT value FROM player_records_v03051 '
            'WHERE account_id=? AND record_key=?',
            (account_id,KEY_PREFIX+item_id)).fetchone()
        if (not countrow or type(countrow[0]) is not int or
                countrow[0]!=expected_quantity or not stagerow or
                type(stagerow[0]) is not int or stagerow[0]!=expected_legacy_stage):
            raise RuntimeError('v106 EQ: liczba lub etap zmieniły się od ręcznej kontroli')
        if _legacy_modifiers(conn,account_id,item_id):
            raise RuntimeError('v106 EQ: stare runy/przekucia/ulepszenia wymagają odrębnej decyzji')
        _refuse_external_copies(conn,account_id,item_id)
        slots=[str(row[0]) for row in conn.execute(
            'SELECT slot FROM equipment WHERE account_id=? AND item_id=? '
            'ORDER BY slot',(account_id,item_id)).fetchall()]
        if len(slots)>expected_quantity:
            raise RuntimeError('v106 EQ: więcej założonych slotów niż kopii')
        if slots:
            if (not isinstance(selected_worn_slot,str) or selected_worn_slot not in slots):
                raise RuntimeError('v106 EQ: wskaż dokładny slot z historyczną ewolucją')
        elif selected_worn_slot is not None:
            raise RuntimeError('v106 EQ: wskazany slot nie ma tego przedmiotu')
        current=_manual_row(conn,account_id,item_id)
        if current is not None:
            if not _manual_verified(conn,account_id,item_id,
                    expected_quantity,expected_legacy_stage):
                raise RuntimeError('v106 EQ: istniejący ręczny zapis nie zgadza się z kopią')
            if (int(current[0])!=chosen_ordinal or
                    current[3]!=reviewer_reference or
                    current[4]!=selected_worn_slot):
                raise RuntimeError('v106 EQ: próba zmiany już zatwierdzonej decyzji lub slotu')
            # Verify exact slot ownership before accepting an idempotent rerun.
            chosen_id=str(uuid5(NAMESPACE_URL,
                f'soulbound:v106:legacy:{account_id}:{item_id}' +
                (f':copy:{chosen_ordinal}' if chosen_ordinal>1 else '')))
            if selected_worn_slot is not None:
                row=conn.execute('SELECT instance_id FROM v106_equipped_instances '
                    'WHERE account_id=? AND slot=?',(account_id,selected_worn_slot)).fetchone()
                if row is None or str(row[0])!=chosen_id:
                    raise RuntimeError('v106 EQ: zmieniono powiązanie wybranej założonej kopii')
            result={'new_instances':0,'already_confirmed':True,'copies':expected_quantity}
        else:
            if conn.execute('SELECT 1 FROM v106_item_instances '
                    'WHERE account_id=? AND item_id=? LIMIT 1',
                    (account_id,item_id)).fetchone():
                raise RuntimeError('v106 EQ: istniejące fizyczne kopie wymagają odrębnego audytu')
            ids=[str(uuid5(NAMESPACE_URL,
                f'soulbound:v106:legacy:{account_id}:{item_id}' +
                (f':copy:{n}' if n>1 else ''))) for n in range(1,expected_quantity+1)]
            for uid in ids:
                if conn.execute('SELECT 1 FROM v106_item_instances WHERE instance_id=?',(uid,)).fetchone():
                    raise RuntimeError('v106 EQ: konflikt deterministycznego identyfikatora')
            conn.executemany('''INSERT INTO v106_item_instances
                (instance_id,account_id,item_id,evolution_stage,origin)
                VALUES(?,?,?,?,?)''',
                ((uid,account_id,item_id,
                  expected_legacy_stage if n==chosen_ordinal else 0,
                  'manual_legacy_review') for n,uid in enumerate(ids,1)))
            if slots:
                # All slots for the same duplicated item are assigned exactly once.
                # Never replace existing mapping from a different migration.
                remaining=[uid for n,uid in enumerate(ids,1) if n!=chosen_ordinal]
                mapping={selected_worn_slot:ids[chosen_ordinal-1]}
                for slot in slots:
                    if slot!=selected_worn_slot:mapping[slot]=remaining.pop(0)
                for slot,uid in mapping.items():
                    if conn.execute('SELECT 1 FROM v106_equipped_instances '
                            'WHERE account_id=? AND slot=?',(account_id,slot)).fetchone():
                        raise RuntimeError('v106 EQ: slot już przypisany do innej kopii')
                    conn.execute('INSERT INTO v106_equipped_instances '
                        '(account_id,slot,instance_id) VALUES(?,?,?)',
                        (account_id,slot,uid))
            conn.execute('INSERT INTO v106_manual_evolution_allocations '
                '(account_id,item_id,chosen_ordinal,expected_quantity,legacy_stage,review_reference,selected_worn_slot) '
                'VALUES(?,?,?,?,?,?,?)',
                (account_id,item_id,chosen_ordinal,expected_quantity,
                 expected_legacy_stage,reviewer_reference,selected_worn_slot))
            conn.execute('DELETE FROM v106_evolution_migration_issues '
                'WHERE account_id=? AND item_id=?',(account_id,item_id))
            if not _manual_verified(conn,account_id,item_id,
                    expected_quantity,expected_legacy_stage):
                raise RuntimeError('v106 EQ: ręczny zapis nie przeszedł kontroli integralności')
            result={'new_instances':expected_quantity,'already_confirmed':False,
                    'copies':expected_quantity}
        conn.execute('RELEASE SAVEPOINT sb106_manual_reconcile')
        if not outer:conn.commit()
        return result
    except BaseException:
        conn.execute('ROLLBACK TO SAVEPOINT sb106_manual_reconcile')
        conn.execute('RELEASE SAVEPOINT sb106_manual_reconcile')
        raise
