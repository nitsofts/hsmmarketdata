from flask import Blueprint, jsonify, request
import logging
import requests
import time

# Blueprint for watchlist data
watchlist_bp = Blueprint('watchlist', __name__)

# Function to fetch companies' data (name, symbol, type, and sector_id)
def fetch_companies_data():
    current_time_ms = int(round(time.time() * 1000))
    url = f"https://chukul.com/api/data/symbol/?_={current_time_ms}"  # Replace with the actual endpoint to get company data
    response = requests.get(url)

    if response.status_code == 200:
        companies = response.json()
        company_list = []

        # Extract company name, symbol, type, and sector_id
        for company in companies:
            if "symbol" in company and "name" in company and "type" in company and "sector_id" in company:
                company_data = {
                    "symbol": company["symbol"],
                    "name": company["name"],
                    "type": company["type"],         # Added "type"
                    "sector_id": company["sector_id"]  # Added "sector_id"
                }
                company_list.append(company_data)

        return company_list
    else:
        return None

# Function to fetch companies' performance data (open, close, volume, etc.)
def fetch_companies_data():
    current_time_ms = int(round(time.time() * 1000))
    url = f"https://chukul.com/api/data/intrahistorydata/performance/?type=stock&_={current_time_ms}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()  # List of companies with performance data
    else:
        return None


# New endpoint to get list of companies (name, symbol, type, and sector_id)
@watchlist_bp.route('/watchlist/get_companies_symbol', methods=['GET'])
def get_companies():
    try:
        # Fetch the list of companies from the external API
        companies_data = fetch_companies_data()
        
        if companies_data:
            return jsonify(companies_data)
        else:
            return jsonify({"error": "Failed to fetch companies data"}), 500
    except Exception as e:
        logging.error(f"An error occurred while fetching companies data: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch companies data.'}), 500


# New endpoint to get performance data for specified stocks or all stocks
@watchlist_bp.route('/get_companies_data', methods=['GET'])
def get_companies_data():
    try:
        # Fetch all companies' performance data
        all_companies_data = fetch_companies_data()
        
        if not all_companies_data:
            return jsonify({"error": "Failed to fetch companies performance data"}), 500

        # Get 'stocks' query parameter from the request
        stocks_param = request.args.get('stocks', default='all', type=str)

        # If 'stocks' is 'all' or not provided, return all data
        if stocks_param == 'all' or not stocks_param:
            return jsonify(all_companies_data)

        # Split the stocks parameter and clean up whitespace and case
        stocks_list = [symbol.strip().upper() for symbol in stocks_param.split('&')]

        # Filter the companies' performance data based on the cleaned symbols
        filtered_data = [
            company for company in all_companies_data if company['symbol'].strip().upper() in stocks_list
        ]

        # Check if no data was found for any of the requested symbols
        missing_symbols = [
            symbol for symbol in stocks_list if not any(company['symbol'].strip().upper() == symbol for company in filtered_data)
        ]
        
        if missing_symbols:
            return jsonify({
                "message": f"No data found for the following symbols: {', '.join(missing_symbols)}"
            }), 404

        return jsonify(filtered_data)

    except Exception as e:
        logging.error(f"An error occurred while fetching companies data: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch companies data.'}), 500
