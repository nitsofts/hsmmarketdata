from flask import Blueprint, jsonify, request
import logging
import requests
from datetime import datetime

marketstatuschart_bp = Blueprint('marketstatuschart', __name__)

API_KEY = "your_super_secret_key"  # Replace with your real key


def is_authenticated(req):
    header_key = req.headers.get('x-api-key')
    query_key = req.args.get('api_key')
    return header_key == API_KEY or query_key == API_KEY


def format_date(date_string):
    try:
        return datetime.fromisoformat(date_string).strftime("%H:%M:%S")
    except ValueError:
        return date_string


@market_bp.route('/api/v1/market/status', methods=['GET'])
def market_status():
    if not is_authenticated(request):
        return jsonify({"success": False, "message": "Unauthorized. Invalid API Key."}), 401
    try:
        status_data = fetch_market_status_data()
        return jsonify({"success": True, "data": status_data})
    except Exception as e:
        logging.error(f"Error in /market/status: {str(e)}")
        return jsonify({"success": False, "message": "Failed to fetch market status."}), 500


@market_bp.route('/api/v1/market/chart', methods=['GET'])
def market_chart():
    if not is_authenticated(request):
        return jsonify({"success": False, "message": "Unauthorized. Invalid API Key."}), 401
    try:
        chart_data = fetch_market_chart_data()
        return jsonify({"success": True, "data": chart_data})
    except Exception as e:
        logging.error(f"Error in /market/chart: {str(e)}")
        return jsonify({"success": False, "message": "Failed to fetch chart data."}), 500


def fetch_market_status_data():
    url = "https://chukul.com/api/tools/market/status/"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def fetch_market_chart_data():
    url = "https://chukul.com/api/data/intrahistorydata/?symbol=NEPSE"
    response = requests.get(url)
    response.raise_for_status()
    raw_data = response.json()
    return [
        {
            "id": item.get("id"),
            "symbol": item.get("symbol"),
            "close": item.get("close"),
            "date": format_date(item.get("date"))
        }
        for item in raw_data
    ]
