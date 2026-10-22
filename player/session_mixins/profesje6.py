# -*- coding: utf-8 -*-
"""Soulbound v6.00.0: eight genuinely distinct, persistent professions."""
import time
import unicodedata
from systems.new_professions import PROFESSIONS, AREAS, TIERS, BASE_ACTIONS, TIER_BONUS_INPUT, work_for
from data.items import ITEMS
from systems.items_resources import FISH_STORAGE_IDS, HERB_STORAGE_IDS, WOOD_STORAGE_IDS
from systems.equipment_crafting import MINING_STORAGE_IDS
from contextlib import contextmanager

SILVER_PER_MITHRIL = 100_000_000
SUPPLY_REWARD = {
    "Łowiectwo": "v600_seeds", "Rolnictwo": "v600_seeds",
    "Hodowla zwierząt": "v600_seeds", "Okrętownictwo": "iron_ingot",
    "Murarstwo": "stone_chunk", "Inżynieria": "iron_ingot",
    "Kupiectwo": "oak_plank", "Żeglarstwo": "oak_plank",
}
ORDER_GOODS = {
    "Łowiectwo": "v600_hunting_hide", "Rolnictwo": "field_grain",
    "Hodowla zwierząt": "farm_wool", "Okrętownictwo": "ship_parts",
    "Murarstwo": "stone_blocks", "Inżynieria": "machine_gears",
    "Kupiectwo": "v600_trade_receipt", "Żeglarstwo": "v600_voyage_log",
}
READY_SECONDS = {"sow":100,"feed":110,"dispatch":130,"voyage":150}
FINISH_KIND = {"harvest":"sow","milk":"feed","delivery":"dispatch","return":"voyage"}


def ensure_schema(db):
    if getattr(db, "_prof6_schema_ready", False):
        return
    schema = '''
    CREATE TABLE IF NOT EXISTS prof6_tools_owned (
        account_id INTEGER NOT NULL, item_id TEXT NOT NULL,
        PRIMARY KEY(account_id, item_id));
    CREATE TABLE IF NOT EXISTS prof6_work_state (
        account_id INTEGER NOT NULL, kind TEXT NOT NULL, tier INTEGER NOT NULL,
        ready_at INTEGER NOT NULL, PRIMARY KEY(account_id,kind));
    CREATE TABLE IF NOT EXISTS prof6_cooldowns (
        account_id INTEGER NOT NULL, action TEXT NOT NULL, ready_at INTEGER NOT NULL,
        PRIMARY KEY(account_id,action));
    CREATE TABLE IF NOT EXISTS prof6_order_claims (
        account_id INTEGER NOT NULL, profession TEXT NOT NULL,
        day_number INTEGER NOT NULL, PRIMARY KEY(account_id,profession,day_number));
    '''
    # sqlite3.executescript commits the connection before DDL; never use it
    # inside a live game command because it could commit unrelated changes.
    for statement in schema.split(';'):
        if statement.strip():
            db.conn.execute(statement)
    db.conn.commit()
    db._prof6_schema_ready = True


def _material_containers(item):
    """Use the real gathering bag for raw resources, plus the craft casket.

    `herbs` is an alias of `herbbag` in profession storage.  Never treat
    unrelated containers as a source of a given material.
    """
    containers = ["craftbox"]
    if item in HERB_STORAGE_IDS:
        containers.append("herbbag")
    if item in FISH_STORAGE_IDS:
        containers.append("net")
    if item in WOOD_STORAGE_IDS:
        containers.append("woodpile")
    if item in MINING_STORAGE_IDS:
        containers.append("bag")
    return tuple(containers)


def _sum(db, account, item):
    return db.item_qty(account, item) + sum(
        db.storage_qty(account, container, item)
        for container in _material_containers(item)
    )


def _remove_all(db, account, item, qty):
    """Spend exactly the requested quantity across the right storage sources.

    Caller owns the SQLite transaction. All guarded writes are reversible on
    failure, including professional XP and quest progress.
    """
    if _sum(db, account, item) < qty:
        return False
    remaining = qty
    for container in _material_containers(item):
        stored = min(db.storage_qty(account, container, item), remaining)
        if not stored:
            continue
        res = db.conn.execute(
            "UPDATE profession_storage SET quantity=quantity-? "
            "WHERE account_id=? AND container=? AND item_id=? AND quantity>=?",
            (stored, account, container, item, stored),
        )
        if res.rowcount != 1:
            return False
        remaining -= stored
        if not remaining:
            break
    if remaining:
        res = db.conn.execute(
            "UPDATE inventory SET quantity=quantity-? "
            "WHERE account_id=? AND item_id=? AND quantity>=?",
            (remaining, account, item, remaining),
        )
        if res.rowcount != 1:
            return False
    return True


def _coins(db, aid, amount):
    """Apply wallet delta without the canonical getter's implicit COMMIT.

    Existing shared-wallet reads normalize/commit automatically when gold>0;
    such a getter inside a multi-item transaction would lose atomicity.
    """
    master = db.master_account_for_character(aid)
    row = db.conn.execute(
        'SELECT silver,gold,mithril FROM account_wallet WHERE master_account_id=?',
        (master,),
    ).fetchone()
    if row is None:
        # Old pre-migration account: use its existing character currency.
        row = db.conn.execute(
            'SELECT silver,gold,mithril FROM characters WHERE account_id=?',
            (aid,),
        ).fetchone()
    if row is None:
        raise RuntimeError('Brak portfela postaci podczas transakcji.')
    old = int(row['silver']) + 100*int(row['gold']) + SILVER_PER_MITHRIL*int(row['mithril'])
    total = old + int(amount)
    if total < 0:
        return False
    if total > 8_000_000_000_000_000_000:
        return False
    # SQLite stores the full balance in the silver column (gold and mithril
    # are presentation units only). Match the canonical normalize_currency_values.
    silver, gold, mithril = total, 0, 0
    # Reuse the standard wallet writer but explicitly inhibit its commit.
    db.set_shared_wallet_for_master(master, silver, gold, mithril, commit=False)
    return (silver, gold, mithril)


def _format_resources(rows):
    return ', '.join(f'{q} × {ITEMS.get(i,{}).get("name",i)}' for i,q in rows) if rows else 'bez materiałów'


class SessionProfesje6Mixin:
    """New mechanics extend, never modify, the AST-locked 14-tool engine."""

    def _prof6_apply_wallet(self, balance):
        # Character-save logic synchronizes the shared wallet FROM the live
        # character. Keep both in-memory and SQLite currency in sync.
        if balance is not False:
            self.character.silver,self.character.gold,self.character.mithril=balance

    def valid_tool_type(self, tool_type):
        return tool_type in {spec[0] for spec in PROFESSIONS.values()} or super().valid_tool_type(tool_type)

    def tool_display_name_v11343(self, tool_type):
        for kind, _, name in PROFESSIONS.values():
            if kind == tool_type:
                return name
        return super().tool_display_name_v11343(tool_type)

    def tool_progress_state(self):
        progress = super().tool_progress_state()
        if self.account_id is not None:
            for kind, _, _ in PROFESSIONS.values():
                row = self.server.db.tool(self.account_id, kind)
                progress[kind] = int(row['level']), int(row['xp']), int(row['uses'])
        return progress

    def _prof6_relabel_xp(self, tool_type, messages):
        for kind, _, name in PROFESSIONS.values():
            if kind == tool_type:
                return [str(line).replace(kind + ':', name + ':') for line in messages]
        return messages

    def grant_profession_progress(self, profession, prof_xp, tool_type, tool_xp, *, content_level=None, **kw):
        msgs, prof_level, tool_level = super().grant_profession_progress(
            profession, prof_xp, tool_type, tool_xp, content_level=content_level, **kw)
        return self._prof6_relabel_xp(tool_type, msgs), prof_level, tool_level

    def grant_tool_progress(self, tool_type, tool_xp, *, content_level=None):
        result = super().grant_tool_progress(tool_type, tool_xp, content_level=content_level)
        if isinstance(result, tuple) and result and isinstance(result[0], list):
            return (self._prof6_relabel_xp(tool_type, result[0]),) + result[1:]
        return result
    async def profession_work_shortcut_v1106(self, args):
        await self.profesje6_command('praca ' + str(args or ''))

    async def profession_named_shortcut_v1106(self, args, profession):
        """`kupiectwo pakuj` == `profesja praca Kupiectwo pakuj`.

        Also accepts `kupiectwo praca pakuj 25`, `kupiectwo kup`,
        `kupiectwo zamowienie`, `kupiectwo oddaj` and `kupiectwo status`.
        No new payouts, timers, ownership or persistence mechanisms.
        """
        raw = str(args or '').strip()
        parts = raw.split(maxsplit=1)
        verb = parts[0].casefold() if parts else 'status'
        rest = parts[1] if len(parts) > 1 else ''
        if verb in {'help', 'pomoc', 'lista'}:
            verb = 'czynnosci'
        elif verb not in {'kup', 'status', 'czynnosci', 'czynności',
                          'zamowienie', 'zamówienie', 'oddaj', 'dostarcz',
                          'praca'}:
            rest = raw
            verb = 'praca'
        await self.profesje6_command(f'{verb} {profession} {rest}'.strip())

    async def profesje6_command(self,args):
        db=self.server.db
        aid=self.account_id
        if aid is None or self.character is None:
            await self.send('Najpierw zaloguj się postacią.')
            return
        # CREATE TABLE IF NOT EXISTS operates on the player's established SQLite
        # connection; does not change any old table, delete data or reset progress.
        ensure_schema(db)
        parts=str(args or '').strip().split()
        if not parts or parts[0].casefold() in {'lista','pomoc','help'}:
            await self.send('Profesje: profesje lista; profesja status <nazwa>; profesja kup <nazwa>; profesja czynnosci <nazwa>; profesja praca <nazwa> <czynność> [próg]; profesja zamowienie <nazwa>; profesja oddaj <nazwa>. Projekty mistrzowskie wszystkich 22 profesji: profesja projekt lista. Możesz też wpisać kupiectwo pakuj albo kupiectwo praca pakuj.')
            await self.send('Poziomy profesji i narzędzi 1–800, trudność pracy: 1, 25, 75, 150, 300, 500, 700. Każde narzędzie kupujesz tylko raz na postać.')
            for prof,(tt,i,name) in PROFESSIONS.items():
                await self.send(f'{prof}: {name}; {", ".join(a.code for a in BASE_ACTIONS if a.prof==prof)}.')
            return
        verb=parts[0].casefold()
        if verb in {'projekt','projekty','masterwork'}:
            await self._v1200_masterwork_command(parts[1:])
            return
        if verb in {'nasiona','nasiono'}:
            await self._prof6_seeds(parts[1:],db,aid)
            return
        prof,act,tier = self._prof6_parse(verb,parts[1:])
        if not prof:
            await self.send('Nieznana profesja lub czynność. Wpisz profesje lista albo help profesje.')
            return
        tool_type,item_id,tool_name=PROFESSIONS[prof]
        row=db.conn.execute('SELECT 1 FROM prof6_tools_owned WHERE account_id=? AND item_id=?',(aid,item_id)).fetchone()
        if verb == 'kup':
            if str(self.character.room_id) not in (AREAS['market'] | AREAS['harbor'] | {'forge', 'v601_mentor_' + tool_type}):
                await self.send('Narzędzie kupisz na targu, w porcie, kuźni albo u mistrza swojej profesji.')
                return
            # Verify database history and existing item before charging: no second
            # purchase even if item is in an alternative storage system.
            if row or db.item_qty(aid,item_id)>0 or db.storage_qty(aid,'craftbox',item_id)>0:
                if not row:
                    db.conn.execute('INSERT OR IGNORE INTO prof6_tools_owned VALUES(?,?)',(aid,item_id));db.conn.commit()
                await self.send('To narzędzie zostało już kupione na tę postać. Nie można kupić drugiego.')
                return
            try:
                balance=_coins(db,aid,-1200)
                if balance is False:
                    await self.send('Narzędzie kosztuje 1200 srebra, masz za mało monet.')
                    return
                db.conn.execute('INSERT INTO prof6_tools_owned VALUES(?,?)',(aid,item_id))
                db.add_item(aid,item_id,1,commit=False)
                # Keep canonical character row in sync with shared-wallet coins,
                # in the SAME transaction as the tool purchase and its ledger.
                db.conn.execute('UPDATE characters SET silver=?,gold=?,mithril=? WHERE account_id=?',
                                (*balance,aid))
                db.conn.commit()
                self._prof6_apply_wallet(balance)
            except Exception:
                db.conn.rollback()
                raise
            await self.send(f'Kupiono {tool_name}. Trwały jednorazowy zakup przypisano do tej postaci.')
            return
        if verb == 'status':
            p=db.profession(aid,prof);t=db.tool(aid,tool_type)
            await self.send(f'{prof}: poziom {p["level"]}/800, EXP {p["xp"]}; {tool_name}: poziom {t["level"]}/800, EXP {t["xp"]}. Narzędzie kupione: {"tak" if row else "nie"}.')
            states=db.conn.execute('SELECT kind,ready_at FROM prof6_work_state WHERE account_id=?',(aid,)).fetchall()
            for x in states:
                await self.send(f'Praca w toku: {x["kind"]}; pozostało {max(0,int(x["ready_at"])-int(time.time()))} sekund.')
            return
        if verb in {'czynnosci','czynności','prace'}:
            for a in BASE_ACTIONS:
                if a.prof==prof:
                    await self.send(f'{a.code} — {a.title}; teren {a.region}; koszty: {_format_resources(a.ingredients)}; wynik: {_format_resources(a.outputs)}.')
            return
        if verb in {'zamowienie','zamówienie'}:
            await self._prof6_order(prof,aid,db,False)
            return
        if verb in {'oddaj','dostarcz'}:
            await self._prof6_order(prof,aid,db,True)
            return
        if verb!='praca' or not act:
            await self.send('Komendy: kup, nasiona, status, czynnosci, praca, zamowienie, oddaj.')
            return
        work=work_for(prof,act,tier)
        if not work:
            await self.send('Nieznana praca albo próg; dostępne 1,25,75,150,300,500,700. Wpisz profesja czynnosci <nazwa>.')
            return
        if not row or db.item_qty(aid,item_id)<=0:
            await self.send(f'Wymagany zakupiony i posiadany {tool_name}.')
            return
        plevel=int(db.profession(aid,prof)['level'])
        if plevel<tier:
            await self.send(f'Praca wymaga poziomu profesji {tier}; masz {plevel}.')
            return
        toollevel=int(db.tool(aid,tool_type)['level'])
        if toollevel<tier:
            await self.send(f'Praca wymaga poziomu narzędzia {tier}; {tool_name} ma poziom {toollevel}.')
            return
        room=str(self.character.room_id)
        if room not in AREAS[work.region]:
            await self.send(f'{work.title}: niewłaściwe miejsce. Wybierz teren: {", ".join(sorted(AREAS[work.region]))}.')
            return
        now=int(time.time())
        if work.pending in FINISH_KIND:
            original=FINISH_KIND[work.pending]
            ongoing=db.conn.execute('SELECT ready_at,tier FROM prof6_work_state WHERE account_id=? AND kind=?',(aid,original)).fetchone()
            if not ongoing:
                await self.send('Najpierw rozpocznij powiązaną pracę.')
                return
            if now < int(ongoing['ready_at']):
                await self.send(f'Praca jeszcze trwa: {int(ongoing["ready_at"])-now} sekund.')
                return
            if tier!=int(ongoing['tier']):
                await self.send(f'Zakończ pracę na tym samym progu: {ongoing["tier"]}.')
                return
        elif work.pending:
            current=db.conn.execute('SELECT ready_at FROM prof6_work_state WHERE account_id=? AND kind=?',(aid,work.pending)).fetchone()
            if current:
                await self.send(f'Praca już trwa. Pozostało {max(0,int(current["ready_at"])-now)} sekund; zakończ ją odpowiednią czynnością.')
                return
        if work.cooldown:
            cd=db.conn.execute('SELECT ready_at FROM prof6_cooldowns WHERE account_id=? AND action=?',(aid,prof+':'+act)).fetchone()
            if cd and now<int(cd['ready_at']):
                await self.send(f'Wypatrujesz kolejnych okazji. Pozostało {int(cd["ready_at"])-now} sekund.')
                return
        shortage=[(i,q-_sum(db,aid,i)) for i,q in work.ingredients if _sum(db,aid,i)<q]
        if shortage:
            await self.send('Brak materiałów: '+_format_resources(shortage)+'.')
            return
        # Materials, timed state AND canonical XP rewards must be atomic.
        try:
            with db.conn.deferred_commits():
                try:
                    messages,changed_quests=self._prof6_do_work(db,aid,work,prof,tool_type,tier,now)
                except Exception:
                    # Roll back BEFORE leaving deferred_commits: its exit may
                    # otherwise flush a pending commit after an XP exception.
                    db.conn.rollback()
                    raise
        except Exception:
            db.conn.rollback()
            raise
        await self.send(f'{prof} — {work.title} (próg {tier}). Zużyto: {_format_resources(work.ingredients)}. Otrzymano: {_format_resources(work.outputs)}.')
        if work.pending in READY_SECONDS:
            await self.send(f'Zadanie rozpoczęte. Zakończenie za {READY_SECONDS[work.pending]} sekund.')
        for m in messages:
            await self.send(str(m))
        for quest_id, _progress, _needed in changed_quests:
            # v11.00.9: show the real quest name and an essential, current
            # progress counter instead of an internal SQLite quest ID.
            if hasattr(self, 'announce_active_quest_progress'):
                await self.announce_active_quest_progress(quest_id)
            else:
                # Standalone profession practice harnesses do not carry the
                # full SessionQuestsMixin, but still receive readable output.
                from systems.content_registry import QUESTS
                name = QUESTS.get(quest_id, {}).get('name', quest_id)
                await self.send(f'Postęp zadania: {name} — {_progress} z {_needed}.')

    def _prof6_do_work(self,db,aid,work,prof,tool_type,tier,now):
        for i,q in work.ingredients:
            if not _remove_all(db,aid,i,q):
                raise RuntimeError('Brak materiału podczas operacji.')
        for i,q in work.outputs:
            db.add_item(aid,i,q,commit=False)
        if work.pending in READY_SECONDS:
            db.conn.execute('INSERT INTO prof6_work_state(account_id,kind,tier,ready_at) VALUES(?,?,?,?)',
                            (aid,work.pending,tier,now+READY_SECONDS[work.pending]))
        elif work.pending in FINISH_KIND:
            db.conn.execute('DELETE FROM prof6_work_state WHERE account_id=? AND kind=?',
                            (aid,FINISH_KIND[work.pending]))
        if work.cooldown:
            db.conn.execute('INSERT INTO prof6_cooldowns(account_id,action,ready_at) VALUES(?,?,?) '
                            'ON CONFLICT(account_id,action) DO UPDATE SET ready_at=excluded.ready_at',
                            (aid,prof+':'+work.code,now+work.cooldown))
        messages,_,_=self.grant_profession_progress(prof,work.xp,tool_type,work.tool_xp,content_level=tier,content_key=work.code)
        changed_quests=db.increment_profession_action_quests_v0700(
            aid,prof,tool_type,1,action_code=work.code,tier=tier)
        db.conn.commit()  # deferred until XP, materials AND quest progress are valid
        return messages,changed_quests

    @staticmethod
    def _prof6_parse(verb,parts):
        tier=1
        if verb=='praca' and parts and parts[-1].isdigit():
            tier=int(parts[-1]);parts=parts[:-1]
        def normalize(txt):
            txt=unicodedata.normalize('NFKD',txt.casefold().replace('ł','l'))
            return ''.join(c for c in txt if not unicodedata.combining(c))
        names=sorted(PROFESSIONS,key=len,reverse=True)
        words=normalize(' '.join(parts))
        # Natural shorthand recognized alongside the full accessible name.
        aliases={'hodowla':'Hodowla zwierząt','okrety':'Okrętownictwo','handel':'Kupiectwo',
                 'rejsy':'Żeglarstwo','polowanie':'Łowiectwo'}
        # Full profession names must win over shorter aliases, e.g.
        # "hodowla zwierząt nakarm", otherwise "zwierzat nakarm" becomes
        # the unrecognized action.
        for name in names:
            low=normalize(name)
            if words==low: return name,None,tier
            if words.startswith(low+' '): return name,words[len(low):].strip(),tier
        for alias,full in aliases.items():
            if words==alias: return full,None,tier
            if words.startswith(alias+' '): return full,words[len(alias):].strip(),tier
        return None,None,tier

    async def _prof6_seeds(self,parts,db,aid):
        if str(self.character.room_id) not in AREAS['market']:
            await self.send('Nasiona kupisz na rynku lub targu rybnym.')
            return
        if not db.conn.execute('SELECT 1 FROM prof6_tools_owned WHERE account_id=? AND item_id=?',(aid,'farming_hoe')).fetchone():
            await self.send('Najpierw kup Motykę Rolniczą.')
            return
        qty=int(parts[0]) if parts and parts[0].isdigit() else 1
        if not 1<=qty<=50:
            await self.send('Podaj liczbę nasion od 1 do 50.')
            return
        try:
            balance=_coins(db,aid,-qty*20)
            if balance is False:
                await self.send('Za mało monet, jedno nasiono kosztuje 20 srebra.')
                return
            db.add_item(aid,'v600_seeds',qty,commit=False)
            db.conn.commit()
            self._prof6_apply_wallet(balance)
        except Exception:
            db.conn.rollback()
            raise
        await self.send(f'Kupiono {qty} nasion za {20*qty} srebra.')

    async def _prof6_order(self,prof,aid,db,finish):
        if str(self.character.room_id) not in AREAS['market'] and str(self.character.room_id)!='harbor':
            await self.send('Zamówienia profesji przyjmuje rynek, targ rybny i port.')
            return
        day=int(time.time())//86400
        good=ORDER_GOODS[prof]
        level=int(db.profession(aid,prof)['level'])
        tier=max(t for t in TIERS if t<=level)
        quantity=3+TIERS.index(tier)
        completed=db.conn.execute('SELECT 1 FROM prof6_order_claims WHERE account_id=? AND profession=? AND day_number=?',(aid,prof,day)).fetchone()
        # Authored order rewards do NOT depend on the EXP requirement curve.
        # Higher tiers must pay useful materials, not only a handful of seeds.
        stage = TIERS.index(tier)
        coins = 350 * quantity + 3 * int(tier) * max(0, int(tier)-1)
        reward = SUPPLY_REWARD[prof]
        reward_amount = 2 + stage
        rare_reward = TIER_BONUS_INPUT[prof][stage] if stage else None
        rare_amount = 1 + stage // 2 if rare_reward else 0
        description = f'{coins} srebra, {reward_amount} × {ITEMS[reward]["name"]}'
        if rare_reward:
            description += f', {rare_amount} × {ITEMS[rare_reward]["name"]}'
        if not finish:
            await self.send(f'Zamówienie {prof}: {quantity} × {ITEMS[good]["name"]}. Nagrody: {description} oraz XP za trudność {tier}. Status dziś: {"odebrane" if completed else "dostępne"}.')
            return
        if completed:
            await self.send('Nagrodę za to zamówienie już dziś odebrano. Kolejne jutro.')
            return
        if _sum(db,aid,good)<quantity:
            await self.send(f'Brak towarów zamówienia: {quantity} × {ITEMS[good]["name"]}.')
            return
        try:
            with db.conn.deferred_commits():
                try:
                    if not _remove_all(db,aid,good,quantity): raise RuntimeError('Dostawa bez towarów.')
                    db.conn.execute('INSERT INTO prof6_order_claims(account_id,profession,day_number) VALUES(?,?,?)',(aid,prof,day))
                    balance=_coins(db,aid,coins)
                    if balance is False: raise RuntimeError('Nie można naliczyć zapłaty.')
                    db.add_item(aid,reward,reward_amount,commit=False)
                    if rare_reward:
                        db.add_item(aid,rare_reward,rare_amount,commit=False)
                    # save_character() writes the wallet from this live object.
                    oldbalance=(self.character.silver,self.character.gold,self.character.mithril)
                    self._prof6_apply_wallet(balance)
                    tool_type=PROFESSIONS[prof][0]
                    msgs,_,_=self.grant_profession_progress(prof,75+tier*8,tool_type,40+tier*5,content_level=tier,content_key=good)
                    db.conn.commit()
                except Exception:
                    db.conn.rollback()
                    if 'oldbalance' in locals(): self._prof6_apply_wallet(oldbalance)
                    raise
        except Exception:
            db.conn.rollback()
            if 'oldbalance' in locals(): self._prof6_apply_wallet(oldbalance)
            raise

        await self.send(f'Zamówienie {prof} zakończone: {description}. Następne jutro.')
        for m in msgs: await self.send(str(m))

    async def _v1200_masterwork_command(self, parts):
        """22 cross-profession projects and one nonrepeatable daily contract each."""
        from systems.profession_projects_v1200 import (
            PROJECTS, LEVELS, resolve, project_item_id, recipe, order_quantity,
            ensure_schema as ensure12)
        db=self.server.db; aid=self.account_id
        if aid is None or not self.character:
            await self.send('Najpierw zaloguj się postacią.'); return
        if not parts or parts[0].casefold() in ('lista','list','pomoc','help'):
            await self.send('PROJEKTY MISTRZOWSKIE 10.0: profesja projekt <nazwa>, profesja projekt wykonaj <nazwa> <25|200|400|600|700|775>, profesja projekt oddaj <nazwa>. Każdy projekt łączy dwie profesje. Przedmioty wspierają AI przywołań, ale nie są wymagane do walki.')
            for prof,p in PROJECTS.items():
                await self.send(f'{prof}: {p.title} ({p.partner_profession}).')
            return
        verb=parts[0].casefold()
        action=verb if verb in ('wykonaj','zrob','zrób','oddaj','dostarcz') else 'info'
        arguments=parts[1:] if action!='info' else parts
        tier=None  # without an explicit tier, use the strongest unlocked project
        if action in ('wykonaj','zrob','zrób') and arguments and arguments[-1].isdigit():
            tier=int(arguments[-1]);arguments=arguments[:-1]
            if tier not in LEVELS:
                await self.send('Próg projektu musi wynosić 25, 200, 400, 600, 700 albo 775.');return
        profession=resolve(' '.join(arguments))
        if not profession:
            await self.send('Nieznana profesja. Wpisz profesja projekt lista.');return
        proj=PROJECTS[profession]
        tool=proj.tool
        ensure12(db.conn)
        p_level=int(db.profession(aid,profession)['level'])
        t_level=int(db.tool(aid,tool)['level'])
        available=max((i for i in LEVELS if min(p_level,t_level)>=i),default=None)
        item_id=project_item_id(profession)
        if action=='info':
            show=available or 25
            ingredients=recipe(profession,show)
            await self.send(f'Projekt {profession}: {proj.title}. Poziom profesji {p_level}, narzędzia {t_level}; wymagany próg {show}. Powiązana profesja: {proj.partner_profession}. Materiały: {_format_resources(ingredients)}. Wybierz profesja projekt wykonaj {profession} {show}.')
            owned=_sum(db,aid,item_id)
            await self.send(f'Gotowe wyroby: {owned}. Kontrakt dzienny: profesja projekt oddaj {profession}; wymaga {order_quantity(show)} sztuk; zaawansowane progi dają większą nagrodę.')
            return
        if available is None:
            await self.send('Projekt wymaga co najmniej poziomu 25 profesji ORAZ narzędzia.');return
        if action in ('wykonaj','zrob','zrób'):
            if tier is None:
                tier=available
            if tier>available:
                await self.send(f'Poziom projektu {tier} jest zablokowany. Profesja: {p_level}; narzędzie: {t_level}. Nie zużyto materiałów.');return
            if profession in PROFESSIONS:
                _,tool_item,_=PROFESSIONS[profession]
                purchased=db.conn.execute('SELECT 1 FROM prof6_tools_owned WHERE account_id=? AND item_id=?',(aid,tool_item)).fetchone()
                if not purchased or db.item_qty(aid,tool_item)<1:
                    await self.send('Najpierw kup i miej przy sobie istniejące narzędzie tej profesji.');return
            ingredients=recipe(profession,tier)
            missing=[(item,qty-_sum(db,aid,item)) for item,qty in ingredients if _sum(db,aid,item)<qty]
            if missing:
                await self.send('Brak materiałów: '+_format_resources(missing)+'.');return
            try:
                with db.conn.deferred_commits():
                    try:
                        for item,qty in ingredients:
                            if not _remove_all(db,aid,item,qty):
                                raise RuntimeError('Materiał zniknął podczas projektu; transakcja wycofana.')
                        db.add_item(aid,item_id,1,commit=False)
                        db.conn.execute('INSERT INTO prof12_masterworks(account_id,profession,made) VALUES(?,?,1) '
                                        'ON CONFLICT(account_id,profession) DO UPDATE SET made=made+1',(aid,profession))
                        messages,_,_=self.grant_profession_progress(
                            profession,650+tier*14,tool,450+tier*10,content_level=tier,content_key=project_item_id(profession)+':'+str(tier))
                        db.conn.commit()
                    except Exception:
                        db.conn.rollback();raise
            except Exception:
                db.conn.rollback();raise
            await self.send(f'Wykonano {proj.title} (poziom {tier}). Zużyto: {_format_resources(ingredients)}. Gotowy wyrób możesz zachować dla AI przywołań lub dostarczyć w kontrakcie.')
            for msg in messages: await self.send(str(msg))
            return
        day=int(time.time())//86400
        already=db.conn.execute('SELECT 1 FROM prof12_contract_claims WHERE account_id=? AND profession=? AND day=?',(aid,profession,day)).fetchone()
        if already:
            await self.send('Ten kontrakt mistrzowski został już dziś oddany.');return
        tier=available
        count=order_quantity(tier)
        if _sum(db,aid,item_id)<count:
            await self.send(f'Kontrakt {profession}: potrzeba {count} × {proj.title}. Masz {_sum(db,aid,item_id)}. Zachowane wyroby możesz wykorzystać jutro.');return
        coins=2500+int(tier)*75
        old_balance=(self.character.silver,self.character.gold,self.character.mithril)
        from player.session_mixins.profesje6 import _coins
        try:
            with db.conn.deferred_commits():
                try:
                    if not _remove_all(db,aid,item_id,count):
                        raise RuntimeError('Nie można pobrać gotowych wyrobów.')
                    db.conn.execute('INSERT INTO prof12_contract_claims(account_id,profession,day) VALUES(?,?,?)',(aid,profession,day))
                    db.conn.execute('UPDATE prof12_masterworks SET turned_in=turned_in+? WHERE account_id=? AND profession=?',(count,aid,profession))
                    balance=_coins(db,aid,coins)
                    if balance is False: raise RuntimeError('Przekroczony limit waluty podczas kontraktu.')
                    messages,_,_=self.grant_profession_progress(
                        profession,900+tier*16,tool,600+tier*12,content_level=tier,content_key=project_item_id(profession)+':contract:'+str(tier))
                    db.conn.commit()
                except Exception:
                    db.conn.rollback();raise
            self._prof6_apply_wallet(balance)
        except Exception:
            db.conn.rollback()
            self._prof6_apply_wallet(old_balance)
            raise
        await self.send(f'Kontrakt mistrzowski {profession} ukończony. Oddano {count} × {proj.title}. Nagroda: {coins} srebra i EXP profesji oraz narzędzia. Następny kontrakt jutro.')
        for msg in messages: await self.send(str(msg))
