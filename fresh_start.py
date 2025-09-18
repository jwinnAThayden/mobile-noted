from flask import Flask, render_template_string, request, redirect, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Simple in-memory storage (will reset on restart)
notes = []

# HTML templates as strings (no external files needed)
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Simple Notes</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; }
        .note { background: white; margin: 10px 0; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 3px; text-decoration: none; display: inline-block; margin: 5px; }
        .btn:hover { background: #0056b3; }
        .delete { background: #dc3545; }
        .delete:hover { background: #c82333; }
        textarea { width: 100%; height: 200px; padding: 10px; border: 1px solid #ddd; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📝 Simple Notes</h1>
        <a href="/new" class="btn">+ New Note</a>
        
        {% if notes %}
            {% for note in notes %}
            <div class="note">
                <div>{{ note.content[:100] }}{% if note.content|length > 100 %}...{% endif %}</div>
                <small>{{ note.created }}</small>
                <div style="margin-top: 10px;">
                    <a href="/edit/{{ loop.index0 }}" class="btn">Edit</a>
                    <a href="/delete/{{ loop.index0 }}" class="btn delete" onclick="return confirm('Delete?')">Delete</a>
                </div>
            </div>
            {% endfor %}
        {% else %}
            <p>No notes yet. <a href="/new">Create your first note!</a></p>
        {% endif %}
    </div>
</body>
</html>
'''

EDIT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Edit Note</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 5px; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 3px; text-decoration: none; display: inline-block; margin: 5px; }
        .btn:hover { background: #0056b3; }
        textarea { width: 100%; height: 300px; padding: 10px; border: 1px solid #ddd; border-radius: 3px; font-size: 16px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{% if note %}Edit Note{% else %}New Note{% endif %}</h1>
        <form method="POST">
            <textarea name="content" placeholder="Write your note here...">{{ note.content if note else '' }}</textarea>
            <div style="margin-top: 10px;">
                <button type="submit" class="btn">Save</button>
                <a href="/" class="btn" style="background: #6c757d;">Cancel</a>
            </div>
        </form>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(INDEX_TEMPLATE, notes=notes)

@app.route('/new', methods=['GET', 'POST'])
def new_note():
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            notes.append({
                'content': content,
                'created': datetime.now().strftime('%Y-%m-%d %H:%M')
            })
        return redirect('/')
    return render_template_string(EDIT_TEMPLATE)

@app.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    if note_id >= len(notes):
        return redirect('/')
    
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            notes[note_id]['content'] = content
        return redirect('/')
    
    return render_template_string(EDIT_TEMPLATE, note=notes[note_id])

@app.route('/delete/<int:note_id>')
def delete_note(note_id):
    if note_id < len(notes):
        notes.pop(note_id)
    return redirect('/')

@app.route('/api/notes')
def api_notes():
    return jsonify(notes)

@app.route('/health')
def health():
    return {'status': 'ok', 'notes_count': len(notes)}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)