# -*- coding: utf-8 -*-
"""v106 STAGING ONLY: prevent legacy crafting from consuming physical EQ.

The existing v104 consumption API can atomically take ordinary ingredients
from storage and inventory. Physical v106 equipment is not a material until a
per-instance recipe/quality/forge flow has been validated end-to-end.
"""
from __future__ import annotations

import os
from systems.equipment_inventory_flow_v10600 import tracked
from core.sqlite_numeric_guard_v10400 import require_sqlite_int64


def active(db):
    """Staging-copy or explicitly approved live physical EQ only."""
    from systems.v10700_eq_runtime_gate import is_enabled
    return is_enabled(db)


def guard_ingredient(db, item_id):
    """Raise before ANY legacy crafting SQL on a per-copy equipment ingredient."""
    if active(db) and tracked(db, str(item_id)):
        raise RuntimeError(
            'v106 EQ: ulepszone lub fizyczne wyposażenie nie może być składnikiem '
            'zwykłej receptury. Użyj później receptury dla konkretnej sztuki.'
        )


def guard_recipe(db, recipe):
    """Check all direct and selectable ingredient IDs ahead of craft wait."""
    if not active(db):
        return
    for key in ('ingredients', 'distinct_ingredient_pool', 'pooled_ingredient_pool'):
        values = recipe.get(key) or ()
        for item_id in values:
            guard_ingredient(db, item_id)


def take_one_kind(db, account_id, item_id, qty, container):
    """Atomically take one ingredient from both sources without partial loss."""
    required = require_sqlite_int64('v106.crafting.ingredient_qty', qty)
    if required < 0:
        raise ValueError('v106: ujemna liczba składników')
    if required == 0:
        return True
    guard_ingredient(db, item_id)
    return db.consume_items_across_storage_and_inventory(
        account_id, (str(item_id),), required, container=container
    )


def craft_output_atomic(db, account_id, ingredients, output_id, output_qty=1,
                        *, containers=None, extra_outputs=(), success_accounting=None,
                        reward_journal=None):
    """Low-level staged recipe transaction, not the high-level XP/quality flow.

    Consume *all* ingredients and mint the output under one SQLite SAVEPOINT,
    including the v106 physical instance ledger and shop cost lots.  This is
    called by staged v106 perform_recipe, NEVER by ordinary v105 gameplay.
    """
    if not active(db):
        raise PermissionError('v106 crafting: dozwolone tylko na jawnej kopii testowej')
    if not isinstance(ingredients, dict) or not ingredients:
        raise ValueError('v106 crafting: brak mapy składników')
    if not isinstance(containers, (dict, type(None))):
        raise TypeError('v106 crafting: nieprawidłowe kontenery')
    containers = containers or {}
    output_qty=require_sqlite_int64('v106.crafting.output_qty', output_qty)
    if output_qty<1:raise ValueError('v106 crafting: ilość wyniku musi być dodatnia')
    if output_id is None or not str(output_id):
        raise ValueError('v106 crafting: brak wyniku')
    # v106: bonuses earned by a successful craft belong to the SAME SQL unit.
    # Stage their quantities before removing any ingredient; reject malformed
    # bonuses rather than allowing negative/overflowing item production.
    extras=[]
    if not isinstance(extra_outputs,(tuple,list)):
        raise TypeError('v106: nieprawidłowe produkty dodatkowe')
    for extra in extra_outputs:
        if not isinstance(extra,(tuple,list)) or len(extra)!=2:
            raise ValueError('v106: nieprawidłowa nagroda dodatkowa')
        iid,amount=extra
        amount=require_sqlite_int64('v106.crafting.extra_qty',amount)
        if not isinstance(iid,str) or not iid or amount<=0:
            raise ValueError('v106: nieprawidłowy produkt dodatkowy')
        if iid not in db._v106_shadow_item_catalog:
            raise ValueError('v106: nieznany produkt dodatkowy')
        extras.append((iid,amount))
    # The durable, synchronous counters of an already successful craft belong
    # to the SAME transaction as ingredients, output and OLC bonus materials.
    # Profession XP, quest progress and external achievement notifications are
    # NOT included here; those paths require dedicated subsequent integration.
    accounting=None
    if success_accounting is not None:
        if not isinstance(success_accounting,dict) or set(success_accounting)!={
            'profession','category','critical','legendary','crafted_items'
        }:
            raise ValueError('v106: nieprawidłowe dane księgowania craftingu')
        profession=success_accounting['profession']
        category=success_accounting['category']
        if not isinstance(profession,str) or not profession or len(profession)>128:
            raise ValueError('v106: nieprawidłowa profesja')
        if not isinstance(category,str) or not category or len(category)>128:
            raise ValueError('v106: nieprawidłowa kategoria mistrzostwa')
        critical=success_accounting['critical']
        legendary=success_accounting['legendary']
        if type(critical) is not bool or type(legendary) is not bool:
            raise ValueError('v106: błędne flagi jakości')
        crafted_items=require_sqlite_int64(
            'v106.crafting.crafted_items',success_accounting['crafted_items'])
        if crafted_items!=output_qty:
            raise ValueError('v106: licznik sztuk musi odpowiadać wynikowi receptury')
        accounting=(profession,category,int(critical),int(legendary),crafted_items)
    # Journal intent is validated before consumption; its INSERT is INSIDE
    # the output SAVEPOINT, never an independent award or an auto-retry.
    if reward_journal is not None:
        if not isinstance(reward_journal,dict) or set(reward_journal)!={'run_id','recipe_id','base_item_id'}:
            raise ValueError('v106: błędny dziennik rozliczenia receptury')
        from systems.equipment_craft_reward_journal_v10600 import assert_ready
        assert_ready(db,account_id)
    plan=[]
    seen=set()
    for iid, quantity in ingredients.items():
        iid=str(iid)
        required=require_sqlite_int64('v106.crafting.ingredient_qty', quantity)
        if not iid or required<=0:
            raise ValueError('v106 crafting: składnik i ilość muszą być dodatnie')
        if iid in seen:
            raise ValueError('v106 crafting: zdublowany identyfikator składnika')
        seen.add(iid)
        guard_ingredient(db, iid)
        container=containers.get(iid)
        if container is not None and (not isinstance(container,str) or not container):
            raise ValueError('v106 crafting: nieprawidłowa szkatułka')
        plan.append((iid,required,container))
    conn=db.conn
    with conn.deferred_commits():
        conn.execute('SAVEPOINT v106_craft_output_atomic')
        try:
            # Preflight first; no ingredient should disappear if one is missing.
            for iid,quantity,container in plan:
                available=db.item_qty(account_id,iid)
                if container:
                    available+=db.storage_qty(account_id,container,iid)
                if available<quantity:
                    conn.execute('ROLLBACK TO SAVEPOINT v106_craft_output_atomic')
                    conn.execute('RELEASE SAVEPOINT v106_craft_output_atomic')
                    return False
            for iid,quantity,container in plan:
                left=quantity
                if container:
                    stored=db.storage_qty(account_id,container,iid)
                    take=min(stored,left)
                    if take:
                        if not db.remove_storage_item(account_id,container,iid,take,commit=False):
                            raise RuntimeError('v106 crafting: zmienił się stan szkatułki')
                        left-=take
                if left and not db.remove_item(account_id,iid,left,commit=False):
                    raise RuntimeError('v106 crafting: zmienił się stan ekwipunku')
            db.add_item(account_id,str(output_id),output_qty,commit=False)
            for bonus_id,bonus_amount in extras:
                db.add_item(account_id,bonus_id,bonus_amount,commit=False)
            if accounting is not None:
                profession,category,critical,legendary,crafted_items=accounting
                # SQLite silently converts INT64 overflow to REAL. For durable
                # counters that would corrupt exact player history; reject it
                # before changing any mastery/statistics row.
                def _safe_increment(existing,inc,label):
                    existing=require_sqlite_int64(label,existing)
                    if existing<0 or existing>9223372036854775807-inc:
                        raise OverflowError('v106: przekroczono limit licznika '+label)
                old_mastery=conn.execute(
                    'SELECT actions,criticals,legendary_count FROM crafting_mastery_v03054 '
                    'WHERE account_id=? AND profession=? AND category=?',
                    (int(account_id),profession,category),
                ).fetchone()
                if old_mastery is not None:
                    for label,old,inc in zip(
                        ('mastery.actions','mastery.criticals','mastery.legendary_count'),
                        old_mastery,(1,critical,legendary),
                    ):
                        _safe_increment(old,inc,label)
                for stat,amount in (
                    ('craft_actions',1),('crafted_items',crafted_items),
                    ('profession_actions',1),
                ):
                    old=conn.execute(
                        'SELECT value FROM lifetime_statistics WHERE account_id=? AND stat_key=?',
                        (int(account_id),stat),
                    ).fetchone()
                    if old is not None:_safe_increment(old[0],amount,'lifetime.'+stat)
                conn.execute('''INSERT INTO crafting_mastery_v03054
                    (account_id,profession,category,actions,criticals,legendary_count)
                    VALUES(?,?,?,1,?,?)
                    ON CONFLICT(account_id,profession,category) DO UPDATE SET
                    actions=actions+1,criticals=criticals+excluded.criticals,
                    legendary_count=legendary_count+excluded.legendary_count''',
                    (int(account_id),profession,category,critical,legendary))
                for stat,amount in (
                    ('craft_actions',1),('crafted_items',crafted_items),
                    ('profession_actions',1),
                ):
                    conn.execute('''INSERT INTO lifetime_statistics(account_id,stat_key,value)
                        VALUES(?,?,?) ON CONFLICT(account_id,stat_key) DO UPDATE SET
                        value=lifetime_statistics.value+excluded.value,
                        updated_at=CURRENT_TIMESTAMP''',
                        (int(account_id),stat,amount))
            from systems.equipment_shadow_slots_v10600 import _check_account
            _check_account(conn,int(account_id),db._v106_shadow_item_catalog)
            if reward_journal is not None:
                from systems.equipment_craft_reward_journal_v10600 import begin_in_savepoint
                begin_in_savepoint(db,account_id,reward_journal['run_id'],
                    reward_journal['recipe_id'],reward_journal['base_item_id'],
                    str(output_id),output_qty)
            conn.execute('RELEASE SAVEPOINT v106_craft_output_atomic')
            return True
        except BaseException:
            conn.execute('ROLLBACK TO SAVEPOINT v106_craft_output_atomic')
            conn.execute('RELEASE SAVEPOINT v106_craft_output_atomic')
            raise
