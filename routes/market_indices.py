from flask import Blueprint, jsonify, request
import logging
import requests
import time

market_indices_bp = Blueprint('market_indices', __name__)

@market_indices_bp.route('/get_market_indices', methods=['GET'])
def get_market_indices():
    indices_type = request.args.get('type', default='all_indices', type=str)

    try:
        if indices_type in ['indices', 'sub_indices']:
            api_endpoint = 'GetIndexLive' if indices_type == 'indices' else 'GetSubIndexLive'
            data = fetch_market_indices(api_endpoint)
        elif indices_type == 'all_indices':
            index_data = fetch_market_indices('GetIndexLive')
            subindex_data = fetch_market_indices('GetSubIndexLive')
            data = index_data + subindex_data if index_data and subindex_data else None
        else:
            return jsonify({"error": "Invalid type parameter"}), 400
        
        return jsonify(data)
    except Exception as e:
        logging.error(f"An error occurred while fetching market indices: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch market indices.'}), 500

def fetch_market_indices(api_endpoint):
    current_time_ms = int(round(time.time() * 1000))
    url = f"https://nepalipaisa.com/api/{api_endpoint}?_={current_time_ms}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()['result']
    else:
        return None
