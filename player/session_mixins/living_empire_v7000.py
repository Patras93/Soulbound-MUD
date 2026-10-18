# -*- coding: utf-8 -*-
"""Soulbound v7.00.0: persistent industry, expeditions, story and accessible UI.

Every successful operation consumes actual inventory/craftbox products and
commits materials, gains, wallet and XP as one SQLite unit.
"""
from __future__ import annotations
import time
import unicodedata
from systems.new_professions import PROFESSIONS, AREAS, TIERS
from systems.living_empire_v7000 import (
    NEW_GOODS, UPGRADES, MISSION_TYPES, VOYAGES, CARAVANS, MASTER_INPUT,
    STORY, STORY_IDS,
)
from systems.profession_quest_expansion import PROFESSION_QUEST_SPECS_V0700
from player.session_mixins.profesje6 import _sum, _remove_all, _coins

OLD_TOOLS = {prof:tool for prof,tool,*_ in PROFESSION_QUEST_SPECS_V0700}
NEW_TOOLS = {prof:tool for prof,(tool,_,_) in PROFESSIONS.items()}
ALL_TOOLS = {**OLD_TOOLS,**NEW_TOOLS}
V700_SCHEMA = (
    '''CREATE TABLE IF NOT EXISTS v700_improvements (
        account_id INTEGER NOT NULL, key TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY(account_id,key))''',
    '''CREATE TABLE IF NOT EXISTS v700_jobs (
        account_id INTEGER NOT NULL, kind TEXT NOT NULL, destination TEXT NOT NULL,
        tier INTEGER NOT NULL, ready_at INTEGER NOT NULL,
        PRIMARY KEY(account_id,kind))''',
    '''CREATE TABLE IF NOT EXISTS v700_master_contracts (
        account_id INTEGER NOT NULL, profession TEXT NOT NULL, day INTEGER NOT NULL,
        PRIMARY KEY(account_id,profession,day))''',
    '''CREATE TABLE IF NOT EXISTS v700_hunts (
        account_id INTEGER PRIMARY KEY, tier INTEGER NOT NULL, needed INTEGER NOT NULL,
        progress INTEGER NOT NULL DEFAULT 0, started_at INTEGER NOT NULL)''',
    '''CREATE TABLE IF NOT EXISTS v700_preferences (
        account_id INTEGER PRIMARY KEY, compact INTEGER NOT NULL DEFAULT 1)''',
)


def ensure_schema(db):
    if getattr(db,'_v700_schema_ready',False):
        return
    for ddl in V700_SCHEMA:
        db.conn.execute(ddl)
    db.conn.commit()
    db._v700_schema_ready=True


def norm(s):
    s=unicodedata.normalize('NFKD',str(s or '').casefold().replace('ł','l'))
    return ''.join(c for c in s if not unicodedata.combining(c)).strip()


def inputs_text(rows):
    from data.items import ITEMS
    return ', '.join(f'{count} × {ITEMS.get(item,{}).get("name",item)}' for item,count in rows)


def tier_for(level):
    return max(t for t in TIERS if t<=int(level))


class SessionLivingEmpireV7000Mixin:
    def _prof6_do_work(self,db,aid,work,prof,tool_type,tier,now):
        """Existing v6 action remains authoritative; permanent land projects
        add earned outputs in that action's own deferred transaction.
        """
        messages,changed=super()._prof6_do_work(db,aid,work,prof,tool_type,tier,now)
        boosts={
            ('Rolnictwo','zbierz'):('pole','field_grain'),
            ('Hodowla zwierząt','odbierz'):('stado','farm_wool'),
            ('Okrętownictwo','buduj'):('stocznia','ship_parts'),
            ('Inżynieria','montuj'):('warsztat','machine_gears'),
        }
        match=boosts.get((prof,work.code))
        if match and getattr(db,'_v700_schema_ready',False):
            key,item=match
            level=self._v7_upgrade(key)
            if level:
                amount=max(1,level//2)
                db.add_item(aid,item,amount,commit=False)
                db.conn.commit()
                messages=list(messages)+[f'Ulepszenie {key}: +{amount} × {item}.']
        return messages,changed

    async def record_empire_hunt_kill_v7000(self,template):
        """Triggered only for actual credited kills from the combat event.
        Party players advance independently. Mercenaries never create credit.
        """
        if not self.character or self.account_id is None: return
        from core.progression_resources import v0190_mob_rank
        if v0190_mob_rank(template) not in {'rare','elite','mini','boss','world_boss'}:
            return
        db=self.server.db
        ensure_schema(db)
        row=db.conn.execute('SELECT tier,needed,progress FROM v700_hunts WHERE account_id=?',
                            (self.account_id,)).fetchone()
        if row is None or int(row['progress'])>=int(row['needed']):return
        moblevel=int(template.get('generator_level',template.get('v019_stage',1)) or 1)
        if moblevel<int(row['tier']):return
        db.conn.execute('UPDATE v700_hunts SET progress=progress+1 WHERE account_id=? AND progress<needed',
                        (self.account_id,))
        db.conn.commit()
        current=int(row['progress'])+1
        await self.send(f'Łowy legendarne: {current} z {row["needed"]}.')

    def _v7_ready(self,prof):
        """Require existing v6 tools physically carried and learned (no duplicate)."""
        if prof not in NEW_TOOLS: return True
        db=self.server.db
        aid=self.account_id
        tool,item,_=PROFESSIONS[prof]
        if not db.conn.execute('SELECT 1 FROM prof6_tools_owned WHERE account_id=? AND item_id=?', (aid,item)).fetchone():
            return False
        return db.item_qty(aid,item)>0

    def _v7_level(self,prof):
        db=self.server.db
        aid=self.account_id
        tool=ALL_TOOLS[prof]
        return min(int(db.profession(aid,prof)['level']),int(db.tool(aid,tool)['level']))

    def _v7_upgrade(self,key):
        r=self.server.db.conn.execute('SELECT level FROM v700_improvements WHERE account_id=? AND key=?',(self.account_id,key)).fetchone()
        return int(r['level']) if r else 0

    def _v7_compact(self):
        r=self.server.db.conn.execute('SELECT compact FROM v700_preferences WHERE account_id=?',(self.account_id,)).fetchone()
        return bool(r['compact']) if r else True

    def _v7_grant(self,prof,tier,amount=1):
        tool=ALL_TOOLS[prof]
        # Higher difficulty pays larger ABSOLUTE XP; never derive the reward
        # from the NEXT_LEVEL_XP, bank limits or character EXP cap.
        xp=(210 + tier*17 + tier*tier//8)*amount
        t_xp=(135 + tier*11 + tier*tier//13)*amount
        messages,_,_=self.grant_profession_progress(prof,xp,tool,t_xp,content_level=tier)
        return messages,xp,t_xp

    def _v7_exec(self,inputs,outputs,profession,tier,*,coin_reward=0,update=None):
        """One fail-closed transaction, including canonical XP, wallet, and state."""
        db=self.server.db;aid=self.account_id
        shortage=[(item,qty-_sum(db,aid,item)) for item,qty in inputs if _sum(db,aid,item)<qty]
        if shortage:
            return None,'Brak materiałów: '+inputs_text(shortage)
        before=(self.character.silver,self.character.gold,self.character.mithril)
        try:
            with db.conn.deferred_commits():
                try:
                    for item,qty in inputs:
                        if not _remove_all(db,aid,item,qty):
                            raise RuntimeError('Niepowodzenie pobrania materiału — transakcja anulowana.')
                    for item,qty in outputs:
                        db.add_item(aid,item,qty,commit=False)
                    if update: update()
                    if coin_reward:
                        balance=_coins(db,aid,coin_reward)
                        if balance is False: raise RuntimeError('Nie można przyznać zapłaty bez utraty danych.')
                        self._prof6_apply_wallet(balance)
                    messages,xp,t_xp=self._v7_grant(profession,tier)
                    db.conn.commit()
                except Exception:
                    db.conn.rollback()
                    self._prof6_apply_wallet(before)
                    raise
        except Exception:
            db.conn.rollback()
            self._prof6_apply_wallet(before)
            raise
        return (messages,xp,t_xp),None

    async def _v7_emit(self,title,detail,rewards):
        """Compact NVDA announces the *actual authored XP grant*, not only a
        vague success line. Full mode retains the canonical progress messages.
        """
        grant_messages, profession_xp, tool_xp = rewards
        if self._v7_compact():
            await self.send(f'{title} EXP profesji +{profession_xp}; EXP narzędzia +{tool_xp}.')
            return
        await self.send(title)
        await self.send(detail)
        for msg in grant_messages:
            await self.send(str(msg))

    async def imperium_caravan_shortcut_v1106(self, args):
        await self.imperium7_command('karawana ' + str(args or ''))

    async def imperium_hunts_shortcut_v1106(self, args):
        await self.imperium7_command('lowy ' + str(args or ''))

    async def imperium_voyage_shortcut_v1106(self, args):
        await self.imperium7_command('wyprawa ' + str(args or ''))

    async def imperium7_command(self,args):
        if self.account_id is None or self.character is None:
            await self.send('Najpierw zaloguj się postacią.');return
        db=self.server.db
        ensure_schema(db)
        raw=str(args or '').strip()
        parts=raw.split()
        mode=norm(parts[0]) if parts else 'pomoc'
        rest=parts[1:]
        if mode in ('pomoc','help','lista'):
            await self.send('IMPERIUM 7: status, koszt <projekt>, ulepsz <pole|stado|warsztat|magazyn|stocznia|mury|latarnia|twierdza>, praca <rolnictwo|hodowla|inżynieria>.')
            await self.send('lowy lista/start/odbierz — prawdziwe zabicia elit i bossów; wyprawa lista/start <rafa|stolica|burze|row>/odbierz; karawana lista/start <rynek|port|kuźnia|targ>/odbierz.')
            await self.send('mistrzostwo lista/<profesja>; fabula; nvda zwięźle/pełne. Wymagane realne wyroby z profesje6 i starych profesji.')
            return
        if mode=='status':
            projects=', '.join(f'{key} {self._v7_upgrade(key)}/8' for key in UPGRADES)
            if self._v7_compact():
                await self.send('Imperium — ulepszenia: '+projects+'.')
            else:
                await self.send('ERA ŻYJĄCEGO IMPERIUM — trwałe ulepszenia:')
                for key in UPGRADES:
                    await self.send(f'{key}: {self._v7_upgrade(key)}/8.')
            jobs=db.conn.execute('SELECT kind,destination,ready_at FROM v700_jobs WHERE account_id=? ORDER BY kind',(self.account_id,)).fetchall()
            if not jobs:
                await self.send('Wyprawy i prace w toku: brak.')
            else:
                now=int(time.time())
                for job in jobs:
                    remaining=max(0,int(job['ready_at'])-now)
                    await self.send(f'{job["kind"]}: {job["destination"]}; '+('gotowe do odbioru.' if remaining==0 else f'pozostało {remaining} sekund.'))
            return
        if mode in ('koszt','projekt'):
            key=norm(' '.join(rest))
            if key not in UPGRADES:
                await self.send('Projekty: '+', '.join(UPGRADES)+'. Użyj imperium7 koszt <projekt>.');return
            prof,area,inputs,_=UPGRADES[key]
            level=self._v7_upgrade(key)
            if level>=8:
                await self.send(f'{key}: ukończono 8/8.');return
            tier=TIERS[min(level,6)]
            actual=tuple((item,qty*(level+1)) for item,qty in inputs)
            missing=tuple((i,n-_sum(db,self.account_id,i)) for i,n in actual if _sum(db,self.account_id,i)<n)
            await self.send(f'{key}: etap {level+1}/8; profesja {prof}, poziom profesji i narzędzia {tier}; teren {area}. Potrzeba: {inputs_text(actual)}.')
            await self.send('Brakuje: '+(inputs_text(missing) if missing else 'nic; można wykonać ulepszenie.') )
            return
        if mode=='nvda':
            value=norm(' '.join(rest))
            if value not in {'zwiezle','pelne'}:
                await self.send('imperium7 nvda zwięźle albo imperium7 nvda pełne.');return
            db.conn.execute('INSERT INTO v700_preferences(account_id,compact) VALUES(?,?) ON CONFLICT(account_id) DO UPDATE SET compact=excluded.compact',(self.account_id,int(value=='zwiezle')))
            db.conn.commit()
            await self.send('Komunikaty Imperium 7: '+('zwięzłe.' if value=='zwiezle' else 'pełne.'))
            return
        if mode=='ulepsz':
            await self._v7_improve(norm(' '.join(rest)));return
        if mode=='praca':
            await self._v7_work(norm(' '.join(rest)));return
        if mode=='lowy':
            await self._v7_hunting(rest);return
        if mode=='wyprawa':
            await self._v7_route('ocean',rest);return
        if mode=='karawana':
            await self._v7_route('trade',rest);return
        if mode=='mistrzostwo':
            await self._v7_master(' '.join(rest));return
        if mode in ('fabula','kronika'):
            await self._v7_story();return
        await self.send('Nieznana komenda. Wpisz imperium7 pomoc.')

    async def _v7_improve(self,key):
        if key not in UPGRADES:
            await self.send('Ulepszenia: '+', '.join(UPGRADES)+'.');return
        prof,area,inputs,reward=UPGRADES[key]
        if str(self.character.room_id) not in AREAS[area]:
            await self.send(f'Ulepszenie {key} wymaga terenu {area}: '+', '.join(sorted(AREAS[area]))+'.');return
        level=self._v7_upgrade(key)
        if level>=8:
            await self.send(f'{key}: poziom 8/8. Zakończono wszystkie rozbudowy.');return
        needed_tier=TIERS[min(level,6)]
        if self._v7_level(prof)<needed_tier or not self._v7_ready(prof):
            await self.send(f'{key}: wymagany poziom profesji i narzędzia {needed_tier} oraz posiadane narzędzie.');return
        real_inputs=tuple((item,qty*(level+1)) for item,qty in inputs)
        def update():
            self.server.db.conn.execute(
                'INSERT INTO v700_improvements(account_id,key,level) VALUES(?,?,1) '
                'ON CONFLICT(account_id,key) DO UPDATE SET level=level+1',
                (self.account_id,key))
        result,error=self._v7_exec(real_inputs,((reward,1+level//2),),prof,needed_tier,update=update)
        if error:
            await self.send(error);return
        await self._v7_emit(f'Ulepszono {key}: {level+1}/8. Otrzymano pieczęć i EXP.',
                            'Zużyto '+inputs_text(real_inputs)+'.',result)

    async def _v7_work(self,kind):
        lookup={'inzynieria':'inżynieria','rolnictwo':'rolnictwo','hodowla':'hodowla'}
        kind=lookup.get(kind,kind)
        if kind not in MISSION_TYPES:
            await self.send('Prace: rolnictwo, hodowla, inżynieria. Polowania: imperium7 lowy start.');return
        prof,area,inputs,reward,cooldown=MISSION_TYPES[kind]
        if str(self.character.room_id) not in AREAS[area]:
            await self.send('Praca wymaga terenu '+area+'.');return
        if not self._v7_ready(prof):
            await self.send('Wymagane zakupione i posiadane narzędzie '+PROFESSIONS[prof][2]+'.');return
        tier=tier_for(self._v7_level(prof))
        now=int(time.time())
        r=self.server.db.conn.execute('SELECT ready_at FROM v700_jobs WHERE account_id=? AND kind=?',(self.account_id,'work:'+kind)).fetchone()
        if r and now<int(r['ready_at']):
            await self.send(f'Zlecenie {kind} jeszcze trwa: {r["ready_at"]-now} s.');return
        mult=1+TIERS.index(tier)
        actual=tuple((item,qty*mult) for item,qty in inputs)
        def update():
            self.server.db.conn.execute(
                'INSERT INTO v700_jobs(account_id,kind,destination,tier,ready_at) VALUES(?,?,?,?,?) '
                'ON CONFLICT(account_id,kind) DO UPDATE SET destination=excluded.destination,tier=excluded.tier,ready_at=excluded.ready_at',
                (self.account_id,'work:'+kind,kind,tier,now+cooldown))
        result,error=self._v7_exec(actual,((reward,mult),),prof,tier,update=update)
        if error: await self.send(error);return
        await self._v7_emit(f'Wykonano {kind} (próg {tier}). Otrzymano {mult} pieczęci i EXP; następna praca za {cooldown}s.',
                            'Zużyto '+inputs_text(actual)+'.',result)

    async def _v7_route(self,kind,parts):
        routes=VOYAGES if kind=='ocean' else CARAVANS
        prof='Żeglarstwo' if kind=='ocean' else 'Kupiectwo'
        stem='wyprawa' if kind=='ocean' else 'karawana'
        option=norm(parts[0]) if parts else 'lista'
        db=self.server.db;aid=self.account_id
        if option in ('lista','list','status'):
            ongoing=db.conn.execute('SELECT destination,ready_at,tier FROM v700_jobs WHERE account_id=? AND kind=?',(aid,kind)).fetchone()
            if ongoing:
                await self.send(f'{stem}: trwa transport do {ongoing["destination"]}; pozostało {max(0,int(ongoing["ready_at"])-int(time.time()))} s.')
            for key,route in routes.items():
                await self.send(f'{key}: poziom {route[0]}; zapasy: '+inputs_text(route[3] if kind=='ocean' else route[3])+'.')
            return
        if option in ('start','rozpocznij','wyslij','wyślij'):
            dest=norm(' '.join(parts[1:]))
            resolved=next((key for key in routes if norm(key)==dest),None)
            if not resolved:
                await self.send(f'{stem} start <'+ '|'.join(routes)+'>.');return
            route=routes[resolved]
            need,place,duration,inputs=route if kind=='ocean' else (routes[resolved][0],routes[resolved][1],routes[resolved][4],routes[resolved][3])
            origin='harbor' if kind=='ocean' else 'market'
            if str(self.character.room_id) not in AREAS[origin]:
                await self.send(f'Wyrusz na {stem} z miejsca {origin}.');return
            if not self._v7_ready(prof) or self._v7_level(prof)<need:
                await self.send(f'{stem}: potrzebne narzędzie i poziom {need}.');return
            ongoing=db.conn.execute('SELECT destination FROM v700_jobs WHERE account_id=? AND kind=?',(aid,kind)).fetchone()
            if ongoing:
                await self.send('Najpierw zakończ rozpoczętą wyprawę/karawanę: '+ongoing['destination']);return
            if kind=='ocean':
                duration=max(60,duration-15*self._v7_upgrade('latarnia'))
            def update():
                db.conn.execute('INSERT INTO v700_jobs(account_id,kind,destination,tier,ready_at) VALUES(?,?,?,?,?)',
                                (aid,kind,resolved,need,int(time.time())+duration))
            result,error=self._v7_exec(inputs,(),prof,need,update=update)
            if error:await self.send(error);return
            await self._v7_emit(f'Rozpoczęto {stem}: {place}. Potrwa {duration} sekund.',
                                'Zużyto '+inputs_text(inputs)+'.',result)
            return
        if option in ('odbierz','zakoncz','zakończ','powrot','powrót'):
            ongoing=db.conn.execute('SELECT destination,ready_at,tier FROM v700_jobs WHERE account_id=? AND kind=?',(aid,kind)).fetchone()
            if not ongoing:
                await self.send(f'Brak trwającej {stem}.');return
            remaining=int(ongoing['ready_at'])-int(time.time())
            if remaining>0:
                await self.send(f'{stem}: pozostało {remaining} s.');return
            place=ongoing['destination']; tier=int(ongoing['tier'])
            expected_room= 'sea' if kind=='ocean' else 'market'
            if str(self.character.room_id) not in AREAS[expected_room]:
                await self.send(f'Odbiór wymaga terenu {expected_room}; nie można zdalnie otrzymać towarów.');return
            reward='v700_ocean_seal' if kind=='ocean' else 'v700_trade_seal'
            product='v600_voyage_log' if kind=='ocean' else 'v600_trade_receipt'
            quantity=1+TIERS.index(tier)
            quantity+=self._v7_upgrade('stocznia')//2 if kind=='ocean' else self._v7_upgrade('magazyn')//2
            # Reward determined by authored difficulty, not level requirements.
            price=(1300+tier*70)*quantity
            if kind=='trade':
                # Day-by-day regional demand is deterministic and persistent
                # across restarts: same price for all characters on one day.
                multiplier=100+((sum(map(ord,place))+int(time.time())//86400*17)%31)
                price=price*multiplier//100
            def update():
                db.conn.execute('DELETE FROM v700_jobs WHERE account_id=? AND kind=?',(aid,kind))
            result,error=self._v7_exec((),((reward,quantity),(product,1)),prof,tier,
                                       coin_reward=price,update=update)
            if error:await self.send(error);return
            await self._v7_emit(f'Zakończono {stem} {place}. +{price} srebra, {quantity} pieczęci, produkt i EXP.',
                                'Dostawa i nagrody zapisane trwale.',result)
            return
        await self.send(f'{stem}: lista, start <cel>, odbierz.')

    async def _v7_hunting(self,parts):
        """Hunts require real credited elite/rare/boss kills, never item spam."""
        mode=norm(' '.join(parts))
        db=self.server.db;aid=self.account_id
        ongoing=db.conn.execute('SELECT tier,needed,progress FROM v700_hunts WHERE account_id=?',(aid,)).fetchone()
        if mode in ('','status','lista'):
            if not ongoing:await self.send('Łowy: brak aktywnego kontraktu; wpisz imperium7 lowy start w dziczy.')
            else:await self.send(f'Łowy: {ongoing["progress"]}/{ongoing["needed"]}; cel: elity, rzadkie bestie i bossy od poziomu {ongoing["tier"]}.')
            return
        if mode=='start':
            if ongoing:
                await self.send('Masz już aktywne łowy; ukończ i odbierz nagrodę.');return
            if str(self.character.room_id) not in AREAS['wild']:
                await self.send('Łowy rozpoczynasz na otwartym terenie dziczy.');return
            prof='Łowiectwo'
            if not self._v7_ready(prof):
                await self.send('Wymagany Nóż Łowiecki.');return
            tier=tier_for(self._v7_level(prof))
            needed=2+TIERS.index(tier)*2
            db.conn.execute('INSERT INTO v700_hunts(account_id,tier,needed,progress,started_at) VALUES(?,?,?,?,?)',
                            (aid,tier,needed,0,int(time.time())))
            db.conn.commit()
            await self.send(f'Łowy rozpoczęte: pokonaj {needed} elitarnych, rzadkich lub bossowych potworów od poziomu {tier}. Liczą się prawdziwe zabicia drużyny.')
            return
        if mode=='odbierz':
            if not ongoing or int(ongoing['progress'])<int(ongoing['needed']):
                await self.send('Łowy nie są jeszcze zakończone.');return
            if str(self.character.room_id) not in AREAS['wild']:
                await self.send('Po trofeum wróć na teren łowiecki.');return
            tier=int(ongoing['tier']);needed=int(ongoing['needed'])
            def update(): db.conn.execute('DELETE FROM v700_hunts WHERE account_id=?',(aid,))
            result,error=self._v7_exec((),(('v700_hunt_seal',1+TIERS.index(tier)),),
                                       'Łowiectwo',tier,coin_reward=needed*(1500+90*tier),update=update)
            if error:await self.send(error);return
            await self._v7_emit(f'Legendarne łowy zakończone. Trofeum i EXP przyznane.',
                                'Wynik prawdziwych walk: '+str(needed)+'.',result)
            return
        await self.send('imperium7 lowy lista / start / odbierz.')

    async def _v7_master(self,raw):
        key=norm(raw)
        if key in ('','lista','list'):
            await self.send('Kontrakty mistrzowskie: imperium7 mistrzostwo <profesja>.')
            await self.send('; '.join(MASTER_INPUT))
            return
        prof=next((x for x in MASTER_INPUT if norm(x)==key),None)
        if not prof:
            await self.send('Nieznana profesja; wpisz imperium7 mistrzostwo lista.');return
        if str(self.character.room_id) not in AREAS['market']:
            await self.send('Kontrakty mistrzowskie składa się na targu.');return
        if not self._v7_ready(prof):
            await self.send('Do kontraktu potrzebujesz własnego narzędzia.');return
        level=self._v7_level(prof)
        tier=tier_for(level)
        amount=3+TIERS.index(tier)*2
        item=MASTER_INPUT[prof]
        day=int(time.time())//86400
        db=self.server.db;aid=self.account_id
        claimed=db.conn.execute('SELECT 1 FROM v700_master_contracts WHERE account_id=? AND profession=? AND day=?',
                                (aid,prof,day)).fetchone()
        if claimed:
            await self.send(f'Mistrzostwo {prof}: dzisiejszy kontrakt odebrany.');return
        def update():
            db.conn.execute('INSERT INTO v700_master_contracts(account_id,profession,day) VALUES(?,?,?)',(aid,prof,day))
        coin=(1200+tier*135)*amount
        result,error=self._v7_exec(((item,amount),),(),prof,tier,coin_reward=coin,update=update)
        if error:
            await self.send(f'Kontrakt {prof}: potrzebne {amount} × {item}. '+error);return
        await self._v7_emit(f'Kontrakt {prof} zakończony: +{coin} srebra i EXP.',
                            'Oddano '+inputs_text(((item,amount),))+'.',result)

    async def _v7_story(self):
        from systems.living_empire_v7000 import STORY
        done=0
        active=None
        for i,qid in enumerate(STORY_IDS):
            state=self.server.db.quest(self.account_id,qid)
            if state and state['status']=='completed':done+=1
            elif active is None:active=(i,qid,state)
        await self.send(f'Kronika Imperium: {done}/64 etapów. Każda część wymaga prawdziwej pracy i materiałów.')
        if active:
            i,qid,state=active
            chapter=i//8;stage=i%8
            await self.send(f'Następny etap {i+1}: {STORY[chapter][2]}, próba {stage+1}/8; mistrz: {STORY[chapter][3]}.')
            await self.send('Odszukaj mistrza w osobnej izbie przy '+STORY[chapter][1]+'. Wpisz quest list, przyjmij 1.')
            await self.send('Stan: '+(str(state['status']) if state else 'nieprzyjęty')+'.')
