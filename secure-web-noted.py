#!/usr/bin/env python3
"""
Secure Mobile Noted Web App
Password-protected note-taking app with device trust system.
Authentication via environment variables (no hardcoded passwords).
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)

# Security Configuration - Load from environment variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Authentication - MUST be set in Railway dashboard
USERNAME = os.environ.get('RAILWAY_USERNAME')
PASSWORD = os.environ.get('RAILWAY_PASSWORD')

if not USERNAME or not PASSWORD:
    print("ERROR: RAILWAY_USERNAME and RAILWAY_PASSWORD environment variables MUST be set!")
    print("Please set these in your Railway dashboard under Variables.")
    print("App will not start without proper authentication configuration.")
    exit(1)

# Directories
NOTES_DIR = 'web_notes'
TRUSTED_DEVICES_FILE = 'trusted_devices.json'
DEVICE_TRUST_DURATION = timedelta(days=30)

# Ensure directories exist
os.makedirs(NOTES_DIR, exist_ok=True)

def generate_device_fingerprint():
    """Generate a unique device fingerprint based on browser characteristics"""
    user_agent = request.headers.get('User-Agent', '')
    accept_language = request.headers.get('Accept-Language', '')
    accept_encoding = request.headers.get('Accept-Encoding', '')
    
    # Create a unique fingerprint
    fingerprint_data = f"{user_agent}|{accept_language}|{accept_encoding}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()

def load_trusted_devices():
    """Load trusted devices from JSON file"""
    if os.path.exists(TRUSTED_DEVICES_FILE):
        try:
            with open(TRUSTED_DEVICES_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_trusted_devices(devices):
    """Save trusted devices to JSON file"""
    try:
        with open(TRUSTED_DEVICES_FILE, 'w') as f:
            json.dump(devices, f, indent=2)
    except Exception as e:
        print(f"Error saving trusted devices: {e}")

def is_device_trusted():
    """Check if current device is trusted"""
    device_id = generate_device_fingerprint()
    trusted_devices = load_trusted_devices()
    
    if device_id in trusted_devices:
        # Check if trust hasn't expired
        trust_date = datetime.fromisoformat(trusted_devices[device_id]['trusted_date'])
        if datetime.now() - trust_date < DEVICE_TRUST_DURATION:
            return True
        else:
            # Remove expired trust
            del trusted_devices[device_id]
            save_trusted_devices(trusted_devices)
    
    return False

def trust_current_device():
    """Add current device to trusted devices"""
    device_id = generate_device_fingerprint()
    trusted_devices = load_trusted_devices()
    
    trusted_devices[device_id] = {
        'trusted_date': datetime.now().isoformat(),
        'user_agent': request.headers.get('User-Agent', '')[:100],  # Truncate for storage
        'ip_address': request.remote_addr
    }
    
    save_trusted_devices(trusted_devices)

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if not session.get('logged_in'):
            # Check if device is trusted
            if is_device_trusted():
                session['logged_in'] = True
                session['device_trusted'] = True
            else:
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_all_notes():
    """Get all notes from the notes directory"""
    notes = []
    if os.path.exists(NOTES_DIR):
        for filename in os.listdir(NOTES_DIR):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(NOTES_DIR, filename), 'r', encoding='utf-8') as f:
                        note_data = json.load(f)
                        note_data['id'] = filename[:-5]  # Remove .json extension
                        notes.append(note_data)
                except Exception as e:
                    print(f"Error loading note {filename}: {e}")
    
    # Sort by last modified date
    notes.sort(key=lambda x: x.get('last_modified', ''), reverse=True)
    return notes

def save_note(note_id, content):
    """Save a note to the notes directory"""
    note_data = {
        'content': content,
        'last_modified': datetime.now().isoformat(),
        'created': datetime.now().isoformat()
    }
    
    # If note exists, preserve creation date
    note_file = os.path.join(NOTES_DIR, f"{note_id}.json")
    if os.path.exists(note_file):
        try:
            with open(note_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                note_data['created'] = existing_data.get('created', note_data['created'])
        except Exception:
            pass  # Use new creation date if can't read existing
    
    try:
        with open(note_file, 'w', encoding='utf-8') as f:
            json.dump(note_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving note {note_id}: {e}")
        return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with device trust option"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        trust_device = request.form.get('trust_device') == 'on'
        
        # Simple password check (you should use hashed passwords in production)
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            session['device_trusted'] = False
            
            # Trust device if requested
            if trust_device:
                trust_current_device()
                session['device_trusted'] = True
                flash('Device trusted for 30 days!', 'success')
            
            flash('Successfully logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('login'))

@app.route('/')
@require_auth
def index():
    """Main page showing all notes"""
    notes = get_all_notes()
    return render_template('simple_index.html', notes=notes)

@app.route('/note/<note_id>')
@require_auth
def view_note(note_id):
    """View a specific note"""
    note_file = os.path.join(NOTES_DIR, f"{note_id}.json")
    if os.path.exists(note_file):
        try:
            with open(note_file, 'r', encoding='utf-8') as f:
                note_data = json.load(f)
                note_data['id'] = note_id
                return render_template('simple_note.html', note=note_data)
        except Exception as e:
            return f"Error loading note: {e}", 500
    return "Note not found", 404

@app.route('/save', methods=['POST'])
@require_auth
def save():
    """Save a note"""
    note_id = request.form.get('note_id', '')
    content = request.form.get('content', '')
    
    if not note_id:
        # Generate a new note ID based on timestamp
        note_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if save_note(note_id, content):
        flash('Note saved successfully!', 'success')
        return redirect(url_for('view_note', note_id=note_id))
    else:
        flash('Error saving note!', 'error')
        return redirect(url_for('index'))

@app.route('/new')
@require_auth
def new_note():
    """Create a new note"""
    return render_template('simple_note.html', note={'id': '', 'content': ''})

@app.route('/delete/<note_id>', methods=['POST'])
@require_auth
def delete_note(note_id):
    """Delete a note"""
    note_file = os.path.join(NOTES_DIR, f"{note_id}.json")
    try:
        if os.path.exists(note_file):
            os.remove(note_file)
            flash('Note deleted successfully!', 'success')
        else:
            flash('Note not found!', 'error')
    except Exception as e:
        flash(f'Error deleting note: {e}', 'error')
    
    return redirect(url_for('index'))

@app.route('/api/notes')
@require_auth
def api_notes():
    """API endpoint to get all notes as JSON"""
    notes = get_all_notes()
    return jsonify(notes)

@app.route('/health')
def health():
    """Health check endpoint - no auth required"""
    return jsonify({
        'status': 'ok',
        'message': 'Secure Mobile Noted is running',
        'features': ['authentication', 'device_trust'],
        'notes_count': len(get_all_notes()) if os.path.exists(NOTES_DIR) else 0,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)