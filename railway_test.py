#!/usr/bin/env python3
"""
Super simple test app for Railway debugging
"""

from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Railway Test App - Working!"

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Railway test app is running',
        'port': os.environ.get('PORT', 'not_set'),
        'python_path': os.getcwd()
    })

@app.route('/debug')
def debug():
    return jsonify({
        'env_vars': {
            'PORT': os.environ.get('PORT'),
            'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT'),
            'NOTED_USERNAME': 'SET' if os.environ.get('NOTED_USERNAME') else 'NOT_SET',
            'NOTED_PASSWORD_HASH': 'SET' if os.environ.get('NOTED_PASSWORD_HASH') else 'NOT_SET',
        },
        'working_directory': os.getcwd(),
        'app_name': 'railway_test'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)