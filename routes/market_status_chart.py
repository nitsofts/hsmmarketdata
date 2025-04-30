from flask import Blueprint, jsonify, request
import logging
import requests
import os
from datetime import datetime

market_status_chart_bp = Blueprint('market_status_chart', __name__)

# API key from environment variable
API_KEY = os.getenv('API_KEY')  # Make sure to set this in Render.com or your local .env

# Authenticate using header or query param
def is_authenticated(req):
    header_key = req.headers.get('x-api-key')
    query_key = req.args.get('api_key')
    return header_key == API_KEY or query_key == API_KEY

# Format date string to HH:MM:SS
def format_date(date_string):
    try:
        return datetime.fromisoformat(date_string).strftime("%H:%M:%S")
    except ValueError:
        return date_string

# GET /v1/market/status
@market_status_chart_bp.route('/v1/market/status', methods=['GET'])
def market_status():
    if not is_authenticated(request):
        return jsonify({"success": False, "message": "Unauthorized. Invalid API Key."}), 401
    try:
        status_data = fetch_market_status_data()
        return jsonify({"success": True, "data": status_data})
    except Exception as e:
        logging.error(f"Error in /market/status: {str(e)}")
        return jsonify({"success": False, "message": "Failed to fetch market status."}), 500

# GET /v1/market/chart
@market_status_chart_bp.route('/v1/market/chart', methods=['GET'])
def market_chart():
    if not is_authenticated(request):
        return jsonify({"success": False, "message": "Unauthorized. Invalid API Key."}), 401

    try:
        # Check index from header or query param (default = nepse)
        index_alias = request.headers.get('index') or request.args.get('index') or 'nepse'

        index_map = {
            "nepse": "nepse",
            "banking": "bankingind",
            "devbank": "devbankind",
            "finance": "financeind",
            "hotels": "hotelind",
            "hydro": "hydropowind",
            "invest": "invidx",
            "life": "lifeinsuind",
            "manufacture": "manufactureind",
            "microfinance": "microfinind",
            "mutual": "mutualind",
            "nonlife": "nonlifeind",
            "others": "othersind",
            "trading": "tradingind"
        }

        index_key = index_map.get(index_alias.lower())
        if not index_key:
            return jsonify({
                "success": False,
                "message": f"Invalid index name '{index_alias}'. Please check your input."
            }), 400

        url = f"https://chukul.com/api/data/v2/daily/{index_key}/"
        response = requests.get(url)
        response.raise_for_status()
        raw = response.json()

        return jsonify({
            "success": True,
            "data": raw.get("data", []),
            "point_change": raw.get("point_change")
        })

    except Exception as e:
        logging.error(f"Error in /market/chart: {str(e)}")
        return jsonify({"success": False, "message": "Failed to fetch chart data."}), 500

# Helper: Fetch market status from chukul
def fetch_market_status_data():
    url = "https://chukul.com/api/tools/market/status/"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
