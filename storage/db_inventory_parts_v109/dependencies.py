# -*- coding: utf-8 -*-
"""Historyczne zaleznosci baz SQLite: nie zmieniac semantyki transakcji."""
# -*- coding: utf-8 -*-
"""Bank, inventory, equipment, storage, transfers and crafting persistence."""

import json

from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL, normalize_currency_values
from storage.db_shared import DROP_HISTORY_LIMIT, V03042_EQ_UPGRADE_MAX, is_craft_material_storage_item

