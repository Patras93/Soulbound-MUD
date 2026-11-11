"""Odroczone wyplaty i krotkie komunikaty NVDA; bez logiki ekonomii."""
import asyncio
import datetime as dt
from .policy import gift_kind
from .legacy import _legacy_claimed
from .payout import claim_once

DELAY_SECONDS = 120

async def announce_gift(session, result):
    if not result or session.closed or not session.character:
        return
    from core.bootstrap_economy_professions import currency_reading_text
    name='ADWENT' if result['kind']=='advent' else 'DZIENNY PREZENT'
    await session.send(f'{name}: automatyczna nagroda: '
                       f'{currency_reading_text(result["silver"],0,0)}, '
                       f'EXP postaci +{result["exp"]}.')

async def award_after_delay(session, account_id, character, delay=DELAY_SECONDS,claim_function=None):
    await asyncio.sleep(delay)
    if (session.closed or session.account_id!=account_id
        or session.character is not character):
        return None
    # Database is shared across sessions; defer for up to three short retries
    # if another gameplay transaction is in progress. Never issue a partial gift.
    for attempt in range(3):
        try:
            result=(claim_function or claim_once)(session)
        except RuntimeError as exc:
            if 'Transakcja SQLite zajęta' not in str(exc):
                raise
            if attempt==2:
                return None
            await asyncio.sleep(5)
            if (session.closed or session.account_id!=account_id
                or session.character is not character):
                return None
        else:
            if (not session.closed and session.account_id==account_id
                and session.character is character):
                await announce_gift(session,result)
            return result
    return None

def schedule_gift(session,award_function=None):
    """Called from the unchanged login method in place of immediate payout."""
    if session.closed or session.account_id is None or not session.character:
        return
    old=getattr(session,'_v109_gift_task',None)
    if old is not None and not old.done():
        old.cancel()
    account=int(session.account_id)
    character=session.character
    task=asyncio.create_task((award_function or award_after_delay)(session,account,character))
    session._v109_gift_task=task
    def report_error(completed):
        if completed.cancelled():
            return
        error=completed.exception()
        if error is not None:
            print('V109_GIFT_ERROR: '+type(error).__name__+': '+str(error),flush=True)
    task.add_done_callback(report_error)

async def daily_on_enter(session):
    schedule_gift(session)

async def advent_status(session, args='', *, _today=None):
    day=dt.datetime.now().astimezone().date() if _today is None else _today
    if gift_kind(day)!='advent':
        await session.send('ADWENT: prezenty automatyczne 1–31 grudnia. Od 1 stycznia Daily Gifts.')
        return
    if not session.character:
        return
    master=int(session.server.db.master_account_for_character(session.account_id))
    conn=session.server.db.conn
    claimed=conn.execute("SELECT 1 FROM sqlite_master WHERE name='v109_gift_claims'").fetchone()
    used=bool(claimed and conn.execute(
        'SELECT 1 FROM v109_gift_claims WHERE master_account_id=? AND gift_date=?',
        (master,day.isoformat())).fetchone())
    used=used or _legacy_claimed(session.server.db,master,day,'advent')
    await session.send('ADWENT: dzień '+str(day.day)+'/31. '
                       +('Prezent odebrany.' if used else 'Prezent wpadnie automatycznie po 2 minutach od logowania.'))
