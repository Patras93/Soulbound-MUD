"""Current-only six authenticated TCP clients, party, commands and restart.
All accounts and writes are confined to a disposable localhost database.
"""
from __future__ import annotations
import asyncio, os, socket, sqlite3, subprocess, sys, tempfile, time
import re
from contextlib import closing, suppress
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
PLAYERS=6
PASSWORD='test_only_current_tcp_password'
PROMPT_TIMEOUT=40
COMMAND_TIMEOUT=30
class TcpPlayer:
    def __init__(self, account, name, port):
        self.account, self.name, self.port = account, name, port
        self.reader = self.writer = None
        self.times = []

    async def until(self, marker: str, timeout=PROMPT_TIMEOUT):
        # The login prompts may have no trailing newline. Use readuntil, not readline.
        raw = await asyncio.wait_for(self.reader.readuntil(marker.encode('utf-8')), timeout)
        return raw.decode('utf-8', 'replace')

    async def send(self, command):
        self.writer.write((command + '\n').encode('utf-8'))
        await asyncio.wait_for(self.writer.drain(), COMMAND_TIMEOUT)

    async def connect_and_login(self):
        self.reader, self.writer = await asyncio.wait_for(
            asyncio.open_connection('127.0.0.1', self.port), 10)
        await self.until('Wybierz opcję: ')
        await self.send('1')
        await self.until('Nazwa konta: ')
        await self.send(self.account)
        await self.until('Hasło: ')
        await self.send(PASSWORD)
        await self.until('Wybierz opcję: ')
        await self.send('1')
        await self.until('Postać: ')
        await self.send('1')
        response = await self.until('Wpisz help, aby poznać komendy.')
        if f'Witaj, {self.name}' not in response and self.name not in response:
            raise AssertionError(f'{self.name}: login did not enter the game')
        await self.drain_idle()

    async def drain_idle(self, quiet=0.15, total=2):
        chunks = []
        until = time.monotonic() + total
        while time.monotonic() < until:
            try:
                data = await asyncio.wait_for(self.reader.read(16384), quiet)
            except asyncio.TimeoutError:
                break
            if not data:
                raise ConnectionError(f'{self.name}: connection closed')
            chunks.append(data)
        return b''.join(chunks).decode('utf-8', 'replace')

    async def command(self, command, quiet=0.18):
        await self.drain_idle(quiet=0.05, total=0.12)
        begin = time.perf_counter()
        await self.send(command)
        # A quiet period is not enough if the server is slow: wait for first bytes.
        first = await asyncio.wait_for(self.reader.read(16384), COMMAND_TIMEOUT)
        if not first:
            raise ConnectionError(f'{self.name}: server closed after {command}')
        tail = await self.drain_idle(quiet=quiet, total=1.8)
        elapsed = (time.perf_counter() - begin) * 1000
        self.times.append(elapsed)
        result = first.decode('utf-8', 'replace') + tail
        if 'Wystąpił błąd komendy' in result or 'Wystąpił błąd sesji' in result or 'Traceback (most recent call last)' in result:
            raise AssertionError(f'{self.name}: runtime failure in {command}: {result[-450:]}')
        return result

    async def close(self):
        if self.writer is not None:
            self.writer.close()
            with suppress(ConnectionError, OSError, asyncio.TimeoutError):
                await asyncio.wait_for(self.writer.wait_closed(), 2)


async def read_complete_party_roster(client, initial, expected_names, *, timeout=20.0):
    """Read a line-streamed status until each numbered member line arrives.

    A short network quiet interval after the header is not proof that the
    following await self.send(...) lines have finished.  An actual missing
    player must STILL fail; never accept the header's count as proof.
    """
    def listed_names(data):
        clean = data.replace("\r", "")
        return {name for name in expected_names if re.search(
            rf"(?im)^\s*\d+\.\s*{re.escape(name)}\.\s+Lokacja:", clean
        )}

    data = initial
    deadline = time.monotonic() + timeout
    while len(listed_names(data)) != len(expected_names):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            chunk = await asyncio.wait_for(client.reader.read(16384), remaining)
        except asyncio.TimeoutError:
            break
        if not chunk:
            break
        data += chunk.decode('utf-8', 'replace')
        if len(data) > 65536:
            raise AssertionError('Party status emitted excessive data without a complete roster')
        if ('Wystąpił błąd komendy' in data or 'Wystąpił błąd sesji' in data
                or 'Traceback (most recent call last)' in data):
            raise AssertionError('Runtime failure while reading party roster: ' + data[-500:])
    missing = [name for name in expected_names if name not in listed_names(data)]
    return data, missing


async def exercise(port):
    clients=[TcpPlayer(f'currenttcp{i}',f'Currenttcp{i}',port) for i in range(1,7)]
    try:
        await asyncio.gather(*(c.connect_and_login() for c in clients))
        for command in ('who','status','look','help','quests','skills','inventory','equipment','money','soul'):
            answers=await asyncio.gather(*(c.command(command) for c in clients))
            assert all(answer.strip() for answer in answers), command
        reader,writer=await asyncio.open_connection('127.0.0.1',port)
        try:
            overflow=await asyncio.wait_for(reader.read(4096),10)
            assert 'Serwer jest pełny' in overflow.decode('utf8','replace'), overflow
        finally:
            writer.close()
            with suppress(ConnectionError,OSError):await writer.wait_closed()
        lead=clients[0]
        await lead.command('druzyna zaloz')
        for member in clients[1:]:
            await lead.command('druzyna zapros '+member.name)
            await member.command('dolacz')
        initial=await lead.command('druzyna status')
        _,missing=await read_complete_party_roster(lead,initial,[c.name for c in clients],timeout=20)
        assert not missing, missing
        return 6*10+6+6+1
    finally:
        await asyncio.gather(*(c.close() for c in clients),return_exceptions=True)

def child():
    db_path=Path(os.environ['SOULBOUND_DB']).resolve()
    assert db_path.parent.name.startswith('sb112_tcp6_')
    assert db_path.name=='current_six.sqlite'
    assert os.environ['SOULBOUND_HOST']=='127.0.0.1'
    assert os.environ['SOULBOUND_V112_STAGING']=='1'
    import server
    from storage.database import Database
    from core.classes_skills import CLASSES,RACES
    db=Database(str(db_path))
    try:
        for i in range(1,7):
            username=f'currenttcp{i}';name=f'Currenttcp{i}'
            existing=db.account_by_name(username)
            if existing is None:
                account=db.create_account(username,PASSWORD)
                cases=dict.fromkeys(('nom','gen','dat','acc','ins','loc','voc'),name)
                db.create_character_for_master(account,name,RACES[0],CLASSES[i-1],cases)
            else:
                chars=db.characters_for_master(int(existing['id']))
                assert len(chars)==1 and chars[0]['name']==name
        db.conn.commit()
    finally:db.conn.close()
    server.main()

def main():
    with tempfile.TemporaryDirectory(prefix='sb112_tcp6_') as folder:
        home=Path(folder);database=home/'current_six.sqlite'
        for cycle in range(2):
            with socket.socket() as probe:
                probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
            env=dict(os.environ)
            for key in list(env):
                if (key.startswith('SOULBOUND_') or key in ('PORT','RAILWAY_TCP_APPLICATION_PORT','DATABASE_URL','RAILWAY_VOLUME_MOUNT_PATH')):
                    env.pop(key,None)
            env.update(SOULBOUND_DB=str(database),SOULBOUND_V112_STAGING='1',SOULBOUND_HOST='127.0.0.1',
                       SOULBOUND_PORT=str(port),SOULBOUND_MAX_CLIENTS='6',SOULBOUND_WORLD_SEED_FILE=str(home/'seed.txt'),
                       PYTHONPATH=str(ROOT),PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1')
            log=home/f'cycle{cycle}.log'
            with log.open('w',encoding='utf8') as output:
                proc=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--child'],
                    cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
                try:
                    deadline=time.monotonic()+180
                    while True:
                        text=log.read_text('utf8',errors='replace')
                        if 'World Core nasłuchuje:' in text:break
                        if proc.poll() is not None or time.monotonic()>deadline:
                            raise AssertionError('Private TCP server did not start: '+text[-6000:])
                        time.sleep(.2)
                    checks=asyncio.run(exercise(port))
                    assert proc.poll() is None
                    assert 'Traceback (most recent call last)' not in log.read_text('utf8',errors='replace')
                    print(f'CURRENT TCP cycle {cycle+1}: 6 authenticated clients, 60 commands, party6, seventh rejected PASS ({checks} checks)',flush=True)
                except BaseException:
                    print(log.read_text('utf8',errors='replace')[-6000:],flush=True)
                    raise
                finally:
                    proc.terminate()
                    try:proc.wait(timeout=12)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=10)
            with closing(sqlite3.connect(database)) as conn:
                assert conn.execute('PRAGMA integrity_check').fetchone()==('ok',)
                assert conn.execute("SELECT COUNT(*) FROM accounts WHERE username LIKE 'currenttcp%'").fetchone()==(6,)
                assert conn.execute('SELECT COUNT(*) FROM characters').fetchone()==(6,)
        print('CURRENT SIX TCP PASS: restart preserved all 6 accounts/characters; temporary DB only',flush=True)
    return 0

if __name__=='__main__':
    if '--child' in sys.argv:child()
    else:raise SystemExit(main())
