# -*- coding: utf-8 -*-
"""Accounts, characters, shared wallet and presence."""

import secrets
import time

from core.bootstrap_economy_professions import (
    MAX_CHARACTERS_PER_ACCOUNT, STARTING_GOLD, STARTING_MITHRIL, STARTING_SILVER,
    normalize_currency_values,
)
from core.classes_skills import class_starting_stats_for
from network.protocol_gameplay_utils import hash_password

class DatabaseAccountsMixin:
    def account_name(self, account_id):
        row = self.conn.execute(
            "SELECT username FROM accounts WHERE id=?", (int(account_id),)
        ).fetchone()
        return str(row["username"]) if row else ""

    def wipe_characters_for_master(self, master_account_id):
        """Usuń postacie/progres konta, ale zachowaj login i hasło konta."""
        master_account_id = int(master_account_id)
        rows = self.conn.execute(
            "SELECT character_account_id FROM account_characters WHERE master_account_id=? ORDER BY slot",
            (master_account_id,),
        ).fetchall()
        char_ids = [int(row["character_account_id"]) for row in rows]

        # Ukryte konta profili można bezpiecznie usunąć — FK CASCADE czyści ich dane.
        for char_id in char_ids:
            if char_id != master_account_id:
                self.conn.execute("DELETE FROM accounts WHERE id=?", (char_id,))

        # Pierwsza postać może używać ID konta głównego, więc kasujemy jej dane,
        # ale nigdy rekordu logowania w accounts.
        if master_account_id in char_ids:
            tables = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            protected = {"accounts", "account_characters", "account_wallet"}
            for table_row in tables:
                table = str(table_row["name"])
                if table in protected:
                    continue
                columns = {
                    str(col["name"])
                    for col in self.conn.execute(f'PRAGMA table_info("{table}")').fetchall()
                }
                if "account_id" in columns:
                    self.conn.execute(
                        f'DELETE FROM "{table}" WHERE account_id=?',
                        (master_account_id,),
                    )

        self.conn.execute(
            "DELETE FROM account_characters WHERE master_account_id=?",
            (master_account_id,),
        )
        # Portfel jest częścią postępu gry, nie danych logowania. Nowa pierwsza
        # postać ponownie dostanie normalny pakiet startowy.
        self.conn.execute(
            "DELETE FROM account_wallet WHERE master_account_id=?",
            (master_account_id,),
        )
        self.conn.commit()
        return len(char_ids)

    def delete_character_for_master(self, master_account_id, character_account_id):
        """v0.9.1: usuń dokładnie jedną postać bez kasowania konta ani wspólnego portfela.

        Pierwsza postać może używać ID konta głównego, dlatego nie wolno wtedy
        usuwać rekordu z accounts. Dodatkowe postacie mają ukryte konta techniczne
        i ich usunięcie przez FK CASCADE czyści cały własny progres postaci.
        """
        master_account_id = int(master_account_id)
        character_account_id = int(character_account_id)
        row = self.conn.execute(
            """
            SELECT ac.slot, ac.character_account_id, c.name
            FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=? AND ac.character_account_id=?
            """,
            (master_account_id, character_account_id),
        ).fetchone()
        if not row:
            return None

        slot = int(row["slot"])
        name = str(row["name"])

        if character_account_id != master_account_id:
            # Ukryty profil postaci. Usunięcie konta technicznego uruchamia
            # ON DELETE CASCADE dla całego progresu i samego powiązania slotu.
            self.conn.execute(
                "DELETE FROM accounts WHERE id=?", (character_account_id,)
            )
        else:
            # Slot oparty na koncie głównym: zachowujemy login, hasło i
            # account_wallet, a czyścimy wyłącznie dane tej postaci.
            tables = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            protected = {"accounts", "account_characters", "account_wallet"}
            for table_row in tables:
                table = str(table_row["name"])
                if table in protected:
                    continue
                columns = {
                    str(col["name"])
                    for col in self.conn.execute(
                        f'PRAGMA table_info("{table}")'
                    ).fetchall()
                }
                if "account_id" in columns:
                    self.conn.execute(
                        f'DELETE FROM "{table}" WHERE account_id=?',
                        (master_account_id,),
                    )
            self.conn.execute(
                "DELETE FROM account_characters WHERE master_account_id=? AND character_account_id=?",
                (master_account_id, character_account_id),
            )

        self.conn.commit()
        return {"slot": slot, "name": name}

    def wipe_all_characters_preserve_accounts(self):
        masters = [
            int(row["id"])
            for row in self.conn.execute(
                "SELECT id FROM accounts WHERE id NOT IN ("
                "SELECT character_account_id FROM account_characters "
                "WHERE character_account_id<>master_account_id) ORDER BY id"
            ).fetchall()
        ]
        removed = 0
        for master_id in masters:
            removed += self.wipe_characters_for_master(master_id)
        return removed, masters

    def master_accounts(self):
        """v0.30.1: lista prawdziwych kont logowania, bez ukrytych profili postaci."""
        return self.conn.execute(
            """
            SELECT a.id,a.username,COUNT(ac.character_account_id) AS character_count
            FROM accounts a
            LEFT JOIN account_characters ac ON ac.master_account_id=a.id
            WHERE a.id NOT IN (
                SELECT character_account_id FROM account_characters
                WHERE character_account_id<>master_account_id
            )
            GROUP BY a.id,a.username
            ORDER BY a.username COLLATE NOCASE,a.id
            """
        ).fetchall()

    def master_account_by_name(self, username):
        """v0.30.1: znajdź tylko konto główne; profil techniczny postaci nie jest celem admina."""
        return self.conn.execute(
            """
            SELECT a.* FROM accounts a
            WHERE a.username=? COLLATE NOCASE
              AND a.id NOT IN (
                  SELECT character_account_id FROM account_characters
                  WHERE character_account_id<>master_account_id
              )
            """,
            (username,),
        ).fetchone()

    def account_by_name(self, username):
        return self.conn.execute(
            "SELECT * FROM accounts WHERE username=? COLLATE NOCASE", (username,)
        ).fetchone()

    def create_account(self, username, password):
        salt, digest = hash_password(password)
        cur = self.conn.execute(
            "INSERT INTO accounts(username,password_salt,password_hash) VALUES(?,?,?)",
            (username, salt, digest),
        )
        self.conn.commit()
        return cur.lastrowid

    def is_character_profile(self, account_id):
        row = self.conn.execute(
            "SELECT 1 FROM account_characters "
            "WHERE character_account_id=? AND master_account_id<>character_account_id",
            (account_id,),
        ).fetchone()
        return row is not None

    def master_account_for_character(self, character_account_id):
        row = self.conn.execute(
            "SELECT master_account_id FROM account_characters "
            "WHERE character_account_id=?",
            (character_account_id,),
        ).fetchone()
        if row:
            return int(row["master_account_id"])
        return int(character_account_id)

    def shared_wallet_for_master(self, master_account_id):
        master_account_id = int(master_account_id)
        row = self.conn.execute(
            "SELECT silver,gold,mithril FROM account_wallet "
            "WHERE master_account_id=?",
            (master_account_id,),
        ).fetchone()
        if row:
            silver, gold, mithril = normalize_currency_values(
                row["silver"], row["gold"], row["mithril"]
            )
            if gold or mithril or silver != int(row["silver"]):
                self.set_shared_wallet_for_master(
                    master_account_id, silver, gold, mithril
                )
            return (silver, gold, mithril)

        # Bezpieczny fallback dla świeżego konta albo nietypowego starego save'a.
        sums = self.conn.execute(
            """
            SELECT COALESCE(SUM(c.silver),0) AS silver,
                   COALESCE(SUM(c.gold),0) AS gold,
                   COALESCE(SUM(c.mithril),0) AS mithril
            FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=?
            """,
            (master_account_id,),
        ).fetchone()
        silver, gold, mithril = normalize_currency_values(
            int(sums["silver"] or 0), int(sums["gold"] or 0), int(sums["mithril"] or 0)
        )
        self.conn.execute(
            "INSERT OR REPLACE INTO account_wallet("
            "master_account_id,silver,gold,mithril,updated_at"
            ") VALUES(?,?,?,?,CURRENT_TIMESTAMP)",
            (master_account_id, silver, gold, mithril),
        )
        self.conn.commit()
        return silver, gold, mithril

    def shared_wallet_for_character(self, character_account_id):
        return self.shared_wallet_for_master(
            self.master_account_for_character(character_account_id)
        )

    def set_shared_wallet_for_master(self, master_account_id, silver, gold, mithril, *, commit=True):
        master_account_id = int(master_account_id)
        silver, gold, mithril = normalize_currency_values(silver, gold, mithril)
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
        # Trzymamy kolumny legacy zsynchronizowane, żeby wszystkie starsze
        # fragmenty gry i narzędzia administracyjne widziały to samo saldo.
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
        if commit:
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

    def character_for_account(self, account_id):
        return self.conn.execute(
            "SELECT * FROM characters WHERE account_id=?", (account_id,)
        ).fetchone()

    def characters_for_master(self, master_account_id):
        return self.conn.execute(
            """
            SELECT ac.slot, ac.character_account_id, c.*
            FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=?
            ORDER BY ac.slot
            """,
            (master_account_id,),
        ).fetchall()

    def character_count_for_master(self, master_account_id):
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM account_characters "
            "WHERE master_account_id=?",
            (master_account_id,),
        ).fetchone()
        return int(row["n"] or 0) if row else 0

    def _next_character_slot(self, master_account_id):
        used = {
            int(r["slot"]) for r in self.conn.execute(
                "SELECT slot FROM account_characters WHERE master_account_id=?",
                (master_account_id,),
            ).fetchall()
        }
        for slot in range(1, MAX_CHARACTERS_PER_ACCOUNT + 1):
            if slot not in used:
                return slot
        return None

    def _create_hidden_character_account(self, master_account_id, slot):
        # Profil jest wyłącznie technicznym kluczem danych postaci. Nie można
        # zalogować się do niego z ekranu logowania.
        while True:
            username = f"__char_{master_account_id}_{slot}_{secrets.token_hex(6)}"
            if not self.account_by_name(username):
                break
        salt, digest = hash_password(secrets.token_urlsafe(32))
        cur = self.conn.execute(
            "INSERT INTO accounts(username,password_salt,password_hash) VALUES(?,?,?)",
            (username, salt, digest),
        )
        return int(cur.lastrowid)

    def create_character_for_master(self, master_account_id, name, race, cls, name_cases):
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
                character_account_id, name, race, cls, name_cases
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

    def mark_player_login_v0363(self, account_id, now_ts=None):
        now_ts = int(time.time() if now_ts is None else now_ts)
        self.conn.execute(
            "INSERT INTO player_presence_v0363(account_id,last_login_ts,last_seen_ts,login_count) VALUES(?,?,?,1) "
            "ON CONFLICT(account_id) DO UPDATE SET last_login_ts=excluded.last_login_ts,last_seen_ts=excluded.last_seen_ts,login_count=player_presence_v0363.login_count+1",
            (int(account_id), now_ts, now_ts),
        )
        self.conn.commit()

    def mark_player_logout_v0363(self, account_id, now_ts=None):
        now_ts = int(time.time() if now_ts is None else now_ts)
        self.conn.execute(
            "INSERT INTO player_presence_v0363(account_id,last_logout_ts,last_seen_ts,login_count) VALUES(?,?,?,0) "
            "ON CONFLICT(account_id) DO UPDATE SET last_logout_ts=excluded.last_logout_ts,last_seen_ts=excluded.last_seen_ts",
            (int(account_id), now_ts, now_ts),
        )
        self.conn.commit()

    def player_presence_v0363(self, account_id):
        return self.conn.execute(
            "SELECT last_login_ts,last_logout_ts,last_seen_ts,login_count FROM player_presence_v0363 WHERE account_id=?",
            (int(account_id),),
        ).fetchone()

    def character_name_exists(self, name):
        return self.conn.execute(
            "SELECT 1 FROM characters WHERE name=? COLLATE NOCASE", (name,)
        ).fetchone() is not None

    def character_account_id_by_name_v0928(self, name):
        row = self.conn.execute(
            "SELECT account_id FROM characters WHERE name=? COLLATE NOCASE",
            (str(name or "").strip(),),
        ).fetchone()
        return int(row["account_id"]) if row else None

    def character_name_by_account_v0928(self, account_id):
        row = self.conn.execute(
            "SELECT name FROM characters WHERE account_id=?",
            (int(account_id),),
        ).fetchone()
        return str(row["name"]) if row else None

    def are_friends_v0928(self, account_id, friend_account_id):
        return self.conn.execute(
            "SELECT 1 FROM player_friends_v0928 WHERE account_id=? AND friend_account_id=?",
            (int(account_id), int(friend_account_id)),
        ).fetchone() is not None

    def create_character(self, account_id, name, race, cls, name_cases):
        rname, _, _race_strength, _race_dexterity, _race_constitution, _race_intelligence, _race_willpower = race
        cname, ctype, soul_weapon, weapon_base = cls
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
                race,class_name,class_type,soul_weapon,weapon_base,
                strength,dexterity,constitution,intelligence,willpower,charisma,
                stat_progress,soul_level,soul_xp,soul_tier,room_id,silver,gold,mithril,deaths
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,1,0,1,'square',?,?,?,0)
            """,
            (
                account_id, name,
                name_cases["nom"], name_cases["gen"], name_cases["dat"],
                name_cases["acc"], name_cases["ins"], name_cases["loc"],
                name_cases["voc"],
                rname, cname, ctype, soul_weapon, weapon_base,
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

    def save_character(self, c):
        (
            c.silver,
            c.gold,
            c.mithril,
        ) = normalize_currency_values(
            c.silver,
            c.gold,
            c.mithril,
        )

        # v0.8.32: waluta należy do konta głównego, nie do slotu postaci.
        self.set_shared_wallet_for_character(
            c.account_id, c.silver, c.gold, c.mithril, commit=False
        )

        self.conn.execute(
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
                min(c.strength_progress, c.dexterity_progress, c.constitution_progress,
                    c.intelligence_progress, c.willpower_progress, c.charisma_progress),
                c.strength_progress, c.dexterity_progress, c.constitution_progress,
                c.intelligence_progress, c.willpower_progress, c.charisma_progress,
                c.soul_level, c.soul_xp, c.soul_tier,
                c.soul_weapon_mastery_level, c.soul_weapon_mastery_xp, c.room_id,
                c.silver, c.gold, c.mithril, c.charisma, c.character_level, c.character_xp, c.deaths,
                c.guild_reputation_json, c.guild_exams_json,
                c.guild_class_quests_json, c.guild_bounty_json,
                c.loot_filter, c.active_title,
                c.account_id,
            ),
        )
        self.conn.commit()
