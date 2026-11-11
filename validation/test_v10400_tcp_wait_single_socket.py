# -*- coding: utf-8 -*-
"""Ensure bootstrap tests wait on a single connection without filling backlog."""
import socket,threading,time,unittest
from validation.v10400_tcp_loopback_smoke import _wait_for_banner

class TestSingleSocket(unittest.TestCase):
    def exercise(self, *, send_after=None, deadline=2.5):
        listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(4)
        port=listener.getsockname()[1];accepted=[];errors=[]
        def work():
            try:
                conn,_=listener.accept();accepted.append(1)
                if send_after is not None:
                    time.sleep(send_after)
                    conn.sendall('SOULBOUND ONLINE\\r\\n'.encode())
                else:
                    time.sleep(deadline+0.2)
                conn.close()
            except OSError as exc:errors.append(exc)
            finally:listener.close()
        t=threading.Thread(target=work,daemon=True);t.start()
        try:
            return _wait_for_banner('127.0.0.1',port,time.monotonic()+deadline),len(accepted)
        finally:
            t.join(timeout=3)
    def test_delayed_login_same_socket(self):
        banner,count=self.exercise(send_after=.6)
        self.assertIn(b'SOULBOUND ONLINE',banner)
        self.assertEqual(count,1)
    def test_telnet_iac_not_treated_as_login(self):
        listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1)
        port=listener.getsockname()[1]
        def work():
            try:
                c,_=listener.accept()
                c.sendall(b"\xff\xfb*\xff\xfa*")
                time.sleep(.5)
                c.close()
            finally:listener.close()
        t=threading.Thread(target=work,daemon=True);t.start()
        try:
            with self.assertRaises((RuntimeError,TimeoutError)):
                _wait_for_banner('127.0.0.1',port,time.monotonic()+1.5)
        finally:t.join(timeout=2)

    def test_split_banner_waits_for_real_menu(self):
        listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1)
        port=listener.getsockname()[1]
        def work():
            try:
                c,_=listener.accept()
                for part in (b"\xff\xfb*",b"SOULBOUND ON",b"LINE v103\r\nMENU G",b"LOWNE\r\nWybierz opcj",b"e: "):
                    c.sendall(part)
                    time.sleep(.04)
                c.close()
            finally:listener.close()
        t=threading.Thread(target=work,daemon=True);t.start()
        try:
            data=_wait_for_banner('127.0.0.1',port,time.monotonic()+3,
                                  required_markers=(b'SOULBOUND ONLINE',b'MENU G',b'Wybierz opcj'))
            self.assertIn(b'Wybierz opcj',data)
            self.assertIn(b'SOULBOUND ONLINE',data)
        finally:t.join(timeout=2)
    def test_timeout_not_false_success(self):
        with self.assertRaises(TimeoutError):self.exercise(deadline=.7)

def run():
    result=unittest.TextTestRunner(verbosity=1).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestSingleSocket))
    if not result.wasSuccessful():raise AssertionError('TCP single socket FAIL')
    return result.testsRun
if __name__=='__main__':print(run())
