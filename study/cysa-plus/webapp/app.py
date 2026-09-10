#!/usr/bin/env python3
"""Server for the CySA+ Field Notes web app.

The app itself is static — all rendering happens in the browser — so this
server exists to make it installable as a PWA (service workers need http/https,
not file://) and to give you something to run locally or deploy.

    pip install -r requirements.txt
    python3 app.py                 # http://localhost:5000

Deploying: any static host works too. The Flask app is here because a service
worker will not register from a file:// URL, and because this project already
deploys this way elsewhere.
"""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, Response, send_from_directory

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"

app = Flask(__name__, static_folder=None)


@app.after_request
def headers(response: Response) -> Response:
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    return response


@app.route("/")
def index() -> Response:
    return send_from_directory(STATIC, "index.html")


@app.route("/healthz")
def healthz() -> Response:
    ready = (STATIC / "content.json").exists()
    return Response("ok" if ready else "content.json missing — run build_content.py",
                    status=200 if ready else 503, mimetype="text/plain")


@app.route("/<path:filename>")
def asset(filename: str) -> Response:
    response = send_from_directory(STATIC, filename)
    if filename.endswith(".webmanifest"):
        response.mimetype = "application/manifest+json"
    if filename.endswith("sw.js"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Service-Worker-Allowed"] = "/"
    return response


def main() -> None:
    if not (STATIC / "content.json").exists():
        raise SystemExit("static/content.json is missing. Run: python3 build_content.py")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    print(f"CySA+ Field Notes → http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
