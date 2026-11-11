# -*- coding: utf-8 -*-
"""v1.40.4: Railway builds must pass with .dockerignore absent in /app."""
from pathlib import Path
from tempfile import TemporaryDirectory
from validation.v1403_docker_guard import run_docker_generator_guard_v1403


_DOCKER = """FROM python:3.12-slim
WORKDIR /app
COPY core /app/core
RUN rm -f /app/core/generator_core.py && test ! -e /app/core/generator_core.py
COPY validation /app/validation
COPY predeploy_check.py /app/predeploy_check.py
RUN python /app/predeploy_check.py && python /app/predeploy_full.py
"""


def run_railway_stage_regression_v1404():
    tests = 0
    with TemporaryDirectory(prefix="soulbound_railway_stage_") as work:
        p = Path(work)
        (p / "core").mkdir()
        (p / "validation").mkdir()
        (p / "Dockerfile").write_text(_DOCKER, encoding="utf-8")
        (p / ".dockerignore").write_text("core/generator_core.py\n", encoding="utf-8")
        source = run_docker_generator_guard_v1403(p)
        assert source["checks"] == 5 and not source["errors"], source
        tests += 1

        # Docker COPY does not put .dockerignore inside the /app build layer.
        (p / ".dockerignore").unlink()
        image = run_docker_generator_guard_v1403(p)
        assert image["checks"] == 5 and not image["errors"], image
        tests += 1

        (p / "core" / "generator_core.py").write_text("# retired", encoding="utf-8")
        stale = run_docker_generator_guard_v1403(p)
        assert any('still in source' in e for e in stale["errors"]), stale
        tests += 1
        (p / "core" / "generator_core.py").unlink()

        (p / "Dockerfile").write_text(_DOCKER.replace(
            "RUN rm -f /app/core/generator_core.py && test ! -e /app/core/generator_core.py\n", ""
        ), encoding="utf-8")
        unprotected = run_docker_generator_guard_v1403(p)
        assert unprotected["errors"], unprotected
        tests += 1
        (p / "Dockerfile").write_text(_DOCKER, encoding="utf-8")

        (p / "core" / "accidental_import.py").write_text(
            "from core.generator_core import something\n", encoding="utf-8")
        invalid_import = run_docker_generator_guard_v1403(p)
        assert any('imported by' in e for e in invalid_import["errors"]), invalid_import
        tests += 1
    return {"tests": tests, "errors": []}


if __name__ == '__main__':
    result = run_railway_stage_regression_v1404()
    print(f"RAILWAY STAGE v1.40.4: {result['tests']} tests PASS")
