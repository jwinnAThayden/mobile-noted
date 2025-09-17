#!/usr/bin/env python3
"""
Simple Mobile Noted Web App - No Security Features
A clean, minimal note-taking web application for Railway deployment.
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)

# Simple configuration
NOTES_DIR = 'web_notes'
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

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

@app.route('/')
def index():
    """Main page showing all notes"""
    notes = get_all_notes()
    return render_template('simple_index.html', notes=notes)

@app.route('/note/<note_id>')
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
def save():
    """Save a note"""
    note_id = request.form.get('note_id', '')
    content = request.form.get('content', '')
    
    if not note_id:
        # Generate a new note ID based on timestamp
        note_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if save_note(note_id, content):
        return redirect(url_for('view_note', note_id=note_id))
    else:
        return "Error saving note", 500

@app.route('/new')
def new_note():
    """Create a new note"""
    return render_template('simple_note.html', note={'id': '', 'content': ''})

@app.route('/delete/<note_id>', methods=['POST'])
def delete_note(note_id):
    """Delete a note"""
    note_file = os.path.join(NOTES_DIR, f"{note_id}.json")
    try:
        if os.path.exists(note_file):
            os.remove(note_file)
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error deleting note: {e}", 500

@app.route('/api/notes')
def api_notes():
    """API endpoint to get all notes as JSON"""
    notes = get_all_notes()
    return jsonify(notes)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Simple Mobile Noted is running',
        'notes_count': len(get_all_notes()),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)