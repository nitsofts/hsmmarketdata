from flask import Blueprint, jsonify, request
import logging
import requests
import time

# Blueprint for watchlist data
watchlist_bp = Blueprint('watchlist', __name__)

# Function to fetch companies' data (name and symbol)
def fetch_companies_data():
    current_time_ms = int(round(time.time() * 1000))
    url = f"https://chukul.com/api/data/symbol/?_={current_time_ms}"  # Replace with the actual endpoint to get company data
    response = requests.get(url)

    if response.status_code == 200:
        companies = response.json()
        company_list = []

        # Extract only the company name and symbol
        for company in companies:
            if "symbol" in company and "name" in company:
                company_data = {
                    "symbol": company["symbol"],
                    "name": company["name"]
                }
                company_list.append(company_data)

        return company_list
    else:
        return None

# New endpoint to get list of companies (name and symbol)
@watchlist_bp.route('/get_companies', methods=['GET'])
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


