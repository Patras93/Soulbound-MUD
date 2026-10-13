# -*- coding: utf-8 -*-
"""v3.00.3: isolated character wipe / mercenary data / public help checks.

No production DB is opened and no player information is read or modified.
"""
import sqlite3
from pathlib import Path

from storage.db_accounts import DatabaseAccountsMixin
from storage.db_mercenaries import DatabaseMercenariesMixin
from storage.schema_core import create_core_schema
from storage.schema_progression import create_progression_schema


class _DB(DatabaseAccountsMixin, DatabaseMercenariesMixin):
    pass


def run_regression():
    checks = 0

    def check(ok, label):
        nonlocal checks
        if not ok:
            raise AssertionError("HELP/WIPE v3.00.3: " + label)
        checks += 1

    db = _DB()
    db.conn = sqlite3.connect(":memory:")
    db.conn.row_factory = sqlite3.Row
    db.conn.execute("PRAGMA foreign_keys=ON")
    try:
        create_core_schema(db)
        create_progression_schema(db)
        db.create_mercenary_schema()
        master = db.create_account("PatrasTest", "StrongTestPassword_111")
        secondary = db.create_account("__char_1_2_test", "StrongTestPassword_222")
        other_master = db.create_account("AnotherPlayerTest", "StrongTestPassword_333")
        other_secondary = db.create_account("__char_3_2_test", "StrongTestPassword_444")
        check(len({master, secondary, other_master, other_secondary}) == 4, "distinct test IDs")

        def character(owner, name, slot, parent):
            db.conn.execute(
                "INSERT INTO account_characters(master_account_id,character_account_id,slot) VALUES (?,?,?)",
                (parent, owner, slot),
            )
            db.conn.execute(
                "INSERT INTO characters(account_id,name,race,class_name,class_type,soul_weapon,weapon_base,"
                "strength,dexterity,constitution,intelligence,willpower) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (owner, name, "czlowiek", "Wojownik", "physical", "weapon", 1, 20, 20, 20, 20, 20),
            )

        character(master, "HeroMain", 1, master)
        character(secondary, "HeroSecond", 2, master)
        character(other_master, "OtherMain", 1, other_master)
        character(other_secondary, "OtherSecond", 2, other_master)

        db.conn.execute("INSERT INTO account_emails_v1223(account_id,email,verified_at) VALUES (?,?,?)",
                        (master, "patras-test@example.invalid", 12345))
        db.conn.execute("INSERT INTO account_wallet(master_account_id,silver) VALUES (?,1000)", (master,))
        db.conn.execute("INSERT INTO account_wallet(master_account_id,silver) VALUES (?,2000)", (other_master,))
        db.conn.execute("INSERT INTO inventory(account_id,item_id,quantity) VALUES (?,?,3)", (master,"old_equipment"))

        def hire(owner, role):
            db.conn.execute(
                "INSERT INTO mercenary_contracts(character_account_id,role,expires_at) VALUES (?,?,0)",
                (owner, role),
            )
            db.conn.execute(
                "INSERT INTO mercenary_progress_v1220(character_account_id,role,xp,specialization,actions) "
                "VALUES (?,?,321,?,7)", (owner, role, "obrona"),
            )

        for ident, role in ((master,"mag"),(secondary,"paladyn"),
                            (other_master,"druid"),(other_secondary,"wojownik"),(99999,"straznik")):
            hire(ident, role)
        db.conn.commit()
        check(db.conn.execute("SELECT count(*) FROM mercenary_contracts").fetchone()[0]==5,
              "five preexisting hires incl orphan")
        db.create_mercenary_schema()  # simulates a version upgrade
        check(db.conn.execute("SELECT count(*) FROM mercenary_contracts").fetchone()[0]==5,
              "startup preserves every contract including old orphans")
        check(db.conn.execute("SELECT count(*) FROM mercenary_progress_v1220").fetchone()[0]==5,
              "startup preserves every progress entry including old orphans")
        check(tuple(db.conn.execute(
              "SELECT xp,specialization,actions FROM mercenary_progress_v1220 "
              "WHERE character_account_id=99999").fetchone())==(321,"obrona",7),
              "orphan progress not modified during migration")
        check(len(db.mercenary_contracts(master))==1, "existing first character untouched")
        check(len(db.mercenary_contracts(other_master))==1, "different player untouched")
        check(len(db.mercenary_contracts(other_secondary))==1, "different player's secondary untouched")

        # Deletion of one secondary character must not mutate any other character.
        deleted=db.delete_character_for_master(master, secondary)
        check(deleted is not None and deleted["name"]=="HeroSecond", "delete secondary succeeded")
        check(db.conn.execute("SELECT id FROM accounts WHERE id=?",(secondary,)).fetchone() is None,
              "hidden profile account deleted")
        for table in ("mercenary_contracts", "mercenary_progress_v1220"):
            check(db.conn.execute(f"SELECT count(*) FROM {table} WHERE character_account_id=?",(secondary,)).fetchone()[0]==0,
                  f"secondary profile {table} cleared")
        check(len(db.mercenary_contracts(master))==1, "main character hires retained")
        check(len(db.mercenary_contracts(other_master))==1, "other main character retained")
        check(len(db.mercenary_contracts(other_secondary))==1, "other secondary retained")

        # wipe my characters must delete original master char data even when login ID survives.
        count=db.wipe_characters_for_master(master)
        check(count==1, "wipe-my reports correct count")
        check(db.conn.execute("SELECT id FROM accounts WHERE id=?",(master,)).fetchone() is not None,
              "master login survives")
        check(db.conn.execute("SELECT id FROM accounts WHERE id=?",(other_master,)).fetchone() is not None,
              "other player's login survives")
        check(db.conn.execute("SELECT count(*) FROM account_characters WHERE master_account_id=?",(master,)).fetchone()[0]==0,
              "all player char links removed")
        check(db.conn.execute("SELECT count(*) FROM inventory WHERE account_id=?",(master,)).fetchone()[0]==0,
              "inventory wiped")
        check(db.conn.execute("SELECT count(*) FROM account_wallet WHERE master_account_id=?",(master,)).fetchone()[0]==0,
              "wallet wiped")
        check(db.conn.execute("SELECT count(*) FROM account_emails_v1223 WHERE account_id=?",(master,)).fetchone()[0]==1,
              "account email preserved")
        for table in ("mercenary_contracts", "mercenary_progress_v1220"):
            check(db.conn.execute(f"SELECT count(*) FROM {table} WHERE character_account_id=?",(master,)).fetchone()[0]==0,
                  f"primary character {table} wiped")
            check(db.conn.execute(f"SELECT count(*) FROM {table} WHERE character_account_id=?",(other_master,)).fetchone()[0]==1,
                  f"other player's {table} remains")
        # When slot 1 gets the same master_account_id after wipe, no old hire returns.
        character(master,"NewHeroSameLogin",1,master)
        check(len(db.mercenary_contracts(master))==0, "new char doesn't inherit old hires")
        check(db.mercenary_progress_v1220(master,"mag")=={"xp":0,"specialization":"","actions":0},
              "new char doesn't inherit mercenary tactics")
        hire(master,"kaplan")
        check(len(db.mercenary_contracts(master))==1, "newly hired mercenary works")
        count,masters=db.wipe_all_characters_preserve_accounts()
        check(count==3, "global wipe finds all remaining characters")
        check(set(masters)=={master,other_master}, "global wipe targets only real logins")
        for ident in (master,other_master):
            check(db.conn.execute("SELECT count(*) FROM account_characters WHERE master_account_id=?",(ident,)).fetchone()[0]==0,
                  "no characters left after global wipe")
            check(db.conn.execute("SELECT id FROM accounts WHERE id=?",(ident,)).fetchone() is not None,
                  "login preserved after global wipe")
        check(db.conn.execute("SELECT count(*) FROM mercenary_contracts").fetchone()[0]==0,
              "all contracts wiped globally (including old orphans)")
        check(db.conn.execute("SELECT count(*) FROM mercenary_progress_v1220").fetchone()[0]==0,
              "all tactics wiped globally (including old orphans)")
        check(db.conn.execute("PRAGMA foreign_key_check").fetchall()==[],
              "foreign keys still consistent")
        # User-facing help corrections, no code paths for forced 600 level cap.
        root=Path(__file__).resolve().parents[1]
        code=(root/'admin/help_truth_current.py').read_text(encoding='utf-8')
        for marker in ('HELP_TOPICS["progresja800"]','HELP_TOPICS["multiclass"]',
                       'HELP_TOPICS["wzniesienie"]','HELP_TOPICS["worldtier"]',
                       'Biegłości 800','Skill Level 1-800','nie mają limitu'):
            check(marker in code, 'current help marker '+marker)
        classsrc=(root/'player/session_mixins/class_progression.py').read_text(encoding='utf-8')
        check('Biegłość {CLASS_MASTERY_MAX_LEVEL}' in classsrc,
              'ascension experience text draws from cap constant')
        worldsrc=(root/'player/session_mixins/world_events_endgame.py').read_text(encoding='utf-8')
        check('Biegłości {CLASS_MASTERY_MAX_LEVEL}' in worldsrc,
              'world tier 2 requirement text draws from cap constant')
        return checks
    finally:
        db.conn.close()


if __name__=='__main__':
    print(f'HELP + WIPE MERCENARIES v3.00.3: {run_regression()} checks PASS')
