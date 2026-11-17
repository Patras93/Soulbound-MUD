# -*- coding: utf-8 -*-
"""Read old character/world customization as data, without editor or DB writes."""
import json,sqlite3,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from systems.published_world_content import PublishedWorldContent,blank
from systems import published_races_v7600 as races
from systems import published_classes_v7700 as classes
from systems import published_heritage_v7100 as heritage

def run():
    checks=0
    with tempfile.TemporaryDirectory(prefix='published_read_test_') as tmp:
        db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row
        db.execute('CREATE TABLE live_content_v1204 (id INTEGER PRIMARY KEY,revision INTEGER NOT NULL,payload TEXT NOT NULL)')
        db.execute('INSERT INTO live_content_v1204 VALUES(1,17,?)',(json.dumps(blank(),ensure_ascii=False),))
        before=db.total_changes
        saved=PublishedWorldContent(SimpleNamespace(conn=db))
        assert saved.revision==17 and db.total_changes==before;checks+=1
        assert saved.active==blank();checks+=1
        assert not any(hasattr(saved,n) for n in ('apply','stage_edit','stage_file','stage_new_quest','export'))
        checks+=1
        db.close()
        for module,key,raw in ((races,'races',{}),(classes,'classes',{}),(heritage,'settings',{'races':{},'classes':{}})):
            config=Path(tmp)/(module.__name__.split('.')[-1]+'.json')
            config.write_text(json.dumps({'schema':1,key:raw}),encoding='utf8')
            with patch.object(module,'CONFIG_PATH',config),patch.object(module,'_SETTINGS',None):
                assert module.current()==raw; checks+=1
            assert not hasattr(module,'dispatch_v7600') and not hasattr(module,'_save');checks+=1
    print(f'SAVED CONTENT COMPATIBILITY: {checks}/{checks} PASS',flush=True)

if __name__=='__main__':run()
