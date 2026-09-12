#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Soulbound v0.5 Railway Ready
Lekki wieloosobowy MUD TCP/Telnet, zgodny z MUSHclientem/Mudletem.

Założenia:
- brak poziomu postaci i XP postaci,
- statystyki rosną automatycznie,
- Broń Duszy ma osobny Soul Level 1-100,
- Tier Broni Duszy 1-3 jest odblokowywany osobno,
- dane kont i postaci są przechowywane w SQLite,
- brak zewnętrznych bibliotek.
"""

import asyncio
import hashlib
import hmac
import os
import random
import re
import secrets
import sqlite3
import sys
from dataclasses import dataclass
from typing import Optional

HOST = os.getenv("SOULBOUND_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", os.getenv("SOULBOUND_PORT", "4000")))

# Railway Volume: po zamontowaniu trwałego dysku baza automatycznie
# trafia do katalogu wskazanego przez RAILWAY_VOLUME_MOUNT_PATH.
_VOLUME_PATH = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "").strip()
_DEFAULT_DB = os.path.join(_VOLUME_PATH, "soulbound.db") if _VOLUME_PATH else "soulbound.db"
DB_PATH = os.getenv("SOULBOUND_DB", _DEFAULT_DB)

MAX_CLIENTS = int(os.getenv("SOULBOUND_MAX_CLIENTS", "100"))
PBKDF2_ROUNDS = 210_000

STAT_GROWTH_THRESHOLD = 100
SOUL_MAX_LEVEL = 100
TIER2_LEVEL = 25
TIER3_LEVEL = 60

RACES = [
    ("Człowiek", "Wszechstronny.", 10, 10, 10, 10, 10),
    ("Ogr", "Potężny i wytrzymały.", 14, 8, 14, 6, 8),
    ("Elf", "Bardzo zręczny i uzdolniony magicznie.", 8, 14, 9, 13, 11),
    ("Krasnolud", "Silny, odporny i uparty.", 12, 9, 14, 9, 12),
    ("Ork", "Urodzony wojownik.", 13, 10, 13, 7, 9),
    ("Niziołek", "Niewielki i bardzo zręczny.", 7, 14, 10, 10, 11),
    ("Mroczny Elf", "Zręczny i związany z mroczną magią.", 9, 13, 9, 14, 10),
    ("Gnom", "Błyskotliwy i odporny psychicznie.", 7, 12, 9, 14, 13),
    ("Smoczy", "Smocza krew, siła i odporność.", 13, 9, 13, 10, 10),
    ("Troll", "Ekstremalnie silny i wytrzymały.", 15, 7, 15, 5, 8),
    ("Diablę", "Demoniczne pochodzenie i talent magiczny.", 9, 11, 9, 13, 13),
    ("Aasimar", "Silna wola i moc światła.", 10, 10, 11, 12, 14),
]

CLASSES = [
    ("Wojownik", "physical", "Miecz Przysięgi", 7),
    ("Berserker", "physical", "Topór Krwi", 9),
    ("Łotrzyk", "physical", "Sztylety Cienia", 6),
    ("Łowca", "physical", "Łuk Echa", 7),
    ("Mnich", "physical", "Rękawice Ducha", 6),
    ("Strażnik", "physical", "Młot Bastionu", 7),
    ("Mag", "magic", "Kostur Arkanów", 7),
    ("Nekromanta", "magic", "Kosa Dusz", 8),
    ("Kapłan", "magic", "Młot Światła", 6),
    ("Czarownik", "magic", "Ostrze Otchłani", 8),
    ("Druid", "magic", "Kostur Korzeni", 6),
    ("Psionik", "magic", "Kryształ Umysłu", 7),
]

ROOMS = {
    "square": {
        "name": "Plac Dusz",
        "desc": "Kamienny plac w centrum osady. Nad fontanną płonie błękitny płomień.",
        "exits": {"north": "training", "east": "forge", "west": "grove"},
    },
    "training": {
        "name": "Dziedziniec Treningowy",
        "desc": "Słychać uderzenia stali i oddechy ćwiczących. Tutaj można użyć komendy fight.",
        "exits": {"south": "square", "north": "gate"},
    },
    "forge": {
        "name": "Kuźnia Dusz",
        "desc": "W powietrzu drga energia związanych z bohaterami Broni Duszy.",
        "exits": {"west": "square"},
    },
    "grove": {
        "name": "Gaj Szeptów",
        "desc": "Cichy gaj na skraju osady. Liście szeleszczą mimo bezwietrznej pogody.",
        "exits": {"east": "square"},
    },
    "gate": {
        "name": "Północna Brama",
        "desc": "Za bramą zaczyna się dzicz. W tej wersji dalsza droga jest jeszcze zamknięta.",
        "exits": {"south": "training"},
    },
}

DIRECTION_ALIASES = {
    "n": "north", "north": "north", "północ": "north", "polnoc": "north",
    "s": "south", "south": "south", "południe": "south", "poludnie": "south",
    "e": "east", "east": "east", "wschód": "east", "wschod": "east",
    "w": "west", "west": "west", "zachód": "west", "zachod": "west",
}

COMMAND_ALIASES = {
    "pomoc": "help",
    "spójrz": "look", "spojrz": "look", "l": "look",
    "kto": "who",
    "staty": "stats", "status": "stats",
    "dusza": "soul",
    "mów": "say", "mow": "say",
    "powiedz": "say",
    "walcz": "fight",
    "odblokuj": "unlock",
    "wyjście": "quit", "wyjscie": "quit",
}

IAC = 255
DONT = 254
DO = 253
WONT = 252
WILL = 251
SB = 250
SE = 240


def clean_telnet(data: bytes) -> str:
    """Minimalnie usuwa negocjacje Telnet/IAC; wystarcza dla typowych klientów MUD."""
    out = bytearray()
    i = 0
    while i < len(data):
        b = data[i]
        if b != IAC:
            out.append(b)
            i += 1
            continue
        i += 1
        if i >= len(data):
            break
        cmd = data[i]
        i += 1
        if cmd in (DO, DONT, WILL, WONT):
            if i < len(data):
                i += 1
        elif cmd == SB:
            while i < len(data):
                if data[i] == IAC and i + 1 < len(data) and data[i + 1] == SE:
                    i += 2
                    break
                i += 1
        elif cmd == IAC:
            out.append(IAC)
    return out.decode("utf-8", errors="ignore")


def safe_name(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9_-]{3,20}", name))


def normalize_name(name: str) -> str:
    return name.strip()


def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return salt.hex(), digest.hex()


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    _, candidate = hash_password(password, salt)
    return hmac.compare_digest(candidate, hash_hex)


class Database:
    def __init__(self, path: str):
        self.path = path
        parent = os.path.dirname(os.path.abspath(path))
        os.makedirs(parent, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.create_schema()

    def create_schema(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS characters (
                account_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                race TEXT NOT NULL,
                class_name TEXT NOT NULL,
                class_type TEXT NOT NULL,
                soul_weapon TEXT NOT NULL,
                weapon_base INTEGER NOT NULL,
                strength INTEGER NOT NULL,
                dexterity INTEGER NOT NULL,
                constitution INTEGER NOT NULL,
                intelligence INTEGER NOT NULL,
                willpower INTEGER NOT NULL,
                stat_progress INTEGER NOT NULL DEFAULT 0,
                soul_level INTEGER NOT NULL DEFAULT 1,
                soul_xp INTEGER NOT NULL DEFAULT 0,
                soul_tier INTEGER NOT NULL DEFAULT 1,
                room_id TEXT NOT NULL DEFAULT 'square',
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );
            """
        )
        self.conn.commit()

    def account_by_name(self, username: str):
        return self.conn.execute(
            "SELECT * FROM accounts WHERE username = ? COLLATE NOCASE", (username,)
        ).fetchone()

    def create_account(self, username: str, password: str) -> int:
        salt, digest = hash_password(password)
        cur = self.conn.execute(
            "INSERT INTO accounts(username,password_salt,password_hash) VALUES(?,?,?)",
            (username, salt, digest),
        )
        self.conn.commit()
        return cur.lastrowid

    def character_for_account(self, account_id: int):
        return self.conn.execute(
            "SELECT * FROM characters WHERE account_id=?", (account_id,)
        ).fetchone()

    def character_name_exists(self, name: str) -> bool:
        return self.conn.execute(
            "SELECT 1 FROM characters WHERE name=? COLLATE NOCASE", (name,)
        ).fetchone() is not None

    def create_character(self, account_id: int, name: str, race, cls):
        rname, _, strength, dexterity, constitution, intelligence, willpower = race
        cname, ctype, soul_weapon, weapon_base = cls
        self.conn.execute(
            """
            INSERT INTO characters(
                account_id,name,race,class_name,class_type,soul_weapon,weapon_base,
                strength,dexterity,constitution,intelligence,willpower,
                stat_progress,soul_level,soul_xp,soul_tier,room_id
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,0,1,0,1,'square')
            """,
            (
                account_id, name, rname, cname, ctype, soul_weapon, weapon_base,
                strength, dexterity, constitution, intelligence, willpower,
            ),
        )
        self.conn.commit()

    def save_character(self, c):
        self.conn.execute(
            """
            UPDATE characters SET
                strength=?, dexterity=?, constitution=?, intelligence=?, willpower=?,
                stat_progress=?, soul_level=?, soul_xp=?, soul_tier=?, room_id=?
            WHERE account_id=?
            """,
            (
                c.strength, c.dexterity, c.constitution, c.intelligence, c.willpower,
                c.stat_progress, c.soul_level, c.soul_xp, c.soul_tier, c.room_id,
                c.account_id,
            ),
        )
        self.conn.commit()


@dataclass
class Character:
    account_id: int
    name: str
    race: str
    class_name: str
    class_type: str
    soul_weapon: str
    weapon_base: int
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    willpower: int
    stat_progress: int
    soul_level: int
    soul_xp: int
    soul_tier: int
    room_id: str

    @classmethod
    def from_row(cls, row):
        return cls(
            account_id=row["account_id"],
            name=row["name"],
            race=row["race"],
            class_name=row["class_name"],
            class_type=row["class_type"],
            soul_weapon=row["soul_weapon"],
            weapon_base=row["weapon_base"],
            strength=row["strength"],
            dexterity=row["dexterity"],
            constitution=row["constitution"],
            intelligence=row["intelligence"],
            willpower=row["willpower"],
            stat_progress=row["stat_progress"],
            soul_level=row["soul_level"],
            soul_xp=row["soul_xp"],
            soul_tier=row["soul_tier"],
            room_id=row["room_id"],
        )

    def max_hp(self):
        return 40 + self.constitution * 5

    def max_mana(self):
        if self.class_type != "magic":
            return 0
        return 20 + self.intelligence * 4 + self.willpower * 3

    def soul_xp_to_next(self):
        if self.soul_level >= SOUL_MAX_LEVEL:
            return 0
        return 60 + (self.soul_level - 1) * 20

    def soul_power(self):
        bonus = {1: 0, 2: 12, 3: 30}[self.soul_tier]
        return self.weapon_base + (self.soul_level - 1) + bonus

    def can_unlock(self):
        if self.soul_tier == 1 and self.soul_level >= TIER2_LEVEL:
            return 2
        if self.soul_tier == 2 and self.soul_level >= TIER3_LEVEL:
            return 3
        return None

    def add_stat_progress(self, amount: int):
        messages = [f"Postęp rozwoju statystyk +{amount}."]
        self.stat_progress += amount
        while self.stat_progress >= STAT_GROWTH_THRESHOLD:
            self.stat_progress -= STAT_GROWTH_THRESHOLD
            if self.class_type == "physical":
                self.strength += 1
                self.dexterity += 1
                self.constitution += 1
                messages.append(
                    "Statystyki rosną automatycznie: Siła +1, Zręczność +1, Kondycja +1."
                )
            else:
                self.intelligence += 1
                self.willpower += 1
                messages.append(
                    "Statystyki rosną automatycznie: Inteligencja +1, Siła Woli +1."
                )
        return messages

    def add_soul_xp(self, amount: int):
        if self.soul_level >= SOUL_MAX_LEVEL:
            return ["Broń Duszy ma już Soul Level 100."]
        messages = [f"Broń Duszy otrzymuje {amount} Soul XP."]
        self.soul_xp += amount
        while self.soul_level < SOUL_MAX_LEVEL:
            need = self.soul_xp_to_next()
            if self.soul_xp < need:
                break
            self.soul_xp -= need
            self.soul_level += 1
            messages.append(f"Broń Duszy awansuje na Soul Level {self.soul_level}.")
            if self.soul_level == TIER2_LEVEL and self.soul_tier == 1:
                messages.append("Możesz odblokować Tier 2 komendą: unlock.")
            if self.soul_level == TIER3_LEVEL and self.soul_tier == 2:
                messages.append("Możesz odblokować Tier 3 komendą: unlock.")
        if self.soul_level >= SOUL_MAX_LEVEL:
            self.soul_level = SOUL_MAX_LEVEL
            self.soul_xp = 0
            messages.append("Osiągnięto maksymalny Soul Level 100.")
        return messages


class Session:
    def __init__(self, server, reader, writer):
        self.server = server
        self.reader = reader
        self.writer = writer
        self.account_id: Optional[int] = None
        self.character: Optional[Character] = None
        self.closed = False

    async def send(self, text=""):
        if self.closed:
            return
        try:
            self.writer.write((text + "\r\n").encode("utf-8"))
            await self.writer.drain()
        except (ConnectionError, BrokenPipeError):
            self.closed = True

    async def prompt(self, text):
        if self.closed:
            return
        try:
            self.writer.write(text.encode("utf-8"))
            await self.writer.drain()
        except (ConnectionError, BrokenPipeError):
            self.closed = True

    async def read_line(self) -> Optional[str]:
        try:
            while True:
                data = await self.reader.readline()
                if not data:
                    return None
                text = clean_telnet(data).replace("\r", "").replace("\n", "").strip()
                # Negocjacja Telnet może dać pustą linię.
                if text == "":
                    continue
                return text
        except (ConnectionError, asyncio.IncompleteReadError):
            return None

    async def ask(self, prompt_text) -> Optional[str]:
        await self.prompt(prompt_text)
        return await self.read_line()

    async def login_flow(self) -> bool:
        await self.send("SOULBOUND ONLINE v0.5")
        await self.send("Tekstowy MUD. Połączono z serwerem.")
        await self.send("Wpisz: login albo new")
        while True:
            cmd = await self.ask("> ")
            if cmd is None:
                return False
            cmd = cmd.lower()
            if cmd in ("login", "zaloguj"):
                if await self.do_login():
                    return True
            elif cmd in ("new", "nowe", "konto"):
                if await self.do_new_account():
                    return True
            elif cmd in ("quit", "wyjdz", "wyjdź"):
                return False
            else:
                await self.send("Dostępne: login, new, quit")

    async def do_login(self) -> bool:
        username = await self.ask("Nazwa konta: ")
        if username is None:
            return False
        row = self.server.db.account_by_name(username)
        if not row:
            await self.send("Nie ma takiego konta.")
            return False

        password = await self.ask("Hasło: ")
        if password is None:
            return False
        if not verify_password(password, row["password_salt"], row["password_hash"]):
            await self.send("Nieprawidłowe hasło.")
            return False

        if self.server.account_online(row["id"]):
            await self.send("To konto jest już zalogowane.")
            return False

        self.account_id = row["id"]
        char_row = self.server.db.character_for_account(self.account_id)
        if char_row:
            self.character = Character.from_row(char_row)
        else:
            await self.send("Konto nie ma jeszcze postaci.")
            if not await self.character_creator():
                return False
        return True

    async def do_new_account(self) -> bool:
        await self.send("Tworzenie nowego konta.")
        while True:
            username = await self.ask("Nazwa konta, 3-20 znaków: ")
            if username is None:
                return False
            username = normalize_name(username)
            if not safe_name(username):
                await self.send("Dozwolone są litery, cyfry, _ i -. Długość 3-20.")
                continue
            if self.server.db.account_by_name(username):
                await self.send("Taka nazwa konta już istnieje.")
                continue
            break

        while True:
            password = await self.ask("Hasło, minimum 6 znaków: ")
            if password is None:
                return False
            if len(password) < 6:
                await self.send("Hasło jest za krótkie.")
                continue
            confirm = await self.ask("Powtórz hasło: ")
            if confirm is None:
                return False
            if password != confirm:
                await self.send("Hasła się różnią.")
                continue
            break

        self.account_id = self.server.db.create_account(username, password)
        await self.send("Konto utworzone.")
        return await self.character_creator()

    async def character_creator(self) -> bool:
        await self.send("KREATOR POSTACI")
        while True:
            name = await self.ask("Nazwa postaci, 3-20 znaków: ")
            if name is None:
                return False
            name = normalize_name(name)
            if not safe_name(name):
                await self.send("Nieprawidłowa nazwa.")
                continue
            if self.server.db.character_name_exists(name):
                await self.send("Postać o tej nazwie już istnieje.")
                continue
            break

        await self.send("Wybierz rasę:")
        for i, race in enumerate(RACES, 1):
            rname, desc, s, d, c, inte, w = race
            await self.send(
                f"{i}. {rname}. {desc} "
                f"Siła {s}, Zręczność {d}, Kondycja {c}, Inteligencja {inte}, Siła Woli {w}."
            )
        race = await self.choose_number(RACES, "Numer rasy: ")
        if race is None:
            return False

        await self.send("Wybierz klasę:")
        for i, cls in enumerate(CLASSES, 1):
            cname, ctype, weapon, _ = cls
            kind = "fizyczna" if ctype == "physical" else "magiczna"
            await self.send(f"{i}. {cname}. Typ {kind}. Broń Duszy: {weapon}.")
        cls = await self.choose_number(CLASSES, "Numer klasy: ")
        if cls is None:
            return False

        self.server.db.create_character(self.account_id, name, race, cls)
        row = self.server.db.character_for_account(self.account_id)
        self.character = Character.from_row(row)
        await self.send(f"Utworzono postać {self.character.name}.")
        await self.send("Postać nie ma levelu. Jej statystyki rosną automatycznie.")
        await self.send("Broń Duszy ma osobny Soul Level od 1 do 100.")
        return True

    async def choose_number(self, items, prompt_text):
        while True:
            raw = await self.ask(prompt_text)
            if raw is None:
                return None
            try:
                n = int(raw)
                if 1 <= n <= len(items):
                    return items[n - 1]
            except ValueError:
                pass
            await self.send("Nieprawidłowy numer.")

    async def enter_world(self):
        await self.server.broadcast_room(
            self.character.room_id,
            f"{self.character.name} pojawia się w okolicy.",
            exclude=self,
        )
        await self.send(f"Witaj, {self.character.name}.")
        await self.send("Wpisz help, aby poznać komendy.")
        await self.look()

    async def look(self):
        room = ROOMS[self.character.room_id]
        await self.send(f"{room['name']}")
        await self.send(room["desc"])
        others = [
            s.character.name
            for s in self.server.sessions
            if s is not self and s.character and s.character.room_id == self.character.room_id
        ]
        if others:
            await self.send("Gracze tutaj: " + ", ".join(sorted(others, key=str.lower)))
        else:
            await self.send("Nie ma tutaj innych graczy.")
        exits = ", ".join(room["exits"].keys()) if room["exits"] else "brak"
        await self.send("Wyjścia: " + exits)

    async def show_help(self):
        await self.send("KOMENDY")
        await self.send("look / l - opis lokacji")
        await self.send("north, south, east, west lub n/s/e/w - ruch")
        await self.send("who - gracze online")
        await self.send("say tekst - powiedz coś graczom w tej lokacji")
        await self.send("tell gracz tekst - prywatna wiadomość")
        await self.send("stats - statystyki postaci")
        await self.send("soul - informacje o Broni Duszy")
        await self.send("fight - walka treningowa; dostępna na Dziedzińcu Treningowym")
        await self.send("unlock - odblokuj kolejny Tier Broni Duszy, gdy spełniasz wymagania")
        await self.send("save - zapisz postać")
        await self.send("quit - wyjdź z gry")

    async def show_stats(self):
        c = self.character
        await self.send(f"{c.name}. Rasa: {c.race}. Klasa: {c.class_name}.")
        await self.send("Poziom postaci: nie istnieje.")
        await self.send(f"Siła: {c.strength}")
        await self.send(f"Zręczność: {c.dexterity}")
        await self.send(f"Kondycja: {c.constitution}")
        await self.send(f"Inteligencja: {c.intelligence}")
        await self.send(f"Siła Woli: {c.willpower}")
        await self.send(
            f"Postęp do automatycznego wzrostu statystyk: "
            f"{c.stat_progress} z {STAT_GROWTH_THRESHOLD}."
        )
        await self.send(f"Maksymalne życie: {c.max_hp()}.")
        if c.class_type == "magic":
            await self.send(f"Maksymalna mana: {c.max_mana()}.")

    async def show_soul(self):
        c = self.character
        await self.send(f"Broń Duszy: {c.soul_weapon}.")
        await self.send(f"Soul Level: {c.soul_level} z {SOUL_MAX_LEVEL}.")
        if c.soul_level < SOUL_MAX_LEVEL:
            await self.send(f"Soul XP: {c.soul_xp} z {c.soul_xp_to_next()}.")
        else:
            await self.send("Soul XP: maksimum.")
        await self.send(f"Tier: {c.soul_tier} z 3.")
        await self.send(f"Moc Broni Duszy: {c.soul_power()}.")
        nxt = c.can_unlock()
        if nxt:
            await self.send(f"Tier {nxt} jest gotowy do odblokowania. Wpisz unlock.")
        elif c.soul_tier == 1:
            await self.send(f"Tier 2 wymaga Soul Level {TIER2_LEVEL}.")
        elif c.soul_tier == 2:
            await self.send(f"Tier 3 wymaga Soul Level {TIER3_LEVEL}.")
        else:
            await self.send("Wszystkie Tiery są odblokowane.")

    async def move(self, direction):
        room = ROOMS[self.character.room_id]
        target = room["exits"].get(direction)
        if not target:
            await self.send("Nie możesz iść w tym kierunku.")
            return
        old_room = self.character.room_id
        await self.server.broadcast_room(
            old_room, f"{self.character.name} odchodzi.", exclude=self
        )
        self.character.room_id = target
        self.server.db.save_character(self.character)
        await self.server.broadcast_room(
            target, f"{self.character.name} przychodzi.", exclude=self
        )
        await self.look()

    async def say(self, text):
        if not text:
            await self.send("Użycie: say tekst")
            return
        await self.send(f"Mówisz: {text}")
        await self.server.broadcast_room(
            self.character.room_id,
            f"{self.character.name} mówi: {text}",
            exclude=self,
        )

    async def tell(self, args):
        parts = args.split(maxsplit=1)
        if len(parts) != 2:
            await self.send("Użycie: tell gracz tekst")
            return
        target_name, text = parts
        target = self.server.find_character_session(target_name)
        if not target:
            await self.send("Ten gracz nie jest online.")
            return
        await target.send(f"{self.character.name} mówi ci prywatnie: {text}")
        await self.send(f"Do {target.character.name}: {text}")

    async def who(self):
        players = sorted(
            [s.character.name for s in self.server.sessions if s.character],
            key=str.lower,
        )
        await self.send(f"Gracze online: {len(players)}.")
        if players:
            await self.send(", ".join(players))

    async def unlock(self):
        c = self.character
        nxt = c.can_unlock()
        if not nxt:
            if c.soul_tier >= 3:
                await self.send("Masz już Tier 3.")
            elif c.soul_tier == 1:
                await self.send(f"Tier 2 wymaga Soul Level {TIER2_LEVEL}.")
            else:
                await self.send(f"Tier 3 wymaga Soul Level {TIER3_LEVEL}.")
            return
        c.soul_tier = nxt
        self.server.db.save_character(c)
        await self.send(f"Odblokowano Tier {nxt} Broni Duszy {c.soul_weapon}.")
        await self.send(f"Nowa moc Broni Duszy: {c.soul_power()}.")

    async def fight(self):
        if self.character.room_id != "training":
            await self.send("Walczysz treningowo tylko na Dziedzińcu Treningowym.")
            return

        c = self.character
        if c.class_type == "physical":
            rating = max(1, (c.strength + c.dexterity + c.constitution) // 3 - 8)
        else:
            rating = max(1, (c.intelligence + c.willpower) // 2 - 8)

        enemy = random.choice(["Goblin", "Wilk Cienia", "Szkielet", "Bandyta"])
        enemy_hp = 25 + rating * 7
        player_hp = c.max_hp()
        await self.send(f"Rozpoczynasz treningową walkę. Przeciwnik: {enemy}.")
        await self.server.broadcast_room(
            c.room_id, f"{c.name} rozpoczyna treningową walkę.", exclude=self
        )

        rounds = 0
        while enemy_hp > 0 and player_hp > 0 and rounds < 30:
            rounds += 1
            if c.class_type == "physical":
                damage = max(1, c.soul_power() + c.strength + c.dexterity // 3 + random.randint(-3, 3))
            else:
                damage = max(1, c.soul_power() + c.intelligence + c.willpower // 2 + random.randint(-3, 3))
            enemy_hp -= damage
            await self.send(f"Runda {rounds}. Zadajesz {damage} obrażeń.")
            if enemy_hp <= 0:
                break
            incoming = max(1, 3 + rating + random.randint(-2, 2))
            player_hp -= incoming
            await self.send(f"{enemy} zadaje ci {incoming} obrażeń. Pozostałe życie: {max(0, player_hp)}.")
            await asyncio.sleep(0)

        if player_hp <= 0:
            await self.send("Przegrywasz trening. Nie tracisz statystyk ani Soul XP.")
            return

        stat_reward = 35 + rating * 5
        soul_reward = 20 + rating * 6
        await self.send(f"Pokonujesz przeciwnika {enemy}.")
        for msg in c.add_stat_progress(stat_reward):
            await self.send(msg)
        for msg in c.add_soul_xp(soul_reward):
            await self.send(msg)
        self.server.db.save_character(c)

    async def command_loop(self):
        while not self.closed:
            raw = await self.ask("> ")
            if raw is None:
                break
            if not raw:
                continue
            parts = raw.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            command = COMMAND_ALIASES.get(command, command)
            direction = DIRECTION_ALIASES.get(command)
            if direction:
                await self.move(direction)
            elif command == "help":
                await self.show_help()
            elif command == "look":
                await self.look()
            elif command == "who":
                await self.who()
            elif command == "say":
                await self.say(args)
            elif command == "tell":
                await self.tell(args)
            elif command == "stats":
                await self.show_stats()
            elif command == "soul":
                await self.show_soul()
            elif command == "fight":
                await self.fight()
            elif command == "unlock":
                await self.unlock()
            elif command == "save":
                self.server.db.save_character(self.character)
                await self.send("Postać zapisana.")
            elif command == "quit":
                await self.send("Do zobaczenia.")
                break
            else:
                await self.send("Nieznana komenda. Wpisz help.")

    async def close(self):
        if self.closed:
            return
        self.closed = True
        if self.character:
            self.server.db.save_character(self.character)
            await self.server.broadcast_room(
                self.character.room_id,
                f"{self.character.name} opuszcza grę.",
                exclude=self,
            )
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
            pass


class MudServer:
    def __init__(self):
        self.db = Database(DB_PATH)
        self.sessions = set()

    def account_online(self, account_id: int) -> bool:
        return any(s.account_id == account_id and s.character for s in self.sessions)

    def find_character_session(self, name: str):
        for s in self.sessions:
            if s.character and s.character.name.lower() == name.lower():
                return s
        return None

    async def broadcast_room(self, room_id: str, text: str, exclude=None):
        targets = [
            s for s in self.sessions
            if s is not exclude and s.character and s.character.room_id == room_id
        ]
        for s in targets:
            await s.send(text)

    async def handle_client(self, reader, writer):
        if len(self.sessions) >= MAX_CLIENTS:
            writer.write(b"Serwer jest pelny.\r\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        session = Session(self, reader, writer)
        self.sessions.add(session)
        try:
            if await session.login_flow():
                await session.enter_world()
                await session.command_loop()
        except Exception as exc:
            try:
                await session.send("Wystąpił błąd sesji. Połączenie zostanie zamknięte.")
            except Exception:
                pass
            print(f"[SESSION ERROR] {exc}", file=sys.stderr)
        finally:
            await session.close()
            self.sessions.discard(session)

    async def run(self):
        server = await asyncio.start_server(self.handle_client, HOST, PORT)
        addresses = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
        print(f"Soulbound v0.5 Online nasłuchuje: {addresses}")
        print(f"Baza danych: {DB_PATH}")
        print(f"Limit jednoczesnych klientów: {MAX_CLIENTS}")
        async with server:
            await server.serve_forever()


def main():
    try:
        asyncio.run(MudServer().run())
    except KeyboardInterrupt:
        print("\nSerwer zatrzymany.")


if __name__ == "__main__":
    main()
