from flask import Blueprint, jsonify, request
import logging
import requests
from datetime import datetime

market_state_bp = Blueprint('market_state', __name__)

def format_date(date_string):
    # Parse the date string and format it as desired
    try:
        # Parse the date string into a datetime object
        date_obj = datetime.fromisoformat(date_string)
        # Format the datetime object to a string with just the time
        return date_obj.strftime("%H:%M:%S")
    except ValueError:
        # Return the original string if parsing fails
        return date_string

@market_state_bp.route('/get_market_state', methods=['GET'])
def get_market_state():
    type_param = request.args.get('type')  # Access request.args to get 'type' parameter

    if type_param == 'market_state_data':
        try:
            market_status_data = fetch_market_status_data()
            intrahistory_data = fetch_intrahistory_data()

            # Extract relevant data from intrahistory_data for the first item
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

            # Wrap the dictionary in a list
            return jsonify([market_state_data])

        except Exception as e:
            logging.error(f"An error occurred while fetching market state data: {str(e)}")
            return jsonify({'success': False, 'message': 'Failed to fetch market state data.'}), 500

    elif type_param == 'market_chart_data':
        try:
            intrahistory_data = fetch_intrahistory_data()

            # Filter the data to only include the required fields
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

        except Exception as e:
            logging.error(f"An error occurred while fetching market chart data: {str(e)}")
            return jsonify({'success': False, 'message': 'Failed to fetch market chart data.'}), 500

    else:
        return jsonify({'success': False, 'message': 'Invalid type parameter.'}), 400


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
