FROM python:3.12-slim AS verified
ENV PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /candidate
# Validate the actual current sources, then prepare a new empty installation.
# No older release image, installation, activation marker or database is used.
COPY . /candidate
RUN python -m systems.current_install install --target /app

FROM python:3.12-slim
ENV PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
ENV SOULBOUND_HOST=0.0.0.0 SOULBOUND_MAX_CLIENTS=100
WORKDIR /app
COPY --from=verified /app /app
EXPOSE 4000
CMD ["python", "-u", "/app/server.py"]
