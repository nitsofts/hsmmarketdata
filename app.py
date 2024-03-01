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

# Basic logging setup for debugging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Configuration for GitHub API
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')  # GitHub API token
REPO_NAME = 'nitsofts/hsmmarketdata'  # Repository name on GitHub
BRANCH = 'main'  # Branch to update in the repository

def fetch_data_from_github(file_path):
    url = f'https://raw.githubusercontent.com/{REPO_NAME}/{BRANCH}/{file_path}'
    headers = {'Accept': 'application/vnd.github.v3.raw'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        logging.error(f"Failed to fetch {file_path} from GitHub. Status code: {response.status_code}")
        return None


# This function is for writing updated data on github page
# GitHub Update Functions
def update_data_on_github(file_path, data):
    url = f'https://api.github.com/repos/{REPO_NAME}/contents/{file_path}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get(url, headers=headers)
    sha = response.json().get('sha') if response.status_code == 200 else None
    content = b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
    update_data = {
        'message': f'Update {file_path}',
        'content': content,
        'branch': BRANCH,
    }
    if sha:
        update_data['sha'] = sha
    put_response = requests.put(url, headers=headers, json=update_data)
    if put_response.status_code in [200, 201]:
        logging.info(f"Successfully updated {file_path} in repository.")
        return True, f'{file_path} updated successfully'
    else:
        logging.error(f"Failed to update {file_path}. Response: {put_response.text}")
        return False, put_response.text

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
    

# API Endpoints to make requests
# 1) TOP PERFORMERS
# 2) PROSPECTS
# 3) CDSC DATA

@app.route('/get_top_performers', methods=['GET'])
def get_top_performers():
    limit = request.args.get('limit', default=100, type=int)
    indicator = request.args.get('indicator', default='gainers', type=str)  # Default to 'gainers' if not specified

    if indicator not in ['turnover', 'gainers', 'losers', 'sharestraded', 'transactions']:
        return jsonify({'success': False, 'message': 'Invalid indicator specified'}), 400

    # Fetch the top performers data
    data = fetch_top_performers(limit, indicator)
    
    # Update the corresponding file on GitHub
    file_path = f'response/top_{indicator}.json'
    success, message = update_data_on_github(file_path, data)

    if success:
        return jsonify(data), 200
    else:
        return jsonify({'success': False, 'message': message}), 500

    
# Prospectus: /get_prospectus for all 3 pages (1,2,3)
# Prospectus: /get_prospectus?pages=1,2 for specific set of pages
@app.route('/get_prospectus', methods=['GET'])
def get_prospectus():
    pages_str = request.args.get('pages', '1,2,3')
    pages = [int(page) for page in pages_str.split(',')]
    data = scrape_prospectus(pages)

    # Update response/prospectus.json
    file_path_prospectus = 'response/prospectus.json'
    success_prospectus, message_prospectus = update_data_on_github(file_path_prospectus, data)

    if success_prospectus:
        # Fetch current lastRefresh timestamp from dataRefresh/prospectus.json
        file_path_timestamp = 'data_refresh/prospectus.json'
        timestamp_data = fetch_data_from_github(file_path_timestamp)

        if timestamp_data:
            # Update the lastRefresh timestamp
            timestamp_data[0]['lastRefreshInMs'] = int(time.time() * 1000)
            nepal_tz = pytz.timezone('Asia/Kathmandu')
            nepal_time = datetime.fromtimestamp(timestamp_data[0]['lastRefreshInMs'] / 1000, nepal_tz)
            timestamp_data[0]['lastRefreshInString'] = nepal_time.strftime('%a %d %b %Y %I:%M:%S %p')

            # Update dataRefresh/prospectus.json on GitHub
            success_timestamp, message_timestamp = update_data_on_github(file_path_timestamp, timestamp_data)

            if success_timestamp:
                return jsonify(data)
            else:
                # Rollback response/prospectus.json if dataRefresh/prospectus.json update fails
                rollback_prospectus, rollback_message = update_data_on_github(file_path_prospectus, [])
                return jsonify({'success': False, 'message': f'Failed to update dataRefresh/prospectus.json. Error: {message_timestamp}'})
        else:
            return jsonify({'success': False, 'message': 'Failed to fetch data_refresh/prospectus.json from GitHub.'})
    return jsonify({'success': False, 'message': f'Failed to update response/prospectus.json. Error: {message_prospectus}'})


@app.route('/get_cdsc_data', methods=['GET'])
def get_cdsc_data():
    data = scrape_cdsc_data()  # You need to define this function
    file_path_cdsc_data = 'response/cdsc_data.json'
    success_cdsc_data, message_cdsc_data = update_data_on_github(file_path_cdsc_data, data)

    if success_cdsc_data:
        # Fetch current lastRefresh timestamp from dataRefresh/prospectus.json
        file_path_timestamp = 'data_refresh/cdsc_data.json'
        timestamp_data = fetch_data_from_github(file_path_timestamp)
        
        if timestamp_data:
            # Update the lastRefresh timestamp
            timestamp_data[0]['lastRefreshInMs'] = int(time.time() * 1000)
            nepal_tz = pytz.timezone('Asia/Kathmandu')
            nepal_time = datetime.fromtimestamp(timestamp_data[0]['lastRefreshInMs'] / 1000, nepal_tz)
            timestamp_data[0]['lastRefreshInString'] = nepal_time.strftime('%a %d %b %Y %I:%M:%S %p')

            # Update dataRefresh/prospectus.json on GitHub
            success_timestamp, message_timestamp = update_data_on_github(file_path_timestamp, timestamp_data)

            if success_timestamp:
                return jsonify(data)
            else:
                # Rollback response/prospectus.json if dataRefresh/prospectus.json update fails
                rollback_cdscData, rollback_message = update_data_on_github(file_path_prospectus, [])
                return jsonify({'success': False, 'message': f'Failed to update data_refresh/cdsc_data.json. Error: {message_timestamp}'})
        else:
            return jsonify({'success': False, 'message': 'Failed to fetch data_refresh/cdsc_data.json from GitHub.'})
       
    else:
        return jsonify({'success': False, 'message': f'Failed to update cdsc_data.json. Error: {message_cdsc_data}'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
