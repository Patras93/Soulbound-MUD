FROM python:3.12-slim
ENV PYTHONUTF8=1
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV SOULBOUND_HOST=0.0.0.0
ENV SOULBOUND_PORT=4000
ENV SOULBOUND_MAX_CLIENTS=100

WORKDIR /app

# v0.30.2: server.py imports these Generator Core modules at startup.
# Railway builds from this Dockerfile, so every runtime module must exist in /app.
COPY server.py /app/server.py
COPY generator_core.py /app/generator_core.py
COPY world_topology_generator.py /app/world_topology_generator.py
COPY dynamic_world_v029.py /app/dynamic_world_v029.py
COPY world_logic_validator.py /app/world_logic_validator.py
COPY README_PL.txt /app/README_PL.txt
COPY CHANGELOG_PL.txt /app/CHANGELOG_PL.txt
COPY RAILWAY_PL.txt /app/RAILWAY_PL.txt

EXPOSE 4000

CMD ["python", "-u", "/app/server.py"]
