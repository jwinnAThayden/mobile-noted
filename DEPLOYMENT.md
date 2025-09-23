# 🚀 Mobile Noted Deployment Guide

This directory contains automated deployment scripts for the Mobile Noted app on Railway.

## 📁 Deployment Files

- **`deploy.ps1`** - PowerShell deployment script (Windows)
- **`deploy.bat`** - Batch file deployment script (Windows)
- **`PowerShellDeployment.ps1`** - PowerShell profile functions for easy access

## 🎯 Quick Deploy

### Option 1: PowerShell Script (Recommended)
```powershell
.\deploy.ps1 "Your commit message"
```

### Option 2: Batch File
```cmd
deploy.bat "Your commit message"
```

### Option 3: Manual Commands
```bash
git add .
git commit -m "Your message"
git push origin master
```

## 🔧 Setup Railway CLI (Optional)

The Railway CLI is installed but requires project linking:

```powershell
# Already installed via npm
railway --version

# Login (already done)
railway login

# Link to project (if needed)
railway link

# Manual redeploy
railway redeploy
```

## 🌐 App URLs

- **Production:** https://mobile-noted-production.up.railway.app
- **Health Check:** https://mobile-noted-production.up.railway.app/health

## ⚡ How It Works

1. **Git Push:** Changes are pushed to GitHub repository
2. **Auto Deploy:** Railway automatically deploys from GitHub integration
3. **Verification:** Scripts check deployment health
4. **Notification:** Success/failure feedback provided

## 🎨 Recent Fixes

- ✅ Fixed OneDrive device flow display (duplicate ID issue)
- ✅ Enhanced UI with clickable links and copy buttons  
- ✅ Added deployment automation scripts
- ✅ Improved authentication flow user experience

## 💡 Tips

- Railway typically deploys within 1-2 minutes after git push
- Use descriptive commit messages for better tracking
- Check Railway dashboard for detailed deployment logs
- The health endpoint confirms deployment success

## 🐛 Troubleshooting

If deployment fails:
1. Check Railway dashboard for error logs
2. Verify GitHub integration is active
3. Ensure all required environment variables are set
4. Try manual redeploy via Railway dashboard

## 📱 Testing Deployments

After deployment, test these features:
- OneDrive authentication flow
- Device code display and copy functionality
- File sync operations
- UI responsiveness on mobile/desktop