from flask import Blueprint, jsonify, request
import logging
import requests
from datetime import datetime

# Updated Blueprint name and URL prefix
marketstate_bp = Blueprint('marketstate', __name__)

# Format ISO datetime string into HH:MM:SS
def format_date(date_string):
    try:
        date_obj = datetime.fromisoformat(date_string)
        return date_obj.strftime("%H:%M:%S")
    except ValueError:
        return date_string

# Unified endpoint for market data
@marketstate_bp.route('/get_market_data', methods=['POST'])
def get_market_data():
    try:
        data = request.get_json()
        type_param = data.get('type') if data else None

        if type_param == 'market_state_data':
            market_status_data = fetch_market_status_data()
            intrahistory_data = fetch_intrahistory_data()
            intrahistory_item = intrahistory_data[0]

            market_state_data = {
                "is_open": market_status_data.get('is_open'),
                "as_of": market_status_data.get('as_of'),
                "as_of_live": market_status_data.get('as_of_live'),
                "as_of_weekly": market_status_data.get('as_of_weekly'),
                "as_of_hourly": market_status_data.get('as_of_hourly'),
                "as_of_live_unix": market_status_data.get('as_of_live_unix'),
                "date": format_date(intrahistory_item.get('date')),
                "symbol": intrahistory_item.get('symbol'),
                "open": intrahistory_item.get('open'),
                "high": intrahistory_item.get('high'),
                "low": intrahistory_item.get('low'),
                "close": intrahistory_item.get('close'),
                "curr_volume": intrahistory_item.get('curr_volume'),
                "volume": intrahistory_item.get('volume'),
                "curr_amount": intrahistory_item.get('curr_amount'),
                "amount": intrahistory_item.get('amount')
            }

            return jsonify([market_state_data])

        elif type_param == 'market_chart_data':
            intrahistory_data = fetch_intrahistory_data()
            filtered_data = [
                {
                    "id": item.get("id"),
                    "close": item.get("close"),
                    "date": format_date(item.get("date")),
                    "symbol": item.get("symbol")
                }
                for item in intrahistory_data
            ]
            return jsonify(filtered_data)

        else:
            return jsonify({'success': False, 'message': 'Invalid or missing "type" parameter.'}), 400

    except Exception as e:
        logging.error(f"Error in /marketstate/get_market_data: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch market data.'}), 500

# External data fetching helpers
def fetch_market_status_data():
    url = "https://chukul.com/api/tools/market/status/"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def fetch_intrahistory_data():
    url = "https://chukul.com/api/data/intrahistorydata/?symbol=NEPSE"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
