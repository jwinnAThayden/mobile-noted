@echo off
REM Simple deployment script for Mobile Noted
REM Usage: deploy.bat "Your commit message"

echo 🚀 Starting deployment process...

REM Check if commit message provided, otherwise use default
if "%~1"=="" (
    set COMMIT_MSG=Update mobile noted app
) else (
    set COMMIT_MSG=%~1
)

echo 📝 Using commit message: %COMMIT_MSG%

REM Add and commit changes
echo ⏳ Adding changes...
git add .

echo ⏳ Committing changes...
git commit -m "%COMMIT_MSG%"

if %errorlevel% neq 0 (
    echo ℹ️  No changes to commit or commit failed
)

echo ⬆️  Pushing to GitHub...
git push origin master

if %errorlevel% equ 0 (
    echo ✅ Successfully pushed to GitHub!
    echo ⏳ Railway will automatically deploy from GitHub...
    echo 🌐 Your app: https://mobile-noted-production.up.railway.app
    echo 🔧 Deployment usually takes 1-2 minutes
) else (
    echo ❌ Failed to push to GitHub
    pause
    exit /b 1
)

echo.
echo 🎉 Deployment initiated!
echo 💡 Tip: Check Railway dashboard for deployment status
pause