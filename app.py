import logging
from base64 import b64encode
import requests
from flask import Flask, jsonify, request
import os
import json
from bs4 import BeautifulSoup
import time 
import pytz
from datetime import datetime
from pyBSDate import convert_AD_to_BS

# Basic logging setup for debugging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

@app.route('/')
def home():
    return "Thanks for visiting! Your IP has been recorded."

# ALL FUNCTIONS
# Function for fetching and writing all TOP PERFORMERS data into github page
def fetch_top_performers(limit, specific_indicator):
    result_data = {}
    current_timestamp = int(time.time() * 1000)
    url = f"https://nepalipaisa.com/api/GetTopMarketMovers?indicator={specific_indicator}&sectorCode=&limit={limit}&_={current_timestamp}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        result_data = data.get('result', [])  # Extract only the 'result' part
        for item in result_data:
            item['type'] = specific_indicator
    else:
        logging.error(f"Error fetching {specific_indicator}: {response.status_code}")

    return result_data
    
# Function for scraping PROSPECTUS
def scrape_prospectus(page_numbers):
    combined_data = []
    
    def get_prospectus_size(url):
        try:
            response = requests.head(url)
            file_size_bytes = int(response.headers.get('content-length', 0))
            file_size_mb = round(file_size_bytes / (1024 * 1024), 2)  # Convert bytes to MB
            return file_size_mb
        except Exception:
            return "N/A"  # Return "N/A" if size can't be calculated
    
    for page_number in page_numbers:
        url = f"https://www.sebon.gov.np/prospectus?page={page_number}"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', class_='table')
            table_rows = table.select('tbody tr')
            for row in table_rows:
                row_data = row.find_all('td')
                if len(row_data) == 4:
                    file_url = row_data[3].find('a').get('href', '') if row_data[3].find('a') else row_data[2].find('a').get('href', '')
                    file_size = get_prospectus_size(file_url) if file_url else "N/A"
                    data = {
                        "title": row_data[0].get_text(strip=True),
                        "date": row_data[1].get_text(strip=True),
                        "english": row_data[2].find('a').get('href', '') if row_data[2].find('a') else '',
                        "nepali": row_data[3].find('a').get('href', '') if row_data[3].find('a') else '',
                        "fileSize": file_size
                    }
                    combined_data.append(data)
        else:
            logging.error(f"Failed to retrieve page {page_number}. Status code: {response.status_code}")
    return combined_data

# Function for scraping CDSC DATA
def scrape_cdsc_data():
    # Define the URL of the website
    url = "https://www.cdsc.com.np/"

    # Send an HTTP request to the website with SSL certificate verification disabled
    response = requests.get(url, verify=False)
    # Parse the HTML content of the website
    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")
    # Locate the div containing the "Current Public Issue" information
    div = soup.find("div", class_="fun-factor-area")
    # Extract all the "h4" elements from the "fun-custom-column" div
    h4_elements = div.find_all("h4")
    # Create a list to store the extracted data in the new format
    data = []
    # Define important positions
    important_positions = [8, 10, 11, 12, 13]

    # Format and add the data to the list
    for i in range(0, len(h4_elements), 2):
        imp_value = "true" if int(i/2) in important_positions else "false"
        item = {
            "id": str(int(i/2)),  # ID as a string
            "dataKey": h4_elements[i + 1].text.strip(),
            "dataValue": h4_elements[i].text.strip(),
            "imp": imp_value
        }
        data.append(item)

    # Sort the data so that items with "imp": "true" are at the top
    data.sort(key=lambda x: x['imp'], reverse=True)
    
    return data

def fetch_market_indices(api_endpoint):
    current_time_ms = int(round(time.time() * 1000))
    url = f"https://nepalipaisa.com/api/{api_endpoint}?_={current_time_ms}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()['result']
    else:
        return None

def fetch_upcoming_issues(issue_type, limit=20):
    """
    Fetches and formats upcoming issue data based on the issue type and limit.
    Args:
        issue_type (int): The type value indicating the kind of issue (e.g., IPO, FPO).
        limit (int): The maximum number of records to fetch.

    Returns:
        list: A list of dictionaries containing formatted upcoming issue data.
    """
    # URL and headers for the request
    url = "https://www.sharesansar.com/existing-issues"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://www.sharesansar.com/existing-issues",
        "X-Requested-With": "XMLHttpRequest",
    }

    # Construct the payload for the GET request
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

    # Send the request
    response = requests.get(url, headers=headers, params=payload)
    if response.status_code == 200:
        data = response.json().get("data", [])
        formatted_data = []
        for entry in data:
            # Extract and format dates
            opening_date_bs = convert_date_to_bs(entry.get("opening_date"))
            closing_date_bs = convert_date_to_bs(entry.get("closing_date"))
            extended_closing_date_bs = convert_date_to_bs(entry.get("final_date"))
            
            # Format status
            status = format_status(entry.get("status"))
            
            # Format entry
            formatted_entry = format_entry(entry, opening_date_bs, closing_date_bs, extended_closing_date_bs, status)
            formatted_data.append(formatted_entry)
        return formatted_data
    else:
        raise Exception(f"Error fetching data: {response.status_code}")

    def convert_date_to_bs(date_str):
        """Converts a date string from AD to BS."""
        if not date_str:
            return "In Progress"
        ad_date = datetime.strptime(date_str, "%Y-%m-%d")
        try:
            bs_date_tuple = convert_AD_to_BS(ad_date.year, ad_date.month, ad_date.day)
            return datetime(*bs_date_tuple).strftime("%Y-%m-%d")
        except ValueError:
            return "Invalid Date"

    def format_status(status_code):
        """Formats the status based on the status code."""
        status_map = {0: "Open", 1: "Closed", -2: "In Progress"}
        return status_map.get(status_code, "Unknown")

    def format_entry(entry, opening_date_bs, closing_date_bs, extended_closing_date_bs, status):
        """Formats a single entry with the necessary data."""
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
        """Formats a number string to remove unnecessary decimal places or returns 'N/A'."""
        try:
            number = float(number_str)
            return str(int(number)) if number.is_integer() else str(number)
        except (TypeError, ValueError):
            return "N/A"
    

# API Endpoints to make requests
# 1) TOP PERFORMERS
# 2) PROSPECTS
# 3) CDSC DATA
# 4) Market Indices

@app.route('/get_top_performers', methods=['GET'])
def get_top_performers():
    limit = request.args.get('limit', default=100, type=int)
    indicator = request.args.get('indicator', default='gainers', type=str)  # Default to 'gainers' if not specified

    if indicator not in ['turnover', 'gainers', 'losers', 'sharestraded', 'transactions']:
        return jsonify({'success': False, 'message': 'Invalid indicator specified'}), 400
    
    if success:
        return jsonify(data)
    else:
        return jsonify({'success': False, 'message': message}), 500


    
# Prospectus: /get_prospectus for all 3 pages (1,2,3)
# Prospectus: /get_prospectus?pages=1,2 for specific set of pages
@app.route('/get_prospectus', methods=['GET'])
def get_prospectus():
    pages_str = request.args.get('pages', '1,2,3')
    pages = [int(page) for page in pages_str.split(',')]
    data = scrape_prospectus(pages)


    if success_prospectus:
        return jsonify(data)
    else:
        return jsonify({'success': False, 'message': message}), 500


# CDSC Data: /get_cdsc_data
@app.route('/get_cdsc_data', methods=['GET'])
def get_cdsc_data():
    data = scrape_cdsc_data()  # You need to define this function
    
    if success_cdsc_data:
        return jsonify(data)
    else:
        return jsonify({'success': False, 'message': message}), 500

# Market Indices: /get_market_indices for market indices & sub-indices as default
# Market Indices: /get_market_indices?type=index for market indices
# Market Indices: /get_market_indices?type=subindex for market sub-indices
# Market Indices: /get_market_indices?type=all for both market indices & sub-indices
@app.route('/get_market_indices', methods=['GET'])
def get_market_indices():
    indices_type = request.args.get('type', default='all_indices', type=str)
    

    # Fetch the data based on the type
    if indices_type in ['indices', 'sub_indices']:
        api_endpoint = 'GetIndexLive' if indices_type == 'indices' else 'GetSubIndexLive'
        data = fetch_market_indices(api_endpoint)
    elif indices_type == 'all_indices':
        index_data = fetch_market_indices('GetIndexLive')
        subindex_data = fetch_market_indices('GetSubIndexLive')
        data = index_data + subindex_data if index_data and subindex_data else None
    else:
        return jsonify({"error": "Invalid type parameter"}), 400

        if not success_response:
            return jsonify({'success': False, 'message': message_response}), 500
        else:
            return jsonify(data)


# Upcoming Issues: /get_upcoming_issues for all types of upcoming issues as default
# Upcoming Issues: /get_upcoming_issues?type=ipo for upcoming IPO issues
# Upcoming Issues: /get_upcoming_issues?type=right for upcoming right issues
# Upcoming Issues: /get_upcoming_issues?type=fpo for upcoming FPO issues
# Upcoming Issues: /get_upcoming_issues?type=local for upcoming local issues
# Upcoming Issues: /get_upcoming_issues?type=debenture for upcoming debenture issues
# Upcoming Issues: /get_upcoming_issues?type=migrant for upcoming migrant issues
@app.route('/get_upcoming_issues', methods=['GET'])
def get_upcoming_issues():
    # Map issue type names to type values used in fetch_data
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

    # For 'all', iterate over all issue types except 'all'
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
            for item in data_to_update:
                item['issueType'] = issue_type
        else:
            return jsonify({"error": "Invalid type parameter"}), 400

    
    if not success_response:
        return jsonify({'success': False, 'message': message_response}), 500
    else:
        return jsonify(data)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
