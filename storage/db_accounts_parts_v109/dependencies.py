# -*- coding: utf-8 -*-
"""Wspólne importy starego modułu kont. Nie zmieniać ich znaczenia."""
# -*- coding: utf-8 -*-
"""Accounts, characters, shared wallet and presence."""

import secrets
import time
import hashlib
import hmac

from core.bootstrap_economy_professions import (
    MAX_CHARACTERS_PER_ACCOUNT, STARTING_GOLD, STARTING_MITHRIL, STARTING_SILVER,
    normalize_currency_values,
)
from core.classes_skills import class_starting_stats_for
from storage.db_shared import hash_password

