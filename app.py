import logging
from base64 import b64encode
import requests
from flask import Flask
import os
import json
import time
from datetime import datetime

# Basic logging setup for debugging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Configuration for GitHub API
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')  # GitHub API token
REPO_NAME = 'nitsofts/hsmmarketdata'  # Repository name on GitHub
FILE_PATH = 'response/prospectus.json'  # Path to the file in the repository
BRANCH = 'main'  # Branch to update in the repository

def get_file_size(url):
    try:
        response = requests.head(url)
        file_size_bytes = int(response.headers.get('content-length', 0))
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)  # Convert bytes to MB
        return file_size_mb
    except Exception:
        return "N/A"  # Return "N/A" if size can't be calculated

def scrape_sebon_data(page_numbers):
    combined_data = []

    for page_number in page_numbers:
        url = f"https://www.sebon.gov.np/prospectus?page={page_number}"
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', class_='table')
            table_rows = table.select('tbody tr')
            data_list = []

            for row in table_rows:
                row_data = row.find_all('td')
                if len(row_data) == 4:
                    file_url = row_data[3].find('a').get('href', '') if row_data[3].find('a') else row_data[2].find('a').get('href', '')
                    file_size = get_file_size(file_url) if file_url else "N/A"

                    data = {
                        "title": row_data[0].get_text(strip=True),
                        "date": row_data[1].get_text(strip=True),
                        "english": row_data[2].find('a').get('href', '') if row_data[2].find('a') else '',
                        "nepali": row_data[3].find('a').get('href', '') if row_data[3].find('a') else '',
                        "fileSize": file_size
                    }
                    data_list.append(data)

            combined_data.extend(data_list)
        else:
            print(f"Failed to retrieve page {page_number}. Status code:", response.status_code)

    return combined_data

def update_prospectus_on_github(data):
    url = f'https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Fetch the current SHA to update the file instead of creating a new one
    response = requests.get(url, headers=headers)
    sha = response.json().get('sha') if response.status_code == 200 else None

    # Prepare the content
    content = b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
    update_data = {
        'message': f'Update {FILE_PATH}',
        'content': content,
        'branch': BRANCH,
    }
    if sha:  # If file exists, include the SHA to update; otherwise, create new file
        update_data['sha'] = sha

    # Send the request to update the file
    put_response = requests.put(url, headers=headers, json=update_data)
    if put_response.status_code in [200, 201]:
        logging.info(f"Successfully updated {FILE_PATH} in repository.")
        return True, 'File updated successfully'
    else:
        logging.error(f"Failed to update {FILE_PATH}. Response: {put_response.text}")
        return False, put_response.text


@app.route('/get_prospectus/<page_numbers>', methods=['GET'])
def get_prospectus(page_numbers):
    page_numbers = [int(page) for page in page_numbers.split(',')]
    data = scrape_sebon_data(page_numbers)

    success, message = update_prospectus_on_github(data)
    if success:
        response = {'success': True, 'message': 'Prospectus data updated on GitHub.'}
        return jsonify(response), 200
    else:
        response = {'success': False, 'message': f'Failed to update prospectus data on GitHub. Error: {message}'}
        return jsonify(response), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
