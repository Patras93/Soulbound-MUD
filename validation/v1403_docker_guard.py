# -*- coding: utf-8 -*-
"""v1.40.3: ensure stale Generator Core never enters a Railway image."""
from pathlib import Path
import re


def run_docker_generator_guard_v1403(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    checks = 0
    errors = []

    def check(condition, reason):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(reason)

    docker = (root / 'Dockerfile').read_text(encoding='utf-8')
    ignore_path = root / '.dockerignore'
    # Docker reads .dockerignore when creating the build context but does not
    # copy it into /app. Validate its pattern in the unpacked source folder;
    # in the Railway image, rely on the explicit cleanup before predeploy.
    ignore = ignore_path.read_text(encoding='utf-8') if ignore_path.is_file() else None
    src_core = root / 'core' / 'generator_core.py'
    check(not src_core.exists(), 'retired Generator Core still in source tree')
    legacy_cleanup = 'RUN rm -f /app/core/generator_core.py && test ! -e /app/core/generator_core.py'
    modern_install = 'RUN python -m systems.current_install install --target /app'
    modern = modern_install in docker
    if ignore is None:
        # Legacy image checks used a cleanup instruction after COPY.
        # New multi-stage images must instead create /app through the
        # inspected installer and must not copy the old source into /app.
        check(modern or legacy_cleanup in docker,
              'Docker image has neither certified installer nor retired-core cleanup')
    else:
        check('core/generator_core.py' in ignore.splitlines(),
              'Docker context must exclude retired core/generator_core.py')
    if modern:
        # The new builder creates an isolated installation with only
        # runtime files. The published stage never copies the raw tree.
        check('COPY . /candidate' in docker and
              docker.find('COPY . /candidate') < docker.find(modern_install) and
              'COPY --from=verified /app /app' in docker and
              'COPY . /app' not in docker,
              'Current multi-stage Docker must install verified sources, never raw copy')
        check(docker.count(modern_install)==1 and
              docker.count('COPY --from=verified /app /app')==1,
              'Current install and copy must each occur exactly once')
    else:
        copy = docker.find('COPY core /app/core')
        remove = docker.find(legacy_cleanup)
        audit = docker.find('RUN python /app/predeploy_check.py')
        check(copy>=0 and copy < remove < audit,
              'Legacy Docker must remove retired Core before audits')
        check(docker.count(legacy_cleanup)==1,
              'Legacy Docker cleanup must exist exactly once')
    imports = []
    for source in root.rglob('*.py'):
        if re.search(r'^\s*(?:from\s+core\.generator_core|import\s+core\.generator_core)',
                     source.read_text(encoding='utf-8-sig'), re.MULTILINE):
            imports.append(str(source.relative_to(root)))
    check(not imports, 'retired Generator Core imported by: ' + ', '.join(imports))
    return {'checks': checks, 'errors': errors}


if __name__ == '__main__':
    result = run_docker_generator_guard_v1403()
    print(f"RAILWAY GENERATOR GUARD v1.40.3: {result['checks']} checks, {len(result['errors'])} errors")
    if result['errors']:
        raise SystemExit('; '.join(result['errors']))
