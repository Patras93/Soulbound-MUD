import faulthandler, runpy
faulthandler.enable()
faulthandler.dump_traceback_later(12, repeat=True)
runpy.run_path('server.py',run_name='__main__')
