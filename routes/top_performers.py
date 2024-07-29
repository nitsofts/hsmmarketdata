from flask import Blueprint, jsonify, request
import logging
import requests
import time

top_performers_bp = Blueprint('top_performers', __name__)

@top_performers_bp.route('/get_top_performers', methods=['GET'])
def get_top_performers():
    limit = request.args.get('limit', default=100, type=int)
    indicator = request.args.get('indicator', default='gainers', type=str)
    
    if indicator not in ['turnover', 'gainers', 'losers', 'sharestraded', 'transactions', 'all']:
        return jsonify({'success': False, 'message': 'Invalid indicator specified'}), 400
    
    try:
        data = fetch_top_performers(limit, indicator)
        return jsonify(data)
    except Exception as e:
        logging.error(f"Error fetching top performers: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to retrieve top performers data.'}), 500

def fetch_top_performers(limit, specific_indicator):
    result_data = []
    current_timestamp = int(time.time() * 1000)
    
    if specific_indicator == 'all':
        indicators = ['turnover', 'gainers', 'losers', 'sharestraded']
    else:
        indicators = [specific_indicator]
    
    for indicator in indicators:
        url = f"https://nepalipaisa.com/api/GetTopMarketMovers?indicator={indicator}&sectorCode=&limit={limit}&_={current_timestamp}"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for HTTP errors
            
            data = response.json()
            fetched_data = data.get('result', [])  # Extract only the 'result' part
            for item in fetched_data:
                item['type'] = indicator
            result_data.extend(fetched_data)  # Combine data from all indicators
            
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred for {indicator}: {http_err}")
            logging.error(f"Response content: {response.text}")
        except Exception as err:
            logging.error(f"Other error occurred for {indicator}: {err}")
            if response is not None:
                logging.error(f"Response content: {response.text}")
    
    return result_data
