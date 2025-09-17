#!/usr/bin/env python3
"""
Quick Share - Creates a temporary public link for your note app
Uses serveo.net for free tunneling
"""

import subprocess
import threading
import time
import webbrowser

def start_serveo_tunnel():
    """Start serveo.net tunnel"""
    try:
        print("🌐 Creating public link...")
        print("⏳ This may take a few seconds...")
        
        # Start serveo tunnel
        result = subprocess.run([
            'ssh', '-R', '80:localhost:5000', 'serveo.net'
        ], capture_output=True, text=True, timeout=10)
        
        if result.stdout:
            print("✅ Public link created!")
            print(result.stdout)
        
    except subprocess.TimeoutExpired:
        print("⏰ Tunnel setup taking longer than expected...")
        print("📱 Try the other options below")
    except FileNotFoundError:
        print("❌ SSH not available. Try other options below.")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_options():
    """Show all available options"""
    print("\n" + "="*60)
    print("📱 PHONE ACCESS OPTIONS")
    print("="*60)
    
    print("\n🔥 OPTION 1: Phone Hotspot (Easiest)")
    print("1. Turn on your phone's WiFi hotspot")
    print("2. Connect this computer to your phone's hotspot")
    print("3. Open http://localhost:5000 on your phone")
    
    print("\n🌐 OPTION 2: Free Cloud Hosting")
    print("Deploy to Railway.app or Render.com:")
    print("1. Sign up at railway.app (free tier)")
    print("2. Connect your GitHub repository")
    print("3. Deploy - get a permanent public URL")
    
    print("\n🔗 OPTION 3: Temporary Public Link")
    print("1. Install ngrok: https://ngrok.com/download")
    print("2. Run: ngrok http 5000")
    print("3. Use the https://xxxx.ngrok.io URL on your phone")
    
    print("\n📡 OPTION 4: Local Network Bridge")
    print("1. Use TeamViewer or similar to access this computer")
    print("2. Open localhost:5000 through the remote connection")
    
    print("\n🏠 OPTION 5: Router Port Forwarding")
    print("1. Access your router settings (usually 192.168.1.1)")
    print("2. Forward port 5000 to this computer")
    print("3. Use your public IP address")
    
    print("\n" + "="*60)
    print("🎯 RECOMMENDED: Try Option 1 (Phone Hotspot) first!")
    print("="*60)

if __name__ == "__main__":
    print("🚀 Setting up phone access for your note app...")
    
    # Try to create a serveo tunnel
    start_serveo_tunnel()
    
    # Show all options
    show_options()
    
    print("\n✨ Your note app is still running at http://localhost:5000")
    print("🔧 Choose the option that works best for you!")