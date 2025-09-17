#!/usr/bin/env python3
"""
Web Mobile Noted - Browser-based note-taking app
Works on desktop and mobile browsers, easier to deploy than native Android
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
import uuid
from datetime import datetime
import logging

app = Flask(__name__)

# Configuration
NOTES_DIR = os.path.join(os.path.dirname(__file__), 'web_notes')
os.makedirs(NOTES_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
def index():
    """Main page with mobile-optimized interface"""
    return render_template('index.html')

@app.route('/api/notes', methods=['GET'])
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
def create_note():
    """Create a new note"""
    try:
        data = request.get_json()
        note_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        note_data = {
            'text': data.get('text', ''),
            'created': timestamp,
            'modified': timestamp
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
def update_note(note_id):
    """Update an existing note"""
    try:
        data = request.get_json()
        notes = load_notes()
        
        if note_id not in notes:
            return jsonify({'success': False, 'error': 'Note not found'}), 404
        
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
def delete_note(note_id):
    """Delete a note"""
    try:
        notes = load_notes()
        
        if note_id not in notes:
            return jsonify({'success': False, 'error': 'Note not found'}), 404
        
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
    print("🌐 Starting Web Mobile Noted...")
    print("📱 Access on mobile: http://your-ip-address:5000")
    print("💻 Access on desktop: http://localhost:5000")
    print("🔧 To stop: Press Ctrl+C")
    
    # Get port from environment variable (for cloud hosting) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    app.run(host='0.0.0.0', port=port, debug=True)