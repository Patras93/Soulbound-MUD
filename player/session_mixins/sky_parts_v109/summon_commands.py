# -*- coding: utf-8 -*-
"""Soulbound v109: oryginalne metody, wydzielone bez zmiany kodu."""
from __future__ import annotations
from .dependencies import *

class SkySummonCommandsV109Mixin:
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
        if getattr(self, 'current_hp', 1) <= 0 or (getattr(self, 'is_downed_v0371', lambda: False)()):
            await self.send('Nie możesz przywoływać ani aktywować pomocników po śmierci. Najpierw się odrodź.')
            return
        if parts and parts[0] in ('ai','sztuczna','inteligencja'):
            conn=self._v1700_conn()
            if len(parts)>1 and parts[1] in ('on','off','wlacz','wylacz'):
                enabled=0 if parts[1] in ('off','wylacz') else 1
                conn.execute('INSERT INTO summon_ai_prefs_v1200(account_id,enabled) VALUES(?,?) '
                             'ON CONFLICT(account_id) DO UPDATE SET enabled=excluded.enabled',
                             (self.account_id,enabled));conn.commit()
                await self.send('AI przywołań: '+('włączona' if enabled else 'wyłączona')+'. Zapisano dla postaci.')
            else:
                row=conn.execute('SELECT enabled FROM summon_ai_prefs_v1200 WHERE account_id=?',(self.account_id,)).fetchone()
                await self.send('AI przywołań: '+('włączona' if row is None or row['enabled'] else 'wyłączona')+'. Komendy: chowaniec ai on/off/status. Miniony samodzielnie leczą, osłaniają i używają umiejętności klasowych bez zewnętrznego API.')
            return
        if parts and parts[0] in ('umiejetnosci','zdolnosci'):
            from systems.summon_ai_v1200 import CLASS_AI
            for cls in sorted(self.active_class_names()):
                if cls in CLASS_AI:
                    title,role,_=CLASS_AI[cls]
                    await self.send(f'{cls}: {title} — {role}. Aktywne w walce, gdy sytuacja tego wymaga.')
            return
        if parts and parts[0] in ('klasy','klasa','klasowe'):
            classes=set(self.active_class_names())
            filter_name=ascii_fold(' '.join(parts[1:]))
            only_available=filter_name in ('dostepne','odblokowane','available')
            if filter_name and not only_available:
                matching={name for name in classes if ascii_fold(name)==filter_name}
                if not matching:
                    await self.send('Nie masz aktywnej klasy o tej nazwie. Wpisz chowaniec klasy, aby poznać dostępne klasy.')
                    return
                classes=matching
            current_level=max(1,int(getattr(self.character,'character_level',1) or 1))
            await self.send('PRZYWOŁANIA KLASOWE: chowaniec klasy <nazwa klasy> (krótka lista) / chowaniec klasy dostepne (odblokowane na twoim poziomie). Progi 1, 90, 200, 400 i 600. chowaniec przywolaj <kod>. Limit 3 aktywne łącznie; po zalogowaniu przywołujesz od nowa. Miniony skalują się do twojej postaci.')
            for cname in sorted(classes):
                for row in CLASS_MINIONS_BY_CLASS_V1119.get(cname, ()):
                    if only_available and current_level<row[3]:
                        continue
                    status=('DOSTĘPNY' if current_level>=row[3] else 'ZABLOKOWANY')
                    await self.send(f'{cname}: {row[1]} — {status}; chowaniec przywolaj {row[0]}; poziom {row[3]}+, koszt {row[4]} MP.')
                if cname in ('Druid','Mag','Nekromanta'):
                    await self.send(f'{cname}: istniejące przywołania: ' + ('call list' if cname=='Druid' else 'mag lista' if cname=='Mag' else 'nekro lista') + '.')
            return
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
            await self.send('CHOWAŃCE: chowaniec klasy (miniony twoich klas); chowaniec lecz <nazwa|wszystko> (mana i tylko żywe przywołania); chowaniec przywolaj <typ>, chowaniec ulepsz <wojownik|mag> <kolor>, chowaniec kamienie, chowaniec schowaj/aktywuj <typ>; chowaniec odwolaj <nazwa|wszystkie>. Do 3 aktywnych. Poziom wszystkich = poziom właściciela, bez osobnego EXP. Żywe regenerują HP poza walką. Powrót wymaga many i materiałów właściwych dla rodzaju (Mag bez materiałów).')
            await self.send('Nekromanta: pająk — 2 zwykłe zęby; wojownik — 1 smoczy ząb; mag — 2 smocze zęby. Dziewięć kolorów Kamieni Duszy ulepsza wojowników i magów. nekro wyrwij; nekro scal <kolor>.')
            await self.send('Druid: call list (zwierzęta na aktualnym terenie), call <zwierzę>, call squirrel (wiewiórka dostarcza szyszki za 20 MP), order <zwierzę> <atakuj|bron|wspieraj|czekaj>. Bez Pieczęci Chowańców. Life Oak: poziom 150+, 2 szyszki i 80 MP; Ancient Oak: poziom 400+, 5 szyszek i 180 MP.')
            await self.send('Mag: mag lista, mag przywolaj ogien mniejszy / blyskawice / lod potezny / krysztal. 4 żywioły, po 3 stopnie; moc z Twojej magii i aktualnego poziomu, bez osobnego EXP; mana za przywołanie i ataki. Bez zębów i Kamieni Duszy.')
            await self.send('Nekromanta: nekro lista — konstrukty, nieumarli, materiały, mana, wymagane poziomy. nekro przywolaj metal / gliniany / kostny_straznik itd. Rozkazy: order <nazwa|all> <atakuj|bron|wspieraj|czekaj>.')
            from systems.live_olc29_creation import ACTIVE as _OLC29_ACTIVE
            for _kind in sorted(_OLC29_ACTIVE['summons']):
                _spec=SUMMONS[_kind]
                await self.send(f"Nowe przywołanie: {_spec[0]}; komenda chowaniec przywolaj {_kind}; klasa {_spec[1]}; mana {SUMMON_MANA[_kind]} MP.")
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
                await self.send(f'Odwołano {cur.rowcount} aktywnych przywołań. Ich HP i ulepszenia pozostały zapisane.')
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
        if kind in CLASS_MINIONS_V1119 and action in ('przywolaj','aktywuj'):
            required_level=CLASS_MINIONS_V1119[kind][3]
            if int(getattr(self.character,'character_level',1) or 1)<required_level:
                await self.send(f'{name} wymaga poziomu postaci {required_level}. Nie zużyto many ani materiałów.')
                return
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
        self._v1710_refresh_summon_health(conn)
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
            mana_cost=55+index*15+max(1,int(row['soul_rank'])+1)*3
            if not await self._v1701_need_mana(mana_cost):return
            stone_cost=summon_upgrade_stones(int(row['soul_rank'])+1)
            new_max=self._v1702_summon_max_hp(kind,self._v1806_owner_summon_level(kind,row['level']))
            previous_max=max(0,int(row['max_hp']))
            previous_hp=max(0,int(row['hp']))
            new_hp=(0 if previous_hp==0 else min(new_max,max(1,previous_hp+max(0,new_max-previous_max))))
            if not self._v1700_spend_and_write({tier[2]:stone_cost},
                'UPDATE summons_v1700 SET soul_rank=MAX(soul_rank,?), hp=?, max_hp=? WHERE account_id=? AND summon_type=?',
                (index,new_hp,new_max,self.account_id,kind)):
                await self.send(f'Potrzebujesz {stone_cost} x {tier[1]}; masz {self._v1700_qty(tier[2])}.');return
            self.current_mana-=mana_cost
            new_grade=max(index,int(row['soul_rank']))
            await self.send(f'{summon_display(kind,new_grade)}: poziom {self._v1806_owner_summon_level(kind,row["level"])}, rezonans {SOULSTONE_TIERS[new_grade][1]}. Zużyto {stone_cost} kamieni i {mana_cost} MP; zostało {self.current_mana} MP.');return
        if action in ('schowaj','aktywuj'):
            if not row:
                await self.send('Najpierw zdobądź przywołanie.');return
            mana_cost=0
            if action=='aktywuj' and not row['active']:
                active=conn.execute('SELECT COUNT(*) FROM summons_v1700 WHERE account_id=? AND active=1',(self.account_id,)).fetchone()[0]
                if active>=3:
                    await self.send('Maksymalnie 3 aktywne przywołania. Schowaj inne.');return
                from systems.live_olc24_revolution import summon_factor
                mana_cost=(SUMMON_MANA[kind]*summon_factor(kind,'mana_percent')+99)//100
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
        from systems.live_olc24_revolution import summon_factor
        mana_cost=(SUMMON_MANA[kind]*summon_factor(kind,'mana_percent')+99)//100
        if not await self._v1701_need_mana(mana_cost):return
        if not self._v1700_spend_and_write(costs,
            'INSERT INTO summons_v1700(account_id,summon_type,level,active,hp,max_hp,xp) VALUES(?,?,?,1,?,?,0)',
            (self.account_id,kind,self._v1806_owner_summon_level(kind),self._v1702_summon_max_hp(kind,self._v1806_owner_summon_level(kind)),self._v1702_summon_max_hp(kind,self._v1806_owner_summon_level(kind)))):
            missing=', '.join(f'{k}: {v} (masz {self._v1700_qty(k)})' for k,v in costs.items())
            await self.send('Brak materiałów: '+missing);return
        self.current_mana-=mana_cost
        await self.send(f'{name} dołącza do Ciebie. Mana -{mana_cost} MP, pozostało {self.current_mana} MP. Walczy automatycznie. Po kolejnym zalogowaniu musisz go przywołać ponownie.')


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





