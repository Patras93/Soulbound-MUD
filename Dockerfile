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
# Force fresh source snapshot after Railway queued-build race
COPY server.py /app/server.py
COPY core /app/core
# v1.40.3: defend upgrades unpacked over previous source directories.
# A stale file must not enter the runtime even with an old Docker COPY cache.
RUN rm -f /app/core/generator_core.py && test ! -e /app/core/generator_core.py
COPY systems /app/systems
COPY world /app/world
COPY network /app/network
COPY storage /app/storage
COPY player /app/player
COPY server /app/server
COPY admin /app/admin
COPY config /app/config
COPY data /app/data
COPY events /app/events
COPY validation /app/validation
# soulbound_world_seed.txt is persistent user data, not a release artifact.
# It is loaded or created next to SOULBOUND_DB at runtime.
COPY CHANGELOG_PL.txt /app/CHANGELOG_PL.txt
COPY predeploy_check.py /app/predeploy_check.py
COPY predeploy_full.py /app/predeploy_full.py
# v2.32.4: Railway needs the Windows quality-gate module imported by
# validation/v2102_predeploy_contract.py and v2302_coverage_contract.py.
COPY testuj_soulbound_windows.py /app/testuj_soulbound_windows.py
COPY Dockerfile /app/Dockerfile
# v1.60.5: Testujemy pliki START/STOP w czasie budowania, chociaz Linux ich nie uruchamia.
# Bez tego v1.60.4 mial FileNotFoundError: /app/START_Soulbound.bat.
COPY START_Soulbound.bat START_Soulbound_UKRYTY.vbs Start-Soulbound-Windows.bat STOP_Soulbound.bat host_windows.py /app/
COPY uruchom_w_tle.py windows_launcher_state.py windows_runtime_state.py stop_soulbound_windows.py aktualizuj_soulbound.py /app/
RUN python /app/predeploy_check.py \
    && python /app/predeploy_full.py \
    && rm -f /app/predeploy_check.py /app/predeploy_full.py /app/Dockerfile \
       /app/START_Soulbound.bat /app/START_Soulbound_UKRYTY.vbs \
       /app/Start-Soulbound-Windows.bat /app/STOP_Soulbound.bat /app/host_windows.py \
       /app/uruchom_w_tle.py /app/windows_launcher_state.py \
       /app/stop_soulbound_windows.py /app/aktualizuj_soulbound.py \
       /app/testuj_soulbound_windows.py
CMD ["python", "-u", "/app/server.py"]
