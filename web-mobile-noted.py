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
from flask_wtf.csrf import CSRFProtect, validate_csrf
from werkzeug.security import check_password_hash, generate_password_hash
import json
import os
import uuid
from datetime import datetime, timedelta
import logging
from functools import wraps
import secrets
import hashlib
from dateutil import parser

app = Flask(__name__)

# Security Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
app.config['SESSION_FILE_THRESHOLD'] = 100
app.config['WTF_CSRF_TIME_LIMIT'] = 3600

# Authentication Configuration
USERNAME = os.environ.get('NOTED_USERNAME', 'admin')
PASSWORD_HASH = os.environ.get('NOTED_PASSWORD_HASH', generate_password_hash('secure123'))  # Change default!

# Initialize security extensions
Session(app)
csrf = CSRFProtect(app)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["100 per hour", "20 per minute"]
)

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
@limiter.limit("5 per minute")
def login():
    """Login page and authentication"""
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
            
            if username == USERNAME and check_password_hash(PASSWORD_HASH, password):
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
        validate_csrf(request.headers.get('X-CSRFToken'))
        
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
        validate_csrf(request.headers.get('X-CSRFToken'))
        
        data = request.get_json()
        device_name = data.get('name', '').strip()
        
        device_id = add_device_trust(device_name)
        session['trusted_device'] = True
        session['device_id'] = device_id
        
        return jsonify({'success': True, 'message': 'Device has been trusted for 30 days', 'device_id': device_id})
        
    except Exception as e:
        logger.error(f"Error trusting current device: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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

@app.route('/')
@login_required
def index():
    """Main page with mobile-optimized interface"""
    return render_template('index.html')

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
        validate_csrf(request.headers.get('X-CSRFToken'))
        
        data = request.get_json()
        note_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        note_data = {
            'text': data.get('text', ''),
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
        validate_csrf(request.headers.get('X-CSRFToken'))
        
        data = request.get_json()
        notes = load_notes()
        
        if note_id not in notes:
            return jsonify({'success': False, 'error': 'Note not found'}), 404
        
        # Check ownership (optional: remove if you want shared notes)
        if notes[note_id].get('owner') != session.get('username') and session.get('username') != USERNAME:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        notes[note_id]['text'] = data.get('text', notes[note_id]['text'])
        notes[note_id]['modified'] = datetime.now().isoformat()
        
        if save_notes(notes):
            notes[note_id]['id'] = note_id
            return jsonify({'success': True, 'note': notes[note_id]})
        else:
            return jsonify({'success': False, 'error': 'Failed to save note'}), 500
    except Exception as e:
        logger.error(f"Error updating note: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notes/<note_id>', methods=['DELETE'])
@login_required
@limiter.limit("10 per minute")
def delete_note(note_id):
    """Delete a note"""
    try:
        # Validate CSRF for API requests
        validate_csrf(request.headers.get('X-CSRFToken'))
        
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

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)

if __name__ == '__main__':
    print("🔐 Starting Secure Web Mobile Noted...")
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
    print("\n⚠️  IMPORTANT: Change default password by setting NOTED_PASSWORD_HASH environment variable!")
    
    # Get port from environment variable (for cloud hosting) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Disable debug in production
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)