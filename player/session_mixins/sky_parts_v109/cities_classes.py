# -*- coding: utf-8 -*-
"""Soulbound v109: oryginalne metody, wydzielone bez zmiany kodu."""
from __future__ import annotations
from .dependencies import *

class SkyCitiesClassesV109Mixin:
    def _v1700_city_bonuses(self):
        if not self.character:return (0,0,0)
        conn=self._v1700_conn()
        row=conn.execute('SELECT walls,workshop,infirmary FROM cities_v1700 WHERE account_id=?',(self.account_id,)).fetchone()
        if not row:return (0,0,0)
        return (int(row['walls']),int(row['workshop']),int(row['infirmary']))

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

