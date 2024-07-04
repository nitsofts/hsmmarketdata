from flask import Blueprint, jsonify
import logging
import requests

stock_movement_summary_bp = Blueprint('stock_movement_summary', __name__)

@stock_movement_summary_bp.route('/get_stock_movement_summary', methods=['GET'])
def get_stock_movement_summary():
    try:
       data = fetch_and_process_data()
        # Use json.dumps with sort_keys=False to maintain order
        return json.dumps(data, sort_keys=False)
    except Exception as e:
        logging.error(f"An error occurred while fetching stock movement summary data: {str(e)}")
        return jsonify([{'success': False, 'message': 'Failed to fetch stock movement data.'}]), 500

def fetch_and_process_data():
    url = "https://chukul.com/api/data/intrahistorydata/performance/?type=stock"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    advanced = 0
    declined = 0
    unchanged = 0
    positive_circuit = 0
    negative_circuit = 0

    for item in data:
        percentage_change = item.get('percentage_change')
        if percentage_change is None:
            unchanged += 1
        elif percentage_change > 9.9:
            positive_circuit += 1
        elif -10.0 < percentage_change <= -9.9:
            negative_circuit += 1
        elif percentage_change > 0:
            advanced += 1
        elif percentage_change < 0:
            declined += 1
        elif percentage_change == 0:
            unchanged += 1

    result = {
        "advanced": advanced,
        "declined": declined,
        "unchanged": unchanged,
        "positiveCircuit": positive_circuit,
        "negativeCircuit": negative_circuit
    }
    
    return result
