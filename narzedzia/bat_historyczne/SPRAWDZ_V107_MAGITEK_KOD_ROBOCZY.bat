@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0..\..\"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONDONTWRITEBYTECODE=1"
set "SOULBOUND_V107_STAGING=1"
where py >nul 2>&1
if not errorlevel 1 (
  py -3 -B -m validation.v10700_consolidated_content_regression
  if errorlevel 1 goto fail
  py -3 -B -m validation.v10700_magitek_regression
  if errorlevel 1 goto fail
  py -3 -B -m validation.v10700_magitek_support_regression
  if errorlevel 1 goto fail
  py -3 -B -m validation.v10700_magitek_magicite_regression
  if errorlevel 1 goto fail
  py -3 -B -m validation.v10700_magitek_diffuser_regression
  if errorlevel 1 goto fail
  py -3 -B -m validation.v10700_magitek_target_router_regression
  if errorlevel 1 goto fail
  py -3 -B -m validation.v10700_no_raids_regression
  if errorlevel 1 goto fail
  py -3 -B -m validation.v10700_no_raids_regression --with-v106
  if errorlevel 1 goto fail
  py -3 -B -m validation.v10700_raid_character_rescue_regression
  if errorlevel 1 goto fail
  py -3 -B -m validation.v10700_insects_expansion_regression
  if errorlevel 1 goto fail
  py -3 -B -m validation.v10700_insects_quest_sqlite_regression
  if errorlevel 1 goto fail
  py -3 -B -m validation.v10700_insects_plus_regression
  if errorlevel 1 goto fail
  py -3 -B -m validation.v10700_insects_plus_sqlite_regression
  if errorlevel 1 goto fail
  py -3 -B -m validation.v10700_chaos_chapter_one_regression
  if errorlevel 1 goto fail
  py -3 -B -m validation.v10700_chaos_chapter_one_sqlite_regression
  if errorlevel 1 goto fail
  py -3 -B -m validation.v10700_chaos_30_realms_regression
  if errorlevel 1 goto fail
  py -3 -B -m validation.v10700_chaos_30_realms_sqlite_regression
  if errorlevel 1 goto fail
) else (
  python -B -m validation.v10700_consolidated_content_regression
  if errorlevel 1 goto fail
  python -B -m validation.v10700_magitek_regression
  if errorlevel 1 goto fail
  python -B -m validation.v10700_magitek_support_regression
  if errorlevel 1 goto fail
  python -B -m validation.v10700_magitek_magicite_regression
  if errorlevel 1 goto fail
  python -B -m validation.v10700_magitek_diffuser_regression
  if errorlevel 1 goto fail
  python -B -m validation.v10700_magitek_target_router_regression
  if errorlevel 1 goto fail
  python -B -m validation.v10700_no_raids_regression
  if errorlevel 1 goto fail
  python -B -m validation.v10700_no_raids_regression --with-v106
  if errorlevel 1 goto fail
  python -B -m validation.v10700_raid_character_rescue_regression
  if errorlevel 1 goto fail
  python -B -m validation.v10700_insects_expansion_regression
  if errorlevel 1 goto fail
  python -B -m validation.v10700_insects_quest_sqlite_regression
  if errorlevel 1 goto fail
  python -B -m validation.v10700_insects_plus_regression
  if errorlevel 1 goto fail
  python -B -m validation.v10700_insects_plus_sqlite_regression
  if errorlevel 1 goto fail
  python -B -m validation.v10700_chaos_chapter_one_regression
  if errorlevel 1 goto fail
  python -B -m validation.v10700_chaos_chapter_one_sqlite_regression
  if errorlevel 1 goto fail
  python -B -m validation.v10700_chaos_30_realms_regression
  if errorlevel 1 goto fail
  python -B -m validation.v10700_chaos_30_realms_sqlite_regression
  if errorlevel 1 goto fail
)
echo.
echo V107 ZBIORCZE TESTY KODU: PASS
pause
exit /b 0
:fail
echo.
echo V107 ZBIORCZE TESTY KODU: FAIL
pause
exit /b 1
