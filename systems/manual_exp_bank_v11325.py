# -*- coding: utf-8 -*-
"""Manual redemption of existing saved EXP-bank balances, one category at a time.

Do not scale the saved amount by new XP event / racial bonuses. Every debit and
progression update must roll back together on failure. Never touch another account.
"""
from __future__ import annotations
import copy

MAX_SAFE_AWARD = 1_000_000_000  # bounded transaction time; remaining bank untouched


def _credit(session, kind, key, amount):
    db, char, account = session.server.db, session.character, session.account_id
    if kind == 'character':
        from core.live_level_caps_v5200 import cap
        if cap('postac') is not None and char.character_level >= cap('postac'):
            return False
        char.add_character_xp(amount)
        db.save_character(char, commit=False)
    elif kind == 'soul':
        from core.live_level_caps_v5200 import cap
        if cap('dusza') is not None and char.soul_level >= cap('dusza'):
            return False
        char.add_soul_xp(amount)
        db.save_character(char, commit=False)
    elif kind == 'class':
        row=db.class_progress_row(account,key)
        if row is None:
            return False
        from core.live_level_caps_v5200 import cap
        if cap('bieglosc') is not None and int(row['level']) >= cap('bieglosc'):
            return False
        db.add_class_mastery_xp(account,key,amount)
    elif kind == 'skill':
        # Never turn an unlearned skill into an available progression track.
        if db.conn.execute('SELECT 1 FROM learned_skills WHERE account_id=? AND skill_id=?',(account,key)).fetchone() is None:
            return False
        db.add_skill_xp(account,key,amount)
    elif kind == 'stat':
        # Historical banks may store translated stat source keys.
        aliases={'siła':'strength','sila':'strength','zręczność':'dexterity',
                 'zrecznosc':'dexterity','kondycja':'constitution',
                 'inteligencja':'intelligence','siła woli':'willpower',
                 'sila woli':'willpower','charyzma':'charisma'}
        stat_key=aliases.get(str(key).casefold(),str(key).casefold())
        if stat_key not in char.STAT_PROGRESS_FIELDS:
            return False
        _,value_field,xp_field=char.STAT_PROGRESS_FIELDS[stat_key]
        progress=int(getattr(char,xp_field))+amount
        original_stat=int(getattr(char,value_field))
        # No new reward multipliers on old banked XP.
        while progress>=char.stat_growth_threshold_for(stat_key) and int(getattr(char,value_field))==original_stat:
            progress-=char.stat_growth_threshold_for(stat_key)
            setattr(char,value_field,int(getattr(char,value_field))+1)
        setattr(char,xp_field,progress)
        db.save_character(char,commit=False)
    elif kind in ('profession','tool'):
        from core.live_level_caps_v5200 import cap
        axis='profesje' if kind=='profession' else 'narzedzia'
        row=db.profession(account,key) if kind=='profession' else db.tool(account,key)
        level,xp=int(row['level']),int(row['xp'])+amount
        axis_cap=cap(axis)
        if axis_cap is not None and level>=axis_cap:
            return False
        ceiling=axis_cap if axis_cap is not None else 1_000_000_000
        threshold=(lambda x:session.profession_xp_to_next(x,key)) if kind=='profession' else (lambda x:session.tool_xp_to_next(x,key))
        while level<min(ceiling,int(row["level"])+1):
            needed=threshold(level)
            if needed<=0 or xp<needed:
                break
            xp-=needed
            level+=1
        if kind=='profession':
            db.save_profession(account,key,level,xp,int(row['actions']))
        else:
            db.save_tool(account,key,level,xp,int(row['uses']))
    else:
        return False
    return True


async def redeem_exp_bank(session, *, all_balances=False):
    """Redeem one normal capped claim, or the full saved balance of every usable axis.

    The full mode is an explicit user action, not a normal XP reward: it is
    not artificially limited by the *per-new-award* Multi Cap or the old
    1-billion claim chunk.  SQLite account isolation, per-axis SAVEPOINTs,
    tier locks and exact balance comparisons still apply.
    """
    db, account, char = session.server.db, session.account_id, session.character
    if account is None or char is None:
        await session.send('Najpierw wybierz postać.')
        return
    rows=[(kind,key,balance) for kind,key,balance in db.experience_bank_rows_v2011(account) if balance>0]
    if not rows:
        await session.send('EXP Bank jest pusty.')
        return
    from systems.multi_cap_v23215 import multi_cap_experience_v23215
    redeemed=[]
    blocked=[]
    for kind,key,balance in rows:
        limit=multi_cap_experience_v23215(db.conn,account)
        if not limit or limit<1:
            blocked.append(kind+' '+key)
            continue
        amount=balance if all_balances else min(balance,int(limit),MAX_SAFE_AWARD)
        if amount<=0:
            continue
        snapshot=copy.deepcopy(char.__dict__)
        try:
            with db.conn.deferred_commits():
                db.conn.execute('SAVEPOINT bank_claim_v11325')
                try:
                    success=_credit(session,kind,key,amount)
                    if success:
                        from core.big_numbers_v10400 import canonical_uint
                        db.conn.execute('UPDATE experience_bank_v2011 SET balance=? WHERE account_id=? AND kind=? AND source_key=? AND balance=?',
                                        (canonical_uint(balance-amount),account,kind,key,canonical_uint(balance)))
                        if db.conn.execute('SELECT changes()').fetchone()[0]!=1:
                            raise RuntimeError('Saldo banku zmieniło się w trakcie wypłaty.')
                    db.conn.execute('RELEASE SAVEPOINT bank_claim_v11325')
                except BaseException:
                    db.conn.execute('ROLLBACK TO SAVEPOINT bank_claim_v11325')
                    db.conn.execute('RELEASE SAVEPOINT bank_claim_v11325')
                    raise
        except (OverflowError, ValueError) as exc:
            char.__dict__.clear()
            char.__dict__.update(snapshot)
            if not all_balances:
                raise
            # A legacy numeric field cannot always store the full TEXT-bank
            # amount. Never debit a single unit unless progress was saved.
            blocked.append(kind+' '+key+' (nie mieści się w zapisie: '+str(exc)+')')
            continue
        except BaseException:
            char.__dict__.clear()
            char.__dict__.update(snapshot)
            raise
        if success:
            # Send only after savepoint success; no EXP_BANK deposit event.
            from systems.v115.optional_sound import record_paid_exp_event_v11329
            record_paid_exp_event_v11329(db, account, amount, limit, kind=kind)
            redeemed.append((kind,key,amount))
        else:
            blocked.append(kind+' '+key)
    if redeemed:
        await session.send(('EXP Bank — wypłata całego dostępnego salda: ' if all_balances else 'EXP Bank: wypłacono ') + '; '.join(f'{kind} {key}: {amount}' for kind,key,amount in redeemed) + ' EXP.')
    if blocked:
        await session.send('Pozostało w banku (nieaktywna ścieżka, blokada poziomu lub limit techniczny): ' + '; '.join(blocked) + '.')
    if not redeemed and not blocked:
        await session.send('Nie ma EXP do wypłaty.')
