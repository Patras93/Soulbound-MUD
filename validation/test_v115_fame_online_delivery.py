import asyncio
import unittest
from types import SimpleNamespace
from systems.v115.fame_online_delivery import FameOnlineDelivery

class OnlineDeliveryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.messages=[]
        async def send(message): self.messages.append(message)
        self.session=SimpleSession(send)

    async def test_success_messages_after_settlement(self):
        calls=[]
        def settle(*args, **kwargs):
            calls.append('committed')
            return [('exp','kraina','boss','Tytan',{'character':100})]
        delivery=FameOnlineDelivery(settle=settle)
        result=await delivery.tick(self.session,now=123)
        self.assertEqual(len(result),1)
        self.assertEqual(calls,['committed'])
        self.assertIn('EXP',self.messages[0])

    async def test_fame_only_after_exp_phase(self):
        phases=iter([[('exp','kraina','boss','Tytan',{})], [],
                     [('fame','kraina','boss','Tytan',1)]])
        delivery=FameOnlineDelivery(settle=lambda *a,**k: next(phases))
        await delivery.tick(self.session)
        self.assertEqual(len(self.messages),1)
        await delivery.tick(self.session)
        self.assertEqual(len(self.messages),1)
        await delivery.tick(self.session)
        self.assertEqual(len(self.messages),2)
        self.assertIn('FAMA',self.messages[1])

    async def test_failed_settlement_does_not_announce(self):
        def settle(*a,**k): raise RuntimeError('SQLite rollback')
        with self.assertRaises(RuntimeError):
            await FameOnlineDelivery(settle=settle).tick(self.session)
        self.assertEqual(self.messages,[])

    async def test_invalid_owner_rejected(self):
        self.session.character.account_id=5
        with self.assertRaises(ValueError):
            await FameOnlineDelivery(settle=lambda *a,**k:[]).tick(self.session)

    async def test_serializes_concurrent_ticks(self):
        active=0
        seen=[]
        def settle(*a,**k):
            nonlocal active
            active+=1
            self.assertEqual(active,1)
            seen.append(True)
            active-=1
            return []
        delivery=FameOnlineDelivery(settle=settle)
        await asyncio.gather(*(delivery.tick(self.session) for _ in range(5)))
        self.assertEqual(len(seen),5)

    async def test_requires_live_character(self):
        self.session.character=None
        with self.assertRaises(ValueError):
            await FameOnlineDelivery(settle=lambda *a,**k:[]).tick(self.session)

class SimpleSession:
    def __init__(self, send):
        self.account_id=1
        self.character=SimpleNamespace(account_id=1)
        self.server=SimpleNamespace(db=object())
        self.send=send

if __name__=='__main__': unittest.main()
