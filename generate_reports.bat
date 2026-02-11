@echo off
echo ===================================================
echo 📊 FJC PIZZA ANALYTICS ENGINE
echo ===================================================
echo.

echo 🏗️  Step 1: Applying Database Migrations...
python manage.py migrate
if %errorlevel% neq 0 (
    echo ❌ Migration failed. Please check your database connection.
    pause
    exit /b %errorlevel%
)

echo.
echo 🌱 Step 2: Seeding 90-Day Historical Data...
python manage.py seed_comprehensive_90days --days 90 --verbose
if %errorlevel% neq 0 (
    echo ❌ Seeding failed.
    pause
    exit /b %errorlevel%
)

echo.
echo 🚀 Step 3: Exporting Data for Power BI...
python manage.py export_bi_data --output-dir bi_exports
if %errorlevel% neq 0 (
    echo ❌ Export failed.
    pause
    exit /b %errorlevel%
)

echo.
echo ===================================================
echo ✅ SUCCESS! CSV reports are ready in 'bi_exports' folder.
echo You can now import these into Power BI.
echo ===================================================
pause
