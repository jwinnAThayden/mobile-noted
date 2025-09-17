# 🔧 Railway Deployment Troubleshooting Guide

## 🚨 **Current Issue**: App fails to start even with environment variables set

The error `ValueError: NOTED_USERNAME environment variable must be set` suggests Railway isn't seeing your environment variables.

## 📋 **Troubleshooting Checklist**

### **1. Verify Environment Variables in Railway**
Go to your Railway project dashboard and check:

**✅ Variables Tab:**
- [ ] `NOTED_USERNAME` is present and has a value
- [ ] `NOTED_PASSWORD_HASH` is present and has the full hash
- [ ] No extra spaces in variable names
- [ ] No quotes around the values (Railway adds them automatically)

**Expected values:**
```
NOTED_USERNAME=your_username_here
NOTED_PASSWORD_HASH=scrypt:32768:8:1$xCdI78FIddf2Mg8Z$77585afd34f0bd3786e0fa22c99d5372b8e68c0c67b155997cc31fb328aad90cc28c9c121808b79bd509b74117b94118b4a7cfb4d2458b9dcad6d67f4f609820
```

### **2. Check Railway Deployment Logs**
In Railway dashboard:
- [ ] Go to **Deployments** tab
- [ ] Click on the latest failed deployment
- [ ] Look for any error messages before the environment variable error
- [ ] Check if there are any dependency installation issues

### **3. Verify Railway Service Configuration**
- [ ] Ensure Railway is pointing to the correct repository branch (`master`)
- [ ] Check that the root directory is correct (where `web-mobile-noted.py` is located)
- [ ] Verify the start command is correct (should be automatic with `Procfile`)

### **4. Check Procfile**
Verify your `Procfile` exists and contains:
```
web: gunicorn --bind 0.0.0.0:$PORT web-mobile-noted:app
```

### **5. Common Railway Issues**

#### **Issue A: Variables Not Applied**
**Solution**: After adding variables, manually trigger a redeploy:
- Go to **Deployments** tab
- Click **"Deploy Latest"** or **"Redeploy"**

#### **Issue B: Variable Names Incorrect**
**Check for typos:**
- `NOTED_USERNAME` (not `NOTED_USER` or `USERNAME`)
- `NOTED_PASSWORD_HASH` (not `PASSWORD_HASH` or `NOTED_PASSWORD`)

#### **Issue C: Hash Value Truncated**
**Ensure the full hash is copied:**
- Password hash should be very long (200+ characters)
- Starts with `scrypt:32768:8:1$`
- No line breaks or truncation

#### **Issue D: Railway Cache**
**Force a clean deployment:**
- Delete the service and recreate it, or
- Push a small change to trigger fresh deployment

## 🔧 **Quick Fixes to Try**

### **Fix 1: Force Railway Refresh**
1. Go to Railway dashboard
2. **Settings** → **Danger Zone**
3. Click **"Restart"** (not delete!)

### **Fix 2: Add a Dummy Variable**
Add a test variable to force Railway to refresh:
```
TEST_VAR=hello
```
Then remove it after deployment works.

### **Fix 3: Verify Variable Format**
Make sure variables look exactly like this in Railway:
```
Variable Name: NOTED_USERNAME
Variable Value: myusername

Variable Name: NOTED_PASSWORD_HASH  
Variable Value: scrypt:32768:8:1$xCdI78FIddf2Mg8Z$77585afd34f0bd3786e0fa22c99d5372b8e68c0c67b155997cc31fb328aad90cc28c9c121808b79bd509b74117b94118b4a7cfb4d2458b9dcad6d67f4f609820
```

## 🚨 **If Still Not Working**

### **Temporary Fallback (for testing only)**
If you need to test the deployment quickly, you can temporarily add fallback values:

**⚠️ ONLY for testing - not secure for production!**

```python
# Temporary fallback - REMOVE after testing
USERNAME = os.environ.get('NOTED_USERNAME') or 'testuser'
PASSWORD_HASH = os.environ.get('NOTED_PASSWORD_HASH') or generate_password_hash('testpass123')
```

**Login would be:**
- Username: `testuser`
- Password: `testpass123`

**🔒 Remember to remove this and use proper environment variables for production!**

## 📞 **Next Steps**

1. **Check all items in the checklist above**
2. **Try Fix 1-3 in order**
3. **Share screenshots of your Railway Variables tab if still having issues**
4. **Check Railway deployment logs for any other error messages**

Railway environment variables should work - this is a common configuration issue that's usually easy to fix once we identify the specific problem! 🚀