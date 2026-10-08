"""Soulbound v1.17.5: economy/shop arbitrage and SQLite purchase-basis audit.

Run only in the disposable full predeploy world, never on production data.
"""
from __future__ import annotations

import os
import tempfile
from types import SimpleNamespace


def audit_economy_final_v1175():
    from core.bootstrap_economy_professions import (
        PROFESSION_RANK_NAMES, SILVER_PER_GOLD, SILVER_PER_MITHRIL,
        legacy_currency_to_coins,
    )
    from systems.equipment_crafting import SHOPS
    from systems.items_resources import CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER
    from core.mines_threat import ITEMS
    from systems.legacy_value_sweep import shop_money_price_v11325
    from player.session_mixins.sales import SessionSalesMixin
    from storage.database import Database

    checks, errors = 0, []
    stats = {"professions": len(PROFESSION_RANK_NAMES), "rooms": len(SHOPS),
             "offers": 0, "at_risk_before": 0, "token_only": 0,
             "purchased_lots": 0, "reopened": 0}

    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(message)

    check(len(PROFESSION_RANK_NAMES) == 14, "14 profession definitions missing")
    check((SILVER_PER_GOLD, SILVER_PER_MITHRIL) == (100, 100_000_000),
          "currency denomination drift")
    sale = SessionSalesMixin()
    sampled = set()
    for room, ids in SHOPS.items():
        for iid in ids:
            item = ITEMS.get(iid)
            stats["offers"] += 1
            if not item:
                check(False, f"{room}/{iid}: missing item")
                continue
            price = shop_money_price_v11325(item)
            token = bool(item.get('fur_shop_token') and
                         int(item.get('fur_shop_token_cost', 0) or 0) > 0)
            if price == 0 and token:
                stats["token_only"] += 1
            else:
                check(price > 0, f"{room}/{iid}: free non-token item")
                for discount in (0, 25, 50, 75):
                    net = price - (price * discount // 100)
                    check(net >= 1, f"{room}/{iid}: zero net price at {discount}%")
            if iid in sampled or price <= 0 or not sale.generic_item_is_sellable(iid, item):
                continue
            sampled.add(iid)
            s = sale.generic_item_sale_value(iid, item)
            resale = legacy_currency_to_coins(s['silver'], s['gold'], s['mithril'])
            check(resale >= 0, f"{room}/{iid}: negative sale")
            if resale > price - price*75//100:
                stats["at_risk_before"] += 1

    # The final class-shop catalog includes dynamic tiers not shown in SHOPS.
    for class_name, stages in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.items():
        for stage, ids in stages.items():
            for iid in ids:
                item = ITEMS.get(iid)
                check(bool(item), f"{class_name}/{stage}/{iid}: missing class shop item")
                if item:
                    price = shop_money_price_v11325(item)
                    check(price >= 1, f"{class_name}/{stage}/{iid}: zero class shop price")

    with tempfile.TemporaryDirectory(prefix="soulbound-economy1175-") as directory:
        path = os.path.join(directory, 'economy.sqlite')
        db = Database(path)
        for aid in (71, 72):
            db.conn.execute(
                'INSERT INTO accounts(id,username,password_salt,password_hash) VALUES(?,?,?,?)',
                (aid, f'economy_{aid}', 'salt', 'hash')
            )
        db.conn.commit()
        sample = 'healing_potion'
        if sample not in ITEMS:
            raise RuntimeError('No baseline shop example for economy audit')
        baseline = sale.generic_item_sale_value(sample, ITEMS[sample])
        unit = legacy_currency_to_coins(baseline['silver'], baseline['gold'], baseline['mithril'])
        check(unit > 25, 'regression fixture must expose original arbitrage')
        db.add_item(71, sample, 4)
        db.record_shop_purchase_v1175(71, sample, 3, 25)
        db.record_shop_purchase_v1175(71, sample, 1, 40)
        stats['purchased_lots'] = 4
        check(db.shop_resale_total_v1175(71, sample, 4, unit) == 115,
              'mixed purchase prices did not cap each bought unit')
        sale.server = SimpleNamespace(db=db)
        sale.account_id = 71
        result = sale.bulk_sell_rewards_for_rows([(sample, 4)], shop_purchase_basis=True)
        check(result['silver'] == 115 and result['gold'] == 0,
              'sell all ignores shop purchase basis')
        check(db.remove_item(71, sample, 1), 'single removal failed')
        check(db.shop_resale_total_v1175(71, sample, 3, unit) == 90,
              'removing one purchased item retained stale tag')
        # Person-to-person trade preserves the cap; destination cannot launder it.
        check(db.transfer_inventory_item(71, 72, sample, 1), 'transfer failed')
        check(db.shop_resale_total_v1175(72, sample, 1, unit) == 25,
              'transfer laundered shop purchase price')
        # Bank deposit & withdrawal must retain price even when inventory is empty.
        bank_key = db.bank_purchase_lot_key_v1175(sample)
        db.move_shop_purchase_basis_v1175(72, sample, bank_key, 1)
        check(db.remove_item(72, sample, 1), 'bank deposit inventory removal failed')
        db.add_bank_item(72, sample, 1)
        check(db.remove_bank_item(72, sample, 1), 'bank withdraw removal failed')
        db.move_shop_purchase_basis_v1175(72, bank_key, sample, 1)
        db.add_item(72, sample, 1)
        check(db.shop_resale_total_v1175(72, sample, 1, unit) == 25,
              'bank laundering allowed')
        # Authentic loot of the same item is not subject to a purchased-item cap.
        db.add_item(72, sample, 1)
        check(db.shop_resale_total_v1175(72, sample, 2, unit) == 25 + unit,
              'earned loot was devalued')
        db.conn.close()
        db = Database(path)
        check(db.shop_resale_total_v1175(72, sample, 2, unit) == 25 + unit,
              'purchase ledger not persisted across DB reopen')
        stats['reopened'] = 1
        check(db.remove_item(72, sample, 2), 'sold mixed shop+loot stack not removed')
        check(db.shop_resale_total_v1175(72, sample, 1, unit) == unit,
              'stale purchase lot after stack removal')
        check(db.conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok',
              'SQLite integrity failed')
        check(not db.conn.execute('PRAGMA foreign_key_check').fetchall(),
              'foreign key integrity failed')
        db.conn.close()

    return {"checks": checks, "errors": errors, "error_count": len(errors), **stats}
