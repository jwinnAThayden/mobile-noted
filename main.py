from flask import Flask, jsonify, render_template_string
import os

app = Flask(__name__)

# Simple HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Mobile Noted - Working!</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial; margin: 20px; }
        .success { color: green; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🎉 Mobile Noted is Running!</h1>
    <p class="success">Railway deployment successful!</p>
    <p>Port: {{ port }}</p>
    <p>Environment: {{ env }}</p>
    <hr>
    <p><a href="/health">Health Check</a></p>
    <p><a href="/test">Test API</a></p>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, 
                                port=os.environ.get('PORT', '5000'),
                                env=os.environ.get('RAILWAY_ENVIRONMENT', 'local'))

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'app': 'Mobile Noted',
        'port': os.environ.get('PORT'),
        'railway_env': os.environ.get('RAILWAY_ENVIRONMENT')
    })

@app.route('/test')
def test():
    return jsonify({
        'message': 'Test endpoint working!',
        'success': True
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)