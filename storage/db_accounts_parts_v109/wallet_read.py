# -*- coding: utf-8 -*-
"""Wydzielone metody bazy kont: wallet_read."""
from .dependencies import *

class WalletReadV109Mixin:
    def shared_wallet_for_character(self, character_account_id):
        return self.shared_wallet_for_master(
            self.master_account_for_character(character_account_id)
        )
