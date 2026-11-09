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


from .db_accounts_parts_v109 import (
    PasswordRecoveryV109Mixin,
    LegacyEmailV109Mixin,
    MasterAccountsV109Mixin,
    AccountIdentityV109Mixin,
    CharacterDeletionV109Mixin,
    CharacterRosterV109Mixin,
    CharacterSlotsV109Mixin,
    PresenceV109Mixin,
    CharacterNamesV109Mixin,
    FriendsV109Mixin,
    WalletReadV109Mixin,
)

class DatabaseAccountsMixin(
    PasswordRecoveryV109Mixin,
    LegacyEmailV109Mixin,
    MasterAccountsV109Mixin,
    AccountIdentityV109Mixin,
    CharacterDeletionV109Mixin,
    CharacterRosterV109Mixin,
    CharacterSlotsV109Mixin,
    PresenceV109Mixin,
    CharacterNamesV109Mixin,
    FriendsV109Mixin,
    WalletReadV109Mixin,
):
    """Publiczny interfejs bazy kont, zachowane krytyczne operacje zapisu."""

    def create_account(self, username, password):
        salt, digest = hash_password(password)
        cur = self.conn.execute(
            "INSERT INTO accounts(username,password_salt,password_hash) VALUES(?,?,?)",
            (username, salt, digest),
        )
        self.conn.commit()
        return cur.lastrowid


    def shared_wallet_for_master(self, master_account_id):
        outer_transaction_v104 = getattr(self.conn, "in_transaction", False)
        master_account_id = int(master_account_id)
        if getattr(self, '_v104_big_number_copy_rehearsal', False):
            from storage.big_number_copy_runtime_v10400 import read_exact_currency_copy
            result = read_exact_currency_copy(self, master_account_id, 'wallet')
            if result is not None:
                return result
        row = self.conn.execute(
            "SELECT silver,gold,mithril FROM account_wallet "
            "WHERE master_account_id=?",
            (master_account_id,),
        ).fetchone()
        if row:
            # v104 etap 12: REAL/TEXT z obcej lub uszkodzonej bazy nie moga
            # przejsc przez int() / float z utrata precyzji.
            from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
            wallet = tuple(require_sqlite_int64('account_wallet.' + axis, row[axis])
                           for axis in ('silver', 'gold', 'mithril'))
            silver, gold, mithril = normalize_currency_values(*wallet)
            if gold or mithril or silver != int(row["silver"]):
                self.set_shared_wallet_for_master(
                    master_account_id, silver, gold, mithril
                )
            return (silver, gold, mithril)

        # Bezpieczny fallback dla świeżego konta albo nietypowego starego save'a.
        # v104 etap 12: SQL SUM(INTEGER) potrafi przekroczyc int64 i
        # dla szczegolnie duzych sald zwrocic wyjatek. Zliczamy w Python int,
        # bez REAL/float. Nie sumujemy zadnego TEXT bez formalnej migracji.
        from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
        totals = [0, 0, 0]
        rows = self.conn.execute(
            """SELECT c.silver,c.gold,c.mithril
            FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=?""", (master_account_id,)
        )
        for row_values in rows:
            for idx, axis in enumerate(('silver', 'gold', 'mithril')):
                raw = row_values[idx]
                if raw is not None:
                    totals[idx] += require_sqlite_int64('characters.'+axis, raw)
        silver, gold, mithril = normalize_currency_values(*totals)
        self.conn.execute(
            "INSERT OR REPLACE INTO account_wallet("
            "master_account_id,silver,gold,mithril,updated_at"
            ") VALUES(?,?,?,?,CURRENT_TIMESTAMP)",
            (master_account_id, silver, gold, mithril),
        )
        if not outer_transaction_v104:
            self.conn.commit()
        return silver, gold, mithril


    def set_shared_wallet_for_master(self, master_account_id, silver, gold, mithril, *, commit=True):
        """v104 stage 11: one atomic wallet + legacy-character mirror operation.

        SAVEPOINT composes with an existing transaction (including save_character).
        A failed mirror never leaves a separately updated shared wallet.
        """
        outer_transaction_v104 = getattr(self.conn, "in_transaction", False)
        master_account_id = int(master_account_id)
        if getattr(self, '_v104_big_number_copy_rehearsal', False):
            from storage.big_number_copy_runtime_v10400 import write_exact_currency_copy
            result = write_exact_currency_copy(
                self, master_account_id, 'wallet', silver, gold, mithril)
            if commit and not outer_transaction_v104:
                self.conn.commit()
            return result
        silver, gold, mithril = normalize_currency_values(silver, gold, mithril)
        self.conn.execute("SAVEPOINT v104_wallet_atomic")
        try:
            self.conn.execute(
                """
                INSERT INTO account_wallet(master_account_id,silver,gold,mithril,updated_at)
                VALUES(?,?,?,?,CURRENT_TIMESTAMP)
                ON CONFLICT(master_account_id) DO UPDATE SET
                    silver=excluded.silver,
                    gold=excluded.gold,
                    mithril=excluded.mithril,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (master_account_id, silver, gold, mithril),
            )
            # Legacy readers still expect the mirrored balances on every slot.
            self.conn.execute(
                """
                UPDATE characters SET silver=?,gold=?,mithril=?
                WHERE account_id IN (
                    SELECT character_account_id FROM account_characters
                    WHERE master_account_id=?
                )
                """,
                (silver, gold, mithril, master_account_id),
            )
            self.conn.execute("RELEASE SAVEPOINT v104_wallet_atomic")
        except BaseException:
            self.conn.execute("ROLLBACK TO SAVEPOINT v104_wallet_atomic")
            self.conn.execute("RELEASE SAVEPOINT v104_wallet_atomic")
            raise
        if commit and not outer_transaction_v104:
            self.conn.commit()
        return silver, gold, mithril


    def set_shared_wallet_for_character(self, character_account_id, silver, gold, mithril, *, commit=True):
        return self.set_shared_wallet_for_master(
            self.master_account_for_character(character_account_id),
            silver, gold, mithril, commit=commit,
        )


    def apply_shared_wallet_to_character(self, character):
        silver, gold, mithril = self.shared_wallet_for_character(character.account_id)
        character.silver = silver
        character.gold = gold
        character.mithril = mithril
        return character


    def enable_big_number_copy_rehearsal_v104(self):
        """Opt in ONLY on a fenced, disposable database copy.

        This does not turn on BigNumber for a real server. It exercises the
        existing save_character / character_for_account methods on a copy.
        """
        from storage.big_number_copy_runtime_v10400 import _require_copy_path
        _require_copy_path(self)
        self._v104_big_number_copy_rehearsal = True


    def create_character_for_master(self, master_account_id, name, race, cls, name_cases, gender="nieokreślona"):
        if self.character_count_for_master(master_account_id) >= MAX_CHARACTERS_PER_ACCOUNT:
            raise ValueError("character_limit")

        slot = self._next_character_slot(master_account_id)
        if slot is None:
            raise ValueError("character_limit")

        existing_master_character = self.character_for_account(master_account_id)
        master_link = self.conn.execute(
            "SELECT 1 FROM account_characters WHERE character_account_id=?",
            (master_account_id,),
        ).fetchone()

        if slot == 1 and not existing_master_character and not master_link:
            character_account_id = int(master_account_id)
        else:
            character_account_id = self._create_hidden_character_account(
                master_account_id, slot
            )

        self.conn.execute(
            "INSERT INTO account_characters(master_account_id,character_account_id,slot) "
            "VALUES(?,?,?)",
            (master_account_id, character_account_id, slot),
        )
        try:
            self.create_character(
                character_account_id, name, race, cls, name_cases, gender=gender
            )
            wallet_row = self.conn.execute(
                "SELECT silver,gold,mithril FROM account_wallet "
                "WHERE master_account_id=?",
                (master_account_id,),
            ).fetchone()
            if wallet_row is None:
                # Pierwsza postać zakłada wspólny portfel z pakietem startowym.
                created = self.character_for_account(character_account_id)
                self.set_shared_wallet_for_master(
                    master_account_id,
                    created["silver"], created["gold"], created["mithril"],
                )
            else:
                # Każda następna postać dostaje dokładnie saldo konta,
                # bez ponownego przyznawania startowych monet.
                self.set_shared_wallet_for_master(
                    master_account_id,
                    wallet_row["silver"], wallet_row["gold"], wallet_row["mithril"],
                )
            # v0.34.5: Gildia jest dziedziczona przez nowe postacie tego samego
            # konta. Ranga zawsze startuje jako `member`; uprawnienia lidera/oficera
            # pozostają przy postaci, która faktycznie dostała tę rangę.
            self.ensure_character_guild_from_master_v0345(
                master_account_id, character_account_id
            )
        except Exception:
            self.conn.execute(
                "DELETE FROM account_characters WHERE master_account_id=? AND slot=?",
                (master_account_id, slot),
            )
            if character_account_id != master_account_id:
                self.conn.execute(
                    "DELETE FROM accounts WHERE id=?", (character_account_id,)
                )
            self.conn.commit()
            raise
        return character_account_id, slot


    def create_character(self, account_id, name, race, cls, name_cases, gender="nieokreślona"):
        rname, _, _race_strength, _race_dexterity, _race_constitution, _race_intelligence, _race_willpower = race
        cname, ctype, soul_weapon, weapon_base = cls
        raw_gender = str(gender or "").strip().casefold()
        if raw_gender in ("kobieta", "k"):
            gender = "kobieta"
        elif raw_gender in ("mężczyzna", "mezczyzna", "m"):
            gender = "mężczyzna"
        elif raw_gender in ("nieokreślona", "nieokreslona", ""):
            gender = "nieokreślona"
        else:
            raise ValueError("invalid_gender")
        if rname == "Driada" and gender != "kobieta":
            raise ValueError("dryad_female_only")
        starting_stats = class_starting_stats_for(race, cls)
        strength = starting_stats["strength"]
        dexterity = starting_stats["dexterity"]
        constitution = starting_stats["constitution"]
        intelligence = starting_stats["intelligence"]
        willpower = starting_stats["willpower"]
        charisma = starting_stats["charisma"]
        self.conn.execute(
            """
            INSERT INTO characters(
                account_id,name,
                name_nom,name_gen,name_dat,name_acc,name_ins,name_loc,name_voc,
                race,gender,class_name,class_type,soul_weapon,weapon_base,
                strength,dexterity,constitution,intelligence,willpower,charisma,
                stat_progress,soul_level,soul_xp,soul_tier,room_id,silver,gold,mithril,deaths
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,1,0,1,'square',?,?,?,0)
            """,
            (
                account_id, name,
                name_cases["nom"], name_cases["gen"], name_cases["dat"],
                name_cases["acc"], name_cases["ins"], name_cases["loc"],
                name_cases["voc"],
                rname, gender, cname, ctype, soul_weapon, weapon_base,
                strength, dexterity, constitution, intelligence, willpower, charisma,
                STARTING_SILVER, STARTING_GOLD, STARTING_MITHRIL,
            ),
        )
        self.conn.execute(
            "INSERT OR REPLACE INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)",
            (account_id, "healing_potion", 2),
        )
        if rname == "Cyborg":
            self.conn.execute(
                "INSERT OR REPLACE INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)",
                (account_id, "moogle_board", 1),
            )
        self.conn.execute(
            "INSERT OR IGNORE INTO class_progress(account_id,class_name,level,xp,active_slot) "
            "VALUES(?,?,1,0,1)",
            (account_id, cname),
        )
        self.conn.execute(
            "UPDATE class_progress SET active_slot=1 "
            "WHERE account_id=? AND class_name=?",
            (account_id, cname),
        )
        self.conn.commit()


    def save_character(self, c, commit=True):
        # v104 stage 10: refuse unrepresentable EXP / stats *before* the wallet
        # is updated, so an overflow cannot leave partial changes behind.
        outer_transaction_v104 = getattr(self.conn, "in_transaction", False)
        from core.sqlite_numeric_guard_v10400 import preflight_character_v104
        from core.big_numbers_v10400 import SQLITE_INT64_MAX
        rehearsal = getattr(self, '_v104_big_number_copy_rehearsal', False)
        if rehearsal:
            from storage.big_number_copy_runtime_v10400 import (
                CHARACTER_COPY_AXES, _require_copy_path, read_exact_progression_copy,
                currency_total_copy,
            )
            _require_copy_path(self)  # fail closed if the test marker disappears
        live_character = (getattr(self, '_v104_live_exact_character', False)
                          and not rehearsal)
        if live_character:
            from storage.big_number_live_character_v10400 import CHARACTER_AXES
        axes = (frozenset(CHARACTER_COPY_AXES) if rehearsal else
                frozenset(CHARACTER_AXES) if live_character else frozenset())
        preflight_character_v104(c, exact_text_axes=axes)
        previous_currency = (c.silver, c.gold, c.mithril)
        # The legacy stat_progress column is derived from the six independent
        # progress fields; its exact shadow must use the SAME derived value.
        derived_stat_progress = min(
            c.strength_progress, c.dexterity_progress, c.constitution_progress,
            c.intelligence_progress, c.willpower_progress, c.charisma_progress,
        )
        def _mirror(axis, value):
            return min(value, SQLITE_INT64_MAX) if (rehearsal or live_character) and axis in axes else value

        self.conn.execute("SAVEPOINT v104_character_atomic")
        try:
            if rehearsal:
                # CAS: refuse to overwrite a shadow whose old INTEGER mirror
                # was modified by an unconverted legacy path.
                for _axis in CHARACTER_COPY_AXES:
                    read_exact_progression_copy(self, c.account_id, _axis)
            if live_character:
                from storage.big_number_live_character_v10400 import stage_live_character_axes
                stage_live_character_axes(self, c.account_id, {
                    axis: derived_stat_progress if axis == 'stat_progress'
                    else getattr(c, axis) for axis in CHARACTER_AXES
                })
            (
                c.silver,
                c.gold,
                c.mithril,
            ) = (
                (currency_total_copy(c.silver, c.gold, c.mithril), 0, 0)
                if rehearsal else normalize_currency_values(c.silver, c.gold, c.mithril)
            )

            # v0.8.32: waluta należy do konta głównego, nie do slotu postaci.
            self.set_shared_wallet_for_character(
                c.account_id, c.silver, c.gold, c.mithril, commit=False
            )

            result = self.conn.execute(
                """
                UPDATE characters SET
                    strength=?, dexterity=?, constitution=?, intelligence=?, willpower=?,
                    stat_progress=?, strength_progress=?, dexterity_progress=?,
                    constitution_progress=?, intelligence_progress=?, willpower_progress=?,
                    charisma_progress=?, soul_level=?, soul_xp=?, soul_tier=?,
                    soul_weapon_mastery_level=?, soul_weapon_mastery_xp=?, room_id=?,
                    silver=?, gold=?, mithril=?, charisma=?, character_level=?, character_xp=?, deaths=?,
                    guild_reputation_json=?, guild_exams_json=?,
                    guild_class_quests_json=?, guild_bounty_json=?,
                    loot_filter=?, active_title=?
                WHERE account_id=?
                """,
                (
                    c.strength, c.dexterity, c.constitution, c.intelligence, c.willpower,
                    _mirror('stat_progress', derived_stat_progress),
                    _mirror('strength_progress', c.strength_progress),
                    _mirror('dexterity_progress', c.dexterity_progress),
                    _mirror('constitution_progress', c.constitution_progress),
                    _mirror('intelligence_progress', c.intelligence_progress),
                    _mirror('willpower_progress', c.willpower_progress),
                    _mirror('charisma_progress', c.charisma_progress),
                    _mirror('soul_level', c.soul_level), _mirror('soul_xp', c.soul_xp),
                    _mirror('soul_tier', c.soul_tier),
                    _mirror('soul_weapon_mastery_level', c.soul_weapon_mastery_level),
                    _mirror('soul_weapon_mastery_xp', c.soul_weapon_mastery_xp), c.room_id,
                    _mirror('silver', c.silver), _mirror('gold', c.gold),
                    _mirror('mithril', c.mithril), c.charisma,
                    _mirror('character_level', c.character_level),
                    _mirror('character_xp', c.character_xp), c.deaths,
                    c.guild_reputation_json, c.guild_exams_json,
                    c.guild_class_quests_json, c.guild_bounty_json,
                    c.loot_filter, c.active_title,
                    c.account_id,
                ),
            )
            if result.rowcount != 1:
                raise LookupError("Nie znaleziono postaci - zapis wycofany.")
            if live_character:
                from storage.big_number_live_character_v10400 import read_live_character_axes
                updated = self.conn.execute('SELECT * FROM characters WHERE account_id=?',
                                            (c.account_id,)).fetchone()
                actual = read_live_character_axes(self, c.account_id, updated)
                for axis in CHARACTER_AXES:
                    expected = derived_stat_progress if axis == 'stat_progress' else getattr(c, axis)
                    if actual[axis] != expected:
                        raise ValueError('BigNumber: niedokladny odczyt postaci: ' + axis)
            if rehearsal:
                from storage.big_number_shadow_v10400 import install_shadow_schema, stage_shadow
                install_shadow_schema(self.conn)
                for _axis in CHARACTER_COPY_AXES:
                    _exact_value = (derived_stat_progress if _axis == 'stat_progress'
                                    else getattr(c, _axis))
                    if _axis in ('silver', 'gold', 'mithril'):
                        existed = self.conn.execute('''SELECT 1 FROM big_number_shadow_v10400
                            WHERE account_id=? AND axis=?''',
                            (c.account_id, 'characters.' + _axis)).fetchone()
                        if _exact_value <= SQLITE_INT64_MAX and existed is None:
                            continue
                    stage_shadow(self.conn, c.account_id, 'characters.' + _axis,
                                 _exact_value, base_value=min(_exact_value, SQLITE_INT64_MAX))
                from storage.big_number_copy_runtime_v10400 import _mark_complete_copy_group, AXES
                _mark_complete_copy_group(self.conn, c.account_id,
                    tuple('characters.' + axis for axis in AXES))
            self.conn.execute("RELEASE SAVEPOINT v104_character_atomic")
        except BaseException:
            self.conn.execute("ROLLBACK TO SAVEPOINT v104_character_atomic")
            self.conn.execute("RELEASE SAVEPOINT v104_character_atomic")
            c.silver, c.gold, c.mithril = previous_currency
            raise
        if commit and not outer_transaction_v104:
            self.conn.commit()

