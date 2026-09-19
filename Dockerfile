FROM python:3.12-slim
ENV PYTHONUTF8=1
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV SOULBOUND_HOST=0.0.0.0
ENV SOULBOUND_MAX_CLIENTS=100
WORKDIR /app
COPY server.py /app/server.py
COPY core_progression.py /app/
COPY items_loot_dungeons.py /app/
COPY world_content_equipment.py /app/
COPY network_gameplay_systems.py /app/
COPY world_runtime_session.py /app/
COPY server_admin_audits.py /app/
COPY soulbound_world_seed.txt /app/soulbound_world_seed.txt
COPY CHANGELOG_PL.txt /app/CHANGELOG_PL.txt
CMD ["python", "-u", "/app/server.py"]
