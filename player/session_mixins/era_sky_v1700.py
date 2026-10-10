# -*- coding: utf-8 -*-
"""Persistent class summons, soul upgrades, sky discovery and personal PvE cities."""
from __future__ import annotations
import time
import random
import unicodedata
from data.mobs import MOB_TEMPLATES

SUMMONS={
 'pajak':('Szkielet Pająka','Nekromanta',{'v1700_common_tooth':2},'physical',.40),
 'wojownik':('Szkielet Wojownika','Nekromanta',{'v1700_dragon_tooth':1},'physical',.67),
 'mag':('Szkielet Maga','Nekromanta',{'v1700_dragon_tooth':2},'magic',.72),
 'lifeoak':('Life Oak','Druid',{'v1702_pinecone':2},'magic',.52),
 'ancientoak':('Ancient Oak','Druid',{'v1702_pinecone':5},'magic',.85),
 'wilk':('Wilk Runiczny','Druid',{},'physical',.44),
 'sowa':('Sowa Gwiezdna','Druid',{},'magic',.46),
 'niedzwiedz':('Niedźwiedź Runiczny','Druid',{},'physical',.66),
}


# Tiers are inspired by Alter Aeon's colored soulstones, but Soulbound
# calculates its own rarity, mana expenditure and combat scaling.
# The original uncolored v1.70.0 stone is the red tier: NO DATA LOSS.
from systems.soulstones_v1701 import SOULSTONE_TIERS, STONE_ALIASES, STONE_BY_KEY
from systems.mage_elementals_v1702 import ELEMENTALS, ELEMENTS, RANKS, resolve_elemental
from systems.druid_call_v1708 import ANIMALS, terrain_animals, biome_for_room, normalize_animal
from systems.necro_constructs_v1710 import NECRO_MINIONS, summon_key
SUMMONS.update({key:(spec['name'],'Mag',{},'magic',spec['damage']) for key,spec in ELEMENTALS.items()})
SUMMONS.update({key:(spec['name'],'Druid',{},spec['damage_kind'],spec['damage']) for key,spec in ANIMALS.items() if key not in SUMMONS})
SUMMONS.update({key:(spec[0],'Nekromanta',spec[3],spec[4],spec[5]) for key,spec in NECRO_MINIONS.items()})
SUMMON_MANA = {'pajak':45,'wojownik':90,'mag':120,'lifeoak':80,
               'ancientoak':180,'wilk':50,'sowa':55,'niedzwiedz':110}
SUMMON_MANA.update({key: spec['mana'] for key,spec in ELEMENTALS.items()})
SUMMON_MANA.update({key: spec['mana'] for key,spec in ANIMALS.items()})
SUMMON_MANA.update({key: spec[2] for key,spec in NECRO_MINIONS.items()})
# Druids unlock living oaks much later than ordinary woodland calls.
DRUID_OAK_MIN_LEVEL={'lifeoak':150, 'ancientoak':400}


def stone_for_enemy(enemy_level, is_boss=False, roll=None):
    """Only sufficiently mighty enemies may yield rarer colors."""
    level = max(1, int(enemy_level))
    ceiling = max(i for i, tier in enumerate(SOULSTONE_TIERS) if level >= tier[4])
    r = random.random() if roll is None else max(0.0, min(0.999999, float(roll)))
    drop = 0 if r < 0.15 else (1 if r < 0.48 else (2 if r < 0.78 else 3))
    return SOULSTONE_TIERS[max(0, ceiling - max(0, drop - int(bool(is_boss))))]


def summon_display(kind, grade):
    grade = max(0, min(8, int(grade)))
    if grade >= 4 and kind == 'wojownik': return 'Rycerz Szkieletów'
    if grade >= 4 and kind == 'mag': return 'Szkielet Licz'
    return SUMMONS[kind][0]


def ascii_fold(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(text).casefold()) if not unicodedata.combining(c)).replace('ł','l').strip()


def ensure_schema(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS summons_v1700 (
      account_id INTEGER NOT NULL, summon_type TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 1,
      active INTEGER NOT NULL DEFAULT 1, soul_rank INTEGER NOT NULL DEFAULT 0,
      hp INTEGER NOT NULL DEFAULT 0, max_hp INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY(account_id,summon_type))''')
    conn.execute('''CREATE TABLE IF NOT EXISTS cities_v1700 (
      account_id INTEGER PRIMARY KEY, title TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 1,
      walls INTEGER NOT NULL DEFAULT 0, market INTEGER NOT NULL DEFAULT 0,
      workshop INTEGER NOT NULL DEFAULT 0, infirmary INTEGER NOT NULL DEFAULT 0,
      market_claim INTEGER NOT NULL DEFAULT 0)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS druid_pinecones_v1702 (
      account_id INTEGER PRIMARY KEY, last_gather INTEGER NOT NULL DEFAULT 0)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS class_paths_v1700 (
      account_id INTEGER NOT NULL, class_name TEXT NOT NULL, path TEXT NOT NULL,
      PRIMARY KEY(account_id,class_name))''')
    # Durable migration for databases created during preview/testing.
    city_cols={r[1] for r in conn.execute('PRAGMA table_info(cities_v1700)')}
    summon_cols={r[1] for r in conn.execute('PRAGMA table_info(summons_v1700)')}
    if 'soul_rank' not in summon_cols:
        conn.execute('ALTER TABLE summons_v1700 ADD COLUMN soul_rank INTEGER NOT NULL DEFAULT 0')
    if 'hp' not in summon_cols:
        conn.execute('ALTER TABLE summons_v1700 ADD COLUMN hp INTEGER NOT NULL DEFAULT 0')
    if 'max_hp' not in summon_cols:
        conn.execute('ALTER TABLE summons_v1700 ADD COLUMN max_hp INTEGER NOT NULL DEFAULT 0')
    if 'xp' not in summon_cols:
        conn.execute('ALTER TABLE summons_v1700 ADD COLUMN xp INTEGER NOT NULL DEFAULT 0')
    if 'stance' not in summon_cols:
        conn.execute("ALTER TABLE summons_v1700 ADD COLUMN stance TEXT NOT NULL DEFAULT 'atakuj'")
    if 'market_claim' not in city_cols:
        conn.execute('ALTER TABLE cities_v1700 ADD COLUMN market_claim INTEGER NOT NULL DEFAULT 0')
    conn.commit()


def summon_upgrade_stones(level):
    return max(1,1+(max(1,int(level))-1)//3)


from player.session_mixins.chaos_v1800 import SessionChaosV1800Mixin
from systems.era_chaos_v1800 import ELEMENT_ALIASES

class SessionSkyV1700Mixin(SessionChaosV1800Mixin):
    def _v1700_conn(self):
        conn=self.server.db.conn
        if not getattr(self.server.db,'_v1700_ready',False):
            ensure_schema(conn)
            self.server.db._v1700_ready=True
        return conn

    def _v1700_qty(self, item):
        db=self.server.db
        return db.item_qty(self.account_id,item)+db.storage_qty(self.account_id,'craftbox',item)

    def _v1700_spend_and_write(self,required,sql,params):
        """Atomically consume mats and persist summon or upgrade, or change nothing."""
        db=self.server.db
        if any(self._v1700_qty(k)<v for k,v in required.items()):return False
        conn=db.conn
        conn.execute('SAVEPOINT v1700_summon')
        try:
            for item,qty in required.items():
                from_box=min(db.storage_qty(self.account_id,'craftbox',item),qty)
                if from_box and not db.remove_storage_item(self.account_id,'craftbox',item,from_box,commit=False):
                    raise RuntimeError('Błąd rezerwacji materiału')
                if qty>from_box and not db.remove_item(self.account_id,item,qty-from_box,commit=False):
                    raise RuntimeError('Błąd rezerwacji materiału')
            conn.execute(sql,params)
            conn.execute('RELEASE SAVEPOINT v1700_summon')
            conn.commit()
            return True
        except Exception:
            conn.execute('ROLLBACK TO SAVEPOINT v1700_summon')
            conn.execute('RELEASE SAVEPOINT v1700_summon')
            raise

    def _v1702_summon_max_hp(self, kind, level=1):
        """Give each summon its own durable life pool, scaled to its owner."""
        try:
            owner_hp=max(1,int(self.max_hp()))
        except (AttributeError,TypeError,ValueError):
            owner_hp=max(100,int(getattr(self.character,'character_level',1) or 1)*100)
        kind_spec=SUMMONS[kind]
        factor={'pajak':.35,'wojownik':.80,'mag':.55,'lifeoak':.95,
                'ancientoak':1.55,'wilk':.50,'sowa':.42,'niedzwiedz':1.1}.get(kind,.65)
        elemental=ELEMENTALS.get(kind)
        if elemental:
            factor=(.40,.65,.95)[elemental['rank']]
            if elemental['element'] in ('lod','krysztal'):
                factor*=1.35
        if kind in ANIMALS:
            factor=ANIMALS[kind]['hp_factor']
        if kind in NECRO_MINIONS:
            factor=NECRO_MINIONS[kind][6]
        return max(40,int(owner_hp*factor*(1+max(0,int(level)-1)*.075)))

    def _v1710_refresh_summon_health(self, conn):
        """Refresh living HP limits after stats/EQ/level change without free healing.

        Keep the HP ratio, preserve deaths and mastery. Only writes when power
        really changes, so idle time has no extra database traffic.
        """
        rows=conn.execute('SELECT summon_type,level,hp,max_hp FROM summons_v1700 '
                          'WHERE account_id=? AND active=1 AND hp>0',(self.account_id,)).fetchall()
        changed=0
        for r in rows:
            kind=r['summon_type']
            if kind not in SUMMONS:continue
            old=max(1,int(r['max_hp']))
            new=self._v1702_summon_max_hp(kind,r['level'])
            if old==new:continue
            life=max(1,min(new,(int(r['hp'])*new+old-1)//old))
            conn.execute('UPDATE summons_v1700 SET hp=?,max_hp=? '
                         'WHERE account_id=? AND summon_type=? AND active=1 AND hp>0',
                         (life,new,self.account_id,kind))
            changed+=1
        if changed:conn.commit()
        return changed

    def _v1710_earn_summon_xp(self, conn, kind, damage):
        """Steady combat mastery, no level cap; stone skeletons keep stone levels."""
        if kind in ('wojownik','mag') or kind not in SUMMONS:return False
        row=conn.execute('SELECT level,xp FROM summons_v1700 WHERE account_id=? AND summon_type=?',
                         (self.account_id,kind)).fetchone()
        if not row:return False
        level=max(1,int(row['level']));xp=max(0,int(row['xp']))
        owner=max(1,int(max(self.physical_power(),self.spell_power())))
        earned=max(1,min(35,2+int(max(0,damage)//max(1,owner//6))))
        xp+=earned; grew=False
        # Increasing quadratic requirements keep high-level grind meaningful.
        while xp>=50+level*level*12:
            xp-=50+level*level*12
            level+=1;grew=True
        conn.execute('UPDATE summons_v1700 SET level=?,xp=? WHERE account_id=? AND summon_type=?',
                     (level,xp,self.account_id,kind))
        if grew:self._v1710_refresh_summon_health(conn)
        conn.commit()
        return grew

    def _v1702_prepare_summon_lives(self,conn):
        """One-time backfill of pre-HP live pets. Dead (max_hp>0) stay dead."""
        rows=conn.execute('SELECT summon_type,level,active,max_hp FROM summons_v1700 '
                          'WHERE account_id=? AND max_hp=0',(self.account_id,)).fetchall()
        for row in rows:
            kind=row['summon_type']
            if kind not in SUMMONS:continue
            maximum=self._v1702_summon_max_hp(kind,row['level'])
            conn.execute('UPDATE summons_v1700 SET hp=?,max_hp=? '
                         'WHERE account_id=? AND summon_type=? AND max_hp=0',
                         (maximum if row['active'] else 0,maximum,self.account_id,kind))
        if rows:conn.commit()

    def _v1703_dismiss_summons_on_login(self):
        """No summon survives a new session, but mastery/rank are permanent.

        Do not infer existence from the old persisted `active` flag: on a new
        login every companion (including hidden ones) must be cast anew.
        This applies to skeletons, druid creatures/trees and elementals alike.
        The next cast always requires mana and its original physical materials.
        """
        if not self.character or self.account_id is None:
            return 0
        conn=self._v1700_conn()
        self._v1702_prepare_summon_lives(conn)  # migrate older schemas first
        cur=conn.execute('UPDATE summons_v1700 SET active=0, hp=0 '
                         'WHERE account_id=? AND (active<>0 OR hp<>0)',
                         (self.account_id,))
        conn.commit()
        return max(0,int(cur.rowcount))

    def _v1702_upgrade_summon_life(self,conn,kind,level):
        """More levels add max HP, but never bring a fallen servant to life."""
        row=conn.execute('SELECT hp,max_hp FROM summons_v1700 WHERE account_id=? AND summon_type=?',
                         (self.account_id,kind)).fetchone()
        if not row:return
        old_max=max(0,int(row['max_hp']))
        new_max=self._v1702_summon_max_hp(kind,level)
        current=int(row['hp'])
        new_hp=0 if current<=0 else min(new_max,max(1,current+max(0,new_max-old_max)))
        conn.execute('UPDATE summons_v1700 SET hp=?,max_hp=? WHERE account_id=? AND summon_type=?',
                     (new_hp,new_max,self.account_id,kind));conn.commit()

    def _v1711_companions_for_healing(self, include_party=False):
        """Living, active summons of local allies only; never foreign/hidden/dead."""
        sessions=[self]
        if include_party:
            sessions=list(self.server.party_sessions(
                self.account_id, same_room=self.character.room_id) or ())
            if self not in sessions:sessions.append(self)
        results=[]
        for owner in sessions:
            if (getattr(owner,'closed',False) or not owner.character
                    or owner.character.room_id!=self.character.room_id
                    or owner.current_hp<=0):continue
            conn=owner._v1700_conn()
            owner._v1702_prepare_summon_lives(conn)
            owner._v1710_refresh_summon_health(conn)
            for row in conn.execute('SELECT summon_type,level,soul_rank,hp,max_hp '
                                    'FROM summons_v1700 WHERE account_id=? AND active=1 AND hp>0',
                                    (owner.account_id,)).fetchall():
                kind=row['summon_type']
                if kind in SUMMONS and owner._v1700_class(SUMMONS[kind][1]):
                    results.append((owner,row))
        return results

    def _v1711_find_companion(self, name, include_party=False):
        wanted=ascii_fold(name)
        if not wanted:return None
        found=[]
        for owner,row in self._v1711_companions_for_healing(include_party):
            key=row['summon_type']; grade=int(row['soul_rank'] or 0)
            names={ascii_fold(key),ascii_fold(SUMMONS[key][0]),ascii_fold(summon_display(key,grade))}
            if wanted in names:
                found.append((owner,row))
        # Own creature takes precedence. Ambiguous party matches are not guessed.
        own=[target for target in found if target[0] is self]
        if own:return own[0]
        return found[0] if len(found)==1 else None

    def _v1711_heal_companion(self, owner, row, amount):
        """Heal surviving summoned ally without resurrecting a dead one.

        SQL guard and transactional update prevent an obsolete row snapshot from
        restoring HP after a summon was destroyed or dismissed.
        """
        from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
        if superboss_healing_blocked_v11179(owner):return 0
        amount=max(0,int(amount))
        if amount<=0:return 0
        conn=owner._v1700_conn()
        current=conn.execute('SELECT hp,max_hp FROM summons_v1700 '
                             'WHERE account_id=? AND summon_type=? AND active=1 AND hp>0',
                             (owner.account_id,row['summon_type'])).fetchone()
        if not current:return 0
        before=int(current['hp']);maximum=int(current['max_hp'])
        restored=min(amount,max(0,maximum-before))
        if restored<=0:return 0
        cur=conn.execute('UPDATE summons_v1700 SET hp=hp+? '
                         'WHERE account_id=? AND summon_type=? AND active=1 AND hp=? AND max_hp=?',
                         (restored,owner.account_id,row['summon_type'],before,maximum))
        conn.commit()
        return restored if cur.rowcount==1 else 0

    async def _v1711_summon_heal_command(self, raw):
        if not self.character:return
        from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
        value=ascii_fold(raw)
        targets=self._v1711_companions_for_healing()
        if not value:
            await self.send('Użycie: chowaniec lecz <nazwa> albo chowaniec lecz wszystko. Czar kosztuje manę i nie wskrzesza pokonanych pomocników.')
            return
        if superboss_healing_blocked_v11179(self):
            await self.send('Nullify Healing blokuje leczenie przywołań.')
            return
        if value in ('wszystko','all'):
            selected=[(owner,row) for owner,row in targets if int(row['hp'])<int(row['max_hp'])]
        else:
            match=self._v1711_find_companion(value)
            if not match:
                await self.send('Nie masz aktywnego, żywego przywołania o tej nazwie. Sprawdź chowaniec lista.')
                return
            selected=[match] if int(match[1]['hp'])<int(match[1]['max_hp']) else []
        if not selected:
            await self.send('Żadne żywe przywołanie nie potrzebuje leczenia. Martwy pomocnik wymaga ponownego przywołania.')
            return
        cost=60 if len(selected)==1 else 85+25*(len(selected)-1)
        if self.current_mana<cost:
            await self.send(f'Za mało many: leczenie wymaga {cost} MP, masz {self.current_mana}.')
            return
        restored=[]
        for owner,row in selected:
            # Hybrid heal scales with summoner HP and the caster's magic/healing.
            power=max(1,int(self.healing_power_v1125()))
            amount=max(1,int(row['max_hp']*.25)+power//5)
            actual=self._v1711_heal_companion(owner,row,amount)
            if actual:
                restored.append((row['summon_type'],actual))
        if not restored:
            await self.send('Nie udało się uleczyć przywołań. Mana nie została pobrana.')
            return
        self.current_mana-=cost
        names=', '.join(f'{SUMMONS[k][0]} +{hp} HP' for k,hp in restored)
        await self.send(f'Wyleczono: {names}. Mana -{cost} MP; pozostało {self.current_mana} MP.')

    async def summon_take_enemy_hit_v1702(self,mob,raw_damage=None,roll=None):
        """An enemy can attack and destroy a real summon instead of its master.

        Only replaces an ordinary hit. Source-authored scripted boss mechanics
        and phases are still resolved by the main combat loop.
        """
        if not self.character or not mob or not mob.alive:return False
        # No pets? Skip all work. A class change never keeps another class's
        # minions active in combat even if the database remembers them.
        conn=self._v1700_conn()
        self._v1702_prepare_summon_lives(conn)
        self._v1710_refresh_summon_health(conn)
        pets=[r for r in conn.execute('SELECT summon_type,level,hp,max_hp,stance FROM summons_v1700 '
                'WHERE account_id=? AND active=1 AND hp>0',(self.account_id,)).fetchall()
              if r['summon_type'] in SUMMONS and self._v1700_class(SUMMONS[r['summon_type']][1])]
        if not pets:return False
        if (random.random() if roll is None else roll)>=(.52 if any(
                r['stance']=='bron' for r in pets) else .32):return False
        chosen=random.choice(pets)
        hp=int(chosen['hp']);maximum=max(1,int(chosen['max_hp']))
        # A real monster hit. The percentage floor prevents companions from
        # surviving forever on enormous late-game HP while mobs deal tiny hits.
        base=max(1,int(raw_damage if raw_damage is not None else
                       MOB_TEMPLATES.get(mob.template_id,{}).get('damage',1)))
        pressure=max(1,int(maximum*.10))
        hit=max(base,pressure)
        # Vitality roles endure longer, but every summon can eventually fall.
        kind=chosen['summon_type']
        if kind in ('ancientoak','niedzwiedz') or kind.startswith(('zywiolak_lod','zywiolak_krysztal')):
            hit=max(1,int(hit*.75))
        if kind in NECRO_MINIONS and NECRO_MINIONS[kind][7]=='obrona':
            hit=max(1,int(hit*.72))
        if kind in ANIMALS and ANIMALS[kind]['role']=='obrona':
            hit=max(1,int(hit*.80))
        # Veteran guardians learn to brace, but damage reduction never exceeds 40%.
        if kind in NECRO_MINIONS or kind in ANIMALS:
            reduction=min(.15,max(0,int(chosen['level'])-1)*.002)
            hit=max(1,int(hit*(1-reduction)))
        hit=min(hp,hit)
        remaining=max(0,hp-hit)
        conn.execute('UPDATE summons_v1700 SET hp=?,active=? '
                     'WHERE account_id=? AND summon_type=? AND hp=? AND active=1',
                     (remaining,1 if remaining>0 else 0,self.account_id,kind,hp))
        conn.commit()
        name=SUMMONS[kind][0]
        enemy_name=MOB_TEMPLATES.get(mob.template_id,{}).get('name','Przeciwnik')
        if remaining:
            msg=f'{enemy_name} atakuje {name} za {hit} obrażeń. {name}: {remaining}/{maximum} HP.'
        else:
            msg=f'{enemy_name} rozbija {name}! Pomocnik traci całe HP i znika. Aby przywołać go ponownie, użyj chowaniec aktywuj {kind} (mana i materiały).'
        await self.send_combat(msg,detail='essential')
        await self.server.party_combat_broadcast(self,msg,detail='essential')
        return True

    async def _v1701_need_mana(self, cost):
        if self.current_mana < cost:
            await self.send(f'Za mało many. Potrzeba {cost} MP, masz {self.current_mana} MP.')
            return False
        return True

    async def _v1701_forge(self, key):
        if not self._v1700_class('Nekromanta'):
            await self.send('Tylko Nekromanta może scalać Kamienie Duszy.'); return
        if self.combat_mob_key:
            await self.send('Scalanie Kamieni Duszy wymaga zakończenia walki.'); return
        key=STONE_ALIASES.get(ascii_fold(key),ascii_fold(key))
        if key not in STONE_BY_KEY or key=='czarny':
            await self.send('Wpisz: nekro scal <kolor> (od czerwonego do białego).'); return
        index,old=STONE_BY_KEY[key]
        new=SOULSTONE_TIERS[index+1]
        cost=35+40*index
        if not await self._v1701_need_mana(cost):return
        if self._v1700_qty(old[2])<3:
            await self.send(f'Potrzeba 3 x {old[1]}; masz {self._v1700_qty(old[2])}.'); return
        db=self.server.db;conn=db.conn
        conn.execute('SAVEPOINT v1701_forge')
        try:
            take_from_box=min(db.storage_qty(self.account_id,'craftbox',old[2]),3)
            if take_from_box and not db.remove_storage_item(self.account_id,'craftbox',old[2],take_from_box,commit=False):
                raise RuntimeError('Brak materiałów w szkatułce')
            if take_from_box<3 and not db.remove_item(self.account_id,old[2],3-take_from_box,commit=False):
                raise RuntimeError('Brak materiałów w ekwipunku')
            db.add_item(self.account_id,new[2],1,commit=False)
            conn.execute('RELEASE SAVEPOINT v1701_forge');conn.commit()
        except Exception:
            conn.execute('ROLLBACK TO SAVEPOINT v1701_forge');conn.execute('RELEASE SAVEPOINT v1701_forge')
            raise
        self.current_mana-=cost
        await self.send(f'Scalono 3 x {old[1]} w {new[1]}. Mana -{cost} MP. Zostało {self.current_mana} MP.')

    def _v1700_city_bonuses(self):
        if not self.character:return (0,0,0)
        conn=self._v1700_conn()
        row=conn.execute('SELECT walls,workshop,infirmary FROM cities_v1700 WHERE account_id=?',(self.account_id,)).fetchone()
        if not row:return (0,0,0)
        return (int(row['walls']),int(row['workshop']),int(row['infirmary']))

    def _v1700_class(self, name):
        return bool(self.character and name in self.active_class_names())

    async def sky_v1700(self, raw=''):
        key=ascii_fold(raw)
        if key in ('bossowie','legendy'):
            await self.send('WOJNY LEGEND: trzy krainy niebios i po trzech bossów w każdej. Polowania z prawdziwymi nagrodami u strażniczek krain.')
        elif key in ('rzemioslo','profesje','craft'):
            await self.send('ARCYMISTRZOWIE 6.0: wszystkie 14 profesji mają po dwie nowe próby. W przystani niebios i trzech regionach stoją NPC. Wpisz quest list. Sześć nowych projektów w kuźni: receptury.')
        else:
            await self.send('NIEBO 1.0: z Traktu Czterech Wiatrów, przy Kamiennym Moście Traktatów, idź GÓRA do Przystani Sterowców. PÓŁNOC — Burze, WSCHÓD — Zorze, POŁUDNIE — Otchłań, ZACHÓD — Miasta Graczy.')
            await self.send('Pomoc: niebo bossowie, niebo profesje, chowaniec, nekro, druid, miasto, przebudzenie.')

    async def summons_v1700(self, raw=''):
        if not self.character:return
        text=ascii_fold(raw); parts=text.split()
        if parts and parts[0] in ('kamienie','kolory','soulstone'):
            await self.send('KAMIENIE DUSZY — od najsłabszego do najsilniejszego:')
            for i, tier in enumerate(SOULSTONE_TIERS):
                await self.send(f'{i+1}. {tier[1]}: {self._v1700_qty(tier[2])} szt.; moc ×{tier[3]:.2f}.')
            await self.send('Ulepszanie: chowaniec ulepsz wojownik <kolor> / mag <kolor>. Scalanie: nekro scal <kolor> (3 sztuki w 1 wyższego koloru).')
            return
        if not parts or parts[0] in ('info','lista','status','pomoc'):
            conn=self._v1700_conn()
            self._v1702_prepare_summon_lives(conn)
            self._v1710_refresh_summon_health(conn)
            rows=conn.execute('SELECT summon_type,level,active,soul_rank,hp,max_hp FROM summons_v1700 WHERE account_id=? ORDER BY summon_type',(self.account_id,)).fetchall()
            await self.send('CHOWAŃCE: chowaniec lecz <nazwa|wszystko> (mana i tylko żywe przywołania); chowaniec przywolaj <typ>, chowaniec ulepsz <wojownik|mag> <kolor>, chowaniec kamienie, chowaniec schowaj/aktywuj <typ>; chowaniec odwolaj <nazwa|wszystkie>. Do 3 aktywnych. Każdy ma HP, może zginąć; powrót wymaga many i materiałów właściwych dla rodzaju (Mag bez materiałów).')
            await self.send('Nekromanta: pająk — 2 zwykłe zęby; wojownik — 1 smoczy ząb; mag — 2 smocze zęby. Dziewięć kolorów Kamieni Duszy ulepsza wojowników i magów. nekro wyrwij; nekro scal <kolor>.')
            await self.send('Druid: call list (zwierzęta na aktualnym terenie), call <zwierzę>, call squirrel (wiewiórka dostarcza szyszki za 20 MP), order <zwierzę> <atakuj|bron|wspieraj|czekaj>. Bez Pieczęci Chowańców. Life Oak: poziom 150+, 2 szyszki i 80 MP; Ancient Oak: poziom 400+, 5 szyszek i 180 MP.')
            await self.send('Mag: mag lista, mag przywolaj ogien mniejszy / blyskawice / lod potezny / krysztal. 4 żywioły, po 3 stopnie; mana za przywołanie i ataki. Bez zębów i Kamieni Duszy.')
            await self.send('Nekromanta: nekro lista — konstrukty, nieumarli, materiały, mana, wymagane poziomy. nekro przywolaj metal / gliniany / kostny_straznik itd. Rozkazy: order <nazwa|all> <atakuj|bron|wspieraj|czekaj>.')
            if not rows:await self.send('Nie masz jeszcze przywołań.')
            for row in rows:
                spec=SUMMONS.get(row['summon_type'])
                if spec:
                    grade=int(row['soul_rank'] or 0)
                    color=SOULSTONE_TIERS[grade][1] if grade else 'bez kamienia'
                    state='aktywny' if row['active'] else ('nieprzywołany/pokonany' if int(row['hp'])<=0 else 'schowany')
                    await self.send(f"{summon_display(row['summon_type'],grade)}: poziom {row['level']}, {color}, {state}, HP {row['hp']}/{row['max_hp']}.")
            return
        if parts[0] in ('odwolaj', 'odwołaj', 'dismiss'):
            requested = ' '.join(parts[1:]).strip()
            if not requested:
                await self.send('Użycie: chowaniec odwolaj <typ|wszystkie>. Zwierzę pozostaje zapisane i może być przywołane ponownie.')
                return
            conn = self._v1700_conn()
            if requested in ('all', 'wszystkie', 'wszystko'):
                cur = conn.execute('UPDATE summons_v1700 SET active=0 WHERE account_id=? AND active=1', (self.account_id,))
                conn.commit()
                await self.send(f'Odwołano {cur.rowcount} aktywnych przywołań. Ich poziomy, HP i ulepszenia pozostały zapisane.')
                return
            kind = summon_key(requested)
            if kind not in SUMMONS:
                kind = normalize_animal(requested)
            if kind not in SUMMONS:
                matching = [key for key, spec in SUMMONS.items() if ascii_fold(spec[0]) == requested]
                if len(matching) == 1:
                    kind = matching[0]
            if kind not in SUMMONS:
                await self.send('Nieznane przywołanie. Wpisz chowaniec lista.')
                return
            cur = conn.execute('UPDATE summons_v1700 SET active=0 WHERE account_id=? AND summon_type=? AND active=1', (self.account_id, kind))
            conn.commit()
            await self.send((f'Odwołano {SUMMONS[kind][0]}. Postęp został zachowany.' if cur.rowcount else f'{SUMMONS[kind][0]} nie jest aktywny.'))
            return
        if parts[0] in ('lecz','heal'):
            await self._v1711_summon_heal_command(' '.join(parts[1:]));return
        if parts[0]=='scal' and len(parts)>1:
            await self._v1701_forge(parts[1]);return
        if parts[0] in ('dusza','wyrywanie','wyrwij'):
            await self._v1700_rip_soul()
            return
        if len(parts)<2 or parts[0] not in ('przywolaj','stworz','stworz','ulepsz','schowaj','aktywuj'):
            await self.send('Użycie: chowaniec przywolaj pajak / wojownik / mag / lifeoak / ancientoak / wilk / sowa / niedzwiedz. Mag: mag lista; mag przywolaj ogien mniejszy|zwykly|potezny. Kamienie Duszy: chowaniec ulepsz mag <kolor>.')
            return
        action,kind=parts[0],parts[1]
        if action in ('przywolaj','stworz','aktywuj','schowaj'):
            kind=summon_key(' '.join(parts[1:]))
        aliases={'pająk':'pajak','szkielet':'wojownik','skelet':'wojownik',
                 'life':'lifeoak','ancient':'ancientoak','niedzwiedź':'niedzwiedz','mage':'mag'}
        kind=aliases.get(kind,kind)
        spec=SUMMONS.get(kind)
        if spec is None:
            await self.send('Nieznany typ. Wpisz chowaniec lista.');return
        name,required_class,costs,_,_=spec
        # `chowaniec przywolaj/aktywuj` must not bypass local `call` fauna or level requirements.
        if kind in ANIMALS and action in ('przywolaj','aktywuj'):
            from data.rooms import ROOMS
            here=biome_for_room(ROOMS.get(self.character.room_id,{}),self.character.room_id)
            if kind not in terrain_animals(here):
                await self.send('To zwierzę nie występuje na bieżącym terenie. Wpisz call list.');return
            minimum=ANIMALS[kind].get('min_level',0)
            if int(getattr(self.character,'character_level',1) or 1)<minimum:
                await self.send(f'To zwierzę wymaga poziomu postaci {minimum}.');return
        if kind in DRUID_OAK_MIN_LEVEL and action in ('przywolaj','aktywuj'):
            minimum=DRUID_OAK_MIN_LEVEL[kind]
            if int(getattr(self.character,'character_level',1) or 1)<minimum:
                await self.send(f'{name} wymaga poziomu Druida {minimum}. Nie zużyto many ani szyszek.');return
        if kind in NECRO_MINIONS and action in ('przywolaj','aktywuj'):
            min_level=NECRO_MINIONS[kind][1]
            if int(getattr(self.character,'character_level',1) or 1)<min_level:
                await self.send(f'{name} wymaga poziomu postaci {min_level}. Materiały i mana nie zostały zużyte.');return
        if not self._v1700_class(required_class):
            await self.send(f'Tylko aktywny {required_class} może używać tego przywołania.');return
        if self.combat_mob_key and action in ('przywolaj','ulepsz'):
            await self.send('Przywoływanie i ulepszenia wymagają zakończenia walki.');return
        conn=self._v1700_conn()
        self._v1702_prepare_summon_lives(conn)
        row=conn.execute('SELECT level,active,soul_rank,hp,max_hp FROM summons_v1700 WHERE account_id=? AND summon_type=?',(self.account_id,kind)).fetchone()
        if action=='ulepsz':
            if kind not in ('wojownik','mag'):
                await self.send('Kamienie Duszy ulepszają TYLKO Szkielet Wojownika i Szkielet Maga.');return
            if not row:
                await self.send('Najpierw przywołaj tego szkieleta za smocze zęby.');return
            color=STONE_ALIASES.get(parts[2],parts[2]) if len(parts)>2 else 'czerwony'
            if color not in STONE_BY_KEY:
                await self.send('Nieznany kolor Kamienia Duszy. Wpisz chowaniec kamienie.');return
            index,tier=STONE_BY_KEY[color]
            mana_cost=55+index*15+max(1,int(row['level']))*3
            if not await self._v1701_need_mana(mana_cost):return
            stone_cost=summon_upgrade_stones(row['level'])
            new_max=self._v1702_summon_max_hp(kind,int(row['level'])+1)
            previous_max=max(0,int(row['max_hp']))
            previous_hp=max(0,int(row['hp']))
            new_hp=(0 if previous_hp==0 else min(new_max,max(1,previous_hp+max(0,new_max-previous_max))))
            if not self._v1700_spend_and_write({tier[2]:stone_cost},
                'UPDATE summons_v1700 SET level=level+1,soul_rank=MAX(soul_rank,?), hp=?, max_hp=? WHERE account_id=? AND summon_type=?',
                (index,new_hp,new_max,self.account_id,kind)):
                await self.send(f'Potrzebujesz {stone_cost} x {tier[1]}; masz {self._v1700_qty(tier[2])}.');return
            self.current_mana-=mana_cost
            new_grade=max(index,int(row['soul_rank']))
            await self.send(f'{summon_display(kind,new_grade)}: poziom {row["level"]+1}, rezonans {SOULSTONE_TIERS[new_grade][1]}. Zużyto {stone_cost} kamieni i {mana_cost} MP; zostało {self.current_mana} MP.');return
        if action in ('schowaj','aktywuj'):
            if not row:
                await self.send('Najpierw zdobądź przywołanie.');return
            mana_cost=0
            if action=='aktywuj' and not row['active']:
                active=conn.execute('SELECT COUNT(*) FROM summons_v1700 WHERE account_id=? AND active=1',(self.account_id,)).fetchone()[0]
                if active>=3:
                    await self.send('Maksymalnie 3 aktywne przywołania. Schowaj inne.');return
                mana_cost=SUMMON_MANA[kind]
                if not await self._v1701_need_mana(mana_cost):return
            # Trees always require fresh pinecones. Every fallen beast or skeleton
            # must also pay its original material cost. Living hidden summons cost MP
            # only (except trees), while elementals never need physical materials.
            reweave_materials = action=='aktywuj' and not row['active'] and (
                kind in ('lifeoak','ancientoak') or int(row['hp'])<=0)
            required_now = costs if reweave_materials else {}
            if required_now:
                if not self._v1700_spend_and_write(required_now,
                    'UPDATE summons_v1700 SET active=1,hp=max_hp WHERE account_id=? AND summon_type=?',
                    (self.account_id,kind)):
                    missing=', '.join(f'{k}: potrzeba {v}, masz {self._v1700_qty(k)}' for k,v in required_now.items())
                    await self.send('Brak materiałów do ponownego wezwania: '+missing);return
            else:
                conn.execute('UPDATE summons_v1700 SET active=?,hp=CASE WHEN ?=1 THEN max_hp ELSE hp END WHERE account_id=? AND summon_type=?',(1 if action=='aktywuj' else 0,1 if action=='aktywuj' else 0,self.account_id,kind))
                conn.commit()
            self.current_mana-=mana_cost
            await self.send(f'{name}: '+('aktywny.' if action=='aktywuj' else 'schowany.')+(f' Mana -{mana_cost} MP.' if mana_cost else ''))
            return
        if row:
            if int(row['active']):
                await self.send(f'{name} jest już przywołany. Możesz go schować: chowaniec schowaj {kind}.');return
            # `przywolaj` works after every login, not only `aktywuj`.
            await self.summons_v1700(f'aktywuj {kind}')
            return
        count=conn.execute('SELECT COUNT(*) FROM summons_v1700 WHERE account_id=? AND active=1',(self.account_id,)).fetchone()[0]
        if count>=3:
            await self.send('Masz 3 aktywne przywołania. Najpierw schowaj jedno.');return
        mana_cost=SUMMON_MANA[kind]
        if not await self._v1701_need_mana(mana_cost):return
        if not self._v1700_spend_and_write(costs,
            'INSERT INTO summons_v1700(account_id,summon_type,level,active,hp,max_hp) VALUES(?,?,1,1,?,?)',
            (self.account_id,kind,self._v1702_summon_max_hp(kind),self._v1702_summon_max_hp(kind))):
            missing=', '.join(f'{k}: {v} (masz {self._v1700_qty(k)})' for k,v in costs.items())
            await self.send('Brak materiałów: '+missing);return
        self.current_mana-=mana_cost
        await self.send(f'{name} dołącza do Ciebie. Mana -{mana_cost} MP, pozostało {self.current_mana} MP. Walczy automatycznie. Po kolejnym zalogowaniu musisz go przywołać ponownie.')

    async def mage_elementals_v1702(self,raw=''):
        """Player-facing Polish and English-friendly elemental spell command."""
        if not self.character:return
        if not self._v1700_class('Mag'):
            await self.send('Przywoływanie żywiołaków wymaga aktywnej klasy Maga.');return
        args=ascii_fold(raw).split()
        if not args or args[0] in ('lista','pomoc','status','info'):
            await self.send('MAG — ŻYWIOŁAKI: mag przywolaj <ogien|blyskawice|lod|krysztal> [mniejszy|zwykly|potezny].')
            await self.send('Mag schowaj <żywioł> [stopień]; mag aktywuj <żywioł> [stopień]. Każde wezwanie kosztuje MP i każde trafienie zużywa trochę many. Bez materiałów.')
            for element,(label,_) in ELEMENTS.items():
                costs=', '.join(f'{RANKS[i]} {ELEMENTALS[f"zywiolak_{element}_{RANKS[i]}"]["mana"]} MP' for i in range(3))
                await self.send(f'Żywiołak {label}: {costs}.')
            await self.summons_v1700('lista')
            return
        action=args[0]
        if action in ('wezwij','summon'):action='przywolaj'
        if action in ('ukryj','odwolaj'):action='schowaj'
        if action in ('przywroc','wlacz'):action='aktywuj'
        if action not in ('przywolaj','schowaj','aktywuj'):
            await self.send('Użyj mag przywolaj, mag schowaj albo mag aktywuj, a następnie żywioł i moc.');return
        kind=resolve_elemental(args[1:])
        if kind is None:
            await self.send('Nieznany żywioł lub stopień. Przykład: mag przywolaj lod potezny.');return
        await self.summons_v1700(f'{action} {kind}')

    async def _v1700_rip_soul(self):
        if not self._v1700_class('Nekromanta'):
            await self.send('Tylko Nekromanta może wyrywać dusze.');return
        mob=self.server.world.mobs.get(self.combat_mob_key) if self.combat_mob_key else None
        if not mob or not mob.alive or mob.room_id!=self.character.room_id:
            await self.send('Musisz walczyć z żywym przeciwnikiem.');return
        if getattr(mob,'soul_extracted_v1700',False):
            await self.send('Z tego przeciwnika już wyrwano duszę.');return
        total=max(1,int(getattr(mob,'max_hp',0) or MOB_TEMPLATES.get(mob.template_id,{}).get('max_hp',1)))
        if mob.hp>total*.20:
            await self.send('Przeciwnik jest jeszcze zbyt silny. Możesz wyrwać duszę dopiero poniżej 20% HP.');return
        template=MOB_TEMPLATES.get(mob.template_id,{})
        level=int(template.get('generator_level') or getattr(mob,'level',1) or 1)
        boss=bool(template.get('boss') or template.get('world_boss'))
        mana_cost=65+min(120,max(0,level)//10)
        if not await self._v1701_need_mana(mana_cost):return
        tier=stone_for_enemy(level,boss)
        qty=2 if boss else 1
        self.server.db.add_item(self.account_id,tier[2],qty)
        mob.soul_extracted_v1700=True
        self.current_mana-=mana_cost
        await self.send(f'Wyrywasz duszę z konającego przeciwnika. Zdobywasz {qty} x {tier[1]}. Mana -{mana_cost} MP, pozostało {self.current_mana} MP.')

    async def necro_v1700(self,raw=''):
        query=ascii_fold(raw)
        if query in ('lista','konstrukty','przywolania','pomoc'):
            await self.send('NEKROMANTA — konstrukty i nieumarli. Wybierz: nekro przywolaj <nazwa>. Mana za przywołanie i utrzymanie w walce; materiały z kopalni, drwalstwa i łupów. Limit 3 aktywnych. Ulepszanie szkieletów: Kamienie Duszy.')
            for key,spec in NECRO_MINIONS.items():
                mat=', '.join(f'{n} x {qty}' for n,qty in spec[3].items())
                await self.send(f'{spec[0]} ({key}): poziom {spec[1]}+, {spec[2]} MP, utrzymanie {spec[8]} MP/atak, {mat}; rola: {spec[7]}.')
            await self.send('Szkielety: pajak (zęby zwykłe), wojownik i mag (smocze zęby). Wojownik/mag rosną dzięki Kamieniom Duszy i statystykom właściciela; pozostałe przywołania ćwiczą się w walce.')
            return
        if query.startswith('wyrwij'):
            await self._v1700_rip_soul()
        elif ascii_fold(raw).startswith('scal '):
            await self._v1701_forge(ascii_fold(raw)[5:])
        else:
            await self.summons_v1700(raw)

    async def druid_call_v1708(self, raw=''):
        """Area-sensitive druid calls; a squirrel brings materials then leaves."""
        if not self._v1700_class('Druid'):
            await self.send('Tylko Druid może użyć call.');return
        from data.rooms import ROOMS
        area=biome_for_room(ROOMS.get(self.character.room_id, {}), self.character.room_id)
        available=terrain_animals(area)
        druid_level=max(1,int(getattr(self.character,'character_level',1) or 1))
        cmd=ascii_fold(raw)
        if cmd.startswith(('odwolaj ', 'dismiss ')):
            who = cmd.split(' ', 1)[1].strip()
            if who in ('all', 'wszystkie', 'wszystko'):
                # `call` specifically dismisses Druids' animals, not allied
                # Necromancer or Mage summons on a multi-class character.
                conn = self._v1700_conn()
                keys = tuple(k for k in ANIMALS if k in SUMMONS)
                if not keys:
                    await self.send('Brak zwierząt do odwołania.');return
                cur = conn.execute('UPDATE summons_v1700 SET active=0 WHERE account_id=? AND active=1 AND summon_type IN (' + ','.join('?' for _ in keys) + ')', (self.account_id,*keys))
                conn.commit()
                await self.send(f'Odwołano {cur.rowcount} aktywnych zwierząt. Postęp pozostaje zapisany.')
                return
            kind = normalize_animal(who)
            if kind not in ANIMALS:
                await self.send('Nieznane zwierzę. Sprawdź call list.');return
            await self.summons_v1700('odwolaj ' + kind)
            return
        if cmd in ('odwolaj','dismiss'):
            await self.send('Użycie: call odwolaj <zwierzę|wszystkie>.');return
        if not cmd or cmd in ('list','lista','zwierzeta'):
            await self.send(f'CALL LIST — teren: {area}. Dostępne zwierzęta:')
            for kind in available:
                if kind=='squirrel':
                    await self.send('wiewiórka (squirrel) — 20 MP, przynosi szyszki i ucieka; nie zajmuje miejsca w drużynie.')
                else:
                    desc=ANIMALS[kind]
                    unlock=desc.get('min_level',0)
                    locked=f' — wymaga poziomu Druida {unlock}' if druid_level<unlock else ''
                    await self.send(f"{desc['name']} ({desc['call']}) — {desc['mana']} MP; {desc['role']}; {desc['rarity']}{locked}.")
            return
        kind=normalize_animal(cmd)
        if kind not in available:
            await self.send('Tego zwierzęcia nie przywołasz na tym terenie. Wpisz call list.');return
        if kind!='squirrel' and druid_level<ANIMALS[kind].get('min_level',0):
            await self.send(f'Ten pomocnik wymaga poziomu Druida {ANIMALS[kind]["min_level"]}. Twoja mana i materiały pozostały bez zmian.');return
        if self.combat_mob_key:
            await self.send('Przywołanie zwierzęcia wymaga zakończenia walki.');return
        if kind=='squirrel':
            cost=20
            conn=self._v1700_conn();now=int(time.time())
            row=conn.execute('SELECT last_gather FROM druid_pinecones_v1702 WHERE account_id=?',(self.account_id,)).fetchone()
            remain=90-(now-int(row['last_gather']) if row else 9999)
            if remain>0:
                await self.send(f'Wiewiórka wróci najwcześniej za {remain} s.');return
            if not await self._v1701_need_mana(cost):return
            amount=2+min(2,max(0,int(self.character.character_level)//200))
            conn.execute('SAVEPOINT v1708_squirrel')
            try:
                self.server.db.add_item(self.account_id,'v1702_pinecone',amount,commit=False)
                conn.execute('INSERT INTO druid_pinecones_v1702(account_id,last_gather) VALUES(?,?) ON CONFLICT(account_id) DO UPDATE SET last_gather=excluded.last_gather',(self.account_id,now))
                conn.execute('RELEASE SAVEPOINT v1708_squirrel');conn.commit()
            except Exception:
                conn.execute('ROLLBACK TO SAVEPOINT v1708_squirrel');conn.execute('RELEASE SAVEPOINT v1708_squirrel');raise
            self.current_mana-=cost
            await self.send(f'Przybiega wiewiórka, rzuca w Ciebie {amount} szyszkami i ucieka. Otrzymujesz {amount} Szyszki Pradawnego Gaju. Mana -{cost} MP. Razem: {self._v1700_qty("v1702_pinecone")}.')
            return
        await self.summons_v1700(f'przywolaj {kind}')

    async def druid_order_v1708(self, raw=''):
        """Orders alter real summoned companions' combat behavior."""
        if not (self._v1700_class('Druid') or self._v1700_class('Nekromanta')):
            await self.send('Rozkazy wymagają klasy Druida lub Nekromanty.');return
        allowed=lambda kind: kind in ANIMALS if self._v1700_class('Druid') else kind in SUMMONS and SUMMONS[kind][1]=='Nekromanta'
        text=ascii_fold(raw).split()
        if text in (['list'],['lista']):
            conn=self._v1700_conn()
            rows=conn.execute('SELECT summon_type,stance FROM summons_v1700 WHERE account_id=? AND active=1 AND hp>0',(self.account_id,)).fetchall()
            active=[r for r in rows if allowed(r['summon_type'])]
            if not active:
                await self.send('Nie masz aktywnych przywołań. Sprawdź call list albo nekro lista.');return
            for r in active:
                await self.send(f"{SUMMONS[r['summon_type']][0]}: {r['stance']}.")
            return
        if len(text)<2:
            await self.send('Rozkazy: order <pomocnik|all> <atakuj|bron|wspieraj|czekaj>. Możesz też wpisać order list.');return
        stance={'atakuj':'atakuj','attack':'atakuj','bron':'bron','defend':'bron',
                'wspieraj':'wspieraj','support':'wspieraj','czekaj':'czekaj','stay':'czekaj'}.get(text[-1])
        if stance is None:
            await self.send('Dostępne rozkazy: atakuj, bron, wspieraj, czekaj.');return
        name=' '.join(text[:-1]);conn=self._v1700_conn()
        if name in ('all','wszystkie'):
            active=[r['summon_type'] for r in conn.execute('SELECT summon_type FROM summons_v1700 WHERE account_id=? AND active=1 AND hp>0',(self.account_id,)) if allowed(r['summon_type'])]
            if not active:
                await self.send('Nie masz aktywnych zwierząt do wydawania rozkazów.');return
            conn.executemany('UPDATE summons_v1700 SET stance=? WHERE account_id=? AND summon_type=?',[(stance,self.account_id,k) for k in active]);conn.commit()
            await self.send(f'Rozkaz {stance} otrzymują {len(active)} zwierzęta.');return
        kind=normalize_animal(name) if self._v1700_class('Druid') else summon_key(name)
        if not allowed(kind):
            await self.send('Nieznane przywołanie. Wpisz call list albo nekro lista.');return
        cur=conn.execute('UPDATE summons_v1700 SET stance=? WHERE account_id=? AND summon_type=? AND active=1 AND hp>0',(stance,self.account_id,kind))
        conn.commit()
        if not cur.rowcount:
            await self.send('Najpierw przywołaj żywego pomocnika przez call lub nekro przywolaj.');return
        await self.send(f"{SUMMONS[kind][0]} otrzymuje rozkaz: {stance}.")

    async def druid_v1700(self,raw=''):
        if not self._v1700_class('Druid'):
            await self.send('Tylko Druid może używać magii natury.');return
        cmd=ascii_fold(raw)
        if cmd in ('szyszki','materialy','materiały'):
            await self.send(f'Szyszki Pradawnego Gaju: {self._v1700_qty("v1702_pinecone")}. Life Oak: poziom 150+, 2 szyszki i 80 MP; Ancient Oak: poziom 400+, 5 szyszek i 180 MP. Zdobywaj: call squirrel. Wymień stare nasiona: druid wymien.')
            return
        if cmd in ('zbierz','zbierz szyszki','szukaj szyszek'):
            await self.send('Szyszki przynosi wiewiórka. Wpisz call squirrel (koszt 20 MP, odnowienie 90 s).')
            return
        if cmd in ('lista','zwierzeta','zwierzęta','call list'):
            await self.druid_call_v1708('list')
            return
        if cmd in ('wymien','wymien nasiona','wymien nasiono'):
            old='v1700_nature_seed'; owned=self._v1700_qty(old)
            if owned<1:
                await self.send('Nie masz Nasion Pradawnego Gaju do wymiany.');return
            conn=self._v1700_conn();db=self.server.db
            conn.execute('SAVEPOINT v1702_exchange')
            try:
                from_box=min(owned,db.storage_qty(self.account_id,'craftbox',old))
                if from_box and not db.remove_storage_item(self.account_id,'craftbox',old,from_box,commit=False):raise RuntimeError('Brak nasion')
                if owned>from_box and not db.remove_item(self.account_id,old,owned-from_box,commit=False):raise RuntimeError('Brak nasion')
                db.add_item(self.account_id,'v1702_pinecone',owned*2,commit=False)
                conn.execute('RELEASE SAVEPOINT v1702_exchange');conn.commit()
            except Exception:
                conn.execute('ROLLBACK TO SAVEPOINT v1702_exchange');conn.execute('RELEASE SAVEPOINT v1702_exchange');raise
            await self.send(f'Wymieniono {owned} nasion na {owned*2} szyszek bez utraty wartości zapasów.');return
        await self.summons_v1700(raw)

    async def summon_combat_turn_v1700(self,mob):
        if not self.character or not mob or not mob.alive or mob.room_id!=self.character.room_id:return
        conn=self._v1700_conn()
        self._v1702_prepare_summon_lives(conn)
        self._v1710_refresh_summon_health(conn)
        rows=conn.execute('SELECT summon_type,level,soul_rank,stance FROM summons_v1700 WHERE account_id=? AND active=1 AND hp>0',(self.account_id,)).fetchall()
        if not rows:return
        # Mixed assault/guard/support orders produce a small tactical synergy.
        # Calculated from the existing active summon rows: no new timers or tables.
        _v1800_team_roles={str(r['stance']) for r in rows if r['summon_type'] in SUMMONS}
        _v1800_team_bonus=1.06 if len(rows)>=2 and len(_v1800_team_roles)>=2 else 1.0
        # No loss of mercenary damage. Summons use their own extra attacks.
        raw_power=max(1,int(max(self.physical_power(),self.spell_power())))
        for row in rows:
            if not mob.alive or mob.hp<=0:break
            spec=SUMMONS.get(row['summon_type'])
            if not spec or not self._v1700_class(spec[1]):continue
            name,_,_,kind,factor=spec
            stance=row['stance'] if 'stance' in row.keys() else 'atakuj'
            if stance=='czekaj':continue
            elemental=ELEMENTALS.get(row['summon_type'])
            if elemental:
                # Alter Aeon-style sustaining energy: no mana means no elemental strike.
                upkeep=elemental['upkeep']
                if self.current_mana<upkeep:
                    continue
                self.current_mana-=upkeep
            necro=NECRO_MINIONS.get(row['summon_type'])
            if necro:
                upkeep=necro[8]
                if self.current_mana<upkeep:
                    continue
                self.current_mana-=upkeep
            grade=max(0,min(8,int(row['soul_rank'] or 0)))
            name=summon_display(row['summon_type'],grade)
            factor*=SOULSTONE_TIERS[grade][3] if row['summon_type'] in ('wojownik','mag') else 1.0
            mastery=max(1,int(row['level']))
            _walls,_workshop,_infirmary=self._v1700_city_bonuses()
            caster_power=max(1,int(self.spell_power())) if elemental else raw_power
            stance_factor=.8 if stance=='bron' else (.7 if stance=='wspieraj' else 1.0)
            formation_bonus,formation_guard=self._v1800_form_bonus()
            amount=max(1,int(caster_power*factor*stance_factor*formation_bonus*_v1800_team_bonus*(1+mastery*.07)*(1+min(.28,.008*_workshop))))
            if formation_guard and self.skill_guard<=0:
                self.skill_guard=max(1,int(self.max_hp()*formation_guard))
            if self._v1800_tactic()=='harmonia' and self.current_hp<self.max_hp():
                from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
                if not superboss_healing_blocked_v11179(self):
                    self.current_hp=min(self.max_hp(),self.current_hp+max(1,int(self.max_hp()*.003)))
            if stance=='bron':
                self.skill_guard=max(int(getattr(self,'skill_guard',0) or 0),max(1,int(self.max_hp()*.02)))
            if stance=='wspieraj':
                self.current_hp=min(self.max_hp(),self.current_hp+max(1,int(self.max_hp()*.015)))
            if elemental and elemental['element'] in ('lod','krysztal'):
                # Ice and crystal specialize in shielding. Use the preexisting guard
                # contract, consumed on the next incoming hit; don't overwrite buffs.
                guard_base=(.025,.05,.085)[elemental['rank']] if elemental['element']=='lod' else (.02,.035,.06)[elemental['rank']]
                barrier=max(1,int(self.max_hp() * min(.12,guard_base+min(.015,mastery*.0004))))
                self.skill_guard=max(int(getattr(self,'skill_guard',0) or 0),barrier)
            amount=await self.apply_boss_defense(mob,amount)
            amount=self.v0210_adjust_player_damage(amount)
            from world.machine_expansion import v0314_adjust_damage_vs_template
            amount,_=v0314_adjust_damage_vs_template(MOB_TEMPLATES.get(mob.template_id,{}),amount,kind,name)
            # Chaos God phases suppress summoned blows only; old bosses unchanged.
            amount=max(1,int(amount*(1.0-.05*int(getattr(mob,'_v1800_chaos_phase',0) or 0))))
            elemental_key=ELEMENT_ALIASES.get(elemental['element']) if elemental else ('dark' if necro and spec[3]=='magic' else None)
            damage=min(max(0,int(mob.hp)),max(1,int(amount)))
            if elemental_key:
                bonus=await self._v1800_elemental_reaction(mob,elemental_key,damage)
                damage=min(max(0,int(mob.hp)),damage+bonus)
            mob.hp-=damage
            if row['summon_type'] in ('lifeoak','ancientoak'):
                from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
                if not superboss_healing_blocked_v11179(self):
                    heal=min(max(0,self.max_hp()-self.current_hp),max(1,int(damage*.06)))
                    self.current_hp+=heal
            self._v1710_earn_summon_xp(conn,row['summon_type'],damage)
            target_name=str(MOB_TEMPLATES.get(mob.template_id, {}).get('name') or mob.template_id)
            msg=(f'{name} (przywołanie {self.character.name}, poziom {mastery}) '
                 f'trafia {target_name} za {damage} obrażeń. '
                 f'{target_name}: {max(0,mob.hp)} HP.')
            if elemental:
                msg+=f' Mana -{elemental["upkeep"]} MP.'
            if necro:
                msg+=f' Mana utrzymania -{necro[8]} MP.'
            await self.send_combat(msg,detail='essential')
            await self.server.party_combat_broadcast(self,msg,detail='essential')
            if mob.hp<=0:
                await self.mob_defeated(mob)
                return

    async def fame_v1702(self, raw=''):
        from systems.fame_v1702 import fame_report,pay_due_fame
        if not self.character:return
        await pay_due_fame(self)
        for line in fame_report(self.server.db.conn,self.account_id,ascii_fold(raw),room_id=self.character.room_id):
            await self.send(line)

    async def city_v1700(self,raw=''):
        if not self.character:return
        conn=self._v1700_conn();parts=ascii_fold(raw).split()
        row=conn.execute('SELECT * FROM cities_v1700 WHERE account_id=?',(self.account_id,)).fetchone()
        if not parts or parts[0] in ('status','info','pomoc'):
            await self.send('MIASTA GRACZY: miasto zaloz <nazwa>; miasto buduj mury / targ / warsztat / lazaret; miasto zbierz. Rozbudowa płatna w srebrze, trwały zapis każdego budynku. Mury osłaniają w walce, warsztat wzmacnia przywołania, lazaret leczy, targ co 2 godziny wypłaca dochód.')
            if row:
                await self.send(f'Miasto {row["title"]}, poziom {row["level"]}. Mury {row["walls"]}, Targ {row["market"]}, Warsztat {row["workshop"]}, Lazaret {row["infirmary"]}.')
            return
        if parts[0]=='zaloz':
            if row:await self.send('Masz już miasto.');return
            title=' '.join(str(raw).strip().split()[1:]).strip()[:42]
            if len(title)<3 or not all(ch.isalnum() or ch in ' -' for ch in title):
                await self.send('Nazwa miasta: 3–42 znaki, tylko litery, cyfry, spacje i myślniki.');return
            price=100000
            if self.character.silver<price:
                await self.send(f'Założenie kosztuje {price} srebra.');return
            self.character.silver-=price
            conn.execute('INSERT INTO cities_v1700(account_id,title) VALUES(?,?)',(self.account_id,title))
            self.server.db.save_character(self.character)
            conn.commit();await self.send(f'Założono miasto {title}. Bez limitu rozbudowy.');return
        if parts[0]=='zbierz':
            if not row or int(row['market'])<1:
                await self.send('Musisz posiadać miasto z co najmniej jednym poziomem Targu.');return
            now=int(time.time())
            remaining=int(row['market_claim'])+7200-now
            if remaining>0:
                await self.send(f'Kolejny dochód z targu za {remaining} sekund.');return
            value=int(row['market'])*25000*(1+int(row['market'])//10)
            if self.character.silver+value>=10**15:
                await self.send('Zbyt duża suma srebra. Najpierw wydaj część waluty.');return
            self.character.silver+=value
            conn.execute('UPDATE cities_v1700 SET market_claim=? WHERE account_id=?',(now,self.account_id))
            self.server.db.save_character(self.character)
            conn.commit();await self.send(f'Dochód z targu: {value} srebra. Następna wypłata za dwie godziny.');return
        if parts[0]=='buduj':
            if not row:await self.send('Najpierw: miasto zaloz <nazwa>.');return
            if len(parts)<2 or parts[1] not in ('mury','targ','warsztat','lazaret'):
                await self.send('Wybierz: miasto buduj mury / targ / warsztat / lazaret.');return
            column={'mury':'walls','targ':'market','warsztat':'workshop','lazaret':'infirmary'}[parts[1]]
            level=int(row[column]);cost=(level+1)**2*45000
            if self.character.silver<cost:
                await self.send(f'Brakuje srebra na budowę. Koszt: {cost}.');return
            self.character.silver-=cost
            conn.execute(f'UPDATE cities_v1700 SET {column}={column}+1,level=level+1 WHERE account_id=?',(self.account_id,))
            self.server.db.save_character(self.character)
            conn.commit();await self.send(f'Rozbudowano {parts[1]} do poziomu {level+1}, koszt {cost} srebra.');return
        await self.send('Komendy: miasto, miasto zaloz <nazwa>, miasto buduj <mury|targ|warsztat|lazaret>.')

    async def classes_v1700(self,raw=''):
        if not self.character:return
        conn=self._v1700_conn();choice=ascii_fold(raw)
        main=self.character.class_name
        existing=conn.execute('SELECT path FROM class_paths_v1700 WHERE account_id=? AND class_name=?',(self.account_id,main)).fetchone()
        if not choice or choice in ('status','pomoc','info'):
            await self.send(f'KLASY 4.0: {main}, przebudzenie: {existing[0] if existing else "nie wybrano"}. Wybierz: przebudzenie ofensywa / obrona / wsparcie. Jedna stała ścieżka na główną klasę, bez zmiany starych umiejętności.')
            return
        if choice not in ('ofensywa','obrona','wsparcie'):
            await self.send('Wybierz ofensywa, obrona albo wsparcie.');return
        if existing:
            await self.send('Ścieżka została już wybrana. Nie nadpisujemy decyzji bez zgody.');return
        conn.execute('INSERT INTO class_paths_v1700(account_id,class_name,path) VALUES(?,?,?)',(self.account_id,main,choice))
        conn.commit();await self.send(f'Przebudzenie Mocy: {main} wybiera {choice}. Bonus działa w walce i nie obniża żadnych dotychczasowych obrażeń.')

    def class_path_v1700(self):
        if not self.character:return ''
        conn=self._v1700_conn()
        row=conn.execute('SELECT path FROM class_paths_v1700 WHERE account_id=? AND class_name=?',(self.account_id,self.character.class_name)).fetchone()
        return str(row['path']) if row else ''

    def class_damage_multiplier_v1700(self):
        return 1.14 if self.class_path_v1700()=='ofensywa' else 1.0

    async def class_support_turn_v1700(self):
        path=self.class_path_v1700()
        walls,workshop,infirmary=self._v1700_city_bonuses()
        if walls and self.skill_guard<=0:
            self.skill_guard=max(1,int(self.max_hp()*min(.20,.01*walls)))
        if infirmary and self.current_hp<self.max_hp():
            from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
            if not superboss_healing_blocked_v11179(self):
                self.current_hp=min(self.max_hp(),self.current_hp+max(1,int(self.max_hp()*min(.12,.005*infirmary))))
        if path=='obrona' and self.skill_guard<=0:
            self.skill_guard=max(1,int(self.max_hp()*.04))
        if path=='wsparcie' and self.current_hp<self.max_hp():
            from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
            if not superboss_healing_blocked_v11179(self):
                self.current_hp=min(self.max_hp(),self.current_hp+max(1,int(self.max_hp()*.02)))
