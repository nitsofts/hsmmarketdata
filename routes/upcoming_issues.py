from flask import Blueprint, jsonify, request
import logging
import requests
import time
from datetime import datetime
from pyBSDate import convert_AD_to_BS

upcoming_issues_bp = Blueprint('upcoming_issues', __name__)

@upcoming_issues_bp.route('/get_upcoming_issues', methods=['GET'])
def get_upcoming_issues():
    issue_type_map = {
        'ipo': 1,
        'right': 3,
        'fpo': 2,
        'local': 5,
        'debenture': 7,
        'migrant': 8,
        'all': 'all'
    }

    issue_type = request.args.get('type', default='all', type=str)
    limit = request.args.get('limit', default=20, type=int)

    try:
        if issue_type == 'all':
            all_data = []
            for key, value in issue_type_map.items():
                if key != 'all':
                    data = fetch_upcoming_issues(value, limit=limit)
                    for item in data:
                        item['issueType'] = key
                    all_data.extend(data)
            data_to_update = all_data
        else:
            if issue_type in issue_type_map:
                type_value = issue_type_map[issue_type]
                data = fetch_upcoming_issues(type_value, limit=limit)
                for item in data:
                    item['issueType'] = issue_type
            else:
                return jsonify({"error": "Invalid type parameter"}), 400

        return jsonify(data)
    except Exception as e:
        logging.error(f"An error occurred while fetching upcoming issues: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch upcoming issues.'}), 500

def fetch_upcoming_issues(issue_type, limit=20):
    url = "https://www.sharesansar.com/existing-issues"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://www.sharesansar.com/existing-issues",
        "X-Requested-With": "XMLHttpRequest",
    }

    current_timestamp = int(time.time() * 1000)
    payload = {
        "draw": 1,
        "start": 0,
        "length": limit,
        "search[value]": "",
        "search[regex]": "false",
        "type": issue_type,
        "_": current_timestamp,
    }

    response = requests.get(url, headers=headers, params=payload)
    if response.status_code == 200:
        data = response.json().get("data", [])
        formatted_data = []
        for entry in data:
            opening_date_bs = convert_date_to_bs(entry.get("opening_date"))
            closing_date_bs = convert_date_to_bs(entry.get("closing_date"))
            extended_closing_date_bs = convert_date_to_bs(entry.get("final_date"))
            status = format_status(entry.get("status"))
            formatted_entry = format_entry(entry, opening_date_bs, closing_date_bs, extended_closing_date_bs, status)
            formatted_data.append(formatted_entry)
        return formatted_data
    else:
        raise Exception(f"Error fetching data: {response.status_code}")

def convert_date_to_bs(date_str):
    if not date_str:
        return "In Progress"
    ad_date = datetime.strptime(date_str, "%Y-%m-%d")
    try:
        bs_date_tuple = convert_AD_to_BS(ad_date.year, ad_date.month, ad_date.day)
        return datetime(*bs_date_tuple).strftime("%Y-%m-%d")
    except ValueError:
        return "Invalid Date"

def format_status(status_code):
    status_map = {0: "Open", 1: "Closed", -2: "In Progress"}
    return status_map.get(status_code, "Unknown")

def format_entry(entry, opening_date_bs, closing_date_bs, extended_closing_date_bs, status):
    return {
        "companyName": entry["company"]["companyname"].split('>')[1].split('<')[0],
        "companySymbol": entry["company"]["symbol"].split('>')[1].split('<')[0],
        "units": format_number(entry.get("total_units")),
        "price": format_number(entry.get("issue_price")),
        "openingDateAd": entry.get("opening_date", "In Progress"),
        "closingDateAd": entry.get("closing_date", "In Progress"),
        "extendedClosingDateAd": entry.get("final_date", "In Progress"),
        "openingDateBs": opening_date_bs,
        "closingDateBs": closing_date_bs,
        "extendedClosingDateBs": extended_closing_date_bs,
        "listingDate": entry.get("listing_date", ""),
        "issueManager": entry.get("issue_manager", ""),
        "status": status,
    }

def format_number(number_str):
    try:
        number = float(number_str)
        return str(int(number)) if number.is_integer() else str(number)
    except (TypeError, ValueError):
        return "N/A"
