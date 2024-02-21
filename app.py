import logging
from base64 import b64encode
import requests
from flask import Flask, jsonify, request
import os
import json
from bs4 import BeautifulSoup
import time 

# Basic logging setup for debugging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Configuration for GitHub API
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')  # GitHub API token
REPO_NAME = 'nitsofts/hsmmarketdata'  # Repository name on GitHub
BRANCH = 'main'  # Branch to update in the repository

# Function to get current timestamp in milliseconds
def get_current_timestamp_ms():
    return int(time.time() * 1000)

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

# Function to update dataRefresh.json
def update_data_refresh(data_type, timestamp, last_message):
    file_path = 'response/dataRefresh.json'
    refresh_data = {
        'cdscData': timestamp if data_type == 'cdsc' else None,
        'prospectus': timestamp if data_type == 'prospectus' else None,
        'topPerformers': timestamp if data_type == 'topPerformers' else None,
        'lastMessage': last_message
    }
    
    try:
        with open(file_path, 'r') as refresh_file:
            existing_data = json.load(refresh_file)
    except FileNotFoundError:
        existing_data = []

    for item in existing_data:
        if data_type in item:
            item[data_type] = timestamp
            item['lastMessage'] = last_message
            break
    else:
        existing_data.append(refresh_data)

    with open(file_path, 'w') as refresh_file:
        json.dump(existing_data, refresh_file, indent=2)
        

# ALL FUNCTIONS
# Function for fetching and writing all TOP PERFORMERS data into github page
def fetch_and_update_top_performers(limit):
    indicators = ['turnover', 'gainers', 'losers', 'sharestraded', 'transactions']
    all_data = {}

    def fetch_market_movers(indicator):
        current_timestamp = int(time.time() * 1000)
        url = f"https://nepalipaisa.com/api/GetTopMarketMovers?indicator={indicator}&sectorCode=&limit={limit}&_={current_timestamp}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            result_data = data.get('result', [])  # Extract only the 'result' part
            # Add 'type' attribute to each item in the result
            for item in result_data:
                item['type'] = indicator
            return result_data
        else:
            raise Exception(f"Error: {response.status_code}")

    for indicator in indicators:
        data = fetch_market_movers(indicator)
        file_path = f'response/top{indicator.capitalize()}.json'
        success, message = update_data_on_github(file_path, data)
        all_data[indicator] = {'success': success, 'message': message}

    return all_data
    
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

# TOP PERFORMERS: /get_top_performers for each 100 items of Top Gainers, Top Losers, Top Turnover, Top Volume, Top Transactions
@app.route('/get_top_performers', methods=['GET'])
def get_top_performers():
    limit = request.args.get('limit', default=100, type=int)
    data = fetch_and_update_top_performers(limit)
    
    timestamp = get_current_timestamp_ms()  # Get current timestamp

    file_path = 'response/topPerformers.json'
    success, message = update_data_on_github(file_path, data)
    if success:
        update_data_refresh('topPerformers', timestamp, 'Top Performers data updated successfully')
        return jsonify(data)
    else:
        update_data_refresh('topPerformers', timestamp, f'Failed to update Top Performers data. Error: {message}')
        return jsonify({'success': False, 'message': f'Failed to update top performers data on GitHub. Error: {message}'})

# Prospectus: /get_prospectus for all 3 pages (1,2,3)
# Prospectus: /get_prospectus?pages=1,2 for a specific set of pages
@app.route('/get_prospectus', methods=['GET'])
def get_prospectus():
    pages_str = request.args.get('pages', '1,2,3')
    pages = [int(page) for page in pages_str.split(',')]
    data = scrape_prospectus(pages)

    timestamp = get_current_timestamp_ms()  # Get current timestamp

    file_path = 'response/prospectus.json'
    success, message = update_data_on_github(file_path, data)
    if success:
        update_data_refresh('prospectus', timestamp, 'Prospectus data updated successfully')
        return jsonify(data)
    else:
        update_data_refresh('prospectus', timestamp, f'Failed to update Prospectus data. Error: {message}')
        return jsonify({'success': False, 'message': f'Failed to update prospectus data on GitHub. Error: {message}'})

# CDSC DATA: /get_cdsc_data all CDSC data
@app.route('/get_cdsc_data', methods=['GET'])
def get_cdsc_data():
    data = scrape_cdsc_data()  # You need to define this function
    
    timestamp = get_current_timestamp_ms()  # Get current timestamp

    file_path = 'response/cdscdata.json'
    success, message = update_data_on_github(file_path, data)
    if success:
        update_data_refresh('cdsc', timestamp, 'CDSC data updated successfully')
        response = {'success': True, 'message': 'CDSC data updated on GitHub.'}
    else:
        update_data_refresh('cdsc', timestamp, f'Failed to update CDSC data. Error: {message}')
        response = {'success': False, 'message': f'Failed to update CDSC data on GitHub. Error: {message}'}

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
