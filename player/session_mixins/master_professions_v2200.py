# -*- coding: utf-8 -*-
"""NVDA-friendly, persistent profession mastery and real-action contracts."""
from systems import profession_mastery_v2200 as mastery
from systems import mastery_crafting_v2201 as recipes


class SessionMasterProfessionsV2200Mixin:
    async def master_professions_v2200(self, args=''):
        tokens=str(args or '').strip().split()
        if not tokens or tokens[0].casefold() in ('pomoc','help','lista'):
            await self.send('MISTRZOWIE PROFESJI 6.0: mistrzprof lista, mistrzprof status <profesja>, mistrzprof wybierz <profesja> <numer>, mistrzprof zamowienie <profesja>, mistrzprof odbierz <profesja>, mistrzprof porzuc <profesja>; mistrzprof receptury <profesja>; mistrzprof wykonaj <profesja> [1..3].')
            for name,specialties in mastery.SPECIALTIES.items():
                await self.send(f'{name}: '+', '.join(f'{i+1}. {s}' for i,s in enumerate(specialties)))
            return
        action=tokens[0].casefold()
        if len(tokens)<2:
            await self.send('Podaj nazwę profesji. Lista: mistrzprof lista.');return
        tier = int(tokens[-1]) if action in ('wykonaj','receptury') and tokens[-1].isdigit() else 1
        raw=' '.join(tokens[1:-1] if action=='wybierz' or (action in ('wykonaj','receptury') and tokens[-1].isdigit()) else tokens[1:])
        try:prof=mastery.canonical(raw)
        except ValueError as exc:await self.send(str(exc));return
        conn=self._econ_v1321()
        mastery.init(conn)
        prow=self.server.db.profession(self.account_id,prof)
        level=int(prow['level']);actions=int(prow['actions'])
        if action=='receptury':
            if tier not in (1,2,3):
                await self.send('Podaj poziom receptury 1, 2 lub 3.');return
            if tier==1:spec,item,materials,price,name=recipes.RECIPES[prof]
            else:
                from systems.mastery_advancement_v2300 import recipe
                spec,item,materials,price,name=recipe(prof,tier)
            await self.send(f'{prof}: {name}. Poziom receptury {tier}; wymagany poziom profesji {(100,250,450)[tier-1]} i specjalizacja {spec}.')
            await self.send('Składniki: '+', '.join(f'{k} x{v}' for k,v in materials.items())+f'. Produkt: {item}. Wartość sprzedaży {price} srebra.')
            await self.send(f'Wytwarzanie: mistrzprof wykonaj {prof} {tier}.')
            return
        if action=='wykonaj':
            try:
                item,name,xp,txp=recipes.craft(conn,self.account_id,prof,level,tier=tier)
                tool_type=recipes.TOOL_TYPES[prof]
                messages,_,_=self.grant_profession_progress(prof,xp,tool_type,txp,content_level=max(100,level))
                await self.send(f'Wytworzono: {name} x1. Materiały odjęte, przedmiot zapisany w SQLite.')
                for message in messages:await self.send(message)
                await self.announce_craft_quest_progress(item,1)
            except ValueError as exc:await self.send(str(exc))
            return
        if action=='status':
            unlocked=[r[0] for r in conn.execute('SELECT specialty FROM profession_specialties_v2200 WHERE account_id=? AND profession=?',(self.account_id,prof))]
            await self.send(f'{prof}: poziom {level}; specjalizacje: {", ".join(unlocked) or "brak"}. Zamówienie: {mastery.status(conn,self.account_id,prof,actions)}.')
            return
        try:
            if action=='wybierz':
                if not tokens[-1].isdigit() or not 1<=int(tokens[-1])<=3:
                    raise ValueError('Podaj numer specjalizacji 1, 2 lub 3.')
                spec=mastery.SPECIALTIES[prof][int(tokens[-1])-1]
                required=mastery.unlock(conn,self.account_id,prof,spec,level)
                await self.send(f'Odblokowano {spec}, poziom wymagany {required}. Rozwój pozostałych gałęzi pozostaje możliwy.')
            elif action=='zamowienie':
                count=mastery.start_order(conn,self.account_id,prof,level,actions)
                await self.send(f'Zamówienie {prof}: wykonaj {count} nowych, rzeczywistych czynności profesji. Odbiór: mistrzprof odbierz {prof}.')
            elif action=='odbierz':
                silver,balance=mastery.claim(conn,self.account_id,prof,level,actions)
                self.character.silver=balance;self.character.gold=0;self.character.mithril=0
                await self.send(f'Zamówienie {prof} odebrane: +{silver} srebra (złoto 100 srebra = 1 złoto). Odnowienie po godzinie.')
            elif action=='porzuc':
                mastery.abandon(conn,self.account_id,prof)
                await self.send(f'Zamówienie {prof} porzucone. Zdobyte poziomy i EXP bez zmian.')
            else:await self.send('Nieznana akcja. mistrzprof pomoc.')
        except ValueError as exc:await self.send(str(exc))
