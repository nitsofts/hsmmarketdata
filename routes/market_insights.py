from flask import Blueprint, jsonify, request
import os
import requests
import logging

# Blueprint setup
market_insights_bp = Blueprint('market_insights', __name__)

# Load secure API key from environment
API_KEY = os.getenv('API_KEY')

# --- Helper Functions ---

def is_authenticated(req):
    """Validate API key via header or query param."""
    return (
        req.headers.get('x-api-key') == API_KEY or
        req.args.get('api_key') == API_KEY
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
    """Return whether market is open, as a single-item list."""
    if not is_authenticated(request):
        return jsonify([{ "error": "Unauthorized. Invalid API Key." }]), 401

    try:
        data = fetch_market_status_data()
        return jsonify([{ "is_open": data.get("is_open", False) }])
    except Exception as e:
        logging.error(f"[Market Insights: Status] {e}")
        return jsonify([{ "error": "Unable to fetch market status." }]), 500
