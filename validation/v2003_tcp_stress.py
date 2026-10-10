# -*- coding: utf-8 -*-
"""Real TCP handshake latency to a running LOCAL Soulbound; no login or character writes.

This deliberately does not impersonate players or report combat latency. To
measure the full combat loop, run PROFILUJ_Soulbound.bat and fight normally.
"""
import asyncio
import os
import statistics
import time
from pathlib import Path


async def probe(port, limit):
    gate=asyncio.Semaphore(limit)
    async def one(number):
        async with gate:
            start=time.perf_counter()
            reader,writer=await asyncio.wait_for(asyncio.open_connection('127.0.0.1',port),8)
            elapsed=(time.perf_counter()-start)*1000
            # Waiting for the login banner verifies the actual MUD handler.
            data=await asyncio.wait_for(reader.read(2048),12)
            writer.close()
            await writer.wait_closed()
            return elapsed, bool(data)
    return await asyncio.gather(*(one(n) for n in range(limit)))


def main():
    port=int(os.getenv('SOULBOUND_PORT') or 4000)
    out=Path(__file__).resolve().parent.parent/'logs'/'TESTY_TCP_Soulbound.log'
    out.parent.mkdir(exist_ok=True)
    records=['SOULBOUND 2.00.3: REAL TCP LOCAL HOST (bez logowania)',
             f'Host=127.0.0.1 Port={port}',
             'Pomiar obejmuje tylko połączenie i ekran logowania, NIE walkę AoE.']
    try:
        result=asyncio.run(probe(port, min(16,max(4,int(os.getenv('SOULBOUND_TCP_CLIENTS','8'))))))
        values=[r[0] for r in result]
        records += [f'Połączenia: {len(result)}, odpowiedzi banera: {sum(r[1] for r in result)}',
                    f'TCP connect avg={statistics.mean(values):.2f}ms, max={max(values):.2f}ms',
                    'WYNIK: PASS' if all(r[1] for r in result) else 'WYNIK: FAIL - brak banera']
        code=0 if all(r[1] for r in result) else 1
    except (OSError, ValueError, TimeoutError, asyncio.TimeoutError) as exc:
        records += [f'WYNIK: FAIL - {type(exc).__name__}: {exc}',
                    'Najpierw uruchom Soulbound normalnie, a potem ponów test.']
        code=1
    text='\n'.join(records)+'\n'
    out.write_text(text,encoding='utf-8')
    print(text,flush=True)
    print('Log:',out,flush=True)
    return code

if __name__=='__main__':
    raise SystemExit(main())
