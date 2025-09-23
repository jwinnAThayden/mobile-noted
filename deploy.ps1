# Railway Deployment Script for Mobile Noted
# This script handles git commits, pushes, and triggers Railway deployment

param(
    [string]$CommitMessage = "Update mobile noted app"
)

Write-Host "🚀 Starting deployment process..." -ForegroundColor Green

# Check if there are any changes to commit
$gitStatus = git status --porcelain
if (-not $gitStatus) {
    Write-Host "ℹ️  No changes to commit. Checking Railway deployment status..." -ForegroundColor Yellow
} else {
    Write-Host "📝 Changes detected. Committing and pushing..." -ForegroundColor Cyan
    
    # Add all changes
    git add .
    
    # Commit with provided message or default
    git commit -m $CommitMessage
    
    # Push to origin
    Write-Host "⬆️  Pushing to GitHub..." -ForegroundColor Blue
    git push origin master
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to push to GitHub" -ForegroundColor Red
        exit 1
    }
}

# Check Railway deployment
Write-Host "🔍 Checking Railway deployment status..." -ForegroundColor Cyan

# Try to get Railway status
try {
    $railwayStatus = railway status 2>&1
    if ($railwayStatus -like "*No linked project*") {
        Write-Host "⚠️  Project not linked to Railway CLI" -ForegroundColor Yellow
        Write-Host "💡 Attempting to trigger deployment via Railway API..." -ForegroundColor Cyan
        
        # Since automatic deployment should happen via GitHub integration,
        # we'll check the deployment URL after a short wait
        Write-Host "⏳ Waiting for automatic Railway deployment (GitHub integration)..." -ForegroundColor Cyan
        Start-Sleep 10
        
        # Test the deployment URL
        $deploymentUrl = "https://mobile-noted-production.up.railway.app"
        try {
            $response = Invoke-WebRequest -Uri "$deploymentUrl/health" -TimeoutSec 10 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ Railway deployment is accessible!" -ForegroundColor Green
                Write-Host "🌐 App URL: $deploymentUrl" -ForegroundColor Blue
            }
        } catch {
            Write-Host "⚠️  Deployment may still be in progress. Please check Railway dashboard." -ForegroundColor Yellow
        }
    } else {
        Write-Host "🔗 Railway project linked. Checking deployment..." -ForegroundColor Green
        railway status
        
        # Try to redeploy if linked
        Write-Host "🔄 Triggering Railway redeploy..." -ForegroundColor Cyan
        railway redeploy
    }
} catch {
    Write-Host "⚠️  Railway CLI command failed. Using fallback method..." -ForegroundColor Yellow
}

Write-Host "`n🎉 Deployment process completed!" -ForegroundColor Green
Write-Host "📱 Check your app at: https://mobile-noted-production.up.railway.app" -ForegroundColor Blue
Write-Host "🔧 If deployment is still in progress, wait 2-3 minutes and refresh." -ForegroundColor Yellow

# Optional: Open the app in browser
$openBrowser = Read-Host "Open app in browser? (y/N)"
if ($openBrowser -eq 'y' -or $openBrowser -eq 'Y') {
    Start-Process "https://mobile-noted-production.up.railway.app"
}