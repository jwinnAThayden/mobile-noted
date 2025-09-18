from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def index():
    return "Railway diagnostic is running. Environment variables check: USERNAME={}, PASSWORD={}".format(
        "SET" if os.environ.get('RAILWAY_USERNAME') else "NOT SET",
        "SET" if os.environ.get('RAILWAY_PASSWORD') else "NOT SET"
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
