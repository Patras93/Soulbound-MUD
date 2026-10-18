# -*- coding: utf-8 -*-
"""Three genuinely endless Soulbound 11 expedition dungeons.

All floors are generated lazily, use existing combat/spawn pipelines, and never
award EP just for entering numbered floors. Checkpoints are personal, durable
SQLite codex entries. Existing portal handlers are wrapped, not replaced.
"""
import re
from systems.eternal_glory_world_v1100 import REGIONS

ENDLESS = {
    'krypta': ('Krypta Wiecznych Przysiąg','bogowie','dark',180),
    'wieza': ('Wieża Spadających Gwiazd','meteory','lightning',420),
    'chaos': ('Wymiar Niekończącego Chaosu','mrok','arcane',650),
}
FLOOR_RE = re.compile(r'^v1100_inf_(krypta|wieza|chaos)_floor_([1-9][0-9]*)$')


def floor_id(key, number):
    if key not in ENDLESS or int(number)<1:
        raise ValueError('Unknown Soulbound 11 dungeon or floor')
    return f'v1100_inf_{key}_floor_{int(number)}'


def identity(room):
    match = FLOOR_RE.fullmatch(str(room or ''))
    return (match.group(1),int(match.group(2))) if match else None


def gate_id(key):
    return f'v1100_inf_{key}_gate'


def create_floor(key, floor, rooms, mobs, spawns, register_seed_spawns=True):
    title,anchor,element,start_level=ENDLESS[key]
    n=max(1,int(floor));rid=floor_id(key,n)
    level=min(800,start_level+5*n)
    factor=1.0+n*0.06+n//10*0.2
    boss=n%10==0
    if rid not in rooms:
        rooms[rid]={
            'name':f'{title} — piętro {n}',
            'zone':title,
            'desc':(f'Piętro {n} nieskończonej wyprawy. ' +
                    ('Miejsce potężnego strażnika i osobistego checkpointu.' if boss else
                     'Na zwykłym piętrze nie ma EP. Bez pułapek.')),
            'exits':{'up':gate_id(key) if n==1 else floor_id(key,n-1),'down':floor_id(key,n+1)},
            'generator_level':level,'recommended_mastery':level,
            'procedural_infinite':True,'v1100_infinite':key,
            'v1100_infinite_floor':n,'v1100_no_traps':True,
            'exploration_ep':0,'v1000_landmark':False,
        }
    created=[]
    for variant in (1,2):
        mid=f'{rid}_enemy_{variant}'
        if mid not in mobs:
            hp=int((350000+level*6000+n*22000)*factor*(1.0+variant*.18))
            dmg=int((1900+level*25+n*125)*(factor**.72)*(1.0+variant*.08))
            xp=int((380000+level*13000+n*70000)*factor)
            mobs[mid]={
                'name':f'{title} — obrońca {n}, odmiana {variant}',
                'max_hp':hp,'damage':dmg,'damage_type':'magic',
                'attack_elements_v11339':(element,),
                'generator_level':level,'silver':int((level*1700+n*11000)*factor),
                'class_xp_reward':xp,'soul_reward':int(xp*.4),
                'stat_reward':int(xp*.2),
                'drops':{'soul_shard':min(.85,.20+n/2000)},
                'v1100_infinite':key,'v1100_floor':n,
                'auto_aggro':False,
            }
        created.append((rid,mid))
    if boss:
        mid=f'{rid}_boss'
        if mid not in mobs:
            xp=int((380000+level*13000+n*70000)*factor)
            mobs[mid]={
                'name':f'Wieczny Strażnik {title}, piętro {n}',
                'max_hp':int((350000+level*6000+n*22000)*factor*16),
                'damage':int((1900+level*25+n*125)*(factor**.75)*2.8),
                'damage_type':'magic','attack_elements_v11339':(element,),
                'generator_level':level,'world_boss':True,'fame_target':True,
                'silver':int((level*10000+n*62000)*factor),
                'class_xp_reward':xp*16,'soul_reward':xp*6,
                'stat_reward':xp*2,'drops':{'soul_shard':1.0,'soul_elixir':.6},
                'boss_mechanic':f'v1100_{key}_eternal',
                'boss_mechanic_text':f'Władca piętra {n}: rosnąca moc {element}.',
                'v1100_infinite':key,'v1100_floor':n,
                'auto_aggro':False,
            }
        created.append((rid,mid))
    # Lazy floors are registered through World._register_runtime_spawn,
    # which applies the world's level-dependent template scaling and adds
    # the resulting template to MOB_SPAWNS. Also appending the unscaled base
    # here would duplicate encounters on the same floor.
    if register_seed_spawns:
        for pair in created:
            if pair not in spawns: spawns.append(pair)
    return rid,tuple(created)


def install(rooms,mobs,spawns,help_topics,aliases,World,Session):
    for key,(title,anchor,element,start) in ENDLESS.items():
        gate=gate_id(key);parent=f'v1100_vault_{anchor}_09'
        if gate in rooms or parent not in rooms or 'down' in rooms[parent]['exits']:
            raise RuntimeError('v11 infinite gateway collision: '+key)
        rooms[gate]={
            'name':'Brama — '+title,'zone':title,
            'desc':'Brama nieskończonego lochu. Schody prowadzą dalej; checkpoint co dziesięć pięter. Bez pułapek.',
            'exits':{'up':parent,'down':floor_id(key,1)},
            'recommended_mastery':start,'generator_level':start,
            'v1100_infinite_gate':key,'exploration_ep':0,
            'v1100_no_traps':True,
        }
        rooms[parent]['exits']['down']=gate
        create_floor(key,1,rooms,mobs,spawns)
    old_ensure=World.ensure_infinite_dungeon_floor
    def ensure(self,room_id):
        recognized=identity(room_id)
        if recognized:
            key,n=recognized
            rid,entities=create_floor(key,n,rooms,mobs,spawns,register_seed_spawns=False)
            self._generatorize_runtime_room(rid)
            for home,template in entities:
                self._register_runtime_spawn(home,template)
            return True
        return old_ensure(self,room_id)
    # The strict world auditor needs to know that *both* the historical
    # Echo Labyrinth and the new infinite-family resolvers remain installed.
    # Without these markers legitimate lazily generated exits look broken.
    ensure._v1500_echo = bool(getattr(old_ensure, '_v1500_echo', False))
    ensure._v1100_infinite = True
    World.ensure_infinite_dungeon_floor=ensure

    # Visiting a checkpoint unlocks only that personal position; this survives
    # logout/restart and does not reset earlier discovered floors.
    old_discover=Session.discover_room
    async def discover(self,room_id,announce=True):
        result=await old_discover(self,room_id,announce=announce)
        found=identity(room_id)
        if found and found[1]%10==0:
            key,n=found
            fresh=self.server.db.add_collection_entry(
                self.account_id,f'v1100_checkpoint_{key}',str(n))
            if fresh and announce:
                await self.send(f'Checkpoint {n} odblokowany: {ENDLESS[key][0]}.')
        return result
    Session.discover_room=discover

    async def portal(self,raw,key):
        title,anchor,_,_=ENDLESS[key]
        origin=str(self.character.room_id)
        current=identity(origin)
        current_n=current[1] if current and current[0]==key else None
        allowed=self.server.db.collection_entry_ids(self.account_id,f'v1100_checkpoint_{key}')
        value=self.normalize_room_query(raw)
        if not value or value in ('status','lista','list'):
            floors=sorted(map(int,(f for f in allowed if f.isdigit())))
            await self.send(f'{title}. Checkpointy: '+(', '.join(map(str,floors)) if floors else 'brak')+'.')
            return
        if self.portal_requires_local_leader_v12811():
            await self.send('Portal uruchamia lider drużyny obecny w tym pokoju.')
            return
        if self.combat_mob_key:
            await self.send('Nie możesz użyć portalu podczas walki.')
            return
        if value in ('wyjdz','wyjdź','exit','out','wyjscie','wyjście'):
            if current_n is None or current_n%10:
                await self.send('Wyjście przez portal jest dostępne na checkpointcie co dziesięć pięter.')
                return
            goal=gate_id(key);label='bramy'
        else:
            m=re.fullmatch(r'[0-9]+',value)
            if not m:
                await self.send('Użycie: portal 10/20/30/... albo portal wyjdz; lista przez portal.')
                return
            target=int(value)
            if target%10 or target<10 or str(target) not in allowed:
                await self.send(f'Checkpoint {target} nie jest odblokowany. Każde dziesiąte piętro.')
                return
            if origin!=gate_id(key) and (current_n is None or current_n%10):
                await self.send('Przejście działa z bramy lub odblokowanego checkpointu.')
                return
            goal=floor_id(key,target);label=f'piętra {target}'
            self.server.world.ensure_infinite_dungeon_floor(goal)
        party=self.party_key()
        members=(list(self.server.party_sessions(self.account_id,same_room=origin))
                 if party==self.account_id else [self])
        if self not in members:members.append(self)
        moved=[];skipped=[]
        for member in members:
            if not getattr(member,'character',None):continue
            if member.combat_mob_key:
                skipped.append(member.character.name+': walczy');continue
            if goal!=gate_id(key) and str(target) not in member.server.db.collection_entry_ids(
                    member.account_id,f'v1100_checkpoint_{key}'):
                skipped.append(member.character.name+': brak checkpointu');continue
            member.previous_room_id=member.character.room_id
            member.character.room_id=goal
            member.server.db.save_character(member.character)
            moved.append(member)
        for member in moved:
            await member.send(f'{title}: lider przenosi do {label}.')
            await member.look()
        if skipped: await self.send('Nie przeniesiono: '+'; '.join(skipped)+'.')

    old_crypt=Session.use_crypt_portal
    old_astral=Session.use_astral_portal
    async def crypt(self,raw):
        origin=str(self.character.room_id)
        key=rooms.get(origin,{}).get('v1100_infinite_gate')
        pair=identity(origin)
        if pair:key=pair[0]
        if key in ('krypta','chaos'):
            return await portal(self,raw,key)
        return await old_crypt(self,raw)
    async def astral(self,raw):
        origin=str(self.character.room_id)
        key=rooms.get(origin,{}).get('v1100_infinite_gate')
        pair=identity(origin)
        if pair:key=pair[0]
        if key=='wieza':
            return await portal(self,raw,key)
        return await old_astral(self,raw)
    Session.use_crypt_portal=crypt
    Session.use_astral_portal=astral
    old_exit=Session.dungeon_exit_destination
    def exit_destination(self,room_id=None):
        rid=str(room_id or (self.character.room_id if self.character else ''))
        pair=identity(rid)
        if pair:return gate_id(pair[0])
        return old_exit(self,room_id)
    Session.dungeon_exit_destination=exit_destination

    help_topics['nieskonczone11']=[
        'Nowe nieskończone lochy: Krypta Wiecznych Przysiąg, Wieża Spadających Gwiazd i Wymiar Chaosu.',
        'Wejścia odnajdziesz na końcu podziemi Bogów, Meteorów i Mroku.',
        'Piętra generowane są bez końcowego limitu. Boss co 10 pięter. Zero pułapek i automatycznych EP za zwykłe piętra.',
        'Checkpoint zapisuje się osobno dla postaci co 10 pięter. Z bramy i checkpointu: portal 10/20/30 lub astralportal w wieży.',
        'Lider może przenieść tylko członków drużyny, którzy mają własny checkpoint odblokowany.',
    ]
    aliases['nieskonczone11']='nieskonczone11'
    return {'infinite_dungeons':len(ENDLESS),'seed_floors':len(ENDLESS)}
