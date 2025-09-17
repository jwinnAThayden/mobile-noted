# 🔐 Authentication Setup Guide - Web Mobile Noted

## 🚨 **IMPORTANT: Required Setup**

Your Web Mobile Noted app now requires authentication credentials to be set via **environment variables** for security. No credentials are stored in the code.

## 🛠️ **Required Environment Variables**

### **NOTED_USERNAME**
- Your chosen username for accessing the app
- Example: `mynotes_user`

### **NOTED_PASSWORD_HASH**
- Secure hash of your password (not the password itself)
- Generated using Werkzeug's `generate_password_hash()` function

## 🚀 **Quick Setup Methods**

### **Method 1: Generate Hash Locally**

1. **Run the password generator**:
   ```bash
   python generate_password.py
   ```

2. **Copy the output** and add to Railway environment variables

### **Method 2: Manual Hash Generation**

```bash
python -c "from werkzeug.security import generate_password_hash; print('Your hash:', generate_password_hash('YourSecurePassword123'))"
```

### **Method 3: Interactive Python Session**

```python
from werkzeug.security import generate_password_hash

# Replace with your desired password
password = "YourSecurePassword123"
hash_value = generate_password_hash(password)
print(f"NOTED_PASSWORD_HASH={hash_value}")
```

## 🌐 **Railway Deployment Setup**

### **Step 1: Generate Your Credentials**
Use any method above to generate your password hash.

### **Step 2: Set Environment Variables in Railway**
1. Go to your **Railway Project Dashboard**
2. Click **"Variables"** tab
3. Add these variables:
   ```
   NOTED_USERNAME=your_chosen_username
   NOTED_PASSWORD_HASH=your_generated_hash_here
   ```

### **Step 3: Deploy**
Railway will automatically redeploy with your secure credentials.

## 💻 **Local Development Setup**

### **Option 1: Environment Variables**
```bash
# Windows (PowerShell)
$env:NOTED_USERNAME="your_username"
$env:NOTED_PASSWORD_HASH="your_generated_hash"
python web-mobile-noted.py

# Linux/Mac
export NOTED_USERNAME="your_username"
export NOTED_PASSWORD_HASH="your_generated_hash"
python web-mobile-noted.py
```

### **Option 2: .env File** (Create `.env` file)
```bash
NOTED_USERNAME=your_username
NOTED_PASSWORD_HASH=your_generated_hash
```

Then load it in your app (add to top of web-mobile-noted.py):
```python
from dotenv import load_dotenv
load_dotenv()
```

## 🔒 **Security Benefits**

### ✅ **Before (Insecure)**
- Username: `admin` (visible in code)
- Password: `secure123` (visible in code)
- Anyone with access to code knows credentials

### ✅ **After (Secure)**
- No credentials in source code
- Environment variables only
- Each deployment can have unique credentials
- Credentials not visible in repository

## 🛡️ **Best Practices**

### **Password Requirements**
- Minimum 12 characters
- Mix of letters, numbers, symbols
- Avoid common words or patterns

### **Username Requirements**
- No spaces or special characters
- Avoid `admin`, `user`, `root`
- Use something unique to you

### **Environment Variable Security**
- Never commit `.env` files to git
- Use different credentials for dev/prod
- Rotate credentials periodically

## 🚨 **Error Handling**

### **Missing Environment Variables**
If you see these errors:
```
ValueError: NOTED_USERNAME environment variable must be set
ValueError: NOTED_PASSWORD_HASH environment variable must be set
```

**Solution**: Set the required environment variables using the methods above.

### **Invalid Password Hash**
If login fails with correct password:
- Regenerate the password hash
- Ensure no extra spaces in environment variables
- Verify the hash was copied completely

## 📋 **Example Complete Setup**

```bash
# 1. Generate hash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('MySecurePassword123!'))"

# Output: scrypt:32768:8:1$abc123...xyz789

# 2. Set Railway variables:
NOTED_USERNAME=johnnotes
NOTED_PASSWORD_HASH=scrypt:32768:8:1$abc123...xyz789

# 3. Deploy and test login with:
#    Username: johnnotes
#    Password: MySecurePassword123!
```

## 🎯 **Quick Test**

After setting up:
1. **Deploy to Railway**
2. **Visit your app URL**
3. **Login with your credentials**
4. **✅ Success!** No more hardcoded passwords

Your app is now production-ready with secure authentication! 🚀