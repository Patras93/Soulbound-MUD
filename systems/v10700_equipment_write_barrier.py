# -*- coding: utf-8 -*-
"""Defense in depth for a future live physical-EQ cutover.

Install ONLY after a complete per-copy migration on a disposable SQLite clone
or an separately approved production cutover. Until then it has no effect on
v106 gameplay. A legacy SQL write which bypasses the physical-instance adapter
is rejected at the *statement* level, before any inventory, equipment, bank or
profession-storage quantity can drift away from physical IDs.

TEMP triggers live only on the guarded connection. SQLite's TEMP trigger is not
persisted into backups and must be reinstalled on every authorized start.
"""
from __future__ import annotations
from contextlib import contextmanager

_TABLES = {
    'inventory': ('account_id','item_id'),
    'equipment': ('account_id','item_id'),
    'bank_items': ('account_id','item_id'),
    'profession_storage': ('account_id','item_id'),
}


def install_on_migrated_connection(db, catalog, *, approved_test_copy=False):
    """Guard only a specifically migrated copy; production is NOT enabled here.

    An explicit copy guard is required. A future authorized production installer
    must have its own audited entrypoint, backed by an offline rehearsal and
    rollback proof; passing a function argument cannot authorize live writes.
    """
    if getattr(db, '_v107_eq_live_active', False):
        # A live server is authorised solely by the installed 60/60 PLUS
        # candidate marker and a verified, committed migration checkpoint.
        from systems.runtime_activation import production_approved
        if (approved_test_copy or not production_approved() or
                not getattr(db, '_v107_eq_migration_committed', False)):
            raise PermissionError('Bramka EQ v107: brak zatwierdzonej migracji produkcyjnej')
    elif approved_test_copy is not True or not getattr(db,'_v106_shadow_slots_disposable_copy',False):
        raise PermissionError('Bramka EQ v107: najpierw migracja na zatwierdzonej kopii')
    catalog_size = sum(1 for meta in catalog.values() if isinstance(meta,dict)
                       and meta.get('type') in ('weapon','armor'))
    if not catalog_size:
        raise RuntimeError('Bramka EQ v107: pusty katalog typów wyposażenia')
    conn = db.conn
    if getattr(conn,'_v107_eq_write_barrier_active',False):
        raise RuntimeError('Bramka EQ v107: już aktywna, odmowa ponownej instalacji')
    if not all(conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
               for table in _TABLES):
        raise RuntimeError('Bramka EQ v107: niekompletny schemat bazowy')
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='v106_item_instances'").fetchone():
        raise RuntimeError('Bramka EQ v107: brak fizycznego ledgeru')

    def gate(item_id):
        identifier=str(item_id)
        item=catalog.get(identifier)
        is_gear=(isinstance(item,dict) and item.get('type') in ('armor','weapon'))
        unknown_dynamic=(identifier.startswith(('craftq_','deepq_','endlessq_'))
                         and not isinstance(item,dict))
        return int(not (is_gear or unknown_dynamic) or
                   getattr(conn, '_v107_eq_write_depth', 0) > 0)

    # A connection-bound SQLite user function cannot be accidentally shared
    # with another process's DB: both the guard and the TEMP triggers disappear
    # when this connection is closed.
    conn.create_function('v107_eq_mutation_allowed',1,gate)
    conn.create_function('v107_eq_instance_mutation_allowed',0,
                         lambda: int(getattr(conn,'_v107_eq_write_depth',0)>0))
    for table in _TABLES:
        for event,ref in (('INSERT','NEW'),('UPDATE','NEW'),('DELETE','OLD')):
            guard = f'v107_eq_mutation_allowed({ref}.item_id)=0'
            if event=='UPDATE':
                guard += ' OR v107_eq_mutation_allowed(OLD.item_id)=0'
            name=f'v107_eq_guard_{table}_{event.lower()}'
            conn.execute(f'''CREATE TEMP TRIGGER IF NOT EXISTS {name}
                BEFORE {event} ON main.{table}
                WHEN {guard}
                BEGIN SELECT RAISE(ABORT, 'v107 EQ: nieśledzony zapis fizycznego przedmiotu'); END''')
    # Protect physical IDs AND template-scoped legacy modifiers from raw SQL.
    tracked_ledgers=('v106_item_instances','v106_equipped_instances',
                     'v106_stored_instances','v106_mail_equipment_escrow')
    legacy_modifiers=('equipment_reforges','equipment_upgrades_v03042',
                      'equipment_runes_v0925','equipment_socket_bonus_v03114',
                      'tech_set_upgrades_v0320')
    for table in tracked_ledgers:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone():
            if table=='v106_mail_equipment_escrow':
                continue
            raise RuntimeError('v107 EQ: brak chronionej tabeli kopii: '+table)
        for event in ('INSERT','UPDATE','DELETE'):
            name=f'v107_eq_identity_{table}_{event.lower()}'
            conn.execute(f'''CREATE TEMP TRIGGER IF NOT EXISTS {name}
                BEFORE {event} ON main.{table}
                WHEN v107_eq_instance_mutation_allowed()=0
                BEGIN SELECT RAISE(ABORT, 'v107 EQ: nieśledzona zmiana tożsamości kopii'); END''')
    for table in legacy_modifiers:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone():
            continue
        for event,ref in (('INSERT','NEW'),('UPDATE','NEW'),('DELETE','OLD')):
            guard = f'v107_eq_mutation_allowed({ref}.item_id)=0'
            if event=='UPDATE':
                guard += ' OR v107_eq_mutation_allowed(OLD.item_id)=0'
            name=f'v107_eq_legacy_{table}_{event.lower()}'
            conn.execute(f'''CREATE TEMP TRIGGER IF NOT EXISTS {name}
                BEFORE {event} ON main.{table}
                WHEN {guard}
                BEGIN SELECT RAISE(ABORT, 'v107 EQ: stare ulepszenie nie śledzi fizycznej kopii'); END''')
    conn._v107_eq_write_depth = 0
    conn._v107_eq_write_barrier_active = True
    return catalog_size


@contextmanager
def approved_instance_operation(conn):
    """Use only around one atomic, checked per-copy adapter operation.

    The per-copy adapter validates owner, slot, stage and old/new quantities in
    the same SQLite SAVEPOINT. This context NEVER creates authorization to
    deploy the game; it only lifts TEMP SQL barriers during that adapter.
    """
    if not getattr(conn,'_v107_eq_write_barrier_active',False):
        yield
        return
    old=getattr(conn,'_v107_eq_write_depth',0)
    conn._v107_eq_write_depth=old+1
    try:
        yield
    finally:
        conn._v107_eq_write_depth=old
