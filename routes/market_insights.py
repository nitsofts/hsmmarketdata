from flask import Blueprint, jsonify, request
import os
import requests
import logging

# Blueprint setup
market_insights_bp = Blueprint('market_insights', __name__)

# Load secure API key from environment (e.g., "light")
API_KEY = os.getenv('API_KEY')

# --- Helper Functions ---

def is_authenticated(req):
    """Validate API key using disguised 'view-mode' header or fallback query param."""
    return (
        req.headers.get('view-mode') == API_KEY or
        req.args.get('view-mode') == API_KEY
    )

def fetch_market_status_data():
    """Fetch live market status from Chukul."""
    url = "https://chukul.com/api/tools/market/status/"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# --- Route ---

@market_insights_bp.route('/v1/market/insights/status', methods=['GET'])
def market_open_status():
    """Return market open status and last updated time in milliseconds."""
    if not is_authenticated(request):
        return jsonify([{ "error": "Unauthorized. Invalid Key." }]), 401

    try:
        data = fetch_market_status_data()
        is_open = data.get("is_open", False)
        last_updated_unix = data.get("as_of_live_unix", 0)

        return jsonify([{
            "marketOpen": is_open,
            "lastUpdated": int(last_updated_unix * 1000)  # convert to ms
        }])
    except Exception as e:
        logging.error(f"[Market Insights: Status] {e}")
        return jsonify([{ "error": "Unable to fetch market status." }]), 500
