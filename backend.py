"""
Backend for the GETAJOB internship agent.
Stores your preferences, stores every listing the Gemini agent sends,
serves both to your frontend, and can trigger the agent on demand.

Run it with:  python3 app.py
It listens on http://localhost:5000
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allows your frontend (running on a different port/domain) to call this API

DB_PATH = Path(__file__).parent / "internships.db"

# Fill these in once you've created the agent in Gemini Enterprise / Agentspace.
# AGENT_ENDPOINT is the "reasoning engine" query URL shown on the agent's deploy page.
# AGENT_AUTH_TOKEN is a short-lived token from `gcloud auth print-access-token`,
# or better, a service account key set up for server-to-server calls.
AGENT_ENDPOINT = os.environ.get("AGENT_ENDPOINT", "")
AGENT_AUTH_TOKEN = os.environ.get("AGENT_AUTH_TOKEN", "")


# creates the database tables the first time the app runs, does nothing if they already exist
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            company_type TEXT,
            category TEXT,
            subcategory TEXT,
            listing_type TEXT,
            work_mode TEXT,
            duration TEXT,
            stipend TEXT,
            location TEXT,
            date_posted TEXT,
            deadline TEXT,
            url TEXT,
            source TEXT,
            summary TEXT,
            received_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            data TEXT
        )
    """)
    # seed one empty preferences row so get/update never has to special-case "missing"
    conn.execute(
        "INSERT OR IGNORE INTO preferences (id, data) VALUES (1, ?)",
        (json.dumps({
            "categories": [],
            "subcategories": [],
            "listing_types": [],
            "work_mode": [],
            "company_type": [],
            "paid_only": False,
            "min_date_posted": "",
            "excluded_companies": []
        }),)
    )
    conn.commit()
    conn.close()


# opens a connection to the sqlite file, used by every route below
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# called by the Gemini agent at the start of each run to know what to filter for
@app.route("/api/preferences", methods=["GET"])
def get_preferences():
    conn = get_db()
    row = conn.execute("SELECT data FROM preferences WHERE id = 1").fetchone()
    conn.close()
    return jsonify(json.loads(row["data"]))


# called by your frontend when you change your filters in the UI
@app.route("/api/preferences", methods=["POST"])
def update_preferences():
    conn = get_db()
    conn.execute(
        "UPDATE preferences SET data = ? WHERE id = 1",
        (json.dumps(request.json),)
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})


# called by the Gemini agent so it doesn't send you the same listing twice
@app.route("/api/known-ids", methods=["GET"])
def get_known_ids():
    conn = get_db()
    rows = conn.execute("SELECT id FROM listings").fetchall()
    conn.close()
    return jsonify([r["id"] for r in rows])


# called by the Gemini agent once per run (hourly or manual) with its findings
@app.route("/api/results", methods=["POST"])
def post_results():
    body = request.json
    listings = body.get("listings", [])
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    for item in listings:
        conn.execute("""
            INSERT OR IGNORE INTO listings
            (id, title, company, company_type, category, subcategory, listing_type,
             work_mode, duration, stipend, location, date_posted, deadline, url, source,
             summary, received_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get("id"), item.get("title"), item.get("company"),
            item.get("company_type"), item.get("category"), item.get("subcategory"),
            item.get("listing_type"), item.get("work_mode"), item.get("duration"),
            item.get("stipend"), item.get("location"), item.get("date_posted"),
            item.get("deadline"), item.get("url"), item.get("source"),
            item.get("summary"), now
        ))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "stored": len(listings)})


# called by your frontend to display listings, newest received first
@app.route("/api/listings", methods=["GET"])
def get_listings():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM listings ORDER BY received_at DESC LIMIT 200"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# called by your frontend's "Scrape Now" button — asks the agent to run immediately
@app.route("/api/trigger", methods=["POST"])
def trigger_agent():
    if not AGENT_ENDPOINT:
        return jsonify({"status": "error", "message": "AGENT_ENDPOINT is not configured"}), 500
    try:
        resp = requests.post(
            AGENT_ENDPOINT,
            headers={
                "Authorization": f"Bearer {AGENT_AUTH_TOKEN}",
                "Content-Type": "application/json"
            },
            json={"input": {"run_type": "manual"}},
            timeout=60
        )
        resp.raise_for_status()
        return jsonify({"status": "ok", "agent_response": resp.json()})
    except requests.RequestException as err:
        return jsonify({"status": "error", "message": str(err)}), 502


init_db()  # runs on both `python3 app.py` and when gunicorn imports this file on Cloud Run

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
