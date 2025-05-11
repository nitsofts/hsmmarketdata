from flask import Blueprint, jsonify, request
import os
import requests
import time
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

# --- Route Insights > Status  ---
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
        
# --- Route Insights > Index  ---
@market_insights_bp.route('/v1/market/insights/index', methods=['GET'])
def get_index_list():
    """Return list of current indices and their stats."""
    if not is_authenticated(request):
        return jsonify([{ "error": "Unauthorized. Invalid Key." }]), 401

    try:
        # Dynamic timestamp in milliseconds
        timestamp = int(time.time() * 1000)
        url = f"https://nepalipaisa.com/api/GetIndexLive?_={timestamp}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        index_list = data.get("result", [])
        return jsonify(index_list)

    except Exception as e:
        logging.error(f"[Market Insights: Index] {e}")
        return jsonify([{ "error": "Unable to fetch index data." }]), 500

# --- Route Insights > Sub Index  ---
@market_insights_bp.route('/v1/market/insights/subindex', methods=['GET'])
def get_subindex_list():
    """Return list of sub-index stats (e.g., Banking, Hydro, Finance)."""
    if not is_authenticated(request):
        return jsonify([{ "error": "Unauthorized. Invalid Key." }]), 401

    try:
        timestamp = int(time.time() * 1000)
        url = f"https://nepalipaisa.com/api/GetSubIndexLive?_={timestamp}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        subindex_list = data.get("result", [])
        return jsonify(subindex_list)

    except Exception as e:
        logging.error(f"[Market Insights: SubIndex] {e}")
        return jsonify([{ "error": "Unable to fetch sub-index data." }]), 500


