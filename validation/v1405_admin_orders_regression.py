# -*- coding: utf-8 -*-
"""Regression for admin SB cleanup shorthand and profession order cancellation."""
import asyncio


def run_admin_orders_v1405(runtime=None):
    from config.command_aliases import COMMAND_ALIAS_DEFINITIONS
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    errors = []
    count = 0

    def check(good, name):
        nonlocal count
        count += 1
        if not good:
            errors.append(name)

    # Static gate runs without booting the 17k-monster world.
    for alias in ('wyczysc', 'wyczyść'):
        check(COMMAND_ALIAS_DEFINITIONS.get(alias) == 'wipe',
              f'legacy clear alias {alias} must route to wipe handler')
    for alias in ('zamowienie', 'zamówienie', 'zamowienia', 'zamówienia'):
        check(COMMAND_ALIAS_DEFINITIONS.get(alias) == 'craftorders',
              f'order alias {alias} must route to crafting order handler')
    admin_source = (root / 'player/session_mixins/admin_tools.py').read_text(encoding='utf-8')
    order_source = (root / 'player/session_mixins/crafting_orders.py').read_text(encoding='utf-8')
    check('admin_error_cleanup_shortcut_v1405' in admin_source,
          'clear shorthand needs explicit guarded handler')
    check('admin_tools_v1224("log wyczysc naprawione POTWIERDZAM")' in admin_source,
          'short clear must use existing audited SB purge')
    check('abandon_crafting_order_v0600(self.account_id)' in order_source,
          'abandon order must use existing account-only database method')
    if runtime is None:
        return {'checks': count, 'errors': errors}

    # Runtime gate executes actual live session methods after server boot.
    from player.session_mixins.admin_tools import SessionAdminToolsMixin
    from player.session_mixins.crafting_orders import SessionCraftingOrdersV0600Mixin
    from player.session_mixins.command_registry import resolve_session_command

    class FakeDB:
        def __init__(self):
            self.conn = None
            self.fixed = 3
            self.active = 2
            self.purges = 0
            self.wipes = 0
            self.orders = {'item_id': '__gather__:ore:1', 'progress': 12}
            self.materials = 100
            self.completed_rewards = 500
            self.abandoned = 0

        def account_name(self, _):
            return 'Owner'

        def purge_resolved_admin_errors_v1371(self, _):
            self.purges += 1
            n = self.fixed
            self.fixed = 0
            return n

        def crafting_order_v0600(self, _):
            return self.orders

        def abandon_crafting_order_v0600(self, _):
            self.abandoned += 1
            self.orders = {'item_id': '', 'progress': 0}

    class FakeSession(SessionAdminToolsMixin, SessionCraftingOrdersV0600Mixin):
        def __init__(self, admin=True):
            self.admin = admin
            self.account_id = 15
            self.master_account_id = 7
            self.server = type('Server', (), {'db': FakeDB()})()
            self.messages = []

        def is_admin(self):
            return self.admin

        @staticmethod
        def normalize_description_query(s):
            return str(s or '').lower().strip()

        async def send(self, msg, **_kw):
            self.messages.append(str(msg))

    check(resolve_session_command('wyczysc', 'naprawione POTWIERDZAM') == 'wipe',
          'legacy wyczysc alias should resolve to guarded wipe handler')
    check(resolve_session_command('wyczyść', 'naprawione POTWIERDZAM') == 'wipe',
          'accented clear alias should resolve to guarded wipe handler')
    for alias in ('zamowienie', 'zamówienie', 'zamowienia', 'zamówienia'):
        check(resolve_session_command(alias, 'porzuć') == 'craftorders',
              f'order alias {alias} should route to crafting orders')

    async def main():
        owner = FakeSession()
        await owner.wipe_command('naprawione')
        check(owner.server.db.purges == 0, 'no purge without confirmation')
        check(any('POTWIERDZAM' in x for x in owner.messages), 'unconfirmed purge explains usage')
        await owner.wipe_command('naprawione POTWIERDZAM')
        check(owner.server.db.purges == 1, 'shorthand invokes SB purge exactly once')
        check(owner.server.db.active == 2 and owner.server.db.fixed == 0,
              'active errors preserved; only resolved cleared')
        check(owner.server.db.wipes == 0, 'shorthand never wipes characters')
        check(any('wyczyszczono 3' in x for x in owner.messages),
              'shorthand reports resolved error count')
        await owner.admin_command('wyczysc naprawione POTWIERDZAM')
        check(owner.server.db.wipes == 0, 'admin shortcut never wipes characters')
        check(owner.server.db.active == 2, 'admin shortcut preserves active errors')
        guest = FakeSession(admin=False)
        await guest.wipe_command('naprawione POTWIERDZAM')
        check(guest.server.db.purges == 0, 'non-admin cannot purge')
        await guest.admin_command('wyczysc naprawione POTWIERDZAM')
        check(guest.server.db.purges == 0, 'non-admin cannot purge via admin shortcut')
        await owner.handle_crafting_orders_v0600('porzuć')
        check(owner.server.db.abandoned == 1, 'profession order was abandoned')
        check(owner.server.db.orders['item_id'] == '', 'active order slot cleared')
        check(owner.server.db.materials == 100, 'materials and inventory preserved')
        check(owner.server.db.completed_rewards == 500, 'previous rewards preserved')
        check(any('Nie zabrano żadnych materiałów' in m for m in owner.messages),
              'abandonment explains inventory safety')
        await owner.handle_crafting_orders_v0600('porzuc')
        check(owner.server.db.abandoned == 1, 'no active order is a no-op')
    asyncio.run(main())
    return {'checks': count, 'errors': errors}


if __name__ == '__main__':
    result = run_admin_orders_v1405()
    print(result)
    if result['errors']:
        raise SystemExit(1)
