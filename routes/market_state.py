from flask import Blueprint, jsonify
import logging
import requests

market_state_bp = Blueprint('market_state', __name__)

@market_state_bp.route('/get_market_state', methods=['GET'])
def get_market_state():
    type_param = request.args.get('type')

    if type_param == 'market_state_data':
        try:
            market_status_data = fetch_market_status_data()
            intrahistory_data = fetch_intrahistory_data()

            # Extract relevant data from intrahistory_data for the first item
            intrahistory_item = intrahistory_data[0]
            additional_data = {
                "date": intrahistory_item.get('date'),
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

            market_status_data.update(additional_data)
            return jsonify(market_status_data)

        except Exception as e:
            logging.error(f"An error occurred while fetching market state data: {str(e)}")
            return jsonify({'success': False, 'message': 'Failed to fetch market state data.'}), 500

    elif type_param == 'market_chart_data':
        try:
            intrahistory_data = fetch_intrahistory_data()
            return jsonify(intrahistory_data)

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


if __name__ == "__main__":
    app.run(debug=True)
