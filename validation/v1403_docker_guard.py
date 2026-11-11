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
    if ignore is None:
        check('RUN rm -f /app/core/generator_core.py && test ! -e /app/core/generator_core.py' in docker,
              'Docker image without .dockerignore must explicitly remove retired Generator Core')
    else:
        check('core/generator_core.py' in ignore.splitlines(),
              'Docker context must exclude retired core/generator_core.py')
    copy = docker.find('COPY core /app/core')
    remove = docker.find('RUN rm -f /app/core/generator_core.py && test ! -e /app/core/generator_core.py')
    audit = docker.find('RUN python /app/predeploy_check.py')
    check(copy >= 0 and copy < remove < audit,
          'Dockerfile must remove old Core before either deploy audit')
    check(docker.count('RUN rm -f /app/core/generator_core.py') == 1,
          'Docker cleanup must exist exactly once')
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
