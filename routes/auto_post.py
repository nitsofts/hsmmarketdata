
from flask import Blueprint, jsonify, request
import os
import requests
import logging

auto_post_bp = Blueprint('auto_post', __name__)
API_KEY = os.getenv('API_KEY')

# --- Authentication Helper ---
def is_authenticated(req):
    return (
        req.headers.get('view-mode') == API_KEY or
        req.args.get('view-mode') == API_KEY
    )

# --- Data Fetcher ---
def fetch_nepse_summary():
    """Fetch NEPSE summary data from Nepalipaisa."""
    url = "https://nepalipaisa.com/api/GetNepseLive"
    response = requests.get(url)
    response.raise_for_status()
    return response.json().get("result", {})

# --- Route: NEPSE Close Summary ---
@auto_post_bp.route('/v2/post/nepse/close', methods=['GET'])
def nepse_close_summary():
    """Return cleaned and structured NEPSE close summary for auto-post."""
    if not is_authenticated(request):
        return jsonify([{ "error": "Unauthorized. Invalid Key." }]), 401

    try:
        data = fetch_nepse_summary()
        
        summary = {
            "index": round(data.get("indexValue", 0.0), 2),
            "change": round(data.get("difference", 0.0), 2),
            "percent_change": round(data.get("percentChange", 0.0), 2),
            "turnover": data.get("turnover", 0),
            "transactions": data.get("noOfTransactions", 0),
            "advanced": data.get("noOfGainers", 0),
            "declined": data.get("noOfLosers", 0),
            "unchanged": data.get("noOfUnchanged", 0),
            "date": data.get("asOfDateString", "")
        }

        return jsonify([summary])

    except Exception as e:
        logging.error(f"[AutoPoster: NEPSE Close] {e}")
        return jsonify([{ "error": "Failed to fetch NEPSE close summary." }]), 500
