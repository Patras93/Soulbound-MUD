# -*- coding: utf-8 -*-
"""Isolated removal of LIVE_CONTENT with old published JSON preserved."""
from pathlib import Path
import hashlib
import tempfile
from systems.current_retire_live_content import retire,RetirementError,carry_published_to_staging


def main():
    checks=0
    with tempfile.TemporaryDirectory(prefix='sb11401_content_') as td:
        base=Path(td);root=base/'game';backup=base/'backup'
        (root/'LIVE_CONTENT').mkdir(parents=True)
        (root/'config').mkdir()
        (backup/'LIVE_CONTENT').mkdir(parents=True)
        for name in ('custom_classes_v7700.json','heritage_v7100.json','era_v10400_overrides.json',
                     'admin_level_caps.json','release_current.json'):
            content=('OLD '+name).encode()
            (root/'LIVE_CONTENT'/name).write_bytes(content)
            (backup/'LIVE_CONTENT'/name).write_bytes(content)
        assert retire(root,backup)==5;checks+=1
        assert not (root/'LIVE_CONTENT').exists();checks+=1
        for name in ('custom_classes_v7700.json','heritage_v7100.json','era_v10400_overrides.json'):
            assert (root/'config'/name).read_bytes()==('OLD '+name).encode();checks+=1
        assert not (root/'config'/'admin_level_caps.json').exists();checks+=1
        assert not (root/'config'/'release_current.json').exists();checks+=1
        assert (backup/'LIVE_CONTENT'/'release_current.json').is_file();checks+=1
        assert retire(root,backup)==0;checks+=1
        # Source changes after backup: refuse deletion.
        (root/'LIVE_CONTENT').mkdir()
        (root/'LIVE_CONTENT'/'extra.json').write_text('DIFFERENT')
        (backup/'LIVE_CONTENT'/'extra.json').write_text('ORIGINAL')
        try:retire(root,backup)
        except RetirementError:checks+=1
        else:raise AssertionError('Niezgodna kopia zaakceptowana')
        assert (root/'LIVE_CONTENT'/'extra.json').exists();checks+=1
        # Existing conflicting configuration: refuse deletion or overwrite.
        (backup/'LIVE_CONTENT'/'extra.json').write_text('DIFFERENT')
        (root/'LIVE_CONTENT'/'custom_classes_v7700.json').write_text('CONFLICT')
        (backup/'LIVE_CONTENT'/'custom_classes_v7700.json').write_text('CONFLICT')
        try:retire(root,backup)
        except RetirementError:checks+=1
        else:raise AssertionError('Konflikt konfiguracji zaakceptowany')
        assert (root/'LIVE_CONTENT'/'custom_classes_v7700.json').exists();checks+=1
        # New Linux code stays in its own directory, old release unchanged.
        linux=base/'linux';(linux/'config').mkdir(parents=True)
        (linux/'LIVE_CONTENT').mkdir()
        (linux/'LIVE_CONTENT'/'admin_level_caps.json').write_text('old')
        assert carry_published_to_staging(linux,backup)==3;checks+=1
        assert not (linux/'LIVE_CONTENT').exists();checks+=1
        assert (linux/'config'/'custom_classes_v7700.json').read_text()=='CONFLICT';checks+=1
        assert (linux/'config'/'heritage_v7100.json').read_text()=='OLD heritage_v7100.json';checks+=1
        assert (backup/'LIVE_CONTENT'/'release_current.json').is_file();checks+=1
    print('NO LIVE_CONTENT MIGRATION: '+str(checks)+'/'+str(checks)+' PASS')

if __name__=='__main__':main()
