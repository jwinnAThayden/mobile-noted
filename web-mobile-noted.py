#!/usr/bin/env python3
"""
Web Mobile Noted - Browser-based note-taking app
Works on desktop and mobile browsers, easier to deploy than native Android
Now with comprehensive security protection
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for, flash, make_response
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, validate_csrf, CSRFError, generate_csrf
from werkzeug.security import check_password_hash, generate_password_hash
import json
import os
import sys
import uuid
import time
import re
from datetime import datetime, timedelta
import logging
from functools import wraps
import secrets
import hashlib
from dateutil import parser

# OneDrive integration
try:
    from onedrive_web_manager import WebOneDriveManager
    ONEDRIVE_AVAILABLE = True
except ImportError as e:
    print(f"OneDrive integration unavailable: {e}")  # Will use proper logger after it's defined
    ONEDRIVE_AVAILABLE = False

app = Flask(__name__)

# Security Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True  # Make sessions persistent
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # 30 days to match device trust duration
app.config['SESSION_FILE_THRESHOLD'] = 100
app.config['WTF_CSRF_TIME_LIMIT'] = 3600

# Authentication Configuration - Optional for Railway deployment
USERNAME = os.environ.get('NOTED_USERNAME')
PASSWORD_HASH = os.environ.get('NOTED_PASSWORD_HASH')

# Authentication is optional - if not set, app runs without authentication
AUTH_ENABLED = USERNAME and PASSWORD_HASH
if not AUTH_ENABLED:
    print("INFO: Authentication disabled - NOTED_USERNAME and NOTED_PASSWORD_HASH not set")
    print("INFO: Running in open access mode for Railway deployment")

# Configuration
NOTES_DIR = os.path.join(os.path.dirname(__file__), 'web_notes')
TRUSTED_DEVICES_FILE = os.path.join(NOTES_DIR, 'trusted_devices.json')
os.makedirs(NOTES_DIR, exist_ok=True)

# Device trust configuration
DEVICE_TRUST_DURATION = int(os.environ.get('DEVICE_TRUST_DAYS', 30))  # Days to trust device
DEVICE_COOKIE_NAME = 'noted_device_id'

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper function for conditional CSRF validation
def validate_csrf_if_enabled(csrf_token):
    """Only validate CSRF if authentication is enabled"""
    if AUTH_ENABLED:
        validate_csrf(csrf_token)

# Initialize security extensions after logger setup
Session(app)
if AUTH_ENABLED:
    csrf = CSRFProtect(app)
    logger.info("🛡️  CSRF protection enabled")
else:
    csrf = None
    logger.info("⚠️  CSRF protection disabled (no authentication)")
    
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["100 per hour", "20 per minute"]
)

# Initialize OneDrive Manager
onedrive_manager = None
onedrive_error_message = None

if ONEDRIVE_AVAILABLE and 'WebOneDriveManager' in globals():
    try:
        onedrive_manager = WebOneDriveManager()
        logger.info("✅ OneDrive manager initialized successfully")
    except Exception as e:
        onedrive_error_message = str(e)
        logger.warning(f"⚠️  OneDrive integration disabled: {e}")
        if "NOTED_CLIENT_ID" in str(e):
            logger.info("💡 To enable OneDrive: Set NOTED_CLIENT_ID environment variable with your Azure App Registration Client ID")
        ONEDRIVE_AVAILABLE = False
else:
    logger.info("⚠️  OneDrive integration not available (import failed)")
    onedrive_error_message = "OneDrive dependencies not installed"

# Create session directory in a Railway-compatible location (after logger is defined)
session_dir = os.path.join(os.path.dirname(__file__), 'flask_session')
try:
    os.makedirs(session_dir, exist_ok=True)
    app.config['SESSION_FILE_DIR'] = session_dir
    logger.info(f"Session directory created: {session_dir}")
except Exception as e:
    logger.warning(f"Could not create session directory, using default: {e}")
    # Railway will use /tmp if we can't create our own directory

# Device Trust System
def generate_device_fingerprint():
    """Generate a device fingerprint based on request headers and IP"""
    # Collect device information
    user_agent = request.headers.get('User-Agent', '')
    accept_language = request.headers.get('Accept-Language', '')
    accept_encoding = request.headers.get('Accept-Encoding', '')
    remote_addr = get_remote_address()
    
    # Create fingerprint
    fingerprint_data = f"{user_agent}|{accept_language}|{accept_encoding}|{remote_addr}"
    fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()
    
    return fingerprint_hash

def get_device_id():
    """Get or create a unique device ID"""
    device_id = request.cookies.get(DEVICE_COOKIE_NAME)
    if not device_id:
        device_id = str(uuid.uuid4())
    return device_id

def load_trusted_devices():
    """Load trusted devices from JSON file"""
    try:
        if os.path.exists(TRUSTED_DEVICES_FILE):
            with open(TRUSTED_DEVICES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading trusted devices: {e}")
    return {}

def save_trusted_devices(devices):
    """Save trusted devices to JSON file"""
    try:
        with open(TRUSTED_DEVICES_FILE, 'w', encoding='utf-8') as f:
            json.dump(devices, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving trusted devices: {e}")
        return False

def is_device_trusted():
    """Check if current device is trusted"""
    device_id = get_device_id()
    fingerprint = generate_device_fingerprint()
    
    trusted_devices = load_trusted_devices()
    
    # First check if device is in trusted devices file
    for device_data in trusted_devices.values():
        if (device_data.get('device_id') == device_id and 
            device_data.get('fingerprint') == fingerprint):
            
            # Check if trust hasn't expired
            trust_expiry = parser.parse(device_data.get('expires_at'))
            if datetime.now() < trust_expiry:
                return True
            else:
                # Remove expired trust
                remove_device_trust(device_id)
    
    # Railway fallback: If trusted_devices.json is empty/missing but we have a device cookie,
    # check if the cookie seems recent (was set in the browser)
    # This handles Railway container restarts where filesystem is lost
    if not trusted_devices and device_id and request.cookies.get(DEVICE_COOKIE_NAME):
        # If we have a device cookie but no trusted devices file (likely Railway restart),
        # we'll temporarily trust the device. This gives users a grace period after restarts.
        logger.info(f"Railway fallback: Temporarily trusting device with valid cookie: {device_id[:8]}...")
        
        # Auto-recreate the trust entry for this session
        try:
            add_device_trust("Auto-recovered device")
            return True
        except Exception as e:
            logger.error(f"Failed to auto-recover device trust: {e}")
    
    return False

def add_device_trust(device_name=None):
    """Add current device to trusted devices"""
    device_id = get_device_id()
    fingerprint = generate_device_fingerprint()
    
    # Generate device info
    user_agent = request.headers.get('User-Agent', 'Unknown Device')
    device_info = parse_user_agent(user_agent)
    
    if not device_name:
        device_name = f"{device_info['browser']} on {device_info['os']}"
    
    trust_data = {
        'device_id': device_id,
        'fingerprint': fingerprint,
        'name': device_name,
        'user_agent': user_agent,
        'ip_address': get_remote_address(),
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(days=DEVICE_TRUST_DURATION)).isoformat(),
        'last_used': datetime.now().isoformat()
    }
    
    trusted_devices = load_trusted_devices()
    trust_key = f"{device_id}_{fingerprint[:8]}"
    trusted_devices[trust_key] = trust_data
    
    # Clean up expired devices while we're here
    cleanup_expired_devices(trusted_devices)
    
    save_trusted_devices(trusted_devices)
    logger.info(f"Added trusted device: {device_name}")
    return device_id

def remove_device_trust(device_id):
    """Remove device trust"""
    trusted_devices = load_trusted_devices()
    
    # Find and remove device
    keys_to_remove = []
    for key, device_data in trusted_devices.items():
        if device_data.get('device_id') == device_id:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del trusted_devices[key]
        logger.info(f"Removed trusted device: {key}")
    
    save_trusted_devices(trusted_devices)

def cleanup_expired_devices(devices_dict=None):
    """Remove expired trusted devices"""
    if devices_dict is None:
        devices_dict = load_trusted_devices()
    
    current_time = datetime.now()
    expired_keys = []
    
    for key, device_data in devices_dict.items():
        try:
            expires_at = parser.parse(device_data.get('expires_at'))
            if current_time >= expires_at:
                expired_keys.append(key)
        except Exception:
            # Remove malformed entries
            expired_keys.append(key)
    
    for key in expired_keys:
        del devices_dict[key]
    
    if expired_keys:
        save_trusted_devices(devices_dict)
        logger.info(f"Cleaned up {len(expired_keys)} expired trusted devices")

def parse_user_agent(user_agent):
    """Simple user agent parsing for device identification"""
    ua = user_agent.lower()
    
    # Detect OS
    if 'windows' in ua:
        os_name = 'Windows'
    elif 'mac' in ua or 'darwin' in ua:
        os_name = 'macOS'
    elif 'linux' in ua:
        os_name = 'Linux'
    elif 'android' in ua:
        os_name = 'Android'
    elif 'iphone' in ua or 'ipad' in ua:
        os_name = 'iOS'
    else:
        os_name = 'Unknown'
    
    # Detect browser
    if 'chrome' in ua and 'edg' not in ua:
        browser = 'Chrome'
    elif 'firefox' in ua:
        browser = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
    elif 'edg' in ua:
        browser = 'Edge'
    else:
        browser = 'Unknown'
    
    return {'os': os_name, 'browser': browser}

def update_device_last_used(device_id):
    """Update last used timestamp for trusted device"""
    trusted_devices = load_trusted_devices()
    
    for device_data in trusted_devices.values():
        if device_data.get('device_id') == device_id:
            device_data['last_used'] = datetime.now().isoformat()
            save_trusted_devices(trusted_devices)
            break

# Security headers middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response

# Authentication decorator
def login_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip authentication if not enabled
        if not AUTH_ENABLED:
            return f(*args, **kwargs)
            
        # Check if user is already authenticated
        if session.get('authenticated'):
            return f(*args, **kwargs)
        
        # Check if device is trusted
        if is_device_trusted():
            # Auto-login trusted device
            device_id = get_device_id()
            session['authenticated'] = True
            session['username'] = USERNAME
            session['trusted_device'] = True
            session['device_id'] = device_id
            session.permanent = True
            
            # Update last used timestamp
            update_device_last_used(device_id)
            
            logger.info(f"Auto-login from trusted device: {device_id}")
            return f(*args, **kwargs)
        
        # Redirect to login if not authenticated or trusted
        if request.is_json:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return redirect(url_for('login'))
    return decorated_function

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
def login():
    """Login page and authentication"""
    # If authentication is disabled, redirect to main app
    if not AUTH_ENABLED:
        return redirect(url_for('index'))
        
    if session.get('authenticated'):
        return redirect(url_for('index'))
    
    # Check for trusted device on GET request
    if request.method == 'GET' and is_device_trusted():
        device_id = get_device_id()
        session['authenticated'] = True
        session['username'] = USERNAME
        session['trusted_device'] = True
        session['device_id'] = device_id
        session.permanent = True
        
        update_device_last_used(device_id)
        logger.info(f"Auto-login from trusted device on login page: {device_id}")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            username = data.get('username', '').strip()
            password = data.get('password', '')
            remember_device = data.get('remember_device', False)
            
            if username == USERNAME and PASSWORD_HASH and check_password_hash(PASSWORD_HASH, password):
                # Set session
                session['authenticated'] = True
                session['username'] = username
                session.permanent = True
                
                device_id = get_device_id()
                
                # Handle device trust
                if remember_device:
                    device_id = add_device_trust()
                    session['trusted_device'] = True
                    session['device_id'] = device_id
                    flash('Device has been remembered for 30 days', 'success')
                
                logger.info(f"Successful login from {get_remote_address()}")
                
                # Set device cookie
                response_data = {'success': True, 'redirect': url_for('index')} if request.is_json else redirect(url_for('index'))
                
                if request.is_json:
                    response = make_response(jsonify(response_data))
                else:
                    response = make_response(response_data)
                
                # Set device ID cookie (30 days)
                response.set_cookie(
                    DEVICE_COOKIE_NAME, 
                    device_id, 
                    max_age=30*24*60*60,  # 30 days
                    secure=request.is_secure,
                    httponly=True,
                    samesite='Lax'
                )
                
                return response
            else:
                logger.warning(f"Failed login attempt from {get_remote_address()}")
                error_msg = 'Invalid username or password'
                
                if request.is_json:
                    return jsonify({'success': False, 'error': error_msg}), 401
                flash(error_msg, 'error')
        
        except Exception as e:
            logger.error(f"Login error: {e}")
            error_msg = 'Login error occurred'
            
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 500
            flash(error_msg, 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

# Device Management Routes
@app.route('/devices')
@login_required
def manage_devices():
    """Device management page"""
    trusted_devices = load_trusted_devices()
    current_device_id = session.get('device_id') or get_device_id()
    
    # Clean up expired devices
    cleanup_expired_devices(trusted_devices)
    
    # Prepare device list for display
    devices_list = []
    for key, device_data in trusted_devices.items():
        device_data['key'] = key
        device_data['is_current'] = device_data.get('device_id') == current_device_id
        devices_list.append(device_data)
    
    # Sort by last used (most recent first)
    devices_list.sort(key=lambda x: x.get('last_used', ''), reverse=True)
    
    return render_template('devices.html', devices=devices_list, current_device_id=current_device_id)

@app.route('/api/devices', methods=['GET'])
@login_required
def get_trusted_devices():
    """Get list of trusted devices"""
    try:
        trusted_devices = load_trusted_devices()
        current_device_id = session.get('device_id') or get_device_id()
        
        cleanup_expired_devices(trusted_devices)
        
        devices_list = []
        for key, device_data in trusted_devices.items():
            device_info = {
                'key': key,
                'name': device_data.get('name', 'Unknown Device'),
                'created_at': device_data.get('created_at'),
                'last_used': device_data.get('last_used'),
                'expires_at': device_data.get('expires_at'),
                'ip_address': device_data.get('ip_address'),
                'is_current': device_data.get('device_id') == current_device_id
            }
            devices_list.append(device_info)
        
        devices_list.sort(key=lambda x: x.get('last_used', ''), reverse=True)
        
        return jsonify({'success': True, 'devices': devices_list})
    except Exception as e:
        logger.error(f"Error getting trusted devices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/devices/<device_key>', methods=['DELETE'])
@login_required
@limiter.limit("10 per minute")
def remove_trusted_device(device_key):
    """Remove a trusted device"""
    try:
        validate_csrf_if_enabled(request.headers.get('X-CSRFToken'))
        
        trusted_devices = load_trusted_devices()
        
        if device_key not in trusted_devices:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        device_name = trusted_devices[device_key].get('name', 'Unknown Device')
        del trusted_devices[device_key]
        save_trusted_devices(trusted_devices)
        
        logger.info(f"Removed trusted device: {device_name}")
        return jsonify({'success': True, 'message': f'Removed device: {device_name}'})
        
    except Exception as e:
        logger.error(f"Error removing trusted device: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/devices/current/trust', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def trust_current_device():
    """Trust the current device"""
    try:
        validate_csrf_if_enabled(request.headers.get('X-CSRFToken'))
        
        data = request.get_json()
        device_name = data.get('name', '').strip()
        
        device_id = add_device_trust(device_name)
        session['trusted_device'] = True
        session['device_id'] = device_id
        
        # Create response with device cookie for 30-day persistence
        response = make_response(jsonify({'success': True, 'message': 'Device has been trusted for 30 days', 'device_id': device_id}))
        
        # Set device ID cookie (30 days) - this is crucial for persistent trust
        response.set_cookie(
            DEVICE_COOKIE_NAME, 
            device_id, 
            max_age=30*24*60*60,  # 30 days
            secure=request.is_secure,
            httponly=True,
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error trusting current device: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_note_title(text_content):
    """Generate a simple filename-like title to match desktop app behavior"""
    if not text_content or not text_content.strip():
        return "Untitled.txt"
    
    # Get first line and create a simple filename
    first_line = text_content.split('\n')[0].strip()
    if not first_line:
        return "Untitled.txt"
    
    # Extract key words and create simple filename like desktop app
    # Remove special characters but keep letters, numbers, spaces
    clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', first_line)
    # Take first few meaningful words
    words = clean_text.split()
    if not words:
        return "Untitled.txt"
    
    # Create simple filename from first 1-3 words, like desktop app
    title = ""
    if len(words) == 1:
        title = words[0].lower()
    elif len(words) >= 2:
        # Use first word or first two words combined
        title = words[0].lower()
        # Add second word if first is very short
        if len(words[0]) <= 3 and len(words) > 1:
            title += words[1].lower()
    
    if not title:
        return "Untitled.txt"
    
    # Limit length to match desktop app pattern
    if len(title) > 20:
        title = title[:20]
    
    # Add .txt extension like desktop app
    if not title.lower().endswith('.txt'):
        title += '.txt'
    
    return title

def get_notes_file():
    """Get the path to the notes JSON file"""
    return os.path.join(NOTES_DIR, 'notes.json')

def load_notes():
    """Load all notes from JSON file"""
    try:
        notes_file = get_notes_file()
        if os.path.exists(notes_file):
            with open(notes_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading notes: {e}")
    return {}

def save_notes(notes):
    """Save all notes to JSON file"""
    try:
        notes_file = get_notes_file()
        with open(notes_file, 'w', encoding='utf-8') as f:
            json.dump(notes, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving notes: {e}")
        return False

@app.route('/health')
def health_check():
    """Simple health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'app': 'Web Mobile Noted',
        'timestamp': datetime.now().isoformat(),
        'environment': 'production' if (os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PORT')) else 'development'
    })

@app.route('/debug-info')
def debug_info():
    """Debug information endpoint (only for troubleshooting)"""
    if not (os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PORT')):
        return "Debug info only available in production", 403
    
    return jsonify({
        'status': 'running',
        'python_version': sys.version,
        'environment_vars': {
            'PORT': os.environ.get('PORT'),
            'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT'),
            'NOTED_USERNAME': 'SET' if os.environ.get('NOTED_USERNAME') else 'NOT_SET',
            'NOTED_PASSWORD_HASH': 'SET' if os.environ.get('NOTED_PASSWORD_HASH') else 'NOT_SET'
        },
        'session_dir': app.config.get('SESSION_FILE_DIR', 'default'),
        'notes_dir': NOTES_DIR
    })

@app.route('/')
@login_required
def index():
    """Main page with mobile-optimized interface"""
    # Pass CSRF token to template if authentication is enabled
    csrf_token = None
    if AUTH_ENABLED and csrf:
        try:
            csrf_token = generate_csrf()
        except Exception as e:
            logger.warning(f"Could not generate CSRF token: {e}")
    
    return render_template('index.html', csrf_token=csrf_token)

@app.route('/api/notes', methods=['GET'])
@login_required
@limiter.limit("30 per minute")
def get_notes():
    """Get all notes"""
    try:
        notes = load_notes()
        # Convert to list and sort by modified date
        notes_list = []
        for note_id, note_data in notes.items():
            note_data['id'] = note_id
            notes_list.append(note_data)
        
        notes_list.sort(key=lambda x: x.get('modified', ''), reverse=True)
        return jsonify({'success': True, 'notes': notes_list})
    except Exception as e:
        logger.error(f"Error getting notes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notes', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def create_note():
    """Create a new note"""
    try:
        # Validate CSRF for API requests
        validate_csrf_if_enabled(request.headers.get('X-CSRFToken'))
        
        data = request.get_json()
        note_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Generate title from first line of text
        text_content = data.get('text', '')
        title = generate_note_title(text_content)
        
        note_data = {
            'text': text_content,
            'title': title,
            'created': timestamp,
            'modified': timestamp,
            'owner': session.get('username', 'anonymous')
        }
        
        notes = load_notes()
        notes[note_id] = note_data
        
        if save_notes(notes):
            note_data['id'] = note_id
            return jsonify({'success': True, 'note': note_data})
        else:
            return jsonify({'success': False, 'error': 'Failed to save note'}), 500
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notes/<note_id>', methods=['PUT'])
@login_required
@limiter.limit("20 per minute")
def update_note(note_id):
    """Update an existing note"""
    try:
        # Validate CSRF for API requests
        validate_csrf_if_enabled(request.headers.get('X-CSRFToken'))
        
        data = request.get_json()
        notes = load_notes()
        
        if note_id not in notes:
            return jsonify({'success': False, 'error': 'Note not found'}), 404
        
        # Check ownership (optional: remove if you want shared notes)
        if notes[note_id].get('owner') != session.get('username') and session.get('username') != USERNAME:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Update text content
        text_content = data.get('text', notes[note_id]['text'])
        notes[note_id]['text'] = text_content
        
        # Only update title if explicitly provided or if note has no title yet
        if 'title' in data:
            # User provided explicit title
            notes[note_id]['title'] = data['title']
        elif not notes[note_id].get('title'):
            # Note has no title, auto-generate one
            notes[note_id]['title'] = generate_note_title(text_content)
        # Otherwise, preserve existing title
        
        notes[note_id]['modified'] = datetime.now().isoformat()
        
        if save_notes(notes):
            notes[note_id]['id'] = note_id
            return jsonify({'success': True, 'note': notes[note_id]})
        else:
            return jsonify({'success': False, 'error': 'Failed to save note'}), 500
    except Exception as e:
        logger.error(f"Error updating note: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/offline/save', methods=['POST'])
@login_required
@limiter.limit("50 per minute")
def save_offline_notes():
    """Save notes to server for offline sync later"""
    try:
        # Validate CSRF for API requests
        validate_csrf_if_enabled(request.headers.get('X-CSRFToken'))
        
        data = request.get_json()
        offline_notes = data.get('notes', {})
        device_id = data.get('device_id', 'unknown')
        
        # Save to temporary offline storage
        offline_dir = os.path.join(NOTES_DIR, 'offline')
        os.makedirs(offline_dir, exist_ok=True)
        
        offline_file = os.path.join(offline_dir, f'offline_{device_id}.json')
        with open(offline_file, 'w', encoding='utf-8') as f:
            json.dump({
                'notes': offline_notes,
                'device_id': device_id,
                'timestamp': datetime.now().isoformat(),
                'synced': False
            }, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True, 'message': 'Notes saved offline'})
    except Exception as e:
        logger.error(f"Error saving offline notes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/offline/sync', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def sync_offline_notes():
    """Sync offline notes back to main storage and OneDrive"""
    try:
        # Validate CSRF for API requests
        validate_csrf_if_enabled(request.headers.get('X-CSRFToken'))
        
        data = request.get_json()
        device_id = data.get('device_id', 'unknown')
        
        offline_dir = os.path.join(NOTES_DIR, 'offline')
        offline_file = os.path.join(offline_dir, f'offline_{device_id}.json')
        
        if not os.path.exists(offline_file):
            return jsonify({'success': True, 'message': 'No offline notes to sync'})
        
        # Load offline notes
        with open(offline_file, 'r', encoding='utf-8') as f:
            offline_data = json.load(f)
        
        if offline_data.get('synced', False):
            return jsonify({'success': True, 'message': 'Notes already synced'})
        
        # Merge with existing notes
        current_notes = load_notes()
        offline_notes = offline_data.get('notes', {})
        
        # Add or update notes from offline storage
        for note_id, note_data in offline_notes.items():
            if note_id not in current_notes or note_data.get('modified', '') > current_notes.get(note_id, {}).get('modified', ''):
                current_notes[note_id] = note_data
        
        # Save merged notes
        if save_notes(current_notes):
            # Mark as synced
            offline_data['synced'] = True
            offline_data['sync_timestamp'] = datetime.now().isoformat()
            with open(offline_file, 'w', encoding='utf-8') as f:
                json.dump(offline_data, f, indent=2, ensure_ascii=False)
            
            return jsonify({'success': True, 'message': 'Offline notes synced successfully', 'notes': current_notes})
        else:
            return jsonify({'success': False, 'error': 'Failed to save synced notes'}), 500
            
    except Exception as e:
        logger.error(f"Error syncing offline notes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notes/<note_id>/title', methods=['PUT'])
@login_required
@limiter.limit("20 per minute")
def update_note_title(note_id):
    """Update only the title of a note without changing content"""
    try:
        # Validate CSRF for API requests
        validate_csrf_if_enabled(request.headers.get('X-CSRFToken'))
        
        data = request.get_json()
        new_title = data.get('title', '').strip()
        
        if not new_title:
            return jsonify({'success': False, 'error': 'Title cannot be empty'}), 400
            
        notes = load_notes()
        
        if note_id not in notes:
            return jsonify({'success': False, 'error': 'Note not found'}), 404
        
        # Check ownership
        if notes[note_id].get('owner') != session.get('username') and session.get('username') != USERNAME:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Update only the title
        notes[note_id]['title'] = new_title
        notes[note_id]['modified'] = datetime.now().isoformat()
        
        if save_notes(notes):
            notes[note_id]['id'] = note_id
            return jsonify({'success': True, 'note': notes[note_id]})
        else:
            return jsonify({'success': False, 'error': 'Failed to save note'}), 500
    except Exception as e:
        logger.error(f"Error updating note title: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notes/<note_id>', methods=['DELETE'])
@login_required
@limiter.limit("10 per minute")
def delete_note(note_id):
    """Delete a note"""
    try:
        # Validate CSRF for API requests
        validate_csrf_if_enabled(request.headers.get('X-CSRFToken'))
        
        notes = load_notes()
        
        if note_id not in notes:
            return jsonify({'success': False, 'error': 'Note not found'}), 404
        
        # Check ownership (optional: remove if you want shared notes)
        if notes[note_id].get('owner') != session.get('username') and session.get('username') != USERNAME:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        del notes[note_id]
        
        if save_notes(notes):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete note'}), 500
    except Exception as e:
        logger.error(f"Error deleting note: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# OneDrive Integration Endpoints
@app.route('/api/csrf-token', methods=['GET'])
def csrf_token():
    """Get CSRF token - only available when authentication is enabled"""
    if AUTH_ENABLED and csrf:
        try:
            token = generate_csrf()
            return jsonify({'csrf_token': token})
        except Exception as e:
            logger.warning(f"Failed to generate CSRF token: {e}")
            return jsonify({'error': 'Failed to generate CSRF token'}), 500
    else:
        return jsonify({'error': 'CSRF protection disabled'}), 404

@app.route('/api/onedrive/status', methods=['GET'])
@login_required
def onedrive_status():
    """Get OneDrive authentication status"""
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        error_msg = onedrive_error_message or 'OneDrive integration not available'
        return jsonify({
            'available': False,
            'error': error_msg,
            'setup_required': 'NOTED_CLIENT_ID' in error_msg if error_msg else False
        }), 503
    
    try:
        status = onedrive_manager.get_auth_status()
        return jsonify({
            'available': True,
            'authenticated': status['authenticated'],
            'account_info': status['account_info']
        })
    except Exception as e:
        logger.error(f"Error getting OneDrive status: {e}")
        return jsonify({
            'available': True,
            'authenticated': False,
            'error': str(e)
        }), 500

@app.route('/api/onedrive/auth/start', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def start_onedrive_auth():
    """Start OneDrive device flow authentication"""
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        return jsonify({'success': False, 'error': 'OneDrive not available'}), 503
    
    try:
        validate_csrf_if_enabled(request.headers.get('X-CSRFToken'))
        
        session_id = session.get('session_id', str(uuid.uuid4()))
        session['session_id'] = session_id
        
        auth_flow = onedrive_manager.start_device_flow_auth(session_id)
        
        if auth_flow:
            return jsonify({
                'success': True,
                'auth_flow': auth_flow
            })
        else:
            # Check if it's a missing client ID issue
            if not os.environ.get('NOTED_CLIENT_ID'):
                return jsonify({
                    'success': False,
                    'error': 'OneDrive not configured: NOTED_CLIENT_ID environment variable is missing. Please set it in Railway dashboard.'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to start OneDrive authentication flow - check server logs for details'
                }), 500
            
    except Exception as e:
        logger.error(f"Error starting OneDrive auth: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/onedrive/auth/check', methods=['GET'])
@limiter.limit("30 per minute")  # Higher limit for auth polling
@login_required
def check_onedrive_auth():
    """Check OneDrive authentication flow status"""
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        return jsonify({'success': False, 'error': 'OneDrive not available'}), 503
    
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'success': False, 'error': 'No active session'}), 400
        
        result = onedrive_manager.check_device_flow_status(session_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error checking OneDrive auth: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/onedrive/auth/simple-check', methods=['GET'])
@limiter.limit("60 per minute")  # Higher limit for simple checks
def simple_onedrive_check():
    """Simple OneDrive authentication status check without session requirements"""
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        return jsonify({'success': False, 'error': 'OneDrive not available'}), 503
    
    try:
        # Basic check without requiring session
        authenticated = onedrive_manager.is_authenticated()
        return jsonify({
            'success': True, 
            'authenticated': authenticated,
            'status': 'authenticated' if authenticated else 'not_authenticated'
        })
        
    except Exception as e:
        logger.error(f"Error checking simple OneDrive status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/onedrive/auth/cancel', methods=['POST'])
@login_required
def cancel_onedrive_auth():
    """Cancel OneDrive authentication flow"""
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        return jsonify({'success': False, 'error': 'OneDrive not available'}), 503
    
    try:
        validate_csrf_if_enabled(request.headers.get('X-CSRFToken'))
        
        session_id = session.get('session_id')
        if session_id:
            success = onedrive_manager.cancel_device_flow(session_id)
            return jsonify({'success': success})
        else:
            return jsonify({'success': False, 'error': 'No active session'}), 400
            
    except Exception as e:
        logger.error(f"Error canceling OneDrive auth: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/onedrive/debug/flow-status', methods=['GET'])
@limiter.limit("20 per minute")
def debug_device_flow():
    """Debug endpoint to check device flow internal state"""
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        return jsonify({'success': False, 'error': 'OneDrive not available'}), 503
    
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'success': False, 'error': 'No active session'}), 400
        
        # Get internal flow state
        flows = getattr(onedrive_manager, '_auth_flows', {})
        if session_id in flows:
            flow_data = flows[session_id]
            elapsed = time.time() - flow_data["started_at"]
            timeout = flow_data.get("extended_expires_in", flow_data["flow"].get("expires_in", 2700))
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'started_at': flow_data["started_at"],
                'elapsed_seconds': elapsed,
                'timeout_seconds': timeout,
                'elapsed_minutes': elapsed / 60,
                'timeout_minutes': timeout / 60,
                'time_remaining_seconds': max(0, timeout - elapsed),
                'time_remaining_minutes': max(0, timeout - elapsed) / 60,
                'completed': flow_data.get("completed", False),
                'original_timeout': flow_data.get("original_expires_in", "unknown"),
                'extended_timeout': flow_data.get("extended_expires_in", "unknown")
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No active device flow',
                'session_id': session_id,
                'available_flows': list(flows.keys())
            })
        
    except Exception as e:
        logger.error(f"Error in debug flow status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/onedrive/extend-timeout', methods=['POST'])
@limiter.limit("5 per minute")
@login_required  
def extend_device_flow_timeout():
    """Extend the timeout for an active device flow"""
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        return jsonify({'success': False, 'error': 'OneDrive not available'}), 503
    
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'success': False, 'error': 'No active session'}), 400
        
        # Get internal flow state
        flows = getattr(onedrive_manager, '_auth_flows', {})
        if session_id in flows:
            flow_data = flows[session_id]
            
            # Extend timeout by another 30 minutes
            additional_time = 1800  # 30 minutes
            current_timeout = flow_data.get("extended_expires_in", flow_data["flow"].get("expires_in", 2700))
            new_timeout = current_timeout + additional_time
            
            # Update the flow data
            flow_data["extended_expires_in"] = new_timeout
            flow_data["flow"]["expires_in"] = new_timeout
            
            logger.info(f"🕐 Extended device flow timeout for session {session_id} by {additional_time}s to {new_timeout}s total")
            
            return jsonify({
                'success': True,
                'message': f'Timeout extended by {additional_time/60} minutes',
                'new_timeout_seconds': new_timeout,
                'new_timeout_minutes': new_timeout / 60,
                'added_minutes': additional_time / 60
            })
        else:
            return jsonify({'success': False, 'error': 'No active device flow found'}), 400
        
    except Exception as e:
        logger.error(f"Error extending device flow timeout: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/onedrive/cleanup-duplicates', methods=['POST'])
@login_required
@limiter.limit("2 per minute")
def cleanup_onedrive_duplicates():
    """Clean up duplicate notes on OneDrive"""
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        return jsonify({'success': False, 'error': 'OneDrive not available'}), 503
    
    try:
        validate_csrf_if_enabled(request.headers.get('X-CSRFToken'))
        
        if not onedrive_manager.is_authenticated():
            return jsonify({
                'success': False,
                'error': 'Not authenticated with OneDrive'
            }), 401
        
        result = onedrive_manager.cleanup_duplicate_notes()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error cleaning up OneDrive duplicates: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/onedrive/logout', methods=['POST'])
@login_required
def onedrive_logout():
    """Logout from OneDrive"""
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        return jsonify({'success': False, 'error': 'OneDrive not available'}), 503
    
    try:
        validate_csrf_if_enabled(request.headers.get('X-CSRFToken'))
        
        success = onedrive_manager.logout()
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error logging out from OneDrive: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/onedrive/sync/push', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def sync_to_onedrive():
    """Sync local notes to OneDrive"""
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        return jsonify({'success': False, 'error': 'OneDrive not available'}), 503
    
    try:
        validate_csrf_if_enabled(request.headers.get('X-CSRFToken'))
        
        if not onedrive_manager.is_authenticated():
            return jsonify({
                'success': False,
                'error': 'Not authenticated with OneDrive'
            }), 401
        
        # Load local notes
        local_notes = load_notes()
        
        # Sync to OneDrive
        result = onedrive_manager.sync_notes_to_cloud(local_notes)
        
        if result['success']:
            # Save updated notes with OneDrive IDs
            save_notes(result['notes'])
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error syncing to OneDrive: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/onedrive/sync/pull', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def sync_from_onedrive():
    """Load notes from OneDrive"""
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        return jsonify({'success': False, 'error': 'OneDrive not available'}), 503
    
    try:
        validate_csrf_if_enabled(request.headers.get('X-CSRFToken'))
        
        if not onedrive_manager.is_authenticated():
            return jsonify({
                'success': False,
                'error': 'Not authenticated with OneDrive'
            }), 401
        
        # Get merge strategy from request (default: 'replace')
        data = request.get_json() or {}
        merge_strategy = data.get('merge_strategy', 'replace')
        
        # Load from OneDrive
        result = onedrive_manager.load_notes_from_cloud()
        
        if result['success']:
            if merge_strategy == 'replace':
                # Replace all local notes
                save_notes(result['notes'])
            elif merge_strategy == 'merge':
                # Merge with local notes (OneDrive takes precedence for conflicts)
                local_notes = load_notes()
                local_notes.update(result['notes'])
                save_notes(local_notes)
                result['notes'] = local_notes
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error syncing from OneDrive: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/onedrive/notes', methods=['GET'])
@login_required
def list_onedrive_notes():
    """List notes from OneDrive without downloading"""
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        return jsonify({'success': False, 'error': 'OneDrive not available'}), 503
    
    try:
        if not onedrive_manager.is_authenticated():
            return jsonify({
                'success': False,
                'error': 'Not authenticated with OneDrive'
            }), 401
        
        notes_list = onedrive_manager.list_notes()
        return jsonify({
            'success': True,
            'notes': notes_list,
            'count': len(notes_list)
        })
        
    except Exception as e:
        logger.error(f"Error listing OneDrive notes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)

@app.route('/debug/onedrive')
def debug_onedrive():
    """Debug OneDrive integration status - no auth required"""
    import sys
    debug_info = {
        'onedrive_available': ONEDRIVE_AVAILABLE,
        'onedrive_manager_exists': onedrive_manager is not None,
        'onedrive_error': onedrive_error_message,
        'auth_enabled': AUTH_ENABLED,
        'environment_vars': {
            'NOTED_CLIENT_ID': bool(os.environ.get('NOTED_CLIENT_ID')),
            'NOTED_CLIENT_ID_length': len(os.environ.get('NOTED_CLIENT_ID', '')),
            'RAILWAY_ENVIRONMENT': bool(os.environ.get('RAILWAY_ENVIRONMENT')),
            'PORT': os.environ.get('PORT', 'Not set')
        },
        'dependencies_check': {
            'WebOneDriveManager_imported': 'WebOneDriveManager' in globals(),
            'msal_available': 'msal' in sys.modules
        }
    }
    return jsonify(debug_info)

@app.route('/onedrive/setup')
def onedrive_setup_guide():
    """OneDrive setup instructions - user-friendly guide"""
    client_id = os.environ.get('NOTED_CLIENT_ID')
    
    if client_id:
        status = "✅ NOTED_CLIENT_ID is configured"
        if ONEDRIVE_AVAILABLE and onedrive_manager:
            message = "🎉 OneDrive is fully configured and ready!"
            next_steps = ["Click the OneDrive button in your app to start authentication"]
        else:
            message = "⚠️ OneDrive configuration found but initialization failed"
            next_steps = [
                "Check that your Client ID is correct",
                "Ensure your Azure App Registration allows device flow",
                f"Current error: {onedrive_error_message or 'Unknown'}"
            ]
    else:
        status = "❌ NOTED_CLIENT_ID not set"
        message = "🔧 OneDrive setup required"
        next_steps = [
            "1. Go to Azure Portal (portal.azure.com)",
            "2. Navigate to Azure Active Directory → App registrations",
            "3. Click 'New registration'",
            "4. Name: 'Mobile Noted Railway'",
            "5. Redirect URI: https://login.microsoftonline.com/common/oauth2/nativeclient",
            "6. Copy the 'Application (client) ID'",
            "7. In Railway: Project → Variables → Add NOTED_CLIENT_ID",
            "8. Paste the Client ID as the value",
            "9. Railway will automatically redeploy"
        ]
    
    return jsonify({
        'status': status,
        'message': message,
        'client_id_configured': bool(client_id),
        'onedrive_ready': ONEDRIVE_AVAILABLE and onedrive_manager is not None,
        'next_steps': next_steps,
        'debug_url': '/debug/onedrive',
        'test_url': '/test/onedrive/auth'
    })

@app.route('/test/onedrive/auth')
def test_onedrive_auth():
    """Test OneDrive authentication setup without session requirements"""
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        return jsonify({
            'success': False,
            'error': 'OneDrive manager not available',
            'onedrive_available': ONEDRIVE_AVAILABLE,
            'manager_exists': onedrive_manager is not None,
            'init_error': onedrive_error_message
        })
    
    try:
        # Test if we can start a device flow
        test_session_id = f"test_{int(time.time())}"
        
        result = onedrive_manager.start_device_flow_auth(test_session_id)
        
        if result:
            # Clean up the test flow
            try:
                if hasattr(onedrive_manager, '_auth_flows'):
                    onedrive_manager._auth_flows.pop(test_session_id, None)
            except:
                pass
                
            return jsonify({
                'success': True,
                'message': 'OneDrive authentication flow can be started successfully',
                'test_flow_keys': list(result.keys()) if result else []
            })
        else:
            return jsonify({
                'success': False,
                'error': 'start_device_flow_auth returned None',
                'client_id_set': bool(os.environ.get('NOTED_CLIENT_ID')),
                'manager_type': type(onedrive_manager).__name__
            })
            
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc(),
            'client_id_set': bool(os.environ.get('NOTED_CLIENT_ID')),
            'manager_exists': onedrive_manager is not None
        })

@app.route('/onedrive/get-token')
def get_onedrive_token():
    """Get current OneDrive token for Railway environment variable setup"""
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        return jsonify({
            'success': False,
            'error': 'OneDrive not available'
        })
    
    try:
        # Check if authenticated
        if not onedrive_manager.is_authenticated():
            return jsonify({
                'success': False,
                'error': 'Not authenticated with OneDrive. Please authenticate first.',
                'instructions': 'Click the OneDrive button and complete authentication, then visit this page again.'
            })
        
        # Get current token cache
        token_data = onedrive_manager._token_cache.serialize()
        
        if token_data and len(token_data) > 10:
            return jsonify({
                'success': True,
                'authenticated': True,
                'token': token_data,
                'instructions': {
                    'step1': 'Copy the token value above',
                    'step2': 'Go to Railway Dashboard → Your Project → Variables',
                    'step3': 'Add new variable: ONEDRIVE_TOKEN_CACHE',
                    'step4': 'Paste the token as the value',
                    'step5': 'Railway will redeploy and remember your OneDrive connection!'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No valid token found',
                'suggestion': 'Try re-authenticating with OneDrive'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error retrieving token: {str(e)}'
        })

@app.route('/test/onedrive/direct-flow')
def test_direct_device_flow():
    """Direct test of device flow without OneDrive manager"""
    try:
        client_id = os.environ.get('NOTED_CLIENT_ID')
        if not client_id:
            return jsonify({
                'success': False,
                'error': 'NOTED_CLIENT_ID not set',
                'setup_required': True
            })
        
        # Import MSAL directly
        from msal import PublicClientApplication
        
        # Create app directly  
        app = PublicClientApplication(
            client_id,
            authority="https://login.microsoftonline.com/common"
        )
        
        # Try device flow directly
        scopes = ["https://graph.microsoft.com/Files.ReadWrite"]
        flow = app.initiate_device_flow(scopes=scopes)
        
        if "user_code" in flow:
            return jsonify({
                'success': True,
                'direct_flow_works': True,
                'user_code': flow['user_code'],
                'verification_uri': flow['verification_uri'],
                'expires_in': flow.get('expires_in', 900),
                'message': 'Direct device flow successful - OneDrive manager may have issues'
            })
        else:
            return jsonify({
                'success': False,
                'direct_flow_works': False,
                'flow_response': flow,
                'error': 'No user_code in flow response'
            })
            
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': f'Direct flow failed: {str(e)}',
            'traceback': traceback.format_exc(),
            'client_id_configured': bool(os.environ.get('NOTED_CLIENT_ID'))
        })

@app.route('/api/simple/onedrive/status')
def simple_onedrive_status():
    """Simple OneDrive status without auth/CSRF - for debugging"""
    client_id = os.environ.get('NOTED_CLIENT_ID')
    
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        # Provide detailed diagnostic information
        if not client_id:
            error_message = '🔑 OneDrive Setup Required: Set NOTED_CLIENT_ID environment variable in Railway dashboard.'
            setup_instructions = {
                'step1': 'Go to Railway dashboard → Your Project → Variables',
                'step2': 'Add variable: NOTED_CLIENT_ID',
                'step3': 'Value: Your Azure App Registration Client ID',
                'step4': 'App will automatically redeploy with OneDrive enabled'
            }
        else:
            error_message = f'⚠️ OneDrive initialization failed: {onedrive_error_message or "Unknown error"}'
            setup_instructions = {
                'issue': 'OneDrive manager failed to initialize',
                'client_id_length': len(client_id),
                'possible_causes': ['Invalid Client ID format', 'MSAL library issue', 'Network connectivity']
            }
            
        return jsonify({
            'available': False,
            'authenticated': False,
            'error': error_message,
            'setup_required': not bool(client_id),
            'setup_instructions': setup_instructions,
            'debug_info': {
                'client_id_set': bool(client_id),
                'client_id_length': len(client_id) if client_id else 0,
                'onedrive_available': ONEDRIVE_AVAILABLE,
                'manager_exists': onedrive_manager is not None,
                'init_error': onedrive_error_message
            },
            'auth_enabled': AUTH_ENABLED,
            'debug': True
        })
    
    try:
        status = onedrive_manager.get_auth_status()
        return jsonify({
            'available': True,
            'authenticated': status['authenticated'],
            'account_info': status['account_info'],
            'auth_enabled': AUTH_ENABLED,
            'debug': True
        })
    except Exception as e:
        return jsonify({
            'available': True,
            'authenticated': False,
            'error': str(e),
            'auth_enabled': AUTH_ENABLED,
            'debug': True
        })

@app.route('/api/simple/onedrive/sync/push', methods=['POST'])
def simple_sync_to_onedrive():
    """Sync local notes to OneDrive without login requirement"""
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        return jsonify({'success': False, 'error': 'OneDrive not available'}), 503
    
    try:
        # Use conditional CSRF validation
        validate_csrf_if_enabled(request.headers.get('X-CSRFToken'))
        
        if not onedrive_manager.is_authenticated():
            return jsonify({
                'success': False,
                'error': 'Not authenticated with OneDrive'
            }), 401
        
        # Load local notes
        local_notes = load_notes()
        
        # Sync to OneDrive
        result = onedrive_manager.sync_notes_to_cloud(local_notes)
        
        if result['success']:
            # Save updated notes with OneDrive IDs
            save_notes(result['notes'])
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error syncing to OneDrive: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simple/onedrive/sync/pull', methods=['POST'])
def simple_sync_from_onedrive():
    """Load notes from OneDrive without login requirement"""
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        return jsonify({'success': False, 'error': 'OneDrive not available'}), 503
    
    try:
        # Use conditional CSRF validation
        validate_csrf_if_enabled(request.headers.get('X-CSRFToken'))
        
        if not onedrive_manager.is_authenticated():
            return jsonify({
                'success': False,
                'error': 'Not authenticated with OneDrive'
            }), 401
        
        # Get merge strategy from request (default: 'replace')
        data = request.get_json() or {}
        merge_strategy = data.get('merge_strategy', 'replace')
        
        # Load from OneDrive
        result = onedrive_manager.load_notes_from_cloud()
        
        if result['success']:
            if merge_strategy == 'replace':
                # Replace all local notes
                save_notes(result['notes'])
            elif merge_strategy == 'merge':
                # Merge with local notes (OneDrive takes precedence for conflicts)
                local_notes = load_notes()
                local_notes.update(result['notes'])
                save_notes(local_notes)
                result['notes'] = local_notes
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error loading from OneDrive: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simple/onedrive/auth/start', methods=['POST'])
def simple_start_onedrive_auth():
    """Start OneDrive auth without CSRF/auth requirements"""
    logger.info("🔍 Simple OneDrive auth endpoint called")
    
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        logger.error(f"OneDrive not available: ONEDRIVE_AVAILABLE={ONEDRIVE_AVAILABLE}, manager={onedrive_manager is not None}")
        return jsonify({'success': False, 'error': 'OneDrive not available'}), 503
    
    try:
        # Don't validate CSRF when auth is disabled
        if AUTH_ENABLED:
            validate_csrf(request.headers.get('X-CSRFToken'))
        
        session_id = session.get('session_id', str(uuid.uuid4()))
        session['session_id'] = session_id
        logger.info(f"🔍 Starting device flow for session: {session_id}")
        
        auth_flow = onedrive_manager.start_device_flow_auth(session_id)
        logger.info(f"🔍 Device flow result: {auth_flow is not None}")
        
        if auth_flow:
            logger.info(f"🔗 Started OneDrive device flow for session {session_id}")
            logger.info(f"🔍 Auth flow keys: {list(auth_flow.keys()) if auth_flow else 'None'}")
            return jsonify({
                'success': True,
                'auth_flow': auth_flow
            })
        else:
            logger.error("🔍 start_device_flow_auth returned None")
            # Check if it's a missing client ID issue
            if not os.environ.get('NOTED_CLIENT_ID'):
                logger.error("🔍 NOTED_CLIENT_ID not found")
                return jsonify({
                    'success': False,
                    'error': 'OneDrive setup required: Please set NOTED_CLIENT_ID environment variable with your Azure App Registration Client ID in Railway dashboard.'
                }), 503
            else:
                client_id = os.environ.get('NOTED_CLIENT_ID', '')
                logger.error(f"🔍 NOTED_CLIENT_ID is set but auth flow failed: {client_id[:8] if client_id else 'None'}...")
                return jsonify({
                    'success': False,
                    'error': 'OneDrive authentication flow failed to start - check server logs'
                }), 500
            
    except Exception as e:
        logger.error(f"🔍 Exception in simple OneDrive auth: {e}")
        import traceback
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simple/onedrive/auth/check', methods=['GET'])
def simple_check_onedrive_auth():
    """Simple OneDrive auth check without CSRF/auth requirements"""
    logger.info("🔍 Simple OneDrive auth check endpoint called")
    
    if not ONEDRIVE_AVAILABLE or not onedrive_manager:
        logger.error(f"OneDrive not available: ONEDRIVE_AVAILABLE={ONEDRIVE_AVAILABLE}, manager={onedrive_manager is not None}")
        return jsonify({'success': False, 'error': 'OneDrive not available'}), 503
    
    try:
        session_id = session.get('session_id')
        if not session_id:
            logger.info("🔍 No session ID found - no auth in progress")
            return jsonify({
                'status': 'error',
                'message': 'No authentication in progress'
            })
        
        logger.info(f"🔍 Checking auth progress for session: {session_id}")
        auth_result = onedrive_manager.check_device_flow_status(session_id)
        logger.info(f"🔍 Auth check result: {auth_result}")
        
        if auth_result:
            return jsonify(auth_result)
        else:
            return jsonify({
                'status': 'error',
                'message': 'Authentication check failed'
            })
            
    except Exception as e:
        logger.error(f"🔍 Exception in simple auth check: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Auth check error: {str(e)}'
        })

if __name__ == '__main__':
    # Only run development server if not in production
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PORT')
    
    if not is_production:
        print("🔐 Starting Secure Web Mobile Noted (Development Mode)...")
        print("🛡️  Security features enabled:")
        print("   - Authentication required")
        print("   - Rate limiting active")
        print("   - CSRF protection enabled")
        print("   - Security headers added")
        print(f"   - Username: {USERNAME}")
        print(f"   - Session timeout: {app.config['PERMANENT_SESSION_LIFETIME']} seconds")
        print("📱 Access on mobile: http://your-ip-address:5000")
        print("💻 Access on desktop: http://localhost:5000")
        print("🔧 To stop: Press Ctrl+C")
        print("\n✅ Authentication configured via environment variables")
        
        # Get port from environment variable (for cloud hosting) or default to 5000
        port = int(os.environ.get('PORT', 5000))
        
        # Disable debug in production
        debug_mode = os.environ.get('FLASK_ENV') == 'development'
        
        app.run(host='0.0.0.0', port=port, debug=debug_mode)
    else:
        print("🚀 Production mode - using Gunicorn via Procfile")