from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    port = os.environ.get('PORT', 'not set')
    return f'Hello Railway! 🎉 Running on port {port}'

@app.route('/health')
def health():
    return {
        'status': 'ok', 
        'port': os.environ.get('PORT', 'not set'),
        'message': 'Minimal app is working!'
    }

@app.route('/debug')
def debug():
    return {
        'PORT': os.environ.get('PORT', 'not set'),
        'all_env': dict(os.environ)
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port)